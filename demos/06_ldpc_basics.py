import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="6 · LDPC codes and message passing")


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

    from dvbs2.codes.ldpc import LDPCCode, dvbs2_ldpc
    return LDPCCode, dvbs2_ldpc, mo, np, plt


@app.cell
def _(mo):
    mo.md(r"""
    # 6 · LDPC codes and message passing

    BCH codes (notebooks 4–5) are decoded *algebraically*: syndromes, an error-locator
    polynomial, its roots. **Low-density parity-check (LDPC)** codes take a different
    route. They are defined by a very large but very *sparse* parity-check matrix
    $\mathbf H$, and they are decoded *iteratively*: bits and parity checks exchange
    beliefs along the edges of a graph until every check is satisfied.

    Gallager invented them in 1962. They were forgotten until the 1990s, and they are
    now the inner code of DVB-S2, where they work within about 0.7–1 dB of the
    Shannon limit. This notebook builds intuition on a toy code with 20 bits.
    """)
    return


@app.cell
def _(LDPCCode, np):
    # A toy irregular repeat-accumulate (IRA) code with exactly the DVB-S2 structure,
    # scaled down: groups of 5 information bits instead of 360.
    toy = LDPCCode([[0, 3, 7], [1, 4, 8]], 20, "toy IRA (20,10)", group=5)
    H = toy.H.toarray().astype(np.uint8)
    n_var, n_chk = toy.n, toy.m
    edges = [(int(c), int(v)) for c, v in zip(*np.nonzero(H))]  # (check, variable)
    return H, edges, n_chk, n_var, toy


@app.cell
def _(H, mo, toy):
    _rows = "\\\\".join(
        " & ".join(("\\color{#4c78a8}{1}" if j < toy.k else "\\color{#e45756}{1}") if x else "\\cdot" for j, x in enumerate(r))
        for r in H
    )
    mo.md(
        rf"""
    ## The toy code

    $n = {toy.n}$ bits, $k = {toy.k}$ information bits, $m = {toy.m}$ parity checks. Each
    **row** of $\mathbf H$ is a parity check (the XOR of the marked bits must be 0) and each
    **column** is a bit:

    $$\mathbf H = \left[\begin{{array}}{{{'c' * toy.n}}}{_rows}\end{{array}}\right]$$

    The blue part (information bits) comes from an address table, just like DVB-S2's
    Annex B; here it is `[[0, 3, 7], [1, 4, 8]]` with 5 bits per group. The red part
    is the **staircase**: parity bit *j* appears in checks *j* and *j+1*. This is what
    makes the code *repeat-accumulate*. The encoder just XORs each information bit
    into a few accumulators and then takes a running XOR, with no matrix inversion.

    Only {int(H.sum())} of the {H.size} entries are 1. In DVB-S2's 64800 × 32400
    matrix the fraction is below 0.01 %.
    """
    )
    return


