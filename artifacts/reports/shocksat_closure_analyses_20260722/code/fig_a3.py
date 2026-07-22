#!/usr/bin/env python3
"""A3 figures: (1) calibration + CRPS table figure; (2) coverage-vs-width plot.
Evidence separation printed ON both figures: shear = measured held-out; normal_Z = synthetic
self-consistency, NOT validation."""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
a3 = json.load(open(os.path.join(WS, "out", "a3_calibration_table.json")))
rec = a3["known_answer_gate"]["recomputed_scorecard"]
crps_s = a3["crps"]["scorecard_grid"]
agg = a3["crps"]["measured_aggregate_strong_drives"]

METHODS = [("baseline_fem+6dB", "FEM+6 dB (incumbent)"),
           ("L5_theta_only", "parameter-only (θ)"),
           ("statfem_Fk", "statFEM F(k) (delivered)")]
AXES = ["shear_X", "shear_Y", "normal_Z"]

# ---------- figure 1: table ----------
fig, ax = plt.subplots(figsize=(12.5, 4.6))
ax.axis("off")
col_labels = ["method",
              "shear_X\ncov / width", "shear_X CRPS\n(MEASURED drives)",
              "shear_Y\ncov / width", "shear_Y CRPS\n(MEASURED drives)",
              "normal_Z\ncov / width", "normal_Z CRPS (SYNTHETIC:\nself-consistency,\nNOT validation)"]
crps_key = {"baseline_fem+6dB": "fem6db_log_uniform_primary",
            "L5_theta_only": "L5_theta_only_param_only", "statfem_Fk": "statfem_Fk"}
rows = []
for mkey, mname in METHODS:
    r = [mname]
    for axname in AXES:
        cell = rec[axname][mkey]
        r.append(f"{cell['weighted_coverage']:.3f} / {cell['sharpness_band_grms_ratio_vs_fem6db']:.3f}×")
        if axname == "normal_Z":
            r.append(f"{crps_s['normal_Z_scorecard_grid'][crps_key[mkey]]:.0f}")
        else:
            r.append(f"{agg[axname][crps_key[mkey]]:.3f}")
    rows.append(r)
tbl = ax.table(cellText=rows, colLabels=col_labels, loc="center", cellLoc="center")
tbl.auto_set_font_size(False)
tbl.set_fontsize(9)
tbl.auto_set_column_width(list(range(len(col_labels))))
tbl.scale(1.0, 2.1)
for j in range(len(col_labels)):
    tbl[0, j].set_text_props(weight="bold")
    tbl[0, j].set_height(0.30)
# bold the best CRPS per axis column
for cidx, axname in [(2, "shear_X"), (4, "shear_Y"), (6, "normal_Z")]:
    vals = [float(rows[i][cidx].replace("×", "")) for i in range(3)]
    tbl[1 + int(np.argmin(vals)), cidx].set_text_props(weight="bold")
ax.set_title("Calibration + proper score: statFEM vs FEM+6 dB incumbent (net-CG force bands)\n"
             "coverage target 0.95 · width = band-GRMS ratio vs FEM+6 dB · CRPS lower = better "
             "(log-uniform envelope convention; statFEM wins 8/10 measured drive-axis cells under all 3 conventions)",
             fontsize=10, loc="left")
ax.text(0.0, 0.02,
        "Shear CRPS = measured held-out drive answer keys (5 drives, strong-observability mean). "
        "normal_Z = synthetic truth ensemble — self-consistency, NOT validation.\n"
        "normal_Z widths: 2.526× delivered reference; 2.958× tier-updated configuration (observed "
        "cross-drive scatter 1.393 > assumed 0.80 for the one matched extended-band mode).\n"
        "Source runs: shocksat_netcg_method_selection_20260701 (reproduced exactly, max|dev|=0.000) "
        "+ this study out/a3_calibration_table.json.",
        transform=ax.transAxes, fontsize=8, va="bottom", color="0.25")
