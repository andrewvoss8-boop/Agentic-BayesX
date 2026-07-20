# Decisions log — ShockSat FULL-SPECTRUM FRF study (20260714)

Append-only. Every human clarification or non-obvious decision that changes an action goes here BEFORE
continuing.

## D20 — Formulation-calibration runner card drafted (2026-07-20)
- `docs/lab/shocksat_formulation_calibration_runner_prompt.md`: the pilot's earned follow-up. Structure:
  F0 physical-plausibility gate FIRST (mechanism from references + real construction of PIDs 601/401/302 +
  discriminating control-region check; verdict PLAUSIBLE/EFFECTIVE-PROXY/UNPHYSICAL decides deliverability,
  written before any calibration score, checker-ordered); then deliberate ≤12-dim per-region
  br_scale/ts_t (+optional geometry) calibration, exact-basis-only scoring, per-fold provenance, NUTS
  honestly attempted on the small space (full gate; MAP fallback labeled), controls = A1 + mr2_elem5-as-is
  + random-prior draws. Bars F1 (≥+0.05 AND ≥2×SE vs A1, the never-cleared S1-class bar), F2 (beats the
  lucky draw), F3 (survives per-fold refits). VAULT default NOT read; Andrew may tick a one-read option at
  dispatch (would be the 4th program read).
- Andrew still owes two decisions flagged in the lead review: (a) vault option for this card; (b) whether
  to adopt Card B's honest widened normal-Z band (2.958×) or keep delivered 2.526× with the caveat; plus
  the formal retirement of the agentic-remodeling search thread in the project log.

## D19 — Lead review of cards A/B/C: all three ACCEPTED; two more corrections to THIS study's record (2026-07-20)
- Spot-verified load-bearing numbers of all three cards independently (28/28 rerank + S2(b) recomputed;
  N0 reproduction; pilot HQ verdicts). All reproduce. Card checkers GREEN = conduct only; science verdicts
  as stated in their findings.
