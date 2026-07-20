#!/usr/bin/env python3
"""Discretization Resolution Gate artifact: coarse shield mesh (10x6/10x3,
~4.6 in elements) vs 2x h-refined, plus the drilling-stiffness x100 arm.
Sorted-frequency pairing is valid only while the two lists track (first ~30
modes); above that only cumulative mode counts N(f) are compared.
Output: out/discretization_check.json
"""
import json
import os

import numpy as np

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = json.load(open(os.path.join(WS, "out", "modes_nominal.json")))
b = json.load(open(os.path.join(WS, "out", "modes_nominal_refined.json")))
dr = json.load(open(os.path.join(WS, "out", "modes_nominal_drillx100.json")))
fa = np.array([m["freq_hz"] for m in a["modes"]])
fb = np.array([m["freq_hz"] for m in b["modes"]])
fd = np.array([m["freq_hz"] for m in dr["modes"]])
n = 30
shift = (fa[:n] - fb[:n]) / fb[:n]
counts = {str(t): dict(coarse=int((fa <= t).sum()),
                       refined_x2=int((fb <= t).sum()))
          for t in (50, 100, 150, 200, 250, 300, 400, 500)}
out = dict(
    note=("Discretization Resolution Gate artifact. Coarse shield mesh (10x6 "
          "upper / 10x3 lower, ~4.6 in elements) vs 2x h-refined; "
          "sorted-frequency pairing valid only while lists track (first ~30 "
          "modes). Above that, compare cumulative mode COUNTS N(f) only."),
    first30_shift_pct=[round(100 * s, 2) for s in shift],
    max_abs_shift_first30_pct=round(100 * float(np.abs(shift).max()), 2),
    median_abs_shift_first30_pct=round(100 * float(np.median(np.abs(shift))), 2),
    f1=dict(coarse=float(fa[0]), refined=float(fb[0])),
    cumulative_mode_counts=counts,
    drill_arm=dict(
        f1_nominal=float(fa[0]), f1_drillx100=float(fd[0]),
        first20_max_abs_shift_pct=round(
            100 * float(np.abs((fa[:20] - fd[:20]) / fd[:20]).max()), 3),
        verdict="drilling-stiffness choice does not drive in-band modes"),
    verdict=("Mode-by-mode trustworthy to ~mode 30 (~150 Hz): median |shift| "
             f"{round(100 * float(np.median(np.abs(shift))), 2)}%, max "
             f"{round(100 * float(np.abs(shift).max()), 2)}%. Above ~250 Hz "
             "the coarse mesh distorts panel modal density "
             f"({counts['500']['coarse']} vs {counts['500']['refined_x2']} "
             "modes <=500 Hz): treat upper band as modal-density-only, not "
             "mode-matched. Acceptable for the coarse-prior purpose; "
             "calibration features should weight the lower band."),
)
with open(os.path.join(WS, "out", "discretization_check.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print("max |shift| first30: %.2f%%; counts@500: %s"
      % (out["max_abs_shift_first30_pct"], counts["500"]))