fig.tight_layout()
p1 = os.path.join(WS, "figures", "a3_table.png")
fig.savefig(p1, dpi=200, bbox_inches="tight")
print("wrote", p1)

# ---------- figure 2: coverage vs width ----------
fig2, axs = plt.subplots(1, 3, figsize=(11.5, 3.9), sharey=True)
mk = {"baseline_fem+6dB": ("s", "0.15"), "L5_theta_only": ("^", "#1f77b4"), "statfem_Fk": ("o", "#d62728")}
for ax2, axname in zip(axs, AXES):
    for mkey, mname in METHODS:
        cell = rec[axname][mkey]
        m, c = mk[mkey]
        ax2.scatter(cell["sharpness_band_grms_ratio_vs_fem6db"], cell["weighted_coverage"],
                    marker=m, s=55, color=c, zorder=3)
        dy = -0.045 if mkey == "baseline_fem+6dB" else 0.02
        ax2.annotate(mname.split(" (")[0], (cell["sharpness_band_grms_ratio_vs_fem6db"],
                                            cell["weighted_coverage"]),
                     textcoords="offset points", xytext=(6, -12 if mkey == "baseline_fem+6dB" else 6),
                     fontsize=8, color=c)
    ax2.axhline(0.95, color="0.6", lw=0.8, ls="--")
    ax2.set_xlim(0.6, 3.4)
    ax2.set_ylim(0.63, 1.03)
    ax2.set_xlabel("band width ratio vs FEM+6 dB")
    title = axname + ("  [SYNTHETIC: self-consistency,\nNOT validation]" if axname == "normal_Z"
                      else "  [measured held-out drives back\nthe coverage answer key]")
    ax2.set_title(title, fontsize=9, loc="left")
    ax2.spines[["top", "right"]].set_visible(False)
axs[0].set_ylabel("energy-weighted coverage")
axs[0].text(0.62, 0.955, "0.95 target", fontsize=8, color="0.4", va="bottom")
fig2.suptitle("Coverage vs width: the incumbent is narrow but leaks (cov 0.71–0.87); statFEM covers at 1.5–2.5×",
              fontsize=10.5, x=0.01, ha="left")
fig2.tight_layout(rect=(0, 0, 1, 0.93))
p2 = os.path.join(WS, "figures", "a3_coverage_width.png")
fig2.savefig(p2, dpi=200)
print("wrote", p2)

cap1 = ("Calibration table: energy-weighted coverage / band-width ratio (both reproduced exactly from the "
        "frozen bake-off, max|dev|=0.000) plus fair-ensemble CRPS (lower better; log-uniform envelope "
        "convention, conclusion stable under all 3 conventions: statFEM wins 8/10 measured drive-axis cells). "
        "Shear CRPS = MEASURED held-out drives; normal_Z = synthetic self-consistency, NOT validation; "
        "normal-Z widths 2.526 (delivered reference) vs 2.958 (tier-updated). Source run: "
        "shocksat_netcg_method_selection_20260701 + out/a3_calibration_table.json.")
cap2 = ("Coverage vs width per axis. FEM+6 dB undercovers (0.865/0.706/0.738 vs 0.95 target); the delivered "
        "statFEM band covers (0.98–0.99) at 1.508–2.526x width; parameter-only propagation is sharp but "
        "undercovers shear_Y. normal_Z panel is synthetic self-consistency, NOT validation (label on panel). "
        "Source run: shocksat_netcg_method_selection_20260701, reproduced in out/a3_calibration_table.json.")
mf_p = os.path.join(WS, "out", "fig_manifest.json")
mf = json.load(open(mf_p)) if os.path.exists(mf_p) else {"figures": []}
mf["figures"] = [f for f in mf["figures"] if f["path"] not in ("figures/a3_table.png", "figures/a3_coverage_width.png")]
mf["figures"] += [{"path": "figures/a3_table.png", "caption": cap1},
                  {"path": "figures/a3_coverage_width.png", "caption": cap2}]
json.dump(mf, open(mf_p, "w"), indent=1)
