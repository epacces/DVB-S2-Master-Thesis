import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="3 · Cyclic codes and LFSR encoders")


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
    import numpy as np

    from dvbs2 import poly2
    from dvbs2.codes.cyclic import CyclicCode, lfsr_divide_trace, lfsr_encode_trace, register_to_parity
    return CyclicCode, lfsr_divide_trace, lfsr_encode_trace, mo, np, poly2, register_to_parity


@app.cell
def _(mo):
    mo.md(r"""
    # 3 · Cyclic codes: encoding is polynomial division

    Read a block of *n* bits as the coefficients of a polynomial, first bit =
    highest power:

    $$1\,0\,1\,1 \;\longleftrightarrow\; x^3 + x + 1 .$$

    A **cyclic code** is the set of multiples of a **generator polynomial**
    $g(x)$ of degree $r = n - k$. To encode a message $m(x)$ *systematically*
    (message bits sent unchanged, followed by $r$ parity bits) shift it up by $r$
    places and subtract the remainder of the division by $g(x)$:

    $$c(x) = m(x)\,x^r + \big[m(x)\,x^r \bmod g(x)\big].$$

    Then $c(x)$ is a multiple of $g(x)$. Everything is binary, so "minus" is XOR
    and the division needs no carries. The BCH code of DVB-S2 is
    exactly this, with a $g(x)$ of degree 192, and the whole of chapters 3–4 of the
    thesis is about doing this division fast.
    """)
    return


@app.cell
def _(mo):
    dividend_in = mo.ui.text(value="1101011000", label="dividend a(x) (bits, highest power first)")
    divisor_in = mo.ui.text(value="1011", label="divisor g(x)")
    mo.vstack([mo.md("## Long division over GF(2), step by step"), mo.hstack([dividend_in, divisor_in], justify="start", gap=2)])
    return dividend_in, divisor_in


@app.cell
def _(dividend_in, divisor_in, mo, poly2):
    _a_txt = dividend_in.value.strip().replace(" ", "")
    _g_txt = divisor_in.value.strip().replace(" ", "").lstrip("0")
    if not _a_txt or not _g_txt or set(_a_txt + _g_txt) - {"0", "1"}:
        _out = mo.callout(mo.md("Enter binary strings; the divisor must contain a 1."), kind="warn")
    else:
        _n, _d = len(_a_txt), len(_g_txt)
        _a, _g = int(_a_txt, 2), int(_g_txt, 2)
        _lines = [f"  {_a_txt}    a(x) = {poly2.to_str(_a)}"]
        _rows = ["| step | remainder before | subtract g(x)·x^s | quotient bit |", "|---|---|---|---|"]
        _rem, _q, _k = _a, 0, 0
        while _rem and poly2.degree(_rem) >= _d - 1:
            _shift = poly2.degree(_rem) - (_d - 1)
            _sub = _g << _shift
            _k += 1
            _rows.append(f"| {_k} | `{format(_rem, f'0{_n}b')}` | `{format(_sub, f'0{_n}b')}` (s = {_shift}) | x^{_shift} |")
            _pad = " " * (_n - poly2.degree(_rem) - 1)
            _lines.append(f"  {_pad}{_g_txt}{' ' * _shift}   ⊕ g(x)·x^{_shift}")
            _rem ^= _sub
            _q |= 1 << _shift
            _lines.append(f"  {'-' * _n}")
            _lines.append(f"  {format(_rem, f'0{_n}b')}")
        _r = _d - 1
        _out = mo.vstack(
            [
                mo.md("```\n" + "\n".join(_lines) + "\n```"),
                mo.md("\n".join(_rows)),
                mo.md(
                    f"quotient **q(x) = {poly2.to_str(_q)}**, remainder **r(x) = {poly2.to_str(_rem)}** "
                    f"= `{format(_rem, f'0{_r}b') if _r else ''}` ({_r} bits). "
                    f"Check: q(x)·g(x) + r(x) = {poly2.to_str(poly2.mul(_q, _g) ^ _rem)} "
                    f"{'✅' if poly2.mul(_q, _g) ^ _rem == _a else '❌'}"
                ),
                mo.md(
                    "Each step looks only at the leading bit and XORs a shifted copy of *g*. "
                    "That is what makes it a good fit for a shift register, below."
                ),
            ]
        )
    _out
    return


