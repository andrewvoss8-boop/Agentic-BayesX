#!/usr/bin/env python3
"""Deck figures — the three roadblocks: damping, re-meshing/stiffness, likelihood formulations (Tufte gate)."""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; OUT = WS / "out"

# ---------------- ROADBLOCK 1: DAMPING ----------------
mm = np.load(WS / "data" / "measured_modes.npz", allow_pickle=True)
mfr = mm["freqs"]; zmeas = mm["damp"] / 100.0          # 33 modes, matches mfr
ff = np.linspace(45, 260, 200); zw = rf.measured_zeta_w(ff)
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.3))
ax[0].plot(ff, zw * 100, color="#b2182b", lw=1.8, label="exp-window ζ_w(f) (measurement artifact)")
ax[0].scatter(mfr, zmeas * 100, s=22, color="#2166ac", zorder=4, label="measured modal ζ (.ash)")
ax[0].set_xlabel("frequency (Hz)"); ax[0].set_ylabel("damping ratio ζ (%)"); ax[0].set_xscale("log")
ax[0].legend(fontsize=7.5); ax[0].set_title("A. Damping is unmeasurable here", fontsize=9.5, loc="left")
ax[0].text(0.03, 0.04, "window ζ_w ≈ the real ζ → apparent damping is mostly the window;\nhalf-power band 2ζf < df=1.25 Hz → bandwidth unresolvable",
           transform=ax[0].transAxes, fontsize=7, color="0.3")
# per-mode-zeta injection hurts (from dampcorr): show sigma_QOI peak across 3 arms
dc0 = json.loads((OUT / "dampcorr_qoi_seed00.json").read_text())["arms"]
arms = ["ARM0_uniform1pct", "ARM1_uniform1pct_plus_window", "ARM2_permode_struct_plus_window"]
lab = ["uniform ζ=1%", "+ window", "+ measured\nper-mode ζ"]
iv = [dc0[a]["scores_theta_plus_qoi_discrepancy"]["peak"]["interval_score_mean"] for a in arms]
b = ax[1].bar(lab, iv, color=["0.6", "#1b7837", "#b2182b"], width=0.6)
ax[1].set_ylabel("held-out peak interval score (lower=better)")
ax[1].set_title("B. Injecting measured ζ makes it WORSE", fontsize=9.5, loc="left")
for i, v in enumerate(iv): ax[1].text(i, v + 20, f"{v:.0f}", ha="center", fontsize=8.5)
for a in ax:
    for sp in ("top", "right"): a.spines[sp].set_visible(False)
fig.text(0.5, 0.005, "Single-impact FRF: exponential window adds frequency-dependent damping comparable to the structure's; df=1.25 Hz can't resolve "
         "the half-power bandwidth. Using the true per-mode ζ hurts because the windowed FRF under-resolves light modes.", ha="center", fontsize=6.5, color="0.4")
fig.tight_layout(rect=[0, 0.04, 1, 1]); fig.savefig(FIG / "fig_roadblock_damping.png", dpi=140); plt.close(fig)

# ---------------- ROADBLOCK 2: RE-MESHING / STIFFNESS ----------------
jf = json.loads((OUT / "cardD_inputs" / "joint_frontier.json").read_text())
pf = jf["pareto_front"]; nom = jf["nominal"]
s1 = json.loads((OUT / "stage1_evidence.json").read_text())
le = s1["log_evidence"]
order = ["M0_fixed_thetaMAP", "M1_joint_split", "M0_base9", "M1_box_split", "M1_full_rich"]
labs = ["M0 as-received", "M1 joint-split", "M0 9-group", "M1 box-split", "M1 full-rich(16p)"]
vals = [le[k] - le["M0_base9"] for k in order]
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.3))
ax[0].scatter([p["mean_abs_df_pct"] for p in pf], [p["hard_region_mac"] for p in pf], s=28, color="#2166ac", label="Pareto front (stiffness updates)")
ax[0].scatter([nom["mean_abs_df_pct"]], [nom["hard_region_mac"]], s=90, color="#b2182b", marker="*", label="as-received FEM", zorder=5)
ax[0].set_xlabel("mean |Δf| (%)  ← better"); ax[0].set_ylabel("hard-region MAC  better →")
ax[0].legend(fontsize=7.5); ax[0].set_title("A. Stiffness re-mesh: shape↔freq Pareto wall (0/6000 both-improve)", fontsize=9, loc="left")
cols = ["#1b7837" if v >= 0 else "#b2182b" for v in vals]
ax[1].barh(range(len(vals))[::-1], vals, color=cols, height=0.6)
ax[1].axvline(0, color="0.3", lw=1); ax[1].set_yticks(range(len(vals))[::-1]); ax[1].set_yticklabels(labs, fontsize=8)
ax[1].set_xlabel("Δ log-evidence vs 9-group (BIC-adj)  ← worse | better →")
ax[1].set_title("B. Richer LOCAL stiffness does NOT earn its complexity", fontsize=9, loc="left")
for y, v in zip(range(len(vals))[::-1], vals): ax[1].text(v + (0.1 if v >= 0 else -0.1), y, f"{v:+.1f}", va="center", ha="left" if v >= 0 else "right", fontsize=8)
for a in ax:
    for sp in ("top", "right"): a.spines[sp].set_visible(False)
