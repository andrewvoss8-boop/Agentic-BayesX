#!/usr/bin/env python3
"""
Consolidation figures for the Bilionis review packet (Agentic BayesX / ShockSat).

These are NEW summary figures built ONLY from numbers already produced and saved
by earlier checker-backed / exploratory threads. Every number is traced in the
docstring of its function to the source out/*.json file. No new science is run
here; this is reporting/consolidation.

Tufte gate applied (.claude/skills/tufte-data-graphics/SKILL.md):
- bars start at 0; lie factor ~1; direct labels; few hues; log axes labelled;
- captions carry the quantity + source + takeaway; no chartjunk.

Run:  python3 make_review_figs.py
Out:  ../figures/{fig_new_metric,fig_theta_movement,fig_remesh_plateau,fig_wide_ci}.png
"""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIG = Path(__file__).resolve().parent.parent / "figures"
FIG.mkdir(exist_ok=True)

# ---- shared style (data-ink, legible deck fonts) --------------------------
plt.rcParams.update({
    "font.size": 13, "axes.titlesize": 15, "axes.labelsize": 13,
    "xtick.labelsize": 12, "ytick.labelsize": 12, "legend.fontsize": 12,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#dddddd", "grid.linewidth": 0.6,
    "figure.dpi": 140, "savefig.dpi": 140, "savefig.bbox": "tight",
})
NAVY = "#1f335e"; ORANGE = "#d1701c"; TEAL = "#1b7837"; RED = "#b2182b"
GREY = "#606060"; BLUE = "#3a66b0"


def _src(ax, text):
    ax.figure.text(0.005, 0.005, text, fontsize=7.5, color=GREY, ha="left", va="bottom")


# ===========================================================================
def fig_new_metric():
    """NEW METRIC: mean-function FRF correlation vs the original inherited FEM.
    Source: shocksat_psd_envelope_twin_20260623/out/frf_comparison.json
      median_logH_corr_original = 0.269 ; median_logH_corr_updated = 0.338 ;
      frac_channels_updated_better = 0.70 ; n_channels = 84 ; reference = +X.
      (deterministic FEM modal participations + ONE global gain; updated =
       measured modal frequency + damping calibration — apples-to-apples mean.)
    """
    orig, upd, frac, n = 0.269, 0.338, 0.70, 84
    fig, ax = plt.subplots(figsize=(7.2, 5.2))
    xs = [0, 1]
    bars = ax.bar(xs, [orig, upd], width=0.55, color=[ORANGE, NAVY], zorder=3)
    ax.set_xticks(xs)
    ax.set_xticklabels(["Original inherited FEM\n(nominal freq + damping)",
                        "Bayesian-updated mean\n(measured freq + damping)"])
    ax.set_ylabel("median per-channel correlation\nof log|H| (twin mean vs measured), 84 ch")
    ax.set_ylim(0, 1.0)
    for x, v in zip(xs, [orig, upd]):
        ax.text(x, v + 0.018, f"{v:.3f}", ha="center", va="bottom",
                fontsize=15, fontweight="bold")
    # improvement arrow
    ax.annotate("", xy=(1, upd), xytext=(0, orig),
                arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=2.2))
    ax.text(0.42, (orig + upd) / 2 + 0.12,
            f"+{upd-orig:.3f}  (+{100*(upd-orig)/orig:.0f}%)\n{int(frac*100)}% of {n} channels improve",
            ha="center", va="bottom", color=TEAL, fontsize=12.5, fontweight="bold")
    # "useful" reference
    ax.axhline(0.70, color=GREY, lw=1.2, ls="--", zorder=2)
    ax.text(1.46, 0.70, "≈ usable\ncorrelation", color=GREY, fontsize=10.5,
            ha="right", va="center")
    ax.set_title("New metric — does updating move the MEAN closer to the data?\n"
                 "Real ShockSat +X, 45–260 Hz", color=NAVY)
    ax.text(0.5, 0.94, "Updating helps (+26%) but the mean stays far from usable",
            transform=ax.transAxes, ha="center", fontsize=11.5, color=RED,
            style="italic")
    _src(ax, "src: psd_envelope/out/frf_comparison.json | EXPLORATORY/YELLOW (no checker) | log|H| Pearson corr, in-sample participation fit")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(FIG / "fig_new_metric.png")
    plt.close(fig)