@app.cell
def _(edges, n_chk, n_var, toy):
    def tanner_svg(var_fill=None, var_text=None, chk_fill=None, edge_color=None, width=760):
        """Tanner graph: variable nodes on top, check nodes below."""
        _w, _h = width, 250
        _vx = [30 + i * (_w - 60) / (n_var - 1) for i in range(n_var)]
        _cx = [60 + j * (_w - 120) / (n_chk - 1) for j in range(n_chk)]
        _vy, _cy = 45, 205
        out = [f'<svg viewBox="0 0 {_w} {_h}" width="100%" style="max-width:{_w}px;font-family:sans-serif">']
        for c, v in edges:
            col = (edge_color or {}).get((c, v), "#9a9a9a")
            sw = 2.2 if (edge_color and (c, v) in edge_color) else 1
            out.append(f'<line x1="{_vx[v]:.1f}" y1="{_vy}" x2="{_cx[c]:.1f}" y2="{_cy}" stroke="{col}" stroke-width="{sw}" opacity="0.8"/>')
        for v in range(n_var):
            fill = (var_fill or {}).get(v, "#4c78a8" if v < toy.k else "#e45756")
            out.append(f'<circle cx="{_vx[v]:.1f}" cy="{_vy}" r="13" fill="{fill}" stroke="#333" stroke-width="0.5"/>')
            txt = (var_text or {}).get(v, "")
            out.append(f'<text x="{_vx[v]:.1f}" y="{_vy + 5}" text-anchor="middle" font-size="12" fill="white" font-weight="bold">{txt}</text>')
            out.append(f'<text x="{_vx[v]:.1f}" y="{_vy - 18}" text-anchor="middle" font-size="9" fill="currentColor">v{v}</text>')
        for c in range(n_chk):
            fill = (chk_fill or {}).get(c, "#bbbbbb")
            out.append(f'<rect x="{_cx[c] - 12:.1f}" y="{_cy - 12}" width="24" height="24" fill="{fill}" stroke="#333" stroke-width="0.5"/>')
            out.append(f'<text x="{_cx[c]:.1f}" y="{_cy + 30}" text-anchor="middle" font-size="9" fill="currentColor">c{c}</text>')
        out.append("</svg>")
        return "".join(out)
    return (tanner_svg,)


@app.cell
def _(mo, tanner_svg):
    mo.vstack(
        [
            mo.md(r"""
    ## The Tanner graph

    The same matrix as a bipartite graph. Circles are **variable nodes** (bits; blue
    for information, red for parity), squares are **check nodes**, and there is an edge
    wherever $\mathbf H$ has a 1. Iterative decoders pass messages along these edges.
    Sparsity keeps every node's work small, so decoding cost grows only linearly
    with the block length.
    """),
            mo.Html(tanner_svg()),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Erasure channel: the peeling decoder

    On the **binary erasure channel** BEC(ε) a bit either arrives intact or is
    marked *erased* ("?"), with probability ε. Decoding is then pure logic. A check
    with exactly **one** erased neighbour knows that bit's value (the XOR of the
    others), so it fills it in, and that may unlock another check. Repeat until
    nothing changes. If erasures remain, they form a *stopping set*: every check
    touching them sees at least two unknowns.
    """)
    return


@app.cell
def _(mo):
    eps = mo.ui.slider(0.0, 0.8, step=0.05, value=0.35, label="erasure probability ε", show_value=True)
    bec_seed = mo.ui.number(start=0, stop=999, value=7, label="channel seed")
    mo.hstack([eps, bec_seed], justify="start", gap=2)
    return bec_seed, eps


@app.cell
def _(H, bec_seed, eps, np, toy):
    _rng = np.random.default_rng(int(bec_seed.value))
    bec_cw = toy.encode(_rng.integers(0, 2, toy.k))
    _erased = _rng.random(toy.n) < eps.value
    # peeling trace: list of (erased mask, bits recovered in this step, checks that fired)
    peel_steps = [(_erased.copy(), set(), set())]
    _cur = _erased.copy()
    while True:
        _fired, _rec = set(), set()
        for _c in range(H.shape[0]):
            _nb = np.flatnonzero(H[_c])
            _unk = [v for v in _nb if _cur[v]]
            if len(_unk) == 1 and _unk[0] not in _rec:
                _fired.add(_c)
                _rec.add(int(_unk[0]))
        if not _rec:
            break
        _cur = _cur.copy()
        _cur[list(_rec)] = False
        peel_steps.append((_cur.copy(), _rec, _fired))
    return bec_cw, peel_steps


@app.cell
def _(mo, peel_steps):
    peel_it = mo.ui.slider(0, len(peel_steps) - 1, value=0, label="peeling step", show_value=True)
    peel_it
    return (peel_it,)


@app.cell
def _(H, bec_cw, edges, mo, np, peel_it, peel_steps, tanner_svg):
    _mask, _rec, _fired = peel_steps[peel_it.value]
    _vf, _vt, _cf, _ec = {}, {}, {}, {}
    for _v in range(len(_mask)):
        if _mask[_v]:
            _vf[_v], _vt[_v] = "#9a9a9a", "?"
        else:
            _vf[_v] = "#f58518" if _v in _rec else "#54a24b"
            _vt[_v] = str(bec_cw[_v])
    for _c in range(H.shape[0]):
        _unk = int(sum(_mask[v] for v in np.flatnonzero(H[_c])))
        _cf[_c] = "#f58518" if _c in _fired else ("#54a24b" if _unk == 0 else ("#e8c33a" if _unk == 1 else "#bbbbbb"))
    for _c, _v in edges:
        if _c in _fired and _v in _rec:
            _ec[(_c, _v)] = "#f58518"
    _left = int(_mask.sum())
    _final = peel_steps[-1][0].sum()
    _msg = (
        f"Step {peel_it.value}: **{_left}** erasures left."
        + (f" Checks {sorted(_fired)} each had one unknown and recovered bits {sorted(_rec)} (orange)." if _rec else "")
        + (
            "\n\nThe decoder ends with **all bits recovered** ✅"
            if _final == 0
            else f"\n\nThe decoder gets stuck with {int(_final)} erasures: a stopping set ❌"
        )
    )
    mo.vstack(
        [
            mo.Html(tanner_svg(_vf, _vt, _cf, _ec)),
            mo.md(
                _msg
                + "\n\nGreen bits are known, grey bits erased. A check is yellow when exactly "
                "one neighbour is unknown (it can fire next) and green when all its "
                "neighbours are known."
            ),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Binary symmetric channel: bit flipping

    With hard bit errors there are no "?" marks, so the decoder has to *guess*.
    Gallager's **bit-flipping** algorithm counts, for each bit, how many of its checks
    fail, and flips the bits with the highest count. It repeats until the syndrome is
    zero or it gives up. Choose which bits the channel flips:
    """)
    return


