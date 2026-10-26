import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="8 · DVB-S2 BER explorer")


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

    from dvbs2.phy.capacity import bicm_capacity, shannon
    from dvbs2.phy.modcod import ModCod
    return BASE, IN_BROWSER, ModCod, bicm_capacity, json, mo, np, plt, shannon


@app.cell
def _(BASE, IN_BROWSER, json):
    # Simulation results: sim/results/*.json locally, results/ next to the page on the website.
    def _load():
        if IN_BROWSER:
            from pyodide.http import open_url

            names = json.loads(open_url(BASE + "/results/index.json").read())
            return [json.loads(open_url(BASE + "/results/" + n).read()) for n in names]
        import pathlib

        from dvbs2.sim import results

        return results.load_dir(pathlib.Path(BASE).parent / "sim" / "results")

    curves = _load()
    return (curves,)


@app.cell
def _(mo):
    mo.md(r"""
    # 8 · DVB-S2 performance over AWGN

    These curves come from the simulator in `sim/` (`dvbs2sim ber …`): full DVB-S2
    frames (BBFRAME → BCH → LDPC → bit interleaver → constellation → PLFRAME) over an
    AWGN channel with ideal synchronization, exact log-MAP demapping and a layered
    sum-product LDPC decoder (50 iterations) followed by the Berlekamp–Massey BCH
    decoder. Each point runs until 50 frame errors or 600 frames.

    The dotted vertical lines are the *quasi-error-free* Es/N0 that ETSI EN 302 307
    (Table 13) gives for each MODCOD with normal frames. The waterfalls drop past
    FER = 10⁻² close to those values.
    """)
    return


@app.cell
def _(curves, mo):
    _labels = sorted({c["modcod"] for c in curves}, key=lambda s: (["QPSK", "8PSK", "16APSK", "32APSK"].index(s.split("-")[0]), s))
    pick = mo.ui.multiselect(
        options=_labels,
        value=[l for l in ("QPSK-1/2", "8PSK-3/5", "16APSK-3/4", "32APSK-4/5") if l in _labels],
        label="MODCODs",
    )
    frame = mo.ui.radio(options=["normal", "short", "both"], value="normal", label="frame", inline=True)
    metric = mo.ui.dropdown(
        options={"frame error rate (after BCH)": "fer", "bit error rate (after BCH)": "ber",
                 "bit error rate after LDPC (before BCH)": "ldpc_ber"},
        value="frame error rate (after BCH)", label="metric",
    )
    xaxis = mo.ui.radio(options={"Es/N0": "esn0", "Eb/N0": "ebn0"}, value="Es/N0", label="x axis", inline=True)
    mo.vstack([pick, mo.hstack([frame, metric, xaxis], justify="start", gap=2)])
    return frame, metric, pick, xaxis


