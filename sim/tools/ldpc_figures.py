#!/usr/bin/env python3
"""Figures of the "LDPC Decoder Design" chapter (figures/ldpc-*.png).

Usage:  python tools/ldpc_figures.py

Structural figures and block diagrams are drawn from the code tables; the
result figures read sim/results/ldpc_study/*.json (tools/ldpc_study.py) and
are skipped when a file is missing.
"""
import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

from dvbs2.codes import ldpc_hw as hw
from dvbs2.codes.ldpc import dvbs2_ldpc

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIG = ROOT.parent / "figures"
STUDY = ROOT / "results" / "ldpc_study"

# Categorical slots in fixed order; ink and grid are recessive grays.
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, GRID, FILL = "#0b0b0b", "#52514e", "#d9d8d4", "#eef3fb"

plt.rcParams.update({
    "font.family": "serif", "mathtext.fontset": "cm", "font.size": 10, "axes.titlesize": 10,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "lines.linewidth": 1.8, "lines.markersize": 5, "legend.frameon": False, "legend.fontsize": 8.5,
    "savefig.dpi": 200, "savefig.bbox": "tight", "axes.spines.top": False, "axes.spines.right": False,
})


def save(fig, name):
    FIG.mkdir(exist_ok=True)
    path = FIG / ("ldpc-%s.png" % name)
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print("wrote", path.relative_to(ROOT.parent))


def load(name):
    p = STUDY / (name + ".json")
    return json.loads(p.read_text()) if p.exists() else None


# -- structure ------------------------------------------------------------------
def fig_qc_structure():
    code = dvbs2_ldpc("1/2", "short")
    qc = hw.qc_structure(code)
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.6), gridspec_kw={"width_ratios": [1.8, 1.8, 1]})
    H = code.H.tocoo()
    Hp = hw.permuted_H(code).tocoo()
    for ax, M, title in ((axs[0], H, "H as in the standard"), (axs[1], Hp, "rows and parity columns permuted")):
        ax.plot(M.col, M.row, ",", color=C[0], alpha=0.6, rasterized=True)
        ax.set_xlim(0, code.n)
        ax.set_ylim(code.m, 0)
        ax.set_title(title)
        ax.set_xlabel("variable node (column)")
        ax.grid(False)
        ax.axvline(code.k, color=INK2, lw=0.8, ls="--")
        ax.set_xticks([0, code.k, code.n])
        ax.set_xticklabels(["0", "$K$ = %d" % code.k, "$N$ = %d" % code.n])
    axs[0].set_ylabel("check node (row)")
    for b in range(0, code.n + 1, 360):
        axs[1].axvline(b, color=GRID, lw=0.3)
    for b in range(0, code.m + 1, 360):
        axs[1].axhline(b, color=GRID, lw=0.3)
    # zoom into one block row: block columns of layer 3 with their shifts
    a = 3
    ax = axs[2]
    cols = sorted(set(c for c, _ in qc.layers[a]))
    sub = hw.permuted_H(code)[a * 360:(a + 1) * 360].tocsc()[:, np.concatenate([np.arange(c * 360, c * 360 + 360) for c in cols])].tocoo()
    ax.plot(sub.col, sub.row, ",", color=C[0], rasterized=True)
    for i in range(len(cols) + 1):
        ax.axvline(i * 360, color=INK2, lw=0.5)
    ax.set_xlim(0, 360 * len(cols))
    ax.set_ylim(360, 0)
    shifts = {c: [s for cc, s in qc.layers[a] if cc == c] for c in cols}
    ax.set_xticks([i * 360 + 180 for i in range(len(cols))])
    ax.set_xticklabels(["%d\n%s" % (c, ",".join(map(str, shifts[c]))) for c in cols], fontsize=7)
    ax.set_title("layer %d: block columns / shifts" % a)
    ax.grid(False)
    save(fig, "qc-structure")


