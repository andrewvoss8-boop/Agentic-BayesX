#!/usr/bin/env python3
"""
Build the ShockSat results-summary .docx.

CONSOLIDATION ONLY — no new science. Every figure is a provenance-labeled copy of an
existing, checker-backed, tufte-linted figure; every headline number is copied from a
study checker or printed on the reused figure. Nothing is stated stronger than its source.

Run:  python3 code/make_report.py
Out:  ShockSat_results_summary.docx  (in the workspace root)
"""
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIG = ROOT / "figures"
OUT = ROOT / "ShockSat_results_summary.docx"

NAVY = RGBColor(0x1F, 0x35, 0x55)
GREY = RGBColor(0x55, 0x55, 0x55)

doc = Document()

# ---- base styles ----
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)

def h(text, level=1):
    p = doc.add_heading(text, level=level)
    for r in p.runs:
        r.font.color.rgb = NAVY
    return p

def para(text, size=11, italic=False, bold=False, color=None, space_after=6):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.italic = italic
    r.bold = bold
    r.font.size = Pt(size)
    if color is not None:
        r.font.color.rgb = color
    p.paragraph_format.space_after = Pt(space_after)
    return p

def bullet(text, bold_lead=None):
    p = doc.add_paragraph(style="List Bullet")
    if bold_lead:
        r = p.add_run(bold_lead)
        r.bold = True
        p.add_run(text)
    else:
        p.add_run(text)
    return p

def figure(fname, caption, width=6.3):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(FIG / fname), width=Inches(width))
    cap = doc.add_paragraph()
    r = cap.add_run(caption)
    r.italic = True
    r.font.size = Pt(9)
    r.font.color.rgb = GREY
    cap.paragraph_format.space_after = Pt(14)
    return cap

# =====================================================================================
# TITLE
# =====================================================================================
t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("Bayesian Model Updating on a Real Aerospace Structure (ShockSat)")
r.bold = True
r.font.size = Pt(19)
r.font.color.rgb = NAVY
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub.add_run("How we measure success, what the updating methods actually delivered, "
                "and where the wall is")
r.font.size = Pt(13)
r.font.color.rgb = GREY
meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = meta.add_run("Andrew Voss  ·  2026-07-21  ·  results summary for advisor review (paper seed)")
r.font.size = Pt(10)
r.font.color.rgb = GREY

para("Provenance note. This is a consolidation of already-completed, independently-checked "
     "studies. Every figure is an unaltered copy of a figure that passed our figure-quality "
     "and honesty checks; every number is copied from the study's automated checker or is "
     "printed on the figure itself. Nothing here is stated more strongly than those sources "
     "support. Figure axis labels sometimes use internal shorthand — each caption translates "
     "it into plain language, and there is a short glossary below.",
     size=9, italic=True, color=GREY, space_after=10)

# =====================================================================================
# EXECUTIVE SUMMARY
# =====================================================================================
h("Executive summary", 1)
para("ShockSat is a small NASA satellite structure with a finite-element model (FEM) that NASA "
     "had already correlated, plus real modal-hammer test data. The goal was to use Bayesian "
     "updating — tuning uncertain model inputs with data while producing an honest uncertainty "
     "band, not a single guess — to turn that FEM into a trustworthy “digital twin” that "
     "predicts a real design load: the net force at the equipment tray’s center of gravity. "
     "We tried many established updating methods and, more recently, let AI agents rebuild the "
     "FEM itself and pick the best rebuild using the data. The honest headline is: the methods "
     "produce a defensible, well-calibrated load band, but none of them meaningfully out-predict "
     "the starting model on held-out data. The most transferable contribution is arguably the set "
     "of success measures we built to decide that — measures strict enough to catch a method that "
     "only looks good.")

para("What we found, in one place:", bold=True, space_after=2)
bullet("The chief obstacle is model-form error, not sloppy numbers. ",
       "The FEM matches frequencies (where the peaks are) but not the amplitudes and shapes that "
       "set the loads. No amount of parameter tuning removes that gap because the model is the "
       "wrong shape of model in the places that matter.")
bullet("Damping and mode shape are confounded, and the data cannot separate them. ",
       "Amplitude depends on both; with one drive point and coarse frequency resolution, many "
       "different (damping, shape) combinations fit the data equally well.")
