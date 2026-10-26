"""Monte Carlo BER/FER simulation of the DVB-S2 link over AWGN.

Each Es/N0 point runs frames until ``min_frame_errors`` frame errors or
``max_frames`` frames, whichever comes first.  Frames are simulated in
batches, optionally on several processes; every batch has its own seed
derived from ``seed`` so results are reproducible for a given batch size.
"""
from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field

import numpy as np

from ..phy.bbframe import bb_scramble, parse_bbframe
from ..phy.channel import awgn, esn0_to_ebn0
from ..phy.link import Receiver, Transmitter
from ..phy.modcod import ModCod


@dataclass
class SimConfig:
    max_iter: int = 50
    algorithm: str = "spa"      # LDPC decoder: spa, nms, oms
    demap: str = "exact"        # exact or maxlog
    min_frame_errors: int = 50
    max_frames: int = 2000
    batch: int = 8
    workers: int = 1
    seed: int = 2008


@dataclass
class PointResult:
    esn0: float
    ebn0: float
    frames: int = 0
    frame_errors: int = 0          # payload of the BBFRAME wrong (after BCH)
    bit_errors: int = 0            # payload bit errors (after BCH)
    bits: int = 0
    ldpc_frame_errors: int = 0     # LDPC output not a codeword / differs from the sent FECFRAME
    ldpc_bit_errors: int = 0       # BCH-input bit errors (after LDPC, before BCH)
    ldpc_bits: int = 0
    bch_failures: int = 0
    iterations: int = 0
    seconds: float = 0.0

    @property
    def fer(self):
        return self.frame_errors / self.frames if self.frames else float("nan")

    @property
    def ber(self):
        return self.bit_errors / self.bits if self.bits else float("nan")

    @property
    def ldpc_ber(self):
        return self.ldpc_bit_errors / self.ldpc_bits if self.ldpc_bits else float("nan")

    @property
    def ldpc_fer(self):
        return self.ldpc_frame_errors / self.frames if self.frames else float("nan")

    @property
    def avg_iterations(self):
        return self.iterations / self.frames if self.frames else float("nan")

    def add(self, other: "PointResult"):
        for name in ("frames", "frame_errors", "bit_errors", "bits", "ldpc_frame_errors", "ldpc_bit_errors",
                     "ldpc_bits", "bch_failures", "iterations"):
            setattr(self, name, getattr(self, name) + getattr(other, name))

    def to_dict(self):
        d = asdict(self)
        d.update(fer=self.fer, ber=self.ber, ldpc_fer=self.ldpc_fer, ldpc_ber=self.ldpc_ber,
                 avg_iterations=self.avg_iterations)
        return d


@dataclass
class CurveResult:
    modcod: str
    frame: str
    pilots: bool
    config: dict
    points: list = field(default_factory=list)

    def to_dict(self):
        mc = ModCod.parse(self.modcod, self.frame, self.pilots)
        return {"modcod": self.modcod, "frame": self.frame, "pilots": self.pilots,
                "efficiency": mc.efficiency, "qef_esn0": mc.qef_esn0, "config": self.config,
                "points": [p.to_dict() for p in self.points]}


_LINKS: dict = {}


def _link(mc: ModCod, cfg: SimConfig):
    key = (mc, cfg.max_iter, cfg.algorithm, cfg.demap)
    if key not in _LINKS:
        _LINKS[key] = (Transmitter(mc), Receiver(mc, max_iter=cfg.max_iter, algorithm=cfg.algorithm,
                                                 demap=cfg.demap))
    return _LINKS[key]


def simulate_batch(mc: ModCod, esn0: float, n_frames: int, cfg: SimConfig, seed) -> PointResult:
    tx, rx = _link(mc, cfg)
    ldpc, bch = rx.fec.ldpc, rx.fec.bch
    rng = np.random.default_rng(seed)
    res = PointResult(esn0, float(esn0_to_ebn0(esn0, mc.efficiency)))
    for _ in range(n_frames):
        f = tx.random_frame(rng)
        y, n0 = awgn(f.plframe, esn0, rng)
        llr, _ = rx.llr(y, n0)
        hard, _, it = ldpc.decode(llr, cfg.max_iter, cfg.algorithm)
        ldpc_errs = int(np.count_nonzero(hard[:bch.n] != f.fecframe[:bch.n]))
        dec = bch.decode(hard[:bch.n])
        # Payload bits are compared in place; a corrupt BBHEADER makes the frame wrong too.
        bb = bb_scramble(dec.codeword[:bch.k])
        errs = int(np.count_nonzero(bb[80:80 + f.data.size] != f.data))
        res.frames += 1
        res.bits += f.data.size
        res.bit_errors += errs
        res.frame_errors += errs > 0 or not parse_bbframe(bb)[1]
        res.ldpc_bits += bch.n
        res.ldpc_bit_errors += ldpc_errs
        res.ldpc_frame_errors += ldpc_errs > 0
        res.iterations += it
        res.bch_failures += not dec.success
    return res


def _batch_task(args):
    return simulate_batch(*args)


def run_point(mc: ModCod, esn0: float, cfg: SimConfig, pool=None, progress=None) -> PointResult:
    total = PointResult(esn0, float(esn0_to_ebn0(esn0, mc.efficiency)))
    seeds = np.random.SeedSequence([cfg.seed, int(round(esn0 * 1000)) & 0xFFFFFFFF, mc.id])
    t0 = time.time()
    width = max(1, cfg.workers)

    def done():
        return total.frame_errors >= cfg.min_frame_errors or total.frames >= cfg.max_frames

    while not done():
        n_tasks = min(width, -(-(cfg.max_frames - total.frames) // cfg.batch))
        tasks = [(mc, esn0, min(cfg.batch, cfg.max_frames - total.frames - i * cfg.batch), cfg, s)
                 for i, s in enumerate(seeds.spawn(n_tasks))]
        tasks = [t for t in tasks if t[2] > 0]
        results = pool.map(_batch_task, tasks) if pool is not None else map(_batch_task, tasks)
        for r in results:
            total.add(r)
        total.seconds = time.time() - t0
        if progress:
            progress(total)
    return total


def run_curve(mc: ModCod, esn0_points, cfg: SimConfig | None = None, progress=None,
              stop_fer: float | None = None) -> CurveResult:
    """Simulate a waterfall; stops early once FER drops below ``stop_fer``."""
    cfg = cfg or SimConfig()
    curve = CurveResult(mc.label, mc.frame, mc.pilots, asdict(cfg))
    pool = ProcessPoolExecutor(cfg.workers) if cfg.workers > 1 else None
    try:
        for esn0 in esn0_points:
            p = run_point(mc, float(esn0), cfg, pool, progress)
            curve.points.append(p)
            if stop_fer is not None and p.fer < stop_fer:
                break
    finally:
        if pool is not None:
            pool.shutdown()
    return curve


def default_workers() -> int:
    return max(1, (os.cpu_count() or 2) - 1)
