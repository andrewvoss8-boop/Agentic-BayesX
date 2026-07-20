#!/usr/bin/env python3
"""Fig B: the beta thermometer. Left = learned inverse-temperature beta per split (dots) vs the forward-model
nominal beta* (where field-variance = sigma_meas^2): beta collapses ~250x BELOW nominal = the twin reporting
strong distrust of the coarse FEM, but BOUNDED (no sigma_d-style runaway). Right = cross-run R-hat per split
(TMCMC reproduces the multimodal posterior) and the beta 95% CI width (identifiability)."""
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

CODE = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE))
import figlib as F

WS = Path(__file__).resolve().parents[2]
cells = sorted((WS / "out" / "ift_tmcmc_cells").glob("ift_tmcmc_seed*.json"))
recs = [json.loads(p.read_text()) for p in cells]
seeds = [r["split_seed"] for r in recs]
bmed = [r["beta_posterior"]["beta_med"] for r in recs]
bstar = recs[0]["beta_posterior"]["beta_star"]
ciw = [r["beta_posterior"]["logbeta_ci_width"] for r in recs]
rhat = [r["convergence"]["max_rhat_crossrun"] for r in recs]

fig, (axL, axR) = plt.subplots(1, 2, figsize=(10.5, 4.8))
fig.subplots_adjust(left=0.075, right=0.975, top=0.85, bottom=0.26, wspace=0.30)

# Left: beta vs beta*
axL.axhline(bstar, color="0.5", ls="--", lw=1.2)
axL.text(0.03, 0.93, f"β*  ≈ {bstar:.0f}  (nominal: field variance = σ_meas²)", transform=axL.transAxes,
         color="0.4", fontsize=8, va="top", ha="left")
axL.plot(seeds, bmed, "o", color=F.C_IFT, ms=9)
for s, b in zip(seeds, bmed):
    axL.plot([s, s], [b, bstar], color=F.C_IFT, lw=0.8, alpha=0.3)
axL.set_yscale("log")
axL.set_xlabel("split seed")
axL.set_ylabel("posterior median β  (log)")
collapse = bstar / np.median(bmed) if bmed else float("nan")
axL.set_title(f"β collapses ≈{collapse:.0f}× below nominal\n= strong coarse-FEM distrust, but bounded", fontsize=9.5)
axL.grid(True, which="both", alpha=0.2)

# Right: cross-run R-hat + CI width
axR.axhline(1.2, color="0.6", ls=":", lw=1.0)
axR.text(0.03, 0.96, "TMCMC converged threshold (R̂ ≤ 1.2)", transform=axR.transAxes, color="0.45",
         fontsize=7.5, va="top", ha="left")
axR.plot(seeds, rhat, "s", color="#059669", ms=8, label="cross-run R̂")
for s, rh in zip(seeds, rhat):
    axR.annotate(f"{rh:.3f}", (s, rh), textcoords="offset points", xytext=(0, 7), fontsize=7,
                 ha="center", color="#059669")
axR.set_xlabel("split seed")
axR.set_ylabel("cross-run R̂ (4 independent TMCMC runs)")
axR.set_ylim(0.99, max(1.25, max(rhat) * 1.05 if rhat else 1.25))
axR.set_title("IFT-TMCMC reproduces the multimodal posterior", fontsize=9.5)
axR.grid(True, alpha=0.2)

cap = ("beta (FEM-physics trust thermometer) collapses ~250x below the forward-model nominal beta* but stays "
       "BOUNDED (unlike M2's sigma_d->inf); cross-run R-hat~=1.00 over 4 TMCMC runs = reproducible multimodal "
       "posterior. REAL ShockSat, 5 channel-splits. Full beta-identifiability detail in the packet.")
F.save(fig, "figB_beta", caption=cap, srcfile=__file__)
