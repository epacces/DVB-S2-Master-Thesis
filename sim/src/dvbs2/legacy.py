"""Line-by-line Python transliterations of the 2008 C simulation package.

The C sources in the repository root (``main.c``, ``gfield.c``, ``berlmass.c``,
...) are kept unchanged because the thesis prints them.  They target Borland
C++ and cannot be built on a modern compiler, so these ports exist to show
that :mod:`dvbs2.codes` reproduces them bit for bit (see ``sim/tests``).

The C code indexes arrays by polynomial power: ``message[i]`` is the
coefficient of x^i, so ``message[n-1]`` is the first bit transmitted.
"""
from __future__ import annotations

import pathlib
import re

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3]
MAXN = (1 << 16) - 1
P = 8
MAXR = 192


def generator_arrays(main_c: pathlib.Path | str | None = None) -> dict[str, list[int]]:
    """The ``gen12``, ``gen10`` and ``gen8`` coefficient arrays (x^0 first) from main.c."""
    text = pathlib.Path(main_c or ROOT / "main.c").read_bytes().decode("cp1252")
    out = {}
    for name in ("gen12", "gen10", "gen8"):
        body = re.search(r"%s\[\]\s*=\s*\{(.*?)\};" % name, text, re.S).group(1)
        out[name] = [int(v) for v in re.findall(r"[01]", body)]
    return out


def gfField(m: int, poly: int):
    """gfield.c: powOfAlpha[i] = alpha^i, indexAlpha[x] = log_alpha(x) (-1 for 0).

    ``poly`` is given without the x^m term (the C code passes 32+8+4+1).  The
    C version allocates one entry too few for powOfAlpha; here it is sized 2^m - 1.
    """
    mask = (1 << m) - 1
    pow_ = [0] * ((1 << m) - 1)
    index = [0] * (1 << m)
    pow_[0] = 1
    index[0] = -1
    index[1] = 0
    reg = 1
    for i in range((1 << m) - 2):
        tmp = reg & (1 << (m - 1))
        reg <<= 1
        if tmp:
            reg ^= poly
            reg &= mask
        pow_[i + 1] = reg
        index[reg] = i + 1
    return pow_, index


def BCH_s_enc(message, n: int, k: int, g) -> list[int]:
    """main.c BCH_s_enc: serial n-clock division; returns codeword[] (power-indexed)."""
    r = n - k
    reg = [0] * r
    for i in range(n - 1, -1, -1):
        mem = reg[r - 1]
        for j in range(r - 2, -1, -1):
            reg[j + 1] = reg[j] ^ (mem & g[j + 1])
        reg[0] = message[i] ^ (mem & g[0])
    codeword = [0] * n
    for i in range(n - 1, r - 1, -1):
        codeword[i] = message[i]
    for i in range(r - 1, -1, -1):
        codeword[i] = reg[i]
    return codeword


def BCHnclk_par(message, n: int, k: int, Ap_n) -> list[int]:
    """main.c BCHnclk_par: 8-parallel division using only the last P columns of A^P."""
    r = n - k
    reg = [0] * r
    z = 0
    for _ in range(n // P):
        reg_old = list(reg)
        inp = [0] * P
        for count in range(P - 1, -1, -1):
            z += 1
            inp[count] = message[n - z]
        for m in range(r):
            comb = 0
            for f in range(P):
                comb ^= Ap_n[m][r - f - 1] & reg_old[r - f - 1]
            reg[m] = inp[m] ^ comb if m < P else comb ^ reg_old[m - P]
    return reg + [message[i] for i in range(r, n)]


def BCHkclk_par(message, n: int, k: int, Ap_k, C) -> list[int]:
    """main.c BCHkclk_par: 8-parallel premultiplied encoder on the shared 192-bit register."""
    r = n - k
    offset = MAXR - r
    reg = [0] * MAXR
    z = 0
    for _ in range(k // P):
        reg_old = list(reg)
        inp = [0] * P
        for count in range(P - 1, -1, -1):
            z += 1
            inp[count] = message[n - z]
        for m in range(MAXR):
            comb_c = 0
            for f in range(P):
                comb_c ^= C[m][f] & inp[f]
            comb_k = 0
            for f in range(P):
                comb_k ^= Ap_k[m][MAXR - f - 1] & reg_old[MAXR - f - 1]
            reg[m] = comb_c ^ comb_k if m < P else comb_c ^ comb_k ^ reg_old[m - P]
    return [reg[i + offset] for i in range(r)] + [message[i] for i in range(r, n)]


def error_detection(codeword, pow_, index, t: int):
    """errdet.c: syndromes S_1..S_2t in exponential notation (-1 = zero)."""
    S = []
    for i in range(2 * t):
        s = 0
        for j, bit in enumerate(codeword):
            if bit:
                s ^= pow_[((i + 1) * j) % MAXN]
        S.append(index[s])
    return any(v != -1 for v in S), S


def BerlMass(S, t2: int, pow_, index) -> list[int]:
    """berlmass.c: Berlekamp-Massey + Chien search; returns the error locations found."""
    p = [0] * t2
    c = [0] * t2
    c[0] = p[0] = 1
    L, l, dm = 0, 1, 1
    for k in range(t2):
        d = 0 if S[k] == -1 else pow_[S[k]]
        for i in range(1, L + 1):
            if S[k - i] >= 0 and c[i] > 0:
                d ^= pow_[(index[c[i]] + S[k - i]) % MAXN]
        if d == 0:
            l += 1
        elif 2 * L > k:
            for i in range(l, t2):
                if p[i - l] != 0:
                    c[i] ^= pow_[(index[d] - index[dm] + index[p[i - l]] + MAXN) % MAXN]
            l += 1
        else:
            T = list(c)
            for i in range(l, t2):
                if p[i - l] != 0:
                    c[i] ^= pow_[(index[d] - index[dm] + index[p[i - l]] + MAXN) % MAXN]
            L = k - L + 1
            p = T
            dm = d
            l = 1
    lam = [index[c[i]] for i in range(L + 1)]
    el = []
    for i in range(MAXN):
        tmp = 0
        for j in range(1, L + 1):
            if lam[j] >= 0:   # the C code reads pow[-1 + ...] here; zero coefficients are skipped
                tmp ^= pow_[(lam[j] + i * j) % MAXN]
        if tmp == 1:
            el.append((MAXN - i) % MAXN)
    return el
