# Todo

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
