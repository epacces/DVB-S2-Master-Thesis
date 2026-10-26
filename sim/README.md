# dvbs2: finite fields, BCH/LDPC codes and a DVB-S2 simulator

A Python rewrite and extension of the C simulation package of the thesis.
It covers everything from GF(2^m) arithmetic to an end-to-end DVB-S2
physical-layer link with BER/FER curves. It also powers the interactive
demos in [`../demos`](../demos).

## Install

```bash
cd sim
python -m venv .venv
.venv/bin/pip install -e '.[fast,dev]'     # fast = numba-compiled LDPC decoder
.venv/bin/pytest                           # ~150 tests, a few seconds
.venv/bin/pytest -m slow                   # QEF-threshold checks (about 20 s on 8 cores)
```

Without numba, the package falls back to pure numpy. That is how it runs in
the browser. Set `DVBS2_NO_NUMBA=1` to force that path.

## What is inside

| Module | Contents |
|---|---|
| `dvbs2.gf` | `GF2m` (log/antilog tables, vectorised arithmetic, cyclotomic cosets, minimal polynomials), primitivity tests, `GFp` |
| `dvbs2.poly2` | binary polynomials as Python ints |
| `dvbs2.codes.hamming` | Hamming and extended (SECDED) codes |
| `dvbs2.codes.cyclic` | systematic cyclic codes; clock-by-clock LFSR division and encoder traces |
| `dvbs2.codes.bch` | BCH design, table-driven encoder, syndromes, Berlekamp–Massey (traceable), Chien search; `dvbs2_bch(rate, frame)` |
| `dvbs2.codes.bch_parallel` | the thesis' state-space p-parallel encoder: A, A^p, B_p; n-clock and k-clock modes; shared 192-bit register |
| `dvbs2.codes.ldpc` | DVB-S2 IRA LDPC codes (21 tables), accumulator encoder, layered sum-product / normalized / offset min-sum |
| `dvbs2.phy` | MODCODs, BBFRAME (header, CRC-8, BB scrambler), FEC, bit interleaver, QPSK/8PSK/16APSK/32APSK, exact and max-log demappers, PLFRAME (SOF, PLS code, pilots, Gold scrambling), AWGN, capacity limits |
| `dvbs2.sim` | Monte Carlo engine (multiprocess, reproducible seeds), JSON results, plots |
| `dvbs2.legacy` | line-by-line ports of the 2008 C functions, used by the tests to prove equivalence |

## Command line

```bash
dvbs2sim info                                    # the 28 MODCODs: K_bch, N_bch, t, slots, efficiency, QEF Es/N0
dvbs2sim ber --modcod QPSK-1/2 --esn0 0.6:0.1:1.2 --plot qpsk12.png
dvbs2sim ber --modcod 8PSK-3/5 --frame short --pilots --esn0 5:0.2:6.4 --decoder nms --workers 8
dvbs2sim plot results/*.json --metric ber --x ebn0 -o all.png
dvbs2sim bch-matrices -o Matrices                # the A^p / B_p files main.c expects
python tools/generate_results.py                 # regenerate results/ (all MODCODs, normal and short)
```

## Python API

```python
import numpy as np
from dvbs2.phy import ModCod, Transmitter, Receiver
from dvbs2.phy.channel import awgn

mc = ModCod.parse("16APSK-3/4", frame="normal", pilots=True)
tx, rx = Transmitter(mc), Receiver(mc)
rng = np.random.default_rng(1)
frame = tx.random_frame(rng)                 # .data .bbframe .fecframe .symbols .plframe
y, n0 = awgn(frame.plframe, esn0_db=10.4, rng=rng)
out = rx.receive(y, n0)
print(out.header_ok, np.array_equal(out.data, frame.data), out.ldpc_iterations)
```

```python
from dvbs2.codes.bch import dvbs2_bch
code = dvbs2_bch("1/2")                      # BCH(32400, 32208), t = 12 over GF(2^16)
cw = code.encode(np.random.default_rng(0).integers(0, 2, code.k))
rx_word = cw.copy(); rx_word[[5, 900, 31000]] ^= 1
trace = []
res = code.decode(rx_word, trace)            # trace: Berlekamp–Massey steps
```

## Scope and validation

* **Ideal synchronization.** The receiver knows frame timing, carrier phase and
  frequency. There is no RRC filtering, phase noise or HPA model.
* **BCH.** Generator polynomials are computed from minimal polynomials and match
  the `gen12/gen10/gen8` arrays in `main.c` bit for bit. The serial, n-clock and
  k-clock parallel encoders agree with each other and with ports of the C code.
* **LDPC.** The address tables of EN 302 307-1 Annexes B and C were taken from
  [AFF3CT](https://github.com/aff3ct/aff3ct) (MIT, see `src/dvbs2/data/ldpc/SOURCE.md`).
  Every code passes H·cᵀ = 0, and its variable-degree profile matches Tables 7a/7b.
* **Framing.** PLFRAME lengths and spectral efficiencies match Table 13 of the standard.
  The constellation bit labels were transcribed from the standard's figures. Check
  them against an official copy of EN 302 307-1 before relying on bit-exact
  interoperability with real equipment.
* **Performance.** The simulated waterfalls use sum-product decoding with 50 iterations,
  and every point runs up to 50 frame errors or 600 frames. For 24 of the 28 normal-frame
  MODCODs they cross FER = 10⁻² 0.1–0.2 dB *below* the QEF Es/N0 of EN 302 307
  Table 13. The difference is expected, since the table targets PER = 10⁻⁷ further down the
  waterfall. QPSK 1/4, 1/3 and 2/5 cross 0.3–0.6 dB below, where the standard's low-rate
  figures are known to be conservative. The agreement across QPSK, 8PSK, 16APSK and
  32APSK is also an end-to-end check of the bit interleaver and the constellation
  labels: a wrong mapping would cost much more than a tenth of a dB.