- ACCEPTED corrections to this study (beyond D17): (1) Card A found a SECOND arm-C defect the review missed
  — rescore_freeze applied θ=1-basis shape coefficients on the enriched basis (silent broadcast, −0.085)
  nearly cancelling the leak (+0.082); the study's 0.1570 was right by accident. Honest C-exact = 0.1595;
  "C collapses on the exact basis" is WRONG — C's lead was basis-robust (+0.044→+0.046); S1 fails on
  PRECISION (drive-dependent folds −0.034…+0.132), not collapse. (2) Card A downgrades D15's mechanism:
  screening-vs-exact inflation is small (+0.005..+0.009 mean, both tracks; random's LARGER) → "reduced-basis
  inflation stole the agent's lead" was too strong; it was selection noise on a small field; screening did
  mis-crown the agent winner (1st→5th). (3) Card B overturns this study's C5 CAVEAT attribution: the QOI
  reproduction failure was a QUANTITY-CONTRACT divergence (band_width_ratio = envelope ratio ≠ netcg's
  width-normalized-by-FEM+6dB; 1.508 vs 21.66 on identical arrays), not "marginal calibration"; plus the
  study's single-θ band structurally omitted the θ-spread term that carries +0.35..+1.11 of delivered width.
- CONSOLIDATED program verdicts after A/B/C: S1 NOT MET (best D +0.0497 vs 0.05 — by 0.0003); S2 NOT MET
  (both conventions; and 3rd-time agent≤random in the pilot with genuine model-form freedom → the impotence
  is the GUIDANCE, not the action space); S4 FALSIFIED on the pre-registered path (measured 254.3 Hz cluster
  amplitude scatter SD 1.393 > assumed 0.80 → normal-Z widens 2.526→2.958; delivered twin stands, mildly
  optimistic); S3 CANNOT-VERIFY-through-mapping (near-degenerate clusters make per-mode participation
  non-invariant); S5 NOT MET at declared prior (fragile). NEW POSITIVE (pilot HQ2): all four genuine
  model-form classes beat A1 ≥2×SE at best; a ZERO-DOF bending-formulation edit (mr2_elem5, RANDOM draw)
  is the best single edit ever (+0.1848; +0.1954 under per-fold amplitude refits, the ONLY refit-robust
  finalist). The sub-200 wall still stands (0.185 << 0.34 << 0.70).

## D18 — Three post-review runner cards drafted for Andrew to dispatch (2026-07-16)
- Card A `docs/lab/shocksat_exact_completion_runner_prompt.md`: arm-C per-fold exact refits (no cross-fold
  MAP reuse), exact re-rank of ALL 28 loop candidates (S2 under both selection conventions), corrected
  verdicts_final + figures with finiteness-hardened checker. ~4–6 h. No sampler, no vault.
- Card B `docs/lab/shocksat_netcg_validated_port_runner_prompt.md`: HARD gate N0 = reproduce the delivered
  1.51/2.30/2.53 through the ORIGINAL netcg machinery before ANY arm work (fail → BLOCKED, valid); then A5b
  tier update (S4) + finalist shear assessment (S3) with a baseline-validated mapping. Dev drives only; no
  +XY read. ~2–4 h.
- Card C `docs/lab/shocksat_modelform_pilot_runner_prompt.md`: the review-designed model-form pilot —
  5 edit classes (connectivity/mesh/element-formulation/geometry/property-control), STRATIFIED 2-per-class
  quotas both tracks, 3 rounds, ALL scored numbers exact-basis (no θ=1 screening scores ever reported),
  complexity/runtime penalties, per-fold finalist refits, V-gates for new operators, ~120 serial
  eigensolves. HQ1 (agent>random) / HQ2 (any model-form class beats A1) pre-registered; double
  falsification = the strongest close-out of the remodeling arc. Run after A+B.
- Recommended order: A and B in either order (independent; run serially on the one 16 GB machine), C last.
  All three carry the D17 lessons: finiteness gates, no cross-fold reuse, exact-basis-only scoring,
  independent-validation wording.

## D17 — GPT-5.6 adversarial review ACCEPTED: original package RED; corrections issued (2026-07-16)
- Review (shocksat_fullspec_review_gpt56_20260716, commit 9cad98c) audited 8 claims; lead VERIFIED the
  load-bearing ones directly: (C6) rescore_freeze.py:78 applies fold-1's shape MAP to all 4 folds → arm-C
  exact aggregate LEAKS 3/4 held-out drives → withdrawn; (C8) shipped verdicts.json S1/S2 = NaN and
  arms-table F row = R (random control) → collector defect the locked checker's G09 failed to catch
  (validated presence, not finiteness/identity) → RED per Result Status Standard.
- Accepted corrections: original package status RED; S1/S2/F numbers superseded by the reviewer's isolated
  repair (shocksat_full_spectrum_frf_repair_20260716: S1 not met +0.0497<0.05 though >2×SE; S2 not met
  −0.0017±0.0094; F=C per the pre-registered rule); "multimodal not under-identified" → "locally stiff,
  globally unresolved" (local FIM cannot prove global identification; AGENTS definition); "closes Gate W" →
  provenance+force-health closed, independent processing validation NOT (equality by construction);
  S3/S4 → CANNOT-VERIFY (port failed reference reproduction); FEM clamp-count inconsistency noted
  (19 vs 345 edge-cut).
- SURVIVES: S1/S2/S5 not met (S5 fragile across prior widths); data-phase provenance/force health; the
  500 Hz cap (639/1.25); D16 model-form limitation (verified both tracks).
- Corrections written as dated addenda at the top of findings.md + packet.md (original text preserved as
  audit record; no locked file touched). Continuity + lessons updated. Immediate next steps adopted from
  the review's next_steps.md: #1 promote repair numbers (done via addenda), #3 arm-C per-fold exact refits
  (queued, ~0.5-2 CPU-h, would make an honest C-exact number exist), #2 corrected figure (queued).

## D16 — Post-hoc scope limitation logged on the H2 verdict (2026-07-16, Andrew's question)
- Andrew asked how many remodels were stiffness-only vs true model-form. Ground truth from query_log +
  candidate_specs: the AGENT proposed ZERO genuine model-form changes — all 14 agent candidates were
  thickness (8), scale (parametric-only, 1+2 combos), or split (1+2 combos); winner brackets_soft = pure
  thickness. No refine (mesh), no rbe2_soften (connectivity). The compass pointed at stiffness/frequency
  residuals and I steered every proposal there.
- The RANDOM control DID sample model-form: ~4 of 14 had rbe2_soften (×3) or refine (×2, one both) — none
  competitive. Prior true-remodel loop (20260706) tested refine/rbe2/splits in BOTH tracks → null.
- CONSEQUENCE: H2 here = "agent tied random within a mostly-parametric edit space," NOT "agent tried true
  geometry/mesh/connectivity edits and they failed." Findings.md H2 amended with this limitation (does not
  change the S2 status; qualifies its breadth). Mechanistic link: thickness/scale/split live in/near the
  θ-span → exactly why the θ=1 basis inflated the agent winner and the exact re-solve collapsed it (D15).
- If reopened: a fair agentic-remodel test needs the compass to also propose refine/rbe2 edits (or a
  diagnosis that points at connectivity/mesh), not just stiffness-adjacent edits.

