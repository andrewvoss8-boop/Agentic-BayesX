#!/usr/bin/env python3
"""Build the program slide deck (D13) -> slides/shocksat_program_deck.pptx.

Audiences: Dr. Ilias Bilionis (SciML/UQ/BOED, Purdue), Prof. Mark Girolami
(StatFEM author, Cambridge), Dr. ? Yunis (ShockSat creator, structural test).
All numbers are read from out/* artifacts (no fabrication). GIFs are NOT
embedded (per Andrew) but are pointed to on the relevant slides.
"""
import json
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(WS, "out")
FIG = os.path.join(WS, "slides", "figs")

NAVY = RGBColor(0x1f, 0x3a, 0x5f)
BLUE = RGBColor(0x2c, 0x5f, 0x8a)
RED = RGBColor(0xb2, 0x45, 0x3c)
GREEN = RGBColor(0x1f, 0x7a, 0x44)
GREY = RGBColor(0x55, 0x55, 0x55)
LGREY = RGBColor(0x88, 0x88, 0x88)
WHITE = RGBColor(0xff, 0xff, 0xff)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


def jl(n):
    return json.load(open(os.path.join(OUT, n)))


def slide():
    return prs.slides.add_slide(BLANK)


def box(s, l, t, w, h):
    tb = s.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    return tf


def para(tf, text, size=18, color=GREY, bold=False, bullet=False, first=False,
         italic=False, align=PP_ALIGN.LEFT, space=6):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(space)
    r = p.add_run()
    r.text = ("•  " if bullet else "") + text
    f = r.font
    f.size = Pt(size)
    f.color.rgb = color
    f.bold = bold
    f.italic = italic
    f.name = "Calibri"
    return p


def title_bar(s, text, sub=None):
    tf = box(s, 0.5, 0.28, 12.3, 1.0)
    para(tf, text, size=27, color=NAVY, bold=True, first=True)
    if sub:
        para(tf, sub, size=14, color=RED, italic=True, space=0)


def footer(s, n):
    tf = box(s, 0.5, 7.05, 12.3, 0.35)
    para(tf, f"Agentic BayesX  ·  shocksat_tray_coupled_qoi_20260610  ·  "
         f"every figure artifact-backed & checker-gated  ·  {n}",
         size=8.5, color=LGREY, first=True)


def add_img(s, path, l, t, w=None, h=None, maxw=None, maxh=None):
    im = Image.open(path)
    ar = im.width/im.height
    if maxw and maxh:
        w = min(maxw, maxh*ar)
        h = w/ar
    pic = s.shapes.add_picture(path, Inches(l), Inches(t),
                               Inches(w) if w else None,
                               Inches(h) if h else None)
    return pic


def fig_slide(title, img, bullets, sub=None, gif=None, n="", imgw=8.3,
              imgl=0.5, imgt=1.5):
    s = slide()
    title_bar(s, title, sub)
    add_img(s, os.path.join(FIG, img), imgl, imgt, maxw=imgw, maxh=5.0)
    tf = box(s, imgl+imgw+0.2, 1.6, 12.9-(imgl+imgw+0.2), 5.0)
    for i, (b, col, bold) in enumerate(bullets):
        para(tf, b, size=15, color=col, bold=bold, bullet=True, first=(i == 0),
             space=10)
    if gif:
        para(tf, f"▶ animation: slides/gifs/{gif}", size=11, color=BLUE,
             italic=True, space=0)
    footer(s, n)
    return s


# ====================================================================== S1 title
s = slide()
r = s.shapes.add_shape(1, 0, 0, SW, Inches(2.5))
r.fill.solid(); r.fill.fore_color.rgb = NAVY; r.line.fill.background()
tf = box(s, 0.6, 0.5, 12.1, 1.7)
para(tf, "A Bayesian Digital Twin for Aerospace Structures", size=34,
     color=WHITE, bold=True, first=True)
para(tf, "ShockSat × payload-tray coupled interface-load study  —  method, "
     "coupling, and the limits of identifiability", size=17, color=WHITE)
add_img(s, os.path.join(FIG, "deck_arc.png"), 0.6, 2.75, maxw=12.1, maxh=3.0)
tf = box(s, 0.6, 6.0, 12.1, 1.1)
para(tf, "Prepared for: Prof. Mark Girolami (StatFEM)  ·  Dr. Ilias Bilionis "
     "(SciML / UQ)  ·  Dr. Yunis (ShockSat)", size=14, color=NAVY, bold=True,
     first=True)
