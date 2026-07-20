#!/usr/bin/env python3
"""
Project status + next steps deck for Agentic BayesX (2026-07-01).

CONSOLIDATION deck: NO new science. Every number traces to a saved file in an
existing workspace (cited in each slide footer). Figures in ../figures are all
COPIES from prior workspaces (reuse_* prefix; provenance in ../README.md and
run_all.sh) — none were generated for this deck.

Status labels follow AGENTS.md: CHECKER-BACKED = SHA-locked grader ran;
EXPLORATORY = figures+numbers, no immutable checker yet.

Run:  python3 make_deck.py  ->  ../slides/project_status_20260701.pptx
"""
from __future__ import annotations
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_AUTO_SIZE

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"
OUT = WS / "slides" / "project_status_20260701.pptx"

NAVY = RGBColor(0x1F, 0x33, 0x5E); GREY = RGBColor(0x5A, 0x5A, 0x5A)
RED = RGBColor(0xB2, 0x18, 0x2B); GREEN = RGBColor(0x1B, 0x78, 0x37)
ORANGE = RGBColor(0xB5, 0x5E, 0x0C); BLUE = RGBColor(0x3A, 0x66, 0xB0)
WHITE = RGBColor(0xFF, 0xFF, 0xFF); DARK = RGBColor(0x20, 0x20, 0x20)

prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
B = lambda t, lvl=0, col=None: (t, lvl, col)


def slide(title, bullets, image=None, footer="", img_w=7.6, img_top=1.25):
    s = prs.slides.add_slide(BLANK)
    tb = s.shapes.add_textbox(Inches(0.45), Inches(0.22), Inches(12.4), Inches(0.95)).text_frame
    tb.word_wrap = True; p = tb.paragraphs[0]; p.text = title
    p.font.size = Pt(23); p.font.bold = True; p.font.color.rgb = NAVY
    bw = Inches(max(4.0, 12.55 - img_w - 0.35)) if image else Inches(12.4)
    if bullets:
        bb = s.shapes.add_textbox(Inches(0.5), Inches(1.3), bw, Inches(5.6)).text_frame
        bb.word_wrap = True; bb.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        for i, (txt, lvl, col) in enumerate(bullets):
            par = bb.paragraphs[0] if i == 0 else bb.add_paragraph()
            par.text = ("• " if lvl == 0 else "    – ") + txt
            par.font.size = Pt(14 if lvl == 0 else 12); par.level = lvl
            par.font.color.rgb = col if col else DARK
            par.space_after = Pt(3)
    if image:
        assert (FIG / image).exists(), f"missing figure: {image}"
        left = Inches(13.333 - img_w - 0.22) if bullets else Inches((13.333 - img_w) / 2)
        s.shapes.add_picture(str(FIG / image), left, Inches(img_top), width=Inches(img_w))
    if footer:
        fb = s.shapes.add_textbox(Inches(0.45), Inches(7.04), Inches(12.4), Inches(0.4)).text_frame
        fb.word_wrap = True; fp = fb.paragraphs[0]; fp.text = footer
        fp.font.size = Pt(8.5); fp.font.color.rgb = GREY
    return s


def divider(kicker, title):
    s = prs.slides.add_slide(BLANK)
    bar = s.shapes.add_shape(1, Inches(0), Inches(2.7), Inches(13.333), Inches(2.1))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    tf = bar.text_frame; tf.word_wrap = True; tf.margin_left = Inches(0.7)
    p0 = tf.paragraphs[0]; p0.text = kicker
    p0.font.size = Pt(15); p0.font.color.rgb = RGBColor(0xA9, 0xC0, 0xE8); p0.font.bold = True
    p1 = tf.add_paragraph(); p1.text = title
    p1.font.size = Pt(30); p1.font.color.rgb = WHITE; p1.font.bold = True
    return s


