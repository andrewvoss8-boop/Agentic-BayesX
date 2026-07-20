#!/usr/bin/env python3
"""ONE thorough results deck: the three headline studies (net-CG method selection GREEN 22/0/0; plate-test
rehearsal RED-by-falsification 28G/3Y/1R; composite bake-off YELLOW 57G/6Y/0R) + the harness that makes them
trustworthy. CONSOLIDATION ONLY — no new science; all figures are provenance-labeled COPIES (reuse_*); every
number traces to a workspace checker/packet and is never stated stronger than the checker."""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"
DARK = RGBColor(0x1F, 0x4E, 0x79); GREY = RGBColor(0x60, 0x60, 0x60)
RED = RGBColor(0xB0, 0x30, 0x30); GREEN = RGBColor(0x2B, 0x7A, 0x2B); AMBER = RGBColor(0xA8, 0x74, 0x00)

prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
N = [0]


def slide(title, color=DARK, tsize=24):
    s = prs.slides.add_slide(BLANK); N[0] += 1
    tb = s.shapes.add_textbox(Inches(0.35), Inches(0.15), Inches(12.65), Inches(0.75)).text_frame
    tb.word_wrap = True
    p = tb.paragraphs[0]; p.text = title; p.font.size = Pt(tsize); p.font.bold = True; p.font.color.rgb = color
    return s


def bullets(s, items, x=0.45, y=1.05, w=12.4, h=5.8, size=14):
    tf = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        lvl = 0; txt = it
        if isinstance(it, tuple):
            lvl, txt = it
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = ("• " if lvl == 0 else "   – ") + txt
        p.font.size = Pt(size if lvl == 0 else size - 1.5)
        p.space_after = Pt(5)
    return tf


def pic(s, name, x, y, w=None, h=None):
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    return s.shapes.add_picture(str(FIG / name), Inches(x), Inches(y), **kw)


def footer(s, text):
    tf = s.shapes.add_textbox(Inches(0.35), Inches(7.02), Inches(12.65), Inches(0.42)).text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]; p.text = f"[{N[0]}] " + text; p.font.size = Pt(8); p.font.color.rgb = GREY


# ============================ PART 0 — FRAME ============================
s = slide("A held-out-validated Bayesian digital twin of a real NASA structure:\nthree studies and the harness that keeps them honest", tsize=28)
bullets(s, [
 "ShockSat: the most complex structure attempted for Bayesian FEM updating relative to the FEM-updating literature — a real, NASA-correlated ~406k-DOF satellite mock-up FEM + a real multi-reference modal test campaign.",
 "Three headline studies (each with a pre-registered, SHA-locked checker; every number below traces to a checker output):",
 (1, "STUDY 1 — net-CG force method selection (checker GREEN 22/0/0): coverage-first selection picks a statFEM-style frequency-correlated output discrepancy; the industry FEM+6dB incumbent UNDER-covers."),
 (1, "STUDY 2 — plate-test rehearsal (checker RED by PRE-REGISTERED FALSIFICATION, 28G/3Y/1R): the promised 5.4x->3.5x test buy-down is falsified; the mechanism and a revised test scope recovered."),
 (1, "STUDY 3 — composite bake-off (checker YELLOW 57G/6Y/0R): agentic remodeling + shape-in-likelihood + Beck shape field each tested against the proven baseline on held-out data; evidence != held-out."),
 "Andrew Voss with Claude (lead agent), 2026-07-02. Audience: Bayesian/UQ methods (Bilionis) + structural dynamics.",
], size=15)
footer(s, "Sources: artifacts/reports/{shocksat_netcg_method_selection_20260701, plate_test_rehearsal_20260701, shocksat_composite_bakeoff_20260702}; statuses copied from each checker_report.json.")

