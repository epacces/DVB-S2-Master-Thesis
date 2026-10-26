import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="4 · BCH codes")


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
    return BCHCode, dvbs2_bch, mo, np, plt, poly2, time


@app.cell
def _(mo):
    mo.md(r"""
    # 4 · BCH codes: correcting *t* errors

    A Hamming code corrects one error per block. **BCH codes** (Bose,
    Ray-Chaudhuri, Hocquenghem, 1959–60) correct any *t* errors. You choose *t*,
    and the code is built from the arithmetic of the finite field GF(2^m)
    (notebook 2).

    **Construction.** Let α be a primitive element of GF(2^m) and
    $n = 2^m - 1$. The generator polynomial is the smallest binary polynomial
    with α, α², …, α^{2t} among its roots:

    $$g(x) = \mathrm{lcm}\{m_1(x), m_3(x), \dots, m_{2t-1}(x)\}$$

    where $m_i(x)$ is the minimal polynomial of α^i. The even powers come for free,
    because α^{2i} is a conjugate of α^i and has the same minimal polynomial.
    The BCH bound guarantees $d_{min} \ge 2t + 1$.

    **Decoding**, as in chapter 5 of the thesis (``errdet.c`` and ``berlmass.c``):

    1. **Syndromes** $S_j = r(\alpha^j)$, $j = 1 … 2t$: all zero exactly when
       *r* is a codeword.
    2. **Berlekamp–Massey** finds the shortest LFSR that generates the syndromes,
       whose connection polynomial is the **error locator**
       $\Lambda(x) = \prod_i (1 - X_i x)$.
    3. **Chien search** tries every position *p* and flags an error where
       $\Lambda(\alpha^{-p}) = 0$.
    """)
    return


@app.cell
def _(mo):
    m_slider = mo.ui.slider(3, 8, value=4, label="field GF(2^m), m", show_value=True)
    m_slider
    return (m_slider,)


