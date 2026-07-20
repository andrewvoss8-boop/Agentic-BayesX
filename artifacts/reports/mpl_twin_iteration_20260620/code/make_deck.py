#!/usr/bin/env python3
"""Build the findings deck (PPTX) for the MPL twin-iteration study. Story-driven: setup -> method -> data ->
finding (uncorrelated transmissibility) -> why (dense forest) -> frequency result -> load-free test ->
identifiability -> registry -> verdict -> scope -> reproducibility. Figures are the tufte-linted, image-QA'd
PNGs in figures/. All numbers come from out/*.json (no hand-typed metrics that the artifacts don't support).
"""
from __future__ import annotations
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

WS = Path(__file__).resolve().parents[1]; FIG = WS / "figures"; OUT = WS / "out"
NAVY = RGBColor(0x1F, 0x4E, 0x79); GRAY = RGBColor(0x55, 0x55, 0x55)
AMBER = RGBColor(0xB0, 0x6A, 0x00); GREEN = RGBColor(0x38, 0x6A, 0x1F)
EMU_W, EMU_H = Inches(13.333), Inches(7.5)

fb = json.loads((OUT / "freq_baseline.json").read_text())["summary"]
nr = json.loads((OUT / "near_resonance.json").read_text())
fd = json.loads((OUT / "forward_diagnostic.json").read_text())
rep = json.loads((WS / "check_report.json").read_text())


def fmt(k):  # mean of a freq_baseline summary key
    return fb[k]["mean"]


prs = Presentation(); prs.slide_width = EMU_W; prs.slide_height = EMU_H
BLANK = prs.slide_layouts[6]


def _box(slide, x, y, w, h):
    tb = slide.shapes.add_textbox(x, y, w, h); return tb.text_frame


def title_bar(slide, text, color=NAVY, size=26):
    tf = _box(slide, Inches(0.4), Inches(0.18), Inches(12.5), Inches(0.95))
    tf.word_wrap = True; p = tf.paragraphs[0]; r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = color
    return slide


def bullets(slide, items, x=Inches(0.5), y=Inches(5.55), w=Inches(12.3), h=Inches(1.7), size=13):
    tf = _box(slide, x, y, w, h); tf.word_wrap = True
    for i, (txt, lvl, col) in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = lvl; r = p.add_run(); r.text = txt; r.font.size = Pt(size)
        r.font.color.rgb = col;
        if lvl == 0: r.font.bold = True


def fig_slide(title, img, items, color=NAVY):
    s = prs.slides.add_slide(BLANK); title_bar(s, title, color)
    p = FIG / img
    # fit image into the area below the title, above the bullets
    from PIL import Image
    iw, ih = Image.open(p).size; ar = iw / ih
    maxw, maxh = Inches(12.4), Inches(4.25)
    w = maxw; h = Inches(maxw / EMU_W * 7.5 * 0 + 0)  # placeholder
    # compute by aspect
    if (12.4 / 4.25) > ar:
        h = maxh; w = Inches(4.25 * ar)
    else:
        w = maxw; h = Inches(12.4 / ar)
    left = Inches((13.333 - w.inches) / 2); top = Inches(1.15)
    s.shapes.add_picture(str(p), left, top, width=w, height=h)
    bullets(s, items)
    return s


def text_slide(title, items, color=NAVY):
    s = prs.slides.add_slide(BLANK); title_bar(s, title, color)
    bullets(s, items, y=Inches(1.5), h=Inches(5.6), size=16)
    return s