bullet("Updating helps the peaks, not the shapes. ",
       "Matching measured frequencies and damping lifts the FEM-vs-test agreement modestly "
       "(median correlation 0.27 → 0.34), but the per-channel shape mismatch remains.")
bullet("Agentic remodeling did not beat a fair random baseline, ",
       "and the model the data’s own evidence score preferred did not predict held-out data "
       "any better — “best by evidence” and “best on new data” were different models.")
bullet("One genuine positive: model-form edits do move held-out predictions ",
       "(element-formulation, connectivity, mesh, and geometry changes each cleared our noise "
       "bar), correcting an earlier belief that remodeling was powerless — but a smart agent "
       "was no better than random at finding them.")
bullet("We did deliver one honest twin. ",
       "A statistical-FEM load band covers the held-out test data and stays humble (it widens "
       "when we hide information); it passed every integrity and calibration check. It is honest, "
       "not sharp — the residual uncertainty is a data limit, not a modeling oversight.")

# ---- glossary box ----
h("How to read this report (plain-language glossary)", 2)
gloss = [
    ("Digital twin", "the FEM tuned to test data, packaged with an uncertainty band on its predictions."),
    ("Bayesian updating", "using data to adjust uncertain inputs and, importantly, to output a probability "
                          "band instead of a single number."),
    ("Held-out test", "hide some measured data, fit on the rest, then score predictions against the hidden "
                      "data. This is the only honest test of whether updating helped."),
    ("Coverage", "of the hidden data points, the fraction that land inside the predicted 95% band. We want "
                 "about 95%: much less is over-confident, much more is needlessly wide."),
    ("Calibration / humility", "a good band widens when we remove information rather than staying falsely "
                               "narrow. A method that never widens is over-confident and is disqualified."),
    ("Model-form error", "the model is missing physics or has the wrong structure — a mismatch that tuning "
                         "the numbers cannot fix (as opposed to a parameter being merely off)."),
    ("Identifiability", "whether the data actually pin down a parameter. If two very different parameter "
                        "sets fit the data equally well, that parameter is not identifiable."),
    ("statistical FEM (statFEM)", "an updating method that adds an explicit “discrepancy” term for the "
                                  "gap between model and reality, so the prediction band stays honest under "
                                  "model-form error."),
    ("Net-CG force", "the net force at the equipment tray’s center of gravity — a real load used to size "
                     "the structure and its vibration test."),
    ("FRF", "frequency response function — response per unit input force versus frequency (structural term, "
            "used as-is)."),
]
for term, defn in gloss:
    p = doc.add_paragraph(style="List Bullet")
    rr = p.add_run(term + " — "); rr.bold = True
    p.add_run(defn)
    p.paragraph_format.space_after = Pt(2)

doc.add_page_break()

# =====================================================================================
# SECTION 1 — HOW WE DEFINE SUCCESS
# =====================================================================================
h("1. How we define success", 1)
para("Before comparing methods, we had to decide what “working” means. This turned out to be "
     "the hardest and, we think, the most useful part of the project. A model that reproduces the "
     "data it was fit on proves nothing; a single predicted number with no uncertainty is not "
     "decision-grade. So we defined success in terms an engineer signing off a load can trust.")

para("Success = a prediction that is right where it can be, and honest where it cannot. "
     "Concretely, an updated twin succeeds only if, on data it never saw:", bold=True, space_after=2)
bullet("its predicted band covers the held-out measurements (coverage near 95%);")
bullet("it stays humble — the band widens when we hide modes or drive points, instead of "
       "staying falsely narrow;")
bullet("it is not beaten by a fair, equal-effort baseline (the original model, or a random change "
       "of the same size);")
bullet("it improves the actual engineering quantity (the net-CG design load), not just an abstract "
       "curve-fit score.")

para("A method can fail any one of these while looking good on the others — which is exactly the "
     "trap the measures are built to catch. Figure 1 shows the delivered load band and the "
     "head-to-head test of these rules across candidate methods.")

figure("f1_success_delivery.png",
       "Figure 1. What “success” looks like, and the head-to-head test behind it. "
       "Top: the delivered 95% prediction band (blue) for the three net-CG tray loads versus "
       "frequency, against the held-out test data. The band covers the data (coverage 0.98–0.99) "
       "and is only modestly wider than the crude “model + 6 dB” rule engineers use today "
       "(1.5× sideways, 2.3× fore-aft, 2.5× vertical). Bottom-left: comparing methods, bar "
       "height is band width and the number on each bar is coverage; every discrepancy-aware method "
       "covers (≥0.98) while the “parameters-only” method (red) is over-confident and is "
       "disqualified. Bottom-right: the humility test — hide some modes and re-predict; honest "
       "methods widen (bars above 1.0), the parameters-only method never does. "
       "Source: net-CG method-selection study (2026-07-01); automated checker GREEN 22/0/0.")