@app.cell
def _(BCHCode, m_slider, mo):
    _m = m_slider.value
    _tmax = 1
    for _t in range(1, min((1 << _m) // 2, 16)):
        try:
            BCHCode(_m, _t)
            _tmax = _t
        except ValueError:
            break
    t_slider = mo.ui.slider(1, _tmax, value=min(2, _tmax), label="correcting capability t", show_value=True)
    t_slider
    return (t_slider,)


@app.cell
def _(BCHCode, m_slider, mo, poly2, t_slider):
    code = BCHCode(m_slider.value, t_slider.value)
    gf = code.gf

    def pw(a):
        """Field element in power form."""
        a = int(a)
        if a == 0:
            return "0"
        e = int(gf.log[a])
        return "1" if e == 0 else f"α^{e}"

    _rows = []
    _seen = set()
    for _i in range(1, 2 * code.t, 2):
        _mp = gf.minimal_polynomial(_i)
        _dup = _mp in _seen
        _seen.add(_mp)
        _rows.append(
            f"| α^{_i} | {{{', '.join(map(str, gf.cyclotomic_coset(_i)))}}} | ${poly2.to_str(_mp)}$ | "
            + ("already a factor" if _dup else "✓ multiplied in")
            + " |"
        )
    mo.md(
        f"""
    ## The code: **BCH({code.n}, {code.k})**, t = {code.t}

    Field: {gf}. Rate {code.k / code.n:.3f}, {code.r} parity bits, $d_{{min}} \\ge {2 * code.t + 1}$.

    | root | cyclotomic coset (exponents) | minimal polynomial | |
    |---|---|---|---|
    {chr(10).join(_rows)}

    $$g(x) = {poly2.to_str(code.g)}$$

    Each new coset adds at most *m* parity bits. That is why a *t*-error-correcting
    BCH code needs at most $m\\,t$ parity bits: DVB-S2 uses $16 \\times 12 = 192$.
    """
    )
    return code, gf, pw


@app.cell
def _(mo):
    msg_seed = mo.ui.button(label="new random message", value=0, on_click=lambda v: v + 1)
    return (msg_seed,)


@app.cell
def _(code, mo, msg_seed, np):
    _rng = np.random.default_rng(7 + msg_seed.value)
    _bits = "".join(map(str, _rng.integers(0, 2, code.k)))
    msg_text = mo.ui.text(value=_bits, label=f"message ({code.k} bits, editable)", full_width=True)
    return (msg_text,)


@app.cell
def _(code, mo):
    flips = (
        mo.ui.array([mo.ui.checkbox(label=str(i)) for i in range(code.n)]) if code.n <= 63 else None
    )
    n_random = mo.ui.slider(0, min(code.t + 4, code.n), value=0, label="extra random errors", show_value=True)
    err_seed = mo.ui.button(label="new random errors", value=0, on_click=lambda v: v + 1)
    return err_seed, flips, n_random


@app.cell
def _(code, err_seed, flips, mo, msg_seed, msg_text, n_random):
    _flip_ui = (
        [mo.md(f"**click to flip received bit** (positions 0 … {code.n - 1}, transmission order)"), flips.hstack(wrap=True)]
        if flips is not None
        else [mo.md(f"n = {code.n} is too long for one checkbox per bit: use random errors.")]
    )
    mo.vstack(
        [
            mo.md("## Encode, corrupt, decode"),
            mo.hstack([msg_text, msg_seed], align="end"),
            *_flip_ui,
            mo.hstack([n_random, err_seed], justify="start"),
        ]
    )
    return


@app.cell
def _(code, err_seed, flips, msg_text, n_random, np):
    _txt = "".join(c for c in msg_text.value if c in "01")
    message = np.array([int(c) for c in (_txt + "0" * code.k)[: code.k]], dtype=np.uint8)
    sent = code.encode(message)
    errors = np.zeros(code.n, dtype=np.uint8)
    if flips is not None:
        errors[[i for i, v in enumerate(flips.value) if v]] = 1
    _rng = np.random.default_rng(1000 + err_seed.value)
    _free = np.flatnonzero(errors == 0)
    errors[_rng.choice(_free, min(n_random.value, _free.size), replace=False)] = 1
    received = sent ^ errors
    bm_trace = []
    result = code.decode(received, bm_trace)
    return bm_trace, errors, message, received, result, sent


@app.cell
def _(code, errors, mo, np, received, result, sent):
    def _strip(bits, title, mark=None, mark_color="#ffbf00"):
        w = max(3.0, min(18.0, 900.0 / code.n))
        out = [f'<text x="0" y="13" font-size="12" fill="currentColor">{title}</text>']
        for i, b in enumerate(bits):
            x = 110 + i * w
            parity = i >= code.k
            fill = ("#4c78a8" if parity else "#555") if b else ("#c6d6ea" if parity else "#ddd")
            if mark is not None and mark[i]:
                fill = mark_color
            out.append(f'<rect x="{x:.1f}" y="2" width="{w - 1:.1f}" height="14" fill="{fill}"/>')
        return out

    _corrected = np.zeros(code.n, dtype=np.uint8)
    _corrected[result.error_positions] = 1
    _rows = [
        _strip(sent, "sent"),
        _strip(errors, "channel errors", errors, "#d62728"),
        _strip(received, "received", errors),
        _strip(result.codeword, "decoded", _corrected, "#2ca02c"),
    ]
    _svg = [f'<svg viewBox="0 0 {110 + 900 + 10} {len(_rows) * 22}" width="100%" style="font-family:sans-serif">']
    for _j, _r in enumerate(_rows):
        _svg.append(f'<g transform="translate(0,{_j * 22})">' + "".join(_r) + "</g>")
    _svg.append("</svg>")

    _nerr = int(errors.sum())
    if not result.success:
        _verdict = f"❗ **decoder failure**: {_nerr} errors > t = {code.t}. The decoder *knows* it cannot fix this word and leaves it unchanged."
    elif np.array_equal(result.codeword, sent):
        _verdict = f"✅ **corrected** {result.n_errors} error(s) at positions {list(map(int, result.error_positions))}"
    else:
        _verdict = (
            f"⚠️ **miscorrection**: {_nerr} errors pushed the word closer to *another* codeword, "
            f"and the decoder 'corrected' it there. Undetectable at the receiver."
        )
    mo.vstack(
        [
            mo.Html("".join(_svg)),
            mo.md(
                "Grey cells are message bits, blue cells parity bits (dark = 1). "
                "Red marks channel errors, yellow the received flipped bits, green the bits the decoder flipped.\n\n"
                + _verdict
            ),
        ]
    )
    return


@app.cell
def _(code, gf, mo, pw, result):
    _rows = "\n".join(
        f"| S{_j + 1} | {pw(_s)} | `{gf.to_bits(_s)}` |" for _j, _s in enumerate(result.syndromes)
    )
    mo.md(
        f"""
    ### Step 1 · syndromes $S_j = r(\\alpha^j)$

    | | power form | binary (α^{gf.m - 1} … 1) |
    |---|---|---|
    {_rows}

    For a binary code $S_{{2j}} = S_j^2$, so only the odd syndromes need computing.
    {"All zero: the received word is a codeword, nothing to do." if not any(result.syndromes) else ""}
    """
    )
    return


@app.cell
def _(bm_trace, mo, pw):
    def _lam(c):
        terms = []
        for i, a in enumerate(c):
            if a:
                coef = pw(a)
                term = coef if i == 0 else (("" if coef == "1" else coef + "·") + ("x" if i == 1 else f"x^{i}"))
                terms.append(term)
        return " + ".join(terms) or "0"

    if bm_trace:
        _rows = "\n".join(
            f"| {s.k + 1} | `{pw(s.syndrome)}` | `{pw(s.discrepancy)}` | {s.L} | `{_lam(s.locator)}` |" for s in bm_trace
        )
        _out = mo.md(
            f"""
    ### Step 2 · Berlekamp–Massey

    Each iteration predicts the next syndrome with the current LFSR Λ(x). A
    non-zero **discrepancy** Δ means the prediction failed, and Λ is corrected
    with a shifted copy of an earlier version. When 2L ≤ k the register also has
    to grow: L ← k + 1 − L.

    | k | S_k | Δ | L | Λ(x) |
    |---|---|---|---|---|
    {_rows}

    The final degree L is the number of errors the decoder believes occurred.
    """
        )
    else:
        _out = mo.md("### Step 2 · Berlekamp–Massey\n\nNot needed: the syndromes are zero.")
    _out
    return


@app.cell
def _(code, gf, mo, np, plt, result):
    _lam = result.locator
    _p = np.arange(code.n)
    _vals = gf.poly_eval(_lam, gf.alpha_pow(-_p))
    _idx = code.n - 1 - _p  # array position of power p
    _zero = _vals == 0
    _fig, _ax = plt.subplots(figsize=(9, 2.6))
    _ax.vlines(_idx, 0, _vals, color="#9aa", lw=1)
    _ax.plot(_idx[~_zero], _vals[~_zero], "o", ms=3, color="#4c78a8")
    _ax.plot(_idx[_zero], np.zeros(_zero.sum()), "o", ms=8, color="#d62728", label="Λ(α^-p) = 0 → error here")
    _ax.set_xlabel("position in the codeword (transmission order)")
    _ax.set_ylabel("Λ(α^-p) as integer")
    _ax.set_xlim(-1, code.n)
    _ax.legend(loc="upper right", fontsize=8)
    _ax.set_title("Chien search: evaluate the error locator at every position")
    _L = len(_lam) - 1
    mo.vstack(
        [
            mo.md(
                "### Step 3 · Chien search\n\n"
                f"Λ(x) has degree {_L}; the search finds **{int(_zero.sum())}** root(s) among the {code.n} positions. "
                + (
                    "Number of roots = degree: the error pattern is located."
                    if result.success
                    else "Fewer roots than the degree (or degree > t): **decoding failure**, detected."
                )
            ),
            _fig,
        ]
    )
    return


@app.cell
def _(code, mo):
    trials = mo.ui.slider(10, 200, step=10, value=40, label="trials per error count", show_value=True)
    run_exp = mo.ui.run_button(label="run experiment")
    mo.vstack(
        [
            mo.md(
                f"""
    ## Beyond *t*: failure or miscorrection?

    With more than t = {code.t} errors, two things can happen. Usually the
    decoder finds a locator without enough roots and **declares a failure**. Sometimes
    the received word lands within distance t of a *different* codeword and gets
    **miscorrected**. The longer the code and the larger t, the rarer
    miscorrection becomes. DVB-S2 relies on this: the BCH outer code reports when the LDPC
    inner decoder leaves too many errors.
    """
            ),
            mo.hstack([trials, run_exp], justify="start"),
        ]
    )
    return run_exp, trials


@app.cell
def _(code, mo, np, plt, run_exp, trials):
    mo.stop(not run_exp.value, mo.md("*Press **run experiment**.*"))
    _rng = np.random.default_rng(5)
    _counts = np.arange(0, min(code.t + 5, code.n) + 1)
    _res = {"corrected": [], "failure (detected)": [], "miscorrected": []}
    for _e in _counts:
        _c = {k: 0 for k in _res}
        for _ in range(trials.value):
            _cw = code.encode(_rng.integers(0, 2, code.k))
            _rx = _cw.copy()
            _rx[_rng.choice(code.n, _e, replace=False)] ^= 1
            _d = code.decode(_rx)
            if not _d.success:
                _c["failure (detected)"] += 1
            elif np.array_equal(_d.codeword, _cw):
                _c["corrected"] += 1
            else:
                _c["miscorrected"] += 1
        for k in _res:
            _res[k].append(_c[k] / trials.value)
    _fig, _ax = plt.subplots(figsize=(8, 3.2))
    _bottom = np.zeros(_counts.size)
    for (_k, _v), _col in zip(_res.items(), ("#2ca02c", "#ff7f0e", "#d62728")):
        _ax.bar(_counts, _v, bottom=_bottom, color=_col, label=_k)
        _bottom += np.array(_v)
    _ax.axvline(code.t + 0.5, color="k", ls=":", lw=1)
    _ax.text(code.t + 0.6, 1.02, "t", fontsize=10)
    _ax.set_xlabel("number of channel errors")
    _ax.set_ylabel("fraction of words")
    _ax.legend(fontsize=8, loc="lower left")
    _fig
    return


@app.cell
def _(mo):
    run_dvb = mo.ui.run_button(label="encode and decode one DVB-S2 frame")
    mo.vstack(
        [
            mo.md(
                r"""
    ## The real thing: the DVB-S2 outer code

    For normal FECFRAMEs DVB-S2 uses BCH codes over GF(2^16), with primitive polynomial
    $x^{16} + x^5 + x^3 + x^2 + 1$ (the ``32+8+4+1`` in the thesis' ``main.c``),
    shortened from $n = 65535$ to $N_{bch} \le 58320$. Here is rate 1/2:
    $t = 12$ and 192 parity bits, the code the thesis' parallel encoder implements
    (notebook 5).
    """
            ),
            run_dvb,
        ]
    )
    return (run_dvb,)


@app.cell
def _(dvbs2_bch, mo, np, run_dvb, time):
    mo.stop(not run_dvb.value, mo.md("*Press the button (building GF(2^16) takes a moment).*"))
    _t0 = time.perf_counter()
    _code = dvbs2_bch("1/2")
    _t_build = time.perf_counter() - _t0
    _rng = np.random.default_rng(12)
    _msg = _rng.integers(0, 2, _code.k).astype(np.uint8)
    _t0 = time.perf_counter()
    _cw = _code.encode(_msg)
    _t_enc = time.perf_counter() - _t0
    _rows = []
    for _e in (12, 13):
        _rx = _cw.copy()
        _pos = np.sort(_rng.choice(_code.n, _e, replace=False))
        _rx[_pos] ^= 1
        _t0 = time.perf_counter()
        _d = _code.decode(_rx)
        _dt = time.perf_counter() - _t0
        _ok = _d.success and np.array_equal(_d.codeword, _cw)
        _rows.append(
            f"| {_e} | {'✅ corrected' if _ok else ('❗ failure detected' if not _d.success else '⚠️ miscorrected')} | {_dt * 1e3:.1f} ms |"
        )
    mo.md(
        f"""
    **{_code.name}**: n = {_code.n}, k = {_code.k}, t = {_code.t}, deg g = {_code.r}.
    Code construction {_t_build * 1e3:.0f} ms (minimal polynomials of α, α³, …, α²³), encoding {_t_enc * 1e3:.1f} ms.

    | errors | outcome | decode time |
    |---|---|---|
    {chr(10).join(_rows)}

    The 12 error positions are found among 32 400 bits by a Chien search over all
    of them. In hardware the search runs in parallel, like the encoder in notebook 5.
    """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Where next

    * **5 · Parallel BCH encoder**: the thesis' 8-bit-per-clock encoder, derived from the LFSR's state-space model.
    * **6 · LDPC basics**: the inner code of DVB-S2, decoded by message passing.
    """)
    return


if __name__ == "__main__":
    app.run()
