"""
Figures for the FIM identifiability / experiment-design packet.
Tufte discipline (per .claude/skills/tufte-data-graphics/SKILL.md): maximize data-ink,
direct labels over legends, small multiples on shared scales, viridis (no jet), documented
scales/units in captions, show the comparison (prior vs posterior, stiff vs sloppy).
All inputs are the saved JSON/NPZ artifacts -- no recomputation, no fabricated numbers.
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

R = json.load(open(os.path.join(ROOT, "fim_results.json")))
Z = np.load(os.path.join(ROOT, "arrays_fim.npz"), allow_pickle=True)
PROF = json.load(open(os.path.join(ROOT, "profile_likelihood.json")))
PNAMES = R["param_names"]
SHORT = {"tray_E": "tray E", "strut_EA": "strut EA", "strut_EI": "strut EI",
         "joint_axial": "joint axial", "joint_lateral": "joint lateral"}
DESIGNS = ["freq_only", "one_sensor_corner_z", "two_sensor_transmissibility"]
DLAB = {"freq_only": "frequencies only", "one_sensor_corner_z": "1 sensor (drive-point)",
        "two_sensor_transmissibility": "2 sensors (transmissibility)"}
PRIOR_SD = R["assumptions"]["PRIOR_SD"]


def _despine(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ---------------------------------------------------------------------------
def fig_eigenspectrum():
    """FIM eigenvalue spectrum (sloppy-models view) for the 3 designs, shared log y."""
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.0), sharey=True)
    thr_prior = R["assumptions"]["IDENT_PRIOR_eig_threshold"]
    thr_well = R["assumptions"]["IDENT_WELL_eig_threshold"]
    for ax, name in zip(axes, DESIGNS):
        ev = np.clip(np.array(R["designs"][name]["fim_eigenvalues"], float), 1e-12, None)
        x = np.arange(1, len(ev) + 1)
        ax.scatter(x, ev, s=55, color="#21908d", zorder=3)
        ax.vlines(x, 1e-12, ev, color="#21908d", lw=1.2, zorder=2)
        ax.axhline(thr_prior, color="0.25", lw=1.0, ls="--")
        ax.axhline(thr_well, color="0.6", lw=1.0, ls=":")
        ax.set_yscale("log")
        ax.set_title(DLAB[name], fontsize=10)
        ax.set_xlabel("eigen-direction (stiff $\\rightarrow$ sloppy)", fontsize=9)
        ax.set_xticks(x)
        _despine(ax)
        nid = R["designs"][name]["n_identifiable_directions"]
        ax.text(0.5, ev[0] * 2, f"{nid} identifiable", fontsize=9, color="#21908d")
    axes[0].set_ylabel("FIM eigenvalue  [1 / (relative-change)$^2$]", fontsize=9)
    axes[-1].text(len(x) + 0.1, thr_prior, " posterior sd = prior sd", va="center",
                  fontsize=8, color="0.25")
    axes[-1].text(len(x) + 0.1, thr_well, " posterior sd = 0.10", va="center",
                  fontsize=8, color="0.5")
    fig.suptitle("Fisher-information spectrum: 3 stiff directions, then a cliff to 2 sloppy ones\n"
                 "(hexapod tray FEM, 8 modes ≤570 Hz; same conclusion for 1 vs 2 sensors)",
                 fontsize=11)
    fig.tight_layout(rect=[0, 0, 0.93, 0.95])
    fig.savefig(os.path.join(FIG, "fig1_fim_eigenspectrum.png"), dpi=150)
    plt.close(fig)


def fig_sensitivity_heatmap():
    """Per-mode frequency sensitivity |df_i/dtheta_g| (Hz per unit relative change)."""
    dF = np.array(Z["dF"])           # (nmodes, nparam)
    freqs = np.array(Z["freqs"])
    A = np.abs(dF).T                 # (nparam, nmodes)
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    Aplot = np.log10(A + 1e-4)
    im = ax.imshow(Aplot, aspect="auto", cmap="viridis", origin="lower")
    ax.set_yticks(range(len(PNAMES)))
    ax.set_yticklabels([SHORT[p] for p in PNAMES], fontsize=9)
    ax.set_xticks(range(len(freqs)))
    ax.set_xticklabels([f"{f:.0f}" for f in freqs], fontsize=8)
    ax.set_xlabel("mode natural frequency [Hz]  (mode 1 $\\rightarrow$ 8)", fontsize=9)
    for i in range(len(PNAMES)):
        for j in range(len(freqs)):
            ax.text(j, i, f"{A[i, j]:.2g}", ha="center", va="center",
                    fontsize=6.5, color="w" if Aplot[i, j] < Aplot.max() - 1.2 else "0.1")
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cb.set_label("$\\log_{10}$ |$df_i/d\\theta_g$|  [Hz/unit]", fontsize=8)
    ax.set_title("Frequency sensitivity: strut EI only shows up in the 542/570 Hz tray-flex modes;\n"
                 "joint-lateral column is exactly zero (moment-free spherical joints carry no lateral load)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_sensitivity_heatmap.png"), dpi=150)
    plt.close(fig)


def fig_param_identifiability():
    """Prior sd vs marginal posterior sd per parameter, 3 designs as small multiples."""
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.8), sharey=True)
    y = np.arange(len(PNAMES))
    for ax, name in zip(axes, DESIGNS):
        msd = R["designs"][name]["marginal_posterior_sd"]
        post = [msd[p] for p in PNAMES]
        ax.barh(y, [PRIOR_SD] * len(PNAMES), color="0.85", height=0.6, zorder=1)
        ax.barh(y, post, color="#440154", height=0.36, zorder=2)
        ax.set_yticks(y)
        ax.set_yticklabels([SHORT[p] for p in PNAMES], fontsize=9)
        ax.set_xlabel("posterior sd of $\\theta$ (relative)", fontsize=9)
        ax.set_title(DLAB[name], fontsize=10)
        ax.axvline(PRIOR_SD, color="0.4", lw=1.0, ls="--")
        for yi, p in zip(y, PNAMES):
            red = R["designs"][name]["prior_to_post_sd_reduction"][p]
            ax.text(msd[p] + 0.005, yi, f"{red:.0f}x" if red >= 1.5 else "~prior",
                    va="center", fontsize=7.5,
                    color="#440154" if red >= 1.5 else "0.5")
        _despine(ax)
    axes[0].invert_yaxis()
    axes[0].text(PRIOR_SD, -0.7, "prior sd = 0.30", fontsize=8, color="0.4", ha="center")
    fig.suptitle("What the test can learn: dark bar = posterior sd, grey = prior. Joints stay at the prior\n"
                 "(near-rigid + moment-free $\\Rightarrow$ unidentifiable); strut EA / tray E / strut EI tighten",
                 fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(FIG, "fig3_param_identifiability.png"), dpi=150)
    plt.close(fig)


def fig_band_sensitivity():
    """Identifiable count and per-param posterior sd vs the resolved frequency band."""
    sb = R["sensitivity"]["vs_resolved_band"]
    fmax = [s["max_freq_hz"] for s in sb]
    nid = [s["n_identifiable"] for s in sb]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.0))
    ax1.step(fmax, nid, where="post", color="#21908d", lw=2)
    ax1.scatter(fmax, nid, color="#21908d", s=40, zorder=3)
    ax1.set_xscale("log")
    ax1.set_xlabel("highest resolved mode frequency [Hz]", fontsize=9)
    ax1.set_ylabel("identifiable parameters", fontsize=9)
    ax1.set_yticks([0, 1, 2, 3])
    ax1.set_ylim(0, 3.4)
    ax1.set_title("How many parameters the test supports\nvs the band it resolves", fontsize=10)
    # annotate only where the identifiable count first reaches each level (avoid overlap)
    seen = set()
    for s in sb:
        n = s["n_identifiable"]
        if n not in seen:
            seen.add(n)
            ax1.annotate(f"+{SHORT[['','strut_EA','tray_E','strut_EI'][n]]}\n({s['n_modes']} modes, {s['max_freq_hz']:.0f} Hz)"
                         if n >= 1 else "",
                         (s["max_freq_hz"], n), textcoords="offset points",
                         xytext=(6, -2), fontsize=7, color="0.35", va="top")
    _despine(ax1)
    # per-param posterior sd vs band
    colors = plt.cm.viridis(np.linspace(0.1, 0.85, len(PNAMES)))
    ax2.text(fmax[-1] * 1.02, PRIOR_SD, "joints\n(≈prior, never learned)", color="#5dc863",
             fontsize=7.5, va="center")
    label_y = {"tray_E": 0.041, "strut_EI": 0.022, "strut_EA": 0.006}
    for p, c in zip(PNAMES, colors):
        sd = [s["marginal_sd"][p] for s in sb]
        ax2.plot(fmax, sd, color=c, lw=1.6, marker="o", ms=3)
        if p in label_y:
            ax2.text(fmax[-1] * 1.02, label_y[p], SHORT[p], color=c, fontsize=8, va="center")
    ax2.axhline(PRIOR_SD, color="0.4", lw=1.0, ls="--")
    ax2.text(fmax[0], PRIOR_SD * 1.02, "prior sd", fontsize=8, color="0.4")
    ax2.set_xscale("log")
    ax2.set_xlabel("highest resolved mode frequency [Hz]", fontsize=9)
    ax2.set_ylabel("posterior sd of $\\theta$ (relative)", fontsize=9)
    ax2.set_title("Each parameter becomes learnable only once\nits driving mode is in band", fontsize=10)
    ax2.set_xlim(fmax[0] * 0.9, fmax[-1] * 1.35)
    _despine(ax2)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_band_sensitivity.png"), dpi=150)
    plt.close(fig)


def fig_experiment_design():
    """Where to measure (D-optimality map) and where to hit (modes excited) over the tray."""
    wm = R["experiment_design"]["where_to_measure_1sensor"]
    wh = R["experiment_design"]["where_to_hit"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.3))
    for ax, data, key, title, cb_lab in (
        (ax1, wm, "logdet", "Where to MEASURE (1 accelerometer, z)\ncolor = D-optimality, log det FIM",
         "log det FIM (higher = more informative)"),
        (ax2, wh, "n_modes_excited", "Where to HIT (vertical tap)\ncolor = # modes excited >20% of peak",
         "modes excited")):
        x = np.array([d["x"] for d in data]) * 1e3   # mm
        y = np.array([d["y"] for d in data]) * 1e3
        c = np.array([d[key] for d in data], float)
        sc = ax.scatter(x, y, c=c, cmap="viridis", s=70, edgecolor="0.3", lw=0.3)
        best = int(np.argmax(c))
        ax.scatter([x[best]], [y[best]], marker="*", s=260, color="#fde725",
                   edgecolor="0.1", lw=0.6, zorder=4)
        ax.annotate("best", (x[best], y[best]), textcoords="offset points",
                    xytext=(6, 6), fontsize=8)
        ax.set_aspect("equal")
        ax.set_xlabel("x [mm]", fontsize=9); ax.set_ylabel("y [mm]", fontsize=9)
        ax.set_title(title, fontsize=9.5)
        fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04).set_label(cb_lab, fontsize=8)
        _despine(ax)
    fig.suptitle("Pre-test experiment design on the 300x300 mm tray (spatial axes linear = physical mm)",
                 fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(FIG, "fig5_experiment_design.png"), dpi=150)
    plt.close(fig)


def fig_qoi_vs_data():
    """QOI need (|dQOI/dtheta|) vs data constraint (prior/post reduction) per parameter."""
    gq = R["qoi"]["d_qoi_d_theta"]
    absg = np.array([abs(gq[p]) for p in PNAMES])
    absg = absg / absg.max()
    red = np.array([R["designs"]["one_sensor_corner_z"]["prior_to_post_sd_reduction"][p]
                    for p in PNAMES])
    redn = red / red.max()
    y = np.arange(len(PNAMES))
    fig, ax = plt.subplots(figsize=(8.0, 3.8))
    ax.barh(y + 0.18, absg, height=0.34, color="#fde725", label="QOI needs it")
    ax.barh(y - 0.18, redn, height=0.34, color="#440154", label="test constrains it")
    ax.set_yticks(y); ax.set_yticklabels([SHORT[p] for p in PNAMES], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("normalized magnitude (each series scaled to its own max)", fontsize=9)
    ax.text(absg[1] - 0.02, 0.82, "QOI sensitivity", color="#b8a800", fontsize=8.5, ha="right")
    ax.text(redn[1] - 0.02, 1.18, "data constraint", color="#440154", fontsize=8.5, ha="right")
    frac = R["designs"]["one_sensor_corner_z"]["qoi_fraction_in_sloppy_subspace"]
    ax.set_title(f"QOI (payload transmissibility) vs identifiability: the QOI is driven by the SAME\n"
                 f"parameters the test can constrain (fraction of QOI sensitivity in sloppy subspace = {frac})",
                 fontsize=9.5)
    _despine(ax)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6_qoi_vs_data.png"), dpi=150)
    plt.close(fig)


def fig_profile():
    """Profile-likelihood chi^2 vs each theta (others re-optimized): flat = unidentifiable."""
    fig, axes = plt.subplots(1, len(PNAMES), figsize=(13, 3.2), sharey=True)
    for ax, p in zip(axes, PNAMES):
        pr = PROF["profiles"][p]
        g = np.array(pr["grid"]); c = np.array(pr["chi2_clean"])
        ax.plot(g, c, color="#21908d", lw=1.8)
        ax.axhline(1.0, color="0.5", lw=0.9, ls=":")
        ax.set_title(SHORT[p], fontsize=9.5)
        ax.set_xlabel("$\\theta$ (relative)", fontsize=8)
        flat = pr["flat_unidentifiable"]
        sd = pr["profile_implied_sd"]
        tag = "FLAT\n(unidentifiable)" if flat else f"sd$\\approx${sd:.2g}"
        ax.text(0.5, 0.86, tag, transform=ax.transAxes, ha="center", fontsize=8,
                color="#b30000" if flat else "#21908d")
        _despine(ax)
    axes[0].set_ylabel("$\\chi^2$ misfit", fontsize=9)
    axes[0].text(0.02, 0.6, "$\\Delta\\chi^2$=1", transform=axes[0].transAxes,
                 fontsize=7.5, color="0.5")
    fig.suptitle("Profile likelihood confirms the FIM: sharp valley = identifiable, flat = not. "
                 "Joints are flat across $\\pm$30% (others re-optimized) $\\Rightarrow$ globally unidentifiable",
                 fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(os.path.join(FIG, "fig7_profile_likelihood.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    fig_eigenspectrum()
    fig_sensitivity_heatmap()
    fig_param_identifiability()
    fig_band_sensitivity()
    fig_experiment_design()
    fig_qoi_vs_data()
    fig_profile()
    print("figures written to", FIG)
