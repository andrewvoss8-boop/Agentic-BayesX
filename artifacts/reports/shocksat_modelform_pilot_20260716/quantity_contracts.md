# quantity_contracts — MODEL-FORM PILOT (pre-registered BEFORE plotting/fitting/scoring)

## Q1: per-channel FRF amplitude score P1′ (COPIED from the full-spectrum study's contract; identical
machinery, reused read-only — `wscore_wide.py` + `metrics.py`)
- **Quantity.** H1 accelerance FRF magnitude per channel: H(f) = accel response [g] / hammer force
  [lbf], H1 estimator averaged over hits. Model side: modal-superposition accelerance in g/lbf
  (G_IN_S2 = 386.0886 in/s²/g), free-free basis, mass-normalized modes.
- **P1′:** per-channel Pearson correlation of log10|H| between model and measurement over the scored
  band, after a TRAIN-side FDAC frequency-scale warp (one scalar ρ per fold, estimated on train drives
  only) and coherence masking (channel used only if median in-band coherence ≥ 0.6). Median over
  channels per drive; mean over the 4 LODO folds. Range [−1,1]; 1 = perfect shape.
- **P3** (no-alignment correlation) recorded in score logs as always.
- **Bands:** sub200 = [45,200) Hz (the HQ band), b200_500 = [200,500) Hz (reported). 500+ not certified
  (FEM/compute-limited, study D11) — not scored.
- **GAIN CONVENTION (hard rule):** ONE global gain (train-side mean log offset) per fold per candidate.
  NO per-channel, per-mode, or per-band amplitude least-squares anywhere in any reported metric.
- **Damping convention:** window-matched forward operator 𝒲 (resolution run's `wforward.py`, reused
  verbatim) + measured survey per-mode ζ (frequency-interpolated; band-median above the 257.6 Hz survey
  top). No free damping anywhere. Same convention as A1 → candidate-vs-A1 deltas are apples-to-apples.
- **Expected limiting behavior:** accelerance → mass line between modes at high f; peak widths set by
  ζ+ζ_w(f); dense sub-260 Hz peaks merge at the 2.03 Hz bin spacing (known).
- **References/pinned bars:** A1 exact sub-200 = 0.11368 (folds +0.27383/+0.49818/−0.00197/−0.31530);
  study exact D = 0.16336 / R = 0.16507 (Card A reproduced both to <1e-10 — my pipeline's reproduction
  target, see Q4). Wall context: ≈0.34 deterministic-update median; ≈0.70 measured-shapes reference.

## Q2: paired-fold SE convention (the study's D2 addendum, reused)
For every comparison bar: per-fold deltas d_k (candidate fold k minus reference fold k, same fold —
fold difficulty cancels), SE = std(d_k, ddof=1)/√4. "≥1×SE" rules use exactly this SE. Raw per-arm fold
scatter is reported in the results table as score uncertainty, never used for the HQ rules.

## Q3: complexity contract (per scored candidate)
- **n_dof:** reduced-system DOF count after MPC elimination (the eigensolve size). ΔDOF% vs baseline
  399,510 (verified at runtime from the A0 T-matrix; if the runtime baseline differs the recorded value
  wins and is reported).
- **Δn_params:** number of free θ blocks minus the baseline 9 (extra blocks from split/thickness/
  formulation ops add calibration freedom — more ways to fit).
- **solve_ratio:** candidate's θ=1 own-space eigensolve wall seconds / the A0-rebuild reference solve
  wall seconds measured in THIS workspace on the same machine (recorded in `out/complexity_ref.json`).
- **not-worth-it rule (pre-registered):** exact sub-200 gain vs A1 < 1×paired-fold SE AND ΔDOF > +10%
  ⇒ labeled not-worth-it regardless of sign.

