#!/usr/bin/env python3
"""Figures for the composite bake-off (Tufte checklist applied; every figure states run/dataset + convergence).
fig_matrix_money.png  — the full-matrix money figure: R2 sharpness per QOI vs the proven bars + hard-gate/R3
                        status; R1 CRPS-skill + sigma vs the pinned bounds; R3 widen ratios.
fig_evidence.png      — shape-inclusive evidence per class across prior widths + freq-only reference column.
fig_funnel.png        — remodeling funnel: tier-1 score distribution (151) -> tier-2 (full) -> tier-3 winner.
fig_heldout_drives.png— per-drive held-out coverage (5 folds) per arm, shear X/Y.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; FIG.mkdir(exist_ok=True)
ARMS = ["M0S0", "M0S1", "M0S2", "M1S0", "M1S1", "M1S2"]
QOIS = ["shear_X", "shear_Y", "normal_Z"]
BARS = {"shear_X": 1.508, "shear_Y": 2.301, "normal_Z": 2.526}
CB = {"M0": "#7a7a7a", "M1": "#1f4e79"}


def arm_color(a):
    return CB[a[:2]]


def main():
    sc = json.loads((WS / "out" / "matrix_scorecard.json").read_text())
    ev = json.loads((WS / "out" / "tier3_evidence.json").read_text())
    t1 = json.loads((WS / "out" / "tier1_screen.json").read_text())["scores"]
    t2 = json.loads((WS / "out" / "tier2_full.json").read_text())["results"]
    arms = sc["arms"]
    conv_note = "; ".join(f"{a}:{'conv' if arms[a]['nuts_diag']['converged'] else 'NOT-CONV R'+str(arms[a]['nuts_diag']['max_rhat'])}"
                          for a in ARMS)

    # ---------------- money figure ----------------
    fig, ax = plt.subplots(1, 3, figsize=(14.5, 4.6))
    a0 = ax[0]
    x = np.arange(len(QOIS)); w = 0.13
    for i, a in enumerate(ARMS):
        vals = [arms[a]["R2"][q]["sharpness_vs_fem6db"] for q in QOIS]
        ok = [arms[a]["R2"][q]["covers_hard_gate"] and not arms[a]["disqualified"] for q in QOIS]
        bars = a0.bar(x + (i - 2.5) * w, vals, w, color=arm_color(a),
                      alpha=[1.0 if o else 0.35 for o in ok][0] if len(set(ok)) == 1 else 0.8,
                      edgecolor="none")
        for j, (b, o) in enumerate(zip(bars, ok)):
            b.set_alpha(1.0 if o else 0.3)
            if not o:
                a0.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.04, "x",
                        ha="center", fontsize=7, color="#b03030")
        a0.text(x[0] + (i - 2.5) * w, -0.16, a, rotation=90, ha="center", va="top", fontsize=6.5,
                color=arm_color(a))
    for j, q in enumerate(QOIS):
        a0.hlines(BARS[q], x[j] - 0.42, x[j] + 0.42, color="#b03030", ls="--", lw=1.2)
    a0.text(x[-1] + 0.44, BARS[QOIS[-1]], " proven statFEM F(k) bar", color="#b03030", fontsize=7, va="center")
    a0.set_xticks(x); a0.set_xticklabels(QOIS)
    a0.set_ylabel("95%-band GRMS ratio vs FEM+6dB (lower = sharper)")
    a0.set_title("A. R2 net-CG band sharpness (faded/x = fails hard gate or R3-disqualified)",
                 fontsize=9, loc="left")
    a0.spines[["top", "right"]].set_visible(False)

    a1 = ax[1]
    sk = [arms[a]["R1"]["crps_skill"] for a in ARMS]
    sg = [arms[a]["R1"]["sigma_qoi"] for a in ARMS]
    cv = [arms[a]["R1"]["coverage"] for a in ARMS]
    xx = np.arange(len(ARMS))
    a1.bar(xx, sk, 0.55, color=[arm_color(a) for a in ARMS])
    for i, (s, c) in enumerate(zip(sk, cv)):
        a1.text(i, s + (0.01 if s >= 0 else -0.03), f"cov {c:.2f}", ha="center", fontsize=6.5)
    a1.axhline(0, color="k", lw=0.6)
    a1.set_xticks(xx); a1.set_xticklabels(ARMS, rotation=45, fontsize=7.5)
    a1.set_ylabel("held-out-sensor CRPS-skill vs climatology")
    a1.set_title("B. R1 per-point peak amplitude (held-out sensors,\n5 drives x 3 splits; sigma_qoi printed)",
                 fontsize=9, loc="left")
    for i, s in enumerate(sg):
        a1.text(i, min(sk) - 0.06, f"s{s:.2f}", ha="center", fontsize=6.2, color="#555")
    a1.spines[["top", "right"]].set_visible(False)

    a2 = ax[2]
    for j, q in enumerate(QOIS):
        wr = [arms[a]["R3_leave_modes_out"][q]["widen_ratio"] for a in ARMS]
        a2.plot(np.arange(len(ARMS)) + j * 0.08 - 0.08, wr, "o", ms=5,
                color=["#1f4e79", "#2b7a2b", "#b06f1f"][j], label=q)
    a2.axhline(1.0, color="#b03030", ls="--", lw=1.2)
    a2.text(len(ARMS) - 0.6, 1.01, "overconfidence line (must be > 1)", fontsize=7, color="#b03030")
    a2.set_xticks(np.arange(len(ARMS))); a2.set_xticklabels(ARMS, rotation=45, fontsize=7.5)
    a2.set_ylabel("leave-modes-out widen ratio")
    a2.set_title("C. R3 overconfidence audit (hide top-3 measured modes)", fontsize=9, loc="left")
    a2.legend(fontsize=7, frameon=False)
    a2.spines[["top", "right"]].set_visible(False)

    d = sc["delivered"]
    cap = (f"Composite bake-off matrix, ShockSat 45-260 Hz, all 5 drives, full in-band mode set "
           f"(n_modes={arms['M0S0']['n_modes_used']}). M1 = {sc['m1_candidate']} ({sc['m1_evidence_flag']}). "
           f"Delivered: shear={d['shear'].get('arm')} normal={d['normal'].get('arm')} (best of N=6, "
           f"pre-registered gate). Bars = proven statFEM F(k) (netcg_method_selection 20260701). "
           f"NUTS: {conv_note}. Source: out/matrix_scorecard.json.")
    fig.text(0.01, -0.05, cap, fontsize=7.2, va="top", wrap=True)
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    fig.savefig(FIG / "fig_matrix_money.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # ---------------- evidence figure ----------------
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    cls = [c for c in ev["by_sigma_prior"]["0.25"] if not c.startswith("_")]
    base = {sp: ev["by_sigma_prior"][sp]["baseline"]["logZ"] for sp in ev["by_sigma_prior"]}
    xx = np.arange(len(cls))
    for k, (sp, mk) in enumerate([("0.15", "v"), ("0.25", "o"), ("0.40", "^")]):
        vals = [ev["by_sigma_prior"][sp][c]["logZ"] - base[sp] for c in cls]
        ax.plot(xx, vals, mk, ms=5, ls="-", lw=0.6, label=f"sigma_prior {sp}",
                color={"0.15": "#9db9d1", "0.25": "#1f4e79", "0.40": "#0e2a44"}[sp])
    fo = ev["freq_only_reference"]
    ax.axhline(0, color="k", lw=0.6)
    ax.set_xticks(xx); ax.set_xticklabels(cls, rotation=45, fontsize=7.5, ha="right")
    ax.set_ylabel("log-evidence - baseline (shape-inclusive)")
    ax.set_title("Shape-inclusive (freq+MAC) evidence per model class, prior-width sweep. "
                 f"freq-only ref would crown: {ev['freq_only_would_have_crowned']} (FORBIDDEN as selector)",
                 fontsize=9, loc="left")
    ax.legend(fontsize=7.5, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, -0.04, f"Winner {ev['headline']['winner']} (prior-robust top: {ev['prior_robust_top']}); "
             "type-II ML (sigma_w2, sigma_mac) per class; frozen Hungarian pairing. Source: out/tier3_evidence.json.",
             fontsize=7.2, va="top")
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    fig.savefig(FIG / "fig_evidence.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # ---------------- funnel figure ----------------
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    s1 = [v["screen_score"] for v in t1.values() if "error" not in v]
    b1 = t1["baseline"]["screen_score"]
    a0 = ax[0]
    a0.hist(s1, bins=40, color="#9db9d1", alpha=0.9)
    a0.axvline(b1, color="#7a7a7a", lw=1.4)
    a0.text(b1, a0.get_ylim()[1] * 0.9, " M0 baseline", fontsize=7.5, color="#444")
    a0.set_xlabel("tier-1 screen score (MAC - 3*freqRMS; shape-inclusive)")
    a0.set_ylabel(f"candidates (n={len(s1)})")
    a0.set_title("A. tier-1 subspace screen (151 candidates)", fontsize=9, loc="left")
    a0.spines[["top", "right"]].set_visible(False)
    a1 = ax[1]
    ids = [k for k in t2 if k != "baseline"]
    xs = [t1[k]["screen_score"] for k in ids]; ys = [t2[k]["full_score"] for k in ids]
    a1.plot(xs, ys, "o", ms=4, color="#1f4e79")
    lims = [min(xs + ys) - 0.01, max(xs + ys) + 0.01]
    a1.plot(lims, lims, "-", lw=0.6, color="#aaa")
    a1.plot(t1["baseline"]["screen_score"], t2["baseline"]["full_score"], "s", ms=7, color="#7a7a7a")
    a1.text(t1["baseline"]["screen_score"], t2["baseline"]["full_score"], " M0", fontsize=7.5)
    win = ev["headline"]["winner"]
    if win in t2 and win in t1:
        a1.plot(t1[win]["screen_score"], t2[win]["full_score"], "*", ms=13, color="#b03030")
        a1.text(t1[win]["screen_score"], t2[win]["full_score"], f" {win}", fontsize=7.5, color="#b03030")
    a1.set_xlabel("tier-1 proxy score"); a1.set_ylabel("tier-2 FULL eigensolve score")
    a1.set_title("B. proxy vs full (tier-2 set); * = evidence winner", fontsize=9, loc="left")
    a1.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, -0.04, "Agentic remodeling funnel: 151 candidates -> ~30 full eigensolves -> ~10 evidence "
             "classes -> 1 M1. Sources: out/tier1_screen.json, tier2_full.json, tier3_evidence.json.",
             fontsize=7.2, va="top")
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    fig.savefig(FIG / "fig_funnel.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # ---------------- held-out drives ----------------
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.0), sharey=True)
    for k, q in enumerate(["shear_X", "shear_Y"]):
        a = ax[k]
        drives = [p["drive"] for p in arms["M0S0"]["R2"][q]["heldout_drive"]["per_drive"]]
        for i, arm in enumerate(ARMS):
            pd = arms[arm]["R2"][q]["heldout_drive"]["per_drive"]
            vals = [p["covered_frac"] for p in pd]
            a.plot(np.arange(len(drives)) + (i - 2.5) * 0.06, vals, "o", ms=4, color=arm_color(arm),
                   alpha=0.9 if arm.endswith("0") else 0.65)
        for i, p in enumerate(arms["M0S0"]["R2"][q]["heldout_drive"]["per_drive"]):
            if p["low_observability"]:
                a.annotate("low-obs", (i, 0.02), fontsize=6.5, color="#888", ha="center")
        a.axhline(0.90, color="#b03030", ls="--", lw=1.0)
        a.set_xticks(np.arange(len(drives))); a.set_xticklabels(drives, fontsize=8)
        a.set_title(f"{q}: per-drive held-out coverage (grey=M0, blue=M1)", fontsize=9, loc="left")
        a.set_ylim(0, 1.05)
        a.spines[["top", "right"]].set_visible(False)
    ax[0].set_ylabel("1-oct energy-weighted coverage")
    fig.text(0.01, -0.04, "Leave-one-drive-out answer keys (measured-FRF reconstruction, arm-independent); "
             "dashed = 0.90 strong-drive gate. Source: out/matrix_scorecard.json.", fontsize=7.2, va="top")
    fig.tight_layout(rect=[0, 0.02, 1, 1])
    fig.savefig(FIG / "fig_heldout_drives.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print("figures written:", [p.name for p in FIG.glob("*.png")])


if __name__ == "__main__":
    main()