fig.text(0.5, 0.005, "Card D: 6000 joint-stiffness updates, 0 improve hard-region MAC without detuning frequency. Card F Stage-1: Bayesian "
         "evidence (Ockham) penalizes added local params. Mesh already converged; stiffness is not the lever.", ha="center", fontsize=6.5, color="0.4")
fig.tight_layout(rect=[0, 0.04, 1, 1]); fig.savefig(FIG / "fig_roadblock_remesh.png", dpi=140); plt.close(fig)

# ---------------- ROADBLOCK 3: LIKELIHOOD FORMULATIONS ----------------
sp = json.loads((OUT / "shape_pattern_test.json").read_text())["all_modes"]
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.3))
# convergence: whole-FRF vs modal-feature
labs2 = ["whole-FRF\nmagnitude\n(NUTS)", "whole-FRF\nmagnitude\n(TMCMC)", "modal\npeak-frequency\n(NUTS)"]
rhats = [104.0, 129.0, 1.002]
b = ax[0].bar(labs2, rhats, color=["#b2182b", "#b2182b", "#1b7837"], width=0.6)
ax[0].axhline(1.05, color="0.4", ls="--", lw=0.9); ax[0].text(2.4, 1.6, "R̂≤1.05 gate", fontsize=7, color="0.4", ha="right")
ax[0].set_yscale("log"); ax[0].set_ylabel("max R̂ (convergence)")
ax[0].set_title("A. Whole-FRF likelihood is multimodal; modal converges", fontsize=9, loc="left")
for i, v in enumerate(rhats): ax[0].text(i, v * 1.15, f"{v:g}", ha="center", fontsize=8.5)
# shape pattern correlation: FEM vs measured
ax[1].bar(["FEM shape", "measured\n.ash shape"], [sp["mean_logamp_corr_FEM"], sp["mean_logamp_corr_measured"]],
          color=["#7b3294", "#2166ac"], width=0.55)
ax[1].axhline(0, color="0.3", lw=1); ax[1].set_ylim(0, 0.6)
ax[1].set_ylabel("corr with single-impact peak-|H| pattern")
ax[1].set_title("B. Neither FEM nor MEASURED shapes predict amplitude", fontsize=9, loc="left")
for i, v in enumerate([sp["mean_logamp_corr_FEM"], sp["mean_logamp_corr_measured"]]): ax[1].text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=9)
for a in ax:
    for sp_ in ("top", "right"): a.spines[sp_].set_visible(False)
fig.text(0.5, 0.005, "Whole-FRF magnitude likelihood is locally identifiable (R̂ 104–129, σ_d runaway); the modal peak-FREQUENCY likelihood converges "
         "(R̂ 1.002). But the cross-channel amplitude pattern is ~uncorrelated (0.15) with EITHER shape → amplitude is not modally predictable.",
         ha="center", fontsize=6.4, color="0.4")
fig.tight_layout(rect=[0, 0.04, 1, 1]); fig.savefig(FIG / "fig_roadblock_likelihood.png", dpi=140); plt.close(fig)
print("wrote fig_roadblock_damping, fig_roadblock_remesh, fig_roadblock_likelihood")
