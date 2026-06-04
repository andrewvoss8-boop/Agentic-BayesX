# Recommendations — Context & Compaction for Agentic BayesX

**Role:** reader / lit-review. This is a **proposal for human approval**, not an applied change. No durable
files (CLAUDE.md, AGENTS.md, checkers, `notes/`, runner code) were edited. Evidence IDs (A1, B4, …) refer
to [sources.md](sources.md). `[OPINION]` = my inference beyond a source.

---

## 0. The gap, restated in our terms (evidence-backed)

- We confirmed nothing in our harness mentions **compaction**, **context windows**, or **re-grounding**.
  Our "Memory" rule (CLAUDE.md/AGENTS.md) handles **cross-session** continuity (externalize to files +
  git) but is silent on **within-session auto-compaction**.
- This is a real, named failure mode, not a hypothetical:
  - Anthropic: "context rot" + an "attention budget"; long-horizon work needs compaction / note-taking /
    sub-agents (A1). Claude Code **auto-compacts** near the limit (A5; "~95% of context window" per B3).
  - Our own repo reference (Bilionis, C1): "the agent's context drifts… what was in the prompt at the
    beginning tends to be forgotten… declares victory after a small improvement, or just takes shortcuts."
- **Two concrete holes for us:**
  1. **Within-session loss:** a runner's interactive clarifications with the human live **only in chat**.
     Anthropic states plainly (A4): after `/compact`, **only project-root CLAUDE.md is re-injected**;
     **conversation-only instructions are lost** unless written to a file. So an auto-compact can silently
     drop the very nuance the human just supplied.
  2. **Cross-session blindness:** the lead (separate session) **cannot see** the runner's clarifications at
     all. Cognition's Principle 1/2 (B4) says this is exactly when conflicting implicit decisions produce
     bad results: "share context, and share full agent traces, not just individual messages."

**Design stance (evidence-backed):** treat the **file system + git as the source of truth**, keep the live
chat as a cache. Every decision/clarification that would change an action must be **externalized to a file
before it can be compacted away**, and a **re-grounding step** must re-read those files. This is the
unifying recommendation of A1, A4, B3, B5, and C1.

---

## 1. DO THIS NOW (cheap, high-value, no durable-rule change needed)

These are habits/artifacts a lead or runner can adopt **today** inside the existing rules. They do not, by
themselves, change CLAUDE.md/AGENTS.md/checkers, so they don't need the durable-rule approval gate — but
item 1.1 proposes a *new artifact file*, so confirm naming with the human.

### 1.1 `decisions_log.md` per runner workspace (externalize clarifications) — **highest value**
- **What:** an append-only, dated file at `runs/round3/<tool>/decisions_log.md`. Every time the human
  clarifies an ambiguous instruction in chat, or the runner makes a non-obvious choice, append one line:
  `[UTC timestamp] DECISION/CLARIFICATION: <what> | RATIONALE: <why> | SOURCE: human-chat / inference`.
- **Why (evidence):** A4 — conversation-only instructions are lost on compaction unless written to a file;
  B4 Principle 1/2 — share full decisions or get conflicting actions; B5 — recitation/externalized state;
  A1 — structured note-taking "excels for iterative development with clear milestones."
- **Re-grounding payoff:** because it's a file, it (a) survives compaction, (b) can be `@`-imported into
  CLAUDE.md (A4) so it is **re-injected** after `/compact`, and (c) is visible to the lead and reviewers.
- **Cost:** ~1 line per decision. `[OPINION]` This is the single biggest risk-reducer for our live failure.

### 1.2 Append-only "current state + next action" block in `notes/memory.md` (for the lead)
- **What:** the lead maintains, at the **top** of its working notes, a short dated block:
  `CURRENT STATE: … | LAST DECISION: … | NEXT ACTION: … | OPEN AMBIGUITIES: …`. Update it before any
  risky/long step and after each human decision; commit to git (we already commit after each decision).
- **Why:** A1 (note-taking) + B5 (recitation pushes the goal into recent attention, fighting drift) +
  C1 (drift is our documented failure). This is the lead-session analogue of the runner's decisions_log.
- **Note:** keep it short. A4 warns CLAUDE.md adherence drops past ~200 lines; `notes/memory.md` isn't
  auto-loaded, so the lead must **re-read it after any compaction** (see 1.4).

### 1.3 Custom compaction instructions (zero-code, Claude Code only)
- **What:** when a long session is about to compact, prefer an explicit
  `/compact Preserve: the task card, all human clarifications, open ambiguities, sampler/convergence
  decisions, and file paths of artifacts produced` over silent auto-compact (A5 supports custom
  `/compact <instructions>`). For runners, also run `/compact` *proactively* at a natural milestone rather
  than letting auto-compact fire mid-thought.
- **Why:** A1 — "the art of compaction lies in what to keep vs discard"; A5 — Claude Code accepts custom
  compaction instructions. **Caveat:** this is **Claude-Code-specific**; Cursor/Codex runners have their
  own mechanisms — do not assume parity (B2 unverified). `[OPINION]`