def table_slide(title, headers, rows, col_w, cell_colors=None, footer="", fontsize=11,
                bullets_below=None):
    s = prs.slides.add_slide(BLANK)
    tb = s.shapes.add_textbox(Inches(0.45), Inches(0.22), Inches(12.4), Inches(0.9)).text_frame
    tb.word_wrap = True; p = tb.paragraphs[0]; p.text = title
    p.font.size = Pt(23); p.font.bold = True; p.font.color.rgb = NAVY
    nr, nc = len(rows) + 1, len(headers)
    tbl = s.shapes.add_table(nr, nc, Inches(0.45), Inches(1.35),
                             Inches(sum(col_w)), Inches(0.5 + 0.6 * len(rows))).table
    for c, w in enumerate(col_w):
        tbl.columns[c].width = Inches(w)
    for c, h in enumerate(headers):
        cell = tbl.cell(0, c); cell.text = h
        para = cell.text_frame.paragraphs[0]
        para.font.size = Pt(fontsize); para.font.bold = True; para.font.color.rgb = WHITE
        cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = tbl.cell(r + 1, c); cell.text = str(val)
            para = cell.text_frame.paragraphs[0]; para.font.size = Pt(fontsize)
            col = cell_colors[r][c] if (cell_colors and cell_colors[r][c]) else DARK
            para.font.color.rgb = col
            cell.fill.solid(); cell.fill.fore_color.rgb = RGBColor(0xF4, 0xF6, 0xFA)
    if bullets_below:
        top = 1.5 + 0.5 + 0.6 * len(rows) + 0.25
        bb = s.shapes.add_textbox(Inches(0.5), Inches(top), Inches(12.3), Inches(1.6)).text_frame
        bb.word_wrap = True
        for i, (txt, lvl, colr) in enumerate(bullets_below):
            par = bb.paragraphs[0] if i == 0 else bb.add_paragraph()
            par.text = "• " + txt; par.font.size = Pt(12.5)
            par.font.color.rgb = colr if colr else DARK; par.space_after = Pt(2)
    if footer:
        fb = s.shapes.add_textbox(Inches(0.45), Inches(7.04), Inches(12.4), Inches(0.4)).text_frame
        fb.word_wrap = True; fp = fb.paragraphs[0]; fp.text = footer
        fp.font.size = Pt(8.5); fp.font.color.rgb = GREY
    return s


# ---------------------------------------------------------------- 1 · title
s = prs.slides.add_slide(BLANK)
bar = s.shapes.add_shape(1, Inches(0), Inches(2.2), Inches(13.333), Inches(2.9))
bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
tf = bar.text_frame; tf.word_wrap = True; tf.margin_left = Inches(0.7)
p0 = tf.paragraphs[0]; p0.text = "Agentic BayesX — project status & next steps"
p0.font.size = Pt(34); p0.font.bold = True; p0.font.color.rgb = WHITE
p1 = tf.add_paragraph()
p1.text = ("A Bayesian digital twin for aerospace structures · ShockSat program · 2026-07-01")
p1.font.size = Pt(17); p1.font.color.rgb = RGBColor(0xA9, 0xC0, 0xE8)
p2 = tf.add_paragraph()
p2.text = ("Consolidation deck — no new science; every number traces to a saved workspace file "
           "(slide footers). Andrew Voss · lead agent: Claude Code")
p2.font.size = Pt(12); p2.font.color.rgb = RGBColor(0xA9, 0xC0, 0xE8)

# ------------------------------------------------------- 2 · one-slide story
slide("The project in one slide", [
    B("GOAL: take StatFEM from the “parking lot” (static, model-matches-data) to a real dynamic "
      "aerospace structure, real test data, and a certifiable loads decision.", 0),
    B("WHAT WE HIT (the wall): per-point FRF bands are HONEST but ~+27 dB — too wide to certify. "
      "Cause isolated: per-node MODE-SHAPE fidelity, a model problem.", 0, RED),
    B("WHAT WE PROVED: no statistical lever and no agentic remeshing closes it — every apparent "
      "remesh gain was a scoring artifact (caught twice, held-out metrics).", 0),
    B("THE PIVOT: match the deliverable’s resolution to what the data supports → integrated "
      "net-CG force QOI, 1-octave-smoothed bands.", 0, BLUE),
    B("WHERE WE ARE NOW: held-out-drive-VALIDATED net-CG shear bands 1.51×/2.30× FEM+6dB "
      "(5/5 drives X, 4/5 Y); honest covering normal band 2.53×. Checker GREEN 22/0/0.", 0, GREEN),
    B("NEXT: the >200 Hz drumhead plate test — REVISED 07-02: a pre-registered rehearsal FALSIFIED "
      "the 3.5x buy-down (12 sensors -> 6.2x); revised scope = resolve ALL 12 band modes (oracle "
      "2.8x), follow-up rehearsal before any hardware ask + two write-ups.", 0),
], footer="src: shocksat_bilionis_review_20260626/packet.md · shocksat_netcg_method_selection_20260701/"
          "findings.md + checker_report (GREEN 22/0/0)")

