#!/usr/bin/env python3
"""2-slide Bilionis update deck (consolidation only — NO new science; figures are provenance-labeled COPIES).
Slide 1: one-paragraph status + ShockSat image (FEM node cloud, 9 calibration groups).
Slide 2: held-out FRF comparison grid (data vs original vs updated FEM).
Numbers are copied from checker-backed artifacts (composite_bakeoff_20260702, netcg_20260701,
modelclass_L5_20260619, bilionis_review_20260626); nothing stated stronger than the checkers."""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"
DARK = RGBColor(0x1F, 0x4E, 0x79); GREY = RGBColor(0x66, 0x66, 0x66)

PARA = (
    "Working on ShockSat — the most complex structure attempted for Bayesian FEM updating relative to the "
    "literature; everything is scored on held-out data (held-out sensors, held-out drive points, and a "
    "hide-known-modes audit that disqualifies overconfident methods). Posterior predictive bands cover the "
    "held-out data but are too wide for industry use; the width is traceable to a specific cluster of "
    "unmeasured modes (~234–258 Hz, purchasable with one >200 Hz modal test), and the industry-standard "
    "FEM+6dB envelope actually UNDER-covers the same data — so the honest state is “wide but never "
    "lying.” The direction needed to match the data is orthogonal to what the stiffness parameters and "
    "forward model can provide: inferring the mode shapes themselves (Beck-style) is the one formulation that "
    "moves that way and is my best per-point predictor (held-out CRPS-skill −0.78 → −0.34), but "
    "it is overconfident when propagated to load QOIs driven by the unmeasured modes. I also ran the idea I "
    "thought most promising — agentic FEM remodeling: ~150 agent-generated model-form candidates, "
    "screened through full eigensolves, selected by Bayesian evidence on a shape-inclusive likelihood; the "
    "evidence picked a winner decisively (posterior model probability ~0.7 over the as-delivered FEM) and it "
    "then failed to improve held-out prediction at all — evidence-based model-class selection is still an "
    "in-sample criterion under this much model-form error and must be gated by held-out validation. Not much "
    "for aerospace industry yet; I think the contribution is to the literature, mostly the negatives nobody "
    "publishes (evidence ≠ held-out, remodeling null, MAC-in-likelihood null, shape-field "
    "sharp-but-unsafe) plus the validation harness itself, all on a real NASA-correlated structure. Nothing "
    "patentable as far as I can tell; I may prefer a simple ipynb module over a paper — could ask "
    "Dr. Gibert if he is interested."
)


def footer(slide, text):
    tb = slide.shapes.add_textbox(Inches(0.25), Inches(7.05), Inches(12.8), Inches(0.4)).text_frame
    tb.word_wrap = True
    p = tb.paragraphs[0]; p.text = text
    p.font.size = Pt(8); p.font.color.rgb = GREY


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # ---- slide 1: paragraph + ShockSat image ----
    s = prs.slides.add_slide(blank)
    tb = s.shapes.add_textbox(Inches(0.35), Inches(0.2), Inches(12.6), Inches(0.6)).text_frame
    p = tb.paragraphs[0]; p.text = "ShockSat Bayesian FEM updating — status (2026-07-02)"
    p.font.size = Pt(26); p.font.bold = True; p.font.color.rgb = DARK
    body = s.shapes.add_textbox(Inches(0.35), Inches(0.95), Inches(8.1), Inches(5.9)).text_frame
    body.word_wrap = True
    p = body.paragraphs[0]; p.text = PARA; p.font.size = Pt(13.5)
    s.shapes.add_picture(str(FIG / "reuse_L5_param_locations.png"), Inches(8.7), Inches(0.95), height=Inches(5.9))
    footer(s, "Image: ShockSat FEM node cloud, side view (base→dish), colored by the 9 stiffness-calibration "
              "groups [copy of shocksat_modelclass_L5_20260619/figures/fig_param_locations.png]. Numbers: "
              "checker-backed artifacts shocksat_composite_bakeoff_20260702 (OVERALL YELLOW 57G/6Y/0R) + "
              "shocksat_netcg_method_selection_20260701 (GREEN 22/0/0).")

    # ---- slide 2: FRF comparison ----
    s = prs.slides.add_slide(blank)
    tb = s.shapes.add_textbox(Inches(0.35), Inches(0.15), Inches(12.6), Inches(0.75)).text_frame
    tb.word_wrap = True
    p = tb.paragraphs[0]
    p.text = ("FRF comparison, measured vs FEM (12 channels spanning the agreement range): updating aligns "
              "peaks, the per-channel SHAPE error remains — the wall")
    p.font.size = Pt(20); p.font.bold = True; p.font.color.rgb = DARK
    s.shapes.add_picture(str(FIG / "reuse_psdenv_frf_comparison_grid.png"), Inches(0.55), Inches(1.0),
                         width=Inches(12.2))
    footer(s, "Measured |H| (black) vs original FEM (blue dashed) vs deterministically updated FEM (orange); "
              "ONE global gain, NO per-channel fitting; log-log. Median log|H| correlation 0.269→0.338 "
              "(70% of channels improve) — far below the ~0.7 needed for per-point industry use; this "
              "per-channel shape error is what drives the wide (but covering) posterior bands. [Copy of "
              "shocksat_psd_envelope_twin_20260623/figures/frf_comparison_grid.png]")

    out = WS / "slides" / "bilionis_update_20260702.pptx"
    prs.save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
