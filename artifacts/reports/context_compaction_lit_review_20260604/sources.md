# Sources — Context & Compaction Literature/Web Review

- **Role:** reader (lit/web review). Evidence-gathering only; no durable files edited.
- **Session date (UTC):** 2026-06-04
- **Fetch tool used:** `curl` from Bash (WebSearch/WebFetch are NOT in this session's toolset; confirmed by tool list). Network egress confirmed (HTTP 301/200 from docs.anthropic.com).
- **HTML→text:** local `html.parser` script (`/tmp/h2t.py`); **PDF→text:** `pypdf` (no `pdftotext` available).
- **Raw captures + hashes:** saved under `raw/` in this folder; `.txt` extractions in this folder. SHA-256 listed per source. Anyone can re-verify with `shasum -a 256 raw/<file>.html`.
- **Verification convention:** "Verified" = I fetched it this session, HTTP 200, and read the relevant text directly from the capture. `[TO-VERIFY]` = could not fetch usable content. `[OPINION]` = my own inference, not in the source.

> Caveat on hashes: HTML pages are dynamic; the SHA-256 fixes *what I read this session* but the same URL may return different bytes later. The extracted `.txt` quotes are the durable evidence.

---

## A. Anthropic — primary/official

### A1. Effective context engineering for AI agents (Anthropic Engineering)
- **URL:** https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- **HTTP:** 200 | **bytes:** 171310 | **sha256:** `005b666db5d50d0ad7467a27a658df35cd94d208651dfba946070fe848e93f56`
- **Capture:** `raw/anthropic_context_engineering.html` → `anthropic_context_engineering.txt` | **Status:** Verified
- **Supports:**
  - "Context rot": as tokens grow, recall accuracy decreases; context is a finite resource with an "attention budget" (transformer n² attention). Treat context as precious.
  - Three named long-horizon techniques: **Compaction**, **Structured note-taking (agentic memory)**, **Sub-agent architectures**.
  - **Compaction** = summarize a near-full context and reinitialize a new window with the summary; in Claude Code it "preserves architectural decisions, unresolved bugs, and implementation details while discarding redundant tool outputs," continuing with the summary + the **five most recently accessed files**. "The art of compaction lies in the selection of what to keep vs discard; overly aggressive compaction can lose subtle but critical context whose importance only becomes apparent later." Recommends tuning the compaction prompt: maximize recall first, then precision. Safest light-touch form = tool-result clearing.
  - **Structured note-taking**: agent writes notes to memory outside the window, pulled back later (NOTES.md, to-do lists); persists across context resets. Cites the memory tool (public beta, Sonnet 4.5).
  - **Sub-agents**: focused tasks with clean context windows; each may use tens of thousands of tokens but returns a condensed 1,000–2,000-token summary; "clear separation of concerns."
  - Choice guidance: compaction for back-and-forth; note-taking for iterative work with milestones; multi-agent for parallel research.
  - Just-in-time retrieval: keep lightweight identifiers (paths, queries, links) and load on demand; CLAUDE.md dropped in up front + grep/glob just-in-time (hybrid).
- **Does NOT support:** any auto-compaction trigger %; any claim specific to non-Claude tools (Cursor/Codex); anything about cross-session human-clarification capture.

### A2. Context editing (Claude Developer Platform docs)
- **URL:** https://docs.anthropic.com/en/docs/build-with-claude/context-editing
- **HTTP:** 200 | **bytes:** 1651795 | **sha256:** `eff3816ebd7aa59f6dbf7dbfbd7586b9cfd458fcbbfaf05711e4da4f98147578`
- **Capture:** `raw/docs_context_editing.html` → `docs_context_editing.txt` | **Status:** Verified
- **Supports:**
  - "For most use cases, **server-side compaction is the primary strategy**." Context editing = finer-grained control for specific scenarios.
  - `clear_tool_uses_20250919`: clears oldest tool results past a threshold, replaces with placeholder text; `clear_tool_inputs` optional. Config: `trigger` (default **100,000 input tokens**), `keep` (default **3** recent tool-use/result pairs), `clear_at_least`, **`exclude_tools`** (list of tools whose results are *never* cleared — "Useful for preserving important context").
  - `clear_thinking_20251015`: clears thinking blocks; `keep` default model-specific (Opus 4.5+/Sonnet 4.6+ keep all; earlier keep last turn).
  - **Combine with memory tool**: "When your conversation context approaches the configured clearing threshold, Claude receives an automatic warning to preserve important information" → Claude can write essential info to memory files before clearing.
  - SDK (client-side) compaction exists but Anthropic recommends server-side.
- **Does NOT support:** Claude Code interactive `/compact` internals (different surface); guarantees about what a *chat-session* compaction keeps.

### A3. Memory tool (Claude Developer Platform docs)
- **URL:** https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/memory-tool
- **HTTP:** 200 | **bytes:** 969300 | **sha256:** `6bece50e8bd18d36a7e357b0e0a26b0ab0dea8fc8ea4226c7942574e5297e7ab`
- **Capture:** `raw/docs_memory_tool.html` → `docs_memory_tool.txt` | **Status:** Verified
- **Supports:** memory tool = file-based store/retrieve **across conversations**; client-side tool, app executes ops locally, restrict to `/memories`. "Claude automatically checks its memory directory before starting tasks" and can "pick up where it left off." Key primitive for just-in-time retrieval.
- **Does NOT support:** that it is enabled by default in Claude Code chat sessions (it's a Developer Platform/API tool you wire up).

### A4. Claude Code — Manage Claude's memory (docs)
- **URL:** https://docs.anthropic.com/en/docs/claude-code/memory
- **HTTP:** 200 | **bytes:** 1371383 | **sha256:** `ea57470e175b8b5acfc9033f13efe2349450cab5b565db41ddd10b0d56f02c1f`
- **Capture:** `raw/docs_cc_memory.html` → `docs_cc_memory.txt` | **Status:** Verified
- **Supports (most directly relevant to our problem):**
  - **"What survives compaction":** *"Project-root CLAUDE.md survives compaction: after `/compact`, Claude re-reads it from disk and re-injects it into the session. Nested CLAUDE.md files in subdirectories are NOT re-injected automatically... If an instruction disappeared after compaction, it was either given **only in conversation** or lives in a nested CLAUDE.md that hasn't reloaded yet. **Add conversation-only instructions to CLAUDE.md to make them persist.**"*
  - CLAUDE.md loaded into context at the **start of every session**; "context rather than enforced configuration"; target **under 200 lines**; longer files reduce adherence.
  - **`@path/to/import`** syntax expands files into context at launch (max depth 4 hops); `CLAUDE.local.md` for gitignored personal prefs; can import `@~/.claude/...`.
  - **AGENTS.md:** *"Claude Code reads CLAUDE.md, **not** AGENTS.md."* Recommends a CLAUDE.md that imports AGENTS.md if a repo uses both.
  - **Auto memory:** notes Claude writes itself from your corrections/preferences (distinct from CLAUDE.md you write); subagents can have their own auto memory.
- **Does NOT support:** auto-compact threshold value (that's in A5/B3); any guarantee nested rules reload before drift.

### A5. Claude Code — Manage costs effectively (docs)
- **URL:** https://docs.anthropic.com/en/docs/claude-code/costs
- **HTTP:** 200 | **bytes:** 1212107 | **sha256:** `8c1d14947472ac649820429cdcbb6c475c3407ce18d3e383d6e5b8a5a2861a46`
- **Capture:** `raw/docs_cc_costs.html` → `docs_cc_costs.txt` | **Status:** Verified
- **Supports:** Claude Code auto-compacts ("summarizes conversation history when approaching context limits"). **Custom compaction instructions** two ways: (1) `/compact Focus on code samples and API usage`; (2) a `# Compact instructions` (a.k.a. summary instructions) section in **CLAUDE.md** to tell Claude what to preserve during summarization. `/usage` shows token usage.
- **Does NOT support:** an explicit % trigger here (LangChain B3 attributes "95% of context window" to Claude Code; treat that number as third-party).

### A6. Claude Code — Subagents (docs)
- **URL:** https://docs.anthropic.com/en/docs/claude-code/sub-agents
- **HTTP:** 200 | **bytes:** 2047195 | **sha256:** `dfc9a29203bdf0c9b5fa510a099c9df0f6735bb1a7cb8a8a0410e7a02b5c31b6`
- **Capture:** `raw/docs_cc_subagents.html` | **Status:** Verified
- **Supports:** "Each subagent runs in its **own context window**" with custom system prompt/tools/permissions; "does that work in its own context and returns only the summary." Subagents receive only their own system prompt + basic env (not full CC system prompt). **`isolation: worktree`** gives an isolated git copy. Subagents work within a single session; background agents/agent teams for parallel/communicating sessions. Use to isolate high-volume output so only the summary returns.
- **Does NOT support:** that subagents see the lead's full conversation/clarifications (they get a task brief, not the full trace) — relevant counterpoint to Cognition C1.

### A7. How we built our multi-agent research system (Anthropic Engineering)
- **URL:** https://www.anthropic.com/engineering/multi-agent-research-system
- **HTTP:** 200 | **bytes:** 175536 | **sha256:** `20d66dff2bb8408ec8c8704212701fc9de0afa30236c05f4f1725e939804432a`
- **Capture:** `raw/anthropic_multi_agent.html` | **Status:** Verified (fetched; keyword-scanned: 64 "subagent", "external memory", "context window")
- **Supports:** orchestrator–worker multi-agent pattern; lead saves plan to memory to survive >200k truncation (per LangChain B3 quoting this); subagents isolate search context and return condensed results. (Used as corroboration, not primary-quoted beyond keyword scan.)
- **Does NOT support:** that multi-agent is always better — Anthropic notes higher token cost; pair with Cognition's caution.

### A8. Building effective agents (Anthropic Engineering)
- **URL:** https://www.anthropic.com/engineering/building-effective-agents
- **HTTP:** 200 | **bytes:** 180672 | **sha256:** `468a839b34aaaf9b029c5b63c1755faedb100b3a41b5939b8760a7b5e3ba23dc`
- **Capture:** `raw/anthropic_building_effective_agents.html` | **Status:** Verified (fetched; keyword-scanned: orchestrator-workers, "do the simplest thing")
- **Supports:** "use the simplest solution possible; only increase complexity when needed"; orchestrator-workers pattern. Background, not compaction-specific.

### A9. Claude Code — Common workflows (docs)
- **URL:** https://docs.anthropic.com/en/docs/claude-code/common-workflows
- **HTTP:** 200 | **bytes:** 1539491 | **sha256:** `fe3d348a7040a89a38b0d4250cd9e23cce4666f538f015baef4d866bb9722650`
- **Capture:** `raw/docs_cc_common_workflows.html` | **Status:** Verified (fetched; keyword-scanned: `/compact`, `/clear`, subagents). Corroborates `/clear` and `/compact` exist as session commands.

---

## B. Other vendors / leading practitioners

### B1. OpenAI — A practical guide to building agents (PDF)
- **URL:** https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
- **HTTP:** 200 | **bytes:** 7335065 | **sha256:** `1903c2b1837b206d1951d8a3d1124515aee1bebebd8f2448c630c75a6b0aad86` | **34 pages**
- **Capture:** `raw/openai_practical_guide.pdf` → `openai_practical_guide.txt` | **Status:** Verified
- **Supports:** "**maximize a single agent's capabilities first**"; add agents only when prompts/tools fail (complex conditional logic; tool overload). Two multi-agent patterns: **Manager (agents-as-tools)** — central LLM orchestrates, "instead of losing context or control, the manager intelligently delegates"; **Decentralized (handoffs)** — peers transfer the **latest conversation state** on handoff. **Guardrails** (input/output, tripwires) for safety. Prompt **templates with policy variables**.
- **Does NOT support:** anything about compaction/context-window mechanics — this guide is silent on compaction (keyword scan: no "compaction"/"context window"/"memory" hits in body). Use it for single-vs-multi-agent and guardrail framing only.

### B2. OpenAI — Agents platform guide (web)
- **URL:** https://platform.openai.com/docs/guides/agents
- **HTTP:** 200 | **bytes:** 296696 | **sha256:** `3a060336167f394efc44bc044531cb8bc2ae7a3c6f9781fcc230ad0aeb8f0e5b`
- **Status:** `[TO-VERIFY]` — fetched 200 but the body is a **JS app shell**; extracted text has no usable content (only ~2 nav keyword hits). Not used as evidence. (Use B1 PDF instead.)

### B3. LangChain — Context Engineering for Agents (blog)
- **URL:** https://blog.langchain.com/context-engineering-for-agents/ (identical bytes from `blog.langchain.dev` mirror)
- **HTTP:** 200 | **bytes:** 197937 | **sha256:** `efe4979fef3bfc2f25a25eb85b957e1653a71361db912caba94dcf7cedff9992`
- **Capture:** `raw/langchain_context_engineering.html` → `langchain_context_engineering.txt` | **Status:** Verified
- **Supports:**
  - Clean taxonomy: **Write** (scratchpads in-session; memories across sessions), **Select** (pull relevant notes/memories; code agents use a narrow always-loaded file set — "Claude Code uses CLAUDE.md, Cursor/Windsurf use rules files"), **Compress** (summarization; trimming/pruning), **Isolate** (sub-agents; runtime state object; sandboxes).
  - Quotes Anthropic multi-agent researcher: LeadResearcher saves plan to Memory because >200k tokens gets truncated.
  - Attributes "**auto-compact after you exceed 95% of the context window**" to Claude Code (third-party characterization).
  - "**Summarization at agent–agent boundaries**" (credits Cognition) to reduce tokens during hand-off; notes summarization can drop key decisions, and **Cognition uses a fine-tuned model** for it.
  - Karpathy framing: context window ≈ RAM; context engineering ≈ OS curating RAM.
  - Risk: bad memory selection ("context no longer belongs to the user" — Simon Willison example).
- **Does NOT support:** numbers as Anthropic-official (the 95% figure is LangChain's wording).

### B4. Cognition — Don't Build Multi-Agents (blog, Walden Yan)
- **URL:** https://cognition.ai/blog/dont-build-multi-agents
- **HTTP:** 200 | **bytes:** 143882 | **sha256:** `21229553cd17d113c29829fd3c55791182c5f0df09ddc79e52660b0fd3553bc4`
- **Capture:** `raw/cognition_dont_build_multi.html` → `cognition_dont_build_multi.txt` | **Status:** Verified
- **Supports (directly relevant to our lead/runner gap):**
  - **Principle 1: "Share context, and share full agent traces, not just individual messages."**
  - **Principle 2: "Actions carry implicit decisions, and conflicting decisions carry bad results."** Default-rule-out architectures that violate these.
  - Prefer **single-threaded linear agents**; parallel sub-agents risk conflicting assumptions. When traces get too long, introduce an LLM that **compresses history into key details/events/decisions** ("hard to get right"; Cognition has fine-tuned a smaller model for it).
  - On Claude Code (June 2025): subagents answer questions, don't write code in parallel, precisely because they lack the main agent's context; benefit is keeping investigative tokens out of the main history.
  - "Running multiple agents in collaboration only results in fragile systems [in 2025]; decision-making too dispersed, context not shared thoroughly."
- **Does NOT support:** that subagents are never useful (it endorses read-only/isolation subagents); not compaction-mechanics.

### B5. Manus — Context Engineering for AI Agents: Lessons from Building Manus (blog, Yichao 'Peak' Ji)
- **URL:** https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus
- **HTTP:** 200 | **bytes:** 229880 | **sha256:** `6944b22215bebaf6266c47daa91e6261a080a3a2a4cdbe9ca0395b60b186c899`
- **Capture:** `raw/manus_context_engineering.html` → `manus_context_engineering.txt` | **Status:** Verified
- **Supports:**
  - **Restorable compression:** "any irreversible compression carries risk"; compression should be **restorable** — drop a web page's content but **keep the URL**; drop a doc's text but **keep the path**. Shrink context without permanently losing information.
  - **File system as externalized memory:** unlimited, persistent, agent-operable.
  - **Recitation / "Manipulate Attention Through Recitation":** Manus keeps a `todo.md` and **rewrites it each step**, reciting objectives into the **end of context** to fight "lost-in-the-middle" and goal drift.
  - **"Keep the Wrong Stuff In":** erasing failed actions "removes evidence"; leaving errors in context lets the model adapt.
  - **KV-cache stability:** keep a **stable prefix**, **append-only** context, deterministic serialization; "Mask, Don't Remove" tools (logit masking) rather than mutating tool list.
- **Does NOT support:** structural-engineering specifics; numbers transfer directly to our stack only as principles.

---

## C. In-repo references (the prompt asked to check these)

### C1. "Bilionis on Agents" / "why scientific autonomy needs a harness" (Ilias Bilionis, repo copies)
- **Paths:** `Bilionis on Agents copy.md`, `why scientific autonomy needs a harness (ilias substack).md`
- **Status:** Verified (read from repo this session)
- **Supports our problem statement directly:**
  - *"over time, the agent's context drifts. What was in the prompt at the beginning of the run tends to be forgotten; the agent stops, asks a stupid question, declares victory after a small improvement, or just takes shortcuts."*
  - A **harness** "endow[s] an agent with long-term memory and keep[s] it on track" via prompt injection and code scaffolding.
  - *"With Codex... AGENTS.md... keeps it in its context. **If the context is compacted, it may read it again.**"* (Claude Code uses CLAUDE.md.) — confirms the re-read-on-compaction mechanism our recommendations lean on.
  - Memory system: "Do not rely on conversational memory across sessions"; dated notes in `notes/memory.md`, `notes/runs.md`, `notes/todo.md`.
- **Note:** this is the philosophical basis already encoded in our CLAUDE.md/AGENTS.md "Memory" section; it covers **cross-session** memory but **not within-session compaction** — exactly the gap this review targets.

### C2. "When AI Agents Start Cheating" (Ilias Bilionis, repo copy)
- **Path:** `When AI Agents Start Cheating (ilias substack).txt` | **Status:** Verified (read; no context/compaction keyword hits) — relevant to anti-cheating gates, **not** to compaction. Logged for completeness.

---

## Coverage vs. the brief's 7 sub-questions
| Question | Best evidence |
|---|---|
| (a) externalize state/decisions | A1, A3, A4, B3 (write), B5 (filesystem), C1 |
| (b) re-ground after compaction | A4 (CLAUDE.md re-injected; "add conversation-only instructions to CLAUDE.md"), B5 (recitation), C1 |
| (c) structured memory (scratchpads/logs/state) | A1, A3, B3 (write/select), B5 (todo.md) |
| (d) subagents vs one long session | A1, A6, A7, B1, **B4 (caution)** |
| (e) fresh session vs compact | A1 (compaction vs note-taking vs multi-agent tradeoff), B4 (single-threaded + compression model), A5 (auto-compact) |
| (f) verify compaction didn't drop constraints | A4 ("what survives compaction"), A2 (`exclude_tools`, memory-before-clear warning), B4 (Principle 1/2), B5 (restorable) |
| (g) hooks/automation | A2 (server-side compaction config, memory-tool warning), A4 (`@import`, auto memory), A5 (CLAUDE.md compact instructions), A6 (`isolation: worktree`) |
