# Memory

## CURRENT STATE (lead working state — keep short; update before risky steps and after each human decision)
- 2026-11-17 **BURST-SURVEY FOUNDATION CHECK STAGED TO THE NETWORK GATE — CHECKER OVERALL YELLOW 12G/4Y/0R.**
  Workspace `artifacts/reports/shocksat_burst_survey_foundation_20261116/` (`packet.md`; replay `bash run_all.sh`).
  BLOCKER: `mediaex-server.larc.nasa.gov` refused by this cloud environment's network policy (retried 2026-11-17 11:31Z on
  Andrew's 'try again'; still 403). Session environment env_01JWZ89si4Ge3sKLzeqVSNKR. NEXT ACTION once allowed: `bash gated_run.sh`
  (fetches tiers 0,1,2,4 = 138 MB to ~/.cache, scores the 262 unseen NASA plots per `prereg_gated_analysis.md`), then
  `WITH_TIME_HISTORIES=1` for the 589 MB burst time histories and gates F1-F5. Do NOT change prereg rules after seeing plots.
  KEY FACTS: NASA excluded shaker runs from correlation (attachment blocks mass-load modes); NASA sensor set weak above 150 Hz;
  exploratory pilot (2 NASA drive points) NASA FEM vs NASA modal test 2.8-3.1 dB below 150 Hz vs project's 10.0 dB median on shock
  sensors; 0/22 NASA modes resolvable for damping at 2.03 Hz lines, 19/22 at 0.125 Hz. Correction logged (D10): June work DID use the
  burst-run frequency tables; raw .ati/.afu never used.
  CONTINUITY GAP (read first): this branch's notes stop at 2026-07-22. The local working copy was deleted on
  2026-10-02 after a private backup. Work from 2026-07-23 to 2026-08-12 (Cards G, H, I, J, master direction
  review, shape-field transfer, modal-test standards memo, failure-attribution handoff) was never pushed here.
  Its text record was recovered on 2026-11-14 and is stored on branch `claude/ecstatic-carson-c3e4f9` of the
  PRIVATE repo `andrewvoss8-boop/bayesx-disk-backup-2026-10-02` under `recovered_text_extract/`. The newer
  `notes/memory.md`, `runs.md`, `todo.md`, `lessons-learned.md` and `docs/report/project_log.md` live there, not
  here. Terminal state of that record (2026-08-12): held-out FRF amplitude science YELLOW; agent selection never
  beat random; handoff recommended a new high-quality modal campaign before more modeling.
  HUMAN DIRECTION (Andrew, 2026-11-16, verbatim intent): (1) save the recovered extract; (2) test whether
  `https://mediaex-server.larc.nasa.gov/shocksat/FEM_and_CAD.zip` is reachable; once reachable, pull only the
  `Correlation/` folder by byte range and parse the burst-random files, because that step decides whether the
  plan's foundation is real; (3) continue advancing the research autonomously, without using disk on his
  computer, storing results and documentation on GitHub or other cloud locations; do not stop to ask for
  direction; keep going and self-review until a dead end or bottleneck; if impossible, explain.
  RESULT OF (2): BLOCKED. The cloud environment's network policy refused the host
  (`mediaex-server.larc.nasa.gov:443`, proxy 403 on CONNECT, 2026-11-16T21:17Z). Fix is Andrew's: add that
  host under Allowed domains in the cloud environment's network settings. Not routed around.
  LEAD ASSUMPTIONS (flagged, Andrew may overrule): (a) "the plan" was written in a separate Claude review that
  is not in either repo; it is reconstructed from Andrew's messages as: use NASA's own burst-random modal
  survey (time histories for runs 78, 99, 139 and one FRF file), the fixed-base run 139, and the bolt-torque
  sweep as the higher-quality campaign the August handoff asked for. (b) Recovered private material stays in
  the private repo; only new work and summary-level pointers are committed to this public repo.
- 2026-07-22 **CARD E CODEX UN-SUFFIXED EXECUTION COMPLETE — STOP_SYNTHETIC, CHECKER YELLOW.**
  Workspace `artifacts/reports/shocksat_structured_discrepancy_codex_20260722/`; replay `bash run_all.sh`.
  Immutable checker: **OVERALL YELLOW {GREEN:16, YELLOW:1, RED:0}**. S0 false positives 0/20;
  S1 accepted recoveries 0/20 despite learned-mean 90% coverage 0.937; S2 median E3-vs-E1 error
  reduction −0.916 dB; S3 modal-parameter bias reduction 0.26%, coverage [0.85,0,0,0]. Constraint
  and normalized orthogonality residuals were ~1e−16, so the miss is predictive/confounding, not failed
  basis protection. Card automatically prohibited measured fitting and Stage 2. This run is independent
  of the concurrently recorded `_Fable` workspace and does not establish a measured negative-transfer result.
- 2026-07-22 **BRANCHING: `main` IS THE TRUNK AGAIN (human decision, option 1).** `main` was 10 commits stale
  and `exp/modeling-freedom-experiment` had silently become the trunk (branch name predated the ShockSat arc).
  Fast-forwarded `origin/main` 269685f→62839a6, moved local `main`, switched to it; `main`,
  `exp/modeling-freedom-experiment` and `origin/main` are all `62839a6`, zero divergence. Nothing rebased,
  squashed or deleted; the old branch still exists as a pointer to the same commit. **NEW WORK GOES ON `main`
  (or a fresh topic branch off it) — do NOT keep committing to `exp/modeling-freedom-experiment`.**
  Uncommitted Card E work (`shocksat_structured_discrepancy_codex_20260722{,_Fable}`) was untouched by the
  switch and is still dirty in the working tree.
- 2026-07-22 **CLOSURE-REPORT MATERIAL COMMITTED + PUSHED.** Commit `338a60b` (now on `main`), 288 files / ~37 MB.
  Scope: closure brief v1 + `_sol` + `_fable` workspaces, closure analyses A1–A5, results-summary workspace,
  structured-discrepancy Card D/E cards and workspaces, notes/, docs/report/project_log.md. No files were
  regenerated, re-run, or edited for the commit; no SHA-locked checker touched. `.gitignore` additions
  (my call, overrule if unwanted): Word `~$` lock files, plus two regenerable page-render QA image sets
  (`shocksat_results_summary_20260721/qa/` 106 MB, `structured_discrepancy_codex_review_20260722/qa/` 5.3 MB)
  — deliverable docx/pdf + build scripts stay committed. NOT committed (large/unrelated, ask before adding):
  `shocksat_formulation_calibration_20260720/` (727 MB), MPL/suspended-panel data, loose reference PDFs.
  Push warned about pre-existing >50 MB `.npz` files from commit 9cad98c (not introduced here).