@app.cell
def _(mo):
    CODES = {
        "(7,4) Hamming, g = x³ + x + 1": (7, 0b1011),
        "(7,4) Hamming, g = x³ + x² + 1": (7, 0b1101),
        "(15,11) Hamming, g = x⁴ + x + 1": (15, 0b10011),
        "(15,7) BCH t=2, g = x⁸ + x⁷ + x⁶ + x⁴ + 1": (15, 0b111010001),
        "(15,5) BCH t=3, g = x¹⁰ + x⁸ + x⁵ + x⁴ + x² + x + 1": (15, 0b10100110111),
    }
    code_sel = mo.ui.dropdown(options=list(CODES), value="(7,4) Hamming, g = x³ + x + 1", label="code")
    mo.vstack([mo.md("## Systematic encoding"), code_sel])
    return CODES, code_sel


@app.cell
def _(CODES, CyclicCode, code_sel, mo):
    _n, _g = CODES[code_sel.value]
    code = CyclicCode(_n, _g)
    _init = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1][: code.k]
    msg_bits = mo.ui.array([mo.ui.switch(value=bool(v), label=f"m{code.k - 1 - i}") for i, v in enumerate(_init)])
    mo.hstack([mo.md("**message** (first bit = highest power)"), msg_bits.hstack()], justify="start", gap=1)
    return code, msg_bits


@app.cell
def _(code, mo, msg_bits, np, poly2):
    msg = np.array([int(v) for v in msg_bits.value], dtype=np.uint8)
    codeword = code.encode(msg)
    _m = poly2.from_bits(msg)
    _par = code.parity(msg)
    _bits = lambda a: "".join(map(str, a))  # noqa: E731
    mo.md(
        f"""
    | | polynomial | bits |
    |---|---|---|
    | g(x) | {poly2.to_str(code.g)} | `{format(code.g, f'0{code.r + 1}b')}` |
    | m(x) | {poly2.to_str(_m)} | `{_bits(msg)}` |
    | m(x)·x^{code.r} | {poly2.to_str(_m << code.r)} | `{_bits(msg)}{'0' * code.r}` |
    | remainder = parity | {poly2.to_str(poly2.from_bits(_par))} | `{_bits(_par)}` |
    | **c(x)** | {poly2.to_str(poly2.from_bits(codeword))} | `{_bits(msg)}` `{_bits(_par)}` |

    The codeword is the message followed by {code.r} parity bits, and c(x) mod g(x) =
    {poly2.to_str(code.syndrome_poly(codeword))} {'✅' if code.is_codeword(codeword) else '❌'}.
    The code is **cyclic** because g(x) divides x^{code.n} + 1:
    {'yes ✅' if code.is_cyclic_generator() else 'no'}.
    """
    )
    return codeword, msg


@app.cell
def _(mo):
    mo.md(r"""
    ## The LFSR encoder, clock by clock

    A shift register of $r$ flip-flops with XOR gates at the taps of $g(x)$ does
    the long division one bit per clock. Stage *j* holds the coefficient of
    $x^j$ of the running remainder; when the bit leaving the top stage is 1, the
    feedback adds $g(x)$. The thesis compares two versions:

    * **n-clock (division circuit, `BCH_s_enc` in `main.c`)**: the input enters at
      stage 0, so all *n* bits $m(x)x^r$, *including the r trailing zeros*,
      must be shifted in: *n* clocks.
    * **k-clock (premultiplied, `BCHenc::Run` in `serial.c`)**: the input is XORed
      with the top stage, which is the same as dividing $m(x)\,x^r$ directly.
      After *k* clocks the register already holds the parity bits, saving *r* cycles.
    """)
    return


@app.cell
def _(mo):
    mode_sel = mo.ui.radio(options=["k-clock (premultiplied)", "n-clock (division)"], value="k-clock (premultiplied)",
                           label="encoder", inline=True)
    mode_sel
    return (mode_sel,)


@app.cell
def _(code, mo, mode_sel):
    _len = code.k if mode_sel.value.startswith("k") else code.n
    clock = mo.ui.slider(0, _len, value=0, label="clock", show_value=True, full_width=True)
    clock
    return (clock,)


