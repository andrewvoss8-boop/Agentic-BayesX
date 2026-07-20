#!/usr/bin/env python3
"""figA (MONEY FIGURE): held-out-sensor QOI coverage across the 5 bias combos, by arm.

Left: combined (peak+band) coverage vs combo, one line per arm, with the 0.95 nominal reference.
Right: per-arm distribution over the 5 combos (dots + mean bar) -- the multi-realization upgrade.
Shows comparison (arms vs naive vs nominal), documents source/synthetic, flags non-converged cells.
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import viz

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
ARMS = ["M0", "M1", "M2", "M3"]

cov = json.load(open(OUT / "coverage_summary.json"))
cells = [json.load(open(p)) for p in glob.glob(str(OUT / "cell_*.json")) if "samples" not in p]
main = [c for c in cells if not c.get("tag")]
nonconv = {(c["combo_idx"], c["arm"]) for c in main if not c.get("converged", False)}

fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"width_ratios": [1.5, 1]})

combos = cov["by_arm"]["M0"]["per_combo_idx"]
combo_names = {1: "identif.", 2: "unident.", 3: "mixed", 4: "large", 5: "broad"}
x = np.arange(len(combos))
for a in ARMS:
    y = cov["by_arm"][a]["per_combo_combined"]
    axL.plot(x, y, "-o", color=viz.ARM_COLOR[a], lw=1.8, ms=5, label=viz.ARM_LABEL[a])
    axL.annotate(viz.ARM_LABEL[a], (x[-1], y[-1]), xytext=(6, 0), textcoords="offset points",
                 color=viz.ARM_COLOR[a], fontsize=8, va="center")
# mark non-converged cells
for ci, a in nonconv:
    j = combos.index(ci)
    axL.plot(x[j], cov["by_arm"][a]["per_combo_combined"][j], "x", color="k", ms=9, mew=1.6)
axL.axhline(0.95, color=viz.C_NOMINAL, ls="--", lw=1.0)
axL.annotate("nominal 0.95", (x[0], 0.95), xytext=(0, 4), textcoords="offset points",
             color="0.45", fontsize=7.5)
axL.set_xticks(x)
axL.set_xticklabels([f"{ci}\n{combo_names[ci]}" for ci in combos], fontsize=8)
axL.set_ylim(0, 1.02)
axL.set_xlabel("truth bias combo")
axL.set_ylabel("held-out QOI 95% coverage (peak+band)")
axL.set_title("Held-out-sensor QOI coverage by arm", fontsize=10)
axL.set_xlim(-0.3, x[-1] + 1.4)

# right: distribution over combos
for i, a in enumerate(ARMS):
    y = cov["by_arm"][a]["per_combo_combined"]
    xa = np.full(len(y), i) + np.random.default_rng(i).uniform(-0.08, 0.08, len(y))
    axR.plot(xa, y, "o", color=viz.ARM_COLOR[a], ms=5, alpha=0.7)
    axR.plot([i - 0.22, i + 0.22], [np.mean(y)] * 2, "-", color=viz.ARM_COLOR[a], lw=2.5)
axR.axhline(0.95, color=viz.C_NOMINAL, ls="--", lw=1.0)
axR.set_xticks(range(len(ARMS)))
axR.set_xticklabels(ARMS, fontsize=9)
axR.set_ylim(0, 1.02)
axR.set_xlabel("arm (bar = mean over 5 combos)")
axR.set_title("Coverage distribution over 5 combos", fontsize=10)

flag = "  [x = NOT-converged cell, intervals not-trustworthy]" if nonconv else ""
viz.save(fig, "figA_heldout_qoi_coverage",
         extra=f"5 combos x 4 arms; held-out QOI = peak |H| + band-GRMS{flag}")
print("figA done; nonconv cells:", sorted(nonconv))
