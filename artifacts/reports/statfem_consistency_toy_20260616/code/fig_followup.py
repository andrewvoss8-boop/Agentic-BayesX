#!/usr/bin/env python3
"""figF (follow-up E1): does the discrepancy mechanism CATCH a spatially-structured model error?
A localized stiffness defect (NOT theta-like) is swept in depth. Panel A: posterior theta vs depth per
construction (all bias, but compare). Panel B: held-out FRF coverage vs depth. Panel C: statFEM's learned
discrepancy sigma_d GROWS with the spatial defect (it absorbs spatial model error) -- unlike the main
study's theta-like Winkler foundation where sigma_d stayed ~0.004 (flat reference line). This is the
qualitative DIFFERENCE between statFEM's additive spatial discrepancy and the residual-weight knobs of
M-lik/M-ift."""
import json
from pathlib import Path

import numpy as np

import viz
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
S = json.load(open(WS / "followup" / "defect_summary.json"))
TT = S["theta_true"]
cells = S["cells"]
depths = np.asarray(S["depths"], float)
ORDER = ["M-lik", "M-statfem", "M-ift"]
# foundation-case statFEM sigma_d baseline (theta-like error) for contrast
FOUND_SIGD = json.load(open(WS / "out" / "cell_Mstatfem_h_64_eps0.3_n8.json")).get("sigma_d_med", 0.004)

fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.5))

# Panel A: theta vs depth
ax = axes[0]
ax.axhline(TT, color=viz.C_TRUTH, ls="--", lw=1.1)
for cn in ORDER:
    d = cells[cn]
    mean = np.array([c["theta"]["mean"] for c in d])
    lo = np.array([c["theta"]["lo"] for c in d]); hi = np.array([c["theta"]["hi"] for c in d])
    ax.fill_between(depths, lo, hi, color=viz.CC[cn], alpha=0.15, lw=0)
    ax.plot(depths, mean, "o-", color=viz.CC[cn], lw=1.7, ms=5)
for i, cn in enumerate(ORDER):
    ax.text(0.035, 0.95 - 0.07 * i, cn, transform=ax.transAxes, color=viz.CC[cn], fontsize=8.6,
            va="top", fontweight="bold")
ax.text(0.97, 0.05, f"dashed = theta_true ({TT})", transform=ax.transAxes, color=viz.C_TRUTH,
        fontsize=7.6, ha="right", va="bottom")
ax.set_xlabel("localized stiffness-defect depth"); ax.set_ylabel("posterior theta (mean, 95% CI)")
ax.set_title("theta vs defect depth", fontsize=10.5)

# Panel B: held-out coverage vs depth
ax = axes[1]
ax.axhline(0.95, color=viz.C_TRUTH, ls="--", lw=1.0)
for cn in ORDER:
    cov = np.array([c["coverage_heldout"] for c in cells[cn]])
    ax.plot(depths, cov, "o-", color=viz.CC[cn], lw=1.7, ms=5)
ax.text(0.97, 0.06, "dashed = nominal 0.95", transform=ax.transAxes, color=viz.C_TRUTH,
        fontsize=7.6, ha="right", va="bottom")
ax.set_ylim(0, 1.08)
ax.set_xlabel("localized stiffness-defect depth"); ax.set_ylabel("held-out FRF 95% coverage")
ax.set_title("held-out prediction vs defect depth", fontsize=10.5)

# Panel C: statFEM sigma_d grows with the SPATIAL defect (vs flat for the theta-like foundation)
ax = axes[2]
sd = cells["M-statfem"]
med = np.array([c["sigma_d"]["med"] for c in sd])
lo = np.array([c["sigma_d"]["lo"] for c in sd]); hi = np.array([c["sigma_d"]["hi"] for c in sd])
ax.fill_between(depths, lo, hi, color=viz.C_STATFEM, alpha=0.18, lw=0)
ax.plot(depths, med, "o-", color=viz.C_STATFEM, lw=1.8, ms=5)
ax.axhline(FOUND_SIGD, color="0.45", ls=":", lw=1.2)
ax.text(0.035, 0.92, "spatial defect:\nstatFEM sigma_d GROWS\n(absorbs spatial model error)",
        transform=ax.transAxes, color=viz.C_STATFEM, fontsize=8.0, va="top", fontweight="bold")
ax.text(0.97, 0.10, f"theta-like Winkler foundation:\nsigma_d ~ {FOUND_SIGD:.3f} (flat, does NOT flag)",
        transform=ax.transAxes, color="0.4", fontsize=7.8, ha="right", va="bottom")
ax.set_xlabel("localized stiffness-defect depth"); ax.set_ylabel("statFEM learned discrepancy sigma_d")
ax.set_title("statFEM discrepancy CATCHES spatial error", fontsize=10.5)

fig.tight_layout()
viz.save(fig, "figF_followup_defect_class",
         extra="follow-up E1: localized-defect error class; truth = high-res reference solve (NOT analytic); n=8")
