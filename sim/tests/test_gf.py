import numpy as np
import pytest

from dvbs2 import legacy, poly2
from dvbs2.gf import GF2m, GFp, PRIMITIVE_POLYS, is_primitive, lfsr_cycle_length


@pytest.mark.parametrize("m", range(2, 17))
def test_default_polynomials_are_primitive(m):
    assert is_primitive(PRIMITIVE_POLYS[m])


@pytest.mark.parametrize("m", [2, 3, 4, 5, 8])
def test_field_axioms(m):
    F = GF2m(m)
    a = F.elements()[:, None]
    b = F.elements()[None, :]
    prod = F.mul(a, b)
    assert np.array_equal(prod, prod.T)                        # commutative
    assert np.array_equal(F.mul(a, 1), a)                      # identity
    nz = F.elements()[1:]
    assert np.all(F.mul(nz, F.inv(nz)) == 1)                   # inverses
    for c in range(F.q):                                       # distributive
        assert np.array_equal(F.mul(c, a ^ b), F.mul(c, a) ^ F.mul(c, b))


def test_tables_match_gfield_c():
    F = GF2m(16, 0x1002D)
    pow_, index = legacy.gfField(16, 32 + 8 + 4 + 1)
    assert np.array_equal(F.exp[:F.order], pow_)
    assert np.array_equal(F.log, index)


def test_non_primitive_polynomial_rejected():
    poly = 0b11111  # x^4+x^3+x^2+x+1: irreducible, period 5
    assert lfsr_cycle_length(poly) == 5
    assert not is_primitive(poly)
    with pytest.raises(ValueError):
        GF2m(4, poly)


def test_minimal_polynomials_gf16():
    F = GF2m(4)  # x^4 + x + 1
    assert F.minimal_polynomial(1) == 0b10011
    assert F.minimal_polynomial(3) == 0b11111
    assert F.minimal_polynomial(5) == 0b111
    assert F.cyclotomic_coset(3) == [3, 6, 12, 9]
    assert sum(len(c) for c in F.cyclotomic_cosets()) == 15


def test_pow_and_div():
    F = GF2m(8)
    x = np.arange(1, 256)
    assert np.all(F.pow(x, 255) == 1)
    assert np.all(F.mul(F.div(x, 7), 7) == x)


def test_gfp():
    F = GFp(7)
    assert F.mul_table()[3, 5] == 1 and F.inv(3) == 5
    assert F.primitive_elements() == [3, 5]
    with pytest.raises(ValueError):
        GFp(9)


def test_poly2_roundtrip():
    rng = np.random.default_rng(0)
    for n in (1, 7, 8, 9, 200):
        bits = rng.integers(0, 2, n).astype(np.uint8)
        assert np.array_equal(poly2.to_bits(poly2.from_bits(bits), n), bits)
    a, b = 0b1101011, 0b1011
    q, r = poly2.divmod2(a, b)
    assert poly2.mul(q, b) ^ r == a and poly2.degree(r) < poly2.degree(b)
    assert poly2.to_str(0b1011) == "x^3 + x + 1"
