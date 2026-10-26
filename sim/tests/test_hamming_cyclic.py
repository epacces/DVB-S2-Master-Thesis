import itertools

import numpy as np
import pytest

from dvbs2 import poly2
from dvbs2.codes.cyclic import CyclicCode, lfsr_divide_trace, lfsr_encode_trace, register_to_parity
from dvbs2.codes.hamming import HammingCode


@pytest.mark.parametrize("r", [2, 3, 4, 5])
def test_hamming_corrects_every_single_error(r):
    code = HammingCode(r)
    H = code.H()
    rng = np.random.default_rng(r)
    for _ in range(20):
        data = rng.integers(0, 2, code.k).astype(np.uint8)
        cw = code.encode(data)
        assert not (H.astype(int) @ cw % 2).any()
        for i in range(code.n):
            rx = cw.copy()
            rx[i] ^= 1
            res = code.decode(rx)
            assert res.status == "corrected" and np.array_equal(res.data, data)


def test_hamming_generator_and_check_are_orthogonal():
    code = HammingCode(3)
    assert code.G().shape == (4, 7)
    assert not (code.G().astype(int) @ code.H().T.astype(int) % 2).any()


def test_secded_detects_double_errors():
    code = HammingCode(3, extended=True)
    cw = code.encode([1, 0, 1, 1])
    for i, j in itertools.combinations(range(code.n), 2):
        rx = cw.copy()
        rx[[i, j]] ^= 1
        assert code.decode(rx).status == "detected"
    for i in range(code.n):
        rx = cw.copy()
        rx[i] ^= 1
        assert np.array_equal(code.decode(rx).codeword, cw)


def test_cyclic_7_4_and_lfsr_traces():
    g = 0b1011  # x^3 + x + 1
    code = CyclicCode(7, g)
    assert code.is_cyclic_generator()
    rng = np.random.default_rng(1)
    for _ in range(16):
        msg = rng.integers(0, 2, 4).astype(np.uint8)
        cw = code.encode(msg)
        assert code.is_codeword(cw) and code.is_codeword(np.roll(cw, 1))
        par = code.parity(msg)
        div = lfsr_divide_trace(np.concatenate([msg, np.zeros(3, np.uint8)]), g)
        enc = lfsr_encode_trace(msg, g)
        assert len(div) == 8 and len(enc) == 5
        assert np.array_equal(register_to_parity(div[-1]), par)
        assert np.array_equal(register_to_parity(enc[-1]), par)
        assert poly2.from_bits(register_to_parity(lfsr_divide_trace(cw, g)[-1])) == 0
