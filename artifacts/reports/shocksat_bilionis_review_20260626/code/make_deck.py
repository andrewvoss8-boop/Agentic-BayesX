#!/usr/bin/env python3
"""
Assemble the Bilionis review PowerPoint for Agentic BayesX / ShockSat.

Consolidation deck: every number traces to a saved out/*.json in an existing
workspace (see footers). No new science. Figures live in ../figures (new
fig_*.png from make_review_figs.py; reuse_*.png copied from prior threads).

Run:  python3 make_deck.py   ->  ../slides/shocksat_bilionis_review.pptx
"""
from __future__ import annotations
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"
NAVY = RGBColor(0x1f, 0x33, 0x5e); GREY = RGBColor(0x5a, 0x5a, 0x5a)
RED = RGBColor(0xb2, 0x18, 0x2b); GREEN = RGBColor(0x1b, 0x78, 0x37)
ORANGE = RGBColor(0xb5, 0x5e, 0x0c); BLUE = RGBColor(0x3a, 0x66, 0xb0)
WHITE = RGBColor(0xff, 0xff, 0xff); LIGHT = RGBColor(0xef, 0xf1, 0xf5)

prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
B = lambda t, lvl=0, col=None: (t, lvl, col)


def slide(title, bullets, image=None, footer="", title_color=NAVY, img_w=8.3,
          img_top=1.2):
    s = prs.slides.add_slide(BLANK)
    tb = s.shapes.add_textbox(Inches(0.45), Inches(0.22), Inches(12.4), Inches(0.95)).text_frame
    tb.word_wrap = True; p = tb.paragraphs[0]; p.text = title
    p.font.size = Pt(23); p.font.bold = True; p.font.color.rgb = title_color
    # bullet column widens when the image is narrower (no overlap with the picture)
    bw = Inches(max(4.0, 12.55 - img_w - 0.35)) if image else Inches(12.4)
    if bullets:
        bb = s.shapes.add_textbox(Inches(0.5), Inches(1.3), bw, Inches(5.65)).text_frame
        bb.word_wrap = True; bb.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        for i, (txt, lvl, col) in enumerate(bullets):
            par = bb.paragraphs[0] if i == 0 else bb.add_paragraph()
            par.text = ("• " if lvl == 0 else "    – ") + txt
            par.font.size = Pt(14 if lvl == 0 else 12); par.level = lvl
            par.font.color.rgb = col if col else RGBColor(0x20, 0x20, 0x20)
            par.space_after = Pt(3)
    if image and (FIG / image).exists():
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
    tf = bar.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.7)
    p0 = tf.paragraphs[0]; p0.text = kicker
    p0.font.size = Pt(15); p0.font.color.rgb = RGBColor(0xa9, 0xc0, 0xe8); p0.font.bold = True
    p1 = tf.add_paragraph(); p1.text = title
    p1.font.size = Pt(30); p1.font.color.rgb = WHITE; p1.font.bold = True
    return s


def table_slide(title, headers, rows, col_w, cell_colors=None, footer="",
                fontsize=11):
    """rows: list[list[str]]; cell_colors[r][c] -> RGBColor or None (body only)."""
    s = prs.slides.add_slide(BLANK)
    tb = s.shapes.add_textbox(Inches(0.45), Inches(0.22), Inches(12.4), Inches(0.9)).text_frame
    tb.word_wrap = True; p = tb.paragraphs[0]; p.text = title
    p.font.size = Pt(23); p.font.bold = True; p.font.color.rgb = NAVY
    nr, nc = len(rows) + 1, len(headers)
    gt = s.shapes.add_table(nr, nc, Inches(0.45), Inches(1.4),
                            Inches(sum(col_w)), Inches(0.45 + 0.66 * len(rows))).table
    for c, w in enumerate(col_w):
        gt.columns[c].width = Inches(w)
    for c, h in enumerate(headers):
        cell = gt.cell(0, c); cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
        tf = cell.text_frame; tf.word_wrap = True; pp = tf.paragraphs[0]
        pp.text = h; pp.font.size = Pt(fontsize); pp.font.bold = True
        pp.font.color.rgb = WHITE; pp.alignment = PP_ALIGN.CENTER
    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            cell = gt.cell(r, c); tf = cell.text_frame; tf.word_wrap = True
            pp = tf.paragraphs[0]; pp.text = val; pp.font.size = Pt(fontsize)
            pp.alignment = PP_ALIGN.CENTER if c > 0 else PP_ALIGN.LEFT
            col = None
            if cell_colors is not None:
                col = cell_colors[r - 1][c]
            if col is not None:
                cell.fill.solid(); cell.fill.fore_color.rgb = col
                pp.font.color.rgb = WHITE; pp.font.bold = True
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = LIGHT if r % 2 else WHITE
    if footer:
        fb = s.shapes.add_textbox(Inches(0.45), Inches(7.04), Inches(12.4), Inches(0.4)).text_frame
        fb.word_wrap = True; fp = fb.paragraphs[0]; fp.text = footer
        fp.font.size = Pt(8.5); fp.font.color.rgb = GREY
    return s


# ============================ 1 TITLE ======================================
s = prs.slides.add_slide(BLANK)
t = s.shapes.add_textbox(Inches(0.7), Inches(2.1), Inches(12), Inches(2.2)).text_frame
t.word_wrap = True
t.paragraphs[0].text = ("Taking StatFEM onto the track: a Bayesian digital twin of a real "
                        "aerospace structure")
