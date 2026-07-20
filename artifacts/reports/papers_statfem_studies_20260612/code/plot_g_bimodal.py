"""figG7: the Study G headline diagnostic — physics-vs-discrepancy BIMODALITY.
Reads out/ums2_chk.npz (4-chain checkpoint) + out/ums2_bimodality.json. .venv_fem_phase1."""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FIG = os.path.join(ROOT, "figures"); OUT = os.path.join(ROOT, "out")
C = np.load(os.path.join(OUT, "ums2_chk.npz")); BI = json.load(open(os.path.join(OUT, "ums2_bimodality.json")))
S = json.load(open(os.path.join(OUT, "ums2_summary.json")))
nchain, nsamp = 4, 700
gz = C["gz"].reshape(nchain, nsamp)
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150, "savefig.bbox": "tight",
    "figure.constrained_layout.use": True})
CH = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd"]
fig, (axa, axb) = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw={"width_ratios": [1, 1.2]})
# left: gz posterior per chain (the bimodality)
for ch in range(nchain):
    axa.hist(gz[ch], bins=40, range=(0, 2), alpha=0.55, color=CH[ch], density=True,
             label=f"chain {ch} (med {np.median(gz[ch]):.2f})")
axa.set_xlabel("global damping scale gz"); axa.set_ylabel("posterior density")
axa.set_title("BIMODAL: a 'damped' basin (gz≈1.2) and a 'zero-damping' basin (gz≈0)")
axa.legend(frameon=False, fontsize=8)
axa.text(0.05, 0.5, "undamped +\nbig discrepancy", transform=axa.transAxes, fontsize=8, color=CH[0])
axa.text(0.55, 0.7, "damped\nphysics", transform=axa.transAxes, fontsize=8, color=CH[1])
# right: per-chain held-out QOI-A vs truth
truth = np.array(BI["truth"]); qa = np.array(BI["per_chain_qoiA"])
x = np.arange(5)
for ch in range(nchain):
    axb.plot(x + (ch - 1.5) * 0.12, qa[ch], "o", ms=6, color=CH[ch],
             label=f"chain {ch} (gz {BI['per_chain_gz'][ch]:.2f})")
axb.plot(x, truth, "_", color="#222", ms=22, mew=2.5, label="truth")
axb.plot(x, S["qoi_deterministic"]["A"], "x", color="#888", ms=8, label="nominal FEM")
axb.set_yscale("log"); axb.set_xticks(x); axb.set_xticklabels([f"hold {i+1}" for i in range(5)], fontsize=8)
axb.set_ylabel("held-out QOI-A (peak |accel|)"); axb.set_title("...and it propagates to predictions (chains disagree)")
axb.legend(frameon=False, fontsize=7.5, ncol=2)
fig.suptitle("Study G headline — the unified method exhibits PHYSICS-vs-DISCREPANCY bimodality (Kennedy–O'Hagan / vision §4)",
             fontsize=11)
fig.text(0.01, 0.005, "Study G · SYNTHETIC · 4-chain R-hat %.0f (NOT a bug — the under-identification the project studies); "
         "even the 'damped' basin over-predicts (local model error) → held-out under-coverage. Cure = CONSTRAIN the discrepancy (§5.2)."
         % S["unified"]["max_rhat"], fontsize=7.3, color="#777")
fig.savefig(os.path.join(FIG, "figG7_bimodality.png")); plt.close(fig)
print("figG7_bimodality written")
