"""End-to-end DVB-S2 transmitter and receiver with ideal synchronization.

TX: data -> BBFRAME (header, padding) -> BB scrambling -> BCH -> LDPC ->
    bit interleaver -> constellation mapper -> PLFRAME (header, pilots, scrambling)
RX: the PLFRAME boundaries, carrier phase and timing are known.  PLS decoding,
    PL descrambling, pilot removal -> soft demapper -> deinterleaver ->
    LDPC decoder -> BCH decoder -> BB descrambling -> BBHEADER check.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .bbframe import BBHeader, bb_scramble, build_bbframe, parse_bbframe
from .fec import FEC
from .modcod import ModCod
from .modulation import Mapper, deinterleave, interleave
from .plframe import build_plframe, decode_pls, split_plframe


@dataclass
class TxFrame:
    data: np.ndarray        # DATA FIELD bits
    bbframe: np.ndarray     # scrambled BBFRAME (BCH input)
    fecframe: np.ndarray    # LDPC codeword (64800 or 16200 bits)
    symbols: np.ndarray     # XFECFRAME symbols
    plframe: np.ndarray     # complete PLFRAME


@dataclass
class RxFrame:
    data: np.ndarray
    header_ok: bool          # BBHEADER CRC-8
    pls: tuple               # (modcod id, short, pilots) decoded from the PLHEADER
    llr: np.ndarray          # channel LLRs at the LDPC input
    ldpc_iterations: int
    ldpc_ok: bool
    bch_ok: bool
    bch_corrections: int


class Transmitter:
    def __init__(self, mc: ModCod, scrambling_code: int = 0):
        self.mc = mc
        self.fec = FEC(mc)
        self.mapper = Mapper(mc)
        self.scrambling_code = scrambling_code

    def frame(self, data) -> TxFrame:
        bb = bb_scramble(build_bbframe(data, self.mc.k_bch, BBHeader()))
        fecframe = self.fec.encode(bb)
        symbols = self.mapper.map(interleave(fecframe, self.mc))
        return TxFrame(np.asarray(data, np.uint8), bb, fecframe, symbols,
                       build_plframe(symbols, self.mc, self.scrambling_code))

    def random_frame(self, rng: np.random.Generator, dfl: int | None = None) -> TxFrame:
        dfl = self.mc.dfl_max if dfl is None else dfl
        return self.frame(rng.integers(0, 2, dfl, dtype=np.uint8))


class Receiver:
    def __init__(self, mc: ModCod, scrambling_code: int = 0, max_iter: int = 50, algorithm: str = "spa",
                 demap: str = "exact", use_bch: bool = True):
        self.mc = mc
        self.fec = FEC(mc)
        self.mapper = Mapper(mc)
        self.scrambling_code = scrambling_code
        self.max_iter, self.algorithm, self.demap_method, self.use_bch = max_iter, algorithm, demap, use_bch

    def llr(self, plframe, n0: float) -> tuple[np.ndarray, tuple]:
        header, symbols, _ = split_plframe(plframe, self.mc, self.scrambling_code)
        pls = decode_pls(header[26:])
        return deinterleave(self.mapper.demap(symbols, n0, self.demap_method), self.mc), pls

    def receive(self, plframe, n0: float) -> RxFrame:
        llr, pls = self.llr(plframe, n0)
        res = self.fec.decode(llr, self.max_iter, self.algorithm, self.use_bch)
        header, ok, data = parse_bbframe(bb_scramble(res.bbframe))
        return RxFrame(data, ok, pls, llr, res.ldpc_iterations, res.ldpc_ok, res.bch_ok, res.ldpc_errors_hint)
