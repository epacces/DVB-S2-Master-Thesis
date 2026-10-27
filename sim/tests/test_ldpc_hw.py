import numpy as np
import pytest
import scipy.sparse as sp

from dvbs2.codes import _kernels
from dvbs2.codes import ldpc_hw as hw
from dvbs2.codes.ldpc import RATES, dvbs2_ldpc, parse_decoder

ALL = [(r, f) for f in ("normal", "short") for r in RATES[f]]


def qc_rebuild(code, qc):
    rows, cols = [], []
    l = np.arange(360)
    for a, layer in enumerate(qc.layers):
        for col, s in layer:
            keep = l != 359 if (a, col) == qc.missing else np.ones(360, bool)
            rows.append(a * 360 + (l[keep] + s) % 360)
            cols.append(col * 360 + l[keep])
    r, c = np.concatenate(rows), np.concatenate(cols)
    return sp.csr_matrix((np.ones(r.size, np.int64), (r, c)), shape=(code.m, code.n))


@pytest.mark.parametrize("rate,frame", ALL)
def test_permuted_H_is_made_of_circulants(rate, frame):
    code = dvbs2_ldpc(rate, frame)
    qc = hw.qc_structure(code)
    Hp = hw.permuted_H(code).astype(np.int64)
    assert (qc_rebuild(code, qc) != Hp).nnz == 0
    # every circulant is one edge per row of the block, except the missing wrap-around entry
    assert code.H.nnz == 360 * sum(qc.layer_degrees) - 1
    w2 = sum(len(row) - len({x % code.q for x in row}) for row in code.table)
    assert len(qc.weight2) == w2


def test_layer_schedule_covers_every_edge_once():
    code = dvbs2_ldpc("3/4", "short")
    s = hw.layer_schedule(code)
    assert s.cols.size == code.H.nnz
    assert sorted(np.concatenate([i[i < code.n] for i in s.idx]).tolist()) == sorted(code.cols.tolist())


def test_parse_decoder():
    assert parse_decoder("spa")["schedule"] == "layered"
    assert parse_decoder("nms:0.875")["alpha"] == 0.875
    assert parse_decoder("flood-oms:0.25") == {"schedule": "flooding", "algorithm": "oms", "alpha": 0.8,
                                               "beta": 0.25, "fmt": None}
    f = parse_decoder("fixed:5,7,6:4:7/8")["fmt"]
    assert (f.w_ch, f.w_L, f.w_R, f.scale, f.alpha) == (5, 7, 6, 4.0, 0.875)
    f = parse_decoder("fixed:6,8,6:2:b1")["fmt"]
    assert (f.alpha, f.beta) == (1.0, 1)
    with pytest.raises(ValueError):
        parse_decoder("fixed:6,8,6:2:3/5")


def noisy(code, sigma, seed):
    rng = np.random.default_rng(seed)
    cw = code.encode(rng.integers(0, 2, code.k))
    return cw, 2 * ((1 - 2.0 * cw) + sigma * rng.standard_normal(code.n)) / sigma ** 2


@pytest.mark.skipif(not _kernels.HAVE_NUMBA, reason="numba not installed")
@pytest.mark.parametrize("spec", ["fixed:6,8,6:2:b1", "fixed:5,7,6:2:7/8", "fixed:4,6,5:1:b1"])
def test_fixed_point_numpy_and_numba_are_bit_exact(spec):
    code = dvbs2_ldpc("3/5", "short")
    cw, llr = noisy(code, 0.75, 4)
    fmt = parse_decoder(spec)["fmt"]
    La, ia = hw.layer_decode(llr, code, 20, fmt=fmt, impl="numpy")
    Lb, ib = hw.layer_decode(llr, code, 20, fmt=fmt, impl="numba")
    assert ia == ib and np.array_equal(La, Lb)


