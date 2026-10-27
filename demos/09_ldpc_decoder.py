import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="9 · Designing the LDPC decoder")


@app.cell
async def _():
    # Setup: in the browser (Pyodide) install the dvbs2 wheel published next to this page.
    import json
    import sys

    import marimo as mo

    IN_BROWSER = "pyodide" in sys.modules
    _loc = str(mo.notebook_location())
    BASE = _loc.rsplit("/", 1)[0] if _loc.endswith(".html") else _loc
    if IN_BROWSER:
        import micropip

        await micropip.install(BASE + "/dvbs2-1.0.0-py3-none-any.whl")
    import matplotlib.pyplot as plt
    import numpy as np

    from dvbs2.codes import _kernels as kernels
    from dvbs2.codes import ldpc_hw as hw
    from dvbs2.codes.ldpc import RATES, dvbs2_ldpc
    return BASE, IN_BROWSER, RATES, dvbs2_ldpc, hw, json, kernels, mo, np, plt


@app.cell
def _(mo):
    mo.md(r"""
    # 9 · Designing the LDPC decoder

    Notebook 6 showed belief propagation on toy codes, and notebook 7 decoded real
    DVB-S2 frames in software. This notebook asks the hardware question: **how do you
    build a decoder that handles 64 800-bit frames at hundreds of Mb/s?** It follows
    the thesis chapter *LDPC Decoder Design* in five steps:

    1. the DVB-S2 parity-check matrix is secretly made of 360 × 360 **circulants**;
    2. the **check-node** function and its hardware-friendly approximations;
    3. **layered** decoding of 360 checks at a time, in float and in bit-true fixed point;
    4. an **architecture calculator**: cycles, throughput, latency and memory;
    5. the Monte Carlo **study** behind the design choices.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 1 · 360 × 360 circulants

    The standard defines the code with an address table: information bit $i = 360g + l$
    (group $g$, position $l$) is added to the parity accumulators
    $(x + l\,q) \bmod (N-K)$ for every address $x$ in row $g$, with $q = (N-K)/360$.
    Write each check index as $r = a + b\,q$ ($0 \le a < q$, $0 \le b < 360$) and renumber
    it $r' = 360a + b$; do the same with the parity bits. Then address
    $x = a + b\,q$ sends bit $l$ of group $g$ to in-block row $(l + b) \bmod 360$ of block
    row $a$: a **cyclically shifted identity** with shift $b$. Block row $a$ is a
    *layer* of 360 checks that touch each bit at most once (with a few exceptions).
    """)
    return


@app.cell
def _(RATES, mo):
    rate_sel = mo.ui.dropdown(RATES["short"], value="1/2", label="short-frame code rate")
    rate_sel
    return (rate_sel,)


@app.cell
def _(dvbs2_ldpc, hw, rate_sel):
    code = dvbs2_ldpc(rate_sel.value, "short")
    qc = hw.qc_structure(code)
    return code, qc


@app.cell
def _(code, hw, plt):
    _fig, _axs = plt.subplots(1, 2, figsize=(10, 3.4))
    for _ax, _M, _t in ((_axs[0], code.H.tocoo(), "H as in the standard"),
                        (_axs[1], hw.permuted_H(code).tocoo(), "rows and parity columns renumbered")):
        _ax.plot(_M.col, _M.row, ",", color="#2a78d6", alpha=0.6)
        _ax.set_xlim(0, code.n)
        _ax.set_ylim(code.m, 0)
        _ax.set_title(_t, fontsize=10)
        _ax.axvline(code.k, color="#52514e", lw=0.8, ls="--")
        _ax.set_xticks([0, code.k, code.n])
        _ax.set_xticklabels(["0", "K", "N"])
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(code, mo):
    row_sel = mo.ui.slider(0, len(code.table) - 1, value=0, label="address-table row g", show_value=True)
    row_sel
    return (row_sel,)


