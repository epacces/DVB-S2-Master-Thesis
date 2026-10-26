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
        numba is available, otherwise flooding min-sum.
        Returns (hard decisions, posterior LLRs, iterations).
        """
        if algorithm not in ("nms", "oms", "spa"):
            raise ValueError("algorithm must be nms, oms or spa")
        a, b = (alpha, 0.0) if algorithm == "nms" else (1.0, beta) if algorithm == "oms" else (1.0, 0.0)
        if _kernels.HAVE_NUMBA:
            L, it = _kernels.layered_decode(llr, self.row_ptr, self.cols, max_iter, a, b, algorithm == "spa")
        else:  # no numba (e.g. Pyodide): flooding min-sum, normalized in place of SPA
            if algorithm == "spa":
                a = alpha
            L, it = _kernels.flooding_minsum(llr, self.row_ptr, self.cols, max_iter, a, b)
        return (L < 0).astype(np.uint8), L, it

    def degree_profile(self) -> dict[int, int]:
        """Number of variable nodes of each degree."""
        deg = np.diff(self.H.tocsc().indptr)
        vals, counts = np.unique(deg, return_counts=True)
        return dict(zip(vals.tolist(), counts.tolist()))


_CACHE: dict = {}


def dvbs2_ldpc(rate: str, frame: str = "normal") -> LDPCCode:
    key = (frame, rate)
    if key not in _CACHE:
        _CACHE[key] = LDPCCode(load_table(rate, frame), FRAME_N[frame],
                               "DVB-S2 LDPC %s %s" % (frame, rate))
    return _CACHE[key]