### 1.4 A written **re-grounding routine** (checklist, not code)
- **What:** a 5-line routine an agent runs **at session start and immediately after any compaction**:
  1. Re-read the task card and `priority_deliverables.md`.
  2. Re-read `decisions_log.md` (runner) or the state block in `notes/memory.md` (lead).
  3. Re-read `notes/todo.md` + latest `notes/runs.md` entry.
  4. Re-state in one line: current goal, last decision, next action, open ambiguities.
  5. If anything is missing/contradictory, **ask the human before acting** (consistent with our
     "do not guess silently" rule).
- **Why:** A4 (re-injection only covers root CLAUDE.md; everything else must be re-read), B5 (recitation),
  C1 (drift). This is the concrete answer to brief question (b)/(f).

### 1.5 Prefer "fresh session + read the files" over heroic long sessions for *new* phases
- **What:** when starting a clearly separable phase (e.g., move from FEM setup → NUTS run → review),
  start a **fresh session** and re-ground from files, rather than compacting a giant session.
- **Why:** A1 — compaction is "the first lever," but note-taking/sub-agents handle long horizons better;
  B4 — long single-threaded sessions need a real compression step that is "hard to get right." Since our
  state is already externalized (notes/, packets, git), a fresh session re-grounded from files is **lower
  risk than trusting a summary** (restorable-over-lossy, B5). `[OPINION]` but well-supported.

---

## 2. LATER (durable changes needing human approval)

Each is written so the human can accept/reject independently. None should be self-applied — they touch
durable rules, roles, notes scaffolding, or checkers (the very things the brief forbids me to edit).

### 2.1 Proposed CLAUDE.md / AGENTS.md "Context & Compaction" rule (text for approval)
Add a short section (mirroring both files, since Claude reads CLAUDE.md and Codex reads AGENTS.md — A4):

> **## Context and Compaction**
> - Treat the file system + git as the source of truth; treat the live chat as a cache that can be
>   compacted or lost at any time.
> - Any human clarification or non-obvious decision that changes an action MUST be written to a file
>   (`decisions_log.md` in the runner workspace; the state block in `notes/memory.md` for the lead)
>   **before** continuing — do not leave it only in chat.
> - At session start and **after any compaction**, run the re-grounding routine: re-read the task card,
>   `priority_deliverables.md`, `decisions_log.md`/`notes/memory.md`, `notes/todo.md`, and the latest
>   `notes/runs.md`; re-state goal/last-decision/next-action/open-ambiguities in one line before acting.
> - Keep externalized state files short and high-signal (target < ~200 lines for any auto-loaded file).
> - If a long session is about to compact, prefer explicit, scoped compaction instructions that preserve
>   the task card, all human clarifications, open ambiguities, and sampler/convergence decisions.

- **Evidence:** A1, A2, A4, A5, B4, B5, C1.
- **Note for human:** A4 says Claude Code ignores AGENTS.md. To keep one source of truth, consider a
  `CLAUDE.md` that `@`-imports `AGENTS.md` (A4 explicitly recommends this), then the compaction rule lives
  once. **Decision needed from you.** `[OPINION]`

### 2.2 Runner role (`docs/agents/roles/runner.md`) — add a live decisions log + re-grounding
- Add to **Do:** "Maintain `decisions_log.md` (append-only) capturing every human clarification and
  non-obvious choice with timestamp + rationale." and "Run the re-grounding routine at start and after any
  compaction."
- Add to **Output:** "`decisions_log.md`."
- **Evidence:** B4 (share full decisions), A4 (survive compaction), A1 (note-taking).

### 2.3 Lead role (`docs/agents/roles/lead.md`) — current-state block + read-runner-decisions
- Add to **Do:** "Keep a `CURRENT STATE / LAST DECISION / NEXT ACTION / OPEN AMBIGUITIES` block at the top
  of `notes/memory.md`, updated before risky steps and after each human decision." and "Before assigning
  or reviewing runner work, read that runner's `decisions_log.md`" (closes the cross-session blindness in
  §0 hole 2).
- **Evidence:** B4 Principle 1/2, A1, B5, C1.

### 2.4 `@`-import the live decision file so it survives compaction (config, needs approval)
- In each runner workspace's `CLAUDE.md`, add `@decisions_log.md` (and optionally `@priority_deliverables.md`)
  so they are re-injected after `/compact` (A4: imports load at launch; root CLAUDE.md re-injected on
  compaction). Keep them short to respect the ~200-line adherence guidance (A4).
- **Risk/caveat:** only **root** CLAUDE.md is guaranteed re-injected; imports load at launch and after
  re-read — verify behavior in-app before relying on it. Mark `[TO-VERIFY]` until tested in our client.

