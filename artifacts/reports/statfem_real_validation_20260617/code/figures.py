#!/usr/bin/env python3
"""Slide figures for Card A (tufte-data-graphics skill applied; decisions_log D14).

Each figure: minimal non-data ink, direct labels, documented caption (quantity/units/source/synthetic-vs-measured),
log axes where the data spans decades, and YELLOW provenance flags ON the figure. Saved to figures/*.png.
Sources are artifact JSONs in out/ (no fabricated numbers). Run: python figures.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
FIG = WS / "figures"
FIG.mkdir(exist_ok=True)
GNAMES = ["al_welds", "angle_brackets", "bottom_box", "contact", "cross_beam",
          "joints", "plates", "steel_welds", "top_box"]
IDENT4 = {"bottom_box", "cross_beam", "plates", "top_box"}

plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": False, "figure.dpi": 130, "savefig.bbox": "tight"})


def _load(name):
    p = OUT / name
    return json.loads(p.read_text()) if p.exists() else None


def fig_error_participation():
    """One dot per property group: x = peak modal strain-energy participation (%), y = inferred stiffness
    correction |theta_med - 1| (%), dot AREA = participation x error footprint (NOT error alone)."""
    idn = _load("identifiability.json"); mf = _load("modal_feature.json")
    if not idn or not mf:
        return None
    se = idn["strain_energy"]; th = mf["theta_post"]
    x = np.array([se[g]["peak_frac"] * 100 for g in GNAMES])
    y = np.array([abs(th[g]["med"] - 1.0) * 100 if g in th else 0.0 for g in GNAMES])
    foot = (x / 100) * (y / 100)
    sizes = 60 + 1700 * foot / max(foot.max(), 1e-9)
    fig, ax = plt.subplots(figsize=(8.4, 5.4))
    ax.set_ylim(-1.2, max(y) * 1.18)
    # custom label offsets to avoid collisions in the crowded low-participation corner
    offs = {"al_welds": (-8, 7, "right"), "contact": (8, -12, "left"), "steel_welds": (8, 7, "left"),
            "joints": (8, 7, "left"), "cross_beam": (8, 11, "left"), "bottom_box": (8, 11, "left"),
            "top_box": (8, 11, "left")}
    for g, xi, yi, s in zip(GNAMES, x, y, sizes):
        ident = g in IDENT4
        ax.scatter(xi, yi, s=s, alpha=0.5, color=("#1f6fb4" if ident else "#b0b0b0"),
                   edgecolor="k", linewidth=0.6, zorder=3)
        ox, oy, ha = offs.get(g, (8, 7, "left"))
        ax.annotate(g.replace("_", " "), (xi, yi), xytext=(ox, oy), textcoords="offset points",
                    ha=ha, fontsize=9, color=("#13456e" if ident else "#777"))
    ax.axvline(30, color="#cc6666", lw=1.0, ls="--", zorder=1)
    ax.text(31, ax.get_ylim()[1] * 0.96, "identifiable\n(peak SE > 30%)", color="#cc6666", fontsize=8, va="top")
    ax.set_xlabel("peak modal strain-energy participation  f_{i,g} = phi^T K_g phi / lambda   [%]")
    ax.set_ylabel("inferred stiffness correction  |theta_med - 1|   [%]")
    ax.set_title("Where the FEM is wrong vs where the modes can see it", fontsize=12)
    ax.text(0.0, -0.20,
            "One dot per 9 property groups. x: peak strain-energy fraction over the calibration modes "
            "(identifiability.json). y: L5 modal-calibrated stiffness correction (modal_feature.json, CONVERGED "
            "R-hat 1.002). Dot AREA = participation x error footprint, NOT error magnitude alone. Blue = the 4 "
            "strain-energy-identifiable groups. Real ShockSat, single impact (1 hit, YELLOW).",
            transform=ax.transAxes, fontsize=7.5, color="#444", va="top", wrap=True)
    p = FIG / "fig_error_participation.png"; fig.savefig(p); plt.close(fig); return p


def fig_arms_comparison():
    """Q-A/Q-B keystone: cross-run R-hat, log-evidence, and discrepancy sigma_w across the 4 whole-FRF arms."""
    arms = ["M0", "M1", "M2", "M3"]
    labels = ["M0\nnaive", "M1\niid", "M2\nSchneider", "M3\northogonal"]
    data = {a: _load(f"tmcmc_faithful_{a}_ident4_n8.json") for a in arms}
    if any(v is None for v in data.values()):
        return None
    rhat = [data[a]["diag"]["max_rhat"] for a in arms]
    logz = [data[a]["diag"]["log_evidence_mean"] for a in arms]
    sw = [data[a]["sigma_w"]["med"] if data[a]["sigma_w"] else np.nan for a in arms]
    x = np.arange(4); col = ["#9aa0a6", "#7bb274", "#1f6fb4", "#d08a2e"]
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.2))

    axes[0].bar(x, rhat, color=col, width=0.62)
    axes[0].axhline(1.05, color="#cc3333", lw=1.0, ls="--")
    axes[0].text(3.4, 1.05, "1.05 gate", color="#cc3333", fontsize=8, ha="right", va="bottom")
    axes[0].set_yscale("log"); axes[0].set_ylabel("cross-run R-hat  (1 = converged)")
    axes[0].set_title("Convergence: only M0 passes", fontsize=10.5)
    for xi, v in zip(x, rhat):
        axes[0].text(xi, v * 1.05, f"{v:.2f}", ha="center", va="bottom", fontsize=8)

    best = max(logz); dz = [v - best for v in logz]            # log-evidence relative to best arm (M2)
    axes[1].bar(x[1:], dz[1:], color=col[1:], width=0.62)       # M0 off-scale -> annotate as text
    axes[1].axhline(0, color="k", lw=0.8)
    axes[1].set_ylabel("log-evidence vs best (M2)   (0 = best fit)")
    axes[1].set_title("Fit: M3 orthogonal STARVED\n(~105 below M2)", fontsize=10.5)
    for xi, v in zip(x[1:], dz[1:]):
        axes[1].text(xi, v, f"{v:.0f}", ha="center", va="top", fontsize=8.5)
    axes[1].text(0.5, axes[1].get_ylim()[1] * 0.5, f"M0 naive:\n{dz[0]:,.0f}\n(no discrepancy,\noff scale)",
                 ha="center", va="center", fontsize=8, color="#777")

    axes[2].bar(x, sw, color=col, width=0.62)
    axes[2].axhline(1.726, color="#3a7", lw=1.0, ls=":")
    axes[2].text(3.4, 1.726, "realized floor 1.73", color="#3a7", fontsize=8, ha="right", va="bottom")
    axes[2].axhline(9.8, color="#cc3333", lw=1.0, ls="--")
    axes[2].text(3.4, 9.8, "old runaway 9.8", color="#cc3333", fontsize=8, ha="right", va="bottom")
    axes[2].set_ylabel("discrepancy sigma_w  (log-mag)")
    axes[2].set_title("M2/M3 sigma_w still pins high\n(near-null-space)", fontsize=10.5)
    for xi, v in zip(x, sw):
        if not np.isnan(v):
            axes[2].text(xi, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8)

    for ax in axes:
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5)
    fig.suptitle("Faithful Schneider under TMCMC (n=4000 x 4 runs): evidence stabilizes, theta does not converge",
                 fontsize=12, y=1.02)
    fig.text(0.0, -0.06,
             "Real ShockSat whole-FRF |H| magnitude, 8 obs channels x 173 band freqs, 4-group theta. Source: "
             "out/tmcmc_faithful_*.json. M0 converges but fits catastrophically (no discrepancy). M2 fits best "
             "(logZ -2717) but R-hat 2.58 (not converged). M3 orthogonal: logZ -2822 = ~105 worse than M2 = the "
             "discrepancy STARVATION (Bayes factor e^105). YELLOW: M1/M2/M3 non-converged.",
             fontsize=7.5, color="#444", va="top", wrap=True)
    p = FIG / "fig_arms_comparison.png"; fig.savefig(p); plt.close(fig); return p


def fig_scoring_suite():
    """Held-out-sensor QOI calibration (next-action #1): theta-only vs theta+QOI-discrepancy, peak & band."""
    d = _load("heldout_qoi_L5.json")
    if not d:
        return None
    variants = [("theta-only\n(no disc.)", d["scores_theta_only"]),
                ("theta + QOI\ndiscrepancy", d["scores_theta_plus_qoi_discrepancy"])]
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.2))
    xv = np.arange(2); width = 0.34
    for j, q in enumerate(("peak", "band")):
        off = (j - 0.5) * width; col = "#1f6fb4" if q == "peak" else "#d08a2e"
        cov = [v[q]["coverage_frac"] for _, v in variants]
        isc = [v[q]["interval_score_mean"] for _, v in variants]
        zst = [v[q]["z_std"] for _, v in variants]
        axes[0].bar(xv + off, cov, width, color=col, label=q)
        axes[1].bar(xv + off, isc, width, color=col)
        axes[2].bar(xv + off, zst, width, color=col)
        for xi, v in zip(xv + off, cov):
            axes[0].text(xi, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
    axes[0].axhline(0.95, color="#cc3333", lw=1.0, ls="--")
    axes[0].text(1.49, 0.55, "0.95\nnominal", color="#cc3333", fontsize=8, ha="right", va="center")
    axes[0].set_ylim(0, 1.08); axes[0].set_ylabel("held-out coverage"); axes[0].set_title("Calibration", fontsize=10.5)
    axes[0].legend(fontsize=8, frameon=False, loc="lower left")
    axes[1].set_yscale("log"); axes[1].set_ylabel("interval (Winkler) score  (lower = better)")
    axes[1].set_title("Proper score (headline)", fontsize=10.5)
    axes[2].axhline(1.0, color="#3a7", lw=1.0, ls=":")
    axes[2].text(1.4, 1.0, "1.0 = calibrated", color="#3a7", fontsize=8, ha="right", va="bottom")
    axes[2].set_ylabel("z-score std  (1 = calibrated)"); axes[2].set_title("Spread calibration", fontsize=10.5)
    for ax in axes:
        ax.set_xticks(xv); ax.set_xticklabels([v[0] for v in variants], fontsize=8.5)
    fig.suptitle("Held-out-SENSOR QOI: frequency calibration alone is overconfident; a QOI discrepancy fixes it",
                 fontsize=12, y=1.02)
    fig.text(0.0, -0.06,
             "L5 modal-calibrated twin (CONVERGED R-hat 1.002), predict held-out peak |H| & band-GRMS [g/lbf] at "
             "32 unseen channels. Source: out/heldout_qoi_L5.json. theta-only: coverage 0.12/0.16, z-std 11-14 "
             "(overconfident). +QOI-discrepancy: coverage 0.91, z-std ~1 (calibrated), proper score improves -> "
             "informative, not band-padding. Real ShockSat, 1 split, 1 hit (YELLOW).",
             fontsize=7.5, color="#444", va="top", wrap=True)
    p = FIG / "fig_scoring_suite.png"; fig.savefig(p); plt.close(fig); return p


def fig_method_comparison():
    """Held-out-sensor QOI (peak |H|) across ALL methods: interval score (log) + coverage. The punchline:
    M2/M3 'cover' 100% but with USELESS width; only the modal-feature L5 is calibrated AND usable."""
    s = _load("scores_summary.json")
    if not s:
        return None
    order = ["M0", "M1", "M2", "M3", "L5"]
    labels = ["M0\nno disc.", "M1\niid", "M2\nSchneider", "M3\northogonal", "L5\nmodal+disc."]
    isc, cov = [], []
    for a in order[:-1]:
        v = s["arms"][a]["peak"]; isc.append(v["interval_score"]); cov.append(v["coverage_frac"])
    l5 = s["L5_reference_converged"]; isc.append(l5["interval_score"]); cov.append(l5["coverage_frac"])
    col = ["#9aa0a6", "#7bb274", "#1f6fb4", "#d08a2e", "#2a9d3a"]
    x = np.arange(5)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4))
    axes[0].bar(x, isc, color=col, width=0.62)
    axes[0].set_yscale("log"); axes[0].set_ylabel("held-out interval score  (lower = better)")
    axes[0].set_title("Proper score: whole-FRF arms are USELESS\n(sigma_w runaway -> ~1e17 wide)", fontsize=10.5)
    for xi, v in zip(x, isc):
        axes[0].text(xi, v, f"{v:.0e}", ha="center", va="bottom", fontsize=7.5)
    axes[1].bar(x, cov, color=col, width=0.62)
    axes[1].axhline(0.95, color="#cc3333", lw=1.0, ls="--")
    axes[1].text(4.4, 0.95, "0.95 nominal", color="#cc3333", fontsize=8, ha="right", va="bottom")
    axes[1].set_ylabel("held-out coverage"); axes[1].set_ylim(0, 1.08)
    axes[1].set_title("Coverage ALONE is fooled:\nM2/M3 'cover' 100% by being absurdly wide", fontsize=10.5)
    for xi, v in zip(x, cov):
        axes[1].text(xi, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
    for ax in axes:
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5)
    fig.suptitle("Held-out-SENSOR peak |H| across methods: only the modal-feature twin is calibrated AND usable",
                 fontsize=12, y=1.02)
    fig.text(0.0, -0.06,
             "Real ShockSat, 1 split. Sources: out/scores_summary.json (M0-M3, YELLOW non-converged whole-FRF) + "
             "out/heldout_qoi_L5.json (L5, CONVERGED). The proper score exposes what coverage hides: M2/M3 reach "
             "100% coverage only by sigma_w~15 -> ~1e17-wide useless bands; L5 (modal freq + marginal QOI disc.) "
             "is the only method both calibrated (0.91) and sharp enough to act on (interval ~1.4e3).",
             fontsize=7.5, color="#444", va="top", wrap=True)
    p = FIG / "fig_method_comparison.png"; fig.savefig(p); plt.close(fig); return p


