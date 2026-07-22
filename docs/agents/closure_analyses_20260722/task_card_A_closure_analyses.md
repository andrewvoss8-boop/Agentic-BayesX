# Task Card A — ShockSat Closure Analyses (four Bayesian audit calculations + phase-diagnostic recovery)

Status: READY TO RUN · Lead: Claude Code · Approved by: Andrew (2026-07-22 adjudication, see `notes/memory.md`)
Workspace: `artifacts/reports/shocksat_closure_analyses_20260722/`
Compute budget: **HARD CAP 4 h active runtime combined** (soft budgets per item below). No detached multi-hour jobs expected; if any single step approaches 45 min, stop and report before continuing.

## Task

Produce the four checker-backed analyses that Andrew's adjudication of the Bilionis-style review selected as the final technical work before the report rebuild, plus recover (or cheaply re-derive) the phase diagnostic. **No new physics studies. No formulation-calibration work. No model-form search.** Everything runs from frozen, hashed, already-existing artifacts.

## Why This Matters

These five items convert the advisor report's asserted conclusions into demonstrated ones: (A1) what the 18 modal frequencies actually identify; (A2) whether the 4.6% discrepancy floor is data-driven or prior-driven; (A3) whether the statFEM load bands beat the FEM+6 dB incumbent under calibration + a proper score, not width alone; (A4) why the whole-FRF posterior separated; (A5) documented negative phase evidence. Task Card B rebuilds the advisor report around their outputs.

## Controlling decisions (read before starting)

- `notes/memory.md` CURRENT STATE entries dated 2026-07-22 (review, probes, adjudication).
- `artifacts/reports/shocksat_results_summary_20260721/decisions_log.md` D1–D6.
- AGENTS.md: all gates apply, including Modal/Eigenproblem Identifiability Gate, Plot Gate (tufte skill + lint), Verification Gate, Runtime Accounting.

## Frozen inputs (hash into `source_manifest.json` at INIT; verify unchanged at end; copy NONE, modify NONE)

| Input | Path | Used by |
|---|---|---|
| Modal NUTS draws (4000×9 θ + σ_f, pooled) | `artifacts/reports/shocksat_fem_modal_twin_20260609/nuts_full_samples.npz` | A1, A2 (reference), A3 |
| Reduced model (A_fix, 9× A_g 74×74, obs_V 228×74, nominal eigvals) | `artifacts/reports/shocksat_fem_modal_twin_20260609/matrices/reduced_blocks.npz` | A2, A3, A4 |
| Measured modes + pairing + θ summary | same workspace: `measured_modes.npz`, `pairing.json`, `theta_full.json` | A1, A2 |
| Measured complex H1 FRFs + coherence, 5 drives, 111 ch × 105 pts, 45–260 Hz | `artifacts/reports/shocksat_netcg_method_selection_20260701/data/multiref_modal/*.npz` | A3, A4, A5 |
| Wide-band FRF caches (45–500 Hz) | `artifacts/reports/shocksat_full_spectrum_frf_20260714/data/multiref_wide/*.npz` | A4/A5 if needed |
| Delivered net-CG posterior + band machinery | `artifacts/reports/shocksat_netcg_method_selection_20260701/out/` (incl. `theta_post_L5.npz`, `heldout_drive.json`) and `artifacts/reports/shocksat_netcg_validated_port_20260716/` | A3 |

**Data-of-record note (from 2026-07-22 probe):** the original raw extract root (`shocksat_multiref_explore_20260623/data/extracted`) no longer exists. The multiref caches above ARE the measured data of record; hash them first.

## Analyses

