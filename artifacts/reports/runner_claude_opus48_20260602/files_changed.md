# Files Changed — Claude Opus 4.8 Full Sequential Runner

## Created (code)
- `scripts/runner_claude_opus48_full_experiment.py` — JAX/NumPyro forward model + hierarchical
  NUTS inference (full FRF/PSD and peak-feature likelihoods), QOI predictive, and figures.
- `scripts/run_runner_claude_opus48.sh` — one-command replay (venv + run + checks).
- `tests/test_runner_claude_opus48_full_experiment.py` — NEW (non-immutable) runner checker;
  writes `checks.json` and re-verifies the four immutable checker hashes.

## Created (outputs in artifacts/reports/runner_claude_opus48_20260602/)
- `results.json`, `nuts_diagnostics.json`, `nuts_diagnostics.md`
- `assumptions_ledger.md`, `assumptions_ledger.json`
- `posterior_samples.npz`
- `figures/01_truth_vs_observed.png` … `figures/06_feature_map.png`
- `commands.md`, `files_changed.md`, `known_failures.md`, `review_request.md`
- `manifest.json`, `packet.md`, `checks.json`

## Created (environment, gitignored caches)
- `.venv_nuts/` — local virtual environment with numpyro 0.19.0 / jax 0.4.30 / matplotlib 3.9.4.

## Edited
- `notes/todo.md` — added a task section for this runner (planning only).

## Immutable checker files — NOT modified (re-verified)
- `harness/checkers/verify_artifacts.py`
- `harness/checkers/check_canary.py`
- `tests/test_posterior_recovery.py`
- `tests/test_mdof_transfer.py`

`shasum -a 256 -c harness/checkers/manifest.sha256` reports OK for all four (see checks.json
and console output in commands.md). The setup packet under
`artifacts/reports/sequential_vibe_modal_flight_20260602/` was read only, never modified.