def fig_fem_error_sweep():
    """Simulation A: convergence (R-hat) and discrepancy sigma_w vs controlled FEM peak-misalignment delta.
    The whole-FRF likelihood converges only below delta* ~ 1%."""
    a = _load("fem_error_sweep.json")
    if not a:
        return None
    d = np.array([r["delta"] * 100 for r in a["sweep"]])
    rhat = np.array([r["max_rhat"] for r in a["sweep"]])
    sw = np.array([r["sigma_w_med"] for r in a["sweep"]])
    conv = np.array([r["converged"] for r in a["sweep"]])
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.3))
    for ax, y, ylab, gate, gtxt in [
            (axes[0], rhat, "cross-run R-hat  (1 = converged)", 1.05, "1.05 gate"),
            (axes[1], sw, "discrepancy sigma_w  (log-mag)", None, None)]:
        ax.plot(d, y, "-", color="#888", lw=1.2, zorder=1)
        ax.scatter(d[conv], y[conv], s=70, color="#2a9d3a", zorder=3, label="converged")
        ax.scatter(d[~conv], y[~conv], s=70, color="#cc3333", marker="X", zorder=3, label="not converged")
        if gate:
            ax.axhline(gate, color="#cc3333", lw=1.0, ls="--")
            ax.text(d.max(), gate, gtxt, color="#cc3333", fontsize=8, ha="right", va="bottom")
        ax.axvspan(0, 1.0, color="#e8f5e9", zorder=0)
        ax.set_xlabel("controlled FEM peak misalignment  delta  [%]")
        ax.set_ylabel(ylab)
    axes[0].set_yscale("log"); axes[0].legend(fontsize=8, frameon=False, loc="upper left")
    axes[0].set_title("Convergence breaks above delta* ~ 1%", fontsize=10.5)
    axes[1].set_title("sigma_w runs away across delta* (0.44 -> 3.76)", fontsize=10.5)
    axes[1].annotate("delta*\n~1%", (1.0, sw.max() * 0.5), color="#2a9d3a", fontsize=9, ha="center")
    fig.suptitle("Simulation A (SYNTHETIC): when does the whole-FRF magnitude likelihood work?  Only for peaks "
                 "aligned within ~1%", fontsize=11.5, y=1.02)
    fig.text(0.0, -0.06,
             "Synthetic truth = FEM(theta=1) with per-mode frequency perturbation (1+delta*xi)^2, xi=+-1 (same mode "
             "shapes = pure peak misalignment). Faithful additive Schneider M2 whole-FRF, TMCMC n=2000 x 4. Source: "
             "out/fem_error_sweep.json. delta=0 reproduces the synthetic-study convergence (R-hat 1.000, sigma_w "
             "0.03); delta>=2% goes multimodal (sigma_w runaway). Real ShockSat misalignment >> 1% -> the real-data "
             "negative (R-hat 104-129) is FEM coarseness, not method failure. Pre-test lever: align FEM peaks to ~1%.",
             fontsize=7.5, color="#444", va="top", wrap=True)
    p = FIG / "fig_fem_error_sweep.png"; fig.savefig(p); plt.close(fig); return p


