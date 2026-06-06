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

## Compute Standard

For where to run multi-hour NUTS / TMCMC / FEM jobs, see `../compute_protocol.md`. Short version: CPU + High-RAM now; Colab A100 + float64 only when the method is validated AND the work is parallel-shaped (vectorized many-chain NUTS, TMCMC particles, or a large differentiable FEM); H100 in reserve. Do not use T4/L4/TPU for the posterior/eigen math (float64). Always force `jax_enable_x64`, checkpoint, pin the env, sync artifacts back to git, and reproduce the immutable checker hashes on the remote machine.

## Manual Helper Prompts

Use the role prompts in:

- `docs/codex_prompts/multi_agent/`
- `docs/agents/roles/`
- `.cursor/agents/`

The helper should always say what files it read, what command output supports its claims, and what remains uncertain.

## Competitive Full-Experiment Pressure Test

For the sequential dome/tray vibe-modal-flight research question, the human may choose a pressure-test mode: multiple runners attempt the whole experiment independently. Failure is allowed and useful. The goal is to see what each agent does under pressure, then let reviewers catch mistakes and improve the harness.

Planned runner set:

- Cursor Composer 2.5 runner.
- Claude Code Opus 4.8 runner.
- Codex GPT-5.5 runner.

Planned support agents:

- Claude Code Opus 4.8 reader for literature and source review.
- Claude Code Opus 4.8 reviewer for technical review.
- Claude Code Opus 4.8 integrity reviewer for copied assets, hidden method swaps, fake success, and weak verification.
- Claude Code Opus 4.8 checker for reproducing commands and reading reports.
- Claude Code Opus 4.8 notes role after human approval.

Runner rule: each runner should work in its own branch, worktree, or copied workspace and write its own packet under `artifacts/reports/runner_<tool>_<date>/`. Runners may implement the whole experiment, including NUTS/HMC, PSD-space dB handling, Matérn forcing, build/flight variability, staged tests, plots, and checks. Reviewers should expect mistakes and report them as evidence for better harness rules.

Handoff rule: external tools cannot reliably hand work to each other automatically from this repo alone. Use file handoffs: each runner writes a manifest, report, commands, checker output, and review request. The master reads those files and assigns review agents.

Automation that is reasonable now:

- Claude Code can use project subagents for reader, reviewer, checker, and notes if the extension supports them.
- The master can generate prompts for Cursor and Codex runners.
- The master can create per-runner task cards and expected packet paths.
- The master can aggregate runner reports after the human pastes paths or summaries back.

Automation that is not assumed:

- Claude Code cannot automatically control the Codex app or Cursor Composer unless a local CLI/API bridge is explicitly configured.
- Model selection is manual in each app unless that app exposes a setting for it.
- Cross-agent handoff is file-based and human-mediated for this proof of concept.

## Runner Isolation and Auto-Run

- Each runner works in its own disposable copied workspace and asserts its working directory at start; it refuses to run in the master repo.
- Because the workspace is disposable and immutable checker hashes are verified afterward, runners may auto-execute within it: Claude Code `--dangerously-skip-permissions`; Codex full-auto/no-approval; Cursor Agent Auto-Run. Never enable auto-run in the master repo. Confirm exact flags in-app.
- Runtime is compared across runners using `active_runtime_s` (sum of per-command execution time), which excludes human-approval wait; record `elapsed_wallclock_s` separately.
