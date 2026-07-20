"""figH (Study H cure A/B) + figI (Study I unknown forcing). .venv_fem_phase1."""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FIG = os.path.join(ROOT, "figures"); OUT = os.path.join(ROOT, "out")
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150, "savefig.bbox": "tight",
    "figure.constrained_layout.use": True})
C = {"G": "#999999", "H_orth": "#1f77b4", "H_local": "#2ca02c", "H_both": "#d62728"}

# ---------------- figH ----------------
if os.path.exists(os.path.join(OUT, "ums3_summary.json")):
    H3 = json.load(open(os.path.join(OUT, "ums3_summary.json")))
    CHK = np.load(os.path.join(OUT, "ums2_chk.npz"))      # G-baseline 4-chain gz
    gz_G = CHK["gz"]
    fig, axs = plt.subplots(1, 3, figsize=(13, 4), gridspec_kw={"width_ratios": [1.2, 1, 1]})
    # (a) gz posterior: baseline bimodal vs arms
    axs[0].hist(gz_G, bins=60, range=(0, 3.2), density=True, color=C["G"], alpha=0.55,
                label="G baseline (BIMODAL)")
    for tag in ("H_orth", "H_local", "H_both"):
        z = np.load(os.path.join(OUT, f"ums3_{tag}.npz"))["gz"]
        axs[0].hist(z, bins=60, range=(0, 3.2), density=True, color=C[tag], alpha=0.5,
                    label=f"{tag} (R-hat {H3['arms'][tag]['max_rhat']:.2f})")
    axs[0].set_xlabel("global damping scale gz"); axs[0].set_ylabel("posterior density")
    axs[0].set_title("Does the constraint kill the zero-damping basin?")
    axs[0].legend(frameon=False, fontsize=7.5)
    # (b) per-arm convergence + coverage bars
    tags = ["H_orth", "H_local", "H_both"]
    rh = [H3["arms"][t]["max_rhat"] for t in tags]
    cov = [H3["arms"][t]["qoi"]["n_cover"] for t in tags]
    x = np.arange(3)
    axs[1].bar(x, [v - 1.0 for v in rh], bottom=1.0, color=[C[t] for t in tags])
    axs[1].axhline(1.05, color="#888", ls="--", lw=1)
    axs[1].set_ylim(1.0, 1.06)
    axs[1].set_xticks(x); axs[1].set_xticklabels([t.replace("H_", "") for t in tags])
    axs[1].set_ylabel("max R-hat"); axs[1].set_title("Convergence (gate 1.05) — baseline was 50")
    for i, v in enumerate(rh): axs[1].text(i, v + 0.002, f"{v:.3f}", ha="center", fontsize=8)
    axs[2].bar(x, cov, color=[C[t] for t in tags]); axs[2].axhline(8, color="#888", ls="--", lw=1)
    axs[2].set_ylim(0, 10.5); axs[2].set_xticks(x)
    axs[2].set_xticklabels([t.replace("H_", "") for t in tags])
    axs[2].set_ylabel("held-out QOI covered /10"); axs[2].set_title("Trust gate (≥8/10)")
    for i, v in enumerate(cov): axs[2].text(i, v + 0.2, str(v), ha="center", fontsize=9)
    note = " · ".join(f"{t}: gz/chain {np.round(H3['arms'][t]['gz_per_chain'],2)}" for t in tags)
    fig.suptitle("Study H — the constrained-discrepancy A/B (vision §13.2): orthogonal fingerprints vs local damping vs both",
                 fontsize=11)
    fig.text(0.01, 0.005, f"Study H · SYNTHETIC · baseline = Study G bimodal run · {note}",
             fontsize=7, color="#777")
    fig.savefig(os.path.join(FIG, "figH_cure_ab.png")); plt.close(fig)
    print("figH written")

