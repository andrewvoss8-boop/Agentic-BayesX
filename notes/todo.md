# Todo

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

## 2026-06-08 Pre-test sensitivity / FIM identifiability analysis (Opus tray FEM) — SPEC PENDING
Artifact-backed answer to "how many parameters can the scrappy test support" + experiment design.
- [ ] On the Opus Phase-1 tray FEM (runs/fem_phase1/opus/), define the candidate parameter menu
      (joint axial k, joint lateral k, joint loss eta, base-plate compliance, strut EA, tray E, ...).
- [ ] Compute the sensitivity Jacobian J = d(observable feature)/d(param) for the observable modes
      AND d(load QOI)/d(param); assemble the Fisher Information Matrix (FIM) = J^T Sigma^-1 J.
- [ ] FIM eigen-decomposition: report stiff vs sloppy parameter COMBINATIONS (sloppy-models view);
      SVD/QR subset-selection downselect with a stated condition-number/collinearity threshold.
- [ ] Do it for the 1-sensor (auto-spectrum) and 2-sensor (transmissibility, input cancelled) cases.
- [ ] Output: "N identifiable params/combinations" with plots + where-to-hit / where-to-measure
      (experiment design = FIM maximized over sensor/excitation). Confirm with profile likelihood.
- [ ] Honesty: FIM = LOCAL/practical identifiability; confirm structural cases w/ profile likelihood;
      run WITH the discrepancy present; held-out coverage is the referee.
- Spec as an Opus runner task (awaiting human go).

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

