# Runner Prompt — Codex GPT-5.5

Open Codex on folder `../Agentic_BayesX_runner_codex_gpt55`, select model **GPT-5.5**, then paste
the block below.

```text
You are the RUNNER for Agentic BayesX (tool: Codex GPT-5.5). You work in an isolated copied
workspace. Do not assume any other agent will help you.

Read first:
- AGENTS.md
- CLAUDE.md
- docs/CODEX.md
- docs/agents/competitive_full_experiment/task_card_full_experiment.md
- docs/agents/competitive_full_experiment/README_handoff_and_isolation.md
- artifacts/reports/runner_codex_gpt55_20260602/task.md
- artifacts/reports/sequential_vibe_modal_flight_20260602/  (all files)

Your task: implement the FULL sequential dome/tray vibe→modal→flight experiment described in the
task card, ending in posterior inference and QOI intervals. Required scope:
- PSD-space dB smoothline (factor = 10**(dB/10)); dome = m1, tray = m2.
- Tray vibe test, dome modal test, coupled modal test, first flight, then 10 later builds/flights.
- Learn build-to-build variability and sensor-noise scale. Keep flight-to-flight at the fixed
  known 3 dB. Use a Matérn forcing GP (NOT RBF).
- Full FRF/PSD likelihood vs peak-feature likelihood comparison (show posterior + QOI differences).
- NUTS/HMC inference with diagnostics: divergences, step size, tree depth, ESS, R-hat.
- 95% and 99% input spectra and tray 3*RMS / 3*GRMS QOI intervals after flights.
- Human-review packet (Markdown + figures), manifest.json, and checker-backed outputs.

Hard rules:
- Existing random-walk/random-scan Metropolis is PROTOTYPE/LEGACY. If you claim posterior inference,
  use NUTS/HMC. If you must use another sampler, say why in a labeled note; do not present it as NUTS.
- numpyro is not installed and Python is 3.9.6. State exactly how you handled this (install, venv,
  or documented blocker). Never fabricate sampler output, plots, or metrics.
- Do NOT edit the immutable checker files: harness/checkers/verify_artifacts.py,
  harness/checkers/check_canary.py, tests/test_posterior_recovery.py, tests/test_mdof_transfer.py.
- Do NOT copy setup/reference assets and present them as newly generated outputs.
- A checker pass is not proof of physical correctness. Define every named quantity (numerator,
  denominator, coordinate, excitation, BC, units, expected limiting/resonance behavior) before plotting.

Write ALL outputs to: artifacts/reports/runner_codex_gpt55_20260602/
You may fail. If blocked, write the exact failing command and stop. Do not overstate results.

When done, produce the report contract from README_handoff_and_isolation.md: commands.md,
files_changed.md, assumptions_ledger, nuts_diagnostics, figures/, checks.json, known_failures.md,
review_request.md, manifest.json, and packet.md. Then stop.
```
