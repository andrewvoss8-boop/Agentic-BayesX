"""figK — Study K real-data global-vs-per-mode frequency-calibration A/B. .venv_fem_phase1."""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FIG = os.path.join(ROOT, "figures"); OUT = os.path.join(ROOT, "out")
K = json.load(open(os.path.join(OUT, "studyk_summary.json")))
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150, "savefig.bbox": "tight",
    "figure.constrained_layout.use": True})
CG = "#7f7f7f"; CP = "#1f77b4"; CT = "#d62728"
g = K["arms"]["K_global"]; pm = K["arms"]["K_permode"]
tA = np.array(g["qoi"]["truth"]); fea = np.array(K["fea_freqs"]); exp = np.array(K["exp_peaks"])

fig, (axa, axb) = plt.subplots(1, 2, figsize=(12, 4.4), gridspec_kw={"width_ratios": [1.1, 1.2]})
# (a) held-out QOI: global vs per-mode vs truth
x = np.arange(5)
for off, a, c, lab in ((-0.16, g, CG, f"global (R-hat {g['max_rhat']:.2f})"),
                       (0.16, pm, CP, f"per-mode (R-hat {pm['max_rhat']:.2f})")):
    lo = np.array(a["qoi"]["lo"]); hi = np.array(a["qoi"]["hi"]); md = np.array(a["qoi"]["med"])
    for h in range(5):
        axa.plot([h + off, h + off], [lo[h], hi[h]], color=c, lw=4, alpha=0.8)
        axa.plot(h + off, md[h], "o", ms=4, color=c)
for h in range(5):
    axa.plot(h, tA[h], "_", color=CT, ms=20, mew=2.4)
axa.set_yscale("log"); axa.set_xticks(x); axa.set_xticklabels([f"p{p}" for p in range(5)], fontsize=8)
axa.set_ylabel("held-out peak |mobility|")
axa.set_title(f"REAL held-out QOI: global {g['qoi']['n_cover']}/5 vs per-mode {pm['qoi']['n_cover']}/5")
axa.legend(handles=[plt.Line2D([0],[0],color=CG,lw=4,label=f"global ({g['qoi']['n_cover']}/5)"),
                    plt.Line2D([0],[0],color=CP,lw=4,label=f"per-mode ({pm['qoi']['n_cover']}/5)"),
                    plt.Line2D([0],[0],color=CT,lw=2,label="REAL measured")], frameon=False, fontsize=8)
# (b) calibrated vs experimental frequencies
calf = np.array(pm.get("cal_freqs", fea))
axb.plot(fea, "o-", color=CG, ms=5, label="FEA (nominal)")
axb.plot(calf, "s-", color=CP, ms=5, label="per-mode calibrated")
# nearest experimental peak per mode
for i, f in enumerate(calf):
    j = int(np.argmin(np.abs(exp - f)))
    axb.plot(i, exp[j], "x", color=CT, ms=8)
axb.set_xlabel("mode index"); axb.set_ylabel("frequency [Hz]")
axb.set_title("Per-mode frequency calibration vs experimental peaks (×)")
axb.legend(frameon=False, fontsize=8)
fig.suptitle("Study K — REAL-panel A/B: does per-mode frequency calibration improve held-out coverage?",
             fontsize=11.5)
verdict = ("per-mode HELPS" if pm["qoi"]["n_cover"] > g["qoi"]["n_cover"]
           else ("no improvement — the limit is shapes/discrepancy, not frequency" if pm["qoi"]["n_cover"] == g["qoi"]["n_cover"]
                 else "per-mode HURTS (overfits)"))
fig.text(0.01, 0.005, f"Study K · REAL DATA · amplitude fixed · verdict: {verdict} · global {g['qoi']['n_cover']}/5 → per-mode {pm['qoi']['n_cover']}/5",
         fontsize=7.5, color="#777")
fig.savefig(os.path.join(FIG, "figK_permode_ab.png")); plt.close(fig)
print(f"figK written: global {g['qoi']['n_cover']}/5 vs per-mode {pm['qoi']['n_cover']}/5")
