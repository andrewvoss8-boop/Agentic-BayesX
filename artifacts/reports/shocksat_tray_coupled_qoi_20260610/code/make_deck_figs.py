#!/usr/bin/env python3
"""Deck-optimized figures (D13): large fonts, one message each, for the
program slide deck shared with Bilionis / Girolami / Yunis. Reads only out/*
JSON (no recompute, no fabrication). tufte discipline applied.

Outputs to slides/figs/.
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(WS, "out")
FIG = os.path.join(WS, "slides", "figs")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({"font.size": 13, "axes.titlesize": 14,
                     "axes.labelsize": 13, "axes.spines.top": False,
                     "axes.spines.right": False, "legend.frameon": False,
                     "figure.dpi": 150, "savefig.dpi": 150})
C = dict(unc="#b2453c", cpl="#2c5f8a", srs="#7a5195", miles="#c98a1e",
         ref="0.4", good="#3a7d44", warn="#c98a1e", bad="#b2453c")
STAMP = "Agentic BayesX  |  shocksat_tray_coupled_qoi_20260610  |  HYPOTHETICAL coupled QOI (methods demo)"


def stamp(fig, txt=STAMP, col="0.45"):
    fig.text(0.005, 0.004, txt, fontsize=7.5, color=col, ha="left")


def jl(n):
    return json.load(open(os.path.join(OUT, n)))


# ---- D1: program arc / story spine -------------------------------------
def fig_arc():
    fig, ax = plt.subplots(figsize=(12.5, 4.3))
    ax.axis("off")
    steps = [
        ("REAL HARDWARE", "NASA ShockSat\nflight-test article\n(33 measured\nfree-free modes)", "#e8eef4"),
        ("VALIDATED TWIN", "from-scratch FEM\n= NASA NX to 2.5pp\nNUTS R-hat 1.022", "#e3efe6"),
        ("DISCREPANCY\nIS REAL", "sigma_f = 4.6%\n>> 0.3% noise\nonly 4/9 groups ID'd", "#fdf6e3"),
        ("COUPLED LOAD\nQOI", "payload tray\nnet-CG interface\nforce (7004C)", "#e8eef4"),
        ("FORCE LIMITING\nQUANTIFIED", "uncoupled over-\ntest x1.1-2.2\n(validated source)", "#e3efe6"),
        ("QOI IS MOUNT-\nDOMINATED", "mount ~100% of\nQOI variance;\ncalibrated primary <1%", "#fdeeee"),
        ("HONEST\nNEGATIVE", "1 modal survey -> only\n2/6 mount axes ID'd;\ndiscrepancy is the wall", "#fdeeee"),
    ]
    n = len(steps)
    w = 0.123
    gap = (1.0 - n*w)/(n+1)
    for i, (head, body, fc) in enumerate(steps):
        x = gap + i*(w+gap)
        ax.add_patch(plt.Rectangle((x, 0.30), w, 0.46, fc=fc, ec="0.5",
                                   lw=1.0))
        ax.text(x+w/2, 0.70, head, ha="center", va="top", fontsize=10.5,
                weight="bold")
        ax.text(x+w/2, 0.55, body, ha="center", va="top", fontsize=9.0)
        if i < n-1:
            ax.annotate("", xy=(x+w+gap*0.85, 0.53), xytext=(x+w, 0.53),
                        arrowprops=dict(arrowstyle="->", lw=1.6, color="0.45"))
    ax.text(0.5, 0.93, "Driving StatFEM onto the track: a real aerospace "
            "structure, real test data, a real load decision",
            ha="center", fontsize=13.5, weight="bold")
    ax.text(0.5, 0.12, "Every step is artifact-backed and checker-gated; the "
            "honest negative is a finding, not a failure of process.",
            ha="center", fontsize=10.5, color="0.35", style="italic")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    stamp(fig)
    fig.savefig(os.path.join(FIG, "deck_arc.png"), bbox_inches="tight")
    plt.close(fig)


# ---- D2: force-limiting headline (clean, single axis) ------------------
def fig_force_limiting():
    A = np.load(os.path.join(OUT, "nominal_transfers.npz"))
    f = A["freqs"]
    panels = [("x", A["T_unc_xx"], A["T_cpl_xx"],
               "LATERAL (x): 3 rocking/sway modes 76-89 Hz;\nsource ≈ load "
               "apparent mass → DEEP notch"),
              ("z", A["T_unc_zz"], A["T_cpl_zz"],
               "VERTICAL (z): one bounce mode at 116 Hz (SDOF-like);\nsource "
               "≫ load apparent mass → SHALLOW notch")]
    fig, axs = plt.subplots(1, 2, figsize=(12.4, 5.0), sharey=True)
    for ax, (axn, u, c, note) in zip(axs, panels):
        u, c = np.abs(u), np.abs(c)
        ratio = c/np.maximum(u, 1e-9)
        ax.loglog(f, u, color=C["unc"], lw=2.2)
        ax.loglog(f, c, color=C["cpl"], lw=2.2)
        iu, ic = int(np.argmax(u)), int(np.argmax(c))
        im = int(np.argmin(ratio))
        ax.annotate("notch @ load's\nfixed-base mode", xy=(f[im], c[im]),
                    xytext=(f[im]*0.30, c[im]*0.45), fontsize=9.5, color="0.3",
                    arrowprops=dict(arrowstyle="->", lw=0.9, color="0.4"))
        ax.annotate("peak @ coupled-\nsystem resonance", xy=(f[ic], c[ic]),
                    xytext=(f[ic]*1.25, c[ic]*1.35), fontsize=9.5, color=C["cpl"],
                    arrowprops=dict(arrowstyle="->", lw=0.9, color=C["cpl"]))
        ax.axhline(3.156, color=C["ref"], lw=0.8, ls=":")
        ax.text(21, 3.5, "rigid = tray 3.16 kg", fontsize=9, color=C["ref"])
        ax.set_xlim(40, 200)
        ax.set_xlabel("frequency [Hz]")
        ax.set_title(f"{note}\nover-test = uncoupled/coupled = "
                     f"×{u[iu]/c[ic]:.1f} peak  ·  ×{1/ratio[im]:.1f} at notch",
                     fontsize=11)
        ax.grid(True, which="both", color="0.92", lw=0.5)
    axs[0].set_ylabel("interface force per unit base accel  [kg]\n"
                      "(= load apparent mass)")
    axs[0].text(0.03, 0.95, "UNCOUPLED (spec)", color=C["unc"], fontsize=12,
                weight="bold", transform=axs[0].transAxes)
    axs[0].text(0.03, 0.88, "COUPLED (7004C)", color=C["cpl"], fontsize=12,
                weight="bold", transform=axs[0].transAxes)
    r = jl("qoi_results.json")["force_limiting_factor_joint"]
    fig.suptitle("Force limiting depends on the source/load apparent-mass "
                 f"match: per-axis over-test ×{min(r['median']):.2f}-"
                 f"{max(r['median']):.2f} median, up to ×{max(r['p97_5']):.1f} "
                 "across the mount prior", fontsize=12.5, weight="bold")
    fig.tight_layout(rect=(0, 0.03, 1, 0.92))
    stamp(fig)
    fig.savefig(os.path.join(FIG, "deck_force_limiting.png"),
                bbox_inches="tight")
    plt.close(fig)


# ---- D3: variance decomposition (mount dominance) ----------------------
def fig_mount_dom():
    vd = jl("variance_decomposition.json")
    bci = vd.get("bootstrap_ci95", {}).get("th_cpl", {})
    fig, ax = plt.subplots(figsize=(9.0, 5.4))
    groups = [("mount", "mount stiffness\n(unknown joint, PRIOR)", C["bad"]),
              ("T", "tray model\n(prior)", C["miles"]),
              ("seed_aleatory", "input randomness\n(aleatory)", "0.6"),
              ("S", "ShockSat primary\n(CALIBRATED posterior)", C["good"])]
    xs = np.arange(3)
    width = 0.2
    for gi, (g, lab, col) in enumerate(groups):
        v = np.array(vd["groups"]["th_cpl"][g])
        pos = xs+(gi-1.5)*width
        ax.bar(pos, v, width, color=col, label=lab)
        if g in bci:
            lo = np.array(bci[g]["ci95_lo"])
            hi = np.array(bci[g]["ci95_hi"])
            ax.errorbar(pos, v, yerr=[v-lo, hi-v], fmt="none", ecolor="0.25",
                        elinewidth=1.1, capsize=3)
    ax.set_xticks(xs)
    ax.set_xticklabels(["F$_x$", "F$_y$", "F$_z$"], fontsize=14)
    ax.set_ylabel("share of QOI variance  (OAT main-effect ratio)")
    ax.set_ylim(0, 1.75)
    ax.axhline(1.0, color="0.7", lw=0.9, ls="--")
    ax.text(2.35, 1.02, "100%", fontsize=9, color="0.5")
    ax.legend(fontsize=10.5, loc="upper center", ncol=2)
    ax.set_title("The unknown mount stiffness controls the load — not the\n"
                 "carefully-calibrated primary structure (<1%)", fontsize=13.5)
    ax.grid(True, axis="y", color="0.9", lw=0.5)
    fig.text(0.5, 0.052, "Bars = OAT ratio (Var when only that group varies / "
             "Var when all vary); NOT a Sobol index, so a dominant group can "
             "exceed 100%. Whiskers = bootstrap 95% CI (n=64/128 → ~22% error): "
             "the mount bars are statistically = 100%.", fontsize=8.2,
             color="0.4", ha="center")
    stamp(fig, col="0.55")
    fig.tight_layout(rect=(0, 0.085, 1, 1))
    fig.savefig(os.path.join(FIG, "deck_mount_dominance.png"),
                bbox_inches="tight")
    plt.close(fig)


# ---- D4: identifiability — SE says yes, FIM says only 2/6 --------------
def fig_identif():
    md = jl("multimodality_diagnosis.json")
    fim = md["fim_combinations"]
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 5.1))
    ax = axs[0]
    ev_a = np.array(fim["actual_discrepancy_3.7pct"]["eigenvalues"])[::-1]
    ev_n = np.array(fim["injected_noise_only_0.3pct"]["eigenvalues"])[::-1]
    pp = fim["actual_discrepancy_3.7pct"]["prior_precision"]
    x = np.arange(6)
    ax.semilogy(x, np.clip(ev_a, 1e-3, None), "o-", color=C["bad"], ms=8,
                lw=1.6, label="at realized discrepancy (3.7%)")
    ax.semilogy(x, np.clip(ev_n, 1e-3, None), "s--", color="0.55", ms=6,
                lw=1.2, label="at injected noise only (0.3%)")
    ax.axhline(pp, color=C["ref"], lw=1.2, ls=":")
    ax.text(0.1, pp*1.3, "prior precision (identifiable above this)",
            fontsize=9.5, color=C["ref"])
    ax.set_xlabel("mount stiffness combination (sorted)")
    ax.set_ylabel("Fisher information eigenvalue")
    ax.set_title("Only 2 of 6 mount combinations\nseparate at the real "
                 "discrepancy floor", fontsize=12.5)
    ax.legend(fontsize=9.5, loc="upper right")
    ax.grid(True, which="both", color="0.92", lw=0.5)

    ax = axs[1]
    base = [r for r in md["base"]["per_chain"]]
    names = ["k_tx", "k_ty", "k_tz", "k_rx", "k_ry", "k_rz"]
    cols = ["#b2453c", "#2c5f8a", "#c98a1e", "#3a7d44"]
    for r in base:
        ax.plot(range(6), r["theta_m_median"], "o-", color=cols[r["chain"]],
                lw=1.3, ms=6, label=f"chain {r['chain']}")
    ax.set_yscale("log")
    ax.set_xticks(range(6))
    ax.set_xticklabels(names, fontsize=9, rotation=30)
    ax.set_ylabel("posterior median multiplier")
    sp = md["base"]["cross_chain_pred_freq_spread_pct"]["median"]
    ax.set_title(f"4 NUTS chains: disagree in PARAMETERS\nyet agree in DATA "
                 f"({sp}% freq spread) = under-ID", fontsize=12.5)
    ax.legend(fontsize=9, ncol=2)
    ax.grid(True, which="both", color="0.92", lw=0.5)
    fig.suptitle("Identifiability gate: strain energy says 'mount matters', "
                 "FIM + sampler say 'frequencies alone cannot split the axes'",
                 fontsize=12.5, weight="bold", y=1.0)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    stamp(fig)
    fig.savefig(os.path.join(FIG, "deck_identifiability.png"),
                bbox_inches="tight")
    plt.close(fig)


# ---- D5: findings scorecard 1-5 ----------------------------------------
SCORE = [
    ("From-scratch ShockSat FEM reproduces NASA NX (2.5pp) & real test modes",
     5, "validated against NASA's own numbers + measured free-free modes"),
    ("NUTS twin converges on full modal set (R-hat 1.022, ESS 232)",
     4, "converges & predicts held-out freqs; identification only partial (4/9)"),
    ("StatFEM discrepancy is REAL on a real structure (sigma_f 4.6% >> noise)",
     4, "the discrepancy lever Girolami/KOH warn about, measured on hardware"),
    ("Bayesian-7004C force limiting quantified (over-test x1.1-2.2)",
     4, "novelty thread realized with a VALIDATED source model"),
    ("Load QOI is mount-dominated (mount ~100% of variance, primary <1%)",
     5, "decision-changing: calibrate the joint, not the primary"),
    ("Response-limit proxy works in-band (rho~1.0, alpha~mass)",
     4, "industry-practical force-limit stand-in (band-specific caveat)"),
    ("One modal survey recovers the full 6-DOF mount",
     2, "HONEST NEGATIVE: only 2/6 combos; model-form discrepancy is the wall"),
    ("Honesty harness catches our OWN overclaim (SE 'yes' -> FIM '2/6')",
     5, "anti-cheating gates + green/yellow/red did their job"),
]


def fig_scorecard():
    fig, ax = plt.subplots(figsize=(12.8, 7.2))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    cmap = {1: "#a11", 2: "#cc7a2b", 3: "#c2a800", 4: "#5a9e4a", 5: "#1f7a44"}
    n = len(SCORE)
    ax.text(0.0, 0.975, "Findings, scored 1 (utter failure) → 5 (smashing "
            "success)", fontsize=16, weight="bold")
    top, bot = 0.91, 0.10
    rowh = (top-bot)/n
    for i, (title, sc, note) in enumerate(SCORE):
        yc = top - (i+0.5)*rowh
        if i % 2 == 0:
            ax.add_patch(plt.Rectangle((0, yc-rowh/2), 1, rowh, fc="0.965",
                                       ec="none"))
        ax.text(0.012, yc+rowh*0.13, title, fontsize=11.5, va="center",
                weight="bold")
        ax.text(0.012, yc-rowh*0.27, note, fontsize=9.2, va="center",
                color="0.4", style="italic")
        # 5-box meter, large
        bx0, bw, bh = 0.66, 0.038, rowh*0.34
        for s in range(1, 6):
            on = s <= sc
            ax.add_patch(plt.Rectangle((bx0+(s-1)*(bw+0.006), yc-bh/2), bw, bh,
                         fc=cmap[sc] if on else "0.9", ec="0.55", lw=0.6))
        ax.text(0.96, yc, f"{sc}/5", fontsize=15, weight="bold", va="center",
                ha="right", color=cmap[sc])
    ax.text(0.0, 0.045, "Median 4 / 5.  The two 5s: the mount-dominance "
            "decision, and the honesty harness catching our OWN overclaim.  "
            "The one 2: an informative negative that localizes the needed "
            "measurement (shapes / FRF / force gauge — not more frequencies).",
            fontsize=10, color="0.3")
    stamp(fig)
    fig.savefig(os.path.join(FIG, "deck_scorecard.png"), bbox_inches="tight")
    plt.close(fig)


# ---- D6: method conservatism (clean) -----------------------------------
def fig_method():
    r = jl("qoi_results.json")["ratios"]
    rows = [("srs_Q10_over_th_unc", "modal-SRS  Q=10"),
            ("srs_Qinf_over_th_unc", "modal-SRS  Q=true"),
            ("srs_Q50_over_th_unc", "modal-SRS  Q=50"),
            ("miles_Qinf_over_th_unc", "Miles 3σ  Q=true"),
            ("miles_Q25_over_th_unc", "Miles 3σ  Q=25")]
    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    ax.axvspan(0.9, 1.1, color="#e8efe6", zorder=0)
    for i, (k, lab) in enumerate(rows):
        y = len(rows)-1-i
        v = r[k]["median"]
        ax.plot([min(v), max(v)], [y, y], color="0.6", lw=2.5,
                solid_capstyle="butt")
        ax.plot(v[2], y, "o", color=C["cpl"], ms=9)
        ax.text(max(v)+0.04, y, lab, va="center", fontsize=11.5)
    ax.axvline(1.0, color=C["ref"], lw=1.0, ls=":")
    ax.set_ylim(-0.8, len(rows)-0.4)
    ax.text(1.0, -0.62, "= time-history reference", fontsize=10,
            color=C["ref"], ha="center")
    ax.set_yticks([])
    ax.set_xlabel("hand-method estimate ÷ time-history truth   "
                  "(bar = per-axis range; dot = z)")
    ax.set_xlim(0.4, 2.45)
    ax.set_title("Method error is ASSUMPTION error: the SRS machinery is "
                 "unbiased\nat the true damping; the assumed Q swings it ×0.7-2.3",
                 fontsize=12.5)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    stamp(fig)
    fig.savefig(os.path.join(FIG, "deck_method.png"), bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_arc()
    fig_force_limiting()
    fig_mount_dom()
    fig_identif()
    fig_scorecard()
    fig_method()
    print("deck figs written to", FIG)
