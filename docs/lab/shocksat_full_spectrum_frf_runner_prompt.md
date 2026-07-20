# Runner card — ShockSat FULL-SPECTRUM FRF study (amplitude-trained updating + remodeling, per-band results)

**Paste-and-run: you are an autonomous runner agent. Execute this card end-to-end without stopping for
approval. A falsified pre-registered claim is a VALID outcome. Never fabricate; never claim beyond your
checker's output.**

Date issued: 2026-07-14. Author: lead (Fable), dispatched by Andrew.
Workspace (create it): `artifacts/reports/shocksat_full_spectrum_frf_20260714/`
Everything you write goes THERE (plus the continuity files named in §10). Do not edit any other workspace,
any durable rules file (`AGENTS.md`, `CLAUDE.md`), any other study's checker, or `docs/` besides nothing.

---

## 0. Re-ground first (mandatory, ~15 min)

Read, in order: `AGENTS.md` (every gate applies), `docs/compute_protocol.md`, this card, then skim:
- `artifacts/reports/shocksat_resolution_consistent_scoring_20260713/{packet.md,findings.md}` — the
  window-matched scoring result this study builds on.
- `artifacts/reports/shocksat_true_remodel_loop_20260706/findings.md` — the remodeling loop that failed and
  its two evaluation traps (reduced-basis score inflation; θ_MAP multimodality).
- `artifacts/reports/shocksat_composite_bakeoff_20260702/findings.md` — shape-inference (Beck) result +
  selection-score result.
- `scratch_test07/bandwidth_scan.json` — raw records: 1.0 s long, 0.5 s ring-down (Δf floor 2.0 Hz), hammer
  energy usable to ~2.4 kHz, repeatable to ~2 kHz.
- `artifacts/reports/shocksat_statfem_runner_20260609/source_manifest.md` — raw-zip names, sizes, and the
  download mechanism (nescacademy workshop page posts a hidden `url` field → mediaex-server.larc.nasa.gov;
  direct mediaex URLs support HEAD + byte ranges).

State in `decisions_log.md` (D0): goal / last decision / next action / open ambiguities, one line each.

## 1. The question (and the five standing explanations this study must challenge)

**Question:** Given every lever we have blamed for past failures — amplitude training data, measured
damping, window-matched scoring, shape inference, a remodeling loop steered by the right signal, and the
extended >258 Hz band — can Bayesian FEM updating and/or agent-driven remodeling beat the baseline FEM on
held-out per-channel FRF amplitude, in EACH band, and improve the net-CG force quantities?

**Key fact motivating this study:** no ShockSat run has ever TRAINED on per-channel FRF amplitude data.
Every method so far calibrated on the 33 survey modes only; the 5 drives of amplitude data were used only
for scoring. This card changes that, with pre-registered splits.

Each arm exists to test one standing explanation (H). `findings.md` MUST answer each H explicitly, with
numbers, GREEN/YELLOW/RED per the Result Status Standard:

- **H1 (the shape wall):** "per-channel amplitude is capped near 0.34 because mode shapes are wrong and no
  available lever moves them." Challenged by shape inference TRAINED ON AMPLITUDES (arm C) — never done.
- **H2 (remodeling impotence):** "the agent loop ties with random because its steering signal (frequency
  fit / evidence) does not correlate with held-out FRF." Challenged by giving the loop an amplitude compass
  (arm D). If it still ties random WITH a correlated compass, impotence is confirmed much more strongly.
- **H3 (damping unusable at 2 Hz):** "fitting damping fits window aliasing." Partially overturned already
  (window-matched + measured ζ = +0.040, direction vault-confirmed, below the 2×SE bar). Here
  window-matched scoring + measured ζ is the STANDARD convention for every arm; attribute any gains.
- **H4 (the unmeasured >200 Hz cluster):** "the normal-force band is wide because the 234–258 Hz plate
  modes were never measured." Challenged by wide-band re-distillation: the cluster's amplitudes at ~111
  sensors become measured data (arm F / extended band).