def fig_checknode():
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
    x = np.linspace(0, 6, 300)
    ax = axs[0]
    phi = lambda v: -np.log(np.tanh(np.maximum(v, 1e-9) / 2))
    ax.plot(x, phi(x), color=C[0], label=r"$\phi(x) = -\ln\tanh(x/2)$")
    ax.set_ylim(0, 5)
    ax.set_xlabel("$x$")
    ax.set_title(r"$\phi$ is its own inverse: $\phi(\phi(x)) = x$")
    ax.plot(x, x, color=GRID, lw=1)
    ax.legend(loc="upper right")
    ax = axs[1]
    rng = np.random.default_rng(0)
    degs = np.arange(3, 31)
    for i, mean in enumerate((2.0, 4.0, 8.0)):
        ratio = []
        for d in degs:
            # d - 1 inputs to a check node: consistent Gaussian LLRs, variance = 2 * mean
            mag = np.abs(rng.normal(mean, np.sqrt(2 * mean), size=(20000, d - 1)))
            ratio.append(np.mean(phi(phi(mag).sum(axis=1))) / np.mean(mag.min(axis=1)))
        ax.plot(degs, ratio, "o-", color=C[i], ms=3.5, label="input LLR mean %g" % mean)
    ax.set_ylim(0, 1)
    ax.set_xlabel("check-node degree $d_c$")
    ax.set_ylabel(r"$E\,|\mathrm{SPA}|\;/\;E\,|\mathrm{MS}|$")
    ax.set_title("min-sum overestimates: the ratio is the ideal $\\alpha$")
    ax.legend(loc="upper right")
    save(fig, "checknode")


# -- block diagrams ------------------------------------------------------------------
def box(ax, x, y, w, h, text, fc=FILL, ec=INK, fs=8.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK,
            fontweight="bold" if bold else "normal")


def arrow(ax, p, q, text=None, color=INK, off=(0, 0.12), fs=7.5, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=9, color=color, lw=1, ls=ls,
                                 shrinkA=0, shrinkB=0))
    if text:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, ha="center", va="bottom",
                fontsize=fs, color=INK2)


