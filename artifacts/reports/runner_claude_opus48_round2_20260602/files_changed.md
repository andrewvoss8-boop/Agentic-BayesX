# Files Changed / Created — Round 2 (Claude Opus 4.8 runner)

## New code (scripts/)
- `scripts/r2_forward.py` — differentiable JAX 2DOF coupled forward model (interface/tray accel-per-
  force, tray transmissibility, dome-only & coupled reciprocal inertance). Verified to reproduce the
  shared dataset clean curves (rel err 0.0).
- `scripts/runner_claude_opus48_round2.py` — hierarchical NUTS pipeline + all figures + diagnostics.
- `scripts/check_round2_artifacts.py` — runner-local (NON-immutable) acceptance checker → checks.json.
- `scripts/write_runtime_round2.py` — assembles runtime.json from per-command components.
- `scripts/run_runner_claude_opus48_round2.sh` — one-command replay (venv build + run + checkers).

## New environment
- `.venv_nuts/` — isolated venv (numpyro 0.15.3, jax/jaxlib 0.4.30, numpy 1.26.4, arviz 0.17.1,
  scipy 1.10.1, matplotlib, imageio, pillow). System Python 3.9.6 had none of these.

## New outputs (artifacts/reports/runner_claude_opus48_round2_20260602/)
- `priority_deliverables.md`, `quantity_contracts_round2.md`, `assumptions_ledger.md`
- `resolution_analysis.md`, `resolution_metrics.json`
- `nuts_diagnostics.json`, `nuts_diagnostics.md`, `posterior_samples.npz`
- `interface_psd_bands.json`, `pipeline_summary.json`, `runtime_pipeline.json`, `runtime.json`
- `commands.md`, `files_changed.md`, `known_failures.md`, `review_request.md`, `manifest.json`,
  `packet.md`, `checks.json`, `pipeline_run.log`
- `figures/interface_response_psd_vs_spec.gif` (+ `figures/gif_frames/frame_flight_00..10.png`)
- `figures/flight_forcing_overlay.png`, `figures/flight_qoi_vs_vibe_reference.png`
- `figures/resolution_sensitivity.png`, `figures/posterior_recovery.png`,
  `figures/sequential_assimilation_qoi.png`

## NOT modified
- The four immutable checker files (`harness/checkers/verify_artifacts.py`,
  `harness/checkers/check_canary.py`, `tests/test_posterior_recovery.py`,
  `tests/test_mdof_transfer.py`) — verified unchanged via `shasum -a 256 -c
  harness/checkers/manifest.sha256` before and after.
- The shared round-1 dataset/setup under `.../sequential_vibe_modal_flight_20260602/` — consumed
  read-only (grid, observations, priors).
- `notes/todo.md` — appended a round-2 section (allowed working note).