t.paragraphs[0].font.size = Pt(30); t.paragraphs[0].font.bold = True
t.paragraphs[0].font.color.rgb = NAVY
p = t.add_paragraph()
p.text = "What worked, what didn't, and the most publishable finding(s) — review with Dr. Bilionis"
p.font.size = Pt(18); p.font.color.rgb = ORANGE
st = s.shapes.add_textbox(Inches(0.7), Inches(4.6), Inches(12), Inches(1.6)).text_frame
st.word_wrap = True
st.paragraphs[0].text = ("Agentic BayesX — Andrew Voss (lead) · Claude Code (lead agent).  Real NASA "
                         "ShockSat FEM (~406k DOF) + real modal-hammer test data; NUTS/TMCMC Bayesian "
                         "updating; held-out scoring against a no-skill baseline.")
st.paragraphs[0].font.size = Pt(14); st.paragraphs[0].font.color.rgb = GREY
p2 = st.add_paragraph()
p2.text = "Consolidation packet · 2026-06-26 · every number traces to a saved out/*.json (footers)."
p2.font.size = Pt(12); p2.font.color.rgb = GREY

# ============================ 2 HOW TO READ ================================
slide("How to read this packet", [
    B("Two audiences: plain-English on the statistics/ML side (terms defined on first use); "
      "advanced on structural dynamics (FRF, modal, MAC, apparent mass).", 0),
    B("Status legend on every result:", 0, NAVY),
    B("GREEN = acceptance threshold met, trustworthy as stated.", 1, GREEN),
    B("YELLOW = threshold NOT met but understood + documented; usable only with the stated caveat "
      "(an honest finding, never 'success').", 1, ORANGE),
    B("RED = blocking / withdrawn.", 1, RED),
    B("EXPLORATORY = ran, figures + numbers exist, but NO immutable checker yet (most of the recent "
      "FRF-correlation / remeshing / new-metric work).", 0, GREY),
    B("CHECKER-BACKED = an immutable, SHA-locked checker graded it (IFT, consistency toy, model-class "
      "selection, FEM-remesh Card D).", 0, GREY),
    B("Sampler labels are explicit: NUTS (default), TMCMC (when NUTS goes multimodal — stated why), or "
      "non-converged (flagged, never reported as a clean pass).", 0, NAVY),
    B("Headline numbers are repeated in footers with their source file so a reviewer can audit them.", 0),
], None,
    footer="Result-status standard from AGENTS.md. 'NUTS active' requires passing all-variable convergence, not just that a sampler ran.")

# ============================ 3 OBJECTIVE =================================
slide("The objective (unchanged) and the scope reset (new)", [
    B("Vision: take StatFEM — fusing a physics FEM with test data while explicitly modelling that the "
      "model is WRONG — from the parking lot (linear-static, model-matches-data) onto the track: a real "
      "DYNAMIC aerospace structure, learn physics from REAL data, push to a load/margin decision.", 0),
    B("StatFEM = statistical finite element method: prediction + a 'discrepancy' (model-form error) + "
      "sensor noise, kept separate.  Discrepancy = a learned correction for where the model is wrong.", 1),
    B("SCOPE RESET (this review): no more building a tray experiment — work the data we already have.", 0, ORANGE),
    B("We inherited a vendor FEM already correlated by the usual standards (mode shapes via MAC, and "
      "natural frequencies).  MAC = modal assurance criterion, 0–1, how parallel two mode shapes are.", 0),
    B("We test whether Bayesian updating makes it a TRUSTWORTHY and USABLE twin in the FRF regime — "
      "the frequency-response function |H(f)| an engineer actually predicts loads from.", 0, NAVY),
    B("Trust gate (our answer to 'garbage-in-garbage-out'): held-out calibration — predict data we hid, "
      "check the 95% bands really cover it ~95% of the time.", 0),
], "reuse_sensor_map.png", img_w=4.7,
    footer="Full vision: notes/project_vision.md. ShockSat = NASA public modal-survey + FEM; single standalone satellite, 9 stiffness groups, 84 'good' accelerometers, 45–260 Hz.")

# ============================ 4 EXEC SUMMARY ==============================
slide("Executive summary", [
    B("The inherited FEM is genuinely correlated on MODES (MAC 0.63, frequency error ~2.5–3%) — but has "
      "LARGE model-form error in the FRF regime (per-channel log|H| correlation only ~0.27).", 0),
    B("Bayesian updating CONVERGES (NUTS, R-hat 1.00) and is HONEST, but the posterior MEAN barely moves: "
      "identifiable stiffness shifts 0–4%; held-out frequency error 3.33%→2.68%; FRF correlation 0.27→0.34.", 0),
    B("Value is real for FREQUENCY (held-out skill +0.93) and absent for per-channel single-impact "
      "AMPLITUDE (skill ≈ −0.9 = worse than guessing) — but the amplitude bands honestly COVER.", 0),
    B("The bands are perpetually TOO WIDE to certify: 95% covering band ≈ +27 dB, ~10–13× the standard "
      "FEM+6 dB envelope. This 'trustworthy-but-not-sharp' wall is itself a key finding.", 0, RED),
    B("It always comes back to MODE SHAPES. Agentic remeshing + ~30 model-form edits could not crack the "
      "per-point FRF correlation (plateau ≈ 0.4). The binding limit is a MODEL problem, not a statistics one.", 0, NAVY),
    B("The strongest forward-looking results are METHODS: the OBSERVABLE + the model-error REGULARIZER decide "
      "well-posedness — modal-feature likelihoods converge, and on the hard whole-FRF observable a bounded learned "
      "knob (IFT's β) works where a free discrepancy variance diverges; a learned knob also answers the "
      "consistency concern.", 0, GREEN),
], "fig_wide_ci.png", img_w=6.0,
    footer="Sources: correlate_all.json, bayes_update.json, value_eval_seed00.json, probe_seed00.json, scorecard.json. EXPLORATORY/YELLOW unless noted.")

