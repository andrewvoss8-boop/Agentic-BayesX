#!/usr/bin/env python3
"""Build the self-contained ShockSat Bayesian FEM/statFEM progress report.

This is a presentation-only synthesis for Ilias Bilionis. Numerical results are
copied from checker-backed study packets; no inference is performed here.
"""
from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from make_report_revised import (
    BLUE,
    GREY,
    INK,
    NAVY,
    add_bullet,
    add_figure,
    add_heading,
    add_paragraph,
    add_table,
    configure_document,
    rgb,
)


HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
OUT = ROOT / "ShockSat_Bayesian_FEM_and_StatFEM_progress_update_working_twin_revision.docx"
AUDIT = json.loads((ROOT / "out" / "advisor_audit_metrics.json").read_text())


def add_equation(
    doc: Document,
    text: str | list[tuple[str, str]],
    note: str | None = None,
) -> None:
    """Add an equation with true Word superscript/subscript formatting.

    A list item is ``(text, style)`` where style is ``normal``, ``sub``, or
    ``sup``.  This avoids relying on plain underscore/caret strings or on
    Unicode glyph fallback for mathematical subscripts.
    """
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(2 if note else 6)
    p.paragraph_format.keep_together = True
    parts = [(text, "normal")] if isinstance(text, str) else text
    for token, style in parts:
        run = p.add_run(token)
        run.font.name = "Cambria Math"
        run.font.size = Pt(10.5)
        run.font.color.rgb = rgb(NAVY)
        run.font.subscript = style == "sub"
        run.font.superscript = style == "sup"
    if note:
        q = doc.add_paragraph()
        q.alignment = WD_ALIGN_PARAGRAPH.CENTER
        q.paragraph_format.space_after = Pt(6)
        q.paragraph_format.keep_together = True
        r = q.add_run(note)
        r.font.name = "Arial"
        r.font.size = Pt(8.4)
        r.font.italic = True
        r.font.color.rgb = rgb(GREY)


def add_numbered_point(doc: Document, number: str, lead: str, body: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.18)
    p.paragraph_format.first_line_indent = Inches(-0.18)
    p.paragraph_format.space_after = Pt(5)
    n = p.add_run(f"{number}. ")
    n.bold = True
    n.font.color.rgb = rgb(BLUE)
    h = p.add_run(lead)
    h.bold = True
    p.add_run(body)


def add_reference(doc: Document, text: str) -> None:
    p = add_paragraph(doc, text, size=8.3, space_after=3)
    p.paragraph_format.first_line_indent = Inches(-0.2)
    p.paragraph_format.left_indent = Inches(0.2)


def set_report_footer(doc: Document) -> None:
    for section in doc.sections:
        p = section.footer.paragraphs[0]
        p.clear()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run("ShockSat Bayesian FEM / statFEM progress report  |  ")
        run.font.name = "Arial"
        run.font.size = Pt(8)
        run.font.color.rgb = rgb(GREY)
        begin = OxmlElement("w:fldChar")
        begin.set(qn("w:fldCharType"), "begin")
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = "PAGE"
        end = OxmlElement("w:fldChar")
        end.set(qn("w:fldCharType"), "end")
        run._r.append(begin)
        run._r.append(instr)
        run._r.append(end)


