# Priority deliverables — ShockSat advisor progress-and-closure revision

Date: 2026-07-21

## Human asks and interpretation

| Priority ask | Working interpretation | Delivery location |
|---|---|---|
| Restore the advisor context | Assume Ilias knows only that the project concerns Bayesian FEM updating/statFEM and last reviewed the original proposal. Start with his stated objective: build and evaluate statFEM, identify gaps, and suggest improvements. | New DOCX introduction and original-objective comparison |
| Remove the rejected framing | Remove the "Decision requested" section, the color-coded research-status section, and unexplained project shorthand such as "honest shear-load band." | New DOCX throughout; automated text/style checks |
| Explain what was actually done | Introduce ShockSat, the available FEM/test data, the implemented statistical model, the likelihoods, priors, inferred/fixed quantities, NUTS settings/diagnostics, and the evaluation sequence. | New DOCX Sections 2–5 |
| Explain the pivot | Explain why parameter updating and output discrepancy could not repair missing model form, what agentic model-form remodeling means, how it was evaluated against equal-budget random search, and what succeeded/failed. | New DOCX Section 7 |
| Clarify the current agentic-remodeling harness | Show discrete model-form choices versus continuous Bayesian updating; identify what the agent may change, what immutable code controls, which candidate-loop pieces exist now, and which `remodelctl`/feedback-training pieces are proposed. | Section 7 prose plus a current-vs-planned flowchart |
| Audit the Bayesian methods comprehensively | Use the experiment catalog plus later checker-backed studies to compare Beck/evidence, Schneider/frequency-domain updating, frequency-only, whole-FRF, MAC/shape, and statFEM discrepancy variants. For each, state data used, likelihood, priors, discrepancy/noise, sampler, diagnostics, held-out result, and claim limit. | New Bayesian-method matrix in Sections 3–5 and provenance appendix |
| Show good and bad FRF channels | Select channels by a documented, reproducible rule; show measured, baseline/failed, and 2–3 eligible successful methods on common axes. One channel must show meaningful movement toward the data and one must show persistent mismatch. | New source-controlled FRF comparison figure and source manifest |
| Defend the two causal conclusions | Explicitly test whether prior strength, likelihood compression/covariance, discrepancy confounding, convergence, spectral resolution, and missing model form explain limited posterior movement and wide prediction bands. Do not blame model form until alternatives are separated. | Bayesian assumption audit and two plain-language conclusions in the report |
| Resolve Andrew's Word comments | Explain the executive-summary phrasing and evaluation-versus-validation distinction; repair equation subscripts; define band median versus plausible-truth median. | Revised paragraphs/equations/caption; final clean DOCX with comments addressed |
| Recover Andrew's direct prose edits | Treat the preserved edited Word draft—not the generated Python text—as the authority. Extract the user editing-session revision IDs and restore every substantive prose change while retaining later Bayesian-audit material. | `code/extract_user_word_edits.py`, `qa/advisor_progress_bayesian/recovered_user_edits.json`, and revised report builder/DOCX |
| Add predictive bands to Section 5.4 | Use stored posterior/posterior-predictive draws only. Distinguish a parameter-propagation envelope from a calibrated predictive interval, print convergence limits, and do not invent a band where draws are absent. | `code/make_bayesian_frf_comparison.py`, `out/frf_predictive_bands.npz`, Figure 2 and caption |
| Recover the converged modular working twin and simplify Section 5.4 | Use frozen `mc_cache.npz` arrays to show measured data, original FEM, updated median, parameter uncertainty, and total uncertainty with the separately estimated model-form term on one improved and one persistent-miss held-out channel. Remove hit-quality shading/axis and failed-method curves. Label the result modular, not jointly inferred whole-FRF StatFEM. | `code/make_working_twin_frf_comparison.py`, `out/working_twin_frf_metrics.json`, Figure 2 in `ShockSat_Bayesian_FEM_and_StatFEM_progress_update_working_twin_revision.docx`, and Task Card B item 11 |
| Support closure rather than request a technical verdict | End with Andrew's less-than-one-month concern: how to close the PSL work, diagnose whether the original direction was wrong or over-scoped, and preserve meaningful contributions and lessons for the lab. | New DOCX Sections 8–9 |
| Reduce figure overload | Give each retained figure one declarative claim; remove secondary panels, most on-plot prose, and repeated status text. Keep the FRF comparison as the main visual evidence. | `code/make_summary_figures.py`, `figures_revised/`, revised DOCX |
| Decide whether charts should be tables | Use tables for compact exact comparisons, status matrices, method outcomes, and provenance; reserve plots for shapes, trends, uncertainty, or residual structure. | Revised DOCX tables |
| Prevent undefined terms | Define statistical terms and all local project shorthand on first use; remove internal candidate labels from the main narrative unless essential. | Revised DOCX body, captions, and compact glossary |
| Add real literature | Use repository references when bibliographic identity is inspectable and web-search authoritative/primary sources for missing context. Every citation must resolve to a real source. | `references_verified.md` and revised DOCX reference list |
| Preserve scientific honesty | Do not recompute or strengthen science claims. Copy values from checker-backed artifacts; describe evidential limits in ordinary language rather than relying on color/status shorthand. | Figure source manifest, captions, appendix, QA report |
| Consolidate the two external reviews | Implement criticisms that survive later repairs; explicitly supersede stale review claims with checker-backed exact reruns. | Run-specific Bayesian diagnostics table; defect/repair/current-claim ledger |
| Correct selection language | Show the selected best-of-12 result separately from the preregistered class-mean control for each genuine model-form class; label the former selection-biased. | Section 7 result table and generated audit metrics |
| Make the Bayesian identifiability claim auditable | Report posterior-SD/prior-SD contraction for all nine modal stiffness groups; do not convert contraction into per-parameter identifiability without the full strain-energy/FIM decomposition. | Section 5.1 and generated audit metrics |
| Define project comparators and ratios | Define +6 dB as a project incumbent allowance, state its amplitude factor, and write the residual-GRMS numerator/denominator and band-width ratio contracts. | Sections 5.2–5.3 |
| Replace generic closure scheduling with an acceptance bar | Ask Ilias to approve or change a finite, artifact-backed definition of a rigorous evaluation closeout. | Final-month section |

## Acceptance criteria

1. Each main-text figure has one written story and no unexplained project-local labels.
2. FRF figures retain log-frequency axes and physical magnitude units; annotations are sparse.
3. Exact multi-method/model comparisons appear as tables unless a plotted relationship materially aids interpretation.
4. The advisor can identify: the original objective, what was built, what worked, what did not, why industry use is not yet supported, why the work pivoted, and what closure help Andrew needs.
5. Literature citations are checked against real repository files or primary web pages and recorded with URLs/identifiers.
6. Plotting code is saved, Tufte-linted, and all numeric artifacts carry source/run/status metadata.
7. The revised DOCX is rendered to page images and every page is visually inspected; structural and accessibility audits are recorded.
8. Section 5.4 contains finite, ordered stored-draw bands and states on the figure/caption whether each band is scientifically trustworthy.
9. The report contains no selected-best/class-mean conflation and no stale leakage/net-CG-port defect presented as current.
10. Each posterior pathology is tied to a named run, target, sampler, stored diagnostic, and limited conclusion.

## Assumptions needing human confirmation

- Audience is an advisor update and report seed: advanced structural dynamics, beginner-to-intermediate ML/statistics, and no ShockSat/project-specific background.
- ShockSat remains the main case; MPL appears only as a boundary/next-case comparison.
- This revision changes presentation and literature framing, not the underlying analyses or checker verdicts.
