"""AWGN channel and SNR conversions (unit-energy symbols, Es = 1)."""
from __future__ import annotations

import numpy as np


def db2lin(db):
    return 10.0 ** (np.asarray(db) / 10.0)


def lin2db(x):
    return 10.0 * np.log10(x)


def esn0_to_ebn0(esn0_db, efficiency):
    """Eb/N0 for a link carrying ``efficiency`` information bits per symbol."""
    return np.asarray(esn0_db) - lin2db(efficiency)


def ebn0_to_esn0(ebn0_db, efficiency):
    return np.asarray(ebn0_db) + lin2db(efficiency)


def awgn(symbols, esn0_db: float, rng: np.random.Generator):
    """Add complex white Gaussian noise; returns (received symbols, N0)."""
    n0 = 1.0 / db2lin(esn0_db)
    noise = rng.standard_normal(symbols.shape) + 1j * rng.standard_normal(symbols.shape)
    return symbols + noise * np.sqrt(n0 / 2), float(n0)
