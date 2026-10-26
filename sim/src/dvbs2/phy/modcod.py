"""DVB-S2 modulation and coding modes (ETSI EN 302 307-1, Tables 5a/5b, 9, 10, 13)."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from ..codes.bch import _NORMAL, _SHORT

BITS_PER_SYMBOL = {"QPSK": 2, "8PSK": 3, "16APSK": 4, "32APSK": 5}

# (modulation, rate) -> PLS MODCOD field value (Table 12)
MODCOD_ID = {}
for _i, _r in enumerate(["1/4", "1/3", "2/5", "1/2", "3/5", "2/3", "3/4", "4/5", "5/6", "8/9", "9/10"]):
    MODCOD_ID[("QPSK", _r)] = 1 + _i
for _i, _r in enumerate(["3/5", "2/3", "3/4", "5/6", "8/9", "9/10"]):
    MODCOD_ID[("8PSK", _r)] = 12 + _i
for _i, _r in enumerate(["2/3", "3/4", "4/5", "5/6", "8/9", "9/10"]):
    MODCOD_ID[("16APSK", _r)] = 18 + _i
for _i, _r in enumerate(["3/4", "4/5", "5/6", "8/9", "9/10"]):
    MODCOD_ID[("32APSK", _r)] = 24 + _i

# Ideal Es/N0 (dB) for quasi-error-free operation (PER = 1e-7, normal frames,
# AWGN, 50 iterations), Table 13.
QEF_ESN0 = {
    ("QPSK", "1/4"): -2.35, ("QPSK", "1/3"): -1.24, ("QPSK", "2/5"): -0.30, ("QPSK", "1/2"): 1.00,
    ("QPSK", "3/5"): 2.23, ("QPSK", "2/3"): 3.10, ("QPSK", "3/4"): 4.03, ("QPSK", "4/5"): 4.68,
    ("QPSK", "5/6"): 5.18, ("QPSK", "8/9"): 6.20, ("QPSK", "9/10"): 6.42,
    ("8PSK", "3/5"): 5.50, ("8PSK", "2/3"): 6.62, ("8PSK", "3/4"): 7.91, ("8PSK", "5/6"): 9.35,
    ("8PSK", "8/9"): 10.69, ("8PSK", "9/10"): 10.98,
    ("16APSK", "2/3"): 8.97, ("16APSK", "3/4"): 10.21, ("16APSK", "4/5"): 11.03,
    ("16APSK", "5/6"): 11.61, ("16APSK", "8/9"): 12.89, ("16APSK", "9/10"): 13.13,
    ("32APSK", "3/4"): 12.73, ("32APSK", "4/5"): 13.64, ("32APSK", "5/6"): 14.28,
    ("32APSK", "8/9"): 15.69, ("32APSK", "9/10"): 16.05,
}

# APSK ring radius ratios (Tables 9 and 10): gamma = R2/R1 (16APSK), (R2/R1, R3/R1) (32APSK)
GAMMA_16APSK = {"2/3": 3.15, "3/4": 2.85, "4/5": 2.75, "5/6": 2.70, "8/9": 2.60, "9/10": 2.57}
GAMMA_32APSK = {"3/4": (2.84, 5.27), "4/5": (2.72, 4.87), "5/6": (2.64, 4.64),
                "8/9": (2.54, 4.33), "9/10": (2.53, 4.30)}

FRAME_BITS = {"normal": 64800, "short": 16200}
BBHEADER_BITS = 80
SLOT = 90
PILOT_BLOCK = 36
PILOT_PERIOD = 16  # slots between pilot blocks


@dataclass(frozen=True)
class ModCod:
    modulation: str
    rate: str
    frame: str = "normal"
    pilots: bool = False

    def __post_init__(self):
        if (self.modulation, self.rate) not in MODCOD_ID:
            raise ValueError("no DVB-S2 MODCOD %s %s" % (self.modulation, self.rate))
        if self.frame == "short" and self.rate == "9/10":
            raise ValueError("rate 9/10 is not defined for short frames")
        if self.frame not in FRAME_BITS:
            raise ValueError("frame must be 'normal' or 'short'")

    @classmethod
    def parse(cls, text: str, frame: str = "normal", pilots: bool = False) -> "ModCod":
        """'8PSK-3/5', '8psk 3/5' or 'QPSK_1_2' -> ModCod."""
        t = text.upper().replace("_", " ").replace("-", " ").split()
        mod, rate = t[0], "/".join(t[1:]) if len(t) > 2 else t[1]
        return cls(mod, rate, frame, pilots)

    def __str__(self):
        return "%s %s%s%s" % (self.modulation, self.rate, " short" if self.frame == "short" else "",
                              " pilots" if self.pilots else "")

    @property
    def label(self) -> str:
        return "%s-%s" % (self.modulation, self.rate)

    @property
    def id(self) -> int:
        return MODCOD_ID[(self.modulation, self.rate)]

    @property
    def bits_per_symbol(self) -> int:
        return BITS_PER_SYMBOL[self.modulation]

    @property
    def n_ldpc(self) -> int:
        return FRAME_BITS[self.frame]

    @property
    def n_bch(self) -> int:
        return _NORMAL[self.rate][0] if self.frame == "normal" else _SHORT[self.rate]

    @property
    def t(self) -> int:
        return _NORMAL[self.rate][1] if self.frame == "normal" else 12

    @property
    def k_bch(self) -> int:
        return self.n_bch - (16 if self.frame == "normal" else 14) * self.t

    @property
    def dfl_max(self) -> int:
        """Data field length: BBFRAME minus the 80-bit BBHEADER."""
        return self.k_bch - BBHEADER_BITS

    @property
    def code_rate(self) -> Fraction:
        """Nominal LDPC rate (short 1/4 etc. are really K/N = 1/5 ...)."""
        return Fraction(self.rate)

    @property
    def slots(self) -> int:
        return self.n_ldpc // (self.bits_per_symbol * SLOT)

    @property
    def pilot_blocks(self) -> int:
        return (self.slots - 1) // PILOT_PERIOD if self.pilots else 0

    @property
    def plframe_symbols(self) -> int:
        return SLOT * (self.slots + 1) + PILOT_BLOCK * self.pilot_blocks

    @property
    def efficiency(self) -> float:
        """Spectral efficiency (information bits per transmitted symbol, Table 13)."""
        return self.dfl_max / self.plframe_symbols

    @property
    def gamma(self):
        if self.modulation == "16APSK":
            return GAMMA_16APSK[self.rate]
        if self.modulation == "32APSK":
            return GAMMA_32APSK[self.rate]
        return None

    @property
    def qef_esn0(self) -> float | None:
        """Es/N0 for QEF operation from Table 13 (normal frames, no pilots)."""
        return QEF_ESN0.get((self.modulation, self.rate))


def all_modcods(frame: str = "normal", pilots: bool = False) -> list[ModCod]:
    out = []
    for (mod, rate), _ in sorted(MODCOD_ID.items(), key=lambda kv: kv[1]):
        if frame == "short" and rate == "9/10":
            continue
        out.append(ModCod(mod, rate, frame, pilots))
    return out