# ------------------------------------------------ 3 · two contribution targets
slide("Two contribution targets — and what “meaningful” means for each", [
    B("AEROSPACE WORKFLOWS (adoption-first, vision §2.1): loads engineers are skeptical of Bayesian "
      "updating (“GIGO / pencil-whipping / slow”). Meaningful = simple, auditable tools that "
      "plug into their existing FEM + modal-survey process on Monday.", 0),
    B("BAYESIAN FEM-UPDATING / StatFEM LITERATURE: published StatFEM lives on benign, mostly static "
      "cases. Meaningful = real-data results with held-out validation — including a rigorous "
      "negative with the cause isolated, which the literature lacks.", 0),
    B("Our position: one real program (inherited 406k-DOF vendor FEM + NASA-correlated modal survey + "
      "5-drive hammer data) feeds BOTH targets.", 0, BLUE),
], footer="src: notes/project_vision.md §1–§2.1 · review_kiran2025_reading_notes.md")

# ---------------------------------------------------------------- 4 · divider
divider("PART 1 · STATUS", "What we found — the wall, its cause, and the proof")

# ---------------------------------------------------------------- 5 · the wall
slide("The wall: honest bands, too wide to certify (per-point FRF)", [
    B("The twin stays calibrated under large model error — it does NOT give a confident wrong "
      "number (held-out frequency skill +0.93; amplitude coverage 0.97).", 0, GREEN),
    B("But the 95% per-point FRF band needs ~+27 dB — 10–13× the FEM+6dB envelope. "
      "Amplitude σ(log) ≈ 1.6; usable needs ≲ 0.35.", 0, RED),
    B("Premise check that reframes the incumbent: FEM+6dB itself LEAKS 10–61% of held-out band "
      "energy. Nobody currently has a band that is both tight and covering.", 0),
    B("Status: EXPLORATORY/YELLOW (honest negative; NUTS R-hat 1.0016, ESS 1758, 0 div).", 0, GREY),
], image="reuse_bil_wide_ci.png", img_w=6.9,
   footer="src: shocksat_psd_envelope_twin_20260623/out/probe_seed00.json via bilionis_review packet §4 "
          "· value_eval_seed00.json (CHECKER-BACKED YELLOW)")

# ------------------------------------------------------------- 6 · the defect
slide("The defect: local mode-shape fidelity — right skeleton, wrong detail", [
    B("Same 54.2 Hz fundamental: MAC 0.97 on the NASA survey’s 76-node global grid, but 0.17 "
      "against shapes at the 84 dense accel channels — the error lives BETWEEN survey nodes.", 0, RED),
    B("Concentrates at interfaces: steel box below the bolted joint / bulkhead, impact-face near-field, "
      "and the dense 150–210 Hz mode cluster.", 0),
    B("|H| folds TWO local shape values (drive × sensor) ÷ damping → wrong local pattern = "
      "energy in the wrong place per point (~15.7 dB median peak error) despite ~3% frequencies.", 0),
    B("Proof shape is THE reducible lever: give the twin the measured shape at a held-out sensor and "
      "σ drops 1.26 → 0.70 (shape-oracle test).", 0, BLUE),
    B("Two independent routes later agreed: point-wise discrepancy ≈ 0.9 log-amp (5-drive scatter "
      "0.86; NUTS-learned σ_d 0.94, R-hat 1.001).", 0),
], image="reuse_bil_residual_map.png", img_w=7.3,
   footer="src: psd_envelope/out/residual_map.json + shape_diag.json · fem_remesh region_diagnosis.md · "
          "netcg out/data_anchored_sigma.json + learned_statfem.json")

