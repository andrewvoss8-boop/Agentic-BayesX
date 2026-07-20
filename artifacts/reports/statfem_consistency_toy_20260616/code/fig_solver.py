#!/usr/bin/env python3
"""figV: solver-validation gate. Forced drive-point-response error vs refinement for the FD operator
(M-lik/M-ift) and the consistent-mass FE (M-statfem), with a 2nd-order (h^2) reference slope. The two
solvers converge at the same 2nd-order rate to the ANALYTIC truth (their curves nearly coincide), so any
posterior drift is the METHOD not under-resolution."""
import json
from pathlib import Path

import numpy as np

import viz
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
sv = json.load(open(WS / "out" / "solver_validation.json"))

fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.3))

# panel A: forced-response convergence (FD filled circles, FE open squares)
ax = axes[0]
hfd = 1.0 / np.asarray(sv["fd"]["levels"], float)
hfe = 1.0 / np.asarray(sv["fe"]["levels"], float)
ax.loglog(hfd, sv["fd"]["max_rel_err"], "o-", color=viz.C_LIK, lw=1.6, ms=6, label="FD")
ax.loglog(hfe, sv["fe"]["max_rel_err"], "s--", color=viz.C_STATFEM, lw=1.2, ms=5,
          mfc="none", mew=1.3)
ref = sv["fd"]["max_rel_err"][0] * (hfd / hfd[0]) ** 2
ax.loglog(hfd, ref, "-", color=viz.C_REF, lw=1.0)
ax.axhline(1e-3, color="#cccccc", lw=0.8, ls=":")
ax.text(0.96, 0.94, f"FD (M-lik/M-ift) ● and FE (M-statfem) ▫\ncoincide; rate ~ {sv['fd']['rate_est']:.2f}",
        transform=ax.transAxes, fontsize=8, ha="right", va="top", color="0.25")
ax.text(0.04, 0.10, "slope 2 (h$^2$)", transform=ax.transAxes, fontsize=7.6, color=viz.C_REF, va="bottom")
ax.text(0.96, 0.06, "checker tol 1e-3", transform=ax.transAxes, fontsize=7, color="#999999",
        ha="right", va="bottom")
ax.set_xlabel("mesh size  h = L / N   (finer -> left)")
ax.set_ylabel("max relative error in drive-point response")
ax.set_title("Forced-response convergence to analytic truth", fontsize=10.5)

# panel B: eigenfrequency convergence (context)
ax = axes[1]
hfd = 1.0 / np.asarray(sv["fd_eigfreq"]["levels"], float)
hfe = 1.0 / np.asarray(sv["fe_eigfreq"]["levels"], float)
ax.loglog(hfd, sv["fd_eigfreq"]["max_rel_err"], "o-", color=viz.C_LIK, lw=1.5, ms=5)
ax.loglog(hfe, sv["fe_eigfreq"]["max_rel_err"], "s--", color=viz.C_STATFEM, lw=1.1, ms=4,
          mfc="none", mew=1.3)
ax.text(0.96, 0.10, f"FD ● and FE ▫ eigenfreq (modes 1-6)\ncoincide; rate ~ {sv['fd_eigfreq']['rate_est']:.2f}",
        transform=ax.transAxes, fontsize=8, ha="right", va="bottom", color="0.25")
ax.set_xlabel("mesh size  h = L / N   (finer -> left)")
ax.set_ylabel("max relative error in modal frequencies 1-6")
ax.set_title("Eigenfrequency convergence (context)", fontsize=10.5)

fig.tight_layout()
viz.save(fig, "figV_solver_convergence",
         extra=f"finest FD/FE response err {sv['fd']['max_rel_err'][-1]:.1e}/{sv['fe']['max_rel_err'][-1]:.1e} << noise floor")