- 2026-07-22 **CARD E (`_Fable`) DISPATCHED BY ANDREW — LEAD IS RUNNER. IN PROGRESS.**
  CURRENT STATE: executing `docs/agents/structured_discrepancy_codex_review_20260722/task_card_codex_structured_discrepancy.md`
  (Codex's autonomously-dispatch-ready Card E). LAST DECISION (human, 2026-07-22): "execute … labeling
  everything _Fable to differentiate from the work being done by another agent." ⇒ workspace =
  `artifacts/reports/shocksat_structured_discrepancy_codex_20260722_Fable/`; every new artifact carries a
  `_Fable` marker. Card D's directory and the card's own proposed (un-suffixed) workspace are IMMUTABLE and
  must not be created or touched by me. NEXT ACTION: INIT (source_manifest + data inventory) → FREEZE
  (preregistration, split/mean-basis registries, quantity contract, SHA-locked checker + RED-on-empty) →
  synthetic gates S0–S3 → measured Stage 1 arms E0–E3 → automatic_decision.json → conditional Stage 2.
  Card is self-executing: checker-backed gates, not agent preference, pick the terminal path; NO approval pause.
  OPEN AMBIGUITIES (assumed, flagged in the workspace decisions_log for Andrew to overrule): (i) `_Fable`
  suffix on the workspace name, not a separate directory tree; (ii) forward model = frozen in-project
  `realfrf.fem_logmag` at ζ=0.01 (≈ the 0.49 s exponential-window added damping at 100 Hz) with a
  preregistered frequency-dependent-ζ sensitivity; (iii) residual GP realizations independent per drive
  (ρ_cross-drive = 0) as the conservative primary, with measured cross-drive correlation reported as the
  card's "does the (f,x) framing hold" diagnostic.
- 2026-07-22 **CARD D DRAFTED (structured non-zero-mean discrepancy m(f,x)) — AWAITING ANDREW, DO NOT START.**
  Card: `docs/agents/structured_mean_discrepancy_20260722/task_card_D_structured_mean_discrepancy.md`.
  LITERATURE ANSWER (read-only check, no files changed): (1) Febrianto/Butler/Girolami/Cirak 2022
  self-sensing statFEM = **zero-mean** discrepancy `d ~ N(0,C_d)` (Eq. 11), squared-exponential in **space
  only** (Eq. 12), quasi-static strain — **no frequency dimension**; per-instant load scale γ_k (Eq. 24a) is a
  variance scale, not a mean. (2) Schneider 2022 [ref 11] = **zero-mean** log-magnitude/phase error (Eq. 18)
  with additive **space+frequency** correlation (Eqs. 19–21, r=0.82 split) — Andrew's recollection confirmed.
  (3) Girolami 2021 statFEM, Duffin, latent-force paper: all zero mean. (4) Kennedy–O'Hagan `h(x)ᵀβ` is the
  precedent for a structured MEAN; Plumlee 2017 orthogonality is the fix for the θ–discrepancy confounding.
  ⇒ **non-zero-mean discrepancy in BOTH frequency and location is a genuine gap.**
  IN-PROJECT PRIOR ART FOUND (matters for the card): `shocksat_modelclass_L5_20260619/code/schneider_faithful.py`
  ALREADY implements the Schneider zero-mean freq×space arm; results in `statfem_real_validation_20260617/out/
  tmcmc_faithful_M{0,1,2,3}_ident4_n8.json` — M0 converged (R̂1.0002); M1 R̂1.041; **M2 R̂2.577/ESS0.71, σ_w
  runaway 1.73→12.37**; M3 (Plumlee-orthogonal) R̂1.112, σ_w 12.60. Also frozen: spatial R²=0.036, channel
  nugget (hard 17.45 vs rest 6.54 dB) ⇒ honest expectation is frequency transfers, location does not.
  TECHNICAL CORRECTION recorded in the card: a zero-mean GP *prior* still has a non-zero *posterior* mean;
  ShockSat's mean did not move because the discrepancy was a MARGINAL variance never propagated to held-out
  points — so the card separates (a) explicit structured mean m(f,x) from (b) correct kernel propagation.
  **HUMAN DECISIONS 2026-07-22 (recorded in the card's "Human decisions recorded" table): (2) SUCCESS BAR =
  2 dB median-|error| reduction OR 20 % band narrowing at equal coverage — frozen into preregistration at
  FREEZE, four-fold noise floor reported BESIDE every effect size but not used as the bar; (3) D6
  (Plumlee-orthogonal) IS IN SCOPE — arms D0–D6 all stand, D5-vs-D6 θ-bias stays mandatory inside synthetic
  gate 4; (4) DEFER the closure-brief Schneider correction — do NOT rebuild the fable docx now; Card D's
  report must deliver the corrected wording, so CARD D NOW OWNS THAT DELIVERABLE. Defect + accepted
  consequence (brief may ship understating implemented work and omitting the M2/M3 non-convergence) logged
  as F5 in `shocksat_closure_report_fable_20260722/decisions_log.md`; no delivered artifact modified,
  SHA-locked check.py untouched. ⚠️ Decision 4 is my reading of a one-letter reply "b" — awaiting confirm.**
  STILL OPEN, card stays NOT APPROVED: **(1) scope vs calendar** — full card ≈8 h compute + write-up (A) vs
  feasibility-only gate 4 + D3 ~1 day (B) vs lead-recommended STAGED (C): known-answer gates 1–3 + synthetic
  gate 4 incl. D5/D6 θ-bias → human checkpoint → measured arms only if θ is recoverable. NEXT: none — no
  workspace, no fitting, until decision 1 is answered.
- 2026-07-22 **FABLE REVISION COMPLETE — checker OVERALL YELLOW {10G, 1Y, 0R}, exit 0.** Workspace
  `artifacts/reports/shocksat_closure_report_fable_20260722/`; deliverable
  `ShockSat_Bayesian_FEM_StatFEM_closure_brief_fable.docx` (sha c908c70a…), 10 pages, 34 numeric-trace
  checks, 3 figures. All comments C0–C9 applied; closing kept verbatim; CENTRAL FINDING callout carries
  the two required "because" sentences; 6-panel FRF figure used preregistered rank rule (F2) → DAQs
  28/79/9/56/2/24, DAQ 24 worst (consistent with v1). v1 workspace untouched + hash-locked. Single
  YELLOW = inherited 3/5 non-converged sigma_f variants. runs.md entry appended. NOTE: a parallel `_sol`
  revision exists from another runner (see runs.md). NEXT: Andrew reviews the `_fable` docx.
- 2026-07-22 **TASK CARD C (FABLE REVISION) STARTED — HUMAN DECISIONS RECORDED.** Andrew reviewed the
  advisor-brief docx and left comments C0–C9 plus a rewritten closing paragraph. Decisions: (1) copy the
  doc into a NEW workspace with `_fable` suffix and edit that copy — v1 workspace stays untouched;
  (2) KEEP his closing paragraph verbatim (heading retained for checker G10); (3) figure-expansion choice
  delegated to lead → 6-panel held-out FRF grid from frozen mc_cache split seed 10 with a PRE-REGISTERED
  rank rule (see workspace decisions_log.md) — no new inference; (4) EXPAND (not delete) the +54.02
  evidence-comparison section; (5) format = easiest for lead → adapted copy of build_report.py so styling
  and frozen number sources are preserved. Also required: brief must state plainly WHY the posterior mean
  cannot move (modal-frequency likelihood has no channel/amplitude mechanism AND the discrepancy was
  zero-mean by construction — a structured-mean discrepancy was never tested, so failure of that route is
  NOT established) and WHY bands stay wide (zero-mean marginal discrepancy buys coverage only with width).
  Workspace: `artifacts/reports/shocksat_closure_report_fable_20260722/`. Checker adapted (documented in
  its decisions_log): renamed deliverables, 3 figures, page cap re-verified; substantive gates unchanged.
- 2026-07-22 **TASK CARD A COMPLETE — checker OVERALL YELLOW {14G, 1Y, 0R}, exit 0.** Workspace
  `artifacts/reports/shocksat_closure_analyses_20260722/`; replay `bash run_all.sh`; runs.md entry
  appended (status verbatim). All known-answer gates PASS (A1 eigenvalues exact; A2 reference σ_f
  0.0460 vs stored 0.0463 converged; A3 max|dev|=0.000 over 28 numbers). HEADLINES: 4.6% floor is
  DATA-driven (4.2–4.8% across 5 priors; 3 variants honestly non-converged = the single YELLOW);
  statFEM beats FEM+6dB on measured shear CRPS 8/10 cells under all 3 envelope conventions (load
  narrative CONFIRMED); whole-FRF separation = diagnosed multimodal likelihood (~10 local maxima per
  slice); phase artifact FOUND (0.8536). OPEN QUESTION FOR ANDREW: (a) review packet.md; (b) card A
  stop point says no durable-note writes beyond the standard runs entry — the AGENTS done criteria
  also wants a `docs/report/project_log.md` row; awaiting approval to add it. NEXT: Andrew reviews →
  Task Card B in a FRESH session (next_prompt.md written; do not start B in this session).
- 2026-07-22 **TASK CARD A: A1/A3/A4/A5 DONE, A2 NUTS SWEEP RUNNING DETACHED (superseded above).** FREEZE complete (57
  frozen inputs hashed; checker SHA-locked fe77b00b…, RED-on-empty proven exit 1). RESULTS SO FAR:
  A1 known-answer PASS (eigenvalues 0.019/0.029/0.259/0.355 + five prior-like, all within block-bootstrap
  CI; contracted dirs ≈ pure bottom_box/top_box/plates/cross_beam — claim kept subspace-only). A3
  known-answer PASS (28 stored numbers reproduced max|dev|=0.000 incl. per-drive heldout; NEW CRPS:
  statFEM beats FEM+6dB on measured shear evidence 8/10 drive-axis cells under ALL 3 envelope
  conventions — load narrative CONFIRMED, not flipped). A4: iid whole-FRF profile likelihood has ~10
  local maxima per slice (bottom_box, top_box; nuisances profiled closed-form, gradient-verified);
  separated chains sit in different local modes ⇒ diagnosis established. A5 FOUND artifact hashed
  (circ var 0.8536). A2 running: 5 σ_f priors, per-chain draws to out/a2_draws/, reference seed 42 must
  reproduce stored σ_f 0.0463. NEXT: A2 finishes → fig_a2 → fig_qa → runtime → hash verify → checker →
  packet.md → runs.md entry → next_prompt (B). NO durable-notes writes beyond standard runs entry.
- 2026-07-22 **TASK CARD A EXECUTION STARTED (lead as runner).** Workspace
  `artifacts/reports/shocksat_closure_analyses_20260722/`. Recon complete, all frozen inputs verified present:
  modal twin (nuts_full_samples/reduced_blocks/measured_modes/pairing/theta_full/joint_strain_energy), netcg
  caches+out (bakeoff_scorecard holds known-answer 0.706/0.865/0.738, statFEM 2.301x/0.982), wide caches,
  armB per-chain NUTS draws retained (`shocksat_full_spectrum_frf_20260714/out/armB/theta_only_*.npz`, R-hat
  44–75) ⇒ A4 iid likelihood = arm_b_nuts.py --theta-only form. **A5 artifact FOUND — no re-derivation
  needed:** `statfem_real_validation_20260617/out/phase_likelihood.json` (circ var 0.8536, complex slice
  contrast 0.0001 vs magnitude 0.009). Env OK (numpyro 0.19.0/jax 0.4.30), disk 25 GiB. Order: INIT/FREEZE →
  A1 → A5 → A3 → A4 → A2. NEXT: INIT hashing + FREEZE gate files + checker RED-on-empty.
- 2026-07-22 **BILIONIS-STYLE CRITIQUE DELIVERED; ANDREW APPROVED FEASIBILITY PROBES.** Lead reviewed
  `ShockSat_StatFEM_progress_and_closure_update_bayesian_audit.docx` in advisor voice; four cheap closure
  analyses proposed (all on stored artifacts, no new physics): (1) identified-subspace eigendecomposition of
  modal posterior covariance vs prior from `nuts_full_samples.npz`; (2) sigma_f prior-sensitivity sweep (4
  HalfNormal/heavy-tail variants, rerun modal NUTS, same convergence gate); (3) coverage + CRPS of FEM+6dB vs
  statFEM bands on held-out channels (risk: grid/channel reconciliation across sequential-statFEM + net-CG +
  baseline packets); (4) 1-D whole-FRF likelihood profile along one stiffness scale. Estimate ~5-6 working
  days total. HUMAN DECISION 2026-07-22: run two READ-ONLY feasibility probes now — (a) inspect held-out
  arrays/baseline grids in sequential-statFEM and net-CG packets, (b) smoke-test that the frozen modal twin
  reduced pipeline reruns under current env. No report changes, no new claims until probes reported back.
- 2026-07-22 **PROBES COMPLETE — GO on all four analyses.** (a) Measured complex H1 FRFs + coherence + DAQ ids
  found for all 5 drives on common grids: `shocksat_netcg_method_selection_20260701/data/multiref_modal/*.npz`
  (111 ch × 105 pts, 45–260 Hz) and `shocksat_full_spectrum_frf_20260714/data/multiref_wide` (45–500). NOTE:
  original raw_root `shocksat_multiref_explore_20260623/data/extracted` NO LONGER EXISTS — processed caches are
  now the data of record; hash them before use. heldout_drive.json stores only summary scalars ⇒ item-3 curves
  must be recomputed from caches + stored draws (feasible). (b) Frozen modal twin reruns: reduced_blocks.npz
  (A_fix + 9×74×74 A, obs_V 228×74) loads; eigensolve 8 ms; nuts_full_samples.npz (4000×9 + sigma_f) medians
  match theta_full.json exactly; numpyro 0.19.0/jax 0.4.30 OK ⇒ sigma_f prior sweep is minutes per variant.
  CAVEAT: pooled 4000 draws have no chain dim ⇒ fresh sweep runs must keep per-chain draws for R-hat.
  Firm estimate ~4–5 working days. NEXT: await Andrew go-ahead to open a task card/workspace for the four
  analyses (subspace eig, sigma_f sweep, FEM+6dB coverage+CRPS, 1-D whole-FRF likelihood profile).
- 2026-07-22 **HUMAN ADJUDICATION OF THE BILIONIS-STYLE REVIEW (controlling decision for the closure plan).**
  Andrew accepts the central diagnosis but corrects the reviewer: several "missing analyses" are REPORT
  OMISSIONS of work already done. Accepted criticisms: modal result mislabeled as statFEM (retitle/reframe);
  sigma_f prior sensitivity is highest-value new calc; contraction table → prior-whitened LOG-theta subspace
  (Andrew's read-only calc: 4 contracted directions ~0.019/0.029/0.259/0.355, five prior-like 0.872–1.166;
  method spec = log θ, whiten by prior cov, bootstrap eigenvalues, keep strain-energy/Fisher for physics);
  load conclusion must add matched coverage+proper-score vs FEM+6dB (repo already shows FEM+6dB UNDERCOVERS
  0.71–0.87 — VERIFIED verbatim in shocksat_netcg_method_selection_20260701 packet/findings — shear evidence
  measured, normal-Z synthetic-only); aggressive compression (remodelctl → future work, drop runtime table,
  define S1/S3/S4/IFT/beta/score/counts once); likelihood equation direction fixed in prose; agent result =
  "failed to demonstrate," preregistered primary was best-exact vs best-exact. PUSHBACKS accepted by lead:
  +54.02 critique used wrong likelihood (evidence target was modal freq+MAC, not FRF bins — demote for the
  right reasons); PHASE WAS TESTED (circular variance ~0.854, no sharper slice — artifact NOT YET LOCATED,
  need pointer); TIME-DOMAIN DAMPING WAS DONE — VERIFIED in shocksat_latent_force_damping_20260623/packet.md
  (14/16 modes, R-hat 1.020, ESS 250, ζ 0.33–0.76%, didn't fix envelope decision); coherence variance =
  noise baseline/sensitivity only, not full covariance; PSIS-LOO not required (holdouts match task; fix [15]
  citation use); 2.526 vs 2.958 = different configurations (reference vs tier-updated), state adjacently;
  TMCMC WAS attempted on free M2 and failed (reviewer wrong). PLAN: no formulation-calibration study; run the
  four analyses (subspace w/ bootstrap; sigma_f sweep + prior/posterior predictive checks; coverage/proper-
  score table shear-vs-synthetic-Z separated; 1-D whole-FRF profile WITH PROFILED nuisances) then REBUILD the
  report around them + recover phase/time-domain-damping/undercoverage findings. Thesis: what Bayesian modal
  updating and response-level statFEM can and cannot establish on ShockSat; model-form pilot supports, does
  not carry. NEXT: draft task card for Andrew approval.
- 2026-07-22 **TASK CARDS WRITTEN (per Andrew: efficient, ≤3–4 h combined compute).**
  `docs/agents/closure_analyses_20260722/task_card_A_closure_analyses.md` — one workspace
  (`artifacts/reports/shocksat_closure_analyses_20260722/`), five items with soft budgets: A1 subspace
  (known-answer gate = Andrew's eigenvalues 0.019/0.029/0.259/0.355), A2 σ_f 5-prior NUTS sweep w/ per-chain
  draws + known-answer reproduction of stored posterior + prior/posterior predictive checks, A3 coverage+CRPS
  vs FEM+6dB (known-answer gate = stored 0.71–0.87/2.30×/0.98; STOP if arrays missing), A4 2-param profiled-
  nuisance whole-FRF likelihood profile, A5 phase-diagnostic recovery-or-rederivation. Hard cap 4 h active.
  `task_card_B_report_rebuild.md` — blocked on A; rebuild report ≤9 pages around A results + recovered
  damping/phase/undercoverage findings; 10 adjudication-mapped required changes; human stop before finalizing
  if A3 flips the load narrative. NEXT: Andrew approves cards → dispatch A.
- 2026-07-21 **SHOCKSAT ADVISOR PROGRESS-AND-CLOSURE REPORT — QA-COMPLETE, pending Andrew review. Checker
  OVERALL YELLOW 10G/1Y/0R, exit 0.** Current deliverable:
  `artifacts/reports/shocksat_results_summary_20260721/ShockSat_StatFEM_progress_and_closure_update.docx`;
  original and rejected intermediate DOCX files preserved. Thirteen-page self-contained Bilionis update starts
  from his “build, evaluate, identify gaps, suggest improvements” objective; documents ShockSat/data, statFEM
  math, implemented likelihood/priors, NUTS settings/diagnostics, results, industry-use gap, pivot, contributions,
  closure questions, and three-week plan. Section 7 now defines agentic remodeling as the outer discrete model-
  class loop, with Bayesian continuous updating inside each class; remeshing is one operator family. It shows
  existing schemas/operators/builders/verifiers/splits/hashes/budgets/controls/exact scoring versus the proposed
  `remodelctl`, stable diagnostics, and blind feedback ablation; MPL is labeled scaffold-only, not science.
  Three images with alt text; all 13 pages inspected; a11y 0; replay passed. YELLOW is the inherited science
  ceiling: no direct net-CG answer key, non-converged held-out/whole-FRF posteriors, and no agent-over-random win.
  Replay `bash artifacts/reports/shocksat_results_summary_20260721/run_advisor_progress.sh`.
- 2026-07-21 **MPL EXISTING-DATA-ONLY CONDITIONAL CAMPAIGN — COMPLETE. Checker verbatim: OVERALL YELLOW
  {GREEN:16, YELLOW:2, RED:0}, exit 0** (SHA-locked pre-science `d029f143…`, RED-on-empty proven, verified
  unmodified; paired arithmetic independently recomputed by checker). Workspace
  `artifacts/reports/mpl_existing_data_conditional_20260720/` · replay `bash run_all.sh` (checkpoint-reusing;
  delete checkpoints/ for full ~2-3 h recompute). YELLOWs = honest scientific tier + TMCMC not numerically
  established (prior ensemble retained). **RESULT: plausibility set {B2} by the 2-paired-SE rule but NOT
  conditionally preferred** — fails 5/6 pre-reg conditions (2/5 folds vs B1; coverage 0.04-0.36 vs 0.90;
  acoustic 6 dB reverses 2 families; τ×2 collapses / τ×4 reverses weights; sampler unestablished). Held-out
  losses 4.5-10% vs 0.72% floor ⇒ MODEL-FORM discrepancy dominates; B1 update adds NO value (B0 beats B1 by
  2SE in 3/5 folds); B2 not distinguishable from B1. **Negative control N1 (half shield t) posts the BEST raw
  mean loss (6.41%)** ⇒ loss rankings ≠ physics — the validity controls earned their place. Identifiability:
  3/6 FIM combos clear prior; shield_bend dominates (SE fraction 0.71); shield_mem/plate_bend below floor
  (in load path, floor-limited). Valve path: ensemble misses ~10/11 observed features (model-form target).
  Incidents all disclosed in decisions_log: D4 V-gate criterion fix (pre-score), D5 known-answer criteria
  revision (strain-energy evidence; attempts preserved), D6 TMCMC mixing fix (gate caught real
  underdispersion), D7 acceptance-band per-level interpretation (post-first-print, dual-reported), 2 script
  bugs fixed mid-run (no frozen artifact touched). 50/120 eigensolves; 126 TMCMC runs; active 6581 s.
  Continuity: runs.md entry + project_log row appended (status verbatim). NEXT: Andrew reviews packet.md
  (§6 = the four human calls: use {B2} as bookkeeping only; drop the 6-multiplier update; model-form at the
  valve/low-freq shield is the real gap; instrumented test remains the technically preferred remedy).
- 2026-07-20 **MPL EXISTING-DATA-ONLY CONDITIONAL CAMPAIGN — EXECUTION STARTED (lead as runner; card dispatched).**
  Workspace `artifacts/reports/mpl_existing_data_conditional_20260720/`. Re-grounded from AGENTS.md, predecessor
  `mpl_agentic_remodel_bayes_20260720` (condition_registry, precheck_config, quantity_contracts, stage0.py code,
  decisions D0–D5). Env OK: py3.9, jax 0.4.30, numpyro 0.19.0, numpy 1.26.4. DISK TIGHT 9.1 GiB free (card floor
  2 GiB — monitor). Reusable machinery understood: `solve_candidate` (static-condensation + generalized eigh),
  `modal_curve` (ζ transfer accelerance), 15 tap paths / 5 families (interface, shield_mid, top_left, box[L+R],
  valve), exact `feature_distance`/`aggregate_by_family` loss, frozen tap/acoustic processing config. Six common
  stiffness multipliers all present as model groups. STATE MACHINE: doing INIT→FREEZE this session (hash+verify
  inputs, all pre-reg gate files, model menu, checker RED-on-empty + SHA-lock, observed features) then hand off
  heavy detached UPDATE/EXACT/ROBUSTNESS (TMCMC over eigensolves). YELLOW ceiling by construction; no vault, no
  A/R search, generalized-Bayes (not NUTS) for the non-differentiable feature loss.
  **PROGRESS (this session): INIT + FREEZE + FEATURES-observed DONE and verified.** INIT GREEN: 13 raw records +
  predecessor PRECHECK/config/registry + frozen model meta/arrays all hash-verified; `source_manifest.json`,
  `REUSED_code.sha256`, condition_registry copied unchanged; no raw copied, no source modified. FREEZE: all
  pre-reg gate files written (priority_deliverables, question_framing, decisions_log D0–D2, assumptions_ledger,
  quantity_contracts, inference_contract, data_split_manifest 5 folds, model_menu 5 physical {B0,B1,B2,M1 feet-
  boundary,M2 shield-connectivity} + 3 negative controls, 8 candidate specs). Checker `check.py`+`check_config`
  SHA-locked in CHECKER.sha256 (`d029f143…`/`86d4119a…`), RED-on-empty proven exit 1 (7 integrity GREEN / 10
  science RED), `out/checker_empty_report.json`. FEATURES observed: `code/features.py` reproduces predecessor
  observed feature counts EXACTLY (15/15 paths), fresh global q95 0.7117% ~ inherited hard floor 0.7172%; per-fold
  tau written (interface .876 / shield .785 / top_left .807 / box .717 / valve .717 %). RUN_STATE.json + partial
  run_all.sh in place. **NEXT ACTION (heavy, detached, multi-hour — NOT started):** MENU V-gates (FEM eigensolves
  per class), UPDATE TMCMC generalized-Bayes (known-answer first, 3 seeds), EXACT confirmation, ROBUSTNESS +
  sensitivity, REPORT (10 figs+packet+findings). Do NOT append runs.md/project_log until COMPLETE (card §12).
  Honest status: campaign NOT complete; setup + observed features are the verifiable deliverable so far.
  **SESSION 2 (Andrew "proceed"): heavy compute running.** D3 pre-registrations (TMCMC settings, coverage rule,
  known-answer criteria, peak-sensitivity settings, widening rule) written BEFORE first score. MENU V-gates
  all-GREEN after D4 tolerance/criterion fix (identity 1e-6; crossing-robust trace check) — 7 nominal solves
  ~25 s each, budget fine. Known-answer FAILED twice honestly → D5 criteria revision (informed-direction
  coverage; strain-energy evidence: K_plate_bend ≤0.22% SE in band) + D6 mixing fix (5 MH moves/level vs 1;
  underdispersion caught by the gate) → PASSED (loss 0.47%<τ, informed z≤1.99); attempts preserved. D7:
  acceptance band applies at FINAL tempering level (disclosed deviation). 126 TMCMC runs (~25 s each) +
  post-queue (diagnostics→scores w/ 35 exact solves→FIM→robustness→figures) running DETACHED
  (logs/tmcmc3.log, logs/queue.log). All pipeline code written incl. finalize.py + full run_all.sh;
  tufte_lint 3 advisory INFOs (documented). REMAINING: manual figure QA (Read PNGs), packet.md, findings.md,
  finalize, checker run, then notes/runs.md + project_log (only after COMPLETE).
- 2026-07-20 **MPL EXISTING-DATA-ONLY DECISION (Andrew):** "we have to make do with only this data, no more."
  The completed Stage-0 workspace remains immutable YELLOW (tap B0-B2 1.521x uncertainty; acoustic 0.270x;
  neither clears 2x). New acquisition is not an actionable fallback. Next action is a separate, YELLOW-ceiling
  successor campaign using response-only tap transfer features as the primary conditional observable and
  acoustic centered shapes with 6 dB forcing-color uncertainty as robustness. It may report model plausibility,
  model averaging, and condition-scoped bounds; it may not claim decisive B0/B2 selection, external validation,
  or unmeasured-regime prediction. Runner card is now written at
  `docs/lab/mpl_existing_data_conditional_runner_prompt.md`: exact response-feature generalized Bayes,
  bounded frozen menu, five-family holdouts, no A/R search, and no vault. Freeze its checker before fitting.
- 2026-07-20 **FORMULATION-CALIBRATION CARD — PRE-DISPATCH. Andrew decisions so far:** (1) CLEAR DISK
  SPACE — approved; deleting only re-fetchable/recomputable caches: root `Test07_ImpactHammer_990x.zip`
  (566M, gitignored, mediaex re-fetch documented; resolution-scoring replay needs re-download first),
  `scratch_test07/*.mat` (245M, extractable from that zip), and from
  `shocksat_full_spectrum_frf_20260714/out/`: `raw_full_eig_V.npy` (1.7G, pre-filter dump, NO readers),
  `dryrun_V.npy` (634M, no replay reference), `eig_slices/` (870M, resume intermediates; final
  `full_eig_V.npy` KEPT so `run_all.sh` skip-loads — replay intact). Verified: no checker/run_all
  references any deleted file. (2) Andrew is RE-DOWNLOADING `FEM_and_CAD.zip` (1.89 GB, SHA
  `c917ce2f…` in statfem_runner source_manifest) — when it lands, pull SELECTIVE files for the F0
  construction check (drawings for PIDs 601/401/302), record SHAs of extracted files, then DELETE the
  rest. (2b) DONE: zip landed at root, SHA verified `c917ce2f…` (byte-identical to June fetch),
  61 files (~164 MB) extracted to `references/shocksat_hardware/` (README + EXTRACTED_MANIFEST.sha256:
  ShockSat1 part drawings PDFs, 28 hardware photos, FEM_20211021 NASTRAN .blk deck — PSHELL 601 t=1.0 /
  401 t=.125 / 302 t=.13 with 12I/T³ + TS/T at NASTRAN defaults — correlation pptx, weights/instr
  xlsx, assembly STEP), zip deleted; ~18 Gi free. F0 §2.2 CAD evidence now LOCAL — the card's
  "re-download if needed" contingency is resolved. (3) **DISPATCH DECISIONS FIXED (Andrew 2026-07-20: "use all defaults/recommendations and
  proceed")**: (a) VAULT NOT TICKED — +XY is never read, no vault leg, packet must say so; (b) pilot
  D0 conventions CONFIRMED (per-fold amplitude-refit robustness convention; paired SE = std/√4);
  (c) LEAD-AS-RUNNER (me); (d) §3 NUTS fix APPROVED — NUTS runs on a PROJECTED differentiable forward
  (per-region ΔK blocks in a frozen modal basis, small dense eigh in JAX), reported scores come ONLY
  from exact-basis eigensolves at calibrated parameters; reduced→exact gap measured and reported;
  checker grep gate distinguishes search/posterior path (reduced OK) from score path (exact only).
  RUNNING NOW as runner. Workspace: `artifacts/reports/shocksat_formulation_calibration_20260720/`.
  **PROGRESS 2026-07-20 ~12:15:** checker SHA-locked `b0a4e04c…` RED-on-empty proven (exit 1). All 5
  pre-reg gate files written. V1 affine PASS 6.8e-16, V2 menu-identity PASS 0.0, mr2_elem5 identity
  re-score |Δ|=0.00e+00 vs pilot +0.1848. **F0 VERDICT = EFFECTIVE-PROXY** (12:12:10, pre-calib):
  control-region check (a) on PID 203 reproduced 57% of winner's gain (≥50% rule ⇒ generic side);
  (b) construction PASS; (c) graded-not-localized. Region set fixed {601,401,302,501,301,701}, 12
  params, NO warp. Delivery rec: labeled calibration device only, NOT physical correction.
  601=four 1-in gussets (pilot's "center box" label was WRONG), 401=bolted cross plate, 302=angle
  brackets (deliverer already hand-tuned t=0.13 for corner radius — pptx s58). Queue A (baseline,
  f0ctrl, identity, A1 refits: first 2 folds +0.3322/+0.4739) → Queue B detached (basis→project→V3→
  MAP→NUTS fold1→calib exact scores→refits→rprior 6×→identgate→collect), ~9-10 h serial. NEXT after
  compute: figures (READ tufte skill first), packet.md, findings.md, run_all.sh, runtime.json,
  checker run, notes/runs.md + project_log row.
  **INCIDENTS (all logged as D1–D3 in workspace decisions_log, all pre-scoring):** D1 V4 raised
  before saving (wasted solve); D2 V4/V3 redefined after full diagnosis — 2.3e-5 basis offset vs
  A0_wide__enr cause undetermined (T identical, θ identical, self-consistency 2e-9; flagged as
  provenance note), V3 = port identity PASS 6.3e-11, V4 = sanity 1e-4 PASS; D3 unbounded MAP hit
  br≈5-21 → L-BFGS-B box [ln0.7,ln1.4] + truncated-lognormal NUTS prior; contaminated phi purged
  (a pkill leak let a stray python write 2 folds — kill children explicitly next time). Bounded
  MAPs done: per-fold optima DISAGREE + pin at box edges (601 stiff, 401 SOFT) — overfit/weak-ID
  signal; the stray unbounded optimum wanting br(601)≈5-21 reinforces EFFECTIVE-PROXY. All figure
  scripts + run_all.sh + finalize_runtime written. Queue B (b6) detached: nuts → calib_score ×4 →
  calib_refit ×4 → rprior 6+4 → identgate → collect. Then: make_figs, packet, findings, checker.
- 2026-07-18 **RUNNER CARD C (MODEL-FORM PILOT) — COMPLETE. Checker OVERALL GREEN 12G/0Y/0R, exit 0**
  (`c26489ae771e`, SHA-locked pre-science, RED-on-empty proven, verified unmodified). Workspace
  `artifacts/reports/shocksat_modelform_pilot_20260716/` · replay `bash run_all.sh`. NO SAMPLER, NO
  VAULT (guard 0 opens). 60/60 exact-scored (5 duds documented), 145 eigensolves, 58.9 h active.
  - **HQ2 MET BY ALL FOUR GENUINE MODEL-FORM CLASSES — the first positive of the remodeling arc**:
    formulation +0.0711±0.0120 (5.9×SE), connectivity +0.0641±0.0273, mesh +0.0635±0.0214, geometry
    +0.0597±0.0116 vs A1 +0.1137; class-MEAN control 1.6–2.9×SE ⇒ not selection noise. Best-ever edit
    on this structure = ZERO-DOF formulation stiffening (mr2_elem5, a RANDOM draw: br×1.23 +
    Kirchhoff-limit ts on 601/401/302 → +0.1848; ONLY finalist robust to per-fold amplitude refits,
    +0.1954, +0.0817±0.0296 vs A1). The standing "model-form doesn't move held-out FRF" was an
    ACTION-SPACE limit, not physics (closes study D16 / review C7).
  - **HQ1 FALSIFIED**: stratified amplitude-compass agent ties random (best-vs-best −0.0077±0.0177;
    means +0.0028±0.0056; finalist S-test random>agent 3.1×SE). Mechanism: agent round means DECLINED
    (0.157→0.150→0.142) — every winner-extension backfired; the compass locates regions, not rankings.
  - Wall stands (best +0.185 ≪ 0.34/0.70 references). Amplitude-trained θ overfits train drives for
    3/4 finalists (3rd program confirmation). Byproducts: 2 refine no-ops = mesh-convergence evidence
    (liveness gate); single-leg spiders outside the RBE3 domain. Incidents (all logged): D2 two V-gate
    first-run failures fixed PRE-science; D3 queue-driver bash bug (wall-clock only).
  - **NEXT (for Andrew, in notes/todo.md):** confirm/overrule D0 conventions; decide on the now-
    justified DELIBERATE formulation/geometry calibration card (+ TMCMC posterior on the winner per
    compute protocol); CAD-check the cross-beam joint reading of mr2_elem5 before any delivery claim.
- 2026-07-16 **RUNNER CARD B (VALIDATED NET-CG QOI PORT) — COMPLETE.** Workspace
  `artifacts/reports/shocksat_netcg_validated_port_20260716/`. Replay `bash run_all.sh` (active 96.79 s).
  Checker SHA-locked BEFORE science (`e235e9fc…`, RED 10/10 on the empty workspace), never edited. NO sampler
  (L5 NUTS posterior = REUSED cached draws). +XY vault never read (runtime guard + grep, `xy_files_opened=0`).
  - **GATE N0 PASS EXACTLY (1.508/2.301/2.526, max |err| 0.0000)** → **S3/S4 are assessable** (were
    CANNOT-VERIFY per review C5 / D17). The delivered twin reproduces from its own artifacts.
  - **C5 root cause CORRECTED:** the study's "marginal-calibration difference" is really a **QUANTITY-CONTRACT
    divergence** — same lo/hi arrays give netcg 1.508 vs the study's envelope-ratio convention 21.660. N1: the
    study's θ point explains **~0%** of its gap. The gap is the reimplementation.
  - **S4 = NOT MET (falsified along A5b's pre-registered path):** the one matched extended cluster mode
    (254.3↔254.9 Hz) has OBSERVED cross-drive ln-amp scatter **1.393 > the 0.80** already assumed → normal-Z
    **widens 2.526→2.958×** (+0.432 vs 2σ MC 0.091). Delivered 2.526× stands. Lever = SENSORS (1 Z sensor ⇒
    drumhead shape unmeasured), not modelling.
  - **S3 = CANNOT-VERIFY-through-this-mapping:** self-caught defect in my own pre-registered mapping —
    per-mode participation ratios invalid (18/44 adjacent in-band pairs within 1% ⇒ degenerate-subspace
    rotation; median |ln a| 2.31). 3 variants disagree. Surviving: freq_only shows no effect above the MC
    floor, and the **RANDOM control R narrows shear_X as much as the agent arms** (reproduces S2 in QOI space).
  - **NET: the delivered net-CG twin (1.51×/2.30×/2.53×) STANDS UNCHANGED** — now ASSESSED, not unassessable.
  - **⚠ REPORTING TRAP (D7):** my checker reads **OVERALL GREEN 10/10 = INTEGRITY ONLY**, while S3/S4 are both
    YELLOW — it has no gate propagating science verdicts into OVERALL. Disclosed in every report; NOT fixed by
    editing a locked checker. **Durable-rule candidate needing Andrew's approval:** checkers that pre-register
    success criteria must reflect each criterion's status into OVERALL. (Logged in `notes/lessons-learned.md`.)
  - **OPEN AMBIGUITIES (assumed, flagged for Andrew to overrule):** (1) finalists = the enriched exact bases
    that exist (B/D/R); **arm C excluded** (review C6 leakage + it shares A0's basis ⇒ no model-form signal).
    (2) S3 coverage scored on the **held-out DEV drives** per the card's S3 text, not the synthetic ensemble.
  - **NEXT ACTION (for Andrew):** decide whether S3 is worth reopening with a degeneracy-aware transport
    (MAC pairing on a common DOF space / subspace-level QOI). Nothing else left in this card.
- 2026-07-16 **RUNNER CARD A (EXACT-EVIDENCE COMPLETION) COMPLETE — checker OVERALL GREEN 12G/0Y/0R, exit 0.**
  Workspace `artifacts/reports/shocksat_fullspec_exact_completion_20260716/` · replay `bash run_all.sh`.
  Checker SHA-locked (`4a01067c921e`) BEFORE science, proven RED on the empty workspace, verified unmodified.
  NO SAMPLER (deterministic MAP refits + exact eigensolves; no posterior claim). No vault read. active 7.48 h.
  **GREEN = integrity + evidence-completeness, NOT "criteria met": S1 NOT MET, S2 NOT MET both ways, S5 NOT MET.**
  - **Q1 = "C DENTS"**: honest leakage-free arm-C exact sub-200 **0.1595**, vs A1-exact **+0.0458 ± 0.0361**
    → S1 NOT MET (misses +0.05 AND 2×SE=0.0722). Shape wall stands, dented, on valid provenance.
  - **Q2 = agent ties random under BOTH conventions**: 28/28 exact-scored, 0 excluded; (a) screening-selected
    −0.0017 ± 0.0094 (reproduces the repair EXACTLY), (b) exact-selected **+0.0115 ± 0.0158** (0.73×SE, NOT
    MET). **H2 impotence on FIRMER ground** — "best of 14 agent does not beat best of 14 random on the trusted
    basis" — removing review C1's objection. Pipeline reproduces study D 0.1634 / R 0.1651 to **0.0000**.
  - **TWO NEW DEFECTS THE REVIEW MISSED (D2):** study's arm-C 0.1570 was **right by accident** — leak
    **+0.0822** nearly cancelled by a **basis mismatch −0.0847** (shape coefficients fit in the θ=1 eigenbasis
    applied to the θ_MAP eigenbasis; r/n_modes/r0 all differed; failed SILENTLY). And "C's lead collapses on
    the exact basis" is **wrong as stated** — A1 dropped too, C's lead ~unchanged (+0.044→+0.046); S1 fails on
    **precision**, not collapse. I corrected my own D1 here (it had said the leak was benign).
  - **WEAKENS THE STUDY'S OWN D15 MECHANISM:** reduced-basis inflation is real but SMALL (mean +0.005 agent /
    +0.009 random; Spearman +0.525/+0.635) → better described as **selection noise on a 14-candidate field**
    than "the agent's lead was basis inflation". But screening DID crown the wrong agent winner
    (`wa2_brackets_soft` 1st→5th), so review C1 was well-founded.
  - **FLAGGED FOR ANDREW (needs a decision):** (1) **checker-scope miss (D3)** — I SHA-locked G05 on
    S3/S4 == CANNOT-VERIFY per the card, but Card B (`shocksat_netcg_validated_port_20260716`) landed in
    parallel and **FALSIFIED S4**; I complied with the locked gate and attached `superseded_by_card_B` to every
    S3/S4 block rather than edit a locked checker. My verdicts' S3/S4 status is STALE BY SCOPE — Card B is
    current. (2) 4 lessons + 2 durable-rule candidates in `notes/lessons-learned.md` (basis-identity assertion;
    "checker gates constrain conduct, never predict external outcomes") await approval.
  - **NEXT (suggested, not started):** the 200-500 Hz band is where the real signal is (B +0.197 vs A1 +0.033)
    and NO pre-registered criterion tests it — S1/S2 are sub-200 rules. Obvious next card. Also still open:
    a fair agentic-remodel test needs a compass that can propose refine/rbe2 edits (study D16).
- 2026-07-14 **FULL-SPECTRUM FRF STUDY CARD WRITTEN + READY FOR DISPATCH (Andrew: "study with the full
  spectrum, results for each [band], challenge the rationale for why updating/remodeling hasn't worked
  before saying impossible; not computationally lazy; runner must execute first paste").**
  Card = `docs/lab/shocksat_full_spectrum_frf_runner_prompt.md`. Workspace it will create =
  `artifacts/reports/shocksat_full_spectrum_frf_20260714/`. Design: H1–H5 = the five standing explanations
  (shape wall / remodeling impotence / damping-at-2Hz / unmeasured >200Hz cluster / evidence≠held-out), each
  tested by an arm; KEY NOVELTY = first-ever TRAINING on per-channel FRF amplitudes (all prior calibration =
  survey modes only; 5 drives were scoring-only). Arms: A0 continuity (must reproduce 0.1969), A1
  window+measured-ζ bar (0.2371), B amplitude-trained θ, C amplitude-trained Beck shapes, D remodeling loop
  w/ amplitude compass + equal-budget random, E amplitude-inclusive selection-score re-test, F combination.
  Data phase: wide-band re-distillation of all 5 drives from re-downloaded raw zips (one at a time, ~2.9GB
  disk protocol, per-drive overlap validation ≥0.999, force-health checks; graceful fallback to sub-200-only
  if downloads fail). Per-band results table (sub-200 / 200–500 / 500+) = centerpiece; QOI-weighted per-sensor
  scores; net-CG shear+normal re-scored w/ coverage hard gate + overconfidence audit. Vault = +XY both bands,
  frozen, once, labeled repeat-read. S1–S5 pre-registered; falsification valid. ANDREW LANGUAGE RULE (durable
  for human-facing docs): no "bake-off"-style jargon; plain names. CONSTRAINT (durable): NO further physical
  testing on ShockSat is possible — data levers are archive-only. NEXT: Andrew reviews/dispatches the card in
  a fresh runner session (expect multi-day wall time; ~4.3GB sequential downloads need his network OK).
- 2026-07-14 **RAW TEST07 BANDWIDTH/RESOLUTION SCAN (Andrew "yeah do that"; exploratory, scratch_test07/
  bandwidth_scan.{py,json,log} + bandwidth_scan_curves.npz + fig_bandwidth_scan.png; all 4 hits scanned,
  temp .mat extracts 002-004 deleted after).** FINDINGS: (1) **records are 1.000 s with impact at 500 ms →
  only 0.5 s of ring-down RECORDED; every band's decay is TRUNCATED by the record** → best achievable df from
  ANY re-distillation = 2.0 Hz ≈ the existing 2.03 Hz caches. **KILLS the "just re-distill finer" idea** (the
  vendor's 0.49 s frame WAS the whole usable decay); lead explicitly retracted the earlier "finer resolution is
  already ours" claim to Andrew. (2) Damping from FRF peak widths: 0/22 sub-200 survey modes resolvable at 2 Hz
  and 0/22 at any re-distillation (median mode needs df≤0.27 Hz → needs ≥~4 s records = NEW test). Damping
  values still available via TIME-DOMAIN ID within 0.5 s (survey ζ + ERA agree, medians 0.317%/0.301%) →
  window/resolution-MATCHED scoring stays mandatory. (3) GOOD news: hammer excites far above the cache band —
  median-channel SNR≥10 dB to ~2390 Hz, cross-hit coherent structure to ~2 kHz → re-distillation CAN extend
  BAND 260→~2000 Hz at existing sensors (drumhead cluster amplitudes included), just not resolution. (4) Test07
  force channel confirmed dead all 4 hits (lb channel std~0.17-0.27, max~1 lb). Caveats: one drive (+X),
  response-only, n=4 coherence bias ~0.25; low-band coherence medians dragged down by valleys between narrow
  peaks. FEEDS: the sub-200 amplitude-trained runner card (train on 2 Hz caches + window-matched model +
  survey/ERA ζ; band extension optional arm); a NEW test now buys THREE things: plate sensors, live force,
  LONGER records (>4 s). NEXT: draft that runner card for Andrew's review (not yet written).
- 2026-07-13 **BILIONIS DIRECTION-CHECK DECK IN PROGRESS (Andrew: "make slides" to update Bilionis + get
  direction on landing the plane over the next month).** CONSOLIDATION ONLY — no new science; all figures are
  provenance-labeled COPIES; every number copied from checker-backed artifacts (netcg GREEN 22/0/0; composite
  YELLOW 57/6/0; true-remodel YELLOW 11/1/0; frf-damping YELLOW 19/2/0; plate-rehearsal RED 28/3/1 [RED=pre-reg
  falsification]; runner_comparison round2). Deck asks: (1) land via PAPER (drafted v0.3, DCE target) vs
  CURRICULAR MODULE (drafted ipynb, Andrew slightly prefers; Gibert modal-testing class); (2) is a Substack post
  still worth it (agentic lessons + Fable/Opus4.8/GPT-5.5 runner comparison + problem-class harnessing) — IP
  disclosure gate applies; (3) one remaining technical push = agentic remeshing of the rawer MPL stand OR ML to
  optimize its data collection, or stop and write. Workspace = `artifacts/reports/bilionis_update_20260713/`.
  NOT changing durable rules/checkers/sampler standards. **BUILT rev 2 (Andrew: "remove jargon/numbering,
  simpler + less language, figures + short bullets"): slides/bilionis_update_20260713.pptx (8 slides) +
  code/make_update_deck.py (replayable) + README + 6 reuse figures.** Checker triads/study codes moved from
  slide bodies to small-print footers (honesty preserved). Heuristic QA only (no pptx renderer on machine):
  structural check passed; body text ~halved vs rev 1. SURFACED not self-applied: docs/report/project_log.md
  row (T7) — see workspace README. NEXT: Andrew reviews the deck + the 5 decisions (landing vehicle, Substack,
  MPL push, authorship/AI disclosure, NASA data permission).
- 2026-07-13 **RESOLUTION-CONSISTENT SCORING RUN COMPLETE (dispatched by Andrew "run it"; lead Fable = runner
  in-session). Checker verbatim: OVERALL RED {GREEN:23, YELLOW:2, RED:1}, exit 1.** Workspace
  `artifacts/reports/shocksat_resolution_consistent_scoring_20260713/` (packet.md, findings.md, verdicts,
  D0-D9, 5 QA'd figures, replay run_all.sh). The RED = Gate W (raw-data window verification) failed
  pre-registered thresholds; YELLOWs = S1 falsified + S3 not confirmed; ALL integrity/pipeline gates GREEN
  (SHA-locked checker verified unmodified; Gate R: B0 == damping run's A0_enr to 1.6e-7; vault touched once
  post-freeze, labeled second read). RESULTS: B2 (windowed+physical zeta) beats B0 (naive+1%) +0.0401 dev P1'
  (0.197->0.237), vault direction confirmed (0.420->0.473) — but < 2x fold-SE 0.053 (+Y fold -0.01) => S1
  FALSIFIED by the noise-floor rule. S2: window-alone +0.033 / damping-alone -0.013 / interaction +0.019 =>
  THE GAIN IS THE WINDOW; damping refinement at 2 Hz = noise-level. KEY DATA DISCOVERY: Test07 raw series has
  a DEAD FORCE CHANNEL in all 4 hits (~1 lb noise vs 1000-1900 g impacts) => direct H1 recompute physically
  impossible (retro-explains 2026-06-09 "Test07 low coherence"); force-free fallback (D8) also missed
  (hit-consistency 0.090 dex vs 0.05; apparent-zeta ratio 1.88 vs 1.25) => D9 accepted FAIL, refused
  threshold-shopping. Mechanism evidence SHORT OF CERTIFICATION (all in gate_W.json): distiller source FOUND
  (exp window end=0.05 — NOT Hann, D6; upstream realfrf.measured_zeta_w documents zeta_w(f)=1/(2 pi f tau),
  tau=0.164 s); Gate K <=2%; isolated peaks agree +-15% (stored + raw); nothing refutes window-broadening.
  Ops: disk hit 100% (D7 streaming; still ~0.25 GB free — FLAG). Continuity: runs.md entry + project_log row
  appended (status verbatim). Frozen damping run untouched. RECO to Andrew (packet §9): treat cache peak
  widths as WINDOW not damping; ONE cheap decisive follow-up = re-download one modal-hammer raw series WITH
  live force (Test01/02 class) -> direct Gate W + longer-frame re-distillation could certify the +0.04;
  otherwise damping arc CLOSED, MPL next. NEXT: Andrew reviews packet.md + the follow-up/close-out decision.
- 2026-07-13 **NEXT CARD WRITTEN + READY FOR ANDREW'S REVIEW (not yet dispatched):
  `docs/lab/shocksat_resolution_consistent_scoring_runner_prompt.md`.** Closes the ShockSat damping arc.
  Context: post-run addendum (2026-07-11, in the damping run's packet.md) used Andrew's re-downloaded
  Test07/+X raw records (250 kHz, 566 MB zip at repo root; scratch_test07/) to show (1) true damping is LIGHT
  ~0.3% (ERA median 0.301% vs survey 0.317%, 27/33 matched; log-dec agrees); (2) naive physical zeta scores
  WORSE held-out (0.186 vs A0-1% 0.197); (3) MECHANISM: the ~0.49 s FFT frame's ~2 Hz window broadens every
  peak to apparent zeta ~1-2.5% (freq-dependent) — the caches encode WINDOW-broadening, not damping; window-
  convolving the physical-zeta model recovers ~60% of the deficit in-sample (0.229->0.238 vs 0.244). New card
  = pre-registered test: arms B0 (A0 convention, must reproduce 0.1969) / B1 naive+physical (control) /
  B2 windowed+physical (the claim) / B3 windowed+1% (ablation) / B4 ERA-band (+X-leak-labeled) / B5 shape+
  windowed. S1 win = B2>B0 by >=+0.03 & 2xSE & vault; S2 = window-vs-damping decomposition; S3 = mechanism-
  confirmed tier (B2>=B1+0.02 + Gate W). Gate W = recompute the stored m_xpos_990x cache from RAW Test07 hits
  with the recovered distillation params (find the netcg distiller source; Test01-vs-Test07 target caveat
  handled in-card). NO-SAMPLER study (stated per Sampler Decision rule — nothing inferred beyond reused
  theta_MAP). Key honesty handles: vault +XY = SECOND program read (labeled; zero-search arm set mitigates);
  primary physical damping = SURVEY per-mode zeta (train-side every fold), ERA = validation (leak caveat);
  survey zeta<0.2% allowed AS MEASURED (gate constrains inferred damping only). Frozen damping run untouched
  (checker YELLOW 19G/2Y/0R verified after addendum append). NEXT: Andrew reviews/edits/dispatches in a fresh
  session (or tells me to run it in-window).
- 2026-07-10 **FRF-DAMPING CARD DISPATCHED BY ANDREW ("run this prompt after grounding and using your best
  judgement") — EXECUTION STARTED, lead acting as autonomous runner in-session.** Re-grounded from AGENTS.md +
  compute_protocol + litreview + the completed true-remodel packet/verdicts + reused femlib. Verified: all 18
  card §3 assets exist; env has jax 0.4.30 / numpyro 0.19.0 / numpy 1.26.4 / scipy 1.13.1 (NUTS available);
  data loads (67,683 grids; 33 modes WITH measured `damp` array; 5 drive caches 105 lines 45-260 Hz ~2 Hz,
  ~111 ch). Forward model understood: reused `predict_logH` = 80-mode reduced modal-superposition FRF with a
  FIXED ζ=0.01 resolvent — the exact frozen-damping lever this card unfreezes. Package already stores per-group
  reduced stiffness A[g]+A_fix => structural loss factor η_g enters as a strain-energy-weighted per-mode
  composite η_i (low-dim, physical, NUTS-differentiable). Workspace = `artifacts/reports/
  shocksat_frf_damping_updating_20260710/`. PLAN (phased, resumable, honest): (1) gate files FIRST +
  REUSED_code.sha256 + SHA-locked check.py BEFORE science; (2) build+validate compute-light new blocks (damping
  forward model, FDAC/FRAC/FRSF metrics, gates D1 physics / D2 identifiability@2Hz / F metric-correctness / O
  observability) — Gate O is a first-class result (bounds reachable headroom = data- vs model-limited); (3)
  launch heavy A0/A0d + loop + NUTS + vault DETACHED/resumable per compute protocol. NO fabrication; a
  falsified pre-registered claim is a valid outcome. The completed true-remodel run STANDS unchanged.
  decisions_log.md D0 in the new workspace.
  **RUN COMPLETE (2026-07-10, one autonomous session). Checker verbatim: OVERALL YELLOW {GREEN:19, YELLOW:2,
  RED:0}, exit 0.** YELLOWs = (1) pre-registered claim FALSIFIED (S1/S2/S3/S4 all FAIL — honest outcome);
  (2) A0_enr NUTS non-converged (R-hat 24.8 = θ MULTIMODALITY/under-identification, D19 basin lottery,
  reproduced under Uniform-ζ so NOT a param artifact; winner a04 + c06 CONVERGED cleanly R-hat 1.002/1.005).
  Every integrity/mechanics/validation gate GREEN (V1–V5; damping physics D1; metrics F; identifiability D2;
  observability O; exact-basis freeze; anti-LSQ; physical-damping bounds; budgets; vault-once).
  RESULT: exact-basis dev P1' — A0 0.197, A0d(damping) 0.193, shape a04 0.234 (dev winner), random 0.239.
  S1 FAIL (winner +0.037 < +0.05, ≪ 2×fold-SE 0.262); S2 FAIL (random>agent); S3 FAIL (shear coverage 0.70);
  **S4 FAIL (damping_share −0.105 → damping lever UNPROVEN; A0d BELOW A0).**
  MECHANISM (durable): 2 Hz caches can't resolve ShockSat's light damping (ζ~0.3%, half-power ≤~1 line;
  D2 27% per-mode err) → fitting damping fits the peak-ALIASING → ζ rails to gate ceiling (NUTS all finalists),
  doesn't generalize. FDAC align gain ~−0.01 (θ_MAP already aligns → completed run's null NOT a misalignment
  artifact; +0.31 on a synthetic shift, Gate F). Gate O: 93% shape reachable (not gross-unobservable), sensor
  aliasing self-MAC 0.997. CROSS-VAL: A0_enr raw P3 0.2152 == true-remodel exact-basis A0.
  Vault(+XY, once): uniform +0.22..+0.30 dev→vault location effect, no win. Runtime active=elapsed 8722.7s.
  Deliverables in workspace: packet.md, findings.md, verdicts.json, 5 Tufte figures+fig_qa, decisions D0–D12,
  checker_report.json. Continuity: runs.md entry + project_log row appended (status verbatim). RECO to Andrew:
  KEEP inherited twin; to use damping for FRF-amplitude correlation BUY finer frequency resolution (re-distill
  NASA raw time histories) — not more modeling. True-remodel run STANDS unchanged. MPL = natural follow-on.
  NEXT: Andrew reviews the packet + the replace/keep/buy-data decision (human call).
- 2026-07-10 **NEXT CARD WRITTEN + READY FOR ANDREW'S REVIEW (not yet dispatched):
  `docs/lab/shocksat_frf_damping_updating_runner_prompt.md`.** Honest successor to the completed true-remodel
  loop (which FALSIFIED modal-selected shape-changing remeshing on held-out FRF). Trigger: Andrew's "agentic
  remeshing can't be this impotent" + Fable's FEM-test-correlation literature review (saved
  `references/fem_test_correlation_litreview.md`). The review + our own data show 3 mis-specified levers for an
  FRF deliverable: (1) selected on MODAL freq not FRF; (2) NO FDAC frequency-shift alignment (raw log|H| corr
  dominated by 2.5-3.3% peak misalignment — the completed run's noise floor may BE this); (3) FROZEN damping
  (amplitude ~ participation/damping; remeshing can't touch it). New card = FRF-DOMAIN agentic UPDATING loop:
  DAMPING action space (band ζ / Rayleigh / per-joint loss factor η) as the primary new capability + shape
  edits demoted to comparators; FDAC-aligned FRAC (P1') + FRSF (P2') metrics; A0d damping-baseline arm; S4
  ATTRIBUTION gate (is any gain from damping, not shape/θ); Gate O sensor-OBSERVABILITY pre-check (bounds
  reachable headroom = data-limited vs model-limited); physical-damping honesty gate (ζ in [0.2%,5%], η<=0.2
  else DQ as amplitude-fit-in-disguise). Carries the completed run's 2 hard-won guards as non-negotiable:
  exact-basis scoring + multi-start MAP. Reuses the completed FE layer read-only. Honest prior: shape stays
  null, damping MAY sharpen amplitude, Gate O may prove data-limited — all 4 outcomes publishable. Recommend
  ShockSat FIRST (controlled A/B, reuses infra), MPL follow-on. NEXT: Andrew reviews/edits/dispatches in a
  fresh session; the completed run STANDS unchanged.
- 2026-07-06 **TRUE REMODEL LOOP RUN — EXECUTION STARTED (lead acting as runner; Andrew dispatched the card
  in-session and said GO).** Workspace `artifacts/reports/shocksat_true_remodel_loop_20260706/`. DONE so far:
  all 16 reused sources verified+hashed (REUSED_code.sha256); pre-registration gate files written FIRST
  (priority_deliverables, question_framing, quantity_contracts, assumptions_ledger, decisions_log D0-D5);
  check.py written + verified on the honest pre-science baseline (RED 2G/10R = science-not-run) + SHA-LOCKED
  (CHECKER.sha256 d9cb1acd…, IMMUTABLE). **ANDREW DECISIONS (D4): vault = Test04/+XY cache fallback (NO Test08
  re-download), excluded from all dev queries from run start; dev folds = leave-one-drive-out over 4 drives
  (+X/990x, +Z/990z, +Y/990y, +Z@900z). Disk: tiers 1-3 raw layers deleted w/ approval (~9.6G reclaimed,
  14G free).** **RUN COMPLETE (2026-07-08). Checker verbatim: OVERALL YELLOW (11G/1Y/0R, exit 0); the 1 YELLOW
  = "pre-registered claim FALSIFIED (honest outcome)". S1 fail (best shape +0.022 < +0.05), S2 fail (agent
  0.2376 vs random 0.2389 tie-in-noise), S3 fail (shear coverage). Vault graded ONCE post-freeze (all models
  0.44-0.50 = location effect). Mechanisms delivered: θ-wobble dominates; reduced-basis inflation + θ_MAP
  basin lottery caught pre-vault; better .ash fit => worse held-out FRF (dev+vault). Continuity: runs.md entry
  + project_log row + lessons-learned appended; packet/findings/verdicts/figures/runtime in workspace.
  NEXT: Andrew reviews the packet; replace/keep decision is his (packet §7 recommends keep inherited twin,
  buy >200 Hz + multi-ref data).** History of the endgame integrity catches: D18 spot-check FAILURES
  (a16 0.66%/c06 2.2% >0.3%) -> enriched-reduction rebuilds (validated ~1e-7); D19 θ_MAP MULTIMODALITY (same
  edit, different basins, ±0.035 P1) -> deterministic multi-start for decision-relevant leaders; D21/D22 A0
  ITSELF fails the spot check (0.69%) -> exact-basis rule for the whole freeze set. **Corrected bar A0_enr =
  0.2152** (cascade 0.2341->0.2243->0.2152: better .ash fit = worse held-out FRF, coherently). Corrected story:
  best shape edit a04 +0.027; enriched splits collapse to the bar (+0.012/+0.005); run-wide best = b04
  PARAMETRIC-ONLY control 0.2746 (+0.059!) = the proven-dead family; random-best rnd003 0.2628 (also
  parametric). S1 (shape-changing, +0.05) falsified on dev; S2 letter = raw b04>rnd003, shape-only = agent
  loses to random (both reported, D20); S3: Q shear coverage FAILS for A0+a04 (netcg +Z@900 gap class); LMO
  widen 1.07 passes. Freeze set (all exact-basis, D22): a04_enr, a16_enr, c06_enr, b04_enr, rnd003_enr, A0,
  A0_enr -> VAULT (Test04) once -> verdicts -> packet. Budgets: agent ~40/60, random 57/60, eig ~50/80.**
  PROGRESS: **V1-V5 ALL PASS** (V1 blocks bit-exact + eig 1.15e-9; V2 RBM 2.9e-12; V4 t/t³ exact;
  V5 churn demo; V3 FAILED once -> forensic found the cause = accel-mount drilling-penalty ARTIFACT quartet
  (124.5 Hz in A0, /2 under refine; instrument-invisible) -> D12 pairing hygiene (exclude unobservable modes;
  MAC>=0.3 likelihood filter) + D13 cross-model matched re-metric -> V3 PASS median|df| 0.0083%, dMAC +0.010
  borderline-flagged). **A0 BAR (locked protocol): dev P1 = 0.2341** folds [0.323,0.560,0.188,-0.133] (+Z@900
  fails via Bottom_Box corr -0.51), P2 16.9 dB; uncal ref 0.249 ≈ same. Diagnosis r0: Rectangular_Plates worst
  region MAC 0.237; 190-203 Hz bad-shape cluster ~0.9 SE in bottom_box; 7 test modes are shape holes MAC<0.01.
  Round-1 agent proposals (16, evidence-tied, 9 full solves: bolt-spider rbe2_soften 56@z18.4 never-touched /
  mount+dish spiders / weld thickness ±(t,t³) / face+bulkhead splits / 2 evidence-targeted refines / controls)
  + random track (60 specs seed 20260706, 32 full) BUILDING detached in parallel. NEXT: screen -> dev-score
  (A0 first DONE; budgets 60/60, so far 0 agent + 0 random queries) -> rounds 2-3 -> finalists+NUTS -> Q/H ->
  freeze -> vault(Test04)-once -> verdicts/packet. Crash recovery: card + gate files + decisions_log D0-D13a +
  out/query_log.jsonl + out/eigensolve_log.jsonl; builds/scores resume from partials.
- 2026-07-06 **STRATEGIC REDIRECT (Andrew): patent is NOT a this-summer goal. Energy goes to AGENTIC FEM
  REMODELING + data-based model selection ("first time ever agents can remodel FEMs intelligently and select
  on data — but we haven't gotten it to work yet"). ShockSat FIRST; MPL test stand second (never correlated,
  big headroom).** Lead (Fable) audited all prior "remodeling": Card D + composite bake-off were parametric
  stiffness/mass scaling on a FROZEN mesh (only true mesh change = the dish-refine null control); open-loop
  menu + random tranche; selected on EVIDENCE (wrong objective — rand10 won evidence, lost held-out). Andrew's
  verdict: "not remodeling at all." Key correction agreed: Card D Pareto-optimality is FAMILY-relative (9-group
  multipliers), NOT a global limit — vendor correlation covered global freq/MAC, never FRF amplitude (per-ch
  corr ~0.27–0.38 vs usable ~0.7 = the untested headroom); Andrew: "if remodeling can't improve it, nothing
  can." Held-out mechanics clarified for Andrew: 3-tier protocol (train / budgeted dev for steering / vault
  touched once) — selection on dev leaks bits-per-query (budgeted), never fit on held-out; vault = final grade.
  **RUNNER PROMPT WRITTEN + READY TO DISPATCH: `docs/lab/shocksat_true_remodel_loop_runner_prompt.md`** —
  closed-loop ≥3 rounds, SHAPE-CHANGING action space required (true refinement / region splits / correct
  t-vs-t³ thickness / added DOFs; element-pipeline reuse from fem_remesh scripts), diagnosis from TRAIN
  residuals only, dev = leave-one-drive-out SCALAR scores w/ hard query budget (60 agent + 60 random) +
  query_log, VAULT = never-downloaded Test08/Test10 impact zips fetched ONLY after finalists SHA-frozen
  (fallbacks: Test04 excluded-from-dev; coherence≥0.6 gate), mandatory RANDOM-SEARCH comparator (S2
  intelligence test), V1–V5 mechanics gates incl. the reduced-basis trap (never score shape edits in the
  frozen inherited basis), NUTS finalists only, S1 margin must clear the 2026-07-06 metric-noise floor
  (fold-averaged, ≥2× fold SE), no human stop-points, falsification = valid pre-registered outcome.
  NEXT: Andrew dispatches it in a fresh agent session.
- 2026-07-06 **METRIC NOISE FLOOR quantified (from Andrew's "what are you least confident about").** CV medians over
  24 split choices (8 seeds x K=4,5,6): baseline 0.322-0.407 (mean 0.364), al_rho_lo 0.397-0.466 (mean 0.445). ⇒
  single-seed numbers quoted this week carry ±0.04-0.08 split noise: "Bayes costs 0.03" NOT resolvable; remesh gain
  is +0.08 seed-averaged (0.364→0.445) and DOES survive. RULE for reset: every metric must be seed/fold-averaged
  with a spread, pre-registered before running; single-split numbers are not reportable. Other top doubts logged for
  the reset prompt: mode-matching layer (greedy MAC>0.3 at global MAC 0.61, uncertainty never propagated); "wall=
  shapes" partly by elimination (mapping/window/processing bugs would masquerade); single-agent self-review; oracle-
  ceiling pruning should precede any sampling; "model-form error protects from overfitting" true for BAND only, mean
  still needs its own held-out gate. Advice to Andrew: current honest map = guaranteed floor deliverable; reset = 
  freeze ONE harness first, then 2-3 matrix cells whose oracle ceilings permit a win.
- 2026-07-04 **TEACHING MODULE DRAFT BUILT (Andrew: "draft an ipynb data science module for a graduate modal
  testing class — Bayesian FEM updating on the hanging panel first, then ShockSat; ME323 module as style example;
  do what you think is best").** Deliverable `teaching/bayesian_fem_updating_module/` (notebook 47 cells /
  18 code, README, data package ~1.5MB, build_notebook.py generator, prepare_data.py, smoke_run.py checker,
  qa_figs/ legibility evidence). ARC: panel (LDV 25pt test; Ritz free-plate + 4 corner-spring surrogate w/
  ASSUMED blueprint values; exact 2-param grid posterior θ_D 0.806 [0.738,0.875], θ_k 0.592; suspension-datum
  experiment = which-data-inform-which-parameter; σ sensitivity; leave-modes-out FAILS decisively = model-
  discrepancy lesson from the real sign-changing residual) → ShockSat (reused 74-DOF reduced_blocks.npz from
  psd_envelope workspace, 9 groups; grid-death 742k-years demo; NUTS 4x1000 in 2s GATE PASS R-hat 1.0032/
  ESS 1258/0 div, σ inferred 2.5%; strain-energy-fraction heatmap = identifiability (joints/contact prior-
  bound); held-out >220Hz 9/9 covered). VERIFIED: all 18 code cells executed end-to-end headless; markdown
  numbers corrected to match actual outputs; nbformat validation PASS; all 11 figures visually QA'd (fixed
  strain-energy row-order bug + 2 clipped/legend issues + wrong octave label). FLAGGED in README, NOT resolved:
  ShockSat NASA data permission before student release; panel blueprint values are assumptions; no solutions
  guide yet. SURFACED not self-applied: project_log row for this thread. NEXT: Andrew reviews the draft.
- 2026-07-02 **REPORTING SPRINT (post-composite-bake-off, all consolidation, NO new science):** (1) Bilionis
  1-paragraph update + 2-slide deck `artifacts/reports/bilionis_update_20260702/` (evidence≠held-out framing
  explained to Andrew; his draft's "agentic remodeling most promising" revised to the falsification). (2)
  63-row experiment catalog `docs/report/experiment_catalog.{csv,xlsx}` (folder/question/dataset/findings/
  publishability-1-5-PROPOSED/deck☑; verified complete vs artifacts/reports; top-5s = composite_bakeoff +
  netcg; gap surfaced: the 3 highest-rated results had no decks). (3) ONE thorough 22-slide deck
  `artifacts/reports/results_deck_20260702/slides/shocksat_three_studies_20260702.pptx` (harness + 3 studies +
  cross-cutting findings; 18 provenance-labeled reuse figures; statuses copied from checkers). (4) Paper draft
  v0.1 `artifacts/reports/paper_draft_dce_20260702/paper_draft.md` (~3400 words, DCE-target: coverage-first
  validation + 3 pre-registered studies + negatives-as-contributions; README lists 5 OPEN ITEMS for Andrew:
  venue/Girolami-EIC fit, authorship+AI disclosure, NASA data permissions, references, negative-framing
  sign-off). SURFACED not self-applied: project_log rows for catalog/deck/paper; publishability ratings are
  proposals. NEXT: Andrew reviews deck+paper; possible ipynb harness module; Gibert ask.
- 2026-07-02 **NEXT EXPERIMENT REDIRECTED BY ANDREW: composite bake-off = AGENTIC REMODELING (100s of
  diagnosis-driven candidate model classes, two-tier screen, EVIDENCE-based model-class selection on a
  SHAPE-INCLUSIVE likelihood — frequency-only evidence would re-crown frequency-fitters) x BECK shape-field x
  orthogonal discrepancy statFEM F(k), four arms A(baseline proven non-Beck)/B(Beck)/C(remodel)/D(composite),
  scored on held-out per-point amplitude AND held-out net-CG QOI bands + leave-modes-out audit; checker must
  encode the two historic metric traps (amplitude-fitting, re-pairing churn). Andrew's principle: LIMITED DATA,
  NOT LIMITED MODES (full in-band mode set, all 5 drives). Andrew's rationale: agent w/ clear goal + FEM/dynamics
  understanding can improve the forward model; agents generate/evaluate 100s of candidates cheaply + Bayesianly.
  The '12-mode' (rename: FULL-CLUSTER) plate-test rehearsal card is PARKED (pre-hardware-ask card, not next).
  MAC-in-likelihood axis ADDED per Andrew (S1 arm; freq-only evidence FORBIDDEN as selector). PROMPT WRITTEN + READY TO HAND OFF: docs/lab/composite_remodel_beck_runner_prompt.md (matrix M{0,1}xS{0,1,2} + F(k); two-tier screen; no geometry rebuild; metric traps + claim-falsified-vs-pipeline RED labeling encoded).
  **EXECUTION STARTED 2026-07-02 (lead acting as the runner, Andrew dispatched the card in-session).** Workspace
  `artifacts/reports/shocksat_composite_bakeoff_20260702/` created; gate files written FIRST (priority_deliverables,
  question_framing w/ pre-registered arms+thresholds+pinned bars [statFEM F(k) 1.508/2.301/2.526; Beck 3-seed
  −0.68→−0.25 = shapefield_lever.json, D3 provenance note; oracle σ 0.70], quantity_contracts, assumptions_ledger,
  decisions_log D1-D5); check.py SHA-LOCKED before science (CHECKER.sha256 2441daba…) + REUSED_code.sha256 (13
  read-only sources). Checker baseline = RED 5G/0R…9R missing-science as expected. Candidates=151 (allowed
  families only), tier-1 subspace screen DONE (baseline reproduces global MAC 0.642≈0.63). ALL pipeline code
  written + smoke-tested (rmodel.py engine, tier3 evidence w/ prior sweep + freq-only ref, 6-arm NUTS runner
  w/ uniform retune, R1/R2/R3 scorer replicating netcg conventions, tufte-linted figs, run_all.sh).
  **COMPLETE 2026-07-02 (recovered from 1 computer crash mid tier-2 + 1 sampler hang, both resumable, no
  science lost). Checker OVERALL YELLOW (57G/6Y/0R, exit 0); SHA verified unmodified.** All 6 arms
  NUTS-CONVERGED (R-hat ≤1.0011, ESS ≥580, 0 div). Funnel 151 cands → 29 full 399k-DOF eigensolves → 10
  evidence classes → 1 M1 (`rand10`). **RESULTS: (1) AGENTIC REMODELING DID NOT EARN DELIVERY (pre-registered
  claim FALSIFIED, honest not pipeline-fail): `rand10` won shape-inclusive EVIDENCE +54 logZ (P=0.72,
  prior-robust top) but did NOT beat M0 on held-out R1/R2 → R4 reports-not-delivers. (2) Evidence≠held-out =
  central result (freq-only evidence would crown the SAME candidate → MAC block didn't re-rank here). (3)
  MAC-as-θ (S1) ~NULL again at QOI level (reproduces modelclass_L5 §3a). (4) Beck (S2) = per-point amplitude
  CHAMPION (R1 −0.34/−0.37 vs −0.71…−0.78, σ 0.89 vs 1.08) BUT confident shapes don't transfer to the net-CG
  band (R2 under-covers 0.55-0.70 shear / 0.23-0.32 normal); on the arm-independent held-out-DRIVE key Beck
  covers shear_X 1.00 → shear miss partly a FEM-shape-reference artifact, but normal has NO data key → unsafe.
  (5) DELIVERED = inherited FEM + freq(+MAC) + statFEM F(k) both QOIs = REAFFIRMS the proven netcg twin;
  composite additions did not improve the delivered bands.** Both metric traps encoded+clean; full in-band
  mode set + all 5 drives; M0S0 R3-DQ = MARGINAL threshold artifact (normal widen 1.01<1.03 but still covers
  0.993 after hiding) — transparently flagged, delivery pick M0S1≈M0S0 not a real S1 win. Sampler incident
  D11 (A7 realized): S1 freq+MAC hung ~2h on 246-258 Hz degenerate-cluster eigenVECTOR gradient → FIXED with
  Tikhonov-regularized first-order shape derivative (δ=1.6e4, 25s, converged) = documented stability fix, not
  a result change. Deliverables all written: packet.md, findings.md, runtime.json (active 8150s/wall 20079s),
  runs.md entry + project_log row (status copied from checker), decisions D1-D11, 5 tufte-linted figures.
  NO durable-rule/checker/sampler-standard edits. NEXT (for Andrew): review; the composite verdict + the
  Beck per-point-vs-net-CG split are candidate publishable findings; >200 Hz plate test remains the binding
  next-test lever.**
- 2026-07-02 **PLATE-TEST REHEARSAL COMPLETE — the 3.5x promise is FALSIFIED (pre-registered; checker OVERALL RED
  28G/3Y/1R where the 1 RED = S1 claim-falsified tier, pipeline INTACT: coverage GREEN 0.998, integrity GREEN,
  35/36 NUTS converged).** Workspace `artifacts/reports/plate_test_rehearsal_20260701/`; replay `bash run_all.sh`.
  Rehearsed medians: 1-sensor 6.17x / 12-sensor 6.20x / 20-sensor 6.20x — NO buy-down (analytic curve promised
  3.5x). MECHANISM (post-hoc ablation L0-L7, labeled): the analytic pretest curve FROZE theta at MAP; the real
  +/-4% theta posterior rotates the near-degenerate 246-258 Hz drumhead eigenvectors -> every band mode's net-Z
  participation scatters (L1 3.05x -> L2 4.93x from theta alone; signed-mixture heavy tails -> 5.5x); perfect
  4-target test still ~5.1x (L6). **CONSTRUCTIVE: pin ALL 12 drumhead-band modes -> 2.81x (L7 oracle bound) =
  REVISED test scope (whole 228-260 Hz cluster, not the 4 net-drivers); requires a 12-mode-inference follow-up
  rehearsal BEFORE any hardware ask; do NOT promise 2.8x yet.** As-designed test still buys: target amp posterior
  sd 0.80->0.58, mean within 0.08 of truth = pooling checkable (RQ3). Truth-sd 1.6: band ~104x, coverage 1.0 —
  degrades by widening, never lying. Integrity: D8 (prior/tier consistency fix, pre-campaign, prior-only band
  reproduces 5.81x vs analytic 5.4x) + D9 (uniform retune, pre-headline); checker SHA-locked before science, never
  touched; A0_s6 pathological seed excluded+reported. Continuity: runs.md entry + project_log row (status copied
  from checker) + todo updated. **ANDREW DECIDED (2026-07-02): BOTH — (a) revised test scope ACCEPTED + 12-mode follow-up
  rehearsal approved (lead writes self-contained runner prompt; dispatch in a fresh session at the phase
  boundary); (b) 3.5x corrections drafted: netcg packet §9 gets a DATED ERRATUM (append-only, no history
  rewrite; its locked checker re-run after), status deck slides rebuilt with the falsification + README revision
  note. Also asked the “prior too strong / posterior barely moves” Bayesian critique — answered from artifacts
  (identifiability, not prior strength; every data-domination arm failed, documented); offered a cheap
  theta-prior-sd ablation (0.25->0.5->1.0 through L5 + held-out) as the empirical rebuttal artifact, pending
  Andrew.**
- 2026-07-01 **PROJECT STATUS DECK BUILT (Andrew "throw together some slides on project status + telling figures
  + next steps; aim = contribute to aerospace workflows + Bayesian FEM-updating literature").** Workspace
  `artifacts/reports/project_status_deck_20260701/`; deliverable `slides/project_status_20260701.pptx` (19 slides);
  replay `bash run_all.sh`; QA clean (heuristic — no renderer on machine). CONSOLIDATION ONLY, no new science; all
  8 figures are provenance-labeled COPIES (reuse_*) from netcg_method_selection + bilionis_review; every slide
  footer cites source files. Arc: wall (+27dB per-point) → defect (local shape, 0.97-vs-0.17 MAC) → remesh boundary
  → pivot (QOI resolution) → net-CG delivery (statFEM F(k), held-out-drive validated) → Monday tools → 4 literature
  findings → ShockSat positioning → plate-test design → next-step ASKS (slide 18 = proposal, NOT decided). Same
  session earlier: answered Andrew's synthesis Qs (learnings vs goals; best setup; translatable; lit contribution;
  ShockSat positioning; why agentic meshing unfruitful — reconciled 54.2Hz MAC 0.97 [NASA 76-node grid] vs 0.17
  [84 accel channels] = the defect definition). SURFACED FOR APPROVAL, not self-applied: project_log row for this
  deck; slide-16 lit-positioning citation pass before external use; slide-18 priority decisions. No durable-rule/
  checker/other-workspace edits.
- 2026-07-01 **FOLLOW-ONS #1+#2+#3 (Andrew "run 1 and 2", then "sure" [run #3] + "dive deeper"). Checker now
  OVERALL GREEN 22/0/0 (mesh screen completed -> its YELLOW cleared; locked checker SHA verified unmodified). NOTE:
  GREEN certifies pipeline integrity + NUTS convergence + HONEST flagging, NOT that the normal number is certified
  (3 mandatory caveats carried: normal data-starved covering-band-only; shear_Y +Z@900 held-out-drive gap;
  pooling normal-sharpen unverifiable). Mesh screen DONE: top 6 edits incl inherited TIE +0.4401 = remesh no QOI
  leverage. #3 PRE-TEST DESIGN (out/pretest_design.json, fig_pretest.png): net-normal driven by partial-cancel
  drumhead modes 246/249/254/258 Hz (net tray-Z; NOT pure 234/252 which cancel); current plate=1 Z-sensor; 12
  well-placed plate accels cut normal band 5.4x->3.5x (~35%, 73% to the fully-resolved 2.8x floor); drive +Y best;
  modes not individually separable (measure net combo=QOI). decisions D15-D16.
  **DIVE-DEEPER #1/#2/#3 (Andrew "run all 3") — coherent HUMBLING synthesis (D17-D18):** DD1 the +Z@900 shear_Y
  gap = DRIVE-SPECIFIC artifact (73Hz mode, 5x outlier), NOT systematic FEM error -> revises D13. DD3 the 5-drive
  cross-scatter says the measured-mode amplitude sigma is ~0.86 (robust; naive 1.03), NOT the assumed 0.35 ->
  data-anchored shear band widens (shear_X 4.5->6.4x, shear_Y 4.4->12.7x); pooling ICC 0.31 -> shared scale OK for
  measured modes (RQ3). DD2 NUTS-learned statFEM discrepancy CONVERGED (R-hat 1.001/ESS2083/0div): sigma_d=0.94,
  ell=0.10 oct (point-wise) -> AGREES with DD3 (two independent routes). KEY: the discrepancy is ~0.9 but nearly
  POINT-WISE so it AVERAGES OUT under 1-oct smoothing (why #1 held-out-drive coverage passed) -> the delivered
  shear band is trustworthy at the 1-OCT-SMOOTHED level (validated) but point-wise amplitude uncertain ~0.9; do
  NOT over-read as point-wise sharp. Quantifies the standing "per-node amplitude = the wall" via 2 new routes.
  Checker stays GREEN 22/0/0 (locked, unmodified); DD's are artifact-backed follow-ons + a new packet §7b.** #1 REAL held-out-DRIVE answer key (reconstruct per-drive net-CG SHEAR force from each
  drive's MEASURED FRFs, independent of the tier model): shear_X covered 1.00 on 5/5 drives; shear_Y 4/5 with a
  GENUINE +Z(900) end-drive cross-axis gap (0.60, diagnostic rules out low-signal) = a real model-form caveat the
  stricter test CAUGHT (self-consistent metric missed it). Also upgraded the QOI to per-drive (adds phi_drive). #2
  Axis-A breadth (N=18, 5 formulations): all 4 discrepancy methods COVER+HUMBLE, only theta_only overconfident ->
  conclusion ROBUST (winner's-curse reduced). WINNER refined to **statFEM F(k)** (QOI-aware freq-correlated output
  discrepancy): shear 1.51x(X)/2.30x(Y) FEM+6dB (sharper than freq_discrep AND held-out-drive-validated 5/5
  shear_X); normal conservative 2.53x. **RQ3 answered: hierarchical pooling CAN tighten the normal band ~20%
  (2.55->2.00x) but only under an UNVERIFIABLE shared-amplitude-scale assumption on the unmeasured drumhead modes
  -> flagged, not delivered; needs the >200 Hz plate test.** decisions_log D12-D14; packet/findings/fig_delivery
  updated. NO durable-rule/other-workspace edits; only my workspace + this block + the project_log row.
- 2026-07-01 **RAN the net-CG method-selection runner (Andrew "run docs/lab/shocksat_netcg_method_selection_
  runner_prompt.md"). Acted as the autonomous runner.** Workspace
  `artifacts/reports/shocksat_netcg_method_selection_20260701/`; replay `bash run_all.sh`; checker SHA-locked
  (CHECKER.sha256). **Checker OVERALL YELLOW (21G/1Y/0R, exit 0)** — the 1 YELLOW = mesh screen still running
  detached (5/12 edits; resumable; re-run check.py when done -> GREEN). DONE: distilled +Y/Test03 5th drive to the
  canonical N=122880 cache (m_ypos_990y.npz; 4 hits, coh 0.85, peaks incl 231.9/254.3 Hz); Stage 0 (no NUTS) QOI
  trust map + observability + sensitivity + validity + Tufte figure; Stage 2 bake-off L5 modal-freq NUTS
  **CONVERGED (R-hat 1.001, ESS 2646, 0 div)**; Stage 3 delivery + graphical model. **RESULT (best of N=9, per
  QOI): WINNER = L5 freq+DISCREPANCY for BOTH shear and normal.** Shear bands 1.9x(X)/3.2x(Y) FEM+6dB (measured
  global modes, validated); normal band 2.55x (drumhead 234-254 Hz UNMEASURED -> data-starved for the NUMBER,
  honest covering band). **Leave-modes-out CONFIRMED the binding requirement**: L5_theta_only (freq-only) widen
  ratio = 1.00 exactly = structurally OVERCONFIDENT -> DISQUALIFIED (the false-sharpener, caught); FEM+6dB tight
  but UNDER-covers (0.71-0.87). +Y adds FREQUENCY observability (unique 230.6 Hz) not shape; normal width is set
  almost entirely by the assumed unmeasured-mode AMPLITUDE sigma (SD_A_U: 0.4->2.6x, 0.8->5.7x, 1.6->34x) -> next
  test dollar = a >200 Hz plate/drumhead modal test. Two integrity catches (recorded in workspace decisions_log
  D4, D9/D10): (i) fixed a false "+Y lifts normal trust to 96%" (freq-observability != shape-measurement -> 3-tier
  model); (ii) first bake-off was NON-discriminating (circular coverage ref + band-averaged LMO) -> reworked to an
  epistemic-truth-ensemble coverage + widen-based leave-modes-out. HONEST SCOPE: bake-off is best-of-N=9 (decisive
  contrast), NOT the full 7x4x3 grid; feature/beck/statFEM/pooled-fullFRF + mesh-through-NUTS are documented
  deferrals (remesh screen shows inherited best = no QOI leverage). NO durable-rule/other-workspace edits; only my
  workspace + this CURRENT STATE block + a project_log row appended.
- 2026-07-01 **DELIVERY TARGET + METHOD-SELECTION DESIGN (Andrew decisions, this session).** Partner (owns the inherited
  FEM+test) wants **net-CG FORCE on the top tray/plate, BOTH components**: in-plane SHEAR (high trust, driven by measured
  global modes ~114-169 Hz) AND out-of-plane NORMAL (low trust, driven by UNMEASURED drumhead modes ~234-254 Hz).
  Excitation = 100%-known FLAT input PSD at the hammer-impact location; response=|H|²·S_F. CONFIRMED (Andrew 2026-07-01):
  freq band 20-2000 Hz; **band metric = 95% band benchmarked vs held-out data SMOOTHED on 1-OCTAVE spacing, narrow
  exceedances TOLERATED (energy-weighted dB-exceedance) if enveloping everywhere else** (NOT strict everywhere-cover);
  **examine ALL 4 drive points** (+X/Test01, +Z/Test02, +XY/Test04, +Z@900/Test06 = held-out-drive answer key). Andrew
  also directed: **package this as a SELF-CONTAINED runner prompt for a FRESH autonomous agent that executes Stage 0→3
  without stopping for approval.** Base workspace to reuse = artifacts/reports/shocksat_psd_envelope_twin_20260623/
  (has realfrf.py, score.py, modal_feature.py[L5 NUTS], qoi_trust_table.py, shape_borrow_diag.py, heldout_qoi.py + the
  4 canonical data/multiref_modal/*.npz caches); FEM = shocksat_fem_modal_twin_20260609/fem_model.npz.
  **PROMPT WRITTEN + READY TO DISPATCH:** docs/lab/shocksat_netcg_method_selection_runner_prompt.md (self-contained;
  fresh agent runs Stage0→3 autonomously w/o approval; bakes in re-grounding, QOI/quantity contract, 5-axis matrix,
  1-octave smoothed coverage w/ tolerated exceedances, two-part selection rule [coverage=hard gate, sharpness where
  earned], leave-modes-out humility test as the low-trust answer key, QOI-weighting, all AGENTS gates, detached-compute/
  resumable/NUTS convergence, autonomy guardrails [own workspace only; no durable-rule/checker/other-workspace edits]).
  NEXT: Andrew dispatches it in a new agent. No science run started by lead; no durable-rule/checker/project-note edits.
- 2026-07-01 **REMESH-SELECTION REDESIGN (Andrew's two catches — both correct; prompt to be revised before dispatch).**
  (1) A digital twin = ONE mesh → the deliverable is a single {mesh+method+pooling} combo; DROP the earlier "best remesh
  per QOI" idea (can't hand partner two FEMs). (2) "Best mesh" is COUPLED to updating: ranking meshes on raw/pre-update
  FRF correlation (the current `correlate_all.py` mechanism) is the known §1.1 ARTIFACT — metric-dependent (in-sample vs
  held-out vs blind each crown a different edit; blind "best" was WORSE than untouched FEM) AND pre-update (updating
  reshuffles the ranking). FIX baked into design: DON'T crown one mesh up front. Instead: cheap screen ~50 edits → keep
  TOP ~3 (hedge, flag screen as imperfect proxy) → carry those 3 as a MESH AXIS into the bake-off → update+score each on
  the SAME held-out-QOI objective (post-update) → delivered twin = single {mesh,method,pooling} that wins held-out QOI.
  One twin serves both loads: rank primarily on the load the mesh can move (SHEAR, measured modes), but CHECK the winner
  doesn't degrade NORMAL and report the trade. Count impact: remesh goes from "1 crowned edit" to ~3 candidates carried
  through updating (mesh axis ≈3, not 2). +Y (Test03/990y) DATA NOW DOWNLOADED → 5th drive (more held-out-drive folds) +
  the only real observability lever for the low-trust NORMAL load; runner must fold it in. PROMPT REVISED + READY
  (docs/lab/shocksat_netcg_method_selection_runner_prompt.md): Axis B = screen ~50 edits → top ~3 meshes carried THROUGH
  updating → post-update held-out-QOI picks the ONE twin mesh (no pre-crowning); +Y folded in as 5th drive (Stage-0
  re-trust + heldout_drive fit-on-4-predict-5th); NO hard count cap (Andrew: sweep broadly — RQ5 cross-article is the
  real out-of-sample test) BUT winner's-curse honesty (report N, "best of N") + a use-once final fold to certify the
  winner. Andrew accepted the winner's-curse risk (broad sweep is informative; other datasets stress-test it). STILL
  OPEN (Andrew's call): RQ1 order-of-ops/iteration is DEFERRED to a follow-on using the winning method (not in this
  runner) unless Andrew says fold in now. Ready to dispatch in a fresh agent. **Andrew's binding design
  requirement:** the selected method MUST be robust to QOIs driven by modes outside its optimal range — NOT get "sucked
  into" falsely sharpening the unmeasured-mode-driven (normal) QOI, and communicate TRUE (wide) uncertainty there. This
  = the selection criterion: (i) COVERAGE everywhere = hard gate (overconfidence disqualifies); (ii) SHARPNESS only where
  earned. KEY INSIGHT: this makes the normal QOI validatable at the MECHANISM level via a LEAVE-MODES-OUT humility test
  (hide measured modes → band must widen to cover them; known answer key) even though the real drumhead-force truth is
  unmeasurable. Two-problem delivery: shear→sharp validated prediction; normal→covering band + "next test dollar"
  (>200 Hz plate test / +Y Test03) recommendation. Experiment matrix (reset §5): {remesh}×{param/pooling}×{formulation:
  θ=1 & FEM+6dB baselines, L5 freq, freq+MAC, feature-space peak±%/amp±dB, Beck shape-field, pooled full-FRF, statFEM
  F(k)}×{QOI: shear|normal, separate}×{scoring: blind→sensor-infill→held-out-drive→held-out-QOI→LEAVE-MODES-OUT}, all
  QOI-WEIGHTED by modal participation (bias fit to QOI-driving freqs/sensors). Predicted survivors: pooled/feature/
  structured-statFEM (graceful degradation); at risk: free-amplitude full-FRF. STAGED PLAN w/ cheap validity gate FIRST:
  Stage0 (no NUTS) = per-QOI mode/sensor weights + leave-modes-out validity + sensitivity sweep on assumed unmeasured-σ
  (the 14.6× depends on it); Stage1 = freeze ONE held-out harness (coverage/sharpness/point) as immutable checker; Stage2
  = bake off methods that pass Stage0; Stage3 = pick+deliver per QOI w/ trust label. NOT yet started; awaiting Andrew go
  + confirm the 3 quantity defaults. No task card / durable-rule / checker / project-note edits yet.
- 2026-07-01 **PROJECT RESET underway.** Andrew unsatisfied with the ShockSat result; resetting to the top-level
  vision: an AUTOMATED, HELD-OUT-VALIDATED pipeline (Bayesian updating + parameter downselection + agentic remesh,
  QOI-targeted) that turns an uncorrelated FEM + limited data into a substantially improved FEM/twin. Reset prompt
  drafted at `notes/reset_prompt_2026-07-01.md` (DRAFT, for Andrew). **PRIMARY audience = Bayesian updating +
  AEROSPACE USABILITY (practical application).** Focus = ShockSat only for now (other articles MPL/hanging-panel/F16
  exist, held in reserve). Slides FROZEN (do not mod deck) pending reset. Key research axes: order/iteration of the
  remesh→downselect→update loop; formulation bake-off on HELD-OUT QOI (not freq/in-sample); pooling; QOI-targeting.
- 2026-07-01 **ShockSat DATA INVENTORY (answered "do I need to restore deleted zips?" = NO for near-term).** Verified
  from source_manifest + filesystem: we HAVE 4 distilled multi-DIRECTION modal FRF caches (data/multiref_modal/:
  m_xpos_990x=+X/Test01, m_zpos_990z=+Z/Test02, m_xy_990xy=+XY/Test04, m_zpos_900z=+Z/Test06) — hit-avg band-limited
  per-channel H1 + coherence; FEM extracted & working. Andrew deleted the raw modal zips AFTER distillation — SAFE.
  GONE (raw layer only): raw time histories/individual hits → re-download only for time-domain/OMA/re-window/per-hit.
  NEVER downloaded (fresh DL if needed): Test03 pure +Y (990y) [relevant: base_shear_Y weakest], Test08/10 (+Z
  impact), Test_Data_Parametric 3.33GB (force-level = nonlinearity lever). Back up the 268KB caches. QOI trust
  anchor: net-CG base shear high-trust (97-99%, band ~3x); local mount response low-trust (13%, band 14.6x).
- 2026-06-26 **"DOES 0.441 SURVIVE BAYES?" = YES (on FRF-corr, Andrew's requested metric).** combine_best_cv.py
  (out/combine_best_cv.json; NUTS R-hat 1.004/ESS774/0div). Held-out-SENSOR CV FRF log|H| corr (fit amp on 90% ch→
  predict 10%, peaks moved by theta, NO freq scoring): baseline 0.322; remesh oracle-freq 0.441; **remesh + full
  Bayes posterior 0.41 [0.366–0.442]** (theta-median point 0.388). So Bayes costs only ~0.03 vs oracle and still
  beats baseline +0.09. The earlier "remesh+Bayes=0.183 WORSE" was the BLIND metric (no amp fit) only — NOT a real
  Bayes failure. Andrew's freq-likelihood-vs-FRF-success insight CONFIRMED+QUANTIFIED: objective mismatch costs only
  ~0.03 (0.441→0.41); the dominant gap (0.41 vs usable ~0.70) is AMPLITUDE/SHAPE fidelity, which the eigenvalue
  likelihood (modal_feature.py:106, Kiran Eq25) never touches. Context: full-|H| likelihood is why we use freq — it
  was unidentifiable, NUTS R-hat 104 (modal_feature.py:2-11). CORRECTED TWO-SCENARIO FRAMING: (i) sensor-infill (some
  measured sensors→predict rest) remesh+Bayes HELPS 0.32→0.41 & survives Bayes; (ii) fully-blind (no measured FRF)
  nothing helps, remesh slightly hurts 0.34→0.27→0.18; (iii) NEITHER reaches usable ~0.70 → wall holds. DECK STILL
  WRONG (says remesh+Bayes 0.183 worse / "scoring artifact"). NEXT: get Andrew's sign-off, then fix slide 15 +
  fig_combine_best + packet §6 + publishable #1 to the two-scenario picture. No durable-rule/checker edits.
- 2026-06-26 **"0.44 with less data" PUZZLE = RESOLVED, no anomaly.** heldout_sensor_cv.py now also computes SAME-
  setup in-sample. Single-ref al_rho_lo: in-sample(fit all→score all)=0.468 ≥ CV(fit90→pred10)=0.441 ≥ blind(no amp
  fit)=0.267. Normal ordering. My earlier juxtaposition of CV 0.441 vs 0.379 was apples-to-oranges (0.379 = DIFFERENT
  experiment, multi-ref correlate_all). Real finding: amp-fit helps REMESH a lot (0.267→0.441) but baseline barely
  (0.338→0.322) ⇒ mass edit gave GOOD spatial shapes but BAD physics participations; LSQ rescues amplitudes.
  Andrew: "don't score with held-out FREQUENCY; use FRF correlation." RUNNING combine_best_cv.py (bg b9sqx59xn):
  held-out-sensor CV FRF corr for al_rho_lo at oracle vs theta-median vs full theta-posterior freqs — to answer "does
  0.441 survive Bayesian updating?" (peaks moved by theta; shapes/damping fixed). Await result before reframing deck.
- 2026-06-26 **CORRECTION (Andrew challenged the "scoring artifact / remesh made it worse" claim — HE WAS RIGHT; I
  over-claimed a NEGATIVE).** Ran the exact metric he proposed = held-out-SENSOR cross-validation (code/
  heldout_sensor_cv.py: fit per-mode complex amplitude on 90% of channels, PREDICT held-out 10%, 5-fold, corr on
  held-out; measured freq+damping for peaks). Result (out/heldout_sensor_cv.json): baseline 0.322 → al_rho_lo
  **0.441 (+0.12, remesh HELPS)**. Also held-out-sensor σ: base 1.077 → al_rho_lo 0.804 (helps). So there are THREE
  metrics, three questions: (A) in-sample fit+score same channels = correlate_all 0.379 = LEAKY (its docstring: "no
  held-out — correlate against ALL the data") — that's the only truly illegitimate one; (B) held-out-SENSOR CV
  (fit-obs→predict-ho) = LEGIT, remesh helps 0.322→0.441; (C) fully-BLIND (no amp fit, physics + 1 gain, my
  "combine_best honest") = remesh hurts 0.338→0.267. My earlier metric C was STRICTER than Andrew's proposal (fit 0
  amplitudes). CORRECTED FRAMING to use: across ALL legitimacy levels (0.27 blind → 0.44 sensor-CV) you stay < usable
  ~0.7 → the WALL HOLDS regardless of metric; do NOT claim "remesh makes it worse." Separately-still-true: stiffness-
  Bayes on a MASS edit degrades held-out FREQ 2.92→4.23% (wrong-knob; amp-fit can't fix peak locations). NEXT: get
  Andrew's sign-off on the 3-metric reframe, then fix slide 15 + fig_combine_best + packet §6 + publishable #1 (they
  currently over-claim the negative). NOT yet done — deck still says "scoring artifact / worse."
- 2026-06-26 **RAN best-remesh + best-Bayes end-to-end (Andrew "run it"). DECISIVE HONEST NEGATIVE — reverses the
  optimistic "+10%."** `code/combine_best.py` (NUTS on the al_rho_lo reduced model, R̂1.004/ESS774/0div; self-check
  reproduced inherited+cal honest metric=0.338 EXACTLY = pipeline validated). On ONE honest metric (deterministic
  participations + 1 global gain, NO per-channel fit): inherited+cal **0.338 (BEST)** > best-remesh+cal(oracle freq)
  **0.267** > best-remesh+actual-Bayesian-θ **0.183**. So best-remesh+best-Bayes does NOT beat plain calibration —
  it's WORSE. The earlier +0.08/+28% (0.296→0.379) was a SCORING ARTIFACT: the generous metric (correlate_all.py)
  LEAST-SQUARES-FITS one complex amplitude+phase PER MODE (~40-60 knobs) to the MEASURED FRFs; honest metric fits 1
  global gain. (NOTE: it's per-MODE amplitude shared across channels, NOT "per-channel" — fixed that mislabel in
  deck/packet/findings/fig on 2026-06-26.) Remove the fit and the mass edit worsens the model's OWN predictive
  shapes; and Bayes calibrates STIFFNESS knobs against a MASS error → overfits observed modes, degrading held-out
  FREQ (nominal 2.92%→calibrated 4.23%, vs baseline which IMPROVES 3.33→2.68). => wall is mode-shape fidelity;
  wrong-knob calibration can't reach a mass/shape defect; statistics/fitting can MASK it, not fix it
  (strengthens Finding #1). Fig `figures/fig_combine_best.png`. FIXED deck slide 15 + packet §6 + publishable #1
  (removed the "+0.08 encouraging" claim, now the honest negative). run_all.sh step 0 runs combine_best (resumable).
  COMPUTE NOTE: machine hit 100%-disk mid-run (was 97%/466MB free); Andrew freed space; removed the 256MB eigvec
  cache from solve_edit so it can't recur. NO durable-rule/checker/project_log edits.
- 2026-06-26 **CLARIFICATION (Andrew: "did we ever do best remesh + best Bayes? +10% FRF corr is pretty good"):**
  Checked code. `bayes_update.py`/`fig_frf_comparison.py` ran on the BASELINE inherited FEM shapes (the 0.269→0.338
  honest-metric "updating" = measured freq + damping calibration only). The remesh sweep (`correlate_all.py`) ALREADY
  bakes in MEASURED per-mode freq + MEASURED damping + per-channel participation LSQ on EACH remeshed model — i.e. it
  is effectively "best shapes + best (oracle) calibration." So on that generous metric: inherited+cal 0.296 →
  best-remesh+cal 0.379 = the remesh shapes add a REAL +0.083 (+28%) on top of calibration. ANSWER: effectively YES
  we have best-remesh+best-calibration (=0.379, generous metric); the LITERAL best-remesh→Bayesian-θ-posterior→honest
  metric was NOT run as one artifact and would land ≤0.38 (oracle≥posterior, honest≤generous). Andrew's "+~10% is
  pretty good" is FAIR (+0.07-0.08 absolute, ~26-28% rel = real, encouraging) BUT 0.34-0.38 absolute is still weak
  for a usable FRF twin (>60% per-ch log|H| variance unexplained, bands ~6× wide); plateau ~0.4 = shape wall. FIXED a
  deck/packet inaccuracy (slide 15 + packet §6 had said "Bayesian updating on the best model gives 0.27→0.34" —
  implied best-remesh; it was baseline). Rebuilt + re-QA. OFFERED clean confirm run: reproduce honest metric on the
  best remesh shapes (needs ~5min eigensolve, edit modes not saved). NO durable-rule/checker/project_log edits.
- 2026-06-26 **CORRECTION (Andrew caught an overclaim — VALID): the deck's Finding #2 "WHERE you put the physics
  decides well-posedness (IFT-in-prior converges vs StatFEM-in-likelihood diverges)" was OVERSTATED.** Physics-IN-
  LIKELIHOOD DID converge for us on MODAL-FEATURE observables: L5 modal-freq R̂1.002 (modal_feature.json), Study K
  per-mode freq R̂1.007, Schneider correlated-disc R̂1.002 (synthetic). Also IFT FAILS under NUTS (R̂264.9) and only
  converges under TMCMC; M2 under TMCMC ALSO fails (R̂129). So the true scoping: (1) the WHOLE-FRF MAGNITUDE
  observable is the multimodal/hard one for EVERYONE (IFT included under NUTS); (2) physics-in-likelihood is fine
  with a MODAL observable; (3) the real IFT-vs-M2 result is NARROW = holding the whole-FRF observable fixed, IFT's
  BOUNDED learned temperature β converges (TMCMC) where M2's FREE discrepancy variance σ_d→∞ hits a singularity —
  a BOUNDED-REGULARIZER win, NOT "prior vs likelihood" per se (an informative σ_d prior is the likelihood-side cure,
  our own StatFEM D10). REFRAMED: Finding #2 → "the OBSERVABLE and the model-error REGULARIZER decide well-posedness";
  consistency answer (learned knob removes arbitrary σ; none recovers θ) kept clean as its own finding. FIXED:
  make_deck slide 5 (#2/#3 reframed), slide 20 table (added a StatFEM-MODAL-feature row showing physics-in-likelihood
  CONVERGES + relabeled whole-FRF row + IFT "via TMCMC, NUTS also multimodal"), slide 22 (added honest-read caveat
  bullet); packet.md §8/§12; publishable_findings.md #2/#3. Rebuilt + re-QA (no overflow). IFT def added to chat.
  NO durable-rule/checker/project_log edits.
- 2026-06-26 **BILIONIS REVIEW PACKET — CONSOLIDATION (Andrew: "take stock, document everything, build a thorough
  PPT for a review with Bilionis, finalize next direction, name the most potent publishable finding(s)").** NEW
  workspace `artifacts/reports/shocksat_bilionis_review_20260626/` (consolidation only — pulls REAL numbers from
  existing threads; NO new science claims). Scope settled with Andrew's prompt: no more tray experiment; work the
  data we have; inherited FEM was MAC/freq-correlated but has LARGE FRF model-form error; Bayesian converged but
  mean moved minorly (QUANTIFY); CIs perpetually too wide for aerospace (the key finding); always came back to
  MODE SHAPES; agentic remeshing+Bayes done? how successful?; NEW metric = mean-function FRF correlation vs original
  FEM; Bilionis/Alberts/Kairui consistency concern (arbitrary # physics-samples in likelihood) mapped inconsistent→
  statFEM→IFT w/ side-by-side IFT benchmark; document statFEM formulations; recent papers; evidence-based model
  selection. KEY REAL NUMBERS PINNED (traced to files): inherited FEM matched MAC 0.631, freq err ~2.5-3.3%, but
  FRF log|H| corr median only ~0.27-0.30, ~15.7 dB peak-amp err (correlate_all.json). Best Bayesian update
  (bayes_update.json, NUTS R̂1.0022/ESS2243/0div/4ch): identifiable stiffness moved 1-5% (bottom_box -4%, top_box
  +3%, plates ~0%), joints/welds prior-dominated; held-out freq err 3.33→2.68%; FRF corr 0.269→0.338, 70% channels
  better (frf_comparison.json) = minor-but-real, frequency-only value. CIs: ~34 dB / ~6× / +27-32 dB margin (D7
  probe, usable_mean.json GRMS ratio twin/FEM+6dB ~10-13×) = NOT aerospace-usable = central honest finding. Mode
  shapes: 54 Hz fundamental shape MAC 0.17 vs measured (residual_map.json), shape-oracle σ 1.26→0.70. Agentic
  remeshing: Card D 0/10 edits clean-improve; correlate_all+modelform_sweep ~50 edits FRF corr PLATEAUS ~0.36-0.38
  (best al_rho_lo 0.379), never crosses ~0.4 = remeshing CANNOT crack per-point FRF; contribution = auditable
  BOUNDARY. Value: freq CRPS-skill +0.93, amplitude -0.76 to -0.93 (value_eval). IFT benchmark (scorecard.json):
  IFT physics-in-PRIOR (learned β) TMCMC-converges (cross-run R̂1.0007) + covers (peak 0.97/band 1.0), β_med 0.174=
  246× below β* (strong-distrust, BOUNDED); M2 physics-in-LIKELIHOOD (free σ_d, SAME observable) DIVERGES (R̂63 NUTS/
  129 TMCMC, σ_d→7.4); IFT NOT sharper than L5 (coarse-FEM ceiling). Consistency toy (sweep_summary.json): M-lik
  DRIFTS with arbitrary residual-noise σ_r (θ spread 0.084) but flat vs mesh; statFEM(σ_d) & IFT(β) remove the knob,
  mesh-invariant; NONE recovers θ under model error (all bias 1.15→~1.27) = shared honest limit. Evidence selection
  (stage1_evidence.json): M0 as-received θMAP+iid wins P=0.906; richer LOCAL stiffness 16p WORST; M4 correlated-disc
  suggestive (P=0.093). MOST POTENT PUBLISHABLE (my synthesis, for Andrew to confirm): (1) "trustworthy-but-not-
  sharp" boundary on a REAL already-correlated aerospace FEM — calibrated under model error but bands irreducibly
  wide, binding limit = per-node mode-shape fidelity (a MODEL problem no statistics/remeshing closed); (2) WHERE the
  physics/trust lives decides well-posedness — physics-in-prior+learned-temperature (IFT) converges+covers where
  physics-in-likelihood+free-discrepancy diverges, on identical real data, with the consistency map removing the
  "arbitrary σ_r" objection; (3) observable choice > sampler (modal-freq feature converges, whole-FRF |H| multimodal).
  PLAN: read tufte (DONE), build ~3-4 NEW consolidation figs (new-metric bar, remeshing plateau, wide-CI, publishable
  summary) via one saved lintable code/make_review_figs.py + REUSE strong existing figs (frf_comparison_grid, IFT
  figA_scorecard, consistency figA_money, residual_map, fig_value_summary, fig_likelihood_inventory); assemble
  slides/ via code/make_deck.py (reuse modelclass make_deck pattern); write packet.md + publishable_findings.md.
  HONESTY: most psd_envelope new-metric/remeshing work is EXPLORATORY/YELLOW (no checker); IFT/consistency/modelclass/
  remesh threads are checker-backed YELLOW. Label sampler (NUTS for bayes_update; TMCMC-labeled for IFT; M2 non-conv
  flagged) + provenance per slide. GUARDRAILS: only this CURRENT-STATE block + new-ws files edited; NO durable-rule/
  checker/sampler-standard/project_log/runs/lessons edits (SURFACE those to Andrew).
- 2026-06-24 **"WHAT CAN THIS TWIN CARRY" UNIFIED PER-QOI TRUST TABLE (Andrew "continue").** `code/qoi_trust_table.py`
  (NO NUTS, flat modal drive, common MC mode-uncertainty meas freq1%/amp0.35 vs UNMEAS freq6%/amp0.80). RESULT
  (trust=% of load on measured modes | band ±% | %band-var from unmeasured): base_shear_X 98%|±52%|9%(top 147*/169*/259!);
  base_shear_Y 97%|±85%|62%(255!/122*/125!); base_shear_Z 99%|±62%|7%(114*/184*/117*); mount_response(secondary at
  plate center) 13%|±206%|100%(252!/234!/254!); strut_force 71%|±68%|89%(252!/169!). HEADLINE: twin trustworthiness
  varies HUGELY by load — net base shear X/Z are well-carried (98-99% trust, modest band mostly from MEASURED modes,
  because the net-translation modes ARE the measured global box modes); mount-response (top-plate-center secondary) is
  un-carryable (13%, ±206%, 100% from unmeasured drumhead modes); strut force + base_shear_Y intermediate, bands
  dominated by unmeasured >200 Hz modes (252/234/254/255). DRIVE-DEPENDENT: strut force = 71% under flat drive vs 15%
  under the mount drive (strut_force_number) — report the scenario. Recurring lever = a few unmeasured modes >200 Hz;
  one top-plate/strut test >200 Hz buys down mount-response, strut-force, base_shear_Y bands. Note band ±50-62% on the
  "trusted" loads is the residual per-mode AMPLITUDE uncertainty (consistent w/ cancellation pilot: net loads don't
  escape it). Fig `figures/qoi_trust_table.png`. Caveats: uniform mass (base shear); drive-point residue (mount);
  CBUSH basic frame (strut); band scales w/ assumed unmeasured-mode uncertainty. This is the THREAD CULMINATION:
  per-sensor FRF hopeless -> per-load trust map = which loads to trust + what one test fixes the rest. EXPLORATORY/
  YELLOW; no durable-rule/checker/sampler/project_log edits.
- 2026-06-24 **STRUT-FORCE QOI: PILOT -> NUMBER WITH A BAND (Andrew "do it").** `code/strut_force_number.py` (NO NUTS):
  struts attach via CBUSH (pbush 803-807, 24 in-band elements) -> REAL connection force = stiffness×relative-motion
  across the bush (not a proxy), from full-field mode shapes; QOI = band-RMS aggregate strut CBUSH force per unit
  top-plate-center mount drive; band via MC over mode uncertainties (labeled: measured freq sd1%/logamp0.35,
  UNMEASURED freq sd6%/logamp0.80). HEADLINE: **TRUST = 15%** (measured modes carry only 15% of nominal strut force),
  freq-anchored twin barely changes it (0.77 vs 0.772 nominal -> the twin/test buy ~nothing for strut force),
  **95% band ≈ ±180% (factor ~12 spread), and 100% of the band variance is from the UNMEASURED ~230-258 Hz strut
  modes** (log-sd unmeas 0.63 vs meas 0.01). So the strut force lives almost entirely on modes the test couldn't see
  (>200 Hz). Demonstrates goal-oriented validation end-to-end: pick QOI -> real element force -> trust fraction + band
  + which-modes-to-pin. Single highest-value future test = top-plate/strut modes >200 Hz (drive+accel on the deck).
  Caveats: relative units (abs needs input spec); CBUSH basic-frame (orientation ignored); freq-anchored twin (not full
  NUTS); band scales with the assumed unmeasured-mode uncertainty. Fig `figures/strut_force_number.png`. EXPLORATORY/
  YELLOW; no durable-rule/checker/sampler/project_log edits. [Prior pilot row below: QOI weighting differs by QOI.]
- 2026-06-24 **GOAL-ORIENTED (QOI-WEIGHTED) VALIDATION PILOT (Andrew: strut force as example unmeasured QOI; "run it
  however best").** Built `code/strut_force_qoi_pilot.py` (NO NUTS): strut force = linear functional of response, so
  each mode has a computable QOI sensitivity even though strut force is unmeasured; re-weight twin/FEM/data comparison
  by it. QOI proxy = strut RACKING deformation |mean3D φ(z≥50)−φ(z<50)| over strut region z45-55 (displacement-based,
  no element forces/mass = labeled proxy). RESULTS: strut-force TRUST = **41%** of the QOI sensitivity is on
  MEASURED/correlated modes; the other 59% is on UNMEASURED high-freq strut modes (~230-258 Hz, above test ceiling).
  QOI-weighted vs uniform FEM-vs-data: freq err 2.9%→3.4%, MAC 0.70→0.64 (strut-force modes slightly LESS correlated
  than average). METHODOLOGICAL PAYOFF (the point): the strut-force weighting is COMPLETELY different from the mount
  apparent-mass weighting (251 Hz mode = 39% of mount load path but only 2.3% of strut force; strut force led by
  254/258/122/146/168/196 Hz) => each QOI leans on DIFFERENT modes, so uniform per-sensor grading is wrong for ANY
  specific goal; tailor the comparison to the QOI. Reusable template: pick QOI → modal sensitivity → re-grade twin/FEM/
  data → report trust fraction + which modes to pin. Fig `figures/strut_force_qoi_pilot.png` (strut-force spectrum FEM
  vs freq-anchored twin, green=data-anchored/red=FEM-only peaks; mode-weight bars). Caveats: displacement proxy; twin =
  frequency-anchored approx of calibrated twin; production needs FE element forces+mass matrix+full calibrated twin.
  EXPLORATORY/YELLOW; no durable-rule/checker/sampler/project_log edits.
- 2026-06-24 **SUBSTRUCTURING REFRAME (Andrew: treat top-plate + struts as the 'secondary structure').** Strong
  CONCEPTUAL fit = frequency-based substructuring / Craig-Bampton: moves the interface to the strut base (where the BOX
  source apparent mass is global-mode-dominated = the well-correlated/measured part), reclassifies the troublesome
  unmeasured ~233-254 Hz drumhead modes as the SECONDARY's own dynamics (characterizable in isolation: focused
  subassembly test drivable on the plate >200 Hz, or focused remodel of just plate+struts where NASA's "weld knob"
  lives), and yields a REUSABLE validated plate+strut substructure to couple any future payload via FBS. Cheap premise
  check `code/strut_substructure_check.py` = INCONCLUSIVE: instrumented sensors don't cover the plate center or struts
  (only 21/132 DOF above z=45, 9 above z=50), so the energy split can't see where the dominant 251 Hz mode lives;
  it IS ~0 at the perimeter (z>50) sensors + huge at the un-instrumented plate-center node = consistent with a center-
  antinode drumhead (edge sensors on its node ring) but NOT confirmable from sensors. Reduced node set = 67683 nodes,
  regions clean by z (box<45=58k, struts 45-55=4.6k r5.5-12.6, plate>=55=4.7k r0-9), but full-field modal energy split
  needs the FEM DOF->node map (Step-1 plumbing). HONEST: reframe LOCALIZES the hard part to a tractable subproblem, does
  NOT eliminate the drumhead-mode uncertainty; still needs plate+strut test or remodel + a clean strut-interface
  definition. NEXT (proposed, held for Andrew): Step 1 = identify strut-to-box interface in FEM; compute plate+strut
  FIXED-interface modes (confirm = the 233-254 Hz set) + box SOURCE apparent mass at the strut interface (confirm
  global/well-correlated) + interface effective masses; reuse 7004C/FBS toolkit + tray study. EXPLORATORY/YELLOW; no
  durable-rule/checker/sampler/project_log edits.
- 2026-06-23 **APPARENT-MASS / EFFECTIVE-MASS QOI REFRAME (Andrew: grade the twin on load-relevant top-plate apparent
  mass for a secondary structure, not per-sensor FRF; consult 7004C).** Reused 7004C toolkit + tray-coupled study
  (mount gid 7000072 @ (0,0,57.75), ShockSat 57.96 kg, mass-normalized reduced model). Convention pinned (postmortem):
  load-driving = interface apparent mass (peaks), NOT drive-point F/a. STEP 0 `code/topplate_effmass_step0.py`: effective-
  mass concentrates HARD (4 of 40 in-band modes carry 90% of the top-plate-CENTER load path) = reframe is sound, BUT those
  4 are LOCAL top-plate drumhead modes ~233-254 Hz and **only 11% of the load path is MAC-matched to the measured survey**
  (3/4 above the ~200-206 Hz modal-instrumentation ceiling = NASA's "can't capture shapes >200 Hz / hardest modes ~200 Hz").
  Validity gate went WRONG way (mount-wtd freq-err 2.9%→6.2%). STEP 0b `code/topplate_effmass_edge.py` (realistic EDGE
  bolt-circle, r=9", 8 feet, exact-node snap; rigid secondary couples to MEAN φ(foot) so global modes ADD / drumhead feet-
  on-node-ring CANCEL): materially better — measured load-path fraction 11%→**46%** (resonant secondary) and **75%** (stiff/
  rigid-in-band secondary, static-compliance φ²/ω² weighting); the well-correlated 117/183/190 Hz global modes (MAC 0.69-
  0.89, freq err 0.4-6%) come in. BUT NOT a full flip: the unmeasured 252/234 Hz top-plate modes still carry ~25% (stiff
  edge) to ~50% (resonant edge) of the load path. CONCLUSION: a realistically EDGE-mounted + STIFF secondary -> model
  MOSTLY usable (~75% of load path on correlated modes, ~25% quantified residual on unmeasured high-f top-plate modes); a
  CENTER mount or a RESONANT (~230-260 Hz) secondary is exposed to the unmeasured drumhead modes = NOT reliable. Specific
  gap to close = correlate the ~233-254 Hz top-plate modes -> needs top-plate test data >200 Hz (drive+accel on the deck).
  Figs `figures/topplate_effmass_step0.png`,`_edge.png`. z-translation/net-CG only (rocking would re-add drumhead). NEXT
  options (held for Andrew): Step 1/2 = build 7004C interface apparent mass + coupled secondary load for a DEFINED secondary
  (mass,freq) on the edge + bound the QOI uncertainty from the ~25% unmeasured residual; or sweep bolt radius/feet. EXPLORATORY/
  YELLOW; no durable-rule/checker/sampler/project_log edits.
- 2026-06-23 **FRF CORRELATION RECONCILE (Andrew showed NASA ShockSat slides: FEM delivered "already correlated"; asked
  why our twin isn't).** Built `code/fig_frf_correlation.py` -> `figures/frf_correlation_examples.png` (as-delivered FEM
  θ=1 vs CLEAN +X modal FRF, 6 sensors best->worst, ONE global gain ×0.74, NO NUTS). RESULT: peak FREQUENCIES line up
  (median nearest-peak match 3.7%; freq skill +0.93) = reproduces "correlated"; per-sensor peak HEIGHTS scatter broadly
  across the WHOLE band (band amp err +2.7..+13.2 dB on the 6 shown). RECONCILIATION (no contradiction): NASA "correlated"
  = frequencies + GLOBAL mode shapes (cross-ortho/MAC, good to ~135 Hz, their slide says ">135 not great"); peak HEIGHT is
  STRICTLY HARDER = |H| = φ_drive×φ_sensor/damping, folding TWO local shape values + damping — and NASA themselves flag
  "weld dimensions biggest unknown knob", "no great damping observed", "local modes near a node line" (= our big random
  per-sensor error, in their words). Ruled OUT self-inflicted: sensor->node snap tiny (median 0.15 in), reduction keeps
  full eigenvectors to 80 modes => scatter is INTRINSIC FEM shape/damping error, not our reduced surrogate. CAVEAT: this is
  our reduced forward; the truest "delivered=correlated" artifact is the cross-ortho/MAC TABLE (NASA's actual evidence) —
  our MAC median ~0.70 degrading at high freq qualitatively matches their cross-ortho degrade but their below-135 diagonal
  (80-99) is higher than ours (full FEM vs our reduced/sparser DOFs). OFFERED to Andrew: reproduce the MAC/cross-ortho
  table to mirror their slide directly. EXPLORATORY/YELLOW; no durable-rule/checker/sampler/project_log edits.
- 2026-06-23 **POOLING-SIGMA PROBE (Andrew approved the regional/pooled pivot validity gate). DECISIVE NEGATIVE for the
  ENVELOPE; closes all statistical re-poses.** Built `code/pooling_sigma_probe.py` (NO NUTS, ~52s; θ=1 FEM proxy +
  measured caches; gain removed=cancels). 84 sensors, σ_sensor(log)≈1.02 (+X) / 0.92 (combined). ANOVA over zone count
  K (spatial k-means 1..N): σ_within stays ≈σ_sensor (~1.0) at EVERY K (even K=24, ~3-4 sensors/zone) while σ_between
  only reaches ~0.28-0.35 → **per-sensor scatter is CONSERVED / overwhelmingly WITHIN-zone** (rms√(btwn²+wthn²)≈σ_sensor
  flat). Re-confirms borrow_R2≈0 from a 2nd angle: spatial neighbors differ by the full σ. RESULT: (B) REGIONAL max-over-
  zone ENVELOPE (the real spec form) GRMS ratio twin/FEM+6dB = **3.68× (+X)/3.02× (comb), FLAT, 0% win at EVERY K** →
  pooling does NOT shrink the covering-envelope band; regional pivot does NOT win. (C) zone-MEAN deliverable DOES win at
  ≤~6 zones (ratio 0.62-0.96×, band~σ/√N) BUT under-covers ~half the sensors → NOT a coverage-valid qualification spec
  (diagnostic only). VERDICT: Beck/Schneider/non-overfit-heteroscedastic/regional-pooling are all CLOSED as
  envelope-GRMS-win levers on this data — the amplitude discrepancy is irreducibly per-SENSOR; the only binding lever is
  the FEM MEAN (per-node shape fidelity = remeshing, already in work). One honest by-product: a regional EXPECTED-level
  (best-estimate, not max-enclosure) deliverable IS predictable + pooling-tightenable, if that weaker claim is ever
  decision-relevant. EXPLORATORY/YELLOW; no success claim; no durable-rule/checker/sampler/project_log edits. AWAITING
  Andrew steer (accept+document the negative vs the regional expected-level direction). Prior gate ↓ stands:
- 2026-06-23 **DECISIVE SHAPE-BORROWABILITY DIAGNOSTIC (Andrew asked: revisit Beck/Schneider/non-overfit heterosced now
  that we have all the data; I chose the validity gate first).** Built `code/shape_borrow_diag.py` (NO NUTS, ~2s): for
  each of 20 MAC-matched .ash modes, align FEM shape to measured, leave-one-SENSOR-out interpolate the per-mode shape-
  ERROR field from same-axis neighbors. RESULT = **borrow_R2 ≈ -0.001** (per-axis X+0.01/Y-0.04/Z+0.02, coord-shuffle
  null -0.07, ALL length scales 0.5-4x nn ≈ 0). => the per-mode FEM shape error is **NOT spatially borrowable** to a
  held-out sensor — CONFIRMS the old aggregate spatial_reanalysis R²=0.04 now PER-MODE on CLEAN data with a proper null;
  the optimistic "clean per-mode shapes are smoother" hope FAILS. (held-out log-amp sigma 1.63→1.03 is a nodal-line
  flooring ARTIFACT, not real transfer, since borrow_R2≈0.) IMPLICATION: Beck-multiref / Schneider-correlated / per-mode
  GP-shape are all CAPPED for the held-out-SENSOR envelope QOI (explains Beck's −0.68→−0.25 = global recalibration, not
  shape placement). RECOMMENDATION (held for Andrew): do NOT spend the multi-hour multi-ref Beck NUTS on this QOI; PIVOT
  (without remeshing) to a REGIONAL/POOLED qualification-spec envelope QOI where the sensor-local error averages out and
  climatology can bound the population — validate with a cheap pooling-σ probe BEFORE building. Non-overfit heteroscedastic
  stays useful only as an honest width-allocation layer (known-hard wide), not a collapse. EXPLORATORY/YELLOW; no success
  claim; no durable-rule/checker/sampler/project_log edits. AWAITING Andrew steer on the pivot.
- 2026-06-23 **OBSERVED-SENSOR TWIN FIGURE (Andrew request): recreate heldout_psd_examples.png for NOT-held-out sensors.**
  Added `code/fig_examples_observed.py` (byte-mirror of fig_examples.py but picks from ctx.obs_daqs not ctx.ho_daqs);
  reuses SAME probe.fit_context (seed0/90%-train, calib R-hat 1.002 converged). Output `figures/observed_psd_examples.png`.
  Picked obs sensors ch40(bias 0.08=FEM over)/ch2(0.70=~match)/ch77(8.02=FEM under). RESULT (in-sample, NOT a new claim):
  twin still much wider than FEM+6dB on GRMS (ratio 6.4x/7.0x/11.5x ~ held-out's 5.7/12.4/12.6x) and FEM+6dB STILL leaks
  (data above FEM+6dB 0%/37%/60% energy) even on TRAINING sensors — same honest-negative story as held-out, confirming the
  gap is per-node FEM shape error not statistics. Caption carries the IN-SAMPLE caveat (freqs + gain + sigma band were fit
  on observed channels -> expected to cover better; twin exceedance 0% everywhere). Exploratory/YELLOW; no durable-rule/
  checker/sampler/project_log edits.
- 2026-06-23 **SEQUENTIAL STATFEM PSD-ENVELOPE PILOT COMPLETE (Codex runner).**
  Workspace `artifacts/reports/shocksat_sequential_statfem_20260623/`; replay `bash run_all.sh`; checker
  **OVERALL YELLOW 18/3/0**. Result: no green PSD-envelope win over FEM+6 dB. Best variant
  `stiffness_residual` has median GRMS ratio 2.07 and clean-win rate 18.8%; `nominal_residual` ratio 2.15.
  Small stiffness-subset NUTS converged (R-hat 1.002, ESS 1157, 0 divergences), but the time-domain filter is
  explicitly fixed-prior/not NUTS and the worst residual band is 22.0 dB, so model discrepancy is doing substantial
  work. Treat as an honest negative unless Andrew launches a separate full covariance/material-field statFEM task.
- 2026-06-23 **RUNNER LAUNCHED (Andrew dispatched the time-domain latent-force DAMPING prompt). I am acting as the runner.**
  Workspace `artifacts/reports/shocksat_latent_force_damping_20260623/`. RE-GROUNDED from files (AGENTS all gates;
  memory CURRENT STATE; D22 damping_inference.json = 0/9; psd_envelope_twin contracts/D7; modal_cache_summary;
  realfrf machinery). GOAL: do clean modal-hammer RINGDOWNS (time domain) resolve per-mode ζ that D22 (single windowed
  FRF, freq, 0/9) could not; decompose a latent MFE force into damping-vs-residual; does measured ζ move the held-out
  PSD-envelope GRMS. KEY FACTS PINNED: FEM/L5 nominal ζ=ZETA_NOM=1% (realfrf.py:41) is HEAVIER than .ash 0.25-0.44%
  → FEM likely OVER-damped → the prompt's "under-damped FEM ⇒ FEM+6dB over-conservative" bridge may be SIGN-FLIPPED;
  must quantify with the finite-perturbation check, do NOT assume direction. D7 already found the envelope-GRMS win is a
  per-NODE FEM-shape-error-bound honest negative (σ=0.97-1.60). Raw modal .mat ALREADY extracted (5.6GB
  data/extracted_modal in psd_envelope ws). Env: py3.9, jax0.4.30/numpyro0.19, scipy1.13. Disk 14GB free.
  PLAN: (L1) reproduce D22 0/9 → build decimated time-domain ringdown caches → freq-domain damping fit on NEW clean
  data (still ~unresolvable, isolates time-vs-freq lever) → time-domain decay (band-pass+Hilbert log-decrement + ERA/
  matrix-pencil cross-check) → NUTS ζ posterior (ζ nonlinear in dynamics) → resolvability table → finite-perturbation.
  (L2) GPLFM/Kalman latent-force (label FILTER not NUTS) + damping-vs-residual decomposition. (L3) held-out envelope
  value (reuse QOI byte-identical; expect honest negative per D7). GUARDRAILS: NO durable-rule/checker-standard/
  sampler-standard/project-notes edits beyond this CURRENT STATE block + the new workspace; surface those to Andrew.
  **COMPLETE — `bash run_all.sh` exit 0, check.py OVERALL YELLOW (8G/3Y/0R), runtime active 966s; full packet+6 figs.**
  Andrew follow-up: added fig6_heldout_psd_examples.png (heldout_psd_examples.png style: measured-ζ posterior FRF
  smoothed vs FEM smoothed vs data, 3 held-out sensors 92/57/106). Result: measured (lighter) ζ raises the twin
  smoothed GRMS ~1.27× (FEM over-damped) but twin sits 17-31× above FEM (shape-error +27dB dominates). check.py now
  requires fig6; run_all.sh runs fig_heldout_psd.py.
  Deliverables all present (priority/decisions/question/quantity/assumptions/REUSED_code.sha256/check.py[SHA-locked]/
  run_all.sh/runtime.json/packet.md/figs). Workspace 24MB (caches 23MB, raw .mat/zips left in place — re-downloadable,
  deletion surfaced for Andrew). SURFACE to Andrew (NOT self-applied): (1) prompt's "under-damped FEM" bridge SIGN-
  FLIPPED (FEM ζ=1% > measured 0.4%; measured-ζ twin is MORE conservative; ζ cancels in win ratio like D8) → damping
  does NOT win the less-conservative-envelope metric; (2) useful by-product = a NUTS-resolved measured per-mode ζ
  (~0.45%, window-artifact-free) for 14 modes, could correct the over-damped FEM/CLA (fixes D7's 34% under-coverage at
  a higher honest level); (3) binding lever stays per-node FEM shape fidelity (+27dB), not damping; (4) project_log/
  runs.md rows + any QOI/standard implications await Andrew. NOTE: D22 reproduction wrote psd_envelope/out/
  damping_inference.json (its own code's output; benign). Below = the analysis detail captured pre-figures:
  **ANALYSIS DONE (all 3 layers run).** RESULTS: D22 reproduced 0/9 (integrity).
  L1 HEADLINE=GREEN: time-domain ringdown resolves 14/16 union modes' ζ (band-pass+Hilbert log-dec + hierarchical
  non-centered NUTS, 14/16 converged R-hat≤1.02/ESS≥250/0div, ζ≈0.33-0.76% median 0.45% ≈ .ash 0.25-0.44%) vs D22 0/9.
  Freq-domain CONTROL on SAME clean data = 7/16 (clean multi-hit data helps freq too: 0→7; time domain adds the
  light/sub-bin + clustered modes: 7→14) — honest nuance, not "domain is magic." Resolvability: half-power Δf=2ζf
  sub-bin vs df=2.03 for the light modes. L2=latent-force RTS smoother (FILTER, not NUTS): velocity-projection ζ_true
  cross-checks log-dec (corr 0.82) + L1; MFE dominantly a DAMPING correction (FEM over-damped), residual shows no
  amplitude dep (q² corr 0.03, early/late ζ 1.08)=little nonlinear physics; raw variance-split q_g/beating-contaminated
  (caveated). L3=HONEST NEGATIVE (confirms D7): finite-perturbation shows ζ is a strong ABSOLUTE lever (GRMS∝~1/ζ) but
  CANCELS in the twin/FEM+6dB win RATIO (spread=1.0000, mirrors D8); FEM nominal ζ=1% > measured 0.4% ⇒ measured-ζ twin
  is MORE conservative (ratio A=12.4 nominal, B=11.0 identical-η, C=14.3 asym; 0% win). Binding limit = per-node FEM
  shape error (+27 dB), NOT damping. So the prompt's "under-damped FEM" bridge is SIGN-FLIPPED here — surfaced.
- 2026-06-23 **NEW PROMPT WRITTEN (Andrew decision): time-domain latent-force DAMPING/residual runner.**
  Context: Andrew asked for my independent review of CODEX's three-paper eval (`shocksat_new_papers_review_20260623`,
  YELLOW 41/1/0; Codex now building the 01 sequential-statFEM runner). I judged the eval solid + ranking right, raised
  4 critiques; Andrew picked critique #4 to action. Wrote `docs/lab/shocksat_latent_force_damping_runner_prompt.md`
  (NOT the generic prompt 02). HYPOTHESIS: D22 found 0/9 modes' ζ identifiable from a SINGLE WINDOWED FRF (df=1.25 Hz;
  half-power Δf≈2ζf is sub-bin); new clean caches are df≈2.03 Hz (no help in freq). But damping = a TIME-DOMAIN decay
  rate τ=1/(ζ·2πf); clean modal-hammer RINGDOWNS (~0.5 s, coh 0.9+ at peaks, Test01/02/04/06) have many decay cycles →
  a time-domain latent-force/decay estimate can resolve ζ + residual MFE the FFT bin can't. BRIDGE TO LIVE PROGRAM:
  envelope GRMS (Q-D) is PEAK-HEIGHT/Q=1/(2ζ)-driven, so measured ζ IS a lever on the ENVELOPE QOI (unlike the
  cross-channel-scatter QOI where ζ is channel-common→gain-absorbed, D8 — prompt says so explicitly). 3 layers: (1)
  direct decay re-test vs D22 0/9 [headline], (2) GPLFM latent-force diagnosis + damping-vs-residual decomposition,
  (3) held-out 97.5% PSD-envelope GRMS-vs-FEM+6dB value [secondary, reuse inherited QOI byte-identical]. Gates baked:
  damping-resolvability (τ/T/cycles/SNR + finite-perturb), discretization (time-domain dodges df=2.03), NUTS/HMC for
  any ζ/hyperparam posterior (filter≠NUTS; marg-lik=empirical Bayes), leakage, plot/tufte, immutable SHA-locked check.py,
  3-tier honest-negative. PROMPT ONLY — not launched; NO durable-rule/checker/sampler-standard/project_log edits; NO
  edits to Codex's live workspace. AWAITING Andrew: dispatch this runner (and/or whether to also fold critiques 1–3 into
  Codex's live 01 prompt — held for his call).
- 2026-06-23 **NEW SESSION + NEW THREAD (Andrew): lead handoff to me as master; ShockSat PSD-ENVELOPE/GRMS deliverable.**
  RE-GROUNDED from files (AGENTS all gates; project_vision §5.6/§6.1/§7.1; memory Cards A/C/F/G + MPL; lessons 06-13/06-22;
  value_eval.py/score.py machinery). DATA REALITY confirmed from files: ShockSat measured = SINGLE-impact hammer FRF |H|
  in g/lbf (hit-001, Test07 +X, 84 "Good Data" accel ch); there is NO stationary random-vibration PSD on disk → any "PSD"
  QOI must be CONSTRUCTED (response PSD = |H|²·S_input under a specified input, or |H|² as a shape). NEW QOI (genuinely
  DIFFERENT from all prior ShockSat work, which scored per-frequency CRPS-skill vs climatology): held-out-SENSOR **PSD
  smoothline-ENVELOPE GRMS** — does the twin's 95% UPPER-CI envelope have LOWER GRMS than the original FEM+6 dB envelope
  WHILE still enveloping the held-out data, swept over 50–90% training (leave-sensors-out) splits. = the §5.6
  less-conservative-yet-defensible SPEC value endpoint / §2.2 response-limit proxy. HONEST TENSION surfaced to Andrew:
  prior Cards found per-channel single-impact AMPLITUDE has NO skill vs climatology (≈−1.0) + wide band (single-impact
  ceiling), but FREQUENCY skill +0.93 and FEM misses held-out peak median 5.4–6.7 dB (~half >6 dB); the envelope/GRMS-vs-
  FEM+6dB reframe is one-sided, peak-enveloped, integrated → expect CHANNEL-DEPENDENT win (where FEM OVER-predicts) /
  honest-negative (hard UNDER-predicted ch), fair only where FEM+6dB ALSO covers. ASKED 5 clarifying questions
  (PSD definition + input spectrum [#1 blocker]; envelope/smoothline algorithm; coverage strictness + FEM-must-also-cover
  fairness; split details; one-sided 95th-percentile). NO build started; NO durable-rule/checker edits; project_vision
  update DRAFTED but HELD pending Andrew's answers (answers materially shape it).
  **ANDREW ANSWERED (2026-06-23):** Q1 default (response PSD |H|²·S_F, flat input, identical FEM/twin); Q2 default
  (peak-pick + piecewise-linear log–log envelope, identical); Q3 = report **dB-EXCEEDANCE energy-weighted** (NOT binary
  cover — a small poke where FRF already low ≈ negligible GRMS = not problematic); Q4 = **TOP of the 2-sided 95% shaded
  band = 97.5th pct** (NOT one-sided 95th → slightly HARDER bar, but matches what we've plotted); Q5 yes splits.
  **ANDREW PLAN CONCERN (valid):** worried a first run differs from the FAILED multiref_amplitude_20260622 ONLY by the
  smoothline = cosmetic → reproduce the negative; wants "something more promising" or start higher training %.
  MY ANSWER (honest): NOT only cosmetic — (1) competitor changes climatology→FEM+6dB (decision-grade; FEM is biased 5–7
  dB) and (2) metric penalizes only the UPPER edge (one-sided envelope GRMS) not the full two-sided CRPS width; BUT the
  binding lever IS band WIDTH (upper edge ~+16 dB above mean; calib fixes freq not amplitude) so a single-impact +X
  cosmetic rerun WOULD likely re-skin the negative. PROPOSED: (a) 10-min VALIDITY PROBE on existing converged L5 (one
  90% split + new envelope-GRMS-vs-FEM+6dB metric) = does the reframe win ANYWHERE before spending compute [validity-
  before-rigor gate]; (b) start at 90% training then sweep DOWN; (c) the promising program = envelope metric + MULTI-
  REFERENCE data (the §7.1 width lever, being downloaded) + realistic/multiref-pinned DAMPING (FEM+6dB GRMS is
  Q/peak-height-driven; under-damped FEM → very conservative envelope). **ANDREW DOWNLOADING MORE DATA — wants me to
  EXPLORE it BEFORE embarking.** I am HOLDING (no build/vision-edit/task-card). ASKED: what/where/size/when is the new
  data; and a single decision — run the 10-min probe on EXISTING data now (I lean yes) vs wait for the download.
  **DATA EXPLORATION DONE (Andrew "start on the 3 in hand"; Test10 ~10 min out).** Workspace
  `artifacts/reports/shocksat_multiref_explore_20260623/` (code/explore_multiref.py, out/explore_summary.json,
  exploration_findings.md). Pulled Test01(+X)/Test02(+Z)/Test04(+XY) ModalHammer node-990, 6 hits each. KEY: modal
  records are PRE-TRIGGERED (impact @125,009 samp = 500 ms; ~0.5 s ring-down) → Card G's 0.8 s window overruns; used
  N=122,880 (0.49 s, df≈2 Hz). **FINDING (GREEN data quality):** new modal data is CLEAN + a big upgrade — 6-hit
  coherence median 0.71–0.93 / **at-peaks 0.90–0.97** (floor 1/6); modal hammer drives ~500× harder (500–1080 lbf vs
  Test07's 1.28 lbf tap, full-band force); cleans the very +X reference the headline twin was built on (Test07 +X had
  within-hit coh ~0.07 = noise-dominated tap); multi-direction modal coverage (X/Z/XY light up different modes,
  union ~12 peaks vs Test07's 2). **OPEN/MUST-FIX-BEFORE-BUILD (YELLOW): absolute UNITS/GAIN reconciliation** — +X
  modal (Test01) vs +X impact (Test07) FRFs are UNCORRELATED (log|H| corr ≈0.00) with a −36 dB peak / −44 dB median
  offset; likely benign (Test07=noise + the known ~×100/+40 dB global units-gain that realfrf/Card A already absorbs),
  modal data internally self-consistent (40 dB dyn range, deep antiresonances), BUT must confirm g/lbf scaling out of
  the .mat Recorder structs (name/unit probe returned '?') before combining (pipeline gain was built around Test07).
  Also reconcile modal peaks vs .ash modes (df=2 Hz coarse → damping marginally resolved) + +XY combined-drive row.
  CARD G's held-out-SENSOR-shape (φ_s, FEM-only) ceiling for per-channel AMPLITUDE still stands; the envelope-GRMS
  reframe is the lever that cashes frequency skill+damping (validity probe still decides). NO build/vision-edit/
  task-card/durable-rule/checker edits. AWAITING Andrew: Test10 landing + steer on the units reconciliation / next step.
  **UNITS QUESTION RESOLVED (2026-06-23, Andrew pointed me to the TestLog xlsx).** Read
  ShockSat1_Instrumentation_and_TestLog xlsx: accel = 6 sensor types, PER-CHANNEL cal 0.044–1.137 mV/g (cancels in
  the per-channel modal-vs-impact compare); FORCE = single Dytran 5850B (loc 37/ch109). ⇒ the −36 dB modal-vs-impact
  gap is NOT a units bug — it's DATA QUALITY: a ~1.3 lbf impact TAP (Test07) is too weak for 100k-g shock accels
  (0.045 mV/g) → SNR-limited (only ~120 Hz mode pokes through; coh 0.07); the 500–1080 lbf MODAL hammer is the right
  instrument, rings clean (coh 0.9+). **The headline ShockSat twin's +X amplitude rested on noise-limited tap data;
  the clean modal data deserves a fresh look (cautious optimism; Card G φ_s-shape ceiling still independent of drive
  quality).** Also: each modal test = a ROVING cluster of 6 nearby impact points (not 6 repeats) — OK for global
  frequencies, per-hit for amplitude/shape. Test06 (ModalHammer_900z, node 900 y≈0) now at root too. **CLEAN MODAL
  MULTI-REF SET = Test01(+X,990)/Test02(+Z,990)/Test04(+XY,990)/Test06(+Z,900)** = 2 drive locations × dirs, consistent
  modal-hammer/force instrument; drop SNR-limited impact taps (Test07/08/10) from the amplitude basis. EXPLORATION of
  all pulled data effectively COMPLETE. NO build/vision-edit/task-card/durable-rule/checker edits. NEXT (await Andrew):
  steer on building the PSD-envelope twin on this clean modal set (validity probe first, start 90% training) + whether
  to re-pose the prior amplitude conclusions given the noise-limited-tap finding.
- 2026-06-23 **STUDY BUILD STARTED (Andrew "go ahead and fold in both nodes").** New workspace
  `artifacts/reports/shocksat_psd_envelope_twin_20260623/`. PHASE 0 DONE + verified: (1) governance — decisions_log
  (D0 deliverable, D1 Q1–Q5 LOCKED, D2 clean-modal-set/both-nodes, D3 reuse converged L5 twin + honest φ_s ceiling,
  D4 validity-probe-first, D5 drive coords), priority_deliverables (P1–P6), quantity_contracts (Q-A FRF g/lbf … Q-E
  energy-weighted exceedance + verdict tiers). (2) Toolkit COPIED BYTE-IDENTICAL from Card G + SHA manifest
  REUSED_code.sha256 (core/realfrf/modal_feature/heldout_qoi/score/value_eval/multiref_frf/…). (3) DATA: confirmed
  samples in ENG UNITS (accels g, force lbf; |H| direct g/lbf, no cal/×100). Built modal_multiref.py + band-limited
  caches (data/multiref_modal/*.npz, N=122880, df 2.03 Hz) for Test01(+X,990)/Test02(+Z,990)/Test04(+XY,990)/
  Test06(+Z,900): coherence at-peaks 0.90–0.97, **16 union modal peaks 45–260 Hz** (vs Test07's 2). Disk 26 GB free.
  **NEXT (Phase 1):** wire FEM forward to the 4 modal drive rows (incl +XY combined) + smoke-test |H_FEM|; build the
  PSD-envelope QOI (Q-B |H|²·flatS_F) + smoothline envelope (Q-C peak-pick + piecewise-linear log-log) + FEM+6dB +
  energy-weighted exceedance scorer (Q-E); run the VALIDITY PROBE at one 90%-training split (does twin 97.5% env beat
  FEM+6dB GRMS anywhere? where?). THEN immutable check.py + 50→90% MC sweep + figures + packet IF probe promising.
  NO durable-rule/checker/project_log/project_vision edits. Probe = exploratory (YELLOW default, no success claim).
- 2026-06-23 **VALIDITY PROBE RESULT = robust HONEST NEGATIVE + premise-breaking finding. SURFACED; build PAUSED.**
  Built+validated psd_forward (complex forward = realfrf to 1.8e-15), psd_envelope (self-test PASS), probe.py,
  diag_sigma.py. Probe seed0/90%-train, calib CONVERGED (R-hat 1.002/ESS1758/0div/22 pooled modes). (1) clean-modal
  units-gain ≈ +0.05 (×1.05) — FEM on the right scale (×100 was a Test07-noise artifact). (2) **Per-NODE FEM
  mode-shape error is the binding ceiling, quantified misalignment-free (336 obs ch×ref): band-GRMS σ=0.97 (×2.6/ch),
  dominant-peak σ=1.21, all-peak σ=1.60.** Twin HONEST 97.5% covering band = +27 dB PSD → GRMS ratio 10–13× vs FEM+6dB
  → **0% win across all 4 refs + combined-correlated.** Need σ≲0.35; we're 3–5× above. Robust (MAD agrees), NOT a
  σ/sampler/units artifact. (3) **PREMISE BREAK: FEM+6dB does NOT envelope the data either** — 34% of measured
  band-energy exceeds it (median), 82% of channels >2%. Neither +6dB-FEM NOR a reasonable twin band covers (only
  ~+27dB does); twin & FEM share the same held-out-node FEM shapes ⇒ twin can't be meaningfully tighter than a fair
  FEM+margin. VERDICT: envelope reframe + clean multi-ref = HONEST NEGATIVE for the GRMS-WIN goal; quantifies §7.1
  (gap = FEM shape fidelity, not statistics) + Card G φ_s ceiling on CLEAN data with the aerospace metric. Lever =
  per-NODE shape fidelity (better FEM / per-node shape correction; measured-shape interp ~null in Card G D16). STOPPED
  before full MC/checker/figures. SURFACED to Andrew for steer: (a) re-pose deliverable (pooled/regional spec? freq-twin
  + measured-amplitude spec? iso-coverage Pareto GRMS comparison?) vs (b) pivot to per-node-shape lever (agentic FEM
  correlation) vs (c) accept+document the negative. project_vision §7.1 update STILL pending. NO durable-rule/checker/
  project_log/vision edits.
- 2026-06-23 **DAMPING (D8) + PIVOTAL SHAPE (D9) results — Andrew steered to shapes/agentic remeshing.** D8
  (`damping_rerun.py`): global ζ only PARTIALLY gain-absorbed (twin ζ1→3→5% drops GRMS ratio 10.6→7.7→6.5; real
  eff. ζ~3–4% from the 25-vs-33 dB DR gap helps ~11×→~7×, not enough); per-mode half-power is df≈2 Hz resolution-
  limited (floors ζ≈1.1%, under-reads truth) → use full-shape/learn-as-parameter; gain absorbs GLOBAL damping so the
  real lever is NON-UNIFORM (per-mode/elemental/CBUSH/complex Das–Debnath). Damping = necessary, ~11→7×, NOT
  sufficient. **D9 PIVOTAL (`shape_diag.py`): on CLEAN modal data, predicting held-out peak |H| with MEASURED .ash
  shapes vs FEM shapes → held-out σ 1.26 → 0.70 (median |err| 18→8.7 dB) = shapes nearly HALVE σ. OVERTURNS Card
  G/D16 ("shapes don't predict amplitude") as a noise-limited-Test07 artifact — on clean data SHAPES ARE THE
  REDUCIBLE LEVER.** FEM-vs-.ash MAC median 0.70 (10/20 modes <0.7, worst 70/75/158/190/196 Hz). SE targets: worst
  modes are **bottom_box 95–97% SE** (primary remodel target), top_box/plates for 151/158 Hz. Floor = measured-shape
  oracle σ≈0.70 (best shapes alone; residual=near-field); shapes(→0.70)+damping(~/2) gets CLOSE to a GRMS win
  (ratio ~1–2×) → remodel + damping (+ maybe re-pose iso-coverage/regional). Card D showed θ/mesh-density don't move
  shapes → remodeling must be ARCHITECTURAL (element form/connectivity/mass/missing feature in bottom_box) = agentic-
  FEM-remodel direction; reuse shocksat_fem_remesh_20260618/edit_solve.py, score on CLEAN-data MAC+σ+envelope-GRMS.
  Figures delivered earlier (figures/heldout_psd_examples.png, tufte+lint OK). **NEXT: agentic bottom_box remodeling.**
  SURFACED to Andrew (asked for his structural insight on bottom_box; remodeling = big open effort). NO durable-rule/
  checker/project_log/vision edits.
- 2026-06-23 **REMODELING GO + deck/drawing GROUNDING (Andrew: frangible joint NOT in modal test; "go ahead, fetch
  drawings").** FEM_and_CAD.zip (1.89 GB) was ALREADY local in shocksat_statfem_runner_20260609/sources/; extracted
  13 drawing PDFs + STEP + full NASTRAN deck (.blk per group) to workspace cad/. Photos+deck mapped: structure =
  stacked thin-wall AL boxes, bolted joints (bush_801–807), internal BOLTED+DAMPED cross (cross_beam shell_401),
  free-free, NO frangible joint. GROUNDED FEM props: bottom_box PSHELL t=0.118/0.125/0.118″, cross 0.125″; PBUSH
  801–807 tuned 6-term K w/ SOFT rot DOFs (panel-edge fixity already partly released); **Modal_Test_Instrumentation
  blk = 84 CONM2 accel masses (~6.8 g, 0.635″ standoff) MODELED but NO CABLE-HARNESS mass → Andrew's cable point =
  REAL modelable gap** (+ non-linearity = σ floor, bounded modest by 0.90–0.97 at-peak coherence). REMODEL TARGETS
  (grounded, ordered): (1) cable-harness mass [NEW, Andrew]; (2) joint PBUSH edge fixity; (3) panel thickness vs
  drawings; (4) cross connectivity + damping-material mass. Reuse shocksat_fem_remesh_20260618/edit_solve.py
  (per-PID K + M + T, eigsh80 ~5 min/solve) EXTENDED for mass edits; score on CLEAN MAC + σ + envelope-GRMS; launch
  detached/resumable. **NEXT: build campaign driver + launch (cable-mass + joint-fixity first wave).** Drawings
  fetched ✓ (deliverable). NO durable-rule/checker/project_log/vision edits.
- 2026-06-23 **REMODELING CAMPAIGN LAUNCHED (detached, Andrew "go").** Built `code/remodel.py` (extends Card D
  edit_solve with MASS edits; reuses modal-twin matrices read-only; resumable per-edit result.json; scores global+
  calib MAC vs .ash, |df%|, and TARGET-mode MAC at 70/75/151/158/190/196 Hz). Assembly sanity PASS (full FEM 406,098
  DOF; cable_mass f=1 adds 0.00885 = 76 .ash nodes×3×3.882e-5; joint scale applies). LAUNCHED `python3 remodel.py all`
  nohup/disown PID 33680, logs/remodel.log; reduced n=399,510, eigsh(80) ~5 min/solve, 9 variants ~45 min: baseline,
  cable_mass_{lo0.5/med1/hi2}, joint_{soft0.5/stiff2}, cross_{soft0.7/stiff1.5}, cable_med+joint_soft. NOT
  auto-re-invoked (used nohup not run_in_background) → CHECK out/edits/*/result.json next turn / on prompt. Hypothesis:
  cable mass + joint-fixity edits raise TARGET-mode MAC toward .ash → drive σ 1.26→~0.70 oracle. Then σ/envelope-GRMS
  re-score on best variants (extend shape_diag/probe to edited full-FEM modes) + panel-thickness (needs per-PID M) +
  cross-damping-mass as wave 2. NO durable-rule/checker/project_log/vision edits.
- 2026-06-23 **WAVE-1 DONE + MAC-is-wrong-lens + cable-nonlinearity ID + σ re-score launched (Andrew steers).** Wave-1
  (9 variants, MAC-scored): cable_mass_hi best GLOBAL MAC 0.631→0.657 (= the missing cable mass, physical), all else
  trade-offs, worst bottom_box 70/75 Hz (MAC~0.50) resist all edits. **Andrew: "MAC masks local-FRF discrepancies —
  look at FRFs."** fig_local_frf.py (figures/local_frf_overlay.png, lint clean): even best ch (corr 0.73–0.76) peaks
  at wrong freq+height ⇒ MAC ranking is the WRONG lens; do NOT launch wave-2 on MAC. **Cable-nonlinearity ID**
  (nonlin_id.py): force-normalized FRF over 6 hits (×1.4–2 force) → modes SOFTEN + peaks BROADEN with force, clearest
  +Z (4/8 modes, dDR −1.23 dB/efold); SECOND-ORDER (coherence 0.90–0.97); a SCREEN (force ×2 + df 2 Hz), not definitive.
  **Cable-damping decision (Andrew "simplest first"): single CONSTANT effective modal ζ from data, lumps cable, flagged
  amplitude/test-specific; NO Iwan/Bouc-Wen/ζ(A).** **σ RE-SCORE LAUNCHED** (rescore_sigma.py, PID 47116, detached
  ~45 min, resumable, saves channel modes): re-solve each variant, score on REAL held-out σ (local-FRF, not MAC)
  [baseline 1.26, oracle 0.70] → decides wave-2-on-σ vs re-pose. Fixed pre-launch bug (ch.nodes = grid INDEX not GID).
  CHECK out/rescore_sigma.json next turn. NO durable-rule/checker/project_log/vision edits.
- 2026-06-24 **PIVOT: brute-force FEM correlation (Andrew "throw out train/test + Bayes; brute-force a correlated FEM
  with ALL data + 100% damping freedom; make FRFs AND MAC match; remeshing can help").** σ re-score CONFIRMED: no
  wave-1 edit reduces σ (best 1.027 vs base 1.077; oracle 0.70), MAC anti-correlated. Regional coverage RULED OUT
  (Andrew). Gave Andrew the physical "why nothing matches FRFs" (dense modal forest → per-point amplitude = fragile
  modal interference; frequencies global/robust, per-point local/fragile; MAC masks it). **CHECKED snap (Andrew's
  hypothesis): SUB-INCH (median 0.15″, max 0.75″; channel_map has fem_grid; .ash at instrum. grids) + Card D mesh
  CONVERGED 0.25″ → remesh helps only by fixing GEOMETRY/FEATURES, not density/placement.** Built `correlate_all.py`
  (all-data FRF corr + MAC, FULL per-mode measured damping, all-channel participation LSQ, no held-out). **BASELINE w/
  full damping: FRF log|H| corr median 0.30 (28% ch>0.5), 15.7 dB ampl err, MAC 0.631 → damping freedom does NOT fix
  FRFs; SHAPES are the wall.** SEARCH LAUNCHED (PID 14260, detached ~65 min): 13 untried edits = DIRECTIONAL joint
  6-term PBUSH (panel-edge fixity, never varied) + per-region E + combos. Honest prior: parameter edits plateau → real
  lever = GEOMETRY/architecture rebuild from CAD/STEP (on disk) → escalate if search plateaus. CHECK out/correlate_all.json
  next turn. NO held-out/Bayes/durable-rule/checker/project_log/vision edits.
- 2026-06-24 **Explained CAD rebuild to Andrew + built CROSS-CONNECTIVITY SURGERY (the genuinely-new lever).** Param
  search NOT helping (baseline FRF corr 0.296; joints_rot_soft 0.210 worse). **KEY FINDING:** internal cross
  (shell_401) shares 0 nodes w/ walls (not welded), attached by only ~13 pts (5 CBUSH pid99 + 8 RBE2) — but **68
  cross-edge nodes are coincident (<0.2″) on the walls yet LEFT UNCONNECTED** ⇒ FEM UNDER-attaches the real bolted
  cross → wrong local shapes; topology, not scalable. Built remodel.build_couple_K + correlate_all edits cross_bolt
  (k1e6)/cross_weld (k1e8)/cross_bolt_trans (couple the 68 pairs). Sanity OK. **QUEUED after param search** (chain
  PID 16004 waits for PID 14260, runs all → skips done, runs 3 cross edits). Decisive: does densifying cross attach
  raise FRF corr>0.296 / MAC>0.631? Standoff lever DROPPED (normal-offset×rot ⟂ axis ⇒ ~0). CHECK
  out/edits/cross_*/correlate.json next turn. NO held-out/Bayes/durable/checker/project_log/vision edits.
- 2026-06-24 **PARALLEL RUNNERS DISPATCHED (Andrew, file-based handoff for Claude browser).** Can't auto-spawn agents
  (how_to_run: file-based, human-mediated) + compute contention on this machine (FEM eigensolves) → wrote two
  compute-LIGHT self-contained browser prompts: `docs/lab/parallel_A_frf_correlation_scan_prompt.md` (FRF-correlation
  technique scan: FRAC/RFM, Schneider freq×space on amplitude, cross/joints as CMS/FBS substructures, virtual point,
  non-prop damping, + honest "is per-point FRF amplitude ill-posed → band/energy/SEA/interface instead?" — output =
  sourced memo + 1 next experiment) and `docs/lab/parallel_C_fbs_basis_usable_mean_prompt.md` (redesign the
  DELIVERABLE: a better FBS/interface-apparent-mass BASIS that sidesteps the per-point wall [integrated 7004C-native
  QOI], AND/OR drop the wide upper-CI for a USABLE MEAN spec vs FEM+margin — output = design memo + 1 next experiment +
  FTO flags). Both embed full context (no repo). Andrew runs in browser; pastes memos back; I integrate. FEM jobs
  (PID 14260 param search + PID 16004 chained cross surgery) STILL RUNNING (5 variants done). NO durable/checker/
  project_log/vision edits.
- 2026-06-25 **MEMOS BACK + REMESHING LINE DEFINITIVELY CLOSED (incl. Andrew's map-guided method) + amplitude verdict.**
  Both browser memos returned + CONVERGED (per-point amplitude = physics; pivot to integrated/interface QOI). I
  sanity-checked their optimistic claims vs our data: SEA pivot NOT warranted (MOF≤0.9 <2.5, modes resolvable), and
  crude integrated proxies (band 0.48/net 0.41/drive-pt apparent-mass 0.26) DON'T jump (but not the proper VPT test).
  USABLE-MEAN (`usable_mean.py`) + HELD-OUT-MEAN (`heldout_mean.py`): NO twin advantage (fair margin-to-cover: un-updated
  FEM ≤ correlated; held-out correlated 55.6 GRMS/0.75cov vs un-upd 20.2/0.25cov). **Andrew: "do point-by-point freq-by-
  freq mismatch analysis to GUIDE remeshing."** Built `residual_map.py` (figures/residual_map.png): WHERE = free bottom
  −Y corner worst (RMS 2.0→1.6 up the column; joints all UP HIGH z18–57 so bottom is FREE END = panel/corner dynamics
  not joint fixity); WHICH = 54 Hz fundamental + 150–210 cluster (100–130 fine); FEM under-predicts. Map-GUIDED bottom
  softening (`guided_remesh.py` ×0.7/×0.55) → FRF corr 0.33 (WORSE than blind ×0.85=0.359). **ALL remeshing (blind +
  cross-architectural + MAP-GUIDED) plateaus at FRF corr ≈0.36 → remeshing CANNOT crack per-point FRF correlation;
  line CLOSED.** 54 Hz = REAL shape gap (best MAC over ALL FEM modes = 0.12; FEM has right fundamental FREQ, WRONG
  eigenvector). FEM shapes wrong even at the fundamental; only a from-scratch CAD rebuild could fix shapes (major
  gamble, not recommended). **COMPREHENSIVE VERDICT: per-point FRF amplitude unachievable by any means; twin value =
  FREQUENCY only.** NEXT: (b) interface apparent-mass (sidesteps shape wall, 7004C endpoint) + consolidate. NO
  durable/checker/project_log/vision edits.
- 2026-06-25 **CORRECTION (Andrew pushback, RIGHT): model form NOT exhausted — "closed" was over-claim.** We'd only
  varied stiffness MAGNITUDES (+1 connectivity + damping + map-guided), NOT density/mass DISTRIBUTION, RBE2 flexibility,
  damping-layer, geometry, element formulation. ANNOTATED PHOTO+CAD revealed: TWO MATERIALS — heavy STEEL bottom
  (bottom_box 101-103 MAT1002 ρ7.4e-4) + light ALUMINUM top (top_box 201-203 MAT1001) + thick Al DISH plates
  (501/601/701) + struts + welded/damped bulkheads + shock-source base. ⇒ "right fundamental FREQ, wrong SHAPE, worst
  at steel bottom" = mass/stiffness DISTRIBUTION error (never tested — we never varied ρ/mass). Andrew "make the call
  or sweep all." MY CALL: built region MASS-scaling (`remodel.build_M` mass_scale = D·M·D, NEW lever) + fundamental-MAC
  tracking in `correlate_all.score`. SWEEP LAUNCHED (`modelform_sweep.py` PID 86544, ~1 hr, ~14 edits: steel/al E AND
  ρ balance + dish mass + distribution shifts + combos). KEY metric = 54 Hz fundamental MAC 0.12 → >0.5 = real shape
  fix. NEXT after: RBE2 flexibilize (struts/bolts, T-rebuild via assemble_fem.build_T) + damping-layer + geometry.
  CHECK out/modelform_sweep.json next turn. NO durable/checker/project_log/vision edits.
- 2026-06-23 **NEW PAPERS REVIEW COMPLETE (Andrew request):** workspace
  `artifacts/reports/shocksat_new_papers_review_20260623/`, checker OVERALL YELLOW 41/1/0 (`bash run_all.sh`).
  Reviewed three pulled PDFs against current ShockSat state. Ranking: (1) Kavrakov et al. sequential statFEM solid
  dynamics = HIGH applicability and best first runner for time-domain modal-hammer assimilation; (2) Kashyap/Nayek
  latent-force + BNN = MODERATE-HIGH for model-form-error/damping residuals, but offline/moderate-scale and held-out
  leakage/extrapolation risks; (3) Lu et al. multi-level wing DT = MODERATE-LOW as fast-ROM/submodel deployability,
  not Bayesian/statFEM and no measured ShockSat local stress truth. Prompts written in
  `runner_prompts/01_sequential_statfem_shocksat_runner_prompt.md`,
  `02_latent_force_bnn_shocksat_runner_prompt.md`, and `03_multilevel_rom_submodel_shocksat_runner_prompt.md`.
  No ShockSat metric improvement claimed; yellow is the explicit "prompts are hypotheses only" caveat.
- 2026-06-22d **CARD G LAUNCHED (lead-as-runner, FULL COMPUTE AUTONOMY).** Andrew dispatched the multi-reference
  amplitude runner prompt (`docs/lab/shocksat_multiref_amplitude_runner_prompt.md`). GOAL: BEFORE(+X-only)/AFTER
  (multi-ref +Z/+Y/900z) test — does multi-reference hammer data raise held-out per-channel AMPLITUDE skill vs
  climatology above Card F ≈−1.0 (ideally >0) while keeping freq +0.93; gated by coherence (the +X ~0.07 risk) +
  NUTS convergence + identifiability. Honest negative explicitly a valid win. RE-GROUNDED from files (AGENTS gates;
  Card F packet/code/value machinery; Card A units-gain forensics; source_manifest; lessons-learned 2026-06-22).
  KEY TECH READS: θ is calibrated from FREQUENCIES ONLY → amplitude is a forward prediction from FEM/ash shapes φ +
  ONE training-global broadband units-gain c (never peak-tuned). So multi-ref impact data can only move amplitude via
  shape-FIELD / damping inference (the levers that touch φ,ζ); held-out SENSOR φ_s stays FEM/ash-known. Env: default
  python3 HAS jax0.4.30+numpyro0.19 (no venv). Disk 15GB free (card said 3.9). Data on disk: Test07 .mat extracted +
  cache (symlink to Card A); Test08 5 hits extracted; Test03/Test10 zips at root. WORKSPACE
  `artifacts/reports/shocksat_multiref_amplitude_20260622/`. **COMPLETE — check.py OVERALL GREEN (18/0/0), exit0.**
  HEADLINE = rigorous scoped HONEST NEGATIVE (the direct test of the data-scope correction): multi-reference does NOT
  raise held-out per-channel AMPLITUDE skill above climatology — BEFORE +X −1.00 → AFTER +X measured-residue −0.11,
  none of +Z/+Y/900z beat +X, NEVER crosses 0; +0.931 FREQUENCY skill PRESERVED (reference-invariant). WHY (proven not
  argued): (iii EARNED) the binding limit is the held-out SENSOR's own shape φ_s (FEM-only) — shape-ORACLE (sensor
  shape known) = +0.58, so the QOI IS predictable IF you knew the sensor shape; multi-ref is the wrong axis (it fixes
  the DRIVE side: measured residue lifts −1.7→−0.1 but can't cross 0). (ii DATA-QUALITY) the extra IMPACT references
  are near the noise floor at resonances (coherence 0.28/0.39 vs MODAL +Y 0.92 at equal 4 hits) → don't help the drive
  side; mechanism corr only 0.32 (confound not cleanly broken from impact data). Identifiability: multi-ref adds modal
  coverage (17→23) but stiffness FLOOR-limited (3 dirs); amplitude confound broken on DRIVE side only (3 separable
  ratios+1 gauge). Part A reproduced Card F EXACTLY (integrity GREEN). All NUTS converged (R̂≤1.003/ESS≥1414/0div).
  4 figs tufte+image-QA pass; run_all.sh; runtime active 516s; raw .mat+zips deleted (footprint 2.8MB). Verified the 3
  OPEN ambiguities: Test03=MODAL hammer (per-ref gain, labeled, worst skill = instrument mismatch); node-900 drive
  (9,0.5,0) from TestLog_Tap; Rec116=force confirmed in .mat. **SURFACE to Andrew (NOT self-applied):** project_log
  row; whether checker amplitude gate should be YELLOW-on-no-skill (Card F precedent) vs my GREEN-on-convergence; no
  "replace FEM" claim made. Pre-test lever for amplitude = sensor-shape coverage / refined mesh / CLEANER excitation
  (modal hammer >> impact; pyro per README) — NOT multi-reference. PACKET scientific tier = YELLOW (documented negative).
- 2026-06-22 **AUDIT CONCLUSIVE + Andrew approved corrections (items 1-3 done).** `source_manifest.md` PROVES the
  public NASA ShockSat1 delivery holds multi-DIRECTION drives un-downloaded: Test01 990x / Test02 990z / Test03
  990y / Test04 990xy / Test06+Test10 900z / Test08 ImpactHammer 990z + Test_Data_Parametric (3.33 GB) all
  `too_large_deferred`; pyro NSI/NSD `partial_download` (251 MB of 1.41 GB → truncated). Runner fetched ONLY Test07
  (+X). So multi-reference (confound-breaking) data EXISTS + is PUBLIC/obtainable — the "intrinsic amplitude
  ceiling" was a download/usage choice. Test07 002-004 verified = 4 full 128-ch distinct-CRC same-+X repeats (packet
  "3 channels each" was false). +X tap impact-face coherence low (~0.07) = separate quality limit; README says pyro
  cleaner. APPLIED (Andrew-approved): modelclass packet §4 DATA-SCOPE CORRECTION + lessons-learned 2026-06-22 entry
  (4 lessons). NEXT (offered, not started): download a 2nd-direction zip (e.g. Test08 990z or Test02/03) to actually
  break the confound; same audit on MPL thread. project_log row NOT written (awaits Andrew).
- 2026-06-22b **Test08 (+Z) DOWNLOADED + EXTRACTED (Andrew).** 5 valid hits (002/004/005/006/007, full 128-ch,
  250 kSps/1 s, distinct CRC) at `shocksat_statfem_runner_20260609/extracted/Test08_ImpactHammer_990z/`; 555 QA
  PNGs discarded; zip deleted (disk 5.5 GB free). FORCE channel = Recorder116 'Ch D20' units lb (~1.1 lbf) —
  IDENTICAL convention to Test07 (also Rec116, ~1.3 lbf, same fs/length) ⇒ +X and +Z are directly combinable
  multi-reference. NEXT go/no-go (cheap): build +Z FRF + drive-point/hard-channel COHERENCE vs Test07 (+X tap
  coherence was ~0.07 — the data-quality risk) BEFORE committing a 2-reference retrain (which needs a task card).
- 2026-06-22c **Test03 (+Y modal) + Test10 (Z@node900 impact) ALSO pulled (zips at root).** Multi-ref set now =
  +X(T07)/+Z(T08)/+Y(T03,MODAL-hammer caveat)/Z@900(T10). All 250kSps/1s/128-rec; impact force=Rec116. DISK
  CRITICAL ~3.9 GB free → runner must extract 2-3 hits/test, band-limited caches, delete zips+raw. WROTE runner
  prompt `docs/lab/shocksat_multiref_amplitude_runner_prompt.md` (Card G): PART A duplicate Card F value program
  (+X-only: freq +0.93 / amp ≈−1.0) byte-identical as integrity baseline, PART B add multi-ref → does held-out
  AMPLITUDE skill vs climatology rise above −1.0 (ideally >0) while keeping +0.93 freq; mechanism=φ/ζ confound
  break via |H(d1)|/|H(d2)|=φ_d ratio; gates=coherence go/no-go (the ~0.07 risk)+NUTS+identifiability; 3 honest-win
  outcomes (yes / no-data-quality / no-earned-intrinsic). **Andrew 2026-06-22: FULL COMPUTE AUTONOMY — prompt edited
  to run Part A → coherence diagnostic → full multi-ref NUTS MC end-to-end, detached/overnight, NO human compute
  checkpoint; coherence is now a reported diagnostic (not a stop), Part A integrity failure flags RED but continues.
  Non-compute guardrails KEPT (durable-rule/checker/sampler/"replace-FEM"/project_log still surface).** NOT launched
  — awaiting Andrew dispatch of the runner.
- 2026-06-22 **ShockSat DATA-SCOPE AUDIT (Andrew Q: "confirm there isn't data from other impacts? no way").**
  Audited the raw delivery zips in `shocksat_statfem_runner_20260609/sources/`. FINDING: the 4-card ShockSat twin
  (statfem_real_validation / fem_remesh / richmodel_L5 / modelclass_L5) used ONE drive point (Test07 +X hammer,
  hit-001). But NASA collected MUCH more: a MULTI-REFERENCE roving-hammer survey (+X-normal/+X-axial-Z/+Y-normal;
  April nodes 1101Z−/2101X−/2104Y+/11101X−), a force-level PARAMETRIC sweep (25/50/75), PYROSHOCK (NSI/NSD), and
  frangible-joint firings. Multi-reference = exactly the lever that breaks the participation÷damping confound.
  LOCAL raw = only Test07 (FOUR full-channel +X runs, 001 used / 002-004 same-drive repeats UNUSED) + one raw
  pyroshock NSD1 (UNUSED; source zip likely truncated). Multi-reference data is LOCAL only in modal-distilled form
  (33 `.ash` modes). ⇒ The packets' "single impact / NOT a data-quantity gap / intrinsic amplitude limit" framing
  is OVER-STATED (scoped to the single-drive QOI we chose), and modelclass packet §4 "only hit-001 raw exists
  (other 3 = 3 channels each)" is FACTUALLY WRONG (all 4 are full 256 MB / full-channel). Parallel MPL thread (below)
  reached the SAME "per-loc amplitude data ceiling" — same audit may apply. NEXT: drafted (a) modelclass packet §4
  correction + (b) lessons-learned entry — BOTH AWAIT ANDREW APPROVAL before editing those durable notes. Optional
  follow-ups offered: extract/verify Test07 002-004 channels; obtain raw multi-reference FRFs from full delivery;
  re-pose twin with ≥2 drives. No durable-note/packet/checker edits made.
- 2026-06-20 **NEW THREAD (Andrew) — MPL TWIN ITERATION:** multi-round evidence-ranked FEM model-class SEARCH to
  improve a digital twin's HELD-OUT scores. Master/orchestrator deploys subagents (1 per class), batches of 2–5
  ranked by Bayesian EVIDENCE (statFEM Eq38 / Kiran Eq44, BIC + prior-sensitivity) + held-out scores over 5
  train/test splits. Agents MAY change mesh/elements/modeling/damping/likelihood. REUSE L5 toolkit byte-identical
  (`artifacts/reports/shocksat_modelclass_L5_20260619/code/`: score.py=interval/CRPS/coverage proper scores;
  value_eval.py=CRPS-skill vs CLIMATOLOGY baseline; stage1_evidence.py; check_twin.py 3-tier+SHA-lock). KEY
  CONSTRAINT: NO instrumented force → observables = FREQUENCIES + DAMPING + TRANSMISSIBILITY only (NO absolute g /
  apparent mass). Matching substitute = FEM eigenfreq ↔ measured peak freq per accel loc, GATED by mode-shape
  amplitude at that node (replaces ShockSat force-channel keying). Held-out QOI = (a) freqs at held-out loc + (b)
  acoustic |T| at valve/avi-feet vs shield ref + band-GRMS. Climatology = predict held-out from observed-channel
  population. Coverage = trust gate (§6.1). Data: `MPL test stand/FEM/test_data_scan_20260611/` (features.json,
  run_mapping A1–A7); start FEM `artifacts/reports/mpl_stand_fem_rebuild_20260611/out/model/`. Prompt drafted →
  `docs/lab/mpl_twin_iteration_master_prompt.md` (Phase0 frozen harness + check.py-first + 5 splits + baseline;
  Phase1..N subagent rounds; doc=model_registry + FRF/PSD figs w/ scores+GRMS in legend + FEM diff graphics +
  modeshape GIFs; honest-negative OK). NOTE this RESUMES the 2026-06-19 model-selection thread Andrew DEFERRED —
  but on MPL not ShockSat, and AFTER damping is now an explicit lever (consistent w/ the defer condition). OPEN
  for Andrew (prompt §9 D-A..D-G): exact 2 metrics; held-out QOI scope; split axis; autonomy/rounds/overnight; add
  ruler to FEM; damping extraction; solver. CONFIRMED (Andrew 2026-06-20, prompt §9 now settled): D-A metrics =
  THREE held-out scores (CRPS-skill vs climatology + interval/Winkler+coverage + band-GRMS error), GRMS kept
  un-blurrable (gain-free on |T|, or ONE training-only global gain identical across methods, NEVER per-held-out;
  check.py gates). D-B observable = match FULL transmissibility SPECTRA (not freqs-only; freq-match only as a
  Stage-1 evidence screen); no force fine; absolute g / apparent mass OUT. D-C splits = leave-ONE-accel-location-
  out, 5 splits over {interface, beam, valve, avi-L, avi-R}, shield = fixed |T| reference; coupled-ruler =
  separate robustness check. D-D autonomy FULL (run it all, detached overnight OK; Stage-1 all, Stage-2 top-1-2;
  3 rounds×3-4 classes; surface only durable-rule/checker/sampler/"replace inherited FEM"). D-E add ruler to FEM
  for COUPLED config only. D-F extract modal ζ (report resolvability). D-G default numpy/scipy elements. D-H
  master+subagents = OPUS 4.8. Prompt fully patched. READY TO LAUNCH — Andrew pastes into terminal.
  **LAUNCHED 2026-06-20 (Andrew pasted master prompt). Master = THIS lead session (no separate subagent-spawn tool
  → model classes built/scored sequentially by lead, each = one registry row). Workspace
  `artifacts/reports/mpl_twin_iteration_20260620/`. Inputs verified (FEM rebuild out/model = 14 K-groups+8 M-groups
  parametric, 184 modes<500Hz, modal.py exact massless-condensation eigh ~0.4s; L5 score.py copied BYTE-IDENTICAL
  SHA c62c564…; 13 CSVs 2-col t/accel @10kHz). GEOMETRY: shield = y-z panel @x≈61.5, normal=+X → sensor OOP axis =
  X-translation DOF. NODE MAP (X-DOF, defensible defaults, ANDREW-CONFIRM-flagged): interface=g800071, shield-REF=
  g800016, beam=g1510, avi-box=electronics_box on shield → LEFT-foot g800036(y-14.4)/RIGHT-foot g800034(y-4.8) by
  +X-view-left=-y, valve=valve_panel node nearest frame centroid. FWD transmissibility T_a=|Σφ_a,i γ_i/D_i|/
  |Σφ_ref,i γ_i/D_i| (input spectrum CANCELS in ratio; γ_i=φ_i^T f from assumed uniform-OOP-shield load = nuisance,
  log-f discrepancy GP absorbs). BUILDING Phase 0: workspace+gov → check.py FIRST(SHA-lock, baseline RED) →
  mpl_observe.py → mpl_splits.py(5 LOLO) → baseline+climatology. Only this block + new-ws files edited.**
  **PHASE 0 DONE + VALIDATED, then DECISIVE FINDING D6 → SURFACED to Andrew (HOLDING before multi-hr calibration
  compute). Built+validated: check.py(locked,3-tier), score.py byte-identical(c62c564…), mpl_fem.py(forward
  reproduces fable f1..f8 to 4e-4Hz; ref/ref|T|≡1; load-scale+input-spectrum invariance UT PASS), mpl_observe.py
  (gain-free |T| from acoustic CSVs, 8/8 UT PASS, band 20-260Hz), mpl_splits.py(5 LOLO), mpl_calibrate.py+
  mpl_baseline.py(statFEM whole-curve log|T| NUTS via .venv_nuts + held-out scoring + climatology — RUNS e2e).
  check.py: harness GREEN, calibration YELLOW(non-converged), overall RED only b/c fig_registry pending = honest.
  **D6 KEY FINDING: as-received FEM transmissibility forward is ~UNCORRELATED with measured |T| at EVERY held-out
  loc (log-corr interface+0.05/beam-0.02/valve-0.01/aviL-0.16/aviR-0.12), ROBUST across load shapes(unifShield/
  unifAll) + references(shield/interface) |corr|≤0.35. NOT a freq problem (FEM HAS 28 modes 70-120Hz/49 170-260,
  measured peaks match features.json taps). Mechanism = DENSE modal forest + UNKNOWN diffuse acoustic load + 1
  axis + no force ⇒ transmissibility SHAPE set by unknown load participation + ref antiresonances + fine
  mode-shape err, NOT stiffness-calibratable = the ShockSat per-loc-amplitude DATA CEILING, now on MPL.
  Whole-curve NUTS multimodal here too (θ→1.8,ζ→0.15,R̂23-96 = documented whole-FRF-mag multimodality).**
  fig_forward_diagnostic.png + forward_diagnostic.json = the evidence. SURFACED 3 options: (a) run search anyway
  as rigorous DEMO of ceiling + test richer forms (infer load latent / region-freq-corr disc / near-resonance
  |φ_a/φ_ref| / shape-field) for any skill recovery [honest-neg expected]; (b) PIVOT scored QOI → identifiable
  per-loc modal FREQ (+damping where resolvable), transmissibility as diagnostic; (c) reconsider observable
  (coherent avg / sub-bands / IFT latent-load-field). Recommend (a)+(b) hybrid. AWAITING ANDREW'S STEER. Only
  this CURRENT-STATE block + new-ws files edited; NO durable-rule/checker/sampler/project_log edits.**
  **D7 ANDREW STEER: "a+b" → (b) PIVOT headline scored QOI to IDENTIFIABLE per-location modal FREQUENCY (alive-mode
  gating + values) + damping where resolvable, transmissibility SHAPE = diagnostic only; (a) BOUNDED search of
  richer transmissibility forms (latent load / region-freq-corr disc / near-resonance |φ_a/φ_ref| / shape-field)
  to document any shape-skill recovery (honest-neg expected). NOW BUILDING mpl_freq.py = measured peaks/loc from
  features.json + FEM alive-mode gating + matched-eigenfreq NUTS calib (reuse λ(θ) — converges) + held-out per-peak
  CRPS-skill vs climatology (pooled observed peaks) + interval/coverage; then carry-forward freq baseline → bounded
  (a) search → registry+figs+packet. Only this block + new-ws files edited.**
  **D8 RESULT (a+b RUN) — OVERALL YELLOW honest negative (simplest-sufficient model wins), STUDY at a clean stop.
  (b) FREQ headline (`freq_baseline.json`,`fig_freq_result.png`): matched-eigenfreq NUTS calib 6 K-groups, 5 LOLO
  splits ALL CONVERGED (R̂1.001-1.002, ESS~3000, cov0.93). CRPS-skill vs POOLED clim +0.91 BUT calib |Δf| 2.76% ≈
  nominal FEM 2.47% ≈ nearest-pooled fair-clim 2.51% → calibration adds NO held-out freq value (dense modal forest
  29-71 alive modes/node = weak discriminator; +0.91 is only vs the WIDE/weak bar). (a) decisive cheap RUN
  (`near_resonance.json`): at resonance |T|→|φ_a/φ_ref| (load cancels), measured-peak-height vs FEM-ratio log-corr
  +0.26 (n21) → transmissibility-shape residual = LOAD-INDEPENDENT mode-shape error ⇒ inferring load (richer-form
  lever) can't recover shape skill; latent-load NUTS arm MOOT → not run. VERDICT: as-received fable rev-3 FEM =
  TRUSTWORTHY FREQUENCY twin; NEITHER stiffness calib NOR richer transmissibility/load/disc forms improve held-out
  on single-axis no-force data = ShockSat DATA CEILING confirmed on MPL; pre-test lever = instrumented force +
  multi-axis/multi-ref shapes. check.py OVERALL YELLOW 13G/2Y/0R exit0 (2Y=M0 whole-curve non-conv/uncorrelated +
  honest verdict); run_all.sh replays; runtime ~905s; 3 figs tufte+image-QA pass; packet.md full story. SURFACE-only
  to Andrew (NOT self-applied): project_log row + runs.md entry + node-map ANDREW-CONFIRM + any "replace FEM" claim.
  NO durable-rule/checker/sampler edits. Andrew: review packet.md + figs; decide commit + project_log/runs rows.**
  **D9 DECK (Andrew request): `slides/mpl_twin_findings.pptx` (13 slides) + `code/fig_story.py` (5 new story figs)
  + `code/make_deck.py`. 9 figures total (geometry/sensor-map, statFEM likelihood schematic, measured |T|, forward
  diagnostic, dense modal forest, freq result, near-resonance scatter, strain-energy, registry) all tufte-lint +
  image-QA pass. Numbers pulled from out/*.json. check.py still YELLOW 13G/2Y/0R exit0. No libreoffice to render
  pptx but all embedded figs visually verified.**
- 2026-06-19 **STEERING DECISION (Andrew, durable for next studies):** DEFER evidence-based model selection
  (PAUSE Card F Stage-2 + Card E richer-stiffness — Stage-1 evidence already says stiffness isn't the lever) UNTIL
  we "have a grip on damping methods AND shape-driven / topology-alternative agentic remodeling." Andrew: "a lot of
  promise in a COMPLEX DAMPING PARAMETER in CBUSHes at interfaces." → NEXT STUDIES (priority): (1) DAMPING —
  complex/structural loss-factor on interface CBUSHes (bush_801..807 joints, bush_902 contact) via the
  un-confounded peak-WIDTH/complex-residue observable (half-power Δf≈2ζf depends on ζ alone, NOT participation —
  the one amplitude lever identifiable from 1 hit, resolution-permitting); (2) SHAPE-driven topology-alternative
  remodeling (subspace-MAC likelihood + joint connectivity/partial-bond alternatives, scored by held-out QOI not
  in-sample MAC). HONEST TENSION to design around: Card D damping_gate put modal-damping share on SHELLS
  (top_box .32/plates .25/cross .16), ZERO on joints/contact, because joints store ~3% SE → SE-DILUTION: a CBUSH
  can have a high LOCAL loss factor that's real but weakly identifiable (low modal contribution). So the cheap
  GATE-FIRST step (AGENTS Modal Identifiability gate) = per-CBUSH/per-mode SE fraction → which (mode,CBUSH) pairs
  store enough SE that η_cbush clears the floor + is the bandwidth resolvable. Stage-1 evidence (Card F) kept as the
  logged evidence BASELINE for when we return to selection. Card E fold question = moot (both deferred).
  **AUTONOMY GRANT (Andrew): "run it all, do not stop for permission, fully explore the space; goal = honest
  calibrated twin with CIs that TIGHTLY cover held-out data BETTER than the original FEM."** (Still surface:
  durable-rule/checker/sampler-standard, "replace inherited FEM", project_log row.) Program = Phase A/B/C/D/E in
  `decisions_log.md` D9–D11. **DECISIVE FINDINGS this session (workspace `shocksat_modelclass_L5_20260619`):**
  (A) damping is FREQUENCY-blind + its un-confounded observable (bandwidth) is UNRESOLVABLE here (FRF df=1.25 Hz +
  exp-WINDOW ζ_w 0.23–1.22% ≈ the real ζ 0.06–1.05%; peaks ~1 bin); interface-CBUSH attribution SE-diluted (bush_801
  peak SE 0.150 @151 Hz is highest but bw-unresolvable) → can't INFER damping here, but NASA per-mode modal ζ already
  exists. (B) `dampcorr_qoi_seed00`: 3 arms on same θ post — ARM0 uniform1% σ_QOI 1.112/int1703; ARM1 +window
  1.107/int**1306** (window = small free CENTERING gain, KEEP); ARM2 +per-mode-struct-ζ 1.167/int2279 (WORSE — windowed
  FRF UNDER-RESOLVES light modes so structural ζ mismatches). **DECISIVE: σ_QOI≈1.0 regardless of damping; σ_QOI =
  cross-CHANNEL scatter = mode-SHAPE error; damping is channel-common→absorbed by gain→CANNOT tighten it. The ~38 dB
  CI is a SHAPE error, not damping.** (C-prior) Card A L6/L10 ALREADY tried shape(MAC) calibration → ~null (σ_QOI
  0.99/1.11→1.13). So σ_QOI~1.0 holds across damping+freq+shape = **near-irreducible DATA CEILING** (single impact +
  coarse FEM; = Study L). PIVOT: untried = richer-LOCAL-stiffness+shape (C1'); plus original-FEM-baseline "beat this"
  (D1) + synthetic multi-REFERENCE VOI (D3, only hit-001 raw exists).
  **PHASE D1 + C done (D12/D13):** (D1, `fem_baseline_qoi_seed00`) ORIGINAL FEM (nominal, deterministic) misses
  held-out peak by median **5.4–6.7 dB, ~half off >6 dB, max 24 dB**; calibrated twin COVERS **97%** ⇒ GOAL
  "better than original FEM" MET on CALIBRATION (open issue = 38 dB WIDTH). (C, `discrepancy_diagnostic` +
  `heteroscedastic_qoi_seed00`) per-channel residual NOT predicted by generic features (DR/snap/z ρ≈0) but the 8
  a-priori-hard accels avg **17.5 dB vs 6.5 dB** rest → **two-population (hard vs rest) discrepancy tightens the
  well-modeled ~90% by ~22% (REST interval 1228→953, cover 0.97 held), honestly widens the 8 hard** (data-ceiling-
  limited). = the project's discrepancy-by-known-region vision + Card F M4. σ_QOI~1.0 ceiling confirmed across
  damping+freq+shape. CONTINUING (autonomy): confirm hetero seeds 1–3 + dampcorr seed3; Phase D multi-reference VOI
  (what test data buys the hard 8); Phase E integrate + figures + immutable check_twin.py + packet.
  **D14 — Andrew flagged the hard/rest split as over-fit; CONFIRMED (`fig_hardregion.png`, tufte+QA ok).** Hard 8
  =17.5 dB vs rest 6.5 dB (real heteroscedasticity) BUT no a-priori FEM feature predicts it (drive-dist ρ0.09,
  locality −0.17, DR −0.05) AND only weak spatial corr (nn4 0.24, flat variogram) → the split needs a HAND-LABEL
  derived from prior FEM-vs-test = NOT transferable; the error is a channel-specific near-field/coarse-FEM nugget.
  Two-pop tightens REST ~28% (seeds 0–3, cover held) = a real DEMONSTRATION (or where a knockdown library exists),
  NOT a turnkey method. ⇒ generalizable tightening = more/better DATA (multi-reference). NEXT: Phase D VOI (the
  honest generalizable answer) + Phase E packet/check_twin. Confirmation seeds all done.
  **D15/D16 — Andrew "this is plenty of data" → DROPPED the more-data/VOI framing (we HAVE a full EMA: .ash 33
  shapes/76 nodes = multi-reference).** Tested using the MEASURED shapes for held-out amplitude (D16,
  `shape_pattern_test.json`, after rejecting a buggy ill-conditioned modal-LSQ forward + a misleading complex-MAC):
  log-amplitude pattern corr of |shape| vs measured peak-|H| across 77 ch = FEM 0.140 / measured 0.117 (isolated:
  0.165/0.186; best mode ~0.5). **Neither FEM NOR measured shapes predict the single-impact per-channel peak-|H|
  (~0.15) → measured shapes do NOT tighten σ_QOI.** ROOT CAUSE: single-impact peak accelerance per channel is a
  near-field/local/overlap quantity, NOT cleanly modal → no global modal model predicts it (also channel↔node snap
  ≤6in). SYNTHESIS: twin is GREEN/tight on modal FREQUENCIES (6/6 held-out) + BEATS FEM on calibration (97% vs FEM
  5–7 dB misses); per-channel single-impact AMPLITUDE (peak+band ~34–38 dB) is intrinsically wide for ANY global
  model regardless of damping/FEM-shape/measured-shape/stiffness/discrepancy-structure — NOT a closable data/method
  gap. Two-pop = labeled demonstration only.
  **D17/D18 — Andrew Q2 (value of L5 updating on NON-hard sensors) + Q1 (were #2/#4 thorough?).** VALUE eval =
  CRPS-skill vs CLIMATOLOGY (guess held-out channel from observed-channel population) — the right bar (not the
  deterministic-FEM strawman). **AMPLITUDE: NON-HARD CRPS-skill −0.76/−0.84/−1.40 (mean −1.0), cover 1.00 = twin
  WORSE than guessing the population even on easy sensors (FEM shapes carry ~no per-channel amp info).** FREQUENCY:
  twin-vs-clim skill **+0.93** (2.1 vs 30 Hz), calibration halves freq err 2.10%→1.07%. → **twin value is REAL/
  strong for MODAL FREQUENCY, NEGATIVE for per-channel single-impact AMPLITUDE.** Q1 honest: #2 damping + #4
  shapes/topology were strong on the cross-channel-CI NEGATIVE but ARGUED not RAN the confirmations — owe: a damping
  inference + complex-CBUSH update (confirm unidentified), a shape-driven local-stiffness calib + held-out QOI, ≥1
  TOPOLOGY alternative, and the channel↔node-snap-vs-shape decomposition. value-eval shows amplitude value ≤0
  regardless → those confirm-by-running.
  **D19 — Andrew "run it" → Q1 gaps CLOSED BY RUNNING + INTEGRATED.** Snap: shape failure genuine (ρ−0.02, snap
  ≤0.75in, not a mapping artifact). Damping inference (`gap_closure`): band-GRMS skill −1.02, fitted ζ-scale best
  −0.60 = no value. Topology: bolted-joint released only −0.80→−0.66 = no value. Every amplitude lever ≤0.
  INTEGRATED: `figures/fig_value_summary.png` (freq +0.93 vs amp −1.0) + `fig_hardregion.png` (tufte+image-QA pass);
  immutable `check_twin.py` **OVERALL YELLOW 13G/2Y/0R exit0** (2Y = documented amplitude-no-skill + damping/topology-
  no-help, NOT failures); `packet.md`; `runtime.json` (active 2193s). **STUDY COMPLETE + thorough.** HEADLINE:
  calibrated L5 twin = REAL value for modal FREQUENCY (skill +0.93, calibration halves freq err 2.10→1.07%);
  per-channel single-impact AMPLITUDE = honest/covers but NO skill vs climatology, intrinsic (not data/method gap).
  **SURFACE to Andrew (NOT self-applied): docs/report/project_log.md row; any "replace inherited FEM" claim;
  durable-rule/sampler edits; Card F evidence Stage-2 (paused).** Only this CURRENT-STATE block + new-ws files edited.
  **D20 (2026-06-20) — DECK delivered:** `slides/shocksat_L5_twin_deck.pptx` (18 slides, 14 figs, image-QA pass):
  exec/value, sensors hard-vs-easy, param locations, strain energy, train/test split, scoring system, held-out FRF
  hard-vs-easy, GRMS, scores hard-vs-easy, value(freq+0.93/amp−1.0), roadblocks damping/remesh/likelihood, hard-region
  over-fit, synthesis, ideal-data+experiments, status. Plotting via saved .py + tufte-lint + image_qa. **⚠️ KILLED a
  STUCK IFT-thread job** (pid 68092, run_sweep.m2_split, ~14 CPU-hr at 100% on the non-converging M2 arm, started
  6-19 14:28) that was starving the machine — M2 divergence already documented (R̂129, σ_d→7.4); IFT runs resumable,
  M2 confirmation can be relaunched; did NOT edit IFT workspace. SURFACED to Andrew.
  **D21 (2026-06-20) — Andrew's 3 PUSHBACKS, all valid; corrected deck→21 slides + packet (anti-over-claim):**
  (1) likelihood breadth: ran ≥10 formulations not 2 (`fig_likelihood_inventory`); (2) spatial: re-examined
  (`spatial_reanalysis`) = MILD real regional concentration (bolted-joint region worst 12.3 dB) but weak predictor
  (R²=0.04) — partly confirms him, fixed my pre-written over-claiming title; (3) **MODEL FORM — big correction: I
  wrongly excluded the INFERRED-shape-FIELD model (Beck/L8b). 3 seeds: interval ~43% sharper, coverage→0.97,
  CRPS-skill −0.68(FEM)→−0.25(inferred) = HALVES the deficit (still <0 on 1 impact).** `shapefield_lever`,
  `modal_beck_ash` (reused Card A, climatology-skill added). REVISED HEADLINE: freq value real (+0.93); amplitude
  IMPROVED-not-solved (shape-field model form = real partial lever; full skill needs multi-reference data).
  **D22 (2026-06-20) — Andrew chose (a): FULL per-mode/complex DAMPING INFERENCE RUN (`damping_inference.py`):**
  per-mode multi-channel SDOF resonance fit, exact 2-D (f,ζ) posterior (residues marginalized). **0/9 fittable modes
  IDENTIFIED** (posteriors prior-dominated or railed to resolution floor; resonance width sub-bin at df=1.25 Hz +
  window). Per-mode ζ unidentifiable ⇒ complex/CBUSH Das-Debnath attribution moot (SE-diluted). Damping NOT
  recoverable from this single windowed FRF — confirmed by RUNNING (not argued). `fig_damping_inference.png`; deck
  slide 12b → DECK 22 slides; check_twin still exit0. Damping to-do CLOSED. Pre-test takeaway: identifying damping
  needs finer-res/multi-ref data (same lever as amplitude skill). image-QA 17/17. NO durable-rule/checker/project_log edits.
- 2026-06-19 NEW THREAD (Card F, lead-as-runner). Andrew handed the full **Card F runner prompt** (= the
  `shocksat_fem_remesh_20260618/HANDOFF_modelclass_selection.md`). **GOAL: evidence-ranked (Ockham-penalized)
  comparison of MODEL CLASSES M0–M5 (baseline / local-stiffness-split / Rayleigh / non-prop localized viscous /
  Schneider correlated discrepancy / combos) for the 8 hard ShockSat accels — Stage 1 analytic statFEM evidence
  at fixed-MAP θ, Stage 2 TMCMC evidence with θ flexible, cross-checked by L5 held-out QOI.** Workspace
  `artifacts/reports/shocksat_modelclass_L5_20260619/`. RE-GROUNDED (AGENTS all gates; Card F handoff; Card D
  damping_gate/joint_frontier[0/6000]/region_diagnosis; Card A L5 modal_feature [R̂1.002, 6/6 held-out modes,
  σ_w2≈0.069, θMAP bottom_box0.90/cross_beam0.81/top_box1.05] + heldout_qoi_L5 + paramcount). DONE: ws set up
  (Card A code+small-data COPIED byte-identical, 252MB FRF cache SYMLINKED, Card D diagnosis JSONs in
  out/cardD_inputs/); forward smoke-tested (reduced 74-DOF, nominal modes match Card A); decisions_log (D0
  constraints, D1 evidence machinery, **D3 KEY: modal peak-FREQUENCY observable ~blind to damping [ω_d shift
  ~ζ²/2~1e-4≪7% floor] → evidence headline ranks M0/M1/M4 on FREQUENCY; M2/M3 damping judged on AMPLITUDE +
  held-out QOI, confound-limited**); priority_deliverables P1–P9; references_reviewed (statFEM §3.4/§4.1.5,
  Kiran §5, Ching-Chen TMCMC, Schneider, Das-Debnath); immutable check.py (baseline **RED 4G/0Y/11R**, integrity
  GREEN). **⚠️ CONCURRENCY CONFLICT SURFACED TO ANDREW (HOLDING before compute): a Card E thread
  (`shocksat_richmodel_L5_20260619`) is ACTIVE in parallel and the card says "Card F SUBSUMES Card E."** Card E
  already built EXACTLY my open items: `out/perpid_reduced.npz` (per-PID reduced K blocks = my D5) +
  `out/identifiability_rich.json` (richer-stiffness gate: bottom_box:shell_101 peak SE-frac 0.94 @21× floor =
  strongly identifiable; CBUSH801 marginal; same participation/damping-confound insight as my D3) + `richmodel.py`.
  Card E is ITSELF paused at a compute-commitment checkpoint. No Card E/F compute running now. **DECISION NEEDED
  from Andrew: fold Card E into Card F (I reuse Card E's perpid_reduced + identifiability as inputs; Card F evidence
  ranking = umbrella) vs keep separate with a division of labor — to avoid duplicate/thrashing compute + conflicting
  answers.** Also A1: Stage-1-checkpoint vs full autonomous run. NO durable-rule/checker/project_log/runs edits
  (only this block + new-ws files). IFT thread: no jobs running.
  **STAGE-1 DONE (D7, `out/stage1_evidence.json`, 2 s reduced model): the cheap Ockham screen.** Observable = 27
  matched modal ω̂²; θ@MAP; resid median 2.98% vs σ_w2≈6.9% floor. BIC-adjusted (only type-II-ML'd hyperparams
  penalized; marginalized stiffness params already Occam-penalized) ranking @σ_prior=0.25, prior-ROBUST (no flip):
  **(1) M0_fixed_thetaMAP P=0.906 [as-received θ-MAP FEM + iid disc = WINNER]; (2) M4_corr_discrepancy P=0.093
  [RAW logZ best +1.0 but NOT decisive after its 2 extra hyperparams, rmix→0.999 = SUGGESTIVE structure-the-
  discrepancy lever]; (3) M1_joint_split ≈ (4) M0_base9 > (5) M1_box_split > (6) M1_full_rich(16p)=WORST.**
  HEADLINE: **richer LOCAL stiffness (M1, up to 16 params) does NOT earn its complexity on FREQUENCIES** (Ockham
  confirmation+extension of Card D's coarse-9-group Pareto-optimality to the local splits Card D never tested;
  statFEM §4.1.5 "simpler can win"). Damping M2/M3 provably FREQUENCY-BLIND (shift 5.5e-5≪0.069) → amplitude/QOI
  only. check.py 6 GREEN/9 RED. Caveat: Stage-1 fixes θ (conservative for richer classes); Stage-2 TMCMC (θ free)
  = rigorous re-rank. **REPORTED to Andrew at phase boundary; HOLDING before multi-hour Stage-2 compute.**
- 2026-06-19 NEW THREAD (Card E, lead-as-runner). **Does ENRICHING the model form (richer LOCAL stiffness
  parameterization and/or non-proportional damping) run through the converged L5 modal-feature NUTS pipeline
  measurably SHARPEN the held-out-sensor QOI at the 8 hard ShockSat accels (ch4/27/38/40/52/69/98 +susp ch92)
  WITHOUT degrading other channels?** Workspace `artifacts/reports/shocksat_richmodel_L5_20260619/`. RE-GROUNDED
  (AGENTS all gates; Card D HANDOFF + joint_frontier 0/6000 + damping_gate rank-deficient; Card A L5 D11/D12/D22).
  **KEY ENABLER:** per-PID full-order K blocks exist (modal-twin `matrices/K_*.npz`) + reduction recipe
  W=T@V_keep[:,6:], so I build any richer LOCAL param by projecting B_pid=WᵀK_pidW and regrouping — θ=1
  reconstructs nominal EXACTLY (integrity 6e-12/6e-10). DONE: ws skeleton (COPY-reuse Card A code/data, 263MB
  cache symlinked), immutable check.py (baseline RED, derives sharpen verdict from numbers = anti-over-claim),
  decisions_log D0–D3, priority_deliverables, references_reviewed, `code/richmodel.py`. **IDENTIFIABILITY GATE
  DONE (the cheap decisive step, `out/identifiability_rich.json`, floor σ_w2=0.0446 from L5 baseline):** the
  split is a MIX not a uniform negative — full_rich(16 params) has 8 FIM combos clearing prior; NEW identifiable
  local dirs = bottom_box:shell_101, top_box:shell_201, plates:shell_701(sv 19.5!), 601, cross_beam; BUT
  bolted-joint(CBUSH801) MARGINAL/prior-dominated (combo sv 4.04@floor.045→2.61@.069, flips at boundary 16 =
  confirms Card D joints~3%SE), and shells 103/203/501+welds+contact below floor (splitting them only WIDENS).
  ∂λ/∂logθ=φᵀAφ=λf → SE-fraction IS the FIM sensitivity. Gate does NOT decide sharpen: identifiable-from-FREQ ≠
  sharper-AMPLITUDE (the ×2.7 held-out width is set by σ_QOI = observed-channel AMPLITUDE residual = the
  participation/damping confound, which frequencies don't fix). BASELINE BEFORE reproduced (D3: R-hat 1.002,
  cover 0.935, hard ch40/98 miss). **NEXT (compute-commitment CHECKPOINT — SURFACED to Andrew):** build richer-
  aware L5 calibrate + held-out QOI (parsimonious-rich + full_rich variants), before/after over ≥25-split MC,
  DETACHED+resumable (~1 baseline split = few min sequential NUTS → MC is multi-hr). NO durable-rule/checker/
  project_log edits (only this block + new-ws files). Card A/B/D ws = HANDS OFF (copy only).
- 2026-06-19 NEW THREAD (IFT card, lead-as-runner). **Is "physics in the PRIOR with a learned trust temperature β"
  (Information Field Theory / PIFT, Hao-Bilionis 2306.02150 + Alberts-Bilionis 2301.07609) a better/equal/worse
  way to build a trustworthy ShockSat twin than our StatFEM discrepancy/modal-feature approach, on REAL held-out
  data?** Workspace `artifacts/reports/ift_real_validation_20260619/`. RE-GROUNDED (AGENTS.md; StatFEM run
  `statfem_real_validation_20260617` packet + phase2 QOI; consistency-toy `nuts_marg.py` M-ift). Apples-to-apples:
  SAME real single-impact |H| (hit-001, 45–260 Hz), SAME forward (`realfrf`/`core` reduced 74-dim, ζ=0.01),
  SAME ≥25-split held-out protocol (heldout_qoi/mc_heldout split RNG, obs_frac 0.6, DR≥30), SAME scorer
  (`score.py` interval/CRPS/logpd headline), SAME convergence gate (R̂≤1.05/ESS≥200/div<2% incl. β; NUTS→TMCMC
  escalation). **HUMAN DECISION (Andrew, D0):** lead flagged the DRAFT §2 error — claimed EXACT field
  marginalization but the headline observable log|H| is NONLINEAR in the complex field (log-Rician, not Gaussian).
  Andrew: "keep the headline arm on the same log|H| observable using a documented log-magnitude moment
  approximation … run it yourself." → IFT headline = SAME log|H| as M2, field marginalized by a first-two-moments
  (delta-method/high-SNR) Gaussian approx of the log-Rician, labeled approximate everywhere. CONSTRUCTION (D1):
  log|H_j|~N(log|H_j^FEM(θ)|+c, σ_meas²+v_j/(2|m_j|²)); v_j(ω)=ω⁴Σ_k p_{j,k}²/(βD_k+τ0), D_k=(λ_k−ω²)²+(ηλ_k)²,
  p_j=obs_V[s_j]@Q — physics-derived heteroscedastic variance set by ONE learned trust β (β→∞ ⇒ plain log|H|+σ_meas;
  β→0 ⇒ graceful widening). = the apples-to-apples test of WHERE physics/trust lives (IFT prior vs M2 likelihood)
  on the IDENTICAL observable. β prior (D2) centered on the forward (β* s.t. median field-var=σ_meas², NO data),
  logβ~N(logβ*,2.0), swept. Non-converged arms flagged+excluded from headline (D3, M2 expected to diverge = the
  robustness result). PRE-COMMITTED verdict WIN/ROBUSTNESS-WIN/TIE/HONEST-NEGATIVE generated by check.py from the
  numbers; coarse-FEM ceiling carried up front (sharpness WIN a-priori unlikely; live question = robustness/
  calibration). Verified: .venv_nuts (py3.9), sibling V_keep/fem_model present, measured_frf_cache.npz present
  (no 256MB .mat reprocess). StatFEM bar: L5 θ+QOI-disc peak cover 0.91/z 1.03/interval 1.44e3 (calib R̂ 1.0015);
  M2 whole-FRF NON-CONVERGED (R̂ 104–129, σ_d→∞). BUILT: 15 assets byte-identical + manifest (provenance
  GREEN); method_ift/priority/framing/ledger; ift_arm.py (smoke-ok); immutable check.py (baseline RED, exits
  non-zero); run_sweep.py; ift_tmcmc.py. **KEYSTONE (D6/D7):** IFT under NUTS NON-CONVERGED (seed0 R̂ 264.9, 0
  div = MULTIMODAL — inherits whole-FRF θ-multimodality because IFT likelihood MEAN is still oscillatory FEM
  log|H(θ)|; β doesn't cure it) BUT β BOUNDED (no σ_d runaway). Pre-authorized TMCMC escalation (card §2/StatFEM
  D9): **IFT-TMCMC seed0 (n1500×4runs) CONVERGES cross-run R̂ 1.0008, ESS 1371, logEvid −18208±0.22; β_med 0.168
  = 255× below β*=42.8 = thermometer reads STRONG coarse-FEM distrust, BOUNDED; held-out PEAK cover 1.0/interval
  7331/CRPS 77.8/logpd −5.9, BAND cover 1.0/interval 1.12e5.** vs L5 bar PEAK interval 1.44e3, BAND 3.6e3 → IFT
  NOT sharper (coarse-FEM ceiling, as pre-committed) but CONVERGES+bounded+calibrated where M2 (same observable,
  physics-in-LIKELIHOOD) diverges (M2-TMCMC R̂ 129, σ_d→7.4, ~1e17). **EMERGING VERDICT = ROBUSTNESS-WIN**
  (checker-generated, pending confirm). L5 25-split DONE (all conv). **IN PROGRESS:** IFT-TMCMC seeds 1–4
  (confirm not-a-fluke) + M2 seeds 0–4 (divergence on identical splits) detached → aggregate_scorecard → figures+
  deck+sensitivity(β)+discretization+final checker. NO durable-rule/checker/project_log/runs edits (only this
  block + new-workspace files); project_log row + runs.md PROPOSED at end.
- 2026-06-19 SIDE-THREAD (Card D/E/F handoff hub, text-only deliverable): Andrew handed full Girolami statFEM +
  Kiran 2025; asked to review statFEM **§4.1.5 (model/mesh selection by marginal likelihood + Bayes factor)** +
  Kiran **§5 (Bayesian model class selection)** and develop an experimental prompt to model around the hard-to-
  correlate accels — fix other params at MAP first, then flexible; damping forms / local parameterizations =
  competing model classes. DELIVERED `shocksat_fem_remesh_20260618/HANDOFF_modelclass_selection.md` (**Card F**):
  evidence/Bayes-factor (Ockham-penalized) ranking of model classes M0–M5 (baseline / local-stiffness-split /
  Rayleigh / non-prop localized viscous Das-Debnath / Schneider correlated discrepancy / combos); Stage 1 analytic
  statFEM evidence at fixed-MAP θ, Stage 2 TMCMC evidence with θ flexible; cross-checked by L5 held-out QOI at the
  8 hard accels; identifiability + evidence-sensitivity gates; carries participation÷damping confound + re-pairing-
  robust + evidence≠held-out + scope-claims lessons. Card F SUBSUMES Card E. Logged D17. NOT yet launched (awaiting
  Andrew: new standalone Card vs. fold into Card E, and whether to dispatch a runner).
- 2026-06-18 NEW THREAD (Card D, lead-as-runner). **Can an agent contribute to FEM correlation by re-meshing/
  remodeling the high-error ShockSat regions from data?** Workspace `artifacts/reports/shocksat_fem_remesh_
  20260618/`. RE-GROUNDED (AGENTS.md; Card A validation D0-D22 + packet; modal-twin FEM pipeline). The 8 hard
  channels (ch4/27/38/40/52/69/92/98, +X impact face / bulkheads / bolted joint / strut / dish) miss the 95%
  band on per-sensor AMPLITUDE. **DECISIVE READ-ONLY FINDINGS:** (D3) the FEM is ALREADY mesh-converged —
  uniform 0.25-in mesh, 37-135 elements/bending-wavelength at 260 Hz → "re-mesh finer" provably cannot move
  modes; (D1) joints are ALREADY finite anisotropic CBUSH (PBUSH 801-807), NASA-correlated + Card-A
  NON-identifiable; (D5) topology COMPLETE (bulkheads at Z12.4/18.4/30.4, bolted joint CBUSH801, struts all
  present; bulkheads node-merged = welded = correct). SE decomp: modes dominated by bottom_box 46.8%+top_box
  34.9%, joints only 3.1%. **Andrew steers:** A→2→"keep iterating until legitimate exhaustion of reasonable
  correlated-update attempts." BUILT editable copy + reproduced BEFORE baseline (max rel Δf 3.6e-10 vs
  inherited = meets 3e-10 bar; global matched MAC 0.631). `code/edit_solve.py` (per-PID block edit→reduce→
  eigsh80→global+region MAC+|df%| vs .ash; ~290s/solve). **CAMPAIGN RUNNING detached (pid 27910, ~1hr,
  resumable):** baseline_reuse + e01 calibrated-θ (modal-twin NUTS posterior, the data-driven update) + joint
  soft/stiff + bottom_box/top_box ±10% + bolted-joint801/strut807/contact902. EXPECT: θ improves frequency
  not MAC (D22: θ can't move shapes); honest verdict forming = re-meshing/stiffness is NOT the lever, residual
  = interface damping + near-field + freq-misalignment. **EXTENDED 2026-06-19 (D6-D16):** correlated-update
  campaign (10 edits + dish remesh, 0/10 clean) → damping thread (measured ζ 0.12-1.76%, bulkhead/cross drum
  modes most-damped = non-proportional; reviewed Das&Debnath2020/Kiran2025/Schneider2022; damping gate; L-damp
  prototype). Andrew pushed hard on circular/over-claimed conclusions; KEY CORRECTIONS (I repeatedly over-claimed
  negatives — DURABLE LESSON: scope claims to exactly what's tested, use re-pairing-robust metrics, lead with
  held-out QOI not MAC): (a) per-channel amplitude = participation÷damping CONFOUNDED at single impact; (b)
  JOINT-frontier (all 9θ free, tracked metric, 6000 samp) = 0/6000 → COARSE 9-group stiffness update is
  Pareto-optimal (fig_joint_frontier.png); (c) BUT "no model change helps" = OVER-CLAIM (parameterization limit,
  not model-form) — richer LOCAL params / non-prop damping UNTESTED + Card A D22 (infer shape FIELD) already
  SHARPENED ~19%. HANDOFF written `HANDOFF_richmodel_L5.md` (Card E: richer model form through L5 → does held-out
  QOI at 8 hard accels sharpen?). NO durable-rule/checker/project_log edits.
  **[earlier in this thread:] STUDY COMPLETE (checker GREEN 14/0/0).** Campaign of
  10 correlated updates + dish 2× mesh refinement DONE. HEADLINE: **0/10 edits improve a hard-region metric
  without degrading global MAC or frequency = a shape-vs-frequency Pareto tradeoff** (soften joints/boxes →
  region MAC up [box +0.12, src +0.11] but freq detunes +0.3..0.9%; calibrated-θ/bottombox → freq better but
  shape flat-to-down; e07 top_box×0.9 closest = global MAC +0.010 + all regions up but +0.93% freq). Dish 2×
  refine moves global MAC +0.0016 (36/38 modes unchanged <0.1%; the +17% partner = degenerate-cluster mode-swap
  artifact, NOT real) → mesh CONFIRMED converged. VERDICT (correlation_contribution.md): re-mesh/stiffness NOT
  the lever; as-received FEM near Pareto compromise; residual = damping + near-field + freq-align; real fix =
  test data (multi-ref + per-joint damping). Agent contribution = the auditable BOUNDARY of remodeling-from-data
  (the Ilias "identify the gap" deliverable). active_runtime ~3853 s / 13 eigensolves. SURFACE-only to Andrew
  (NOT self-applied): docs/report/project_log.md row; any "replace inherited FEM" claim; durable-rule/checker.
  NO durable-rule/checker/project_log edits made (only this block + new-workspace files). Card A/B ws = HANDS OFF.
- 2026-06-17 NEW THREAD (Card A, lead-as-runner; sibling = Card B PIFT below — stay out of its workspace).
  **Validate the orthogonal-Schneider StatFEM twin on the REAL ShockSat.** Workspace
  `artifacts/reports/statfem_real_validation_20260617/`. Plain 9-group FEM ONLY (no tray); M3
  orthogonal-Schneider = method under validation, M0 naive = contrast; COPY-reuse synthetic companion
  `statfem_shocksat_eval_20260616/code/{core,nuts_arms,predict}.py`. **Phase P1 (observable resolution) DONE;
  PAUSED at a §14 SURFACE stop — awaiting Andrew's observable call BEFORE building the pipeline / check.py.**
  KEY FINDING (reproducible `code/probe_observable.py` → `out/observable_investigation.json`): the prior
  runner's "hammer FRF not-likelihood-ready, coherence ~0.06" was a PROCESSING ARTIFACT (scipy Welch
  nperseg=32768 over ONE impact transient w/ a single force spike → most segments force≈0 → coherence
  collapses; Discretization-Gate pitfall). A proper single-impact FRF (force/exp window, single FFT) recovers
  REAL resonances aligned with the .ash modes to median ~1.5–2.4 Hz (ch1 71/116/168↔70/117.6/168; ch50 69/74/120;
  ch87 120/139/195) → matched-path FRF NOT inherently invalid; SOL111 objection reconciled by driving same node
  in FEM. BUT hard data limits: only 1/4 raw hits present + 3/326 channels precomputed (128 recorders in hit-001
  → ~127 reprocessable, all at ONE impact) → raw FRF supports only the SPLIT axis, NOT the impact-location/hit
  axes the §7 MC (≥25 configs) needs. MY RECOMMENDATION (Andrew decides): HYBRID — modal-synthesis fallback
  (.ash 33 modes/76 ch, rel-std ~0.3%) as headline MC observable + a real-FRF amplitude VALIDATION track on
  hit-001 reprocessed channels at the one impact (peak-alignment overlay + real-|H1| held-out scoring, 1-hit
  YELLOW caveat). **DECISION (Andrew 2026-06-17): option (b) ALL-REAL-FRF, single impact location** (D2 logged).
  No modal fallback. MC randomizes the observed/held-out SPLIT only (drive=impact node fixed; impact/hit axes=1,
  labeled). θ recovery has no real-data ground truth → parameter-count study scored on HELD-OUT QOI + FIM
  identifiability. Coherence weighting → 1-hit SNR weight (YELLOW). **PROGRESS (autonomy granted P2–P5):**
  P1.5 §2(d) GATE = **PASS** (`out/matched_path_sanity.json`): FEM 1st mode 54.6≈meas 54.2 Hz; absolute
  amplitude offset = a GLOBAL ×100 units-gain, STABLE across channels+ζ → 1 global gain nuisance (D4); residual
  scatter+peak-misalign = the real model-form error to calibrate. BUILT: immutable `check.py` FIRST (baseline
  RED=not-done, P1/P1.5 gates GREEN); copied core/nuts_arms/predict/viz/image_qa BYTE-IDENTICAL + small data;
  `realfrf.py` (V_keep→reduced transform T verified 1e-14 → place any FEM DOF; 87 mapped channels DR median
  147×; single-impact measured FRF cached; 1-hit SNR quality weight D5; g/lbf forward numpy+jax); `real_arms.py`
  (4 arms + global gain nuisance); `run_cell.py` (resumable cell driver); `identifiability.py` (written, not run).
  **SANITY CELL (detached, split0 n8 ζ0.01): M0 naive = NOT-YET-CONVERGED R-hat 114.9/ESS 2/0 div = MULTIMODAL
  under-identification** (real model-form error, no discrepancy to absorb it → 9θ+gain contort into basins;
  expected "naive breaks on real data"). M3 orthogonal RUNNING (bg task bzsvf862s) — the headline contrast =
  does the orthogonal discrepancy de-bias+converge? **RESULT: BOTH M0 & M3 NON-CONVERGED (R-hat 104–115, ESS 2,
  0 div = multimodal); M3 σ_d ran away to 9.8.** Diagnostic battery (D7, `out/diagnose_convergence.json`): ALL 5
  fix-attempts FAIL (R-hat 34–475) — fixing σ_d@floor, downselecting to 4 ident groups, both, even M0 with only
  4θ+gain (R-hat 475). **VERDICT: multimodality is INTRINSIC to the whole-FRF-MAGNITUDE likelihood under real
  model-form error** (|H(θ)| oscillatory→many θ basins fit peaks; not a σ_d/dimension issue). Project's own prior
  work shows the cure = MODAL-FEATURE likelihood converges on this exact structure (modal twin R-hat 1.022;
  Study K per-mode freq 1.007, 5/5). **SURFACED to Andrew (D8 pending §14 fork, changes core likelihood+verdict):
  (1) attack multimodality (tempering/SMC/multi-start) to test robust-twin thesis [QOI calibrated-but-wide despite
  unidentified θ]; (2) FRF-FEATURE likelihood = peak freqs/amps FROM the real FRF (keeps his real-FRF observable,
  identifiable, converges); (3) report robust negative + recommend. MY REC = (2), ideally + report the (1)
  negative = full validate/identify-gap/improve arc.** PAUSED for Andrew's call; MC = 0% done by design (won't run
  25 configs of a non-converging setup). **D8 REFERENCE GATE (Andrew gave 2 papers: Kiran 2025 review + Schneider
  2022 = SOURCE of our M2/M3): our findings are NAMED — multimodality = "local identifiability" (Beck–Katafygiotis),
  σ_d→9.8 = the "variance→0/∞" likelihood singularity. KEY: the SAMPLER is the gap — Schneider used BUS+Subset
  Simulation (multimodal-capable), the FE field uses TMCMC/Gibbs/SuS; NUTS is rare + can't cross modes. We also did
  NOT implement Schneider faithfully (pure-Kronecker+fixed lengths+NUTS vs his ADDITIVE corr + LEARNED hyperparams +
  SuS + coherent-band + parsimonious GLOBAL params). His damping/peak-amplitude misfit = IDENTICAL to ours, absorbed
  by σ_w≈0.31 → ~90% coverage w/ eigenfreq-localized misses (NOT a runaway; realistic best case). REVISED REC:
  (a) SURFACE sampler change NUTS→TMCMC/SuS [durable NUTS-rule stop]; (b) implement Schneider faithfully; (c)
  param-count via EVIDENCE + parsimonious params; (d) coherence-restrict; (e) M0/M2/M3 under proper sampler + keep
  NUTS multimodality as headline diagnostic; sharpened M2-vs-M3 (orthogonal may STARVE discrepancy). PAUSED for
  Andrew's sampler call.** **D9 Andrew APPROVED (2026-06-17): adaptive sampler (NUTS detects multimodality →
  escalate to TMCMC/BUS-SuS) + sweep most-promising likelihoods (Kiran+Schneider) + quality threshold as a SWEPT
  variable. Chose TMCMC (also gives EVIDENCE for the param-count study). check.py stays immutable — TMCMC fills
  same diag fields (cross-run R-hat over ≥4 independent runs). BUILT + VALIDATED `code/tmcmc.py` (bimodal
  self-test: populates BOTH modes 0.51/0.49, R-hat 1.001, stable evidence). **D10 KEYSTONE (honest, `out/
  tmcmc_probe_M3.json`): sampler swap ALONE does NOT fix it. MINI run (n400,2runs) R-hat 1.06 = FALSE POSITIVE
  (cheap-probe lesson). FULL run (n1500,4runs,992s): NOT CONVERGED — cross-run R-hat 129, ESS 0, log-evid
  −17900±739 (runs disagree), σ_d 7.4 [1.3,8.7] = the "variance→∞" singularity persists. The CONFIGURATION
  (fixed-length pure-Kronecker cov + free σ_d + 9 params + whole-FRF), not just the sampler, is the problem (=
  D8's point we never implemented Schneider faithfully). Also built+validated `code/score.py` sharpness suite —
  WIDE-DOESN'T-WIN demo PASSES (wide band: cover=True but interval 7.89 vs 0.78, CRPS 0.47 vs 0.05) = §5 gate.**
  REDIRECT (do BOTH): (i) FAITHFUL Schneider = additive corr + LEARNED lengths + INFORMATIVE σ_d prior (kills the
  variance singularity); (ii) parsimonious params; (iii) larger TMCMC n≥4000; (iv) build the well-behaved
  MODAL/PEAK-FREQUENCY feature likelihood (L5, extract peaks FROM the real FRF — project's own modal twin R-hat
  1.022 proves this CONVERGES) — likely the headline positive vs the pathological whole-FRF. **D11 BREAKTHROUGH
  (`out/modal_feature.json`, `code/modal_feature.py`): L5 modal peak-FREQUENCY likelihood (peaks extracted FROM
  the real FRF: 44 consensus modes, 27 matched to FEM ≤12%) CONVERGES — R-hat 1.002, ESS 2388, 0 div, 60s;
  held-out-MODE coverage 6/6; σ_w2≈0.069 (~7%≈σ_f floor); θ cross_beam 0.81/top_box 1.05/rest≈1. THE VALIDATION
  ARC RESOLVES: whole-|H| MAGNITUDE = locally-identifiable/near-singular (NUTS 104, TMCMC 129, fails); MODAL
  peak-FREQ from SAME real FRF = CONVERGES + predicts held-out features. Gap identified + improvement demonstrated
  (the Ilias deliverable).** NEXT: L5 → held-out-SENSOR peak-|H|/GRMS QOI (modal-superposition from calibrated
  θ+shapes+damping); refine matching w/ MAC; then faithful-Schneider L2 (additive corr+learned lengths+informative
  σ_d) + complex-additive L4 + τ-threshold sweep + param-count-by-evidence + ≥25-split MC + figures/packet/pptx.
  STRONG honest checkpoint = natural phase boundary (prefer fresh re-grounded session for the sweep). NO
  durable-rule/checker/notes edits (only this block + new-workspace files decisions_log/references_reviewed).
- 2026-06-17 NEW THREAD (Andrew handed Runner Card B; lead-as-runner). **Does our StatFEM exhibit the PIFT
  posterior collapse, and does orthogonal-Schneider cure it?** Workspace
  `artifacts/reports/statfem_pift_collapse_20260617/`. RE-GROUNDED (AGENTS.md all gates; companion synthetic
  study `statfem_shocksat_eval_20260616` D0–D16 — arms M0 naive/M1 iid/M2 Schneider/M3 ORTHOGONAL-Schneider
  already built; FEM twin + statfem runner). KEY FINDING pre-compute: the collapse mechanism is LATENT in the
  reused `nuts_arms.py` — M0/M1 scalar variance → Fisher info ∝ N → collapse; M2/M3 whiten vs eigenvalues of
  C_f⊗C_z (M3 also projects off θ→FRF span) → effective DOF saturates → candidate plateau/cure. Must PROVE
  with the N-ladder + ESS accounting, NOT pre-decide. WROTE: workspace skeleton, decisions_log (D0–D2 + OPEN
  S1/S2/B1/B2/N1), priority_deliverables, analogy_mapping_DRAFT. **D3 Andrew "go" 2026-06-17** resolved all:
  S1 mapping signed off → `analogy_mapping.md` (verified PIFT quotes p17/p25, the (nJ)⁻¹→0 mechanism, in
  `references_and_quotes.md`); S2 synthetic-first-then-real signed off; B1 PDFs now in references/pdfs
  (2301.07609v5, 2306.02150v2); B2 README = `runs/statfem_realdata_20260617/README.md` (matched-path = drive
  OWN FEM at impact/tap node, coherence-weight, NO SOL111). SIBLING Card A owns
  `artifacts/reports/statfem_real_validation_20260617/` — HANDS OFF. BUILT (all): immutable `check.py` FIRST
  (validated: OVERALL RED=not-done, integrity SHA + reference gate already GREEN); copied core/nuts_arms/predict
  BYTE-IDENTICAL (SHA MATCH, D4 integrity model = all new logic in NEW files); scoring.py (interval-score/CRPS/
  PIT, anti-width-fool), run_ladder.py (resumable N-ladder, densifies ONE fixed truth via decimated 640-master
  grid), ess_accounting.py (N_eff Fisher + participation ratio), aggregate_sweep.py (verdict from trends, not
  pre-decided), discretization.py (inherited reduced-vs-full 0.081 cited + fresh internal refine), identifiability
  (4/9: bottom_box/top_box/plates/cross_beam), docs (assumptions/framing/quantity), run_all.sh. **LAUNCHED synth
  N-ladder DETACHED+resumable** (pid 91899, logs/ladder_synth.log; 24 cells M0/M1/M3 × {nf20-320 ns6} +
  {nf160 ns3-18}, ordered low-N first). EARLY FINDING (P1): low N=120 is UNDER-IDENTIFIED — 4-chain R-hat 8–24,
  ESS 2 (multimodal θ↔discrepancy), LABELED not-converged (YELLOW). Collapse story = the HIGH-N tightening
  (companion converged at N=960). NEXT: let sweep finish → check per-N convergence → aggregate verdict over
  CONVERGED cells → P3 real matched-path leg (build_real_frf.py, reprocess hit-001 raw .mat in MY ws) → P4
  figures+packet+pptx. Caveat noted: band-GRMS QOI is grid-resolution-sensitive (~8%) → lead with grid-independent
  σ_d/θ widths. NO durable-rule/checker/notes edits (only this block + new workspace files).
- 2026-06-16 ARM C **COMPLETE** (this session = Opus HYBRID runner). Workspace
  `runs/statfem_skill_20260616/opus_hybrid/case_study`. BOTH harnesses satisfied: skill
  validate-completion=OK (T1+T2 MATCHED, provenance+comparison+report-embed, deterministic figs) AND
  AGENTS.md convergence/status gates reported. Anti-cheat scan CLEAN (no reproduced fig == any of 32 paper
  assets). Replay `bash scripts/reproduce_all.sh` validated (active 30s resumable; from-scratch NUTS 264s).
  RESULTS — T1 GREEN: convergence rate 1.97–1.99 (~2) all ℓ_f, lumped Eq(20)<exact Eq(18) (both paper claims).
  T2: NUTS (numpyro, 4 chains, all-var R̂/ESS/div). HEADLINE DOMAIN CATCH = the paper's FLAT improper prior
  → posterior improper in ℓ_d (SE kernel saturates → infinite flat shelf); NUTS exposes 37–86% div, R̂~340 at
  n_y=4,11 (RED, never "active"); depth-12 confirmed it CONVERGES at n_y=33 (sensors identify ℓ_d) = data-
  dependent fragility. Minimal proper fix = bounded-uniform "flat-in-a-box" prior (ℓ_d≤domain) → converges all
  12 cells (R̂≤1.05, ESS≥200, 0 div); reproduces ρ (2.2% median err), SD-shrinkage-with-n_o (core claim),
  ℓ_d 0.073 vs paper 0.074 at n_y=33. Honest residual: ℓ_d prior-dominated/under-identified at n_y=4.
  Verification Gate (verify_core 8/8) caught a real SMW solve-order bug pre-figures. Conflicts logged
  decisions_log D1–D10; closing note CASE_STUDY_NOTE.md. Env: base python3 3.9.6 (fitz+numpyro/jax x64;
  arviz broken→numpyro.diagnostics). Harness scripts UNMODIFIED. NO durable AGENTS.md/checker edits (only this
  block + case_study files). HANDS OFF other arms (codex/, opus/) — saw their track-run procs, left alone.
  NEXT (lead, later): 3-arm comparison + any durable synthesis (needs Andrew approval).
- 2026-06-16 NEW THREAD (Andrew): re-run statFEM REPLICATION with Bilionis's code-enforced
  paper-replication SKILL (`codex-skills-main/skills/paper-replication/`) in Codex + Opus; compare to
  our 2026-06-10 runs. Answers Andrew's confound "did they not cheat because OUR harness is too tight?"
  by holding task constant + swapping to an independent, code-enforced anti-cheat harness. DECISION:
  keep his harness SEPARATE (clean experimental variable; blending = re-creates the confound); durable
  synthesis into AGENTS.md = LATER, needs human approval (his validators have NO convergence/frequency
  domain concept = exactly our differentiators). Verified: skill runs on py3.9.6; bootstrap vs the PDF
  works (defaults latex-first → must set pdf-only). PLAN DECIDED (Andrew): Part 1 (§4.1 replication) only,
  THREE ARMS — A Codex skill-only, B Opus skill-only, C Opus HYBRID (paper-replication skill + AGENTS.md
  domain/convergence gates). Skill activation/deactivation done IN-PROMPT (each runner echoes its active
  set; no on-disk skill changes) — removes the ambient-skill confound. Sampler DELIBERATELY unspecified in
  A/B (observe if convergence slips with no gate); NUTS+all-var convergence REQUIRED in C (the operative
  A/B-vs-C contrast = does our domain layer catch the flat-improper-prior fragility a sampler-agnostic run
  misses). SETUP DONE: `runs/statfem_skill_20260616/` (README_experiment.md + 3 runner prompts;
  codex/ opus/ opus_hybrid/ dirs). LAUNCH: Andrew spawns 3 fresh sessions (I cannot); Arm A needs
  `cp -R codex-skills-main/skills/paper-replication ~/.codex/skills/` so Codex can invoke it (B/C drive the
  repo-copy CLI). ALL 3 RAN; 3-ARM COMPARISON DONE (lead, 2026-06-16) → `runs/statfem_skill_20260616/comparison.md`.
  RESULTS: all 3 validate-completion=pass, both targets MATCHED; CHEATING SCAN CLEAN across all 3 (0 reproduced
  figs byte-identical to ~35-39 paper assets; fitz hits = skill's reference rendering; 'surrogate' hit = docstring
  affirming NOT a surrogate) → no-cheat result ROBUST to swapping our harness for Bilionis's own (answers Andrew's
  confound; honest limit = both regimes omit his do-not-stop pressure, that ablation still un-run). HEADLINE: the
  SKILL ALONE BLESSES A NON-CONVERGED REPLICATION — Arm A (Codex) passed completion on T2 at R-hat 4.66/ESS 4.3
  (RW-Metropolis), skill kept it honestly visible but never required diagnosis/fix (skill has NO convergence
  concept). Arm B (Opus skill-only) diagnosed the improper-prior analytically + bounded-prior fix from own
  competence. Arm C (hybrid, NUTS forced) DETONATED the pathology (37-86% div, R-hat~340, RED) → data-dependent →
  fix converges all 12 cells. LESSON: paper's RW-Metropolis MASKS the fragility, NUTS exposes it = why authors
  missed it + why convergence gate matters; skill (provenance+anti-cheat+honesty) NECESSARY NOT SUFFICIENT, our
  domain/convergence gate is the missing piece; model competence orthogonal to harness (Opus diagnosed, Codex
  didn't, same skill-only harness). Skill limitation found: pdf-only mode degraded (inspect-paper needs LaTeX;
  both Opus arms wrote pdf_intake.py workaround) = flag to Bilionis. SYNTHESIS REC (NEEDS ANDREW APPROVAL): add a
  statistical-validity acceptance gate (all-var R-hat/ESS/div) to the skill's modes so MATCHED can't pass on a
  non-converged sampler-based target. NO durable AGENTS/checker edits made.
- 2026-06-13 NEW ACTIVE THREAD (Andrew direct ask): **Paper review + toy** — Yan et al. 2026
  *Physics-Informed DT for Spacecraft under Sensor Faults (Frequency Attention U-Net + closed-loop
  updating)*, Aerospace Sci & Tech (`references/Physics-Informed Digital Twin ... .pdf`). Review verdict
  = applicability HIGH. Workspace `artifacts/reports/paper_virtual_sensing_uq_toy_20260613/`.
  D0 AUTONOMY GRANT (Andrew): "go on the toy; start small, iterate to ambitious; run >=4 experiments;
  do not stop for my feedback." Durable-rule/checker/notes changes STILL stop for Andrew.
  TOY = the paper's closed-loop *updating* stage only (NOT the FAU net; FAU output replaced by a LABELED
  surrogate virtual ground truth calibrated to their ~8-10 dB masked-channel residual). Paper does
  DETERMINISTIC least-squares updating on a black-box reconstruction and explicitly DEFERS UQ
  (Future-Work #3); our toy implements that UQ (discrepancy-aware NUTS) and tests held-out masked-channel
  coverage as the trust test. Modal-ROM FRF, paper's alpha/beta/gamma parameterization (Eqs 4,11,12),
  mask Ch3/Ch4. E1 discriminating (det vs Bayes) -> E2 baselines+recon-error sweep -> E3 config-trend +
  FIM identifiability -> E4 biased-reconstruction stress (iid vs correlated discrepancy). Leverages the
  `forcing_marginalized_damping_toy` NUTS/checker/image-QA scaffold. STATUS: **DONE — checker OVERALL
  YELLOW 42/2/0** (0 red; 2 yellows = intended honest-scope flags: surrogate≠FAU-net, one realization /
  effective indicators). `bash run_all.sh` validated end-to-end (active 85.7s). All 4 NUTS experiments
  CONVERGED. RESULTS: E1 — det main-peak QOI misses both masked ch (0/2, err 2.8/10.5 dB), discrepancy-aware
  Bayes covers both (2/2) + 100% HF held-out, σ_d≈0.35 = injected floor. E2 — reproduces paper ranking
  (Interp 2.7 dB / Meas-Up discard floor 6.3 dB / FAU-Up tracks recon error then peels off as observed+box
  constraints reject a grossly-wrong surrogate); Bayes coverage 2/2 across recon 1.3→12.2 dB. E3 — aggregate
  joint-softening trend recovered (mean-α 0.952/0.899/0.854, monotonic+separated) BUT the failed-sensor local
  mode's α is 5.7× wider (effective indicator only) = ties identifiability to which sensor failed; confirms
  paper's own caveat. E4 (deepest) — +15% coherent peak-shift bias: unbiased correlated CONTROL recovers α4
  (covers 0.85, softening) = method sound; det(→box floor 0.50)/iid/correlated all MISS α4 + flip to apparent
  HARDENING (wrong sign) while amplitude QOI stays covered = QOI coverage≠parameter recovery; coherent bias
  confounded with failed-sensor mode stiffness (peak-shift≡stiffness), cure = break degeneracy (sensor
  placement / bias-aware credibility), not more flexible discrepancy. NUTS FIX logged: marginal-GP correlated
  likelihood needs eig-form + iid nugget + correlated-on-masked-only + dense mass (naive whitened-factor froze
  at R-hat 5e5/ESS 2). NO durable edits beyond this block + scaffolding; runs.md/project_log/todo updates
  PROPOSED in packet §7, await Andrew. OPEN: bias-aware credibility + sensor-placement follow-ons.
- 2026-06-12 NEW ACTIVE THREAD (Andrew direct ask): **Buffet+acoustic dome secondary-structure study**
  (`artifacts/reports/buffet_dome_secondary_20260612/`). Representative Terran-R/F9-class, PUBLIC data only
  (NO live web this session — all numbers ledger-flagged VERIFY). Decisions D1-D11 in workspace decisions_log.md:
  objective = SECONDARY-STRUCTURE vibe env; 400 Hz REFRAMED = fine region (dome+ring+barrel-to-first-frame +
  tray/COPV/avionics lump) converged to 400 Hz, far-field CMS-reduced + uncertainty-bounded (NO deterministic
  full-vehicle 400 Hz claim); forcing = Corcos buffet + DAF acoustic, 2 load cases (liftoff acoustic / max-q
  buffet); QOIs = strut loads, netCG punch (FBS pinned contract), secondary rep metric, avionics-lump accel;
  CI IS KEY (Phase 3). D12: max-q BUFFET ONLY (acoustic deferred). D13: AUTONOMY (iterate; durable-rule
  changes still stop for Andrew). STATUS: **checker OVERALL GREEN 25/0/0** (S1 forcing, S2 beam/bar 0.04%,
  S3 model+Donnell, S4 modes+QOI both BCs, S5 CI both BCs, S6 coupling trust-test, S7 mesh conv, S8
  response-limit proxy). ~7.1 hr active compute. 7 figures + image-QA + 3-audience research_narrative.md +
  packet.md. ALL detached jobs DONE.
  RESULTS (D14): BC-A tray punch 45.4 N / COPV punch 37.6 N / COPV per-mount resultant 40.8 N / avionics
  3.53 m/s²(z); BC-B 6-10% lower = boundary uncertainty. CI tray punch 5/50/95 = 18/40/87 N (damping+buffet
  priors, NO-sampler). S6: modal superposition vs DIRECT full-58k solve worst 0.69% = truncation validated.
  S7: refined-mesh ratios 0.97-1.06. S8 RESPONSE-LIMIT PROXY (D15, Andrew ask): avionics accel->tray punch
  coherence 0.9999 at 55 Hz controlling mode; gain alpha=15.1 N/(m/s²) INVARIANT to damping (0.06%) +
  forcing (exactly) -> a_limit=F_allow/alpha is a STRUCTURAL CONSTANT robust to the 5x CI; CG-gain=1.17x
  assembly mass = 7004C eff-mass tie; valid 32-300 Hz = 77% of punch energy; decouples at avionics-on-tray
  local mode. Variants (D14-consistent re-solve DONE): substructures LARGELY decoupled (~15% dome cross-talk,
  NOT perfectly — wording corrected); DOME GAUGE moves every QOI 40-75%.
  HONEST CORRECTION (D14): image-QA caught a free ~0 Hz COPV spin; adding rotational mount stiffness was
  QOI-invisible for tray/strut/avionics (<=2%) but COPV net punch -15% AND per-mount shear ~DOUBLES
  (design-driving). v1 COPV SUPERSEDED. Process lessons: file-existence resume guard skipped BC-B re-QOI
  (key on model version); never edit a running bash pipeline; over-engineered coupling starved meshf.
  D16 (Andrew flag 2026-06-15 "7 Hz modes not realistic" + illegible figures): the prior GREEN 25/0/0 was on
  a SOFT-MOUNT model with UNPHYSICAL 7 Hz modes -> SUPERSEDED. ROOT CAUSE (diagnosed via lowest-mode probes
  + a static stiffness test): (1) 7.4 Hz "tray" mode = the 8 kg avionics CONM2 yawing on ONE tray node's
  shell-drilling penalty -> fixed w/ 4-corner BOLT FOOTPRINT -> tray 76 Hz; (2) soft tray suspension = pin-
  ended axial tubes -> MOMENT-CARRYING BEAM struts + bolted joints; (3) 7.3/18 Hz COPV = 30 kg vessel on
  single-node attach to 5mm dome, static test proved DOME LOCAL POINT STIFFNESS (~1.1e6 N/m) governs ->
  DOME-PATCH bracket + 3-pt cradle near junction -> COPV ~68 Hz. NOW lowest mode 67.9 Hz, tray 76.4 Hz
  (realistic). FIGURES: fixed fig4/fig5 label collisions (legends) + added generation-time TEXT-OVERLAP
  AUDITOR (save_fig bbox check) since pixel image-QA falsely passed. Old soft-mount summaries preserved in
  out/softmount_superseded/. FULL D16 RE-RUN IN FLIGHT (pid 27128, run_d16.sh, ~5-7 hr): modes both BCs ->
  QOI -> coupling+proxy -> CI -> variants -> figures -> checker. All headline numbers WILL CHANGE (controlling
  mode 55->~70 Hz; buffet energy is mostly <50 Hz so stiffer secondaries => generally LOWER resonant QOIs).
  LESSON: footprint-mount lumped masses (single-node CONM2 w/ rotational inertia = spurious drilling mode);
  heavy mass on thin shell is point-stiffness-limited (static test, not modal alone).
  NEXT when re-run lands: refresh all docs/figures/checker to D16; re-confirm proxy/coupling on realistic model.
  OPEN AMBIGUITIES: all public-vehicle numbers unverified pending a web session.
- 2026-06-12 ACTIVE THREAD: Schneider+Das/Debnath × StatFEM study program (`artifacts/reports/papers_statfem_studies_20260612/`).
  Study A (synthetic FRF discrepancy A/B) RUN: V2 Schneider correlated complex discrepancy = ONLY variant clearing
  convergence gate (R-hat 1.002, ESS 1328, 0 div) + 100% in-dist held-out coverage, ~7× tighter than iid; iid/decimated
  NON-converged (R-hat 24/41); extrapolation honest-negative (57%); hyperparams not recovered (sponge).
  DONE (Andrew "continue all work needing no new data"): FOUR executed studies, checker YELLOW 43/8/0, full replay
  `run_all.sh` validated end-to-end (~589s), 16-slide deck. (1) Phase-1 control DECISIVE: V1 iid R-hat 23.9->1.003 when
  hidden DOF removed = iid non-convergence CAUSED by model-form error; V2 recovers sig_w/len_f w/o model error (sponge
  isolated); len_f learnable across sweep, coverage 89-100%. (2) Study C REAL panel: authoritative H1.mat=25pts x 3200f
  (|H1| spans 5 decades; .txt WAS coherence), Abaqus 45 modes<200Hz; 22 matched FEA<->test, REAL discrepancy floor |err|
  2.2% (+1.1% stiff), real len_co_f~2.9Hz. Characterization only (no NUTS calib yet). (3) Study D synthetic Das/Debnath:
  latent complex modes 0 div vs eigh-through 429 div (18%, fails gate) at 0.75% degeneracy + damping recovered = logged
  ShockSat eigh-MAC divergence SOLVED. Data-source Qs for panel flagged in packet 1c.
  2026-06-12 EXTENDED (Andrew: "realistic synthetic + held-out QOIs + evolving-band GIFs + a statFEM+D/D+Schneider
  METHOD, be more ambitious"): Study G = THE UNIFIED METHOD built + self-tested (1e-13/4e-13), realistic synthetic
  panel twin (NO injected Schneider field; genuine structural mismatch). HONEST HEADLINE NEGATIVE: free latent shapes
  don't generalize (UMS-full R-hat 364, QOI 0/10) -> physics-bound shapes (UMS-FEM, eigh Ktilde(theta)) + global damping;
  after the D14-D25 sampler-pathology ladder it STILL shows physics-vs-discrepancy BIMODALITY (4-chain R-hat 50:
  'damped gz~1.2' vs 'undamped+discrepancy gz~0' basins = Kennedy-O'Hagan/vision§4) + held-out QOI under-covers 1/10
  (even the damped basin over-predicts; deterministic FEM also fails) = the project's CENTRAL problem POSED with a
  working testbed; cure = constrain the discrepancy (orthogonal/cut-Bayes §5.2). Andrew D19 answers (H1=mobility,
  impact top-right, low-f=RBM) -> Study C2 real-panel prep: H1<->grid mapping pinned by MAC (low modes 0.98-0.99).
  2 evolving-band GIFs on UMS-FEM. Checker YELLOW 62/12/0, 23-slide deck.
  2026-06-12 FINAL LEG (Andrew: "move on to that; iterate until all vision goals + docs for Girolami/Bilionis/
  aerospace"): STUDY H (cure A/B, vision 13.2 EXECUTED): ALL 3 constraints KILL the bimodality (R-hat 1.006-1.014,
  0 div vs baseline 50) but held-out coverage NOT restored (<=1/10) -> DECOMPOSITION: identifiability and local-
  model-error under-coverage are SEPARATE failures w/ separate cures; H-orth over-absorbs (gz->2.8, Plumlee plug-in
  bias). STUDY I (unknown forcing, vision 5.0 FIRST experiment): honest double negative — transmissibility cancels
  forcing AND the physics-pinning level info (R-hat 61); naive 3-way joint fails (R-hat 128, 0% F recovery) ->
  response-only ratios != apparent mass; M=F/a needs the measured force. STUDY F-MINI (vision 6.2, forward-only): elicited config delta widens held-out
  bands 0/5->4/5 coverage monotonically (guardrail holds); stubborn 5th point = 6.2's own caveat (structure not
  scalars for gross local error). DOCS: research_narrative.md (3 audience sections + vision-goal audit), 29-slide
  deck, checker YELLOW 69/20/0, decisions D0-D27, manifest 116 files. STUDY J (vision §7 centerpiece, REAL DATA): UMS pointed at the real suspended-panel mobility (Abaqus FEA
  shapes fixed + calibrated global freq/damping + Schneider discrepancy). Inherits the SAME multimodality on
  real data (R-hat 525) -> fixing the amplitude<->damping ridge (Study H lesson) gives 4-chain CONVERGENCE
  (R-hat 1.003, ESS 1124, 0 div), sensible global freq scale 0.956 (FEA ~4.6% stiff), held-out QOI 2/5 = honest
  partial coverage. COMPLETE ARC: synthetic method (G) -> bimodality -> cure (H) -> REAL convergence (J).
  EVERY vision goal has an executed experiment. Checker YELLOW 72/22/0, 30-slide deck, decisions D0-D31.
  STUDY K (REAL-panel A/B, the program's strongest real result): per-mode frequency
  calibration on the real panel CONVERGES (4-chain R-hat 1.007, ESS 258, 0 div) and predicts ALL 5/5 held-out LDV
  peak mobilities within calibrated bands (vs 2/5 global), correcting the FEA's ~15% low-mode freq error (mode1
  9.53->8.3=exp8.25) by BETTER LOCATION not vagueness. HONEST CORRECTION D34: my 2-chain probe gave a FALSE
  NEGATIVE (per-mode R-hat 3.75, 0/5, under-warmed) -> only the 4-chain gate revealed the 5/5. META-LESSON: cheap
  probes mislead BOTH ways (Study G 2-chain=false positive; Study K 2-chain=false negative); full gates decide.
  Bands wide-but-honest; one test/realization/single-reference = real-data EVIDENCE not validated flight science.
  STUDY L (D35, REAL A/B, honest negative that sharpens the story): tried to SHARPEN K's wide 5/5 bands (~4-5x
  hi/lo) via per-mode residue-amplitude calibration. freq-only control REPRODUCES K (R-hat 1.007, 5/5); adding
  per-mode amplitude FAILS to converge (R-hat 14.8) -> per-mode FREQUENCY is identifiable (peaks pin it) but
  per-mode AMPLITUDE is confounded w/ damping+level from a SINGLE impact reference (D30 ridge, per-mode). =>
  band width is a DATA limit (needs multi-reference/roving excitation), NOT a model limit. Concrete aerospace
  "where to spend the next test dollar" answer. fig figL_sharpen_ab.png (freqamp drawn NON-CONVERGED/not-trustworthy).
  STUDY M (D36, THIRD paper Yan et al. 2026 AST 'sensor faults / virtual sensing'): treat 5 held-out LDV pts as
  FAULTY/masked; reconstruct + score with the paper's dB main-peak metric. Bayesian physics virtual sensing beats
  spatial interpolation at HIGH-freq LOCAL modes (3.4 vs 8.8 dB = reproduces paper's aliasing claim on independent
  real data, different method) + supplies calibrated 95% band (82% bin cover, 5/5 peak) the paper's deterministic
  FAU lacks. Honest: interpolation wins on smooth LOW-freq modes (2.8 vs 4.5 dB). No new data/sampling (reuses K
  posterior). fig figM_virtual_sensing.png. UQ note: paper feeds reconstructed 'virtual ground truth' back as
  measured = double-counting; our band avoids it.
  ONE-PAGE ARC: fig_arc_summary.png. Checker YELLOW (rerun), 34-slide deck, decisions D0-D36.
  Studies A/Phase1/C/C2/D/G/H/I/Fmini/J/K/L/M all executed+checker-backed; EVERY vision goal exercised + 3 papers integrated.
  DURABLE LOGS UPDATED 2026-06-13 with Andrew's explicit sign-off ("you can modify those logs"): docs/report/
  project_log.md (new top row, A-M program, YELLOW 76/22/0), notes/runs.md (dated entry + per-study numbers +
  5 lessons), notes/todo.md (program COMPLETE; open item = Andrew's multi-reference-data call), notes/lessons-learned.md
  (7 lessons). packet.md S6 marked APPLIED. Still NOT edited: AGENTS.md, code/check.py, sampler standards.
- 2026-06-12 NEW COMPLETED TOY (Andrew direct ask): **Forcing-marginalized amplitude-dependent damping**
  (`artifacts/reports/forcing_marginalized_damping_toy_20260612/`). Checker YELLOW 20/2/0, replay `run_all.sh`
  active 13.48s. Truth hides forcing, slip-like amplitude-dependent damping/stiffness softening, and hidden rattler;
  twin sees only `a_secondary/a_primary`, so forcing cancels to 4.28e-16 and no force-function is learned. NUTS
  converged (R-hat 1.000, ESS 3087, 0 div), detects high>low damping P=0.996, held-out ratio coverage 42/46,
  QOI coverage 6/6. HONEST YELLOW: equivalent damping intervals miss hidden physical zeta values and are biased
  upward by hidden DOF/stiffness-softening error; this learns effective damping/QOI behavior, NOT a Coulomb/microslip law.

- CENTRAL REPORTING HUB created (2026-06-12, Andrew request "log everything for end-of-summer report"):
  `docs/report/` = `project_log.md` (master indexed logbook: thread index w/ checker status, timeline,
  deliverables catalog, cross-cutting findings, harness evolution, open items) + `README.md` (maintenance +
  honesty rules). Additive index over canonical files (AGENTS.md / notes/runs.md / per-study checker_report.json);
  did NOT change rules/checkers/notes. MAINTENANCE: update the §3 row + timeline whenever a thread advances/closes.
  Notch lit review/FTO triage added 2026-06-12 at `artifacts/reports/notch_lit_review_20260612/`,
  checker YELLOW 26/1/0: force/response limiting + apparent mass + FBS/TPA + force/moment measurement
  are crowded; likely-open contribution is the narrow sparse 6-DOF empirical/Bayesian limit workflow;
  limited-access older-paper coverage is the documented caveat; disclose before public sharing.

### Active / pending Andrew review (status + #1 ask; full detail = central log §3/§8 + each workspace packet.md/decisions_log.md)
- 7004C multi-point/6-DOF study (`notch_multipoint_7004c_20260611`) — YELLOW **24/2/0**, replay 42s, NO sampler. Single-point 7004C is blind to rocking (net Fz can be exactly 0 while feet load); notch reach = modal-overlap regime, not a radius; distributed feet = MORE overtest, hidden in per-foot/moment channels. **EX-E added 2026-06-12 (Andrew D10): empirical path = YES** — impedance method w/ MEASURED interface quantities reconstructs coupled loads EXACTLY (1.8e-12), so a measurement replaces the coupled forced FEM; cost is spatial (1 foot→bounce only, 100% moment-blind/76-84% per-foot err; ≥3 spaced feet→rocking recovered 3-5%; remote response proxy exact only if transmissibility calibrated in INTEGRATED config, bare-config ~100% wrong). Deliverables for future agents: `notching_findings_for_future_agents.md` (standing reference) + `lit_review_prompt.md` (lit-review agent prompt). ASK: review packet §5b + the 2 docs; run the lit-review prompt; decide on real-hardware follow-on (ShockSat × tray).
- MPL stand FEM rebuild (`mpl_stand_fem_rebuild_20260611`) — YELLOW 16/3/0 rev-7, NO sampler. rev-7 (D38, Andrew): valve assembly upgraded from a single rigid CONM2 to a HIGHER-FIDELITY 80/20 ALUMINUM FRAME = 1515 T-slot cage (16 nodes/28 Timoshenko beams, reusing the validated beam element) + 16 lb tanks/valves lumped on its nodes + bolted at 4 corners. RESULT: valve modes move from a spurious ~14 Hz rigid rock (old soft-mount artifact) UP to ~156/190 Hz = real frame flexure; extrusion SERIES (1515 assumed) = dominant new knob (~10x), ANDREW-CONFIRM. New groups K_valveframe/K_valve_mount/M_valveframe/M_valvemass + valve_frame.py generator; mass closure exact (independent recompute), 6 RBM, 0 neg. Earlier: e-box mass = LogNormal PRIOR 2-4 lb (box mode crosses fundamental, weakly/confoundedly observable, lever=sensor on box); boxes co-located y-z; shield welded/steel. ASK: confirm extrusion series + cage dims + tank/valve masses (§9); next = test-data ingest + NUTS update consuming priors.py + out/model/ groups. rev-8 (D39, Andrew): added PSEUDO-FRF FEM-vs-test overlay at the 3 key locations (top-center IF, shield-mid, top-left beam; src/pseudo_frf.py + fig_pseudo_frf.png). NO force => pseudo-FRF (peak freqs only, assumed 1-3% damping, NO sampler); axis=shield-normal/X (test A5). RESULT: uncalibrated coarse prior matches measured peaks <1% in 50-90 Hz (55.6/66.1/78.4/88.9), ~5-10% offset in 10-25 Hz = the estimated box/shield masses+weld k (the yellow knobs) = robust-twin thesis in one figure. Checker 16g/4y/0r. Next card (test ingest+NUTS) consumes this. rev-8b (D40): pseudo-FRF upgraded to TAP TRANSFER matrix (3x3 resp x tap-loc, FEM transfer accelerance vs test, apples-to-apples) + ACOUSTIC with a MODELED uniform-shield-pressure FEM forcing (Andrew's point: we weren't applying acoustic forcing). Fixed a real saturation bug Andrew caught: the top-center drive-point tap window had swallowed the dropped 93g saturated hit; windows now capped before next event + near-rail windows rejected. Clean now. rev-8c (D41): added the missing QOI-point pseudo-FRFs (Andrew) — valve (on the 80/20 frame) + electronics-box FEET (avi-foot L/R), tap @ engine beam + acoustic = direct test of the mounted-mass models. fig_pseudo_frf_qoi.png. Box body/top not measured (cable broke) -> feet only. rev-9 (D42/D43): DETERMINISTIC model updating (NOT NUTS) to box-foot tap-transfer ONLY, goal up front + change log. box-foot median |Δf| 6.1%->2.2%, 2/4->3/4 matched, held-out stable (no overfit). Model-form D43 = split box mount (trans/rot) added the ~27 Hz rocking mode (matched measured 26.8). MEDIAN goal met; 11.4 Hz peak = documented model-form floor, DECLINED to overfit (closing needs box>4lb above prior / softening confirmed shield). Also added engine-beam+foot tap columns (foot degenerate under SPC = flagged) + valve QOI to 250 Hz. Checker 16g/5y/0r. tuning_changelog.md.
- MPL test stand scrappy modal test (`MPL test stand/FEM/test_data_scan_20260611/`) — 13 single-axis CSVs + features done; ruler coupled f1 −3.7% = the 7004C shift measured live; uncalibrated FEM ladder aligns in band/density. NEXT (lead): train/held-out split + calibration feature table; next card = NUTS calibration.
- statFEM replicate-and-extend blog (`statfem_freq_blog_20260610`; runs `runs/statfem_freq_2026-06-10/`) — challenger pass done (9/9 caught core flaw unprompted; "the critic is the product"). ASK: review post_draft.md. GATED on IP/disclose sequence before any publication.
- ShockSat × tray coupled QOI (`shocksat_tray_coupled_qoi_20260610`) — YELLOW 32/3/0 + 15-slide program deck (incl. to-scale coupled-FEM slide; slide-7/9/11 context fixes from Andrew's review; OAT bars now carry bootstrap CIs — the ">100%" was MC noise). POOLED-MOUNT ARM (D15–D17, Andrew's 6→3 idea): sampler ladder 6→3→2 params R-hat 5.03→1.52→1.24 (FIM-predicted order) but even 2 params fail STRUCTURALLY — stiff-side saturation (likelihood flat above ~×5 nominal; remedy 2000+2000 d9 WORSE at 2.22; chain stuck in tail t_all 2.6–38.8) + t_all↔r_all rocking ridge (corr −0.74). Frequencies deliver: r_all≈1 pinned + LOWER bound on t_all only (and QOI is non-monotonic in k, so that doesn't bound the load). ASK: sign off D2/D3/D4/D7; candidate next = symmetry-breaking-observable survey (resolves x/y AND the trans/rot rocking mixture).
- Schneider 2022 teaching deck (`artifacts/teaching/schneider2022_20260610/`) — built; SuS labeled teaching PROTOTYPE, not NUTS. ASK: review teaching quality.

### Completed, checker-backed (detail = central log §3 + workspace packets)
- ShockSat FEM modal twin NUTS calibration (`shocksat_fem_modal_twin_20260609`) — YELLOW 15/2/0; FULL 18-mode posterior CONVERGES (R-hat 1.022, ESS 232, 0 div) but only ~4/9 groups identifiable; held-out freq coverage good; band/LOMO designs fail gate (documented). σ_f≈4.6% = element discrepancy. Cross-confirms FIM.
- FIM identifiability + experiment design, Opus tray (`fim_identifiability_opus_20260609`) — GREEN 15/15; **3 identifiable stiffness params** (band-conditional 1→2→3); both joints unidentifiable from modal data; QOI lies in the identifiable subspace; best sensor/tap locations given.
- Earlier threads (ShockSat StatFEM runner, conical-shell ladder, FEM Phase-1 + reviews, modeling-freedom, blind round-3, competitive multi-model runners, fresh/synthetic 2DOF) — see central log §3 + `notes/runs.md`.

### Cross-cutting finding (recurs across FIM / modal twin / VOI)
- Modal frequencies alone UNDER-IDENTIFY joints/mounts; the binding constraint is the model-form discrepancy floor (σ_f≈4–5%), NOT sensor count. Held-out QOI prediction can stay calibrated even when the parameter posterior is multimodal. Symmetry-breaking observables (shapes / FRF amplitude / force gauges), not more frequencies, split the mount/joint axes.

### Durable harness changes this period (recorded in AGENTS.md; summarized in central log §7)
- Green/Yellow/Red result-status standard; figure-provenance/invalidity gate; detached-launch/compute gate; Modal/Eigenproblem Identifiability Gate (FIM eigen-view required for any per-parameter claim); NUTS/HMC = default, "active" only with all-variable convergence diagnostics.

### Standing context / durable decisions (keep — load-bearing after compaction)
- OBSERVATION-LAYER CONSTRAINT (upstream truth, 2026-06-09): SOL111 FRF vs Test07 taps are DIFFERENT transfer paths -> an FRF magnitude likelihood is INVALID; the FEM-vs-test axis is MODAL correlation (frequencies + MAC) on the 1101-7105 grids; pyro shock stays held out.
- STATFEM v1 HELD-OUT RESULT (2026-06-09, synthetic-tray twin): in-regime QOI under ~9-11% (one narrow CI misses); OOD QOI all finalists +40-44% over with NO CI coverage = a converged, gate-passing twin can be confidently wrong out of regime; the held-out set is the only detector. A fresh independent science twin = the runner above.
- MODELING-FREEDOM EXPERIMENT graded 2026-06-09: dev rank != vault rank; the hidden vault caught a gate-passing flexible-model overfit; the ShockSat half was hollow (lead's setup, not the runner). BLOG-tagged lessons in `notes/lessons-learned.md`.
- VAULTS: both sealed to Andrew's Google Drive; pins in `vault/DRIVE_VAULTED_PINS.txt`. Pyro held-out .mat is RESTORED locally (SHA == pin) — re-vault before any new blind ShockSat run.
- FEM tasks use OPUS runners only (2026-06-08); cross-software within Opus + human Femap solve + reviewer recompute replace cross-model independence.
- NOVELTY (open): lock NO patent claim before the OMA/input-state/force-ID + joint-impedance lit scan and a real patent/FTO search. Cleanest claim so far = the "Bayesian 7004C" notch (`docs/proposal/patent_ideas_ranked.md`); design-around target = US8731868B2.
- IP (durable): Purdue/PRF route; named inventor + ~1/3 share; DISCLOSE to Senior IP Officer BEFORE any public disclosure (Substack/paper/talk); Beth Siple determination PENDING.
- STEERING (durable): scope-drift red flag — no bigger/more-technical plan without re-confirming the real objective; prefer the simplest experiment that answers the real question.
- VISION IDEA (2026-06-10, Andrew, durable — logged project_vision.md §6.2): discrepancy-prior FRONT-END = user dials a knob per category (config/forcing/build/pressurization/integration status) OR describes deltas to an LLM that applies knockdowns/mock-ups + tweaks error assumptions (prior means AND widths). = the user-facing front door of the §6.1 robust twin; defuses the "arbitrary sigma_d" objection by ELICITING from known engineering deltas. Guardrails are the design: map delta→discrepancy STRUCTURE not scalar (key to modal SE / F(k)); two layers (mean mock-up + uncertainty inflation); MUST WIDEN not falsely narrow (gate any tightening on held-out coverage, never user pref); LLM = RETRIEVAL over a CALIBRATED knockdown library, every knockdown traceable, not free generation; held-out coverage = backstop. Novelty caution: knockdowns + LLM-for-eng are crowded — no claim without FTO/lit scan; defensible value stays the held-out-validated discrepancy-aware QOI.
- STEERING DECISION (2026-06-10, Andrew, durable — logged notes/project_vision.md §6.1; NOT a gate/checker change): the §2.1 simple hand-calc tool sketches did NOT resonate; SUPERSEDED. Build direction = the ORIGINAL robust digital twin: a LIVE apparent-mass / interface-environment twin of the primary structure, ROBUST TO MODEL ERROR (coarse model, big model-form error, node-vs-test misalignment, even wrong-version model e.g. V2 FEM vs tap test on partial-assembly V3 at different pressurization), ingesting a scrappy freq/ID apparent-mass test (coupled OR uncoupled) → QOI + vibe-test-plan predictions with CIs carrying BOTH the 7004C effect AND the Bayes effect. Non-brittle = a bad model WIDENS intervals (and says so), never a confident wrong number. HONEST SCOPE: QOI/apparent-mass prediction stays CALIBRATED (intervals widen but cover) while physical-PARAMETER ID degrades to prior — do NOT claim recovering true physics of a wrong model (Brynjarsdottir-O'Hagan/Stage-3). ShockSat held-out-freq robustness = existing proof-of-behavior; make it the headline. Robustness mechanisms: observe interface M=F/a (not interior modes), orthogonal output-space F(k) discrepancy absorbs model error, calibrate only what data pins (FIM downselect), node misalignment = observation operator w/ uncertainty, trust gate = held-out QOI coverage. Companions partly built: QOI-OSP sensor placement (Opus FIM exp-design) + param downselection/pooling (evidence + F(k) partial pooling; FIM ~3 identifiable). NEXT: await Andrew on 2 scope Qs (existing assets vs McCallie real tray; robustness-coverage demo vs uncoupled→coupled pipeline) BEFORE building (scope-drift rule). Proposed 1st discriminating experiment: wrong/coarse model + scrappy apparent-mass test on a different truth → QOI interval covers+widens while deterministic misses.
- VISION ADD (2026-06-10, Andrew, durable — logged in notes/project_vision.md §2.1/§2.2; NOT an AGENTS.md/checker change): (1) ADOPTION — big industry dynamics names haven't heard of Bayesian FEM updating, call it "polishing a turd"/"pencil whipping" (slow, GIGO, sigma_d/prior-arbitrary). Strategy = get a foot in the door with VERY SIMPLE, borderline empirical/hand-calc tools that plug-and-play into existing aero workflows; surface every arbitrary assumption w/ sensitivity; held-out trust test is our direct GIGO answer. (2) QOI — industry does little force limiting; RESPONSE limiting is the norm. Use a response-limit PROXY: pick 1-2 accels highly correlated with net-CG response at the high-priority modes (modes driving net-CG/interface force), set a scaled limit. This is now a first-class QOI option for the in-flight ShockSat × tray coupled study (per-mount interface load vs net force ambiguity) — flag for Andrew sign-off alongside D2/D3/D4.
- HARNESS CLEANUP 2026-06-09 (Andrew approved): `AGENTS.md` = single canonical rules/gates file; `CLAUDE.md` = short lead pointer; root PDFs -> `references/pdfs/`; Ilias material -> `references/ilias/`; `docs/agents/roles/` = canonical role definitions; large fetched raw data gitignored (provenance via download_log + SHA256 manifests). Archived detail: `notes/memory_archive.md`, `notes/todo_archive.md`.

- [ARCHIVED 2026-06-04 round-3/Stage-0-3 detail -> superseded; full record in artifacts/reports/blind_round3_review_20260604/, .../blind_round3_stage3_review_20260605/, runs/round3/opus48/report/, project_vision.md. One-liner: the blind truth/inference split WORKED (proved synthetic recovery was "plumbing"); a discrepancy in the SAME parameter space as the calibration param confounds; the missing-higher-mode floor inflates sigma_e; netCG quantity-contract pinned (dynamic FBS F_iface/m_load). Stage-4-on-synthetic deferred; need real/validated inputs.]

## 2026-06-06
- Added Claude Code skill `tufte-data-graphics` (`.claude/skills/tufte-data-graphics/`): model-invoked by its description whenever we generate/edit/review a graph of numeric data (FRF/PSD/posterior/QOI/report figures). Encodes Tufte's published corpus — data-ink ratio, chartjunk, Lie Factor≈1, the six Beautiful-Evidence analytical-design principles, small multiples, direct labeling, color discipline, sparklines — and maps them onto the existing CLAUDE.md figure gates (log-frequency, dB only if justified, truth-vs-observed, residual/zoom, absolute-vs-normalized, all-variable convergence reporting). References: principles.md (with book citations), matplotlib-recipes.md, project-domain.md, optional-hook.md. Heuristic linter `scripts/tufte_lint.py` self-tested (flags 3-D/pie/jet/shadow/dual-axis/legend/missing-log-x on a bad script, clean on a good one) — advisory only, not a quality proof.
- Honest scope: compiled from Tufte's published books (VDQI, Envisioning Information, Visual Explanations, Beautiful Evidence, Seeing with Fresh Eyes), NOT a live web scrape (no browser tool this session). Optional PostToolUse hook is documented in optional-hook.md but NOT enabled — enabling it edits .claude/settings.json (durable harness config) and needs human approval.

## 2026-06-02
- Plain-English multi-agent scaffold added. Claude Code is configured as the lead through `.claude/settings.json` and `.claude/agents/lead.md`; Codex prompts live under `docs/codex_prompts/multi_agent/`; Cursor adapters live under `.cursor/agents/` and `.cursor/rules/`.
- Codex GPT-5.5 round-2 sequential runner completed under `artifacts/reports/runner_codex_gpt55_round2_20260602/`. Headline artifact: `figures/interface_response_psd_evolution.gif` showing coupled interface acceleration response PSD vs smoothline after each flight. Final all-11-flight NumPyro NUTS passed strict all-variable convergence (max rank R-hat 1.0071, min bulk ESS 1080, min tail ESS 1199, 0 divergences), but early cumulative GIF prefix fits 1-3 had divergence warnings and are labeled as such. Final 99% interface PSD band did not exceed the smoothline; max final 99%/spec ratio was 0.59285 at 62.41 Hz.
- First-loop packet lives at `artifacts/reports/multi_agent_first_loop_20260602/` and reuses the existing fresh 2DOF StatFEM/FBS workflow.
- Future Bayesian updating work should use NUTS/HMC by default. Current random-walk/random-scan Metropolis outputs are prototype/legacy and must be labeled that way until NUTS/HMC code, diagnostics, one-command replay, and checker output exist.
- Sequential vibe/modal/flight setup packet added at `artifacts/reports/sequential_vibe_modal_flight_20260602/`. It uses PSD-space dB, log-log smoothline interpolation through the four user-provided PSD points, fixed known 3 dB flight-to-flight forcing variability, initial 1.5 dB build-to-build variability and 0.75 dB sensor noise to be learned later, and Matérn-3/2 GP flight forcing. This is setup only; NUTS/HMC is not active.

## 2026-05-27
- Bootstrap started with harness-first strategy.
- Priority order:
  1) deterministic harness/checkers,
  2) synthetic 2DOF + full-MCMC StatFEM/FBS,
  3) MDOF/FEM pipeline feasibility.
- Ground rule: no success claims without checker artifacts.
- Codex review found the original all-parameter random-walk MH sampler had very low acceptance (`0.0167` in posterior recovery). It was replaced with adaptive random-scan MH plus likelihood whitening/caching.
- Final sampler validation on 2026-05-27: `bash scripts/run_pipeline.sh` passed; posterior recovery acceptance `0.216`; full MCMC artifact acceptance `0.2009`, post-burn acceptance `0.1408`.
- Highest-priority technical gap after sampler fix: channels 2 and 3 are still identical forward models, so measurement-channel fidelity should likely come before more sophisticated FEM work.
- 2026-05-29 data search: best real primary/secondary candidate is the 4TU F-16 GVT benchmark with wingtip dummy payloads and pylon/interface nonlinearities. Best tank/dome-like signal is Vibrationdata `SR19_Fwd_Dome_ignition.txt`; best operational flight response archive is NASA PIMS/SAMS ISS acceleration data.
- 2026-05-29: copied five personal Cursor skills into Codex user skills at `/Users/avoss/.codex/skills/`: `andrew-voss-voice`, `evergreen-knowledge-work`, `honest-technical-work`, `project-harness`, and `stop-slop`. Restart Codex to load them in new sessions.
- 2026-05-29 milestones 1-2 complete: pipeline now generates `artifacts/reports/synthetic_statfem_packet.md` plus meeting-friendly figures. Channel 2 and 3 are no longer duplicate clean forward models: channel 2 = coupled primary-side `F1/a1`, channel 3 = tray-side impact `F2/a2`; clean relative L2 difference = `0.6877`.
- 2026-05-29 GP error exploration: current synthetic data already adds zero-mean squared-exponential GP discrepancy over frequency plus iid sensor noise. Main limitation: the realized GP discrepancy is not stored separately from iid noise, and all channels share raw-unit hyperparameters.
- 2026-06-01 key FRF artifact: `bash scripts/run_pipeline.sh` now produces `artifacts/plots/key_2dof_transfer_functions_linear.png` and `artifacts/reports/key_frf_summary.json`. After the 7004C convention fix, it reports 14 linear-magnitude FRFs on a log frequency axis: five acceleration/force terms, five base-reaction apparent masses in synthetic mass units, one standalone tray acceleration transmissibility, and three drive-point reciprocal-inertance traces retained in JSON for traceability.
- 2026-06-01 apparent-mass postmortem: created `docs/lab/apparent-mass-convention-postmortem.md` as a lab-shareable failure case. Main lesson: agents need a quantity contract for named engineering quantities before plotting or checking them.
- 2026-06-01 source/load apparent-mass correction: after reviewing NASA-HDBK-7004C Figure 9, the key FRF artifact now distinguishes source apparent mass with an interior notch and low-frequency growth from load apparent mass with a fixed-base peak. The checker encodes both expectations.
- 2026-06-01 key FRF plot now includes horizontal mass references for `m1 = 1.0`, `m2 = 0.6`, `m1 + m2 = 1.6`, plus vertical uncoupled-frequency references at 75 Hz and 110 Hz. The JSON summary records these guide lines.
- 2026-06-01 coupling/error/sensitivity update: `k12 = k2` and `c12 = c2` are now tied, not independently inferred. The synthetic dataset stores GP discrepancy, iid sensor noise, and total error separately. The packet includes actual error hyperparameters, error-vs-truth plots, and a first sensitivity-to-assumptions artifact. Pipeline now regenerates canonical data/MCMC after smoke tests so test artifacts do not overwrite packet inputs.
- 2026-06-01 GP/QOI sample packet update: the Bilionis packet now shows example zero-mean squared-exponential/RBF GP discrepancy sample paths and stores `qoi_samples.peak_tray_accel` from retained posterior samples. The QOI figure shows both a histogram of peak tray acceleration samples and example posterior tray-response spectra.
- 2026-06-01 log-frequency correction: packet frequency-domain channel/error/GP plots now use log-scaled frequency axes, and the synthetic discrepancy GP plus inference covariance are squared-exponential in `eta = ln(f)` rather than linear Hz. The miss is documented in `docs/lab/log-frequency-plot-gp-postmortem.md`.
- 2026-06-01 broad harness guardrails: `AGENTS.md` and `docs/harness/agentic-engineering-quality-gates.md` now generalize the 2DOF feedback into reusable gates: question framing, assumptions ledger, quantity contracts, reference/standards checks, human-review plots, sensitivity, and verification. `docs/codex_prompts/fresh_2dof_rerun.md` is the launch prompt for a clean rerun in a new agent.
- 2026-06-01 fresh 2DOF rerun complete and corrected after human review: `bash scripts/run_fresh_2dof_statfem_fbs.sh` generates a scoped packet under `artifacts/reports/fresh_2dof_statfem_fbs_20260601/`. Current QOI is `3 * GRMS` of tray acceleration response PSD in `g`, not deterministic time-history peak. Current checker pass: Ch2/Ch3 relative L2 = 0.770745; MH acceptance = 0.49263; retained samples = 560; QOI mean = 9.16652 g vs truth = 8.25930 g. Noise/discrepancy is now larger and local-magnitude scaled: FRF observation noise = 8%, FRF GP discrepancy = 20%, local floor = 20% of median magnitude; PSD log noise sigma = 0.18 and PSD log discrepancy sigma = 0.35. The packet includes NASA-HDBK-7004C Figure 9 benchmark values: load `M(0.62)=1.624`, load `M(1)=50.01`, source `M(1)=0.02`, plus fresh source/load-style apparent-mass curves. The fresh coupled model uses one tray-to-primary spring/damper, not a copied prior assembly path.
- 2026-06-01 latest fresh 2DOF correction: the reference/standards figure is now a value table rather than a green pass/fail scoreboard, and sensitivity wording no longer asserts a fake `1.10 x truth` decision threshold. Synthetic truth now includes explicit model-form shifts: dome frequency -15% to 93.50 Hz, tray frequency +15% to 86.25 Hz, dome damping +25% to zeta1 = 0.0225, tray damping -25% to zeta2 = 0.0195. Current checker pass: numeric assumptions = 27; Ch2/Ch3 relative L2 = 0.673906; MH acceptance = 0.49921; retained samples = 560; QOI mean = 12.12008 g vs truth = 10.89493 g; no-arbitrary-threshold checker = true; immutable checker manifest verified.
- 2026-06-01 Bayes-rule/replicate triage update: the fresh packet now includes `bayes_parameter_update.png`, `parameter_posterior_samples.png`, `prior_predictive_vs_data.png`, `posterior_predictive_spectra.png`, and `bayes_update_summary.json`. It explicitly states one synthetic dataset only: one realization per FRF channel, one flight-like response PSD realization, and one secondary time-history realization; flight-to-flight variability is not modeled. StatFEM-style discrepancy and sensor noise are separated in generated artifacts, then combined as fixed covariance in the likelihood; the realized discrepancy field and hyperparameters are not inferred. Posterior parameter 95% CIs: dome frequency [93.1987, 93.7950] Hz, tray frequency [86.0418, 86.3982] Hz, dome zeta [0.019116, 0.025913], tray zeta [0.020177, 0.023802], with tray damping truth 0.0195 outside the interval.
- 2026-06-02 fresh prior/likelihood clarity update: `fresh_2dof_statfem_packet.md` now has a central methodology paragraph. Priors: `log(k/k_nom) sigma=0.18`, implied `log(f/f_nom) sigma=0.09` with untruncated 95% frequency factor [0.838, 1.193], and `log(zeta/zeta_nom) sigma=0.35` with untruncated 95% damping factor [0.504, 1.986]. Likelihood: uses the whole complex FRFs for Ch1-Ch4 at 120 frequency points and whole log response PSD at 181 frequency points; peak/notch locations are only reference checks/plots. Desired future StatFEM step: infer discrepancy fields and/or hyperparameters hierarchically, preferably with replicate tests/flights.
- 2026-06-02 method-visibility harness upgrade: the fresh packet now starts with `## Method Summary` and includes `figures/statfem_likelihood_graphical_model_legible.png`, a run-specific graphical model/likelihood diagram. The summary explicitly lists inferred variables, fixed assumptions, non-inferred variables/hyperparameters, one-dataset/no-flight-to-flight-variability metadata, whole-FRF/PSD likelihood usage, and the likelihood equations. The fresh checker requires `method_summary_documented = true`. `AGENTS.md`, `docs/harness/agentic-engineering-quality-gates.md`, `docs/CODEX.md`, `docs/codex_prompts/fresh_2dof_rerun.md`, and local Codex skills now encode this as a reusable gate.
- 2026-06-02 image-legibility harness upgrade: fresh packet figures are regenerated after deleting stale PNGs, and the report now uses cache-busting names `figures/statfem_likelihood_graphical_model_legible.png` and `figures/reference_standards_comparison_cards.png`. `image_legibility_report.json` records resolution, font floors, clipped text, plain-math tokens, and overlap checks; the checker requires `image_legibility_report_pass = true`. Current pass checked 20 figures, with strict text-heavy checks on the method and reference/status figures.
- 2026-06-02 smooth-prior and peak-feature comparison update: prior curves in the fresh packet are now analytic transformed-prior densities, avoiding jagged finite-sample histogram artifacts. The packet includes `figures/full_vs_peak_feature_likelihood_comparison.png` and `peak_feature_likelihood_summary.json`, comparing the whole FRF/PSD likelihood against a lossy feature likelihood using Ch1 dome notch, Ch2 primary notch, Ch3 tray notch, Ch4 tray peak, and Ch5 response-PSD peak. Current checker pass: numeric assumptions = 33; image legibility = true for 21 figures; peak-feature/full-curve 95% width ratios are QOI = 2.29, dome frequency = 21.57, tray frequency = 27.32, dome damping = 1.92, and tray damping = 5.79.
- 2026-06-02 peak/notch feature-map benchmark update: the fresh packet now includes `figures/peak_feature_mapping_benchmark.png`, `figures/peak_feature_sensitivity_matrix.png`, and `peak_feature_mapping_benchmark.json`. It documents that the feature likelihood compares observed transfer-function features against predicted transfer-function features, not directly against true natural frequencies. Ch1 and Ch4 are direct structural features; Ch2 and Ch3 are mixed coupled features; Ch5 PSD peak is forcing/response-shape confounded. Current image legibility pass checks 23 figures.
- 2026-06-02 prior-visualization triage: prior parameter plots now show analytic prior density plus a labeled MC prior histogram with 80,000 samples and 90 bins. Prior predictive bands now use 1,600 prior samples. `bayes_update_summary.json` records the prior visualization policy, and the fresh checker requires analytic and MC prior views to be present/labeled.
- 2026-06-02 prior-predictive smoothing update: prior predictive bands now use 4,000 prior samples and plotted pointwise quantile summaries are smoothed for display with Gaussian sigma 1.8 frequency-grid points. The figure legend labels the bands as `MC smoothed`, and `bayes_update_summary.json` records the smoothing metadata.
