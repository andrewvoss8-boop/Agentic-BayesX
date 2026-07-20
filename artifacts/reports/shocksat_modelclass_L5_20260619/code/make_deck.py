#!/usr/bin/env python3
"""Assemble the ShockSat L5 twin PowerPoint from the deck figures + concise, scope-accurate bullets."""
from __future__ import annotations
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"
NAVY = RGBColor(0x1f, 0x33, 0x5e); GREY = RGBColor(0x60, 0x60, 0x60); RED = RGBColor(0xb2, 0x18, 0x2b)
GREEN = RGBColor(0x1b, 0x78, 0x37)
prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def slide(title, bullets, image=None, footer="", title_color=NAVY, img_w=8.3):
    s = prs.slides.add_slide(BLANK)
    tb = s.shapes.add_textbox(Inches(0.45), Inches(0.22), Inches(12.4), Inches(0.85)).text_frame
    tb.word_wrap = True; p = tb.paragraphs[0]; p.text = title
    p.font.size = Pt(24); p.font.bold = True; p.font.color.rgb = title_color
    bw = Inches(4.4) if image else Inches(12.4)
    if bullets:
        bb = s.shapes.add_textbox(Inches(0.5), Inches(1.25), bw, Inches(5.7)).text_frame
        bb.word_wrap = True
        for i, (txt, lvl, col) in enumerate(bullets):
            par = bb.paragraphs[0] if i == 0 else bb.add_paragraph()
            par.text = ("• " if lvl == 0 else "   – ") + txt
            par.font.size = Pt(15 if lvl == 0 else 12.5); par.level = lvl
            par.font.color.rgb = col if col else RGBColor(0x20, 0x20, 0x20)
    if image and (FIG / image).exists():
        left = Inches(13.333 - img_w - 0.25) if bullets else Inches((13.333 - img_w) / 2)
        s.shapes.add_picture(str(FIG / image), left, Inches(1.2), width=Inches(img_w))
    if footer:
        fb = s.shapes.add_textbox(Inches(0.45), Inches(7.02), Inches(12.4), Inches(0.4)).text_frame
        fb.word_wrap = True; fp = fb.paragraphs[0]; fp.text = footer
        fp.font.size = Pt(8.5); fp.font.color.rgb = GREY
    return s


B = lambda t, lvl=0, col=None: (t, lvl, col)

# 1 title
s = prs.slides.add_slide(BLANK)
t = s.shapes.add_textbox(Inches(0.7), Inches(2.5), Inches(12), Inches(2)).text_frame; t.word_wrap = True
t.paragraphs[0].text = "Calibrated ShockSat digital twin: where Bayesian model updating has value — and where it doesn't"
t.paragraphs[0].font.size = Pt(30); t.paragraphs[0].font.bold = True; t.paragraphs[0].font.color.rgb = NAVY
st = s.shapes.add_textbox(Inches(0.7), Inches(4.4), Inches(12), Inches(1.5)).text_frame; st.word_wrap = True
st.paragraphs[0].text = ("Real single-impact hammer FRF + NASA modal survey, reduced 74-DOF FEM, NUTS calibration, "
                         "held-out scoring vs a no-skill baseline. Agentic BayesX / StatFEM — Andrew Voss.")
st.paragraphs[0].font.size = Pt(15); st.paragraphs[0].font.color.rgb = GREY

# 2 executive summary
slide("Executive summary", [
    B("Modal FREQUENCY: strong value — held-out CRPS-skill +0.93 vs climatology; calibration halves the FEM "
      "frequency error (2.10%→1.07%).", 0, GREEN),
    B("Per-channel single-impact AMPLITUDE: honestly calibrated (covers) but does NOT beat climatology.", 0, RED),
    B("Strongest amplitude lever = MODEL FORM: inferring the mode-shape FIELD (Beck/L8b) sharpens interval ~43% and "
      "HALVES the skill deficit (−0.68→−0.25, coverage→0.97) — real, but still < 0.", 1, NAVY),
    B("Damping / FEM-shape-as-θ / richer stiffness / joint topology / discrepancy structure: little-to-no amplitude gain.", 1),
    B("≥10 likelihood/observable formulations evaluated; the converging+useful ones are MODAL (freq + shape field).", 0),
    B("Single-impact amplitude is improved-but-not-solved: a partial model-form lever exists, full skill needs "
      "multi-reference data — not a method dead-end.", 0, NAVY),
], "fig_value_summary.png", img_w=7.0,
    footer="CRPS-skill = 1 − CRPS_twin/CRPS_climatology. Real ShockSat, ≥3 held-out splits. (Slides 12–15 give the full lever + likelihood inventory.)")

