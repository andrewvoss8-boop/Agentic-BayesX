# Codex task: REPLICATE baseline

You are in `Agentic BayesX`. Read `AGENTS.md` and `docs/harness/agentic-engineering-quality-gates.md` first.

## Goal
Independently verify the existing bootstrap by re-running the full pipeline and matching checker-gated success.

## Steps
1. `export PYTHONPATH=.`
2. Run `bash scripts/run_pipeline.sh`
3. If anything fails, diagnose and fix only non-immutable files. Do NOT edit:
   - `harness/checkers/verify_artifacts.py`
   - `harness/checkers/check_canary.py`
   - `tests/test_posterior_recovery.py`
   - `tests/test_mdof_transfer.py`
   (listed in `harness/checkers/manifest.sha256`)
4. Run `python3 scripts/visualize_results.py` and confirm `artifacts/plots/manifest.json` lists all PNGs.
5. Inspect the review packet for the broad gates: numerical assumptions, standards/reference comparison, sensitivity, log frequency axes, and human-review figures.
6. Append a dated entry to `notes/runs.md` with commands, pass/fail, key metrics, and any broad-gate gaps.

## Deliverables
- All existing test reports updated under `artifacts/tests/`
- Plot manifest at `artifacts/plots/manifest.json`
- Short replication note in `notes/runs.md` (what matched, what differed)
- Explicit note on whether the packet satisfies the broad quality gates

## Stop condition
Do not claim success unless canary harness + both tests pass.