# ============================ 5 PUBLISHABLE ===============================
slide("The most potent, publishable finding(s)", [
    B("#1  'Trustworthy but not sharp' on a REAL, already-correlated aerospace FEM.", 0, NAVY),
    B("StatFEM stays calibrated under large model error (held-out frequency coverage good, +0.93 skill) "
      "but the FRF-amplitude bands are irreducibly too wide to certify; the binding limit is per-node "
      "mode-shape fidelity — a MODEL problem no statistical lever or agentic remeshing closed.", 1),
    B("#2  The OBSERVABLE and the model-error REGULARIZER — not 'where the physics lives' — decide well-posedness.", 0, NAVY),
    B("Physics-in-the-LIKELIHOOD converges fine for a MODAL-feature observable (L5, R-hat 1.002). The whole-FRF "
      "MAGNITUDE is the hard, multimodal observable for everyone (IFT included under NUTS). On that hard observable, "
      "a BOUNDED learned regularizer (IFT's temperature β — or an informative discrepancy prior) restores a "
      "tractable, calibrated posterior where a FREE discrepancy variance (σ_d→∞) does not.", 1),
    B("#3  A LEARNED model-error knob answers the consistency concern (Bilionis/Alberts/Kairui).", 0, NAVY),
    B("Both StatFEM's σ_d and IFT's β remove the arbitrary 'residual-noise / number-of-physics-samples' knob (the "
      "toy: the drift is to the fictitious σ_r, not the mesh). Honest shared limit: none recovers θ under genuine "
      "model error — the discrepancy absorbs the error, it does not flag it.", 1),
    B("Cross-cutting (for autonomous engineering): convergence ≠ trust — only a held-out gate (and a full "
      "4-chain run) detects an over-confident or under-identified twin; cheap probes mislead both ways. The "
      "agentic deliverable is the auditable BOUNDARY of data-driven remodeling.", 0, GREEN),
], None,
    footer="Detail on each: PART B slides + slide 26. Honest framing: #1 is a strong negative/boundary result; #2/#3 are the constructive method contributions.")

# ============================ PART A =======================================
divider("PART A — the ShockSat twin", "What Bayesian updating did to a real, already-correlated FEM")

# 6 inheritance
slide("The inheritance: correlated on modes, wrong on the FRF", [
    B("We did NOT build this FEM — it is a vendor model, already correlated to a modal survey.", 0),
    B("On MODES it looks good: matched MAC 0.63, natural-frequency error ~2.5–3.3%.", 0, GREEN),
    B("On the FRF |H(f)| it is NOT good: per-channel log|H| correlation only ~0.27–0.30; "
      "median peak-amplitude error ~15.7 dB.", 0, RED),
    B("Why the gap? |H| = (drive shape)×(sensor shape)/damping — it folds TWO local mode-shape values "
      "plus damping, so a model that gets global frequencies right can still place per-point energy wrong.", 0, NAVY),
    B("This is exactly the 'already-correlated yet not FRF-usable' problem the review is about.", 0),
    B("Plain-English: the model hums at the right pitches, but predicts the wrong loudness at each point.", 1, GREY),
], "reuse_strain_energy.png", img_w=6.4,
    footer="src: correlate_all.json (baseline MAC 0.631, FRF corr median 0.296, 15.7 dB) | strain-energy: which modes load which groups; joints only ~3% (SE-diluted).")

# 7 new metric
slide("New metric: does updating move the MEAN closer to the data?", [
    B("Old scoring judged the 95% intervals + smoothing — which proved unusable (slides 11–12). So we add "
      "a metric on the MEAN function alone:", 0),
    B("Correlation between the twin's predicted MEAN log|H| and the measured log|H|, per channel, vs the "
      "ORIGINAL inherited FEM. Apples-to-apples: deterministic modal participations + one global gain.", 1),
    B("Result: original FEM 0.269 → Bayesian-updated 0.338 (+26%); 70% of 84 channels improve.", 0, GREEN),
    B("But the mean stays far from a usable correlation (~0.7). Updating helps; it does not fix the FRF.", 0, RED),
    B("So: a real but minor mean improvement — useful as a sanity gain, not a certification-grade twin.", 0, NAVY),
], "fig_new_metric.png", img_w=6.6,
    footer="src: frf_comparison.json (orig 0.269, updated 0.338, 70% better, 84 ch, +X). EXPLORATORY/YELLOW. 'updated' = measured modal freq + damping calibration.")

# 8 new metric detail
slide("New metric, channel by channel (12 examples)", [
    B("Measured |H| (black) vs original FEM (orange) vs updated mean (blue).", 0),
    B("Peaks line up (frequency is right); per-channel LEVELS scatter — the shape error.", 0, NAVY),
    B("Updating nudges many channels toward the data, but several stay badly off.", 0),
    B("Per-panel correlation in each title: most go up a little, a few go down.", 1),
    B("This is the visual behind the +0.27→0.34 headline.", 0),
], "reuse_frf_grid.png", img_w=8.6,
    footer="src: psd_envelope/figures/frf_comparison_grid.png. Log–log |H| (g/lbf), real ShockSat +X. EXPLORATORY/YELLOW.")