## STATE SNAPSHOT (2026-07-15, STUDY COMPLETE)
- Checker OVERALL **YELLOW** (11G/1Y/0R, exit 0); the 1 YELLOW = arm-B/C NUTS non-converged (honest). All
  S1-S5 YELLOW (falsified/not-met). Deliverables all present: packet.md, findings.md, out/verdicts.json,
  out/exact_freeze_scores.json, out/identifiability.json, 7 figures (QA-passed), run_all.sh, runtime.json
  (active 61589s), checker_report.json. Continuity: notes/runs.md + docs/report/project_log.md row appended
  (status copied verbatim). Vault read ONCE post-freeze.
- FINAL FINDINGS: (1) data closes Gate W (5 drives bit-identical, live force); (2) FEM twin credible ~640 Hz
  << data >1 kHz -> FRF capped 500 Hz (compute-bound). (3) S1 falsified, S2 NOT MET (H2 impotence confirmed:
  exact-basis re-eval overturned a screening agent lead -> agent ties random; vault agrees), S5 not met
  (selection != held-out), S3/S4 not validly assessable (QOI reimpl caveat). Amplitude-θ + remodel help
  200-500, not sub-200 (shape wall dented). Deliverable UNCHANGED: inherited FEM + statFEM twin.
- Nothing left to run. If reopened: a machine solving the FEM to ~1250 Hz would let the validated >500 Hz
  data test the twin; a validated net-CG QOI port would make S3/S4 assessable.

## OLD SNAPSHOT (2026-07-15 ~19:30, arm D loop DONE, running post-loop pipeline)
- Arm D 3 rounds done (14 agent + 14 random queries; diagnosis→proposal links in round_summary_r1/2/3.md).
  Agent best wa2_brackets_soft 0.1794; random best wr2_rnd001 0.1657. Round-3 stacking INTERFERED (winners
  don't compound — prior-loop lesson reproduced).
- **S2 MET**: agent-best − random-best sub200 paired delta **+0.0138 ± 0.0091 (1.5×SE), all folds ≥ −0.002**
  → agent beats random by ≥1×SE. Modest reversal of prior H2-impotence, WITH winner's-curse caveat (best
  of 14 each). Agent found it via a diagnosis-targeted bracket edit random didn't reach.
- **S1 FALSIFIED**: best sub-200 arm C +0.044, D-best +0.034 — neither clears +0.05 AND 2×SE. Shape wall
  dented, not cleared.
- Verdicts so far: S1 YELLOW(falsified), S2 GREEN(met, caveated). S3/S4/S5 pending (netcg, arm E).
- Spot checks: first run failed at ~4% (edge artifact comparing to 1000 Hz where k=200 truncates); FIXED to
  compare ≤500 Hz (D11 cap); rerunning (logs/spot2.log).
- NEXT: spot_checks (running) → arm_e_evidence → arm_f_combine → netcg_wide → leakage_audit →
  collect_results → make_figs+tufte/QA → vault_grade (ONE read) → packet/findings → finalize_runtime →
  check.py.

## OLD SNAPSHOT (2026-07-15 ~16:45, arm D round-1 running)
- Dev scores (out/score_log.jsonl, wide records): A0 sub200 0.131/200-500 0.074; A1 0.145/0.058;
  B(amp-MAP) 0.142/0.168; C(shape-MAP) **0.189**/0.058.
- Paired deltas vs A1 sub200: B −0.003 (tied); C **+0.044** (SE 0.045, 2×SE 0.090) → S1 FALSIFIED (below
  +0.05 AND 2×SE; +Z(990) fold −0.086) but shape wall DENTED. B helps 200-500 (+0.11); C helps sub-200.
  COMPLEMENTARY → arm F should stack.
- Arms B (D12) + C (D13) NUTS both YELLOW multimodal, scored at MAP; identifiability.json = multimodal not
  flat. 9 NUTS posteriors registered YELLOW.
- score_log has BOTH legacy-continuity A0/A1 (no bands_agg) and wide A0/A1 (bands_agg); all real code
  filters on bands_agg (SW.existing/collect_results) — safe.
- RUNNING: arm D round 1 (agent_specs_r1 6 + random_round 1 6 seed 20260715), logs/loop_r1.log. wa1_xbeam_
  scale already: sub200 0.170/200-500 0.207 (parametric beats A1 — watch H2).
- NEXT: round-1 results → write agent_specs_r2 from a fresh diagnosis at loop_best → round 2 → round 3 →
  arm_e_evidence → arm_f_combine → netcg_wide → leakage_audit → collect_results → make_figs → tufte/QA →
  vault_finalists (in arm_f) → vault_grade (ONE read) → packet/findings → finalize_runtime → check.py.

