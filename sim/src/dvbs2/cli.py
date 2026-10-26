"""Command-line interface: ``dvbs2sim <command>``.

    dvbs2sim info                                   # MODCOD table
    dvbs2sim ber --modcod QPSK-1/2 --esn0 0.6:0.1:1.2
    dvbs2sim ber --modcod 8PSK-3/5 --frame short --esn0 5:0.2:6.4 --workers 8 --plot fer.png
    dvbs2sim plot results/*.json -o curves.png
    dvbs2sim bch-matrices -o Matrices              # A^p and B_p text files read by main.c
"""
from __future__ import annotations

import argparse
import sys

from . import __version__


def cmd_info(args):
    from .phy.capacity import shannon_esn0
    from .phy.modcod import all_modcods

    print("%-4s %-12s %6s %6s %6s %3s %7s %7s %9s %9s" % ("id", "MODCOD", "Kbch", "Nbch", "Nldpc", "t", "slots",
                                                         "symbols", "eta", "QEF Es/N0"))
    for mc in all_modcods(args.frame, args.pilots):
        q = mc.qef_esn0 if args.frame == "normal" else None
        print("%-4d %-12s %6d %6d %6d %3d %7d %7d %9.4f %9s   (Shannon %.2f dB)" % (
            mc.id, mc.label, mc.k_bch, mc.n_bch, mc.n_ldpc, mc.t, mc.slots, mc.plframe_symbols, mc.efficiency,
            "%.2f" % q if q is not None else "-", float(shannon_esn0(mc.efficiency))))


def cmd_ber(args):
    from .phy.modcod import ModCod
    from .sim import results
    from .sim.montecarlo import SimConfig, default_workers, run_curve

    mc = ModCod.parse(args.modcod, args.frame, args.pilots)
    cfg = SimConfig(max_iter=args.iters, algorithm=args.decoder, demap=args.demap,
                    min_frame_errors=args.min_errors, max_frames=args.max_frames, batch=args.batch,
                    workers=args.workers or default_workers(), seed=args.seed)
    print("%s: K_bch=%d, %d symbols/frame, eta=%.4f, %d worker(s)" % (mc, mc.k_bch, mc.plframe_symbols,
                                                                      mc.efficiency, cfg.workers))

    last = []

    def progress(p):
        if not sys.stdout.isatty():
            return
        if last and last[-1] != p.esn0:
            print()
        last.append(p.esn0)
        print("\r  Es/N0 %6.2f dB  frames %6d  frame errors %5d  FER %.3e  BER %.3e  (%.0fs)" % (
            p.esn0, p.frames, p.frame_errors, p.fer, p.ber, p.seconds), end="", flush=True)

    curve = run_curve(mc, results.frange(args.esn0), cfg, progress=progress, stop_fer=args.stop_fer)
    if last:
        print()
    data = curve.to_dict()
    print(results.summary_table(data))
    out = args.output or "results/" + results.filename(mc.label, mc.frame, mc.pilots)
    print("saved", results.save(data, out))
    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        ax = results.plot([data], metric="fer")
        ax.figure.savefig(args.plot, dpi=150, bbox_inches="tight")
        print("plot", args.plot)


def cmd_plot(args):
    import matplotlib
    matplotlib.use("Agg")
    from .sim import results

    curves = [results.load(p) for p in args.files]
    ax = results.plot(curves, metric=args.metric, x=args.x)
    ax.figure.savefig(args.output, dpi=150, bbox_inches="tight")
    print("wrote", args.output)


def cmd_bch_matrices(args):
    from .codes.bch import dvbs2_bch
    from .codes.bch_parallel import ParallelLFSR

    for rate, tag in (("1/2", "t12"), ("2/3", "t10"), ("8/9", "t8")):
        g = dvbs2_bch(rate).g
        for mode in ("n", "k"):
            enc = ParallelLFSR(g, args.p, mode, reg_len=192 if mode == "k" else None)
            for path in enc.write_matrices(args.output, tag):
                print("wrote", path)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="dvbs2sim", description="DVB-S2 physical-layer simulator")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("info", help="list the MODCODs and their parameters")
    p.add_argument("--frame", default="normal", choices=["normal", "short"])
    p.add_argument("--pilots", action="store_true")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("ber", help="Monte Carlo BER/FER curve over AWGN")
    p.add_argument("--modcod", required=True, help="e.g. QPSK-1/2, 8PSK-3/5, 16APSK-3/4, 32APSK-9/10")
    p.add_argument("--esn0", required=True, help="start:step:stop or comma list, in dB")
    p.add_argument("--frame", default="normal", choices=["normal", "short"])
    p.add_argument("--pilots", action="store_true")
    p.add_argument("--decoder", default="spa", choices=["spa", "nms", "oms"])
    p.add_argument("--demap", default="exact", choices=["exact", "maxlog"])
    p.add_argument("--iters", type=int, default=50)
    p.add_argument("--min-errors", type=int, default=50)
    p.add_argument("--max-frames", type=int, default=2000)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--workers", type=int, default=0, help="processes (default: CPUs - 1)")
    p.add_argument("--seed", type=int, default=2008)
    p.add_argument("--stop-fer", type=float, default=None, help="stop the sweep below this FER")
    p.add_argument("-o", "--output", help="JSON output (default results/<modcod>_<frame>.json)")
    p.add_argument("--plot", help="also save a FER plot (png/pdf/svg)")
    p.set_defaults(func=cmd_ber)

    p = sub.add_parser("plot", help="plot saved curves")
    p.add_argument("files", nargs="+")
    p.add_argument("-o", "--output", default="curves.png")
    p.add_argument("--metric", default="fer", choices=["fer", "ber", "ldpc_fer", "ldpc_ber"])
    p.add_argument("--x", default="esn0", choices=["esn0", "ebn0"])
    p.set_defaults(func=cmd_plot)

    p = sub.add_parser("bch-matrices", help="write the A^p / B_p matrices of the parallel BCH encoder")
    p.add_argument("-o", "--output", default="Matrices")
    p.add_argument("-p", type=int, default=8, help="degree of parallelism")
    p.set_defaults(func=cmd_bch_matrices)

    args = ap.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
