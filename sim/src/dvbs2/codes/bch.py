"""Binary BCH codes: design, fast systematic encoding and algebraic decoding.

Decoding follows the thesis (chapter 5): syndromes S_1 .. S_2t, the
Berlekamp-Massey algorithm for the error-locator polynomial Lambda(x), and a
Chien search for its roots.  Codes may be shortened (n < 2^m - 1), as all
DVB-S2 BCH codes are: the missing leading positions are taken as zeros.

Bit arrays are in transmission order: index 0 is the coefficient of x^(n-1).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .. import poly2
from ..gf import GF2m
from .cyclic import CyclicCode


@dataclass
class BMStep:
    """One iteration of Berlekamp-Massey, for tracing and teaching."""
    k: int                 # iteration (uses syndrome S_{k+1})
    syndrome: int          # S_{k+1}
    discrepancy: int
    locator: list[int]     # Lambda(x) after this step, lowest degree first
    L: int                 # current LFSR length


@dataclass
class BCHDecodeResult:
    codeword: np.ndarray
    success: bool                       # False: more than t errors detected
    n_errors: int                       # errors corrected (0 if failure)
    error_positions: np.ndarray         # array indices that were flipped
    syndromes: list[int]                # S_1 .. S_2t as field elements
    locator: list[int] = field(default_factory=list)


class BCHCode(CyclicCode):
    """Narrow-sense binary BCH code over GF(2^m) correcting t errors.

    ``n`` shortens the primitive code of length 2^m - 1.
    """

    def __init__(self, m: int, t: int, n: int | None = None, prim_poly: int | None = None,
                 name: str | None = None):
        self.gf = GF2m(m, prim_poly)
        self.t = t
        self.n_primitive = self.gf.order
        self.minimal_polys = []      # distinct minimal polynomials of alpha^1, alpha^3, ...
        g = 1
        for i in range(1, 2 * t, 2):
            mp = self.gf.minimal_polynomial(i)
            if mp not in self.minimal_polys:
                self.minimal_polys.append(mp)
                g = poly2.mul(g, mp)
        n = self.n_primitive if n is None else n
        super().__init__(n, g, name)
        if not 0 < self.k:
            raise ValueError("n too small for this generator")
        if n > self.n_primitive:
            raise ValueError("n exceeds 2^m - 1")
        if name is None:
            self.name = "BCH(%d,%d) t=%d" % (self.n, self.k, t)
        self._table = None

    # -- encoding ------------------------------------------------------------
    def _crc_table(self):
        if self._table is None:
            # T[i] = (i(x) x^r) mod g(x): remainder of one input byte.
            self._table = [poly2.mod(i << self.r, self.g) for i in range(256)]
        return self._table

    def parity(self, msg) -> np.ndarray:
        """Remainder of m(x) x^r / g(x), byte at a time (table-driven LFSR)."""
        msg = np.asarray(msg, dtype=np.uint8)
        if self.r < 8:
            return super().parity(msg)
        pad = (-msg.size) % 8
        data = np.packbits(np.concatenate([np.zeros(pad, np.uint8), msg])).tobytes()
        table, r, mask = self._crc_table(), self.r, (1 << self.r) - 1
        reg = 0
        for byte in data:
            reg = ((reg << 8) & mask) ^ table[(reg >> (r - 8)) ^ byte]
        return poly2.to_bits(reg, r)

    # -- decoding ------------------------------------------------------------
    def syndromes(self, word) -> list[int]:
        """S_j = r(alpha^j) for j = 1 .. 2t."""
        word = np.asarray(word, dtype=np.uint8)
        powers = (self.n - 1 - np.flatnonzero(word)).astype(np.int64)
        gf, S = self.gf, [0] * (2 * self.t)
        for j in range(1, 2 * self.t + 1, 2):
            S[j - 1] = int(np.bitwise_xor.reduce(gf.exp[(j * powers) % gf.order])) if powers.size else 0
        for j in range(2, 2 * self.t + 1, 2):   # binary code: S_2i = S_i^2
            S[j - 1] = int(gf.mul(S[j // 2 - 1], S[j // 2 - 1]))
        return S

    def berlekamp_massey(self, S, trace: list | None = None) -> list[int]:
        """Error-locator polynomial Lambda(x) (lowest degree first) from S_1..S_2t."""
        gf = self.gf
        C, B = [1], [1]
        L, shift, b = 0, 1, 1
        for k in range(len(S)):
            d = S[k]
            for i in range(1, L + 1):
                if i < len(C) and C[i] and S[k - i]:
                    d ^= int(gf.mul(C[i], S[k - i]))
            if d == 0:
                shift += 1
            else:
                coef = int(gf.div(d, b))
                T = list(C)
                upd = [0] * shift + [int(gf.mul(coef, x)) for x in B]
                size = max(len(C), len(upd))
                C = [(C[i] if i < len(C) else 0) ^ (upd[i] if i < len(upd) else 0) for i in range(size)]
                if 2 * L <= k:
                    L, B, b, shift = k + 1 - L, T, d, 1
                else:
                    shift += 1
            if trace is not None:
                trace.append(BMStep(k, S[k], d, _trim(C, L), L))
        return _trim(C, L)

    def chien_search(self, locator) -> np.ndarray:
        """Powers p (0 <= p < n) with Lambda(alpha^-p) = 0, i.e. the error locations."""
        gf = self.gf
        p = np.arange(self.n, dtype=np.int64)
        acc = np.full(self.n, locator[0], dtype=np.int64)
        for j, c in enumerate(locator[1:], start=1):
            if c:
                acc ^= gf.exp[(gf.log[c] - p * j) % gf.order]
        return p[acc == 0]

    def decode(self, word, trace: list | None = None) -> BCHDecodeResult:
        word = np.array(word, dtype=np.uint8)
        S = self.syndromes(word)
        if not any(S):
            return BCHDecodeResult(word, True, 0, np.array([], dtype=np.int64), S, [1])
        lam = self.berlekamp_massey(S, trace)
        L = len(lam) - 1
        roots = self.chien_search(lam) if L <= self.t else np.array([], dtype=np.int64)
        if L > self.t or roots.size != L:
            return BCHDecodeResult(word, False, 0, np.array([], dtype=np.int64), S, lam)
        idx = self.n - 1 - roots
        word[idx] ^= 1
        return BCHDecodeResult(word, True, int(L), np.sort(idx), S, lam)

    def extract(self, word) -> np.ndarray:
        return np.asarray(word, dtype=np.uint8)[:self.k]


def _trim(C, L):
    """Coefficients 0 .. L of C (zero-padded)."""
    return list(C[:L + 1]) + [0] * max(0, L + 1 - len(C))


# DVB-S2 BCH codes (EN 302 307-1, 5.3.1): Nbch and t for each LDPC code rate.
_NORMAL = {"1/4": (16200, 12), "1/3": (21600, 12), "2/5": (25920, 12), "1/2": (32400, 12),
           "3/5": (38880, 12), "2/3": (43200, 10), "3/4": (48600, 12), "4/5": (51840, 12),
           "5/6": (54000, 10), "8/9": (57600, 8), "9/10": (58320, 8)}
_SHORT = {"1/4": 3240, "1/3": 5400, "2/5": 6480, "1/2": 7200, "3/5": 9720, "2/3": 10800,
          "3/4": 11880, "4/5": 12600, "5/6": 13320, "8/9": 14400}
_CACHE: dict = {}


def dvbs2_bch(rate: str, frame: str = "normal") -> BCHCode:
    """The outer BCH code of a DVB-S2 FECFRAME (cached)."""
    key = (frame, rate)
    if key not in _CACHE:
        if frame == "normal":
            n, t = _NORMAL[rate]
            code = BCHCode(16, t, n, 0x1002D)     # x^16 + x^5 + x^3 + x^2 + 1
        elif frame == "short":
            code = BCHCode(14, 12, _SHORT[rate], 0x402B)  # x^14 + x^5 + x^3 + x + 1
        else:
            raise ValueError("frame must be 'normal' or 'short'")
        code.name = "DVB-S2 BCH(%d,%d) t=%d, %s %s" % (code.n, code.k, code.t, frame, rate)
        _CACHE[key] = code
    return _CACHE[key]
