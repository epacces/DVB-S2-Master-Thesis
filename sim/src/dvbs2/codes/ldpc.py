"""DVB-S2 LDPC codes (ETSI EN 302 307-1, 5.3.2 and Annexes B/C).

The codes are irregular repeat-accumulate (IRA): H = [H_info | H_parity] with
H_parity the dual-diagonal "staircase".  Information bit i, in group
row = i // 360 and position l = i % 360, is added to parity accumulators

    (x + l * q) mod (N - K),   x in table[row],   q = (N - K) / 360

after which p_j ^= p_(j-1) for j = 1 .. N-K-1.
"""
from __future__ import annotations

import pathlib
from importlib import resources

import numpy as np
import scipy.sparse as sp

from . import _kernels

FRAME_N = {"normal": 64800, "short": 16200}
RATES = {"normal": ["1/4", "1/3", "2/5", "1/2", "3/5", "2/3", "3/4", "4/5", "5/6", "8/9", "9/10"],
         "short": ["1/4", "1/3", "2/5", "1/2", "3/5", "2/3", "3/4", "4/5", "5/6", "8/9"]}


def load_table(rate: str, frame: str = "normal") -> list[list[int]]:
    name = "%s_%s.txt" % (frame, rate.replace("/", "_"))
    text = resources.files("dvbs2").joinpath("data", "ldpc", name).read_text()
    return [[int(v) for v in line.split()] for line in text.splitlines() if line.strip()]


class LDPCCode:
    """A DVB-S2 LDPC code, or any IRA code given by an address table."""

    def __init__(self, table: list[list[int]], n: int, name: str = "LDPC", group: int = 360):
        self.table = table
        self.n = n
        self.k = len(table) * group
        self.m = n - self.k
        self.group = group
        self.q = self.m // group
        self.name = name

        rows, cols = [], []
        for row, addrs in enumerate(table):
            x = np.asarray(addrs, dtype=np.int64)
            l = np.arange(group, dtype=np.int64)
            rows.append(((x[None, :] + l[:, None] * self.q) % self.m).ravel())
            cols.append(np.repeat(row * group + l, x.size))
        self._info_rows = np.concatenate(rows)
        self._info_cols = np.concatenate(cols)
        self.H_info = sp.csr_matrix((np.ones(self._info_rows.size, np.uint8),
                                     (self._info_rows, self._info_cols)), shape=(self.m, self.k))
        stair_r = np.concatenate([np.arange(self.m), np.arange(1, self.m)])
        stair_c = np.concatenate([np.arange(self.m), np.arange(self.m - 1)]) + self.k
        r = np.concatenate([self._info_rows, stair_r])
        c = np.concatenate([self._info_cols, stair_c])
        H = sp.csr_matrix((np.ones(r.size, np.uint8), (r, c)), shape=(self.m, self.n))
        H.sort_indices()
        if H.max() > 1:
            raise ValueError("duplicate entries in the address table")
        self.H = H
        self.row_ptr = H.indptr.astype(np.int64)
        self.cols = H.indices.astype(np.int64)

    @property
    def rate(self) -> float:
        return self.k / self.n

    # -- encoding -------------------------------------------------------------
    def encode(self, msg) -> np.ndarray:
        msg = np.asarray(msg, dtype=np.uint8)
        if msg.shape[-1] != self.k:
            raise ValueError("expected %d information bits" % self.k)
        acc = (self.H_info @ msg.astype(np.int64)) & 1
        parity = np.bitwise_xor.accumulate(acc.astype(np.uint8))
        return np.concatenate([msg, parity])

    def syndrome(self, word) -> np.ndarray:
        return (self.H @ np.asarray(word, dtype=np.int64)) & 1

    def is_codeword(self, word) -> bool:
        return not self.syndrome(word).any()

    # -- decoding -------------------------------------------------------------
    def decode(self, llr, max_iter: int = 50, algorithm: str = "spa", alpha: float = 0.8,
               beta: float = 0.5):
        """Iterative decoding of channel LLRs (log P(0)/P(1)).

        algorithm: "nms" normalized min-sum (scale ``alpha``), "oms" offset
        min-sum (offset ``beta``), "spa" sum-product.  Layered schedule when
        numba is available, otherwise flooding min-sum.  The parameter can
        follow a colon ("nms:0.875", "oms:0.5"), and a prefix picks another
        decoder (see :func:`parse_decoder`): "flood-" flooding schedule, "hw-"
        360-parallel layers as in hardware, "fixed:6,8,6[:scale[:7/8|:b1]]"
        the bit-true fixed-point model.
        Returns (hard decisions, posterior LLRs, iterations).
        """
        spec = parse_decoder(algorithm, alpha, beta)
        if spec["schedule"] != "layered":
            return self._decode_spec(llr, max_iter, spec)
        algorithm, alpha, beta = spec["algorithm"], spec["alpha"], spec["beta"]
        a, b = (alpha, 0.0) if algorithm == "nms" else (1.0, beta) if algorithm == "oms" else (1.0, 0.0)
        if _kernels.HAVE_NUMBA:
            L, it = _kernels.layered_decode(llr, self.row_ptr, self.cols, max_iter, a, b, algorithm == "spa")
        else:  # no numba (e.g. Pyodide): flooding min-sum, normalized in place of SPA
            if algorithm == "spa":
                a = alpha
            L, it = _kernels.flooding_minsum(llr, self.row_ptr, self.cols, max_iter, a, b)
        return (L < 0).astype(np.uint8), L, it

    def _decode_spec(self, llr, max_iter, spec):
        from . import ldpc_hw
        if spec["schedule"] == "flooding":
            if spec["algorithm"] == "spa":
                raise ValueError("flooding is implemented for min-sum only")
            a, b = (spec["alpha"], 0.0) if spec["algorithm"] == "nms" else (1.0, spec["beta"])
            L, it = _kernels.flooding_minsum(llr, self.row_ptr, self.cols, max_iter, a, b)
        else:
            L, it = ldpc_hw.layer_decode(llr, self, max_iter, spec["algorithm"], spec["alpha"], spec["beta"],
                                         fmt=spec["fmt"])
        return (L < 0).astype(np.uint8), L, it

    def degree_profile(self) -> dict[int, int]:
        """Number of variable nodes of each degree."""
        deg = np.diff(self.H.tocsc().indptr)
        vals, counts = np.unique(deg, return_counts=True)
        return dict(zip(vals.tolist(), counts.tolist()))


