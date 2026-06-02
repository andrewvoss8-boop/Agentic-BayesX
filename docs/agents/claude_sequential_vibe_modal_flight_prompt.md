# Claude Code Prompt: Sequential Vibe/Modal/Flight Setup

Paste this into Claude Code after opening the project root.

```text
You are the lead agent for the next Agentic BayesX research loop.

Read:
- AGENTS.md
- CLAUDE.md
- docs/agents/how_to_run.md
- artifacts/reports/sequential_vibe_modal_flight_20260602/task.md
- artifacts/reports/sequential_vibe_modal_flight_20260602/sequential_research_packet.md
- artifacts/reports/sequential_vibe_modal_flight_20260602/nuts_backend_choice.md
- artifacts/reports/sequential_vibe_modal_flight_20260602/experiment_schema.json
- artifacts/reports/sequential_vibe_modal_flight_20260602/summary.json
- artifacts/tests/sequential_vibe_modal_flight_setup_report.json

Use plain English. Do not claim NUTS/HMC is active yet. The current packet is a setup packet: PSD conventions, staged synthetic data, Matérn forcing, variability bookkeeping, plots, schema, and checker.

Your first job:
1. Summarize the setup in five bullets.
2. Confirm the dB convention is PSD-space.
3. Confirm what is fixed, what is generated, and what future NUTS/HMC should infer.
4. Propose the next implementation task card for the NumPyro NUTS model.
5. Stop for human approval before asking Codex or Cursor helpers to implement anything.
```

