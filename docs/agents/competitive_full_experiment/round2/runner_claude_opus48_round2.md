# Round-2 Runner Prompt — Claude Code Opus 4.8

Open Claude Code on a FRESH isolated copy `../Agentic_BayesX_runner_claude_opus48_r2`, select
**Opus 4.8**, launch with `--dangerously-skip-permissions` (isolated copy only), paste:

```text
You are the RUNNER for Agentic BayesX, ROUND 2 (tool: Claude Code Opus 4.8). Runner only, NOT master.
Isolated copied workspace.

FIRST: print your working directory and assert it is this runner's workspace, NOT the master repo.
Refuse to proceed if you are in the master repo.

Read first:
- AGENTS.md, CLAUDE.md
- .claude/agents/runner.md
- docs/agents/competitive_full_experiment/round2/task_card_full_experiment_round2.md
- artifacts/reports/sequential_vibe_modal_flight_20260602/ (all files)
- Optional context on round-1 misses: artifacts/reports/runner_comparison_20260602/human_feedback.md

Then do Step 0 (priority clarification -> priority_deliverables.md) and the priority deliverables and
round-1 fixes in the round-2 task card. Headline ask = the per-flight coupled INTERFACE ACCELERATION
RESPONSE PSD with mean/95/99 bands vs the original test spec, as an animated GIF; plus the forcing
overlay and the flight-3*GRMS-vs-vibe-RMS overlay. Keep your round-1 strengths (real NUTS, 4 chains,
non-centered, convergence gate) AND this round report R-hat/ESS over the RAW latents too, not only the
monitored marginals; meet the source-backed bar (rank-normalized split-R-hat < 1.01; bulk AND tail
ESS >= 100 x chains; 0 divergences ideal — see the task card). Resolve the QOI-driving resonances (no
clipped peaks) and run a resolution
sensitivity check. Every figure gets a legend. Write runtime.json.

Write ALL outputs to: artifacts/reports/runner_claude_opus48_round2_20260602/
You may fail; report blockers exactly. Never claim NUTS active or "pass" without converged diagnostics
over all variables. Produce the full round-2 report contract, then stop.
```
