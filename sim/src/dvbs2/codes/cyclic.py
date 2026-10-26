"""Systematic binary cyclic codes and the LFSR circuits that encode them.

A message m(x) of k bits becomes c(x) = m(x) x^r + rem(m(x) x^r, g(x)) with
r = deg g.  Bit arrays are in transmission order (highest power first), the
same convention as the DVB-S2 standard and :mod:`dvbs2.poly2`.

Two LFSR encoders are modelled clock by clock (thesis, chapter 3):

* ``lfsr_divide_trace``: the plain division circuit.  The input enters at
  stage 0, so all n bits (message followed by r zeros) must be shifted in:
  n clock cycles (``BCH_s_enc`` in ``main.c``).
* ``lfsr_encode_trace``: the premultiplied encoder.  The input is added to the
  feedback, which divides m(x) x^r directly: k clock cycles, after which the
  register holds the parity bits (``BCHenc::Run`` in ``serial.c``).
"""
from __future__ import annotations

import numpy as np

from .. import poly2


class CyclicCode:
    def __init__(self, n: int, g: int, name: str | None = None):
        self.n = n
        self.g = g
        self.r = poly2.degree(g)
        self.k = n - self.r
        self.name = name or "cyclic (%d,%d)" % (n, self.k)

    def is_cyclic_generator(self) -> bool:
        """g(x) divides x^n + 1 (only meaningful for unshortened codes)."""
        return poly2.mod((1 << self.n) | 1, self.g) == 0

    def parity(self, msg) -> np.ndarray:
        rem = poly2.mod(poly2.from_bits(msg) << self.r, self.g)
        return poly2.to_bits(rem, self.r)

    def encode(self, msg) -> np.ndarray:
        msg = np.asarray(msg, dtype=np.uint8)
        if msg.size != self.k:
            raise ValueError("expected %d message bits" % self.k)
        return np.concatenate([msg, self.parity(msg)])

    def syndrome_poly(self, word) -> int:
        return poly2.mod(poly2.from_bits(word), self.g)

    def is_codeword(self, word) -> bool:
        return self.syndrome_poly(word) == 0


def _g_taps(g: int, r: int) -> np.ndarray:
    return np.array([(g >> j) & 1 for j in range(r)], dtype=np.uint8)


def lfsr_divide_trace(bits, g: int) -> np.ndarray:
    """Division LFSR: one row per clock, row t = register (stage 0 .. r-1) after t inputs.

    Shifting in a(x) (highest power first) leaves a(x) mod g(x) in the register,
    stage j holding the coefficient of x^j.
    """
    r = poly2.degree(g)
    taps = _g_taps(g, r)
    reg = np.zeros(r, dtype=np.uint8)
    states = [reg.copy()]
    for u in np.asarray(bits, dtype=np.uint8):
        fb = reg[r - 1]
        reg[1:] = reg[:-1] ^ (fb & taps[1:])
        reg[0] = u ^ (fb & taps[0])
        states.append(reg.copy())
    return np.array(states)


def lfsr_encode_trace(msg, g: int) -> np.ndarray:
    """Premultiplied (k-clock) encoder: one row per clock, register after t inputs.

    After k clocks stage j holds the coefficient of x^j of rem(m(x) x^r, g(x)).
    """
    r = poly2.degree(g)
    taps = _g_taps(g, r)
    reg = np.zeros(r, dtype=np.uint8)
    states = [reg.copy()]
    for u in np.asarray(msg, dtype=np.uint8):
        fb = reg[r - 1] ^ u
        reg[1:] = reg[:-1] ^ (fb & taps[1:])
        reg[0] = fb & taps[0]
        states.append(reg.copy())
    return np.array(states)


def register_to_parity(reg) -> np.ndarray:
    """Register (stage 0 first) -> parity bits in transmission order."""
    return np.asarray(reg, dtype=np.uint8)[::-1].copy()
