#!/usr/bin/env python3
"""make_figs — T3 corrected figures (card §2 T3).

The study's shipped figures carry the defective collector output (NaN statistics, an invalid F=R row).
These replace them with figures built from the REPAIR's finite numbers + this card's T1/T2 results.

Two figures:
  (i)  fig_arms_bands_corrected.png — arms x bands, real fold SEs, NO F=R row, arm C carrying its per-fold
       refit provenance, and the study's worst R-hat / ESS printed beside every MAP-derived bar.
  (ii) fig_screening_vs_exact.png   — screening vs exact sub-200 for all 28 loop candidates, tracks
       distinguished, both S2 selection conventions annotated.

Tufte skill (.claude/skills/tufte-data-graphics/SKILL.md) read and applied before writing this:
  * data-ink: no top/right spines, no frame fills, muted y-grid only (bars need a value-reading aid),
    no 3-D, no chartjunk;
  * lie factor ~1: every bar starts at zero on a shared linear P1' axis (P1' is a correlation on [-1,1];
    zero is its natural, meaningful origin -> no truncated baseline);
  * direct labelling over legends wherever it fits (track labels sit on the data in fig ii);
  * caption does the work: quantity contract, data counts, provenance, and the takeaway sit ON the figure;
  * documented deviations (stated on the figures themselves, see DEVIATIONS below).

DEVIATIONS from the checklist, and why:
  1. NO log frequency axis: neither figure has a frequency axis. These are per-BAND aggregate scores
     (sub-200 Hz / 200-500 Hz) and per-candidate scores, not spectra. The project's log-frequency rule
     applies to FRF/PSD curves; it is inapplicable here and stated on the figure.
  2. Arm F is NOT drawn as its own bar. Under the pre-registered rule F = C (B doesn't beat A1; C beats A1;
     D doesn't beat C), so an F bar would be a duplicate of the C bar — redundant data-ink for zero
     information. F's identity is annotated instead. (The invalid F=R row from the study's collector is
     gone entirely; that is the point of this figure.)
  3. Fig (i) uses a legend-free small-multiple pair of panels rather than direct end-labels, because bar
     charts have no line ends to label; arm names sit under their bars.
"""
from __future__ import annotations
import json, os, sys, textwrap

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                     # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                 # noqa: E402

TUFTE_RC = {"figure.dpi": 150, "savefig.dpi": 200, "font.size": 10,
            "axes.spines.top": False, "axes.spines.right": False,
            "axes.edgecolor": "#444444", "axes.linewidth": 0.8,
            "axes.grid": True, "grid.color": "#dddddd", "grid.linewidth": 0.6,
            "axes.axisbelow": True, "xtick.direction": "out", "ytick.direction": "out",
            "legend.frameon": False, "axes.titlelocation": "left", "font.family": "DejaVu Sans"}
plt.rcParams.update(TUFTE_RC)

STAMP = ("run: shocksat_fullspec_exact_completion_20260716 (this card) | numbers: repair "
         "shocksat_full_spectrum_frf_repair_20260716 + T1/T2 here | measured NASA ShockSat hammer data, "
         "4 dev drives | CPU float64")
WORST_RHAT, WORST_ESS = 360.6, 2.0                  # study out/nuts_diagnostics.json (arm B, m_zpos_990z)
manifest = []

# distinguishable, grayscale-legible, non-rainbow hues (color encodes data, never decoration)
COL_AGENT, COL_RANDOM = "#2d5f8a", "#b3541e"
COL_BAR, COL_MAPBAR = "#5b7f9e", "#8a6d3b"


def wrap(cap, width):
    """Hard-wrap each caption paragraph so no text is clipped at the canvas edge (legibility QA)."""
    return "\n".join(textwrap.fill(par, width=width) for par in cap.split("\n"))


