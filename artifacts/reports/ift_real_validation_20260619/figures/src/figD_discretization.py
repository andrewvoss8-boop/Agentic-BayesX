#!/usr/bin/env python3
"""Fig D: discretization invariance (§8). The IFT selling point: the theta/QOI/beta posterior should NOT depend
on the analysis-grid density. We re-fit IFT-TMCMC at frequency-grid densities (full, 1/2, 1/4) and plot the
learned beta and the held-out peak-QOI (normalized to the full-grid value). Flat ~= invariant."""
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

CODE = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE))
import figlib as F

WS = Path(__file__).resolve().parents[2]
rec = json.loads((WS / "out" / "discretization.json").read_text())
g = rec["grids"]
nf = np.array([r["n_freq"] for r in g])
beta = np.array([r["ift_beta_med"] for r in g])
qoi = np.array([r["ift_peak_qoi_med"] for r in g])
order = np.argsort(nf)
nf, beta, qoi = nf[order], beta[order], qoi[order]
beta_n = beta / beta[-1]; qoi_n = qoi / qoi[-1]   # normalize to the finest (full) grid

fig, ax = plt.subplots(figsize=(9.2, 5.0))
fig.subplots_adjust(left=0.10, right=0.96, top=0.89, bottom=0.30)

ax.axhline(1.0, color="0.6", ls="--", lw=1.0)
ax.plot(nf, beta_n, "o-", color=F.C_IFT, lw=1.8, ms=9, label="β")
ax.plot(nf, qoi_n, "s-", color="#0891b2", lw=1.8, ms=9, label="peak QOI")
for x, y in zip(nf, beta_n):
    ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(0, 9), fontsize=8, ha="center", color=F.C_IFT)
for x, y in zip(nf, qoi_n):
    ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(0, -14), fontsize=8, ha="center", color="#0891b2")

ax.set_xlabel("number of frequency lines in the likelihood (analysis-grid density)")
ax.set_ylabel("IFT posterior median, normalized to full grid")
ax.text(0.015, 0.96, "β (learned trust)", transform=ax.transAxes, color=F.C_IFT, fontsize=9.5, va="top")
ax.text(0.015, 0.90, "held-out peak QOI", transform=ax.transAxes, color="#0891b2", fontsize=9.5, va="top")
bspread = rec["ift_beta_rel_spread"]; qspread = rec["ift_peak_qoi_rel_spread"]
ax.set_title(f"IFT posterior ≈ invariant to grid density (β spread {bspread:.0%}, QOI spread {qspread:.0%})",
             fontsize=10.5)
ax.grid(True, alpha=0.2)

cap = ("IFT-TMCMC re-fit at 3 frequency-grid densities (REAL ShockSat, split seed " + str(rec["seed"]) + "). "
       "Learned β and held-out peak-QOI are ~flat across grids = discretization-invariant (the IFT promise), "
       "echoing the consistency-toy C2 result on real data. Values normalized to the full grid.")
F.save(fig, "figD_discretization", caption=cap, srcfile=__file__)