- **H5 (selection scores are not validation):** "Bayesian model-class selection fails under model-form
  error." Previously tested with modal/shape observables only. Re-test with the amplitude-inclusive
  likelihood (arm E): does the selection ranking now correlate with held-out ranking?

## 2. Reused assets (verify EVERY path exists before science; record SHA-256 of each in `REUSED_code.sha256`; all read-only)

| What | Path |
|---|---|
| FEM (67,683 grids, ~406k DOF) | `artifacts/reports/shocksat_fem_modal_twin_20260609/fem_model.npz` |
| 33 survey modes + shapes + PER-MODE DAMPING (`damp` is in PERCENT) | `artifacts/reports/shocksat_fem_remesh_20260618/measured_modes.npz` |
| ERA damping cross-check (raw Test07, time-domain) | `scratch_test07/era_result.npz` |
| Bandwidth/ceiling evidence | `scratch_test07/bandwidth_scan.json` |
| 4 drive caches 46.8–258.4 Hz, 2.03 Hz, ~111 ch (+X, +Z, +XY, +Z@900) | `artifacts/reports/shocksat_psd_envelope_twin_20260623/data/multiref_modal/*.npz` |
| 5th drive cache (+Y) | `artifacts/reports/shocksat_netcg_method_selection_20260701/data/multiref_modal/m_ypos_990y.npz` |
| Canonical distiller (N=122880 @ 250 kHz, exponential window end=0.05) | `artifacts/reports/shocksat_netcg_method_selection_20260701/code/build_ypos_cache.py` |
| Window-matched forward model + scorer (REUSE, do not re-derive) | `artifacts/reports/shocksat_resolution_consistent_scoring_20260713/code/{wforward.py,wscore.py,arms.py}` |
| Reduced-blocks FRF engine + θ machinery | `artifacts/reports/shocksat_psd_envelope_twin_20260623/code/` |
| Shape-inference (Beck) + statFEM output-error arms | `artifacts/reports/shocksat_composite_bakeoff_20260702/code/{rmodel.py,run_arms.py,tier3_evidence.py}` |
| Remodeling action families, exact-basis enrichment, multi-start MAP | `artifacts/reports/shocksat_true_remodel_loop_20260706/code/` |
| Damping action space (band ζ / Rayleigh / per-joint η) | `artifacts/reports/shocksat_frf_damping_updating_20260710/code/` |
| Net-CG QOI weights per sensor/mode | `artifacts/reports/shocksat_netcg_method_selection_20260701/out/stage0_qoi_weights.json` |
| Net-CG QOI + held-out-drive answer-key machinery | `artifacts/reports/shocksat_netcg_method_selection_20260701/code/{netcg_qoi.py,heldout_drive.py}` |
| Raw zip in hand (+X impacts; FORCE CHANNEL DEAD → response-only cross-checks only) | `Test07_ImpactHammer_990x.zip` (repo root) |

If any path is missing, STOP and write `BLOCKED.md` naming it. Do not substitute silently.

## 3. Pre-registration BEFORE any science (order is mandatory)

1. Create the workspace; write `priority_deliverables.md`, `question_framing.md` (the H1–H5 table + the S1–S5
   criteria below verbatim + the pinned bars), `quantity_contracts.md` (log|H| per-channel correlation
   convention: ONE global gain per fold, no per-channel or per-mode amplitude fitting anywhere in any
   selection score; net-CG shear/normal contracts copied from the netcg workspace), `assumptions_ledger.md`
   (window params, ζ source and units, band edges, split definitions, priors with numbers).
2. Write `check.py` covering every gate in §9; run it on the empty workspace (must report RED
   science-not-run); SHA-lock it (`CHECKER.sha256`); NEVER edit it afterward.
