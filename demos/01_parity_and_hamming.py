import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="1 · Parity and Hamming codes")


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

    from dvbs2.codes.hamming import HammingCode
    return HammingCode, mo, np, plt


@app.cell
def _(mo):
    mo.md(r"""
    # 1 · Parity bits and Hamming codes

    A channel flips bits. **Forward error correction (FEC)** adds structured
    redundancy so the receiver can find and undo those flips without asking for a
    retransmission. That matters on a satellite link, where a round trip takes about
    half a second.

    This notebook starts from the simplest ideas (repeat every bit, add one
    parity bit) and builds up to the **Hamming code**: the first code that corrects
    errors efficiently and the ancestor of the BCH and LDPC codes used in DVB-S2.

    The model channel is the **binary symmetric channel** BSC(*p*): every bit is
    flipped independently with probability *p*.
    """)
    return


@app.cell
def _(mo):
    p_slider = mo.ui.slider(0.0, 0.2, step=0.005, value=0.05, label="bit-flip probability p", show_value=True)
    text_in = mo.ui.text(value="DVB-S2 brings TV from 36000 km away!", label="message", full_width=True)
    reseed = mo.ui.button(label="new channel noise", value=0, on_click=lambda v: v + 1)
    mo.vstack([mo.md("## Send a message through a noisy channel"), text_in, mo.hstack([p_slider, reseed])])
    return p_slider, reseed, text_in


