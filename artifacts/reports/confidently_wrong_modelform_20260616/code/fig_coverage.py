#!/usr/bin/env python3
"""Fig A (money): held-out predictive coverage vs injected model-form error delta.
Small multiples by error class. A1 (naive, no discrepancy) COLLAPSES below nominal as delta grows
while staying converged + confident; A2/A3 (discrepancy-aware) hold near nominal. This is the
Hao-Bilionis Fig 4 analog and our project's central 'confidently wrong vs honestly uncertain' result.

Coverage shown = predictive coverage of the held-out NOISY masked observation at nominal 95%
(the conservative/standard calibration check). The stricter latent-truth coverage is even more
extreme for A1 and is reported in the packet.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import viz

OUT = Path(__file__).resolve().parent.parent / "out"
S = json.load(open(OUT / "sweep_summary.json"))
NOM = S["meta"]["nominal"]

ARMS = [("A1", viz.C_NAIVE, "A1 naive\n(no discrepancy)"),
        ("A2", viz.C_IID, "A2 disc-aware\niid"),
        ("A3", viz.C_CORR, "A3 disc-aware\ncorrelated")]

fig, axs = plt.subplots(1, 2, figsize=(11.2, 4.8))

panels = [("correlated", "injected discrepancy std  delta  (high-freq)", axs[0],
           "Error class 1: smooth correlated model-form error"),
          ("missingmode", "missing-mode severity (hidden 280 Hz DOF)", axs[1],
           "Error class 2: missing mode / hidden DOF")]

# the three coverage curves crowd the top band (A2/A3 near-coincident), so a frameless legend in
# the empty lower-left corner is cleaner than colliding direct labels (Tufte: legend when needed).
from matplotlib.lines import Line2D
handles = [Line2D([0], [0], color=c, marker="o", lw=2, ms=5, label=l.replace("\n", " ")) for _, c, l in ARMS]

for cls, xlab, ax, title in panels:
    for arm, col, lab in ARMS:
        rows = S[cls][arm]
        if not rows:
            continue
        x = [r["level"] for r in rows]
        y = [r["cov_noisy"] for r in rows]
        nonconv = [not r["converged"] for r in rows]
        ax.plot(x, y, "-o", color=col, lw=2.0, ms=5, zorder=3)
        for xi, yi, nc in zip(x, y, nonconv):
            if nc:
                ax.plot(xi, yi, "o", mfc="white", mec=col, ms=10, zorder=4)  # should be none
    ax.axhline(NOM, color=viz.C_NOMINAL, ls="--", lw=1.2)
    ax.text(0.99, NOM + 0.015, "nominal 95%", color="0.45", fontsize=8, ha="right",
            transform=ax.get_yaxis_transform())
    ax.set_xlabel(xlab)
    ax.set_ylim(-0.03, 1.08)
    ax.set_xlim(left=-0.01)
    ax.set_title(title, fontsize=9.5)
    viz.style(ax, logx=False)
    ax.legend(handles=handles, loc="lower left", fontsize=7.6, handlelength=1.5)

axs[0].set_ylabel("held-out predictive coverage\n(masked Ch3/Ch4, nominal 0.95)")
fig.suptitle("Held-out coverage collapses for the naive fit but holds for the discrepancy-aware fit "
             "(all arms NUTS-converged)", fontsize=10.5, y=0.99)
fig.subplots_adjust(right=0.86, wspace=0.18)
viz.save(fig, "figA_coverage_vs_delta", extra="Fig A money | held-out NOISY coverage")
print("figA done")
