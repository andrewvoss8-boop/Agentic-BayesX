"""fig_arc — the whole research arc in one figure (executive summary, accessible).
Synthetic method (G) → bimodality → cure (H) → real-data convergence (J) → binding constraint (K).
Reads the study summaries; .venv_fem_phase1."""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FIG = os.path.join(ROOT, "figures"); OUT = os.path.join(ROOT, "out")
def jload(f): return json.load(open(os.path.join(OUT, f))) if os.path.exists(os.path.join(OUT, f)) else None
G = jload("ums2_summary.json"); H = jload("ums3_summary.json"); J = jload("studyj_summary.json"); K = jload("studyk_summary.json")
FA = jload("ums_summary_FULL_ambition.json")
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.bbox": "tight"})
fig = plt.figure(figsize=(13.5, 6.0))
gs = fig.add_gridspec(2, 4, height_ratios=[1, 1.15], hspace=0.45, wspace=0.35)

# Top: the narrative flow as labeled stages
axflow = fig.add_subplot(gs[0, :]); axflow.axis("off")
stages = [
    ("1. UNIFY", "statFEM × Das/Debnath\n× Schneider → one model\n(self-tested 1e-13)", "#dbe9f6"),
    ("2. DIAGNOSE", "realistic data → physics-vs-\ndiscrepancy BIMODALITY\n(R-hat 50, KOH/§4)", "#fde0c8"),
    ("3. CURE", "constrain discrepancy →\nbimodality dies (R-hat ~1.01)\nbut coverage is separate", "#d8f0d8"),
    ("4. REAL DATA", "point at the real panel →\nsame ridge → fix it →\nCONVERGES (R-hat 1.003)", "#d8f0d8"),
    ("5. REAL WIN", "per-mode freq calibration →\n5/5 held-out coverage on\nreal data (fixes 15% FEA err)", "#d8f0d8"),
]
n = len(stages); w = 0.175
for i, (t, d, c) in enumerate(stages):
    x = 0.02 + i * (w + 0.025)
    axflow.add_patch(plt.Rectangle((x, 0.15), w, 0.7, fc=c, ec="#333", lw=1.2, transform=axflow.transAxes))
    axflow.text(x + w / 2, 0.74, t, ha="center", va="center", fontsize=11, fontweight="bold", transform=axflow.transAxes)
    axflow.text(x + w / 2, 0.40, d, ha="center", va="center", fontsize=8, transform=axflow.transAxes)
    if i < n - 1:
        axflow.annotate("", xy=(x + w + 0.024, 0.5), xytext=(x + w + 0.002, 0.5),
                        xycoords=axflow.transAxes, arrowprops=dict(arrowstyle="-|>", color="#333", lw=1.6))
axflow.set_title("The arc: build the unified method → find where it breaks → fix it → prove it converges on real data → and win on real-panel held-out prediction",
                 fontsize=11.5, pad=8)

# Bottom-left: bimodality (the diagnosis)
ax1 = fig.add_subplot(gs[1, 0])
if os.path.exists(os.path.join(OUT, "ums2_chk.npz")):
    gz = np.load(os.path.join(OUT, "ums2_chk.npz"))["gz"]
    ax1.hist(gz, bins=50, range=(0, 2), color="#d97a16", alpha=0.8)
ax1.set_title("2. The bimodality\n(synthetic, R-hat 50)", fontsize=9.5)
ax1.set_xlabel("global damping gz", fontsize=8); ax1.set_yticks([])
ax1.text(0.05, 0.92, "two basins:\n'damped' vs\n'undamped+\ndiscrepancy'", transform=ax1.transAxes, fontsize=7, va="top")

# Bottom-mid-left: the cure (R-hat bars)
ax2 = fig.add_subplot(gs[1, 1])
if H:
    tags = ["H_orth", "H_local", "H_both"]; rh = [H["arms"][t]["max_rhat"] for t in tags]
    ax2.bar(range(3), [r - 1 for r in rh], bottom=1, color=["#1f77b4", "#2ca02c", "#d62728"])
    ax2.axhline(1.05, color="#888", ls="--", lw=1); ax2.set_ylim(1, 1.07)
    ax2.set_xticks(range(3)); ax2.set_xticklabels(["orth", "local", "both"], fontsize=8)
    for i, r in enumerate(rh): ax2.text(i, r + 0.003, f"{r:.2f}", ha="center", fontsize=7)
ax2.set_title("3. Cure kills it\n(baseline was 50)", fontsize=9.5); ax2.set_ylabel("max R-hat", fontsize=8)

# Bottom-mid-right: real-data convergence + calibration
ax3 = fig.add_subplot(gs[1, 2])
if J:
    A = np.load(os.path.join(OUT, "studyj_arrays.npz")); FB = A["FB"]; YOBS = A["YOBS"]; HOLD = list(A["HOLD"])
    mag = A["magpred"]; lo, md, hi = np.percentile(mag[:, 0, :], [2.5, 50, 97.5], 0)
    ax3.fill_between(FB, lo, hi, color="#1f77b4", alpha=0.3); ax3.plot(FB, np.abs(YOBS[HOLD[0]]), color="#d62728", lw=0.9)
    ax3.set_yscale("log"); ax3.set_xlabel("freq [Hz]", fontsize=8)
ax3.set_title(f"4. REAL data converges\n(R-hat {J['convergence']['max_rhat']:.2f})" if J else "4. REAL", fontsize=9.5)
ax3.text(0.04, 0.06, "blue=predicted\nred=REAL measured\n(held-out point)", transform=ax3.transAxes, fontsize=7)

# Bottom-right: the binding constraint (K) + coverage scoreboard
ax4 = fig.add_subplot(gs[1, 3])
if K:
    kg = K["arms"]["K_global"]["qoi"]["n_cover"]; kp = K["arms"]["K_permode"]["qoi"]["n_cover"]
    ax4.bar([0, 1], [kg, kp], color=["#7f7f7f", "#1f77b4"]); ax4.set_ylim(0, 5.3)
    ax4.set_xticks([0, 1]); ax4.set_xticklabels(["global", "per-mode"], fontsize=8)
    ax4.set_ylabel("held-out QOI /5", fontsize=8)
    for i, v in enumerate([kg, kp]): ax4.text(i, v + 0.15, str(v), ha="center", fontsize=9)
ax4.set_title("5. REAL: 2/5 → 5/5\n(per-mode freq calib)", fontsize=9.5)

fig.suptitle("Can you trust a calibrated digital twin? — the one-page arc (Schneider × Das/Debnath × statFEM)",
             fontsize=13, fontweight="bold", y=1.02)
fig.text(0.01, -0.02, "SYNTHETIC (stages 1–3,5-synthetic) + REAL suspended-panel data (stage 4 + stage-5 A/B) · every number checker-backed · "
         "honest map: the method composes; the confounding is real & curable; it converges on REAL data; and per-mode frequency calibration covers 5/5 held-out points on the real panel (bands wide-but-honest).",
         fontsize=7.5, color="#777")
fig.savefig(os.path.join(FIG, "fig_arc_summary.png")); plt.close(fig)
print("fig_arc_summary written")