3. Write `REUSED_code.sha256`.
4. **Pinned continuity bars (report all in the packet):**
   - A0 (historical convention: frozen basis, flat 1% ζ, naive scoring) dev P1′ must reproduce
     **0.1969 ± 0.002** on the same 4-drive leave-one-drive-out folds. HARD GATE — do not proceed if it fails.
   - A1 (window-matched + measured ζ) must reproduce **0.2371 ± 0.005** (resolution run's result).
   - Wall references: deterministic-update median log|H| corr ≈ 0.34; measured-shapes reference ≈ 0.70.
   - Vault location effect from prior runs: dev→vault shifts of +0.22–0.30 are a LOCATION effect, not a win.
5. **Splits (pre-registered, never changed mid-run):**
   - Dev folds = leave-one-drive-out over the 4 dev drives {+X/990x, +Z/990z, +Y/990y, +Z@900z}: train on 3
     drives' amplitudes, score the 4th. Fold-average and report the fold SE.
   - VAULT = the ENTIRE +XY/Test04 drive (both bands, existing cache AND its wide-band re-distillation),
     SHA-frozen at build time, never queried during development, graded ONCE on the frozen finalist set
     (`VAULT_FREEZE.sha256` first). Label it honestly: +XY has been read by prior programs — state this and
     rely on the pre-registered arm set (no search against the vault).
   - Query budget on dev folds: agent remodeling ≤ 80 scored queries; random control ≤ 80; every dev query
     appended to `out/query_log.jsonl`.

## 4. Data phase — wide-band re-distillation from raw (the non-negotiable new data work)

Goal: rebuild each drive's FRF cache over **45 Hz → the certified ceiling** (target ≥ 1000 Hz; certified
per drive by multi-hit, force-referenced coherence ≥ 0.6), at the SAME 2.03 Hz spacing and window
(N=122880 @ 250 kHz, exponential window end=0.05 — reuse `build_ypos_cache.py`, change only the band).

- Download the raw modal-hammer zips ONE AT A TIME, in this order (smallest first):
  `Test03_ModalHammer_990y.zip` (645 MB), `Test06_ModalHammer_900z.zip` (881 MB),
  `Test02_ModalHammer_990z.zip` (908 MB), `Test04_ModalHammer_990xy.zip` (923 MB),
  `Test01_ModalHammer_990x.zip` (1.00 GB). Resolve URLs by the documented mechanism in
  `source_manifest.md`; record final URL + SHA-256 per file in `data/source_register.md`.
- **DISK PROTOCOL (hard):** free space is ~2.9 GB. Never hold more than one zip. Extract one `.mat` hit at a
  time, distill it, delete it, then the next; delete the zip once its drive's cache is built and validated.
  Wide caches are small (~500 lines × ~111 ch). Check `df` before each download; if free space < 1.5 GB,
  clean before proceeding.
- **Per-hit health check (Test07 lesson):** verify the force channel is live (std and max in physical range)
  and coherence per hit; log per-drive in `data/force_health.json`. Drop dead hits, never dead-force drives
  silently — report them.
