# Task Card B — Advisor Report Rebuild (post-closure-analyses)

Status: COMPLETE — advisor-context and narrative rebuild verified 2026-07-22 · Lead: Codex · Approved by: Andrew
Workspace: `artifacts/reports/shocksat_closure_report_20260722/` (new; preserve all prior DOCX files untouched)
Compute budget: ≈ 0 (document build + figure regeneration only; no inference, no eigensolves beyond regenerating existing figures).

## Task

Rebuild `ShockSat_StatFEM_progress_and_closure_update` around the four Task Card A results plus three recovered existing findings, applying Andrew's adjudication of the Bilionis-style review. This is an editorial/synthesis task: **no new science, no recomputation, no strengthened claims.**

## Controlling inputs
- Task Card A packet + `out/` artifacts (checker-verified).
- Andrew's adjudication (2026-07-22, `notes/memory.md`) — the authoritative list of accepted criticisms and pushbacks.
- Predecessor report workspace `artifacts/reports/shocksat_results_summary_20260721/` (D1–D6 decisions still bind; D4 user-edit recovery authority still applies).

## Required changes (each maps to an adjudicated decision)

1. **Retitle and reframe.** The converged result is Bayesian modal-frequency FEM updating with an inferred iid residual scale — NOT statFEM. Title/opening must distinguish "Bayesian FEM updating" (converged) from "response-level statFEM attempts" (not converged). Thesis: *what Bayesian modal updating and response-level statFEM can and cannot establish on ShockSat*; the model-form pilot supports the diagnosis, it does not carry the thesis.
2. **Core = the four A results.** Restructure so A1 (identified subspace, replaces the nine-marginal contraction table), A2 (σ_f prior sensitivity + predictive checks), A3 (coverage/proper-score table vs FEM+6 dB), A4 (profile-likelihood diagnosis of the whole-FRF failure) are the analytic spine. Carry each result's status (GREEN/YELLOW) and caveats verbatim from the A packet.
3. **Recover the three omitted findings:**
   - Time-domain damping study (`shocksat_latent_force_damping_20260623`): 14/16 modes, R-hat 1.020, ESS 250, ζ 0.33–0.76% — converged damping did NOT fix the envelope decision ⇒ direct positive evidence for the shape/model-form attribution.
   - Phase diagnostic (A5 output): circular variance ~0.854, no sharper parameter slice than magnitude; state found-vs-re-derived provenance.
   - FEM+6 dB undercoverage (0.71–0.87) with the delivered method's 2.30×/0.98 — via the A3 table; frame the load result as a calibration/width tradeoff, not a simple failure. Keep normal-Z strictly labeled synthetic self-consistency.
   - Recover the retained L5 working-twin FRF result: converged modal-frequency NUTS parameter stage plus an
     observed-channel-estimated marginal log-amplitude discrepancy transferred to held-out channels. Label it
     a **two-stage/modular predictive construction**, not a jointly converged whole-FRF StatFEM posterior.
4. **Fix the likelihood equation direction:** `log f_meas,m ~ Normal(log f_pred,m(θ), σ_f)`; note the implementation was already correct.
5. **Agent result restated:** "this study failed to demonstrate an advantage" + minimum detectable effect; name the preregistered primary (best-exact vs best-exact) and the track mean as secondary, citing the pilot workspace.
6. **Demote +54.02 log-evidence** to an approximate type-II-ML model-ranking diagnostic — for the correct reasons (local linearization, no MC error, conditional evidence target of matched modal freq+MAC), NOT the FRF-bin argument.
7. **Reconcile 2.526 vs 2.958** adjacently as different configurations (delivered reference vs tier-updated), one sentence.
8. **Aggressive compression:** `remodelctl`/CLI section → ≤3 sentences + a future-work appendix; delete the runtime-accounting appendix from the advisor document (keep in repo); collapse repeated caveat tables to one work-products-and-limits table; define only terms used later, including IFT and β, the model-form score (units), channel/drive counts, and frequency bands. Omit unused internal S1/S3/S4 labels. Target length: **≤ 9 pages** (from 13).
9. **Advisor update, not a defense:** start from the “Stress Testing StatFEM” proposal and Bilionis's last guidance, explain the research sequence before results, and ask for closure direction. Do not use a “claims I will defend” list or traffic-light shorthand in the advisor-facing document.
10. **Keep PSIS-LOO out**; fix the [15] citation to motivate predictive holdout evaluation generally. Coherence-derived variance, orthogonal discrepancy, and Schneider surrogate appear only as future-work options, clearly unimplemented.
11. **Replace the Section 5.4 method wall.** Use the frozen
    `statfem_real_validation_20260617/out/mc_cache.npz` arrays to show two held-out channels from split seed 10:
    DAQ 20 (improves) and DAQ 24 (persistent miss). Each panel contains only measured FRF, original FEM,
    updated posterior median, parameter-only 5th–95th percentile envelope, and total 5th–95th percentile
    predictive envelope after the modular model-form term. No hit-quality shading/axis, failed-method curves,
    or on-panel diagnostic prose. Move joint whole-FRF and Beck failure diagnostics to the method/status table.

## Not Allowed
- Any new inference or metric; any number not traceable to a checker-backed artifact.
- Weakening the YELLOW ceiling: no direct net-CG answer key, non-converged response-level posteriors, no agent-over-random win — all stay prominent.
- Overwriting or editing prior report DOCX files (new file, prior versions preserved).
- Reintroducing figures reconstructed from unretained draws.

## Required files
`priority_deliverables.md` · `decisions_log.md` · report builder in `code/` (single script, replayable) · regenerated figures (tufte-linted, source-run + validity flags on-figure) · `check.py` + SHA-lock with RED-on-empty proof · `run_all.sh` · `runtime.json` · final DOCX + a plain-Markdown mirror of the report body for diffability.

## Checker must verify (minimum)
1. Every numeric value in the report body appears in a listed source artifact (spot-check table with ≥25 sampled values and their sources).
2. Definitions table exists and terms used later, including IFT/β, score units, counts, and bands, are defined exactly once; unused internal labels are omitted.
3. Likelihood equation direction correct.
4. Normal-Z rows/figures carry the synthetic-self-consistency label.
5. Page count ≤ 9; remodelctl content confined to future-work.
6. All prior DOCX files byte-identical to their pre-task hashes.
7. Figure legibility + alt-text QA pass.

## Done criteria
Checker exit 0; packet with before/after structure map (which old section went where); `notes/runs.md` entry; deliverable DOCX ready for Andrew's read-through, with the four closure questions to Bilionis (§10 of the previous version) retained but updated to reflect the A3 outcome.

## Human stop points
- A3 changed the load narrative from simple failure to a calibration/width tradeoff. Andrew reviewed the runner's
  interim A3 result and instructed the report update to proceed on 2026-07-22; this stop point is satisfied.
- Any conflict between an adjudicated decision and an A-result.