def fig_hard_locations():
    """The consistently-failing held-out locations (MC pattern) on the structure (X-Z), with all eligible
    channels for context. Loads geometry/channels live (no fabricated coords)."""
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).resolve().parent))
    import realfrf as rf
    mp = _load("mc_pattern_summary.json")
    if not mp:
        return None
    fail = mp["consistently_fail_ch"]
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    gg = np.load(WS.parent / "statfem_shocksat_eval_20260616" / "data" / "group_geometry.npz", allow_pickle=True)
    nx, nz = np.asarray(gg["xyz"])[:, 0], np.asarray(gg["xyz"])[:, 2]
    elig = dr >= 30.0
    fig, ax = plt.subplots(figsize=(7.6, 6.6))
    ax.scatter(nx, nz, s=1.5, c="#dddddd", lw=0, zorder=0)
    cx = ch.coords[:, 0]; cz = ch.coords[:, 2]
    ax.scatter(cx[elig], cz[elig], s=22, facecolors="none", edgecolors="#3a7", lw=0.8, label="held-out OK (eligible)", zorder=2)
    for d in fail:
        if d in ch.daq:
            p = ch.daq.index(d)
            ax.scatter(ch.coords[p, 0], ch.coords[p, 2], s=150, c="#cc2222", edgecolor="k", lw=0.8, zorder=4)
            ax.annotate(f"ch{d}", (ch.coords[p, 0], ch.coords[p, 2]), xytext=(6, 4), textcoords="offset points",
                        fontsize=9, color="#8a1111", weight="bold")
    ax.scatter([], [], s=120, c="#cc2222", edgecolor="k", label=f"consistently FAIL ({len(fail)})")
    ax.scatter([rf.IMPACT_XYZ[0]], [rf.IMPACT_XYZ[2]], marker="*", s=240, c="k", label="impact (drive)", zorder=5)
    ax.set_xlabel("x [in]"); ax.set_ylabel("height z [in]")
    ax.set_title("Hard-to-predict held-out locations (consistent MC failures)", fontsize=12)
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    ax.text(0.0, -0.13, f"Channels that miss the 95% held-out band in (almost) every split: {fail} "
            f"(pass-rate corr with dynamic range +0.06 = none, with height -0.10). Grey = FEM structure (X-Z). "
            f"NOT a mapping artifact (snap shift <1%). Real ShockSat, 25-split MC.", transform=ax.transAxes,
            fontsize=7.5, color="#444", va="top", wrap=True)
    p = FIG / "fig_hard_locations.png"; fig.savefig(p, bbox_inches="tight"); plt.close(fig); return p


