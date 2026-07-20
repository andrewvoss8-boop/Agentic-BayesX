#!/usr/bin/env python3
"""Fig D (honest limit): a coherent +15% peak-frequency shift on the masked virtual target is
CONFOUNDED with the failed-sensor local-mode stiffness alpha_4. Left: alpha_4 posteriors -- only the
UNBIASED control recovers truth; the biased disc-aware fits MISS alpha_4. Right: the masked channel --
the disc-aware band still covers the peak HEIGHT (amplitude QOI) but the peak LOCATION (alpha_4) is
wrong. The cure is to BREAK the degeneracy (a sensor that sees the local mode), not more discrepancy.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import viz

OUT = Path(__file__).resolve().parent.parent / "out"
L = json.load(open(OUT / "limit_summary.json"))
F = L["fig"]
arms = L["arms"]
freqs = np.array(F["freqs"]); cm = F["cm"]
a4_truth = F["alpha4_truth"]
DB = 20.0 / np.log(10.0)  # ln|H| -> dB

fig, axs = plt.subplots(1, 2, figsize=(12.4, 5.2))

# ---- Left: alpha_4 across arms ----
ax = axs[0]
order = [("deterministic", None, viz.C_DET, "deterministic\n(trusts target)"),
         ("bayes_iid_biased", "bayes_iid_biased", viz.C_IID, "disc-aware iid\n(biased target)"),
         ("bayes_correlated_biased", "bayes_correlated_biased", viz.C_CORR, "disc-aware corr\n(biased target)"),
         ("bayes_correlated_unbiased_control", "bayes_correlated_unbiased_control", "#0f766e",
          "disc-aware corr\nCONTROL (unbiased)")]
ax.axhspan(0.45, 1.0, color="#e8f5e9", zorder=0)
ax.axhspan(1.0, 1.55, color="#fdecea", zorder=0)
ax.text(3.45, 0.52, "softening (true direction)", color="#1b5e20", fontsize=8, ha="right")
ax.text(3.45, 1.45, "apparent hardening (wrong)", color="#9b1c1c", fontsize=8, ha="right")
for j, (key, akey, col, lab) in enumerate(order):
    if akey is None:
        ax.plot(j, F["det_alpha4"], "D", color=col, ms=9, zorder=4)
        ax.annotate("box floor" if F["det_alpha4"] <= 0.51 else "point", (j, F["det_alpha4"]),
                    textcoords="offset points", xytext=(0, 8), fontsize=7.5, color=col, ha="center")
    else:
        ci = arms[akey]["alpha4_ci"]
        ax.plot([j, j], [ci[0], ci[2]], color=col, lw=8, alpha=0.5, solid_capstyle="butt", zorder=3)
        ax.plot(j, ci[1], "o", color=col, ms=8, zorder=4)
        ok = arms[akey]["alpha4_covers_truth"]
        ax.annotate("covers" if ok else "MISSES", (j, ci[2]), textcoords="offset points",
                    xytext=(0, 7), fontsize=7.8, ha="center",
                    color=("#1b5e20" if ok else "#9b1c1c"), fontweight="bold")
ax.axhline(a4_truth, color=viz.C_TRUTH, ls="--", lw=1.4)
ax.text(0.0, a4_truth - 0.045, f"truth alpha_4 = {a4_truth:.2f}", fontsize=8.5, color="0.2")
ax.set_xticks(range(4)); ax.set_xticklabels([o[3] for o in order], fontsize=7.6)
ax.set_ylabel("local-mode stiffness alpha_4  (95% interval)")
ax.set_ylim(0.45, 1.55)
ax.set_title("alpha_4: only the unbiased control recovers it; the +15% bias misses it", fontsize=9.4)
viz.style(ax, logx=False)

# ---- Right: masked channel prediction ----
ax = axs[1]
ax.plot(freqs, F["truth_db"], color=viz.C_TRUTH, lw=2.0, zorder=4)
ax.annotate("true masked (held out)", (freqs[-1], F["truth_db"][-1]), textcoords="offset points",
            xytext=(-4, 4), fontsize=8, color=viz.C_TRUTH, ha="right")
ax.plot(freqs, F["virtual_db"], color="#b45309", lw=1.1, ls=":", zorder=3)
ax.annotate("biased virtual target\n(+15% peak shift)", (freqs[np.argmax(F["virtual_db"])], max(F["virtual_db"])),
            textcoords="offset points", xytext=(6, -2), fontsize=7.6, color="#b45309")
for akey, col, lab in [("bayes_iid_biased", viz.C_IID, "iid 95%"),
                       ("bayes_correlated_biased", viz.C_CORR, "corr 95%")]:
    lo = DB * np.array(arms[akey]["band_lo"]); hi = DB * np.array(arms[akey]["band_hi"])
    ax.fill_between(freqs, lo, hi, color=col, alpha=0.16, zorder=2)
ax.annotate("disc-aware bands cover the\npeak HEIGHT (QOI) but not the\npeak LOCATION (alpha_4)",
            (freqs[int(np.argmax(F["truth_db"]))], min(F["truth_db"]) + 6),
            fontsize=7.8, color="0.25", ha="center")
ax.set_xlabel("frequency [Hz], log scale")
ax.set_ylabel(f"Ch{cm+1} |H|  [dB]")
ax.set_title("masked local-mode channel: amplitude QOI survives, location is wrong", fontsize=9.4)
viz.style(ax, logx=True)

fig.suptitle("Honest limit: a coherent bias is confounded with a parameter -- sigma_d does NOT rescue "
             "alpha_4 (cure = break the degeneracy)", fontsize=10.2, y=1.0)
fig.subplots_adjust(wspace=0.22)
viz.save(fig, "figD_honest_limit", extra="Fig D | E-LIMIT | honest negative")
print("figD done")