def _fig_arms_bands(armC, verdicts):
    """(i) Corrected arms x bands. Repair numbers + T1's honest arm C. No F=R row."""
    tab = verdicts["arms_bands_table"]
    arms = ["A0", "A1", "B", "C", "D", "R"]
    bands = [("sub200", "sub-200 Hz  [45, 200)"), ("b200_500", "200-500 Hz  [200, 500)")]
    map_derived = {"B", "C"}                        # scored at a deterministic MAP of a NON-converged posterior

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 7.0), sharey=True)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.88, bottom=0.44, wspace=0.06)
    for ax, (b, btitle) in zip(axes, bands):
        means = [tab[a][b]["mean"] for a in arms]
        ses = [tab[a][b]["fold_se"] for a in arms]
        cols = [COL_MAPBAR if a in map_derived else COL_BAR for a in arms]
        x = np.arange(len(arms))
        ax.bar(x, means, width=0.62, color=cols, edgecolor="none")
        # fold spread as a thin range whisker (shows the data's actual spread, not a decorative cap)
        ax.errorbar(x, means, yerr=ses, fmt="none", ecolor="#333333", elinewidth=0.9, capsize=0)
        ax.axhline(0, color="#444444", linewidth=0.8)
        ax.set_xticks(x); ax.set_xticklabels(arms, fontsize=10)
        ax.set_title(btitle, fontsize=10.5)
        ax.grid(True, axis="y"); ax.grid(False, axis="x")
        for xi, (m, a) in enumerate(zip(means, arms)):
            top = m + ses[xi]
            ax.annotate(f"{m:+.3f}", (xi, top), xytext=(0, 5), textcoords="offset points",
                        ha="center", fontsize=8.5, color="#222222")
            # the non-convergence diagnostic rides ON every MAP-derived bar (Convergence + Plot gates).
            # Adaptive placement: inside the bar (white) when it is tall enough to hold the text, else
            # just above the value label (brown) — a short bar would otherwise render white-on-white.
            if a in map_derived:
                txt = f"MAP\nR-hat {WORST_RHAT:.1f}\nESS {WORST_ESS:.1f}"
                if m > 0.10:
                    ax.annotate(txt, (xi, 0.006), ha="center", va="bottom", fontsize=6.6,
                                color="white", linespacing=1.25)
                else:
                    ax.annotate(txt, (xi, top), xytext=(0, 17), textcoords="offset points",
                                ha="center", va="bottom", fontsize=6.6, color=COL_MAPBAR,
                                linespacing=1.25)
        if b == "sub200":
            ax.set_ylabel("held-out P1' (per-channel fractional\ncorrelation of log10|H|)   higher = better",
                          fontsize=9.5)
    axes[0].set_ylim(0.0, 0.40)

    fig.suptitle("Corrected arms x bands — exact-basis held-out FRF score\n(the shipped study figure carried "
                 "NaN statistics and an invalid F=R row)", fontsize=11, x=0.012, y=0.985, ha="left")
    cap = (
        "QUANTITY: P1' = median-over-channels fractional correlation between predicted and measured "
        "log10|H1| (accelerance, g/lbf), after a TRAIN-side frequency warp and ONE global gain per fold; "
        "dimensionless, gain-invariant. Mean over 4 leave-one-drive-out folds; whisker = +/-1 fold SE "
        "(std across the 4 folds / sqrt 4).\n"
        "READ THE WHISKERS CAREFULLY: the fold SE (~0.16) is dominated by fold-to-fold DIFFICULTY, which "
        "CANCELS in the paired arm-vs-arm test the decisions actually use — e.g. D-A1 = +0.0497 +/- 0.0174 "
        "PAIRED. Overlapping whiskers here do NOT mean the arms are indistinguishable.\n"
        f"ARM C (brown, this card's T1): 4 per-fold shape-MAP refits on the exact basis, each fit on that "
        f"fold's 3 TRAIN drives only -> {armC['fold_mean']['sub200']:+.4f} sub-200. It REPLACES the study's "
        f"withdrawn 0.1570, which was right BY ACCIDENT: its leak (+0.082, review C6) was nearly cancelled "
        f"by a basis mismatch the review missed (-0.085; shape coefficients fit in the theta=1 eigenbasis, "
        f"applied to the theta_MAP eigenbasis). See out/leak_probe.json.\n"
        "BROWN BARS (B, C) are deterministic optimizer points from NON-CONVERGED posteriors (worst "
        f"R-hat {WORST_RHAT}, min ESS {WORST_ESS}) — NOT posterior means, NOT trustworthy as intervals.\n"
        "ARM F is not drawn: under the pre-registered rule F = C (B does not beat A1; C beats A1; D does "
        "not beat C), so an F bar would duplicate C. The study collector's F=R (random control) row was "
        "INVALID and is deleted.\n"
        "No frequency axis on this figure (per-band aggregates, not spectra), so the log-frequency rule "
        "does not apply. Linear P1' scale, zero baseline.\n" + STAMP)
    fig.text(0.012, 0.375, wrap(cap, 168), fontsize=7.4, color="#333333", va="top",
             linespacing=1.55)
    p = "figures/fig_arms_bands_corrected.png"
    fig.savefig(os.path.join(C.WS, p)); plt.close(fig)
    manifest.append({"file": p, "script": "code/make_figs.py",
                     "data_label": "out/verdicts_final.json (repair numbers + T1 arm C); "
                                   "out/armC_exact.json"})


