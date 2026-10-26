import numpy as np
import pytest

from dvbs2.phy import ModCod, Receiver, Transmitter, all_modcods
from dvbs2.phy.bbframe import BBHeader, bb_scramble, crc8
from dvbs2.phy.channel import awgn
from dvbs2.phy.modulation import Mapper, constellation, deinterleave, interleave, label_bits
from dvbs2.phy.plframe import decode_pls, pl_scrambling_sequence, pls_code
from dvbs2.sim.montecarlo import SimConfig, run_point

ALL = all_modcods("normal") + all_modcods("short")


def test_frame_sizes_and_efficiency():
    assert ModCod("QPSK", "1/2").plframe_symbols == 32490
    assert ModCod("QPSK", "1/2", pilots=True).plframe_symbols == 33282
    assert ModCod("8PSK", "3/5").plframe_symbols == 21690
    assert ModCod("32APSK", "8/9", "short").plframe_symbols == 3330
    # Table 13 spectral efficiencies
    assert ModCod("QPSK", "1/4").efficiency == pytest.approx(0.490243, abs=1e-6)
    assert ModCod("8PSK", "3/5").efficiency == pytest.approx(1.779991, abs=1e-6)
    assert ModCod("32APSK", "9/10").efficiency == pytest.approx(4.453027, abs=1e-6)
    assert len(all_modcods()) == 28
    assert ModCod.parse("8psk_3_5") == ModCod("8PSK", "3/5")


@pytest.mark.parametrize("mod", ["QPSK", "8PSK", "16APSK", "32APSK"])
def test_constellations_unit_energy(mod):
    pts = constellation(mod)
    assert np.mean(np.abs(pts) ** 2) == pytest.approx(1.0)
    assert len(set(np.round(pts, 9))) == pts.size


@pytest.mark.parametrize("mod", ["QPSK", "8PSK"])
def test_psk_mappings_are_gray(mod):
    pts = constellation(mod)
    order = np.argsort(np.angle(pts))
    labels = label_bits(int(np.log2(pts.size)))
    for a, b in zip(order, np.roll(order, -1)):
        assert np.sum(labels[a] != labels[b]) == 1


@pytest.mark.parametrize("mc", [ModCod("8PSK", "3/5"), ModCod("8PSK", "2/3"), ModCod("16APSK", "3/4", "short"),
                                ModCod("32APSK", "4/5")], ids=str)
def test_interleaver_roundtrip(mc):
    x = np.arange(mc.n_ldpc)
    y = interleave(x, mc)
    assert np.array_equal(deinterleave(y, mc), x)
    rows = mc.n_ldpc // mc.bits_per_symbol
    first = [0, rows, 2 * rows] if mc.rate != "3/5" else [2 * rows, rows, 0]
    if mc.modulation == "8PSK":
        assert list(y[:3]) == first


def test_bbheader_and_scrambler():
    hdr = BBHeader(dfl=32128)
    bits = hdr.to_bits()
    assert bits.size == 80 and crc8(bits[:72]) == int("".join(map(str, bits[72:])), 2)
    parsed, ok = BBHeader.from_bits(bits)
    assert ok and parsed.dfl == 32128
    bits[5] ^= 1
    assert not BBHeader.from_bits(bits)[1]
    x = np.random.default_rng(0).integers(0, 2, 1000, dtype=np.uint8)
    assert np.array_equal(bb_scramble(bb_scramble(x)), x)


def test_pls_codes_and_scrambler():
    codes = {tuple(pls_code(m, s, p)) for m in range(32) for s in (0, 1) for p in (0, 1)}
    assert len(codes) == 128
    seq = pl_scrambling_sequence(1000)
    assert set(np.round(seq, 9)) <= {1, 1j, -1, -1j}


@pytest.mark.parametrize("mc", ALL + [ModCod("QPSK", "1/2", pilots=True), ModCod("32APSK", "3/4", "short", True)],
                         ids=str)
def test_noiseless_link_is_bit_exact(mc):
    rng = np.random.default_rng(mc.id)
    tx, rx = Transmitter(mc), Receiver(mc)
    f = tx.random_frame(rng)
    assert f.plframe.size == mc.plframe_symbols
    r = rx.receive(f.plframe, 1e-3)
    assert r.header_ok and np.array_equal(r.data, f.data)
    assert r.pls == (mc.id, mc.frame == "short", mc.pilots)


def test_pls_decoding_survives_noise():
    mc = ModCod("16APSK", "8/9", pilots=True)
    rng = np.random.default_rng(3)
    f = Transmitter(mc).random_frame(rng)
    y, _ = awgn(f.plframe[:90], -3.0, rng)
    assert decode_pls(y[26:]) == (mc.id, False, True)


def test_maxlog_close_to_exact():
    mp = Mapper(ModCod("16APSK", "3/4"))
    rng = np.random.default_rng(4)
    y, n0 = awgn(mp.map(rng.integers(0, 2, 4000)), 12.0, rng)
    exact, maxlog = mp.demap(y, n0), mp.demap(y, n0, "maxlog")
    assert np.mean(np.sign(exact) == np.sign(maxlog)) > 0.999


def test_monte_carlo_point():
    mc = ModCod("QPSK", "1/2", "short")
    cfg = SimConfig(min_frame_errors=5, max_frames=16, batch=8, workers=1)
    good = run_point(mc, 2.0, cfg)
    assert good.frames == 16 and good.frame_errors == 0
    bad = run_point(mc, -1.0, cfg)
    assert bad.frame_errors >= 5 and bad.ber > 0.01


@pytest.mark.slow
@pytest.mark.parametrize("label", ["QPSK-1/2", "8PSK-3/5"])
def test_qef_threshold(label):
    """Normal frames decode with FER < 1e-2 at 0.3 dB above the EN 302 307 QEF Es/N0."""
    mc = ModCod.parse(label)
    cfg = SimConfig(min_frame_errors=3, max_frames=200, batch=8, workers=4)
    assert run_point(mc, mc.qef_esn0 + 0.3, cfg).fer < 1e-2