# 3 setup / sensors
slide("Setup: the satellite, the sensors, the hard regions", [
    B("Plain standalone 9-group ShockSat (stacked: boxes, bulkheads, bolted joint, struts, dish).", 0),
    B("Single-impact hammer FRF, 45–260 Hz; 77 high-DR accelerometers; one drive (impact) node.", 0),
    B("8 a-priori HARD accels (red): impact face, bulkhead box column, bolted joint, strut, dish.", 0, RED),
    B("These are the known model-form hotspots (Card D region diagnosis).", 1),
], "fig_sensor_map.png", img_w=5.0,
    footer="Side view (x vs z). Hard = impact face / bulkheads / bolted joint / strut / dish.")

# 4 parameters
slide("What we calibrate: 9 stiffness groups", [
    B("θ_g scales each group's stiffness (exact modulus scaling).", 0),
    B("Groups: bottom/top box, steel/Al welds, angle brackets, cross-beam, plates, joints (bolted CBUSH), contact.", 0),
    B("Calibrated from MEASURED modal frequencies (L5 likelihood), NUTS, all-variable convergence gate.", 0),
    B("Identifiable from frequency: bottom/top box, cross-beam, plates. Joints/welds/contact: weak.", 1),
], "fig_param_locations.png", img_w=5.0,
    footer="FEM node cloud colored by calibration group, side view.")

# 5 strain energy
slide("Strain energy: which modes inform which parameters", [
    B("SE fraction f = φᵀ(θ A_g)φ / λ — how much each mode loads each group.", 0),
    B("Low modes → bottom box; high modes → top box; mid → plates / cross-beam.", 0),
    B("JOINTS column is dark: ~3% SE (peak ~20% at one 151 Hz mode).", 0, RED),
    B("→ joint stiffness AND damping are strain-energy-diluted → weakly identifiable from this data.", 1, RED),
], "fig_strain_energy.png", img_w=6.6,
    footer="Matched measured modes × 9 groups. Joints SE-diluted = a recurring roadblock for joint/damping inference.")

# 6 train/test
slide("The held-out experiment", [
    B("Random split of eligible channels: observe 60%, predict 40% (≥3 seeds).", 0),
    B("θ calibrated ONLY on observed-channel modal frequencies.", 0),
    B("Held-out channel's |H| is NEVER used in fitting → genuine prediction.", 0, NAVY),
    B("Score the held-out QOI (peak accelerance, band-GRMS) + held-out modal frequencies.", 0),
], "fig_train_test_split.png", img_w=5.0,
    footer="One split shown (seed 0). Same protocol for amplitude and frequency value.")

# 7 scoring
slide("The scoring system", [
    B("Each held-out channel/mode gets a predictive DISTRIBUTION, scored vs the measured truth.", 0),
    B("Coverage: is truth in the 95% interval (calibration).", 0),
    B("Interval score / CRPS: reward SHARP and calibrated together.", 0),
    B("SKILL = 1 − CRPS_twin/CRPS_climatology.", 0, NAVY),
    B("Climatology = no-skill baseline that guesses from the observed-channel population.", 1),
    B("Skill > 0 only if the model carries information beyond the population.", 1, GREEN),
], "fig_scoring_schematic.png", img_w=7.2,
    footer="The deterministic FEM point (no UQ) is a weak bar; climatology is the honest baseline.")

# 8 FRF
slide("Held-out FRF: twin band vs measured", [
    B("Twin θ-posterior |H| band (blue) vs measured (black) at held-out channels.", 0),
    B("HARD (top): the band misses the measured peak by 10–20+ dB — FEM mode shape gives the wrong per-channel level.", 0, RED),
    B("EASY (bottom): closer, but still wide.", 0, GREEN),
    B("The miss is the cross-channel SHAPE error, not frequency (peaks line up).", 0, NAVY),
], "fig_frf_examples.png", img_w=8.0,
    footer="Real single-impact ShockSat, seed-0 held-out channels. Log–log |H| (g/lbf). Band = θ posterior.")

