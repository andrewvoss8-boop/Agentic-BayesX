#!/usr/bin/env python3
"""Finalize the deterministic tuning (D42/D43): compute baseline vs final-tuned
box-foot pseudo-FRFs, scores, held-out, and a before/after figure. The final
config keeps box mass at its prior nominal (3 lb) and is physically plausible
(softer box standoffs + spot welds; box mount split into separate translational
and rotational springs = the D43 model-form change that added the ~27 Hz box
rocking mode). NO sampler; deterministic POINT estimate.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sys

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WS, "src"))
import tune_correlation as T

BASE = dict(T.NOM)
FINAL = dict(T.NOM)
FINAL.update({"K_shield_att": 0.3, "K_att_ebox": 0.3, "K_att_ebox_rot": 3.0,
              "M_m_ebox": 1.0})   # box mass stays 3 lb (prior nominal)


def curve(scal, out_key, in_key):
    fr, Phi = T.solve(scal)
    po, pi = Phi[T.MROW[out_key]], Phi[T.MROW[in_key]]
    f = np.linspace(2, 110, 3000)
    w = 2 * np.pi * f
    wr = 2 * np.pi * np.maximum(fr, 1e-6)
    H = np.zeros(w.size, complex)
    for r in range(fr.size):
        if fr[r] >= 1.0:
            H += po[r] * pi[r] / (wr[r] ** 2 - w ** 2 + 2j * T.ZETA * wr[r] * w)
    y = np.abs(-w ** 2 * H)
    m = (f >= 5) & (f <= 90)
    return f, y / y[m].max(), T.transfer_peaks(fr, Phi, out_key, in_key)


fb, yb, pkb = curve(BASE, "box", "engine_beam")
ff, yf, pkf = curve(FINAL, "box", "engine_beam")
sb = T.match_score(T.TARGETS, pkb)
sf = T.match_score(T.TARGETS, pkf)
ho_b, ho_f = T.heldout_score(BASE), T.heldout_score(FINAL)

# test box-foot curves (avg of L/R normalized)
pf = json.load(open(os.path.join(WS, "out", "pseudo_frf.json")))
res = dict(
    targets_hz=T.TARGETS,
    baseline=dict(median=round(sb[0], 2), max=round(sb[1], 2), matched=sb[2],
                  heldout=round(ho_b, 2), fem_peaks=[round(p, 1) for p in pkb]),
    final=dict(median=round(sf[0], 2), max=round(sf[1], 2), matched=sf[2],
               heldout=round(ho_f, 2), fem_peaks=[round(p, 1) for p in pkf],
               scalars={k: v for k, v in FINAL.items() if v != 1.0}),
    goal=dict(median_le_3="MET" if sf[0] <= 3 else "not met",
              full_max6_and_4of4="not met (11.4 Hz model-form floor)"),
    model_form_change="D43: split box mount into separate translational + "
                      "rotational springs (added the ~27 Hz box rocking mode)",
    residual="lowest peak 11.4 Hz (shield/box fundamental) remains ~+17% high "
             "in FEM; closing it needs non-physical params (box>4 lb above "
             "prior, or softening the confirmed 1.7mm shield) -> DECLINED as "
             "overfitting; honest model-form error for the Bayesian/robust "
             "next card to absorb as discrepancy.",
    note="DETERMINISTIC point estimate. Tuning used ONLY box-foot tap-transfer; "
         "stand transfer held out (did not degrade: %.1f%% -> %.1f%%)."
         % (ho_b, ho_f))
json.dump(res, open(os.path.join(WS, "out", "tuning_result.json"), "w"),
          indent=1)

# ---- before/after figure: 2 panels (baseline vs test, tuned vs test) ----
box_test = None
for key in ("box_foot_left", "box_foot_right"):
    c = pf["qoi"][key]["curves"]["tap_test"]
    fx, fy = np.array(c[0]), np.array(c[1])
    box_test = (fx, fy) if box_test is None else (box_test[0],
               box_test[1] + np.interp(box_test[0], fx, fy))
btf, bty = box_test[0], box_test[1] / 2.0

fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
for ax, (lab, f, y, pk, s, ho) in zip(axes, [
        ("BEFORE (rev-7 prior)", fb, yb, pkb, sb, ho_b),
        ("AFTER (tuned, D42/D43)", ff, yf, pkf, sf, ho_f)]):
    ax.plot(f, np.clip(y, 2e-3, 1.2), color="#1f78b4", lw=1.3, label="FEM")
    ax.plot(btf, np.clip(bty, 2e-3, 1.2), color="#e31a1c", lw=1.0, label="test")
    for t in T.TARGETS:
        ax.axvline(t, color="0.7", ls=":", lw=0.8)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(5, 90); ax.set_ylim(2e-3, 1.3)
    ax.set_xticks([5, 10, 20, 50, 90]); ax.set_xticklabels([5, 10, 20, 50, 90])
    ax.tick_params(length=0)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_title(f"{lab}\nbox-foot median |Δf|={s[0]:.1f}%  matched {s[2]}/4  "
                 f"held-out {ho:.1f}%", fontsize=9, loc="left")
    ax.set_xlabel("frequency [Hz]")
axes[0].set_ylabel("normalized |FRF|")
axes[0].legend(fontsize=9, loc="upper left", frameon=False)
fig.suptitle("Deterministic model updating: box-foot tap-transfer, FEM vs test "
             "(dotted = target peaks). NO force/sampler; peak freqs only.",
             fontsize=11)
fig.text(0.005, 0.015, "Tuned ONLY on box-foot tap-transfer (held-out stand "
         "transfer did not degrade). Final = softer welds (x0.3) + softer box "
         "translational mount (x0.3) + stiffer rotational (x3, D43 split mount "
         "-> adds the ~27 Hz rocking peak); box mass kept at 3 lb (prior). "
         "11.4 Hz peak = documented model-form floor (NOT overfit). FABLE",
         fontsize=6.5, color="0.35")
fig.tight_layout(rect=(0, 0.05, 1, 0.93))
fig.savefig(os.path.join(WS, "figures", "fig_tuning_box_foot.png"), dpi=160)
plt.close(fig)

print("BEFORE box-foot: median %.2f%% max %.2f%% n%d; held-out %.2f%%"
      % (sb[0], sb[1], sb[2], ho_b))
print("AFTER  box-foot: median %.2f%% max %.2f%% n%d; held-out %.2f%%"
      % (sf[0], sf[1], sf[2], ho_f))
print("FEM peaks before:", [round(p, 1) for p in pkb])
print("FEM peaks after: ", [round(p, 1) for p in pkf])
print("wrote out/tuning_result.json + figures/fig_tuning_box_foot.png")
