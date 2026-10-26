"""Mode adaptation and stream adaptation (EN 302 307-1, 5.1 and 5.2).

A BBFRAME is the 80-bit BBHEADER, the DATA FIELD (DFL bits) and zero padding
up to K_bch, all XORed with the base-band scrambling sequence 1 + x^14 + x^15.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

CRC8_POLY = 0xD5  # x^8 + x^7 + x^6 + x^4 + x^2 + 1


def crc8(bits) -> int:
    reg = 0
    for b in np.asarray(bits, dtype=np.uint8):
        fb = ((reg >> 7) & 1) ^ int(b)
        reg = (reg << 1) & 0xFF
        if fb:
            reg ^= CRC8_POLY
    return reg


def _bits(value: int, n: int) -> list[int]:
    return [(value >> (n - 1 - i)) & 1 for i in range(n)]


@dataclass
class BBHeader:
    """Generic continuous stream (GS), single input stream, CCM, by default."""
    ts_gs: int = 0b01      # 11 = TS, 01 = generic continuous, 00 = generic packetized
    sis: int = 1           # single input stream
    ccm: int = 1           # constant coding and modulation
    issyi: int = 0
    npd: int = 0
    rolloff: int = 0b00    # 00 = 0.35, 01 = 0.25, 10 = 0.20
    isi: int = 0           # MATYPE-2
    upl: int = 0
    dfl: int = 0
    sync: int = 0
    syncd: int = 0

    def to_bits(self) -> np.ndarray:
        bits = (_bits(self.ts_gs, 2) + [self.sis, self.ccm, self.issyi, self.npd] + _bits(self.rolloff, 2)
                + _bits(self.isi, 8) + _bits(self.upl, 16) + _bits(self.dfl, 16) + _bits(self.sync, 8)
                + _bits(self.syncd, 16))
        return np.array(bits + _bits(crc8(bits), 8), dtype=np.uint8)

    @classmethod
    def from_bits(cls, bits) -> tuple["BBHeader", bool]:
        """Parse 80 bits; also return whether the CRC-8 checks."""
        b = [int(x) for x in bits[:80]]

        def val(lo, n):
            return int("".join(map(str, b[lo:lo + n])), 2)

        hdr = cls(val(0, 2), b[2], b[3], b[4], b[5], val(6, 2), val(8, 8), val(16, 16), val(32, 16),
                  val(48, 8), val(56, 16))
        return hdr, crc8(b[:72]) == val(72, 8)


def bb_scrambling_sequence(n: int) -> np.ndarray:
    """PRBS 1 + x^14 + x^15 with initial state 100101010000000 (Fig. 5)."""
    reg = [1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0]  # cells 1 .. 15
    out = np.empty(n, dtype=np.uint8)
    for i in range(n):
        b = reg[13] ^ reg[14]
        out[i] = b
        reg = [b] + reg[:14]
    return out


_SEQ_CACHE: dict[int, np.ndarray] = {}


def bb_scramble(bits) -> np.ndarray:
    """XOR with the BB scrambling sequence (its own inverse)."""
    bits = np.asarray(bits, dtype=np.uint8)
    n = bits.shape[-1]
    if n not in _SEQ_CACHE:
        _SEQ_CACHE[n] = bb_scrambling_sequence(n)
    return bits ^ _SEQ_CACHE[n]


def build_bbframe(data, k_bch: int, header: BBHeader | None = None) -> np.ndarray:
    """BBHEADER + DATA FIELD + padding, before scrambling."""
    data = np.asarray(data, dtype=np.uint8)
    header = header or BBHeader()
    header.dfl = data.size
    if data.size > k_bch - 80:
        raise ValueError("data field longer than K_bch - 80")
    frame = np.zeros(k_bch, dtype=np.uint8)
    frame[:80] = header.to_bits()
    frame[80:80 + data.size] = data
    return frame


def parse_bbframe(frame) -> tuple[BBHeader, bool, np.ndarray]:
    header, ok = BBHeader.from_bits(frame[:80])
    return header, ok, np.asarray(frame[80:80 + header.dfl], dtype=np.uint8)