def build() -> None:
    doc = Document()
    configure_document(doc)
    set_report_footer(doc)

    # Report cover: no decision-request masthead and no research traffic lights.
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("Evaluating Bayesian FEM Updating and Response-Level StatFEM on ShockSat")
    r.font.name = "Arial"
    r.font.size = Pt(24)
    r.font.bold = True
    r.font.color.rgb = rgb(NAVY)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(13)
    r = p.add_run("Methods, results, gaps, the model-form pivot, and a path to closure")
    r.font.name = "Arial"
    r.font.size = Pt(13.5)
    r.font.color.rgb = rgb(BLUE)

    add_paragraph(doc, "Progress update for Ilias Bilionis", size=10.4, color=NAVY, space_after=1)
    add_paragraph(doc, "Andrew Voss  |  21 July 2026", size=9.2, color=GREY, space_after=12)

    add_heading(doc, "Why I am sending this now", 1)
    add_paragraph(
        doc,
        "The last plan I sent you proposed a dynamic statistical finite-element (statFEM) twin of a "
        "small aerospace structure: learn uncertain properties from vibration data, represent model "
        "discrepancy, and propagate the result to a load quantity of interest.",
    )
    add_paragraph(
        doc,
        "I moved to NASA's public ShockSat structure because it supplies a real spacecraft-like article, a correlated FEM, "
        "modal-survey data, and impact-hammer response data [1]. This report explains what I built, what the "
        "evaluation showed, why it does not yet support industry use, and why the work moved from parameter "
        "updating toward model-form remodeling.",
    )
    add_paragraph(
        doc,
        "I have less than one month left in my PSL studies. The final section asks you to approve or change "
        "a concrete closeout bar and to advise which scientific conclusions are worth preserving.",
        size=10.5,
        color=NAVY,
        space_after=8,
    )

    add_heading(doc, "Executive summary", 1)
    add_numbered_point(
        doc, "1", "A real evaluation was built. ",
        "The work progressed from Bayesian modal updating to response-level statFEM, load prediction, "
        "whole-frequency-response likelihoods, and finally controlled model-form edits. Each stage used held-out "
        "data or an explicit comparator so that a converged fit was not mistaken for validation.",
    )
    add_numbered_point(
        doc, "2", "The original industry-use goal was not achieved. ",
        "Model-to-test mismatch was much larger than repeat-test noise, no response-level ShockSat posterior "
        "jointly inferred a whole-FRF discrepancy, converged, and supported the intended load claim, and the dataset represents one article rather "
        "than build-to-build variability. The resulting load intervals are conditional predictions, not "
        "validated flight-load products. They are too wide and inaccurate for industry use.",
    )
    add_numbered_point(
        doc, "3", "The main gap is model form, not a missing optimizer. ",
        "Stiffness parameters improved natural frequencies and moved resonance locations, but they could not "
        "repair channel-dependent FRF shape and participation errors. A discrepancy term can stop the method "
        "from becoming overconfident; it cannot make a structurally wrong FEM sharp enough to beat the current-"
        "practice baseline used here: smooth the FEM FRF and add 6 dB.",
    )
    add_numbered_point(
        doc, "4", "Testing model-form freedom produced a narrower positive result and a useful negative result. ",
        "Controlled changes to connectivity, mesh, element formulation, and geometry each improved held-out "
        "FRF prediction. However, the language-model-guided search did not outperform an equal-budget random "
        "search. The evidence supports model-form freedom as a lever, not agent superiority.",
    )

    doc.add_page_break()
    add_heading(doc, "1. Original objective and what was actually achieved", 1)
    add_table(
        doc,
        ["Original goal", "What this project delivered", "What remains unresolved"],
        [
            ["Build and evaluate dynamic statFEM on a realistic aerospace structure", "A real-data ShockSat evaluation spanning modal features, FRF curves, response envelopes, and a net-CG load proxy", "No direct measured net-CG force and no new purpose-built tray experiment"],
            ["Learn physical properties from vibration data", "A converged nine-group modal-frequency posterior; posterior SD/prior SD ranged from 0.13 to 1.07", "Contraction under one likelihood is not per-parameter identifiability; the full nine-group strain-energy/Fisher decomposition was not completed"],
            ["Represent model discrepancy without posterior collapse", "Output discrepancy widened predictions where the FEM missed the data and exposed the model-error floor", "Discrepancy and physical parameters remain confounded; wide intervals are not automatically useful"],
            ["Produce a credible engineering load", "Direction-specific conditional bands and held-out response checks for two shear directions", "Normal load had no direct answer key; even shear is an indirect response-based check"],
            ["Suggest improvements", "A model-form pilot, resolution diagnosis, observability gaps, and test-design requirements", "A final deliberate calibration study or new experiment has not been completed"],
        ],
        [2500, 3400, 3260],
        font_size=7.9,
    )
    add_paragraph(
        doc,
        "Here, evaluation means testing whether the implemented method is internally correct, samples its "
        "posterior, and predicts held-out responses better than named baselines. Validation would require "
        "evidence that the model predicts the intended real-world quantity accurately enough for its proposed "
        "use—most importantly, a measured net-CG load or an equivalent answer key over relevant configurations. "
        "The project completed much of the evaluation; the available data cannot complete that validation.",
        size=10.3,
        color=NAVY,
    )
    add_paragraph(
        doc,
        "The result therefore matches the evaluation objective better than the original validation objective. "
        "It establishes where the approach works, where it becomes non-identifiable or computationally unstable, "
        "and which changes are likely to matter. It does not establish an industry-ready digital twin.",
        size=10.3,
        color=NAVY,
    )

    add_heading(doc, "2. Testbed and data", 1)
    add_figure(
        doc,
        "fig0_shocksat1_nasa.jpg",
        "Photograph of the instrumented ShockSat1 satellite-like sheet-metal test article. The tall free-free test structure has bolted joints, bulkheads, struts, material changes, and attached accelerometer cables.",
        "ShockSat1 test article. Source and released data: NASA Engineering and Safety Center Academy, "
        "https://nescacademy.nasa.gov/workshops/ShockSat [1].",
        width=2.0,
    )
    add_paragraph(
        doc,
        "ShockSat1 is a NASA public-domain, satellite-like sheet-metal structure with bolted joints, "
        "bulkheads, struts, material changes, a correlated FEM, hammer tests, and pyrotechnic-shock tests [1]. "
        "The study used the standalone structure, not the proposed coupled tray. ShockSat was a practical way "
        "to test the method on real model-to-hardware disagreement before committing the remaining time and "
        "resources to a new physical test campaign.",
    )
    add_table(
        doc,
        ["Item", "What was available", "How it entered this work"],
        [
            ["Finite-element model", "67,683 nodes; approximately 399,510 active structural degrees of freedom before modal reduction", "Assembled and reduced to a 74-mode basis for repeated eigensolutions and FRF prediction"],
            ["Modal survey", "33 measured free-free modes; 76 accelerometer nodes and 132 measured degrees of freedom", "18 calibration-clean modes at or below 222 Hz were paired to FEM modes"],
            ["Repeatability", "Nine repeat modal runs on the same article", "Estimated test-to-test frequency noise; not build-to-build variability"],
            ["Impact-hammer response", "Five drives and roughly 111 usable response channels over 45–260 Hz", "FRF fitting, held-out-drive checks, and response-based checks on the load proxy"],
            ["Spectral resolution", "Approximately 2 Hz line spacing in the inherited FRFs", "Adequate for broad FRF shape; inadequate for resolving the smallest damping ratios"],
            ["Missing observation", "No direct net-CG force measurement", "Makes the load result a conditional model prediction rather than direct validation"],
        ],
        [2100, 3650, 3410],
        font_size=7.9,
    )
    add_paragraph(
        doc,
        "Data scope matters. The work contains multiple impacts and drive locations on one hardware article. "
        "It does not learn flight-to-flight, build-to-build, or assembly-to-assembly variability, and it does "
        "not identify unknown operational forcing from flight data.",
        italic=True,
        size=9.3,
        color=GREY,
    )

    add_heading(doc, "3. Statistical and mechanical formulation", 1)
    add_heading(doc, "3.1 The intended statFEM model", 2)
    add_paragraph(
        doc,
        "At a circular frequency ω (radians per second), the deterministic frequency-domain FEM solves",
    )
    add_equation(
        doc,
        [("[−ω", "normal"), ("2", "sup"), (" M(θ) + iω C(θ) + K(θ)] u(ω; θ) = f(ω)", "normal")],
        "M, C, K: mass, damping, and stiffness; u: response; f: applied force; θ: uncertain physical parameters.",
    )
    add_paragraph(
        doc,
        "The statFEM idea is to treat the observation as the sum of an FEM-based prediction, model "
        "misspecification, and measurement noise [5,6]:",
    )
    add_equation(
        doc,
        [("y(ω) = P u(ω; θ) + δ(ω) + ε(ω)", "normal")],
        "P maps FEM degrees of freedom to sensors; δ is model discrepancy; ε is measurement noise.",
    )
    add_paragraph(
        doc,
        "A hierarchical Bayesian model assigns prior distributions to θ and to discrepancy hyperparameters ηδ, "
        "which control discrepancy size and correlation, then conditions them on the observed data:",
    )
    add_equation(
        doc,
        [("p(θ, η", "normal"), ("δ", "sub"), (" | y) ∝ p(y | θ, η", "normal"),
         ("δ", "sub"), (") p(θ) p(η", "normal"), ("δ", "sub"), (")", "normal")],
        "Posterior = likelihood × prior, normalized. A predictive load integrates over remaining uncertainty.",
    )
    add_equation(
        doc,
        [("p(q", "normal"), ("*", "sup"), (" | y) = ∫ p(q", "normal"), ("*", "sup"),
         (" | θ, δ) p(θ, δ | y) dθ dδ", "normal")],
        "q* is a future or unmeasured engineering quantity of interest, such as a net-CG force spectrum.",
    )
    add_paragraph(
        doc,
        "This decomposition follows the computer-model calibration literature [6,7] and the statFEM "
        "formulation [5]. The important warning is also established in that literature: a flexible discrepancy "
        "term can explain the same residual as a parameter change. Prediction may remain useful while physical "
        "parameter identification becomes weak or biased [7]. Orthogonal discrepancy constructions address "
        "part of this confounding by restricting the discrepancy away from the parameter-sensitivity space [8]. "
        "That construction is cited as a plausible improvement; it was not implemented in the ShockSat runs.",
    )

    add_heading(doc, "3.2 The implemented modal Bayesian update", 2)
    add_paragraph(
        doc,
        "The repeated large eigensolve was reduced to 74 mass-normalized modes. Nine dimensionless stiffness "
        "multipliers scaled physically grouped contributions to the reduced stiffness matrix:",
    )
    add_equation(
        doc,
        [("K", "normal"), ("r", "sub"), ("(θ) = A", "normal"), ("fix", "sub"),
         (" + Σ", "normal"), ("g", "sub"), (" θ", "normal"), ("g", "sub"),
         (" A", "normal"), ("g", "sub"), (",        M", "normal"), ("r", "sub"),
         (" = I", "normal")],
    )
    add_paragraph(
        doc,
        "The statement Mr = I is a coordinate convention: the reduced basis is mass-normalized. It does not "
        "mean that physical mass is an identity matrix. The substantive modeling choice was to keep the "
        "delivered FEM mass distribution fixed and infer no continuous mass parameter in this posterior. "
        "Later model-form screens included discrete mass/hardware candidates, but they are separate model classes.",
        size=9.3,
        color=GREY,
    )
    add_equation(
        doc,
        [("log f", "normal"), ("meas,m", "sub"), ("  ∼  Normal(log f", "normal"),
         ("pred,m", "sub"), ("(θ), σ", "normal"), ("f", "sub"), (")", "normal")],
        "The likelihood used paired modal frequencies; σf is a fractional residual/discrepancy scale.",
    )
    add_table(
        doc,
        ["Bayesian component", "Implemented choice", "Interpretation / limitation"],
        [
            ["Unknown parameters", "Nine stiffness multipliers θg and frequency residual scale σf", "Mass, geometry, mesh, element formulation, pairing, and modal damping were fixed in this stage"],
            ["Stiffness prior", "θg ∼ LogNormal(0, 0.25); central 95% interval 0.613–1.632", "Positive, deliberately wide around the delivered FEM because NASA had hand-tuned joint properties; width 0.15/0.40 sensitivity was also run"],
            ["Residual-scale prior", "σf ∼ HalfNormal(0.05)", "Relative log-frequency error; the same-article replicate floor was 0.30% median and 0.93% at p90, so posterior scale above about 1% was treated as model discrepancy"],
            ["Data in likelihood", "18 paired modal frequencies", "Mode shapes/MAC informed pairing and sensitivity checks, not the headline likelihood"],
            ["Prediction checks", "Six-mode-band holdout and leave-one-mode-out runs", "Tests prediction beyond the fitted modes, but does not validate FRF amplitude or force"],
        ],
        [2300, 3100, 3760],
        font_size=8.0,
    )

    add_heading(doc, "3.3 NUTS and convergence checks", 2)
    add_paragraph(
        doc,
        "The default sampler was the No-U-Turn Sampler (NUTS), a gradient-based Hamiltonian Monte Carlo "
        "method [9]. Every reported run used at least four chains and was checked over all sampled variables "
        "with rank-normalized R-hat, effective sample size (ESS), and divergent transitions [10]. The project "
        "thresholds were maximum R-hat ≤ 1.05, minimum ESS ≥ 200, and divergence fraction < 2%.",
    )
    add_table(
        doc,
        ["Run", "Settings", "Worst diagnostic", "What can be claimed"],
        [
            ["All 18 modal frequencies", "1,000 warmup + 1,000 retained draws per chain; target acceptance 0.90; tree depth 8", "R-hat 1.022; ESS 232; 0 divergences", "The reported modal posterior cleared the project thresholds"],
            ["Six modes fitted / 12 predicted", "2,000 + 2,000 draws; tree depth 10", "R-hat 1.076; ESS 63; 0 divergences", "Prediction coverage is descriptive; the posterior was not converged"],
            ["Leave one mode out", "18 separate fits", "R-hat 2.503; ESS 2.5; 0 divergences", "Wide 18/18 coverage cannot be called validation"],
            ["Whole-FRF likelihood", "Complex/high-dimensional response likelihood", "R-hat as high as 360.6; ESS about 2", "No trustworthy full-spectrum posterior intervals"],
        ],
        [2200, 2940, 1900, 2120],
        font_size=7.7,
    )
    add_paragraph(
        doc,
        "Transitional Markov chain Monte Carlo (TMCMC) [14] was used as a documented escalation for a bounded "
        "whole-FRF comparator after NUTS failed. The table below keeps three different posterior pathologies "
        "separate; they should not all be called multimodality or sampler failure.",
        size=9.3,
        color=GREY,
    )
    add_table(
        doc,
        ["Exact run and target", "Computation and stored diagnostic", "Limited conclusion"],
        [[row["run"] + "\n" + row["target"], row["sampler"] + "\n" + row["diagnostic"], row["finding"]]
         for row in AUDIT["posterior_bookkeeping"]],
        [3100, 3150, 2910],
        font_size=7.4,
    )
    add_paragraph(
        doc,
        "Raw draws exist for the modal and displayed whole-FRF NUTS runs. The reportable IFT and M2 artifacts "
        "retain run summaries, not raw TMCMC populations, so I did not reconstruct trace or pair plots from "
        "information that was not stored.",
        italic=True,
        size=8.8,
        color=GREY,
    )

    add_heading(doc, "3.4 Bayesian methods tried and what each one established", 2)
    add_paragraph(
        doc,
        "The project did not test one generic 'Bayesian update.' It tested different observables, residual "
        "models, discrepancy locations, and posterior computations. The table separates a method that learned "
        "frequencies from one that attempted to learn an entire FRF, because they make different conditional-"
        "independence and identifiability assumptions.",
    )
    add_table(
        doc,
        ["Method / literature link", "Data and likelihood", "Discrepancy and prior", "Inference / result", "Claim limit"],
        [
            ["Modal-frequency update (Beck framework [4])", "18 paired natural frequencies; independent Gaussian log-frequency residuals", "Nine positive stiffness scales: log θg ~ N(0,0.25²); σf ~ HalfNormal(0.05)", "NUTS converged on all 18 modes: R-hat 1.022, ESS 232, 0 divergences; contraction varied strongly by group", "Only response-independent ShockSat posterior that converged; does not test FRF amplitude, participation, or load"],
            ["L5 modular predictive twin", "Modal-frequency posterior propagated to held-out sensor FRFs", "Observed-channel residual scatter supplies a marginal log-amplitude discrepancy after the parameter fit", "The modal NUTS stage converged in every retained split; held-out coverage was near 0.9, but total intervals were roughly 30–38 dB wide", "A two-stage predictive construction: calibrated but not sharp; not a jointly converged whole-FRF StatFEM posterior"],
            ["Frequency + MAC / shape variants", "Natural frequencies plus modal assurance criterion (MAC), or shape residuals", "Same stiffness prior; shape-error scales inferred or profiled", "Adding MAC did not improve held-out ShockSat delivery; near-degenerate modes made individual-vector gradients fragile", "MAC is useful for pairing/subspaces but was not an amplitude solution"],
            ["Peak / damping features (Das–Debnath lens [17])", "Selected resonance frequency, complex modal information, or narrow-band damping features", "Positive modal quantities; nuisance residues marginalized", "Synthetic latent-complex-mode test avoided 429 eigh-through divergences; ShockSat damping was unresolved on the ~2 Hz grid", "Good near-degeneracy lesson; not a successful ShockSat damping posterior"],
            ["Whole log-magnitude FRF, iid residual", "All selected channel × frequency bins; conditionally independent Gaussian residuals", "θ prior unchanged; one drive-level gain; iid noise inferred", "ShockSat chains occupied separated high-probability regions; frequency-bin dependence makes the iid likelihood scientifically doubtful", "No usable posterior interval; this is distinct from the separate freq+MAC evidence result"],
            ["Schneider correlated complex/log-FRF discrepancy [13]", "Dense FRF residual correlated across frequency and sensors", "Correlation length, magnitude/phase scale, and space–frequency split", "Synthetic structural-error test: R-hat 1.002, ESS 1,328, 100% interleaved holdout and ~7× tighter than iid; extrapolation coverage 57%. The faithful ShockSat target did not converge", "Promising covariance model; the positive coverage result is not a ShockSat posterior"],
            ["IFT physics-in-prior comparator", "Whole ShockSat log|H|; field variance derived from dynamic equilibrium", "Four stiffness scales use lognormal prior; learned physics-trust β with log prior centered by the forward model; σmeas fixed 0.15", "TMCMC reproduced across four populations per split; peak-QOI coverage 0.97 and better peak proper scores than modal L5", "β was bounded but reduced ~246×; band-GRMS over-widened; one hit / one drive"],
            ["Free output-discrepancy statFEM (M2 / F(k))", "Whole log|H| or propagated load spectrum", "Frequency-correlated output error with learned or calibrated amplitude", "Free σd was boundary-seeking and not stably identified in whole-FRF inference; propagated F(k) retained coverage but produced load bands 1.508–2.526× the FEM+6 dB widths", "Coverage-protecting, not sharp; discrepancy and θ are confounded"],
            ["Hardened Beck/Au/Vanik modal-shape field", "Global modal-survey frequencies and shapes; impact channels held out only for prediction", "Shape field φi = eki + 0.3 Prawi; observed-channel QOI discrepancy added modularly", "The 12-mode calibration converged (R-hat 1.004, ESS 2,384, 0 divergences) and produced held-out predictive bands", "A converged modal/shape calibration with modular output discrepancy; not joint whole-FRF StatFEM and not a new-build validation"],
            ["Older exact-basis Beck whole-FRF target", "45–500 Hz held-out-drive amplitude target", "Field mean retained; no reportable posterior draws", "NUTS did not converge (R-hat 13.95, ESS about 2)", "A separate failed target; it must not be used to erase the later converged modal-shape result"],
            ["Sequential response statFEM", "Four drives and held-out sensor responses", "Fixed/propagated parameter prior plus response discrepancy", "Best residual GRMS ratio 2.07 versus FEM+6 dB; only 18.8% clean channel wins", "Shows honest widening without engineering replacement value"],
            ["Evidence / model-class comparison", "Analytic statFEM evidence on matched squared frequencies + MAC at each θMAP; type-II ML residual scales and equal two-hyperparameter BIC adjustment", "Prior-width sweep σlogθ = 0.15, 0.25, 0.40", "+54.02 log-evidence winner stayed top across the sweep but failed held-out QOI delivery; amplitude-screen rank correlation was −0.3 only at the declared 0.25 width", "The +54 result is not from the iid whole-FRF likelihood and is conditional on this evidence target"],
        ],
        [1600, 1900, 1900, 2140, 1600],
        font_size=6.55,
    )

    add_heading(doc, "4. Evaluation sequence", 1)
    add_paragraph(
        doc,
        "The project did not consist of one final model. It was a sequence of increasingly demanding tests. "
        "Each stage asked whether the favorable result from the previous stage survived a more relevant "
        "observable or held-out prediction.",
    )
    add_table(
        doc,
        ["Stage", "Question and method", "Main result", "Why the next stage was needed"],
        [
            ["1. Modal Bayesian update", "Infer nine stiffness groups from 18 natural frequencies using NUTS", "Converged full-data posterior; only four groups informed", "Frequencies do not test mode participation, amplitude, or load"],
            ["2. Sequential response statFEM", "Update a response envelope across drives and held-out sensors", "Best residual GRMS ratio was 2.07 relative to FEM + 6 dB", "Uncertainty widened, but prediction was not sharper than the engineering baseline"],
            ["3. Net-CG force proxy", "Propagate modal/response uncertainty to three load directions", "Conditional bands: 1.508×, 2.301×, and 2.526× the FEM + 6 dB widths", "The force itself was not measured; direction observability differed"],
            ["4. Whole-FRF and damping", "Fit response magnitude/shape and per-mode damping", "Some deterministic correlation gain; NUTS chains occupied separated solutions and damping was below grid resolution", "Parameter values could not repair channel-specific model-form error"],
            ["5. Evidence and model classes", "Compare parameterizations under marginal likelihood and held-out scoring", "Evidence winner did not improve held-out delivery", "Model ranking under a likelihood is not the same as prediction of the downstream QOI"],
            ["6. Model-form pilot", "Permit connectivity, mesh, formulation, and geometry edits; compare agent with random", "All four classes helped; agent did not beat random", "Supports deliberate model-form work, not autonomous-agent superiority"],
        ],
        [1550, 3150, 2400, 2060],
        font_size=7.5,
    )

    add_heading(doc, "5. Results from parameter updating and statFEM", 1)
    add_heading(doc, "5.1 Modal parameters: convergence did not imply full identifiability", 2)
    add_bullet(doc, "Model-error floor: ", "The posterior median frequency-residual scale was 4.6%, compared with repeat-test frequency variation of 0.30% at the median and 0.93% at the 90th percentile. The mismatch was therefore dominated by FEM/model-form error, not measurement repeatability.")
    add_bullet(doc, "Partial learning: ", "Posterior contraction was strong for the bottom and top boxes, moderate for plates and the cross-beam, and negligible for the other five groups. This describes learning under the frequency likelihood; it is not by itself a per-parameter identifiability certificate.")
    add_bullet(doc, "Joint diagnosis: ", "Joint-group modal strain energy averaged 3.1% and peaked at 19%. A finite 50% perturbation moved frequencies by as much as 2.71%, so the joints were in the load path; their signal was mostly below the realized 4.6% discrepancy floor.")
    add_bullet(doc, "Held-out frequencies: ", "Ten of 12 band-held-out modes and 18 of 18 leave-one-mode-out cases fell inside reported intervals, but both posterior families failed the convergence gate. Their broad coverage is a warning about uncertainty width, not clean validation.")
    add_table(
        doc,
        ["Stiffness group", "Posterior median", "Posterior SD / prior SD", "Strongest posterior correlation"],
        [[row["group"].replace("_", " ").title(), f"{row['posterior_median']:.3f}",
          f"{row['posterior_sd_over_prior_sd']:.2f}",
          f"{row['strongest_abs_correlation_partner'].replace('_', ' ')} ({row['correlation']:+.2f})"]
         for row in AUDIT["modal_posterior_contraction"]["rows"]],
        [2150, 1750, 2250, 3010],
        font_size=7.4,
    )
    add_paragraph(
        doc,
        "Contraction ratio = posterior standard deviation divided by the analytic prior standard deviation on "
        "the θ scale (0.262). Values near 1 are prior-like. The nine-group modal strain-energy/Fisher analysis "
        "needed for a per-parameter identifiability claim was not completed; only the joint-group strain-energy "
        "and finite-perturbation diagnosis was completed.",
        italic=True,
        size=8.7,
        color=GREY,
    )

    add_heading(doc, "5.2 Response envelopes: calibrated width was not enough", 2)
    add_paragraph(
        doc,
        "The sequential response-level statFEM used four hammer drives, six impacts per drive, 84 mapped "
        "sensors, 76 observed channels, and eight held-out channels. For a smoothline power-spectral-density "
        "envelope E(f), GRMS(E) = sqrt(∫45–260 Hz E(f) df). The reported residual ratio was "
        "GRMS(Eseq,97.5)/GRMS(EFEM+6dB) = 2.07, where the numerator is the sequential 97.5% upper envelope "
        "and the denominator is the project incumbent FEM envelope with a +6 dB amplitude allowance. The "
        "intended acceptance value was below 1. Only 18.8% of channels were clean wins and the residual band remained about 22 dB. "
        "This showed the central limitation: a discrepancy model can enlarge uncertainty until it covers "
        "mismatch, but the resulting band may still be too wide for an engineering replacement.",
    )
    add_paragraph(
        doc,
        "+6 dB means an amplitude multiplier 10^(6/20) = 1.995. It was a project/incumbent comparator carried "
        "from the earlier response-envelope and net-CG studies, not an industry standard or measured truth. "
        "Changing that allowance changes the reported width ratios, so the absolute bands and held-out coverage "
        "must be read alongside the ratios.",
        italic=True,
        size=8.9,
        color=GREY,
    )

    add_heading(doc, "5.3 Net-CG load: what the bands do and do not mean", 2)
    add_paragraph(
        doc,
        "The net center-of-gravity (net-CG) quantity is a frequency-dependent inertial-force proxy obtained "
        "by summing modal/nodal contributions to each global direction. Compared with inspecting every local "
        "acceleration FRF, this aggregation down-weights response errors that cancel in the global inertial "
        "load and concentrates the comparison on response components that contribute to the load proxy. It "
        "does not by itself predict damage at a location. The applied scale assumed a uniform "
        "mass proxy and flat input; it was not a measured interface-force channel. The comparison below uses "
        "band width relative to the project incumbent: the nominal FEM response with a +6 dB amplitude allowance. "
        "The exact statistic is GRMS(high − low)/GRMS(highFEM+6dB − lowFEM+6dB), after one-octave smoothing over "
        "45–260 Hz. A ratio of 1.5 means the selected uncertainty band is 50% wider than that baseline, not that the "
        "load is 1.5 times a measured truth.",
    )
    add_figure(
        doc,
        "fig1_load_bands.png",
        "Three log-frequency panels show conditional net center-of-gravity load proxy bands for shear X, shear Y, and normal Z from 45 to 260 hertz. Blue curves are posterior predictive medians and 95 percent intervals; green curves are medians from a modeled plausible-truth ensemble, not measured force.",
        "Figure 1. Synthetic self-consistency stress test—not measured load validation. At each frequency, the blue band median is the "
        "50th percentile of the delivered statFEM predictive ensemble; its blue limits are the 2.5th and 97.5th "
        "percentiles. The green plausible-truth median is the 50th percentile of a separate stress-test ensemble "
        "created by perturbing the same model with pre-defined unmodeled-mode tiers. It is used only to test "
        "self-consistency; it is neither observed force nor part of the blue posterior. Source: 2026-07-01 net-CG "
        "study; five hammer drives, 45–260 Hz. The normal direction is least supported because measured modes "
        "represent only 45% of its proxy.",
        width=6.6,
    )
    add_table(
        doc,
        ["Direction", "Band width / FEM + 6 dB", "Available check", "Interpretation"],
        [
            ["Shear X", "1.508", "Reconstructed held-out response covered on all five drives", "Strongest of the three directions, but still an indirect response check"],
            ["Shear Y", "2.301", "Four of five drives covered; worst coverage 0.596", "One drive exposes a meaningful gap"],
            ["Normal Z", "2.526", "No direct normal-force answer key", "Conditional on unmeasured-mode assumptions; not validated"],
        ],
        [1600, 2050, 2800, 2710],
        font_size=8.0,
    )

    add_heading(doc, "5.4 FRFs: calibrated prediction required a large model-form term", 2)
    add_paragraph(
        doc,
        "A frequency response function (FRF) is response divided by applied force; magnitude is shown here "
        "in g/lbf. The retained L5 working twin first inferred stiffness parameters from modal frequencies with "
        "NUTS, then propagated those draws to held-out sensor FRFs. It estimated a separate marginal log-amplitude "
        "model-discrepancy scale from observed channels and transferred that scale to the held-out channels. This "
        "is a modular predictive model: the parameter posterior converged, but the discrepancy was not jointly "
        "sampled with the parameters in a whole-FRF posterior.",
    )
    add_figure(
        doc,
        "fig2_working_twin_good_bad_frf.png",
        "Two held-out accelerance FRFs compare measured data, the original FEM, and the updated posterior median. A nested blue envelope shows parameter uncertainty. A wider amber envelope adds the separately calibrated model-form discrepancy. There is no hit-quality shading or secondary axis. DAQ 20 improves after updating; DAQ 24 remains far from the data.",
        "Figure 2. Held-out channels from retained split seed 10, 45–260 Hz. Black is measured; dashed gray is the "
        "original FEM; blue is the updated posterior median. The blue 5th–95th percentile envelope propagates "
        "parameter uncertainty. The amber 5th–95th percentile envelope adds the observed-channel-estimated "
        "model-form discrepancy. Modal NUTS converged for this split (maximum R-hat 1.0012). DAQ 20's mean "
        "absolute log10-magnitude error decreases from 0.684 to 0.587. DAQ 24 remains about an order of magnitude "
        "wrong, and its held-out peak QOI is not covered. The outer envelope is a two-stage posterior-predictive interval, not evidence "
        "that a joint whole-FRF StatFEM posterior converged. Source: statfem_real_validation_20260617/out/mc_cache.npz; "
        "one ShockSat article and one main impact hit.",
        width=6.65,
    )
    add_paragraph(
        doc,
        "The distinction matters. Parameter uncertainty alone remained narrow and under-covered held-out response "
        "amplitudes. The added discrepancy improved calibration by admitting the residual model-to-test variation, "
        "but the resulting 30–38 dB QOI intervals were too wide for the intended engineering use. The separate "
        "joint whole-FRF target still failed to converge, so it remains a diagnostic rather than the source of the "
        "bands shown above. The measured median damping ratio was approximately 0.32%, while every in-band mode occupied fewer "
        "than 1.5 lines on the approximately 2 Hz grid. Damping fits repeatedly hit an artificial 5% bound. "
        "A raw-record follow-up showed that windowing and coarse resolution broadened the apparent FRF peaks; "
        "adding physical damping did not improve the held-out score (0.1931 versus 0.1969 baseline). The whole-"
        "FRF NUTS result was correspondingly non-converged. This is both a data-resolution failure and a "
        "likelihood/identifiability failure—not evidence for 5% physical damping.",
    )

    add_heading(doc, "5.5 Bayesian assumption audit: what actually limits movement and width", 2)
    add_table(
        doc,
        ["Potential explanation", "Test performed / evidence", "Judgment"],
        [
            ["The prior is too strong", "The stiffness prior has a central 95% range 0.613–1.632. A local full-FRF Fisher calculation at one solution gave eigenvalues 1,641–3.6×10^6 versus prior precision 16; prior-width sweeps were also run.", "The prior is not negligible, but local curvature is not global identifiability. It cannot rule out separated basins, likelihood misspecification, or weak raw-parameter separation."],
            ["The frequency-feature likelihood throws away needed data", "Correct. The converged likelihood used 18 frequencies and omitted channel amplitudes. Adding MAC was null for held-out delivery; adding all amplitudes produced separated chain solutions.", "Numerical stability was purchased by discarding participation/amplitude information needed by the QOI."],
            ["FRF bins are conditionally independent", "They are not. The iid whole-FRF likelihood failed. Schneider-style correlation produced calibrated, ~7× tighter in-distribution bands in a controlled structural-error test, but extrapolation still covered only 57% and the faithful ShockSat target did not converge.", "Covariance misspecification is a real contributor. ShockSat has not quantified how much a better correlated discrepancy alone would sharpen its bands."],
            ["Discrepancy is independent of, and separable from, θ", "The residual can be explained by a stiffness change or by output discrepancy. Free σd was boundary-seeking and not stably identified; bounded β in IFT was learned about 246× below nominal physics trust.", "Parameter–discrepancy confounding is active. Orthogonal discrepancy was identified in the literature but not implemented here."],
            ["The sampler merely needed more iterations", "Whole-FRF chains occupied different modes: NUTS R-hat 29–360 and ESS about 2. TMCMC converged for bounded IFT but not for free M2. Multi-start MAPs also found separated solutions.", "The failure is posterior geometry/model construction, not a cosmetic run length issue."],
            ["Damping and spectral processing are adequate", "Median ζ was 0.32%, yet each resonance had fewer than 1.5 frequency lines. Damping fits hit a 5% bound and true per-mode ζ worsened held-out score.", "Damping information is below the inherited grid/window resolution; damping estimates cannot be used to blame material physics."],
            ["The nine stiffness groups span the residual", "Finite perturbations move eigenvalues, but the converged modular twin improves DAQ 20 while DAQ 24 remains about an order of magnitude wrong. Preregistered class-mean controls for four genuine model-form families were positive.", "The tested property span does not contain all response mechanisms. This is evidence for model-form limitation after the Bayesian alternatives above are considered."],
            ["The data identify population variability", "There is one hardware article, one main impact realization in several likelihood studies, and no direct net-CG force. Repeated hits estimate same-article test noise, not build-to-build variability.", "Wide predictive bands also carry unlearned extrapolation and QOI-observability uncertainty."],
        ],
        [2100, 4100, 3060],
        font_size=7.15,
    )
    add_paragraph(
        doc,
        "Why the posterior mean does not move enough toward the FRF data: the converged posterior is driven by "
        "modal frequencies, so it can move the identifiable stiffness combinations and resonance locations but "
        "does not observe the channel-specific participation amplitudes. When amplitudes are put into the "
        "likelihood, the tested FEM/likelihood admits several separated solutions and the posterior does not "
        "converge. Leakage-safe point estimates show that extra shape freedom can move a good channel, but the "
        "bad channel remains far away. The evidence therefore points to a combination of likelihood information "
        "loss, separated whole-FRF solutions, and response mechanisms outside the nine-stiffness parameter span—not "
        "to an obviously over-tight θ prior alone.",
        size=10.2,
        color=NAVY,
    )
    add_paragraph(
        doc,
        "Why the uncertainty bands remain unusably large: the model-to-test residual is much larger than repeat "
        "noise, so any model that honestly covers held-out responses must allocate substantial variance to "
        "discrepancy. That discrepancy is confounded with θ and must also absorb unmodeled spatial participation, "
        "under-resolved damping, unobserved modes, and transfer to an unmeasured load QOI. A frequency-correlated "
        "residual can avoid some iid over-counting and may sharpen in-distribution interpolation, but the ShockSat "
        "study has not demonstrated that it can make the extrapolative load bands both narrow and calibrated.",
        size=10.2,
        color=NAVY,
    )

    add_heading(doc, "5.6 Defects found, repaired, and carried forward", 2)
    add_paragraph(
        doc,
        "Several early results were correctly challenged. The table distinguishes the original defect from the "
        "later exact repair so that a stale flaw is not mistaken for the current conclusion.",
    )
    add_table(
        doc,
        ["Original defect", "Repair / superseding evidence", "Current claim"],
        [
            ["Arm-C held-out score used one fold's shape MAP elsewhere and transplanted coefficients between incompatible reduced bases", "Four leakage-free per-fold MAP refits on each correct basis: score 0.1595; delta vs A1 +0.0458 ± 0.0361", "The numerical score is repaired. S1 is still not met because the gain misses both +0.05 and 2×SE."],
            ["Only selected winners had been exact-scored", "All 28 candidates were reranked on candidate-own exact bases: agent−random −0.0017 ± 0.0094 under screening selection and +0.0115 ± 0.0158 under exact selection", "No detectable agent advantage under either selection convention."],
            ["The wide-package net-CG port reported incompatible widths and blamed calibration", "The validated port reproduced 1.508/2.301/2.526 exactly. The earlier code had computed upper/lower envelope ratio instead of band width relative to FEM+6 dB.", "The delivered twin stands. S3 remains cannot-verify through the available mode mapping; S4 is not met because normal Z widens to 2.958."],
            ["An earlier checker certified process integrity without propagating S3/S4 science verdicts", "Later packets label checker scope and report science verdicts separately", "This report carries the scientific ceiling explicitly; checker GREEN is never used as proof that a criterion was met."],
            ["An earlier search space was too property-heavy to support a model-form claim", "The later pilot explicitly tested connectivity, mesh density, element formulation, and geometry with exact candidate scoring", "The later pilot supersedes that criticism, but selected-best and class-mean results remain separated below."],
        ],
        [2600, 3900, 2660],
        font_size=7.05,
    )

    doc.add_page_break()
    add_heading(doc, "6. Why the original goal is not industry-usable yet", 1)
    add_table(
        doc,
        ["Gap", "Evidence in this project", "Consequence"],
        [
            ["The target load was not observed", "No direct net-CG force channel; only reconstructed response checks", "Coverage of the actual engineering QOI was not measured"],
            ["The FEM error exceeds test noise", "4.6% modal residual scale versus 0.30% median repeatability", "Narrow parameter posteriors cannot be interpreted as a physically complete model"],
            ["The useful likelihoods answer different questions", "Modal-feature NUTS converged; a modular amplitude discrepancy calibrated held-out prediction but remained wide; joint whole-FRF NUTS did not converge", "No jointly inferred whole-FRF ShockSat posterior earned convergence and downstream-load support"],
            ["Parameterization is too limited", "Stiffness changes move eigenvalues but not missing connectivity, element kinematics, mesh behavior, or channel participation", "Property updating cannot repair all model-to-test discrepancy"],
            ["Damping is under-resolved", "0.32% median damping with fewer than 1.5 frequency lines per mode", "Per-mode damping estimates are processing-dominated"],
            ["Variability is incomplete", "One hardware article; leave-one-drive-out tests predict an unseen excitation location on that same article, not a new build or flight", "The posterior omits build-to-build, assembly-to-assembly, and flight variability"],
            ["Prediction bands remain wide or conditional", "Sequential residual ratio 2.07; load ratios 1.508–2.526 relative to FEM + 6 dB", "The method does not yet replace common loads margins or certification practice"],
            ["Model selection did not transfer", "A candidate gained 54.02 log-evidence over baseline but no held-out QOI improvement", "Marginal likelihood under one model/likelihood is not an engineering delivery test"],
        ],
        [2250, 3850, 3060],
        font_size=7.4,
    )
    add_paragraph(
        doc,
        "This is not evidence that statFEM is useless. Published statFEM applications show that combining "
        "an FEM prior, discrepancy, and sensor data can improve spatial prediction; for example, the bridge "
        "digital-twin study predicted strain at uninstrumented locations [11]. The ShockSat case is a harder "
        "contract: narrow-band dynamics, sharp resonances, unknown or indirect forcing, unmeasured load QOIs, "
        "and a requirement that parameter meaning survive model discrepancy. The current result shows where "
        "that extension needs new method and new data.",
    )

    add_heading(doc, "7. Why I tested model-form freedom", 1)
    add_heading(doc, "7.1 The reasoning", 2)
    add_paragraph(
        doc,
        "A parameter update searches only within the span of the existing model: scale a stiffness group, "
        "change a damping value, or adjust a mass. When the residual comes from missing load paths, incorrect "
        "element kinematics, mesh-dependent local modes, or geometry, no value of those parameters can make "
        "the model structurally correct. A discrepancy process can represent the remaining error and protect "
        "uncertainty, but it does not repair the FEM. The next logical evaluation was therefore to let the FEM "
        "model form change and test whether those changes improve held-out response.",
    )
    add_paragraph(
        doc,
        "The language-model agent was one search strategy inside this test: it read training residuals, proposed a bounded "
        "physical edit, and submitted it to deterministic validation and exact eigensolution. This did not mean "
        "the agent certified the structure or altered the acceptance criteria. Every proposal was checked for "
        "valid connectivity, positive mass/stiffness behavior, finite modes, bounded rigid-body leakage, and "
        "fair held-out scoring.",
        size=10.2,
        color=NAVY,
    )

    add_heading(doc, "7.2 What remodeling means in the current work", 2)
    add_paragraph(
        doc,
        "The outer loop chooses a discrete FEM model class: change connectivity or a joint representation, "
        "add or remove modeled hardware or mass, alter a geometry idealization, change an element formulation, "
        "or remesh a selected region. Remeshing is therefore one operator family, not a synonym for the entire "
        "method. Within each valid class, a separate Bayesian update may infer continuous stiffness, density or "
        "mass, damping, joint coefficients, nuisance quantities, and model-discrepancy quantities. Keeping these "
        "layers separate prevents a property multiplier from being presented as a model-form repair.",
    )
    add_figure(
        doc,
        "fig3_agentic_remodeling_cli.png",
        "Flowchart of the controlled agentic-remodeling candidate loop. A language-model agent selects a registered discrete model-form operator and writes candidate.json. Existing project-owned machinery builds the edit, verifies mechanics, performs continuous Bayesian updating within the class when applicable, and scores protected data splits. Structured feedback returns to the agent. A proposed remodelctl wrapper and feedback-training layer are distinguished from existing components. The agent cannot change the verifier, splits, thresholds, budgets, scoring code, or checker.",
        "Figure 3. Controlled model-form search with an agent as one proposer. Solid blue components already exist across the ShockSat pilot and reusable harness; dashed orange components are the proposed unified interface and training increment. Deterministic project code builds, verifies, updates within each class, and scores protected splits.",
        width=6.55,
    )

    add_heading(doc, "7.3 Current components versus the proposed CLI", 2)
    add_table(
        doc,
        ["Layer", "What exists now", "What is proposed next"],
        [
            ["Candidate definition", "A candidate.json specification, registered operator families, and deterministic builders", "One immutable agent-facing command-line interface, provisionally named remodelctl"],
            ["Physics and integrity", "Schema checks and validity gates for connectivity, rigid-body behavior, positive mass/stiffness behavior, units, solver success, hashes, and budgets", "Stable JSON failure codes and evidence so the agent can repair a candidate without receiving unconstrained hints"],
            ["Data discipline", "TRAIN/development/vault separation, equal-budget random or human controls, and final scoring in each candidate’s own exact model", "Commands such as status, submit, verify, diagnose, score, compare, promote, finalize, and replay behind the same frozen rules"],
            ["Agent training", "ShockSat tested one diagnosis-guided agent against equal-budget random search", "A blinded ablation: no feedback versus pass/fail versus structured diagnostics"],
        ],
        [1800, 3770, 3590],
        font_size=7.4,
    )
    add_paragraph(
        doc,
        "The unified remodelctl interface is not yet implemented. The present work has the component pieces: "
        "candidate schemas, registered operators, deterministic builders, validity gates, protected data splits, "
        "state and input hashes, budgets, controls, and exact candidate scoring. The separate MPL harness also "
        "demonstrates a restart-safe filesystem state machine and fail-closed schemas. Its Stage-0 data check "
        "stopped before a remodeling search, so it is evidence that the scaffold runs—not an MPL remodeling or "
        "posterior result.",
        size=9.5,
        color=NAVY,
    )
    add_paragraph(
        doc,
        "The feedback roles must remain separate. A hard verifier rejects invalid mechanics. A TRAIN-only "
        "diagnostic coach identifies the violated check and returns bounded evidence. A restricted development "
        "grader returns only the pre-registered score needed for selection. The vault is opened once after the "
        "rules and finalists freeze. The agent cannot modify the verifier, data split, thresholds, budgets, "
        "scoring code, or final checker.",
    )
    add_paragraph(
        doc,
        "The proposed training experiment asks whether feedback teaches useful repair rather than test-set "
        "querying. It would compare no feedback, pass/fail feedback, and structured diagnostics at equal budgets. "
        "Outcomes include valid-candidate rate, repair success, CLI calls, eigensolves, elapsed time, held-out gain "
        "over random search, false acceptance, and attempts to exploit the score or exceed the claim boundary.",
    )

    add_heading(doc, "7.4 What the completed ShockSat pilot tested", 2)
    add_bullet(doc, "Search budget: ", "60 exact candidates: three rounds × two candidates × five model classes × two tracks.")
    add_bullet(doc, "Allowed model-form classes: ", "Connectivity, mesh density, element formulation, geometry, plus controls.")
    add_bullet(doc, "Evaluation: ", "Four leave-one-drive-out folds, whole log-magnitude FRFs from 45–200 Hz, approximately 100–130 channels per fold.")
    add_bullet(doc, "Fair comparator: ", "A seeded equal-budget random track used the same edit classes and validators.")
    add_bullet(doc, "Sampler: ", "None for candidate ranking. Candidates used deterministic multi-start parameter fits and exact-basis eigensolutions because the whole-FRF posterior remained unresolved.")
    add_bullet(doc, "Held-back data: ", "A fifth +XY vault was not read during model selection.")

    add_heading(doc, "7.5 Results and meaning", 2)
    add_paragraph(
        doc,
        "The agent comparison and the model-form-class comparison answer different questions. The first tests "
        "search guidance. The second asks whether a family of genuine model changes contains useful candidates. "
        "For each family, the selected best-of-12 is exploratory and selection-biased; the class mean is the "
        "preregistered control against winner's curse.",
    )
    add_table(
        doc,
        ["Genuine model-form family", "Selected best of 12", "Class-mean control", "Reading"],
        [[row["class"].replace("_", " ").title(),
          f"{row['selected_best_delta_mean']:+.4f} ± {row['selected_best_delta_se']:.4f}",
          f"{row['class_mean_delta_mean']:+.4f} ± {row['class_mean_delta_se']:.4f}",
          "Positive class mean; selected best remains exploratory"]
         for row in AUDIT["model_form_selection"]["rows"]],
        [2350, 2200, 2200, 2410],
        font_size=7.5,
    )
    add_bullet(doc, "Agent versus random: ", "Agent minus random = −0.0077 ± 0.0177; track-mean difference = +0.0028 ± 0.0056. No detectable guidance advantage.")
    add_bullet(doc, "Selected finalist: ", "The formulation candidate retained +0.0817 ± 0.0296 after per-fold amplitude refits with zero added mass or degrees of freedom. It is still a selected finalist, not an unbiased class effect or a Bayesian posterior.")
    add_paragraph(
        doc,
        "The pivot was scientifically justified because it tested the mechanism implicated by the statFEM "
        "evaluation. Its result is deliberately narrow. Genuine model-form edits improved prediction; the "
        "agent did not choose better edits than random under the available feedback and budget. The work has "
        "therefore produced evidence for a model-form research direction, not evidence for autonomous FEM "
        "correlation. The planned follow-on formulation-calibration study is incomplete and is not reported "
        "here as a result.",
    )

    add_heading(doc, "8. What the project established", 1)
    add_paragraph(
        doc,
        "I do not want to overstate novelty. Classical FEM updating, Bayesian calibration, model discrepancy, "
        "NUTS, TMCMC, and cross-validation all predate this project [2–10,12–14]. The claims below are limited "
        "to results that the ShockSat artifacts support.",
    )
    add_numbered_point(doc, "1", "A run-specific evaluation of Bayesian FEM updating and response-level StatFEM. ", "The modal-frequency posterior converged and showed sharply unequal contraction across stiffness groups. A modular discrepancy calibrated held-out FRFs only by accepting wide intervals; the joint response-level targets and load delivery did not clear the required gates. The work separates those outcomes instead of treating a successful fit as validation.")
    add_numbered_point(doc, "2", "A quantified distinction between model-class evidence and downstream prediction. ", "The shape-inclusive +54.02 log-evidence result remained top across three prior widths but did not improve the held-out load QOI. The evidence target and the engineering decision were demonstrably different.")
    add_numbered_point(doc, "3", "A controlled test of model-form freedom and search guidance. ", "Preregistered class-mean controls were positive for connectivity, mesh, formulation, and geometry, while the agent did not beat equal-budget random search. Model-form freedom helped; agent superiority was not observed.")

    add_heading(doc, "9. Lessons I want to preserve", 1)
    add_paragraph(
        doc,
        "My current interpretation is that the original question was not wrong; it bundled too many hard "
        "claims into one demonstration and chose data that did not directly observe the final load QOI. The "
        "project was much better posed as an evaluation than as a validation or industry-deployment study.",
        size=10.4,
        color=NAVY,
    )
    add_bullet(doc, "Observability sets the ceiling. ", "A response-only holdout on one article cannot validate an unmeasured force or learn build-to-build variability, regardless of sampler sophistication.")
    add_bullet(doc, "Likelihood choice changes the question. ", "Natural frequencies are sampleable but omit participation; whole FRFs contain that information but exposed covariance, discrepancy, resolution, and global-identification problems.")
    add_bullet(doc, "Model and search effects must be separated. ", "Genuine model-form families helped in aggregate, but the agent did not select better candidates than random. The useful result is about model freedom, not automation.")

    add_heading(doc, "10. What I need help deciding in the final month", 1)
    add_paragraph(
        doc,
        "I want to stop adding open-ended experiments and close against an explicit scientific bar. I would "
        "value your judgment on four questions:",
    )
    add_numbered_point(doc, "1", "Primary thesis of the work. ", "Should I close around an evaluation of dynamic statFEM and its failure modes, use the model-form result as the main contribution, or present one combined story in which the failed prediction contract motivates the model-form experiment?")
    add_numbered_point(doc, "2", "One remaining technical task, if any. ", "Would a bounded formulation-calibration study materially strengthen the conclusion, or is the better use of the time to freeze the evidence and write? I do not want to run another study merely because the current answer is negative.")
    add_numbered_point(doc, "3", "Personal diagnosis. ", "Did I embark on the wrong problem, or did I start with a worthwhile problem whose original scope—dynamic statFEM, property identification, unknown forcing, hierarchical variability, and an industry load decision—was too broad for the available data and time?")
    add_numbered_point(doc, "4", "Research record and lab value. ", "Which parts should become the PSL report, a paper or workshop submission, reusable lab software, and a lessons-learned note? I want the record to distinguish established methods from any contribution I can reasonably claim.")

    add_heading(doc, "Proposed closeout acceptance bar—please approve or change", 2)
    add_table(
        doc,
        ["Required closeout element", "Evidence that it is complete", "Boundary that remains explicit"],
        [
            ["Modal Bayesian evaluation", "Converged 18-mode posterior, prior rationale, contraction table, joint finite-perturbation evidence, and held-out nonconvergence disclosed", "No per-parameter identifiability claim without the missing full nine-group strain-energy/Fisher analysis"],
            ["Response-level StatFEM evaluation", "Run-specific modular-L5/whole-FRF/M2/IFT diagnostics; good/bad FRF channels; exact likelihood and discrepancy assumptions", "The modular L5 interval is calibrated but wide; no trustworthy jointly inferred whole-FRF ShockSat interval and no claim that orthogonal discrepancy was implemented"],
            ["Load-QOI evaluation", "Validated 1.508/2.301/2.526 reference reproduction; S3 cannot-verify and S4 not met; +6 dB and GRMS contracts defined", "No direct net-CG force validation and no build/flight generalization"],
            ["Model-form/search result", "Exact 28/28 rerank; selected-best/class-mean separation; agent-versus-random result", "No autonomous-remodeling superiority or industry-delivery claim"],
            ["Reproducible handoff", "One evidence index, source hashes, runtimes, checkers, defect-repair ledger, and final report", "Incomplete formulation-calibration and unimplemented improvements are listed as future work, not results"],
        ],
        [2500, 4050, 2610],
        font_size=7.15,
    )
    add_paragraph(
        doc,
        "If you agree with this bar, I will spend the remaining time closing these artifacts and writing. If you "
        "do not, I need your help identifying the one missing item that would materially change the thesis rather "
        "than merely add another negative or underpowered study.",
        size=10.5,
        color=NAVY,
    )

    add_heading(doc, "11. Literature positioning", 1)
    add_paragraph(
        doc,
        "This work sits at the intersection of mature FEM updating [2,3], Bayesian structural model updating "
        "and model-class selection [4,12], computer-model calibration with explicit discrepancy [6,7], "
        "statFEM [5,11], frequency-domain Bayesian dynamics [13,17], held-out predictive evaluation [15], and "
        "modern posterior computation and diagnostics [9,10,14]. The literature supports each component. It "
        "does not, by itself, establish that "
        "their combination is identifiable, convergent, or useful for ShockSat's unmeasured load QOI; those "
        "are the questions the project evaluated.",
    )

    references = [
        "[1] NASA Engineering and Safety Center Academy. ShockSat. https://nescacademy.nasa.gov/workshops/ShockSat",
        "[2] Mottershead, J. E., and Friswell, M. I. (1993). Model Updating in Structural Dynamics: A Survey. Journal of Sound and Vibration, 167(2), 347–375. doi:10.1006/jsvi.1993.1340.",
        "[3] Mottershead, J. E., Link, M., and Friswell, M. I. (2011). The sensitivity method in finite element model updating: A tutorial. Mechanical Systems and Signal Processing, 25(7), 2275–2296. doi:10.1016/j.ymssp.2010.10.012.",
        "[4] Beck, J. L., and Katafygiotis, L. S. (1998). Updating Models and Their Uncertainties. I: Bayesian Statistical Framework. Journal of Engineering Mechanics, 124(4), 455–461. doi:10.1061/(ASCE)0733-9399(1998)124:4(455).",
        "[5] Girolami, M., Febrianto, E., Yin, G., and Cirak, F. (2021). The statistical finite element method (statFEM) for coherent synthesis of observation data and model predictions. Computer Methods in Applied Mechanics and Engineering, 375, 113533. doi:10.1016/j.cma.2020.113533.",
        "[6] Kennedy, M. C., and O'Hagan, A. (2001). Bayesian calibration of computer models. Journal of the Royal Statistical Society: Series B, 63(3), 425–464. doi:10.1111/1467-9868.00294.",
        "[7] Brynjarsdóttir, J., and O'Hagan, A. (2014). Learning about physical parameters: the importance of model discrepancy. Inverse Problems, 30(11), 114007. doi:10.1088/0266-5611/30/11/114007.",
        "[8] Plumlee, M., and Joseph, V. R. (2018). Orthogonal Gaussian process models. Statistica Sinica, 28(2), 601–619. doi:10.5705/ss.202015.0404.",
        "[9] Hoffman, M. D., and Gelman, A. (2014). The No-U-Turn Sampler: Adaptively Setting Path Lengths in Hamiltonian Monte Carlo. Journal of Machine Learning Research, 15(47), 1593–1623. https://www.jmlr.org/papers/v15/hoffman14a.html",
        "[10] Vehtari, A., Gelman, A., Simpson, D., Carpenter, B., and Bürkner, P.-C. (2021). Rank-normalization, folding, and localization: An improved R-hat for assessing convergence of MCMC. Bayesian Analysis, 16(2), 667–718. doi:10.1214/20-BA1221.",
        "[11] Febrianto, E., Butler, L., Girolami, M., and Cirak, F. (2022). Digital twinning of self-sensing structures using the statistical finite element method. Data-Centric Engineering, 3, e31. doi:10.1017/dce.2022.28.",
        "[12] Mthembu, L., Marwala, T., Friswell, M. I., and Adhikari, S. (2011). Model selection in finite element model updating using the Bayesian evidence statistic. Mechanical Systems and Signal Processing, 25(7), 2399–2412. doi:10.1016/j.ymssp.2011.04.001.",
        "[13] Schneider, R., Papaioannou, I., and Straub, D. (2022). Bayesian parameter updating in linear structural dynamics with frequency transformed data using rational surrogate models. Mechanical Systems and Signal Processing, 166, 108407. doi:10.1016/j.ymssp.2021.108407.",
        "[14] Ching, J., and Chen, Y.-C. (2007). Transitional Markov Chain Monte Carlo Method for Bayesian Model Updating, Model Class Selection, and Model Averaging. Journal of Engineering Mechanics, 133(7), 816–832. doi:10.1061/(ASCE)0733-9399(2007)133:7(816).",
        "[15] Vehtari, A., Gelman, A., and Gabry, J. (2017). Practical Bayesian model evaluation using leave-one-out cross-validation and WAIC. Statistics and Computing, 27(5), 1413–1432. doi:10.1007/s11222-016-9696-4.",
        "[16] ASME V&V 10-2019 (R2025). Standard for Verification and Validation in Computational Solid Mechanics. American Society of Mechanical Engineers. https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-solid-mechanics",
        "[17] Das, A., and Debnath, N. (2020). A Bayesian model updating with incomplete complex modal data. Mechanical Systems and Signal Processing, 136, 106524. doi:10.1016/j.ymssp.2019.106524.",
    ]
    for ref in references:
        add_reference(doc, ref)

    doc.add_page_break()
    add_heading(doc, "Appendix A. Evidence provenance and claim limits", 1)
    add_table(
        doc,
        ["Report evidence", "Checker-backed source", "Claim limit carried into this report"],
        [
            ["Modal Bayesian model, priors, contraction, and NUTS", "shocksat_fem_modal_twin_20260609 + advisor_audit_metrics.json", "Only the full 18-mode posterior converged; contraction is not a per-parameter identifiability certificate"],
            ["Sequential response statFEM", "shocksat_sequential_statfem_20260623", "Fixed-prior sequential MAP for most arms, not a full hierarchical posterior"],
            ["Net-CG load proxy and direction-specific bands", "shocksat_netcg_method_selection_20260701", "No direct force answer key; normal direction relies heavily on unmeasured modes"],
            ["Validated net-CG reproduction and tier update", "shocksat_netcg_validated_port_20260716", "Reference reproduced exactly; S3 cannot-verify through mapping; S4 not met, normal Z 2.958"],
            ["FRF comparison", "shocksat_psd_envelope_twin_20260623", "Deterministic comparison only"],
            ["Working-twin good/bad FRF comparison", "statfem_real_validation_20260617/out/mc_cache.npz", "Converged modal parameter stage plus observed-channel-estimated marginal discrepancy; calibrated but wide and not a joint whole-FRF posterior"],
            ["Failed joint whole-FRF and older exact-basis comparisons", "shocksat_full_spectrum_frf_20260714 plus shocksat_fullspec_exact_completion_20260716", "Leakage-safe point estimates only; their NUTS posteriors did not converge"],
            ["IFT versus free discrepancy", "ift_real_validation_20260619", "IFT TMCMC converged and improved peak-QOI scores; band-GRMS remained over-wide and validation used one hit / one drive"],
            ["Schneider / Das–Debnath method stress tests", "papers_statfem_studies_20260612", "Synthetic and suspended-panel evidence is a method comparator, not a ShockSat posterior"],
            ["Damping and shape update", "shocksat_frf_damping_updating_20260710", "Damping resolution inadequate; Bayesian shape/damping intervals not trustworthy"],
            ["Evidence/model-class conclusion", "shocksat_composite_bakeoff_20260702 and full-spectrum completion", "Evidence ranking did not earn held-out QOI delivery"],
            ["Model-form pilot", "shocksat_modelform_pilot_20260716 + advisor_audit_metrics.json", "Selected-best results are selection-biased; class-mean controls are separate; agent did not beat random"],
            ["Agent-facing remodeling harness", "mpl_agentic_remodel_bayes_harness README, schemas, and validator", "Reusable scaffold validated; unified remodelctl and structured-feedback ablation are proposed; no MPL remodeling posterior was produced"],
            ["Follow-on formulation calibration", "shocksat_formulation_calibration_20260720", "Incomplete; excluded from the results"],
        ],
        [2350, 3500, 3310],
        font_size=7.5,
    )
    add_paragraph(
        doc,
        "This synthesis performs no new inference. The earlier original summary and the rejected intermediate "
        "decision memo are preserved in the same report workspace. Figures are regenerated from the frozen "
        "source manifest; numerical values are copied from the listed study packets and checker outputs.",
        italic=True,
        size=8.8,
        color=GREY,
    )

    doc.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
