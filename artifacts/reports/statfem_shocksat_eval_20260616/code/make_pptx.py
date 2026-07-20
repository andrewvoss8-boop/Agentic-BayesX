#!/usr/bin/env python3
"""Assemble an actual editable PowerPoint (.pptx) for Ilias from the figures + summary numbers.

Run with the BASE python (has python-pptx): python3 code/make_pptx.py
Every data slide embeds a saved figure; every claim traces to a checker number (coverage_summary / scorecard /
arm_comparison / identifiability). Writes slides/StatFEM_ShockSat_eval.pptx.
"""
from __future__ import annotations

import json
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
FIG = WS / "figures"
SL = WS / "slides"
SL.mkdir(exist_ok=True)

cov = json.load(open(OUT / "coverage_summary.json"))["by_arm"]
sc = json.load(open(OUT / "scorecard.json"))
H = sc["headline"]
idf = json.load(open(OUT / "identifiability.json"))
try:
    chk = json.load(open(WS / "checker_report.json"))
    chk_line = f"checker: {chk['overall']}  ({chk['counts']['GREEN']} green / {chk['counts']['YELLOW']} yellow / {chk['counts']['RED']} red)"
except Exception:
    chk_line = "checker: see checker_report.json"

INK = RGBColor(0x11, 0x11, 0x11)
GREY = RGBColor(0x55, 0x55, 0x55)
ACC = RGBColor(0x05, 0x96, 0x69)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = prs.slide_width, prs.slide_height


def _title(slide, text, size=28):
    tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.25), SW - Inches(1.0), Inches(0.9))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = INK
    return slide


def _foot(slide):
    tb = slide.shapes.add_textbox(Inches(0.4), SH - Inches(0.42), SW - Inches(0.8), Inches(0.35))
    r = tb.text_frame.paragraphs[0].add_run()
    r.text = ("StatFEM ShockSat held-out-QOI evaluation | plain ShockSat (9-group), SYNTHETIC, one realization/combo "
              "| NUTS 4-chain | run statfem_shocksat_eval_20260616")
    r.font.size = Pt(8); r.font.color.rgb = GREY


def bullets_slide(title, bullets, sub=None, size=18):
    s = prs.slides.add_slide(BLANK); _title(s, title)
    top = Inches(1.35)
    if sub:
        tb = s.shapes.add_textbox(Inches(0.6), Inches(1.15), SW - Inches(1.2), Inches(0.5))
        r = tb.text_frame.paragraphs[0].add_run(); r.text = sub
        r.font.size = Pt(13); r.font.italic = True; r.font.color.rgb = GREY
        top = Inches(1.75)
    body = s.shapes.add_textbox(Inches(0.7), top, SW - Inches(1.4), SH - top - Inches(0.6))
    tf = body.text_frame; tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = b; r.font.size = Pt(size); r.font.color.rgb = INK
        p.space_after = Pt(8)
    _foot(s); return s


def figure_slide(title, img, caption=None):
    s = prs.slides.add_slide(BLANK); _title(s, title, size=24)
    p = FIG / img
    if p.exists():
        # fit within the content area preserving aspect
        from PIL import Image
        iw, ih = Image.open(p).size
        maxw, maxh = SW - Inches(1.0), SH - Inches(2.0)
        scale = min(maxw / iw, maxh / ih)
        w = int(iw * scale); h = int(ih * scale)
        left = int((SW - w) / 2); top = Inches(1.25)
        s.shapes.add_picture(str(p), left, top, width=w, height=h)
    if caption:
        tb = s.shapes.add_textbox(Inches(0.5), SH - Inches(0.95), SW - Inches(1.0), Inches(0.5))
        tf = tb.text_frame; tf.word_wrap = True
        r = tf.paragraphs[0].add_run(); r.text = caption
        r.font.size = Pt(11); r.font.color.rgb = GREY
    _foot(s); return s


m0 = H["naive_mean_coverage"]; best = H["best_statfem_mean_coverage"]

# 1 title
s = prs.slides.add_slide(BLANK)
tb = s.shapes.add_textbox(Inches(0.8), Inches(2.3), SW - Inches(1.6), Inches(2.5))
tf = tb.text_frame; tf.word_wrap = True
r = tf.paragraphs[0].add_run(); r.text = "Evaluating StatFEM on the ShockSat"
r.font.size = Pt(40); r.font.bold = True; r.font.color.rgb = INK
p = tf.add_paragraph(); r = p.add_run(); r.text = "A held-out-sensor QOI trust test"
r.font.size = Pt(22); r.font.color.rgb = ACC
p = tf.add_paragraph(); r = p.add_run()
r.text = f"Headline: {H['verdict_one_line']}  (naive {m0:.0%} -> best StatFEM {best:.0%})"
r.font.size = Pt(15); r.font.color.rgb = GREY
p = tf.add_paragraph(); r = p.add_run()
r.text = "Lead: Agentic BayesX  |  Advisor objective: Ilias Bilionis  |  Human: Andrew Voss  |  " + chk_line
r.font.size = Pt(12); r.font.color.rgb = GREY
_foot(s)

# 2 objective
bullets_slide("The objective and the concern under test", [
    "Ilias (verbatim): \"Your objective should be to evaluate the StatFEM approach. It may not be possible to",
    "    validate it because it may not be working. So, build, evaluate, identify its gaps, and suggest",
    "    improvements should be your goal.\"",
    "",
    "Concern (hypothesis, relayed via Andrew): a converged StatFEM posterior can be CONFIDENTLY WRONG",
    "under model-form error, with no warning.",
    "",
    "Trust test: calibrate on a FEW sensors, predict a QOI at sensors never used, check whether the truth",
    "lands in the predicted 95% band. Either verdict is the science.",
], sub="StatFEM = a FEM whose output carries a learned discrepancy d (model-form-error function).")

