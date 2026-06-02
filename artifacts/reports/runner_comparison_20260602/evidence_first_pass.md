# Lead First-Pass Evidence (file-grounded) — 2026-06-02

This is the LEAD's reading of the artifacts, to orient the independent subagent reviews. It is not a
substitute for them. Every claim cites a file the lead actually opened. A checker pass is NOT proof
of physical correctness, and tight posteriors here ride on synthetic data from the same model.

## Sampler / environment (the NUTS decision question)

| Item | Cursor Composer 2.5 | Claude Opus 4.8 | Codex GPT-5.5 |
|---|---|---|---|
| Installed a sampler? | venv, jax 0.4.23 / numpyro 0.13.2 (pinned for py3.9) | venv, numpyro 0.19.0 / jax 0.4.30 | none installed |
| Sampler used | real NUTS (NumPyro) | real NUTS (NumPyro) | custom PyTorch fixed-trajectory HMC (10 leapfrog) |
| Claims NUTS active? | yes (`checks.json: nuts_active true`) | yes (real) | NO — explicitly "NUTS active: false, HMC active: true" |
| Chains | 2 | 4 (1000 warmup + 1000 draws) | 2 |
| Convergence (from each runner's OWN diagnostics) | POOR: R-hat up to 1.83, ess_bulk≈3 on sigma_build_ln, sigma_sensor_ln, x_struct, several raw latents | CLEAN on monitored marginals: max R-hat 1.002, min ESS 942/1495 | POOR: R-hat up to 2.67 (full) / 4.57 (peak), ESS down to ~6 |
| Runtime tracked | none | "~2m48s" sampler step (no tracked total) | ~18 min (human-reported) |

Reads: cursor `nuts_diagnostics.md` + `checks.json` + `commands.md`; opus `nuts_diagnostics.md` +
`commands.md`; codex `nuts_diagnostics.md` + `known_failures.md` + `commands.md`.

### Lead interpretation (to be confirmed by reviewers)
- **Opus made the cleanest NUTS decision**: recognized numpyro absent, built an isolated venv,
  installed it, ran 4-chain NUTS, and reports converged diagnostics — but note the published summary
  table covers MONITORED MARGINALS (dome_hz, tray_hz, zetas, sigmas), not necessarily every raw
  hierarchical latent. Reviewers should open `nuts_diagnostics.json` and confirm the raw build/flight
  latents also converged, not just the marginals.
- **Cursor used real NUTS but under-resourced it** (2 chains, low ESS) and still reports
  `pass: true, nuts_active: true`. This is the clearest OVERCLAIM RISK: "NUTS done" while key
  hierarchical scales did not converge. It does admit poor R-hat in `known_failures.md`, so it is not
  hidden — but the checker did not catch it.
- **Codex declined to install and substituted custom HMC, labeled honestly** (did not claim NUTS).
  Good integrity on labeling; but convergence is also poor and intervals should not be trusted as final.
- **Shared harness gap:** the runner checkers pass on artifact existence + immutable hashes + a
  `nuts_active` boolean. None gate R-hat/ESS. So 2 of 3 non-converged runs "passed."

## Key-plot deliverable gap (matches human item B)

Figure inventories:
- Codex: `input_spectra_and_tray_qoi_intervals_after_flights.png` (one static figure).
- Opus: `03_input_spectra_95_99.png`, `04_qoi_intervals.png` (static).
- Cursor: `posterior_predictive_input_and_qoi.png` (static).

None is the requested per-flight evolving **coupled interface-acceleration PSD with mean/95/99 bands
vs the original spec**, and none is a GIF. None overlays all 10 flight forcing draws vs the +6 dB mean.

## Codex figure issues (confirmed by viewing the PNG)

`sequential_observations_truth_vs_observed.png`:
- Bottom-left "First flight input and tray response" (dual y-axis, blue force PSD / red tray PSD):
  **no legend**. Confirmed.
- Top-left "Tray vibe test": observed markers coarsely spaced around the ~90 Hz tray peak; peak
  likely under-resolved. Consistent with the human's frequency-spacing concern.
- Bottom-right "Observed flight 3*GRMS sequence": tray vs interface scalars vs flight id, but NO
  reference line for the original vibe-test 3*GRMS (matches human item C).

## Frequency-spacing decision (human item D) — needs reviewer dig
- Cursor `known_failures.md` notes "Modal/PSD subsampling stride 4/4" — i.e. it downsampled the grid
  by 4x for the likelihood. That directly bears on peak resolution and should be examined.
- Opus `known_failures.md` mentions subsampling but the exact grid choice/rationale needs checking.
- Codex grid rationale not yet located. Reviewers: find each runner's frequency-grid construction in
  its script and report (a) spacing, (b) whether log or linear, (c) any peak-resolution check.

## Scope creep / unrequested artifacts (for integrity + technical)
- The master working tree gained infographic files (`multi_agent_architecture_*.svg`,
  `runner_experiment_infographic.md`, `runner_experiment_artist_brief.txt`) not requested by the
  task card. Identify which runner produced them and whether effort went there instead of the
  requested key plot.

## What looks honest (credit where due)
- All three wrote candid `known_failures.md` files. Opus's is especially detailed (soft-argmax
  beta=45 labeled, flight likelihood = scalar QOI only, "truth recovery looks too good" caveat).
- Codex clearly labeled its sampler as not-NUTS. No silent method swap detected so far.
- Immutable checker hashes verified OK in all three `checks.json` / commands.
