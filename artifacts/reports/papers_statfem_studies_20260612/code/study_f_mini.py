"""Study F-mini — the discrepancy-prior FRONT-END guardrail demo (vision §6.2), forward-only.

Premise: Study G's converged twin UNDER-COVERS held-out QOIs because of LOCAL model error the
calibration could not see. §6.2's front-end says: when the engineer KNOWS a config delta exists
("this panel has local layup/damping variation my 4-quadrant FEM cannot represent"), that knowledge
becomes a DISCREPANCY-PRIOR WIDENING — which must WIDEN the bands (never falsely narrow them).

Demo (no sampler; posterior draws from the converged Study H 'local' arm):
  knob=0  : the as-calibrated predictive (the bands that under-covered).
  knob=1,2: elicited 'unrepresented local variation' delta -> inflate the predictive discrepancy
            sd by x2 / x3 at held-out points (the front-end's structured widening).
Report: held-out QOI coverage vs knob + band width vs knob. The guardrail: coverage may only
IMPROVE with widening; tightening is forbidden without held-out evidence.
Outputs -> ../out/studyF_summary.json + ../figures/figF_frontend.png
"""
from __future__ import annotations
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import run_ums as R

OUT = R.OUT; FIG = os.path.join(os.path.dirname(__file__), "..", "figures")
Z = np.load(os.path.join(OUT, "ums3_H_local.npz"))      # converged unimodal arm
QA_true = R.QA_true
qoiA = Z["qoiA"]                                        # [S,5] as-calibrated predictive samples
med = np.median(qoiA, 0)

knobs = [1.0, 2.0, 3.0]
labels = ["as-calibrated (knob 0)", "delta knob ×2", "delta knob ×3"]
rows = []
for kf in knobs:
    # structured widening: inflate the SPREAD of the predictive about its median by kf
    infl = med[None, :] + (qoiA - med[None, :]) * kf
    lo, hi = np.percentile(infl, [2.5, 97.5], 0)
    cover = [bool(l <= t <= h) for l, t, h in zip(lo, QA_true, hi)]
    rows.append(dict(knob=kf, lo=lo.tolist(), hi=hi.tolist(),
                     cover=cover, n_cover=int(sum(cover)),
                     mean_width=float(np.mean(hi - lo))))
json.dump(dict(rows=rows, truth=QA_true.tolist(),
               guardrail="widening may only INCREASE coverage; tightening requires held-out evidence (vision 6.2)",
               source="posterior draws from converged Study H local arm; forward-only, no sampler"),
          open(os.path.join(OUT, "studyF_summary.json"), "w"), indent=2)

plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 150, "savefig.bbox": "tight",
    "figure.constrained_layout.use": True})
fig, (axa, axb) = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={"width_ratios": [1.4, 1]})
cols = ["#999999", "#1f77b4", "#2a7d2a"]
x = np.arange(5)
for j, (r_, c, lab) in enumerate(zip(rows, cols, labels)):
    off = (j - 1) * 0.18
    for h in range(5):
        axa.plot([h + off, h + off], [r_["lo"][h], r_["hi"][h]], color=c, lw=4, alpha=0.8)
    axa.plot([], [], color=c, lw=4, label=f"{lab}: covers {r_['n_cover']}/5")
for h in range(5):
    axa.plot(h, QA_true[h], "_", color="#222", ms=20, mew=2.4)
axa.set_yscale("log"); axa.set_xticks(x); axa.set_xticklabels([f"hold {i+1}" for i in range(5)], fontsize=8)
axa.set_ylabel("held-out QOI-A (peak |accel|)")
axa.set_title("An elicited config delta WIDENS the bands until they cover (truth = —)")
axa.legend(frameon=False, fontsize=8)
axb.plot([r_["mean_width"] for r_ in rows], [r_["n_cover"] for r_ in rows], "o-", color="#1f77b4")
for r_, lab in zip(rows, labels):
    axb.annotate(lab.split("(")[-1].rstrip(")"), (r_["mean_width"], r_["n_cover"]),
                 textcoords="offset points", xytext=(8, -4), fontsize=8)
axb.set_xlabel("mean band width"); axb.set_ylabel("held-out QOIs covered /5")
axb.set_ylim(-0.3, 5.3); axb.set_title("The trade the dial makes explicit")
fig.suptitle("Study F-mini — the §6.2 front-end guardrail: known config deltas may WIDEN bands, never falsely narrow them",
             fontsize=11)
fig.text(0.01, 0.005, "Study F-mini · SYNTHETIC · forward-only (no sampler) on converged Study-H draws · the dial buys "
         "honesty for free; CONFIDENCE must be earned by held-out evidence (tightening forbidden by construction)",
         fontsize=7.3, color="#777")
fig.savefig(os.path.join(FIG, "figF_frontend.png")); plt.close(fig)
print("Study F-mini:", [(r_["knob"], r_["n_cover"], round(r_["mean_width"], 1)) for r_ in rows])
