#!/usr/bin/env python3
"""Parse NASA's SOL 111 punch files (FEM/Correlation/FRF_Verification/SOL_111_Free_Free_Force_*.pch):
acceleration FRFs in magnitude/phase, SORT2 layout. Record per frequency (four 80-column lines):
  data line   freq  G  |T1| |T2| |T3|
  -CONT-      |R1| |R2| |R3|
  -CONT-      phase T1 T2 T3 (deg)
  -CONT-      phase R1 R2 R3 (deg)
Each point starts with a '$POINT ID = n' header. Layout follows the parser the project used in
June 2026 (shocksat_opus_20260609/scripts/opus_hammer_frf.py::parse_pch_frf), extended to all three
translations. Units are those of NASA's run; the factor to the plotted g/lbf is calibrated, not assumed.
Returns {point: (freq_hz, mag (n, 3), phase_deg (n, 3))}."""
import re

import numpy as np

NUM = re.compile(r"[-+]?\d+\.\d+E[-+]?\d+")


def parse(path):
    out, cur, freq, buf = {}, None, None, []

    def flush():
        nonlocal buf, freq
        if cur is not None and freq is not None and len(buf) >= 12:
            d = out.setdefault(cur, ([], [], []))
            d[0].append(freq); d[1].append(buf[0:3]); d[2].append(buf[6:9])
        buf, freq = [], None

    for line in open(path, errors="replace"):
        if line.startswith("$POINT ID"):
            flush()
            m = re.search(r"\$POINT ID\s*=\s*(\d+)", line)
            cur = int(m.group(1)) if m else None
            continue
        if line.startswith("$"):
            continue
        nums = [float(x) for x in NUM.findall(line[:72])]
        if line.lstrip().startswith("-CONT-"):
            buf.extend(nums)
        else:
            flush()
            if nums:
                freq, buf = nums[0], nums[1:]
    flush()
    res = {}
    for p, (f, m, ph) in out.items():
        o = np.argsort(f)
        res[p] = (np.asarray(f)[o], np.asarray(m)[o], np.asarray(ph)[o])
    return res


def write_synthetic(path, points, f, mags, phases):
    """Writer used only by the known-answer test (same layout as parse expects)."""
    with open(path, "w") as fh:
        fh.write("$TITLE   = SYNTHETIC\n$ACCELERATION\n$REAL-IMAGINARY OUTPUT\n")
        for p, M, P in zip(points, mags, phases):
            fh.write(f"$POINT ID =     {p:8d}  IDENTIFIED BY FREQUENCY\n")
            for i, fi in enumerate(f):
                fh.write(f"{fi:18.6E}       G   {M[i,0]:18.6E}{M[i,1]:18.6E}{M[i,2]:18.6E}\n"[:80] + "\n" if False else
                         f"{fi:13.6E}  G   {M[i,0]:13.6E}{M[i,1]:13.6E}{M[i,2]:13.6E}\n")
                fh.write(f"-CONT-          {0.0:13.6E}{0.0:13.6E}{0.0:13.6E}\n")
                fh.write(f"-CONT-          {P[i,0]:13.6E}{P[i,1]:13.6E}{P[i,2]:13.6E}\n")
                fh.write(f"-CONT-          {0.0:13.6E}{0.0:13.6E}{0.0:13.6E}\n")
