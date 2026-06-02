# Runner Comparison Packet — 2026-06-02

Master/lead orientation for the competitive full-experiment pressure test review.
This packet is collaborative with the human. The human has given first-pass feedback
(`human_feedback.md`); independent Opus 4.8 subagent reviews are launched separately
(`review_round1_*.md`).

## Where each runner actually wrote (corrected)

Isolation only held for ONE of three runners. This is a process finding, not a result.

| Runner | Ran in | Output folder |
|---|---|---|
| Cursor Composer 2.5 | its isolated copy | `../Agentic_BayesX_runner_cursor_composer25/artifacts/reports/runner_cursor_composer25_20260602/` |
| Claude Opus 4.8 | the ORIGINAL master repo | `artifacts/reports/runner_claude_opus48_20260602/` |
| Codex GPT-5.5 | the ORIGINAL master repo | `artifacts/reports/runner_codex_gpt55_20260602/` |

Consequence: Opus and Codex both wrote scripts/tests/figures into the master working tree
(e.g. `scripts/runner_claude_opus48_full_experiment.py`, `scripts/run_codex_gpt55_full_experiment.py`,
`tests/test_runner_*_full_experiment.py`, and some infographic SVGs/docs). They did not collide only
by luck of different filenames. Next iteration must force each runner into its own workspace.

## Files in this packet

- `human_feedback.md` — the human's first-pass review, verbatim + structured.
- `evidence_first_pass.md` — lead's file-grounded findings (verified from the artifacts).
- `comparison_matrix.md` — scope coverage per runner.
- `harness_improvements_proposed.md` — proposed rule/hook/checker changes (NEEDS HUMAN APPROVAL
  before any durable file is edited).
- `review_round1_reader.md`, `review_round1_technical.md`, `review_round1_integrity.md`,
  `review_round1_checker.md` — ready-to-paste prompts for four independent Opus 4.8 subagents,
  with corrected paths and the human's round-1 focus injected.

## Status

- Lead has read the three runners' nuts_diagnostics, known_failures, commands, checks, and one
  disputed figure, and recorded grounded findings here.
- Independent subagent reviews are NOT yet run. The lead cannot spawn subagents from its current
  toolset; the human launches them (see `review_round1_*.md`).
- No durable rules/notes/checker files were changed.