# 3 testbed
figure_slide("Testbed: plain ShockSat (9-group), two injected error layers", "fig_schematic.png",
             "Plain standalone ShockSat ONLY (no tray). Truth = model(theta_truth) x Schneider discrepancy field. "
             "Synthetic is valid here because truth and inference share the FEM geometry.")

# 3b spatial prior-error map (per combo)
figure_slide("Where the error is vs where we measure: prior-error map per combo", "figF_spatial_error.png",
             "Front X-Z view of the FEM. Grey = un-biased groups; colour = injected prior error |theta_truth-1|. "
             "Green = 6 observed sensors, open orange = 14 held-out, star = drive. Same sensors every combo.")

# 3c spatial identifiability map
figure_slide("Where the data can see: identifiability map (modal strain energy)", "figG_spatial_ident.png",
             "Same geometry + sensors, groups coloured by modal strain-energy %. Only ~4/9 groups (boxes, "
             "plates, cross-beam) carry signal; joints/welds/contact are near-invisible to the modal data.")

# 4 what 'covered' means
bullets_slide("What 'covered' means (the trust metric)", [
    "Per held-out sensor, two QOIs: (a) peak |H| in the band, (b) band-GRMS energy sqrt(integral |H|^2 df).",
    "Each has a TRUE value (from the synthetic truth FRF) and a 95% posterior-PREDICTIVE band.",
    "COVERED = the true value falls inside the 95% band. Coverage = covered / total (14 sensors x 2 QOIs).",
    "A trustworthy 95% band covers ~95%.  'Confidently wrong' = a TIGHT band that MISSES.",
    "-> both coverage AND band width matter (see the arm-comparison slide).",
])

# 5 money
figure_slide("MONEY RESULT: held-out-QOI coverage across 5 combos, by arm", "figA_heldout_qoi_coverage.png",
             f"naive {m0:.0%} (confidently wrong) | iid {H['iid']:.0%} | Schneider {H['schneider']:.0%} | "
             f"orthogonal {H['orthogonal']:.0%}. Reported as a distribution over 5 scenarios. "
             f"x = NOT-converged cell (intervals not-trustworthy).")

# 6 arms
figure_slide("Discrepancy structure: naive vs iid vs Schneider vs orthogonal", "figB_arm_comparison.png",
             "Coverage, predictive band width (sharpness), learned sigma_d (error thermometer), theta over-absorption.")

# 7 FRF visual
figure_slide("The visual: naive vs Schneider held-out FRF bands", "figD_heldout_frf_bands.png",
             "A tight naive band that misses the truth peak = 'confidently wrong'. Schneider kriges the spatial "
             "discrepancy from observed sensors to the held-out one. (An animated version: gif_story.gif.)")

# 8 theta recovery
figure_slide("theta recovery: identifiable groups recover, unidentifiable missed", "figC_theta_recovery.png",
             f"Tied to the strain-energy gate: only ~4/9 groups carry signal "
             f"({idf['informed_groups_strain_energy']}). Recovery of out-of-floor groups is NOT claimed.")

# 9 identifiability
figure_slide("Identifiability gate (strain energy + FIM + finite perturbation)", "figE_identifiability.png",
             "Reproduces the prior ShockSat modal-twin 4/9 finding on a different observable; the FRF-FIM "
             "linearization is optimistic near resonances.")

# 10 gaps
bullets_slide("Gaps (what StatFEM does NOT solve here)", [
    "- theta recovery is PARTIAL: unidentifiable groups (joints/contact/welds) stay at prior -- a data/",
    "  identifiability limit, not a sampler bug.",
    "- Coverage can be restored partly by WIDER bands; sharpness depends on the spatial-correlation transfer.",
    "- naive and orthogonal arms FAILED to converge on the 'large'-bias scenario (multimodal, flagged).",
    "- Injected discrepancy is a synthetic surrogate; one realization per combo (5 combos = 5 truths).",
    "- Schneider inference uses the TRUE correlation lengths (favorable); sensitivity tests mismatch.",
    "- Testbed fidelity: the reused 74-mode basis (fmax 321 Hz, 1.2x band) has ~5-8% FRF-amplitude truncation",
    "  error vs the full FEM -- a testbed limit; the study is internally exact so conclusions are unaffected.",
])

# 11 improvements + verdict
bullets_slide("Suggested improvements + verdict", [
    "Improvements:",
    "  - report sigma_d as a model-form-error thermometer next to every QOI;",
    "  - use the kriged spatial (Schneider) discrepancy to predict un-instrumented sensors;",
    "  - calibrate correlation lengths from repeated measurements, don't assume them;",
    "  - use the ORTHOGONAL projection when theta has physical meaning (de-biases it);",
    "  - spend the next test on sensors/bands that excite the unidentified groups (~147 Hz joints).",
    "",
    f"VERDICT: {H['verdict_one_line']}.",
    "Scope: synthetic, plain ShockSat, one realization per combo; either direction is the science.",
], sub="Every claim traces to a checker number (coverage_summary / arm_comparison / scorecard / identifiability).")

out = SL / "StatFEM_ShockSat_eval.pptx"
prs.save(out)
print(f"saved {out} ({len(prs.slides._sldIdLst)} slides)")
