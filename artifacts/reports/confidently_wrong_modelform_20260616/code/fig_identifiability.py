#!/usr/bin/env python3
"""Fig E (identifiability gate, required for the E-LIMIT per-parameter claim).
Left: modal participation |Phi_{c,i} * part_i| per channel x mode (the parameter->observable
sensitivity / strain-energy analog) -- the local mode 4 (760 Hz) is ~invisible to the observed
channels Ch1/Ch2 and lives at the masked Ch3/Ch4. Right: the Fisher-information eigenspectrum of
the OBSERVED-channel sensitivity at the REALIZED discrepancy floor -- the alpha_4 combination is the
WEAKEST (only ~4x the prior precision, vs >1000x for modes 1-3), so the masked virtual target (which
carries the coherent bias) dominates alpha_4. Annotated: a peak-frequency shift is
ALGEBRAICALLY a stiffness scaling (cosine of the two sensitivity columns ~ 1), so the coherent bias
and alpha_4 are confounded. This certifies the E-LIMIT parameter miss is under-identification, not a
sampler bug; the pre-test lever is a sensor that sees the local mode.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import core
import viz

OUT = Path(__file__).resolve().parent.parent / "out"
modes = core.local_mode_modes()
freqs = core.freq_grid(160)
nm, nc = modes.nm, modes.nc

# realized discrepancy floor (from the E-LIMIT control arm if available, else the injected hi std)
sd = 0.30
lim = OUT / "limit_summary.json"
if lim.exists():
    L = json.load(open(lim))
    sd = float(L["arms"]["bayes_correlated_unbiased_control"]["sigma_d"][1])
SIGMA_MEAS = 0.05
floor_var = SIGMA_MEAS ** 2 + sd ** 2

# ---- participation matrix (channels x modes) ----
P = np.abs(modes.Phi * modes.part[None, :])  # (nc, nm)
Pn = P / P.max()

# ---- sensitivity columns: dlog|H|/dlog(alpha_i) via finite difference ----
a0 = np.ones(nm); b0 = np.ones(nm); g0 = core.GAMMA0
H0 = core.frf_np(freqs, a0, b0, g0, modes)
lm0 = np.log(np.abs(H0))
eps = 1e-4
Jcols = []  # each (nf*nc_used,) for observed channels
obs = core.OBSERVED
for i in range(nm):
    a = a0.copy(); a[i] *= (1 + eps)
    lm = np.log(np.abs(core.frf_np(freqs, a, b0, g0, modes)))
    d = (lm - lm0) / np.log(1 + eps)  # dlog|H|/dlog alpha_i  (nf,nc)
    Jcols.append(d[:, obs].ravel())
Jobs = np.array(Jcols).T  # (n_obs_lines, nm)
FIM = (Jobs.T @ Jobs) / floor_var
evals, evecs = np.linalg.eigh(FIM)
evals = evals[::-1]; evecs = evecs[:, ::-1]
prior_prec = 1.0 / (0.15 ** 2)  # log-alpha prior precision

# ---- peak-shift == stiffness colinearity (mode 4) on all channels ----
a = a0.copy(); a[3] *= (1 + eps)
d_alpha4 = (np.log(np.abs(core.frf_np(freqs, a, b0, g0, modes))) - lm0) / np.log(1 + eps)
# peak shift of mode 4 by eps: scale ONLY its natural frequency (participation is f-independent)
m2 = core.local_mode_modes()
f_shift = m2.f.copy(); f_shift[3] *= (1 + eps)
m2 = core.Modes(f=f_shift, zeta=m2.zeta.copy(), Phi=m2.Phi.copy(), Binput=m2.Binput.copy())
d_shift = (np.log(np.abs(core.frf_np(freqs, a0, b0, g0, m2))) - lm0) / eps
va = d_alpha4.ravel(); vs = d_shift.ravel()
cos = float(abs(va @ vs) / (np.linalg.norm(va) * np.linalg.norm(vs) + 1e-12))

fig, axs = plt.subplots(1, 2, figsize=(12.0, 4.8))

# Panel A: participation heatmap
ax = axs[0]
im = ax.imshow(Pn, cmap="viridis", aspect="auto", vmin=0, vmax=1)
ax.set_xticks(range(nm)); ax.set_xticklabels([f"mode {i+1}\n{modes.f[i]:.0f}Hz" for i in range(nm)], fontsize=8)
ax.set_yticks(range(nc)); ax.set_yticklabels([f"Ch{c+1}" + (" (obs)" if c in obs else " (masked)") for c in range(nc)], fontsize=8)
for c in range(nc):
    for i in range(nm):
        ax.text(i, c, f"{Pn[c,i]:.2f}", ha="center", va="center",
                color="white" if Pn[c, i] < 0.55 else "black", fontsize=8)
ax.set_title("Modal participation |Phi*part| (normalized): mode 4 lives at the MASKED sensors", fontsize=9.2)
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03); cb.set_label("relative participation", fontsize=8)

# Panel B: FIM eigenspectrum
ax = axs[1]
xs = np.arange(nm)
ax.bar(xs, evals, color=viz.C_IID, alpha=0.8, width=0.6)
ax.set_yscale("log")
ax.axhline(prior_prec, color=viz.C_NAIVE, ls="--", lw=1.4)
ax.text(0.05, prior_prec * 1.35, "prior precision (1/0.15^2)", color=viz.C_NAIVE, fontsize=8, ha="left")
# annotate the dominant raw param of the weakest eigenvector
weak = evecs[:, -1]
wi = int(np.argmax(np.abs(weak)))
ratio = evals[-1] / prior_prec
ax.annotate(f"weakest direction ~ alpha_{wi+1}\nonly {ratio:.0f}x prior (vs >1000x for\nmodes 1-3): masked target dominates it",
            (nm - 1, evals[-1]), textcoords="offset points", xytext=(-8, 26), fontsize=7.8, color="0.2", ha="right")
ax.set_xticks(xs); ax.set_xticklabels([f"e{i+1}" for i in range(nm)])
ax.set_xlabel("FIM eigen-direction (observed channels, realized floor sigma_d=%.2f)" % sd)
ax.set_ylabel("eigenvalue (information)")
ax.set_title(f"alpha_4 is the weakest direction ({ratio:.0f}x prior); peak-shift==stiffness cosine = {cos:.3f}", fontsize=9.2)
viz.style(ax, logx=False)

fig.suptitle("Identifiability: alpha_4 is barely observable from the healthy sensors and a peak shift is "
             "algebraically a stiffness scaling -> the E-LIMIT miss is under-identification", fontsize=10.0, y=1.0)
fig.subplots_adjust(wspace=0.28)
viz.save(fig, "figE_identifiability", extra="Fig E | identifiability gate")
json.dump({"fim_eigs": evals.tolist(), "prior_prec": prior_prec, "peakshift_stiffness_cos": cos,
           "sigma_d_floor": sd, "participation": P.tolist()},
          open(OUT / "identifiability.json", "w"), indent=2)
print(f"figE done; peakshift==stiffness cos={cos:.3f}; weakest eig {evals[-1]:.2e} vs prior {prior_prec:.1f}")
