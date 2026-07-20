#!/usr/bin/env python3
"""Pseudo-FRF figures, rev-7 FEM vs test (D39/D40). ONE graph = exactly 2
curves (FEM vs test). NO mode comb, no tick marks. Two products:
  (A) tap TRANSFER matrix: 3x3 grid (rows=response location, cols=tap/
      excitation location); diagonal = drive points. Apples-to-apples (tap =
      point force vs FEM transfer accelerance).
  (B) acoustic: 1x3 (per response location); FEM uses a MODELED uniform-
      pressure acoustic forcing on the shield (apples-to-apples forcing).
Tufte: log-freq + log-magnitude (standard FRF view), normalized to own peak.
Also writes each panel as its own PNG in figures/pseudo_frf/.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(WS, "figures")
os.makedirs(os.path.join(FIG, "pseudo_frf"), exist_ok=True)
pf = json.load(open(os.path.join(WS, "out", "pseudo_frf.json")))
LAB = pf["locations_label"]
ORDER = ["interface", "shield_mid", "top_left"]
FLOOR = 2e-3
C_FEM, C_TEST = "#1f78b4", "#e31a1c"

CAV = ("PSEUDO-FRF (no force measured): peak FREQUENCIES comparable, amplitudes "
       "NOT. FEM transfer accelerance, ASSUMED 3% damping, axis=shield-normal/X. "
       "Each curve normalized to its 5-150 Hz peak. Uncalibrated coarse prior. "
       "NO sampler. run mpl_stand_fem_rebuild_20260611 | FABLE")


def clog(y):
    return np.clip(np.array(y), FLOOR, 1.2)


def style(ax):
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(5, 150); ax.set_ylim(FLOOR, 1.3)
    ax.set_xticks([5, 10, 20, 50, 100]); ax.set_xticklabels([5, 10, 20, 50, 100])
    ax.set_yticks([0.01, 0.1, 1.0]); ax.set_yticklabels(["0.01", "0.1", "1"])
    ax.tick_params(length=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def two_curve(ax, curves, ntaps=None):
    c = curves
    ax.plot(c["fem"][0], clog(c["fem"][1]), color=C_FEM, lw=1.2, label="FEM")
    tv = np.array(c["test"][1])
    has = tv.max() > 0 and (ntaps is None or ntaps > 0)
    if has:
        ax.plot(c["test"][0], clog(tv), color=C_TEST, lw=1.0, label="test")
    style(ax)
    return has


# ---------- (A) tap TRANSFER matrix (ragged: engine-beam all rows, foot only
#               interface; foot FEM is grounded under SPC -> model-form gap) ----
COL = ["interface", "shield_mid", "top_left", "engine_beam", "foot"]
fig, axes = plt.subplots(3, 5, figsize=(17, 9.5), sharex=True, sharey=True)
for i, rkey in enumerate(ORDER):
    for j, tkey in enumerate(COL):
        ax = axes[i, j]
        key = f"resp_{rkey}__tap_{tkey}"
        if key not in pf["transfer"]:
            ax.axis("off"); continue
        T = pf["transfer"][key]
        grounded = (tkey == "foot")
        has = two_curve(ax, T["curves"], T["n_taps_used"])
        diag = " (drive pt)" if T["is_drive_point"] else ""
        ax.set_title(f"{LAB[rkey].split()[0]} ← {LAB[tkey].split()[0]}"
                     f"{diag} [{T['n_taps_used']}t]", fontsize=7.5, loc="left")
        if grounded:
            ax.text(0.5, 0.78, "FEM: feet SPC-grounded\n→ no transfer (model-"
                    "form gap)", transform=ax.transAxes, fontsize=6.5,
                    ha="center", color=C_FEM)
        if j == 0:
            ax.set_ylabel(f"resp:\n{LAB[rkey]}", fontsize=8)
        if i == 2:
            ax.set_xlabel("frequency [Hz]")
axes[0, 0].legend(fontsize=8, loc="upper left", frameon=False)
fig.suptitle("Tap TRANSFER pseudo-FRFs: FEM vs test  (rows = accel/response "
             "location, cols = wrench-tap/excitation location; diagonal = drive "
             "point)", fontsize=11)
fig.text(0.005, 0.012, CAV, fontsize=7, color="0.35")
fig.tight_layout(rect=(0, 0.035, 1, 0.965))
fig.savefig(os.path.join(FIG, "fig_pseudo_frf_transfer.png"), dpi=160)
plt.close(fig)

# ---------- (B) acoustic (modeled forcing) ----------
fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
for ax, rkey in zip(axes, ORDER):
    A = pf["acoustic"][rkey]
    two_curve(ax, A["curves"])
    ax.set_title(LAB[rkey], fontsize=10, loc="left")
    ax.set_xlabel("frequency [Hz]")
axes[0].set_ylabel("normalized |FRF|")
axes[0].legend(fontsize=9, loc="upper left", frameon=False)
fig.suptitle("Acoustic pseudo-FRFs: FEM (modeled uniform shield pressure) vs "
             "test (speaker pink-noise), per response location", fontsize=11)
fig.text(0.005, 0.02, "FEM acoustic forcing = UNIFORM in-phase pressure on the "
         "shield (normal-incidence plane wave; valid where wavelength>>panel = "
         "low freq, FLAGGED) -> apples-to-apples forcing. " + CAV,
         fontsize=6.5, color="0.35")
fig.tight_layout(rect=(0, 0.06, 1, 0.94))
fig.savefig(os.path.join(FIG, "fig_pseudo_frf_acoustic.png"), dpi=160)
plt.close(fig)

# ---------- (C) QOI points: valve + box feet ----------
QLAB = {"valve": "Valve (QOI)", "box_foot_left": "Box foot — LEFT (QOI)",
        "box_foot_right": "Box foot — RIGHT (QOI)"}
qkeys = [k for k in ("valve", "box_foot_left", "box_foot_right")
         if k in pf["qoi"]]
fig, axes = plt.subplots(len(qkeys), 2, figsize=(11, 3.4 * len(qkeys)),
                         sharex=False, sharey=True)
for i, qk in enumerate(qkeys):
    Q = pf["qoi"][qk]
    for jc, (tk, fk, clab) in enumerate(
            [("tap_test", "tap_fem", "tap @ engine beam (transfer)"),
             ("ac_test", "ac_fem", "acoustic (FEM=modeled shield pressure)")]):
        ax = axes[i, jc]
        c = Q["curves"]
        ax.plot(c[fk][0], clog(c[fk][1]), color=C_FEM, lw=1.2, label="FEM")
        ax.plot(c[tk][0], clog(c[tk][1]), color=C_TEST, lw=1.0, label="test")
        style(ax)
        if qk == "valve":            # show the ~156/190 Hz frame modes
            ax.set_xlim(5, 250)
            ax.set_xticks([5, 10, 20, 50, 100, 200])
            ax.set_xticklabels([5, 10, 20, 50, 100, 200])
        flag = "  [weak acoustic / low SNR]" if (jc == 1 and
                                                 Q.get("weak_acoustic")) else ""
        ax.set_title(f"{QLAB[qk]} — {clab}{flag}", fontsize=8.5, loc="left")
        if jc == 0:
            ax.set_ylabel("normalized |FRF|", fontsize=8)
        if i == len(qkeys) - 1:
            ax.set_xlabel("frequency [Hz]")
axes[0, 0].legend(fontsize=8, loc="upper left", frameon=False)
fig.suptitle("QOI pseudo-FRFs: FEM mounted-mass models vs test (valve on the "
             "80/20 frame; electronics-box feet)", fontsize=11)
fig.text(0.005, 0.012, "QOI = HELD-OUT records. Box BODY/top NOT measured "
         "(DAQ cable broke) -> box FEET only, both -> rigid-box CONM2 node. "
         "Valve's OWN frame modes ~156/190 Hz are ABOVE this band (this tests "
         "the stand->QOI PATH, not the QOI resonance). " + CAV,
         fontsize=6.5, color="0.35")
fig.tight_layout(rect=(0, 0.04, 1, 0.96))
fig.savefig(os.path.join(FIG, "fig_pseudo_frf_qoi.png"), dpi=160)
plt.close(fig)

# keep the canonical name pointing at the transfer matrix (for image_qa)
import shutil
shutil.copy(os.path.join(FIG, "fig_pseudo_frf_transfer.png"),
            os.path.join(FIG, "fig_pseudo_frf.png"))

# ---------- individual PNGs ----------
for key, T in pf["transfer"].items():
    f1, a1 = plt.subplots(figsize=(6, 3.9))
    two_curve(a1, T["curves"], T["n_taps_used"])
    a1.legend(fontsize=9, loc="upper left", frameon=False)
    a1.set_xlabel("frequency [Hz]"); a1.set_ylabel("normalized |FRF|")
    a1.set_title(f"resp {LAB[T['resp']]} ← tap {LAB[T['tap_loc']]}", fontsize=9)
    f1.text(0.005, 0.01, CAV, fontsize=6, color="0.4")
    f1.tight_layout(rect=(0, 0.06, 1, 1))
    f1.savefig(os.path.join(FIG, "pseudo_frf", f"transfer_{key}.png"), dpi=150)
    plt.close(f1)
for rkey, A in pf["acoustic"].items():
    f1, a1 = plt.subplots(figsize=(6, 3.9))
    two_curve(a1, A["curves"])
    a1.legend(fontsize=9, loc="upper left", frameon=False)
    a1.set_xlabel("frequency [Hz]"); a1.set_ylabel("normalized |FRF|")
    a1.set_title(f"{LAB[rkey]} — acoustic (FEM modeled shield pressure)",
                 fontsize=9)
    f1.text(0.005, 0.01, CAV, fontsize=6, color="0.4")
    f1.tight_layout(rect=(0, 0.06, 1, 1))
    f1.savefig(os.path.join(FIG, "pseudo_frf", f"acoustic_{rkey}.png"), dpi=150)
    plt.close(f1)

print("wrote fig_pseudo_frf_transfer.png (3x3), fig_pseudo_frf_acoustic.png "
      "(1x3), + individuals in figures/pseudo_frf/")
