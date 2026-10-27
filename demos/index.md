# Interactive demos: from parity bits to DVB-S2

These notebooks teach the coding theory behind the thesis, from the simplest
error-correcting code to the complete DVB-S2 transmitter, receiver and their
performance. They run **in your browser**: Python is executed by WebAssembly
(Pyodide), so the first one takes a few seconds to load and nothing needs to be
installed. Every slider and switch recomputes the results live.

| # | Notebook | What you can play with |
|---|---|---|
| 1 | [Parity and Hamming codes](demos/01_parity_and_hamming/) | send text through a noisy channel; flip bits on the Hamming (7,4) Venn diagram and watch the syndrome point at them |
| 2 | [Finite fields](demos/02_finite_fields/) | GF(*p*) tables; build GF(2<sup>m</sup>) with a shift register, step by step; primitive polynomials, logarithms, minimal polynomials |
| 3 | [Cyclic codes and LFSRs](demos/03_cyclic_codes/) | polynomial long division over GF(2); the LFSR encoder clock by clock; n-clock vs k-clock encoders |
| 4 | [BCH codes](demos/04_bch_codes/) | design a *t*-error-correcting BCH code; inject errors; syndromes, Berlekamp–Massey and Chien search |
| 5 | [The parallel BCH encoder](demos/05_parallel_bch/) | the thesis core: the state-space model, A<sup>p</sup> and B<sub>p</sub>, *p* bits per clock, one 192-bit datapath for *t* = 12, 10, 8 |
| 6 | [LDPC codes](demos/06_ldpc_basics/) | Tanner graphs; peeling, bit flipping and belief propagation, iteration by iteration |
| 7 | [The DVB-S2 chain](demos/07_dvbs2_chain/) | MODCODs, the IRA parity-check matrix, APSK constellations and LLRs, PLFRAME anatomy, live end-to-end frames |
| 8 | [BER explorer](demos/08_ber_explorer/) | simulated FER/BER waterfalls for every MODCOD against the standard's thresholds and the capacity limits |
| 9 | [Designing the LDPC decoder](demos/09_ldpc_decoder/) | the 360 × 360 circulants hidden in the DVB-S2 matrix; min-sum and its corrections; layered decoding in float and bit-true fixed point; an architecture calculator for throughput, latency and memory |

The notebooks are [marimo](https://marimo.io) files in
[`demos/`](https://github.com/epacces/DVB-S2-Master-Thesis/tree/master/demos) and use
the `dvbs2` Python package in
[`sim/`](https://github.com/epacces/DVB-S2-Master-Thesis/tree/master/sim). To run them
locally, with full speed and editable code:

```bash
cd sim && python -m venv .venv && .venv/bin/pip install -e '.[fast,demos]'
.venv/bin/marimo edit ../demos/01_parity_and_hamming.py
```