### 2.5 A **shared, hash-locked re-grounding/compaction checker** (driver-run, not self-graded)
This is the harness-grade fix and aligns with our audit goal of moving off self-graded gates.
- **What the checker verifies on a finished packet:**
  1. `decisions_log.md` exists, is non-empty, and is append-only (timestamps monotonic; no rewritten
     history vs git diff).
  2. Every human clarification referenced in the packet/report has a matching `decisions_log.md` entry
     (cross-reference by keyword/quote) — catches "clarified in chat, never externalized."
  3. A re-grounding marker exists (e.g., the one-line restate) at session start and after any logged
     compaction event.
  4. `notes/memory.md` has a current-state block updated within the run window (date check).
- **Why:** A4/B4 give the *content* requirements; our harness philosophy requires a **driver-run,
  hash-locked** check rather than trusting the runner's self-report. `[OPINION]` on exact encoding;
  the requirement itself is evidence-backed.
- **Caveat (honest):** a checker can verify *files exist and are consistent*; it **cannot verify the
  summary preserved the right nuance** (A1: "what to keep vs discard" is judgment). Document this as
  residual risk + a manual review item, per our Verification gate.

### 2.6 Optional: a lightweight pre-compaction hook (automation, needs approval)
- **What:** if/when our client exposes a pre-compact hook (Claude Code supports session hooks; A2 shows the
  API memory-tool "warning before clearing" pattern), wire a hook that, before compaction, dumps
  `decisions_log.md` + the current-state block to disk and `git add`s them.
- **Evidence:** A2 (memory-before-clear pattern), A6 (hooks in subagent frontmatter exist). Mark
  `[TO-VERIFY]` — confirm the exact hook surface in our installed client version before promising it.

---

## 3. Policy answers the brief explicitly asked for

### 3.1 Fresh session vs. compact (proposed policy)
- **Compact** (or keep going) when the work is a single continuous thread needing back-and-forth and the
  recent context is the point (A1: "compaction maintains conversational flow"). Use **scoped** `/compact`
  instructions (A5).
- **Start fresh** when crossing a phase boundary (setup → sampling → review), when the session is long and
  state is already externalized, or after a confusing/error-filled stretch. Re-ground from files (§1.4).
  Rationale: our state is in files+git, so a fresh re-grounded session is **more reliable than a lossy
  summary** (B4 "hard to get right"; B5 "irreversible compression carries risk"). `[OPINION]`, well-supported.
- **Never** rely on chat-only memory across a compaction or session boundary (A4, C1).

### 3.2 Subagent vs. one long session (proposed policy)
- **Use a subagent / isolated session** for high-volume, read-mostly work whose details you won't reuse:
  literature fetches (this very task), log/test crunching, big file scans. It returns a **condensed
  summary** and keeps the lead's context clean (A1, A6 "own context window", A7).
- **Keep it in the main thread (single-threaded)** for the core reasoning/decision chain, especially the
  Bayesian-modeling and FEM-setup decisions, because **conflicting implicit decisions across parallel
  agents are our biggest reliability risk** (B4 Principle 1/2; OpenAI B1 "maximize a single agent first").
- **Do NOT run parallel runners that must agree on shared modeling choices** without a shared,
  file-based decision record — our competitive runners are *independent by design* (good), but any
  *collaborative* split must share full traces/decisions via files (B4). `[OPINION]` consistent with B4.
- Our existing reviewer/checker/reader subagents fit the "isolated, returns-a-summary" pattern well (A6).

---

## 4. Priority summary (what I'd approve first)

| Rank | Item | Type | Approval needed? | Evidence |
|---|---|---|---|---|
| 1 | `decisions_log.md` per runner (§1.1) | now | confirm filename | A4,B4,B5 |
| 2 | Re-grounding routine after compaction (§1.4) | now | no | A4,B5,C1 |
| 3 | Lead current-state block in notes/memory.md (§1.2) | now | no | A1,B5,C1 |
| 4 | CLAUDE.md/AGENTS.md "Context & Compaction" rule (§2.1) | later | **yes (durable rule)** | A1,A4,B4,C1 |
| 5 | Runner + Lead role edits (§2.2/2.3) | later | **yes (durable)** | B4,A1 |
| 6 | Shared hash-locked re-grounding checker (§2.5) | later | **yes (checker)** | A4,B4 |
| 7 | `@`-import decisions_log + pre-compact hook (§2.4/2.6) | later | **yes + [TO-VERIFY]** | A2,A4,A6 |

---

## 5. Honest limitations of this review
- I could not fetch usable text from the OpenAI **web** agents guide (B2, JS shell); I relied on the OpenAI
  **PDF** (B1), which is silent on compaction mechanics — so OpenAI informs only the single-vs-multi-agent
  and guardrail points, not compaction.
- The "auto-compact at ~95%" figure is **LangChain's** characterization of Claude Code (B3), not an
  Anthropic-official number I located; treat as approximate.
- Claude-Code-specific behaviors (`/compact`, CLAUDE.md re-injection, `@import`, hooks) do **not**
  automatically transfer to the **Cursor** and **Codex** runners; their compaction/memory surfaces need
  separate verification before any cross-tool rule claims parity. Marked `[TO-VERIFY]`.
- A checker can confirm decision files exist and are consistent; it **cannot** confirm a compaction
  preserved the right nuance — that remains human review (documented residual risk per our Verification gate).