s = slide("The structure and the data")
bullets(s, [
 "Inherited FEM: NASA-correlated 9-group shell/bush model (~406k DOF; reduced 74-80 mode basis for updating). Global matched MAC 0.63; low modes excellent (54.2 Hz: MAC 0.97, df +0.75%).",
 "Data: 33-mode .ash EMA survey (76 nodes x 3 axes — the shape truth source) + FIVE hammer-drive FRF cache sets (+X, +Z/990, +XY, +Z/900, +Y; hit-averaged H1, 45-260 Hz band).",
 "Principle (Andrew): LIMITED DATA, NEVER LIMITED MODES — all in-band modes, all 5 drives, no pruning to flatter a method.",
], x=0.45, y=0.95, w=6.6, size=13.5)
pic(s, "reuse_L5_param_locations.png", 7.4, 0.95, h=5.9)
footer(s, "Image: FEM node cloud colored by the 9 stiffness-calibration groups [copy: shocksat_modelclass_L5_20260619/figures/fig_param_locations.png].")

s = slide("The wall this program keeps hitting: per-point FRF amplitude")
pic(s, "reuse_psdenv_frf_grid.png", 0.6, 0.95, w=9.6)
bullets(s, [
 "Measured vs FEM |H|, 12 channels.",
 "Updating aligns PEAKS (frequency value is real: FEM freq error ~halved).",
 "Per-channel log|H| correlation: 0.27 blind -> 0.44 held-out-sensor CV -> 0.70 shape-ORACLE ceiling; usable ~0.7 is never reached by theta-updating or remeshing.",
 "The residual is SHAPE error — the direction the stiffness parameters cannot move.",
 "Consequence: deliver QOI-level (net force) bands, not per-point FRFs.",
], x=10.3, y=1.0, w=2.7, size=11)
footer(s, "Copy: shocksat_psd_envelope_twin_20260623/figures/frf_comparison_grid.png; ladder numbers: psd_envelope packet + bilionis_review. Median corr 0.269->0.338 (70% of channels improve).")

# ============================ PART 1 — HARNESS ============================
s = slide("The validation harness (what makes a result a result)")
bullets(s, [
 "PRE-REGISTRATION: question, arms, thresholds, and baseline bars written BEFORE science; the checker (check.py) is SHA-locked first and never edited during the trial; falsification is an accepted outcome, labeled 'claim falsified' (honest) vs 'pipeline failure'.",
 "THREE-TIER STATUS: GREEN met / YELLOW documented honest miss (never called success) / RED blocking. Checker exit non-zero only on RED.",
 "COVERAGE-FIRST SELECTION (two-part rule): (1) the 95% band must COVER held-out data (energy-weighted, 1-octave smoothed; narrow exceedances tolerated) — overconfidence disqualifies; (2) among covering methods, the SHARPEST wins.",
 "THREE HELD-OUT GATES: (a) truth-ensemble/answer-key coverage; (b) leave-one-DRIVE-out — 5 folds, the held-out drive's net-CG force reconstructed from ITS OWN measured FRFs (arm-independent answer key); (c) LEAVE-MODES-OUT audit — hide the top QOI-driving measured modes: an honest band MUST widen (widen ratio > 1); a method that stays sharp is structurally overconfident and is disqualified regardless of sharpness.",
 "CONVERGENCE GATE: NUTS, 4 chains, float64; ALL-variable R-hat <= 1.05, ESS >= 200, divergences < 2% — 'converged' is never claimed otherwise.",
], size=13.5)
footer(s, "AGENTS.md Engineering Harness Gates; per-study checkers. This slide is the transferable method (candidate ipynb module).")

s = slide("Two metric traps this harness encodes (both burned us before)")
bullets(s, [
 "TRAP 1 — per-mode amplitude/phase fitting inside a score: LSQ-fitting ~40-60 per-mode complex amplitudes to the measured FRFs once produced a fake '+0.083' improvement. RULE: no per-mode amplitude fitting in ANY selection score; one global gain per fold only. (LSQ is allowed in exactly one place: reconstructing the held-out drive's answer key from its own data — identical for every arm.)",
 "TRAP 2 — re-pairing churn: greedy per-mode MAC matching lets each candidate model pick its most flattering mode pairing (a fake '+0.010'). RULE: one-to-one Hungarian assignment on the full MAC matrix, computed once per model and FROZEN through scoring.",
 "Both are declared fields in the scorecard that the locked checker verifies.",
], size=14)
footer(s, "Trap history: shocksat_fem_remesh_20260618/correlation_contribution.md; encoded in shocksat_composite_bakeoff_20260702/check.py.")