# 9 GRMS
slide("Band-GRMS: predicted vs measured", [
    B("Band energy QOI (GRMS, 45–260 Hz) per held-out channel.", 0),
    B("Wide scatter for BOTH hard and easy channels around the 1:1 line.", 0, RED),
    B("Same story as the peak: the per-channel amplitude/energy is poorly predicted by the FEM shapes.", 0),
    B("Bars = twin 95% band — covers, but wide.", 1),
], "fig_grms.png", img_w=5.6,
    footer="Held-out band-GRMS, twin band vs measured. Log–log.")

# 10 scores hard/easy
slide("Scores at hard vs easy locations", [
    B("A: coverage ~ honest for both (twin band covers the truth).", 0),
    B("B: the as-received FEM point misses by ~6 dB (easy) to ~20 dB (hard).", 0),
    B("C: amplitude SKILL vs climatology is NEGATIVE for both — the model adds no amplitude information.", 0, RED),
    B("Easy sensors are 'easy' only relative to hard — still no positive amplitude skill.", 1),
], "fig_scores_hard_easy.png", img_w=8.0,
    footer="Held-out peak accelerance. Coverage honest, but skill < 0 = worse than guessing the population.")

# 11 value
slide("Value of updating: frequency vs amplitude", [
    B("FREQUENCY: skill +0.93; updating halves the as-received FEM frequency error.", 0, GREEN),
    B("AMPLITUDE (peak & band): skill ≈ −1.0; every lever stays ≤ 0.", 0, RED),
    B("The twin is a trustworthy, valuable FREQUENCY twin; an honest-but-no-skill amplitude predictor.", 0, NAVY),
], "fig_value_summary.png", img_w=7.6,
    footer="Held-out CRPS-skill vs climatology. Amplitude levers: damping / shapes / stiffness / topology / discrepancy structure.")

# 12 roadblock damping
slide("Roadblock 1 — Damping", [
    B("Frequency-blind: damped-freq shift 5.5e-5 ≪ 7% floor.", 0),
    B("The exponential window adds ζ_w(f) = 0.23–1.22% — comparable to the real modal ζ (0.06–1.05%).", 0, RED),
    B("df=1.25 Hz can't resolve the half-power bandwidth → damping unmeasurable from this FRF.", 0),
    B("Interface-CBUSH loss factors are strain-energy-diluted (unidentifiable).", 0),
    B("Injecting the true per-mode ζ makes held-out scores WORSE (windowed FRF under-resolves light modes).", 0, RED),
], "fig_roadblock_damping.png", img_w=7.6,
    footer="Damping is per-mode/channel-common → absorbed by the gain → cannot tighten a cross-channel CI.")

# 12b damping inference (closing the to-do, run not argued)
slide("Damping inference — run, not argued (closes the to-do)", [
    B("Per-mode Bayesian SDOF resonance fit (multi-channel, exact 2-D (f,ζ) posterior, residues marginalized).", 0),
    B("Result: 0 of 9 fittable modes give an IDENTIFIED damping.", 0, RED),
    B("Posteriors are prior-dominated (e.g., 48.8 Hz: ζ 0.06–5.84%) or railed to the resolution floor.", 1),
    B("df=1.25 Hz + window can't resolve the half-power width of these lightly-damped modes.", 1),
    B("Per-mode ζ unidentifiable ⇒ localized-CBUSH (Das–Debnath) attribution is moot (also SE-diluted).", 0, NAVY),
    B("Confirms by RUNNING: damping is not recoverable from this single windowed FRF.", 0),
], "fig_damping_inference.png", img_w=7.4,
    footer="damping_inference.py — the resonance width is the only un-confounded damping signal, and it's below resolution here.")

