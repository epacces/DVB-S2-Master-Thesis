"""Polynomials over GF(2) stored as Python ints (bit i = coefficient of x^i).

Bit arrays follow the DVB-S2 transmission order: ``bits[0]`` is the first bit
sent and the coefficient of the *highest* power, so ``from_bits`` reads the
array as a binary number.
"""
from __future__ import annotations

import numpy as np


def degree(p: int) -> int:
    """Degree of p; -1 for the zero polynomial."""
    return p.bit_length() - 1


def mul(a: int, b: int) -> int:
    """Carry-less product a(x) b(x)."""
    out = 0
    while b:
        if b & 1:
            out ^= a
        a <<= 1
        b >>= 1
    return out


def divmod2(a: int, b: int) -> tuple[int, int]:
    """Quotient and remainder of a(x) / b(x)."""
    if b == 0:
        raise ZeroDivisionError("division by the zero polynomial")
    db = degree(b)
    q = 0
    while a and degree(a) >= db:
        shift = degree(a) - db
        q |= 1 << shift
        a ^= b << shift
    return q, a


def mod(a: int, b: int) -> int:
    return divmod2(a, b)[1]


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, mod(a, b)
    return a


def from_bits(bits) -> int:
    """Bit array (highest power first) -> int."""
    bits = np.asarray(bits, dtype=np.uint8)
    if bits.size == 0:
        return 0
    return int.from_bytes(np.packbits(bits, bitorder="big").tobytes(), "big") >> ((-bits.size) % 8)


def to_bits(p: int, n: int) -> np.ndarray:
    """int -> bit array of length n (highest power first)."""
    nbytes = (n + 7) // 8
    raw = np.frombuffer((p << ((-n) % 8)).to_bytes(nbytes, "big"), dtype=np.uint8)
    return np.unpackbits(raw, bitorder="big")[:n].copy()


def coeffs(p: int) -> list[int]:
    """Coefficient list, lowest degree first."""
    return [(p >> i) & 1 for i in range(max(degree(p) + 1, 1))]


def to_str(p: int, var: str = "x") -> str:
    if p == 0:
        return "0"
    terms = []
    for i in range(degree(p), -1, -1):
        if p >> i & 1:
            terms.append("1" if i == 0 else var if i == 1 else "%s^%d" % (var, i))
    return " + ".join(terms)