## Q4: pipeline reproduction check (before trusting any new-candidate score)
Rebuild + enrich + exact-score the study's random winner `wr2_rnd001` (spec read-only from the study;
θ_MAP from the study's `theta_maps.json`) through THIS workspace's redirected pipeline: must reproduce
exact sub-200 = 0.16507 within |Δ| ≤ 0.01 (ARPACK start-vector tolerance, Card A's G07 bar). Written to
`out/repro_check.json`; checker-verified.

## Q5: mechanical gates (before any candidate is scored; recorded per candidate)
- **RBM:** exactly 6 modes below 10 Hz in the θ=1 own-space solve (free-free; >6 ⇒ disconnected or
  mechanism ⇒ dud; <6 ⇒ spurious grounding ⇒ dud).
- **Positive stiffness:** all elastic eigenvalues > 0 (eigsh shift-invert at σ=−1e3 must return
  physically ordered λ; failures = dud with reason).
- **Mass contract:** total mass change vs baseline recorded; |Δm| ≤ 10% for thickness ops (mass follows
  t by physics), ≤ 0.5% for geometry ops (small warps/offsets must not create mass), 0 for
  formulation/connectivity/scale/split (stiffness-only edits).
- **Element quality (geometry ops):** min corner-Jacobian ratio of edited elements > 0.2 and warp slope
  |∂w| ≤ 0.35 per element edge; violations = dud.
- **Finite-perturbation liveness:** the candidate must move at least one paired mode by ≥0.05% vs the
  A0 pairing (a numerical no-op is not a genuine candidate; recorded as max_mode_shift_pct).

## Q6: V-gate contracts for NEW operators (each written to out/vgate_<name>.json BEFORE first scored use)
- **vgate_tbuilder (unconditional):** my extended T-builder on the UNEDITED baseline model reproduces
  femlib.build_T exactly: identical shape, identical kept-DOF set, max|ΔT| = 0 (same construction path).
- **vgate_rbe3_convert:** (a) interpolation exactness — prescribe a rigid-body field (translation +
  finite rotation, linearized) on the master nodes of a converted spider: the reference node's recovered
  motion matches the rigid field to ≤1e-9 relative; (b) 6 RBMs preserved on a converted full model
  (k=12 solve, modes < 10 Hz exactly 6); (c) liveness — conversion moves ≥1 paired mode ≥0.05%.
- **vgate_formulation:** standalone flat-plate patch test (fe_core MITC4/DKT, free-free dense eigh):
  (a) bend_ratio scale s multiplies pure-bending drumhead frequencies by √s within 2% (thin plate,
  membrane-decoupled); (b) ts_t: monotone — decreasing ts_t (softer transverse shear) lowers bending
  frequencies; increasing toward the Kirchhoff limit raises them, plate-theory direction; (c) mass
  unchanged (Δm = 0 exactly).
- **vgate_geometry:** (a) RBM test — 6 zero modes (<10 Hz) preserved after warping a panel of the FULL
  model; (b) known-answer — warping a standalone FLAT plate (amp/t ∼ 1) must RAISE its fundamental
  drumhead frequency (shallow-shell membrane-bending stiffening, expected direction from shell theory),
  and the shift must GROW with amplitude (monotone over 3 amplitudes); (c) mass drift ≤0.1% on the
  patch; (d) element quality per Q5 on the warped elements.

## Q7: file schemas the locked checker reads (fixed now so the checker can be immutable)
- `out/query_log.jsonl`: one line per SCORED candidate: {cid, track, round, cls, ops[], seed?
  (random), diagnosis_link? (agent), basis:"exact_at_thetaMAP", exact_sub200, exact_b200_500,
  exact_folds{4}, exact_folds_b200_500{4}, theta_map[], enriched_pkg, spot_max_pct, n_dof,
  delta_dof_pct, n_params, mech{n_rbm, mass_delta_pct, max_mode_shift_pct, pass}, solve_s_theta1,
  solve_s_enrich, ts}. Keys containing "screening" are FORBIDDEN (checker RED).
- `out/duds.jsonl`: {cid, track, round, cls, reason, ts}.
- `out/complexity.json`, `out/results_table.json`, `out/verdicts.json`, `out/finalists.json`,
  `out/seeds.json`, `out/vault_guard.json` {xy_files_opened:0, checked_paths[]},
  `out/dropped_classes.json` (only if a class is dropped: {cls: {vgate, reason}}),
  `out/vgate_<op>.json` {op, status, checks[], ts}, `out/repro_check.json`,
  `out/eigensolve_log.jsonl`, `out/runtime_log.jsonl`, `runtime.json`,
  `out/fig_manifest.json` + `out/fig_qa.json`, `out/round_summary_r{1,2,3}.md` (diagnosis→class→edit
  links per agent proposal).
