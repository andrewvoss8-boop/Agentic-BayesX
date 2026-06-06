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

## Communication Style

Write reports and packets for a reader who is beginner-to-intermediate in machine learning / statistics (~1 year of ML experience) but advanced in structural dynamics (fluent with FRFs, modal analysis, FEM, damping, apparent mass). So: plain English over jargon for ML/statistics terms (define them on first use) and define every ML/statistical variable in plain words (with units) when used; structural-dynamics terminology and symbols can be used directly. Lead with intuition + a concrete example before the formal statistical detail. (Full rule in `CLAUDE.md` / `AGENTS.md`.)

## Human Stop Point

The lead agent must stop for human review before changing project rules, checker expectations, sampler choice, or durable notes.