def fig_schematic():
    """Method/observable schematic (pure diagram): real impact-hammer FRF -> two likelihood branches
    (whole-|H| FAILS vs modal-feature WORKS) -> FEM twin theta -> held-out-sensor QOI. No fabricated data."""
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    fig, ax = plt.subplots(figsize=(11.5, 5.6)); ax.axis("off")
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)

    def box(x, y, w, h, text, fc, ec="#333", fs=9):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.5",
                                    fc=fc, ec=ec, lw=1.2, zorder=2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, zorder=3, wrap=True)

    def arrow(x0, y0, x1, y1, color="#555"):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=14,
                                     color=color, lw=1.4, zorder=1))

    box(1, 60, 22, 26, "REAL ShockSat\nimpact hammer (1 hit,\nnode 22951, +X)\n-> measured single-impact\n"
        "FRF |H1| [g/lbf]\n87 ch, 45-260 Hz", "#eef3f8", fs=8.5)
    box(30, 78, 30, 14, "Likelihood A: WHOLE-|H| magnitude\n(every frequency point)", "#fde8e8", ec="#cc3333")
    box(30, 56, 30, 14, "Likelihood B: MODAL peak FREQUENCIES\n(features from the same FRF)", "#e6f5e9", ec="#2a9d3a")
    box(66, 78, 32, 14, "FAILS: multimodal / singular\nNUTS R-hat 104, TMCMC 129,\nsigma_w runaway", "#fde8e8", ec="#cc3333", fs=8.5)
    box(66, 56, 32, 14, "WORKS: CONVERGES\nR-hat 1.002, held-out modes 6/6", "#e6f5e9", ec="#2a9d3a", fs=8.5)
    box(40, 33, 30, 13, "FEM 9-group twin: calibrate theta\n(4 identifiable: bottom/top box,\nplates, cross-beam)", "#eef3f8", fs=8.5)
    box(36, 8, 38, 15, "HELD-OUT-SENSOR QOI: observe a channel\nsubset -> predict UNSEEN channels'\npeak |H| / band-GRMS -> proper score\n"
        "(calibrated 0.91, but WIDE x2.7)", "#eef3f8", fs=8.5)

    arrow(23, 76, 30, 85); arrow(23, 70, 30, 63)
    arrow(60, 85, 66, 85); arrow(60, 63, 66, 63)
    arrow(82, 56, 60, 46)            # working branch -> theta
    arrow(55, 33, 55, 23)            # theta -> held-out QOI
    ax.text(50, 97, "StatFEM on the REAL ShockSat: the observable/likelihood CHOICE decides feasibility",
            ha="center", fontsize=12, weight="bold")
    ax.text(0, 1.5, "Schematic of THIS run (not a paper figure). The whole-FRF-magnitude observable is a dead end "
            "on the coarse FEM (Sim A: needs <=~1% peak alignment); the modal-feature observable converges and "
            "yields calibrated held-out-sensor predictions. Plain 9-group ShockSat, matched-path, no SOL111.",
            fontsize=7.5, color="#444")
    p = FIG / "fig_schematic.png"; fig.savefig(p, bbox_inches="tight"); plt.close(fig); return p


