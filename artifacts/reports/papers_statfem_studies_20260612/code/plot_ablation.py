"""figAB_ablation — Study A correlation-knob ablation (D37): which Schneider ingredient does what? .venv_fem_phase1."""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FIG = os.path.join(ROOT, "figures"); OUT = os.path.join(ROOT, "out")
R = json.load(open(os.path.join(OUT, "study_a_ablation.json")))
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150, "savefig.bbox": "tight",
    "figure.constrained_layout.use": True})
order = ["v1", "v2iid", "v2"]
labs = ["V1\nlinear-iid", "V2-iid\nlog, NO correlation\n(the ablation)", "V2\nlog + correlation"]
cols = ["#d62728", "#ff7f0e", "#1f77b4"]
rh = [R[k]["max_rhat"] for k in order]; bw = [R[k]["band_width"] for k in order]
cov = [R[k]["coverage"]*100 for k in order]

fig, (axa, axb) = plt.subplots(1, 2, figsize=(12.5, 4.6))
# (a) convergence
axa.bar(range(3), rh, color=cols)
axa.axhline(1.05, color="#444", ls="--", lw=1.2); axa.text(2.45, 1.05, "1.05 gate", fontsize=7.5, va="bottom", ha="right")
axa.set_yscale("log"); axa.set_ylabel("max R-hat (log scale; ≤1.05 = converged)")
axa.set_xticks(range(3)); axa.set_xticklabels(labs, fontsize=8.5)
for i, v in enumerate(rh): axa.text(i, v*1.1, f"{v:.2f}", ha="center", fontsize=9, fontweight="bold")
axa.set_title("Convergence: the LOG error space fixes mixing\n(NOT the correlation — V2-iid over-counts identically yet converges)", fontsize=9.5)
axa.annotate("linear-additive error\nmisspecified for an FRF\n→ won't mix", xy=(0, rh[0]), xytext=(0.16, 0.55),
             textcoords="axes fraction", fontsize=7.5, color="#d62728",
             arrowprops=dict(arrowstyle="->", color="#d62728", lw=1))

# (b) held-out band width (+ coverage labels)
axb.bar(range(3), bw, color=cols)
# hatch V1 as not-trustworthy (didn't converge)
axb.patches[0].set_hatch("xxx"); axb.patches[0].set_edgecolor("white")
axb.set_ylabel("held-out 95% band width (interleaved)")
axb.set_xticks(range(3)); axb.set_xticklabels(labs, fontsize=8.5)
for i, (v, c) in enumerate(zip(bw, cov)):
    note = "  (not trustworthy:\n  didn't converge)" if order[i] == "v1" else f"\ncover {c:.0f}%"
    axb.text(i, v + 0.12, f"{v:.2f}{note}", ha="center", fontsize=7.8)
axb.set_title("Held-out bands: CORRELATION tightens them ~2.4×\n(via conditioning on neighbouring lines)", fontsize=9.5)
axb.annotate("", xy=(2, bw[2]), xytext=(1, bw[1]), arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=1.4))
axb.text(1.5, (bw[1]+bw[2])/2 + 0.15, "2.16 → 0.88\n(96% → 100%)", color="#1f77b4", fontsize=7.8, ha="center")

fig.suptitle("Study A ablation (D37) — separating Schneider's two ingredients: T-S1 (log error) fixes CONVERGENCE; T-S2 (correlation) tightens the BANDS",
             fontsize=10.5)
fig.text(0.01, -0.03, "Identical data/split/physics-priors/sampler; only the discrepancy MODEL changes. "
         "V1→V2-iid removes the linear-additive error space (→log-multiplicative, separate mag/phase scales): convergence is restored (R-hat 24→1.00) with the SAME iid over-counting. "
         "V2-iid→V2 adds the Schneider correlation: held-out band tightens 2.16→0.88 (~2.4×) and coverage 96%→100% by interpolating the discrepancy from neighbouring observed lines.",
         fontsize=6.8, color="#777")
fig.savefig(os.path.join(FIG, "figAB_ablation.png")); plt.close(fig)
print("figAB_ablation written:", R["verdict"])