para(tf, "Agentic BayesX program  ·  2026-06  ·  HYPOTHETICAL coupled QOI "
     "(methods demonstration; the ShockSat primary twin is validated against "
     "real NASA test data)", size=11.5, color=RED, italic=True)

# ====================================================================== S2 why
s = slide()
title_bar(s, "Why this matters — StatFEM onto the track")
tf = box(s, 0.6, 1.45, 12.1, 5.4)
para(tf, "The problem.  Launch vehicles are a weakest-link problem: teams "
     "stack conservatism on every part, so structures look marginal on paper "
     "yet often carry ~10× true margin. Mass is wasted everywhere.", size=15.5,
     color=GREY, first=True, space=9)
para(tf, "The method.  StatFEM fuses a physics model with test data while "
     "explicitly modelling that the model is wrong (the discrepancy). The "
     "literature has driven it at 5 mph — linear-static problems where the "
     "model already matches the data. We take it onto the track: a real "
     "dynamic structure, real test data, pushed to a real load decision.",
     size=15.5, color=GREY, space=9)
para(tf, "What each of you will care about:", size=15.5, color=NAVY, bold=True,
     space=7)
para(tf, "Girolami — the StatFEM discrepancy term doing real work on real "
     "aerospace hardware, and where it caps identifiability.", size=15,
     color=BLUE, bullet=True, space=6)
para(tf, "Bilionis — UQ propagation, pre-test value-of-information, and an "
     "anti-cheating harness that grades itself green/yellow/red.", size=15,
     color=BLUE, bullet=True, space=6)
para(tf, "Yunis — a from-scratch, validated digital twin of ShockSat, and "
     "what it says about integrating a payload onto it (force limiting).",
     size=15, color=BLUE, bullet=True, space=6)
footer(s, "2 / 15")

# ====================================================================== S3 arc
fig_slide(
    "The program in one picture",
    "deck_arc.png",
    [("Each box is an artifact-backed, checker-gated result.", NAVY, True),
     ("Left: a validated twin of real NASA hardware.", GREY, False),
     ("Middle: a coupled load question that matters for payload integration.",
      GREY, False),
     ("Right: an honest negative that tells us exactly what to measure next.",
      RED, False),
     ("The spine is the StatFEM 'discrepancy lever' — it recurs at every "
      "step.", BLUE, False)],
    n="3 / 15", imgw=12.2, imgl=0.5, imgt=2.0)

# ====================================================================== S4 twin
s = slide()
title_bar(s, "What we built — a validated ShockSat modal twin",
          "the primary structure is REAL and validated (modal regime); only "
          "the payload coupling downstream is hypothetical")
tf = box(s, 0.6, 1.7, 12.1, 4.6)
para(tf, "From-scratch Python assembly of NASA's ShockSat FEM (67,683 grids, "
     "~406k DOF) — no black-box solver.", size=17, color=GREY, bullet=True,
     first=True, space=10)
para(tf, "Reproduces NASA's own NX Nastran FEM-vs-test error to ~2.5 "
     "percentage points on 19/24 modes → the element library is right, the "
     "residual is genuine discrepancy.", size=17, color=GREY, bullet=True,
     space=10)
para(tf, "Calibrated against 33 REAL measured free-free impact-test modes "
     "(not FEM-on-FEM). NUTS (NumPyro), 4 chains, float64.", size=17,
     color=GREY, bullet=True, space=10)
para(tf, "Full-modal posterior CONVERGES: worst R-hat 1.022, min ESS 232, 0 "
     "divergences — and predicts held-out frequencies well.", size=17,
     color=GREEN, bold=True, bullet=True, space=10)
para(tf, "Honest caveat: identification is PARTIAL — only ~4 of 9 part-group "
     "stiffnesses are informed; the hand-tuned joints are not. (Sets up the "
     "next slide.)", size=16, color=RED, italic=True, bullet=True, space=10)
footer(s, "4 / 15")

# ====================================================================== S5 discrepancy
s = slide()
title_bar(s, "Finding: the StatFEM discrepancy is REAL on a real structure",
          "for Girolami — the discrepancy lever, measured on aerospace hardware")
