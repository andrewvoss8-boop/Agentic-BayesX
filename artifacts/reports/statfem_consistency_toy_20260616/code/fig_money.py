#!/usr/bin/env python3
"""figA (the MONEY figure): posterior theta mean +/- 95% CI vs the refinement knob, per construction,
with the theta_true line. This adjudicates Bilionis's charge: FLAT vs the knob = discretization-invariant
(good); SLOPED = drift (the indicted behaviour). Rows = model-form error eps (0 control, 0.3 error);
columns = the four knob sweeps. The headline contrast is the FIRST column (M-lik vs the FICTITIOUS
residual noise sigma_r) drifting while the genuine mesh/discretization columns stay flat."""
import json
from pathlib import Path

import numpy as np

import viz
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
SS = json.load(open(WS / "out" / "sweep_summary.json"))
TT = SS["theta_true"]
cons = SS["constructions"]

# (construction, knob, column title, "fictitious" flag, colour)
PANELS = [
    ("M-lik", "sigma_r", "M-lik  vs  residual noise sigma_r", True, viz.C_LIK),
    ("M-lik", "N_c", "M-lik  vs  mesh  N_c", False, viz.C_LIK),
    ("M-ift", "N_c", "M-ift  vs  mesh  N_c", False, viz.C_IFT),
    ("M-statfem", "h", "M-statfem  vs  mesh  n_el", False, viz.C_STATFEM),
]
EPS = ["0.0", "0.3"]
EPS_LBL = {"0.0": "eps = 0  (no model-form error: a correct method MUST stay on theta_true)",
           "0.3": "eps = 0.3  (omitted Winkler foundation = model-form error)"}

fig, axes = plt.subplots(2, 4, figsize=(15.5, 7.6))

for r, eps in enumerate(EPS):
    # shared y-limits per row
    vals = []
    for cn, kn, *_ in PANELS:
        eb = cons[cn]["knobs"][kn]["eps"].get(eps)
        if eb:
            vals += eb["theta_lo"] + eb["theta_hi"] + [TT]
    ylo, yhi = min(vals), max(vals)
    pad = 0.12 * (yhi - ylo + 1e-9)
    for c, (cn, kn, title, fict, col) in enumerate(PANELS):
        ax = axes[r, c]
        eb = cons[cn]["knobs"][kn]["eps"].get(eps)
        ax.axhline(TT, color=viz.C_TRUTH, ls="--", lw=1.1)
        if eb is None:
            ax.text(0.5, 0.5, "no data", transform=ax.transAxes, ha="center"); continue
        x = np.asarray(eb["levels"], float)
        ax.set_xscale("log")
        ax.fill_between(x, eb["theta_lo"], eb["theta_hi"], color=col, alpha=0.18, lw=0)
        ax.plot(x, eb["theta_mean"], "o-", color=col, lw=1.8, ms=5)
        ax.set_ylim(ylo - pad, yhi + pad)
        # annotate C2 spread + convergence flag
        spread = eb["c2_spread"]
        tag = "DRIFT (knob carries NO info)" if fict else "flat = invariant"
        ax.text(0.04, 0.05, f"C2 spread of mean = {spread:.3f}\n{tag}", transform=ax.transAxes,
                fontsize=8, va="bottom", ha="left",
                color=(viz.C_LIK if (fict and spread > 0.02) else "0.35"))
        if not eb["all_converged"]:
            ax.text(0.04, 0.95, f"NOT-YET-CONVERGED (R-hat {eb['worst_rhat']:.2f})", transform=ax.transAxes,
                    fontsize=7.5, color=viz.C_LIK, va="top")
        if r == 0:
            ax.set_title(title, fontsize=10)
        if c == 0:
            ax.set_ylabel(f"posterior theta (mean, 95% CI)\n", fontsize=9)
        ax.set_xlabel({"sigma_r": "residual noise sigma_r (fictitious)",
                       "N_c": "collocation points N_c", "h": "FE elements n_el"}[kn], fontsize=8.5)
    # row label (theta_true note) on the far right of row
    axes[r, 3].text(1.02, 0.5, EPS_LBL[eps], transform=axes[r, 3].transAxes, rotation=90,
                    va="center", ha="left", fontsize=8.2, color="0.4")

# one shared note: dashed line = theta_true
axes[0, 0].text(0.04, 0.93, f"dashed = theta_true ({TT})", transform=axes[0, 0].transAxes,
                fontsize=7.8, color=viz.C_TRUTH, va="top")
fig.suptitle("Consistency money figure: posterior theta vs each refinement knob, per construction "
             "(flat = discretization-invariant; sloped = drift)", fontsize=11.5, y=0.995)
fig.tight_layout(rect=(0, 0, 0.985, 0.97))
viz.save(fig, "figA_money_theta_vs_knob",
         extra="n=8 replicate tests per cell; 95% CI from 4-chain NUTS")