@app.cell
def _(code, mo, qc, row_sel):
    _row = code.table[row_sel.value]
    _lines = ["| address x | layer a = x mod q | shift b = x div q |", "|---:|---:|---:|"]
    _layers = [x % code.q for x in _row]
    for _x in _row:
        _dup = " (weight-2 circulant)" if _layers.count(_x % code.q) > 1 else ""
        _lines.append("| %d | %d%s | %d |" % (_x, _x % code.q, _dup, _x // code.q))
    mo.md(
        "Table row %d with q = %d. Each address becomes one circulant, i.e. one entry of the "
        "block-column/shift ROM of the decoder:\n\n" % (row_sel.value, code.q) + "\n".join(_lines)
        + "\n\nThis code has **%d layers** of 360 checks, %d circulants in all, and **%d weight-2 circulants** "
          "(two addresses of a row in the same layer): there one bit meets two checks of the same layer, "
          "which a 360-parallel decoder has to resolve (the model adds both message updates)."
        % (code.q, sum(qc.layer_degrees), len(qc.weight2))
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 2 · The check-node function

    Belief propagation sends log-likelihood ratios along the edges. A check node with
    inputs $Q_1, \dots, Q_{d-1}$ answers

    $$R = 2\,\mathrm{atanh}\prod_i \tanh\frac{Q_i}{2} \;=\; \Big(\prod_i \mathrm{sign}\,Q_i\Big)\;\phi\Big(\sum_i \phi(|Q_i|)\Big),\qquad \phi(x) = -\ln\tanh\frac{x}{2}.$$

    The sum is dominated by the smallest $|Q_i|$, which gives **min-sum**: sign product
    times the smallest magnitude. Min-sum always *overestimates*; the **normalized**
    ($\alpha \cdot \min$) and **offset** ($\max(\min - \beta, 0)$) variants pull it back.
    Change the degree and the input reliability and compare the distributions.
    """)
    return


@app.cell
def _(mo):
    dc = mo.ui.slider(3, 30, value=7, label="check degree d_c", show_value=True)
    mean = mo.ui.slider(1.0, 10.0, value=3.0, step=0.5, label="mean input LLR", show_value=True)
    alpha = mo.ui.slider(0.5, 1.0, value=0.8125, step=0.0625, label="normalization α", show_value=True)
    beta = mo.ui.slider(0.0, 1.5, value=0.5, step=0.125, label="offset β", show_value=True)
    mo.vstack([mo.hstack([dc, mean], justify="start"), mo.hstack([alpha, beta], justify="start")])
    return alpha, beta, dc, mean


@app.cell
def _(alpha, beta, dc, mean, np, plt):
    _rng = np.random.default_rng(1)
    _q = np.abs(_rng.normal(mean.value, np.sqrt(2 * mean.value), size=(20000, dc.value - 1)))
    _phi = lambda v: -np.log(np.tanh(np.clip(v, 1e-12, 40) / 2))
    _spa = _phi(_phi(_q).sum(axis=1))
    _ms = _q.min(axis=1)
    _fig, _ax = plt.subplots(figsize=(8, 3.4))
    _bins = np.linspace(0, np.percentile(_ms, 99), 60)
    for _v, _lab, _c in ((_spa, "sum-product (exact)", "#2a78d6"), (_ms, "min-sum", "#eb6834"),
                         (alpha.value * _ms, "normalized, α = %.4g" % alpha.value, "#1baf7a"),
                         (np.maximum(_ms - beta.value, 0), "offset, β = %.3g" % beta.value, "#eda100")):
        _ax.hist(_v, bins=_bins, histtype="step", lw=1.8, color=_c, label="%s, mean %.2f" % (_lab, _v.mean()))
    _ax.set_xlabel("|R| sent by the check node")
    _ax.set_ylabel("count")
    _ax.legend(fontsize=8)
    _ax.set_title("ideal α for this degree and reliability: E|SPA| / E|MS| = %.2f" % (_spa.mean() / _ms.mean()),
                  fontsize=10)
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 3 · Layered decoding, 360 checks at a time

    A layered decoder keeps the posterior $L_v$ of each bit and, for one layer at a time,
    computes $Q = L_v - R^{old}$, the new check messages $R^{new}$, and writes back
    $L_v = Q + R^{new}$. Each layer uses the freshest information, so it converges in
    about half the iterations of the textbook *flooding* schedule. The bit-true model
    quantizes the channel LLRs to $w_{ch}$ bits ($s$ LSBs per LLR unit), saturates $L$ and
    $Q$ to $w_L$ bits and the messages to $w_R$ bits, and uses offset min-sum with an
    integer offset. Keep $w_L \ge w_R + 2$: with less headroom the saturated posterior
    makes the decoder diverge (try $w_L = 7$, $w_R = 6$ at a high Eb/N0).
    Decode one short frame (BPSK over AWGN, LDPC only):
    """)
    return


@app.cell
def _(mo):
    ebn0 = mo.ui.slider(0.5, 4.0, value=1.6, step=0.1, label="Eb/N0 [dB]", show_value=True)
    w_ch = mo.ui.slider(3, 8, value=6, label="w_ch", show_value=True)
    w_L = mo.ui.slider(5, 12, value=8, label="w_L", show_value=True)
    w_R = mo.ui.slider(4, 10, value=6, label="w_R", show_value=True)
    scale = mo.ui.dropdown({"1": 1.0, "2": 2.0, "4": 4.0, "8": 8.0}, value="4", label="LSB per LLR unit")
    offset = mo.ui.slider(0, 4, value=2, label="offset β [LSB]", show_value=True)
    seed = mo.ui.number(0, 10_000, value=1, label="frame seed")
    run = mo.ui.run_button(label="decode")
    mo.vstack([mo.hstack([ebn0, seed], justify="start"), mo.hstack([w_ch, w_L, w_R], justify="start"),
               mo.hstack([scale, offset, run], justify="start")])
    return ebn0, offset, run, scale, seed, w_L, w_R, w_ch


@app.cell
def _(code, ebn0, hw, kernels, mo, np, offset, plt, run, scale, seed, w_L, w_R, w_ch):
    mo.stop(not run.value, mo.md("*Press **decode** to run the three decoders on one frame.*"))
    _rng = np.random.default_rng(seed.value)
    _cw = code.encode(_rng.integers(0, 2, code.k))
    _sigma = np.sqrt(1 / (2 * code.rate * 10 ** (ebn0.value / 10)))
    _llr = 2 * ((1 - 2.0 * _cw) + _sigma * _rng.standard_normal(code.n)) / _sigma ** 2
    _fmt = hw.FixedPoint(w_ch.value, w_L.value, w_R.value, scale=scale.value, alpha_num=1, alpha_shift=0,
                         beta=offset.value)
    _runs = {}
    _t = []
    _L, _ = hw.layer_decode(_llr, code, 30, "oms", beta=0.5, trace=_t, impl="numpy")
    _runs["layered, float offset MS (β = 0.5)"] = (_t, _L)
    _t = []
    _L, _ = hw.layer_decode(_llr, code, 30, fmt=_fmt, trace=_t, impl="numpy")
    _runs["layered, fixed point %s" % _fmt.label()] = (_t, _L)
    _tf = []
    _L, _ = kernels.flooding_minsum(_llr, code.row_ptr, code.cols, 30, 1.0, 0.5, trace=_tf)
    _fig, _ax = plt.subplots(figsize=(9, 3.6))
    _cols = ["#2a78d6", "#eb6834", "#1baf7a"]
    _rows = []
    for _i, (_name, (_tr, _Lx)) in enumerate(_runs.items()):
        _x = [(it - 1) + (l + 1) / code.q for it, l, _ in _tr]
        _ax.semilogy(_x, [max(u, 0.5) for _, _, u in _tr], color=_cols[_i], lw=1.4, label=_name)
        _rows.append((_name, _tr[-1][0], int(((_Lx < 0) != _cw).sum())))
    _ax.semilogy(np.arange(1, len(_tf) + 1), [max(u, 0.5) for u in _tf], "o-", color=_cols[2], ms=4,
                 label="flooding, float offset MS (β = 0.5)")
    _rows.append(("flooding, float offset MS (β = 0.5)", len(_tf), int(((_L < 0) != _cw).sum())))
    _ax.set_xlabel("iteration (layered curves are updated after every layer)")
    _ax.set_ylabel("unsatisfied checks")
    _ax.set_ylim(0.4, code.m)
    _ax.legend(fontsize=8)
    _table = "| decoder | iterations | bit errors |\n|---|---:|---:|\n" + "\n".join(
        "| %s | %d | %d |" % r for r in _rows)
    mo.vstack([_fig, mo.md("Channel bit errors before decoding: %d of %d.\n\n" % (int(((_llr < 0) != _cw).sum()), code.n)
                           + _table)])
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 4 · Architecture calculator

    $P$ check-node processors (a divisor of 360) process one block column of a layer
    every $360/P$ cycles: read a word of $L$ memory, rotate it by the circulant shift,
    run the min-sum datapath, rotate back and write. With a pipeline, the next layer starts
    reading while the previous one is still writing, but it must not read a block
    column that has not been written back yet: those **read-after-write hazards** stall
    the pipeline unless the layers and block columns are reordered.
    """)
    return


@app.cell
def _(mo):
    frame_a = mo.ui.radio(["normal", "short"], value="normal", label="frame", inline=True)
    P = mo.ui.dropdown([str(p) for p in (360, 180, 120, 90, 72, 60, 45, 40, 36, 30, 24, 20, 18, 15, 12, 10, 9, 8)],
                       value="360", label="P (CNPs)")
    fclk = mo.ui.slider(50, 400, value=200, step=25, label="f_clk [MHz]", show_value=True)
    iters = mo.ui.slider(5, 50, value=30, label="iterations", show_value=True)
    depth = mo.ui.slider(2, 12, value=6, label="pipeline depth", show_value=True)
    sched = mo.ui.radio(["serial", "overlap", "reordered"], value="reordered", label="schedule", inline=True)
    mo.vstack([mo.hstack([frame_a, P, sched], justify="start"), mo.hstack([fclk, iters, depth], justify="start")])
    return P, depth, fclk, frame_a, iters, sched


@app.cell
def _(P, RATES, depth, dvbs2_ldpc, fclk, frame_a, hw, iters, mo, sched):
    _rows = ["| rate | layers q | block columns | weight-2 | cycles/iter | stalls/iter | info Mb/s | latency µs | memory kbit |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for _r in RATES[frame_a.value]:
        _a = hw.architecture(dvbs2_ldpc(_r, frame_a.value), int(P.value), fclk.value, iters.value,
                             hw.FixedPoint(6, 8, 6, scale=2, alpha_num=1, alpha_shift=0, beta=1), depth.value)
        _s = sched.value
        _rows.append("| %s | %d | %d | %d | %d | %d | %.0f | %.1f | %.0f |" % (
            _r, _a.q, _a.block_edges, _a.weight2, _a.cycles_per_iter[_s], _a.stalls[_s], _a.throughput_mbps[_s],
            _a.latency_us[_s], _a.memory_bits["total"] / 1000))
    mo.md("\n".join(_rows) + "\n\nWord lengths (w_ch, w_L, w_R) = (6, 8, 6); R memory stores per check "
          "min1, min2, the index of min1 and one sign per edge.")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 5 · The study behind the design

    The curves below come from `sim/tools/ldpc_study.py`: the complete DVB-S2 link
    (BBFRAME to PLFRAME, AWGN, exact demapper, BCH) for each decoder, up to 50 frame errors
    or 300 frames per point.
    """)
    return


@app.cell
def _(BASE, IN_BROWSER, json):
    def _load(name):
        try:
            if IN_BROWSER:
                from pyodide.http import open_url

                return json.loads(open_url(BASE + "/results/%s.json" % name).read())
            import pathlib

            return json.loads((pathlib.Path(BASE).parent / "sim" / "results" / "ldpc_study" / (name + ".json")).read_text())
        except Exception:
            return None

    study = {n: _load(n) for n in ("correction", "algorithms", "quantization", "convergence")}
    return (study,)


@app.cell
def _(mo, study):
    _avail = [k for k in ("algorithms", "quantization") if study[k]]
    exp_sel = mo.ui.radio(_avail or ["(no results)"], value=(_avail or ["(no results)"])[0], label="experiment",
                          inline=True)
    exp_sel
    return (exp_sel,)


@app.cell
def _(exp_sel, mo, plt, study):
    _data = study.get(exp_sel.value)
    mo.stop(not _data, mo.md("*No study results found.*"))
    _codes = list(dict.fromkeys((c["modcod"], c["frame"]) for c in _data["curves"]))
    _fig, _axs = plt.subplots(1, len(_codes), figsize=(4.2 * len(_codes), 3.6), sharey=True)
    _cols = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
    for _ax, (_m, _f) in zip(_axs, _codes):
        for _i, _c in enumerate([c for c in _data["curves"] if (c["modcod"], c["frame"]) == (_m, _f)]):
            _p = [p for p in _c["points"] if p["frames"] and p["fer"] > 0]
            if _p:
                _ax.semilogy([p["esn0"] for p in _p], [p["fer"] for p in _p], "o-", ms=3, color=_cols[_i % 6],
                             label=_c["decoder"])
        _ax.set_title("%s %s" % (_m, _f), fontsize=9)
        _ax.set_xlabel("Es/N0 [dB]")
    _axs[0].set_ylabel("FER")
    _axs[-1].legend(fontsize=7)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(mo, study):
    _c = study.get("correction")
    mo.stop(not _c, None)
    _codes = list(dict.fromkeys((p["modcod"], p["frame"], p["esn0"]) for p in _c["points"]))
    _decs = list(dict.fromkeys(p["decoder"] for p in _c["points"]))
    _rows = ["| decoder | " + " | ".join("%s %s @ %.1f dB" % c for c in _codes) + " |",
             "|---|" + "---:|" * len(_codes)]
    for _d in _decs:
        _v = []
        for _m, _f, _e in _codes:
            _p = [p for p in _c["points"] if (p["modcod"], p["frame"], p["decoder"]) == (_m, _f, _d)][0]
            _v.append("%.3f" % _p["fer"])
        _rows.append("| %s | %s |" % (_d, " | ".join(_v)))
    mo.md("**FER at the Es/N0 where sum-product first reaches FER < 10⁻²**, for each min-sum correction "
          "(nms:α normalized, oms:β offset):\n\n" + "\n".join(_rows))
    return


if __name__ == "__main__":
    app.run()
