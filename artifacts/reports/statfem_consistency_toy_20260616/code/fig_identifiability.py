#!/usr/bin/env python3
"""figI: identifiability (P5). theta->observable sensitivity du/dtheta of the forced drive-point response
by drive frequency, plus the Fisher information for theta. theta is well-identified at both eps levels
(approx posterior SD ~0.005 from one test), so non-recovery under eps>0 is a model-form-error BIAS, not
an identifiability failure."""
import json
from pathlib import Path

import numpy as np

import core
import viz
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
ID = json.load(open(WS / "out" / "identifiability.json"))

fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4))

# Panel A: RMS du/dtheta by drive frequency (eps=0 control)
ax = axes[0]
sens = ID["eps"]["0.0"]["rms_dudtheta_by_freq"]
freqs = [float(k) for k in sens]
vals = [sens[k] for k in sens]
ax.bar(np.arange(len(freqs)), vals, color=viz.C_STATFEM, alpha=0.85, edgecolor="white")
for i, (f, v) in enumerate(zip(freqs, vals)):
    ax.text(i, v + 0.01, f"{v:.2f}", ha="center", fontsize=7.5, color="0.3")
ax.set_xticks(np.arange(len(freqs))); ax.set_xticklabels([f"{f:.1f}" for f in freqs])
ax.set_xlabel("fit drive frequency (rad/s)")
ax.set_ylabel("RMS sensitivity  |du/dtheta|")
ax.set_title("theta -> response sensitivity (identifiability)", fontsize=10)

# Panel B: Fisher info / approx posterior SD per eps
ax = axes[1]
epss = list(ID["eps"].keys())
fim = [ID["eps"][e]["fisher_theta"] for e in epss]
sd1 = [ID["eps"][e]["approx_post_sd_1test"] for e in epss]
ax.bar(np.arange(len(epss)), fim, color=viz.C_IFT, alpha=0.85, edgecolor="white", width=0.5)
for i, (e, f, s) in enumerate(zip(epss, fim, sd1)):
    ax.text(i, f * 1.02, f"FIM {f:.0f}\napprox post SD {s:.4f}", ha="center", fontsize=7.6, color="0.3",
            va="bottom")
ax.set_xticks(np.arange(len(epss))); ax.set_xticklabels([f"eps={e}" for e in epss])
ax.set_ylabel("Fisher information for theta (one test)")
ax.set_ylim(0, max(fim) * 1.25)
ax.set_title("theta is well-identified at both eps", fontsize=10)
ax.text(0.5, 0.45, "=> non-recovery under eps>0 is a\nmodel-form-error BIAS,\nnot an identifiability failure",
        transform=ax.transAxes, fontsize=8.2, ha="center", color="0.3")
fig.tight_layout()
viz.save(fig, "figI_identifiability", extra="analytic sensitivity; theta absorbs the omitted physics under eps>0")
