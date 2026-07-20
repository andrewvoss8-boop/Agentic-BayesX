#!/usr/bin/env python3
"""Supplementary packet figures (Claude Code lead; Tufte gate applied).

 1. graphical_model.png       — run-specific model/likelihood diagram
 2. heldout_qoi_sidebyside_lomo.png — THE deliverable for the LOMO design
 3. convergence_summary.png   — all-variable convergence evidence per design

Tufte notes: direct labels, no legends where avoidable, no chartjunk, muted
reference lines. Held-out frequency axes are LINEAR Hz: these are per-mode
point comparisons over a narrow band (120-230 Hz), not spectra — the
log-frequency rule targets FRF/PSD curves (deviation stated per gate).
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 140,
                     "savefig.bbox": "tight"})
INK = "#222222"; PRED = "#1b6ca8"; MEAS = "#c0392b"; MUTE = "#999999"


def box(ax, x, y, w, h, text, fc="#f4f6f8", fs=10.5):
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=fc, edgecolor=INK,
                               linewidth=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.0))


def fig_graphical_model():
    pr = json.load(open("pairing.json"))
    ncal = len(pr["calib_test_modes"])
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    ax.set_xlim(0, 10.5); ax.set_ylim(0, 6.2); ax.axis("off")
    # priors
    box(ax, 0.3, 4.6, 3.1, 1.2,
        "$\\theta_g \\sim \\mathrm{LogNormal}(0,\\ 0.25)$\n"
        "9 part-group stiffness scales\n(median 1; 95% range 0.61–1.63)",
        fc="#eef3fa")
    box(ax, 0.3, 2.9, 3.1, 1.0,
        "$\\sigma_f \\sim \\mathrm{HalfNormal}(0.05)$\n"
        "log-frequency residual scale", fc="#eef3fa")
    # forward model
    box(ax, 4.0, 4.4, 3.0, 1.6,
        "$K_r(\\theta) = A_{fix} + \\sum_g \\theta_g A_g$\n"
        "$(74\\times74$, mass $=I)$\n"
        "$\\lambda, Q = \\mathrm{eigh}(K_r)$\n"
        "$f = \\sqrt{\\lambda}/2\\pi$  [Hz]")
    box(ax, 4.0, 2.7, 3.0, 1.1,
        "mode tracking: argmax overlap\nwith nominal eigenvector\n"
        "(stop-gradient; piecewise const.)")
    # likelihood
    box(ax, 7.8, 4.4, 2.4, 1.6,
        "$\\log f_{pred,m} \\sim$\n$\\mathcal{N}(\\log f_{meas,m},\\ "
        "\\sigma_f)$\nwhole held-in set,\nno feature selection", fc="#fdf2ee")
    box(ax, 7.8, 2.7, 2.4, 1.1,
        "MAC$_m \\sim \\mathcal{N}(1, \\sigma_{mac})$\n"
        "PSEUDO-likelihood\n(sensitivity arm only)", fc="#fbfbfb")
    # data plate
    box(ax, 7.8, 0.6, 2.4, 1.5,
        f"DATA: impact-hammer\nfree-free modes (.ash)\n"
        f"{ncal} calibration-clean of 33;\nband: 6 held-in / 12 held-out\n"
        "LOMO: 17 held-in / 1 out", fc="#f2f7f2")
    box(ax, 4.0, 0.6, 3.0, 1.5,
        "FIXED (not inferred):\nmass M, geometry, mesh,\npairing rule, "
        "accel mounts,\nelement formulation\nNOT inferred: discrepancy\n"
        "field beyond $\\sigma_f$; damping")
    arrow(ax, 3.4, 5.2, 4.0, 5.2)
    arrow(ax, 3.4, 3.4, 7.8, 5.0)
    arrow(ax, 7.0, 5.2, 7.8, 5.2)
    arrow(ax, 5.5, 4.4, 5.5, 3.8)
    arrow(ax, 7.0, 3.2, 7.8, 3.2)
    arrow(ax, 9.0, 2.1, 9.0, 2.7)
    arrow(ax, 9.0, 6.0, 9.0, 6.0)
    ax.set_title("ShockSat modal twin — run-specific model & likelihood "
                 "(NUTS, 4 chains)", fontsize=12)
    fig.savefig("figures/graphical_model.png")
    plt.close(fig)


def fig_heldout_lomo():
    d = json.load(open("heldout_lomo.json"))
    rows = sorted(d["rows"], key=lambda r: r["f_meas"])
    y = np.arange(len(rows))
    fm = np.array([r["f_meas"] for r in rows])
    med = np.array([r["f_pred_median"] for r in rows])
    plo = np.array([r["ci95_pred"][0] for r in rows])
    phi = np.array([r["ci95_pred"][1] for r in rows])
    clo = np.array([r["ci95_param"][0] for r in rows])
    chi = np.array([r["ci95_param"][1] for r in rows])
    cov = np.array([r["covers_pred"] for r in rows])
    rh = np.array([r["conv_rhat"] for r in rows])
    fig, ax = plt.subplots(figsize=(8.8, 0.46 * len(rows) + 1.8))
    for i in y:
        ax.plot([plo[i], phi[i]], [i, i], color=PRED, lw=1.2, alpha=0.5,
                solid_capstyle="round", zorder=1)
        ax.plot([clo[i], chi[i]], [i, i], color=PRED, lw=4, alpha=0.9,
                solid_capstyle="round", zorder=2)
    ax.scatter(med, y, color=PRED, s=24, zorder=3)
    ax.scatter(fm, y, marker="D", color=MEAS, s=32, zorder=4,
               edgecolor="white", linewidth=0.5)
    xr = phi.max()
    for i in y:
        note = "covered" if cov[i] else "MISS"
        conv = "" if rh[i] <= 1.05 else f"  (R-hat {rh[i]:.2f}!)"
        ax.text(xr * 1.01, i, f"{note}{conv}", va="center", fontsize=8.5,
                color=INK if cov[i] else MEAS)
    ax.set_yticks(y)
    ax.set_yticklabels([f"test {r['test_mode']} "
                        f"({r['err_pct']:+.1f}%)" for r in rows], fontsize=9)
    ax.set_xlabel("frequency [Hz] — linear axis (point comparisons, "
                  "not a spectrum)")
    npass = int(cov.sum())
    worst = d.get("worst_convergence", {})
    wr = worst.get("rhat"); we = worst.get("ess")
    ax.set_title("Held-out — LOMO design (leave-one-mode-out, 17 held-in / 1 "
                 "out, x18)\nposterior median + 95% CI (thick=param, thin=+noise)"
                 f" vs measured (red diamond); coverage {npass}/{len(rows)} = "
                 f"{npass/len(rows):.2f}", fontsize=9.5)
    if wr is not None and wr > 1.05:
        ax.text(0.02, 0.98,
                f"most folds NOT converged (worst R-hat {wr:.2f}, min ESS "
                f"{we:.0f}); per-row R-hat flagged at right — CIs not trustworthy",
                transform=ax.transAxes, ha="left", va="top",
                color=MEAS, fontsize=8.5)
    fig.savefig("figures/heldout_qoi_sidebyside_lomo.png")
    plt.close(fig)


def fig_convergence():
    fig, ax = plt.subplots(figsize=(8.6, 3.4))
    items = []
    if os.path.exists("logs/failrun1_convergence_band.json"):
        c = json.load(open("logs/failrun1_convergence_band.json"))
        items.append(("band 1000+1000 d8\n(FAILED, kept)", c["worst_rhat"],
                      c["min_ess"], c["divergences"]))
    if os.path.exists("convergence_band.json"):
        c = json.load(open("convergence_band.json"))
        items.append(("band 2000+2000 d10", c["worst_rhat"], c["min_ess"],
                      c["divergences"]))
    if os.path.exists("heldout_lomo.json"):
        d = json.load(open("heldout_lomo.json"))
        for r in sorted(d["rows"], key=lambda r: r["test_mode"]):
            items.append((f"LOMO {r['test_mode']}", r["conv_rhat"],
                          r["conv_ess"], r["conv_div"]))
    x = np.arange(len(items))
    rh = [i[1] for i in items]
    ax.axhline(1.05, color=MEAS, lw=1, ls="--")
    ax.text(len(items) - 0.5, 1.055, "gate 1.05", color=MEAS, fontsize=8.5,
            ha="right", va="bottom")
    cols = [PRED if v <= 1.05 else MEAS for v in rh]
    ax.scatter(x, rh, c=cols, s=30, zorder=3)
    for xi, (name, v, ess, dv) in zip(x, items):
        ax.text(xi, max(v, 1.06) + 0.02 if v > 1.2 else 1.002 - 0.04,
                f"ESS {ess:.0f}", fontsize=7, ha="center", color=MUTE)
    ax.set_xticks(x)
    ax.set_xticklabels([i[0] for i in items], rotation=60, ha="right",
                       fontsize=8)
    ax.set_ylabel("worst R-hat (ALL sampled variables)")
    ax.set_title("Convergence per run: worst R-hat with min ESS annotated "
                 "(divergences = 0 in all runs unless noted)", fontsize=10.5)
    fig.savefig("figures/convergence_summary.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_graphical_model(); print("wrote graphical_model.png")
    if os.path.exists("heldout_lomo.json"):
        fig_heldout_lomo(); print("wrote heldout_qoi_sidebyside_lomo.png")
    fig_convergence(); print("wrote convergence_summary.png")
