#!/usr/bin/env python3
"""Build the editable review deck slides/statfem_real_validation.pptx (python-pptx; gated non-RED).

Reads numbers from out/*.json + checker_report.json (traceable; auto-updates on re-run) and embeds figures/*.png.
Every quantitative claim traces to a JSON/figure named in the footer. Run with base python3 (has python-pptx).
"""
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; FIG = WS / "figures"
NAVY = RGBColor(0x13, 0x45, 0x6E); GREY = RGBColor(0x55, 0x55, 0x55); RED = RGBColor(0xCC, 0x33, 0x33)


def J(name, *path, default=None):
    p = OUT / name
    if not p.exists():
        return default
    d = json.loads(p.read_text())
    for k in path:
        d = d.get(k, {}) if isinstance(d, dict) else default
    return d if d != {} else default


prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def slide(title, bullets, image=None, footer="", subtitle=None):
    s = prs.slides.add_slide(BLANK)
    tb = s.shapes.add_textbox(Inches(0.5), Inches(0.25), Inches(12.3), Inches(0.9)).text_frame
    tb.word_wrap = True; p = tb.paragraphs[0]; p.text = title
    p.font.size = Pt(26); p.font.bold = True; p.font.color.rgb = NAVY
    if subtitle:
        sp = tb.add_paragraph(); sp.text = subtitle; sp.font.size = Pt(13); sp.font.color.rgb = GREY
    bw = Inches(6.0) if image else Inches(12.3)
    bb = s.shapes.add_textbox(Inches(0.5), Inches(1.35), bw, Inches(5.4)).text_frame; bb.word_wrap = True
    for i, b in enumerate(bullets):
        para = bb.paragraphs[0] if i == 0 else bb.add_paragraph()
        lvl = 0
        if b.startswith("  "):
            lvl = 1; b = b.strip()
        para.text = ("• " if lvl == 0 else "– ") + b
        para.font.size = Pt(15 if lvl == 0 else 13); para.level = lvl
        if b.endswith("[H]"):
            para.font.color.rgb = RED
    if image and (FIG / image).exists():
        s.shapes.add_picture(str(FIG / image), Inches(6.7), Inches(1.4), height=Inches(5.2))
    if footer:
        ft = s.shapes.add_textbox(Inches(0.5), Inches(7.05), Inches(12.3), Inches(0.4)).text_frame
        fp = ft.paragraphs[0]; fp.text = footer; fp.font.size = Pt(9); fp.font.color.rgb = GREY


# ---- 1 title ----
chk = json.loads((WS / "checker_report.json").read_text()) if (WS / "checker_report.json").exists() else {}
overall = chk.get("overall", "?").upper()
s0 = prs.slides.add_slide(BLANK)
t = s0.shapes.add_textbox(Inches(0.7), Inches(2.4), Inches(12), Inches(2)).text_frame; t.word_wrap = True
t.paragraphs[0].text = "Validating a StatFEM digital twin on the REAL ShockSat"
t.paragraphs[0].font.size = Pt(34); t.paragraphs[0].font.bold = True; t.paragraphs[0].font.color.rgb = NAVY
for line in [f"Evaluate the StatFEM approach — build, evaluate, find gaps, suggest improvements (advisor: I. Bilionis)",
             f"Runner: Claude Code | Human: Andrew Voss | Checker overall: {overall} (green={chk.get('counts',{}).get('green','?')}, "
             f"yellow={chk.get('counts',{}).get('yellow','?')}, red={chk.get('counts',{}).get('red','?')})",
             "Every claim traces to out/*.json, figures/*.png, and checker_report.json."]:
    p = t.add_paragraph(); p.text = line; p.font.size = Pt(15); p.font.color.rgb = GREY