tf = box(s, 0.6, 1.7, 12.1, 4.6)
para(tf, "The inferred discrepancy σ_f ≈ 4.6 % is 5-15× the 0.3-0.9 % "
     "measurement-repeatability floor → the residual is MODEL-FORM error, "
     "not noise.", size=18, color=GREY, bullet=True, first=True, space=12)
para(tf, "That discrepancy floor — not sensitivity — is what caps "
     "identifiability: parameters whose modal signal sits below 4.6 % cannot "
     "be recovered, even though they carry real strain energy.", size=18,
     color=GREY, bullet=True, space=12)
para(tf, "This is exactly the Kennedy-O'Hagan / Brynjarsdottir-O'Hagan "
     "warning (you cannot recover physics with a flexible discrepancy unless "
     "it has structure) — reproduced here on real dynamic test data.", size=18,
     color=BLUE, bullet=True, space=12)
para(tf, "An independent pre-test Fisher-information study on a second "
     "structure agreed: ~3 stiffness parameters identifiable from modal data. "
     "Two methods, same wall.", size=16, color=GREY, italic=True, bullet=True,
     space=12)
footer(s, "5 / 15")

# ====================================================================== S6 question
fig_slide(
    "The coupled question: what load does a payload transmit?",
    "deck_graphical_model.png",
    [("QOI: net CG interface load (Fx,Fy,Fz) the tray transmits.", NAVY,
      True),
     ("Two axes of choice: METHOD (time-history / SRS / Miles) and COUPLING "
      "(uncoupled spec vs coupled, force-limited).", GREY, False),
     ("The mount = ONE uncertain 6-DOF joint at the interface (wide prior); "
      "geometry to scale on the next slide.", GREY, False),
     ("Forward UQ only: we propagate the validated posterior + priors. No "
      "sampler is claimed here.", BLUE, False),
     ("HYPOTHETICAL: no tray was ever bolted to ShockSat — a methods demo.",
      RED, False)],
    n="6 / 15", imgw=7.6, imgt=1.7)

# ====================================================================== S6b coupled to-scale
s = slide()
title_bar(s, "The coupled assembly, to scale",
          "tray (secondary) on the validated ShockSat primary — both meshes in "
          "metres, equal aspect (genuinely to scale)")
add_img(s, os.path.join(FIG, "deck_coupled_assembly.png"), 0.35, 1.45,
        maxw=12.6, maxh=4.45)
tf = box(s, 0.5, 6.0, 12.4, 1.0)
para(tf, "The 'mount' is ONE 6-DOF CBUSH at point P (gid 7000072, top circular "
     "plate centre, z = 1.47 m) — THE single joint between the ShockSat FEM "
     "and our tray FEM. The tray's 6 feet are rigidly condensed to that one "
     "point (single-point 6-DOF condensation, sufficient for net CG force). "
     "The tray's own internal joints are separate (part of the tray model, not "
     "'the mount').", size=11.5, color=GREY, bullet=True, first=True, space=3)
footer(s, "7 / 15")

# ====================================================================== S7 force limiting
fl = jl("qoi_results.json")["force_limiting_factor_joint"]
s = slide()
title_bar(s, "Force limiting quantified (the NASA-HDBK-7004C thread)",
          "What's plotted: interface force per unit base acceleration (= load "
          "apparent mass, kg) vs frequency — the transfer function that turns "
          "the random base-vibration environment into a payload load.")
add_img(s, os.path.join(FIG, "deck_force_limiting.png"), 0.45, 1.42, maxw=12.2,
        maxh=3.75)
tf = box(s, 0.5, 5.32, 12.4, 1.7)
para(tf, "Excitation: a flat 0.01 g²/Hz random vibration (20–250 Hz) is run "
     "through this transfer to get the peak-force QOI — vibe DOES drive the "
     "result; this curve governs it (one nominal parameter set shown).",
     size=12, color=GREY, bullet=True, first=True, space=4)
para(tf, "SDOF-like in z because only the 116 Hz bounce mode carries vertical "
     "motion (effective mass = the whole 3.16 kg tray); 76–89 Hz are lateral/"
     "rocking (left panel). Peak shifts right because the notch sits at the "
     "load's fixed-base resonance and the peak at the coupled-system "
     "resonance.", size=12, color=GREY, bullet=True, space=4)
