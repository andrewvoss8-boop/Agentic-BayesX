# Task Card Template

Copy this into a loop packet as `task.md`.

## Task

One sentence describing the work.

## Why This Matters

What engineering or workflow decision this supports.

## Allowed Work

- Files or folders the agent may read.
- Files or folders the agent may edit, if any.
- Commands the agent may run.

## Not Allowed

- Immutable checker files that must not be edited.
- Any method that would be a hidden shortcut.
- Any output that would be copied from a reference and presented as generated.

## Main Command

`bash scripts/run_fresh_2dof_statfem_fbs.sh`

## Required Checks

- `python3 tests/test_fresh_2dof_rerun.py`
- `python3 tests/test_multi_agent_scaffold.py`
- `shasum -a 256 -c harness/checkers/manifest.sha256`

## Expected Files

- `commands.md`
- `checks.json`
- `sources.md`
- `review.md`
- `next_prompt.md`
- `manifest.json`

## Human Stop Point

The lead agent must stop for human review before changing project rules, checker expectations, sampler choice, or durable notes.

