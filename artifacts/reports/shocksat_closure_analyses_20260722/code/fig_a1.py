#!/usr/bin/env python3
"""A1 figure: prior-whitened eigenvalue spectrum with bootstrap CIs + eigenvector composition.

Tufte: direct labels, minimal ink, log y (variance ratios span 0.02-1.2), diverging colormap for
signed eigenvector components, caption carries source + numbers.
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
a1 = json.load(open(os.path.join(WS, "out", "a1_subspace.json")))

lam = np.array(a1["eigenvalues_ascending"])
ci = np.array(a1["eigenvalues_ci95"])
P = len(lam)
gnames = list(a1["directions"][0]["all_components"].keys())
V = np.array([[d["all_components"][g] for g in gnames] for d in a1["directions"]])  # (dir, group)

fig, (ax, ax2) = plt.subplots(
    1, 2, figsize=(10.5, 4.4), gridspec_kw={"width_ratios": [1.0, 1.25]})

# ---- panel 1: eigenvalue spectrum ----
x = np.arange(1, P + 1)
ax.errorbar(x, lam, yerr=[lam - ci[:, 0], ci[:, 1] - lam], fmt="o", ms=5,
            color="0.15", ecolor="0.45", elinewidth=1.2, capsize=2.5, zorder=3)
ax.axhline(1.0, color="0.6", lw=0.8, ls="--")
ax.text(P + 0.15, 1.0, "prior variance\n(no information)", fontsize=8.5,
        color="0.4", va="center")
ax.axvspan(0.5, 4.5, color="0.93", zorder=0)
ax.text(2.5, 2.1, "4 contracted\ncombinations", ha="center", fontsize=9, color="0.25")
for k in range(4):
    ax.annotate(f"{lam[k]:.3f}", (x[k], lam[k]), textcoords="offset points",
                xytext=(0, -14), ha="center", fontsize=8, color="0.25")
ax.set_yscale("log")
ax.set_ylim(0.012, 3.2)
ax.set_xlim(0.4, P + 1.6)
ax.set_xticks(x)
ax.set_xlabel("eigenvalue rank (ascending)")
ax.set_ylabel("posterior / prior variance ratio  (log scale)")
ax.set_title("What 18 modal frequencies identified", fontsize=10.5, loc="left")
ax.spines[["top", "right"]].set_visible(False)

# ---- panel 2: eigenvector composition ----
im = ax2.imshow(V.T, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
ax2.set_xticks(range(P))
ax2.set_xticklabels([f"{k+1}\n{lam[k]:.2f}" for k in range(P)], fontsize=8)
ax2.set_yticks(range(len(gnames)))
ax2.set_yticklabels(gnames, fontsize=9)
ax2.set_xlabel("direction rank / variance ratio")
ax2.set_title("Eigenvector composition (log-θ loadings)", fontsize=10.5, loc="left")
for i in range(len(gnames)):
    for j in range(P):
        if abs(V[j, i]) >= 0.25:
            ax2.text(j, i, f"{V[j, i]:+.2f}", ha="center", va="center", fontsize=7,
                     color="white" if abs(V[j, i]) > 0.6 else "0.15")
ax2.axvline(3.5, color="0.2", lw=1.0)
cb = fig.colorbar(im, ax=ax2, shrink=0.85, pad=0.02)
cb.set_label("loading", fontsize=8.5)
cb.ax.tick_params(labelsize=8)

fig.suptitle("")
fig.tight_layout()
p = os.path.join(WS, "figures", "a1_subspace.png")
fig.savefig(p, dpi=200)
print("wrote", p)

caption = (
    "Prior-whitened identified subspace of the modal posterior. Left: eigenvalues of the "
    "prior-whitened log-θ posterior covariance (posterior/prior variance ratio, dimensionless; "
    "1 = prior returned) with 95% block-bootstrap CIs (block 40, 1000 resamples). Four combinations "
    "are contracted (0.019/0.029/0.259/0.355 — matches the adjudicated known answer); five are "
    "prior-like (0.87–1.17). Right: eigenvector loadings; labeled cells |loading| ≥ 0.25. "
    "Claim is subspace-level only — no per-parameter identifiability is asserted. "
    "Source run: shocksat_fem_modal_twin_20260609/nuts_full_samples.npz (converged full-calibration "
    "NUTS, worst R-hat 1.022, min ESS 232); this study out/a1_subspace.json.")
mf_p = os.path.join(WS, "out", "fig_manifest.json")
mf = json.load(open(mf_p)) if os.path.exists(mf_p) else {"figures": []}
mf["figures"] = [f for f in mf["figures"] if f["path"] != "figures/a1_subspace.png"]
mf["figures"].append({"path": "figures/a1_subspace.png", "caption": caption})
json.dump(mf, open(mf_p, "w"), indent=1)