# ============================ PART 2 — NETCG ============================
s = slide("STUDY 1 — Which formulation delivers the net-CG force twin?  (checker GREEN 22/0/0)", color=GREEN)
bullets(s, [
 "QOI: net-CG interface FORCE on the top tray (NASA-HDBK-7004C convention) — in-plane SHEAR X/Y and out-of-plane NORMAL Z, reported separately. Flat known input at each drive.",
 "Why this QOI: per-point FRF is walled (slide 3); net force is what a payload integrator actually needs.",
 "Trust is wildly QOI-dependent (right): shear rides the MEASURED global box modes (~114-197 Hz, shape-trust 94-96%); normal rides UNMEASURED drumhead plate modes (~234-258 Hz, trust 45%).",
 "Bake-off: N=18 configurations, 5 uncertainty formulations on the same converged L5 NUTS posterior (R-hat 1.001, ESS 2646, 0 div).",
], x=0.45, y=0.95, w=6.3, size=13)
pic(s, "reuse_netcg_trust.png", 6.95, 1.0, w=6.1)
footer(s, "shocksat_netcg_method_selection_20260701: out/stage0_trust.json, bakeoff_scorecard.json; fig_stage0_qoi_trust.png (copy).")

s = slide("STUDY 1 result — winner: statFEM F(k) (QOI-aware, frequency-correlated output discrepancy)", color=GREEN)
pic(s, "reuse_netcg_delivery.png", 0.5, 0.95, w=8.6)
bullets(s, [
 "Delivered 95% bands vs FEM+6dB incumbent:",
 (1, "shear_X 1.51x — validated"),
 (1, "shear_Y 2.30x — validated"),
 (1, "normal_Z 2.53x — covering band; the NUMBER is data-starved (drumhead modes unmeasured)"),
 "F(k): multiplicative log-amp field, 1-octave correlated, wide exactly where unmeasured modes drive the response.",
 "Selection: coverage hard gate + humility, THEN sharpest (best of N=18, stated).",
], x=9.3, y=1.0, w=3.7, size=11.5)
footer(s, "fig_delivery_netcg_bands.png (copy); numbers: bakeoff_scorecard.json (statfem_Fk row).")

s = slide("STUDY 1 — the two incumbent-killers", color=GREEN)
bullets(s, [
 "THE FALSE SHARPENER, CAUGHT: theta-only (frequency-posterior only, no discrepancy) looks great — sharp bands, high coverage on measured-driven QOIs. The leave-modes-out audit exposes it: hide the top measured modes and its band widens by EXACTLY 1.00 (uncertainty invariant to information = structural overconfidence). DISQUALIFIED despite being the sharpest. This is the audit doing its job.",
 "THE INDUSTRY INCUMBENT UNDER-COVERS: FEM+6dB envelope weighted coverage 0.87 (shear_X) / 0.71 (shear_Y) / 0.74 (normal_Z) vs the 0.90 gate — i.e., the standard practice band is both arbitrary and, here, NOT conservative enough where it matters.",
 "HELD-OUT-DRIVE validation (real data answer keys): winner covers shear_X 5/5 drives (1.00); shear_Y 4/5 — the one gap (+Z@900, 0.60) was diagnosed as a drive-specific 73 Hz outlier artifact, not systematic FEM error.",
 "Learned-discrepancy cross-check: inferring the output discrepancy with NUTS (R-hat 1.001) gives sigma_d ~ 0.94 log-amp, correlation length 0.10 octave — two independent routes agree the point-wise discrepancy is ~0.9 but nearly point-wise, so it AVERAGES OUT under 1-octave smoothing: the band is trustworthy at the 1-oct level, NOT point-wise sharp.",
], size=13)
footer(s, "leave_modes_out.json (widen ratios), bakeoff_scorecard.json (fem+6dB rows), heldout_drive.json, learned_statfem.json + DD1/DD3 diagnostics.")