# --------------------------------------------------------- 7 · remesh boundary
slide("Agentic remeshing: competently executed, decisively unfruitful", [
    B("Mesh already CONVERGED: dish 2× refinement (+74,592 DOF) moved global MAC +0.0016. "
      "Topology complete (bulkheads, CBUSH joint, struts all present).", 0),
    B("Stiffness family exhausted: 0 of 6,000 points in θ∈[0.6,1.4]⁹ improve hard-region "
      "shape without a frequency penalty — the FEM sits on a shape-vs-frequency Pareto wall "
      "(vendor correlation already spent that lever).", 0, RED),
    B("The “+0.08” remesh gain was an amplitude-fitting artifact: honest metric + actual NUTS "
      "→ best remesh scores 0.183–0.267, BELOW plain calibration 0.338 (figure).", 0, RED),
    B("QOI-level confirmation: blind mesh screen of 12 edits — the inherited mesh ties for best; "
      "remesh has no net-CG QOI leverage.", 0),
    B("The agentic deliverable: an auditable BOUNDARY — the agent proved mesh/stiffness are not "
      "the lever and redirected effort. Open (untested): richer local interface parameterization.", 0, BLUE),
], image="reuse_bil_combine_best.png", img_w=6.9,
   footer="src: fem_remesh Card D (CHECKER-BACKED GREEN 14/0/0) · bilionis out/combine_best.json · "
          "netcg out/mesh_screen_summary.json")

# ---------------------------------------------------------------- 8 · divider
divider("PART 2 · THE PIVOT", "Match the deliverable’s resolution to the data — and validate it")

# -------------------------------------------------------------- 9 · trust map
slide("Stage-0 QOI trust map — which numbers the twin can carry (no sampling)", [
    B("Shape-trust = share of each QOI carried by shape-MEASURED modes. Computable from the existing "
      "FEM + modal survey alone — before any Bayesian machinery runs.", 0),
    B("Net-CG SHEAR X/Y: 96%/94% — carried by measured global box modes (114–197 Hz). "
      "Deliverable.", 0, GREEN),
    B("Net-CG NORMAL Z: 45% — carried by UNMEASURED drumhead plate modes (234–258 Hz; one "
      "off-antinode Z-sensor on the plate). Data-starved.", 0, ORANGE),
    B("Point mount response: 13% — reproduces the known ~14.6× per-point wall. NOT deliverable.", 0, RED),
    B("The normal band is ASSUMPTION-dominated: unmeasured-mode amplitude σ 0.4→2.6×, "
      "0.8→5.7×, 1.6→34× (panel D) → next test dollar goes exactly there.", 0),
], image="reuse_netcg_stage0_qoi_trust.png", img_w=7.2,
   footer="src: netcg_method_selection out/stage0_qoi_weights.json + stage0_sensitivity.json (checker GREEN "
          "22/0/0) · packet §3")

# --------------------------------------------------------------- 10 · delivery
slide("The delivery: held-out-drive-validated net-CG force bands", [
    B("Winner (best of N=18, per QOI): statFEM F(k) — QOI-aware frequency-correlated OUTPUT "
      "discrepancy; tight where measured modes drive, wide where unmeasured modes drive.", 0, GREEN),
    B("SHEAR X 1.51× / SHEAR Y 2.30× FEM+6dB, coverage 0.99/0.98 — validated on REAL "
      "held-out drives: 5/5 (X), 4/5 (Y; one genuine +Z-end-drive gap, surfaced + diagnosed as "
      "drive-specific).", 0, GREEN),
    B("NORMAL Z 2.53× — honest COVERING band + trust label (number is data-starved until the "
      "plate test). Pooling could reach 2.00× but only via an unverifiable assumption → "
      "flagged, not delivered.", 0, ORANGE),
    B("L5 modal-frequency NUTS: R-hat 1.001, ESS 2646, 0 divergences.", 0),
    B("Value proposition vs incumbent: FEM+6dB leaks (cov 0.71–0.87); the twin COVERS, sharp where "
      "earned, and says where it isn’t.", 0, BLUE),
], image="reuse_netcg_delivery_bands.png", img_w=7.4,
   footer="src: netcg out/bakeoff_scorecard.json + heldout_drive.json + fig_delivery (checker GREEN 22/0/0, "
          "SHA-locked)")

