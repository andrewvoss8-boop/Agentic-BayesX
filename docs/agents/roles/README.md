# Agent Roles — CANONICAL definitions

The six role files here (lead, runner, reviewer, reader, checker, notes) are the single
canonical definitions. Tool-specific adapter copies exist and must defer to these:

- `.claude/agents/<role>.md` — Claude Code subagent adapters (frontmatter + short body).
- `.cursor/agents/<role>.md` — Cursor adapters (point here for instructions).
- `docs/codex_prompts/multi_agent/<role>.md` — Codex paste-in helper prompts (point here).

Edit role behavior HERE first, then propagate only what each adapter format needs.
All roles also obey the project-root `AGENTS.md` gates (canonical rules file).
