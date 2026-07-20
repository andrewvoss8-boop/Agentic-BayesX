#!/usr/bin/env python3
"""figC: theta recovery (identifiable vs not) by combo, for the Schneider arm (M2).

Per combo, plot the 9-group posterior medians + 95% CI vs the truth multiplier, identifiable groups
(strain-energy set) drawn dark, unidentifiable light. Shows: identifiable-group bias recovered;
unidentifiable groups stay near prior (median ~1), and the truth marker reveals covered/missed.
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
ARM = "M2"

idf = json.load(open(OUT / "identifiability.json"))
informed = set(idf.get("informed_groups_strain_energy", []))
cells = {}
for p in glob.glob(str(OUT / f"cell_*_{ARM}.json")):
    c = json.load(open(p))
    if not c.get("tag"):
        cells[c["combo_idx"]] = c
combos = sorted(cells)
GN = [r["group"] for r in cells[combos[0]]["theta"]]
yy = np.arange(len(GN))

fig, axs = plt.subplots(1, len(combos), figsize=(3.0 * len(combos), 4.6), sharey=True)
combo_names = {1: "identif.", 2: "unident.", 3: "mixed", 4: "large", 5: "broad"}
for k, ci in enumerate(combos):
    ax = axs[k]
    th = {r["group"]: r for r in cells[ci]["theta"]}
    for i, g in enumerate(GN):
        r = th[g]
        dark = g in informed
        col = "#111111" if dark else "#b0b0b0"
        ax.plot([r["lo"], r["hi"]], [i, i], "-", color=col, lw=2.2 if dark else 1.4,
                solid_capstyle="round", alpha=0.95 if dark else 0.7)
        ax.plot(r["median"], i, "o", color=col, ms=4)
        # truth marker: red diamond if biased, else small grey tick
        biased = abs(r["truth"] - 1.0) > 1e-6
        tcol = "#dc2626" if biased else "#9ca3af"
        ax.plot(r["truth"], i, "D", color=tcol, ms=5 if biased else 3,
                mec="k" if (biased and not r["covered"]) else "none", mew=1.0)
    ax.axvline(1.0, color="0.8", lw=0.8)
    ax.set_title(f"combo {ci}\n{combo_names[ci]}", fontsize=9)
    ax.set_xlim(0.5, 1.7)
    ax.set_xlabel("theta (stiffness mult.)", fontsize=8)
axs[0].set_yticks(yy); axs[0].set_yticklabels(GN, fontsize=8)
axs[0].annotate("dark = identifiable (strain energy);  red diamond = biased truth;\nblack-edged diamond = MISSED",
                (0.02, 1.04), xycoords="axes fraction", fontsize=7.5, color="0.3")
fig.suptitle(f"theta recovery by combo (Schneider arm {ARM}); identifiable groups recover, "
             f"unidentifiable stay near prior", fontsize=10.5, y=1.05)
viz.save(fig, "figC_theta_recovery", extra=f"arm {ARM}; truth=red diamond; informed set={sorted(informed)}")
print("figC done")
