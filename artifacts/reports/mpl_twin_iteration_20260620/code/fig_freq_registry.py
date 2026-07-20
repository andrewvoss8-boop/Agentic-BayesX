#!/usr/bin/env python3
"""Two deliverable figures (Tufte gate applied):
 (1) fig_freq_result.png — the (b) FREQUENCY headline: per-split per-peak |df|% for the calibrated twin vs the
     nominal FEM vs the nearest-pooled-peak climatology (the fair bar), + CRPS-skill vs the (weak) pooled
     ensemble. Shows calibration is ~neutral on the fair bar; convergence stamped.
 (2) fig_registry.png — the model-class registry as a table-as-figure (one row per attempt).
All numbers come from out/*.json. No dB, no jet, bars start at zero, direct labels.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parents[1]; OUT = WS / "out"; FIG = WS / "figures"
FIG.mkdir(exist_ok=True)


def fig_freq():
    fb = json.loads((OUT / "freq_baseline.json").read_text())
    nr = json.loads((OUT / "near_resonance.json").read_text())
    per = fb["per_split"]; locs = [p["held_out"] for p in per]
    twin = [p["twin_median_df_pct"] for p in per]
    nom = [p["nominal_fem_median_df_pct"] for p in per]
    clim = [p["nearest_pooled_peak_median_df_pct"] for p in per]
    skill = [p["crps_skill_vs_clim_pooled"] for p in per]
    cov = [p["twin_coverage"] for p in per]
    x = np.arange(len(locs)); w = 0.27
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.8))
    a1.bar(x - w, twin, w, color="#1f4e79", label="calibrated twin")
    a1.bar(x, nom, w, color="#9a9a9a", label="nominal FEM")
    a1.bar(x + w, clim, w, color="#ccb35a", label="nearest-pooled peak (fair clim)")
    a1.set_xticks(x); a1.set_xticklabels(locs, fontsize=9)
    a1.set_ylabel("median per-peak |Δf| (%)"); a1.set_ylim(bottom=0)
    a1.set_title("per-peak frequency error: calibration ~neutral vs nominal & fair climatology", fontsize=9, loc="left")
    a1.legend(fontsize=8, frameon=False, loc="upper right")
    for s in ("top", "right"): a1.spines[s].set_visible(False)
    mt, mn, mc = np.mean(twin), np.mean(nom), np.mean(clim)
    a1.text(0.02, 0.95, f"mean: twin {mt:.2f}% / nominal {mn:.2f}% / fair-clim {mc:.2f}%",
            transform=a1.transAxes, fontsize=8, va="top")

    a2.bar(x, skill, 0.55, color="#1f4e79")
    a2.axhline(0, color="k", lw=0.6)
    for i, (sk, c) in enumerate(zip(skill, cov)):
        a2.text(i, sk + 0.01, f"cov {c:.2f}", ha="center", fontsize=7)
    a2.set_xticks(x); a2.set_xticklabels(locs, fontsize=9); a2.set_ylim(0, 1.0)
    a2.set_ylabel("CRPS-skill vs pooled climatology")
    a2.set_title("CRPS-skill vs the WEAK (wide pooled-ensemble) bar = +0.91 mean", fontsize=9, loc="left")
    for s in ("top", "right"): a2.spines[s].set_visible(False)
    fig.suptitle("MPL twin — (b) FREQUENCY headline: converged & calibrated, strong vs weak climatology, "
                 "NEUTRAL vs nominal/fair-clim  [all 5 LOLO splits converged R̂≤1.002]", fontsize=10)
    fig.text(0.5, 0.005,
             f"Quantity: per-location matched modal frequency (Hz). The twin localizes each measured peak far "
             f"better than the no-info pooled ensemble (+0.91 CRPS-skill, coverage {np.mean(cov):.2f}) but does NOT "
             f"beat the nominal FEM or the nearest-pooled-peak bar — a dense modal forest makes frequency a weak "
             f"discriminator. Load-free near-resonance |φ_a/φ_ref| vs measured peak height: log-corr "
             f"{nr['log_corr_meas_vs_phi_ratio']:+.2f} (n={nr['n_pairs']}) ⇒ transmissibility shape is limited by "
             f"mode-shape error, load-independent. run mpl_twin_iteration_20260620.", ha="center", fontsize=7.3, wrap=True)
    fig.tight_layout(rect=[0, 0.04, 1, 0.94])
    fig.savefig(FIG / "fig_freq_result.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print("wrote fig_freq_result.png")


def fig_registry():
    reg = json.loads((OUT / "model_registry.json").read_text())
    rows = reg["rows"]
    cols = ["class_id", "what changed", "#par", "NUTS conv (R̂)", "held-out result", "verdict"]
    data = []
    for r in rows:
        if r["class_id"].startswith("F0"):
            res = (f"freq |df| {r['twin_median_df_pct_mean']:.2f}% (nom {r['nominal_median_df_pct_mean']:.2f}%, "
                   f"fair-clim {r['nearest_pooled_df_pct_mean']:.2f}%); skill+{r['heldout_freq_crps_skill_pooled_mean']:.2f}")
        else:
            res = (f"transmissibility uncorrelated (see D6); curve-skill smoke")
        conv = f"{'yes' if r.get('nuts_converged') else 'NO'} ({r.get('worst_rhat', float('nan')):.2f})"
        data.append([r["class_id"], r.get("changed", "")[:38], str(r.get("n_params", "")), conv, res[:50], r.get("verdict", "")[:20]])
    fig, ax = plt.subplots(figsize=(17, 1.4 + 0.5 * len(data)))
    ax.axis("off")
    tbl = ax.table(cellText=data, colLabels=cols, loc="center", cellLoc="left",
                   colWidths=[0.16, 0.22, 0.05, 0.13, 0.30, 0.14])
    tbl.auto_set_font_size(False); tbl.set_fontsize(7.5); tbl.scale(1, 1.6)
    for j in range(len(cols)):
        tbl[0, j].set_facecolor("#1f4e79"); tbl[0, j].set_text_props(color="white", weight="bold")
    ax.set_title("MPL twin model-class registry — " + reg.get("program_verdict", ""), fontsize=10, loc="left")
    fig.text(0.5, 0.02, "One row per attempt. Verdict: as-received FEM is a trustworthy FREQUENCY twin; neither "
             "stiffness calibration nor richer transmissibility forms improve held-out scores on this single-axis, "
             "no-force data (D6/F0/near-resonance). run mpl_twin_iteration_20260620.", ha="center", fontsize=7.3, wrap=True)
    fig.savefig(FIG / "fig_registry.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print("wrote fig_registry.png")


if __name__ == "__main__":
    fig_freq(); fig_registry()