@app.function
def register_svg(state, g, r, kclock, fb, inp):
    """Shift register dividing by g: stage j holds the coefficient of x^j; inputs as described in the notebook."""
    w, x0, y, top = 60, 90, 100, 34
    width = x0 + r * w + 110
    red, grey = "#d62728", "#999"
    fbc = red if fb else grey
    out = [f'<svg viewBox="0 0 {width} 170" width="{width}" style="font-family:sans-serif;max-width:100%">']
    x_last = x0 + (r - 1) * w + 36
    if kclock:
        xo = x_last + 34  # XOR of input and top stage
        out.append(f'<line x1="{x_last}" y1="{y}" x2="{xo - 9}" y2="{y}" stroke="currentColor"/>')
        out.append(f'<circle cx="{xo}" cy="{y}" r="9" fill="none" stroke="currentColor"/>')
        out.append(f'<text x="{xo}" y="{y + 5}" text-anchor="middle" font-size="15" fill="currentColor">+</text>')
        out.append(f'<line x1="{xo}" y1="{y + 50}" x2="{xo}" y2="{y + 9}" stroke="currentColor"/>')
        out.append(f'<text x="{xo}" y="{y + 64}" text-anchor="middle" font-size="12" fill="currentColor">'
                   f'input {"" if inp is None else inp}</text>')
        out.append(f'<path d="M{xo} {y - 9} V{top} H{x0 - 40}" fill="none" stroke="{fbc}" stroke-width="2"/>')
    else:
        out.append(f'<path d="M{x_last} {y} H{x_last + 34} V{top} H{x0 - 40}" fill="none" stroke="{fbc}" stroke-width="2"/>')
        out.append(f'<text x="{x0 - 85}" y="{y + 30}" font-size="12" fill="currentColor">input {"" if inp is None else inp}</text>')
        out.append(f'<line x1="{x0 - 85}" y1="{y + 14}" x2="{x0 - 28}" y2="{y + 14}" stroke="currentColor"/>')
        out.append(f'<line x1="{x0 - 22}" y1="{y + 14}" x2="{x0 - 22}" y2="{y + 9}" stroke="currentColor"/>')
    out.append(f'<text x="{x0 + r * w / 2 - 30}" y="{top - 12}" font-size="12" fill="{fbc}">feedback = {int(fb)}</text>')
    for j in range(r):
        x = x0 + j * w
        tap = (g >> j) & 1
        cx = x - 22
        if tap:
            out.append(f'<line x1="{cx}" y1="{top}" x2="{cx}" y2="{y - 9}" stroke="{fbc}" stroke-width="2"/>')
            out.append(f'<circle cx="{cx}" cy="{y}" r="9" fill="none" stroke="currentColor"/>')
            out.append(f'<text x="{cx}" y="{y + 5}" text-anchor="middle" font-size="15" fill="currentColor">+</text>')
            out.append(f'<line x1="{cx + 9}" y1="{y}" x2="{x}" y2="{y}" stroke="currentColor"/>')
            out.append(f'<text x="{cx + 2}" y="{top - 2}" font-size="10" fill="currentColor">g{j}</text>')
        if j > 0:
            px = x0 + (j - 1) * w + 36
            out.append(f'<line x1="{px}" y1="{y}" x2="{cx - 9 if tap else x}" y2="{y}" stroke="currentColor"/>')
        bit = int(state[j])
        out.append(f'<rect x="{x}" y="{y - 18}" width="36" height="36" rx="4" fill="{"#4c78a8" if bit else "none"}" stroke="currentColor"/>')
        out.append(f'<text x="{x + 18}" y="{y + 7}" text-anchor="middle" font-size="18" fill="{"white" if bit else "currentColor"}">{bit}</text>')
        out.append(f'<text x="{x + 18}" y="{y + 38}" text-anchor="middle" font-size="11" fill="currentColor">x^{j}</text>')
    out.append("</svg>")
    return "".join(out)


@app.cell
def _(clock, code, codeword, lfsr_divide_trace, lfsr_encode_trace, mo, mode_sel, msg, np, register_to_parity):
    _k = mode_sel.value.startswith("k")
    _inputs = msg if _k else np.concatenate([msg, np.zeros(code.r, np.uint8)])
    _trace = lfsr_encode_trace(msg, code.g) if _k else lfsr_divide_trace(_inputs, code.g)
    _t = clock.value
    _state = _trace[_t]
    _next_in = int(_inputs[_t]) if _t < _inputs.size else None
    _fb = bool(_state[code.r - 1] ^ (_next_in or 0)) if _k else bool(_state[code.r - 1])
    _svg = register_svg(_state, code.g, code.r, _k, _fb and _next_in is not None, _next_in)
    _rows = ["| clock | input bit | register (x^0 … x^%d) |" % (code.r - 1), "|---|---|---|"]
    for _c in range(len(_trace)):
        _inb = str(_inputs[_c - 1]) if _c else "–"
        _reg = "".join(map(str, _trace[_c]))
        _rows.append(f"| {'**%d**' % _c if _c == _t else _c} | {_inb} | `{_reg}` |")
    _done = _t == _inputs.size
    _parity = register_to_parity(_trace[-1])
    _msg = (
        f"Finished after **{_inputs.size}** clocks: the register, read from the top stage down, is "
        f"`{''.join(map(str, _parity))}` = the parity bits of the codeword "
        f"`{''.join(map(str, codeword[code.k:]))}` {'✅' if np.array_equal(_parity, codeword[code.k:]) else '❌'}."
        if _done
        else f"Next input bit: **{_next_in}**. "
        + ("Feedback = top stage ⊕ input" if _k else "Feedback = top stage")
        + f" = **{int(_fb)}**, so the next clock {'adds g(x) (red taps)' if _fb else 'only shifts'}."
    )
    mo.vstack(
        [
            mo.Html(_svg),
            mo.md(_msg),
            mo.md(
                f"The k-clock encoder needs **{code.k}** clocks, the n-clock one **{code.n}**. "
                "In DVB-S2 (k = 32208, r = 192 for rate 1/2) the difference is small, but both still "
                "need one clock per bit. At 1 Gbit/s that is a 1 GHz clock, which is why chapter 4 "
                "processes *p* = 8 bits per clock (notebook 5)."
            ),
            mo.accordion({"register trace": mo.md("\n".join(_rows))}),
        ]
    )
    return