def fig_heldout_frf():
    """Predicted |H| band at a HELD-OUT channel (modal-calibrated twin) vs the real measured FRF. Log-frequency."""
    d = _load("heldout_frf_band.json")
    if not d:
        return None
    f = np.array(d["freqs_hz"]); tru = np.array(d["measured_absH"])
    lo, med, hi = np.array(d["pred_lo"]), np.array(d["pred_med"]), np.array(d["pred_hi"])
    wq = np.array(d["quality_weight"]); sig = d.get("sigma_qoi", 0.0)
    det = np.array(d.get("deterministic_nasa_absH", med))
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    # updated twin: total (param + model-form) then param-only band
    ax.fill_between(f, med * np.exp(-1.96 * sig), med * np.exp(1.96 * sig), color="#cfd3d6", alpha=0.8, lw=0,
                    label="total uncertainty (with model-form error)")
    ax.fill_between(f, lo, hi, color="#9ec6e6", alpha=0.8, lw=0, label="param uncertainty (theta posterior)")
    ax.plot(f, med, color="#1f6fb4", lw=1.3, label="updated twin median")
    # deterministic as-received NASA-correlated FEM (prior mean theta=1) + PSD margins
    ax.plot(f, det, color="k", lw=1.1, ls="-.", label="as-received NASA FEM (theta=1, deterministic)")
    ax.plot(f, det * 1.4125, color="#e8820c", lw=0.9, ls=":", label="+3 dB PSD margin (x1.41 amplitude)")
    ax.plot(f, det * 1.9953, color="#cc3333", lw=0.9, ls=":", label="+6 dB PSD margin (x2.0 amplitude)")
    ax.plot(f, tru, color="#c44", lw=1.4, label="measured |H1| (truth, held-out)")
    ax2 = ax.twinx(); ax2.fill_between(f, 0, wq, color="#bbb", alpha=0.2, lw=0, zorder=0)
    ax2.set_ylim(0, 1); ax2.set_ylabel("single-hit quality weight", color="#888", fontsize=9); ax2.tick_params(labelsize=8)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("|accelerance| [g/lbf]")
    ax.set_title(f"Held-out channel {d['channel_daq']}: as-received FEM + margins, updated twin, vs real FRF", fontsize=11.5)
    ax.legend(fontsize=7.2, frameon=False, loc="upper left", ncol=2)
    flag = "CONVERGED" if d["calib_converged"] else f"NOT-converged R-hat {d['calib_rhat']:.2f}"
    ax.text(0.0, -0.19,
            f"ONE representative (median dynamic-range) held-out channel {d['channel_daq']}; ALL 32 held-out "
            f"channels are in out/heldout_report.pdf. Held out of calibration (split seed {d['split_seed']}, "
            f"{d['n_observed']} obs ch; {flag}, R-hat {d['calib_rhat']:.3f}). Dash-dot = as-received NASA-correlated "
            f"FEM (prior mean theta=1; NASA SOL111 not used = mismatched path; our reduced model reproduces the NASA "
            f"FEM eigenfreqs to 3e-10). Dotted = +3/+6 dB PSD margins above it (x1.41 / x2.0 in amplitude, since "
            f"PSD ~ |H|^2). The twin places the RESONANCE FREQUENCIES; per-channel amplitude error is FEM MODE-SHAPE "
            f"model-form error (NOT the node mapping: snap->interp shifts the peak <1% median, vs the several-fold "
            f"measured mismatch -- out/mapping_sensitivity.json), absorbed by a ~x2.7 amplitude discrepancy. Real "
            f"ShockSat, 1 hit (YELLOW). Grey fill = single-hit quality weight.", transform=ax.transAxes,
            fontsize=7.3, color="#444", va="top", wrap=True)
    p = FIG / "fig_heldout_frf.png"; fig.savefig(p); plt.close(fig); return p


