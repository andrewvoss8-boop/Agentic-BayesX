"""figL — Study L real-data A/B: does per-mode residue-amplitude calibration SHARPEN the Study-K bands? .venv_nuts."""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FIG = os.path.join(ROOT, "figures"); OUT = os.path.join(ROOT, "out")
L = json.load(open(os.path.join(OUT, "studyl_summary.json")))
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150, "savefig.bbox": "tight",
    "figure.constrained_layout.use": True})
CF = "#1f77b4"; CA = "#9467bd"; CT = "#d62728"
fo = L["arms"]["L_freqonly"]; fa = L["arms"]["L_freqamp"]
tA = np.array(fo["qoi"]["truth"])
fa_conv = fa["max_rhat"] <= 1.05

fig, (axa, axb) = plt.subplots(1, 2, figsize=(12, 4.4), gridspec_kw={"width_ratios": [1.25, 1.0]})
# (a) held-out QOI: freq-only (converged 5/5) vs freq+amp (NON-CONVERGED -> not trustworthy)
x = np.arange(5)
lo = np.array(fo["qoi"]["lo"]); hi = np.array(fo["qoi"]["hi"]); md = np.array(fo["qoi"]["med"])
for h in range(5):
    axa.plot([h - 0.16, h - 0.16], [lo[h], hi[h]], color=CF, lw=4, alpha=0.85)
    axa.plot(h - 0.16, md[h], "o", ms=4, color=CF)
loa = np.array(fa["qoi"]["lo"]); hia = np.array(fa["qoi"]["hi"]); mda = np.array(fa["qoi"]["med"])
for h in range(5):                                   # freq+amp drawn hatched/faded = NOT trustworthy
    axa.plot([h + 0.16, h + 0.16], [loa[h], hia[h]], color=CA, lw=4, alpha=0.30, ls=":")
    axa.plot(h + 0.16, mda[h], "x", ms=5, color=CA, alpha=0.5)
for h in range(5):
    axa.plot(h, tA[h], "_", color=CT, ms=20, mew=2.4)
axa.set_yscale("log"); axa.set_xticks(x); axa.set_xticklabels([f"p{p}" for p in range(5)], fontsize=8)
axa.set_ylabel("held-out peak |mobility|  (m/s)/N")
axa.set_title("REAL held-out QOI", fontsize=10)
axa.legend(handles=[plt.Line2D([0],[0],color=CF,lw=4,label=f"freq-only: CONVERGED, {fo['qoi']['n_cover']}/5 (R-hat {fo['max_rhat']:.2f})"),
                    plt.Line2D([0],[0],color=CA,lw=4,alpha=0.4,ls=":",label=f"freq+amp: NON-CONVERGED (R-hat {fa['max_rhat']:.1f}) — not trustworthy"),
                    plt.Line2D([0],[0],color=CT,lw=2,label="REAL measured")], frameon=False, fontsize=8, loc="lower right")

# (b) THE finding: adding per-mode amplitude breaks convergence (the amplitude ridge)
rh = [fo["max_rhat"], fa["max_rhat"]]
axb.bar([0, 1], rh, color=[CF, CA])
axb.axhline(1.05, color="#d62728", ls="--", lw=1.2); axb.text(1.5, 1.05, "1.05 gate", color="#d62728", fontsize=7, va="bottom", ha="right")
axb.set_yscale("log"); axb.set_ylabel("max R-hat (log scale; lower=mixed)")
axb.set_xticks([0, 1]); axb.set_xticklabels(["freq-only\n(per-mode freq)", "freq+amp\n(+per-mode amplitude)"], fontsize=8)
axb.set_title("Adding per-mode amplitude breaks identifiability\n(the amplitude↔damping ridge, D30/D35)", fontsize=9.5)
for i, v in enumerate(rh):
    axb.text(i, v * 1.08, f"{v:.2f}", ha="center", fontsize=9, fontweight="bold")

fig.suptitle("Study L — REAL panel: can per-mode amplitude calibration SHARPEN the Study-K 5/5 bands?  NO.", fontsize=11.5)
fig.text(0.01, -0.02, "Study L · REAL DATA · 4-chain gate · per-mode FREQUENCY is identifiable (each sharp peak pins one frequency) so it stays 5/5; "
         "per-mode AMPLITUDE is NOT identifiable from a single impact reference — it reintroduces the amplitude↔damping ridge (R-hat 14.8). "
         f"The ~4-5x band width is the honest SINGLE-REFERENCE limit; sharper bands need multi-reference data, not a fancier model.", fontsize=7, color="#777")
fig.savefig(os.path.join(FIG, "figL_sharpen_ab.png")); plt.close(fig)
print("figL written:", L["verdict"])
