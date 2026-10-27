"""Hardware view of the DVB-S2 LDPC decoder: quasi-cyclic structure, a
layer-parallel (bit-true) decoder model and an architecture cost model.

Quasi-cyclic structure.  With q = (N - K) / 360, write every check row and
every parity column as r = a + b*q (0 <= a < q, 0 <= b < 360) and renumber it
r' = a*360 + b.  An information bit l of group g that the address table sends
to x = a + b*q then sits in block (a, g) at in-block row (l + b) mod 360: the
permuted H is made of 360x360 circulants (cyclically shifted identities), and
the staircase becomes identities plus one circulant shifted by 1 with its
wrap-around entry missing.  A *layer* is one block row: the 360 checks
a, a + q, ..., a + 359q.  They can be processed at the same time by 360
check-node processors, apart from the weight-2 circulants (two addresses of a
table row equal mod q), where one bit feeds two checks of the same layer.

The decoder model processes the checks of a layer simultaneously, as the
hardware does: every check reads the posterior L before any of them writes,
and L is updated with the sum of the message changes,

    L <- sat(L + sum over the layer's checks of (R_new - R_old)),

which is how a weight-2 circulant is resolved in hardware.  ``fmt`` turns
the float model into a bit-true integer model.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import _kernels

GROUP = 360


# -- quasi-cyclic structure ------------------------------------------------------
@dataclass
class QCStructure:
    q: int
    k_blocks: int                       # information block columns, K / 360
    layers: list                        # per layer: list of (block column, shift)
    weight2: list                       # (layer, information block column) of weight-2 circulants
    missing: tuple = (0, 0)             # (layer, parity block column) of the circulant with the missing entry

    @property
    def n_blocks(self) -> int:
        return self.k_blocks + self.q

    @property
    def layer_degrees(self) -> list[int]:
        return [len(l) for l in self.layers]


def qc_structure(code) -> QCStructure:
    """Circulant description of a DVB-S2 LDPC code built from its address table."""
    q, kb = code.q, len(code.table)
    layers = [[] for _ in range(q)]
    weight2 = []
    for g, addrs in enumerate(code.table):
        seen = set()
        for x in addrs:
            a, b = x % q, x // q
            layers[a].append((g, b))
            if a in seen:
                weight2.append((a, g))
            seen.add(a)
    # staircase: parity column j = a + b*q is checked by rows j and j + 1
    for a in range(q):
        layers[a].append((kb + a, 0))
        if a > 0:
            layers[a].append((kb + a - 1, 0))
    layers[0].append((kb + q - 1, 1))   # rows (b+1)*q: shift 1, entry b = 359 missing
    for l in layers:
        l.sort()
    return QCStructure(q=q, k_blocks=kb, layers=layers, weight2=sorted(weight2), missing=(0, kb + q - 1))


def row_permutation(q: int) -> np.ndarray:
    """perm[r'] = r: the original row (or parity column) at permuted position r' = a*360 + b."""
    a, b = np.divmod(np.arange(q * GROUP), GROUP)
    return a + b * q


def permuted_H(code):
    """H with rows and parity columns renumbered so that it is made of 360x360 circulants."""
    rows = row_permutation(code.q)
    cols = np.concatenate([np.arange(code.k), code.k + rows])
    return code.H[rows][:, cols]


def circulant(shift: int, size: int = GROUP, missing_last: bool = False) -> np.ndarray:
    """Identity with column l moved to row (l + shift) mod size."""
    m = np.zeros((size, size), np.uint8)
    l = np.arange(size)
    m[(l + shift) % size, l] = 1
    if missing_last:
        m[(size - 1 + shift) % size, size - 1] = 0
    return m


# -- layer schedule ---------------------------------------------------------------
@dataclass
class LayerSchedule:
    """The checks of H grouped by layer: padded (360, d) index arrays."""
    q: int
    n: int
    idx: list            # per layer: (360, d) variable indices, padding = n
    valid: list          # per layer: (360, d) bool, or None if no padding
    row_ptr: np.ndarray  # flat CSR of the layer-ordered rows (for the numba kernel)
    cols: np.ndarray


def layer_schedule(code) -> LayerSchedule:
    cached = getattr(code, "_layer_schedule", None)
    if cached is not None:
        return cached
    q, n = code.q, code.n
    order = row_permutation(q)
    deg = np.diff(code.row_ptr)
    idx, valid, flat, ptr = [], [], [], [0]
    for a in range(q):
        rows = order[a * GROUP:(a + 1) * GROUP]
        d = int(deg[rows].max())
        m = np.full((GROUP, d), n, dtype=np.int64)
        for i, r in enumerate(rows):
            c = code.cols[code.row_ptr[r]:code.row_ptr[r + 1]]
            m[i, :c.size] = c
            flat.append(c)
            ptr.append(ptr[-1] + c.size)
        v = m < n
        idx.append(m)
        valid.append(None if v.all() else v)
    sched = LayerSchedule(q=q, n=n, idx=idx, valid=valid,
                          row_ptr=np.asarray(ptr, dtype=np.int64), cols=np.concatenate(flat).astype(np.int64))
    code._layer_schedule = sched
    return sched


# -- fixed point -------------------------------------------------------------------
@dataclass(frozen=True)
class FixedPoint:
    """Word lengths (two's complement, sign included) and scaling of the bit-true model.

    w_ch: channel LLRs; w_L: posterior L and variable-to-check Q; w_R:
    check-to-variable messages.  ``scale`` is LSBs per LLR unit.  Normalized
    min-sum multiplies by alpha_num / 2**alpha_shift (7/8: m - m/8, a shift
    and a subtraction); offset min-sum subtracts ``beta`` LSBs.  The defaults
    are the format the LDPC decoder study recommends: (6, 8, 6) bits, 4 LSBs
    per LLR unit, offset 2 LSBs (0.5).  w_L must exceed w_R by 2 bits, or the
    saturated posterior makes the decoder diverge.
    """
    w_ch: int = 6
    w_L: int = 8
    w_R: int = 6
    scale: float = 4.0
    alpha_num: int = 1
    alpha_shift: int = 0
    beta: int = 2

    @property
    def alpha(self) -> float:
        return self.alpha_num / 2 ** self.alpha_shift

    @staticmethod
    def lim(w: int) -> int:
        return 2 ** (w - 1) - 1

    def quantize(self, llr) -> np.ndarray:
        """Channel LLRs to w_ch-bit integers (round to nearest, symmetric saturation)."""
        m = self.lim(self.w_ch)
        return np.clip(np.floor(np.asarray(llr, dtype=np.float64) * self.scale + 0.5), -m, m)

    @classmethod
    def parse(cls, text: str, **kw) -> "FixedPoint":
        """'5,7,6' -> w_ch=5, w_L=7, w_R=6."""
        w = [int(v) for v in text.split(",")]
        return cls(*w, **kw)

    def label(self) -> str:
        corr = "a=%g" % self.alpha if self.alpha != 1 else "b=%d" % self.beta
        return "(%d,%d,%d) s=%g %s" % (self.w_ch, self.w_L, self.w_R, self.scale, corr)


# -- layer-parallel decoder ----------------------------------------------------------
def layer_decode(llr, code, max_iter: int = 50, algorithm: str = "nms", alpha: float = 0.875,
                 beta: float = 0.5, fmt: FixedPoint | None = None, early_stop: bool = True,
                 trace: list | None = None, impl: str = "auto"):
    """Layered decoding with the 360 checks of each layer processed in parallel.

    algorithm: "nms", "oms" or "spa" (float only).  With ``fmt`` the model is
    bit-true min-sum (normalized by fmt.alpha, offset by fmt.beta).
    ``trace`` (numpy implementation only) receives (iteration, layer,
    unsatisfied checks) after every layer.  impl: "auto", "numpy" or "numba".
    Returns (posterior LLRs in LLR units, iterations).
    """
    sched = layer_schedule(code)
    if fmt is not None:
        algorithm = "fixed"
    if algorithm not in ("nms", "oms", "spa", "fixed"):
        raise ValueError("algorithm must be nms, oms, spa or fixed")
    use_numba = (impl == "numba" or (impl == "auto" and trace is None)) and _kernels.HAVE_NUMBA \
        and algorithm != "spa"
    if fmt is not None:
        L0 = fmt.quantize(llr)
        a, b = fmt.alpha, float(fmt.beta)
        params = (fmt.alpha_num, fmt.alpha_shift, float(fmt.beta), fmt.lim(fmt.w_L), fmt.lim(fmt.w_R))
    else:
        L0 = np.asarray(llr, dtype=np.float64)
        a, b = (alpha, 0.0) if algorithm == "nms" else (1.0, beta)
        params = None
    if use_numba:
        L, it = _kernels.layer_parallel_decode(L0, sched.row_ptr, sched.cols, sched.q, max_iter, a, b,
                                               params, early_stop)
    else:
        L, it = _layer_numpy(L0, code, sched, max_iter, algorithm, a, b, params, early_stop, trace)
    if fmt is not None:
        L = L / fmt.scale
    return L, it


def _layer_numpy(L0, code, sched, max_iter, algorithm, a, b, params, early_stop, trace):
    n = sched.n
    L = np.empty(n + 1)
    L[:n] = L0
    L[n] = 1e30                                   # padding: never the minimum, never negative
    R = [np.zeros(i.shape) for i in sched.idx]
    fixed = params is not None
    if fixed:
        anum, ashift, beta_q, limL, limR = params
    rows = np.arange(GROUP)
    it = 0
    for it in range(1, max_iter + 1):
        for l in range(sched.q):
            idx, valid, Rl = sched.idx[l], sched.valid[l], R[l]
            Q = L[idx] - Rl
            if fixed:
                Q = np.clip(Q, -limL, limL)
            mag = np.abs(Q)
            if valid is not None:
                mag[~valid] = np.inf
            neg = Q < 0
            odd = (neg.sum(axis=1) & 1).astype(bool)
            if algorithm == "spa":
                with np.errstate(divide="ignore"):
                    phi = -np.log(np.tanh(np.clip(mag, 1e-12, 40.0) / 2))
                out = -np.log(np.tanh(np.clip(phi.sum(axis=1, keepdims=True) - phi, 1e-12, 40.0) / 2))
            else:
                i1 = np.argmin(mag, axis=1)
                min1 = mag[rows, i1]
                mag[rows, i1] = np.inf
                min2 = mag.min(axis=1)
                mins = np.stack([min1, min2], axis=1)
                if fixed:
                    mins = np.minimum(np.maximum(np.floor(mins * anum / 2 ** ashift) - beta_q, 0), limR)
                else:
                    mins = np.maximum(a * mins - b, 0.0)
                out = np.where(np.arange(idx.shape[1])[None, :] == i1[:, None], mins[:, 1:2], mins[:, 0:1])
            Rnew = np.where(neg ^ odd[:, None], -out, out)
            if valid is not None:
                Rnew[~valid] = 0.0
            delta = Rnew - Rl
            R[l] = Rnew
            L += np.bincount(idx.ravel(), weights=delta.ravel(), minlength=n + 1)
            L[n] = 1e30
            if fixed:
                np.clip(L[:n], -limL, limL, out=L[:n])
            if trace is not None:
                trace.append((it, l, int(code.syndrome((L[:n] < 0).astype(np.uint8)).sum())))
        if early_stop and not code.syndrome((L[:n] < 0).astype(np.uint8)).any():
            break
    return L[:n].copy(), it


# -- architecture cost model -----------------------------------------------------------
@dataclass
class Architecture:
    name: str
    n: int
    k: int
    q: int
    edges: int
    block_edges: int            # nonzero circulants (sum of layer degrees)
    weight2: int
    parallelism: int
    f_clk_mhz: float
    iterations: float
    pipeline_depth: int
    cycles_per_iter: dict = field(default_factory=dict)     # schedule -> cycles
    stalls: dict = field(default_factory=dict)              # schedule -> stall cycles per iteration
    memory_bits: dict = field(default_factory=dict)
    throughput_mbps: dict = field(default_factory=dict)     # schedule -> information Mb/s
    latency_us: dict = field(default_factory=dict)
    layer_order: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def _overlap_cycles(layers, order, depth, sub, reorder_cols):
    """Steady-state cycles of one iteration when layer i+1 reads while layer i writes.

    A layer with d block columns reads one per ``sub`` cycles and, after
    ``depth`` cycles of pipeline, writes them back in the same order.  A block
    column may be read only once the previous layer has finished writing it;
    otherwise the next layer stalls.  Iterations follow each other without a
    break, so the count is taken over the third of three iterations.
    Returns (cycles, stall cycles) per iteration.
    """
    seq = [sorted(set(c for c, _ in layers[i])) for i in order]
    if reorder_cols:
        # read late what the previous layer writes; write early what the next layer reads
        for i in range(len(seq)):
            prev, nxt = set(seq[i - 1]), set(seq[(i + 1) % len(seq)])
            seq[i].sort(key=lambda c: (c in prev, c not in nxt))
    t, done, stall, marks = 0, {}, 0, []
    for _ in range(3):
        marks.append((t, stall))
        for cols in seq:
            start = t
            for pos, c in enumerate(cols):
                if c in done:
                    start = max(start, done[c] - pos * sub)
            stall += start - t
            d = len(cols)
            done = {c: start + d * sub + depth + (pos + 1) * sub for pos, c in enumerate(cols)}
            t = start + d * sub
    return t - marks[2][0], stall - marks[2][1]


def _greedy_layer_order(layers):
    """Visit next the layer sharing the fewest block columns with the current one."""
    sets = [set(c for c, _ in l) for l in layers]
    left, order = set(range(1, len(layers))), [0]
    while left:
        cur = sets[order[-1]]
        nxt = min(left, key=lambda i: (len(cur & sets[i]), i))
        order.append(nxt)
        left.remove(nxt)
    return order


def architecture(code, parallelism: int = GROUP, f_clk_mhz: float = 200.0, iterations: float = 30,
                 fmt: FixedPoint = FixedPoint(), pipeline_depth: int = 6) -> Architecture:
    """Cycle, memory and throughput model of a layered decoder with ``parallelism`` CNPs.

    Each block column of a layer is read in 360 / P cycles by P check-node
    processors fed through a cyclic shifter (a weight-2 circulant is one
    memory read feeding two shifters).  Three schedules are counted per
    iteration: "serial" (each layer reads, waits for the pipeline, writes),
    "overlap" (the next layer reads while the previous writes, natural order,
    stalling on read-after-write hazards) and "reordered" (layer and column
    order chosen to reduce the stalls).
    """
    if GROUP % parallelism:
        raise ValueError("parallelism must divide 360")
    qc = qc_structure(code)
    sub = GROUP // parallelism
    layers = qc.layers
    serial = sum(2 * sub * len(set(c for c, _ in l)) + pipeline_depth for l in layers)
    nat, nat_stall = _overlap_cycles(layers, list(range(qc.q)), pipeline_depth, sub, False)
    order = _greedy_layer_order(layers)
    reo, reo_stall = _overlap_cycles(layers, order, pipeline_depth, sub, True)
    cyc = {"serial": serial, "overlap": nat, "reordered": reo}

    deg = np.diff(code.row_ptr)
    w_mag = fmt.w_R - 1
    rom_entry = math.ceil(math.log2(qc.n_blocks)) + math.ceil(math.log2(GROUP))
    block_edges = sum(len(l) for l in layers)
    mem = {
        "L": code.n * fmt.w_L,
        "R_compressed": int(sum(2 * w_mag + math.ceil(math.log2(d)) + d for d in deg)),
        "R_uncompressed": int(code.H.nnz) * fmt.w_R,
        "input_buffer": code.n * fmt.w_ch,
        "output_buffer": code.k,
        "rom": block_edges * rom_entry,
    }
    mem["total"] = mem["L"] + mem["R_compressed"] + mem["input_buffer"] + mem["output_buffer"] + mem["rom"]
    load = code.n // parallelism          # move the next frame from the input buffer into L
    thr, lat = {}, {}
    for s, c in cyc.items():
        lat[s] = (iterations * c + load) / f_clk_mhz
        thr[s] = code.k / lat[s]
    return Architecture(name=code.name, n=code.n, k=code.k, q=qc.q, edges=int(code.H.nnz),
                        block_edges=block_edges, weight2=len(qc.weight2), parallelism=parallelism,
                        f_clk_mhz=f_clk_mhz, iterations=iterations, pipeline_depth=pipeline_depth,
                        cycles_per_iter=cyc, stalls={"serial": 0, "overlap": nat_stall, "reordered": reo_stall},
                        memory_bits=mem, throughput_mbps=thr, latency_us=lat, layer_order=order)
