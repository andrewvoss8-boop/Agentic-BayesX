#!/usr/bin/env python3
"""Fig B (thermometer): learned discrepancy scale sigma_d vs injected model-form error delta.
A2/A3 sigma_d rises monotonically with delta (a thermometer for unmodeled physics); A1 has no
such mechanism (sigma_d == 0, flat). The Hao-Bilionis Fig 5 analog (their learned beta).

sigma_d is an EFFECTIVE band-average output-side std; it tracks the band-average of the injected
(heteroscedastic) std, shown as the reference band between the low/high injected std.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import viz

OUT = Path(__file__).resolve().parent.parent / "out"
S = json.load(open(OUT / "sweep_summary.json"))

rowsA2 = S["correlated"]["A2"]
rowsA3 = S["correlated"]["A3"]
x = [r["level"] for r in rowsA2]
inj_avg = [r["injected_band_avg_std"] for r in rowsA2]
inj_hi = [r["injected_hi_std"] for r in rowsA2]

fig, ax = plt.subplots(figsize=(7.4, 5.0))

# injected-error reference band (absolute): between band-average and high-freq std
ax.fill_between(x, inj_avg, inj_hi, color="0.82", alpha=0.7, zorder=0)
ax.plot(x, inj_avg, color="0.55", lw=1.1, ls=":", zorder=1)
ax.annotate("injected error band\n(band-avg .. high-freq std)", (x[-1], inj_hi[-1]),
            textcoords="offset points", xytext=(-2, 6), fontsize=8, color="0.4", ha="right")

for rows, col, lab in [(rowsA2, viz.C_IID, "A2 disc-aware iid"),
                       (rowsA3, viz.C_CORR, "A3 disc-aware correlated")]:
    med = [r["sigma_d_med"] for r in rows]
    lo = [r["sigma_d_lo"] for r in rows]
    hi = [r["sigma_d_hi"] for r in rows]
    ax.fill_between(x, lo, hi, color=col, alpha=0.15, zorder=2)
    ax.plot(x, med, "-o", color=col, lw=2.2, ms=5, zorder=3)
    ax.annotate(lab, (x[-1], med[-1]), textcoords="offset points", xytext=(6, 0),
                fontsize=8.5, color=col, va="center", fontweight="bold")

ax.axhline(0.0, color=viz.C_NAIVE, ls="--", lw=1.6)
ax.annotate("A1 naive: sigma_d = 0 (NO model-error mechanism)", (x[1], 0.0),
            textcoords="offset points", xytext=(4, 6), fontsize=8.5, color=viz.C_NAIVE)

ax.set_xlabel("injected discrepancy std  delta  (high-freq)")
ax.set_ylabel("learned discrepancy scale  sigma_d  (posterior median, 95% CI)")
ax.set_title("sigma_d is a thermometer for model-form error: it rises with delta for the disc-aware\n"
             "fits and is absent (0) for the naive fit", fontsize=9.8)
ax.set_xlim(-0.01, x[-1] + 0.06)
ax.set_ylim(bottom=-0.02)
viz.style(ax, logx=False)
fig.subplots_adjust(right=0.80)
viz.save(fig, "figB_sigmad_thermometer", extra="Fig B thermometer")
print("figB done")
