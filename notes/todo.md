# Todo

## 2026-11-17 NASA burst-survey foundation check

- [x] Save the recovered extract (zip sent; private repo branch claude/ecstatic-carson-c3e4f9).
- [x] Headers-only request to NASA: BLOCKED by the cloud environment's network policy (proxy 403).
- [x] Exact fetch plan, tested ranged fetcher, binary probe, NASA deck evidence, exploratory pilot, frozen 264-curve pre-registration, burst rehearsal.
- [ ] Andrew: allow `mediaex-server.larc.nasa.gov` in the cloud environment (Network access, Limited, Allowed domains).
- [ ] Then `bash artifacts/reports/shocksat_burst_survey_foundation_20261116/gated_run.sh`; score the 262 unseen plots (Test 1); then `WITH_TIME_HISTORIES=1` and foundation gates F1-F5.
- [ ] If SUPPORTED: write a decoder for .ati/.afu and a polyreference damping estimator; model the shaker blocks (masses from the test plan).

## 2026-07-22 ShockSat advisor report — WORKING-TWIN FRF CORRECTION IN PROGRESS

Human priority: while Task Card A finishes its A2 sweep, correct Section 5.4 using the retained converged
working-twin result. Replace the eight-panel method wall with a two-panel held-out comparison containing only
measured data, original FEM, updated posterior median, parameter uncertainty, and total predictive uncertainty
after the separately calibrated model-form term. Remove hit-quality shading. State that the modal parameter
posterior converged but the discrepancy was estimated modularly rather than jointly sampled with the parameters.

- [x] Record the corrected method classification and Figure 5.4 contract in the predecessor decisions log and Task Card B.
- [x] Generate the simplified two-channel figure from the frozen `mc_cache.npz` arrays only; run Tufte lint and image QA.
- [x] Correct the modal likelihood direction and distinguish the modular working twin from the failed joint whole-FRF target.
- [x] Build a new DOCX without overwriting any prior report, run the checker, render it, and inspect every page.
- [x] Carry the correction into the post-A2 Task Card B rebuild.

Completed 2026-07-22. New interim deliverable:
`ShockSat_Bayesian_FEM_and_StatFEM_progress_update_working_twin_revision.docx`. Checker **OVERALL YELLOW
13G/1Y/0R, exit 0**; Tufte lint 0 flags; accessibility 0 findings; all 16 pages inspected. The YELLOW is the
scientific ceiling. Task Card B remains blocked only on the A2 completion packet and still owns final compression.

## 2026-07-21 ShockSat advisor report — REVIEW CONSOLIDATION COMPLETE

Human priority: starting with the initial external review and the later reviewer correction, implement every
criticism that still survives the repaired project artifacts. Treat later checker-backed repairs—not either
reviewer's prose—as the current source of truth.

- [x] Separate the whole-FRF, free-discrepancy, and IFT posterior pathologies by exact run and diagnostic.
- [x] Correct model-form best-selected results versus preregistered class-mean controls and label selection bias.
- [x] Add a defect/repair/current-claim ledger for leakage, exact reranking, net-CG porting, and checker scope.
- [x] Clarify mass normalization, priors, local-versus-global information, evidence target, LODO scope, +6 dB,
      and the residual-GRMS quantity contract.
- [x] Add artifact-derived modal posterior contraction and compact runtime accounting; do not invent trace plots
      where raw TMCMC draws were not retained.
- [x] De-emphasize agentic branding, tighten contributions/lessons, and replace the generic calendar with a
      concrete closeout acceptance bar for Ilias to approve or change.
- [x] Rebuild, Tufte-lint, check, render, inspect every page, and update the report ledger and central project log.

Completed 2026-07-21. The consolidated revision implements the criticisms that survive the repaired artifacts
and explicitly rejects superseded claims. It distinguishes the three posterior pathologies, separates selected
best candidates from class-mean controls, adds a defect/repair/current-claim ledger, and defines the disputed
quantities and Bayesian assumptions. No new inference was run and no missing TMCMC trace was fabricated.
Tufte lint: 0 flags. Checker: **OVERALL YELLOW 13G/1Y/0R, exit 0**. All 16 pages inspected.

## 2026-07-21 ShockSat advisor report — RECOVER USER PROSE AND ADD FRF PREDICTIVE BANDS

Human correction: the Bayesian-audit rebuild recovered the four comments but lost other prose edits Andrew
made directly in the previous Word draft. Treat the preserved edited DOCX as the text authority. Recover every
user-authored text change before revising Section 5.4. Add predictive FRF bands only from stored posterior or
posterior-predictive draws; do not manufacture bands around deterministic MAP curves, and print convergence/
validity limits on the figure and caption.

- [x] Extract all Word paragraphs/runs carrying the user-edit revision IDs and compare them with the current report.
- [x] Reinsert each substantive user prose edit in the report builder, preserving later Bayesian-audit additions.
- [x] Inventory whole-FRF/modal/Beck stored draws and identify which methods have valid predictive ensembles.
- [x] Revise the Section 5.4 plot and caption with honest predictive bands and explicit non-convergence labeling.
- [x] Tufte-lint, rebuild, structurally check, render and inspect every page, rerun the one-command replay, and update records.

Completed 2026-07-21. The extraction found two user editing-session revision IDs and restored every substantive
prose change, including the shorter opening, evaluation-versus-validation conclusion, Net-CG explanation, and
remeshing/remodeling wording. Section 5.4 now shows a 120-draw modal parameter-propagation envelope and a
120-draw whole-FRF pointwise predictive interval. The latter is printed as NOT TRUSTWORTHY because the fold
posterior has R-hat 48.8 and ESS 2.0. No Beck band was invented: its run retained no posterior draws and did
not converge. Tufte lint: 0 flags. Checker: **OVERALL YELLOW 12G/1Y/0R, exit 0**. All 15 pages inspected.

## 2026-07-21 ShockSat advisor report — BAYESIAN METHOD AUDIT AND COMMENT RESOLUTION COMPLETE

Human priority: address the four Word comments and make the Bayesian evaluation comprehensive enough for
Ilias Bilionis. Use `experiment_catalog.xlsx` as a starting index, then incorporate later checker-backed work.
Add a method/likelihood/discrepancy table; select 2–3 strongest methods; compare them with a baseline/failed
method on one genuinely improved FRF channel and one persistent-failure channel; and state, with evidence,
why the posterior mean did not move enough and why the predictive bands remained too wide. Audit prior
strength, likelihood/covariance assumptions, discrepancy confounding, convergence, and data resolution before
attributing failure to model form.

- [x] Preserve and inventory the user-commented DOCX and extract all comments/anchors.
- [x] Inspect and render every sheet of `experiment_catalog.xlsx`; reconcile it against later report workspaces.
- [x] Build a source-backed Bayesian method matrix with likelihood, priors, discrepancy, sampler, diagnostics,
      data usage, held-out result, and claim limit for each relevant technique.
- [x] Locate reproducible same-channel FRF arrays for a good and bad channel; pre-register selection and method
      eligibility before plotting.
- [x] Create a source-controlled two-channel comparison figure, run Tufte lint, and record legibility/provenance.
- [x] Revise the advisor DOCX, repair equation subscripts, clarify the two commented phrases and band medians,
      add the method matrix/figure, and state the two causal conclusions with Bayesian alternatives ruled in/out.
- [x] Rebuild, structurally audit, render every page, inspect all pages, run the checker, and update records.

