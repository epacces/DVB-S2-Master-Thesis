#!/usr/bin/env python3
"""LDPC decoder design study: the numbers behind the "LDPC Decoder Design" chapter.

Usage:  python tools/ldpc_study.py [--only correction,algorithms,convergence,quantization,headroom,architecture]
                                   [--max-frames 300] [--step 0.1]

Writes one JSON file per experiment to sim/results/ldpc_study/:

correction    FER vs the min-sum correction (normalization alpha, offset beta) at the
              Es/N0 where the sum-product decoder first reaches FER < 1e-2
algorithms    waterfalls of sum-product, min-sum, normalized (alpha 0.8125) and offset
              (beta 0.5) min-sum and the bit-true fixed-point decoder
convergence   FER and mean iterations vs the iteration limit, flooding vs layered,
              and the distribution of the iterations needed with early termination
quantization  waterfalls of the fixed-point decoder for several word lengths
headroom      FER above the waterfall vs the extra bits of the posterior over the messages
architecture  cycles, stalls, memory and throughput for all 21 codes (no simulation)

Every simulation runs the full DVB-S2 link (BBFRAME .. PLFRAME, AWGN, exact
demapper, BCH), up to 50 frame errors or --max-frames frames per point.
"""
import argparse
import json
import pathlib
import time
from dataclasses import asdict

import numpy as np

from dvbs2.codes import ldpc_hw
from dvbs2.codes.ldpc import RATES, dvbs2_ldpc
from dvbs2.phy.channel import awgn
from dvbs2.phy.link import Receiver, Transmitter
from dvbs2.phy.modcod import ModCod
from dvbs2.sim import results
from dvbs2.sim.montecarlo import SimConfig, default_workers, run_curve

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "ldpc_study"

# Representative MODCODs: low-rate QPSK, the 8PSK workhorse, a high rate, one short frame.
CODES = [("QPSK-1/2", "normal"), ("8PSK-3/5", "normal"), ("QPSK-9/10", "normal"), ("QPSK-1/2", "short")]
ALPHAS = [0.625, 0.75, 0.8125, 0.875, 0.9375, 1.0]
BETAS = [0.25, 0.5, 0.75, 1.0]
FIXED = "fixed:6,8,6:2:b1"           # the format the chapter proposes
WORDS = ["fixed:4,6,5:2:b1", "fixed:5,7,6:2:b1", "fixed:6,8,6:2:b1", "fixed:6,8,6:4:b2", "fixed:8,10,8:4:b2"]
# normalized min-sum in fixed point: floor(7m/8) at 2 LSB/unit vs a fine 32 LSB/unit grid
NORMALIZED = ["fixed:6,8,6:2:7/8", "fixed:10,14,12:32:7/8"]


def spa_threshold(label, frame):
    """Es/N0 where the reference (sum-product) curve in sim/results first has FER < 1e-2."""
    curve = results.load(ROOT / "results" / results.filename(label, frame, False))
    return next(p["esn0"] for p in curve["points"] if p["frames"] and p["fer"] < 1e-2)


def cfg_for(decoder, args, **kw):
    return SimConfig(algorithm=decoder, min_frame_errors=50, max_frames=args.max_frames, batch=8,
                     workers=default_workers(), **kw)


def curve_dict(curve):
    d = curve.to_dict()
    d["decoder"] = curve.config["algorithm"]
    return d


