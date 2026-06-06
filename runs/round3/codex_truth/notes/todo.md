# Todo - Round 3 Codex Truth

Re-grounding summary: build independent synthetic truth in `runs/round3/codex_truth/`; last decision is that 11 flight forcing draws are reused across all 8 builds; next action is to author and validate the generator; open ambiguity is limited to schema interpretation and is documented in `report/priority_deliverables.md`.

- [x] Read allowed shared files only.
- [x] Create workspace, priority deliverables, and initial decisions log.
- [x] Implement independent truth generator and one-command replay.
- [x] Generate `dataset/observations.npz` plus observable-only `data_contract.md`.
- [x] Seal generator, true parameters, as-built draws, hidden model description, and scoring key.
- [x] Generate mesh exports and review figures.
- [x] Run validation/check scripts and record `checks.json`.
- [x] Record commands, runtime, files changed, and final packet.

## Stage-3 netCG republish plan

Priority deliverables: recompute only netCG-derived public quantities and sealed scoring keys using the canonical dynamic FBS interface-force definition; leave apparent-mass observations, interface acceleration PSD, as-built draws, model-form imperfections, and generator inputs unchanged.

- [x] Inspect the existing truth generator and published/scoring array schemas.
- [x] Patch only the netCG computation to use dynamic transmitted load interface force over `load_mass_kg`; retain rigid mass-ratio only as a low-frequency check.
- [x] Re-run the targeted netCG republish path inside `runs/round3/codex_truth/`.
- [x] Verify unchanged non-netCG arrays, f->0 rigid limit, resonant amplification, and updated runtime/log artifacts.