# ===========================================================================
def fig_theta_movement():
    """How much did the posterior MEAN move from the inherited FEM (theta=1)?
    Source: shocksat_psd_envelope_twin_20260623/out/bayes_update.json
      theta_posterior_2.5_50_97.5 (NUTS, R-hat 1.0022, ESS 2243, 0 div, 4 chains).
    """
    # (name, lo, med, hi, identifiable?)
    rows = [
        ("bottom_box", 0.918, 0.960, 0.999, True),
        ("plates",     0.932, 0.998, 1.052, True),
        ("top_box",    0.950, 1.028, 1.102, True),
        ("cross_beam", 0.658, 0.941, 1.387, False),
        ("joints",     0.533, 0.823, 1.364, False),
        ("contact",    0.599, 0.991, 1.635, False),
        ("al_welds",   0.616, 1.011, 1.640, False),
        ("angle_brackets", 0.600, 0.968, 1.647, False),
        ("steel_welds",0.627, 1.020, 1.686, False),
    ]
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    ys = np.arange(len(rows))[::-1]
    for y, (name, lo, med, hi, ident) in zip(ys, rows):
        c = NAVY if ident else GREY
        ax.plot([lo, hi], [y, y], color=c, lw=2.4 if ident else 1.6,
                solid_capstyle="round", zorder=3)
        ax.plot(med, y, "o", color=c, ms=9, zorder=4)
        tag = "identifiable" if ident else "prior-dominated"
        ax.text(hi + 0.03, y, f"{name}  ({tag})", va="center", fontsize=11,
                color=c)
    ax.axvline(1.0, color=ORANGE, lw=1.6, ls="--", zorder=2)
    ax.text(1.0, -1.05, "inherited FEM (θ=1)", color=ORANGE,
            ha="center", va="center", fontsize=10.5)
    ax.set_yticks([])
    ax.set_ylim(-1.7, len(rows) - 0.25)
    ax.set_xlim(0.45, 2.05)
    ax.set_xlabel("posterior stiffness multiplier θ_g  (median, 95% credible interval)")
    ax.set_title("Bayesian updating moved the mean only MINORLY\n"
                 "Identifiable groups shifted 0–4%; the rest fell back to the prior",
                 color=NAVY)
    _src(ax, "src: psd_envelope/out/bayes_update.json | NUTS R-hat 1.0022, ESS 2243, 0 div, 4 chains | held-out freq err 3.33%→2.68%")
    fig.tight_layout()
    fig.savefig(FIG / "fig_theta_movement.png")
    plt.close(fig)


