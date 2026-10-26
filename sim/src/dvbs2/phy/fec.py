"""FEC encoding (5.3): BCH outer code + LDPC inner code -> FECFRAME."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..codes.bch import dvbs2_bch
from ..codes.ldpc import dvbs2_ldpc
from .modcod import ModCod


@dataclass
class FECResult:
    bbframe: np.ndarray       # decoded (scrambled) BBFRAME, K_bch bits
    ldpc_iterations: int
    ldpc_errors_hint: int     # BCH corrections needed after LDPC (-1: BCH failure)
    ldpc_ok: bool             # LDPC output was a valid codeword
    bch_ok: bool


class FEC:
    def __init__(self, mc: ModCod):
        self.mc = mc
        self.bch = dvbs2_bch(mc.rate, mc.frame)
        self.ldpc = dvbs2_ldpc(mc.rate, mc.frame)
        assert self.bch.n == self.ldpc.k and self.bch.k == mc.k_bch

    def encode(self, bbframe) -> np.ndarray:
        return self.ldpc.encode(self.bch.encode(bbframe))

    def decode(self, llr, max_iter: int = 50, algorithm: str = "spa", use_bch: bool = True) -> FECResult:
        hard, _, it = self.ldpc.decode(llr, max_iter, algorithm)
        ldpc_ok = self.ldpc.is_codeword(hard)
        bch_word = hard[:self.bch.n]
        if not use_bch:
            return FECResult(bch_word[:self.bch.k], it, 0, ldpc_ok, True)
        res = self.bch.decode(bch_word)
        return FECResult(res.codeword[:self.bch.k], it, res.n_errors if res.success else -1, ldpc_ok, res.success)
