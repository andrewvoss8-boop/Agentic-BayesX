#!/usr/bin/env python3
"""A2 figures: (1) sigma_f posterior per prior variant with analytic prior densities;
(2) predictive checks (prior predictive coverage per variant + posterior-predictive PIT, reference)."""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import halfnorm, halfcauchy, expon

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
a2 = json.load(open(os.path.join(WS, "out", "a2_sigma_f_sweep.json")))
V = a2["variants"]
ORDER = ["hn002", "hn005_reference", "hn015", "hc005", "exp005"]
PDF = {"hn002": lambda x: halfnorm.pdf(x, scale=0.02),
       "hn005_reference": lambda x: halfnorm.pdf(x, scale=0.05),
       "hn015": lambda x: halfnorm.pdf(x, scale=0.15),
       "hc005": lambda x: halfcauchy.pdf(x, scale=0.05),
       "exp005": lambda x: expon.pdf(x, scale=0.05)}

# ---------- figure 1: sigma_f posterior vs prior ----------
fig, axs = plt.subplots(1, 5, figsize=(12.5, 3.4), sharex=True, sharey=True)
x = np.linspace(1e-4, 0.20, 400)
for ax, name in zip(axs, ORDER):
    r = V[name]
    z = np.load(os.path.join(WS, "out", "a2_draws", f"{name}.npz"))
    sf = z["sigma_f"].reshape(-1)
    ax.hist(sf, bins=60, range=(0, 0.20), density=True, color="#9ecae1", label="posterior")
    pr = PDF[name](x)
    ax.plot(x, pr, color="0.3", lw=1.2, label="analytic prior")
    med = r["sigma_f_median"]
    ax.axvline(med, color="#d62728", lw=1.2)
    ax.axvline(0.046, color="0.5", lw=0.8, ls="--")
    ax.text(med + 0.004, ax.get_ylim()[1] * 0.0 + 38, f"{med*100:.1f}%", color="#d62728", fontsize=8)
    conv = r["convergence"]
    tag = "" if conv["gate_pass"] else (f"\nNOT CONVERGED\nR-hat {conv['worst_rhat']:.2f} "
                                        f"ESS {conv['min_ess']:.0f}")
    ax.set_title(r["prior"].replace(" [frozen reference]", "\n(reference)") + tag,
                 fontsize=8.5, loc="left", color=("0.1" if conv["gate_pass"] else "#d62728"))
    ax.set_xlim(0, 0.20)
    ax.set_xlabel("σ_f (log-freq sd)")
    ax.spines[["top", "right"]].set_visible(False)
axs[0].set_ylabel("density")
axs[0].legend(fontsize=7.5, frameon=False)
axs[0].text(0.05, 30, "dashed gray = stored 4.6%", fontsize=7.5, color="0.4")
fig.suptitle("σ_f prior-sensitivity sweep: the ~4.6% discrepancy floor under 5 priors "
             "(red = posterior median)", fontsize=10.5, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.90))
p1 = os.path.join(WS, "figures", "a2_sigma_f_sweep.png")
fig.savefig(p1, dpi=200)
print("wrote", p1)

# ---------- figure 2: predictive checks ----------
fig2, (axA, axB) = plt.subplots(1, 2, figsize=(10.5, 3.6))
fr = [V[n]["prior_predictive_frac"] for n in ORDER]
labels = [V[n]["prior"].replace(" [frozen reference]", "*") for n in ORDER]
axA.bar(range(5), fr, color="0.55", width=0.6)
axA.axhline(0.95, color="0.4", lw=0.8, ls="--")
axA.set_xticks(range(5))
axA.set_xticklabels(labels, fontsize=7.5, rotation=15)
axA.set_ylim(0, 1.05)
axA.set_ylabel("fraction of 18 measured modes\nin prior predictive 95%")
axA.set_title("Prior predictive check (per variant; * = reference)", fontsize=9.5, loc="left")
for i, f in enumerate(fr):
    axA.text(i, f + 0.02, V[ORDER[i]]["prior_predictive_covered"], ha="center", fontsize=8)
axA.spines[["top", "right"]].set_visible(False)

pit = a2["posterior_predictive_PIT_reference"]["per_mode"]
modes = list(pit.keys())
vals = np.array(list(pit.values()))
axB.plot(np.sort(vals), (np.arange(len(vals)) + 0.5) / len(vals), "o-", ms=4, color="0.15",
         label="empirical CDF of PIT")
axB.plot([0, 1], [0, 1], "--", color="0.6", lw=0.8, label="uniform (calibrated)")
axB.set_xlabel("PIT value (posterior-predictive CDF at measured freq)")
axB.set_ylabel("empirical CDF")
axB.set_title("Posterior predictive PIT, reference run (18 modes)", fontsize=9.5, loc="left")
axB.legend(fontsize=8, frameon=False, loc="upper left")
axB.spines[["top", "right"]].set_visible(False)
fig2.tight_layout()
p2 = os.path.join(WS, "figures", "a2_predictive_checks.png")
fig2.savefig(p2, dpi=200)
print("wrote", p2)

conv_ref = V["hn005_reference"]["convergence"]
cap1 = (f"σ_f posterior (pooled per-chain draws, histogram) vs analytic prior density under 5 priors; "
        f"red = posterior median, dashed gray = stored 4.6% reference. Reference run reproduces the "
        f"stored posterior (worst R-hat {conv_ref['worst_rhat']:.3f}, min ESS "
        f"{conv_ref['min_ess']:.0f}); any non-converged variant is labeled IN RED on its panel with "
        "worst R-hat/ESS. Source runs: frozen twin shocksat_fem_modal_twin_20260609 likelihood; this "
        "study out/a2_sigma_f_sweep.json + out/a2_draws/.")
cap2 = ("Left: prior predictive check — fraction of the 18 measured modal frequencies inside each "
        "variant's per-mode central 95% prior predictive envelope (800 prior draws). Right: "
        "posterior-predictive PIT for the reference HalfNormal(0.05) run (500 posterior draws); "
        "calibrated ⇒ near the diagonal. Source run: out/a2_sigma_f_sweep.json.")
mf_p = os.path.join(WS, "out", "fig_manifest.json")
mf = json.load(open(mf_p))
mf["figures"] = [f for f in mf["figures"] if f["path"] not in
                 ("figures/a2_sigma_f_sweep.png", "figures/a2_predictive_checks.png")]
mf["figures"] += [{"path": "figures/a2_sigma_f_sweep.png", "caption": cap1},
                  {"path": "figures/a2_predictive_checks.png", "caption": cap2}]
json.dump(mf, open(mf_p, "w"), indent=1)
