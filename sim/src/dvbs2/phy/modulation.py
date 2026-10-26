"""Bit interleaving, constellation mapping and soft demapping (EN 302 307-1, 5.3.3 and 5.4).

Constellations are normalised to unit average symbol energy.  Point ``i`` of
a constellation carries the bits of ``i`` written MSB first, the first of
which is the first bit read out of the interleaver.
"""
from __future__ import annotations

import numpy as np

from .modcod import ModCod

# Point angles in units of pi, listed by label (0 .. M-1), with the ring of each.
_8PSK = [1 / 4, 0, 1, 5 / 4, 1 / 2, 7 / 4, 3 / 4, 3 / 2]
_16APSK = ([(2, a) for a in (1 / 4, -1 / 4, 3 / 4, -3 / 4, 1 / 12, -1 / 12, 11 / 12, -11 / 12,
                             5 / 12, -5 / 12, 7 / 12, -7 / 12)]
           + [(1, a) for a in (1 / 4, -1 / 4, 3 / 4, -3 / 4)])
_32APSK = [(2, 1 / 4), (2, 5 / 12), (2, -1 / 4), (2, -5 / 12), (2, 3 / 4), (2, 7 / 12), (2, -3 / 4), (2, -7 / 12),
           (3, 1 / 8), (3, 3 / 8), (3, -1 / 4), (3, -1 / 2), (3, 3 / 4), (3, 1 / 2), (3, -7 / 8), (3, -5 / 8),
           (2, 1 / 12), (1, 1 / 4), (2, -1 / 12), (1, -1 / 4), (2, 11 / 12), (1, 3 / 4), (2, -11 / 12), (1, -3 / 4),
           (3, 0), (3, 1 / 4), (3, -1 / 8), (3, -3 / 8), (3, 7 / 8), (3, 5 / 8), (3, 1), (3, -3 / 4)]


def constellation(modulation: str, gamma=None) -> np.ndarray:
    """Complex points indexed by bit label, unit average energy."""
    if modulation == "QPSK":
        pts = np.array([(1 - 2 * (i >> 1)) + 1j * (1 - 2 * (i & 1)) for i in range(4)]) / np.sqrt(2)
    elif modulation == "8PSK":
        pts = np.exp(1j * np.pi * np.array(_8PSK))
    elif modulation in ("16APSK", "32APSK"):
        table = _16APSK if modulation == "16APSK" else _32APSK
        if gamma is None:
            gamma = 2.85 if modulation == "16APSK" else (2.84, 5.27)
        radii = {1: 1.0, 2: gamma, 3: None} if modulation == "16APSK" else {1: 1.0, 2: gamma[0], 3: gamma[1]}
        pts = np.array([radii[ring] * np.exp(1j * np.pi * a) for ring, a in table])
    else:
        raise ValueError("unknown modulation %s" % modulation)
    return pts / np.sqrt(np.mean(np.abs(pts) ** 2))


def label_bits(m: int) -> np.ndarray:
    """bits[i, j] = j-th (MSB first) bit of label i, for 2^m labels."""
    i = np.arange(1 << m)
    return ((i[:, None] >> np.arange(m - 1, -1, -1)[None, :]) & 1).astype(np.uint8)


# -- bit interleaver ------------------------------------------------------------

def _columns(mc: ModCod) -> int:
    return 0 if mc.modulation == "QPSK" else mc.bits_per_symbol


def interleave(bits, mc: ModCod) -> np.ndarray:
    """Column-wise write, row-wise read; 8PSK 3/5 reads the columns in reverse order."""
    cols = _columns(mc)
    if not cols:
        return np.asarray(bits)
    rows = np.asarray(bits).reshape(cols, -1)
    if mc.modulation == "8PSK" and mc.rate == "3/5":
        rows = rows[::-1]
    return rows.T.reshape(-1)


def deinterleave(values, mc: ModCod) -> np.ndarray:
    """Inverse of :func:`interleave` (works on bits or LLRs)."""
    cols = _columns(mc)
    if not cols:
        return np.asarray(values)
    mat = np.asarray(values).reshape(-1, cols).T
    if mc.modulation == "8PSK" and mc.rate == "3/5":
        mat = mat[::-1]
    return mat.reshape(-1)


# -- mapping / demapping --------------------------------------------------------

class Mapper:
    def __init__(self, mc: ModCod):
        self.mc = mc
        self.m = mc.bits_per_symbol
        self.points = constellation(mc.modulation, mc.gamma)
        self.labels = label_bits(self.m)
        self._weights = (1 << np.arange(self.m - 1, -1, -1)).astype(np.int64)

    def map(self, bits) -> np.ndarray:
        idx = np.asarray(bits, dtype=np.int64).reshape(-1, self.m) @ self._weights
        return self.points[idx]

    def demap(self, symbols, n0: float, method: str = "exact") -> np.ndarray:
        """Bit LLRs log(P(b=0|y)/P(b=1|y)), ``method`` "exact" (log-MAP) or "maxlog"."""
        y = np.asarray(symbols)
        metric = -np.abs(y[:, None] - self.points[None, :]) ** 2 / n0     # (N, M)
        out = np.empty((y.size, self.m))
        for j in range(self.m):
            zero = self.labels[:, j] == 0
            if method == "maxlog":
                out[:, j] = metric[:, zero].max(axis=1) - metric[:, ~zero].max(axis=1)
            else:
                out[:, j] = _logsumexp(metric[:, zero]) - _logsumexp(metric[:, ~zero])
        return out.reshape(-1)

    def hard(self, symbols) -> np.ndarray:
        y = np.asarray(symbols)
        idx = np.argmin(np.abs(y[:, None] - self.points[None, :]), axis=1)
        return self.labels[idx].reshape(-1)


def _logsumexp(a):
    mx = a.max(axis=1)
    return mx + np.log(np.exp(a - mx[:, None]).sum(axis=1))


def pi2_bpsk(bits) -> np.ndarray:
    """pi/2-BPSK of the PLHEADER: even symbols on the (1+j) axis, odd on (-1+j)."""
    bits = np.asarray(bits, dtype=np.float64)
    rot = np.where(np.arange(bits.size) % 2 == 0, 1 + 1j, -1 + 1j) / np.sqrt(2)
    return (1 - 2 * bits) * rot
