# Round-1 Checker Subagent — paste into a fresh Claude Code Opus 4.8 session

Run from the master repo root: `/Users/avoss/Downloads/bayesX/Agentic BayesX`

```text
You are the CHECKER subagent for Agentic BayesX (model: Opus 4.8). Read .claude/agents/checker.md
first. Report only what passed, failed, or was not checked. Do not infer success from plots.

Runner workspaces / outputs:
- Cursor:  workspace ../Agentic_BayesX_runner_cursor_composer25 ; output .../runner_cursor_composer25_20260602/
- Opus:    workspace . (master) ; output artifacts/reports/runner_claude_opus48_20260602/
- Codex:   workspace . (master) ; output artifacts/reports/runner_codex_gpt55_20260602/

For EACH runner:
1. Re-run the commands listed in that runner's commands.md, in the correct working directory. Record
   exit codes. (Opus/Cursor use a venv they created; recreate or reuse it as their commands.md says.)
2. Run: shasum -a 256 -c harness/checkers/manifest.sha256 and record the result.
3. Open every JSON report (checks.json, manifest.json, nuts_diagnostics.json, assumptions_ledger,
   posterior_results/results) and QUOTE: divergences, max R-hat (over ALL variables), min ESS,
   nuts_active, and the reported tray 3*GRMS 95%/99% intervals.
4. Apply a CONVERGENCE READ (report, do not silently pass): flag any variable with R-hat >= 1.05 or
   ESS_bulk < 200. State per runner whether the headline intervals rest on converged chains.

Write a consolidated checks summary + per-runner pass/fail/not-checked with quoted evidence to
artifacts/reports/runner_comparison_20260602/checker_review.md. Note anything you could not reproduce.
```
