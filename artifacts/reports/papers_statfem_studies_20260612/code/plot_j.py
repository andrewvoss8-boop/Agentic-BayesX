"""figJ — Study J REAL-panel UMS calibration. .venv_fem_phase1."""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FIG = os.path.join(ROOT, "figures"); OUT = os.path.join(ROOT, "out")
S = json.load(open(os.path.join(OUT, "studyj_summary.json")))
A = np.load(os.path.join(OUT, "studyj_arrays.npz"))
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150, "savefig.bbox": "tight",
    "figure.constrained_layout.use": True})
C_D = "#d62728"; C_U = "#1f77b4"; C_T = "#222"
FB = A["FB"]; YOBS = A["YOBS"]; HOLD = list(A["HOLD"]); PTS = A["PTS"]; DRIVE = int(A["DRIVE"])
mag = A["magpred"]                                # [S,5,nf]
hq = S["held_out_qoi"]

fig, (ax, axq, axm) = plt.subplots(1, 3, figsize=(13.5, 4.2), gridspec_kw={"width_ratios": [2, 1, 0.9]})
# (a) held-out mobility prediction at the first held-out point
h0 = 0
lo, md, hi = np.percentile(mag[:, h0, :], [2.5, 50, 97.5], 0)
ax.fill_between(FB, lo, hi, color=C_U, alpha=0.3, label="UMS 95% predictive")
ax.plot(FB, md, color=C_U, lw=1)
ax.plot(FB, np.abs(YOBS[HOLD[h0]]), color=C_D, lw=1.1, label="REAL held-out mobility")
ax.set_yscale("log"); ax.set_xlabel("frequency [Hz]"); ax.set_ylabel("|mobility| [(m/s)/N]")
ax.set_title(f"REAL held-out point {HOLD[h0]} (never fit) — prediction vs measurement")
ax.legend(frameon=False, fontsize=8)
linecov = float(np.mean((np.abs(YOBS[HOLD[h0]]) >= lo) & (np.abs(YOBS[HOLD[h0]]) <= hi)))
conv = S["convergence"]
ax.text(0.02, 0.97, f"line coverage {linecov*100:.0f}% · R-hat {conv['max_rhat']:.2f} · ESS {conv['min_ess']:.0f} · div {conv['divergences']}",
        transform=ax.transAxes, fontsize=8.5, va="top", bbox=dict(boxstyle="round", fc="white", ec="#ccc"))
# (b) held-out QOI vs measured truth, all 5
x = np.arange(5); tA = np.array(hq["truth"])
for h in range(5):
    ax2lo, ax2hi = hq["lo"][h], hq["hi"][h]
    axq.plot([h, h], [ax2lo, ax2hi], color=C_U, lw=4, alpha=0.75)
    axq.plot(h, hq["med"][h], "o", ms=4, color=C_U)
    axq.plot(h, tA[h], "_", color=C_D, ms=18, mew=2.4)
axq.set_yscale("log"); axq.set_xticks(x); axq.set_xticklabels([f"p{p}" for p in HOLD], fontsize=8)
axq.set_ylabel("peak |mobility|"); axq.set_title(f"Held-out QOI: covered {hq['n_cover']}/5")
axq.legend(handles=[plt.Line2D([0],[0],color=C_U,lw=4,label="UMS 95%"),
                    plt.Line2D([0],[0],color=C_D,lw=2,label="REAL measured")], frameon=False, fontsize=8)
# (c) scan map
axm.scatter(PTS[:, 1], PTS[:, 0], s=30, color="#ccc")
axm.scatter(PTS[[p for p in range(25) if p not in HOLD], 1], PTS[[p for p in range(25) if p not in HOLD], 0], s=30, color=C_U, label="observed")
axm.scatter(PTS[HOLD, 1], PTS[HOLD, 0], s=55, marker="s", fc="none", ec=C_D, lw=1.6, label="held out")
axm.scatter([PTS[DRIVE, 1]], [PTS[DRIVE, 0]], s=90, marker="*", color="#d6a700", label="impact (drive)")
axm.set_xticks([]); axm.set_yticks([]); axm.set_title("25-pt LDV grid", fontsize=9)
axm.legend(frameon=False, fontsize=7, loc="lower center")
fig.suptitle("Study J — REAL suspended-panel UMS calibration (FEA shapes + calibrated modal freqs + Schneider discrepancy)",
             fontsize=11)
fig.text(0.01, 0.005, "Study J · REAL DATA (H1.mat mobility) · physics = Abaqus FEA modes · held-out = 5 never-fit LDV points · "
         "FIRST real-data calibration (single impact reference; C2 margin-scan mapping; one test/realization)",
         fontsize=7, color="#777")
fig.savefig(os.path.join(FIG, "figJ_real_calibration.png")); plt.close(fig)
print("figJ written; held-out QOI", hq["n_cover"], "/5")
