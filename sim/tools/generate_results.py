#!/usr/bin/env python3
"""Regenerate the BER/FER curves in sim/results/ (used by demos/08_ber_explorer.py).

Usage:  python tools/generate_results.py [--frame normal|short|both] [--only QPSK-1/2,...] [--skip-existing]

Each curve starts below the EN 302 307 QEF Es/N0 and stops once FER < 1e-3.
Up to 600 frames per point; normal frames take a few minutes per MODCOD on 8 cores.
"""
import argparse
import pathlib

import numpy as np

from dvbs2.phy.modcod import all_modcods
from dvbs2.sim import results
from dvbs2.sim.montecarlo import SimConfig, default_workers, run_curve

OUT = pathlib.Path(__file__).resolve().parent.parent / "results"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", default="both", choices=["normal", "short", "both"])
    ap.add_argument("--only", default="")
    ap.add_argument("--max-frames", type=int, default=600)
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()
    frames = ["normal", "short"] if args.frame == "both" else [args.frame]
    only = set(filter(None, args.only.split(",")))
    cfg = SimConfig(min_frame_errors=50, max_frames=args.max_frames, batch=8, workers=default_workers())
    for frame in frames:
        for mc in all_modcods(frame):
            if only and mc.label not in only:
                continue
            target = OUT / results.filename(mc.label, frame, False)
            if args.skip_existing and target.exists():
                continue
            ref = mc.qef_esn0 if mc.qef_esn0 is not None else 0.0
            start, stop = (ref - 0.8, ref + 0.6) if frame == "normal" else (ref - 0.4, ref + 1.6)
            if frame == "short" and mc.rate in ("1/4", "1/3", "2/5", "1/2"):
                start = ref - (2.4 if mc.rate == "1/4" else 1.6)  # short low-rate codes have a lower effective rate (e.g. 1/4 is really 1/5)
            pts = np.round(np.arange(start, stop + 1e-9, 0.1), 2)
            curve = run_curve(mc, pts, cfg, stop_fer=1e-3)
            path = results.save(curve, target)
            last = curve.points[-1]
            print("%-12s %-6s %2d points, last Es/N0 %.2f FER %.1e (%s)" % (
                mc.label, frame, len(curve.points), last.esn0, last.fer, path.name), flush=True)


if __name__ == "__main__":
    main()
