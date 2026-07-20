# Decisions log — plate-test rehearsal

- D1 (2026-07-01, Andrew): APPROVED the rehearsal — "Good idea. Go ahead and execute it, the
  original idea." The "original idea" = the synthetic end-to-end plate-test rehearsal ALONE;
  the offered 2x2 ablation bundle was not taken. Lead executes as runner (netcg precedent).
- D2 (lead): Success criteria S1-S6 PRE-REGISTERED in question_framing.md and encoded in check.py
  BEFORE any science runs; CHECKER.sha256 locks check.py. Falsification accepted: a failed S1
  yields a revised-test-design deliverable, not a hidden result.
- D3 (lead): Joint single-NUTS model (theta + shape coefficients + sigma_y + sigma_w2) rather than
  a two-stage theta-then-conjugate pipeline — stronger claim ("the actual pipeline through NUTS")
  at similar cost; the L5 eigenvalue likelihood is reused verbatim (Kiran Eq 25 form).
- D4 (lead): Shape basis FROZEN at theta_MAP inside inference (assumptions A9) to avoid
  eigenvector-derivative degeneracy on the near-degenerate drumhead cluster under NUTS. The truth
  generator does NOT share this simplification (truth shapes come from theta_true modes + extra
  out-of-band structure), so the simplification is TESTED, not assumed away.
- D5 (lead): Honest fine structure: the truth's out-of-basis component (out-of-band plate modes)
  is deliberately included so the sensor array CANNOT capture everything (pretest says worst-mode
  captured ~0.39 at 12 sensors); delivery carries the un-captured part as the A10 inflation.
  Without this the rehearsal would be circular (data model = inference model = guaranteed pass).
- D6 (lead): Arms A0 (1 sensor, integrity), A1 (12, headline), A2 (20, margin), A3 (12 + jitter,
  robustness); +Y drive only; +Z(990) arm and identification-failure modeling = documented
  deferrals (cost control).
- D7 (lead): Runs launched detached with per-(arm,seed) resumable outputs (out/runs/*.json);
  BLAS threads pinned; convergence gate per run; non-converged seeds excluded from headline AND
  reported (S3).
- D8 (lead, PRE-CAMPAIGN FIX from the smoke test — before any recorded runs; checker untouched):
  the first smoke run (A1 s0: band 7.96x, converged) exposed a MODEL-SPECIFICATION bug in my
  rehearsal code, not a design finding: the shape-coefficient prior (sd 0.5) was inconsistent with
  the tier model — with NO data it implied a band far wider than the tier prior's 5.4x, so arms
  were not comparable to the analytic curve, and the A10 exp-inflation DOUBLE-counted out-of-basis
  structure already present in the prior. FIX: (i) c prior sd = kappa (the calibrated truth-mix
  scale, making prior == truth-generating process == tier model — the rehearsal then cleanly tests
  sensor INFORMATION CONTENT); (ii) out-of-basis structure carried in delivery as explicit
  d ~ N(0, kappa) draws through g_extra (replaces the A10 inflation rule). Consistency check
  required before campaign: prior-only (no-sensor) delivered band must reproduce ~5.4x. The
  pre-fix smoke-run artifact was deleted (model changed; nothing scored against the checker yet).
  assumptions_ledger A10 revised accordingly.
- D9 (lead, mid-campaign, checker untouched): several A0 runs finished with divergence fractions
  2.4-2.6% — just over the 2% convergence gate (R-hat/ESS clean). Remedy = the STANDARD NUTS fix:
  a UNIFORM retune pass (`python3 code/rehearsal.py retune` with TARGET_ACCEPT=0.98) re-running
  EVERY non-converged (arm,seed) with identical data/seeds and only the sampler's target-accept
  changed; the per-run record stores target_accept so mixed-tuning provenance is explicit. The
  running campaign (already-loaded module) is unaffected by the code edit; the retune runs after
  it completes. No thresholds changed; runs that still fail after retune stay excluded+reported
  per S3. Policy adopted BEFORE seeing any A1/A2/A3 headline results (only the A0 integrity arm
  was complete), so it could not have been chosen to favor an outcome.
