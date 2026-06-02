# First Multi-Agent Loop Task

## Task

Run a proof-of-concept multi-agent review loop around the existing fresh 2DOF StatFEM/FBS workflow.

## Why This Matters

This tests whether Claude Code, Codex, Cursor, and the human can coordinate through files, commands, reviews, and notes without making unbacked claims.

## Allowed Work

- Read project docs, notes, source, tests, and existing artifacts.
- Run the existing fresh workflow and scaffold checks.
- Write reports into `artifacts/reports/multi_agent_first_loop_20260602/`.
- Revise scaffold docs only with human approval after the first loop.

## Not Allowed

- Do not change the scientific model in this first loop.
- Do not edit immutable checker files listed in `harness/checkers/manifest.sha256`.
- Do not copy reference assets and present them as generated outputs.
- Do not call NUTS/HMC active until code, diagnostics, and checker output exist.

## Main Command

```bash
bash scripts/run_fresh_2dof_statfem_fbs.sh
```

## Required Checks

```bash
python3 tests/test_fresh_2dof_rerun.py
python3 tests/test_multi_agent_scaffold.py
shasum -a 256 -c harness/checkers/manifest.sha256
```

## Human Stop Point

The lead agent must stop for human review before changing project rules, checker expectations, sampler code, or durable notes.