def canvas(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    ax.set_aspect("equal")
    return fig, ax


def wire(ax, pts, text=None, at=0, off=(0.08, 0.06), ls="-", head=True, ha="left"):
    """Orthogonal connection through ``pts``; arrow head on the last segment."""
    xs, ys = zip(*pts)
    ax.plot(xs[:-1] if head else xs, ys[:-1] if head else ys, color=INK, lw=1, ls=ls, solid_capstyle="butt")
    if head:
        arrow(ax, pts[-2], pts[-1], ls=ls)
    if text:
        ax.text(pts[at][0] + off[0], pts[at][1] + off[1], text, fontsize=7.5, color=INK2, ha=ha, va="bottom")


def fig_architecture():
    fig, ax = canvas(12, 5.6)
    ctl = "#fdf3e6"
    box(ax, 0.2, 2.2, 1.3, 1.0, "demapper\nLLRs, $w_{ch}$ bits")
    box(ax, 1.9, 2.2, 1.6, 1.0, "input buffer\n$N/360\\times 360\\,w_{ch}$")
    box(ax, 3.9, 2.2, 1.8, 1.0, "L memory\n$N/360$ words\n$\\times\\,360\\,w_L$ bits")
    box(ax, 6.1, 2.2, 1.4, 1.0, "cyclic shifter\n$360\\times w_L$")
    box(ax, 7.9, 2.0, 2.0, 1.4, "360 check-node\nprocessors\nCNP 0 ... 359")
    box(ax, 7.9, 4.0, 2.0, 1.0, "R memory, compressed\n(min1, min2, idx, signs)")
    box(ax, 6.1, 0.4, 1.4, 1.0, "inverse\ncyclic shifter")
    box(ax, 10.3, 2.2, 1.5, 1.0, "early stop:\nall checks\nsatisfied")
    box(ax, 1.65, 0.4, 1.85, 1.0, "hard decisions\nsign($L$), $K$ bits\nto the BCH decoder")
    box(ax, 1.9, 4.0, 1.6, 1.0, "control\n(layer, iteration)", fc=ctl)
    box(ax, 3.9, 4.0, 1.8, 1.0, "block-column/shift\nROM (Annex B/C)", fc=ctl)
    arrow(ax, (1.5, 2.7), (1.9, 2.7))
    arrow(ax, (3.5, 2.7), (3.9, 2.7))
    ax.text(3.7, 2.78, "load", fontsize=7.5, color=INK2, ha="center", va="bottom")
    arrow(ax, (5.7, 2.7), (6.1, 2.7))
    arrow(ax, (7.5, 2.7), (7.9, 2.7))
    ax.text(5.9, 2.78, "$L$", fontsize=8, color=INK2, ha="center", va="bottom")
    ax.text(7.7, 2.78, "$L_v$", fontsize=8, color=INK2, ha="center", va="bottom")
    arrow(ax, (8.5, 4.0), (8.5, 3.4))
    arrow(ax, (9.3, 3.4), (9.3, 4.0))
    ax.text(8.45, 3.62, "$R^{old}$", fontsize=8, color=INK2, ha="right")
    ax.text(9.35, 3.62, "$R^{new}$", fontsize=8, color=INK2, ha="left")
    wire(ax, [(8.9, 2.0), (8.9, 0.9), (7.5, 0.9)], "$L^{new}_v$", at=1, off=(-0.6, 0.06))
    wire(ax, [(6.1, 0.9), (4.8, 0.9), (4.8, 2.2)], "write back", at=1, off=(0.08, 0.35))
    wire(ax, [(4.2, 2.2), (4.2, 0.9), (3.5, 0.9)])
    arrow(ax, (9.9, 2.7), (10.3, 2.7))
    arrow(ax, (3.5, 4.5), (3.9, 4.5))
    arrow(ax, (4.8, 4.0), (4.8, 3.2))
    ax.text(4.86, 3.5, "address", fontsize=7.5, color=INK2)
    wire(ax, [(5.7, 4.5), (6.8, 4.5), (6.8, 3.2)], "shift", at=1, off=(-0.5, 0.06), ls="--")
    wire(ax, [(11.05, 3.2), (11.05, 5.35), (2.7, 5.35), (2.7, 5.0)], "stop", at=1, off=(-0.4, 0.06), ls="--")
    save(fig, "decoder-architecture")


def fig_cnp():
    fig, ax = canvas(11, 3.6)
    box(ax, 0.1, 1.5, 1.2, 0.8, "$L_v$ (shifted)")
    box(ax, 0.1, 0.2, 1.2, 0.8, "$R_{cv}^{old}$\n(decompress)")
    box(ax, 1.9, 0.9, 0.9, 0.9, "$-$\nsat($w_L$)")
    box(ax, 3.4, 2.2, 1.4, 0.9, "sign/\nmagnitude")
    box(ax, 5.3, 2.2, 1.7, 0.9, "two-minimum\nfinder\n(min1, min2, idx)")
    box(ax, 7.5, 2.2, 1.3, 0.9, "correction\n$\\max(m-\\beta,0)$")
    box(ax, 3.4, 0.2, 1.4, 0.9, "FIFO\n$Q_{cv}$, $d_c$ deep")
    box(ax, 7.5, 0.2, 1.3, 0.9, "select\nmin1/min2,\nsign")
    box(ax, 9.3, 0.2, 1.4, 0.9, "$+$\nsat($w_L$)")
    box(ax, 9.3, 2.2, 1.4, 0.9, "$R$ memory\n(compressed)", fc="#fdf3e6")
    arrow(ax, (1.3, 1.9), (1.9, 1.5))
    arrow(ax, (1.3, 0.6), (1.9, 1.2))
    arrow(ax, (2.8, 1.35), (3.4, 2.6), "$Q_{cv}$", off=(-0.25, 0.0))
    arrow(ax, (2.8, 1.2), (3.4, 0.65))
    arrow(ax, (4.8, 2.65), (5.3, 2.65))
    arrow(ax, (7.0, 2.65), (7.5, 2.65))
    arrow(ax, (8.15, 2.2), (8.15, 1.1))
    arrow(ax, (8.8, 2.65), (9.3, 2.65))
    arrow(ax, (4.8, 0.65), (7.5, 0.65), "$Q_{cv}$, sign($Q_{cv}$)")
    arrow(ax, (8.8, 0.65), (9.3, 0.65), "$R_{cv}^{new}$", off=(0, 0.15))
    arrow(ax, (10.7, 0.65), (10.95, 0.65))
    ax.text(10.95, 0.5, "$L_v^{new}$", fontsize=8.5, color=INK2, ha="right", va="top")
    ax.text(5.4, 3.3, "phase 1: $d_c$ cycles (read)", fontsize=8, color=INK2)
    ax.text(5.4, 1.35, "phase 2: $d_c$ cycles (write)", fontsize=8, color=INK2)
    save(fig, "cnp")


def fig_pipeline():
    code = dvbs2_ldpc("1/2", "short")
    qc = hw.qc_structure(code)
    depth = 4
    fig, axs = plt.subplots(2, 1, figsize=(10, 3.8), sharex=True)
    for ax, (order, reorder, title) in zip(axs, (
            (list(range(qc.q)), False, "natural layer order"),
            (hw._greedy_layer_order(qc.layers), True, "layers and block columns reordered"))):
        seq = [sorted(set(c for c, _ in qc.layers[i])) for i in order]
        if reorder:
            for i in range(len(seq)):
                prev, nxt = set(seq[i - 1]), set(seq[(i + 1) % len(seq)])
                seq[i].sort(key=lambda c: (c in prev, c not in nxt))
        t, done = 0, {}
        for li, cols in enumerate(seq[:7]):
            start = t
            for pos, c in enumerate(cols):
                if c in done:
                    start = max(start, done[c] - pos)
            if start > t:
                ax.add_patch(Rectangle((t, li - 0.35), start - t, 0.7, fc="none", ec=C[7], hatch="////", lw=0))
            d = len(cols)
            ax.add_patch(Rectangle((start, li - 0.35), d, 0.7, fc=C[0], ec="white", lw=1))
            ax.add_patch(Rectangle((start + d, li - 0.35), depth, 0.7, fc=GRID, ec="white", lw=1))
            ax.add_patch(Rectangle((start + d + depth, li - 0.35), d, 0.7, fc=C[1], ec="white", lw=1))
            done = {c: start + d + depth + pos + 1 for pos, c in enumerate(cols)}
            t = start + d
        ax.set_ylim(6.6, -0.6)
        ax.set_yticks(range(7))
        ax.set_yticklabels(["layer %d" % order[i] for i in range(7)], fontsize=7.5)
        ax.set_title(title, loc="left")
        ax.grid(False)
    axs[1].set_xlim(0, 95)
    axs[1].set_xlabel("clock cycle")
    handles = [Rectangle((0, 0), 1, 1, fc=C[0]), Rectangle((0, 0), 1, 1, fc=GRID),
               Rectangle((0, 0), 1, 1, fc=C[1]), Rectangle((0, 0), 1, 1, fc="none", ec=C[7], hatch="////")]
    axs[0].legend(handles, ["read $L$ (one block column per cycle)", "CNP pipeline", "write $L$",
                            "stall (read-after-write hazard)"], loc="upper right", ncol=2)
    save(fig, "pipeline")


# -- results -------------------------------------------------------------------------
LABELS = {"spa": "sum-product", "nms:1": "min-sum"}


def dec_label(d):
    if d in LABELS:
        return LABELS[d]
    if d.startswith("nms:"):
        return r"normalized MS, $\alpha=%s$" % d[4:]
    if d.startswith("oms:"):
        return r"offset MS, $\beta=%s$" % d[4:]
    if d.startswith("fixed:"):
        parts = d.split(":")
        w = parts[1].replace(",", ", ")
        return "fixed (%s), %s LSB/unit" % (w, parts[2]) if len(parts) > 2 else "fixed (%s)" % w
    return d


def fig_correction():
    data = load("correction")
    if not data:
        return
    pts = data["points"]
    codes = list(dict.fromkeys((p["modcod"], p["frame"]) for p in pts))
    floor = 0.5 / max(p["frames"] for p in pts)
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
    for i, (label, frame) in enumerate(codes):
        sel = [p for p in pts if (p["modcod"], p["frame"]) == (label, frame)]
        name = "%s %s, %.1f dB" % (label, frame, sel[0]["esn0"])
        for ax, kind in zip(axs, ("nms", "oms")):
            xy = [(float(p["decoder"][4:]), p["fer"]) for p in sel if p["decoder"].startswith(kind)]
            x, y = zip(*xy)
            ax.semilogy(x, [max(v, floor) for v in y], "-", color=C[i], label=name if kind == "nms" else None)
            ax.semilogy([a for a, v in xy if v > 0], [v for a, v in xy if v > 0], "o", color=C[i], ms=5)
            ax.semilogy([a for a, v in xy if v == 0], [floor] * sum(v == 0 for _, v in xy), "o", mfc="white",
                        color=C[i], ms=5)
    for ax in axs:
        ax.axhline(floor, color=INK2, lw=0.8, ls=":")
    axs[1].text(1.0, floor * 1.25, "no frame error", ha="right", va="bottom", fontsize=7.5, color=INK2)
    axs[0].set_xlabel(r"normalization $\alpha$")
    axs[1].set_xlabel(r"offset $\beta$")
    axs[0].set_ylabel("FER")
    axs[0].set_title("normalized min-sum")
    axs[1].set_title("offset min-sum")
    fig.legend(loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.1))
    save(fig, "correction")