def parse_decoder(spec: str, alpha: float = 0.8, beta: float = 0.5) -> dict:
    """Decoder description string -> schedule, algorithm, alpha, beta, fixed-point format.

    "spa" | "nms[:alpha]" | "oms[:beta]"   layered, rows in natural order
    "flood-nms[:alpha]" | "flood-oms[:beta]"   flooding schedule
    "hw-nms[:alpha]" | "hw-oms[:beta]" | "hw-spa"   layers of 360 checks in parallel
    "fixed:w_ch,w_L,w_R[:scale[:A/2^k | :bB]]"   bit-true model of the hw decoder,
        e.g. "fixed:6,8,6:2:7/8" (normalized by 7/8) or "fixed:6,8,6:2:b1" (offset 1 LSB)
    """
    head, _, arg = spec.partition(":")
    if head == "fixed":
        from .ldpc_hw import FixedPoint
        parts = arg.split(":") if arg else []
        if not parts:
            raise ValueError("fixed needs word lengths, e.g. fixed:6,8,6")
        kw = {}
        if len(parts) > 1:
            kw["scale"] = float(parts[1])
        if len(parts) > 2:
            corr = parts[2]
            if corr.startswith("b"):
                kw.update(alpha_num=1, alpha_shift=0, beta=int(corr[1:]))
            else:
                num, den = (int(v) for v in corr.split("/"))
                shift = den.bit_length() - 1
                if 2 ** shift != den:
                    raise ValueError("the alpha denominator must be a power of two")
                kw.update(alpha_num=num, alpha_shift=shift)
        return {"schedule": "hw", "algorithm": "fixed", "alpha": alpha, "beta": beta,
                "fmt": FixedPoint.parse(parts[0], **kw)}
    schedule = "layered"
    for prefix, name in (("flood-", "flooding"), ("hw-", "hw")):
        if head.startswith(prefix):
            schedule, head = name, head[len(prefix):]
    if head not in ("nms", "oms", "spa"):
        raise ValueError("unknown decoder %r" % spec)
    if arg:
        if head == "nms":
            alpha = float(arg)
        elif head == "oms":
            beta = float(arg)
    return {"schedule": schedule, "algorithm": head, "alpha": alpha, "beta": beta, "fmt": None}


_CACHE: dict = {}


def dvbs2_ldpc(rate: str, frame: str = "normal") -> LDPCCode:
    key = (frame, rate)
    if key not in _CACHE:
        _CACHE[key] = LDPCCode(load_table(rate, frame), FRAME_N[frame],
                               "DVB-S2 LDPC %s %s" % (frame, rate))
    return _CACHE[key]