# ===========================================================================
def fig_remesh_plateau():
    """Agentic remeshing + model-form edits: FRF correlation PLATEAUS ~0.4.
    Source: psd_envelope/out/correlate_all.json (+ modelform_sweep.json).
      Same metric for all: all-channel participation LSQ + full measured damping,
      FRF_logmag_corr_median over 84 ch x 4 refs. baseline=0.296; best al_rho_lo=0.379.
    """
    baseline = 0.296
    # edit medians (excluding the baseline row), correlate_all + modelform_sweep
    edits = [0.305, 0.307, 0.315, 0.210, 0.202, 0.295, 0.296, 0.308, 0.359,
             0.309, 0.215, 0.231, 0.313, 0.330, 0.199, 0.275,            # correlate_all
             0.237, 0.323, 0.379, 0.305, 0.365, 0.312, 0.278, 0.293,
             0.192, 0.280, 0.349, 0.224, 0.341]                          # modelform_sweep
    best = max(edits)
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    rng = np.random.default_rng(0)
    jit = rng.uniform(-0.13, 0.13, size=len(edits))
    ax.scatter(jit, edits, s=42, color=BLUE, alpha=0.75, zorder=3,
               edgecolor="white", linewidth=0.5)
    ax.scatter([0], [baseline], s=160, marker="D", color=ORANGE, zorder=5,
               edgecolor="black", linewidth=0.7)
    ax.text(0.18, baseline, f"inherited FEM  {baseline:.3f}", color=ORANGE,
            va="center", fontsize=11, fontweight="bold")
    ax.text(0.18, best, f"best of {len(edits)} edits  {best:.3f}", color=BLUE,
            va="center", fontsize=11)
    ax.scatter([], [], s=42, color=BLUE, label=f"{len(edits)} mesh / stiffness / mass-distribution edits")
    ax.axhspan(best, 0.40, color="#f3d9c0", alpha=0.5, zorder=1)
    ax.axhline(0.70, color=GREY, lw=1.2, ls="--", zorder=2)
    ax.text(-0.34, 0.70, "≈ usable", color=GREY, fontsize=10.5, va="bottom")
    ax.text(-0.34, 0.385, "ceiling ≈ 0.4", color=ORANGE, fontsize=10.5, va="bottom")
    ax.set_xlim(-0.38, 0.95)
    ax.set_ylim(0, 1.0)
    ax.set_xticks([])
    ax.set_ylabel("median per-channel log|H| correlation\n(twin mean vs measured), 84 ch × 4 refs")
    ax.set_title("Agentic remeshing CANNOT crack per-point FRF correlation\n"
                 "~30 data-guided model-form edits all plateau below ~0.4",
                 color=NAVY)
    ax.legend(loc="upper right", frameon=False)
    _src(ax, "src: psd_envelope/out/correlate_all.json + modelform_sweep.json | EXPLORATORY/YELLOW | all-channel-LSQ participation metric (more generous than fig_new_metric)")
    fig.tight_layout()
    fig.savefig(FIG / "fig_remesh_plateau.png")
    plt.close(fig)


# ===========================================================================
def fig_wide_ci():
    """The central honest finding: the trustworthy band is too WIDE to certify.
    Source: psd_envelope/out/probe_seed00.json (clean multi-ref, NUTS converged
      R-hat 1.0016, ESS 1758, 0 div):
      amplitude_discrepancy_sigma_log = 1.604 ;
      sigma_implies_975_band_PSD_dB    = 27.3 ;
      median GRMS ratio twin / FEM+6dB ~ 10-13x (combined 10.2) ;
      FEM+6dB itself leaks 10-61% of held-out band energy (premise break).
    """
    fig, ax = plt.subplots(figsize=(7.6, 5.2))
    labels = ["Usable band\n(≈ +3 dB target)",
              "Standard FEM + 6 dB\nenvelope",
              "Honest Bayesian twin\n95% covering band"]
    vals = [3.0, 6.0, 27.3]   # dB margin needed to cover the held-out data
    colors = [TEAL, ORANGE, RED]
    ys = np.arange(len(labels))[::-1]
    ax.barh(ys, vals, color=colors, zorder=3, height=0.55)
    for y, v in zip(ys, vals):
        ax.text(v + 0.5, y, f"{v:.0f} dB", va="center", fontsize=14,
                fontweight="bold")
    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 33)
    ax.set_xlabel("band margin needed to cover the held-out data  (dB, PSD)")
    ax.set_title("The bands are honest but too WIDE to certify\n"
                 "Twin needs +27 dB to cover — vs the +6 dB engineers use",
                 color=NAVY)
    ax.text(0.97, 0.30,
            "GRMS ≈ 10–13× the FEM+6 dB envelope\n"
            "σ_amp(log) ≈ 1.0–1.6 per channel;\nneed ≲ 0.35 for a usable band\n"
            "(FEM+6 dB itself leaks 10–61% energy)",
            transform=ax.transAxes, ha="right", va="center", fontsize=11,
            color=GREY, bbox=dict(boxstyle="round", fc="#f6f6f6", ec="#cccccc"))
    _src(ax, "src: psd_envelope/out/probe_seed00.json | clean multi-ref, NUTS R-hat 1.0016/ESS 1758/0 div | EXPLORATORY/YELLOW (honest negative)")
    fig.tight_layout()
    fig.savefig(FIG / "fig_wide_ci.png")
    plt.close(fig)