# 9 mean movement quantified
slide("Bayesian updating converges — but the mean moves only minorly", [
    B("Question: by how much did calibration actually move the model?", 0),
    B("NUTS converged cleanly: R-hat 1.0022, ESS 2243, 0 divergences, 4 chains, 22 pooled modes.", 0, GREEN),
    B("Identifiable stiffness groups moved 0–4% (bottom_box −4%, top_box +3%, plates ~0%).", 0, NAVY),
    B("The other 6 groups (joints, welds, contact, brackets) fell back to the prior — wide, ~unmoved.", 0, ORANGE),
    B("Held-out frequency error improved 3.33% → 2.68%. Real, modest.", 0),
    B("Industry read: this is a small, defensible refinement of an already-correlated model — NOT a "
      "transformation. The data simply does not pin most of the knobs.", 0, RED),
], "fig_theta_movement.png", img_w=6.6,
    footer="src: bayes_update.json (NUTS R-hat 1.0022 / ESS 2243 / 0 div / 4 ch). θ = stiffness multiplier; θ=1 is the inherited FEM. EXPLORATORY/YELLOW.")

# 10 value freq vs amp
slide("Value of updating: strong for frequency, none for amplitude", [
    B("Held-out skill = 1 − (twin error)/(climatology error). Climatology = a no-skill baseline that "
      "guesses a held-out channel from the population of observed channels.", 0),
    B("Skill > 0 only if the twin carries information beyond the population.", 1),
    B("FREQUENCY: skill +0.93 — calibration roughly halves the as-received FEM frequency error.", 0, GREEN),
    B("Per-channel single-impact AMPLITUDE: skill −0.76 (easy) to −2.8 (hard) — worse than guessing.", 0, RED),
    B("BUT amplitude coverage is honest (~0.97): the bands are wide enough to contain the truth.", 0, NAVY),
    B("So the twin is a valuable FREQUENCY twin and an honest-but-uninformative amplitude predictor.", 0),
], "reuse_value_summary.png", img_w=6.8,
    footer="src: value_eval_seed00.json (freq skill +0.93; non-hard amp −0.76, hard −2.79, all −0.93, coverage 0.97). CHECKER-BACKED (modelclass_L5, YELLOW).")

# 11 wide CI (central)
slide("The central finding: the bands are too WIDE to certify", [
    B("This is the honest wall, and it recurs on every dataset (ShockSat single-impact, clean multi-ref, "
      "and the MPL test stand).", 0, NAVY),
    B("To actually COVER the held-out data the twin needs a 95% band of ≈ +27 dB (PSD).", 0, RED),
    B("That is ~10–13× the GRMS of the standard FEM+6 dB envelope an engineer uses today.", 0, RED),
    B("No aerospace team certifies against a band ~6× above the mean. So: honest, but not usable as-is.", 0),
    B("Premise check: even FEM+6 dB does not cover — it leaks 10–61% of the held-out band energy. "
      "Neither a fair FEM margin NOR a reasonable twin band is tight AND covering.", 0, ORANGE),
    B("The width is the honest cost of a coarse model + scrappy data — exactly the regime the robust-twin "
      "vision promises to SURVIVE; making it SHARP (not just honest) is the open work.", 0, NAVY),
], "fig_wide_ci.png", img_w=6.4,
    footer="src: probe_seed00.json (clean multi-ref, NUTS R-hat 1.0016/ESS 1758/0 div; σ_amp(log) 1.60 → +27.3 dB band; GRMS ratio ~10–13×). EXPLORATORY/YELLOW (honest negative).")

# 12 wide bands visual
slide("The wide bands, shown on held-out channels", [
    B("Twin 95% band (shaded) vs measured (black) at held-out sensors.", 0),
    B("The band covers — but it spans more than a decade in |H| at the hard channels.", 0, RED),
    B("Peaks are located well; the VERTICAL spread (amplitude) is the problem.", 0, NAVY),
    B("A tighter, still-covering band would require a model whose per-point energy is right — i.e. better "
      "mode shapes, not cleverer statistics.", 0),
], "reuse_heldout_frf.png", img_w=8.4,
    footer="src: psd_envelope/figures/heldout_psd_examples.png. Real ShockSat. EXPLORATORY/YELLOW.")

# 13 mode shapes
slide("It always came back to MODE SHAPES", [
    B("We mapped WHERE the model is wrong after frequency + damping were already corrected.", 0),
    B("The fundamental 54 Hz mode has the right FREQUENCY but the wrong SHAPE: best MAC over ALL FEM "
      "modes ≈ 0.17. The model gets the pitch but not the deflected shape, even at mode 1.", 0, RED),
    B("Worst residuals: the free bottom (steel) corner and the 150–210 Hz cluster.", 0, NAVY),
    B("'Shape-oracle' test: if you GIVE the twin the measured shape at a held-out sensor, the amplitude "
      "error σ drops 1.26 → 0.70 — proof the shape IS the reducible lever, and it is missing.", 0, GREEN),
    B("But measured shapes do NOT transfer to held-out sensors from this single-impact data (borrow-R² ≈ 0): "
      "per-point single-impact |H| is a near-field quantity, not cleanly modal.", 0, ORANGE),
], "reuse_residual_map.png", img_w=6.6,
    footer="src: residual_map.json (54 Hz shape MAC 0.17), shape_diag.json (σ 1.26→0.70), shape_borrow_diag.json (R²≈0). EXPLORATORY/YELLOW.")

