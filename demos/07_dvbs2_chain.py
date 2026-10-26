import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="7 · The DVB-S2 transmission chain")


@app.cell
async def _():
    # Setup: in the browser (Pyodide) install the dvbs2 wheel published next to this page.
    import sys

    import marimo as mo

    if "pyodide" in sys.modules:
        import micropip

        _loc = str(mo.notebook_location())
        _loc = _loc.rsplit("/", 1)[0] if _loc.endswith(".html") else _loc
        await micropip.install(_loc + "/dvbs2-1.0.0-py3-none-any.whl")
    import matplotlib.pyplot as plt
    import numpy as np

    from dvbs2.codes.ldpc import dvbs2_ldpc
    from dvbs2.phy import ModCod, Receiver, Transmitter, all_modcods
    from dvbs2.phy.channel import awgn
    from dvbs2.phy.modcod import PILOT_BLOCK, PILOT_PERIOD, SLOT
    from dvbs2.phy.modulation import Mapper, constellation, label_bits
    return (
        Mapper,
        ModCod,
        PILOT_BLOCK,
        PILOT_PERIOD,
        Receiver,
        SLOT,
        Transmitter,
        all_modcods,
        awgn,
        constellation,
        dvbs2_ldpc,
        label_bits,
        mo,
        np,
        plt,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # 7 · The DVB-S2 transmission chain

    DVB-S2 (ETSI EN 302 307-1) puts everything from the earlier notebooks together:

    ```
    data ─► BBFRAME ─► BB scrambler ─► BCH (outer) ─► LDPC (inner) ─► bit interleaver
         ─► QPSK / 8PSK / 16APSK / 32APSK mapper ─► PLFRAME (header, pilots, scrambling) ─► channel
    ```

    A **MODCOD** (modulation + code rate) fixes every block's parameters. There are 28
    of them, from QPSK 1/4 (works below 0 dB SNR, 0.49 bit/symbol) to 32APSK 9/10
    (needs 16 dB, 4.45 bit/symbol). With adaptive coding and modulation (ACM) the
    transmitter can change the MODCOD on every frame to follow the weather.
    """)
    return


@app.cell
def _(mo):
    frame_sel = mo.ui.radio(["normal", "short"], value="normal", label="FECFRAME", inline=True)
    pilots_sel = mo.ui.checkbox(value=False, label="pilots")
    mo.hstack([frame_sel, pilots_sel], justify="start", gap=2)
    return frame_sel, pilots_sel


@app.cell
def _(all_modcods, frame_sel, mo):
    _labels = [m.label for m in all_modcods(frame_sel.value)]
    modcod_sel = mo.ui.dropdown(_labels, value="8PSK-3/5" if "8PSK-3/5" in _labels else _labels[0], label="MODCOD")
    modcod_sel
    return (modcod_sel,)


@app.cell
def _(ModCod, frame_sel, modcod_sel, pilots_sel):
    mc = ModCod.parse(modcod_sel.value, frame_sel.value, pilots_sel.value)
    return (mc,)


@app.cell
def _(mc, mo):
    _q = mc.qef_esn0
    _rows = [
        ("PLS MODCOD field", mc.id, "5-bit code sent in the PLHEADER"),
        ("K<sub>bch</sub>", mc.k_bch, "BBFRAME bits (80-bit header + data field)"),
        ("N<sub>bch</sub> = K<sub>ldpc</sub>", mc.n_bch, f"after the BCH code ({mc.n_bch - mc.k_bch} parity bits)"),
        ("t", mc.t, "errors the BCH code corrects"),
        ("N<sub>ldpc</sub>", mc.n_ldpc, f"FECFRAME length (LDPC rate {mc.rate}, really {mc.n_bch / mc.n_ldpc:.4f})"),
        ("bits / symbol", mc.bits_per_symbol, mc.modulation),
        ("slots", mc.slots, "of 90 symbols each"),
        ("pilot blocks", mc.pilot_blocks, "36 symbols after every 16 slots" if mc.pilots else "pilots off"),
        ("PLFRAME symbols", mc.plframe_symbols, "90 header + slots + pilots"),
        ("spectral efficiency", f"{mc.efficiency:.4f}", "information bits per symbol"),
        ("QEF E<sub>s</sub>/N<sub>0</sub>", f"{_q:.2f} dB" if _q is not None else "–", "EN 302 307 Table 13 (normal frames, PER 10⁻⁷)"),
    ]
    mo.Html(
        "<table><tr><th>parameter</th><th>value</th><th></th></tr>"
        + "".join(f"<tr><td>{a}</td><td><b>{b}</b></td><td>{c}</td></tr>" for a, b, c in _rows)
        + "</table>"
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## The LDPC parity-check matrix

    Below is $\mathbf H$ for the selected rate, shrunk to a density map. On the left are the
    information columns, organised in groups of 360 by the Annex B/C address tables;
    on the right is the dual-diagonal **staircase** of the parity bits (notebook 6). The
    zoom shows the boundary between the two parts.
    """)
    return


