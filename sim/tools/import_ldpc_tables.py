#!/usr/bin/env python3
"""Convert AFF3CT's DVB-S2 LDPC constants (MIT licence) into plain-text tables.

Usage:  python3 sim/tools/import_ldpc_tables.py DVBS2_constants_64800.hpp DVBS2_constants_16200.hpp

The headers come from https://github.com/aff3ct/aff3ct
(include/Tools/Code/LDPC/Standard/DVBS2/).  They hold the parity bit
accumulator addresses of ETSI EN 302 307-1 Annex B (normal frames) and
Annex C (short frames).  Each output file has one line per group of 360
information bits, as printed in the standard.
"""
import pathlib
import re
import sys

OUT = pathlib.Path(__file__).resolve().parent.parent / "src" / "dvbs2" / "data" / "ldpc"
RATES = {(64800, 58320): "9_10", (64800, 57600): "8_9", (64800, 54000): "5_6", (64800, 51840): "4_5",
         (64800, 48600): "3_4", (64800, 43200): "2_3", (64800, 38880): "3_5", (64800, 32400): "1_2",
         (64800, 25920): "2_5", (64800, 21600): "1_3", (64800, 16200): "1_4",
         (16200, 14400): "8_9", (16200, 13320): "5_6", (16200, 12600): "4_5", (16200, 11880): "3_4",
         (16200, 10800): "2_3", (16200, 9720): "3_5", (16200, 7200): "1_2", (16200, 6480): "2_5",
         (16200, 5400): "1_3", (16200, 3240): "1_4"}


def main(paths):
    OUT.mkdir(parents=True, exist_ok=True)
    for path in paths:
        text = pathlib.Path(path).read_text()
        for body in re.findall(r"struct dvbs2_values_\d+_\d+ : dvbs2_values.*?\n\};", text, re.S):
            values = [int(v) for v in re.findall(r"-?\d+", re.search(r"\(\s*\{(.*?)\}\s*\)", body, re.S).group(1))]
            n = int(re.search(r"this->N = (\d+);", body).group(1))
            k = int(re.search(r"this->K = (\d+);", body).group(1))
            lines, i = [], 0
            while i < len(values):
                count = values[i]
                lines.append(" ".join(map(str, values[i + 1:i + 1 + count])))
                i += 1 + count
            assert len(lines) == k // 360, (n, k, len(lines))
            frame = "normal" if n == 64800 else "short"
            name = OUT / ("%s_%s.txt" % (frame, RATES[(n, k)]))
            name.write_text("\n".join(lines) + "\n")
            print("wrote", name.relative_to(OUT.parent.parent.parent.parent), len(lines), "rows")


if __name__ == "__main__":
    main(sys.argv[1:])