# 14 agentic remeshing
slide("Was agentic remeshing + Bayesian updating ever done? Yes — we ran it (honest result)", [
    B("We ran the literal experiment: the BEST remesh (al_rho_lo, top FRF-corr edit) THROUGH the actual "
      "modal-feature NUTS, all on ONE honest metric (deterministic physics participations + 1 global gain — NO "
      "per-channel fitting). Self-check reproduced inherited + calibration = 0.338 exactly.", 0),
    B("Honest result: inherited FEM + calibration = 0.338 (best). Best-remesh + calibration = 0.267. Best-remesh + "
      "the actual Bayesian θ-posterior = 0.183. The combination does NOT beat plain calibration — it is WORSE.", 0, RED),
    B("The earlier '+0.08 / ~10%' was a SCORING ARTIFACT: the generous metric (=0.379) least-squares-fits one "
      "complex amplitude+phase PER MODE (~40–60 knobs) to the MEASURED FRFs; the honest metric fits 1 global gain. "
      "Remove the fitting and the mass edit worsens the model's own shapes; Bayes (stiffness knobs, a MASS error) "
      "overfits observed modes → held-out frequency 2.92% → 4.23%.", 0, ORANGE),
    B("NUTS converged cleanly (R-hat 1.004, ESS 774, 0 div) — a TRUSTWORTHY negative, not a sampler failure. "
      "Card D (checker): 0 of 6000 stiffness points fix shape without detuning frequency.", 0, NAVY),
    B("Conclusion: best-remesh + best-Bayes ≈ 0.18–0.27 ≪ usable ~0.7; neither lever nor their combination cracks "
      "per-point FRF. The wall is mode-shape fidelity — statistics/fitting can MASK it but not fix it. = the boundary.", 0, GREEN),
], "fig_combine_best.png", img_w=6.5,
    footer="src: out/combine_best.json (combine_best.py; NUTS al_rho_lo R-hat 1.004/ESS 774/0 div; self-check=0.338). EXPLORATORY/YELLOW honest negative. Generous-metric plateau: fig_remesh_plateau.")

# 15 remesh detail
slide("Why remeshing can't fix it (the Pareto wall)", [
    B("The mesh is already converged: 37–135 elements per bending wavelength at 260 Hz — finer cannot "
      "move the modes (dish 2× refine moved global MAC +0.0016).", 0),
    B("Topology is complete: bulkheads, bolted CBUSH joint, struts all present and node-merged correctly.", 0),
    B("Softer interfaces improve hard-region SHAPE but DETUNE frequency; stiffer does the reverse — same "
      "knobs, opposite directions. That trade is WHY the data can't pin a clean optimum.", 0, NAVY),
    B("Bayesian evidence agrees: a richer 16-parameter local-stiffness model is the WORST by Occam "
      "(slide 22). Stiffness is not the lever; the residual is shape + near-field + damping.", 0, RED),
    B("Only a from-scratch geometry/architecture rebuild could change the shapes — a major gamble, not "
      "recommended on an already-correlated model.", 0),
], "reuse_roadblock_remesh.png", img_w=6.8,
    footer="src: Card D correlation_contribution.md, joint_frontier (0/6000), dish-refine +0.0016; stage1_evidence.json (16-param worst). CHECKER-BACKED + EXPLORATORY.")

# ============================ PART B =======================================
divider("PART B — method", "StatFEM formulations, the consistency concern, and IFT")

# 16 formulations
slide("We evaluated many StatFEM / likelihood formulations (≥10)", [
    B("The deliverable was not one model — it was a structured search over WHERE and HOW physics, "
      "discrepancy, and the observable enter.", 0),
    B("Converge AND useful (green): modal peak-FREQUENCY; inferred mode-shape FIELD (Beck); shape-MAC; "
      "analytic Bayesian evidence.", 0, GREEN),
    B("Converge but ~null on one impact (amber): frequency+MAC-as-constraint; complex PHASE.", 0, ORANGE),
    B("Non-converged / multimodal (red): whole-FRF magnitude; peak-AMPLITUDE feature; free correlated "
      "discrepancy on the whole FRF.", 0, RED),
    B("Pattern: the converging, useful observables are MODAL; the whole-FRF magnitude is pathological.", 0, NAVY),
    B("Also evaluated: orthogonal Schneider (space×frequency-correlated discrepancy), Das–Debnath complex "
      "latent modes, Rayleigh / non-proportional damping, hierarchical two-population discrepancy.", 0),
], "reuse_likelihood_inventory.png", img_w=7.4,
    footer="src: modelclass_L5 likelihood inventory + papers_statfem_studies (Schneider/Das-Debnath/orthogonal arms). CHECKER-BACKED (YELLOW).")

# 17 the concern stated
slide("The concern from Bilionis / Alberts / Kairui (stated plainly)", [
    B("For ODE/PDE inverse problems, putting the physics in the LIKELIHOOD can be INCONSISTENT:", 0, NAVY),
    B("you choose how many times to 'sample' / evaluate the physics residual (collocation points, mesh "
      "density, frame count), and that count acts like a free knob on the posterior.", 1),
    B("Equivalently, the residual is treated as pseudo-observations with a residual-noise scale σ_r that "
      "is set ARBITRARILY — tighten σ_r and the posterior tightens, with no principled value.", 1),
    B("This is the same family as the 'GIGO / arbitrary σ_d' objection industry skeptics raise.", 0, RED),
    B("We have NOT yet published a clean map from this inconsistent method → our StatFEM → Information "
      "Field Theory (IFT). We HAVE run the experiments to tell that story — next slides.", 0, ORANGE),
    B("Why it matters: if the method's answer depends on an arbitrary sampling/σ choice, it is not "
      "defensible for certification. We need to show our formulation removes that dependence.", 0, NAVY),
], "reuse_consistency_schematic.png", img_w=6.0,
    footer="IFT/PIFT references: Hao & Bilionis 2306.02150; Alberts & Bilionis 2301.07609. Concern = posterior should not depend on an arbitrary count of physics evaluations / σ_r.")

