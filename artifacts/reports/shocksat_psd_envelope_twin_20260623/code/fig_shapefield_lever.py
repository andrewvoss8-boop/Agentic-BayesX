#!/usr/bin/env python3
"""Deck figure — the MODEL-FORM lever that DOES help amplitude: inferring the mode-shape FIELD (L8b Beck) vs
using FEM shapes (corrects the earlier 'no model-form lever helps amplitude'). Tufte gate."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
d = json.loads((WS / "out" / "shapefield_lever.json").read_text())
seeds = sorted(d["seeds"]);
fem_IS = [d["seeds"][s]["fem_IS"] for s in seeds]; inf_IS = [d["seeds"][s]["inf_IS"] for s in seeds]
fem_sk = [d["seeds"][s]["fem_skill"] for s in seeds]; inf_sk = [d["seeds"][s]["inf_skill"] for s in seeds]

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.4))
x = np.arange(len(seeds)); w = 0.36
ax[0].bar(x - w/2, fem_IS, w, color="#9970ab", label="FEM shapes")
ax[0].bar(x + w/2, inf_IS, w, color="#1b7837", label="inferred shape field")
ax[0].set_xticks(x); ax[0].set_xticklabels([f"split {s}" for s in seeds]); ax[0].set_ylabel("held-out interval score (lower=better)")
ax[0].set_title(f"A. Inferring shapes sharpens amplitude (~{round(100*(1-d['mean_inf_IS']/d['mean_fem_IS']))}% on avg)", fontsize=9.5, loc="left")
ax[0].legend(fontsize=8)
ax[1].bar(x - w/2, fem_sk, w, color="#9970ab", label="FEM shapes")
ax[1].bar(x + w/2, inf_sk, w, color="#1b7837", label="inferred shape field")
ax[1].axhline(0, color="0.3", lw=1); ax[1].text(len(seeds)-0.5, 0.03, "climatology (skill 0)", fontsize=7, ha="right", color="0.4")
ax[1].set_xticks(x); ax[1].set_xticklabels([f"split {s}" for s in seeds]); ax[1].set_ylabel("CRPS-skill vs climatology")
ax[1].set_title(f"B. Halves the skill deficit (−0.68→−0.25) — still <0", fontsize=9.5, loc="left"); ax[1].legend(fontsize=8, loc="lower left")
fig.suptitle("Model-form lever that DOES help amplitude: infer the mode-shape FIELD (Beck/L8b) vs FEM shapes",
             fontsize=10.5, y=0.99)
fig.text(0.5, 0.005, "Held-out impact-channel peak |H|, 3 splits; free system shapes pulled to the .ash measured shapes (MAC) + Rayleigh-consistency. "
         "Sharpens interval ~43% & coverage→0.97, halves CRPS-skill deficit — but single-impact amplitude still doesn't beat climatology.",
         ha="center", fontsize=6.6, color="0.4")
fig.tight_layout(rect=[0, 0.04, 1, 0.95]); fig.savefig(WS / "figures" / "fig_shapefield_lever.png", dpi=140); plt.close(fig)
print("wrote fig_shapefield_lever.png")