figure("f2_success_trust.png",
       "Figure 2. Success is direction-specific, and the metric says so. The two sideways loads "
       "(shear) ride on modes the single sensor actually measured, so the twin can carry them "
       "(96% / 94% of the load sits on measured modes, panel A). The vertical load rides on "
       "“drumhead” modes above 230 Hz that the one vertical sensor never resolved (only 45% "
       "measured), so its band is honest-but-wide. Panel D shows why: with those modes unmeasured, "
       "the vertical band is set almost entirely by an assumption about their amplitude, not by "
       "data. A success measure that hid this would be lying. "
       "Source: net-CG method-selection study (2026-07-01); checker GREEN 22/0/0.")

para("Takeaway. These measures are strict on purpose. They reward honesty (cover and widen), "
     "penalize false confidence, insist on beating a fair baseline, and are tied to a real load "
     "rather than a curve score. In the sections that follow, this is the bar every method is held "
     "to — and it is the bar that most of them fail to clear by a meaningful margin.", bold=False)

doc.add_page_break()

# =====================================================================================
# SECTION 2 — SURVEY OF UPDATING TECHNIQUES
# =====================================================================================
h("2. Bayesian updating techniques, checked against those measures", 1)
para("We ran the main families of Bayesian FEM updating on ShockSat: tuning stiffness/mass "
     "parameters from measured frequencies; adding mode-shape information; the statistical-FEM "
     "approach that models the model-vs-reality discrepancy explicitly; sequential (filtering) "
     "updates; and updating the damping directly against the measured frequency responses. Each "
     "was scored against the Section 1 measures on held-out data.")

para("Result 2a — Updating fixes the peaks, not the shapes. ", bold=True, space_after=2)
para("Matching measured natural frequencies and measured damping does move the model toward the "
     "data: across response channels the median agreement improves from 0.27 to 0.34, and about "
     "70% of channels get better (Figure 3). But the improvement is in where the peaks sit and how "
     "tall they are — the detailed shape of each channel’s response still disagrees. This "
     "“shape wall” is the recurring signature of model-form error: the model is right about "
     "resonances and wrong about the response between and across them.")

figure("f3_frf_wall.png",
       "Figure 3. Updating fixes the peaks, not the shapes. Each panel is one response channel: "
       "black = measured data, dashed = original FEM, orange = updated FEM (measured frequencies "
       "and measured damping). Panels are ordered by how well they agree. The update aligns the "
       "resonant peaks and sets their heights, but the overall curve shape still departs from the "
       "data in most channels. Median curve-correlation improves 0.27 → 0.34 (70% of channels "
       "improve) — real but small, and the residual shape error is the wall. "
       "Source: ShockSat FRF-updating comparison (2026-06/07).")

para("Result 2b — Updating the damping does not clear the bar, and we can prove why. ", bold=True,
     space_after=2)
para("Amplitude is governed jointly by damping and mode shape, so damping is the natural lever for "
     "the amplitude mismatch. We implemented and physics-validated a genuine damping update (band, "
     "Rayleigh, and per-joint loss-factor forms) and scored it against held-out responses "
     "(Figure 4). It did not help: the damping-updated model actually scored slightly below the "
     "baseline, the best gain came from a shape change (not damping), and a fair random change did "
     "as well as the agent-chosen one. The mechanism is decisive and is a genuine finding: at the "
     "available ~2 Hz frequency resolution, ShockSat’s light damping (~0.3%) spans barely one "
     "frequency line, so fitting damping fits the resolution artifact rather than the physics.")

figure("f4_damping.png",
       "Figure 4. Updating the damping does not clear the noise floor. Held-out agreement (blue, "
       "higher is better) for the baseline, a damping-updated model, two shape edits, a combined "
       "edit, and a random edit. The grey band is the baseline ± 2 fold-to-fold standard errors "
       "— the noise floor a real improvement must clear. The damping model (0.193) sits below the "
       "baseline (0.197); the best arm is a shape edit (+0.042) that does not clear the floor; and "
       "random does as well as the rest. Red = a separate held-back drive, graded once. "
       "Source: FRF-domain damping-updating study (2026-07-10); checker YELLOW 19/2/0 "
       "(the yellow is the pre-registered “claim not supported” outcome, honestly reported).")

