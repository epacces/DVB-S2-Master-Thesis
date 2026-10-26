import numpy as np
import pytest

from dvbs2.codes import _kernels
from dvbs2.codes.ldpc import RATES, dvbs2_ldpc

# Variable-node degree profiles, EN 302 307-1 Tables 7a (normal) and 7b (short):
# rate -> (high degree j, count of j, count of degree 3); degree 2: N-K-1 and one degree-1 node.
PROFILE = {
    "normal": {"1/4": (12, 5400, 10800), "1/3": (12, 7200, 14400), "2/5": (12, 8640, 17280),
               "1/2": (8, 12960, 19440), "3/5": (12, 12960, 25920), "2/3": (13, 4320, 38880),
               "3/4": (12, 5400, 43200), "4/5": (11, 6480, 45360), "5/6": (13, 5400, 48600),
               "8/9": (4, 7200, 50400), "9/10": (4, 6480, 51840)},
    "short": {"1/4": (12, 1440, 1800), "1/3": (12, 1800, 3600), "2/5": (12, 2160, 4320),
              "1/2": (8, 1800, 5400), "3/5": (12, 3240, 6480), "2/3": (13, 1080, 9720),
              "3/4": (12, 360, 11520), "4/5": (None, 0, 12600), "5/6": (13, 360, 12960),
              "8/9": (4, 1800, 12600)},
}
CASES = [(f, r) for f in ("normal", "short") for r in RATES[f]]


@pytest.mark.parametrize("frame,rate", CASES)
def test_encoder_and_profile(frame, rate):
    code = dvbs2_ldpc(rate, frame)
    rng = np.random.default_rng(0)
    for _ in range(2):
        cw = code.encode(rng.integers(0, 2, code.k))
        assert code.is_codeword(cw)
    j, nj, n3 = PROFILE[frame][rate]
    expected = {1: 1, 2: code.m - 1, 3: n3}
    if j:
        expected[j] = nj
    assert code.degree_profile() == expected
    assert code.n == (64800 if frame == "normal" else 16200)


@pytest.mark.parametrize("algorithm", ["spa", "nms", "oms"])
def test_decoders_converge(algorithm):
    code = dvbs2_ldpc("1/2", "short")
    rng = np.random.default_rng(1)
    cw = code.encode(rng.integers(0, 2, code.k))
    sigma = 0.8
    llr = 2 * ((1 - 2.0 * cw) + sigma * rng.standard_normal(code.n)) / sigma ** 2
    hard, _, it = code.decode(llr, 50, algorithm)
    assert np.array_equal(hard, cw) and it < 50


def test_flooding_fallback():
    code = dvbs2_ldpc("3/4", "short")
    rng = np.random.default_rng(2)
    cw = code.encode(rng.integers(0, 2, code.k))
    sigma = 0.55
    llr = 2 * ((1 - 2.0 * cw) + sigma * rng.standard_normal(code.n)) / sigma ** 2
    L, it = _kernels.flooding_minsum(llr, code.row_ptr, code.cols, 50)
    assert np.array_equal((L < 0).astype(np.uint8), cw)