### A1 — Prior-whitened identified-subspace analysis (soft budget: 15 min compute)
- Coordinates: **log θ** (9 groups). Whiten by the analytic prior covariance (log θ ~ N(0, 0.25²) i.i.d. ⇒ whitening = divide by 0.25). Eigendecompose the whitened posterior covariance of the stored draws.
- Report eigenvalues (posterior/prior variance ratios per direction), eigenvectors with plain-English physical naming of each strong direction (which stiffness groups it mixes), and **bootstrap CIs** on the eigenvalues (≥1,000 resamples of the 4000 draws; note draws are autocorrelated — use block bootstrap with a stated block length and say why).
- **Known-answer gate:** Andrew's read-only calculation found ~4 contracted directions ≈ 0.019, 0.029, 0.259, 0.355 and five prior-like 0.872–1.166. Your point estimates must match within bootstrap CI or you must stop and explain the discrepancy before proceeding.
- Tie to physics per the Identifiability Gate: reuse the existing joint strain-energy artifact (`joint_strain_energy.json`) for interpretation; do NOT claim per-parameter identifiability — the claim is subspace-level only.
- Output: `out/a1_subspace.json`, one figure (eigenvalue spectrum with CIs + eigenvector composition), caption states run source.

### A2 — σ_f prior-sensitivity sweep + prior/posterior predictive checks (soft budget: 75 min compute)
- Rerun the modal-frequency NUTS model (exact likelihood of the frozen twin: 18 paired log-frequencies, 9 log-normal θ multipliers) under **five σ_f priors**: HalfNormal(0.02), HalfNormal(0.05) [reference — must reproduce stored posterior], HalfNormal(0.15), HalfCauchy(0.05), and Exponential(mean 0.05).
- NUTS, ≥4 chains, **retain per-chain draws** (the stored draws are pooled — this sweep must not repeat that omission). Convergence gate per AGENTS.md for every run; a non-converged variant is YELLOW and reported with worst R-hat/ESS, never silently dropped.
- **Known-answer gate:** the HalfNormal(0.05) rerun must reproduce the stored posterior (σ_f median ≈ 4.6%, θ medians within MC error of `theta_full.json`) before the other variants are interpreted.
- Deliver: table of σ_f posterior median/CI per prior; one sentence per variant on whether the 4.6% floor and the model-form conclusion survive. Prior predictive check (do prior draws' predicted frequencies contain the measured 18?) and posterior predictive check (PIT/residual plot for the reference model).
- Output: `out/a2_sigma_f_sweep.json`, per-variant NUTS diagnostics, 2 figures.

### A3 — Matched coverage + proper-score table: statFEM vs FEM+6 dB (soft budget: 60 min compute)
- **Recovery first:** reproduce the already-computed incumbent undercoverage from `shocksat_netcg_method_selection_20260701` (FEM+6 dB weighted coverage 0.71–0.87; shear_Y 0.71, normal 0.74; delivered method 2.30×/cov 0.98). **Known-answer gate:** match those stored numbers from the stored arrays before computing anything new. If the arrays needed to reproduce them are not stored, STOP and report exactly what is missing — do not re-derive a different pipeline silently.
- **New columns:** for the same channels/drives/grid, add a proper score — CRPS (continuous ranked probability score: a proper scoring rule generalizing absolute error to distributions; lower is better) or held-out log predictive density — for (i) FEM+6 dB treated as a stated-width interval predictor (document the distributional convention used to score an envelope, and a sensitivity to that convention), (ii) the delivered statFEM band, (iii) the parameter-only modal propagation.
- **Strict evidence separation:** shear X/Y columns = measured held-out evidence; normal Z = synthetic answer key only, labeled "self-consistency, NOT validation" in the table and on the figure. State both normal-Z width values adjacently (2.526 delivered reference; 2.958 tier-updated) with one sentence on the configuration difference.
- Output: `out/a3_calibration_table.json`, one table figure + one coverage-vs-width figure.

### A4 — 1-D whole-FRF profile likelihood (soft budget: 45 min compute)
- Target: the iid log-magnitude whole-FRF likelihood that failed (document its exact form from the source study before computing).
- Profile along **two** stiffness multipliers separately (choose the two with largest whole-FRF sensitivity; state the choice rule): grid of ≥41 points spanning the prior 95% range; at each grid point **profile (optimize) the nuisance quantities** (drive gain, noise scale) rather than freezing them; record inner-optimization convergence.
- Deliver the profile curves annotated with the separated NUTS chain locations (from stored whole-FRF diagnostics where retained). The deliverable claim is diagnostic: show whether the profile is multimodal (peak-crossing structure) — turning "posterior geometry" from verdict into diagnosis.
- Output: `out/a4_profile_likelihood.json`, one figure.

### A5 — Phase-diagnostic recovery or re-derivation (soft budget: 20 min compute)
- First search the repo for the existing circular-variance phase diagnostic (~0.854, "no sharper parameter slice than magnitude"). If found: hash it, cite workspace + file, done.
- If not found within 30 minutes of searching: re-derive it deterministically from the complex H1 caches — circular variance of phase residuals between measured H1 and the nominal reduced-model FRF across coherence-qualified channels, plus a 1-D parameter slice of a phase-based misfit vs the magnitude-based misfit to test "no sharper slice." No sampler. Label clearly as a re-derivation if the original is not found.
- Output: `out/a5_phase_diagnostic.json` (+ provenance note stating found vs re-derived).

## Sampler statement (required by AGENTS.md)
NUTS is used for A2 only (differentiable modal-frequency likelihood; matches the frozen twin). A1/A3/A4/A5 are deterministic post-processing/optimization — no sampler, and none is claimed.

## Not Allowed
- Modifying, moving, or copying any frozen input; touching any predecessor workspace.
- New physics candidates, model-form edits, formulation calibration, TMCMC reruns of IFT/M2, or reconstructing trace/pair plots from draws that were not retained.
- Reporting any interval from a non-converged run without worst-case R-hat/ESS printed beside it.
- Editing `check.py`/`check_config` after the SHA-lock.

## Required workspace files (write at FREEZE, before science)
`priority_deliverables.md` · `question_framing.md` · `assumptions_ledger.md` (all priors/settings with units) · `quantity_contracts.md` (CRPS convention, coverage weighting, band-width statistic, profile-likelihood definition) · `decisions_log.md` · `source_manifest.json` (SHA-256 of every frozen input) · `code/` (all scripts saved as .py, tufte-linted for figures) · `check.py` + `CHECKER.sha256` with proven RED-on-empty (`out/checker_empty_report.json`, exit 1) · `run_all.sh` one-command replay · `runtime.json`.

## Checker must verify (minimum)
1. All frozen-input hashes unchanged end-to-end.
2. A1 known-answer gate: eigenvalues match adjudicated values within bootstrap CI.
3. A2 reference rerun reproduces the stored posterior; per-variant convergence diagnostics present for ALL sampled variables; per-chain draws retained.
4. A3 known-answer gate: stored 0.71–0.87 / 2.30× / 0.98 reproduced before new columns; shear vs synthetic-Z labels present in table AND figure captions.
5. A4 inner-optimizer convergence recorded at every grid point.
6. A5 provenance (found vs re-derived) stated.
7. Figures pass tufte lint + legibility QA; every figure names its source run and flags any non-converged content.
8. `runtime.json` active total ≤ 4 h.

## Result status expectation
Overall GREEN is achievable for A1/A3/A4/A5 (deterministic, known-answer-gated). A2 variants may individually be YELLOW (a heavy-tailed prior may not converge) — that is a reportable finding, not a failure. The inherited science ceiling (no net-CG answer key; one article) is unchanged and must be restated in the packet.

## Done criteria
All five `out/` artifacts + figures exist; checker exits 0 with every gate GREEN or documented YELLOW; `packet.md` written (method summary first, per AGENTS.md plot gate); `notes/runs.md` entry appended; `next_prompt.md` points to Task Card B. Do not begin Task Card B in the same session.

## Human stop points
- Before FREEZE if any frozen input fails to hash/load.
- A3 if the undercoverage numbers cannot be reproduced from stored arrays.
- Any known-answer gate miss.
- Before appending to durable notes beyond the standard runs entry.
