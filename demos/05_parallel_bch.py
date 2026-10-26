import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="5 · Parallel BCH encoder")


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
    import time

    import matplotlib.pyplot as plt
    import numpy as np

    from dvbs2 import poly2
    from dvbs2.codes.bch import BCHCode, dvbs2_bch
    from dvbs2.codes.bch_parallel import ParallelLFSR, companion, gf2_matpow
    from dvbs2.codes.cyclic import lfsr_encode_trace, register_to_parity
    return (
        BCHCode,
        ParallelLFSR,
        companion,
        dvbs2_bch,
        gf2_matpow,
        lfsr_encode_trace,
        mo,
        np,
        plt,
        poly2,
        register_to_parity,
        time,
    )


@app.cell
def _(mo):
    mo.md(r"""
    # 5 · The parallel BCH encoder: the core of the thesis

    A systematic BCH encoder computes the remainder of $m(x)\,x^r$ divided by $g(x)$.
    The textbook circuit is an LFSR that takes **one bit per clock** (notebook 3). For a
    DVB-S2 modulator running at 1 Gbit/s that means a 1 GHz clock, which was out of reach
    for the 2008 space-qualified FPGAs.

    The thesis treats the LFSR as a **linear system over GF(2)**. Let x(i) be the
    *r* register bits and u(i) the input bit:

    $$\mathbf x(i+1) = \mathbf A\,\mathbf x(i) + \mathbf b\,u(i)$$

    $\mathbf A$ is the companion matrix of $g(x)$: it shifts the register and feeds the last
    stage back through the taps of $g$. Choosing $\mathbf b = \mathbf g$ (input added to the
    feedback) gives the *premultiplied* encoder, which needs only *k* clocks. Apply the
    equation *p* times:

    $$\mathbf x(i+p) = \mathbf A^p\,\mathbf x(i) + \mathbf B_p\,\mathbf u_p(i),
    \qquad \mathbf B_p = [\,\mathbf b,\ \mathbf A\mathbf b,\ \dots,\ \mathbf A^{p-1}\mathbf b\,]$$

    The new circuit consumes **p bits per clock**. With $p = 8$ the 1 Gbit/s target needs
    only 125 MHz.
    """)
    return


@app.cell
def _(BCHCode, mo):
    small_codes = {
        "(15,11) Hamming, t = 1": BCHCode(4, 1),
        "(15,7) BCH, t = 2": BCHCode(4, 2),
        "(15,5) BCH, t = 3": BCHCode(4, 3),
        "(31,21) BCH, t = 2": BCHCode(5, 2),
        "(31,16) BCH, t = 3": BCHCode(5, 3),
    }
    code_pick = mo.ui.dropdown(list(small_codes), value="(15,7) BCH, t = 2", label="small code")
    p_slider = mo.ui.slider(steps=[1, 2, 4, 8, 16], value=4, label="parallelism p", show_value=True)
    mo.hstack([code_pick, p_slider], justify="start", gap=2)
    return code_pick, p_slider, small_codes


@app.cell
def _(ParallelLFSR, code_pick, companion, gf2_matpow, mo, p_slider, plt, poly2, small_codes):
    small = small_codes[code_pick.value]
    p = p_slider.value
    small_enc = ParallelLFSR(small.g, p, "k")
    _A = companion(small.g)
    _Ap = gf2_matpow(_A, p)
    _fig, _axes = plt.subplots(1, 3, figsize=(10, 3.6), gridspec_kw={"width_ratios": [small.r, small.r, max(p, 2)]})
    for _ax, _M, _title in zip(_axes, (_A, _Ap, small_enc.Bp), ("A", f"A^{p}", f"B_{p} (k-clock)")):
        _ax.imshow(_M, cmap="Blues", vmin=0, vmax=1.4)
        _ax.set_title(_title)
        _ax.set_xticks([])
        _ax.set_yticks([])
        _ax.set_xlabel("column")
    _axes[0].set_ylabel("register stage 0 … r−1")
    if p < small.r:
        _axes[1].axvline(small.r - p - 0.5, color="#d62728", lw=1.5)
        _axes[1].text(small.r - p - 0.5, -0.8, " dense", color="#d62728", fontsize=8)
    _fig.tight_layout()
    mo.vstack(
        [
            mo.md(
                f"""
    ## The matrices for $g(x) = {poly2.to_str(small.g)}$ (r = {small.r})

    $\\mathbf A^p$ is a shift by *p* (the diagonal on the left) plus a dense block in its
    **last p columns**, the feedback of the *p* stages that leave the register during
    one clock. That regular structure is what makes the hardware cheap:
    stage *j* needs a single XOR network over the last *p* stages, the inputs and stage *j − p*.
    {"With p ≥ r there is no pure shift left: every column is feedback." if p >= small.r else ""}
    """
            ),
            _fig,
        ]
    )
    return p, small, small_enc


