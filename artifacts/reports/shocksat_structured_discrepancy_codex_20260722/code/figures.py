#!/usr/bin/env python3
"""Saved, lintable plotting script for Card E review figures."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import DB_PER_LN, WS, read_json


FIG = WS / "figures"
FIG.mkdir(exist_ok=True)
RC = {"figure.dpi": 150, "savefig.dpi": 180, "font.size": 9, "axes.spines.top": False,
      "axes.spines.right": False, "axes.edgecolor": "#444444", "axes.linewidth": 0.8,
      "axes.grid": True, "grid.color": "#dddddd", "grid.linewidth": 0.5,
      "axes.axisbelow": True, "legend.frameon": False, "axes.titlelocation": "left"}
plt.rcParams.update(RC)
BLUE, ORANGE, GREEN, RED, GRAY = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#666666"


def footer(fig, text):
    fig.text(0.01, 0.008, text, fontsize=6.5, color="#444444", va="bottom")


def save(fig, name):
    fig.tight_layout(rect=[0, 0.055, 1, 0.97])
    fig.savefig(FIG / name, bbox_inches="tight")
    plt.close(fig)


def graphical_model(decision):
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.axis("off")
    boxes = {
        "theta": (0.05, 0.64, "modal posterior θ\n4,000 retained draws\n(modular; not updated in Stage 1)"),
        "fem": (0.31, 0.64, "fixed FEM response\nq_fem(f,x;θ)"),
        "beta": (0.05, 0.18, "structured mean β\nβ ~ Normal(0, Λβ)"),
        "gp": (0.31, 0.18, "residual GP u\nzero prior mean, K(f,x,a)"),
        "obs": (0.58, 0.42, "whole log-magnitude residual\nr = Hβ + u + e"),
        "pred": (0.80, 0.42, "held-out prediction\nE[H*β] + E[u*]\nseparate covariance + sum"),
    }
    for x, y, txt in boxes.values():
        ax.text(x, y, txt, transform=ax.transAxes, ha="left", va="center",
                bbox=dict(boxstyle="round,pad=0.5", fc="#f7f7f7", ec="#555555", lw=0.8))
    arrows = [("theta", "fem"), ("fem", "obs"), ("beta", "obs"), ("gp", "obs"), ("obs", "pred")]
    for a, b in arrows:
        x1, y1, _ = boxes[a]; x2, y2, _ = boxes[b]
        ax.annotate("", xy=(x2 - 0.015, y2), xytext=(x1 + 0.18, y1), xycoords=ax.transAxes,
                    arrowprops=dict(arrowstyle="->", lw=1.0, color="#555555"))
    ax.set_title("Card E graphical model: conditioning and learned mean are different mechanisms", fontsize=12)
    footer(fig, f"Run: shocksat_structured_discrepancy_codex_20260722 | terminal path: {decision['chosen_terminal_path']} | schematic (not numeric).")
    save(fig, "fig_graphical_model.png")


def synthetic_recovery(syn, decision):
    z = np.load(WS / "out/synthetic_conditionals.npz")
    test = z["test_index"].astype(int)
    reg = read_json(WS / "mean_basis_registry.json")
    split = read_json(WS / "split_registry.json")
    f = np.asarray(split["frequency_grid_hz"])
    nx = len(reg["selected_daq"])
    xidx = test % nx
    target_x = np.unique(xidx)[0]
    pick = np.where(xidx == target_x)[0]
    freq = f[test[pick] // nx]
    truth = z["truth"][pick] * DB_PER_LN
    e1 = z["e1_mean"][pick] * DB_PER_LN
    e3 = (z["e3_mean_beta"][pick] + z["e3_mean_u"][pick]) * DB_PER_LN
    sd1 = np.sqrt(z["e1_var"][pick]) * DB_PER_LN
    sd3 = np.sqrt(z["e3_var_total"][pick]) * DB_PER_LN
    fig, ax = plt.subplots(2, 2, figsize=(10.5, 7.2))
    a = ax[0, 0]
    a.fill_between(freq, e1 - 1.645 * sd1, e1 + 1.645 * sd1, color=BLUE, alpha=0.14)
    a.plot(freq, truth, color="#111111", lw=1.5, label="injected mean")
    a.plot(freq, e1, color=BLUE, lw=1.1, label="E1 GP conditional")
    a.plot(freq, e3, color=GREEN, lw=1.1, label="E3 protected mean+GP")
    a.fill_between(freq, e3 - 1.645 * sd3, e3 + 1.645 * sd3, color=GREEN, alpha=0.13)
    a.set_xscale("log"); a.set_xlabel("frequency [Hz], log scale"); a.set_ylabel("residual [dB]")
    a.set_title("A. S1 held-out channel, seed 0")
    a.legend(loc="best", fontsize=7)
    for j, case in enumerate(["S0", "S1", "S2"]):
        aa = ax.ravel()[j + 1]
        rows = syn["cases"][case]["seeds"]
        x = np.arange(20)
        d = [r["E3_vs_E1"]["error_reduction_db"] for r in rows]
        aa.axhline(0, color=GRAY, lw=0.7)
        aa.axhline(2, color=RED, lw=0.7, ls="--")
        aa.plot(x, d, "o", ms=3.5, color=GREEN)
        aa.set_xlabel("deterministic seed"); aa.set_ylabel("E1 - E3 median error [dB]")
        aa.set_title(f"{chr(66+j)}. {case}: paired predictive effect")
    invalid = "SYNTHETIC GATE FAILED — measured fit prohibited" if not syn["all_synthetic_gates_pass"] else "synthetic gates passed"
    footer(fig, f"Run: shocksat_structured_discrepancy_codex_20260722 | 20 seeds/case; 15 channels × 87 frequencies; {invalid}. Bands are analytic 90% Gaussian intervals.")
    save(fig, "fig_synthetic_recovery.png")


def fold_effects(syn, measured, decision):
    fig, ax = plt.subplots(1, 3, figsize=(11, 4.2), sharey=False)
    for a, case in zip(ax, ["S0", "S1", "S2"]):
        rows = syn["cases"][case]["seeds"]
        err = np.array([r["E3_vs_E1"]["error_reduction_db"] for r in rows])
        cov = np.array([r["E3_vs_E1"]["coverage_delta"] for r in rows])
        a.axvline(0, color=GRAY, lw=0.7); a.axvline(2, color=RED, lw=0.7, ls="--")
        a.axhline(-0.02, color=RED, lw=0.7, ls=":")
        a.scatter(err, cov, s=20, color=BLUE, alpha=0.8)
        a.set_xlabel("median error reduction [dB]")
        a.set_ylabel("90% coverage change")
        a.set_title(f"{case}: each point is one seed")
    footer(fig, f"Run: shocksat_structured_discrepancy_codex_20260722 | paired E3−E1 gate view; dashed 2 dB and dotted −0.02 coverage limits | path {decision['chosen_terminal_path']}.")
    save(fig, "fig_fold_effects.png")


def identifiability(known, syn, decision):
    mid = known["modal_identifiability"]
    groups = list(mid["group_summary"])
    vals = np.array([mid["group_summary"][g]["mean_se_pct"] for g in groups])
    order = np.argsort(vals)
    eig = np.asarray(mid["fim_eigenvalues_vs_prior_precision"])
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 5.2))
    ax[0].barh(np.arange(len(groups)), vals[order], color=BLUE, height=0.65)
    ax[0].set_yticks(np.arange(len(groups)), np.asarray(groups)[order], fontsize=8)
    ax[0].set_xlabel("mean modal strain-energy fraction [%]")
    ax[0].set_title("A. Physical sensitivity across 18 calibration modes")
    ax[1].plot(np.arange(1, len(eig) + 1), eig, "o-", color=ORANGE, ms=4)
    ax[1].axhline(1, color=RED, ls="--", lw=0.8)
    ax[1].set_yscale("log"); ax[1].set_xlabel("parameter-combination rank")
    ax[1].set_ylabel("FIM information / prior precision [log scale]")
    ax[1].set_title(f"B. Realized modal floor: {mid['n_parameter_combinations_clearing_prior_precision']} combinations > 1")
    footer(fig, f"Run: shocksat_structured_discrepancy_codex_20260722 | modal σ_f={mid['sigma_f_floor']:.4f}; synthetic max normalized orthogonality residual={syn['max_normalized_orthogonality_residual']:.2e}; path {decision['chosen_terminal_path']}.")
    save(fig, "fig_identifiability.png")


def beta_prior(decision):
    rng = np.random.default_rng(20260722)
    n = 100000; bins = 80; tau = 0.35
    x = np.linspace(-1.5, 1.5, 500)
    pdf = np.exp(-0.5 * (x / tau) ** 2) / (tau * np.sqrt(2 * np.pi))
    s = rng.normal(0, tau, n)
    fig, ax = plt.subplots(figsize=(8.5, 4.7))
    ax.hist(s, bins=bins, density=True, color="#bbbbbb", alpha=0.55, label="Monte Carlo check")
    ax.plot(x, pdf, color=BLUE, lw=1.6, label="analytic Normal(0, 0.35²)")
    ax.set_xlabel("coefficient on RMS-normalized basis [natural-log ratio]")
    ax.set_ylabel("density")
    ax.set_title("Analytic beta prior and sampling check")
    ax.legend(loc="upper left")
    footer(fig, f"Run: shocksat_structured_discrepancy_codex_20260722 | analytic prior vs PCG64 Monte Carlo, n={n:,}, bins={bins}; not a posterior | path {decision['chosen_terminal_path']}.")
    save(fig, "fig_beta_prior_check.png")


def heldout(measured, decision):
    z = np.load(WS / "out/measured_conditionals.npz")
    reg = read_json(WS / "mean_basis_registry.json")
    split = read_json(WS / "split_registry.json")
    f = np.asarray(split["frequency_grid_hz"])
    nx = len(reg["selected_daq"])
    test = z["test_index"].astype(int)
    xidx = test % nx
    target = np.unique(xidx)[0]
    p = np.where(xidx == target)[0]
    ff = f[test[p] // nx]
    obs = z["observed_q"][p] * DB_PER_LN
    m1 = z["e1_total_mean"][p] * DB_PER_LN; s1 = np.sqrt(z["e1_total_var"][p]) * DB_PER_LN
    m3 = z["e3_total_mean"][p] * DB_PER_LN; s3 = np.sqrt(z["e3_total_var"][p]) * DB_PER_LN
    fig, (ax, ar) = plt.subplots(2, 1, figsize=(9.5, 6), sharex=True, height_ratios=[3, 1])
    ax.plot(ff, obs, color="#111111", lw=1.3, label="measured H1 log magnitude")
    ax.plot(ff, m1, color=BLUE, lw=1.1, label="E1")
    ax.fill_between(ff, m1 - 1.645*s1, m1 + 1.645*s1, color=BLUE, alpha=0.14)
    ax.plot(ff, m3, color=GREEN, lw=1.1, label="E3")
    ax.fill_between(ff, m3 - 1.645*s3, m3 + 1.645*s3, color=GREEN, alpha=0.13)
    ar.axhline(0, color=GRAY, lw=0.7); ar.plot(ff, m1-obs, color=BLUE); ar.plot(ff, m3-obs, color=GREEN)
    ax.set_ylabel("20 ln(|H1|/1 g/lbf)/ln(10) [dB]"); ar.set_ylabel("residual [dB]")
    ar.set_xlabel("frequency [Hz], log scale"); ax.set_xscale("log"); ax.legend(fontsize=8)
    ax.set_title("Held-out contiguous frequency core: measured versus modular predictions")
    footer(fig, f"Run: shocksat_structured_discrepancy_codex_20260722 | whole log-magnitude H1; 90% analytic+modal-mixture bands; path {decision['chosen_terminal_path']}; five-fold uncertainty weak.")
    save(fig, "fig_heldout_frf.png")


def main():
    syn = read_json(WS / "out/synthetic_results.json")
    known = read_json(WS / "out/known_answers.json")
    decision = read_json(WS / "automatic_decision.json")
    measured = read_json(WS / "out/stage1_results.json") if (WS / "out/stage1_results.json").exists() else None
    graphical_model(decision)
    synthetic_recovery(syn, decision)
    fold_effects(syn, measured, decision)
    identifiability(known, syn, decision)
    beta_prior(decision)
    if measured:
        heldout(measured, decision)
    print("figures written", len(list(FIG.glob("*.png"))))


if __name__ == "__main__":
    main()