para("Across the family. ", bold=True)
para("The pattern repeats: discrepancy-aware methods (statistical FEM) are the ones that pass the "
     "honesty test — they cover the held-out data and widen when blinded — and one such twin was "
     "delivered (Figures 1–2). Sharper methods that fit only parameters or only frequencies look "
     "better in-sample but become over-confident out-of-sample and are disqualified. Sequential "
     "filtering did not beat the simple “model + 6 dB” envelope on held-out vibration level. "
     "In short: the methods that are honest do not sharpen much, and the methods that sharpen are "
     "not honest — a direct consequence of the model-form and identifiability limits in Section 4.")

doc.add_page_break()

# =====================================================================================
# SECTION 3 — AGENTIC REMODELING & MODEL-CLASS SELECTION
# =====================================================================================
h("3. Letting agents rebuild the model, and selecting the best rebuild", 1)
para("If tuning a fixed model cannot cross the shape wall, the next idea is to change the model "
     "itself. Modern AI agents can now propose real structural changes — remeshing, changing "
     "element formulations, altering connectivity and joints, editing geometry — not just scaling "
     "parameters. We built a closed loop: an agent inspects where the model disagrees with data, "
     "proposes rebuilt FEMs, we solve them, and we select among them. Two questions matter: does a "
     "smart agent beat an equal-effort random search, and does selecting on the data’s own "
     "evidence pick the model that predicts new data best?")

para("Result 3a — The evidence score and the held-out score disagree. ", bold=True, space_after=2)
para("We funneled 151 candidate rebuilds down to a single winner by Bayesian model evidence — the "
     "quantity that formally scores “how well does this model class explain the data” (Figures 5–6). "
     "The winner was a clear top by evidence, and prior-robust. But it did not predict the held-out "
     "design load any better than the original model. “Best by evidence” and “best on new "
     "data” were different models — a concrete, reproducible instance of a known but under-"
     "appreciated gap: model evidence rewards fitting the observed data, which under model-form "
     "error is not the same as predicting the load you care about.")

figure("f5_funnel.png",
       "Figure 5. The agentic remodeling funnel. 151 candidate FEM rebuilds (left, screened by a "
       "cheap proxy score) were reduced to ~30 full solves, then ~10 model classes, then one "
       "winner. Right: the cheap proxy score vs the full solve score — the proxy is only loosely "
       "predictive, so screening itself adds noise. Source: composite model-selection study "
       "(2026-07-02); checker YELLOW 57/6/0.")

figure("f6_evidence.png",
       "Figure 6. The model the evidence preferred did not win on new data. Each point is a "
       "candidate model class; height is its Bayesian evidence (higher = better explains the "
       "observed data), shown for three prior widths. The winner (‘rand10’) is a robust top by "
       "evidence — yet on held-out prediction it did not beat the original model. Evidence ≠ "
       "held-out skill. Source: composite model-selection study (2026-07-02); checker YELLOW 57/6/0.")

para("Result 3b — Model-form edits DO move held-out predictions, but a smart agent is no better "
     "than random at finding them. ", bold=True, space_after=2)
para("This is the most encouraging result of the remodeling work, and it corrects an earlier "
     "conclusion. When we gave the agent genuine structural freedom and scored strictly on "
     "held-out data (Figure 7), four different kinds of model-form change — element formulation, "
     "connectivity, mesh density, and geometry — each cleared the noise bar (for example, "
     "element-formulation edits gave +0.071 ± 0.012, about six times the noise). So remodeling is "
     "not powerless: the right structural change genuinely improves out-of-sample prediction, and "
     "the single best edit we ever found added zero degrees of freedom and zero mass. But the "
     "agent’s targeted search was statistically tied with a fair random search (top row, "
     "−0.008 ± 0.018): the payoff came from the freedom to change model form, not from the "
     "agent’s cleverness in aiming.")