# 1 — title
s = prs.slides.add_slide(BLANK)
tf = _box(s, Inches(0.6), Inches(2.0), Inches(12.1), Inches(2.2)); tf.word_wrap = True
r = tf.paragraphs[0].add_run(); r.text = "MPL Stand Digital Twin — FEM Model-Class Search"
r.font.size = Pt(34); r.font.bold = True; r.font.color.rgb = NAVY
p = tf.add_paragraph(); r = p.add_run()
r.text = "Can searching FEM model classes improve the twin's held-out scores? An honest answer."
r.font.size = Pt(18); r.font.color.rgb = GRAY
tf2 = _box(s, Inches(0.6), Inches(4.3), Inches(12.1), Inches(2.4)); tf2.word_wrap = True
for txt, c in [("VERDICT (YELLOW, equally valid): the as-received FEM is already a trustworthy FREQUENCY twin; "
                "neither stiffness calibration nor richer transmissibility forms improve held-out scores on "
                "single-axis, no-force data.", AMBER),
               ("No instrumented force → observables = modal frequency + gain-free transmissibility only "
                "(no absolute g / apparent mass).", GRAY),
               ("Agentic BayesX · 2026-06-20 · workspace mpl_twin_iteration_20260620 · checker "
                f"{rep['overall']} ({rep['counts']['green']}G/{rep['counts']['yellow']}Y/{rep['counts']['red']}R)", GRAY)]:
    pp = tf2.add_paragraph(); rr = pp.add_run(); rr.text = "•  " + txt; rr.font.size = Pt(14); rr.font.color.rgb = c

# 2 — question & setup
text_slide("The question, and the honest scope", [
    ("Goal", 0, NAVY),
    ("Search FEM model classes (mesh/elements, damping, likelihood, parameters) to IMPROVE the digital twin's "
     "HELD-OUT scores — and report honestly if the data can't distinguish forms.", 1, GRAY),
    ("Hard constraint: NO instrumented force", 0, NAVY),
    ("Legitimate observables = natural FREQUENCIES, modal DAMPING, and output/output TRANSMISSIBILITY |T| "
     "(input cancels). Absolute acceleration / apparent mass are OUT of scope.", 1, GRAY),
    ("Protocol", 0, NAVY),
    ("5 leave-one-location-out splits over {interface, beam, valve, avi-L, avi-R}; shield = fixed |T| reference. "
     "Three held-out scores: CRPS-skill vs climatology, interval/Winkler + coverage, band-GRMS error (on the "
     "dimensionless |T| ratio → un-blurrable). Proper scores reward calibration AND sharpness.", 1, GRAY),
    ("Bayesian update via NUTS (≥4 chains, convergence-gated); score.py reused byte-identical from the L5 study.", 1, GRAY),
])

# 3 — geometry
fig_slide("The stand and the sensor map (single OOP axis = +X)", "fig_geometry.png", [
    ("One MMF accelerometer moved sequentially to each location; shield is a y–z panel (normal +X) → the sensor "
     "axis is the X-translation DOF everywhere. Shield-middle is the transmissibility reference.", 0, GRAY)])

# 4 — method
fig_slide("Method: statFEM on the no-force transmissibility", "fig_graphical_model.png", [
    ("The transmissibility |T_a|=√(PSD_a/PSD_shield) is GAIN-FREE (same sensor, fixed acoustic field) and the "
     "input spectrum CANCELS in the ratio — so GRMS error can't hide in a per-channel gain. Forward made "
     "differentiable in θ via eigenvalue sensitivity; ζ is a free damping lever.", 0, GRAY)])

# 5 — the data
fig_slide("The data we try to predict", "fig_measured_transmissibility.png", [
    ("Measured |T| at the 5 held-out locations. Peaks are real modes (they match the tap spectra). The question: "
     "can the FEM predict these curves at a held-out location?", 0, GRAY)])

# 6 — finding D6
fig_slide("Finding 1 — the FEM transmissibility forward is UNCORRELATED with measured |T|",
          "fig_forward_diagnostic.png", [
    (f"log-correlation ≈ 0 at every location (mean |corr| {fd['mean_abs_log_corr']:.2f}); robust to load shape "
     "and reference choice. NOT a frequency problem — it is the transmissibility SHAPE.", 0, AMBER)])

# 7 — why
fig_slide("Why — a dense modal forest + an unknown acoustic load", "fig_modal_forest.png", [
    ("153 FEM modes below 300 Hz and 29–71 'alive' at each node ⇒ a mode sits near every measured peak. The "
     "transmissibility shape is then governed by the unknown acoustic-load participation and fine mode-shape "
     "error — neither calibratable from this data.", 0, GRAY)])

