#!/usr/bin/env python3
"""Build report/packet.pptx for the BLIND round (review layer). Embeds the key figures + headline numbers."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / ".pylibs"))
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

OUT = HERE / "report"; FIG = OUT / "figures"
res = json.load(open(OUT / "blind_results.json"))
qoi = json.load(open(OUT / "blind_qoi_results.json"))
conv = res["convergence"]["with_d_CAPPED_discrepancy_MAIN"]

prs = Presentation(); prs.slide_width = Inches(13.33); prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]; TITLE = prs.slide_layouts[5]


def title_slide(t, sub):
    s = prs.slides.add_slide(BLANK)
    tx = s.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(12.3), Inches(1.2)).text_frame
    tx.word_wrap = True; tx.text = t
    tx.paragraphs[0].font.size = Pt(30); tx.paragraphs[0].font.bold = True
    tx.paragraphs[0].font.color.rgb = RGBColor(0x1f, 0x3a, 0x5f)
    p = tx.add_paragraph(); p.text = sub; p.font.size = Pt(15); p.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    return s


def bullets(s, lines, top=1.7, left=0.6, width=12.0, size=15):
    tf = s.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(5.3)).text_frame
    tf.word_wrap = True
    for i, (txt, lvl) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = txt; p.level = lvl; p.font.size = Pt(size - 2 * lvl)


def pic_slide(t, img, caption=""):
    s = title_slide(t, caption)
    if (FIG / img).exists():
        s.shapes.add_picture(str(FIG / img), Inches(0.7), Inches(1.7), height=Inches(5.4))
    return s


# 1 title
title_slide("BLIND StatFEM inference vs an INDEPENDENT ground truth",
            "Round 3 · Claude Code Opus 4.8 · inference runner (blind). Master scores vs the SEALED truth.")
bullets(prs.slides[-1], [
    ("HEADLINE: the independent truth carries model-form error OUTSIDE my coarse model's span ->", 0),
    ("the hierarchical StatFEM NUTS inference does NOT converge (multimodal / sigma_d<->sigma_e ridge),", 1),
    ("held-out coverage is 'wide-but-covering', and the netCG QOI is biased ~5x high.", 1),
    ("This is the intended outcome of a genuine blind test — recovery is not a tautology, and it breaks.", 0),
    ("I do NOT claim 'NUTS active'. Consumed ONLY published observations; sealed truth never opened.", 0),
], top=3.0)

# 2 method
s = title_slide("Method (coarse NOMINAL design model)", "")
bullets(s, [
    ("Observed/inferred: published per-build 6-DOF diagonal interface APPARENT MASS (8 builds x 6 DOF x 4040 f).", 0),
    ("Forward model: M_base6 (rigid, from low-f asymptote) + hexapod(k_strut, 6 equal struts) + dome axial resonator(f_dome).", 0),
    ("Anchors: tray axial 86.25 Hz, dome bounce 93.5 Hz. Likelihood: whole-curve log|app. mass| (magnitude), 40-115 Hz.", 0),
    ("Adaptive grid from DATA peaks (true modes unknown), 62 pts, fixed during inference.", 0),
    ("Inferred: k_strut + sigma_build (hierarchy) + f_dome + sigma_e + discrepancy d (sigma_d capped, ell_d fixed -> break ridge).", 0),
    ("Sampler: NumPyro NUTS, 4 chains, 1000+1000, non-centered. Magnitude-only -> damping fixed (eta=0.04).", 0),
], top=1.7)

# 3 convergence
s = title_slide("Convergence — FAILS the gate (honest)", "")
bullets(s, [
    (f"worst rank-split R-hat = {conv['worst_rhat']:.2f} ({conv['worst_rhat_var']})  [gate < 1.01]  -> FAIL", 0),
    (f"min bulk ESS = {conv['min_ess_bulk']:.0f}, min tail ESS = {conv['min_ess_tail']:.0f}  [gate >= 400]  -> FAIL", 0),
    (f"divergences = {conv['divergences']}/{conv['n_draws_total']} (0.0%)  [gate < 2%]  -> ok; 4 chains, non-centered -> ok", 0),
    ("Fast steps but NO between-chain mixing -> genuine MULTIMODALITY (same at 150 & 1500 warmup).", 0),
    ("sigma_e inflates to 0.62 (log) ~ factor 1.85 misfit. EVERY variant fails (flexible-d ridge; minimal bimodal k_strut;", 0),
    ("pure-physics worst). No single symmetric k_strut fits all 6 DOF; as-built shows symmetry-breaking mode splits.", 1),
    ("Best-available marginals (NOT-YET-CONVERGED): k_strut 1.42e7 [1.08e7,3.29e7]; f_dome 83.2; sigma_e 0.62.", 0),
], top=1.7, size=14)

# 4 held-out calibration figure
pic_slide("Held-out calibration (PRIMARY trust test)",
          "blind_heldout_calibration.png",
          "Hold out whole builds + a whole frequency band. New-build cov 0.94 but log-width 2.84 (~12x) = WIDE-BUT-COVERING; band cov 0.88 (<0.95). n_eff(k_strut)~0.9 vs 1800 pts.")

# 5 posteriors figure
pic_slide("Learned parameters (true values SEALED — master scores)", "blind_posteriors.png",
          "k_strut biased low + bimodal; f_dome pulled below nominal 93.5; sigma_build/sigma_e non-identified (ridge).")

# 6 QOI figure
pic_slide("netCG QOI vs test spec — full uncertainty", "blind_netcg_psd_vs_spec.png",
          f"Predicted 3*GRMS q50 {qoi['netcg_3grms_g_PREDICTED_full_uncertainty']['netcg_3grms_g_q50']:.2f} g vs published 0.46-0.96 g (~5x high). 99%-hi exceeds spec on {100*qoi['narrow_band_exceedance']['frac_freqs_99hi_exceeds_spec']:.0f}% of band; overall margin {qoi['narrow_band_exceedance']['overall_scalar_margin_spec_over_pred']:.1f}x.")

# 7 QOI hist
pic_slide("netCG 3*GRMS: predicted (full uncertainty) vs published", "blind_netcg_3grms.png",
          "Driving-point QOI mapping ~2x high (measured on published data) x inflated/multimodal posterior -> ~5x; published low tail below my 99% CI = honest over-prediction.")

# 8 expected bias + fix
s = title_slide("Where I expect to be biased / under-covering — and the fix", "")
bullets(s, [
    ("k_strut biased low, f_dome low, both non-identified (multimodal).", 0),
    ("sigma_e inflated; sigma_build/sigma_d non-identified (frequency-only discrepancy can't represent the error).", 0),
    ("netCG QOI biased ~5x high; under-covers the published low tail; held-out band coverage 0.88.", 0),
    ("Nothing modeled > 115 Hz; no asymmetry / lateral dome dynamics; magnitude-only (no damping).", 0),
    ("FIX: structure-based (per-strut/property) discrepancy; asymmetric / higher-fidelity forward model;", 0),
    ("complex (mag+phase) likelihood; possibly modular/cut updating. -> next stage.", 1),
], top=1.7)

prs.save(str(OUT / "packet.pptx"))
print("wrote", OUT / "packet.pptx", "slides:", len(prs.slides._sldIdLst))
