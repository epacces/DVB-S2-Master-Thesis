import numpy as np
import pytest

from dvbs2 import legacy
from dvbs2.codes.bch import BCHCode, dvbs2_bch
from dvbs2.codes.bch_parallel import ParallelLFSR

RATES_NORMAL = ["1/4", "1/3", "2/5", "1/2", "3/5", "2/3", "3/4", "4/5", "5/6", "8/9", "9/10"]
RATES_SHORT = ["1/4", "1/3", "2/5", "1/2", "3/5", "2/3", "3/4", "4/5", "5/6", "8/9"]


@pytest.mark.parametrize("rate,name", [("1/2", "gen12"), ("2/3", "gen10"), ("8/9", "gen8")])
def test_generators_match_main_c(rate, name):
    g = legacy.generator_arrays()[name]
    assert dvbs2_bch(rate).g == sum(b << i for i, b in enumerate(g))


def test_dimensions():
    for rate in RATES_NORMAL:
        c = dvbs2_bch(rate, "normal")
        assert c.r == 16 * c.t
    assert dvbs2_bch("1/2").k == 32208
    assert dvbs2_bch("9/10").k == 58192
    for rate in RATES_SHORT:
        c = dvbs2_bch(rate, "short")
        assert c.r == 168 and c.t == 12
    assert dvbs2_bch("1/4", "short").k == 3072


def test_small_bch_15_7():
    c = BCHCode(4, 2)
    assert (c.n, c.k) == (15, 7) and c.g == 0b111010001
    rng = np.random.default_rng(0)
    for _ in range(50):
        cw = c.encode(rng.integers(0, 2, 7))
        rx = cw.copy()
        rx[rng.choice(15, rng.integers(0, 3), replace=False)] ^= 1
        res = c.decode(rx)
        assert res.success and np.array_equal(res.codeword, cw)


@pytest.mark.parametrize("frame,rate", [("normal", "1/2"), ("normal", "2/3"), ("normal", "9/10"), ("short", "3/5")])
def test_decoder_corrects_up_to_t(frame, rate):
    c = dvbs2_bch(rate, frame)
    rng = np.random.default_rng(42)
    cw = c.encode(rng.integers(0, 2, c.k))
    assert c.is_codeword(cw)
    for nerr in (0, 1, c.t // 2, c.t):
        rx = cw.copy()
        idx = rng.choice(c.n, nerr, replace=False)
        rx[idx] ^= 1
        trace = []
        res = c.decode(rx, trace)
        assert res.success and res.n_errors == nerr
        assert np.array_equal(res.codeword, cw)
        assert np.array_equal(res.error_positions, np.sort(idx))


def test_decoder_flags_too_many_errors():
    c = dvbs2_bch("1/2")
    rng = np.random.default_rng(7)
    cw = c.encode(rng.integers(0, 2, c.k))
    failures = 0
    for _ in range(5):
        rx = cw.copy()
        rx[rng.choice(c.n, c.t + 3, replace=False)] ^= 1
        res = c.decode(rx)
        failures += not res.success
        assert not np.array_equal(res.codeword, cw)
    assert failures == 5  # miscorrection is astronomically unlikely for t = 12


@pytest.mark.parametrize("rate", ["1/2", "2/3", "8/9"])
@pytest.mark.parametrize("mode", ["n", "k"])
def test_parallel_encoders_match_serial(rate, mode):
    c = dvbs2_bch(rate)
    msg = np.random.default_rng(3).integers(0, 2, c.k).astype(np.uint8)
    enc = ParallelLFSR(c.g, 8, mode, reg_len=192 if mode == "k" else None)
    assert np.array_equal(enc.parity(msg), c.parity(msg))


def test_ap_structure():
    enc = ParallelLFSR(dvbs2_bch("1/2").g, 8, "n")
    r = enc.r
    shift = np.zeros((r, r - 8), np.uint8)
    shift[np.arange(8, r), np.arange(r - 8)] = 1
    assert np.array_equal(enc.Ap[:, :r - 8], shift)   # only the last p columns are "dense"
    assert np.array_equal(enc.Bp[:8], np.eye(8, dtype=np.uint8))


# --- against the transliterated C (short codes keep pure-Python loops fast) ----

def _power_indexed(bits):
    return list(np.asarray(bits)[::-1])


def test_legacy_serial_encoder():
    c = dvbs2_bch("1/4")       # n = 16200, k = 16008, as in main.c
    msg = np.random.default_rng(5).integers(0, 2, c.k).astype(np.uint8)
    message = [0] * c.r + _power_indexed(msg)
    gen12 = legacy.generator_arrays()["gen12"]
    codeword = legacy.BCH_s_enc(message, c.n, c.k, gen12)
    assert np.array_equal(np.array(codeword[::-1]), c.encode(msg))


@pytest.mark.parametrize("rate", ["1/4", "2/3"])
def test_legacy_parallel_encoders(rate):
    c = dvbs2_bch(rate)
    msg = np.random.default_rng(6).integers(0, 2, c.k).astype(np.uint8)
    message = [0] * c.r + _power_indexed(msg)
    k_enc = ParallelLFSR(c.g, 8, "k", reg_len=192)
    cw_k = legacy.BCHkclk_par(message, c.n, c.k, k_enc.Ap.tolist(), k_enc.Bp.tolist())
    assert np.array_equal(np.array(cw_k[::-1]), c.encode(msg))
    if c.r == 192:
        n_enc = ParallelLFSR(c.g, 8, "n")
        cw_n = legacy.BCHnclk_par(message, c.n, c.k, n_enc.Ap.tolist())
        assert np.array_equal(np.array(cw_n[::-1]), c.encode(msg))


def test_legacy_decoder():
    c = dvbs2_bch("1/4")
    rng = np.random.default_rng(8)
    cw = c.encode(rng.integers(0, 2, c.k))
    idx = rng.choice(c.n, c.t, replace=False)
    rx = cw.copy()
    rx[idx] ^= 1
    pow_, index = legacy.gfField(16, 32 + 8 + 4 + 1)
    detected, S = legacy.error_detection(rx[::-1], pow_, index, c.t)
    assert detected
    assert S == [int(c.gf.log[s]) for s in c.syndromes(rx)]
    el = legacy.BerlMass(S, 2 * c.t, pow_, index)
    assert sorted(c.n - 1 - np.array(el)) == sorted(idx)