@pytest.mark.skipif(not _kernels.HAVE_NUMBA, reason="numba not installed")
def test_float_numpy_and_numba_agree():
    code = dvbs2_ldpc("1/2", "short")
    cw, llr = noisy(code, 0.85, 2)
    La, ia = hw.layer_decode(llr, code, 10, "oms", beta=0.5, impl="numpy", early_stop=False)
    Lb, ib = hw.layer_decode(llr, code, 10, "oms", beta=0.5, impl="numba", early_stop=False)
    assert np.allclose(La, Lb, atol=1e-9)


def test_kernels_match_brute_force_min_sum():
    code = dvbs2_ldpc("8/9", "short")
    llr = np.random.default_rng(0).normal(0.5, 2, code.n)
    H = code.H
    alpha = 0.875
    R, L = {}, llr.copy()
    for r in range(code.m):  # one layered iteration, rows in natural order
        cs = H.indices[H.indptr[r]:H.indptr[r + 1]]
        Q = {v: L[v] - R.get((r, v), 0.0) for v in cs}
        for v in cs:
            others = [Q[u] for u in cs if u != v]
            R[(r, v)] = alpha * np.prod(np.sign(others)) * min(abs(x) for x in others)
            L[v] = Q[v] + R[(r, v)]
    if _kernels.HAVE_NUMBA:
        Lk, _ = _kernels.layered_decode(llr, code.row_ptr, code.cols, 1, alpha, 0.0, False)
        assert np.allclose(Lk, L)
    # flooding: every check from the channel LLRs only
    Lf, _ = _kernels.flooding_minsum(llr, code.row_ptr, code.cols, 1, alpha, 0.0)
    ref = llr.copy()
    for r in range(code.m):
        cs = H.indices[H.indptr[r]:H.indptr[r + 1]]
        for v in cs:
            others = [llr[u] for u in cs if u != v]
            ref[v] += alpha * np.prod(np.sign(others)) * min(abs(x) for x in others)
    assert np.allclose(Lf, ref)


def test_wide_fixed_point_tracks_float_offset_min_sum():
    code = dvbs2_ldpc("2/3", "short")
    cw, llr = noisy(code, 0.62, 9)
    h_float, _, _ = code.decode(llr, 30, "hw-oms:0.5")
    h_fixed, _, _ = code.decode(llr, 30, "fixed:14,18,16:256:b128")
    assert np.array_equal(h_float, h_fixed)
    assert np.array_equal(h_float, cw)


@pytest.mark.parametrize("rate,frame", ALL)
def test_fixed_point_decodes_noiseless_frames(rate, frame):
    code = dvbs2_ldpc(rate, frame)
    cw, _ = noisy(code, 1.0, 1)
    hard, _, it = code.decode(4.0 * (1 - 2.0 * cw), 5, "fixed:6,8,6:2:b1")
    assert np.array_equal(hard, cw) and it == 1


@pytest.mark.parametrize("spec", ["hw-nms:0.875", "hw-oms:0.5", "flood-oms:0.5", "fixed:6,8,6:2:b1"])
def test_decoders_correct_moderate_noise(spec):
    code = dvbs2_ldpc("1/2", "short")
    cw, llr = noisy(code, 0.8, 3)
    assert np.array_equal(code.decode(llr, 50, spec)[0], cw)


def test_architecture_model():
    code = dvbs2_ldpc("1/2", "normal")
    a = hw.architecture(code, 360, 200.0, 30)
    distinct = sum(len({c for c, _ in l}) for l in hw.qc_structure(code).layers)
    # reordering can at best read each distinct block column of a layer once per cycle
    assert a.cycles_per_iter["reordered"] >= distinct
    assert a.cycles_per_iter["overlap"] == distinct + a.stalls["overlap"]
    assert a.cycles_per_iter["serial"] == 2 * distinct + 6 * code.q
    assert a.memory_bits["L"] == code.n * 8
    half = hw.architecture(code, 180, 200.0, 30)
    assert half.throughput_mbps["serial"] < a.throughput_mbps["serial"]
    with pytest.raises(ValueError):
        hw.architecture(code, 100)