# 18 the map (table)
table_slide("Mapping the concern: inconsistent method → StatFEM → IFT",
    ["Construction", "Physics lives in", "Model-error knob",
     "Arbitrary knob?", "Converges on whole-FRF |H|?", "Recovers θ under model error?"],
    [
     ["Classical (physics-in-likelihood)", "Likelihood", "σ_r — fixed residual 'noise'",
      "YES — θ drifts", "(toy only)", "No"],
     ["StatFEM, whole-FRF |H| (our M2)", "Likelihood (FEM + discrepancy)", "σ_d — FREE / learned",
      "No (mesh-invariant)", "NO — free-σ_d singularity", "No — θ absorbs error"],
     ["StatFEM, MODAL feature (our L5)", "Likelihood (FEM modal freq)", "σ_w on freq residual",
      "No (mesh-invariant)", "YES — NUTS R-hat 1.002", "frequency only"],
     ["IFT / PIFT", "PRIOR (physics as soft constraint)", "β — BOUNDED learned temp.",
      "No (mesh-invariant)", "via TMCMC (NUTS also multimodal)", "No (shared limit)"],
    ],
    col_w=[2.45, 2.05, 2.0, 1.65, 2.25, 1.7],
    cell_colors=[
     [None, None, None, RED, GREY, RED],
     [None, None, None, GREEN, RED, RED],
     [None, None, None, GREEN, GREEN, ORANGE],
     [None, None, None, GREEN, GREEN, RED],
    ],
    footer="src: consistency_toy/sweep_summary.json + ift_real_validation/scorecard.json + modal_feature.json. KEY (corrected): physics-in-the-LIKELIHOOD converges fine for a MODAL observable; the whole-FRF MAGNITUDE is the hard one for everyone (IFT also multimodal under NUTS). IFT-vs-M2 win = a BOUNDED learned regularizer (β) vs a FREE variance (σ_d); an informative σ_d prior is the likelihood-side cure.",
    fontsize=9.5)

# 19 consistency evidence
slide("Consistency toy: the drift is to the arbitrary knob, not the mesh", [
    B("Controlled toy (truth θ=1.15) comparing the three constructions across refinement knobs.", 0),
    B("Physics-in-likelihood (M-lik): θ DRIFTS as you change the fictitious residual-noise σ_r "
      "(spread 0.084) — exactly the inconsistency.  But it is ~flat vs the genuine mesh knob.", 0, RED),
    B("StatFEM (learned σ_d) and IFT (learned β): ~flat vs the mesh — no arbitrary σ_r knob to set.", 0, GREEN),
    B("So the 'discretization-dependence' charge is real but SHARPENED: the sensitivity is to the "
      "fictitious noise/temperature, which a LEARNED knob removes.", 0, NAVY),
    B("Honest shared limit: under genuine model-form error (ε=0.3) all three bias θ to ~1.27 — none "
      "recovers the true parameter. The discrepancy absorbs the error; it does not flag it.", 0, ORANGE),
    B("All cells converged (R-hat ≤ 1.008).", 1, GREY),
], "reuse_consistency_money.png", img_w=7.0,
    footer="src: statfem_consistency_toy/out/sweep_summary.json. CHECKER-BACKED (YELLOW). Each panel: posterior θ vs a refinement knob; flat = consistent, sloped = drift.")

# 20 IFT benchmark
slide("Side-by-side on the WHOLE-FRF observable: IFT vs free-discrepancy StatFEM", [
    B("Apples-to-apples on the SAME (hard) whole-FRF |H| observable: identical data, forward, splits, scorer.", 0, NAVY),
    B("M2 = whole-FRF likelihood with a FREE discrepancy variance: fails under BOTH samplers (NUTS R-hat 63, "
      "TMCMC 129; σ_d runs away to 7.4 — a variance singularity).", 0, RED),
    B("IFT = physics in the PRIOR with a BOUNDED learned temperature β, same |H|: TMCMC CONVERGES "
      "(R-hat 1.0007) and COVERS (peak 0.97 / band 1.0). NOTE: both are multimodal under NUTS.", 0, GREEN),
    B("Honest read of the contrast: the win is the BOUNDED LEARNED regularizer, not 'prior vs likelihood' per se. "
      "Physics-in-the-likelihood converges fine for a MODAL observable (L5, R-hat 1.002); an informative σ_d prior "
      "is the likelihood-side cure for M2.", 0, ORANGE),
    B("IFT does NOT beat the modal twin on overall sharpness (band interval ≈ 20× wider — coarse-FEM ceiling), "
      "but is bounded, convergent, and calibrated where the free-discrepancy form is not.", 0, NAVY),
], "reuse_ift_scorecard.png", img_w=7.0,
    footer="src: ift_real_validation/out/scorecard.json + modal_feature.json. IFT TMCMC-escalated (NUTS multimodal). 25 splits L5, 5 IFT, 1 M2 (flagged non-converged). CHECKER-BACKED (YELLOW).")

