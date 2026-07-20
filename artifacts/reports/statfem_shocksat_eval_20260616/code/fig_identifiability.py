#!/usr/bin/env python3
"""figE: identifiability gate -- modal strain energy + FIM eigen-view + finite-perturbation.

Left: per-group mean & peak modal strain-energy fraction (identifiable groups dark; >5% mean threshold).
Middle: FRF-FIM eigenvalue spectrum vs prior precision (with the linearization-inflation caveat).
Right: finite +20% perturbation -> held-out band-QOI shift (in-path vs out-of-path mechanism check).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import viz

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
idf = json.load(open(OUT / "identifiability.json"))
se = idf["strain_energy"]
GN = [r["group"] for r in se]
informed = set(idf["informed_groups_strain_energy"])

fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.4))

# --- strain energy ---
y = np.arange(len(GN))
mean_se = [r["mean_se_pct"] for r in se]
peak_se = [r["peak_se_pct"] for r in se]
cols = ["#111111" if g in informed else "#b9b9b9" for g in GN]
axs[0].barh(y, mean_se, color=cols, height=0.6)
for i, r in enumerate(se):
    axs[0].plot(r["peak_se_pct"], i, "|", color=cols[i], ms=12, mew=2)
axs[0].axvline(5.0, color=viz.C_NOMINAL, ls="--", lw=1.0)
axs[0].annotate("5% floor", (5, len(GN) - 0.5), fontsize=7, color="0.45")
axs[0].set_yticks(y); axs[0].set_yticklabels(GN, fontsize=8)
axs[0].set_xlabel("modal strain-energy fraction [%]")
axs[0].set_title("Strain energy (bar=mean, | =peak)\ndark=identifiable", fontsize=9.5)

# --- FIM spectrum ---
ev = [c["eigval"] for c in idf["fim"]["eig_combinations"]]
pp = idf["fim"]["prior_precision"]
xk = np.arange(len(ev))
axs[1].semilogy(xk, ev, "o-", color="#2563eb", ms=5)
axs[1].axhline(pp, color=viz.C_NOMINAL, ls="--", lw=1.0)
axs[1].annotate(f"prior precision {pp:.0f}", (0, pp), xytext=(0, 4), textcoords="offset points",
                fontsize=7.5, color="0.45")
axs[1].set_xlabel("FIM eigen-combination (sorted)")
axs[1].set_ylabel("FIM eigenvalue (log)")
axs[1].set_title(f"FRF-FIM eigen-view ({idf['fim']['n_above_prior']}/9 above prior)\n"
                 "LINEARIZED -- inflated near resonances", fontsize=9)

# --- finite perturbation ---
fp = idf["finite_perturbation"]
mx = [r["max_band_qoi_rel_shift"] * 100 for r in fp]
cols2 = ["#111111" if r["group"] in informed else "#b9b9b9" for r in fp]
axs[2].barh(y, mx, color=cols2, height=0.6)
axs[2].set_yticks(y); axs[2].set_yticklabels(GN, fontsize=8)
axs[2].set_xlabel("max held-out band-QOI shift at +20% [%]")
axs[2].set_title("Finite perturbation\n(in-path vs out-of-path)", fontsize=9.5)

fig.suptitle("Identifiability gate: only ~4/9 groups store real modal strain energy (the modal-twin 4/9 "
             "finding); FIM linearization is optimistic", fontsize=10.5, y=1.04)
viz.save(fig, "figE_identifiability", extra=f"informed (strain energy) = {sorted(informed)}")
print("figE done")