def curves_fig(data, codes, name, ncols=2):
    fig, axs = plt.subplots(1, len(codes), figsize=(5 * len(codes), 3.8), sharey=True)
    for ax, (label, frame) in zip(np.atleast_1d(axs), codes):
        sel = [c for c in data["curves"] if (c["modcod"], c["frame"]) == (label, frame)]
        for i, c in enumerate(sel):
            pts = [p for p in c["points"] if p["frames"] and p["fer"] > 0]
            if pts:
                wide = c["decoder"].startswith("fixed:8,10,8")      # coincides with (6, 8, 6) at 4 LSB/unit
                ax.semilogy([p["esn0"] for p in pts], [p["fer"] for p in pts], "o--" if wide else "o-",
                            ms=3 if wide else 4, color=C[i % 8], label=dec_label(c["decoder"]))
        q = sel[0].get("qef_esn0")
        if q is not None and frame == "normal":
            ax.axvline(q, color=INK2, lw=0.8, ls=":")
        ax.set_title("%s, %s frame" % (label, frame))
        ax.set_xlabel("$E_s/N_0$ [dB]")
        ax.set_ylim(5e-4, 1.2)
    np.atleast_1d(axs)[0].set_ylabel("FER (after BCH)")
    handles, labels = np.atleast_1d(axs)[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=min(len(labels), 3), fontsize=8, bbox_to_anchor=(0.5, -0.12))
    save(fig, name)


