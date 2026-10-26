"""Physical-layer framing (EN 302 307-1, 5.5).

PLFRAME = PLHEADER (90 pi/2-BPSK symbols: 26-bit SOF + 64-bit PLS code)
followed by the XFECFRAME split in slots of 90 symbols, with an optional
block of 36 pilot symbols after every 16 slots.  Everything after the
PLHEADER is multiplied by a complex Gold-sequence scrambler.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .modcod import PILOT_BLOCK, PILOT_PERIOD, SLOT, ModCod
from .modulation import pi2_bpsk

SOF = 0x18D2E82
PLS_SCRAMBLE = "0111000110011101100000111100100101010011010000100010110111111010"
_RM_ROWS = [0x55555555, 0x33333333, 0x0F0F0F0F, 0x00FF00FF, 0x0000FFFF, 0xFFFFFFFF]
PILOT_SYMBOL = (1 + 1j) / np.sqrt(2)


def _bits(value: int, n: int) -> np.ndarray:
    return np.array([(value >> (n - 1 - i)) & 1 for i in range(n)], dtype=np.uint8)


def pls_code(modcod_id: int, short: bool, pilots: bool) -> np.ndarray:
    """64-bit PLS code: (32,6) first-order Reed-Muller of MODCOD + frame-size bit, expanded by the pilot bit."""
    b = list(_bits(modcod_id, 5)) + [int(short)]
    y = 0
    for bit, row in zip(b, _RM_ROWS):
        if bit:
            y ^= row
    y = _bits(y, 32)
    out = np.empty(64, dtype=np.uint8)
    out[0::2] = y
    out[1::2] = y ^ int(pilots)
    return out ^ np.array([int(c) for c in PLS_SCRAMBLE], dtype=np.uint8)


def plheader_bits(mc: ModCod) -> np.ndarray:
    return np.concatenate([_bits(SOF, 26), pls_code(mc.id, mc.frame == "short", mc.pilots)])


def plheader(mc: ModCod) -> np.ndarray:
    return pi2_bpsk(plheader_bits(mc))


@lru_cache(maxsize=1)
def _pls_codebook():
    keys = [(m, s, p) for m in range(32) for s in (0, 1) for p in (0, 1)]
    book = np.array([pi2_bpsk(pls_code(m, s, p)) for m, s, p in keys])
    return keys, book


def decode_pls(symbols) -> tuple[int, bool, bool]:
    """Maximum-likelihood PLS decoding from the 64 received header symbols after SOF."""
    keys, book = _pls_codebook()
    corr = np.real(book.conj() @ np.asarray(symbols)[:64])
    m, s, p = keys[int(np.argmax(corr))]
    return m, bool(s), bool(p)


@lru_cache(maxsize=4)
def pl_scrambling_sequence(n: int, code: int = 0) -> np.ndarray:
    """Complex multipliers {1, j, -1, -j} for n symbols, scrambling code number ``code``."""
    period = (1 << 18) - 1
    length = n + code + 131072 + 18
    x = np.zeros(max(length, period) + 18, dtype=np.uint8)
    y = np.zeros_like(x)
    x[0] = 1
    y[:18] = 1
    for i in range(x.size - 18):
        x[i + 18] = x[i + 7] ^ x[i]
        y[i + 18] = y[i + 10] ^ y[i + 7] ^ y[i + 5] ^ y[i]
    i = np.arange(n)
    z = lambda k: x[(k + code) % period] ^ y[k % period]  # noqa: E731
    R = 2 * z((i + 131072) % period) + z(i)
    return np.array([1, 1j, -1, -1j])[R]


def build_plframe(xfec: np.ndarray, mc: ModCod, scrambling_code: int = 0) -> np.ndarray:
    """PLHEADER + slots (+ pilots), scrambled."""
    slots = np.asarray(xfec).reshape(mc.slots, SLOT)
    body = []
    for s in range(mc.slots):
        body.append(slots[s])
        if mc.pilots and (s + 1) % PILOT_PERIOD == 0 and s + 1 < mc.slots:
            body.append(np.full(PILOT_BLOCK, PILOT_SYMBOL))
    body = np.concatenate(body)
    body = body * pl_scrambling_sequence(body.size, scrambling_code)
    return np.concatenate([plheader(mc), body])


def split_plframe(frame: np.ndarray, mc: ModCod, scrambling_code: int = 0):
    """Inverse of :func:`build_plframe`: (header symbols, XFECFRAME symbols, pilot symbols)."""
    header, body = frame[:SLOT], frame[SLOT:]
    body = body * np.conj(pl_scrambling_sequence(body.size, scrambling_code))
    if not mc.pilots:
        return header, body, np.array([], dtype=complex)
    period = PILOT_PERIOD * SLOT + PILOT_BLOCK
    idx = np.arange(body.size)
    is_pilot = (idx % period) >= PILOT_PERIOD * SLOT
    return header, body[~is_pilot], body[is_pilot]