# 13 roadblock remesh
slide("Roadblock 2 — Re-meshing / stiffness", [
    B("Mesh already converged (Card D): finer mesh can't move modes.", 0),
    B("6000 joint-stiffness updates: 0 improve hard-region MAC without detuning frequency (Pareto wall).", 0, RED),
    B("Bayesian evidence (Ockham): richer LOCAL stiffness does NOT earn its complexity — full-rich(16p) is worst.", 0, RED),
    B("Stiffness is not the lever; the residual is shape/amplitude, not frequency.", 0, NAVY),
], "fig_roadblock_remesh.png", img_w=7.8,
    footer="Card D joint frontier + Card F Stage-1 analytic evidence (BIC-adjusted, prior-robust).")

# 14 roadblock likelihood (convergence contrast)
slide("Roadblock 3 — Likelihood: whole-FRF vs modal", [
    B("Whole-FRF magnitude likelihood is locally identifiable / multimodal:", 0),
    B("NUTS R̂≈104, TMCMC R̂≈129, σ_d runaway → non-converged.", 1, RED),
    B("Modal peak-FREQUENCY likelihood CONVERGES (R̂ 1.002) — the working twin.", 0, GREEN),
    B("Cross-channel amplitude pattern ~0.15-correlated with FEM or measured shapes (per-mode).", 0),
    B("(This is 2 of ≥10 formulations — full inventory next slide.)", 0, NAVY),
], "fig_roadblock_likelihood.png", img_w=7.6,
    footer="Whole-FRF vs modal-feature convergence + shape-pattern correlation.")

# 14b full likelihood inventory (correction: many formulations, not 2)
slide("Likelihood / observable inventory — the full set (≥10)", [
    B("The program evaluated ~10–11 formulations, not 2.", 0, NAVY),
    B("Converge & useful (green): modal peak-FREQUENCY; INFERRED shape field (Beck); shape MAC; analytic evidence.", 0, GREEN),
    B("Converge but ~null / single-hit limit (amber): freq+MAC-as-θ; complex PHASE (incoherent single hit).", 0),
    B("Non-converged / multimodal (red): whole-FRF magnitude; peak-AMPLITUDE feature (R̂ 55); correlated discrepancy.", 0, RED),
    B("Pattern: the converging, useful observables are MODAL.", 0, NAVY),
], "fig_likelihood_inventory.png", img_w=8.4,
    footer="Sources: Card A out/{modal_feature,modal_beck,modal_beck_ash,modal_mac,modal_ash_mac,phase_likelihood,modal_amp_feature,paramcount,tmcmc_faithful_*}.json + this thread.")

# 14c model-form lever that helps amplitude (correction)
slide("Model-form lever that DOES help amplitude: infer the shape FIELD", [
    B("Beck/L8b: the system mode shapes become FREE parameters pulled to the .ash measured shapes (MAC) + Rayleigh.", 0),
    B("Unlike MAC-as-θ-constraint (L6/L10), this corrects the shape FIELD → transfers to held-out locations.", 1),
    B("Result (3 splits): interval ~43% sharper, coverage→0.97, σ_QOI 0.92→0.86.", 0, GREEN),
    B("CRPS-skill deficit HALVED: FEM shapes −0.68 → inferred −0.25.", 0, GREEN),
    B("Still < 0 (doesn't beat climatology on one impact) — improved, not solved.", 0, RED),
    B("Corrects the earlier 'no model-form lever helps amplitude' — model form DOES matter.", 0, NAVY),
], "fig_shapefield_lever.png", img_w=7.4,
    footer="Held-out impact-channel peak |H|, 3 splits. modal_beck_ash.py (L8b), converged R̂ 1.003–1.004.")

# 15 spatial structure (re-examined per Andrew)
slide("Is there a spatial pattern to the hard sensors? (re-examined)", [
    B("Partly yes: a MILD regional concentration — bolted-joint region worst (12.3 dB), dish/strut elevated.", 0, NAVY),
    B("Physically sensible (interface + free-boundary model-form error).", 1),
    B("But weak as a PREDICTOR: region/feature location explains only R²=0.04 of the residual.", 0, RED),
    B("Co-located channels vary hugely; proximity to a feature does NOT predict hardness.", 1),
    B("So a physical-region discrepancy prior is justified but captures only a small fraction;", 0),
    B("the dominant variation is a channel-specific near-field nugget.", 1),
], "fig_spatial_reanalysis.png", img_w=7.6,
    footer="Residual vs distance to impact/joint/strut/dish/bulkheads. MEASURED data.")

