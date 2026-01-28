# BCH-LDPC Concatenated Coding and High Order Modulations for Satellite Transmitters

![Status](https://img.shields.io/badge/Status-Archived-red)
![Standard](https://img.shields.io/badge/Standard-DVB--S2-blue)
![Platform](https://img.shields.io/badge/Platform-Altera%20Stratix%20II-orange)
![License](https://img.shields.io/badge/License-MIT-green)

> **Note:** This repository contains the Master's Thesis work of **Eriprando Pacces** (Politecnico di Torino, 2008), developed in collaboration with **Thales Alenia Space**. It implements a high-speed DVB-S2 satellite transmitter section.

## 📖 Table of Contents
- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [The Parallel BCH Encoder](#-the-parallel-bch-encoder)
- [Repository Structure](#-repository-structure)
- [Experimental Results](#-experimental-results)
- [Citation](#-citation)

---

## 🛰️ Overview

This project delivers a hardware implementation of a **DVB-S2 compliant digital transmitter** capable of achieving data throughputs up to **1 Gbps**. 

The design bridges the gap between the theoretical Shannon-limit performance of **LDPC codes** and the practical constraints of FPGA hardware. By implementing a novel **parallel BCH encoder** and supporting **Adaptive Coding and Modulation (ACM)**, the system is optimized for next-generation satellite broadband and Earth observation missions.

---

## 🚀 Key Features

* **Concatenated Coding Scheme:**
    * **Inner Code:** Low-Density Parity-Check (LDPC) for performance near the Shannon limit.
    * **Outer Code:** BCH (Bose-Chaudhuri-Hocquenghem) to eliminate error floors.
* **High-Order Modulations:** Full support for **QPSK**, **8PSK**, **16APSK**, and **32APSK**.
* **High-Speed Architecture:** Custom **8-bit parallel BCH encoder** replacing standard serial LFSRs to meet Gbps requirements.
* **Adaptive Coding and Modulation (ACM):** Frame-by-frame switching of coding rates and modulation to handle variable link conditions (e.g., rain fading).
* **Signal Pre-distortion:** Digital pre-compensation filters to minimize Error Vector Magnitude (EVM) at high symbol rates (30 MBaud).

---

## ⚙️ System Architecture

The transmission chain is implemented on an **Altera Stratix II (EP2S180)** FPGA. The data flow follows the DVB-S2 FEC Frame structure:

1.  **Mode Adapter:** Handles stream interfacing and ACM control.
2.  **BCH Encoder:** Outer error correction (programmable $t=8, 10, 12$).
3.  **LDPC Encoder:** Inner error correction (code rates 1/4 to 9/10).
4.  **Bit Interleaver:** Decorrelates burst errors for 8PSK/16APSK/32APSK.
5.  **Mapper:** Maps bits to complex constellation symbols.
6.  **Physical Layer Framer:** Adds Pilot blocks and PLHeaders.
7.  **Baseband Filter:** Square Root Raised Cosine (SRRC) filter.

---

## 📐 The Parallel BCH Encoder

A core contribution of this work is the derivation of a parallel architecture to overcome the clock speed limitations of serial Linear Feedback Shift Registers (LFSR).

**The Challenge:**
A standard LFSR processes 1 bit per clock. For 1 Gbps throughput, the FPGA would need to run at 1 GHz, which is infeasible.

**The Solution:**
We derived a state-space transformation to process **$p=8$ bits** per clock cycle. The state evolution equation is transformed from:

$$S_{n+1} = A \cdot S_n + B \cdot u_n$$

To the parallel form:

$$S_{n+p} = A^p \cdot S_n + B_p \cdot U_p$$

Where:
* $A^p$ is the look-ahead transition matrix.
* $B_p$ is the parallel input matrix.
* $U_p$ is the vector of 8 input bits.

This allows the system to sustain **1 Gbps** throughput with a clock frequency of only **125 MHz**.

---

## 📂 Repository Structure

```text
├── docs/
│   ├── thesis_full.pdf        # Full Master's Thesis text
│   └── diagrams/              # Block diagrams and schematics
├── src/
│   ├── rtl/                   # VHDL source code (Quartus II projects)
│   │   ├── bch_parallel/      # The 8-bit parallel encoder core
│   │   └── mapper/            # Constellation mapping logic
│   ├── sim/                   # C++ Simulation Package
│   │   ├── berlekamp_massey/  # BCH decoding algorithm validation
│   │   └── ldpc_model/        # Floating point LDPC verification
│   └── scripts/               # MATLAB scripts for LUT generation
├── results/
│   ├── evm_data/              # Excel sheets with lab measurements
│   └── constellations/        # VSA captured screenshots
└── README.md