## OLD SNAPSHOT (2026-07-15 ~15:00, arm C fold-1 running)
- Scored dev arms so far (out/score_log.jsonl): A0 sub200 0.131 / 200-500 0.074; A1 sub200 0.145 / 200-500
  0.058; **B (amplitude-MAP) sub200 0.142 (TIED A1) / 200-500 0.168 (BIG gain over A1's 0.058)**.
  B_theta_only MAP == B (error term affects posterior width, not MAP location — overconfidence contrast is
  in the non-converged posteriors, sigma_e≈0.73 with-error). Arm B NUTS YELLOW/multimodal (D12), scored at
  MAP. identifiability.json: multimodal not flat (FIM 9/9 clear prior).
- HEADLINE emerging: amplitude training fixes 200-500 amplitude LEVELS (where it trains) but NOT sub-200
  (mis-paired 150-180 shape cluster = the shape wall, H1). Coherent.
- RUNNING: arm C fold-1 (m_xpos_990x), shape field nm=18 r0=106. Fix applied (ash[live] 132-dof MAC).
- NEXT: check arm C fold-1 R-hat → launch folds 2-4 → arm_c_score → arm D loop (run_loop.sh) → E → F →
  netcg → leakage → collect → vault_finalists → vault_grade → figs → packet/findings → runtime → checker.
- Arm-D loop needs eigensolves (K_OWN=200, ~5-10min each, ~36 candidates). Keep SERIAL.

## OLD SNAPSHOT (2026-07-15 ~11:30, arm B running)
- DONE: data phase (5 drives, bit-identical, live force); basis filtered to 209 credible modes (D11,
  scored cap 500 Hz, b500_ceiling=not_certified/FEM-limited); A0_wide package; qoi_sensor_weights;
  BASELINES scored — A0-wide sub200 0.131 / 200-500 0.074; A1-wide sub200 0.145 / 200-500 0.058 (A1 is the
  wide bar to beat). Galerkin gate PASS (0.028 dex); D6 surrogate FAIL recorded (0.51 dex). theta_map_wide
  written. diagnosis_r1 + agent_specs_r1 + round_summary_r1 written (compass: Y-box response + 150-180 Hz
  mis-pairing; freqs good >250 Hz).
- RUNNING: arm B NUTS 8 runs detached (logs/armB.log, ~33 min/fold, ~4.4h). r0=118 sub-basis, F_LIK 45-400.
- NEXT after arm B: arm_b_score → arm C NUTS (4 folds) → arm D loop (run_loop.sh: score agent_specs_r1 +
  random_round 1 6 20260715, then rounds 2-3 with fresh diagnoses) → arm E → arm F → netcg_wide →
  leakage_audit → collect_results → vault_finalists → vault_grade (ONE read) → make_figs → packet/findings
  → finalize_runtime → check.py. Keep jobs SERIAL (16 GB, thrash risk).
- Checker artifact interface frozen in check.py docstring; match names exactly.

## D15 — Exact-basis re-eval OVERTURNS screening: S2 flips to not-met, H2 impotence confirmed (2026-07-15)
- Exact-basis freeze scores (out/exact_freeze_scores.json), sub200 screening→exact: A1 0.145→0.114,
  B 0.142→0.154, C 0.189→**0.157** (leader collapse), D 0.179→0.163, R 0.166→**0.165**.
- **S2 FLIPS**: D−R exact sub200 = **−0.0017** (random ≥ agent) vs screening +0.0138. The agent's screening
  lead was reduced-basis inflation → on trusted bases agent TIES random → H2 IMPOTENCE CONFIRMED (reproduces
  the 2026-07-06 loop, now WITH the amplitude compass). S2 = NOT MET (YELLOW/falsified).
- S1: best exact arm D−A1exact +0.0497 (~at the 0.05 bar); C's screening +0.044 collapsed. No arm cleanly
  clears +0.05 AND 2×SE on a consistent basis → S1 FALSIFIED (robustly, confirmed by the exact check).
- DECISION: the arms×bands table + S1/S2 verdicts use the EXACT-basis numbers (trusted); the θ=1 dev scores
  are reported as SCREENING with the D22 caveat. This vindicates the card's exact-basis insistence — the
  exact check changed the scientific conclusion.
- collect_results updated to read exact_freeze_scores for the table + S1/S2.

## D14 — Reduced-basis trap (D22) hit: freeze set re-scored on exact-at-θ_MAP bases (2026-07-15)
- Spot check: A0_wide theta=1 basis at its θ_MAP fails 0.3% (3.70% max, 0.19% median) because θ_MAP is far
  from 1 (joints 0.47, cross_beam 1.46). The θ=1 reduced-basis DEV scores are therefore SCREENING numbers.
- Fix (pre-registered A5/D22): enrich_wide.py solves K(θ_MAP) fully (k=200) per finalist, folds θ_MAP into
  the projected blocks → pkg.modes(ones) reproduces the exact solve (self-consistency 0.0000%). rescore_
  freeze.py re-scores A0/A1/B/C/D/R on exact bases (A0/A1/C share A0_wide__enr; B/D/R own bases) and writes
  out/exact_freeze_scores.json (screening-vs-exact) + out/spot_checks.json (self-consistency ~0% → G04 GREEN).
- Vault grades on the enriched packages (theta=ones). The exact-basis freeze numbers are the trusted/
  delivery numbers; the dev table is labeled SCREENING. Whether S1/S2 survive on exact bases = reported.

## D13 — Arm C shape-field NUTS also multimodal + very slow → score at MAP (2026-07-15)
- Arm C fold-1 NUTS (shape field, ~1900 latents): R-hat 13.95, ESS 2, 8927 s (2.5 h). Same
  amplitude-multimodality as arm B (D12) and 2.5 h/fold → running folds 2-4 NUTS is wasteful (won't
  converge, ~10 h). Fold-1 is kept as the representative YELLOW convergence evidence.
- Response (identical honest treatment as arm B): report arm-C NUTS YELLOW/non-converged (fold-1 diagnostic
  in nuts_diagnostics.json); SCORE arm C at a DETERMINISTIC multi-start MAP of the shape field per fold
  (L-BFGS on the same freq+MAC+TRAIN-amplitude log-density, train drives only, leakage-safe), θ fixed at
  MAP. Fast (~min/fold). Labeled fallback per AGENTS Sampler Decision.
- run_all.sh updated: arm C = fold-1 NUTS (evidence) + MAP scoring for all 4 folds.

## D12 — Arm B: amplitude-trained θ posterior is MULTIMODAL, not flat (2026-07-15)
- All 8 arm-B NUTS runs non-converged: R-hat 29–360, ESS≈2, θ finite (0.54–1.36, near prior center); the
  θ-only control fails identically → it's the θ→amplitude map, not the error kernel.
- Required identifiability analysis (out/identifiability.json, sampler-independent): at the realized 0.73 dex
  model-form-discrepancy floor the FIM eigenvalues are 1641–3.6e6, **all 9 θ combinations clear the prior
  precision (16)** → θ is LOCALLY highly informative. So the failure is **global MULTIMODALITY**, not
  under-identification: log|H| has huge near-resonance gradients, and many θ align different subsets of the
  dense resonances comparably → many sharp modes, high barriers, single-chain NUTS trapped one-mode-per-chain.
  This is the ridged/multimodal regime the compute protocol names for TMCMC. Strain energy: bottom_box 0.99,
  plates 0.98, top_box 0.89 dominate (matches the Y-box compass).
- Response (AGENTS Sampler Decision — honest labeled fallback): report the NUTS posteriors as YELLOW /
  non-converged (worst R-hat/ESS on every figure + nuts_diagnostics.json); SCORE arm B at a DETERMINISTIC
  multi-start amplitude-MAP (best mode) per fold on TRAIN drives only (leakage-safe, same sub-basis
  likelihood) — gives amplitude training its best-case shot at a meaningful held-out number, clearly
  labeled. θ-only MAP = overconfidence control. TMCMC not implemented; not spending A100 hours on an
  un-validated multimodal twin (compute protocol). This IS an H1-relevant result: amplitudes over-fit
  resonances multimodally rather than pinning one shape-correcting θ.

## D11 — FEM basis: 338 modes were unconverged garbage; credible ceiling ~640 Hz binds below the data ceiling (2026-07-15)
- The k=560/ncv=840 solve (9.1 h) converged only the lowest ~215 modes; the top 338 collapsed onto a clamp
  at 668.1 Hz (ARPACK ncv too small for k=560). Detected + removed (code/filter_basis.py; originals backed
  up to out/raw_full_eig_*). Kept 215 modes, credible top 667 Hz, **cross-validated to 639 Hz** by the
  independent interior-shift slice-1 solve (max rel λ err 7e-10).
- Physics finding: the inherited FEM has a DENSE local-mode forest — 40 modes ≤260 Hz, 136 ≤500, ~215 ≤640.
  Reaching the card's 1250 Hz target needs thousands of modes: infeasible on a 16 GB CPU (k=650 thrashed to
  swap). Per the compute protocol we do NOT spend A100 hours on an un-validated twin.