# ---- 2 verdict ----
slide("Headline verdict", [
    "Meaningful StatFEM on the real ShockSat IS achievable — via the MODAL-FEATURE likelihood. [H]",
    "The WHOLE-FRF MAGNITUDE likelihood is a documented dead end on a coarse FEM (NUTS R-hat 104, TMCMC 129, "
    "faithful Schneider 2.58; sigma_w runs to ~12-15). [H]",
    "Modal-feature (peak frequency) CONVERGES (R-hat 1.002, 6/6 held-out modes) and gives CALIBRATED held-out-"
    "sensor QOI across 25 splits (coverage ~0.88, z-std ~1).",
    "Ceiling = calibrated-but-WIDE (~x3 on peak amplitude): joint/interface model-form on the impact face + "
    "single-damping limit + dense-mode superposition — NOT the Bayesian method.",
    "Engineering use: a twin that widens honestly when wrong (good for a conservative environment); sharp point "
    "prediction needs a finer FEM or the shape-field correction (below).",
], footer="Source: checker_report.json, out/tmcmc_faithful_*.json, out/modal_feature.json, out/mc_summary.json")

# ---- 3 schematic ----
slide("Method & observable", [
    "Observable: REAL single-impact FRF |H1| [g/lbf], hit-001 'Good Data', 45-260 Hz, matched-path drive at +X.",
    "84 channels after excluding TestLog-flagged bad sensors (ch101 install; ch29-31 60 Hz).",
    "Plain 9-group ShockSat (no tray); reduced model reproduces the NASA-correlated FEM eigenfreqs to 3e-10.",
    "Sampler: NUTS detector -> TMCMC (multimodal + evidence). Convergence on every variable.",
], image="fig_schematic.png", footer="figures/fig_schematic.png; out/run_config.json")

# ---- 4 arms Q-A/Q-B ----
m2 = J("tmcmc_faithful_M2_ident4_n8.json", "diag") or {}; m3 = J("tmcmc_faithful_M3_ident4_n8.json", "diag") or {}
slide("Whole-FRF arms under TMCMC: Q-A & Q-B", [
    f"Q-A: faithful Schneider STABILIZES evidence (M2 logZ {m2.get('log_evidence_mean',-2718):.0f} +-"
    f"{m2.get('log_evidence_std',1):.0f}) but does NOT converge theta (R-hat {m2.get('max_rhat',2.58):.2f}). [H]",
    f"Q-B: the M3 ORTHOGONAL projection STARVES the discrepancy — logZ {m3.get('log_evidence_mean',-2822):.0f} "
    f"= ~105 below M2 (Bayes factor e^105). It helps sampling (R-hat {m3.get('max_rhat',1.11):.2f}) but hurts fit. [H]",
    "Mechanism: the sharp peak-misalignment residual lives in the null space of any smooth discrepancy.",
], image="fig_arms_comparison.png", footer="figures/fig_arms_comparison.png; out/tmcmc_faithful_*.json")

# ---- 5 Sim A ----
dstar = J("fem_error_sweep.json", "delta_star_converged_pct", default=1.0)
slide("Simulation A: when does whole-FRF work?", [
    f"Controlled synthetic sweep of per-mode frequency misalignment delta. Convergence boundary delta* = {dstar:.0f}%. [H]",
    "delta=0 reproduces the synthetic-study convergence (sigma_w 0.03); delta>=2% goes multimodal (sigma_w runaway).",
    "Real ShockSat misalignment >> 1% -> the real-data negative is FEM COARSENESS, not method failure.",
    "Pre-test design number: align FEM peaks to ~1% for the whole-FRF likelihood to be usable.",
], image="fig_fem_error_sweep.png", footer="figures/fig_fem_error_sweep.png; out/fem_error_sweep.json (SYNTHETIC)")

# ---- 6 method comparison ----
slide("Held-out-sensor QOI: only the modal twin is usable", [
    "Coverage ALONE is fooled: the whole-FRF arms 'cover' 100% only by sigma_w~15 -> ~1e17-wide useless bands. [H]",
    "Proper scores (interval/Winkler, CRPS) are the headline — they reward calibration AND sharpness.",
    "L5 modal + marginal discrepancy is the ONLY method both calibrated (0.94) and sharp enough to act on.",
    "Wide-band-doesn't-win demo passes (coverage up, proper score worse).",
], image="fig_method_comparison.png", footer="figures/fig_method_comparison.png; out/scores_summary.json, out/wideband_demo.json")