Completed 2026-07-21. Deliverable: `ShockSat_StatFEM_progress_and_closure_update_bayesian_audit.docx`.
Checker: **OVERALL YELLOW 11G/1Y/0R, exit 0**. All document, context, method, assumption-audit,
good/bad-FRF, remodeling, literature, equation/comment, and render gates are GREEN. The one YELLOW is the
scientific claim ceiling: no direct net-CG answer key; whole-FRF and Beck NUTS posteriors did not converge;
the comparison curves are held-out deterministic MAP points, not Bayesian intervals. All 14 pages inspected.


## 2026-07-21 ShockSat advisor report — AGENTIC-REMODELING CLI EXPLANATION COMPLETE

Human priority: incorporate the separate advisor through-line on training the remodeling skill/harness. Make
clear that agentic remodeling is the outer discrete model-form loop (not just mesh refinement and not Bayesian
property scaling), distinguish existing candidate/build/V-gate/split/exact-score components from the proposed
`remodelctl` wrapper, and use a flowchart to show the controlled feedback cycle.

- [x] Read the pasted guidance and re-ground in the current MPL harness and completed ShockSat pilot.
- [x] Record the current-versus-proposed distinction and the agent's allowed/forbidden modification boundary.
- [x] Build a source-controlled agentic-remodeling/CLI flowchart and visually inspect it.
- [x] Add concise current-method, planned-CLI, feedback-role, and blind-training details to Section 7.
- [x] Rebuild the DOCX, update the appendix/checker, render every page, and record visual QA.
- [x] Update the report README, run log, and central project log with the new delivered artifact/hash.

Completed 2026-07-21. Current checker: **OVERALL YELLOW 10G/1Y/0R, exit 0**. Ten artifact/context/method/
agentic-remodeling/literature/render gates are GREEN. The one YELLOW remains the inherited scientific claim
ceiling, not a document defect. Final DOCX has 13 inspected pages and three figures with alt text.

## 2026-07-21 ShockSat advisor update — CONTEXT/TECHNICAL/CLOSURE REWRITE COMPLETE

Human correction: replace the decision-memo framing with a self-contained technical progress report for Ilias,
who last saw the original statFEM proposal and has no ShockSat or agentic-remodeling context. Remove color-coded
research status, define local terms, show the Bayesian model and NUTS details, explain the unmet industry-use
goal and model-form pivot, and end with the requested final-month closure discussion.

- [x] Re-read Ilias's last-reviewed proposal and his controlling evaluation objective.
- [x] Audit the checker-backed ShockSat modal, sequential statFEM, net-CG, damping, FRF, and model-form results.
- [x] Record the corrected audience, purpose, and acceptance criteria in the report workspace.
- [x] Verify and expand the StatFEM, calibration-discrepancy, NUTS, diagnostics, TMCMC, and model-updating literature.
- [x] Build a new self-contained DOCX; preserve the original and rejected intermediate memo.
- [x] Run automated content/structure/a11y checks, render every page, and record page-by-page visual QA.
- [x] Update the report README and central project log with the final artifact-backed result.

Completed 2026-07-21. Current deliverable: `ShockSat_StatFEM_progress_and_closure_update.docx`. Checker:
**OVERALL YELLOW 9G/1Y/0R**, exit 0. Nine document/context/method/reference/render gates are GREEN; the single
YELLOW is the inherited scientific ceiling (unmeasured net-CG load, non-converged held-out/full-FRF posterior
families, and no agent-over-random advantage), all stated in the report.

## 2026-07-21 ShockSat advisor results summary — FIGURE/NARRATIVE REVISION IN PROGRESS

Human priority: make the advisor packet easy for Bilionis to interpret and use to decide the next research
step. Preserve the strong FRF plots, reduce their annotations, require every remaining graphic to tell one
story that supports the overall message, prefer tables when exact comparisons matter, define any term a
reader could reasonably ask about, and add only verified literature references from the repository or web.

- [x] Audit each current figure against a one-sentence claim and the report's main decision narrative.
- [x] Replace overloaded comparison graphics with advisor-readable tables where appropriate.
- [x] Rebuild retained plots from source artifacts with fewer series, fewer annotations, and explicit provenance.
- [x] Add a short, verified literature frame and reference list; do not infer bibliographic details.
- [x] Rebuild a separate revised DOCX, preserving the original packet.
- [x] Run Tufte lint, structural/a11y checks, render every page, and inspect all page images before delivery.

Completed 2026-07-21. Revised checker: **OVERALL YELLOW 6G/1Y/0R**, exit 0. Artifact and layout gates are
GREEN; YELLOW is the honest science ceiling (normal force lacks a direct answer key; full-spectrum NUTS did
not converge; evidence winner did not earn held-out delivery).

## 2026-07-20 MPL EXISTING-DATA-ONLY CONDITIONAL CAMPAIGN — COMPLETE 2026-07-21, checker OVERALL YELLOW {16G/2Y/0R} exit 0, pending Andrew review of packet.md

Andrew decision: no additional MPL test data can be acquired; make the strongest defensible use of the 13
existing sequential single-response records. Preserve the completed Stage-0 YELLOW result and start a separate
workspace with an explicit YELLOW claim ceiling.

- [x] Record the human constraint and its consequences in the completed campaign `decisions_log.md` D5 and
      the lead CURRENT STATE.
- [x] Write the dispatch-ready successor card at
      `docs/lab/mpl_existing_data_conditional_runner_prompt.md`; it freezes the YELLOW ceiling, bounded model
      menu, five-family cross-validation, exact feature-loss generalized Bayes, and no A/R or vault claim.
- [x] Create an isolated successor workspace and `priority_deliverables.md`: model plausibility and
      condition-scoped uncertainty, not validated winner selection.
      (`artifacts/reports/mpl_existing_data_conditional_20260720/`; INIT verified all 13 raw + predecessor locks
      + frozen model by hash; all pre-registration gate files written.)
- [x] Freeze an existing-data-only likelihood/evaluation contract and fail-closed checker before fitting:
      primary response-only tap transfer features; acoustic centered spectral shapes as a 6 dB robustness arm;
      leave-one-response-family-out checks; empirical hit/block uncertainty; no true vault.
      (`check.py`+`check_config.json` SHA-locked in `CHECKER.sha256`; RED-on-empty proven exit 1,
      `out/checker_empty_report.json`. Menu frozen in `model_menu.json` + `candidates/`. Five folds in
      `data_split_manifest.json`. FEATURES observed side done: observed counts reproduce predecessor EXACTLY
      15/15 paths; fresh global q95 0.7117% ~ inherited floor 0.7172%; per-fold tau floors written.)
- [x] MENU V-gate battery (all GREEN after D4) (identity/no-op, RBM, positive mass/stiffness,
      finite eig, finite perturbation directional, mesh/resolution) for B0/B1/B2/M1/M2 + negative controls;
      then modeled-side features per class/fold.
- [x] UPDATE = known-answer-validated TMCMC generalized-Bayes over the 6
      stiffness multipliers, per updatable class x 5 folds x 3 seeds; EXACT candidate-own confirmation + reduced
      gap; ROBUSTNESS acoustic 1.5/3/6 dB + full sensitivity axes. Do not smooth the observable to claim NUTS.
- [x] Model averaging/plausibility-set path taken (headline = plausibility_set {B2}, NOT preferred); YELLOW ceiling held.
- [x] Packet, findings, 10 QA-fixed figures, sensitivity/identifiability, runtime, manifest, replay; runs.md + project_log rows appended with verbatim checker status.

## 2026-07-20 MPL ONE-DISPATCH AGENTIC REMODEL + BAYES HARNESS — COMPLETE, checked Stage-0 YELLOW stop, pending Andrew review