s = slide("STUDY 1 — learned vs assumed discrepancy (honest width audit)", color=GREEN)
pic(s, "reuse_netcg_learned.png", 0.6, 1.0, w=9.2)
bullets(s, [
 "Learned sigma_d 0.94 >> assumed 0.25 marginal...",
 "...but ell = 0.10 octave (point-wise) -> 1-oct band survives.",
 "Quantifies 'per-node amplitude = the wall' via an independent route.",
], x=10.0, y=1.1, w=3.0, size=11.5)
footer(s, "fig_learned_statfem.png (copy); learned_statfem.json (NUTS R-hat 1.001, ESS 2083, 0 div).")

s = slide("STUDY 1 — the next test dollar: a >200 Hz plate/drumhead test (pre-test design)", color=GREEN)
pic(s, "reuse_netcg_pretest.png", 0.5, 0.95, w=8.6)
bullets(s, [
 "Normal-band width is set almost entirely by the assumed unmeasured-mode amplitude sigma (0.4->2.6x, 0.8->5.7x, 1.6->34x).",
 "Analytic design: 12 well-placed plate accels + drive +Y promised 5.4x -> 3.5x (~35% of the band, 73% of the way to the 2.8x floor).",
 "This promise is what STUDY 2 rehearses — before asking for hardware.",
], x=9.3, y=1.0, w=3.7, size=11.5)
footer(s, "fig_pretest.png (copy); pretest_design.json; sensitivity: stage0_sensitivity.json.")

# ============================ PART 3 — REHEARSAL ============================
s = slide("STUDY 2 — Rehearse the test BEFORE the hardware ask  (checker RED = pre-registered falsification; pipeline GREEN)", color=RED)
bullets(s, [
 "Question: if we ran the proposed 12-sensor >200 Hz plate test, would the normal-Z band really drop 5.4x -> 3.5x?",
 "Method: full synthetic end-to-end rehearsal ON the real ShockSat FEM — simulate the test data from an epistemic truth, run the ACTUAL inference pipeline (36 NUTS runs; 35/36 converged), score the ACTUAL delivered band. Criteria S1-S6 pre-registered; checker SHA-locked before science.",
 "RESULT: FALSIFIED. Rehearsed medians: 6.17x (1 sensor) / 6.20x (12 sensors) / 6.20x (20 sensors) — NO buy-down at all, vs the promised 3.5x.",
 "Checker OVERALL RED (28G/3Y/1R) where the single RED is the claim-falsified tier — the honest-outcome design working exactly as intended: the pipeline is intact (coverage 0.998 GREEN, integrity GREEN), the CLAIM died.",
], size=13.5)
footer(s, "plate_test_rehearsal_20260701: packet.md, checker_report.json; replay bash run_all.sh.")

s = slide("STUDY 2 — why the analytic design curve lied: theta rotates the degenerate cluster", color=RED)
pic(s, "reuse_reh_buydown.png", 0.5, 0.95, w=8.4)
bullets(s, [
 "The analytic curve FROZE theta at its MAP.",
 "The real +/-4% theta posterior ROTATES the near-degenerate 246-258 Hz drumhead eigenvectors -> every band mode's net-Z participation scatters.",
 "Ablation: analytic floor 3.05x -> 4.93x from theta alone; signed-mixture heavy tails -> ~5.5x; even a PERFECT 4-target test stays ~5.1x.",
 "Lesson: rehearse test designs against the POSTERIOR, not a point estimate — especially near modal degeneracy.",
], x=9.1, y=1.0, w=3.9, size=11.5)
footer(s, "fig_buydown_rehearsed.png (copy); ablation L0-L7 in packet §mechanism (post-hoc, labeled).")