figure("f7_modelform.png",
       "Figure 7. Model-form edits clear the bar; the agent does not beat random. Each row is a "
       "pre-registered comparison; the diamond is the held-out improvement over the tuned baseline "
       "with ±1 standard-error bars, dots are the four hidden-drive folds. Four model-form "
       "families (element formulation, connectivity, mesh, geometry) each clear the +1-standard-"
       "error bar [MET] — remodeling genuinely helps. But the top row, agent-best minus random-best, "
       "is −0.008 ± 0.018 [not met]: a targeted agent ties an equal-budget random search. "
       "Source: model-form pilot (2026-07-16); checker GREEN 12/0/0 on integrity "
       "(science: model-form-helps MET, agent-beats-random not met).")

para("Reading Section 3 together. ", bold=True)
para("Agents can now propose real, useful model changes, and model-form freedom is where the "
     "held-out gains live. What is still missing is (i) a selection signal that tracks held-out "
     "prediction rather than in-sample evidence, and (ii) an agent search that reliably beats "
     "random — which today it does not. Both are addressable, and Section 4 lays out how.")

doc.add_page_break()

# =====================================================================================
# SECTION 4 — WHY LIMITED SUCCESS; GAPS; FUTURE WORK
# =====================================================================================
h("4. Why success was limited — and what would unlock it", 1)

h("4.1 The two physical walls", 2)
para("Model-form error dominates. ", bold=True, space_after=2)
para("Everywhere we look, the residual is a model-shape error, not a wrong number. The FEM gets "
     "resonant frequencies right and the between-peak amplitudes and shapes wrong; on our second, "
     "deliberately-worse structure (Section 4.4) the held-out prediction errors are 4.5–10% "
     "against a 0.7% best-possible floor — an order of magnitude gap that no parameter update "
     "closes. Updating a parameter cannot fix a missing or mis-structured piece of physics.")

para("Damping and mode shape are confounded and under-identified. ", bold=True, space_after=2)
para("Response amplitude depends on damping and mode shape together, and the available data cannot "
     "separate them. Figure 8 makes this precise: the information the data carry about the "
     "amplitude parameters sits far above the prior (the parameters are locally over-identified), "
     "yet the posterior is multi-modal — many different parameter combinations explain the data "
     "equally well. That is the technical fingerprint of confounding: the data are informative but "
     "point to several answers at once, so no single “correct” damping/shape split exists to be "
     "found. With one drive point and one vertical sensor, the vertical (drumhead) shapes are "
     "simply unmeasured, and their amplitude is set by assumption (Figure 2D).")

figure("f8_identifiability.png",
       "Figure 8. The amplitude parameters are informative but confounded. Each point is one "
       "combination of the amplitude parameters, ranked by how much information the data carry "
       "about it (vertical axis, log scale); all nine sit far above the prior line — so the data "
       "are not weak. Yet fits land in several different parameter basins that match the data "
       "equally well (multi-modal posterior). Informative-but-multi-modal = confounding, not a "
       "solver bug: there is no unique damping/shape split to recover. "
       "Source: full-spectrum FRF study (2026-07-14); the identifiability sub-result was confirmed "
       "in the exact-evidence follow-up (checker GREEN 12/0/0).")

h("4.2 Technical gaps (methodology to build)", 2)
bullet("A selection score that tracks held-out prediction. ",
       "Bayesian evidence rewards explaining the observed data; under model-form error that is not "
       "the same as predicting the design load. We need a model-class selection criterion built "
       "around held-out predictive skill on the quantity of interest.")
bullet("An agent search that beats random. ",
       "Today a targeted agent ties an equal-budget random search. The remodeling loop needs a "
       "verifiable feedback signal (a CLI the agent calls to score a candidate against held-out "
       "data and get back structured, physics-aware feedback) so proposals are steered, not "
       "guessed — this is the harness-design problem, not a physics problem.")
bullet("Discrepancy models that respect the physics of the gap. ",
       "The honest twins widen but do not sharpen; a discrepancy term informed by where the model "
       "is structurally weak (rather than a generic smooth correction) could tighten the band "
       "without losing coverage.")

h("4.3 Knowledge gaps (what we do not yet understand)", 2)
bullet("When is remodeling worth it? ",
       "We have shown model-form freedom can help, but not which diagnosis reliably points to the "
       "right kind of edit. We lack a principled map from “where the model disagrees” to "
       "“which structural change to make.”")
bullet("How to score honesty and skill together. ",
       "Our success measures are strict but bespoke. Turning them into a standard, reusable "
       "scorecard for Bayesian FEM updating is itself an open contribution.")

