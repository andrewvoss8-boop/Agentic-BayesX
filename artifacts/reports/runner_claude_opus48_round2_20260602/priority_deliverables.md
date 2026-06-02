# Priority Deliverables — Round 2 (Runner: Claude Code Opus 4.8)

Date: 2026-06-02
Workspace (isolated, asserted NOT master): `Agentic_BayesX_runner_claude_opus48_r2`
Output folder: `artifacts/reports/runner_claude_opus48_round2_20260602/`

This file is Step 0. It restates the human's PRIORITY deliverables in my own words, states each
acceptance test, flags ambiguous terms with my chosen interpretation, and records where each priority
is delivered. A priority with no delivered artifact is a FAILURE; an "assumed" interpretation without
human confirmation is a WARNING (I could not ask mid-run, so I state the assumption prominently and,
where cheap, produce both interpretations).

---

## P1 (HIGHEST) — Key plot: per-flight coupled interface acceleration RESPONSE PSD vs spec, as a GIF

**My restatement.** The headline product is the *coupled-system interface acceleration response PSD*
(units g^2/Hz) — i.e. the acceleration response at the dome/source interface DOF of the coupled
dome+tray system under flight forcing, NOT the forcing input. For each flight I plot the posterior
predictive distribution of that response PSD as **mean + 95% + 99% credible bands**, overlaid on the
**original test spec** (the smoothline, g^2/Hz), on a **log-frequency axis**, one frame per flight,
assembled into an **animated GIF** that shows how the distribution evolves across the 11 flights.

**Defensible engineering question (GEVS / GSFC-STD-7000, verified source register):** does the test
spec ENVELOPE the flight interface environment across frequency? The PSD-envelope comparison (spec vs
flight response PSD at every frequency) is the PRIMARY check; the scalar 3·GRMS overlay (P3) is a
summary only and can hide a narrow-band exceedance.

**Acceptance tests.**
- Quantity contract for "interface acceleration response PSD" stated BEFORE plotting (DOF,
  numerator/denominator, excitation, BC, units, expected resonance behavior).
- GIF exists, 11 frames (one per flight), log-frequency x-axis, mean/95%/99% bands + spec line + legend.
- Bands come from a real, converged posterior (see P5), not fabricated.

**AMBIGUITY FLAG (term: "how the distribution evolves across flights" / "after each flight").**
Two defensible readings:
- (A) **Sequential assimilation**: after assimilating flights 1..k, show the predictive interface PSD
  for a future flight; bands should tighten/shift as flight data accumulates.
- (B) **Per-flight realized build**: each frame is the predictive interface PSD for *that* specific
  flight's build (build f), combining the posterior over structural parameters, the posterior over
  that flight's build effect, and the known flight-to-flight forcing GP.
Round-1 human words were "the ... interface accel PSD ... after each flight ... showing how that graph
changes with each flight." This is genuinely ambiguous. **Primary interpretation = (B) per-flight**,
because the task card title says "per-flight ... INTERFACE ACCELERATION RESPONSE PSD" and the dataset
ties build_id == flight_id (each flight is its own build), so per-flight build variation is the natural
frame-to-frame change. I ALSO produce a **secondary (A) sequential-assimilation** view (QOI/parameter
posterior tightening vs cumulative flights) because it is cheap and answers the "updating" reading.
Status: WARNING until human confirms which GIF they consider canonical.

**Delivered:** `figures/interface_response_psd_vs_spec.gif` (primary, B) + per-frame PNGs;
secondary sequential view `figures/sequential_assimilation_qoi.png`. Quantity contract in
`quantity_contracts_round2.md`. See `packet.md`.

## P2 — Forcing overlay (discrete sample curves vs original +6 dB forcing)

**My restatement.** Overlay all 11 flight forcing PSD draws as **discrete sample curves** (not just
smooth quantile bands) on the **original forcing PSD**. The original forcing sits +6 dB ABOVE the
flight mean (equivalently the flight mean is the project −6 dB offset below the original). Units N^2/Hz,
log-log.

**Margin note (verified).** The −6 dB flight-forcing offset is a PROJECT assumption, NOT a GEVS margin.
The GEVS qualification-vs-acceptance margin is +3 dB. I will NOT present 6 dB as a qualification margin
or conflate it with GEVS "+6 dB/oct" spectral slopes.