s = slide("STUDY 2 — constructive recovery: the revised test scope", color=AMBER)
pic(s, "reuse_reh_amp.png", 0.5, 0.95, w=8.4)
bullets(s, [
 "Pin ALL 12 drumhead-band modes (whole 228-260 Hz cluster, not just the 4 net-drivers) -> 2.81x oracle bound.",
 "The as-designed test STILL buys real things: target amplitude posterior sd 0.80 -> 0.58, mean within 0.08 of truth = the netcg pooling assumption becomes CHECKABLE.",
 "Robustness: truth-sd 1.6 -> band ~104x but coverage 1.0 — the pipeline degrades by WIDENING, never by lying.",
 "Status: revised scope accepted (Andrew); 12-mode-inference follow-up rehearsal required BEFORE any hardware ask; do NOT promise 2.8x yet.",
], x=9.1, y=1.0, w=3.9, size=11.5)
footer(s, "fig_amp_recovery.png (copy); netcg packet §9 carries a dated erratum for the 3.5x claim (append-only).")

# ============================ PART 4 — COMPOSITE ============================
s = slide("STUDY 3 — the composite bake-off: can ANY of three levers beat the proven baseline on held-out data?  (checker YELLOW 57G/6Y/0R)", color=AMBER)
bullets(s, [
 "Pre-registered 2x3 matrix, statFEM F(k) always on: MODEL {M0 inherited FEM, M1 best agent remodel} x SHAPE-USE {S0 freq-only (proven baseline), S1 freq+MAC in the likelihood, S2 Beck inferred shape FIELD}.",
 "All six arms calibrated on the SAME observations (.ash survey modes, frozen Hungarian pairing) so the axes are unconfounded; the 5 tap-test drives are then genuinely held out for every arm.",
 "All 6 NUTS arms converged (R-hat <= 1.0011, ESS >= 580, 0 divergences).",
 "Scored on: R1 per-point held-out-sensor amplitude (CRPS-skill), R2 net-CG bands (coverage HARD gate + leave-one-drive-out), R3 leave-modes-out audit, R4 evidence sanity (an M1 winner must beat M0 on evidence AND held-out).",
 "Agentic remodeling funnel: 151 diagnosis-seeded + random model-form candidates -> subspace screen -> 29 full 399k-DOF eigensolves -> 10 evidence classes -> 1 winner.",
], size=13.5)
footer(s, "shocksat_composite_bakeoff_20260702: question_framing.md (pre-registered), matrix_scorecard.json; replay bash run_all.sh.")

s = slide("STUDY 3 — the agentic remodeling funnel", color=AMBER)
pic(s, "reuse_comp_funnel.png", 0.5, 1.0, w=9.4)
bullets(s, [
 "Families: joint compliance, connectivity (new DOFs), weld/contact, per-region stiffness, mass distribution + a random tranche. NO geometry rebuild (prior Card-D boundary).",
 "Tier-1 subspace proxy validated: exact at the nominal model (score matches full solve to 4 decimals).",
 "Diversity hedge: every family carried to full eigensolves.",
], x=10.1, y=1.1, w=2.9, size=11)
footer(s, "fig_funnel.png (copy); candidates.json (151), tier1_screen.json, tier2_full.json (29).")

s = slide("STUDY 3 — headline: EVIDENCE IS NOT HELD-OUT VALIDATION", color=RED)
pic(s, "reuse_comp_evidence.png", 0.5, 1.0, w=7.9)
bullets(s, [
 "The evidence winner (`rand10`) beat the inherited FEM DECISIVELY on shape-inclusive (freq+MAC) evidence: +54 logZ, P(M|data)=0.72, top rank robust across prior widths.",
 "Then it failed to improve held-out prediction AT ALL (R1 skill -0.75 vs -0.78; bands no sharper).",
 "With this much model-form error, evidence — even Occam-penalized, even shape-inclusive — rewards absorbing calibration residuals into the wrong structure.",
 "Pre-registered R4 rule: evidence-only wins are REPORTED, NOT DELIVERED. It fired.",
 "(Aside: freq-only evidence would have crowned the SAME candidate — the MAC block did not re-rank here.)",
], x=8.6, y=1.0, w=4.4, size=11.5)
footer(s, "fig_evidence.png (copy); tier3_evidence.json (prior sweep 0.15/0.25/0.40; freq-only column labeled reference-only).")