@app.cell
def _(mo, p, small, small_enc):
    _lines = []
    _r = small.r
    for _j in range(_r):
        _terms = []
        if _j >= p:
            _terms.append(f"x{_j - p}")
        _terms += [f"x{c}" for c in range(max(0, _r - p), _r) if small_enc.Ap[_j, c] and not (_j >= p and c == _j - p)]
        _terms += [f"u{f}" for f in range(p) if small_enc.Bp[_j, f]]
        _lines.append(f"x{_j}' = " + (" ⊕ ".join(_terms) if _terms else "0"))
    mo.accordion(
        {
            f"XOR equations of one clock (p = {p}; uₚ₋₁ is the first bit of the chunk)": mo.md(
                "```\n" + "\n".join(_lines) + "\n```"
            )
        }
    )
    return


@app.cell
def _(mo):
    reseed = mo.ui.button(label="new message", value=0, on_click=lambda v: v + 1)
    return (reseed,)


@app.cell
def _(lfsr_encode_trace, mo, np, p, plt, register_to_parity, reseed, small, small_enc):
    _rng = np.random.default_rng(31 + reseed.value)
    _msg = _rng.integers(0, 2, small.k).astype(np.uint8)
    _pad = (-small.k) % p
    _bits = np.concatenate([np.zeros(_pad, np.uint8), _msg])  # leading zeros do not change m(x)
    _serial = lfsr_encode_trace(_bits, small.g)
    _final, _par = small_enc.run(_bits, trace=True)
    _agree = np.array_equal(_serial[::p], _par)
    _fig, _axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    _axes[0].imshow(_serial, cmap="Blues", vmin=0, vmax=1.4, aspect="auto", interpolation="nearest")
    _axes[0].set_title(f"serial LFSR: {_bits.size} clocks")
    _axes[1].imshow(
        _par,
        cmap="Oranges",
        vmin=0,
        vmax=1.4,
        aspect="auto",
        interpolation="nearest",
        extent=(-0.5, small.r - 0.5, _bits.size + p / 2, -p / 2),
    )
    _axes[1].set_title(f"p = {p} parallel: {_bits.size // p} clocks")
    for _ax in _axes:
        _ax.set_xlabel("register stage")
    _axes[0].set_ylabel("input bits consumed")
    _fig.tight_layout()
    _par_bits = register_to_parity(_final)
    mo.vstack(
        [
            mo.md(
                f"""
    ## Serial and parallel register traces

    Message ({small.k} bits{f", with {_pad} leading zeros to fill whole chunks" if _pad else ""}):
    `{''.join(map(str, _msg))}`

    Each row is the register after that many input bits. The parallel encoder
    skips straight from one multiple of *p* to the next and lands on exactly the
    same states: **{'✅ every parallel state matches the serial one' if _agree else '❌ mismatch'}**.

    parity (parallel) `{''.join(map(str, _par_bits))}`, parity (polynomial division) `{''.join(map(str, small.parity(_msg)))}`
    """
            ),
            mo.hstack([reseed]),
            _fig,
        ]
    )
    return


