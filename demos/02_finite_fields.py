import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="2 · Finite (Galois) fields")


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

    from dvbs2 import poly2
    from dvbs2.gf import PRIMITIVE_POLYS, GF2m, GFp, is_primitive, lfsr_cycle_length
    return GF2m, GFp, PRIMITIVE_POLYS, is_primitive, lfsr_cycle_length, mo, np, plt, poly2


@app.cell
def _(mo):
    mo.md(r"""
    # 2 · Finite fields: the arithmetic of algebraic codes

    The Hamming code of notebook 1 needs nothing beyond XOR. To correct
    **several** errors per block, BCH and Reed–Solomon codes do arithmetic on
    the *positions* of the errors, and that arithmetic must happen in a set
    where every non-zero element can be divided by. Such a set with finitely many
    elements is a **finite field**, or **Galois field** GF(*q*).

    A finite field exists only when *q* is a prime power, $q = p^m$. We start with
    the primes, then build GF(2^m) with the shift register a DVB-S2 encoder
    actually uses.
    """)
    return


@app.cell
def _(mo):
    p_sel = mo.ui.dropdown(options={str(p): p for p in (2, 3, 5, 7, 11, 13)}, value="7", label="prime p")
    mo.vstack([mo.md("## GF(p): integers modulo a prime"), p_sel])
    return (p_sel,)


