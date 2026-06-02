# Provenance / Isolation Note — Codex GPT-5.5 Round 2

This round-2 output was produced by the Codex GPT-5.5 runner running in the **master repo**, not in
its assigned isolated copy `../Agentic_BayesX_runner_codex_gpt55_r2`. This was an accidental launch.

Consequences handled by the lead (kept vs reverted):
- KEPT: this folder's round-2 deliverables (packet, manifest, scripts, priority_deliverables, etc.)
  and Codex's append-only additions to notes/lessons-learned.md, notes/memory.md, notes/runs.md,
  notes/todo.md.
- REVERTED: Codex's run had reset/gutted the ROUND-1 records
  (runner_codex_gpt55_20260602/{checks.json,commands.md,manifest.json}) and rewritten timing in
  runner_claude_opus48_20260602/nuts_diagnostics.json. Those round-1 files were restored to their
  canonical committed state so the round-1 vs round-2 comparison stays clean.

Isolation caveat for reviewers: because this ran in master, its replay paths and any environment it
created were relative to the master tree, and it did not honor the round-2 prompt's "assert cwd / refuse
to run in master" instruction (Opus did honor it and refused). Treat cross-runner runtime/replay
comparisons with this in mind. The harness fix is a MECHANICAL isolation guard (sentinel file /
refuse-if-origin-remote), not just a prompt instruction.
