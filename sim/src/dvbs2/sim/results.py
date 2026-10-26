"""Store simulation curves as JSON and plot them."""
from __future__ import annotations

import json
import pathlib

import numpy as np

from ..phy.channel import lin2db


def save(curve, path) -> pathlib.Path:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(curve.to_dict() if hasattr(curve, "to_dict") else curve, indent=1))
    return path


def load(path) -> dict:
    return json.loads(pathlib.Path(path).read_text())


def load_dir(directory) -> list[dict]:
    return [load(p) for p in sorted(pathlib.Path(directory).glob("*.json"))]


def filename(modcod: str, frame: str, pilots: bool) -> str:
    return "%s_%s%s.json" % (modcod.replace("/", "_"), frame, "_pilots" if pilots else "")


def plot(curves, ax=None, metric: str = "fer", x: str = "esn0", show_qef: bool = True):
    """Plot ``metric`` (fer, ber, ldpc_ber, ldpc_fer) vs ``x`` (esn0 or ebn0) for curve dicts."""
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4.5))
    for c in curves:
        pts = [p for p in c["points"] if p[metric] and p[metric] > 0]
        xs = [p[x] for p in pts]
        line, = ax.semilogy(xs, [p[metric] for p in pts], "o-", ms=4, label="%s %s" % (c["modcod"], c["frame"]))
        if show_qef and c.get("qef_esn0") is not None and c["frame"] == "normal":
            q = c["qef_esn0"] if x == "esn0" else c["qef_esn0"] - lin2db(c["efficiency"])
            ax.axvline(q, color=line.get_color(), ls=":", lw=1)
    ax.set_xlabel("Es/N0 [dB]" if x == "esn0" else "Eb/N0 [dB]")
    ax.set_ylabel(metric.upper().replace("_", " "))
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    return ax


def summary_table(curve: dict) -> str:
    rows = ["%7s %7s %7s %7s %10s %10s %10s %6s" % ("Es/N0", "Eb/N0", "frames", "errors", "FER", "BER",
                                                    "LDPC BER", "iters")]
    for p in curve["points"]:
        rows.append("%7.2f %7.2f %7d %7d %10.3e %10.3e %10.3e %6.1f" % (
            p["esn0"], p["ebn0"], p["frames"], p["frame_errors"], p["fer"], p["ber"], p["ldpc_ber"],
            p["avg_iterations"]))
    return "\n".join(rows)


def frange(spec: str) -> np.ndarray:
    """'5:0.1:7' (start:step:stop, inclusive) or '1,2,3' -> array."""
    if ":" in spec:
        a, step, b = (float(v) for v in spec.split(":"))
        return np.round(np.arange(a, b + step / 2, step), 6)
    return np.array([float(v) for v in spec.split(",")])