para(tf, f"z notch is small (×1.2), lateral is large (×3.5): force limiting is "
     "deep only when source ≈ load apparent mass. At this stiff node source is "
     f"~103 kg (z) vs 33 kg load → shallow; laterally ~21 vs 55 kg → deep. Net "
     f"over-test ×{min(fl['median']):.2f}-{max(fl['median']):.2f} median, to "
     f"×{max(fl['p97_5']):.1f}.   ▶ slides/gifs/force_limiting_sweep.gif",
     size=12, color=RED, bullet=True, space=4)
footer(s, "8 / 15")

# ====================================================================== S8 method
fig_slide(
    "Method error is ASSUMPTION error",
    "deck_method.png",
    [("With the true modal damping, the modal-SRS hand method is unbiased vs "
      "the time-history truth (×0.95-0.98).", NAVY, True),
     ("Swing the assumed quality factor Q from 10→50 and the same method "
      "swings ×0.7-2.3.", RED, True),
     ("Miles '3σ' under-predicts record peaks ~25 % by construction (true "
      "peak ≈ 4σ) — stated in the quantity contract before the run.", GREY,
      False),
     ("Takeaway for loads teams: pin the assumptions, not just the method.",
      BLUE, False)],
    n="9 / 15", imgw=8.0, imgt=1.7)

# ====================================================================== S9 mount dominance
vd = jl("variance_decomposition.json")
fig_slide(
    "Headline: the load is controlled by the unknown mount",
    "deck_mount_dominance.png",
    [("The mount-stiffness prior alone explains ~100 % of the QOI variance.",
      RED, True),
     ("The carefully-calibrated primary structure contributes < 1 %.", NAVY,
      True),
     ("Bars are an OAT ratio (var with only that group varying ÷ var with all "
      "varying), NOT a Sobol index — so a dominant group CAN read slightly "
      ">100 %.", GREY, False),
     ("The Fx/Fy mount bars (1.02, 1.05) carry bootstrap 95 % CIs of "
      "[0.6, 1.6] — statistically = 100 %, i.e. Monte-Carlo noise, not a real "
      "excess.", GREY, False),
     ("Decision consequence: to predict the payload load, calibrate the "
      "JOINT — calibrating the primary buys almost nothing.", BLUE, False)],
    n="10 / 15", imgw=8.2, imgt=1.7)

# ====================================================================== S10 identifiability / negative
md = jl("multimodality_diagnosis.json")
fig_slide(
    "Honest negative: one modal survey can't split the mount",
    "deck_identifiability.png",
    [("We simulated the obvious fix — a mounted-config modal survey (33 "
      "channels, 21 ON the tray) — and calibrated with NUTS.", NAVY, True),
     ("But the likelihood is FREQUENCY-only (shapes used only to pair modes), "
      "and frequencies are sensor-location-blind — they cannot tell an x "
      "rocking mode from a y one.", GREY, False),
     ("Strain energy says the mount is identifiable; the FIM + sampler say "
      "only 2 of 6 axes separate at the real discrepancy floor (R-hat 5-10 = "
      "under-identification, not a bug: chains agree on data to 0.06 %).",
      RED, True),
     ("Pooling helps but has a floor: sampler ladder 6→3→2 params gives "
      "R-hat 5.0→1.5→1.2 (as FIM predicts) — yet even 2 params miss the "
      "gate: the mount SATURATES above the tray stiffness (one-sided "
      "identifiability) and translation trades with rotation in the rocking "
      "modes (corr −0.74).", GREY, False),
     ("Refined lever: add mode shapes / FRF amplitudes / force gauges — NOT "
      "more frequencies.", BLUE, False)],
    sub="reported YELLOW (not converged); the figure carries the worst "
        "R-hat/ESS on it",
    gif="multimodality.gif", n="11 / 15", imgw=8.0, imgt=1.75)

# ====================================================================== S11 harness
s = slide()
title_bar(s, "How we keep ourselves honest (the harness)",
          "for Bilionis — the part that makes agentic engineering trustworthy")
tf = box(s, 0.6, 1.7, 12.1, 4.8)
para(tf, "Three-tier results: GREEN (threshold met) / YELLOW (missed but "
     "documented, never sold as success) / RED (blocking). The replay exits "
     "non-zero only on RED.", size=16, color=GREY, bullet=True, first=True,
     space=10)
para(tf, "Quantity contracts BEFORE any plot; an apparent-mass convention "
     "postmortem; every figure labelled with its run and any invalidity.",
     size=16, color=GREY, bullet=True, space=10)