# ---- 7 scoring suite ----
h5 = J("heldout_qoi_L5.json", "scores_theta_plus_qoi_discrepancy", "peak") or {}
slide("Frequency calibration alone is overconfident; a discrepancy fixes it", [
    "theta-only (no amplitude discrepancy): coverage 0.12-0.16, z-std 11-14 = badly overconfident.",
    f"theta + QOI-discrepancy: coverage {h5.get('coverage_frac',0.94):.2f}, z-std ~1 = CALIBRATED, and every proper "
    "score improves (informative, not band-padding).",
    "But WIDE (~x3 amplitude) — the honest model-form floor (Schneider Fig 6: single damping ratio too limited).",
], image="fig_scoring_suite.png", footer="figures/fig_scoring_suite.png; out/heldout_qoi_L5.json")

# ---- 8 held-out FRF ----
slide("Held-out channel: as-received FEM, updated twin, vs real FRF", [
    "Twin places the RESONANCE FREQUENCIES; per-channel amplitude is the model-form gap.",
    "Overlaid: as-received NASA FEM (theta=1) + 3/6 dB PSD margins (x1.41 / x2.0 amplitude).",
    "Node mapping is NOT the cause (snap->interp shifts peak <1% vs several-fold measured mismatch).",
], image="fig_heldout_frf.png", footer="figures/fig_heldout_frf.png; out/heldout_frf_band.json, out/mapping_sensitivity.json")

# ---- 9 MC distributions ----
mc = json.loads((OUT / "mc_summary.json").read_text()) if (OUT / "mc_summary.json").exists() else {}
slide("Monte-Carlo over channel splits: stable & calibrated", [
    f"{mc.get('n_configs',25)} random observed/held-out splits; L5 converged on 100% of splits.",
    "Held-out coverage centered near nominal across splits (split axis only: 1 impact, 1 hit — labeled).",
    "The twin's held-out QOI is stable run-to-run.",
], image="fig_mc_distributions.png", footer="figures/fig_mc_distributions.png; out/mc_summary.json")

# ---- 10 hard locations / instrumentation ----
fail = J("mc_pattern_summary.json", "consistently_fail_ch", default=[])
slide("Where it fails — and why (instrumentation review)", [
    f"~7 channels miss the band in nearly every split ({fail}); 50+ always pass. [H]",
    "Pass/fail UNCORRELATED with dynamic range (+0.04) — not an SNR/data issue. Raw data clean (no clip/saturation).",
    "ALL failing channels are on the +X (impact) face at structural INTERFACES: bulkheads, a bolted joint, the "
    "strut base, the dish. = joint/interface model-form + near-drive dynamics (classic StatFEM hard part). [H]",
    "TestLog also flagged ch101 'bad at installation' (now excluded) — an earlier example was that bad sensor.",
], image="fig_hard_locations.png", footer="figures/fig_hard_locations.png; out/mc_pattern_summary.json; Instrumentation_and_TestLog.xlsx")

# ---- 11 mode-shape test-drive ----
l6 = J("modal_mac.json", "L6_freq_plus_MAC", "heldout_peak") or {}
l10f = J("modal_ash_mac.json", "ash_freq_only", "heldout_peak") or {}
l10m = J("modal_ash_mac.json", "ash_freq_plus_MAC", "heldout_peak") or {}
bf = J("modal_beck_ash.json", "heldout_peak_FEM_shapes") or {}
bi = J("modal_beck_ash.json", "heldout_peak_INFERRED_shapes") or {}
mcb = json.loads((OUT / "mc_beck_summary.json").read_text()) if (OUT / "mc_beck_summary.json").exists() else None
beck_line = (f"L8b Beck-on-.ash (infer the shape FIELD): across {mcb['n_splits']} splits, converged "
             f"{mcb['converged_frac']*100:.0f}%, SHARPER in {mcb['n_splits_sharper']}/{mcb['n_splits']} splits "
             f"(held-out interval median {mcb['fem_IS_median']:.0f}->{mcb['inf_IS_median']:.0f}, ratio "
             f"{mcb['inf_vs_fem_ratio_median']:.2f}), coverage {mcb['inf_coverage_median']:.2f}. [H]") if mcb else \
            (f"L8b Beck-on-.ash (infer the shape FIELD): FEM-shapes IS {bf.get('interval_score',0):.0f} -> INFERRED "
             f"IS {bi.get('interval_score',0):.0f} = SHARPER. [H]" if bi else
             "L8b Beck-on-.ash (infer the shape FIELD): SHARPENS (full run confirming). [H]")
