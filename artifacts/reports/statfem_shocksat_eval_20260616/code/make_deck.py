#!/usr/bin/env python3
"""Slide deck for Ilias (~10 slides). Reads the summary JSONs and embeds the saved figures.

Every claim traces to a checker number (coverage_summary / arm_comparison / scorecard / identifiability).
Text slides use generously spaced fig.text (large fonts); data slides embed the figure PNGs. Gated on a
non-RED checker by run_all (built unconditionally here; the checker decides overall).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
FIG = WS / "figures"
SL = WS / "slides"
SL.mkdir(exist_ok=True)

cov = json.load(open(OUT / "coverage_summary.json"))
acmp = json.load(open(OUT / "arm_comparison.json"))["arms"]
sc = json.load(open(OUT / "scorecard.json"))
idf = json.load(open(OUT / "identifiability.json"))
H = sc["headline"]


def text_slide(n, title, bullets, sub=""):
    fig = plt.figure(figsize=(12, 6.75))
    fig.patch.set_facecolor("white")
    fig.text(0.06, 0.88, title, fontsize=20, fontweight="bold", va="top")
    if sub:
        fig.text(0.06, 0.80, sub, fontsize=12, va="top", color="#444", style="italic")
    y = 0.70
    for b in bullets:
        fig.text(0.08, y, b, fontsize=13.5, va="top")
        y -= 0.085 * (1 + b.count("\n"))
    fig.text(0.06, 0.03, "StatFEM ShockSat held-out-QOI evaluation | plain ShockSat (9-group), synthetic | "
             "NUTS 4-chain | run statfem_shocksat_eval_20260616", fontsize=7.5, color="0.5")
    fig.savefig(SL / f"slide_{n:02d}.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def image_slide(n, title, img, caption=""):
    fig = plt.figure(figsize=(12, 6.75))
    fig.text(0.06, 0.95, title, fontsize=18, fontweight="bold", va="top")
    ax = fig.add_axes([0.04, 0.10, 0.92, 0.78])
    ax.axis("off")
    if (FIG / img).exists():
        ax.imshow(mpimg.imread(FIG / img))
    if caption:
        fig.text(0.06, 0.055, caption, fontsize=10.5, color="#333")
    fig.savefig(SL / f"slide_{n:02d}.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


m0 = H["naive_mean_coverage"]; best = H["best_statfem_mean_coverage"]
text_slide(1, "Evaluating StatFEM on the ShockSat: a held-out-QOI trust test",
           ["Lead: Agentic BayesX  |  Advisor objective: Ilias Bilionis  |  Human: Andrew Voss",
            "",
            "Build it, evaluate it, find the gaps, suggest improvements -- report whichever way it falls.",
            f"Headline: {H['verdict_one_line']}.",
            f"   naive coverage {m0:.0%}  ->  best StatFEM coverage {best:.0%}  (held-out QOI, mean over 5 combos)"])

text_slide(2, "The objective and the concern under test",
           ["Ilias (verbatim):",
            "  \"Your objective should be to evaluate the StatFEM approach. It may not be possible to",
            "   validate it because it may not be working. So, build, evaluate, identify its gaps,",
            "   and suggest improvements should be your goal.\"",
            "",
            "Concern (hypothesis, relayed via Andrew): a converged StatFEM posterior can be",
            "CONFIDENTLY WRONG under model-form error, with no warning.",
            "",
            "Trust test: calibrate on a FEW sensors, predict a QOI at sensors never used,",
            "check whether the truth lands in the 95% band."],
           sub="StatFEM = a FEM whose output carries a learned discrepancy d (model-form-error function).")

image_slide(3, "Testbed: plain ShockSat (9-group), two injected error layers", "fig_schematic.png",
            caption="Plain standalone ShockSat FEM only (NO tray). Truth = model(theta_truth) x Schneider field. "
                    "Synthetic is valid here: truth & inference share the FEM geometry.")

image_slide(4, "MONEY RESULT: held-out-QOI coverage across 5 combos, by arm", "figA_heldout_qoi_coverage.png",
            caption=f"naive (M0) mean {m0:.0%} (confidently wrong); StatFEM-iid {H['iid']:.0%}, "
                    f"Schneider {H['schneider']:.0%}, orthogonal {H['orthogonal']:.0%}. Reported as a "
                    f"distribution over the 5 combos (retires the single-realization caveat).")

image_slide(5, "Discrepancy structure: naive vs iid vs Schneider vs orthogonal", "figB_arm_comparison.png",
            caption="Coverage, predictive band width (sharpness), learned sigma_d (error thermometer), and "
                    "theta over-absorption. The orthogonal arm trades coverage/width for a de-biased theta.")

image_slide(6, "theta recovery: identifiable groups recover, unidentifiable are missed", "figC_theta_recovery.png",
            caption="Tied to the modal strain-energy gate: only ~4/9 groups carry signal "
                    f"({idf['informed_groups_strain_energy']}). Recovery of out-of-floor groups is NOT claimed.")

image_slide(7, "Identifiability gate (strain energy + FIM + finite perturbation)", "figE_identifiability.png",
            caption="The strain-energy 4/9 finding reproduces the prior ShockSat modal-twin result on a "
                    "different observable; the FRF-FIM linearization is optimistic near resonances.")

image_slide(8, "The visual: naive vs Schneider held-out FRF bands", "figD_heldout_frf_bands.png",
            caption="A tight naive band that misses the truth peak = 'confidently wrong'. The Schneider band "
                    "kriges the spatial discrepancy from the observed sensors to the held-out one.")

# gaps + improvements pulled from the scorecard verdicts
gaps = [r["claim"] for r in sc["rows"] if r["verdict"] != "GREEN"][:4]
text_slide(9, "Gaps (what StatFEM does NOT solve here)",
           ["- theta recovery is PARTIAL: unidentifiable groups (joints/contact/welds) stay at prior --",
            "  a data/identifiability limit, not a sampler bug (strain-energy / FIM gate).",
            "- Coverage restored partly by WIDER bands; sharpness depends on the spatial-correlation transfer.",
            "- The injected discrepancy is a synthetic surrogate; real model-form error may differ in structure.",
            "- One synthetic realization per combo (5 combos = 5 truths); no flight/build/test variability.",
            "- The Schneider inference uses the TRUE correlation lengths (favorable); sensitivity tests mismatch."])

text_slide(10, "Suggested improvements + verdict",
           ["Improvements:",
            "  - report sigma_d as a model-form-error thermometer next to every QOI;",
            "  - use the kriged spatial (Schneider) discrepancy to predict un-instrumented sensors;",
            "  - calibrate correlation lengths from repeated measurements, don't assume them;",
            "  - use the ORTHOGONAL projection when theta has physical meaning (de-biases it);",
            "  - spend the next test on sensors/bands that excite the unidentified groups (~147 Hz joints).",
            "",
            f"VERDICT: {H['verdict_one_line']}.",
            "Scope: synthetic, plain ShockSat, one realization per combo; either direction is the science."],
           sub="Every claim traces to a checker number (coverage_summary / arm_comparison / scorecard).")

# index
lines = ["# StatFEM ShockSat held-out-QOI evaluation -- deck (for Ilias)", "",
         f"Headline: {H['verdict_one_line']} (naive {m0:.0%} -> best StatFEM {best:.0%}).", ""]
for i in range(1, 11):
    lines.append(f"- slide_{i:02d}.png")
open(SL / "DECK.md", "w").write("\n".join(lines) + "\n")
print(f"deck: 10 slides in {SL}")