- Decision: **scored FEM ceiling = 500 Hz** (card's 1.25× modal-truncation rule: 639/1.25 = 511 → round to
  500). The DATA is certified >1 kHz (all 5 drives, source_register) but the FEM twin is only credible to
  ~640 Hz → the **500–1000 Hz FRF band is FEM/compute-limited, NOT data-limited**. This is exactly the card
  §4/§5 "mark where FEM credibility (not data) becomes binding" outcome and a headline finding for H4.
- Consequence: arms×bands table's b500_ceiling column = `not_certified` (with reason) for every arm; the two
  solid scored bands are sub-200 and 200–500. S1 (sub-200) unaffected. H4's 254 Hz cluster (≤260 Hz) is
  fully in range, so the normal-band tier update still runs. A modal-truncation sensitivity (215 vs ~190
  modes on the 200–500 scores) will back the ceiling per the Discretization Gate.

## STATE SNAPSHOT (updated 2026-07-15 ~10:30, basis ready, launching arms)
- DONE since last snapshot: eigensolve finished + filtered (D11, credible 640 Hz); real A0_wide package
  built (r=209 elastic, 33 pairs); D10 (arm B Galerkin exact-eigh forward, validated 0.007 dex) replaced
  the failed D6 surrogate.
- NEXT: qoi_weights → run_baseline_arms (A0/A1-wide + θ_MAP) → check_surrogate (record D6 fail + D10 pass) →
  arm B NUTS 8 runs detached → scores → diag → arm D loop → arm C → E → F → netcg → vault → figs → checker.