def fig_mc_distributions():
    """Score distributions across the >=25 channel-split MC configs (the CONVERGED L5 method)."""
    m = _load("mc_summary.json")
    if not m:
        return None
    ps = m["per_split"]
    pk_cov = [r["peak_cov"] for r in ps]; pk_is = [r["peak_is"] for r in ps]
    bd_cov = [r["band_cov"] for r in ps]
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.3))
    axes[0].hist(pk_cov, bins=np.linspace(0, 1.0, 11), color="#1f6fb4", alpha=0.8)
    axes[0].axvline(0.95, color="#cc3333", lw=1.0, ls="--")
    axes[0].set_xlabel("held-out PEAK coverage"); axes[0].set_ylabel(f"# of {len(ps)} splits")
    axes[0].set_title(f"Coverage (med {np.median(pk_cov):.2f})", fontsize=10.5)
    axes[1].hist(bd_cov, bins=np.linspace(0, 1.0, 11), color="#d08a2e", alpha=0.8)
    axes[1].axvline(0.95, color="#cc3333", lw=1.0, ls="--")
    axes[1].set_xlabel("held-out BAND coverage"); axes[1].set_title(f"Coverage (med {np.median(bd_cov):.2f})", fontsize=10.5)
    axes[2].hist(pk_is, bins=12, color="#2a9d3a", alpha=0.8)
    axes[2].set_xlabel("held-out PEAK interval score"); axes[2].set_title(f"Proper score (med {np.median(pk_is):.0f})", fontsize=10.5)
    fig.suptitle(f"Monte-Carlo over {len(ps)} channel splits (CONVERGED L5+discrepancy): score DISTRIBUTIONS",
                 fontsize=12, y=1.02)
    cf = m.get("calib_converged_frac", 0)
    fig.text(0.0, -0.06,
             f"Source: out/mc_summary.json. {len(ps)} random observed/held-out channel splits (1 impact, 1 hit -- "
             f"split axis ONLY, labeled reduction). L5 calibration converged on {cf*100:.0f}% of splits. The "
             f"calibrated twin's held-out QOI is stable across splits (coverage near 0.95). Real ShockSat (YELLOW: "
             f"1 hit / 1 impact).", fontsize=7.5, color="#444", va="top", wrap=True)
    p = FIG / "fig_mc_distributions.png"; fig.savefig(p); plt.close(fig); return p


if __name__ == "__main__":
    made = []
    for fn in (fig_error_participation, fig_arms_comparison, fig_scoring_suite, fig_method_comparison,
               fig_fem_error_sweep, fig_schematic, fig_heldout_frf, fig_mc_distributions):
        p = fn()
        made.append(str(p.name) if p else f"SKIP {fn.__name__}")
        print(("made " + p.name) if p else f"SKIP {fn.__name__} (missing source)")
    print("figures:", made)