Purpose: extend the ShockSat lessons to a long-running, restart-safe MPL campaign that separates genuine
model-form search from continuous Bayesian property updating and scores both on admissible held-out dynamic
observables. Campaign workspace: `artifacts/reports/mpl_agentic_remodel_bayes_20260720/`. No MPL science
result or posterior was produced because Stage 0 did not earn an admissible discriminating observable. The
precheck is OVERALL YELLOW with 7 GREEN conduct/integrity gates and 0 RED; schema and figure QA are GREEN.

- [x] Bootstrap isolated workspace and re-ground from the card/repository continuity files.
- [x] Record priority deliverables and D0/D1, including exclusion of the still-incomplete ShockSat
      formulation-calibration study and the 7.9 GiB disk constraint.
- [x] Audit all 13 raw MPL records into `condition_registry.json`, including acquisition legality,
      independent-realization count, clipping/SNR, grid/window/detrend, usable bands, and split eligibility.
- [x] Freeze `data_admissibility_contract.md`, `precheck_config.json`, and `precheck.py`; prove RED on empty
      outputs and write `PRECHECK.sha256` before the first validity perturbation.
- [x] Run the frozen B0/B2/four-perturbation discriminating-validity test and independently checked null.
- [x] Stage 0 is YELLOW: package the honest stop and minimum new-test request. The GREEN-only full
      science harness—baselines, operators, fair A/R search, finalists, held-out evaluation, and science
      checker—was intentionally not run. One-command Stage-0 replay exits 0.

- [x] New autonomous runner card: `docs/lab/mpl_agentic_remodel_bayes_runner_prompt.md`.
- [x] Correct the old MPL prompt's no-force assumption: sequential single-accelerometer records default to
      repeated-source pseudo-transmissibility or response-only features; input cancellation must be proven.
- [x] Pre-register B0 untouched prior / B1 property-only Bayes / B2 human D43 / equal-budget random / agent
      arms; genuine connectivity, geometry, element-formulation, mesh, and missing-hardware families.
- [x] Encode three-round default budgets, exact candidate-own reporting, NUTS/TMCMC labeling, FIM at the
      realized discrepancy floor, train/dev/one-time-vault discipline, a locked Stage-0 admissibility
      precheck, and science-status propagation.
- [x] Add reusable scaffold under `docs/lab/mpl_agentic_remodel_bayes_harness/`: bootstrap, state machine,
      fail-closed templates, candidate/run-state/evaluation/condition JSON schemas, examples, and validator.
- [x] Validation: Python compilation GREEN; `validate_harness.py` GREEN; isolated bootstrap smoke test GREEN
      (`SCIENCE_NOT_RUN`, INIT state, schema bundle; test workspace moved outside the repo afterward).
- [x] Andrew dispatch received through the attached successor card; Stage 0 data/observable validity runs
      before the immutable science checker and before any remodeling search.

## 2026-07-16/18 MODEL-FORM PILOT (runner card C) — COMPLETE, checker GREEN 12G/0Y/0R, pending Andrew review
Workspace `artifacts/reports/shocksat_modelform_pilot_20260716/` · replay `bash run_all.sh`.
**SCIENCE (pre-registered): HQ1 FALSIFIED (stratified agent still ties random: −0.0077±0.0177 best,
+0.0028±0.0056 means; finalist S-test random>agent 3.1×SE) · HQ2 MET BY ALL FOUR GENUINE CLASSES
(formulation +0.0711±0.0120 5.9×SE, connectivity +0.0641±0.0273, mesh +0.0635±0.0214, geometry
+0.0597±0.0116; class-mean control 1.6–2.9×SE ⇒ not selection noise).** First positive of the
remodeling arc: model-form freedom moves held-out FRF; the guidance still doesn't. Best-ever edit =
zero-DOF formulation stiffening `mr2_elem5` +0.1848 (robust to per-fold refits, +0.1954).
Open items for ANDREW (decisions, not work):
- [ ] **Overrule or confirm the D0 assumptions** (workspace `decisions_log.md`): HQ1 best-vs-best
      primary convention; HQ2 pooled-class best vs A1; finalist refits = reinforcement (not verdict);
      dud-replacement + class-drop rules.
- [ ] **Next-card decision:** a DELIBERATE formulation/geometry calibration study (grid over br/ts_t
      and joint-offset direction on the winning regions, exact-basis, + a TMCMC posterior on the
      winner per the compute protocol) is now justified for the first time; blind agentic search over
      the same space is not (HQ1). Also still open from Card A: the 200–500 Hz criterion gap.
- [ ] Note: `mr2_elem5`'s physical reading (cross-beam/center-box bending stiffer than modeled) agrees
      with the long-standing cross_beam×1.4 property lever — worth a drawing/CAD check of the real
      cross-beam joint before any delivery claim.

## 2026-07-16 EXACT-EVIDENCE COMPLETION (runner card A) — COMPLETE, checker GREEN 12G/0Y/0R, pending Andrew review
Workspace `artifacts/reports/shocksat_fullspec_exact_completion_20260716/` · replay `bash run_all.sh`.
Closed review D17's 3 evidence holes. **GREEN = integrity/evidence-completeness, NOT criteria met**:
Q1 "C dents" (arm-C exact +0.0458 ± 0.0361 vs A1 → S1 NOT MET); Q2 agent ties random under BOTH selection
conventions (28/28 exact-scored; (a) −0.0017 ± 0.0094, (b) +0.0115 ± 0.0158) → H2 impotence on firmer ground.
Open items for ANDREW (decisions, not work):
- [ ] **Approve/reject 2 durable-rule candidates** in `notes/lessons-learned.md` (2026-07-16 block):
      (a) any code path loading modal/reduced coefficients fit elsewhere must ASSERT basis identity
          (r, matched-mode count, truncation index, basis hash) — a silent basis mismatch cost −0.085 here;
      (b) checker gates constrain the CONDUCT of their own workspace and must NEVER encode a predicted
          external outcome (my G05 locked on "S3/S4 == CANNOT-VERIFY" and Card B then falsified S4).
- [ ] **Overrule or confirm 3 unconfirmed assumptions** (`decisions_log.md` D0): "all 28" = query_log rows
      (dud `wr3_rnd001` excluded-with-reason); T1 refits shapes at θ=ones on the enriched basis; paired SE
      = std/√4 (verified to reproduce the repair exactly).
- [ ] **Note the stale S3/S4 status** in my `verdicts_final.json` (D3): Card B
      (`shocksat_netcg_validated_port_20260716`) FALSIFIED S4; my file says CANNOT-VERIFY by locked-checker
      scope and carries `superseded_by_card_B` everywhere. Card B is current.