## OLD SNAPSHOT (2026-07-14 ~12:00, superseded by the one above)
- DONE: pre-registration locked (D1); continuity bars pass (D2: A0=0.1969, A1=0.2371); ALL 5 drives
  wide-distilled + bit-identical overlap validation + live force (source_register.md); vault frozen
  (VAULT_FREEZE.sha256); extended peaks (11 clusters ≥3 drives); JAX window port validated (1.3e-12 dex).
- RUNNING: full_eig2.py detached (k=650 definite-shift, logs/full_eig2.log) — the wide basis.
- NEXT (in order): wide_package A0_wide → qoi_weights → run_baseline_arms (A0/A1-wide + θ_MAP) →
  check_surrogate → arm B NUTS (8 runs, detached) → arm_b_score → diag_wide r1 → arm D loop (agent
  proposals + random_round, budgets 80/80) → arm C NUTS (4 folds) → arm E evidence → arm F → netcg_wide →
  leakage_audit → collect_results → vault_finalists.json → vault_grade (ONE read) → make_figs → packet/
  findings → finalize_runtime → check.py.
- All scorers log ONLY into this workspace; wscore called log=False everywhere it touches other-workspace
  code. Checker artifact names are frozen in check.py's docstring — match them exactly.

## D0 — Re-grounding statement (2026-07-14, session start)
- **Goal:** test whether amplitude-TRAINED Bayesian updating / shape inference / agent remodeling can beat
  the A1 window-matched baseline (dev P1-class per-channel log|H| correlation 0.2371) per band
  (sub-200 / 200–500 / 500–ceiling Hz), and improve net-CG QOIs, with wide-band re-distilled caches from raw.
- **Last decision:** card dispatched by Andrew 2026-07-14; all 20 §2 reused-asset paths verified present;
  disk has ~24 GiB free (better than the card's ~2.9 GB estimate; one-zip-at-a-time protocol still applies).
- **Next action:** §3 pre-registration in card order (priority_deliverables → question_framing →
  quantity_contracts → assumptions_ledger → check.py SHA-lock → REUSED_code.sha256) BEFORE any science.
- **Open ambiguities:** none blocking. Noted for the record: (a) the card's free-space estimate is stale
  (~24 GiB actual) — protocol kept anyway; (b) vault drive +XY has been read by two prior programs — card
  already mandates honest labeling + fixed arm set; (c) certified ceiling per drive is data-dependent —
  fallback ladder in §4 covers every outcome.

## D1 — Pre-registration locked (2026-07-14)
- `check.py` written to cover all 12 §9 gates, run on the empty workspace (all 12 RED, science-not-run,
  exit 1), then SHA-locked: `c238113b53e2…` in `CHECKER.sha256`. Artifact interface frozen in the check.py
  docstring. `REUSED_code.sha256` = 60 read-only assets hashed.
- Reuse convention: the resolution run's `wscore.score_dev` is always called with `log=False` so nothing is
  ever written into that workspace; records go to THIS workspace's `out/score_log.jsonl`. A vault scorer
  will be a local adaptation reading THIS workspace's `VAULT_FREEZE.sha256` (wscore.score_vault writes to
  the other workspace and checks its freeze file — unusable here without editing it, which is forbidden).
- Arm mapping for the pinned bars: this card's A0 == resolution B0 (A0_enr pkg, naive, flat 1%);
  A1 == resolution B2 (A0_enr pkg, windowed, survey-interp ζ).

