# Runner Task — Cursor Composer 2.5

Date: 2026-06-02
Workspace: ../Agentic_BayesX_runner_cursor_composer25 (isolated copy)
Output folder (write everything here): artifacts/reports/runner_cursor_composer25_20260602/

## What to do
Implement the FULL sequential dome/tray vibe→modal→flight Bayesian experiment defined in
docs/agents/competitive_full_experiment/task_card_full_experiment.md and your runner prompt
docs/agents/competitive_full_experiment/runner_cursor_composer25.md.

## Required scope (summary; full detail in the task card)
- PSD-space dB smoothline (factor = 10**(dB/10)); dome = m1, tray = m2.
- Tray vibe test, dome modal test, coupled modal test, first flight, then 10 later builds/flights.
- Learn build-to-build variability and sensor-noise scale; flight-to-flight fixed at 3 dB.
- Matern forcing GP (NOT RBF).
- Full FRF/PSD likelihood vs peak-feature likelihood comparison.
- NUTS/HMC inference with diagnostics (divergences, step size, tree depth, ESS, R-hat).
- 95% and 99% input spectra; tray 3*RMS / 3*GRMS QOI intervals after flights.
- Human-review packet, plots, manifest.json, checker-backed outputs.

## Hard rules
- numpyro is not installed; Python is 3.9.6. State exactly how you resolved it. Never fake output.
- Do NOT edit immutable checker files (see task card). Verify with
  shasum -a 256 -c harness/checkers/manifest.sha256.
- NUTS/HMC if you claim posterior inference; label any other sampler and say why.
- Do not copy setup/reference assets and present them as generated.
- A checker pass is not proof of physical correctness.

## Report contract
Populate this folder per README_handoff_and_isolation.md: commands.md, files_changed.md,
assumptions_ledger.(md|json), nuts_diagnostics.(md|json), figures/, checks.json, known_failures.md,
review_request.md, manifest.json, packet.md.

## You may fail
If blocked, write the exact failing command in commands.md and stop. Do not overstate results.