@app.cell
def _(GFp, mo, np, p_sel, plt):
    _F = GFp(p_sel.value)
    _p = _F.p
    _fig, _axes = plt.subplots(1, 2, figsize=(9, 4.2))
    for _ax, _tab, _name in zip(_axes, (_F.add_table(), _F.mul_table()), ("a + b mod p", "a · b mod p")):
        _ax.imshow(_tab, cmap="viridis")
        _ax.set_title(_name)
        _ax.set_xticks(range(_p))
        _ax.set_yticks(range(_p))
        _ax.set_xlabel("b")
        _ax.set_ylabel("a")
        if _p <= 13:
            for _i in range(_p):
                for _j in range(_p):
                    _ax.text(_j, _i, _tab[_i, _j], ha="center", va="center", fontsize=7 if _p > 7 else 9,
                             color="white" if _tab[_i, _j] < _p / 2 else "black")
    _fig.tight_layout()
    _prims = _F.primitive_elements()
    _g = _prims[0]
    _powers = [pow(_g, _k, _p) for _k in range(_p - 1)]
    _inv = ", ".join(f"{_a}⁻¹ = {_F.inv(_a)}" for _a in range(1, _p))
    mo.vstack(
        [
            _fig,
            mo.md(
                f"""
    Every row of the multiplication table except row 0 is a **permutation** of
    0 … {_p - 1}: each non-zero *a* has exactly one inverse ({_inv}).
    That fails when the modulus is not prime: modulo 4, $2 \\cdot 2 = 0$ and 2 has no inverse.

    **Primitive elements** (generators of the multiplicative group): {_prims}.
    The powers of g = {_g} visit every non-zero element:
    {" → ".join(map(str, _powers))} → 1.
    So every non-zero element is a power of g, and multiplication becomes adding
    exponents. Keep that idea in mind: it is how GF(2^m) is built and how decoders
    multiply quickly.
    """
            ),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## GF(2^m): polynomials modulo a polynomial

    For codes we want fields of size $2^m$, so that an element is an *m*-bit
    word. Integers mod $2^m$ do not work, because $2^m$ is not prime. Instead take
    **polynomials with binary coefficients** and reduce them modulo a degree-*m*
    polynomial $p(x)$, exactly like integers mod a prime. If $p(x)$ is
    **irreducible**, the result is a field. If it is also **primitive**, the
    powers $\alpha^0, \alpha^1, \alpha^2, \dots$ of the root $\alpha$ of $p(x)$
    run through all $2^m - 1$ non-zero elements.

    Hardware computes the successive powers of α with a **linear feedback shift
    register (LFSR)**. Multiplying by α shifts the register one place, and the
    bit falling off the top is fed back through the taps of $p(x)$ (because
    $\alpha^m$ equals the lower terms of $p(\alpha)$). Choose *m* and a polynomial, then
    clock the register.
    """)
    return


@app.cell
def _(mo):
    m_sel = mo.ui.dropdown(options={str(k): k for k in range(2, 9)}, value="4", label="degree m")
    return (m_sel,)


@app.cell
def _(PRIMITIVE_POLYS, is_primitive, m_sel, mo, poly2):
    def _irreducible(p):
        d = poly2.degree(p)
        for q in range(2, 1 << (d // 2 + 1)):
            if 1 <= poly2.degree(q) <= d // 2 and poly2.mod(p, q) == 0:
                return False
        return True

    _m = m_sel.value
    _opts = {}
    _default = None
    for _p in range((1 << _m) | 1, 1 << (_m + 1), 2):  # degree m, constant term 1
        if is_primitive(_p):
            _kind = "primitive"
        elif _irreducible(_p):
            _kind = "irreducible, not primitive"
        else:
            _kind = "reducible"
        _label = f"{poly2.to_str(_p)}   ({_kind})"
        _opts[_label] = _p
        if _p == PRIMITIVE_POLYS[_m]:
            _default = _label
    poly_sel = mo.ui.dropdown(options=_opts, value=_default, label="p(x)")
    mo.hstack([m_sel, poly_sel], justify="start", gap=2)
    return (poly_sel,)


@app.cell
def _(lfsr_cycle_length, mo, poly_sel):
    period = lfsr_cycle_length(poly_sel.value)
    step = mo.ui.slider(0, period, value=1, label="clock i (register holds α^i)", show_value=True, full_width=True)
    step
    return period, step


@app.function
def lfsr_svg(state, m, poly, highlight_fb):
    """SVG of the Galois LFSR that multiplies by alpha: stage j holds the coefficient of alpha^j."""
    w, x0, y = 56, 60, 90
    width = x0 + m * w + 80
    red, grey = "#d62728", "#999"
    fb_col = red if highlight_fb else grey
    out = [f'<svg viewBox="0 0 {width} 150" width="{width}" style="font-family:sans-serif;max-width:100%">']
    top = 30
    x_end = x0 + (m - 1) * w + 40
    # feedback path from the top stage back to the taps
    out.append(f'<path d="M{x_end} {y} H{x_end + 30} V{top} H{x0 - 30}" fill="none" stroke="{fb_col}" stroke-width="2"/>')
    for j in range(m):
        x = x0 + j * w
        tap = (poly >> j) & 1
        if tap:
            cx = x - 10
            out.append(f'<line x1="{cx}" y1="{top}" x2="{cx}" y2="{y - 9}" stroke="{fb_col}" stroke-width="2"/>')
            out.append(f'<circle cx="{cx}" cy="{y}" r="8" fill="none" stroke="currentColor"/>')
            out.append(f'<text x="{cx}" y="{y + 5}" text-anchor="middle" font-size="14" fill="currentColor">+</text>')
        bit = int(state[j])
        out.append(f'<rect x="{x}" y="{y - 18}" width="36" height="36" rx="4" fill="{"#4c78a8" if bit else "none"}" '
                   'stroke="currentColor"/>')
        out.append(f'<text x="{x + 18}" y="{y + 7}" text-anchor="middle" font-size="18" '
                   f'fill="{"white" if bit else "currentColor"}">{bit}</text>')
        out.append(f'<text x="{x + 18}" y="{y + 38}" text-anchor="middle" font-size="12" fill="currentColor">α^{j}</text>')
        if j < m - 1:
            nx = x0 + (j + 1) * w
            tgt = nx - 18 if (poly >> (j + 1)) & 1 else nx
            out.append(f'<line x1="{x + 36}" y1="{y}" x2="{tgt}" y2="{y}" stroke="currentColor"/>')
    out.append(f'<line x1="{x0 - 30}" y1="{top}" x2="{x0 - 30}" y2="{y}" stroke="{fb_col}" stroke-width="2"/>')
    out.append(f'<line x1="{x0 - 30}" y1="{y}" x2="{x0 - 18 if poly & 1 else x0}" y2="{y}" stroke="{fb_col}" stroke-width="2"/>')
    out.append(f'<text x="{x_end + 34}" y="{top + 14}" font-size="11" fill="{fb_col}">feedback</text>')
    out.append(f'<text x="{x_end + 34}" y="{top + 28}" font-size="11" fill="{fb_col}">(α^{m} = p − x^{m})</text>')
    out.append(f'<line x1="{x0 + (m - 1) * w + 36}" y1="{y}" x2="{x_end}" y2="{y}" stroke="currentColor"/>')
    out.append("</svg>")
    return "".join(out)


@app.cell
def _(m_sel, mo, np, period, poly2, poly_sel, step):
    _m, _p = m_sel.value, poly_sel.value
    states = [1]
    for _ in range(period):
        _r = states[-1] << 1
        if _r >> _m & 1:
            _r ^= _p
        states.append(_r)
    _i = step.value
    _cur = states[_i]
    _bits = [(_cur >> _j) & 1 for _j in range(_m)]
    _svg = lfsr_svg(_bits, _m, _p, highlight_fb=bool(_bits[_m - 1]))
    _visited = set(states[:period])
    _n_nonzero = (1 << _m) - 1
    if period == _n_nonzero:
        _verdict = (f"Period **{period} = 2^{_m} − 1**: α visits every non-zero element, so "
                    f"*p(x)* is **primitive** and every non-zero element is a power of α.")
    else:
        _verdict = (f"Period **{period}** < {_n_nonzero}: only {len(_visited)} of the {_n_nonzero} non-zero "
                    "elements are powers of x. The polynomial is not primitive, so x is not a generator. "
                    + ("If p(x) is reducible, the ring even has zero divisors and is **not a field**."
                       if any(poly2.mod(_p, q) == 0 for q in range(2, 1 << (_m // 2 + 1)) if 1 <= poly2.degree(q) <= _m // 2)
                       else "p(x) is irreducible, so this is still a field, but another element must play the generator."))
    _rows = ["| i | α^i as polynomial | vector (α^{m−1} … α^0) | integer |", "|---|---|---|---|"]
    _lo = max(0, _i - 7)
    for _k in range(_lo, _i + 1):
        _s = states[_k]
        _mark = "**" if _k == _i else ""
        _rows.append(f"| {_mark}{_k}{_mark} | {poly2.to_str(_s, 'α')} | `{format(_s, f'0{_m}b')}` | {_s} |")
    mo.vstack(
        [
            mo.Html(_svg),
            mo.md(
                f"After **{_i}** clock(s) the register holds α^{_i} = **{poly2.to_str(_cur, 'α')}**. "
                + ("The top stage is 1, so on the next clock the feedback (red) adds p(x) back in."
                   if _bits[_m - 1] else "The top stage is 0, so the next clock is a plain shift.")
            ),
            mo.md("\n".join(_rows)),
            mo.md(_verdict),
        ]
    )
    return


@app.cell
def _(GF2m, PRIMITIVE_POLYS, is_primitive, m_sel, poly_sel):
    # The field used from here on: the chosen polynomial if primitive, else the default one.
    field_poly = poly_sel.value if is_primitive(poly_sel.value) else PRIMITIVE_POLYS[m_sel.value]
    F = GF2m(m_sel.value, field_poly)
    return (F,)


@app.cell
def _(F, mo, poly2):
    _rows = [{"power": "0 (zero)", "polynomial": "0", "vector": format(0, f"0{F.m}b"), "integer": 0, "log": "−∞"}]
    for _i in range(F.order):
        _e = int(F.exp[_i])
        _rows.append({"power": f"α^{_i}", "polynomial": poly2.to_str(_e, "α"), "vector": format(_e, f"0{F.m}b"),
                      "integer": _e, "log": _i})
    mo.vstack(
        [
            mo.md(f"""
    ### All {F.q} elements of {F}

    Each element has two names: the **vector** (*m* bits, handy for addition, which is
    XOR) and the **power** of α (handy for multiplication, which adds exponents mod {F.order}).
    A decoder keeps two tables to translate between them: `exp[i] = α^i` and
    `log[x]`. The thesis' `gfield.c` builds exactly these two tables, `powOfAlpha`
    and `indexAlpha`.
    """),
            mo.ui.table(_rows, selection=None, page_size=16),
        ]
    )
    return


@app.cell
def _(F, mo):
    _opts = {f"α^{i} = {F.to_bits(int(F.exp[i]))}": int(F.exp[i]) for i in range(F.order)}
    _keys = list(_opts)
    a_sel = mo.ui.dropdown(options=_opts, value=_keys[min(3, len(_keys) - 1)], label="a")
    b_sel = mo.ui.dropdown(options=_opts, value=_keys[min(F.order - 2, len(_keys) - 1)], label="b")
    mo.vstack([mo.md("### Multiplying with log tables"), mo.hstack([a_sel, b_sel], justify="start", gap=2)])
    return a_sel, b_sel


@app.cell
def _(F, a_sel, b_sel, mo, np, plt, poly2):
    _a, _b = a_sel.value, b_sel.value
    _la, _lb = int(F.log[_a]), int(F.log[_b])
    _s = (_la + _lb) % F.order
    _prod = int(F.mul(_a, _b))
    _direct = poly2.mod(poly2.mul(_a, _b), F.prim_poly)
    _inv_b = int(F.inv(_b))
    _txt = mo.md(
        f"""
    | step | value |
    |---|---|
    | a | {poly2.to_str(_a, 'α')} = α^{_la} |
    | b | {poly2.to_str(_b, 'α')} = α^{_lb} |
    | log a + log b mod {F.order} | {_la} + {_lb} ≡ **{_s}** |
    | a · b = exp[{_s}] | **{poly2.to_str(_prod, 'α')}** (`{F.to_bits(_prod)}`) |
    | check: (a(x) b(x)) mod p(x) | {poly2.to_str(_direct, 'α')} {'✅' if _direct == _prod else '❌'} |
    | a + b (XOR) | {poly2.to_str(_a ^ _b, 'α')} |
    | b⁻¹ = α^{(F.order - _lb) % F.order} | {poly2.to_str(_inv_b, 'α')}, and b · b⁻¹ = {int(F.mul(_b, _inv_b))} |

    One table lookup, one addition and one more lookup replace a polynomial
    multiplication and reduction. The BCH decoder (notebook 4) does thousands of these per frame.
    """
    )
    if F.m <= 5:
        _idx = np.argsort(F.log[1:]) + 1  # order elements as powers of alpha
        _order = np.concatenate([[0], _idx])
        _tab = F.mul(_order[:, None], _order[None, :])
        _fig, _ax = plt.subplots(figsize=(4.4, 4.2))
        _ax.imshow(F.log[_tab], cmap="twilight")
        _ax.set_title("a·b, rows/cols: 0, α^0, α^1, …\ncolour = exponent of the product", fontsize=9)
        _ax.set_xticks([])
        _ax.set_yticks([])
        _out = mo.hstack([_txt, _fig], widths=[1.4, 1])
    else:
        _out = _txt
    _out
    return


@app.cell
def _(F, mo, poly2):
    _rows = ["| cyclotomic coset {i, 2i, 4i, …} mod %d | minimal polynomial | degree |" % F.order, "|---|---|---|"]
    for _c in F.cyclotomic_cosets()[1:]:
        _mp = F.minimal_polynomial(_c[0])
        _rows.append(f"| {{{', '.join(map(str, _c))}}} | {poly2.to_str(_mp)} | {poly2.degree(_mp)} |")
    mo.md(
        f"""
    ## Conjugates and minimal polynomials

    Squaring is linear in characteristic 2, so if α^i is a root of a binary
    polynomial, then α^(2i), α^(4i), … are roots too. These exponent sets are the
    **cyclotomic cosets**. The **minimal polynomial** of α^i is the product of
    (x − α^j) over its coset: the smallest binary polynomial with α^i as a root.
    Over {F}:

    """
        + "\n".join(_rows)
        + """

    A binary **BCH code** that corrects *t* errors needs the consecutive powers
    α, α^2, …, α^(2t) to be roots of its generator. Since α^(2i) shares the coset of α^i, it is
    enough to multiply the minimal polynomials of the **odd** powers α^1, α^3, …,
    α^(2t−1). Each contributes at most *m* parity bits, hence $n - k \\le m t$.
    """
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Back to the thesis: GF(2^16) in DVB-S2

    The outer code of DVB-S2 normal frames is a BCH code over **GF(2^16)**
    built from the primitive polynomial

    $$p(x) = x^{16} + x^5 + x^3 + x^2 + 1,$$

    the `32+8+4+1` passed to `gfField(16, …)` in the thesis' `main.c`. With
    *t* = 12 the generator is the product of the minimal polynomials of α^1, α^3, …, α^23:
    twelve polynomials of degree 16, so $n - k = 192$ parity bits. That is the
    192-bit register of the parallel encoder in chapter 4.
    """)
    return


@app.cell
def _(mo, poly2):
    from dvbs2.codes.bch import dvbs2_bch

    _c = dvbs2_bch("1/2")
    _rows = ["| i | minimal polynomial of α^i |", "|---|---|"]
    for _k, _mp in enumerate(_c.minimal_polys):
        _rows.append(f"| {2 * _k + 1} | {poly2.to_str(_mp)} |")
    mo.accordion(
        {
            f"Show the 12 minimal polynomials of the DVB-S2 t = 12 code ({_c.name})": mo.md(
                "\n".join(_rows)
                + f"\n\nTheir product g(x) has degree **{_c.r}**, and it equals the `gen12` array "
                "hard-coded in `main.c` (checked by the test suite)."
            )
        }
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Where next

    * **3 · Cyclic codes**: encoding as polynomial division, and the LFSR that does it.
    * **4 · BCH codes**: syndromes, Berlekamp–Massey and the Chien search, all in GF(2^m).
    """)
    return


if __name__ == "__main__":
    app.run()