# 21 IFT thermometer
slide("IFT's learned trust 'thermometer' reads strong-but-bounded distrust", [
    B("β is an inverse temperature: high β = trust the FEM; β → 0 = distrust it and widen gracefully.", 0),
    B("Learned β median ≈ 0.17 — about 246× BELOW the no-data anchor β* ≈ 42.8.", 0, NAVY),
    B("Reading: 'this coarse FEM deserves strong distrust' — and it says so quantitatively, BOUNDED "
      "(no runaway), without an arbitrary σ chosen by hand.", 0, GREEN),
    B("Contrast with M2's σ_d → 7.4 runaway: the prior-temperature form self-regularizes; the "
      "likelihood-variance form does not.", 0, RED),
    B("This β is the natural place for the 'tell the twin how wrong to expect the model to be' front-end "
      "(elicit β / its prior from known config deltas) — a defensible alternative to a hand-set σ_d.", 0, NAVY),
], "reuse_ift_beta.png", img_w=6.8,
    footer="src: ift_real_validation/out/scorecard.json (β_med 0.174, β* 42.8, collapse ×246, bounded). CHECKER-BACKED (YELLOW).")

# 22 evidence selection
slide("Evidence-based model selection (Occam): simpler wins", [
    B("We scored model classes by Bayesian evidence (marginal likelihood, which penalizes needless "
      "complexity) on 27 matched modal frequencies, BIC-adjusted and prior-robust.", 0),
    B("Winner: the as-received FEM with one global discrepancy — posterior model probability 0.91.", 0, GREEN),
    B("A richer 16-parameter LOCAL-stiffness model is the WORST — it does not earn its complexity.", 0, RED),
    B("Only suggestive structure: a space×frequency-CORRELATED discrepancy (M4), P≈0.09 — a hint that "
      "structuring the discrepancy (not adding stiffness knobs) is the lever if any.", 0, NAVY),
    B("Damping is frequency-blind here (damped-frequency shift 5.5e-5 ≪ the 7% discrepancy floor), so the "
      "frequency evidence cannot rank damping models — judged separately, also unidentified from one hit.", 0, ORANGE),
    B("Takeaway: on this data, don't add knobs — the inherited model is already Occam-optimal.", 0, NAVY),
], "reuse_strain_energy.png", img_w=6.2,
    footer="src: stage1_evidence.json (M0 P=0.906; M1_full_rich worst; M4 P=0.093; damped shift 5.5e-5). CHECKER-BACKED (YELLOW).")

# ============================ PART C =======================================
divider("PART C — related work, synthesis, and the next direction", "")

# 23 related papers
slide("Recent related papers we investigated", [
    B("Sequential StatFEM (Kavrakov et al.): time-domain modal-hammer assimilation — HIGH applicability; "
      "we ran a PSD-envelope pilot (honest negative: did not beat FEM+6 dB; same shape wall).", 0),
    B("Latent-force + Bayesian NN model-error twin (Kashyap/Nayek): MODERATE-HIGH for damping / residual "
      "model-form; offline + extrapolation caveats.", 0),
    B("Multi-level wing ROM / submodel digital twin (Lu et al.): MODERATE-LOW — fast deployment, but not "
      "Bayesian/statFEM and no local stress truth for ShockSat.", 0),
    B("Yan et al. 2026 (sensor faults / virtual sensing): we reproduced its aliasing claim on independent "
      "real data with a Bayesian method AND added the calibrated bands its deterministic net lacks "
      "(3.4 vs 8.8 dB at high-freq local modes).", 0, GREEN),
    B("Schneider 2022 (correlated-FRF discrepancy) and Das–Debnath 2020 (complex incomplete modal): "
      "integrated as discrepancy/likelihood arms — Schneider gives ~7× tighter bands in-distribution "
      "when iid fails to converge; Das–Debnath survives near-degenerate modes (0 vs 429 divergences).", 0),
], None,
    footer="src: shocksat_new_papers_review (YELLOW 41/1/0), paper_virtual_sensing_uq_toy (YELLOW 42/2/0), papers_statfem_studies (YELLOW 76/22/0). CHECKER-BACKED.")

# 24 synthesis
slide("Honest synthesis", [
    B("The inherited FEM is correlated on modes but has large FRF model-form error; Bayesian updating is "
      "trustworthy and converges, but moves the mean only minorly and cannot make the bands certifiable.", 0, NAVY),
    B("The wall is per-node mode-shape fidelity — a MODEL problem. Statistics (damping, shape-field, "
      "correlated discrepancy, evidence selection) and agentic remeshing all hit the same ~0.4 ceiling.", 0, RED),
    B("What DOES generalize: frequency value (+0.93), honest coverage, and two method results — IFT's "
      "physics-in-prior robustness, and the observable-over-sampler lesson.", 0, GREEN),
    B("Report it as a CONSERVATIVE screening / flag-when-the-FEM-is-wrong twin — NOT a sharp certification "
      "twin. The width is the honest cost of a coarse model + scrappy data.", 0, NAVY),
    B("The single biggest external risk to the vision: an ALREADY-correlated, relatively simple structure "
      "still needs better shapes for usable FRF bands. That is the finding to confront with Bilionis.", 0, ORANGE),
], None,
    footer="This synthesis is consistent with project_vision.md §7.1 (the bands-too-wide gap) and the held-out trust gate.")