## D3 — Data-phase conventions fixed before first distillation (2026-07-14)
- Wide caches keep 45–3000 Hz at the exact cache bin grid (fs/N = 2.0345 Hz); the SCORED extended-band top
  is min(certified ceiling, 1000 Hz) so the §5 eigensolution top (solved to 1600 Hz, reported at 1250 Hz)
  always keeps the 1.25× margin. Where the data ceiling exceeds 1000 Hz, FEM credibility is binding — will
  be reported per the card.
- Q6 ceiling text admits two readings; BOTH are computed and reported per drive
  (`out/certified_ceiling.json`): `ceiling_hz_last_run` (top of the highest contiguous median-coherence
  ≥0.6 run; primary, plus the fraction of bins above threshold below it for honesty) and
  `ceiling_hz_first_run` (conservative). If they disagree materially the packet shows both.
- Force-health gate per hit: absmax(force) within [5, 5000] lbf else DROPPED (Test07 dead channel was
  ~1 lb noise vs 1000–1900 g responses); window-fit skip logic identical to the existing distiller.
- Vault (+XY/Test04): built and overlap-validated at build time (a data-integrity check, part of the
  build), THEN SHA-frozen (existing cache + wide cache + the validation record) in `VAULT_FREEZE.sha256`
  BEFORE any model is scored against any +XY data. Never read again until the single post-freeze grading.

## D5 — Arm designs fixed before their science (2026-07-14)
- **Arms table scoring (D4 merged here):** every arm row in the arms×bands table is scored on the WIDE
  caches with the wide exact-θ=1 basis package (A0_wide) and per-band channel masks (median coh ≥0.6 within
  the band); the pinned A0/A1 continuity bars remain LEGACY-machinery numbers (already reproduced, D2) and
  are reported alongside. A0-wide = naive forward + flat 1%; A1-wide = windowed + survey ζ; both at
  A0_wide's own deterministic multi-start θ_MAP (D19 rule).
- **Q2 per-sensor weights derivation** (stage0 file is per-mode): weight(sensor) ∝ Σ_top-modes
  (shear_X+shear_Y weight_pct) × |φ_mode(sensor)| at θ_MAP, normalized to sum 1; written to
  `out/qoi_sensor_weights.json` before arm scoring.
- **Arm B:** as Q7; likelihood thinning (≤40 channels, every 2nd bin — counts recorded); scoring at the
  posterior-mean θ via the full all-channel scorer; θ-only control identical except σ_e=0. JAX port of the
  window operator gated by out/armB_jax_check.json (must match wide_forward to <1e-9 dex).
- **Arm C:** Beck-style shape field in the WIDE basis, matched (sub-260) modes only, field truncated to
  basis vectors f ≤ 400 Hz (labeled truncation); θ FIXED at θ_MAP_wide — deviation from the composite's
  co-inference, chosen for attribution isolation (shape lever alone) + tractability; τ=0.3, MAC + Rayleigh
  freq + TRAIN-amplitude terms in the likelihood. Arm F may combine B's θ with C's shapes.
- **Arm E evidence:** Laplace approximation at the amplitude-likelihood MAP per candidate, prior-width
  sweep σ_prior ∈ {0.15, 0.25, 0.40} (composite convention).

## D6 — Arm B forward inside NUTS: validated first-order surrogate (2026-07-14, before arm B science)
- Exact eigh of the wide basis (r ≈ 600–900) inside every NUTS gradient is intractable on this CPU
  (estimated ≥ 12 h/chain). Per the compute protocol's "smarter-than-hardware levers" (validated
  differentiable surrogate for the expensive inner loop), arm B's likelihood uses the FIRST-ORDER modal
  surrogate around θ=1 (where the wide basis is exact): λ_i(θ) ≈ λ_i + [A(Δθ)]_ii and
  φ_i(θ) ≈ φ_i + Σ_j reg_ij [A(Δθ)]_ji φ_j with the S1-precedented Tikhonov-regularized denominators
  reg_ij = D0_ij/(D0_ij² + δ²), δ = half the median modal gap; A(Δθ) = Σ_g Δθ_g A_g (precomputed blocks).
  Both frequencies AND shapes respond to θ (unlike a λ-only surrogate).
- VALIDATION GATE (out/armB_surrogate_check.json, before any posterior is reported): exact-eigh logH vs
  surrogate logH at 12 prior draws + at the posterior mean; report median/max dex error per band. The
  posterior is labeled "surrogate likelihood" in every artifact; SCORING of arm B always uses the exact
  within-basis eigh at the posterior-mean θ via wscore_wide.