@app.cell
def _(curves, frame, metric, mo, np, pick, plt, xaxis):
    _sel = [c for c in curves if c["modcod"] in pick.value and (frame.value == "both" or c["frame"] == frame.value)]
    _fig, _ax = plt.subplots(figsize=(8, 4.8))
    _colors = {}
    for _c in _sel:
        _pts = [p for p in _c["points"] if p[metric.value] and p[metric.value] > 0]
        if not _pts:
            continue
        _col = _colors.setdefault(_c["modcod"], f"C{len(_colors) % 10}")
        _ax.semilogy([p[xaxis.value] for p in _pts], [p[metric.value] for p in _pts],
                     "o-" if _c["frame"] == "normal" else "s--", color=_col, ms=4,
                     label=f'{_c["modcod"]} {_c["frame"]}')
        if _c.get("qef_esn0") is not None:
            _q = _c["qef_esn0"] - (10 * np.log10(_c["efficiency"]) if xaxis.value == "ebn0" else 0)
            _ax.axvline(_q, color=_col, ls=":", lw=1)
    _ax.set_xlabel("Es/N0 [dB]" if xaxis.value == "esn0" else "Eb/N0 [dB]")
    _ax.set_ylabel(metric.selected_key)
    _ax.grid(True, which="both", alpha=0.3)
    if _sel:
        _ax.legend(fontsize=8, ncol=2)
    _rows = []
    for _c in _sel:
        _below = [p for p in _c["points"] if p["frames"] and p["fer"] < 1e-2]
        _at = f'{_below[0]["esn0"]:.2f}' if _below else "—"
        _q = f'{_c["qef_esn0"]:.2f}' if _c.get("qef_esn0") is not None else "—"
        _rows.append(f'| {_c["modcod"]} | {_c["frame"]} | {_c["efficiency"]:.3f} | {_at} | {_q} |')
    mo.vstack([
        _fig,
        mo.md("| MODCOD | frame | η [bit/symbol] | sim. Es/N0 at FER < 10⁻² | EN 302 307 QEF Es/N0 |\n|---|---|---|---|---|\n"
              + "\n".join(_rows)) if _rows else mo.md("_No results for this selection._"),
    ])
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## How close is DVB-S2 to capacity?

    Each MODCOD carries η information bits per symbol. Shannon's limit says this needs
    at least $E_s/N_0 = 2^{\eta} - 1$. A constellation with $2^m$ points, decoded bit by bit
    (BICM), needs a little more. The chart below shows each MODCOD's threshold
    (the Es/N0 where the simulated FER first drops below 10⁻², or the standard's QEF
    value) against those limits. The gap of roughly 0.6–1.2 dB is what remains for
    finite block length, iterative decoding and the BCH/LDPC overhead.
    """)
    return


@app.cell
def _(ModCod, bicm_capacity, curves, mo, np, plt, shannon):
    _es = np.linspace(-4, 18, 45)
    _fig, _ax = plt.subplots(figsize=(8, 4.8))
    _ax.plot(_es, shannon(_es), "k-", label="Shannon log2(1+Es/N0)")
    for _i, _mod in enumerate(["QPSK", "8PSK", "16APSK", "32APSK"]):
        _ax.plot(_es, bicm_capacity(_mod, _es, n=3000), color=f"C{_i}", lw=1, label=f"{_mod} BICM")
    _done = set()
    for _c in curves:
        if _c["frame"] != "normal":
            continue
        _mc = ModCod.parse(_c["modcod"])
        _i = ["QPSK", "8PSK", "16APSK", "32APSK"].index(_mc.modulation)
        _below = [p for p in _c["points"] if p["fer"] < 1e-2]
        if _below:
            _ax.plot(_below[0]["esn0"], _c["efficiency"], "o", color=f"C{_i}", ms=5)
            _done.add(_c["modcod"])
    for _c in [ModCod.parse(l) for l in (
        "QPSK-1/4 QPSK-1/3 QPSK-2/5 QPSK-1/2 QPSK-3/5 QPSK-2/3 QPSK-3/4 QPSK-4/5 QPSK-5/6 QPSK-8/9 QPSK-9/10 "
        "8PSK-3/5 8PSK-2/3 8PSK-3/4 8PSK-5/6 8PSK-8/9 8PSK-9/10 16APSK-2/3 16APSK-3/4 16APSK-4/5 16APSK-5/6 "
        "16APSK-8/9 16APSK-9/10 32APSK-3/4 32APSK-4/5 32APSK-5/6 32APSK-8/9 32APSK-9/10").split()]:
        _i = ["QPSK", "8PSK", "16APSK", "32APSK"].index(_c.modulation)
        _ax.plot(_c.qef_esn0, _c.efficiency, "x", color=f"C{_i}", ms=6)
    _ax.set_xlabel("Es/N0 [dB]")
    _ax.set_ylabel("spectral efficiency η [bit/symbol]")
    _ax.set_ylim(0, 5)
    _ax.grid(True, alpha=0.3)
    _ax.legend(fontsize=8, loc="upper left")
    _ax.set_title("× EN 302 307 QEF points   ● simulated FER = 10⁻² points")
    _fig
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Reproduce or extend

    ```bash
    cd sim && pip install -e '.[fast]'
    dvbs2sim ber --modcod 8PSK-3/5 --esn0 5.0:0.1:5.8 --plot 8psk35.png
    python tools/generate_results.py          # all curves on this page
    ```
    """)
    return


if __name__ == "__main__":
    app.run()
