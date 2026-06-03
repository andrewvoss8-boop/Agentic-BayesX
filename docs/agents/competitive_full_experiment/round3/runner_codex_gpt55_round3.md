# Round-3 Runner Prompt — Codex GPT-5.5

Open Codex on the master repo root, GPT-5.5, full-auto / no-approval (your work is confined to your
workspace), paste:

```text
You are the RUNNER for Agentic BayesX, ROUND 3 (Codex GPT-5.5).

Your ENTIRE workspace is runs/round3/codex/ — put EVERYTHING you create there (code/, tests/, report/
incl. report/mesh/ and report/packet.pptx, runtime.json, files_changed.md, priority_deliverables.md,
.venv*). Read shared inputs READ-ONLY; write nothing outside your workspace (not notes/, AGENTS.md,
CLAUDE.md, other runners, or prior rounds). Round-2 lesson for you specifically: do NOT run in the
master tree or edit shared/round-1/round-2 files — stay in runs/round3/codex/.

Read first:
- AGENTS.md, CLAUDE.md, docs/CODEX.md
- docs/agents/competitive_full_experiment/round3/task_card_round3.md  (the full spec — follow it)
- artifacts/reports/mdof_femagent_scoping_20260603/recon_and_scope.md
- runs/round3/spike/  (validated FEM baseline — start here)
- artifacts/reports/sequential_vibe_modal_flight_20260602/  (staged data, anchors)

Do Step 0 (priority_deliverables.md) then build round 3: MDOF dome (source) + MDOF tray (load) coupled
at a SINGLE interface; netCG QOI = interface force / load mass. Anchor first modes dome 93.50 / tray
86.25 Hz (state which dome mode). Tray isogrid + 136 kg on struts/clevis, no isolators; dome spin-formed
Al ~5.5 m dia 2:1 ellipsoidal pressure-stiffened (~3-6 bar). Default to real NumPyro NUTS (install in
your venv as in round 2); TensorMesh P2 only if continuum geometry is needed. Deliver: FEM viz/export
(CSV card + NASTRAN .bdf + .vtu/.obj via meshio + mode-shape PNGs), interface-PSD-vs-spec GIF,
narrow-band-exceedance quantification, numeric netCG 95/99 intervals, convergence over ALL latents
(R-hat<1.01, bulk+tail ESS>=400, 0 div, >=4 chains), resolution sensitivity, runtime (whole-run wall +
active; full pipeline, no replay-skip), and report/packet.pptx. Validate vs an analytical benchmark and
show drive-point antiresonance interlacing before claiming success. You may fail; report blockers. Stop.
```