# 25 publishable detail
slide("The publishable finding(s) — paper angles", [
    B("Paper 1 (boundary / negative-with-teeth): 'How far does StatFEM go on a REAL, already-correlated "
      "dynamic aerospace structure — and where the wall is.'", 0, NAVY),
    B("Contribution: a held-out-validated demonstration that the discrepancy machinery delivers TRUST but "
      "not SHARPNESS; the binding limit is per-node shape fidelity, quantified, with agentic remeshing "
      "establishing the boundary. Directly addresses the 'GIGO / pencil-whipping' skepticism.", 1),
    B("Paper 2 (method): 'What makes model-form-error-dominated dynamic StatFEM well-posed — observable "
      "choice + a bounded learned model-error regularizer (IFT temperature vs free discrepancy variance).'", 0, NAVY),
    B("Contribution: identical-data evidence that on the HARD whole-FRF observable a BOUNDED learned regularizer "
      "(IFT's β) gives a convergent, calibrated posterior where a FREE discrepancy variance diverges — while "
      "MODAL-feature likelihoods converge regardless (the observable is the bigger lever) — plus the consistency "
      "map that removes the arbitrary-σ objection. The Bilionis/Alberts/Kairui story, honestly scoped.", 1),
    B("Strongest single message for the review: #1 is the most DEFENSIBLE (real data, held-out, honest); "
      "#2 is the most NOVEL (method + consistency). Recommend leading with #1, anchoring novelty on #2.", 0, GREEN),
], None,
    footer="IP note: disclose to Purdue Senior IP Officer BEFORE any public disclosure; FTO/lit scan before any patent claim (project_vision.md §9).")

# 26 next direction
slide("Recommended next direction (to decide today)", [
    B("Option A — Lead with the BOUNDARY result + the IFT/consistency method (lowest new-compute, "
      "highest-confidence): write up #1 and #2 from the data we already have. RECOMMENDED.", 0, GREEN),
    B("Option B — Feature-space discrepancy: put the uncertainty in FEATURES ('peak at f0 ± X%, amplitude "
      "Y ± Z dB per mode') instead of a per-frequency |H| band — removes the misalignment-driven width; "
      "test how close a usable +3/+6 dB band is. Bounded, near-term, we have the modal machinery.", 0, NAVY),
    B("Option C — Maximally-informative OWN test (data lever): multi-reference / roving excitation + "
      "QOI-optimal sensor placement, designed to beat the single-impact shape/damping limits. Highest "
      "ceiling, needs hardware + time.", 0, NAVY),
    B("Explicitly NOT recommended: more whole-FRF stiffness remeshing (Pareto wall) or a from-scratch "
      "geometry rebuild (major gamble on an already-correlated model).", 0, RED),
    B("Decision needed from the review: confirm A as the write-up spine; choose B and/or C as the next "
      "experiment; and whether IFT's β-front-end is the headline robustness story.", 0, ORANGE),
], None,
    footer="Cross-ref: project_vision.md §13 next actions (feature-space discrepancy 1b; agentic FEM correlation 1c; own-stand informative testing).")

# 27 reproducibility
slide("Status, provenance & what is surfaced for approval", [
    B("Checker-backed (immutable, SHA-locked): IFT real-validation, consistency toy, model-class "
      "selection (L5), FEM-remesh Card D, the papers studies — all OVERALL YELLOW (honest negatives) "
      "or GREEN integrity.", 0, GREEN),
    B("Exploratory (figures + numbers, NO checker yet): the recent FRF-correlation, remeshing-sweep, "
      "new-metric, wide-CI work (psd_envelope_twin). Labeled EXPLORATORY/YELLOW throughout.", 0, ORANGE),
    B("Every figure traces to a saved out/*.json; new figures from a single lintable make_review_figs.py "
      "(tufte-linted); this deck from make_deck.py. Samplers labeled (NUTS / TMCMC / non-converged).", 0),
    B("Surfaced for Andrew's approval (NOT self-applied): a docs/report/project_log.md row for this "
      "consolidation; promoting any EXPLORATORY result to checker-backed; any 'replace the inherited FEM' "
      "claim; durable-rule / sampler-standard edits.", 0, RED),
    B("No durable rules, checkers, sampler standards, or project notes were changed to build this packet "
      "(only the lead CURRENT-STATE block in notes/memory.md).", 0, NAVY),
], None,
    footer="Workspace: artifacts/reports/shocksat_bilionis_review_20260626/ (code/, figures/, slides/, packet.md, publishable_findings.md).")

# 28 appendix index
table_slide("Appendix — where each result lives",
    ["Result", "Workspace", "Status"],
    [
     ["New mean-function FRF metric; remeshing plateau; wide-CI; θ-movement",
      "shocksat_psd_envelope_twin_20260623", "EXPLORATORY/YELLOW"],
     ["IFT vs StatFEM-in-likelihood head-to-head (real ShockSat)",
      "ift_real_validation_20260619", "CHECKER YELLOW"],
     ["Consistency toy (physics-in-likelihood vs StatFEM vs IFT)",
      "statfem_consistency_toy_20260616", "CHECKER YELLOW"],
     ["Evidence-based model selection; value (freq vs amp); likelihood inventory",
      "shocksat_modelclass_L5_20260619", "CHECKER YELLOW"],
     ["Agentic FEM remeshing boundary (0/6000; mesh converged)",
      "shocksat_fem_remesh_20260618", "CHECKER GREEN 14/0/0"],
     ["StatFEM formulations program (Schneider / Das–Debnath / orthogonal)",
      "papers_statfem_studies_20260612", "CHECKER YELLOW 76/22/0"],
     ["Recent-paper applicability review + Yan virtual-sensing toy",
      "shocksat_new_papers_review_ / paper_virtual_sensing_uq_toy_", "CHECKER YELLOW"],
    ],
    col_w=[5.1, 4.9, 2.3],
    footer="Full chronological detail: notes/memory.md (CURRENT STATE), notes/runs.md, docs/report/project_log.md. Per-study: <workspace>/packet.md + checker_report.json.",
    fontsize=10)

out = WS / "slides" / "shocksat_bilionis_review.pptx"
out.parent.mkdir(exist_ok=True); prs.save(str(out))
print(f"wrote {out}  ({len(prs.slides._sldIdLst)} slides)")
