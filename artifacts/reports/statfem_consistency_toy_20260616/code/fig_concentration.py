#!/usr/bin/env python3
"""figC1: concentration (C1). Posterior theta mean +/- ~95% (mean +/- 1.96 SD) vs the number of
replicate modal tests n, per construction, at eps=0 (control) and eps=0.3 (model-form error). The
teaching point: at eps=0 all three CONCENTRATE on theta_true; at eps=0.3 all three STILL concentrate
(SD shrinks) but onto a BIASED theta -- 'confidently wrong' under model error."""
import json
from pathlib import Path

import numpy as np

import viz
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
SS = json.load(open(WS / "out" / "sweep_summary.json"))
TT = SS["theta_true"]
cons = SS["constructions"]
ORDER = ["M-lik", "M-statfem", "M-ift"]

fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))
for c, eps in enumerate(["0.0", "0.3"]):
    ax = axes[c]
    ax.axhline(TT, color=viz.C_TRUTH, ls="--", lw=1.1)
    for cn in ORDER:
        cb = cons[cn]["concentration"].get(eps)
        if not cb:
            continue
        x = np.asarray(cb["n"], float)
        mean = np.asarray(cb["theta_mean"]); sd = np.asarray(cb["theta_sd"])
        ax.set_xscale("log")
        ax.fill_between(x, mean - 1.96 * sd, mean + 1.96 * sd, color=viz.CC[cn], alpha=0.15, lw=0)
        ax.plot(x, mean, "o-", color=viz.CC[cn], lw=1.7, ms=5)
    ax.set_xlabel("number of replicate tests  n")
    if c == 0:
        ax.set_ylabel("posterior theta  (mean +/- 1.96 SD)")
    ttl = ("eps = 0  (control): concentrate on theta_true"
           if eps == "0.0" else "eps = 0.3: concentrate on a BIASED theta (confidently wrong)")
    ax.set_title(ttl, fontsize=10)
    # the three lines nearly COINCIDE here -> a staggered colour legend (direct labels would collide)
    for i, cn in enumerate(ORDER):
        ax.text(0.035, 0.95 - 0.07 * i, cn, transform=ax.transAxes, color=viz.CC[cn],
                fontsize=8.6, va="top", ha="left", fontweight="bold")
    # final SD-shrink note (lower-right, away from the legend)
    txt = "\n".join(f"{cn}: SD {cons[cn]['concentration'][eps]['theta_sd'][0]:.3f}->"
                    f"{cons[cn]['concentration'][eps]['final_sd']:.3f}"
                    for cn in ORDER if cons[cn]['concentration'].get(eps))
    ax.text(0.97, 0.04, txt, transform=ax.transAxes, fontsize=7.4, va="bottom", ha="right", color="0.35")
axes[0].text(0.97, 0.96, f"dashed = theta_true ({TT})", transform=axes[0].transAxes,
             fontsize=7.6, color=viz.C_TRUTH, va="top", ha="right")
fig.tight_layout()
viz.save(fig, "figC1_concentration", extra="fixed finest discretization; n = independent replicate tests")