def _fig_screening_vs_exact(rr):
    """(ii) Screening vs exact for all 28 candidates; both S2 selection conventions annotated."""
    rows = rr["rows"]
    ag = [r for r in rows if r["track"] == "agent"]
    rd = [r for r in rows if r["track"] == "random"]
    s2s, s2e = rr["S2"]["screening_selected"], rr["S2"]["exact_selected"]

    fig, ax = plt.subplots(figsize=(9.6, 9.6))
    fig.subplots_adjust(left=0.10, right=0.975, top=0.94, bottom=0.30)
    lo, hi = 0.060, 0.192
    # y=x reference: where the theta=1 screening basis would have been an unbiased proxy for the exact basis
    ax.plot([lo, hi], [lo, hi], color="#999999", linewidth=0.9, linestyle=(0, (4, 3)), zorder=1)
    ax.annotate("y = x  (screening = exact:\nno reduced-basis inflation)", (0.1235, 0.1235),
                xytext=(6, -30), textcoords="offset points", ha="left", fontsize=7.8,
                color="#777777", linespacing=1.3)

    for grp, col in ((ag, COL_AGENT), (rd, COL_RANDOM)):
        ax.scatter([r["screening_sub200"] for r in grp], [r["exact_sub200"] for r in grp],
                   s=38, facecolor=col, edgecolor="white", linewidth=0.6, zorder=3)
    # colour key placed in empty canvas (no box, no frame) rather than a legend over the data
    ax.scatter([0.0680], [0.1055], s=38, facecolor=COL_AGENT, edgecolor="white", linewidth=0.6)
    ax.annotate("agent (14 candidates)", (0.0680, 0.1055), xytext=(9, 0), textcoords="offset points",
                va="center", fontsize=9, color=COL_AGENT, fontweight="bold")
    ax.scatter([0.0680], [0.0985], s=38, facecolor=COL_RANDOM, edgecolor="white", linewidth=0.6)
    ax.annotate("random (14 candidates)", (0.0680, 0.0985), xytext=(9, 0), textcoords="offset points",
                va="center", fontsize=9, color=COL_RANDOM, fontweight="bold")

    # the candidates the two S2 conventions actually select (leader lines; offsets chosen to not collide)
    picks = {}
    for cid, tag in ((s2s["agent_cid"], "S2(a) agent"), (s2s["random_cid"], "S2(a) random"),
                     (s2e["agent_cid"], "S2(b) agent"), (s2e["random_cid"], "S2(b) random")):
        picks.setdefault(cid, []).append(tag)
    # offsets hand-tuned into EMPTY canvas so no label covers a data point or another label
    offs = {s2e["agent_cid"]: (-104, 30), s2s["agent_cid"]: (24, -34), s2s["random_cid"]: (-178, 14)}
    for cid, tags in picks.items():
        r = next(x for x in rows if x["cid"] == cid)
        sx, ey = r["screening_sub200"], r["exact_sub200"]
        ax.scatter([sx], [ey], s=170, facecolor="none", edgecolor="#222222", linewidth=1.2, zorder=4)
        ax.annotate(" + ".join(tags) + f"\n{cid}\nexact {ey:+.4f}", (sx, ey),
                    xytext=offs.get(cid, (30, 20)), textcoords="offset points", ha="center",
                    fontsize=7.6, color="#222222", linespacing=1.3, zorder=5,
                    arrowprops=dict(arrowstyle="-", color="#666666", lw=0.7,
                                    shrinkA=0, shrinkB=7))

    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
    ax.set_xlabel("SCREENING sub-200 P1'   (theta = 1 reduced basis — the study's triage metric)")
    ax.set_ylabel("EXACT sub-200 P1'   (basis re-solved at each candidate's theta_MAP — trustworthy)")
    ax.set_title("All 28 remodel-loop candidates, re-scored on the exact basis\n"
                 "(the study exact-scored only the 2 screening winners)", fontsize=10.5)
    ax.grid(True, color="#dddddd", linewidth=0.6)

    ra = rr["rank_agreement"]
    box = (
        f"S2 = agent - random, sub-200, paired over the same 4 folds (SE = std of per-fold deltas / sqrt 4):\n"
        f"  (a) SCREENING-selected winners, exact-scored  [the study's convention]\n"
        f"        {s2s['agent_cid']} - {s2s['random_cid']} = {s2s['delta_mean']:+.4f} +/- "
        f"{s2s['delta_se']:.4f}   rule (>= 1x SE) met: {s2s['S2_rule_met']}\n"
        f"  (b) EXACT-selected winners (best exact per track)  [winner's-curse-honest]\n"
        f"        {s2e['agent_cid']} - {s2e['random_cid']} = {s2e['delta_mean']:+.4f} +/- "
        f"{s2e['delta_se']:.4f}   rule (>= 1x SE) met: {s2e['S2_rule_met']}\n"
        f"Screening->exact rank agreement (Spearman): agent "
        f"{ra['agent']['spearman_screening_vs_exact']:+.3f}  (top-1 changes), random "
        f"{ra['random']['spearman_screening_vs_exact']:+.3f}  (top-1 holds)\n"
        f"NEITHER convention meets the S2 rule -> agent does not beat equal-budget random either way.")
    ax.annotate(box, (0.985, 0.015), xycoords="axes fraction", va="bottom", ha="right", fontsize=7.6,
                color="#222222", linespacing=1.55)

    cap = (
        "QUANTITY: P1' = median-over-channels fractional correlation of log10|H1| (accelerance, g/lbf) vs "
        "measurement, TRAIN-side warp + ONE global gain per fold, mean over 4 leave-one-drive-out folds; "
        "dimensionless. Each point = one remodel candidate (14 agent-proposed + 14 equal-budget random), "
        "measured NASA ShockSat hammer data.\n"
        "Points BELOW y=x were flattered by the theta=1 screening basis (the reduced-basis trap, study "
        "D15/D22): the basis was built at theta=1 but evaluated at theta_MAP (joints 0.47, cross_beam 1.46), "
        "which mispredicts the modes it is most sensitive to. Exact = basis re-solved AT theta_MAP.\n"
        "Deterministic scores (no sampler): each candidate's theta_MAP is reused verbatim from the study, "
        "never re-optimized here. No frequency axis (per-band aggregate), so the log-frequency rule does "
        "not apply; linear P1' on both axes.\n"
        "SCOPE (study D16): all 14 agent candidates were thickness/scale/split edits — the agent proposed "
        "ZERO genuine model-form (mesh/connectivity) changes, so this compares tracks within a "
        "mostly-parametric edit space.\n" + STAMP)
    fig.text(0.012, 0.245, wrap(cap, 143), fontsize=7.4, color="#333333", va="top",
             linespacing=1.55)
    p = "figures/fig_screening_vs_exact.png"
    fig.savefig(os.path.join(C.WS, p)); plt.close(fig)
    manifest.append({"file": p, "script": "code/make_figs.py", "data_label": "out/exact_rerank.json"})


