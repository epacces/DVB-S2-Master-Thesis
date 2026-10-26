"""LDPC decoding kernels.

With numba installed (and DVBS2_NO_NUMBA unset) the layered (row-serial) decoders are compiled; without
it (e.g. in the browser under Pyodide) a vectorised numpy flooding min-sum is
used instead.  All decoders take channel LLRs log(P(0)/P(1)) and return the
posterior LLRs and the number of iterations run.
"""
from __future__ import annotations

import numpy as np

import os

try:
    if os.environ.get("DVBS2_NO_NUMBA"):  # force the pure-numpy path (as in the browser)
        raise ImportError
    import numba
    HAVE_NUMBA = True
except ImportError:
    HAVE_NUMBA = False


def _layered_impl(llr, row_ptr, cols, max_iter, alpha, beta, spa):
    n_rows = row_ptr.size - 1
    L = llr.astype(np.float64).copy()
    R = np.zeros(cols.size, dtype=np.float64)
    max_deg = 0
    for r in range(n_rows):
        max_deg = max(max_deg, row_ptr[r + 1] - row_ptr[r])
    Q = np.empty(max_deg, dtype=np.float64)
    T = np.empty(max_deg, dtype=np.float64)
    fwd = np.empty(max_deg + 1, dtype=np.float64)
    it = 0
    while it < max_iter:
        it += 1
        for r in range(n_rows):
            a, b = row_ptr[r], row_ptr[r + 1]
            d = b - a
            if not spa:
                min1 = 1e300
                min2 = 1e300
                pos = 0
                sgn = 1.0
                for e in range(d):
                    q = L[cols[a + e]] - R[a + e]
                    Q[e] = q
                    mag = abs(q)
                    if q < 0:
                        sgn = -sgn
                    if mag < min1:
                        min2 = min1
                        min1 = mag
                        pos = e
                    elif mag < min2:
                        min2 = mag
                m1 = max(alpha * min1 - beta, 0.0)
                m2 = max(alpha * min2 - beta, 0.0)
                for e in range(d):
                    q = Q[e]
                    s = sgn if q >= 0 else -sgn
                    msg = s * (m2 if e == pos else m1)
                    R[a + e] = msg
                    L[cols[a + e]] = q + msg
            else:
                for e in range(d):
                    q = L[cols[a + e]] - R[a + e]
                    Q[e] = q
                    T[e] = np.tanh(0.5 * min(max(q, -40.0), 40.0))
                fwd[0] = 1.0
                for e in range(d):
                    fwd[e + 1] = fwd[e] * T[e]
                bwd = 1.0
                for e in range(d - 1, -1, -1):
                    prod = fwd[e] * bwd
                    prod = min(max(prod, -0.999999999999), 0.999999999999)
                    msg = 2.0 * np.arctanh(prod)
                    R[a + e] = msg
                    L[cols[a + e]] = Q[e] + msg
                    bwd *= T[e]
        # early termination: every parity check satisfied
        ok = True
        for r in range(n_rows):
            par = 0
            for e in range(row_ptr[r], row_ptr[r + 1]):
                if L[cols[e]] < 0:
                    par ^= 1
            if par:
                ok = False
                break
        if ok:
            break
    return L, it


if HAVE_NUMBA:
    _layered = numba.njit(cache=True, fastmath=False)(_layered_impl)
else:
    _layered = None


def layered_decode(llr, row_ptr, cols, max_iter=50, alpha=0.8, beta=0.0, spa=False):
    if _layered is None:
        raise RuntimeError("layered decoding needs numba; use flooding_minsum")
    return _layered(np.ascontiguousarray(llr, dtype=np.float64), row_ptr, cols,
                    int(max_iter), float(alpha), float(beta), bool(spa))


def flooding_minsum(llr, row_ptr, cols, max_iter=50, alpha=0.8, beta=0.0):
    """Normalized/offset min-sum with a flooding schedule, numpy only."""
    llr = np.asarray(llr, dtype=np.float64)
    # np.intp: Pyodide is 32-bit, where np.repeat refuses int64 counts.
    row_ptr = np.asarray(row_ptr, dtype=np.intp)
    cols = np.asarray(cols, dtype=np.intp)
    starts = row_ptr[:-1]
    deg = np.diff(row_ptr)
    row_of_edge = np.repeat(np.arange(deg.size), deg)
    R = np.zeros(cols.size)
    L = llr.copy()
    it = 0
    for it in range(1, max_iter + 1):
        Q = L[cols] - R
        mag = np.abs(Q)
        neg = Q < 0
        sgn = np.where(np.add.reduceat(neg.astype(np.int64), starts) % 2 == 1, -1.0, 1.0)
        min1 = np.minimum.reduceat(mag, starts)
        is_min = mag == min1[row_of_edge]
        # min2: minimum after removing the first occurrence of min1 in each row
        first = np.zeros(cols.size, dtype=bool)
        cand = np.flatnonzero(is_min)
        _, first_idx = np.unique(row_of_edge[cand], return_index=True)
        first[cand[first_idx]] = True
        min2 = np.minimum.reduceat(np.where(first, np.inf, mag), starts)
        m = np.where(first, min2[row_of_edge], min1[row_of_edge])
        m = np.maximum(alpha * m - beta, 0.0)
        R = np.where(neg, -1.0, 1.0) * sgn[row_of_edge] * m
        L = llr + np.bincount(cols, weights=R, minlength=llr.size)
        hard = (L < 0).astype(np.int64)
        if not np.any(np.add.reduceat(hard[cols], starts) % 2):
            break
    return L, it