# ---------------------------------------------------- 11 · method selection tbl
table_slide(
    "Method selection — coverage is the hard gate; overconfidence disqualifies",
    ["QOI", "FEM+6dB (incumbent)", "freq-only θ-posterior", "statFEM F(k)  ← WINNER", "held-out drives"],
    [
        ["shear_X", "1.0× · cov 0.86 LEAKS", "1.07× · OVERCONFIDENT", "1.51× · cov 0.99", "5/5 cov 1.00"],
        ["shear_Y", "1.0× · cov 0.71 LEAKS", "1.22× · OVERCONFIDENT", "2.30× · cov 0.98", "4/5 (one real gap)"],
        ["normal_Z", "1.0× · cov 0.74 LEAKS", "1.02× · OVERCONFIDENT", "2.53× · cov 0.99", "no answer key (unmeasured)"],
    ],
    [1.4, 2.85, 2.85, 2.85, 2.55],
    cell_colors=[
        [None, ORANGE, RED, GREEN, GREEN],
        [None, ORANGE, RED, GREEN, ORANGE],
        [None, ORANGE, RED, GREEN, GREY],
    ],
    bullets_below=[
        B("The catch that matters: leave-modes-out — hide the measured modes; the freq-only method’s band "
          "does NOT widen (ratio 1.00 exactly = structurally blind) → DISQUALIFIED. All 4 discrepancy "
          "methods widen 1.06–1.80 = humble. Robust across formulations (N=18).", 0, RED),
        B("This is the operational answer to “pencil-whipping”: the machinery demonstrably refuses to be "
          "confidently wrong — and the audit is one cheap re-run any workflow can adopt.", 0, BLUE),
    ],
    footer="src: netcg out/bakeoff_scorecard.json (leave-modes-out widen ratios) · packet §2 (checker "
           "GREEN 22/0/0)", fontsize=11)

# --------------------------------------------------------- 12 · precise honesty
slide("Precise honesty: what the shear band is — and is not", [
    B("Two INDEPENDENT routes agree the measured-mode amplitude discrepancy is ~0.9 log-amp (not the "
      "assumed 0.35): 5-drive cross-scatter 0.86; NUTS-learned statFEM σ_d 0.94 (R-hat 1.001).", 0),
    B("But the learned discrepancy is nearly POINT-WISE (correlation length 0.10 octaves) → it "
      "averages out under 1-octave smoothing — exactly why held-out-drive coverage passed.", 0, BLUE),
    B("Read the deliverable precisely: trustworthy at the 1-octave-smoothed level (validated); "
      "point-frequency amplitude uncertain ~0.9 — do NOT read the band as point-wise sharp.", 0, ORANGE),
    B("This quantifies the standing “per-point amplitude is the wall” via two new routes — "
      "the negative and the positive are the same physics, at two resolutions.", 0),
], image="reuse_netcg_learned_statfem.png", img_w=6.8,
   footer="src: netcg out/data_anchored_sigma.json + learned_statfem.json · packet §7b (DD2/DD3)")

# ---------------------------------------------------------------- 13 · divider
divider("PART 3 · CONTRIBUTIONS & NEXT STEPS", "Aerospace workflows · the literature · the next test dollar")

# ------------------------------------------------- 14 · aerospace contributions
table_slide(
    "Immediately translatable to aerospace workflows (no Bayesian buy-in required)",
    ["Tool", "What it gives a loads engineer", "Cost"],
    [
        ["Per-QOI trust map (Stage 0)", "Which numbers from the correlated FEM to believe (shear 94–96% vs normal 45% vs point 13%) — from FEM + survey only", "hand-calc, no sampling"],
        ["Envelope-leak audit", "FEM+6dB leaks 10–29% coverage on held-out drives — leave-one-drive-out QA on data every multi-drive survey already has", "a re-score"],
        ["Leave-modes-out audit", "One cheap re-run that catches a falsely-sharp band (widen ratio 1.00 = blind)", "a re-run"],
        ["Rehearsed pre-test design", ">200 Hz plate test: the analytic 3.5× promise FAILED a full-pipeline rehearsal (12 sensors → 6.2×); revised scope = all 12 band modes (oracle 2.8×) — rehearse before you buy hardware", "rehearsal done 07-02"],
        ["Delivery convention", "1-octave-smoothed bands + tolerated narrow exceedances + per-QOI trust labels — matches how loads spectra are actually compared", "a template"],
    ],
    [3.1, 7.4, 2.2],
    bullets_below=[
        B("Each is auditable and works inside the existing test-correlation process — the vision’s "
          "“tool an engineer runs on Monday” bar (§2.1).", 0, BLUE),
    ],
    footer="src: netcg stage0_qoi_weights/heldout_drive/pretest_design.json · notes/project_vision.md §2.1",
    fontsize=10.5)