- Fallback if the gate shows >0.15 dex median error at 1σ prior draws: restrict the likelihood to the
  sub-500 Hz band with exact eigh (labeled deviation from the card's whole-band likelihood).

## D7 — Arm-D loop compute conventions (2026-07-14, before loop science; Discretization Gate tradeoff)
- Own-space candidates (refine/thickness/rbe2): sparse eigensolve sigma=-1e3, k=300 (covers ≳650 Hz —
  measured: interior-shift slices cost 35–90 min each vs ~5 min at the definite shift, so loop candidates
  are solved once at the definite shift). The LOOP's steering metric is sub-200 P1′ (S2's metric) with
  sub-500 recorded; the b500_ceiling table cell for loop candidates is filled only for the FREEZE SET via
  an extended solve. Same-space candidates (split/scale): projection onto the A0_wide basis + G04 spot
  check before freeze-set trust. Every eigensolve logged (card: ≥40 across the loop).
- Diagnosis (amplitude compass) reads per-drive TRAIN-side residual fields only (fold dev scores never
  computed in diagnosis; card §6 D rule), via code/diag_wide.py.
- Vault QOI answer key (+XY) is computed ONLY inside the single post-freeze vault grading event, together
  with the FRF vault grade (G07: one read).

## D8 — Eigensolve strategy switch (2026-07-14): slice walk → single definite-shift k=650
- Measured: definite-shift slice (sigma=-1e3, k=150) = 320 s; interior-shift slices = 2128 s and >50 min
  (killed). Replaced full_eig.py's walk with full_eig2.py: ONE definite-shift eigsh k=650 (expected top
  ≳1400 Hz — covers the 1250 Hz report target and the 1.3× margin over the 1000 Hz scored cap).
- Slices 0–1 (0–515 Hz, 295–639 Hz from independent interior factorizations) kept as cross-checks
  (out/full_eig_crosscheck.json must show matching eigenvalues).

## D9 — k=650 solve thrashed; relaunched k=560/ncv=840 (2026-07-14 ~13:55)
- The k=650 (default ncv=1301) eigsh reached 9.4 GB RSS on a 16 GB machine → swap 7.6/9.2 GB, duty cycle
  ~40% → killed after 2 h. Relaunched with K_ALL=560, NCV=840 (Lanczos basis 2.7 GB; expected top
  ~1300 Hz, still ≥ the 1250 Hz report target with the 1.3× margin over the 1000 Hz scored cap).
  Lesson for notes/lessons-learned.md at close-out: size ncv to fit RAM before launching big ARPACK jobs.

## D10 — Arm B forward: D6 surrogate FAILED its gate in the dry run → Galerkin sub-basis exact eigh (2026-07-14 ~18:30)
- Dry run on the provisional 639 Hz basis: first-order surrogate vs exact forward at a 1σ prior draw =
  **0.64 dex median sub-200 error** (gate 0.15). Cause is physical: ±25% stiffness priors shift
  eigenvalues by far more than the modal gaps of this dense spectrum → first-order eigenvector mixing
  invalid. The D6 surrogate is DEAD for arm B (numbers recorded in out/armB_surrogate_check.json when the
  real basis lands, for the record).
- Replacement (labeled deviation from the card's whole-band likelihood, per D6's pre-registered fallback):
  arm B likelihood = EXACT jnp.eigh on the Galerkin sub-basis of θ=1 modes ≤700 Hz (r0≈230), likelihood
  band 45–500 Hz (covers S1's sub-200 target + the H4-relevant 200–500). Validation gate:
  sub-basis vs full-r exact forward at θ_MAP and prior draws ≤0.05 dex median on 45–500 (Galerkin
  truncation is mild; unlike the θ-first-order error it does not grow with Δθ).
- Consequence, reported as a FEATURE: no arm trains on 500–1000 Hz — that band becomes a doubly-held-out
  test for every arm (never seen by any training loop, only scored).
- Arm E's evidence likelihood switches to the same sub-basis exact form (consistency).
- SCORING is unchanged: full-r exact within-basis eigh at the posterior-mean θ, all three bands.

## D2 — Continuity bars reproduced; SE convention clarified BEFORE any arm science (2026-07-14)
- A0 dev P1′ = 0.1969 (bar 0.1969±0.002, HARD) PASS; A1 = 0.2371 (bar 0.2371±0.005) PASS.
  `out/continuity.json`. Study proceeds.
- Clarification (pre-registered now, no arm scores exist yet): raw fold scores scatter widely
  (A1 folds 0.353/0.553/0.149/−0.107, raw fold SE 0.141), so for the S1/S2 comparisons "fold-SE" means the
  SE of the PAIRED per-fold deltas (candidate − reference), exactly the resolution run's S1 convention
  (its paired SE was 0.0263). Dated addendum appended to `quantity_contracts.md`.