def fig_combine_best():
    """Best remesh + best Bayes, scored on ONE honest metric (no per-channel fitting).
    Source: out/combine_best.json (combine_best.py; NUTS on the al_rho_lo reduced model
      R-hat 1.004, ESS 774, 0 div; self-check reproduced the inherited+cal honest metric = 0.338).
      honest (deterministic participations + 1 global gain): inherited no-cal 0.269; inherited+cal 0.338;
      best-remesh+oracle-cal 0.267; best-remesh+Bayes-theta 0.183. generous LSQ metric (artifact): 0.379.
    """
    import json
    OUT = FIG.parent / "out"
    j = json.load(open(OUT / "combine_best.json")) if (OUT / "combine_best.json").exists() else None
    s = j["summary"] if j else {}
    labels = ["Inherited FEM\n(no calibration)", "Inherited FEM\n+ calibration",
              "Best remesh\n+ calibration", "Best remesh\n+ Bayesian θ"]
    vals = [s.get("inherited_FEM_no_cal (fig)", 0.269),
            s.get("inherited_FEM_calibrated_honest (selfcheck)", 0.338),
            s.get("best_remesh_calibrated_oracle_honest", 0.267),
            s.get("best_remesh_calibrated_BAYES_honest", 0.183)]
    gen = s.get("best_remesh_generous_LSQ_metric (modelform_sweep)", 0.379)
    fig, ax = plt.subplots(figsize=(7.8, 5.2))
    cols = [ORANGE, NAVY, BLUE, RED]
    xs = np.arange(len(labels))
    ax.bar(xs, vals, width=0.6, color=cols, zorder=3)
    for x, v in zip(xs, vals):
        ax.text(x, v + 0.012, f"{v:.3f}", ha="center", va="bottom", fontsize=13, fontweight="bold")
    # the inherited+cal best-honest reference
    ax.axhline(vals[1], color=NAVY, lw=1.1, ls="--", zorder=2)
    ax.text(3.45, vals[1] + 0.004, "best honest = plain calibration", color=NAVY, fontsize=9.5,
            ha="right", va="bottom")
    # generous LSQ artifact marker
    ax.scatter([2], [gen], marker="v", s=130, color="#999999", zorder=5, edgecolor="black", linewidth=0.6)
    ax.text(2, gen + 0.016, f"{gen:.3f}\ngenerous metric\n(fits amplitude/mode\nto the data)", ha="center",
            va="bottom", fontsize=8.5, color="#666666")
    ax.axhline(0.70, color=GREY, lw=1.0, ls=":", zorder=1)
    ax.text(-0.45, 0.70, "≈ usable", color=GREY, fontsize=10, va="bottom")
    ax.set_xticks(xs); ax.set_xticklabels(labels)
    ax.set_ylim(0, 0.8); ax.set_ylabel("median per-channel log|H| correlation\n(honest: deterministic participations + 1 gain)")
    ax.set_title("Best remesh + best Bayes, scored HONESTLY: it does NOT beat plain calibration\n"
                 "the '+0.08' was an amplitude-fitting scoring artifact; the wall is mode shapes",
                 color=NAVY, fontsize=13)
    _src(ax, "src: out/combine_best.json | NUTS on al_rho_lo R-hat 1.004/ESS 774/0 div; self-check reproduced 0.338 | EXPLORATORY/YELLOW")
    fig.tight_layout()
    fig.savefig(FIG / "fig_combine_best.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_new_metric()
    fig_theta_movement()
    fig_remesh_plateau()
    fig_wide_ci()
    fig_combine_best()
    print("wrote 5 figures to", FIG)