Suggested next card (NOT started, needs Andrew's go):
- [ ] **The 200–500 Hz band has the real signal and NO pre-registered criterion tests it** — arm B is
      +0.197 there vs A1 +0.033 (a ~6x gap, far larger than anything in sub-200 where S1/S2 live). S1/S2 are
      sub-200 rules by construction, so the study's headline "no lever works" is a statement about the band
      where the levers were weakest. A mid-band criterion is the obvious cheap next question.
- [ ] A fair agentic-remodel test still needs a compass that can propose `refine`/`rbe2_soften` edits — the
      agent proposed ZERO genuine model-form changes (study D16), so H2 remains scoped to a
      mostly-parametric edit space under every convention tested here.

## 2026-07-01 Plate-test rehearsal (synthetic end-to-end validation of the >200 Hz drumhead test design) — COMPLETE 2026-07-02, pending Andrew review
Checker OVERALL RED (28G/3Y/1R): the RED = pre-registered S1 claim-falsified (buy-down 3.5x does NOT survive the pipeline; 12 sensors -> 6.2x). Mechanism found (theta posterior re-mixes the near-degenerate drumhead cluster); revised scope: pin ALL 12 band modes -> 2.81x oracle bound. Follow-up needed: 12-mode-inference rehearsal before any hardware ask; netcg packet §9's 3.5x claim needs a caveat (Andrew decision).
Workspace: `artifacts/reports/plate_test_rehearsal_20260701/`. Andrew approved 2026-07-01 ("execute it, the original idea"; 2x2 ablation NOT bundled). Lead acts as runner.
- [ ] Gate files first: priority_deliverables, question_framing (PRE-REGISTERED success criteria), quantity_contracts, assumptions_ledger, decisions_log.
- [ ] check.py written + SHA-locked (CHECKER.sha256) BEFORE any science runs; immutable during trial.
- [ ] code/rehearsal.py: synthetic truth ensemble (drumhead shape mixing incl un-representable fine structure) -> simulated plate-array data (1 / 12 / 20 Z-sensors, +Y drive; placement-jitter arm) -> JOINT numpyro NUTS (theta 9 + shape coeffs + noise scale; shape basis frozen at theta_MAP, documented) -> delivered normal-Z band -> coverage + band factor vs known truth. Resumable per (arm,seed); detached launch; threads pinned.
- [ ] Arms: A0 current 1-sensor (no-false-sharpen integrity arm), A1 12-sensor (headline <=3.5x claim), A2 20-sensor, A3 12-sensor + placement jitter (graceful degradation). n_seed=8 main; SD_A_U in {0.4,1.6} sensitivity at 2 seeds.
- [ ] Figures (Tufte skill + lint): buy-down analytic-vs-rehearsed money figure; bands vs truth per arm; amplitude recovery; truth-vs-observed sensor data; run-specific graphical model.
- [ ] packet.md + findings.md + runtime.json + checker run; notes/runs.md + project_log row copied from checker; status never stronger than checker output.

## 2026-07-01 Project reset artifact review — COMPLETE
Workspace: repo root; scope = `notes/reset_prompt_2026-07-01.md` plus `artifacts/`.
- [x] Compare current artifact evidence against the reset vision: held-out validated, QOI-targeted, Bayesian updating + downselection + agentic remeshing, aerospace usability first.
- [x] Identify which experiment families are strong evidence, honest negatives, stale/mixed-era, or not aligned with the reset.
- [x] Recommend the next run with a concrete acceptance target and caveats.

## 2026-06-23 ShockSat sequential statFEM elastodynamics pilot — COMPLETE, pending Andrew review
Workspace: `artifacts/reports/shocksat_sequential_statfem_20260623/`.
- [x] Scaffold priority deliverables, decisions log, question framing, quantity contracts, assumptions ledger, replay script, checker, and packet.
- [x] Implement a bounded reduced modal-state sequential filter using clean modal-hammer Test01/Test02/Test04/Test06 time histories, with the first 90% leave-sensors-out split.
- [x] Score only the inherited PSD-envelope metrics: 97.5% envelope GRMS ratio vs FEM+6 dB and energy-weighted positive dB exceedance on held-out measured PSD.
- [x] Compare nominal all-error-as-residual filtering against stiffness-updated-plus-residual filtering on the same split, with sampler/filter labels kept explicit.
- [x] Run one-command replay, checker, runtime accounting, and continuity updates; report GREEN/YELLOW/RED no stronger than checker output. Checker OVERALL YELLOW 18/3/0; best sequential variant = `stiffness_residual`, median GRMS ratio 2.07 vs FEM+6 dB, clean-win rate 18.8%, worst residual band 22.0 dB.
- [ ] Andrew: decide whether this honest negative stops the sequential-statFEM branch for PSD-envelope GRMS, or whether a full covariance/material-field implementation is still worth a separate task card.

## 2026-06-23 New ShockSat-applicability paper review — COMPLETE, pending Andrew review
Workspace: `artifacts/reports/shocksat_new_papers_review_20260623/`.
- [x] Re-ground from current ShockSat state and review the three pulled PDFs from `references/pdfs/`.
- [x] Triage each paper against the project vision, current ShockSat data reality, and near-term PSD-envelope/modal-hammer thread.
- [x] Write runner prompt(s) only for papers whose contributions are at least moderately applicable to ShockSat.
- [x] Run a lightweight checker, then update continuity files with the exact checker status. Checker OVERALL YELLOW 41/1/0; yellow = prompts are hypotheses only, no ShockSat metric improvement claimed yet.
- [ ] Andrew: choose whether to launch the high-priority sequential statFEM runner, the latent-force/BNN runner, or defer both until the PSD-envelope probe finishes.

## 2026-06-13 Schneider × Das/Debnath × Yan(2026) × StatFEM study program — COMPLETE (13 studies), pending Andrew review
Workspace: `artifacts/reports/papers_statfem_studies_20260612/`. Decisions D0–D36 in workspace decisions_log.md.
Checker OVERALL YELLOW 76/22/0. Replay `bash run_all.sh`.
- [x] Review Schneider 2022, Das/Debnath 2020, Yan et al. 2026; design the unified-method study program.
- [x] A (Schneider discrepancy A/B), Phase-1 (control+sweep), C+C2 (REAL panel floor + MAC mapping), D (latent complex modes).
- [x] G = THE UNIFIED METHOD (bimodality finding + 12-rung HMC ladder + evolving-band GIFs); H (3 cures A/B); I (unknown forcing).
- [x] J (REAL-panel UMS converges), K (per-mode freq → 5/5 held-out, the real-data win + false-negative meta-lesson).
- [x] L (sharpen A/B: per-mode amplitude non-identifiable from one reference → band width is a DATA limit).
- [x] M (Yan 2026 sensor faults: Bayesian virtual sensing vs spatial interpolation, paper's dB metric, calibrated UQ).
- [x] Deck (34 slides), research_narrative.md (3 audiences + vision audit), packet.md, manifest, runtime.
- [x] Durable-file updates (this entry + project_log row + runs.md + lessons-learned) — Andrew signed off 2026-06-13.
- [ ] **Andrew: the single highest-value next action (from Study L) is acquiring MULTI-REFERENCE / roving-excitation
      panel data** to turn the calibrated 5/5 bands from "trustworthy" into "trustworthy AND sharp" (needs new data).
- [ ] LATER (no new data): production-scale 4-chain finals for H/I (currently probe scale); seed-replication coverage
      curves; UMS → tray/MPL FEMs; exact-vs-smooth likelihood appendix; Study E (IP-gated FBS notch endpoint).
- [ ] LATER (the Yan-paper extension): honest double-counting demo — re-calibrate using reconstructed "virtual ground
      truth" AS data and show the posterior over-tightens (the closed-loop overconfidence trap), vs weighting by the band.

## 2026-06-12 Buffet+acoustic dome secondary-structure study — ACTIVE (D13 autonomy)
Workspace: `artifacts/reports/buffet_dome_secondary_20260612/`. Decisions D1-D13 in
workspace decisions_log.md (D12: max-q buffet ONLY; D13: iterate autonomously).
- [x] P0: task card, priority deliverables, quantity contracts, assumptions ledger
      (VERIFY list — no live web), decisions log.
- [x] S1 forcing-math plumbing validation (analytic plate) — GREEN.
- [x] S2 beam/bar element added + validated (<=0.04%) — GREEN.
- [x] Fine-region model build (58,662 DOF; mass parts match hand calc; rigid-body
      machine-zero after mount rigid-arm fix) + Donnell cylinder assembly check
      (n=3..6 within -3..-6%, pairs 1e-10).
- [x] Modal solves BC-A/BC-B launched detached (marching shift-invert, resumable).
- [ ] forcing_qoi.py nominal sweeps (both BCs) -> 4 QOI sets (self-check 1e-15 wired).
- [ ] Figures fig1-fig5 (Tufte-linted; 2 justified deviations: 3D geometry render;
      'dB' lint hit is the RdBu colormap string).
- [ ] CI v1 propagation MC (ci_mc.py, 144 draws, labeled NO-sampler).
- [ ] Overnight: resolve_variants.py (kmlo/kmhi/kjlo/tdlo/meshf re-solves).
- [ ] Checker S3+ gates; packet.md; project_log row update; runs.md entry.
- [ ] LATER (vision tie-ins): monolithic-toy coupling cross-check (P2); response-limit
      proxy from av_acc; acoustic co-driver reactivation (deferred by D12).

## 2026-06-12 Amplitude-dependent damping / hysteresis scan — COMPLETE, pending Andrew review
Workspace: `artifacts/reports/amplitude_dependent_damping_scan_20260612/`.
- [x] Re-ground from notes/memory.md, notes/todo.md, notes/runs.md, and ShockSat/MPL prior decision notes.
- [x] Create priority deliverables, decisions log, assumptions ledger, and quantity contracts.
- [x] Inventory ShockSat, MPL test stand, and suspended panel data products.
- [x] Run reproducible amplitude-dependence triage checks where supported by data.
- [x] Write `analysis_report.md`, `results.json`, checker report, runtime, and notes update.
- [ ] Andrew: decide whether to run a purpose-built MPL amplitude sweep with force/displacement
      measurement, since the current evidence is response-only and yellow.

## 2026-06-12 Forcing-marginalized amplitude-dependent damping toy — COMPLETE, pending Andrew review
Workspace: `artifacts/reports/forcing_marginalized_damping_toy_20260612/`.
- [x] Re-ground from notes/memory.md, notes/todo.md, notes/runs.md, and central project log.
- [x] Create priority deliverables, decisions log, assumptions ledger, quantity contracts, and checker scaffold.
- [x] Build a replayable synthetic primary/secondary toy where truth hides forcing, nonlinear joint damping, and model-form error.
- [x] Fit a Bayesian digital twin using force-normalized response ratios so the forcing function is analytically canceled / marginalized.
- [x] Report what effective damping and damping-dependent QOIs are learned, with green/yellow/red gates and caveats.
- [x] Run one-command replay, update notes/runs.md and docs/report/project_log.md with checker status.
- [ ] Andrew: review `packet.md` and decide whether the next toy should use explicit Iwan/Bouc-Wen friction,
      amplitude sweeps, or a real MPL/ShockSat joint dataset.

## 2026-06-12 Notch literature review — ACTIVE
Workspace: `artifacts/reports/notch_lit_review_20260612/`.
- [x] Re-ground from AGENTS.md, notes/memory.md, notes/todo.md, notes/runs.md, prior
      7004C study handoff docs, and central project log.
- [x] Create priority deliverables, decisions log, and checker scaffold.
- [x] Search standards/handbooks, peer-reviewed/conference literature, substructuring
      literature, response-limiting practice, statistical/Bayesian work, and patents.
- [x] Write source-tiered `lit_review.md`, `bibliography.md`,
      `novelty_and_fto_notes.md`, and `gaps_and_next_experiments.md`.
- [x] Run checker and update project log/runs with the resulting green/yellow/red
      status and coverage caveats. Checker YELLOW 26/1/0; only yellow =
      documented limited-access source boundary.

## 2026-06-11 7004C multi-point/6-DOF teaching study — COMPLETE, pending Andrew review
Workspace: `artifacts/reports/notch_multipoint_7004c_20260611/` (packet.md; check.py
OVERALL YELLOW 20/2/0 exit 0; PPTX + 3 GIFs). NO sampler (D1).
- [x] Re-ground; 7004C anchors extracted; harness docs; EX-A..D built + verified;
      gifs; pptx; checker; packet; runtime/manifest/files_changed; notes updated.
- [ ] Andrew: review packet.md + 7004c_multipoint_notch_summary.pptx (GIFs animate
      in slideshow mode); then decide whether to commit.
- [x] EX-E (Andrew D10, 2026-06-12): empirical-path experiment DONE (impedance recon
      vs coupled FEM; checker 24/2/0). Standing handoff doc + lit-review prompt written.
- [ ] Andrew: review packet §5b + notching_findings_for_future_agents.md + lit_review_prompt.md.
- [ ] RUN the lit-review prompt in a web-capable agent → artifacts/reports/notch_lit_review_<date>/.
- [ ] OPTIONAL follow-on: same questions on the real ShockSat × tray coupled thread
      (distributed 6-DOF CBUSH feet vs single-point condensation) + a faithful lateral-axis
      EX-D arm — needs a task card if pursued.


## 2026-06-10 ShockSat × tray coupled QOI study — COMPLETE, pending Andrew review
Workspace: `artifacts/reports/shocksat_tray_coupled_qoi_20260610/` (packet.md;
check.py OVERALL GREEN 22/0/0). NO sampler this task (propagation only, D1).
- [x] Re-ground; workspace + decisions_log D1–D9; priority_deliverables,
      question_framing, quantity_contracts, assumptions_ledger (A1–A20).
- [x] Build + verify (15/15 green): tray condensation vs FIM freqs 2.6e-11;
      RBM mass line 9e-5; FBS algebra exact; Newmark 0.6%; 7004C TDOF anchors;
      exact Woodbury damped apparent mass (D8 upgrade after V6 exposed 31%
      peak error in diagonal modal damping).
- [x] All methods end-to-end + MC (128 joint + 3×64 OAT draws × 8 seeds,
      detached) + sweeps (mount decades, damping grid, source damping,
      placement, T/df probe, adapter mass).
- [x] Mount identifiability gate (90% SE @ 87 Hz; dlnf/dlnk 0.449 vs 4.6%
      floor; ×0.5/×2 perturbation) + D7 response-limit proxy (tray_center
      ρ≈1.000, α≈m_tray, band-specific caveat).
- [x] 9 figures (tufte-linted, QA'd + regenerated, run+HYPOTHETICAL stamps),
      check.py, run_all.sh, runtime/manifest/files_changed/image_qa, packet.md.
- [x] OVERNIGHT (D10/D11): synthetic mounted-survey NUTS VOI experiment =
      STRUCTURED HONEST NEGATIVE (YELLOW): NUTS multimodal (R-hat 5–10, ESS 2,
      0 div; remedy made it worse); diagnosis = only 2/6 mount stiffness
      COMBINATIONS identifiable at the realized σ_f≈3.7% discrepancy floor
      (5/6 at the 0.3% noise floor) → model-form discrepancy is the binding
      constraint; §7 sharpened (overall level identifiable, per-axis split
      NOT, from frequencies alone). Packet §10, multimodality_diagnosis.json,
      fig_voi.png (NOT-CONVERGED flag). Checker 27g/2y/0r.
- [ ] AWAITING ANDREW: sign-off D2 input spec / D3 placement / D4 mount values
      / D7 proxy promotion; review packet §10 honest negative; then consider
      commit.
- [ ] CANDIDATE NEXT PHASE (needs Andrew go): symmetry-breaking-observable
      survey design — add mode-shape/FRF-amplitude (or force-gauge) data to
      split the mount axes; requires the degenerate-pair-safe subspace-MAC
      likelihood (logged below under 2026-06-10 follow-up). Pre-test FIM
      first (cheap), sampler second.

## 2026-06-10 ShockSat modal twin — recommended follow-up (logged, not started)
- [ ] **Differentiable subspace-MAC pseudo-likelihood (degenerate-mode fix).**
      The current MAC sensitivity arm diverges (82 div, R-hat 2.97) because the
      `eigh` backward has a `1/(λ_i−λ_j)` term that blows up at near-degenerate
      pairs (e.g. modes 6 & 7 at 117.63/118.53 Hz). Fix = make the shape
      likelihood operate on the INVARIANT SUBSPACE of each near-degenerate
      cluster, not individual eigenvectors: subspace-MAC / principal angles /
      mass-weighted cross-orthogonality (smooth in θ, no singularity). Lets MAC
      enter the headline likelihood with 0 divergences. Alt mitigations noted:
      repeated-eigenvalue sensitivity (Mills-Curran/Dailey/Friswell) or
      Lorentzian-broadened eigh backward. PRIOR ART IS RICH — NOT a patent
      candidate without a real FTO/lit scan (see chat 2026-06-10). Workspace
      `artifacts/reports/shocksat_fem_modal_twin_20260609/`; touch `run_nuts.py`
      `model`/`forward` + add as a new sensitivity arm.

## 2026-06-09 ShockSat FEM modal twin runner — IN FLIGHT, session 1 ended (out of credits)
Workspace: `artifacts/reports/shocksat_fem_modal_twin_20260609/`. Full handoff in
its `next_prompt.md` (read that first; also `decisions_log.md` D1-D8).
- [x] Task 0 RESOLVED: measured modes = `Final_FF_Test_Shapes_100121.ash` (33 modes
      w/ shapes on 76 nodes, parsed + validated); Modes.pch proven FEM-not-test.
- [x] NASTRAN deck parsed (67,720 grids); element library written + validated.
- [x] Per-PID stiffness blocks + mass assembled (~15 s runtime).
- [ ] BLOCKER: RBE2 double-dependency (Shock_Test_Instrumentation.blk) — fix per
      next_prompt.md, then nominal eigensolve vs NASA pptx freqs.
- [ ] Reduction, NUTS calibration, held-out QOI side-by-side, sensitivity,
      femap_handoff, checker, packet (plan + acceptance values in next_prompt.md).

## 2026-06-09 Proposed next 3 steps (post-cleanup; awaiting human go)
- [x] 1. Launch the ShockSat full parametric FEM modal twin runner (`docs/lab/shocksat_fem_modal_twin_runner_prompt.md`). Task 0 measured-modes provenance gates everything; human runs the FEMAP cross-check; lead reviews convergence + held-out coverage. STATUS: launched 2026-06-09, session 1 handed off mid-assembly (see top of this file).
- [ ] 2. Unblock the IP track: send the Beth email, write the dated invention-disclosure/conception record (Bayesian-7004C + F(k)), decide on the cheap provisional over A/D + B + H. Gates all public disclosure, including the blog.
- [ ] 3. Draft the Bilionis blog post from the seven BLOG-tagged entries in `notes/lessons-learned.md` (draft in chat first); publication waits on step 2's disclose-before-publish sequence.
- Runner-up: the FIM identifiability pre-test analysis (spec below) once the modal twin runner is in flight.

## 2026-06-09 ShockSat StatFEM Runner
Workspace: `artifacts/reports/shocksat_statfem_runner_20260609/`.
- [x] Phase 0: write priority deliverables, question framing, decisions log, and re-grounding state.
- [x] Phase 1: fetch ShockSat README, overview PDF, and Instrumentation/TestLog zip with provenance; disk-check and attempt header/range/listing for larger archives.
- [x] Phase 2: inventory fetched archives with sizes, SHA256 checksums, archive listings, extraction status, and minimum extracted working subset.
- [x] Phase 3: audit FEM/CAD package if fetched or document precise blocker; identify solver/file formats, units, node/element/material metadata when parseable.
- [x] Phase 4: extract instrumentation/test-log channel map and test metadata before plotting time histories.
- [x] Phase 5: generate first measured-data plots only after units/sample rates/channel map are credible.
- [x] Phase 6: write quantity contracts for acceleration, SRS, FRF, cross-channel transfer, modal frequency, mode shape/MAC, observation, and QOI.
- [x] Phase 7: write FEM/test alignment assessment with supported comparisons and blockers.
- [x] Phase 8: write StatFEM digital-twin v1 launch definition with observations, inferred variables, discrepancy, QOI, and held-out validation.
- [x] Phase 9: implement a checked StatFEM stub only if likelihood inputs and validation support it; otherwise stop at launch definition. Decision: stopped at launch definition because FRF/MAC likelihood inputs and held-out validation are not ready.
- [x] Phase 10: write the review packet, manifest, checker report, runtime accounting, and one-command replay.
- [x] ShockSat next action: extract/parse NASA correlation FRF assets and compute hammer accelerance FRFs from Test07 force channel 116 to selected response channels, then map those response channels to verified FEM grids for the first held-out FRF comparison. Result: FRF diagnostic computed and mapped, but low coherence and NASA/Test07 grid-convention mismatch keep it out of the likelihood.
- [x] ShockSat next action: recover more valid hammer hits/full Test07 archive and source-location metadata, then average impact FRFs and reconcile 9900001-style shock grids with NASA 11101/11110 SOL 111 correlation grids before any FEM/test FRF overlay. Result: full Test07 archive fetched and verified; four MAT hammer hits loaded and averaged; source metadata recorded; low coherence and source/grid convention mismatch still block FEM/test overlay.
- [ ] ShockSat next action: build an explicit Test07 source/response mapping audit that reconciles physical TestLog impact points and 9900001-style response grids with NASA SOL 111 force grids 11101X/11110Y and modal-test response grids; only then attempt a FEM/test FRF overlay.

## 2026-06-08 Pre-test sensitivity / FIM identifiability analysis (Opus tray FEM) — DONE 2026-06-09
Artifact-backed answer to "how many parameters can the scrappy test support" + experiment design.
Executed by lead (Andrew's "execute this" go). Workspace `artifacts/reports/fim_identifiability_opus_20260609/`,
`bash run_all.sh`, checker 15/15 PASS. See packet.md.
- [x] Candidate parameter menu: tray_E, strut_EA, strut_EI, joint_axial, joint_lateral (5).
- [x] Sensitivity Jacobian (exact analytic eigen/Fox-Kapoor) for modes AND load QOI; FIM = J^T Σ^-1 J.
- [x] FIM eigendecomposition (stiff/sloppy combos) + column-pivoted QR subset (cond≤100).
- [x] 1-sensor (auto-spectrum) and 2-sensor (transmissibility) cases — same headline.
- [x] "N identifiable" = 3 (band-conditional 1→2→3); joints unidentifiable; plots + where-to-hit/measure.
- [x] Profile-likelihood confirmation (joints flat across ±30%).
- [x] Honesty: labeled LOCAL FIM + profile; discrepancy NOT included (upper bound) — flagged in packet.
- FOLLOW-UPS (next_prompt.md): redesign to make joints observable; promote 3-of-5 to a real NUTS update;
  band-aware test plan; repeat WITH discrepancy. Possible reusable pre-test FIM gate — needs Andrew's OK.

## 2026-06-08 Patent prior-art dossier v1 — fold-in + next searches
- [x] Cue browser patent-DB prompt; receive dossier v1 (saved docs/proposal/patent_prior_art_dossier_v1.md; folded into patent_ideas_ranked.md).
- [ ] Next browser session: run the dossier SEARCH NEXT list (ABEMIS full family + pending "AI provisionals"; arXiv 2604.12688; force-limiting clearance CPC G01M7/02; NVH joint-impedance CPC F16F; acoustic metamaterial CPC G10K11; OSP patents; TO-with-model-uncertainty CPC G06F30/23+G06N7/01).
- [ ] Ask Doehring what the ABEMIS "AI provisionals" cover BEFORE any H/I filing.
- [ ] Consider one PROVISIONAL over the A/D + B + H combination to lock priority (cheap), pending PRF/attorney + disclosure-first.
- [ ] Professional claim-chart FTO before any filing (CPC F16F, G01M7/02, G10K11, G06F30/23; DE/JP/CN; defense/ITAR).

## 2026-06-05 Project Vision + IP Decision + Framing Challenger
- [ ] Send corrected Beth email (research credits + MA 511; disclosure-vs-publication timing) and get the IP-ownership determination in writing.
- [ ] Finalize and share the Bilionis proposal (Purdue-supported patent framing; rewrite patent section to co-inventor-friendly).
- [ ] Write the dated invention-disclosure / conception record for the property-keyed discrepancy (Sec 101 "method of testing/updating a physical structure" framing).
- [ ] Design the spatial-fails-vs-property-keyed-succeeds demo on the subscale tray (the Sec 103 non-obviousness evidence) under NUTS/HMC + convergence gate.
- [ ] Run a real patent-database / freedom-to-operate search (Google Patents / Lens.org) or route to an attorney.
- [ ] Review/steer the master-generated FRAMING CHALLENGER prompt (vs Stage 3 / Round 3 framing) BEFORE the human deploys it.

## Active
- [ ] Keep harness checkers immutable during trials.
- [ ] Finish 2DOF synthetic channels and NUTS/HMC posterior checks.
- [ ] Add MDOF reduced-order transfer-function prototype tests.
- [ ] Inspect `/Users/avoss/Downloads/check pages.pdf` for incorrect crop seams; record PDF page numbers, visible textbook page numbers, assumptions, and validation artifacts.

## Candidate Next Work
- [ ] Separate channel 2 and channel 3 forward models so interface modal and tray impact measurements are not duplicates.
- [ ] Add per-channel noise/discrepancy scaling and posterior predictive checks.
- [ ] Add NUTS/HMC sampler diagnostics instead of relying on acceptance rate alone.
- [ ] Make the MDOF prototype explicitly fixed-base and export matrix artifacts.
- [ ] Set a writable Matplotlib cache path in the pipeline.

## 2026-07-06 TRUE remodel loop run (workspace artifacts/reports/shocksat_true_remodel_loop_20260706)
Plan (card = docs/lab/shocksat_true_remodel_loop_runner_prompt.md; checker LOCKED d9cb1acd):
1. [done] pre-registration gate files + REUSED hashes + check.py SHA-lock (RED 2G/10R baseline).
2. code/femlib.py (element reassembly on fe_core, refine w/ hanging-node MPC ties, splits, thickness,
   added-connectivity, full-order eigsh, own-basis packages, frozen Hungarian pairing, theta_MAP).
3. code/mech_gates.py -> V1-V5 (detached; out/mech_gates.json). BLOCKS science if failed.
4. code/score.py (P1/P2 scalar dev scorer, one global gain, NO per-mode LSQ) + code/baseline.py (A0).
5. code/actions.py (edit-spec grammar + uniform random sampler seed 20260706) + code/diag.py (train-side
   residual fields) + code/loop.py (orchestration; never loads drive caches directly).
6. >=3 agent rounds + random track (eigensolve alloc 32 agent / 32 random / 16 vgates+spot; dev queries
   <=60/track); round summaries; funnel.
7. Finalists (<=3) + A0 + random-best: NUTS (S0 form, 4 chains x64), statFEM F(k) Q leg, leave-modes-out H,
   freeze VAULT_FREEZE.sha256 -> vault = Test04 (+XY) once -> S1/S2/S3 verdicts.
8. Figures (tufte skill + lint + legibility QA), packet.md, findings.md, runtime.json, run_all.sh,
   runs.md entry + project_log row (status verbatim from checker).

## 2026-07-22 Task Card A — ShockSat closure analyses (EXECUTING, lead as runner)

Workspace: artifacts/reports/shocksat_closure_analyses_20260722/ · hard cap 4 h active.
Recon done: all frozen inputs exist; A5 artifact FOUND (statfem_real_validation_20260617/out/
phase_likelihood.json, circ var 0.8536); A4 iid likelihood = armB_theta_only (per-chain draws retained).

- [x] INIT: source_manifest.json (SHA-256 all frozen inputs), verify loads
- [x] FREEZE: priority_deliverables / question_framing / assumptions_ledger / quantity_contracts /
      decisions_log; check.py + CHECKER.sha256 + RED-on-empty proof; run_all.sh skeleton
- [x] A1 subspace (known answer 0.019/0.029/0.259/0.355; block bootstrap; fig)
- [x] A5 phase recovery (hash + cite; provenance json)
- [x] A3 coverage+CRPS (known-answer reproduce 0.706-0.865/2.30x/0.98 FIRST; STOP if arrays missing)
- [x] A4 2-param profiled-nuisance whole-FRF profile (iid log10|H1|; inner-opt convergence at every point)
- [x] A2 sigma_f 5-prior NUTS sweep (reference reproduction gate; per-chain draws; predictive checks)
- [x] Verify input hashes unchanged; runtime.json; checker GREEN/YELLOW; packet.md; runs.md entry;
      next_prompt.md -> Task Card B (do NOT start B)

## 2026-07-22 Task Card B — ShockSat advisor closure report (COMPLETE)

Workspace: `artifacts/reports/shocksat_closure_report_20260722/`. Editorial synthesis only; Task Card A is the
checker-backed analytic source and prior report DOCX files are immutable inputs.

- [x] Re-ground from Task Cards A/B, A packet/results, predecessor report decisions, and project rules.
- [x] Freeze priority interpretations, human decisions, source inventory, and prior-DOCX hashes.
- [x] Build concise report figures: modal subspace/residual diagnosis, simple two-channel FRF comparison, and
      whole-FRF profile-likelihood diagnosis; lint and visually inspect each.
- [x] Build Markdown mirror and ≤9-page DOCX with one definitions table, one work-products-and-limits table, corrected
      likelihood direction, and explicit modal-update versus response-level StatFEM distinction.
- [x] Add checker with ≥25 numeric trace checks, SHA lock, RED-on-empty proof, page/definition/alt-text checks,
      one-command replay, runtime, before/after packet, and figure QA.
- [x] Run replay/checker, render every page, correct layout/content failures, then update runs log and project log.
- [x] Rebuild the opening from Bilionis's actual context: the stress-testing StatFEM proposal and his instruction
      to build/evaluate the method, identify gaps, and suggest improvements.
- [x] Remove advisor-facing GREEN/YELLOW/RED language and the “claims I will defend” posture; preserve all
      convergence and evidence limitations in ordinary technical language.
- [x] Explain the work chronologically before presenting results: why ShockSat, modal update, response-level
      likelihoods/discrepancy, held-out/load evaluation, then the model-form-remodeling pivot.
- [x] Re-render all pages, inspect at 100%, update checker/report packet/logs, and return the revised DOCX.

Completed 2026-07-22. The nine-page advisor brief now starts from Ilias's last-reviewed proposal and guidance,
uses pages 1–2 for chronology and method before presenting results, and contains no traffic-light shorthand or
defense-of-claims framing. Unused S1/S3/S4 labels were removed. All scientific convergence failures and limits
remain in ordinary technical language. Replay/checker, 34 numeric trace checks, a11y, and nine-page visual QA
were rerun; final DOCX SHA-256 `b4327f78728add7859b68889dd22f455229ba91ed197772d6b8b2ff7ed5ac91d`.

## 2026-07-22 ShockSat advisor brief — user-comment rebuild (COMPLETE; isolated `_sol` copy)

Planning authority is the user-edited `ShockSat_Bayesian_FEM_StatFEM_closure_brief.docx`, SHA-256
`e8e04f40bcc69c03634e5c6d94eb5beee64f5ebdcbe13f7882ab09f16ee01a8f`. It contains 10 unresolved Word
comments and two direct text edits; no tracked insertions/deletions. Andrew approved execution on 22 July. The
user-edited source DOCX remains untouched; all edits go to the isolated `_sol` DOCX, builder, figures, and checks.

- [x] Preserve the direct edits: remove “I treated that as the research question” and use Andrew's single
      final-month closure request in place of the prescriptive four-question/three-deliverable closeout.
- [x] Replace the early single-likelihood presentation with a chronological Bayesian-method matrix covering
      modal frequency, frequency+MAC, Beck shape, whole-FRF magnitude/phase, damping, modular discrepancy,
      M2/IFT, evidence ranking, and unimplemented Schneider-style correlated discrepancy. State data,
      likelihood/discrepancy, sampler, diagnostics, why tried, comparator, and result for each.
- [x] Move the modal subspace/prior-sensitivity graphic out of the main narrative. In the main text use an
      explicit prior comparator: prior-whitened variance = 1.0, four directions = 0.019–0.355, five directions
      = 0.872–1.166. Put full eigen/prior-sensitivity diagnostics in an appendix.
- [x] Make the two causal conclusions the report spine. Mean: the modal likelihood omits channel amplitudes and
      the implemented modular discrepancy is zero-centered, so it does not learn a channel/frequency bias mean;
      it is not yet proven that the FRF residual is orthogonal to every available parameter effect. Width: the
      observed residual scatter is large and structured, while the marginal discrepancy scale is transferred
      broadly to held-out channels, so calibration is obtained mainly by widening.
- [x] Add the log-amplitude predictive equation and an explicit mean/variance comparator showing that the
      implemented zero-mean discrepancy leaves the parameter-updated mean unchanged but increases covariance.
      State that a structured nonzero discrepancy mean could move predictions and was not implemented.
- [x] Delete the whole-FRF profile-likelihood graph from the main report; retain only a compact diagnostic table
      or appendix note if needed to support the nonconvergence explanation.
- [x] Expand held-out FRF evidence without cherry-picking: summarize all held-out channels, define a frozen
      selection rule, then show 4–6 small-multiple FRFs spanning improved, typical, and persistent-miss cases.
      Keep only data, original FEM, updated mean, parameter interval, and total interval.
- [x] Restrict the advisor-facing load section to measured shear X/Y. Remove normal-Z and its reconciliation.
      Define coverage, CRPS, FEM+6 dB, and the three envelope-to-distribution conventions (log-uniform,
      linear-uniform, Gaussian-95%) before reporting 8/10.
- [x] Expand the +54.02 evidence comparison into an explicit “modal evidence target versus held-out engineering
      target” result, or delete it if the exact held-out comparator cannot be stated plainly. Do not leave it as
      an unexplained diagnostic.
- [x] Change the work-products table to plain-language titles plus a “Where explained” column with section/page
      references. Answers in the Bayesian question table must begin Yes/No/Partly; broaden “what remains
      unresolved” to the full project rather than only the modal sensitivity run.
- [x] Rebuild the main narrative before the appendix, update source tracing/checker expectations, render every
      page, inspect at 100%, and resolve Word comments only after each mapped change is verified.

Completed 2026-07-22 in `ShockSat_Bayesian_FEM_StatFEM_closure_brief_sol.docx`; the user-edited source remained
byte-identical. Isolated checker: **OVERALL YELLOW {GREEN: 11, YELLOW: 1, RED: 0}, exit 0**. The inherited
sampler caveat is unchanged: 3/5 sigma_f sensitivity variants did not converge. Nine pages, two figures, 44
numeric source checks, a11y 0/0/0, RED-on-empty exit 1, final DOCX SHA-256
`ea5d30f8b1a5b75b48fbdbfde4bb0b06fe93441495dfaffb7e3fc3a742b3f948`.

## 2026-07-22 `_sol` versus Fable comparison (COMPLETE)

- [x] Compare both Markdown sources and rendered layouts, including opening order, Bayesian explanation,
      evidence/CRPS definitions, FRF density, literature positioning, and closure request.
- [x] Carry over only concise improvements that preserve the approved context-first narrative, measured-shear
      scope, four-panel FRF evidence, nine-page limit, and source-backed claims.
- [x] Rebuild `_sol`, rerun the isolated checker and render audits, and inspect every changed page.

Retained four Fable-inspired improvements: a concrete structured-mean example, a proper-score/units definition
of CRPS, a fully integrated marginal-likelihood versus local-linear/type-II-ML distinction, and a short
literature-positioning paragraph. Rejected the result-first opening, restored deleted sentence, six-panel FRF,
normal-Z appendix, and tenth page. Final `_sol` remains nine pages; checker **OVERALL YELLOW {GREEN: 11,
YELLOW: 1, RED: 0}, exit 0**; final SHA-256
`9adce4cf09a52cabe751c29286a98eef6a6fe20860caf05095409e7e677181df`.
# 2026-07-22 — Codex independent review of structured-discrepancy Task Card D

- [x] Inspect the supplied card, original closure brief, Febrianto et al., Schneider et al., and frozen in-project evidence.
- [x] Write an artifact-backed review identifying scientific, statistical, and execution risks.
- [x] Write and audit a separate dispatch-ready runner card without modifying or dispatching Task Card D.

Completed 2026-07-22. Static card audit: **OVERALL GREEN**. The supplied card and all predecessor workspaces remain untouched.

## 2026-07-22 — Make independent structured-discrepancy Card E autonomous

- [x] Remove all pre-start and between-stage human approval requirements from Card E.
- [x] Freeze numerical synthetic and measured-data rules that automatically choose stop, Stage 1-only closure, or joint Stage 2 NUTS.
- [x] Update and rerun the static card checker; preserve Task Card D and its running workspace.

Completed 2026-07-22. Revised Card E is autonomously dispatch-ready; static audit **OVERALL GREEN**. No science was launched.

## 2026-07-22 — Execute structured-discrepancy Card E

- [x] Re-ground from Card E, continuity logs, direct paper equations, and frozen project artifacts; restate priorities and claim ceiling.
- [ ] Freeze the isolated workspace: priorities, question, assumptions, quantity contract, inventories/registries, preregistration, hashes, checker canary, replay, and runtime accounting.
- [ ] Reproduce deterministic frozen known answers and run the S0–S3 exact-Gaussian synthetic gates on the actual split geometry.
- [ ] Follow `automatic_decision.json`: stop with a complete packet on any synthetic miss, otherwise run measured Stage 1 and only run joint Stage 2 when every frozen transition criterion permits it.
- [ ] Generate saved-script figures, Tufte lint, legibility QA, checker report, closure-brief correction, and narrow continuity-log updates copied from checker status.

Execution is autonomous within the 2 h Stage 1 / 8 h total active-runtime caps. No predecessor workspace or Card D directory will be modified.
