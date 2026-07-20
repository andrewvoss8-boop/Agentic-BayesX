#!/usr/bin/env python3
"""Generate review figures from saved scorecard / sampler outputs.

Tufte checklist applied: direct labels, log frequency for FRF, sparse grid,
source/count captions on figure, and explicit non-convergence flags.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import heldout_qoi as hq
import ift_arm as IFT
import realfrf as rf

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
FIG = WS / "figures"
PROV = WS / "provenance"

plt.rcParams.update({
    "font.size": 9.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.22,
    "grid.linewidth": 0.5,
    "figure.dpi": 120,
    "savefig.dpi": 220,
})

C_IFT = "#D55E00"
C_L5 = "#0072B2"
C_M2 = "#555555"
C_BAD = "#8B0000"


def load(name):
    return json.loads((OUT / name).read_text())


def stamp(fig, text):
    fig.text(0.01, 0.006, text, fontsize=7, color="0.35", ha="left")


def save(fig, name):
    FIG.mkdir(exist_ok=True)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    hits = []
    for ax in fig.get_axes():
        boxes = []
        for t in ax.texts:
            if not t.get_text().strip():
                continue
            try:
                boxes.append((t.get_text()[:32], t.get_window_extent(renderer)))
            except Exception:
                pass
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                inter = boxes[i][1].intersection(boxes[i][1], boxes[j][1])
                if inter is not None and inter.width > 2 and inter.height > 2:
                    hits.append([boxes[i][0], boxes[j][0]])
    overlap_p = OUT / "text_overlap.json"
    data = json.loads(overlap_p.read_text()) if overlap_p.exists() else {}
    if hits:
        data[name] = hits
    else:
        data.pop(name, None)
    overlap_p.write_text(json.dumps(data, indent=2))
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    fig.savefig(FIG / name, bbox_inches="tight")
    plt.close(fig)
    print(f"saved figures/{name}")


def fig_a_scorecard():
    sc = load("scorecard.json")
    ift = sc["IFT"]
    l5 = sc["L5_modal_feature_marginal_qoi_discrepancy"]
    m2 = sc["M2_whole_frf_schneider"]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), sharey=True)
    qois = ["peak", "band"]
    ypos = np.arange(len(qois))
    for ax, metric, label in zip(axes, ["interval", "crps"], ["Interval score lower is better", "CRPS lower is better"]):
        for i, q in enumerate(qois):
            vals = [
                ("IFT", ift["summary"][q][metric]["med"], ift["summary"][q][metric].get("p5"), ift["summary"][q][metric].get("p95"), C_IFT),
                ("L5", l5["qoi"][q][metric]["med"], l5["qoi"][q][metric].get("p5"), l5["qoi"][q][metric].get("p95"), C_L5),
            ]
            m2v = m2.get("seed0", {}).get(q, {}).get("interval" if metric == "interval" else "crps")
            vals.append(("M2 seed0", m2v, None, None, C_M2))
            offsets = [-0.22, 0.0, 0.22]
            for off, (name, med, lo, hi, color) in zip(offsets, vals):
                y = i + off
                if lo is not None and hi is not None:
                    ax.plot([lo, hi], [y, y], color=color, lw=2, alpha=0.55)
                ax.plot(med, y, "o", color=color, ms=5)
                ax.annotate(name, (med, y), xytext=(5, 0), textcoords="offset points", va="center", fontsize=8, color=color)
        ax.set_xscale("log")
        ax.set_title(label, loc="left")
        ax.set_xlabel("proper score, log axis")
        ax.set_yticks(ypos)
        ax.set_yticklabels(["peak |H| [g/lbf]", "band-GRMS [g/lbf]"])
    fig.suptitle("Fig A. Held-out QOI scorecard: IFT is an honest negative, not a win", x=0.01, ha="left", fontsize=13)
    stamp(fig, "Real ShockSat hit-001; 25 channel splits for IFT/L5; M2 copied one-split whole-FRF failure; IFT 0/25 converged.")
    save(fig, "figA_scorecard.png")


def fig_b_beta():
    mc = load("ift_mc_headline.json")
    rows = mc["per_split"]
    seeds = np.array([r["seed"] for r in rows])
    beta = np.array([r["beta_med"] for r in rows])
    rhat = np.array([r["max_rhat"] for r in rows])
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(9.5, 5.4), sharex=True)
    ax.plot(seeds, beta, "o-", color=C_IFT, lw=1.2)
    ax.axhline(1e3, color="0.35", lw=0.9)
    ax.annotate("prior median beta=1e3", (seeds[-1], 1e3), xytext=(5, 0), textcoords="offset points", va="center", fontsize=8)
    ax.set_yscale("log")
    ax.set_ylabel("median beta")
    ax.set_title("Fig B. Beta thermometer is unstable across splits", loc="left")
    ax2.plot(seeds, rhat, "o-", color=C_BAD, lw=1.2)
    ax2.axhline(1.05, color="0.35", lw=0.9)
    ax2.annotate("R-hat gate 1.05", (seeds[-1], 1.05), xytext=(5, 0), textcoords="offset points", va="center", fontsize=8)
    ax2.set_yscale("log")
    ax2.set_xlabel("channel split seed")
    ax2.set_ylabel("worst R-hat")
    stamp(fig, "Real ShockSat hit-001; IFT diagnostic-budget NUTS; every split failed R-hat/ESS convergence.")
    save(fig, "figB_beta_thermometer.png")


def fig_c_frf_overlay():
    split = IFT.load_split(seed=0, obs_frac=0.6)
    freqs = split["freqs"]
    truth = np.exp(split["y_ho"])
    k = int(np.argmax(np.max(truth, axis=0)))
    daq = split["ho_daqs"][k]
    z = np.load(OUT / "ift_split_0_headline_samples.npz")
    sub = np.linspace(0, len(z["beta"]) - 1, min(80, len(z["beta"]))).astype(int)
    rng = np.random.default_rng(12)
    ift_curves = []
    for s in sub:
        mu, var = IFT._ift_moments_np(split["R"], freqs, split["ho_rows"][k:k + 1], split["drive_row"], z["theta"][s], z["beta"][s], z["gain_c"][s])
        ift_curves.append(np.exp((mu + rng.normal(0, np.sqrt(var + IFT.SIGMA_MEAS ** 2)))[:, 0]))
    ift_curves = np.asarray(ift_curves)

    l5 = np.load(PROV / "l5_theta_0.npz")
    theta = l5["theta"]
    sub_l5 = np.linspace(0, len(theta) - 1, min(120, len(theta))).astype(int)
    all_rows = np.vstack([split["obs_rows"], split["ho_rows"][k:k + 1]])
    lm = rf.fem_logmag_batch(split["R"], freqs, theta[sub_l5], all_rows, split["drive_row"], zeta=rf.ZETA_NOM)
    didx = {d: i for i, d in enumerate(split["meas"]["daq"])}
    w_obs = np.array([split["meas"]["weight"][didx[d]][(split["meas"]["freqs"] >= rf.BAND[0]) & (split["meas"]["freqs"] <= rf.BAND[1])] for d in split["obs_daqs"]]).T
    c = np.array([hq.wmedian((split["y_obs"] - lm[j, :, :len(split["obs_daqs"])]).ravel(), w_obs.ravel()) for j in range(len(sub_l5))])
    l5_curves = np.exp(lm[:, :, -1] + c[:, None])

    def band(a):
        return np.percentile(a, [2.5, 50, 97.5], axis=0)

    b_ift = band(ift_curves)
    b_l5 = band(l5_curves)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(freqs, truth[:, k], color="black", lw=1.4)
    ax.annotate("measured held-out", (freqs[-1], truth[-1, k]), xytext=(5, 0), textcoords="offset points", va="center", fontsize=8)
    ax.fill_between(freqs, b_l5[0], b_l5[2], color=C_L5, alpha=0.16)
    ax.plot(freqs, b_l5[1], color=C_L5, lw=1.2)
    ax.annotate("L5 median/band", (freqs[-1], b_l5[1, -1]), xytext=(5, 8), textcoords="offset points", va="center", fontsize=8, color=C_L5)
    ax.fill_between(freqs, b_ift[0], b_ift[2], color=C_IFT, alpha=0.14)
    ax.plot(freqs, b_ift[1], color=C_IFT, lw=1.2)
    ax.annotate("IFT not-converged band", (freqs[-1], b_ift[1, -1]), xytext=(5, -8), textcoords="offset points", va="center", fontsize=8, color=C_IFT)
    ax.text(0.02, 0.03, "M2 whole-FRF: not plotted as a curve; copied baseline is non-converged and QOI-wide.", transform=ax.transAxes, fontsize=8, color=C_M2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("frequency [Hz], log scale")
    ax.set_ylabel("|H1| [g/lbf], log magnitude scale")
    ax.set_title(f"Fig C. Held-out FRF overlay, DAQ ch{daq}: IFT widens but does not converge", loc="left")
    stamp(fig, "Real ShockSat hit-001; held-out channel from split 0; y-axis log is a deliberate readability deviation from linear-magnitude preference.")
    save(fig, "figC_heldout_frf_overlay.png")


def fig_d_convergence_table():
    mc = load("ift_mc_headline.json")
    l5 = json.loads((PROV / "mc_summary.json").read_text())
    m2 = json.loads((PROV / "tmcmc_faithful_M2_ident4_n8.json").read_text())
    rows = [
        ["IFT", "NUTS", "25", f"{mc['converged_frac']:.2f}", f"{max(r['max_rhat'] for r in mc['per_split']):.1f}", f"{min(r['min_ess'] for r in mc['per_split']):.0f}", "HONEST NEGATIVE"],
        ["L5", "NUTS", str(l5["n_configs"]), f"{l5['calib_converged_frac']:.2f}", "see source", "see source", "baseline bar"],
        ["M2", "TMCMC", "1", str(m2["converged"]), f"{m2['diag']['max_rhat']:.2f}", f"{m2['diag']['min_ess']:.0f}", "whole-FRF failure"],
    ]
    fig, ax = plt.subplots(figsize=(10.5, 3.2))
    ax.axis("off")
    table = ax.table(cellText=rows, colLabels=["arm", "sampler", "splits", "conv frac", "worst R-hat", "min ESS", "reading"], loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.45)
    for (r, c), cell in table.get_celld().items():
        cell.set_linewidth(0.4)
        if r == 0:
            cell.set_facecolor("#eeeeee")
        if r == 1:
            cell.set_facecolor("#fff2e8")
    ax.set_title("Fig E. Convergence table: IFT fails the all-variable gate on every split", loc="left", fontsize=13)
    stamp(fig, "R-hat <=1.05 and ESS >=200 required for GREEN; IFT intervals are labeled not-yet-converged.")
    save(fig, "figE_convergence_table.png")


def fig_d_discretization():
    d = load("discretization_sensitivity.json")
    grids = list(d["grids"].keys())
    labels = [g.replace("_", "\n") for g in grids]
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.1), sharey=True)
    x = np.arange(len(grids))
    width = 0.32
    for ax, qoi, title in zip(axes, ["peak", "band"], ["peak |H|", "band-GRMS"]):
        vals_ift = [d["arms"]["IFT"][g][qoi]["interval_score"]["med"] for g in grids]
        vals_l5 = [d["arms"]["L5"][g][qoi]["interval_score"]["med"] for g in grids]
        ax.plot(x - width / 2, vals_ift, "o-", color=C_IFT, lw=1.4)
        ax.plot(x + width / 2, vals_l5, "o-", color=C_L5, lw=1.4)
        ax.set_yscale("log")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_title(f"{title}: interval score vs grid", loc="left")
        ax.set_xlabel("frequency grid used for QOI")
        ax.set_ylabel("interval score, log axis")
        ax.annotate("IFT", (x[-1] - width / 2, vals_ift[-1]), xytext=(5, 0), textcoords="offset points", fontsize=8, color=C_IFT)
        ax.annotate("L5", (x[-1] + width / 2, vals_l5[-1]), xytext=(5, 0), textcoords="offset points", fontsize=8, color=C_L5)
    fig.suptitle("Fig D. Discretization diagnostic: post-hoc QOI grid sweep, not certified posterior invariance", x=0.01, ha="left", fontsize=13)
    stamp(fig, "Split 0 only; same posterior samples reused on 173/87/44 frequency-line QOI grids; headline IFT is non-converged.")
    save(fig, "figD_discretization_invariance.png")


def main():
    from subprocess import run

    if not (OUT / "discretization_sensitivity.json").exists():
        run([sys.executable, str(WS / "code/discretization_sensitivity.py")], check=True)
    fig_a_scorecard()
    fig_b_beta()
    fig_c_frf_overlay()
    fig_d_discretization()
    fig_d_convergence_table()
    (OUT / "figure_manifest.json").write_text(json.dumps({
        "figures": [
            "figA_scorecard.png",
            "figB_beta_thermometer.png",
            "figC_heldout_frf_overlay.png",
            "figD_discretization_invariance.png",
            "figE_convergence_table.png",
        ],
        "tufte_notes": [
            "Direct labels and sparse grids used.",
            "Frequency axis is log in FRF overlay.",
            "FRF y-axis uses log magnitude scale as a deliberate readability deviation because IFT bands span orders of magnitude.",
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
