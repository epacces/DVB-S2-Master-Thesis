"""Capacity limits for the DVB-S2 constellations over AWGN.

* Shannon: log2(1 + Es/N0), the unconstrained limit.
* CM: mutual information I(X;Y) with equiprobable constellation points.
* BICM: sum of the bit-channel capacities seen by an ideal bit-interleaved
  decoder (what DVB-S2's LDPC + demapper can at best achieve).

The constrained capacities are Monte Carlo estimates with a fixed seed.
"""
from __future__ import annotations

import numpy as np

from .channel import db2lin
from .modulation import constellation, label_bits


def shannon(esn0_db):
    return np.log2(1 + db2lin(esn0_db))


def shannon_esn0(efficiency):
    """Es/N0 (dB) at which the Shannon capacity equals ``efficiency``."""
    return 10 * np.log10(2.0 ** np.asarray(efficiency) - 1)


def _samples(points, esn0_db, n, seed):
    rng = np.random.default_rng(seed)
    n0 = 1 / db2lin(esn0_db)
    idx = rng.integers(0, points.size, n)
    noise = (rng.standard_normal(n) + 1j * rng.standard_normal(n)) * np.sqrt(n0 / 2)
    y = points[idx] + noise
    metric = -np.abs(y[:, None] - points[None, :]) ** 2 / n0
    return idx, metric


def cm_capacity(modulation: str, esn0_db, gamma=None, n: int = 20000, seed: int = 1):
    pts = constellation(modulation, gamma)
    out = []
    for e in np.atleast_1d(esn0_db):
        idx, metric = _samples(pts, e, n, seed)
        own = metric[np.arange(n), idx]
        mx = metric.max(axis=1)
        lse = mx + np.log(np.exp(metric - mx[:, None]).sum(axis=1))
        out.append(np.log2(pts.size) - np.mean(lse - own) / np.log(2))
    return np.array(out)


def bicm_capacity(modulation: str, esn0_db, gamma=None, n: int = 20000, seed: int = 1):
    pts = constellation(modulation, gamma)
    m = int(np.log2(pts.size))
    labels = label_bits(m)
    out = []
    for e in np.atleast_1d(esn0_db):
        idx, metric = _samples(pts, e, n, seed)
        mx = metric.max(axis=1, keepdims=True)
        ex = np.exp(metric - mx)
        total = 0.0
        for j in range(m):
            zero = labels[:, j] == 0
            b = labels[idx, j].astype(bool)
            same = np.where(b, ex[:, ~zero].sum(axis=1), ex[:, zero].sum(axis=1))
            other = np.where(b, ex[:, zero].sum(axis=1), ex[:, ~zero].sum(axis=1))
            total += 1 - np.mean(np.log2(1 + other / same))
        out.append(total)
    return np.array(out)


def required_esn0(capacity_fn, efficiency, lo=-10.0, hi=30.0, iters=30):
    """Es/N0 (dB) where ``capacity_fn(esn0_db)`` reaches ``efficiency`` (bisection).

    Example: ``required_esn0(lambda e: bicm_capacity("8PSK", e), 1.78)``.
    """
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if float(np.atleast_1d(capacity_fn(mid))[0]) < efficiency:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)