- **Validation gate (per drive, HARD):** over the overlap band 46.8–258.4 Hz, the new wide cache must
  reproduce the existing cache: per-channel |H| correlation ≥ 0.999 and median absolute log10|H| difference
  ≤ 0.01. This finally closes the raw-vs-cache verification (the prior run's Gate W) WITH live force. If a
  drive fails, diagnose (channel map, units, window) before using it; an unexplained failure = that drive's
  wide cache is excluded and reported.
- **Fallbacks (the study must run regardless):** ≥3 dev drives wide-band = full plan. 1–2 = extended-band
  arm runs on those drives only (say so). 0 (all downloads fail) = sub-200 portion proceeds on the existing
  5 caches unchanged, extended-band arm is reported BLOCKED with the exact file list for Andrew. Never stall
  the whole study on a download.
- Report the certified ceiling per drive, and mark where FEM credibility (not data) becomes binding.

## 5. Model/basis phase (do not be computationally lazy)

- Full eigensolution of the inherited FEM to **1.25 × the certified band top** (≥ 625 Hz even in the worst
  fallback; target ~1250 Hz). Detached, resumable, threads pinned. Report the mode count.
- ALL decision-relevant scores use the **exact-basis rule** (full solve at the candidate's θ_MAP or
  validated enriched basis, spot-check ≤ 0.3% frequency error — the true-remodel D22 rule). Reduced-basis
  screening allowed only for the remodeling loop's triage, never for freeze-set numbers.
- **Multi-start deterministic MAP** (≥ 5 starts) for every θ that feeds a selection decision (D19 rule).
- Mode pairing: Hungarian assignment on the full MAC matrix, FROZEN per candidate before scoring.
- Extended band: match FEM modes to the newly measured >258 Hz peaks; update the per-mode uncertainty tiers
  (the 234–258 Hz cluster moves from "unmeasured" to "amplitude-measured at ~111 sensors, shapes still
  sparse on the plate — 1 Z sensor"). Document the new tier table in the assumptions ledger.

## 6. Arms (every arm scored identically; window-matched scoring + measured ζ everywhere except A0)

Damping convention for all arms: survey per-mode ζ (percent → ratio), ERA values as cross-check; modes
without a measured ζ get the band median; NO free per-mode damping fitting inside any selection score.

- **A0 — historical baseline** (frozen basis, flat 1% ζ, naive scoring). Continuity gate only.
- **A1 — resolution-consistent baseline** (inherited FEM + window-matched + measured ζ). THE bar to beat.
- **B — amplitude-trained parameters.** NUTS posterior over the 9 group stiffness θ (log-normal priors,
  σ=0.25, as inherited) with the likelihood on TRAIN-drive log|H| (whole band, one global gain per drive,
  statFEM-style frequency-correlated output-error term with inferred magnitude). Also run θ-only (no error
  term) as the overconfidence control. First time θ ever sees amplitudes.
- **C — amplitude-trained shape inference.** Beck-style shape perturbations (reuse the composite-run
  machinery incl. the Tikhonov-regularized shape derivative) with TRAIN amplitudes + survey shapes in the
  likelihood. Report per-point gains AND net-CG coverage — the known failure mode is confident shapes where
  no data checks them; quantify it, don't hide it.
- **D — remodeling loop with the amplitude compass.** ≥ 3 rounds: diagnose from TRAIN-drive amplitude
  residuals (never the fold's held-out drive) → propose model changes from the validated action families
  (shape edits, joint compliance, thickness t/t³, region splits, damping fields) → screen → dev-score.
  Budgets: ≤ 80 agent dev queries, ≥ 40 full eigensolves across the loop, EQUAL-BUDGET random-edit control
  (same action families, random parameters, seed recorded). Round summaries must show the diagnosis→proposal
  link. This is H2's fair test: the compass now IS the deliverable metric.
- **E — selection-score re-test.** For the top ~10 candidates from D (plus A1 and the historical winner
  `rand10` rebuilt read-only), compute Bayesian model-class selection with the amplitude-inclusive
  likelihood (prior-width sweep as in the composite run). Deliverable: Spearman rank correlation between
  selection score and held-out fold-average, with a scatter figure.
- **F — best combination.** Combine the best-performing levers from B/C/D into one model; score it on dev,
  carry it to the vault. If nothing beats A1, F = A1 (say so).

## 7. Scoring and reporting (per-band results are the point)

For EVERY arm, report fold-averaged held-out per-channel log|H| correlation with fold SE, split three ways:
**sub-200 Hz**, **200–500 Hz**, **500 Hz–ceiling** (where certified). One table, arms × bands — this table
is the study's centerpiece. Additionally:
- **QOI-weighted sensor score:** the same correlation weighted per sensor by its net-CG shear participation
  (`stage0_qoi_weights.json`) — Andrew's "sensor B matters more" requirement. Report per-sensor deltas for
  the 10 highest-weight sensors.
- **Net-CG shear (X and Y):** band width vs the delivered twin's 1.51×/2.30×, with held-out-drive coverage
  (reuse `heldout_drive.py` answer keys). Coverage is a hard gate: an arm that narrows but stops covering
  is DISQUALIFIED for delivery (still reported).
- **Net-CG normal (H4):** rebuild the band with the extended-band measured amplitudes feeding the cluster
  tiers; report width vs the delivered 2.53× and coverage vs the plausible-truth ensemble + any data key.
- **Overconfidence audit:** hide the top 3 measured QOI-driving modes; every delivered band must widen
  (ratio > 1). Arms that don't respond are flagged exactly as in the netcg study.

**Pre-registered success criteria (each maps to an H; falsification is a valid, reportable outcome):**
- **S1 (H1/H3):** some arm beats A1 on fold-averaged SUB-200 per-channel correlation by ≥ +0.05 AND
  ≥ 2×fold-SE, vault direction confirmed.
- **S2 (H2):** the agent track beats the equal-budget random track by ≥ 1×fold-SE on the same metric.
- **S3 (QOI):** a delivered arm narrows net-CG shear while keeping ≥ 0.95 coverage on the held-out-drive keys.
- **S4 (H4):** the normal band narrows by ≥ 25% (2.53× → ≤ 1.90×) while still covering.
- **S5 (H5):** amplitude-inclusive selection score vs held-out ranking: Spearman ≥ 0.5.

## 8. Sampler and convergence

NUTS (NumPyro, 4 chains, float64) for every posterior; the AGENTS.md convergence gate over ALL variables
(R-hat ≤ 1.05 — prefer ≤ 1.01, ESS ≥ 200, divergences < 2%). Non-converged = YELLOW at best, intervals
labeled not-trustworthy with worst-case R-hat/ESS printed on the figures. Multimodality in θ is reported as
under-identification (an expected finding), not a bug. Long jobs detached + resumable per (arm, fold);
`OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1` for small dense eigh/posterior math.

## 9. Integrity gates the checker must encode (all history-driven; the checker is SHA-locked before science)

1. A0 reproduces 0.1969 ± 0.002; A1 reproduces 0.2371 ± 0.005 (continuity).
2. Wide-cache overlap validation per drive (§4) passed or drive excluded + reported.
3. No per-channel / per-mode amplitude least-squares in any selection score (grep + code review; one global
   gain per fold only).
4. Frozen pairing per candidate; exact-basis spot checks ≤ 0.3% on the freeze set.
5. Query budgets respected; `query_log.jsonl` complete; random control same budget + seeded.
6. Held-out fold's drive never appears in ANY training/diagnosis input for that fold (leakage grep on the
   data-loading code paths).
7. Vault: `VAULT_FREEZE.sha256` written before first vault read; vault read exactly once; labeled second
   program read.
8. NUTS gates per §8 for every reported posterior.
9. Per-band results table present for every arm; per-H verdicts present in `findings.md`.
10. Figures: written by saved `.py`, tufte-lint run, legibility QA pass (no clipped/overlapping labels);
    every figure names its run/dataset and flags any non-converged interval on the figure.
11. `runtime.json` with `active_runtime_s` and `elapsed_wallclock_s`.
12. Checker SHA verified unmodified at the end; overall status = worst gate.

## 10. Deliverables and continuity

In the workspace: `packet.md` (method summary first: model form, likelihood equations, data counts,
whole-data-vs-feature choice, inferred vs fixed; then results incl. THE arms × bands table),
`findings.md` (per-H answers, plain English, statuses copied from the checker), `out/verdicts.json`
(S1–S5 + per-H), ≥ 6 figures (per-band table figure, per-sensor QOI-weighted deltas, remodeling
agent-vs-random trajectories, selection-vs-held-out scatter, net-CG bands before/after, run-specific
graphical model), `decisions_log.md` (D0…), `run_all.sh` one-command replay, `checker_report.json`.

Continuity: append a run entry to `notes/runs.md`; add the row to `docs/report/project_log.md` with the
status COPIED from the checker; do NOT edit `notes/memory.md` (lead's file), durable rules, or any other
workspace.

## 11. Honest failure modes to expect (do not panic; report)

- Downloads fail → §4 fallbacks; the sub-200 study must still complete on existing caches.
- Amplitude-trained θ goes multimodal or the error term absorbs everything → that IS an H1-relevant result;
  report the θ-only vs with-error-term contrast.
- Shape inference wins per-point and fails QOI coverage again → quantify the split; that sharpens H1.
- Agent ties random again → H2 confirmed with the correct compass; that is a publishable strengthening.
- Everything ties A1 → the study's conclusion is "the remaining error is not reachable by any lever we own,
  now shown with amplitude training and the full spectrum" — which is exactly the claim Andrew wants
  challenged before we make it. Write it with the same care as a win.