# ------------------------------------------------ 15 · literature contributions
slide("Contributions to the StatFEM / Bayesian FEM-updating literature", [
    B("#1 THE BOUNDARY (lead paper): on a real, vendor-correlated aerospace FEM, StatFEM is trustworthy "
      "but not sharp at the per-point FRF level; cause isolated (local shape, ~0.9 log-amp, two routes); "
      "no statistical lever or agentic remeshing closes it. A negative with teeth.", 0),
    B("#2 THE CONSTRUCTIVE COUNTERPART (new): at the integrated-QOI, octave-smoothed resolution, a "
      "QOI-aware statFEM output discrepancy gives held-out-validated near-usable bands — “match "
      "deliverable resolution to the data” as a design principle, with a per-QOI selection protocol.", 0, GREEN),
    B("#3 WELL-POSEDNESS MECHANISM: the observable + a BOUNDED learned model-error regularizer decide "
      "convergence — not “where the physics lives.” Whole-FRF |H| is multimodal for everyone "
      "(IFT too); modal features converge; bounded β / informative σ_d prior cures the rest.", 0),
    B("#4 CONSISTENCY ANSWER (Bilionis/Alberts/Kairui): a learned model-error knob removes the arbitrary "
      "residual-noise/evaluation-count drift (figure) — honest shared limit: discrepancy ABSORBS "
      "model error, none recovers true θ.", 0),
    B("Cross-cutting (autonomous science): convergence ≠ trust — only held-out gates caught the "
      "failures; cheap probes misled both ways.", 0, BLUE),
], image="reuse_bil_consistency_money.png", img_w=6.3,
   footer="src: bilionis_review publishable_findings.md · statfem_consistency_toy sweep_summary.json + "
          "ift_real_validation scorecard.json (CHECKER-BACKED YELLOW)")

# ------------------------------------------------------- 16 · ShockSat position
slide("Where ShockSat sits among the literature’s physical test cases", [
    B("Bayesian-updating literature (Kiran 2025 review): mostly civil/SHM cases — IASC-ASCE "
      "benchmark, shear buildings, RC beams; StatFEM’s flagship real case is the self-sensing "
      "bridge (benign, near-static regime).", 0),
    B("ShockSat is a step up on every axis that matters:", 0),
    B("INHERITED model — a 406k-DOF vendor FEM we didn’t build, already industry-correlated "
      "(the actual industrial use case, nearly absent from the literature)", 1),
    B("real multi-drive hammer data with real defects (bad channels, unmeasured modes, drive scatter)", 1),
    B("the failure regime the review names but its examples avoid (model-form error, partial "
      "identifiability)", 1),
    B("a certification-grade endpoint: net-CG force per NASA-HDBK-7004C — pushed to the decision, "
      "not just “parameters recovered”", 1),
    B("Honest placement: the most industrially realistic dynamic StatFEM case yet — but one "
      "structure, one build, ground data, 45–260 Hz. Lab-data, not operational.", 0, ORANGE),
    B("Positioning gap: the Kiran review under-covers explicit discrepancy/StatFEM — our "
      "discrepancy-structure + load-QOI + test-design combination sits in it. (Citation pass needed "
      "before this goes in writing.)", 0, BLUE),
], footer="src: notes/review_kiran2025_reading_notes.md §J + connections · netcg quantity_contracts.md "
          "(7004C) · lit positioning beyond Kiran notes = to be verified")