@app.cell
def _(mo, toy):
    bf_flips = mo.ui.array([mo.ui.checkbox(label=str(i), value=(i in (3,))) for i in range(toy.n)])
    mo.hstack([mo.md("**flip bit**"), bf_flips.hstack()], justify="start", gap=1, wrap=True)
    return (bf_flips,)


@app.cell
def _(H, bec_cw, bf_flips, mo, np):
    _e = np.array([int(x) for x in bf_flips.value], dtype=np.uint8)
    _r = bec_cw ^ _e
    _H = H.astype(int)
    _rows = []
    _word = _r.copy()
    for _it in range(10):
        _syn = _H @ _word % 2
        _unsat = _H.T @ _syn  # failed checks per bit
        _rows.append(
            f"| {_it} | `{''.join(map(str, _word))}` | {int(_syn.sum())} | "
            f"{', '.join(str(int(v)) for v in np.flatnonzero(_word != bec_cw)) or '–'} |"
        )
        if not _syn.any():
            break
        _flip = _unsat == _unsat.max()
        _word = _word ^ _flip.astype(np.uint8)
    _ok = np.array_equal(_word, bec_cw)
    mo.md(
        "| iter | word | failed checks | wrong bits |\n|---|---|---|---|\n"
        + "\n".join(_rows)
        + (
            "\n\n✅ decoded to the transmitted codeword."
            if _ok
            else "\n\n❌ not decoded. Hard decisions throw away *how sure* the receiver "
            "was about each bit, and with only 10 checks a few errors are already too many."
        )
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## AWGN channel: belief propagation

    Over a Gaussian channel the receiver knows how *reliable* each bit is. That
    is the **log-likelihood ratio**
    $L = \ln\frac{P(b=0\mid y)}{P(b=1\mid y)} = \frac{2y}{\sigma^2}$ for BPSK.
    The magnitude is the confidence and the sign is the decision.

    Each iteration of the **sum-product** algorithm has two half-steps:

    * **check → variable**: $\;r_{c\to v} = 2\,\operatorname{atanh}\!\prod_{v'\neq v}\tanh\frac{q_{v'\to c}}{2}$
      ("given what the other bits say, here is what the parity requires of you");
    * **variable → check**: $\;q_{v\to c} = L_v + \sum_{c'\neq c} r_{c'\to v}$.

    **Min-sum** replaces the tanh product by the sign product times the smallest
    magnitude (scaled by α ≈ 0.8). It needs no transcendental functions, which is
    why hardware decoders use it.
    """)
    return


@app.cell
def _(mo):
    awgn_snr = mo.ui.slider(-1.0, 6.0, step=0.25, value=1.5, label="Eb/N0 [dB]", show_value=True)
    awgn_alg = mo.ui.dropdown(["sum-product", "normalized min-sum"], value="sum-product", label="algorithm")
    awgn_seed = mo.ui.number(start=0, stop=999, value=3, label="noise seed")
    mo.hstack([awgn_snr, awgn_alg, awgn_seed], justify="start", gap=2)
    return awgn_alg, awgn_seed, awgn_snr


@app.cell
def _(H, np):
    def traced_bp(llr, max_iter=12, minsum=False, alpha=0.8):
        """Flooding BP on a small dense H; returns the posterior LLRs after each iteration."""
        _mask = H.astype(bool)
        R = np.zeros(H.shape)
        post = [llr.copy()]
        L = llr.copy()
        for _ in range(max_iter):
            Q = np.where(_mask, L[None, :] - R, 0.0)
            if minsum:
                _mag = np.where(_mask, np.abs(Q), np.inf)
                _sgn = np.where(_mask, np.where(Q < 0, -1.0, 1.0), 1.0)
                _prod = _sgn.prod(axis=1, keepdims=True)
                _srt = np.sort(_mag, axis=1)
                _m1, _m2 = _srt[:, :1], _srt[:, 1:2]
                _other = np.where(_mag == _m1, _m2, _m1)
                R = np.where(_mask, alpha * _prod * _sgn * _other, 0.0)
            else:
                _t = np.where(_mask, np.tanh(np.clip(Q, -30, 30) / 2), 1.0)
                _t = np.where(np.abs(_t) < 1e-12, 1e-12, _t)
                _ext = _t.prod(axis=1, keepdims=True) / _t
                R = np.where(_mask, 2 * np.arctanh(np.clip(_ext, -0.999999, 0.999999)), 0.0)
            L = llr + R.sum(axis=0)
            post.append(L.copy())
        return np.array(post)
    return (traced_bp,)


@app.cell
def _(awgn_alg, awgn_seed, awgn_snr, bec_cw, mo, np, plt, toy, traced_bp):
    _rng = np.random.default_rng(int(awgn_seed.value))
    _sigma = np.sqrt(1 / (2 * toy.rate * 10 ** (awgn_snr.value / 10)))
    _y = (1 - 2.0 * bec_cw) + _sigma * _rng.standard_normal(toy.n)
    _llr = 2 * _y / _sigma**2
    _post = traced_bp(_llr, 12, awgn_alg.value != "sum-product")
    _wrong0 = np.flatnonzero((_llr < 0) != bec_cw.astype(bool))
    _wrong = [int(np.sum((p < 0) != bec_cw.astype(bool))) for p in _post]

    _fig, (_a1, _a2) = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [2.2, 1]})
    _signed = _post * np.where(bec_cw == 0, 1, -1)[None, :]  # positive = correct
    for _v in range(toy.n):
        _bad = _v in _wrong0
        _a1.plot(_signed[:, _v], color="#e45756" if _bad else "#4c78a8", lw=2 if _bad else 0.8, alpha=1 if _bad else 0.6)
    _a1.axhline(0, color="k", lw=0.8)
    _a1.set_xlabel("iteration")
    _a1.set_ylabel("posterior LLR × (±1)\n(> 0 means correct)")
    _a1.set_yscale("symlog", linthresh=2)
    _a1.set_title("bits wrong at the channel output in red")
    _a2.bar(range(len(_wrong)), _wrong, color="#f58518")
    _a2.set_xlabel("iteration")
    _a2.set_ylabel("bit errors")
    _a2.set_title("hard-decision errors")
    _fig.tight_layout()
    mo.vstack(
        [
            _fig,
            mo.md(
                f"The channel left **{len(_wrong0)}** wrong bits (signs). After 12 iterations of "
                f"{awgn_alg.value}: **{_wrong[-1]}** errors. Each curve is one bit's belief. "
                "Correct bits grow more and more confident, and wrong ones are usually pulled "
                "back across zero by their checks. At low Eb/N0 the beliefs can lock onto the "
                "wrong answer: a 20-bit code has too few checks to average out the noise."
            ),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## The real thing: a DVB-S2 short-frame code

    Scale the same algorithm up to the DVB-S2 rate-1/2 short code: 16200 bits,
    7200 information bits, 48 600 edges. Short codes show the **waterfall**:
    over a fraction of a dB the decoder goes from failing on almost every frame to
    almost never failing. (In the browser the decoder is a numpy flooding min-sum;
    the local Python package uses a compiled layered decoder.)
    """)
    return


