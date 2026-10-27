# BCH-LDPC Concatenated Coding and High Order Modulations for Satellite Transmitters

![Status](https://img.shields.io/badge/Status-Archived-red)
![Standard](https://img.shields.io/badge/Standard-DVB--S2-blue)
![Platform](https://img.shields.io/badge/Platform-Altera%20Stratix%20II-orange)

Master's Thesis of **Eriprando Pacces** (Politecnico di Torino, July 2008), carried out at **Thales Alenia Space Italia** (L'Aquila) under the supervision of prof. Roberto Garello and ing. Domenico Giancristofaro.

The thesis contributes to the design of an on-board DVB-S2 satellite transmitter. Its core result is a **parallel (8-bit) BCH encoder** for the outer code of the DVB-S2 BCH-LDPC concatenated FEC, derived from a state-space model of the serial LFSR encoder, plus a C simulation package used to validate the VHDL implementation and preliminary lab measurements of the transmitter on an Altera Stratix II FPGA board.

The body of the thesis is in English; the abstract, acknowledgements and the extended summary (*Riassunto*) are in Italian.

## 📖 Read the thesis

- **Website:** <https://epacces.github.io/DVB-S2-Master-Thesis/>, one page per chapter with rendered equations.
- **Markdown:** [`markdown/`](markdown/README.md), the same chapters, readable directly on GitHub.
- **Interactive demos:** <https://epacces.github.io/DVB-S2-Master-Thesis/demos.html>, nine notebooks from Hamming codes to the full DVB-S2 chain and the LDPC decoder design that run in the browser ([`demos/`](demos)).
- **Simulator:** [`sim/`](sim/README.md), the `dvbs2` Python package and `dvbs2sim` command-line tool.
- **PDF:** [`TESI_FINALE.pdf`](TESI_FINALE.pdf) is the final version and the reference text. [`Ultima_versione.pdf`](Ultima_versione.pdf) and [`Tesi_05-07-08.pdf`](Tesi_05-07-08.pdf) are earlier drafts.

The Markdown is generated from the LaTeX sources, and its figure, table and equation numbers match the PDF. The diagrams that were drawn in TikZ are images cut from the PDF ([`figures/`](figures)). The English text was proofread in 2026 (grammar, spelling and word choice only; the technical content is unchanged), and `TESI_FINALE.pdf` was rebuilt from the corrected sources. See [Rebuilding the PDF, the Markdown and the website](#-rebuilding-the-pdf-the-markdown-and-the-website).

## 🗂️ Contents of the thesis

| Chapter | LaTeX source |
|---|---|
| Riassunto (Italian extended summary) | `riassunto.tex` |
| 1. Applications and Features of Satellite Communications | `cap1.tex` |
| 2. DVB-S2 MODEM Concepts and Architecture | `cap2.tex` |
| 3. BCH Encoding Algorithms for DVB-S2 Digital Transmissions | `cap3.tex` |
| 4. Hardware Implementation of BCH Encoder | `cap4.tex` |
| 5. Software Package for VHDL Validation | `cap5.tex` |
| 6. Preliminary Laboratory Test of DVB-S2 TX Section | `cap6.tex` |
| 7. LDPC Decoder Design (2026 addendum) | `ldpcdec.tex` |
| Conclusions | `conclusioni.tex` |
| Appendices: Galois (or Finite) Fields, Cyclic Codes | `Basic.tex` |
| Front matter (abstract, acknowledgements) | `preliminari.tex` |

## 📐 The parallel BCH encoder

A serial LFSR encoder processes one bit per clock, so 1 Gbit/s would need a 1 GHz clock. Writing the LFSR as a linear system

$$\mathbf{x}(i+1) = \mathbf{A}\,\mathbf{x}(i) + \mathbf{b}\,u(i)$$

and applying it $p$ times gives the parallel form

$$\mathbf{x}(i+p) = \mathbf{A}^p\,\mathbf{x}(i) + \mathbf{B}_p\,\mathbf{u}_p(i)$$

which processes $p = 8$ bits per clock (1 Gbit/s at 125 MHz). The regular structure of $\mathbf{A}^p$ leads to a hardware architecture with a 192-flip-flop register and 192 input and 192 output combinational networks (8-input XORs gated by coefficients stored in LUTs). By disabling the first 32 or 64 network pairs, the same hardware serves all DVB-S2 BCH codes ($t = 12, 10, 8$), so it can switch on a frame-by-frame basis (ACM).

## 🛰️ Simulator and interactive demos

The 2008 C code covered only the BCH encoder and decoder. In 2026 it was rewritten and extended in Python ([`sim/`](sim/README.md)):

- **Coding theory library.** GF(2^m) arithmetic, Hamming, cyclic and BCH codes (Berlekamp–Massey, Chien search) and the thesis' state-space **p-parallel BCH encoder**, which gives A^p and B_p for any p. The library reproduces the original C functions bit for bit, and the tests check it against line-by-line ports of `main.c`, `gfield.c` and `berlmass.c`.
- **Full DVB-S2 physical layer.** All 28 MODCODs with normal and short frames, with or without pilots: BBFRAME and scrambling, BCH + LDPC (all 21 codes of the standard), bit interleaver, QPSK/8PSK/16APSK/32APSK, PLFRAME, AWGN, soft demapping and a numba-compiled layered LDPC decoder. Synchronization is ideal.
- **Monte Carlo BER/FER** across multiple processes, with the results for every MODCOD in [`sim/results/`](sim/results).
- **LDPC decoder design.** The quasi-cyclic (360 × 360 circulant) view of the DVB-S2 codes, a bit-true fixed-point model of a 360-parallel layered decoder and a cycle/memory/throughput model of its architecture. The study in [`sim/results/ldpc_study/`](sim/results/ldpc_study) is the basis of the added chapter *LDPC Decoder Design* (`ldpcdec.tex`).

```bash
cd sim && python -m venv .venv && .venv/bin/pip install -e '.[fast,dev]'
.venv/bin/dvbs2sim ber --modcod 8PSK-3/5 --esn0 5.0:0.1:5.8 --plot 8psk35.png
```

The [interactive demos](demos/index.md) are [marimo](https://marimo.io) notebooks. They are published on the website as WebAssembly pages, and they also run locally with `marimo edit demos/01_parity_and_hamming.py`.

## 📂 Repository structure

Everything lives in the repository root, as it was in the original LaTeX working folder:

```text
.
├── master.tex               # Main LaTeX file (toptesi class); includes the files below
├── preliminari.tex          # Abstract and acknowledgements (Italian)
├── riassunto.tex            # Extended summary (Italian)
├── cap1.tex … cap6.tex      # Chapters 1–6
├── ldpcdec.tex              # Chapter 7, LDPC Decoder Design (added in 2026)
├── conclusioni.tex          # Conclusions
├── Basic.tex                # Appendices: Galois fields, cyclic codes
├── bibliografy.tex, thesis.bib
├── mymacros.sty, macros.sty, signalflowdiagram.sty, gnuplot-lua-tikz.sty, toptesi.cfg
├── *.jpg, *.eps             # Figures: block diagrams, constellations, VSA scatter plots and spectra
├── schemi/                  # Extra diagrams (SVG/EPS sources, Interface.ppt)
├── TESI_FINALE.pdf          # Final thesis PDF (plus earlier drafts)
├── markdown/                # Thesis as Markdown, one file per chapter (generated, do not edit)
├── figures/                 # TikZ diagrams cropped from TESI_FINALE.pdf; ldpc-*.png from sim/tools/ldpc_figures.py
├── tools/                   # LaTeX → Markdown converter, website and demo builders
├── sim/                     # dvbs2 Python package: codes, DVB-S2 PHY simulator, tests, results
├── demos/                   # marimo notebooks (interactive demos, exported to the website)
├── .github/workflows/       # Publishes the website to GitHub Pages on every push
├── main.c                   # C simulation package: driver for the BCH encoder/decoder tests
├── serenc.c, serial.c       # Serial (LFSR) BCH encoder models
├── ParEncn.c, parnclk.c, parkclk.c   # Parallel (p = 8) BCH encoder models
├── gfield.c                 # GF(2^m) power/index table generation
├── errdet.c                 # Syndrome computation / error detection
├── berlmass.c               # Berlekamp–Massey BCH decoder
├── comb1.c, comb2.c         # Combinational-network snippets (also listed in the thesis)
└── Copar.xls                # Spreadsheet of BCH/LDPC block sizes and encoding timing per code rate
```

The repository also contains LaTeX build output (`.aux`, `.log`, `.dvi`, …) and a Windows build of gnuplot (`gnuplot.exe`, `gnuplot-win.zip`) used to produce the plots. They were committed with the original import and are not needed to read the thesis.

### Notes on the C code

The simulation code was written in 2008 for Borland/Turbo C++ on Windows: it uses `<conio.h>`, `<dos.h>` and the pre-standard `<iostream.h>`/`<fstream.h>` headers. It will not compile with a modern GCC/Clang without small changes. The files are kept as they were because chapter 5 prints them. Their Python counterparts in [`sim/`](sim/README.md) run on any platform, and `dvbs2sim bch-matrices` generates the `Matrices/*.txt` files that `load_matrices()` expects. `main.c` is the driver; the other `.c` files contain the functions it uses (encoders, Galois field tables, error detection, Berlekamp–Massey decoding).

There is no VHDL in this repository. The hardware design was developed at TAS-I and is not part of this archive.

## 🧪 Lab results

Chapter 6 reports preliminary tests of the full TX section on an Altera Stratix II EP2S180 prototyping board, measured with an Agilent wideband VSA and oscilloscope (QPSK/8PSK/16APSK/64APSK at 2 and 30 MBaud). For example, at 30 MBaud 8PSK the DAC pre-compensation filter brings the EVM from 9% down to 4%. The scatter plots and spectra are the `*APSK*.jpg`, `8PSK*.jpg`, `IQ*.jpg` and `Spectr*.jpg` images.

## 🔧 Rebuilding the PDF, the Markdown and the website

Requires Python 3, [pandoc](https://pandoc.org) 3.x and, for the PDF, [Tectonic](https://tectonic-typesetting.github.io) (`brew install tectonic`).

```sh
python3 tools/build_pdf.py --install  # LaTeX → TESI_FINALE.pdf
python3 tools/tex2md.py               # LaTeX → markdown/ (one file per chapter)
python3 tools/build_site.py           # markdown/ → _site/ (the website, for a local preview)
python3 tools/build_demos.py          # demos/ → _site/demos/ (needs: pip install marimo uv build)
```

`tools/build_pdf.py` compiles `master.tex` from a patched UTF-8 copy in `tools/build/pdf/`, because the 2008 sources target an older `toptesi` class and `latex`. The sources themselves are left unchanged. The title page layout and the line breaks differ slightly from the 2008 PDF.

`tools/tex2md.py` reads the cp1252-encoded LaTeX, expands the thesis macros (`\vet`, `\ped`, `\unit`, …), swaps the TikZ figures for the PNGs in `figures/` and runs pandoc with `tools/number.lua`, which numbers chapters, figures, tables and equations the way the PDF does. Edit the `.tex` files and rerun it rather than editing `markdown/` by hand.

The website is rebuilt and published by GitHub Actions ([`.github/workflows/pages.yml`](.github/workflows/pages.yml)) on every push to `master`. To preview it locally, run `python3 -m http.server -d _site` and open <http://localhost:8000>.

## 📝 Citation

```bibtex
@mastersthesis{pacces2008dvbs2,
  author = {Eriprando Pacces},
  title  = {{BCH-LDPC} Concatenated Coding and High Order Modulations for Satellite Transmitters},
  school = {Politecnico di Torino},
  year   = {2008},
  note   = {Developed at Thales Alenia Space Italia, L'Aquila}
}
```