def save(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (name + ".json")
    path.write_text(json.dumps(data, indent=1) + "\n")
    print("wrote", path.relative_to(ROOT), flush=True)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def exp_correction(args):
    out = []
    for label, frame in CODES:
        mc = ModCod.parse(label, frame)
        es = spa_threshold(label, frame)
        decoders = ["spa"] + ["nms:%g" % a for a in ALPHAS] + ["oms:%g" % b for b in BETAS]
        for dec in decoders:
            c = run_curve(mc, [es], cfg_for(dec, args))
            p = c.points[0]
            log(label, frame, dec, "FER %.3f it %.1f" % (p.fer, p.avg_iterations))
            out.append({"modcod": label, "frame": frame, "esn0": es, "decoder": dec, **p.to_dict()})
    save("correction", {"description": "FER vs min-sum correction at the SPA FER<1e-2 Es/N0", "points": out})


def sweep(label, frame, step):
    es = spa_threshold(label, frame)
    return np.round(np.arange(es - 0.3, es + 1.2 + step / 2, step), 2)


def exp_algorithms(args):
    out = []
    for label, frame in CODES:
        mc = ModCod.parse(label, frame)
        # the same corrections for every code, so that the curves compare (correction.json has the sweep)
        for dec in ["spa", "nms:1", "nms:0.8125", "oms:0.5", FIXED]:
            c = run_curve(mc, sweep(label, frame, args.step), cfg_for(dec, args), stop_fer=1e-3)
            log(label, frame, dec, " ".join("%.1f:%.2g" % (p.esn0, p.fer) for p in c.points))
            out.append(curve_dict(c))
    save("algorithms", {"description": "waterfalls per decoder", "curves": out})


def exp_convergence(args):
    label, frame = "QPSK-1/2", "normal"
    mc = ModCod.parse(label, frame)
    es = round(spa_threshold(label, frame) + 0.2, 2)
    limits = [2, 4, 6, 8, 10, 15, 20, 30, 50]
    out = []
    for dec in ("spa", "oms:0.5", "hw-oms:0.5", "flood-oms:0.5"):
        for it in limits:
            c = run_curve(mc, [es], cfg_for(dec, args, max_iter=it))
            p = c.points[0]
            log("convergence", dec, it, "FER %.3f" % p.fer)
            out.append({"decoder": dec, "max_iter": it, **p.to_dict()})
    # iterations needed with early termination, frame by frame
    hist = []
    tx = Transmitter(mc)
    for dec in ("oms:0.5", "flood-oms:0.5", FIXED):
        rx = Receiver(mc, max_iter=50, algorithm=dec)
        for e in (es - 0.1, es + 0.2, es + 0.5):
            rng = np.random.default_rng(int(e * 100) + 7)
            its = []
            for _ in range(min(args.max_frames, 200)):
                f = tx.random_frame(rng)
                y, n0 = awgn(f.plframe, e, rng)
                llr, _ = rx.llr(y, n0)
                its.append(int(rx.fec.ldpc.decode(llr, 50, dec)[2]))
            hist.append({"decoder": dec, "esn0": round(e, 2), "iterations": its})
            log("histogram", dec, round(e, 2), "mean %.1f" % np.mean(its))
    save("convergence", {"modcod": label, "frame": frame, "esn0": es, "limits": out, "histograms": hist})


def exp_quantization(args):
    out = []
    for label, frame in [("QPSK-1/2", "normal"), ("8PSK-3/5", "normal"), ("QPSK-1/2", "short")]:
        mc = ModCod.parse(label, frame)
        for dec in ["oms:0.5", "nms:0.875"] + WORDS + NORMALIZED:
            c = run_curve(mc, sweep(label, frame, args.step), cfg_for(dec, args), stop_fer=1e-3)
            log(label, frame, dec, " ".join("%.1f:%.2g" % (p.esn0, p.fer) for p in c.points))
            out.append(curve_dict(c))
    save("quantization", {"description": "fixed-point word lengths", "curves": out})


def exp_headroom(args):
    """Posterior saturation: FER well above the waterfall vs the extra bits of L over R."""
    out = []
    for label, frame, extra in (("QPSK-1/2", "normal", 0.6), ("8PSK-3/5", "normal", 0.6)):
        mc = ModCod.parse(label, frame)
        es = round(spa_threshold(label, frame) + extra, 2)
        for w_r in (5, 6):
            for head in (0, 1, 2, 3):
                for w_ch in (w_r - 1, w_r):
                    dec = "fixed:%d,%d,%d:2:b1" % (w_ch, w_r + head, w_r)
                    p = run_curve(mc, [es], cfg_for(dec, args)).points[0]
                    log("headroom", label, dec, "FER %.3f LDPC BER %.2e" % (p.fer, p.ldpc_ber))
                    out.append({"modcod": label, "frame": frame, "esn0": es, "decoder": dec, "w_ch": w_ch,
                                "w_L": w_r + head, "w_R": w_r, **p.to_dict()})
    save("headroom", {"description": "posterior saturation: w_L - w_R", "points": out})


def exp_architecture(args):
    rows = []
    fmt = ldpc_hw.FixedPoint(6, 8, 6, scale=2, alpha_num=1, alpha_shift=0, beta=1)
    for frame in ("normal", "short"):
        for rate in RATES[frame]:
            code = dvbs2_ldpc(rate, frame)
            qc = ldpc_hw.qc_structure(code)
            deg = np.diff(code.row_ptr)
            for iters in (10, 30, 50):
                a = ldpc_hw.architecture(code, 360, 200.0, iters, fmt, pipeline_depth=6)
                d = a.as_dict()
                d.pop("layer_order")
                d.update(frame=frame, rate=rate, check_degree=[int(deg.min()), int(deg.max())],
                         layer_degree=[min(qc.layer_degrees), max(qc.layer_degrees)])
                rows.append(d)
    par = []
    for rate in ("1/2", "9/10"):
        code = dvbs2_ldpc(rate, "normal")
        for p in (360, 180, 120, 90, 72, 60, 45, 40, 36, 30):
            a = ldpc_hw.architecture(code, p, 200.0, 30, fmt, pipeline_depth=6)
            par.append({"rate": rate, "parallelism": p, "cycles_per_iter": a.cycles_per_iter,
                        "throughput_mbps": a.throughput_mbps})
    save("architecture", {"f_clk_mhz": 200.0, "pipeline_depth": 6, "format": asdict(fmt),
                          "codes": rows, "parallelism": par})


EXPERIMENTS = {"correction": exp_correction, "algorithms": exp_algorithms, "convergence": exp_convergence,
               "quantization": exp_quantization, "headroom": exp_headroom,
               "architecture": exp_architecture}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=",".join(EXPERIMENTS))
    ap.add_argument("--max-frames", type=int, default=300)
    ap.add_argument("--step", type=float, default=0.1, help="Es/N0 step of the waterfalls [dB]")
    args = ap.parse_args()
    for name in args.only.split(","):
        log("==", name)
        EXPERIMENTS[name](args)


if __name__ == "__main__":
    main()
