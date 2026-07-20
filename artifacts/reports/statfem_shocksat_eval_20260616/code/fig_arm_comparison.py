#!/usr/bin/env python3
"""figB: discrepancy-structure comparison -- naive vs StatFEM-iid vs Schneider vs orthogonal.

Four small multiples (bars over arms): (a) mean held-out QOI coverage (vs nominal 0.95), (b) mean predictive
band width [dB] (sharpness; lower = tighter), (c) learned sigma_d (model-form-error thermometer),
(d) mean |theta bias| on the biased IDENTIFIABLE groups (over-absorption / Plumlee plug-in bias).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import viz

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
ARMS = ["M0", "M1", "M2", "M3"]

A = json.load(open(OUT / "arm_comparison.json"))["arms"]
colors = [viz.ARM_COLOR[a] for a in ARMS]
x = np.arange(len(ARMS))

fig, axs = plt.subplots(1, 4, figsize=(13, 3.8))


def bars(ax, vals, title, ylab, ref=None, ref_lab=None, pct=False):
    vv = [(v if v is not None else 0.0) for v in vals]
    ax.bar(x, vv, color=colors, width=0.66)
    for i, v in enumerate(vals):
        if v is not None:
            ax.annotate(f"{v*100:.0f}%" if pct else f"{v:.2f}", (i, vv[i]), xytext=(0, 2),
                        textcoords="offset points", ha="center", fontsize=8)
    if ref is not None:
        ax.axhline(ref, color=viz.C_NOMINAL, ls="--", lw=1.0)
        ax.annotate(ref_lab, (-0.4, ref), xytext=(0, 3), textcoords="offset points", fontsize=7, color="0.45")
    ax.set_xticks(x); ax.set_xticklabels(ARMS, fontsize=8.5)
    ax.set_title(title, fontsize=9.5); ax.set_ylabel(ylab, fontsize=8.5)


bars(axs[0], [A[a]["mean_combined_coverage"] for a in ARMS], "Held-out QOI coverage", "coverage",
     ref=0.95, ref_lab="0.95", pct=True)
axs[0].set_ylim(0, 1.05)
bars(axs[1], [A[a]["mean_band_width_db"] for a in ARMS], "Predictive band width", "dB (lower = tighter)")
bars(axs[2], [A[a]["mean_sigma_d"] for a in ARMS], "Learned sigma_d", "log-mag (0 = no error mech.)")
bars(axs[3], [A[a]["mean_theta_bias_identified"] for a in ARMS],
     "theta bias (identifiable)", "|median/truth-1|", pct=True)

fig.suptitle("Naive vs StatFEM-iid vs Schneider vs orthogonal (means over 5 combos)", fontsize=11, y=1.02)
viz.save(fig, "figB_arm_comparison", extra="bars = means over the 5 bias combos")
print("figB done")
