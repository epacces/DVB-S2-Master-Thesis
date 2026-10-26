"""p-parallel LFSR encoders from the state-space model (thesis, chapters 3-4).

The serial LFSR is the linear system over GF(2)

    x(i+1) = A x(i) + b u(i)

with A the companion matrix of g(x).  Applying it p times gives

    x(i+p) = A^p x(i) + B_p u_p(i),     B_p = [b, A b, ..., A^(p-1) b]

which consumes p bits per clock.  ``b = e_0`` gives the division circuit
(n/p clocks, ``BCHnclk_par``); ``b = g`` gives the premultiplied encoder
(k/p clocks, ``BCHkclk_par``).

Because the first r - p columns of A^p are a plain shift by p, the hardware
only needs p "state" XOR networks per register bit plus p "input" networks:
the 192 + 192 combinational networks of chapter 4.  With ``reg_len`` larger
than r, the generator is moved to the top of a longer register
(g'(x) = x^(reg_len - r) g(x)), which is how one 192-bit datapath serves the
t = 12, 10 and 8 DVB-S2 codes by switching off the lowest 32 or 64 stages.
"""
from __future__ import annotations

import pathlib

import numpy as np

from .. import poly2


def companion(g: int, r: int | None = None) -> np.ndarray:
    """A such that x(i+1) = A x(i) shifts the register and feeds back stage r-1 through g."""
    r = poly2.degree(g) if r is None else r
    A = np.zeros((r, r), dtype=np.uint8)
    A[np.arange(1, r), np.arange(r - 1)] = 1
    A[:, r - 1] ^= np.array([(g >> j) & 1 for j in range(r)], dtype=np.uint8)
    return A


def gf2_matmul(X, Y) -> np.ndarray:
    return (X.astype(np.int64) @ Y.astype(np.int64) & 1).astype(np.uint8)


def gf2_matpow(A, p: int) -> np.ndarray:
    out = np.eye(A.shape[0], dtype=np.uint8)
    for _ in range(p):
        out = gf2_matmul(A, out)
    return out


class ParallelLFSR:
    """p-parallel BCH encoder.

    mode "n": division circuit, the whole n-bit word (message + r zeros) is shifted in.
    mode "k": premultiplied circuit, only the k message bits are shifted in.
    """

    def __init__(self, g: int, p: int = 8, mode: str = "k", reg_len: int | None = None):
        if mode not in ("n", "k"):
            raise ValueError("mode must be 'n' or 'k'")
        self.r = poly2.degree(g)
        self.R = reg_len or self.r                  # physical register length
        if self.R < self.r:
            raise ValueError("reg_len shorter than deg g")
        self.offset = self.R - self.r               # disabled low stages
        self.g = g << self.offset if mode == "k" else g
        if mode == "n" and self.offset:
            raise ValueError("the shared-register trick applies to the k-clock encoder")
        self.p, self.mode = p, mode
        self.A = companion(self.g, self.R)
        self.Ap = gf2_matpow(self.A, p)
        if mode == "n":
            b = np.zeros(self.R, dtype=np.uint8)
            b[0] = 1
        else:
            b = np.array([(self.g >> j) & 1 for j in range(self.R)], dtype=np.uint8)
        cols, v = [], b
        for _ in range(p):
            cols.append(v)
            v = gf2_matmul(self.A, v[:, None])[:, 0]
        self.Bp = np.array(cols).T                  # column f multiplies input[f]
        self.b = b

    def clocks(self, n: int, k: int) -> int:
        return (n if self.mode == "n" else k) // self.p

    def run(self, bits, trace: bool = False):
        """Shift ``bits`` in p at a time; returns the final register (and the per-clock states)."""
        bits = np.asarray(bits, dtype=np.uint8)
        if bits.size % self.p:
            raise ValueError("number of input bits must be a multiple of p")
        x = np.zeros(self.R, dtype=np.uint8)
        states = [x.copy()]
        Ap, Bp = self.Ap.astype(np.int64), self.Bp.astype(np.int64)
        for chunk in bits.reshape(-1, self.p):
            u = chunk[::-1].astype(np.int64)  # input[p-1] is the first bit of the chunk
            x = ((Ap @ x + Bp @ u) & 1).astype(np.uint8)
            if trace:
                states.append(x.copy())
        return (x, np.array(states)) if trace else x

    def parity(self, msg) -> np.ndarray:
        """Parity bits (transmission order) of a message."""
        msg = np.asarray(msg, dtype=np.uint8)
        bits = np.concatenate([msg, np.zeros(self.r, np.uint8)]) if self.mode == "n" else msg
        reg = self.run(bits)
        return reg[self.offset:][::-1].copy()

    def network_inputs(self) -> dict:
        """Number of active inputs of each register bit's XOR networks (for the hardware view)."""
        state_part = self.Ap[:, self.R - self.p:]
        return {"state": state_part.sum(axis=1), "input": self.Bp.sum(axis=1)}

    def write_matrices(self, directory, tag: str) -> list[pathlib.Path]:
        """Write A^p and B_p as tab-separated text, the format ``load_matrices`` in main.c reads."""
        directory = pathlib.Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        out = []
        for name, M in (("ADVBS2_%sclk_%s.txt" % (self.mode, tag), self.Ap),
                        ("CDVBS2_%sclk_%s.txt" % (self.mode, tag), self.Bp)):
            path = directory / name
            path.write_text("".join("\t".join(map(str, row)) + "\t\n" for row in M))
            out.append(path)
        return out
