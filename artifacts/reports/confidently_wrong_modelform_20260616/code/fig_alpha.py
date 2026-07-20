#!/usr/bin/env python3
"""Fig C: per-mode stiffness-scaling alpha_i posterior 95% intervals vs injected error delta, plus
the interval WIDTH (the overconfidence summary). Honest, nuanced finding:
  - A1 naive: alpha intervals NEVER widen (width flat ~0.002) -> overconfident as delta grows.
  - A2 iid:   alpha intervals widen 6-7x honestly (uncertainty shows up in the parameter).
  - A3 corr:  alpha stays tight but the structured error is absorbed into its correlated discrepancy
              term, so held-out COVERAGE still holds (Fig A) by a different mechanism.
Truth alpha line shown. The Hao-Bilionis Fig 4 analog at the parameter level.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

import viz

OUT = Path(__file__).resolve().parent.parent / "out"
S = json.load(open(OUT / "sweep_summary.json"))
ATRUTH = S["meta"]["alpha_truth_main"]
nm = len(ATRUTH)
freqs_lbl = [18, 95, 280]

ARMS = [("A1", viz.C_NAIVE, "A1 naive"),
        ("A2", viz.C_IID, "A2 disc-aware iid"),
        ("A3", viz.C_CORR, "A3 disc-aware corr")]

fig = plt.figure(figsize=(12.4, 6.4))
gs = fig.add_gridspec(2, nm, height_ratios=[1.0, 0.85], hspace=0.42, wspace=0.1)

# ---- top row: per-mode alpha intervals (zoomed near truth) ----
axs = [fig.add_subplot(gs[0, i]) for i in range(nm)]
for i, ax in enumerate(axs):
    for arm, col, lab in ARMS:
        rows = S["correlated"][arm]
        x = [r["level"] for r in rows]
        lo = [r["alpha"][i]["lo"] for r in rows]
        hi = [r["alpha"][i]["hi"] for r in rows]
        med = [r["alpha"][i]["med"] for r in rows]
        ax.fill_between(x, lo, hi, color=col, alpha=0.22, zorder=2)
        ax.plot(x, med, "-", color=col, lw=1.6, zorder=3)
    ax.axhline(ATRUTH[i], color=viz.C_TRUTH, ls="--", lw=1.2)
    ax.set_ylim(0.934, 0.966)
    ax.set_title(f"mode {i+1}  (~{freqs_lbl[i]} Hz)", fontsize=9.3)
    ax.set_xlabel("injected delta")
    ax.set_xlim(-0.01, x[-1] + 0.02)
    viz.style(ax, logx=False)
    if i > 0:
        ax.tick_params(labelleft=False)
axs[0].set_ylabel("alpha_i  (95% interval)")
axs[0].text(0.02, ATRUTH[0] + 0.007, f"truth alpha = {ATRUTH[0]:.2f}", fontsize=7.6, color="0.2")
handles = [Line2D([0], [0], color=c, lw=6, alpha=0.55, label=l) for _, c, l in ARMS]
axs[1].legend(handles=handles, loc="lower center", fontsize=7.4, handlelength=1.3, ncol=1)

# ---- bottom row: alpha interval WIDTH vs delta (overconfidence, log-y) ----
axw = [fig.add_subplot(gs[1, i]) for i in range(nm)]
for i, ax in enumerate(axw):
    for arm, col, lab in ARMS:
        rows = S["correlated"][arm]
        x = [r["level"] for r in rows]
        w = [r["alpha"][i]["hi"] - r["alpha"][i]["lo"] for r in rows]
        ax.plot(x, w, "-o", color=col, lw=1.8, ms=4)
    ax.set_yscale("log")
    ax.set_xlabel("injected delta")
    ax.set_xlim(-0.01, x[-1] + 0.02)
    viz.style(ax, logx=False)
    if i > 0:
        ax.tick_params(labelleft=False)
axw[0].set_ylabel("alpha 95% width\n(log scale)")
axw[1].annotate("A2 widens (honest)", (0.35, 0.012), fontsize=7.6, color=viz.C_IID)
axw[1].annotate("A1 naive flat (overconfident)", (0.05, 0.0016), fontsize=7.6, color=viz.C_NAIVE)

fig.suptitle("Naive alpha intervals never widen (overconfident); iid widens honestly; correlated "
             "stays tight but absorbs error into its discrepancy term", fontsize=10.0, y=0.99)
viz.save(fig, "figC_alpha_intervals", extra="Fig C | per-mode alpha + width")
print("figC done")
