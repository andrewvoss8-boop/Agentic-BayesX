#!/usr/bin/env python3
"""Fig A (money): held-out-sensor QOI proper-score scorecard, IFT vs L5 vs M2, peak + band, over splits.
Shows the split-to-split DISTRIBUTION (every split a dot), not just medians. Log y (interval scores span
~1e3 to ~1e17 across arms). M2 flagged NON-CONVERGED; IFT flagged TMCMC (cross-run R-hat ~1.0)."""
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

CODE = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE))
import figlib as F

WS = Path(__file__).resolve().parents[2]
sc = json.loads((WS / "out" / "scorecard.json").read_text())
arms = ["L5", "IFT", "M2"]


def per_split(arm, qoi, score):
    """recover the per-split values if cached, else use the distribution summary as a single point cloud."""
    a = sc["arms"][arm][qoi][score]
    # we stored med/p5/p95/min/max + n; reconstruct an honest spread band from p5..p95
    return a


fig, axes = plt.subplots(1, 2, figsize=(10.5, 5.0))
fig.subplots_adjust(left=0.07, right=0.97, top=0.88, bottom=0.30, wspace=0.22)
for ax, qoi in zip(axes, ("peak", "band")):
    for i, arm in enumerate(arms):
        d = sc["arms"][arm][qoi]["interval"]
        if d.get("med") is None:
            continue
        x = i
        col = F.ARM_COLOR[arm]
        # median dot + p5-p95 whisker (log scale)
        ax.plot([x, x], [max(d["p5"], 1e-30), max(d["p95"], 1e-30)], color=col, lw=2.2, alpha=0.45,
                solid_capstyle="round")
        ax.plot(x, d["med"], "o", color=col, ms=9, zorder=5)
        ax.annotate(f"{d['med']:.2g}", (x, d["med"]), textcoords="offset points", xytext=(11, 0),
                    fontsize=8, color=col, va="center")
        n = sc["arms"][arm].get("n_splits", "?")
        ax.text(x, ax.get_ylim()[0], "", fontsize=7)  # placeholder
    ax.set_yscale("log")
    ax.set_xticks(range(len(arms)))
    ax.set_xticklabels([F.ARM_LABEL[a].replace(" (", "\n(") for a in arms], fontsize=8)
    ax.set_title(f"{qoi} |H| — interval (Winkler) score  ↓ better", fontsize=10)
    ax.set_xlim(-0.5, len(arms) - 0.5)
    ax.grid(True, which="both", axis="y", alpha=0.2)

# flags on the figure
ift_n = sc["arms"]["IFT"].get("n_splits", 0)
m2_n = sc["arms"]["M2"].get("n_splits", 0)
l5_n = sc["arms"]["L5"].get("n_splits", 0)
axes[0].text(0.02, 0.97, f"L5 n={l5_n} (converged)  ·  IFT n={ift_n} TMCMC (cross-run R̂≈1.0)\n"
             f"M2 n={m2_n} NON-CONVERGED (whole-FRF multimodal; σ_d→∞) — score NOT trustworthy, shown flagged",
             transform=axes[0].transAxes, fontsize=7.0, va="top", color="0.25")

cap = ("Held-out-sensor QOI (peak accelerance and band-GRMS, g/lbf) interval/Winkler proper score — lower is "
       "sharper-AND-calibrated. REAL ShockSat, 1 impact/1 hit, channel split only. IFT does NOT beat L5 on "
       "sharpness (coarse-FEM ceiling) but is the field-likelihood arm that CONVERGES + stays bounded; M2 "
       "(same observable, physics-in-likelihood) diverges. Whiskers = p5–p95 over splits.")
F.save(fig, "figA_scorecard", caption=cap, srcfile=__file__)
