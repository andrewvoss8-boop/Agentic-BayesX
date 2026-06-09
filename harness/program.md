# harness/ — what lives here and why

This folder is the 2026-05-27 bootstrap checker scaffolding, kept because parts of it are
IMMUTABLE and still verified by replay scripts. The live, durable harness rules are NOT
here: they are the gates in project-root `AGENTS.md` (canonical) plus
`docs/harness/agentic-engineering-quality-gates.md` (the reusable structural-dynamics
guide). `CLAUDE.md` is a short lead-role pointer to `AGENTS.md`.

## Contents
- `checkers/manifest.sha256` — IMMUTABLE hash manifest pinning `checkers/verify_artifacts.py`,
  `checkers/check_canary.py`, `tests/test_posterior_recovery.py`, and `tests/test_mdof_transfer.py`.
  Replay scripts (e.g. `scripts/run_pipeline.sh`, runner `run_*.sh`) verify it with
  `shasum -a 256 -c harness/checkers/manifest.sha256`. Do not edit, move, or rename anything
  it pins; that breaks every recorded replay.
- `checkers/` — the two pinned checker scripts above.
- `driver.py` — generic trial runner: verifies the manifest before and after a run, executes
  a configured run + check command, and writes a run bundle (metadata/logs) under
  `artifacts/runs/`. Used by the original canary trial; reusable but not required by current
  runner workflows (those carry their own `run_all.sh` + `check.py`).
- `configs/canary_trial.json`, `specs/canary_artifacts.json` — the May-27 canary trial config,
  kept for traceability of the first checker-gated loop (`experiments/canary/`).

## Rules
- Never modify immutable checker files during a trial (AGENTS.md anti-cheating rule).
- New experiments should NOT add to this folder; give each run its own workspace under
  `artifacts/reports/<run>/` with its own `run_all.sh`, `check.py`, and `checker_report.json`.