s = slide("STUDY 3 — the full matrix (money figure)", color=AMBER)
pic(s, "reuse_comp_money.png", 0.4, 1.0, w=12.5)
footer(s, "fig_matrix_money.png (copy); matrix_scorecard.json. Panel A: R2 sharpness vs proven bars (x = fails gate). Panel B: R1 per-point CRPS-skill. Panel C: R3 widen ratios (must exceed 1).")

s = slide("STUDY 3 — the Beck shape field: per-point champion, unsafe for the derived QOI", color=AMBER)
pic(s, "reuse_comp_drives.png", 0.5, 1.0, w=8.2)
bullets(s, [
 "PER-POINT (R1): Beck halves the CRPS-skill deficit (-0.78 -> -0.34; sigma 1.08 -> 0.89) — the one lever that moves the SHAPE direction, confirmed on a stricter non-leaky convention.",
 "NET-CG BAND (R2): Beck's confident corrected shapes UNDER-cover (shear 0.55-0.70, normal 0.23-0.32 vs 0.95 gate) -> cannot win any QOI.",
 "Nuance (anti-circularity check): on the arm-independent held-out-DRIVE key, Beck covers shear_X 1.00 — the shear 'miss' is partly an artifact of a truth ensemble built from the FEM shapes Beck corrects. But normal_Z has NO data answer key -> Beck's confidence there is unvalidatable. Verdict: use Beck where sensors can validate it; never for the unmeasured-driven QOI.",
 "MAC-in-likelihood (S1): ~NULL again (third time, now multi-reference at QOI level).",
], x=8.9, y=1.0, w=4.1, size=11)
footer(s, "fig_heldout_drives.png (copy); matrix_scorecard.json R1/R2 blocks; historical Beck bar: modelclass_L5 shapefield_lever.json (-0.68->-0.25).")

s = slide("STUDY 3 — delivered twin + integrity notes", color=AMBER)
bullets(s, [
 "DELIVERED (best of N=6, pre-registered gate): inherited FEM + freq(+MAC) likelihood + statFEM F(k), for BOTH shear and normal — the composite additions did not improve the delivered bands; STUDY 1's twin is REAFFIRMED.",
 "Transparently flagged, not hidden:",
 (1, "M0S0's R3 'disqualification' is a marginal threshold artifact (normal widen 1.01 vs 1.03 threshold while STILL covering 0.993 after hiding) -> the delivered 'M0S1 over M0S0' is not a real MAC win; honestly the twin is 'inherited FEM + F(k), MAC optional'."),
 (1, "Sampler incident: the freq+MAC arm hung ~2 h on the 246-258 Hz degenerate-cluster eigenVECTOR gradient (a pre-flagged risk). Fixed with a documented Tikhonov-regularized first-order shape derivative (25 s, R-hat 1.0008) — a stability fix, not a result change."),
 (1, "Recovered from one computer crash mid-eigensolves (11/29 packages preserved; everything resumable)."),
 "So: did agentic remodeling earn a place in the workflow? NOT as a model-improver on this QOI/data. Where agents DID contribute: the diagnosis, the 151-candidate funnel mechanics, the harness itself, and the honest verdict.",
], size=13)
footer(s, "matrix_scorecard.json delivered block; decisions_log.md D11 (S1 fix), D10 (compute); checker_report.json YELLOW 57/6/0.")