def fig_algorithms():
    data = load("algorithms")
    if data:
        codes = list(dict.fromkeys((c["modcod"], c["frame"]) for c in data["curves"]))
        curves_fig(data, codes[:2], "algorithms")
        if len(codes) > 2:
            curves_fig(data, codes[2:], "algorithms-2")


def fig_quantization():
    data = load("quantization")
    if data:
        # word lengths with offset min-sum; the normalized variants are tabulated in the text
        data = {"curves": [c for c in data["curves"] if "/" not in c["decoder"] and not c["decoder"].startswith("nms")]}
        codes = list(dict.fromkeys((c["modcod"], c["frame"]) for c in data["curves"]))
        curves_fig(data, codes, "quantization")


def fig_convergence():
    data = load("convergence")
    if not data:
        return
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
    ax = axs[0]
    decs = list(dict.fromkeys(p["decoder"] for p in data["limits"]))
    names = {"spa": "sum-product, layered", "oms:0.5": "offset MS, layered (row by row)",
             "hw-oms:0.5": "offset MS, 360 checks in parallel", "flood-oms:0.5": "offset MS, flooding"}
    floor = 0.5 / max(p["frames"] for p in data["limits"])
    for i, d in enumerate(decs):
        sel = [p for p in data["limits"] if p["decoder"] == d]
        x = [p["max_iter"] for p in sel]
        ax.semilogy(x, [max(p["fer"], floor) for p in sel], "-", color=C[i], label=names.get(d, d))
        ax.semilogy([p["max_iter"] for p in sel if p["fer"] > 0], [p["fer"] for p in sel if p["fer"] > 0], "o",
                    ms=4, color=C[i])
        ax.semilogy([p["max_iter"] for p in sel if p["fer"] == 0], [floor] * sum(p["fer"] == 0 for p in sel), "o",
                    ms=4, mfc="white", color=C[i])
    ax.axhline(floor, color=INK2, lw=0.8, ls=":")
    ax.text(50, floor * 1.25, "no frame error", ha="right", va="bottom", fontsize=7.5, color=INK2)
    ax.set_xlabel("maximum number of iterations")
    ax.set_ylabel("FER")
    ax.set_title("%s %s, $E_s/N_0$ = %.1f dB" % (data["modcod"], data["frame"], data["esn0"]))
    ax.legend(loc="center right", fontsize=7.5)
    ax = axs[1]
    hists = data["histograms"]
    sel = [h for h in hists if h["decoder"] == hists[0]["decoder"]]
    bins = np.arange(0.5, 51.5, 1)
    for i, h in enumerate(sel):
        ax.hist(h["iterations"], bins=bins, histtype="step", lw=1.6, color=C[i],
                label="%.1f dB, mean %.1f" % (h["esn0"], np.mean(h["iterations"])))
    ax.set_xlabel("iterations to a valid codeword (early termination)")
    ax.set_ylabel("frames")
    flood = {h["esn0"]: np.mean(h["iterations"]) for h in hists if h["decoder"].startswith("flood")}
    ax.set_title("offset MS, layered (flooding needs %s)" % ", ".join("%.1f" % flood[h["esn0"]] for h in sel
                                                                       if h["esn0"] in flood), fontsize=9)
    ax.legend(loc="upper right")
    save(fig, "convergence")