@app.cell
def _(mo):
    big_snr = mo.ui.slider(0.0, 3.0, step=0.1, value=1.4, label="Eb/N0 [dB]", show_value=True)
    big_rate = mo.ui.dropdown(["1/4", "1/3", "2/5", "1/2", "3/5", "2/3", "3/4", "4/5", "5/6", "8/9"], value="1/2", label="code rate")
    big_go = mo.ui.run_button(label="encode → AWGN → decode")
    mo.hstack([big_rate, big_snr, big_go], justify="start", gap=2)
    return big_go, big_rate, big_snr


@app.cell
def _(big_go, big_rate, big_snr, dvbs2_ldpc, mo, np, plt):
    mo.stop(not big_go.value, mo.md("*Press the button to run one frame.*"))
    import time as _time

    _code = dvbs2_ldpc(big_rate.value, "short")
    _rng = np.random.default_rng()
    _cw = _code.encode(_rng.integers(0, 2, _code.k))
    _sigma = np.sqrt(1 / (2 * _code.rate * 10 ** (big_snr.value / 10)))
    _llr = 2 * ((1 - 2.0 * _cw) + _sigma * _rng.standard_normal(_code.n)) / _sigma**2
    _t0 = _time.time()
    _hard, _L, _it = _code.decode(_llr, 50, "nms")
    _dt = _time.time() - _t0
    _ch = int(np.sum((_llr < 0) != _cw.astype(bool)))
    _res = int(np.sum(_hard != _cw))

    _fig, _ax = plt.subplots(figsize=(8, 2.8))
    _s = np.where(_cw == 0, 1, -1)
    _ax.hist(np.clip(_llr * _s, -30, 60), bins=120, alpha=0.6, label="channel LLR (signed to the truth)")
    _ax.hist(np.clip(_L * _s, -30, 60), bins=120, alpha=0.6, label="after decoding")
    _ax.axvline(0, color="k", lw=0.8)
    _ax.set_xlabel("LLR × (±1): left of 0 means a wrong decision")
    _ax.legend(fontsize=8)
    _fig.tight_layout()
    mo.vstack(
        [
            mo.md(
                f"**{_code.name}**, k = {_code.k}, n = {_code.n}, rate {_code.rate:.3f}: "
                f"channel errors **{_ch}** → after {_it} iterations **{_res}** "
                f"({'✅ decoded' if _res == 0 else '❌ failed'}) in {_dt:.2f} s"
            ),
            _fig,
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Where next

    * **7 · The DVB-S2 chain**: the LDPC code inside the full transmitter (BCH,
      interleaver, APSK constellations, PL framing) and the receiver.
    * **8 · BER explorer**: simulated waterfalls of all 28 MODCODs against the
      Shannon and BICM limits.
    """)
    return


if __name__ == "__main__":
    app.run()