h("4.4 Data gaps (the binding limit)", 2)
para("Repeatedly, the wall is the data, not the modeling effort. The vertical load is wide because "
     "one sensor cannot see the drumhead shapes; the damping cannot be updated because ~2 Hz "
     "resolution cannot resolve a 0.3% damped peak; the sideways loads are trustworthy precisely "
     "because the sensor did see those modes. Concretely, the measures point to specific, "
     "affordable next tests: about a dozen well-placed plate sensors would cut the vertical load "
     "band by roughly a third, and longer time records would let damping be identified at all. The "
     "value of the strict success measures is that they say where the next test dollar buys the "
     "most — a pre-test design output, not just a post-mortem.")

h("4.5 Future work", 2)
para("Two concrete tracks follow directly:", space_after=2)
bullet("Refine the methods on a harder, less-correlated structure. ",
       "We have a second FEM-plus-data set (the MPL test stand) whose model is deliberately worse, "
       "so there is more headroom for updating and remodeling to show a real gain. A first "
       "existing-data-only pass (Figure 9) confirms the same diagnosis — held-out errors 4.5–10% "
       "against a 0.7% floor, so model-form error dominates and parameter updates add no value — "
       "and it is data-starved (one sensor). This is where the agentic remodeling loop, once it "
       "has a held-out-tracking selection score and a working feedback CLI, should be proven.")
bullet("Publish the success measures and the honest limits. ",
       "The strict, honesty-first scorecard and the documented walls (model-form error; "
       "damping/shape confounding; the evidence-≠-held-out gap; the promise and current ceiling "
       "of agentic remodeling) are a publishable contribution on their own, independent of a "
       "headline accuracy win.")

figure("f9_mpl.png",
       "Figure 9. The next, harder dataset (MPL test stand). Observed response peaks (black) vs "
       "five candidate models’ predictions (colors), across five held-out measurement families. "
       "The models miss many observed peaks — most starkly the valve path (bottom), where the "
       "ensemble misses about ten of eleven observed features — the same model-form gap as "
       "ShockSat, on a worse model with more headroom. It is also data-starved (one sensor). "
       "Source: MPL existing-data-only study (2026-07-20); checker YELLOW 16/2/0 "
       "(existing-data-only, no external validation).")

# =====================================================================================
# APPENDIX — PROVENANCE
# =====================================================================================
doc.add_page_break()
h("Appendix. Figure provenance and checker status", 1)
para("Every figure is an unaltered copy of a figure from the study named below, each of which "
     "passed our figure-quality and honesty checks. “Checker” is the study’s automated "
     "pass/withhold status, copied verbatim. GREEN = criteria met and integrity intact; YELLOW = a "
     "documented, non-fatal shortfall (often a pre-registered “claim not supported” outcome, "
     "honestly reported), never presented as success.", size=10, color=GREY)

rows = [
    ("Fig", "Source study", "Checker (verbatim)"),
    ("1, 2", "ShockSat net-CG method selection (2026-07-01)", "GREEN 22/0/0"),
    ("3", "ShockSat FRF-updating comparison (2026-06/07)", "reused figure; median corr 0.27→0.34 on-figure"),
    ("4", "FRF-domain damping updating (2026-07-10)", "YELLOW 19/2/0 (pre-registered claim not supported)"),
    ("5, 6", "Composite model-class selection (2026-07-02)", "YELLOW 57/6/0"),
    ("7", "Model-form pilot (2026-07-16)", "GREEN 12/0/0 integrity; model-form MET, agent-beats-random not met"),
    ("8", "Full-spectrum FRF study (2026-07-14); confirmed in exact-evidence follow-up", "GREEN 12/0/0 (follow-up)"),
    ("9", "MPL existing-data-only conditional ensemble (2026-07-20)", "YELLOW 16/2/0"),
]
tbl = doc.add_table(rows=0, cols=3)
tbl.style = "Light Grid Accent 1"
for i, (a, b, c) in enumerate(rows):
    cells = tbl.add_row().cells
    cells[0].text, cells[1].text, cells[2].text = a, b, c
    if i == 0:
        for cell in cells:
            for pp in cell.paragraphs:
                for rr in pp.runs:
                    rr.bold = True

para("")
para("Reproduce this document: python3 code/make_report.py  (needs python-docx). "
     "All source studies are replayable from their own run_all.sh. This summary adds no new "
     "computation.", size=9, italic=True, color=GREY)

doc.save(str(OUT))
print(f"wrote {OUT}")