# ============================ PART 5 — SYNTHESIS ============================
s = slide("Cross-cutting findings (the report's results)")
bullets(s, [
 "1. WIDE-BUT-HONEST BEATS SHARP-BUT-WRONG, and it is testable: coverage hard gate + leave-modes-out audit caught the false sharpener (theta-only, widen=1.00) and the overconfident shape field (Beck at QOI level); the FEM+6dB incumbent under-covers.",
 "2. EVIDENCE != HELD-OUT: a +54-logZ, P=0.72, prior-robust evidence winner added zero held-out skill. Model-class selection must be gated by held-out prediction under real model-form error.",
 "3. THE SHAPE WALL IS REAL AND DIRECTIONAL: theta-updating, remeshing (plateau ~0.38), richer parameterizations, MAC-in-likelihood — none crack per-point amplitude (0.27/0.44 vs oracle 0.70). The one lever that moves it (Beck shape field) is exactly the one whose confidence must be quarantined from unvalidatable QOIs.",
 "4. POINT ESTIMATES OVERPROMISE NEAR DEGENERACY: the analytic test design (frozen theta) promised 3.5x; the posterior rehearsal delivered 6.2x — theta rotates near-degenerate eigenvectors. Rehearse designs against the posterior.",
 "5. DISCREPANCY IS LARGE BUT POINT-WISE (sigma_d~0.9, ell~0.1 oct) -> QOI bands survive at 1-octave smoothing; per-point FRFs do not. Deliver at the resolution the physics supports.",
], size=13.5)
footer(s, "Each finding traces to a checker-backed workspace; see docs/report/experiment_catalog.xlsx for the full 63-experiment index.")

s = slide("Positioning + next steps")
bullets(s, [
 "LITERATURE: real, NASA-correlated structure + multi-reference test campaign — vs the simulated beams/frames dominating the FEM-updating literature; the contribution is the validation harness + the NEGATIVES nobody publishes (evidence!=held-out, remodeling null, MAC null, shape-field sharp-but-unsafe), each with mechanism.",
 "PAPER: draft in progress targeting a data-centric engineering venue (harness + case study + negative results).",
 "REUSABLE MODULE: the selection harness (coverage gate + leave-modes-out audit + held-out folds) as a simple ipynb — the piece a practicing engineer can lift.",
 "NEXT TEST DOLLAR (unchanged and now rehearsal-calibrated): >200 Hz drumhead/plate modal test with the REVISED scope (identify the whole 228-260 Hz cluster); requires the 12-mode follow-up rehearsal before promising numbers (~2.8x floor, NOT 3.5x).",
 "OPEN ASKS: Andrew review of the composite packet; publishability ratings in the experiment catalog; Dr. Gibert interest.",
], size=14)
footer(s, "Catalog: docs/report/experiment_catalog.xlsx (63 runs, 13 decks). Everything replays: bash run_all.sh per workspace.")

s = slide("Backup — provenance and replay map", tsize=20)
bullets(s, [
 "STUDY 1: artifacts/reports/shocksat_netcg_method_selection_20260701 — checker GREEN 22/0/0; L5 NUTS R-hat 1.001/ESS 2646/0 div; decisions D1-D18.",
 "STUDY 2: artifacts/reports/plate_test_rehearsal_20260701 — checker RED 28G/3Y/1R (RED = pre-registered claim-falsified tier); 35/36 NUTS converged; decisions D1-D9.",
 "STUDY 3: artifacts/reports/shocksat_composite_bakeoff_20260702 — checker YELLOW 57G/6Y/0R; 6/6 arms converged; decisions D1-D11; REUSED_code.sha256 pins 13 read-only sources.",
 "Foundations: shocksat_fem_modal_twin_20260609 (406k-DOF assembly), statfem_real_validation_20260617 (identifiability + fail-7 channels), shocksat_modelclass_L5_20260619 (value split + Beck lever + evidence machinery), shocksat_fem_remesh_20260618 (diagnosis + metric traps), shocksat_psd_envelope_twin_20260623 (the 0.27/0.44/0.70 ladder).",
 "All numbers in this deck were copied from checker outputs / packets; none are stated stronger than the checker. Figures are provenance-labeled copies (reuse_*).",
], size=13)
footer(s, "Deck: artifacts/reports/results_deck_20260702; rebuild: python3 code/make_deck.py.")

out = WS / "slides" / "shocksat_three_studies_20260702.pptx"
prs.save(out)
print(f"wrote {out} ({N[0]} slides)")
