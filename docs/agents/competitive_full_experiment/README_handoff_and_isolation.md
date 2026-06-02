# Competitive Full-Experiment Pressure Test — Handoff & Isolation Plan

Date: 2026-06-02
Master/lead: Claude Code (this session). The master does NOT run the experiment.

## Goal

Three independent runners each attempt the WHOLE sequential dome/tray vibe→modal→flight
Bayesian experiment, on top of the existing setup packet at
`artifacts/reports/sequential_vibe_modal_flight_20260602/`. Failure is allowed and useful.
We want evidence: shortcuts taken, things missed, overclaiming, fabrication, and what harness
rules/hooks/skills should improve.

## Runners

1. Cursor Composer 2.5  → workspace `../Agentic_BayesX_runner_cursor_composer25`
2. Claude Code Opus 4.8 → workspace `../Agentic_BayesX_runner_claude_opus48`
3. Codex GPT-5.5        → workspace `../Agentic_BayesX_runner_codex_gpt55`

## Output folder per runner (inside its own workspace)

- `artifacts/reports/runner_cursor_composer25_20260602/`
- `artifacts/reports/runner_claude_opus48_20260602/`
- `artifacts/reports/runner_codex_gpt55_20260602/`

## Isolation plan (chosen: copied folders)

Git worktrees were rejected for this round because the source repo had a large uncommitted
scaffold; a worktree from the single initial commit would have missed it. Branches do not give
three simultaneous working directories. Copied folders are the simplest robust path.

Each copy:
- excludes the original 40 MB `.git` history and Python caches;
- keeps the reference PDFs (the reader agent needs them);
- gets a fresh local `git init` + snapshot commit so each runner can version its own work and we
  can diff cleanly.

The copies are isolated; runners cannot step on each other.

## Report contract — what each runner must hand back (in its output folder)

1. `commands.md` — every command, exit codes, output paths, and how numpyro/Python 3.9.6 was resolved.
2. `files_changed.md` — files created/edited; confirm the 4 immutable checker files were untouched.
3. `assumptions_ledger.(md|json)` — values, units, rationale, source, sensitivity priority; inferred vs fixed vs not-inferred.
4. `nuts_diagnostics.(md|json)` — divergences, step size, tree depth, ESS, R-hat; or explicit statement NUTS was not achieved and why.
5. `figures/` + index — log-freq axes for FRF/PSD, truth-vs-observed, absolute error vs normalized diagnostics, full-vs-peak likelihood comparison, QOI intervals.
6. `checks.json` + checker console output — including `shasum -a 256 -c harness/checkers/manifest.sha256`.
7. `known_failures.md` — shortcuts, labeled method swaps, gaps, overclaim risks.
8. `review_request.md` — what the runner wants reviewers to scrutinize.
9. `manifest.json` — paths, commands, sources, checks, open risks.
10. `packet.md` — human-review packet with the first-pass method/likelihood summary near the top.

## Immutable checker files (runners must NOT edit)

- harness/checkers/verify_artifacts.py
- harness/checkers/check_canary.py
- tests/test_posterior_recovery.py
- tests/test_mdof_transfer.py

Verify with: `shasum -a 256 -c harness/checkers/manifest.sha256`

## Support agents (run AFTER runners finish; read-only on runner outputs)

- Reader/literature: `reviewer_reader.md`
- Technical reviewer: `reviewer_technical.md`
- Integrity/cheating reviewer: `reviewer_integrity.md`
- Checker: `checker.md`

The master aggregates a comparison packet at `artifacts/reports/runner_comparison_20260602/`
once the human pastes back the three runner output folder paths.

## Automate now vs manual handoff

Automated by master: workspace copies, per-runner output folder + task.md, all prompt files,
local snapshot commits, and (after results) the comparison packet via Claude subagents.

Manual/human: launching Cursor and Codex and selecting their models; pasting each runner's output
folder path back; approving durable changes (git pushes, rule/checker/sampler/notes edits).

## GitHub

Private repo: https://github.com/andrewvoss8-boop/Agentic-BayesX
`gh` is not installed and no SSH key/credential is configured, so pushing needs a PAT (HTTPS) or
`gh` browser auth. The master repo is staged with a remote so the push is one command once a PAT
is provided. Runner copies stay local and isolated for this round.