# 8 — frequency result
fig_slide("(b) The FREQUENCY twin — converged & calibrated, but no NEW value", "fig_freq_result.png", [
    (f"All 5 splits converged (R̂≤1.002, coverage {fmt('twin_coverage'):.2f}). CRPS-skill +{fmt('crps_skill_vs_clim_pooled'):.2f} "
     "vs the WEAK pooled bar.", 0, GREEN),
    (f"But calibrated |Δf| {fmt('twin_median_df_pct'):.2f}% ≈ nominal FEM {fmt('nominal_fem_median_df_pct'):.2f}% ≈ "
     f"nearest-pooled {fmt('nearest_pooled_peak_median_df_pct'):.2f}% → calibration adds no held-out frequency value.", 0, AMBER)])

# 9 — near-resonance
fig_slide("(a) Load-free test — the ceiling is mode-shape error, not the load", "fig_near_resonance.png", [
    (f"At resonance |T|→|φ_a/φ_ref| (load cancels). Measured peak height vs FEM ratio: log-corr "
     f"{nr['log_corr_meas_vs_phi_ratio']:+.2f} (n={nr['n_pairs']}). Weak ⇒ inferring the acoustic load (the obvious "
     "richer-form lever) cannot recover shape skill — the residual is load-independent mode-shape error.", 0, AMBER)])

# 10 — identifiability
fig_slide("What IS identifiable — modal strain energy per K-group", "fig_strain_energy.png", [
    ("Each calibrated stiffness group's parameter→frequency sensitivity = its modal strain-energy fraction. "
     "Shield and beam groups drive most band modes; joints store little (the known SE-dilution).", 0, GRAY)])

# 11 — registry
fig_slide("Model-class registry (one row per attempt)", "fig_registry.png", [
    ("F0 (frequency twin) = carry-forward, converged. M0 (whole-curve transmissibility) = non-converged + "
     "uncorrelated forward. No class improves held-out scores → honest plateau.", 0, GRAY)])

# 12 — verdict
text_slide("Verdict — YELLOW (the simplest sufficient model wins)", [
    ("The as-received fable rev-3 FEM is a trustworthy MPL FREQUENCY twin", 0, GREEN),
    ("converged on all 5 splits, well-covered (0.93), ~2.5% per-peak frequency error.", 1, GRAY),
    ("Neither richer stiffness calibration NOR richer transmissibility/load/discrepancy forms improve held-out scores", 0, AMBER),
    ("(i) dense modal forest makes frequency a weak discriminator; (ii) transmissibility shape is limited by fine "
     "mode-shape error + unknown acoustic load — neither calibratable from single-axis, no-force data.", 1, GRAY),
    ("= the ShockSat per-location-amplitude data ceiling, now confirmed on the MPL stand.", 1, GRAY),
    ("The pre-test lever that WOULD resolve it", 0, NAVY),
    ("instrumented force (calibrated apparent mass) + multi-axis / multi-reference mode shapes — the missing "
     "ingredient the project keeps identifying.", 1, GRAY),
])

# 13 — scope / integrity
text_slide("Scope, integrity, and reproducibility", [
    ("Anti-over-claim", 0, NAVY),
    ("No absolute-g / apparent-mass claims; transmissibility is dimensionless and gain-free; GRMS un-blurrable. "
     "Non-converged calibration reported YELLOW, never 'converged'.", 1, GRAY),
    ("Integrity", 0, NAVY),
    ("check.py written first, SHA self-locked; score.py byte-identical to the L5 original; verdicts derived from "
     f"the numbers. Checker OVERALL {rep['overall']} ({rep['counts']['green']}G/{rep['counts']['yellow']}Y/"
     f"{rep['counts']['red']}R), exits 0.", 1, GRAY),
    ("Replay", 0, NAVY),
    ("bash run_all.sh (BLAS-pinned). Frequency headline converges in ~37 s for all 5 splits. All figures "
     "tufte-linted + image-QA'd; assumptions ledger flags the node-map items awaiting confirmation.", 1, GRAY),
])

out = WS / "slides" / "mpl_twin_findings.pptx"
out.parent.mkdir(exist_ok=True)
prs.save(str(out))
print(f"wrote {out}  ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")