@app.cell
def _(mo, np):
    _rows = []
    for _p in (1, 2, 4, 8, 16, 32):
        _rows.append(
            f"| {_p} | {1000 / _p:.1f} MHz | {125 * _p / 1000:.3g} Gbit/s | {np.ceil(32208 / _p):.0f} | {_p} + {_p} |"
        )
    mo.md(
        f"""
    ## Why p = 8

    Throughput is $p \\cdot f_{{clk}}$. For the DVB-S2 rate-1/2 code (k = 32 208 bits per BBFRAME):

    | p | clock for 1 Gbit/s | throughput at 125 MHz | clocks per frame (k-clock) | XOR-network inputs per stage (state + input) |
    |---|---|---|---|---|
    {chr(10).join(_rows)}

    The thesis picked **p = 8**: 1 Gbit/s at a 125 MHz clock on the Altera Stratix II,
    and each network stays an 8-input XOR (plus 8 inputs for the data bits),
    gated by coefficients stored in LUTs.
    """
    )
    return


@app.cell
def _(mo):
    dvb_p = mo.ui.slider(steps=[1, 2, 4, 8, 16], value=8, label="p for the DVB-S2 matrices", show_value=True)
    mo.vstack(
        [
            mo.md(
                r"""
    ## The DVB-S2 t = 12 code: a 192 × 192 state matrix

    The normal-frame generator $g(x)$ (degree 192) is the product of the minimal
    polynomials of α, α³, …, α²³ in GF(2^16). Compare its $\mathbf A^p$ with the small
    example above: the same shift, and all the feedback in the last *p* columns.
    """
            ),
            dvb_p,
        ]
    )
    return (dvb_p,)


@app.cell
def _(ParallelLFSR, dvb_p, dvbs2_bch, mo, np, plt):
    g12 = dvbs2_bch("1/2").g
    _p = dvb_p.value
    _enc = ParallelLFSR(g12, _p, "k")
    _r = _enc.R
    _fig, _axes = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [4, 1]})
    _axes[0].imshow(_enc.Ap, cmap="Blues", vmin=0, vmax=1.4, interpolation="nearest")
    _axes[0].set_title(f"A^{_p}  (192 × 192)")
    _axes[0].axvline(_r - _p - 0.5, color="#d62728", lw=1)
    _axes[1].imshow(
        np.hstack([_enc.Ap[:, _r - _p :], _enc.Bp]), cmap="Blues", vmin=0, vmax=1.4, aspect="auto", interpolation="nearest"
    )
    _axes[1].axvline(_p - 0.5, color="#d62728", lw=1)
    _axes[1].set_title(f"last {_p} cols | B_{_p}")
    for _ax in _axes:
        _ax.set_xticks([])
    _fig.tight_layout()
    _dense = int(_enc.Ap[:, _r - _p :].sum())
    _shift = int(_enc.Ap[:, : _r - _p].sum())
    _ni = _enc.network_inputs()
    _fig2, _ax2 = plt.subplots(figsize=(10, 2.4))
    _ax2.bar(np.arange(_r), _ni["state"], color="#4c78a8", label="state network inputs (of last p stages)")
    _ax2.bar(np.arange(_r), _ni["input"], bottom=_ni["state"], color="#f58518", label="input network inputs")
    _ax2.set_xlabel("register stage")
    _ax2.set_ylabel("XOR inputs")
    _ax2.set_xlim(-1, _r)
    _ax2.legend(fontsize=8, loc="upper right")
    mo.vstack(
        [
            _fig,
            mo.md(
                f"""
    {_shift} ones in the first {_r - _p} columns (the pure shift) and {_dense} in the last {_p}.
    Each of the 192 stages needs one XOR over at most {_p} state bits and one over at most
    {_p} input bits: the **192 + 192 combinational networks** of chapter 4. On average they use
    {_ni['state'].mean():.1f} state and {_ni['input'].mean():.1f} input bits, since a zero
    coefficient simply removes an input.
    """
            ),
            _fig2,
        ]
    )
    return


