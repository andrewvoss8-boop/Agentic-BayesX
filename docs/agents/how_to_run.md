# Plain-English Multi-Agent Workflow

Purpose: give Claude Code, Codex, Cursor, and the human a shared way to run one careful structural-dynamics research loop without pretending the agents are more autonomous than they are.

## Current Setup

- Claude Code is the lead agent. It works with the human, writes task cards, and asks for helper work only when the task is specific.
- Codex can be launched manually as a helper for independent checks, code review, or a scoped implementation task.
- Cursor can be used manually for review or implementation, using the project rules and agent role files.
- The first proof-of-concept loop uses the existing fresh 2DOF StatFEM/FBS workflow. It does not change the science model.

## Run Order

1. Start Claude Code in the project root.
2. Paste the starter prompt from `docs/agents/claude_code_starter_prompt.md`.
3. Claude writes or revises a task card using `docs/agents/task_template.md`.
4. The human approves the task card.
5. Claude asks the human to launch Codex or Cursor only with a specific helper prompt.
6. The helper writes its result into the first-loop packet or gives text for Claude to place there.
7. Claude collects command output, checker output, review notes, open risks, and the next prompt.
8. The human approves any notes updates or durable rule changes.

## First Loop Output

The first packet lives at:

`artifacts/reports/multi_agent_first_loop_20260602/`

It contains:

- `task.md`: what the loop is trying to do.
- `framing.md`: decision, objective, and what remains human judgment.
- `assumptions.md`: assumptions for this workflow trial.
- `quantity_contracts.md`: quantities that must be defined before plots or checks.
- `commands.md`: commands to run and where outputs land.
- `checks.json`: machine-readable check status.
- `sources.md`: sources used by the reader role.
- `review.md`: independent review notes.
- `next_prompt.md`: prompt for the next loop.
- `manifest.json`: paths, roles, commands, sources, checks, and open risks.

## Sampler Standard

For future Bayesian updating, use NUTS/HMC as the default sampler. The current random-walk/random-scan Metropolis code is a prototype baseline. Do not call NUTS active until code, diagnostics, and checker output exist.

## Manual Helper Prompts

Use the role prompts in:

- `docs/codex_prompts/multi_agent/`
- `docs/agents/roles/`
- `.cursor/agents/`

The helper should always say what files it read, what command output supports its claims, and what remains uncertain.

