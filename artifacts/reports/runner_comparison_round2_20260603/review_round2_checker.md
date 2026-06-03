# Round-2 Checker — paste into a fresh Claude Code Opus 4.8 session (master repo root)

```text
You are the CHECKER for Agentic BayesX, ROUND 2 (model: Opus 4.8). Read .claude/agents/checker.md
first. Report only what passed, failed, or was not checked, with quoted evidence. Do not infer
success from plots.

Round-2 outputs (all in this master repo):
- artifacts/reports/runner_cursor_composer25_round2_20260602/
- artifacts/reports/runner_codex_gpt55_round2_20260602/
- artifacts/reports/runner_claude_opus48_round2_20260602/

For EACH runner:
1. Reproduce its commands from commands.md, in the master repo.
   - Opus: scripts/run_runner_claude_opus48_round2.sh (+ scripts/r2_forward.py,
     runner_claude_opus48_round2.py, check_round2_artifacts.py, write_runtime_round2.py) are present.
   - Codex: scripts/run round-2 entrypoint is inside its output folder (run_round2.py / run_round2.sh).
   - Cursor: its SOURCE SCRIPTS WERE LOST in cleanup (see README). You CANNOT replay Cursor; record
     that explicitly and verify Cursor only by reading its committed JSON/figures.
2. Run shasum -a 256 -c harness/checkers/manifest.sha256 and record the result.
3. Open every JSON report (checks.json, manifest.json, nuts_diagnostics.json, runtime.json,
   resolution_metrics/resolution_sensitivity, interface_psd_bands, results/pipeline_summary) and
   QUOTE: sampler, num_chains, divergences, max R-hat (over ALL variables), min bulk-ESS, min
   tail-ESS, and the tray 3*GRMS 95%/99% intervals.
4. CONVERGENCE READ against the verified bar (report, don't silently pass): flag any variable with
   R-hat >= 1.01 or bulk/tail ESS < 100 x chains, and any divergence. State per runner whether the
   headline intervals rest on converged chains.
5. RUNTIME check: confirm active_runtime_s <= elapsed_wallclock_s and note discarded-run accounting.

Write a consolidated summary + per-runner pass/fail/not-checked with quoted evidence to
artifacts/reports/runner_comparison_round2_20260603/checker_review.md. Note anything not reproducible
(especially Cursor, which cannot be replayed).
```
