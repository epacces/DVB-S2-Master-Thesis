"""Hamming codes and the extended (SECDED) variant.

Bits are numbered 1 .. n as in Hamming's original construction: column j of H
is the binary representation of j, so the syndrome of a single error *is* its
position.  Parity bits sit at the power-of-two positions, data bits elsewhere.
The extended code adds an overall parity bit at position 0.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class DecodeResult:
    codeword: np.ndarray   # corrected codeword
    data: np.ndarray       # decoded information bits
    syndrome: int          # Hamming syndrome (error position, 0 = none)
    status: str            # "ok", "corrected", "detected" (double error, extended code only)
    error_position: int | None


class HammingCode:
    def __init__(self, r: int = 3, extended: bool = False):
        if r < 2:
            raise ValueError("r must be >= 2")
        self.r = r
        self.extended = extended
        self.n0 = (1 << r) - 1                 # length of the plain Hamming code
        self.k = self.n0 - r
        self.n = self.n0 + int(extended)
        self.parity_positions = [1 << i for i in range(r)]
        self.data_positions = [j for j in range(1, self.n0 + 1) if j & (j - 1)]

    @property
    def name(self):
        return "%s(%d,%d)" % ("Extended Hamming" if self.extended else "Hamming", self.n, self.k)

    @property
    def dmin(self):
        return 4 if self.extended else 3

    # Index helpers: array index <-> Hamming position (array index 0 is the
    # overall parity bit of the extended code).
    def _pos(self, j):
        return j if self.extended else j - 1

    def H(self) -> np.ndarray:
        """Parity-check matrix (r x n, or r+1 x n for the extended code)."""
        cols = np.arange(1, self.n0 + 1)
        H = ((cols[None, :] >> np.arange(self.r)[:, None]) & 1).astype(np.uint8)
        if self.extended:
            H = np.hstack([np.zeros((self.r, 1), np.uint8), H])
            H = np.vstack([H, np.ones((1, self.n), np.uint8)])
        return H

    def G(self) -> np.ndarray:
        """Generator matrix (k x n): row i is the codeword of the i-th unit message."""
        return np.array([self.encode(e) for e in np.eye(self.k, dtype=np.uint8)])

    def encode(self, data) -> np.ndarray:
        data = np.asarray(data, dtype=np.uint8)
        if data.size != self.k:
            raise ValueError("expected %d data bits" % self.k)
        cw = np.zeros(self.n, dtype=np.uint8)
        for bit, j in zip(data, self.data_positions):
            cw[self._pos(j)] = bit
        for p in self.parity_positions:
            cw[self._pos(p)] = sum(int(cw[self._pos(j)]) for j in range(1, self.n0 + 1) if j & p and j != p) & 1
        if self.extended:
            cw[0] = cw[1:].sum() & 1
        return cw

    def syndrome(self, word) -> int:
        word = np.asarray(word, dtype=np.uint8)
        s = 0
        for j in range(1, self.n0 + 1):
            if word[self._pos(j)]:
                s ^= j
        return s

    def parity_checks(self, word) -> list[int]:
        """Value of each parity check (1 = violated), lowest check first."""
        s = self.syndrome(word)
        return [(s >> i) & 1 for i in range(self.r)]

    def extract(self, word) -> np.ndarray:
        word = np.asarray(word, dtype=np.uint8)
        return np.array([word[self._pos(j)] for j in self.data_positions], dtype=np.uint8)

    def decode(self, word) -> DecodeResult:
        cw = np.array(word, dtype=np.uint8)
        s = self.syndrome(cw)
        overall = int(cw.sum() & 1) if self.extended else None
        if s == 0 and not overall:
            return DecodeResult(cw, self.extract(cw), 0, "ok", None)
        if self.extended and s and not overall:
            # Even overall parity but a non-zero syndrome: two errors.
            return DecodeResult(cw, self.extract(cw), s, "detected", None)
        pos = self._pos(s) if s else 0  # s == 0 with odd parity: the overall bit itself
        cw[pos] ^= 1
        return DecodeResult(cw, self.extract(cw), s, "corrected", pos)