@app.cell
def _(mo):
    run_share = mo.ui.run_button(label="encode one frame with each t on the shared datapath")
    mo.vstack(
        [
            mo.md(
                r"""
    ## One datapath for t = 12, 10 and 8

    DVB-S2 changes MODCOD frame by frame (ACM), and the BCH code changes with it:
    t = 12, 10 or 8, so 192, 160 or 128 parity bits. The thesis serves all three with
    **one 192-stage register**. Placing the generator at the top of the register,
    $g'(x) = x^{192 - r} g(x)$, leaves the remainder in stages $192 - r \dots 191$, while
    the lowest $192 - r$ stages always stay zero. Switching codes means swapping the
    network coefficients (LUT contents) and disabling 0, 32 or 64 network pairs.
    """
            ),
            run_share,
        ]
    )
    return (run_share,)


@app.cell
def _(ParallelLFSR, dvbs2_bch, mo, np, run_share, time):
    _rows = []
    _svg = ['<svg viewBox="0 0 1000 96" width="100%" style="font-family:sans-serif">']
    for _i, (_rate, _t) in enumerate((("1/4", 12), ("2/3", 10), ("8/9", 8))):
        _code = dvbs2_bch(_rate)
        _enc = ParallelLFSR(_code.g, 8, "k", reg_len=192)
        _svg.append(f'<text x="0" y="{_i * 30 + 17}" font-size="12" fill="currentColor">t = {_t}</text>')
        for _s in range(192):
            _col = "#ccc" if _s < _enc.offset else "#4c78a8"
            _svg.append(f'<rect x="{60 + _s * 4.9:.1f}" y="{_i * 30 + 4}" width="4.2" height="18" fill="{_col}"/>')
        if run_share.value:
            _msg = np.random.default_rng(_t).integers(0, 2, _code.k).astype(np.uint8)
            _t0 = time.perf_counter()
            _par = _enc.parity(_msg)
            _dt = time.perf_counter() - _t0
            _ok = np.array_equal(_par, _code.parity(_msg))
            _rows.append(
                f"| {_t} | {_rate} | {_code.n} | {_code.k} | {_enc.offset} | {_code.k // 8} | {'✅' if _ok else '❌'} | {_dt:.2f} s |"
            )
        else:
            _rows.append(f"| {_t} | {_rate} | {_code.n} | {_code.k} | {_enc.offset} | {_code.k // 8} | | |")
    _svg.append('<text x="60" y="94" font-size="11" fill="currentColor">stage 0</text>')
    _svg.append('<text x="940" y="94" font-size="11" fill="currentColor">stage 191</text></svg>')
    mo.vstack(
        [
            mo.Html("".join(_svg)),
            mo.md(
                "Grey: disabled stages (always 0); blue: stages holding the parity.\n\n"
                "| t | rate | N_bch | K_bch | disabled stages | clocks (p = 8) | parity = serial? | time (numpy model) |\n"
                "|---|---|---|---|---|---|---|---|\n" + "\n".join(_rows)
            ),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## From the thesis' C code to this notebook

    The 2008 validation package, kept unchanged in the repository root, modelled these
    circuits in C to check the VHDL:

    | thesis file | what it does | Python equivalent |
    |---|---|---|
    | `serial.c`, `serenc.c` | serial LFSR encoders | `dvbs2.codes.cyclic.lfsr_encode_trace`, `lfsr_divide_trace` |
    | `parnclk.c`, `ParEncn.c` | 8-parallel division, n/8 clocks | `ParallelLFSR(g, 8, "n")` |
    | `parkclk.c` | 8-parallel premultiplied, k/8 clocks, 192-bit register | `ParallelLFSR(g, 8, "k", reg_len=192)` |
    | `comb1.c`, `comb2.c` | one XOR network (input / state) | rows of `Bp` / last *p* columns of `Ap` |

    `main.c` loaded $\mathbf A^p$ and $\mathbf B_p$ from text files (`Matrices/ADVBS2_kclk_t12.txt`, …)
    that were never committed. They can be regenerated:

    ```
    dvbs2sim bch-matrices -o Matrices        # A^8 and B_8 for t = 12, 10, 8, n- and k-clock
    ```

    The test suite (`sim/tests/test_bch.py`) runs line-by-line ports of the C functions
    and checks that they match these encoders bit for bit.
    """)
    return


if __name__ == "__main__":
    app.run()