**Acceptance tests.** Figure shows 11 discrete forcing draws + original force PSD + flight mean, legend,
log-log axes; caption states the −6 dB offset is a project assumption.

**Delivered:** `figures/flight_forcing_overlay.png`.

## P3 — QOI vs test reference (flight tray 3·GRMS vs original vibe-test 3·GRMS)

**My restatement.** Plot the flight tray 3·GRMS sequence (per flight) overlaid with the **first-build
vibe-test 3·GRMS reference (43.9 g)** and the **smoothline input 3·GRMS (28.3 g)**. The large
qual-vs-flight gap is expected; annotate it and use a **log-y axis** so both scales stay visible.

**Verified meaning.** 3·GRMS = 3σ (~99.73%) peak estimate of a zero-mean Gaussian response — an
estimate, NOT a hard max. This scalar overlay is a SUMMARY; P1's PSD-envelope is the primary check.

**Acceptance tests.** Figure shows per-flight tray 3·GRMS + the 43.9 g and 28.3 g reference lines,
log-y, annotation of the gap, legend.

**Delivered:** `figures/flight_qoi_vs_vibe_reference.png`.

## P4 — Resolution (consume shared grid; mode-local refinement; sensitivity check)

**My restatement.** Consume the shared `sequential_dataset.json` frequency grid; do not silently
regenerate a coarser truth. Ensure the QOI-driving resonances (tray ~86 Hz, dome ~93.5 Hz; half-power
band Δf = 2ζf_n ≈ 3.4 Hz at ζ≈0.02) are resolved using **mode-local refinement** (extra points
clustered near each f_n), not just more global points. Document grid spacing + rationale + the
runtime/accuracy tradeoff, and run a **resolution sensitivity check** (refine near peaks, report the
QOI/posterior shift). No clipped peaks. No invented "lines per band" hard rule — keep density a
documented assumption and PROVE resolution via the sensitivity check.

**Acceptance tests.** Resolution doc + figure showing coarse-vs-refined response near peaks; reported
3·GRMS QOI shift between grids; statement that QOI-driving modes are resolved.

**Delivered:** `figures/resolution_sensitivity.png`, `resolution_analysis.md`.

## P5 — Sampler + convergence (NUTS/HMC, ≥4 chains, non-centered, source-backed gate over ALL latents)

**My restatement.** Use NUTS/HMC (NumPyro). ≥4 chains, adequate warmup, **non-centered** hierarchical
build/flight latents. Report R-hat and ESS over **ALL sampled variables including raw latents**, and
self-gate using the SOURCE-BACKED thresholds (Stan Reference Manual / Vehtari et al. 2021):
- max rank-normalized split-R-hat **< 1.01** (1.05 only as a labeled early-workflow fallback);
- **both bulk-ESS AND tail-ESS ≥ 100 × #chains** (≥ 400 with 4 chains) for reported parameters;
  nuisance latents documented;
- divergences: **0 ideal**; any nonzero is a hard-WARN / bias risk; > 2% post-warmup = fail.
If not converged, say so and do NOT report a clean "pass" or "NUTS active".

**Acceptance tests.** `nuts_diagnostics.json` with per-variable rank-split-R-hat, bulk-ESS, tail-ESS,
divergence count/fraction, tree depth, step size, #chains, #draws; self-gate verdict; honest labeling.

**Delivered:** `nuts_diagnostics.json`, `nuts_diagnostics.md`, gate verdict in `checks.json` + `packet.md`.

## P6 — Plot hygiene
Every figure/panel has a legend; log-frequency axes for FRF/PSD; dual axes clearly labeled. Delivered
across all figures; checked in `checks.json`.

## P7 — Runtime
`runtime.json` with `active_runtime_s` (sum of per-command execution times) and `elapsed_wallclock_s`,
`active <= elapsed`. Delivered.

## P8 — Isolation
At start, printed working directory and asserted it is the runner workspace, NOT the master repo.
Confirmed: path contains `runner_claude_opus48_r2`, no git remote. Recorded in `commands.md`.

---

## Not allowed (honored)
- The four immutable checker files are NOT edited (verified via `shasum -a 256 -c
  harness/checkers/manifest.sha256` → all OK; re-verified at end).
- No copying setup/reference assets as generated outputs.
- No "pass"/"NUTS active" claim unless chains converged by the gate above.
