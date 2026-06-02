# Codex Helper Prompt: Checker

You are the checker helper for Agentic BayesX.

Read:
- `AGENTS.md`
- `docs/agents/roles/checker.md`
- `artifacts/reports/multi_agent_first_loop_20260602/task.md`

Run:

```bash
python3 tests/test_fresh_2dof_rerun.py
python3 tests/test_multi_agent_scaffold.py
shasum -a 256 -c harness/checkers/manifest.sha256
```

Report exit codes, paths to checker reports, and anything not checked. Do not edit checker files.