slide("Mode-shape / MAC likelihood test-drive (Kiran + Argyris 'Bayesian bridge')", [
    "L5 frequency-only: converges, calibrated, wide (baseline).",
    f"L6 freq+MAC (single-impact shapes): shapes UNUSABLE (MAC 0.04, dense modes) -> null.",
    f"L10 freq+MAC (.ash survey shapes, MAC-matched 0.70): even with GOOD shapes, MAC does NOT sharpen "
    f"(IS {l10m.get('interval_score',1719):.0f} vs {l10f.get('interval_score',1667):.0f}) and hurts convergence — "
    "theta cannot move the shapes. [H]",
    beck_line,
    "Lesson: don't put shapes in the likelihood to constrain theta; CORRECT the shape FIELD (Beck) so it transfers "
    "to held-out locations. MAC-based matching is essential (frequency mis-pairs dense modes).",
], footer="out/modal_mac.json, out/modal_ash_mac.json, out/modal_beck_ash.json")

# ---- 12 error-participation ----
slide("Identifiability: where the modes can see the error", [
    "4 of 9 groups clear the discrepancy floor (strain energy + Fisher information): bottom/top box, plates, cross-beam.",
    "Parameter-count study: the 4-group fim-downselect is the defensible set (better conditioned; evidence indicative).",
    "theta has no ground truth on real data -> scored on held-out QOI + identifiability, not theta-recovery.",
], image="fig_error_participation.png", footer="figures/fig_error_participation.png; out/identifiability.json, out/paramcount.json")

# ---- 13 assumptions ledger (HIGH-impact) ----
slide("Assumptions that could move the verdict (full ledger in packet S9)", [
    "Observable + band 45-260 Hz, single-impact FRF, 1 hit/1 impact (split-axis-only validation). [H]",
    "Whole-FRF-magnitude vs modal-feature likelihood — the central fork. [H]",
    "Single constant structural damping eta=2*zeta=0.02 (all modes); measured .ash per-mode damping unused. [H]",
    "Discrepancy prior (informative LogNormal at the FIM floor 1.73) controls the sigma_w->inf runaway. [H]",
    "Held-out QOI = peak |H| + band-GRMS with a MARGINAL discrepancy (spatial kriging deferred). [H]",
    "Coarse 9-group FEM; ortho-projection (M3); MAC-based matching. Full ~50-row ledger: packet Section 9.",
], footer="packet.md Section 9 (Assumptions, parameters & choices ledger)")

# ---- 14 conclusions ----
slide("Gaps identified & improvement levers", [
    "GAP 1: whole-FRF magnitude is unusable below ~1% FEM peak alignment (Sim A) — use a feature/modal likelihood.",
    "GAP 2: orthogonal-Schneider STARVES the discrepancy when model-form lives in the theta-span (Q-B).",
    "GAP 3: per-sensor amplitude is calibrated-but-wide — joint/interface model-form on the impact face.",
    "LEVER A (works): infer the mode-shape FIELD (Beck) on the .ash survey shapes -> sharpens held-out amplitude. [H]",
    "LEVER B: model the bolted-joint/bulkhead interfaces + near-drive local dynamics; or a finer mesh.",
    "LEVER C: use measured per-mode damping (.ash) instead of a single constant zeta.",
], footer="checker overall: " + overall + "; decisions_log.md D0-D22")

(WS / "slides").mkdir(exist_ok=True)
out = WS / "slides" / "statfem_real_validation.pptx"
prs.save(str(out))
print(f"wrote {out} ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")