def main():
    with open(os.path.join(C.MY_OUT, "armC_exact.json")) as f:
        armC = json.load(f)
    with open(os.path.join(C.MY_OUT, "exact_rerank.json")) as f:
        rr = json.load(f)
    with open(os.path.join(C.MY_OUT, "verdicts_final.json")) as f:
        verdicts = json.load(f)
    _fig_arms_bands(armC, verdicts)
    _fig_screening_vs_exact(rr)
    with open(os.path.join(C.MY_OUT, "fig_manifest.json"), "w") as f:
        json.dump({"figures": manifest,
                   "tufte_note": "skill read and applied; deviations documented in this script's docstring "
                                 "and ON each figure"}, f, indent=1)

    # heuristic auto-QA; the lead's actual visual read is merged from fig_qa_visual.json (never assumed)
    qa = {}
    vp = os.path.join(C.MY_OUT, "fig_qa_visual.json")
    vis = json.load(open(vp)) if os.path.exists(vp) else {}
    for f in manifest:
        fp = os.path.join(C.WS, f["file"])
        name = os.path.basename(f["file"])
        auto = os.path.exists(fp) and os.path.getsize(fp) > 30000
        v = vis.get(name, {})
        qa[name] = {"exists": os.path.exists(fp), "size_B": os.path.getsize(fp) if os.path.exists(fp) else 0,
                    "auto_pass": bool(auto),
                    "visual_review": v.get("visual_review", "PENDING visual check"),
                    "pass": bool(auto and v.get("pass", False))}
    with open(os.path.join(C.MY_OUT, "fig_qa.json"), "w") as f:
        json.dump({"figures": qa}, f, indent=1)
    print(f"{len(manifest)} figures written; QA:", {k: v["pass"] for k, v in qa.items()})


if __name__ == "__main__":
    main()
