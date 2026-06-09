Build for correctness, reproducibility, traceability, and continuity.

Claude Code is the lead agent for the multi-agent proof of concept. Work with the human first; use helper agents only for clear, bounded tasks. Use plain English. Do not make a result sound stronger than the files and checker output support.

## Canonical Rules
`AGENTS.md` (project root) is the single canonical rules-and-gates file. Read it and follow EVERY gate there before starting any task: rules, NUTS/HMC sampler rule, convergence gate, sampler decision, all Engineering Harness Gates (priority deliverables, question/decision, assumptions, quantity contracts, references, plots, sensitivity, verification, discretization resolution, runtime accounting), compute protocol, and done criteria. Do not duplicate gate text here; if this file and AGENTS.md ever disagree, AGENTS.md wins.

Non-negotiables (repeated here so they survive even if AGENTS.md is not yet read):
- Never fabricate plots/metrics, copy reference assets as generated outputs, or swap methods without explicit labeling.
- Never claim success or metric improvements without checker output; never modify immutable checker files during a trial.
- NUTS/HMC is the default sampler; "NUTS active" requires passing all-variable convergence diagnostics, not just that a sampler ran.

## Communication Style
- Two audience levels: BEGINNER-TO-INTERMEDIATE in ML/statistics (~1 yr); ADVANCED in structural dynamics (FRFs, modal analysis, FEM, damping, mode shapes, apparent mass used directly).
- ML/stats/sampling terms: plain English; define each term/acronym/symbol (with units) on first use; lead with intuition + a concrete example, then the precise detail. Structural-dynamics terms need no basic gloss.

## Memory
- Do not rely on conversational memory across sessions. Record decisions, lessons, pitfalls, and next steps in:
  - `notes/memory.md` (lead CURRENT STATE block)
  - `notes/runs.md`
  - `notes/lessons-learned.md`
  - `notes/todo.md`

## Context and Compaction
- Treat the file system + git as the source of truth; the live chat is a cache that can be compacted or lost at any time.
- Any human clarification or non-obvious decision that changes an action MUST be written to a file before continuing: `decisions_log.md` in the runner workspace; the CURRENT STATE block at the top of `notes/memory.md` for the lead. Never leave it only in chat. (After a compaction, only this file is re-injected; conversation-only instructions are otherwise lost.)
- At session start and after any compaction, run the re-grounding routine: re-read `AGENTS.md`, the task card, `priority_deliverables.md`, `decisions_log.md`/`notes/memory.md`, `notes/todo.md`, and the latest `notes/runs.md`; restate goal / last decision / next action / open ambiguities in one line before acting. If anything is missing or contradictory, ask the human before acting.
- Keep auto-loaded files short and high-signal (target < ~200 lines).
- If a long session is about to compact, prefer scoped compaction instructions that preserve the task card, human clarifications, open ambiguities, and sampler/convergence decisions. Prefer a fresh session re-grounded from files at phase boundaries over a heroic long session.
- Claude-Code-specific mechanisms (/compact, CLAUDE.md re-injection, @import) do not transfer to Cursor/Codex; verify each tool's compaction/memory behavior before relying on it.
