# Round-2 Runner Prompt — Codex GPT-5.5

Open Codex on a FRESH isolated copy `../Agentic_BayesX_runner_codex_gpt55_r2`, select **GPT-5.5**, run
in full-auto / no-approval mode (isolated copy only), paste:

```text
You are the RUNNER for Agentic BayesX, ROUND 2 (tool: Codex GPT-5.5). Isolated copied workspace.

FIRST: print your working directory and assert it is this runner's workspace, NOT the master repo.
Refuse to proceed if you are in the master repo.

Read first:
- AGENTS.md, CLAUDE.md, docs/CODEX.md
- docs/agents/competitive_full_experiment/round2/task_card_full_experiment_round2.md
- artifacts/reports/sequential_vibe_modal_flight_20260602/ (all files)
- Optional context on round-1 misses: artifacts/reports/runner_comparison_20260602/human_feedback.md

Then do Step 0 (priority clarification -> priority_deliverables.md) and the priority deliverables and
round-1 fixes in the round-2 task card. Headline ask = the per-flight coupled INTERFACE ACCELERATION
RESPONSE PSD with mean/95/99 bands vs the original test spec, as an animated GIF; plus the forcing
overlay and the flight-3*GRMS-vs-vibe-RMS overlay.

Round-1 fixes specific to you: (a) DO try real NUTS first — install NumPyro in a venv as Opus did on
the same Python 3.9.6; only fall back to a labeled custom HMC if install genuinely fails, and say why.
(b) Use >=4 chains, longer warmup, non-centered hierarchical latents, and actually SAMPLE the
per-build/flight latents; self-gate convergence over ALL variables (your round-1 R-hat hit 4.57).
(c) Consume the shared sequential_dataset.json grid; do NOT regenerate a coarse 56-point grid that
clips the tray peak. (d) Give the first-flight dual-axis panel a legend.
Resolve the QOI-driving resonances and run a resolution sensitivity check. Write runtime.json.

Write ALL outputs to: artifacts/reports/runner_codex_gpt55_round2_20260602/
You may fail; report blockers exactly. Never claim NUTS active or "pass" without converged diagnostics.
Produce the full round-2 report contract, then stop.
```
