#!/usr/bin/env python3
"""A4 figure: 1-D profiled-nuisance whole-FRF log-likelihood along the two most sensitive
stiffness multipliers, with separated NUTS chain locations annotated."""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
a4 = json.load(open(os.path.join(WS, "out", "a4_profile_likelihood.json")))

fig, axs = plt.subplots(1, 2, figsize=(11, 4.0), sharey=True)
for ax, (pname, prof) in zip(axs, a4["profiles"].items()):
    th = np.array([p["theta"] for p in prof["points"]])
    ll = np.array([p["profile_loglik"] for p in prof["points"]])
    dll = ll - ll.max()
    ax.plot(th, dll, "-", color="0.15", lw=1.4, zorder=3)
    ax.plot(th, dll, ".", color="0.15", ms=4, zorder=3)
    for i, tm in enumerate(prof["local_maxima_theta"]):
        ax.axvline(tm, color="0.85", lw=0.7, zorder=1)
    for i, cm in enumerate(prof["chain_means_theta"]):
        ax.axvline(cm, color="#d62728", lw=1.2, ls=":", zorder=2)
        ax.text(cm, -3.5 - 4 * (i % 2), f"c{i+1}", color="#d62728", fontsize=7.5,
                ha="center")
    ax.set_xscale("log")
    ax.set_xticks([0.65, 0.8, 1.0, 1.25, 1.6])
    ax.set_xticklabels(["0.65", "0.8", "1.0", "1.25", "1.6"])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel(f"θ ({pname}), other θ = 1  (log scale)")
    ax.set_title(f"{pname}: {prof['n_local_maxima']} local maxima "
                 f"(sens. {prof['sensitivity_rank_value']})", fontsize=10, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
axs[0].set_ylabel("profile log-likelihood − max  (nats)")
axs[0].annotate("gray verticals = local maxima\nred dotted = separated NUTS chain means\n"
                "(stored run: R-hat 44.7, ESS 2.0 — NOT converged)",
                xy=(0.02, 0.05), xycoords="axes fraction", fontsize=8, color="0.3")
fig.suptitle("Why the whole-FRF posterior separated: the iid log-magnitude likelihood is multimodal "
             "(peak-crossing ridges), diagnosis not verdict", fontsize=10.5, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.93))
p = os.path.join(WS, "figures", "a4_profile.png")
fig.savefig(p, dpi=200)
print("wrote", p)

cap = ("1-D profile log-likelihood (drive gains + sigma_n PROFILED at every point, closed-form MLE, "
       "gradient-verified) of the iid log-magnitude whole-FRF likelihood, along the two most "
       "FRF-sensitive stiffness multipliers (bottom_box, top_box), 41 log-spaced points over the "
       "prior 95% range; y = log-likelihood relative to max, nats. Both slices show ~10 local maxima; "
       "red dotted lines mark the 4 separated NUTS chain means of the stored non-converged run "
       "(R-hat 44.7, min ESS 2.0 — intervals from that run are not trustworthy). "
       "Source runs: shocksat_full_spectrum_frf_20260714 (arm_b_nuts theta-only, fold m_xpos_990x) "
       "+ this study out/a4_profile_likelihood.json.")
mf_p = os.path.join(WS, "out", "fig_manifest.json")
mf = json.load(open(mf_p))
mf["figures"] = [f for f in mf["figures"] if f["path"] != "figures/a4_profile.png"]
mf["figures"].append({"path": "figures/a4_profile.png", "caption": cap})
json.dump(mf, open(mf_p, "w"), indent=1)