# ------------------------------------------------------- 17 · next test dollar
slide("The next test dollar — REVISED 07-02: the rehearsal falsified the 3.5× promise", [
    B("The analytic design curve (netcg §9) promised 12 plate accels buy the normal band "
      "5.4×→3.5×. A pre-registered, SHA-locked-checker REHEARSAL ran the designed test through "
      "the full NUTS pipeline on synthetic truth: 12 sensors → 6.2×, 20 sensors → 6.2×. "
      "NO buy-down (checker RED = the claim-falsified tier; coverage stayed 0.998).", 0, RED),
    B("Why the curve was wrong: it FROZE θ at MAP. The real ±4% θ posterior rotates the "
      "near-degenerate 246–258 Hz drumhead eigenvectors and re-scatters every band mode’s net-Z "
      "participation (ablation: 3.05×→4.93× from θ alone).", 0),
    B("REVISED scope: resolve ALL ~12 drumhead-band modes (228–260 Hz), not the 4 net-drivers — "
      "oracle bound 2.81×. Harder identification job; 12-mode follow-up rehearsal APPROVED "
      "before any hardware ask. Do not quote 3.5× (or 2.8×) to a partner yet.", 0, GREEN),
    B("What the as-designed test still buys: target amplitude posterior sd 0.80→0.58 (mean "
      "within 0.08 of truth) → the pooling assumption becomes checkable.", 0),
    B("Meta-lesson for the workflow: analytic pre-test curves computed OUTSIDE the twin’s own "
      "uncertainty carriage overpromise — rehearse the test before you buy it.", 0, BLUE),
], image="reuse_rehearsal_buydown.png", img_w=7.0,
   footer="src: plate_test_rehearsal_20260701 (checker RED 28G/3Y/1R = pre-registered falsification; "
          "35/36 NUTS converged) SUPERSEDES netcg pretest_design.json §9 (erratum appended there)")

# --------------------------------------------------------- 18 · next steps/asks
table_slide(
    "Next steps — proposed priorities (decisions to make together)",
    ["#", "Action", "Feeds", "Cost / risk"],
    [
        ["1", "Write-up #1: the boundary paper (trustworthy-but-not-sharp + remesh boundary + the wall quantified)", "literature", "low — data in hand; promote EXPLORATORY → checker-backed first"],
        ["2", "Write-up #2: method paper (observable + bounded regularizer + consistency answer + net-CG delivery)", "literature", "low-med — needs the 2×2 ablation (M2 + informative σ_d prior vs IFT)"],
        ["3", "REVISED: 12-mode follow-up rehearsal (approved 07-02) — re-optimize sensors/drives to resolve the whole 228-260 Hz cluster; only then propose hardware", "aerospace + normal QOI", "compute only; the 3.5x claim is falsified — no hardware ask until rehearsed"],
        ["4", "Package the Monday tools (trust map, envelope-leak audit, leave-modes-out audit) as a template", "aerospace adoption", "low — consolidation"],
        ["5", "NOT recommended: more remeshing / whole-FRF sharpening / from-scratch geometry rebuild", "—", "boundary proven; gamble"],
    ],
    [0.5, 6.2, 2.4, 3.6],
    cell_colors=[
        [None, None, None, None],
        [None, None, None, None],
        [None, GREEN, None, None],
        [None, None, None, None],
        [None, RED, None, None],
    ],
    footer="src: bilionis_review packet §13 (options A–C) + publishable_findings.md · netcg packet "
           "§9 · priorities = proposal, not yet decided", fontsize=10.5)

# ------------------------------------------------------ 19 · status & provenance
slide("Status, provenance, and honest limits", [
    B("CHECKER-BACKED (SHA-locked graders): net-CG method selection (GREEN 22/0/0 — certifies "
      "integrity + convergence + honest flagging, NOT the normal number); FEM-remesh Card D (GREEN); "
      "IFT real-validation, consistency toy, model-class L5 (YELLOW = honest negatives).", 0, GREEN),
    B("EXPLORATORY (no immutable checker yet): FRF-correlation, remesh-sweep, wide-CI work — "
      "promote before publication.", 0, ORANGE),
    B("Caveats that ride with every headline: normal-Z NUMBER uncertified (data-starved); shear_Y "
      "carries one caught held-out-drive gap; bands trustworthy SMOOTHED, not point-wise; bake-off is "
      "best-of-N with documented deferrals; one structure, one build, 45–260 Hz.", 0, ORANGE),
    B("Every figure in this deck is a labeled COPY from its source workspace (run_all.sh); no figure "
      "was made for this deck. Replay: bash run_all.sh.", 0),
    B("Nothing on these slides is stronger than the cited files — read the footers.", 0, BLUE),
], footer="workspace: artifacts/reports/project_status_deck_20260701/ · sources: shocksat_netcg_method_"
          "selection_20260701 · shocksat_bilionis_review_20260626 (+ their cited upstream workspaces)")

OUT.parent.mkdir(exist_ok=True)
prs.save(str(OUT))
print(f"saved {OUT} ({len(prs.slides._sldIdLst)} slides)")