@app.cell
def _(code, mo):
    shift = mo.ui.slider(0, code.n - 1, value=1, label="cyclic shift s", show_value=True)
    mo.vstack([mo.md("## Why “cyclic”: rotate a codeword, get another codeword"), shift])
    return (shift,)


@app.cell
def _(code, codeword, mo, np, poly2, shift):
    _rot = np.roll(codeword, -shift.value)
    _rem = code.syndrome_poly(_rot)
    mo.md(
        f"""
    `{''.join(map(str, codeword))}` rotated left by {shift.value} → `{''.join(map(str, _rot))}`

    remainder mod g(x): **{poly2.to_str(_rem)}** {'✅ still a codeword' if _rem == 0 else '❌'}

    Rotating is multiplying by $x^s$ modulo $x^n + 1$, and g(x) divides $x^n + 1$, so
    multiples of g stay multiples of g. DVB-S2 uses **shortened** BCH codes
    (n = 16200 … 58320 instead of 65535). They lose this property but keep the
    encoder and the decoder of the full-length code.
    """
    )
    return


@app.cell
def _(code, mo):
    err_flips = mo.ui.array([mo.ui.checkbox(label=str(code.n - 1 - i)) for i in range(code.n)])
    mo.vstack(
        [
            mo.md("## Error detection: the syndrome is a remainder"),
            mo.hstack([mo.md("**flip bit (power of x)**"), err_flips.hstack()], justify="start", gap=1),
        ]
    )
    return (err_flips,)


@app.cell
def _(code, codeword, err_flips, lfsr_divide_trace, mo, np, poly2):
    _e = np.array([int(v) for v in err_flips.value], dtype=np.uint8)
    _rx = codeword ^ _e
    _s = code.syndrome_poly(_rx)
    _s_lfsr = lfsr_divide_trace(_rx, code.g)[-1]
    _span = np.flatnonzero(_e)
    _burst = int(_span[-1] - _span[0] + 1) if _span.size else 0
    if not _span.size:
        _verdict = "No errors: remainder 0."
    elif _s:
        _verdict = f"Remainder ≠ 0, so the errors are **detected** ({_span.size} flipped bit(s), burst length {_burst})."
    else:
        _verdict = ("Remainder 0: the error pattern is itself a codeword, so it goes **undetected**. "
                    "That needs at least d_min flips.")
    mo.md(
        f"""
    received `{''.join(map(str, _rx))}`

    syndrome s(x) = r(x) mod g(x) = **{poly2.to_str(_s)}**. The same division LFSR, fed
    the received word, ends in `{''.join(map(str, _s_lfsr))}` (stages x^0 … x^{code.r - 1}).

    {_verdict}

    Since e(x) mod g(x) = 0 only when e(x) is a multiple of g(x), **every burst of length
    ≤ r = {code.r} is detected**: a non-zero polynomial of degree < r cannot be a multiple of g.
    This is the principle of the CRC-8 that protects the DVB-S2 BBHEADER. To *locate* the
    errors you need more structure: the BCH codes of notebook 4.
    """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Where next

    * **4 · BCH codes**: choosing g(x) so that up to *t* errors can be *corrected*.
    * **5 · Parallel BCH encoder**: the state-space model that runs this LFSR 8 bits per clock.
    """)
    return


if __name__ == "__main__":
    app.run()