def fig_parallelism():
    data = load("architecture")
    if not data:
        return
    fig, ax = plt.subplots(figsize=(6, 3.6))
    styles = {"serial": ("o", C[0]), "overlap": ("s", C[1]), "reordered": ("^", C[2])}
    for rate, ls in (("1/2", "-"), ("9/10", "--")):
        sel = [p for p in data["parallelism"] if p["rate"] == rate]
        for s, (m, col) in styles.items():
            ax.loglog([p["parallelism"] for p in sel], [p["throughput_mbps"][s] for p in sel], m, ls=ls, ms=4,
                      color=col, label="%s, rate %s" % (s, rate))
    ax.set_xlabel("check-node processors $P$")
    ax.set_ylabel("information throughput [Mb/s]")
    ax.set_title("200 MHz, 30 iterations, normal frame")
    ax.set_xticks([30, 45, 90, 180, 360])
    ax.set_xticklabels(["30", "45", "90", "180", "360"])
    ax.legend(ncol=2, fontsize=7.5)
    save(fig, "parallelism")


def main():
    fig_qc_structure()
    fig_checknode()
    fig_architecture()
    fig_cnp()
    fig_pipeline()
    fig_correction()
    fig_algorithms()
    fig_quantization()
    fig_convergence()
    fig_parallelism()


if __name__ == "__main__":
    main()