@app.cell
def _(HammingCode, mo, np, p_slider, reseed, text_in):
    def _to_bits(s):
        return np.unpackbits(np.frombuffer(s.encode("latin-1", "replace"), dtype=np.uint8))

    def _to_text(bits):
        return np.packbits(bits[: bits.size // 8 * 8]).tobytes().decode("latin-1")

    _rng = np.random.default_rng(1000 + reseed.value)
    _bits = _to_bits(text_in.value)
    _p = p_slider.value

    def _bsc(x):
        return x ^ (_rng.random(x.shape) < _p).astype(np.uint8)

    # uncoded
    _rx_plain = _bsc(_bits)
    # repetition (3,1): majority vote
    _rx_rep = _bsc(np.repeat(_bits, 3)).reshape(-1, 3)
    _dec_rep = (_rx_rep.sum(axis=1) >= 2).astype(np.uint8)
    # Hamming (7,4)
    _h = HammingCode(3)
    _cw = np.array([_h.encode(b) for b in _bits.reshape(-1, 4)])
    _rx_h = _bsc(_cw)
    _dec_h = np.concatenate([_h.decode(w).data for w in _rx_h])

    def _row(name, rate, dec, sent):
        errs = int(np.sum(dec != _bits))
        return f"| {name} | {rate} | {sent} | {errs} | `{_to_text(dec)}` |"

    mo.md(
        "\n".join(
            [
                "| scheme | rate | bits sent | bit errors left | received text |",
                "|---|---|---|---|---|",
                _row("uncoded", "1", _rx_plain, _bits.size),
                _row("repetition (3,1)", "1/3", _dec_rep, 3 * _bits.size),
                _row("Hamming (7,4)", "4/7", _dec_h, 7 * _bits.size // 4),
            ]
        )
        + "\n\nRepetition is strong but triples the bandwidth. Hamming (7,4) costs only 75 % "
        "extra bits and still fixes any single error in each 7-bit block. Push *p* up "
        "and see where each scheme breaks down."
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## One parity bit: detection, not correction

    Append the XOR of the data bits, so that every codeword has an **even number of 1s**.
    Any *odd* number of flips makes the parity odd and is detected; an even number
    goes unnoticed, and nothing says *which* bit is wrong.

    Hamming's idea (1950) is to use several parity bits, each checking an
    overlapping subset of the data. The *pattern* of failed checks, the
    **syndrome**, then points at the flipped bit.
    """)
    return


@app.cell
def _(mo):
    data_bits = mo.ui.array([mo.ui.switch(value=v, label=f"d{i + 1}") for i, v in enumerate((True, False, True, True))])
    flips = mo.ui.array([mo.ui.checkbox(label=str(i + 1)) for i in range(7)])
    mo.vstack(
        [
            mo.md("## Hamming (7,4) on a Venn diagram"),
            mo.hstack([mo.md("**data bits**"), data_bits.hstack()], justify="start", gap=1),
            mo.hstack([mo.md("**channel flips position**"), flips.hstack()], justify="start", gap=1),
        ]
    )
    return data_bits, flips


@app.cell
def _(HammingCode, data_bits, flips, mo, np):
    ham = HammingCode(3)
    _data = np.array([int(v) for v in data_bits.value], dtype=np.uint8)
    codeword = ham.encode(_data)
    received = codeword ^ np.array([int(v) for v in flips.value], dtype=np.uint8)
    result = ham.decode(received)
    checks = ham.parity_checks(received)

    # positions 1..7: p1 p2 d1 p4 d2 d3 d4 ; circles: c1 = {1,3,5,7}, c2 = {2,3,6,7}, c4 = {4,5,6,7}
    _xy = {1: (95, 105), 2: (245, 105), 4: (170, 235), 3: (170, 95), 5: (125, 175), 6: (215, 175), 7: (170, 150)}
    _names = {1: "p1", 2: "p2", 3: "d1", 4: "p4", 5: "d2", 6: "d3", 7: "d4"}
    _circles = [(130, 120, "c1", checks[0]), (210, 120, "c2", checks[1]), (170, 190, "c4", checks[2])]
    _svg = ['<svg viewBox="0 0 340 300" width="340" style="font-family:sans-serif">']
    for _cx, _cy, _label, _bad in _circles:
        _col = "#d62728" if _bad else "#2ca02c"
        _svg.append(
            f'<circle cx="{_cx}" cy="{_cy}" r="80" fill="{_col}" fill-opacity="0.12" stroke="{_col}" stroke-width="2"/>'
        )
    for _lab, (_x, _y) in zip(("check 1", "check 2", "check 3"), ((40, 40), (250, 40), (140, 290))):
        _svg.append(f'<text x="{_x}" y="{_y}" font-size="13" fill="currentColor">{_lab}</text>')
    for _pos, (_x, _y) in _xy.items():
        _flipped = bool(flips.value[_pos - 1])
        _fill = "#ffbf00" if _flipped else ("#4c78a8" if _pos in (1, 2, 4) else "#888")
        _svg.append(f'<circle cx="{_x}" cy="{_y}" r="17" fill="{_fill}"/>')
        _svg.append(
            f'<text x="{_x}" y="{_y + 6}" text-anchor="middle" font-size="17" fill="white" font-weight="bold">{received[_pos - 1]}</text>'
        )
        _svg.append(
            f'<text x="{_x}" y="{_y - 21}" text-anchor="middle" font-size="11" fill="currentColor">{_names[_pos]} ({_pos})</text>'
        )
    _svg.append("</svg>")

    _syn = result.syndrome
    _status = {
        "ok": "all three checks pass: no error",
        "corrected": f"syndrome = {_syn:03b}₂ = **{_syn}** → flip bit at position {_syn}",
    }.get(result.status, result.status)
    _explain = mo.md(
        f"""
    **sent** `{''.join(map(str, codeword))}`
    **received** `{''.join(map(str, received))}`

    failed checks (c4 c2 c1): `{checks[2]}{checks[1]}{checks[0]}`
    {_status}

    **decoded data** `{''.join(map(str, result.data))}`
    {'✅ correct' if np.array_equal(result.data, _data) else '❌ wrong: two or more errors fool the decoder'}

    Blue dots are parity bits, grey dots data bits, yellow ones flipped by the channel.
    A red circle is a parity check that fails. Every position lies in a unique
    set of circles, and that set, read as a binary number, *is* its position.
    """
    )
    mo.hstack([mo.Html("".join(_svg)), _explain], widths=[1, 1.2])
    return


@app.cell
def _(HammingCode, mo, np):
    _h = HammingCode(3)
    _fmt = lambda M: "\\begin{bmatrix}" + "\\\\".join(" & ".join(map(str, r)) for r in M) + "\\end{bmatrix}"
    mo.md(
        rf"""
    ## Matrices

    The same code in linear-algebra form. Codewords are the vectors **c** with
    $\mathbf H\,\mathbf c^T = \mathbf 0$ (mod 2), and they are produced from the data by
    $\mathbf c = \mathbf d\,\mathbf G$. Column *j* of $\mathbf H$ is *j* written in binary,
    so a single error in position *j* gives syndrome
    $\mathbf s = \mathbf H\,\mathbf e^T$ = column *j*.

    $$\mathbf H = {_fmt(_h.H())} \qquad \mathbf G = {_fmt(_h.G())}$$

    Any two columns of $\mathbf H$ are different, so every single error is
    distinguishable: minimum distance $d_{{min}} = 3$, which corrects $t = 1$ error.
    Adding an overall parity bit (the *extended* Hamming code, SECDED) makes
    $d_{{min}} = 4$: it still corrects one error and also **detects** any two.
    """
    )
    return


@app.cell
def _(mo):
    r_slider = mo.ui.slider(2, 6, value=3, label="parity bits r", show_value=True)
    mo.vstack([mo.md("## The Hamming family: n = 2ʳ − 1, k = n − r"), r_slider])
    return (r_slider,)


@app.cell
def _(HammingCode, mo, np, plt, r_slider):
    from math import comb

    _code = HammingCode(r_slider.value)
    _p = np.logspace(-4, -0.7, 60)
    _fig, _ax = plt.subplots(figsize=(7, 4))
    _ax.loglog(_p, _p, "k--", label="uncoded")
    for _r in range(2, 7):
        _c = HammingCode(_r)
        _n = _c.n
        # P(block wrong) = P(>= 2 errors); about 1.5 * (i/n) of those bits end up wrong (approximation)
        _pb = sum(comb(_n, i) * _p**i * (1 - _p) ** (_n - i) * min(i + 1, _n) / _n for i in range(2, _n + 1))
        _ax.loglog(_p, _pb, lw=3 if _r == r_slider.value else 1, label=f"{_c.name}, rate {_c.k / _c.n:.2f}")
    _ax.set_xlabel("channel bit-flip probability p")
    _ax.set_ylabel("decoded bit error rate (approx.)")
    _ax.grid(True, which="both", alpha=0.3)
    _ax.legend(fontsize=8)
    _ax.set_title("Longer Hamming codes: higher rate, weaker protection")
    mo.vstack(
        [
            mo.md(
                f"**{_code.name}**: {_code.k} data bits + {_code.r} parity bits, rate "
                f"{_code.k / _code.n:.3f}. It corrects one error per {_code.n}-bit block, so "
                f"as blocks grow, a single correction protects more and more bits. "
                "To correct *t* errors per block you need more structure: "
                "Galois fields (notebook 2) and BCH codes (notebook 4)."
            ),
            _fig,
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Where next

    * **2 · Finite fields**: the arithmetic behind BCH and Reed–Solomon codes.
    * **3 · Cyclic codes**: encoding by polynomial division with a shift register.
    * **4 · BCH codes**: correcting *t* errors with Berlekamp–Massey.
    """)
    return


if __name__ == "__main__":
    app.run()
