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
- **PDF:** [`TESI_FINALE.pdf`](TESI_FINALE.pdf) is the final version and the reference text. [`Ultima_versione.pdf`](Ultima_versione.pdf) and [`Tesi_05-07-08.pdf`](Tesi_05-07-08.pdf) are earlier drafts.

The Markdown is generated from the LaTeX sources, and its figure, table and equation numbers match the PDF. The diagrams that were drawn in TikZ are images cut from the PDF ([`figures/`](figures)). See [Rebuilding the Markdown and the website](#-rebuilding-the-markdown-and-the-website).

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
| Conclusions | `conclusioni.tex` |
| Appendices: Galois (or Finite) Fields, Cyclic Codes | `Basic.tex` |
| Front matter (abstract, acknowledgements) | `preliminari.tex` |

## 📐 The parallel BCH encoder

A serial LFSR encoder processes one bit per clock, so 1 Gbit/s would need a 1 GHz clock. Writing the LFSR as a linear system

$$\mathbf{x}(i+1) = \mathbf{A}\,\mathbf{x}(i) + \mathbf{b}\,u(i)$$

and applying it $p$ times gives the parallel form

$$\mathbf{x}(i+p) = \mathbf{A}^p\,\mathbf{x}(i) + \mathbf{B}_p\,\mathbf{u}_p(i)$$

which processes $p = 8$ bits per clock (1 Gbit/s at 125 MHz). The regular structure of $\mathbf{A}^p$ leads to a hardware architecture with a 192-flip-flop register and 192 input and 192 output combinational networks (8-input XORs gated by coefficients stored in LUTs). By disabling the first 32 or 64 network pairs, the same hardware serves all DVB-S2 BCH codes ($t = 12, 10, 8$), so it can switch on a frame-by-frame basis (ACM).

## 📂 Repository structure

Everything lives in the repository root, as it was in the original LaTeX working folder:

```text
.
├── master.tex               # Main LaTeX file (toptesi class); includes the files below
├── preliminari.tex          # Abstract and acknowledgements (Italian)
├── riassunto.tex            # Extended summary (Italian)
├── cap1.tex … cap6.tex      # Chapters 1–6
├── conclusioni.tex          # Conclusions
├── Basic.tex                # Appendices: Galois fields, cyclic codes
├── bibliografy.tex, thesis.bib
├── mymacros.sty, macros.sty, signalflowdiagram.sty, gnuplot-lua-tikz.sty, toptesi.cfg
├── *.jpg, *.eps             # Figures: block diagrams, constellations, VSA scatter plots and spectra
├── schemi/                  # Extra diagrams (SVG/EPS sources, Interface.ppt)
├── TESI_FINALE.pdf          # Final thesis PDF (plus earlier drafts)
├── markdown/                # Thesis as Markdown, one file per chapter (generated, do not edit)
├── figures/                 # TikZ diagrams as PNGs cropped from TESI_FINALE.pdf
├── tools/                   # LaTeX → Markdown converter and website builder
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

The simulation code was written in 2008 for Borland/Turbo C++ on Windows: it uses `<conio.h>`, `<dos.h>` and the pre-standard `<iostream.h>`/`<fstream.h>` headers. It will not compile with a modern GCC/Clang without small changes. `main.c` is the driver; the other `.c` files contain the functions it uses (encoders, Galois field tables, error detection, Berlekamp–Massey decoding).

There is no VHDL in this repository. The hardware design was developed at TAS-I and is not part of this archive.

## 🧪 Lab results

Chapter 6 reports preliminary tests of the full TX section on an Altera Stratix II EP2S180 prototyping board, measured with an Agilent wideband VSA and oscilloscope (QPSK/8PSK/16APSK/64APSK at 2 and 30 MBaud). For example, at 30 MBaud 8PSK the DAC pre-compensation filter brings the EVM from 9% down to 4%. The scatter plots and spectra are the `*APSK*.jpg`, `8PSK*.jpg`, `IQ*.jpg` and `Spectr*.jpg` images.

## 🔧 Rebuilding the Markdown and the website

Requires [pandoc](https://pandoc.org) 3.x and Python 3.

```sh
python3 tools/tex2md.py       # LaTeX → markdown/ (one file per chapter)
python3 tools/build_site.py   # markdown/ → _site/ (the website, for a local preview)
```

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