@app.cell
def _(dvbs2_ldpc, mc, mo, np, plt):
    _code = dvbs2_ldpc(mc.rate, mc.frame)
    _coo = _code.H.tocoo()
    _img, _, _ = np.histogram2d(_coo.row, _coo.col, bins=[150, 300], range=[[0, _code.m], [0, _code.n]])
    _fig, (_a1, _a2) = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={"width_ratios": [2, 1]})
    _a1.imshow(_img > 0, aspect="auto", cmap="Greys", extent=[0, _code.n, _code.m, 0], interpolation="nearest")
    _a1.axvline(_code.k, color="#e45756", lw=1)
    _a1.set_title(f"H: {_code.m} × {_code.n}, {_code.H.nnz} ones")
    _a1.set_xlabel("bit (column)")
    _a1.set_ylabel("parity check (row)")
    _r0, _c0 = 0, _code.k - 40
    _sub = _code.H[_r0 : _r0 + 40, _c0 : _c0 + 80].toarray()
    _a2.imshow(_sub, cmap="Greys", extent=[_c0, _c0 + 80, _r0 + 40, _r0], interpolation="nearest")
    _a2.axvline(_code.k, color="#e45756", lw=1)
    _a2.set_title("zoom: information | parity")
    _fig.tight_layout()
    _deg = _code.degree_profile()
    mo.vstack(
        [
            _fig,
            mo.md(
                "Variable-node degrees (degree: number of bits): "
                + ", ".join(f"{d}: {n}" for d, n in sorted(_deg.items()))
                + ". A few high-degree bits converge early and help the others."
            ),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Constellations

    After the bit interleaver (column-wise write, row-wise read, so the bits of one
    symbol come from distant parts of the codeword), groups of
    $\log_2 M$ bits select a point. QPSK and 8PSK are Gray-mapped circles. 16APSK and
    32APSK use concentric rings (4+12 and 4+12+16 points). Rings suit a satellite's
    power amplifier, which compresses amplitudes more than it distorts phase. The
    ring ratio γ = R₂/R₁ is optimised per code rate.
    """)
    return


@app.cell
def _(mc, mo):
    if mc.modulation == "16APSK":
        g1 = mo.ui.slider(1.5, 5.0, step=0.05, value=mc.gamma, label="γ = R2/R1", show_value=True)
        g2 = None
        _ui = g1
    elif mc.modulation == "32APSK":
        g1 = mo.ui.slider(1.5, 4.0, step=0.05, value=mc.gamma[0], label="γ1 = R2/R1", show_value=True)
        g2 = mo.ui.slider(3.0, 7.0, step=0.05, value=mc.gamma[1], label="γ2 = R3/R1", show_value=True)
        _ui = mo.hstack([g1, g2], justify="start")
    else:
        g1 = g2 = None
        _ui = mo.md(f"*{mc.modulation} has no ring ratio.*")
    esn0_sc = mo.ui.slider(-3.0, 20.0, step=0.5, value=round(mc.qef_esn0 or 5.0), label="Es/N0 [dB] for the scatter", show_value=True)
    mo.vstack([_ui, esn0_sc])
    return esn0_sc, g1, g2


@app.cell
def _(Mapper, awgn, constellation, esn0_sc, g1, g2, label_bits, mc, mo, np, plt):
    _gamma = None if g1 is None else (g1.value if g2 is None else (g1.value, g2.value))
    _pts = constellation(mc.modulation, _gamma)
    _mapper = Mapper(mc)
    _mapper.points = _pts
    _m = mc.bits_per_symbol
    _labels = label_bits(_m)
    _rng = np.random.default_rng(5)
    _bits = _rng.integers(0, 2, 3000 * _m).astype(np.uint8)
    _y, _n0 = awgn(_mapper.map(_bits), esn0_sc.value, _rng)
    _llr = _mapper.demap(_y, _n0).reshape(-1, _m)
    _b = _bits.reshape(-1, _m)

    _fig, _axes = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1, 1.25]})
    _ax = _axes[0]
    _ax.scatter(_y.real, _y.imag, s=2, alpha=0.25, color="#9a9a9a")
    _ax.scatter(_pts.real, _pts.imag, s=30, color="#e45756", zorder=3)
    for _i, _p in enumerate(_pts):
        _ax.annotate("".join(map(str, _labels[_i])), (_p.real, _p.imag), textcoords="offset points", xytext=(0, 7),
                     ha="center", fontsize=7 if _m >= 5 else 8)
    _lim = 1.25 * np.abs(_pts).max() + 0.3
    _ax.set_xlim(-_lim, _lim)
    _ax.set_ylim(-_lim, _lim)
    _ax.set_aspect("equal")
    _ax.grid(alpha=0.3)
    _ax.set_title(f"{mc.modulation}, Es/N0 = {esn0_sc.value} dB")
    _ax2 = _axes[1]
    _bins = np.linspace(-40, 40, 81)
    for _j in range(_m):
        _signed = np.clip(_llr[:, _j] * np.where(_b[:, _j] == 0, 1, -1), -40, 40)
        _ax2.hist(_signed, bins=_bins, histtype="step", lw=1.5, label=f"bit {_j} (BER {np.mean(_signed < 0):.3f})")
    _ax2.axvline(0, color="k", lw=0.8)
    _ax2.set_xlabel("LLR × (±1): negative = wrong hard decision")
    _ax2.set_title("LLR per bit position")
    _ax2.legend(fontsize=8)
    _fig.tight_layout()
    mo.vstack(
        [
            _fig,
            mo.md(
                "The bit positions are **not equally protected**: in 8PSK and APSK some label bits "
                "switch between far-apart points and others between neighbours. The soft demapper "
                "gives each bit its own reliability, and the interleaver spreads the weak positions "
                "over the LDPC codeword. Together, demapper and decoder form *bit-interleaved coded "
                "modulation* (BICM)."
            ),
        ]
    )
    return


@app.cell
def _(PILOT_BLOCK, PILOT_PERIOD, SLOT, mc, mo):
    _W = 900
    _total = mc.plframe_symbols
    _sc = (_W - 20) / _total
    _x = 10
    _svg = [f'<svg viewBox="0 0 {_W} 120" width="100%" style="max-width:{_W}px;font-family:sans-serif">']
    _svg.append(f'<rect x="{_x}" y="30" width="{max(SLOT * _sc, 3):.2f}" height="40" fill="#e45756"/>')
    _x += SLOT * _sc
    for _s in range(mc.slots):
        _svg.append(
            f'<rect x="{_x:.2f}" y="30" width="{SLOT * _sc:.2f}" height="40" fill="{"#4c78a8" if _s % 2 else "#6f97c4"}"/>'
        )
        _x += SLOT * _sc
        if mc.pilots and (_s + 1) % PILOT_PERIOD == 0 and _s + 1 < mc.slots:
            _svg.append(f'<rect x="{_x:.2f}" y="22" width="{max(PILOT_BLOCK * _sc, 1.5):.2f}" height="56" fill="#f58518"/>')
            _x += PILOT_BLOCK * _sc
    _svg.append('<text x="10" y="18" font-size="12" fill="currentColor">PLHEADER (90 symbols, π/2-BPSK)</text>')
    _svg.append(
        f'<text x="10" y="98" font-size="12" fill="currentColor">{mc.slots} slots × 90 symbols'
        + (f" + {mc.pilot_blocks} pilot blocks × 36 (orange)" if mc.pilots else "")
        + f" = {_total} symbols</text>"
    )
    _svg.append("</svg>")
    mo.vstack(
        [
            mo.md(r"""
    ## The physical-layer frame

    Each FECFRAME becomes a **PLFRAME**. A 90-symbol header comes first: a 26-bit
    start-of-frame word plus the 64-bit PLS code, which carries the MODCOD, the frame
    size and the pilot flag. It is protected by a Reed–Muller code and sent in robust
    π/2-BPSK, so a receiver can always read it even when it cannot yet decode the
    payload. The payload follows in 90-symbol slots, optionally with known pilot
    symbols that help carrier recovery. Everything after the header is multiplied by
    a Gold-sequence scrambler that spreads the spectrum.
    """),
            mo.Html("".join(_svg)),
        ]
    )
    return


@app.cell
def _(mc, mo):
    _q = mc.qef_esn0 if mc.qef_esn0 is not None else 3.0
    run_esn0 = mo.ui.slider(round(_q - 3), round(_q + 3), step=0.1, value=round(_q + 0.5, 1), label="Es/N0 [dB]", show_value=True)
    run_n = mo.ui.slider(1, 5, value=2, label="frames", show_value=True)
    run_it = mo.ui.slider(5, 50, step=5, value=25, label="LDPC iterations", show_value=True)
    run_go = mo.ui.run_button(label="run the link")
    mo.vstack(
        [
            mo.md(
                "## End to end\n\nSimulate a few **short** frames (16200 bits) of "
                f"**{mc.modulation} {mc.rate}** through the whole chain over AWGN. The receiver "
                "has ideal synchronisation: it reads the PLHEADER, descrambles, drops the "
                "pilots, demaps to LLRs, deinterleaves, runs the LDPC decoder (normalized "
                "min-sum), corrects residual errors with BCH and checks the BBHEADER CRC."
            ),
            mo.hstack([run_esn0, run_n, run_it, run_go], justify="start", gap=2),
        ]
    )
    return run_esn0, run_go, run_it, run_n


@app.cell
def _(ModCod, Receiver, Transmitter, awgn, mc, mo, np, run_esn0, run_go, run_it, run_n):
    mo.stop(not run_go.value, mo.md("*Press **run the link**.*"))
    import time as _time

    _smc = ModCod(mc.modulation, mc.rate, "short", mc.pilots)
    _tx = Transmitter(_smc)
    _rx = Receiver(_smc, max_iter=run_it.value, algorithm="nms")
    _rng = np.random.default_rng()
    _rows = []
    _fe = _be = _bits = 0
    _t0 = _time.time()
    for _f in range(run_n.value):
        _frame = _tx.random_frame(_rng)
        _y, _n0 = awgn(_frame.plframe, run_esn0.value, _rng)
        _llr, _pls = _rx.llr(_y, _n0)
        _ch = int(np.sum((_llr < 0) != _frame.fecframe.astype(bool)))
        _r = _rx.receive(_y, _n0)
        _err = int(np.sum(_r.data != _frame.data)) if _r.data.size == _frame.data.size else _frame.data.size
        _fe += _err > 0 or not _r.header_ok
        _be += _err
        _bits += _frame.data.size
        _rows.append(
            f"| {_f + 1} | {_pls[0]} | {_ch} | {_r.ldpc_iterations} | {'yes' if _r.ldpc_ok else 'no'} | "
            f"{_r.bch_corrections if _r.bch_ok else 'fail'} | {'✓' if _r.header_ok else '✗'} | {_err} |"
        )
    _dt = _time.time() - _t0
    mo.md(
        f"**{_smc}** at Es/N0 = {run_esn0.value} dB: {_smc.plframe_symbols} symbols per frame, "
        f"{_frame.data.size} payload bits.\n\n"
        "| frame | PLS MODCOD | channel bit errors | LDPC iterations | LDPC codeword | BCH corrections | BBHEADER CRC | payload errors |\n"
        "|---|---|---|---|---|---|---|---|\n"
        + "\n".join(_rows)
        + f"\n\n**FER {_fe}/{run_n.value}, BER {_be / _bits:.2e}** ({_dt:.1f} s). "
        "Move Es/N0 below the threshold and watch the decoder give up: the waterfall is only a few "
        "tenths of a dB wide. Notebook 8 shows thousands of frames per point."
    )
    return


if __name__ == "__main__":
    app.run()