# 15b over-fitting caution
slide("Caution: the hand-labeled 'hard' split is over-fit", [
    B("A 2-population (hard vs rest) discrepancy tightens the easy channels ~28% — but it's OVER-FIT as a method.", 0, RED),
    B("No a-priori FEM feature predicts which channels are hard (drive-dist/locality/DR ρ≈0).", 0),
    B("The hard label comes from prior FEM-vs-test comparison → a demonstration, not a turnkey method.", 0, NAVY),
    B("Generalizable version = the physical-region/shape-field priors above, not a hand-label.", 0),
], "fig_hardregion.png", img_w=7.2,
    footer="Reported as a labeled demonstration only.")

# 16 synthesis
slide("What it means (honest synthesis)", [
    B("Modal FREQUENCY — trustworthy and valuable (held-out skill +0.93, halves the as-received FEM error).", 0, GREEN),
    B("Per-channel single-impact AMPLITUDE — honestly calibrated; the strongest lever is MODEL FORM (infer the "
      "shape field): halves the skill deficit & sharpens ~43%, but still doesn't beat climatology on one impact.", 0, NAVY),
    B("Damping (per-mode inference RUN: 0/9 identified — unrecoverable from this FRF), FEM-shape-as-θ, richer "
      "stiffness, joint topology, discrepancy structure: little/no amplitude gain.", 0),
    B("Spatial: a weak physical-region component (joint worst); not a strong predictor (R²=0.04).", 0),
    B("So amplitude is IMPROVED-not-solved on one impact — a partial model-form lever exists; closing it fully "
      "needs multi-reference excitation (the apparent-mass / roving GVT plan).", 0, NAVY),
    B("Report: a valuable frequency twin + an improving (shape-field) amplitude predictor; don't claim FEM replacement.", 0, RED),
], None,
    footer="Levers RUN not argued: damping inference, topology release, measured-shape fusion, INFERRED shape field (Beck), snap & spatial decomposition.")

# 17 next data
slide("Ideal additional data + experiment series", [
    B("Binding limit = single-impact, single-reference, windowed, coarse-resolution FRF.", 0, NAVY),
    B("1. Multi-reference modal survey (≥3–4 refs, force+response, fine res, no/known window) — the keystone:", 0, GREEN),
    B("separates residues from damping, gives clean shapes, proper modal damping.", 1),
    B("2. Force / interface measurement → apparent mass M=F/a (flight QOI), resolves the gain confound.", 0),
    B("3. Joint instrumentation + bolt-torque sweep → joint stiffness & damping + nonlinearity.", 0),
    B("4. Repeat / re-torque / build-to-build → variability for honest discrepancy widths.", 0),
    B("5. Amplitude sweep → microslip / amplitude-dependent damping.", 0),
    B("Step 0 (now, no hardware): FEM-based FIM/VOI pre-test to optimize drives & sensors + predict the skill gain.", 0, NAVY),
], None,
    footer="Each new dataset re-scored with the SAME held-out-skill-vs-climatology framework → measured ROI, not assumed.")

# 18 repro
slide("Status & reproducibility", [
    B("check_twin.py: OVERALL YELLOW (13 GREEN / 2 YELLOW / 0 RED).", 0, NAVY),
    B("Yellows are documented HONEST limitations (amplitude no-skill; damping/topology no-help) — not failures.", 1),
    B("Integrity GREEN: reused L5 code byte-identical to Card A; immutable checker self-SHA lock.", 0, GREEN),
    B("Every figure traces to a saved .py + out/*.json; tufte-linted + image-QA pass; runtime ≈ 2200 s active.", 0),
    B("Surfaced (not self-applied): project_log row; any 'replace the FEM' claim; durable-rule/sampler edits.", 0, RED),
], None,
    footer="Workspace: artifacts/reports/shocksat_modelclass_L5_20260619/. decisions_log.md D0–D19; packet.md.")

out = WS / "slides" / "shocksat_L5_twin_deck.pptx"
out.parent.mkdir(exist_ok=True); prs.save(str(out))
print(f"wrote {out}  ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")