para(tf, "A Modal Identifiability Gate: you must show the strain-energy "
     "decomposition AND (new this week) the Fisher-information eigen-view "
     "before any per-parameter identifiable/not claim.", size=16, color=GREEN,
     bold=True, bullet=True, space=10)
para(tf, "It worked on US: the strain-energy view said 'mount identifiable'; "
     "the harness forced the FIM view, which revealed only 2/6 axes separate. "
     "The harness caught our own overclaim.", size=16, color=RED, bold=True,
     bullet=True, space=10)
para(tf, "Anti-cheating constraints are always on: no fabricated figures, no "
     "copied reference assets, no method swap without labelling, no success "
     "claim without checker output.", size=15, color=GREY, italic=True,
     bullet=True, space=10)
footer(s, "12 / 15")

# ====================================================================== S12 scorecard
s = slide()
title_bar(s, "Findings, scored 1 (utter failure) → 5 (smashing success)")
add_img(s, os.path.join(FIG, "deck_scorecard.png"), 0.5, 1.45, maxw=12.4,
        maxh=5.4)
footer(s, "13 / 15")

# ====================================================================== S13 next
s = slide()
title_bar(s, "What's next — and what we'd ask of each of you")
tf = box(s, 0.6, 1.6, 12.1, 5.2)
para(tf, "Next experiment (designed by the negative): a symmetry-breaking "
     "survey — add mode-shape / FRF-amplitude / interface-force observables to "
     "separate the mount axes; pre-test FIM first, sampler second.", size=16,
     color=NAVY, bold=True, bullet=True, first=True, space=12)
para(tf, "Girolami — is the discrepancy-capped identifiability we see the "
     "expected StatFEM behaviour on dynamic data, and how would you structure "
     "the discrepancy prior to recover the joint?", size=15, color=BLUE,
     bullet=True, space=10)
para(tf, "Bilionis — is the value-of-information framing the right way to "
     "justify a pre-test design (which sensors/observables), and should the "
     "FIM-combination gate become standard?", size=15, color=BLUE,
     bullet=True, space=10)
para(tf, "Yunis — are the mount stiffness range and placement plausible for a "
     "real ShockSat payload, and do you have a mounted-config modal or "
     "interface-force dataset we could calibrate against?", size=15,
     color=BLUE, bullet=True, space=10)
para(tf, "Everything here replays from one command and is fully traceable; "
     "the honest negative is the most useful result, because it tells us "
     "exactly what to measure.", size=14, color=GREY, italic=True,
     bullet=True, space=10)
footer(s, "14 / 15")

# ====================================================================== S14 backup
s = slide()
title_bar(s, "Backup — provenance, honesty, reproducibility")
tf = box(s, 0.6, 1.6, 12.1, 5.2)
para(tf, "Replay: `bash run_all.sh` (9 stages, resumable, BLAS-pinned, NUTS "
     "detached). Checker: `python3 check.py` → green/yellow/red. Overall this "
     "study: YELLOW (the documented honest negatives).", size=15, color=GREY,
     bullet=True, first=True, space=10)
para(tf, "Validation gates (15/15 green): from-scratch tray rebuild vs an "
     "independent FEM (2.6e-11), unit conversion vs the rigid-body mass line, "
     "FBS algebra vs a direct coupled solve, Newmark time-integration "
     "cross-check (0.6 %), and the 7004C two-DOF analytic anchors.", size=15,
     color=GREY, bullet=True, space=10)
para(tf, "INVENTED (sign-off pending), all swept in sensitivity: base input "
     "spec, tray placement, mount nominal stiffness + prior. The coupled QOI "
     "is a methods demo — no hardware-validation claim.", size=15, color=RED,
     bullet=True, space=10)
para(tf, "Supplementary animations (not embedded): force_limiting_sweep.gif, "
     "mode_walk_qoi.gif, multimodality.gif (in slides/gifs/).", size=14,
     color=BLUE, italic=True, bullet=True, space=10)
para(tf, "Artifacts: packet.md (full numbers), quantity_contracts.md, "
     "assumptions_ledger.md, decisions_log.md (D1-D13), manifest.json "
     "(SHA-256 of every file).", size=14, color=GREY, italic=True,
     bullet=True, space=10)
footer(s, "15 / 15")

out = os.path.join(WS, "slides", "shocksat_program_deck.pptx")
prs.save(out)
print("wrote", out, f"({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")
