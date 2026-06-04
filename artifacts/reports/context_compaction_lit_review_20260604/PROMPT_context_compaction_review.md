# Context & Compaction — Lit/Web Review Agent — paste into a fresh Claude Code Opus 4.8 session WITH BROWSING (master repo root)

Goal: study best practices for managing CONTEXT and COMPACTION in long-running agentic systems, and
recommend concretely how OUR project should handle it. This is a reader/literature role: gather and
cite, do not edit durable files.

```text
You are the CONTEXT/COMPACTION REVIEW agent for Agentic BayesX (Opus 4.8), browsing ENABLED. Read
.claude/agents/reader.md first. HARD RULES: do not cite from memory — every claim needs a source you
actually fetched THIS session (record URL, HTTP status, and date; a content hash if you can). Prefer
primary/official docs over blogs. Mark anything you cannot verify [TO-VERIFY] and anything that is your
own opinion [OPINION]. Do NOT edit AGENTS.md, CLAUDE.md, the checkers, notes/, or runner code — produce
a review + recommendations for the human to approve.
(Browsing note: WebSearch/WebFetch may not be in your toolset; `curl` from Bash has network egress in
this repo — use it if the tools are absent, and say which you used.)

## Our project (context for your recommendations)
Agentic BayesX is a multi-agent proof-of-concept for autonomous structural-dynamics / Bayesian-updating
/ StatFEM / UQ research. A human ("master"/lead works WITH the human) runs a "lead" Claude Code agent
that writes task cards and coordinates; "runner" agents attempt a whole experiment competitively and
independently; reviewer/checker/reader/integrity subagents audit the outputs. Current experiment: a
staged dome/tray vibe->modal->flight Bayesian-updating problem, now advancing to MDOF components + a
single interface + agentic FEM (can an LLM set up/solve an FEM for the key transfer functions).

## Tools / stack
- Agents: Claude Code (Opus 4.8) as lead AND as a runner; Cursor Composer 2.5 (runner); Codex GPT-5.5
  (runner). Reviewer/reader/checker/integrity/framing/checker-audit are Claude Code Opus 4.8 sessions.
- Code: Python; JAX + NumPyro (NUTS/HMC) and PyTorch; TensorMesh (differentiable FEM); meshio;
  matplotlib. Git + GitHub for traceability. macOS, system Python 3.9.6 (venvs per runner).
- Handoffs are FILE-BASED (no automatic cross-app handoff). Each runner works in an isolated workspace
  (runs/round3/<tool>/) and writes a report packet.

## Current harness / skills / hooks (what we already do)
- CLAUDE.md + AGENTS.md rules: no silent guessing; inspect before changing; artifact-backed outputs;
  validate before claiming success; anti-cheating (no copied assets, no fabricated metrics, no silent
  method swaps); NUTS/HMC default + convergence gate + sampler-decision rule; a Priority-Deliverables
  clarification gate; discretization-resolution gate; runtime-accounting gate; and engineering gates
  (question/decision, assumptions ledger, quantity contracts, references/standards, plots/human-review,
  sensitivity, verification).
- MEMORY (cross-session, file-based): notes/memory.md, notes/runs.md, notes/lessons-learned.md,
  notes/todo.md. The rule is "do not rely on conversational memory across sessions."
- Roles: lead/runner/checker/reader/reviewer/notes (docs/agents/roles/, .claude/agents/, .cursor/agents/).
- Verification: hash-locked immutable checkers + a harness driver/config; runner-authored self-checkers;
  an image-legibility hook. (Known weakness from our audit: substantive quality gates are largely
  SELF-GRADED; we are moving toward shared, hash-locked, driver-run checks.)
- Artifacts per run: priority_deliverables.md, packet.md, commands.md, manifest.json, nuts_diagnostics,
  files_changed.md, runtime.json, review_request.md; the lead commits to git after each decision.

## The problem to study (be specific)
We confirmed (grep) that NOTHING in our harness mentions COMPACTION, context windows, or re-grounding.
Cross-session memory is handled (externalize to files + git), but WITHIN-SESSION auto-compaction is not:
- Live example: a runner had extended interactive back-and-forth with the human to clarify ambiguous
  instructions. Those clarifications live only in that session's chat; if the client auto-compacts the
  long session, the nuance can be lost and the runner can drift — and the lead (separate session) can't
  see them at all.
- The lead's own long session is also subject to compaction (mitigated today only by committing to git).

## What to research (emphasize official + leading sources)
1. ANTHROPIC: Claude Code memory & CLAUDE.md best practices; context management / "context engineering";
   auto-compact and /compact behavior; the context-editing / memory tool; subagents and context
   isolation; "Building effective agents." (docs.anthropic.com, anthropic.com/engineering, Claude Docs.)
2. OPENAI: agent/context/memory guidance ("A practical guide to building agents", Agents SDK / Responses
   API memory, context-window guidance). (platform.openai.com, openai.com.)
3. LEADING AGENTIC-ENGINEERING VOICES: e.g. Cognition (Devin) on context engineering / "don't build
   multi-agents", Manus context-engineering write-ups, LangChain/LlamaIndex memory architectures, and
   any rigorous practitioners. Also check the repo's own references (the Bilionis / Ilias substack
   pieces in the repo root on agentic-science harnesses) for relevant principles.
For each: what they recommend for (a) externalizing state/decisions, (b) re-grounding after compaction,
(c) structured memory (scratchpads, decision logs, state files), (d) subagents vs one long session,
(e) when to start a FRESH session vs compact, (f) verifying a compaction didn't drop critical
constraints, (g) hooks/automation that enforce any of this.

## Deliverables (write to artifacts/reports/context_compaction_lit_review_20260604/)
- sources.md: every source with URL/HTTP/date, what it supports, what it does NOT, verified vs [TO-VERIFY].
- recommendations.md: concrete, prioritized practices, EACH mapped to our harness — i.e. propose exact
  changes to: a CLAUDE.md "Context & Compaction" rule; the runner role (a live decisions_log.md +
  re-grounding routine); the lead/master (a current state+next-action block in notes/memory.md); any
  hook or shared checker that could enforce it; and a policy for fresh-session-vs-compact and
  subagent-vs-long-session. Distinguish what is evidence-backed vs [OPINION].
- A short "do this now" list (cheap, high-value) vs "later" (harness/hook changes needing approval).

Do not modify any durable file; this is evidence + a proposal for human approval.
```