# ---------------- figI ----------------
if os.path.exists(os.path.join(OUT, "ums4_summary.json")):
    I4 = json.load(open(os.path.join(OUT, "ums4_summary.json")))
    A4 = np.load(os.path.join(OUT, "ums4_arrays.npz"))
    fig, axs = plt.subplots(1, 3, figsize=(13, 4), gridspec_kw={"width_ratios": [1.3, 1, 1]})
    # (a) forcing recovery (I-joint)
    axs[0].fill_between(A4["FI4"], A4["logF_lo"], A4["logF_hi"], color="#1f77b4", alpha=0.3,
                        label="I-joint 95% CI")
    axs[0].plot(A4["FI4"], A4["logF_med"], color="#1f77b4", lw=1)
    axs[0].plot(A4["FI4"], A4["logF_true"], color="#222", lw=1.2, label="true log|F| (never measured)")
    axs[0].set_xlabel("frequency [Hz]"); axs[0].set_ylabel("log|F(ω)|")
    covF = I4["arms"]["I_joint"].get("forcing_logF_coverage", float("nan"))
    axs[0].set_title(f"Unknown force spectrum recovered jointly (coverage {covF*100:.0f}%)")
    axs[0].legend(frameon=False, fontsize=8)
    # (b) structural QOI per arm
    tA = A4["QA_true"]
    for off, key, c, lab in ((-0.15, "qa_ratio", "#2ca02c", "I-ratio (transmissibility)"),
                             (0.15, "qa_joint", "#1f77b4", "I-joint (3-way)")):
        qa = A4[key]; lo, md, hi = np.percentile(qa, [2.5, 50, 97.5], 0)
        for h in range(5):
            axs[1].plot([h + off, h + off], [lo[h], hi[h]], color=c, lw=4, alpha=0.75)
            axs[1].plot(h + off, md[h], "o", ms=4, color=c)
    for h in range(5):
        axs[1].plot(h, tA[h], "_", color="#222", ms=18, mew=2.2)
    axs[1].set_yscale("log"); axs[1].set_xticks(range(5))
    axs[1].set_xticklabels([f"hold {i+1}" for i in range(5)], fontsize=8)
    axs[1].set_ylabel("peak |H| (structure property)")
    rq = I4["arms"]["I_ratio"]["qoi"]["n_cover"]; jq = I4["arms"]["I_joint"]["qoi"]["n_cover"]
    axs[1].set_title(f"Held-out structural QOI: ratio {rq}/5 vs joint {jq}/5")
    axs[1].legend(handles=[plt.Line2D([0],[0],color="#2ca02c",lw=4,label=f"I-ratio (R-hat {I4['arms']['I_ratio']['max_rhat']:.2f})"),
                           plt.Line2D([0],[0],color="#1f77b4",lw=4,label=f"I-joint (R-hat {I4['arms']['I_joint']['max_rhat']:.2f})"),
                           plt.Line2D([0],[0],color="#222",lw=2,label="truth")],
                  frameon=False, fontsize=7.5)
    # (c) gz identifiability under unknown forcing
    axs[2].hist(A4["gz_ratio"], bins=40, range=(0, 2), density=True, color="#2ca02c", alpha=0.6,
                label="I-ratio")
    axs[2].hist(A4["gz_joint"], bins=40, range=(0, 2), density=True, color="#1f77b4", alpha=0.5,
                label="I-joint")
    axs[2].set_xlabel("global damping gz"); axs[2].set_title("Damping identifiability, force unknown")
    axs[2].legend(frameon=False, fontsize=8)
    fig.suptitle("Study I — unknown stochastic forcing (vision §5.0): cancel it (transmissibility) vs infer it (three-way)",
                 fontsize=11)
    fig.text(0.01, 0.005, "Study I · SYNTHETIC · responses only, force never measured · QOI = peak |H| "
             "(forcing-independent structure property) · physics-only intervals (discrepancy-mapping ambiguity documented)",
             fontsize=7, color="#777")
    fig.savefig(os.path.join(FIG, "figI_unknown_forcing.png")); plt.close(fig)
    print("figI written")
print("plot_hi done")
