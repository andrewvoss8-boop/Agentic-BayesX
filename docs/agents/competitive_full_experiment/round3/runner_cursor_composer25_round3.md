# Round-3 Runner Prompt — Cursor Composer 2.5

Open Cursor on the master repo root, Composer 2.5, Agent Auto-Run on (your work is confined to your
workspace), paste:

```text
You are the RUNNER for Agentic BayesX, ROUND 3 (Cursor Composer 2.5).

Your ENTIRE workspace is runs/round3/cursor/ — put EVERYTHING you create there (code/, tests/, report/
incl. report/mesh/ and report/packet.pptx, runtime.json, files_changed.md, priority_deliverables.md,
.venv*). Read shared inputs READ-ONLY; write nothing outside your workspace. Round-2 lessons for you
specifically: (a) keep your SOURCE inside your workspace (don't write to shared scripts/); (b) do NOT
reuse another runner's figures as your own (generate your own; declare any copy); (c) report runtime
for the FULL producing run, not a replay that skips the GIF.

Read first:
- AGENTS.md, CLAUDE.md, .cursor/rules/*, .cursor/agents/runner.md
- docs/agents/competitive_full_experiment/round3/task_card_round3.md  (the full spec — follow it)
- artifacts/reports/mdof_femagent_scoping_20260603/recon_and_scope.md
- runs/round3/spike/  (validated FEM baseline — start here)
- artifacts/reports/sequential_vibe_modal_flight_20260602/  (staged data, anchors)

Do Step 0 (priority_deliverables.md) then build round 3: MDOF dome (source) + MDOF tray (load) coupled
at a SINGLE interface; netCG QOI = interface force / load mass. Anchor first modes dome 93.50 / tray
86.25 Hz (state which dome mode). Tray isogrid + 136 kg on struts/clevis, no isolators; dome spin-formed
Al ~5.5 m dia 2:1 ellipsoidal pressure-stiffened (~3-6 bar). CRITICAL quantity-contract fix from round 2:
the interface response PSD is the FORCE-DRIVEN coupled INTERFACE accelerance (it MUST show the
drive-point antiresonance notch and a flat high-frequency plateau) — NOT a tray transmissibility /
base-driven response. Default to the JAX/numpyro NUTS path; TensorMesh P2 only if continuum geometry is
needed. Deliver: FEM viz/export (CSV card + NASTRAN .bdf + .vtu/.obj via meshio + mode-shape PNGs),
interface-PSD-vs-spec GIF, narrow-band-exceedance quantification, numeric netCG 95/99 intervals,
convergence over ALL latents (R-hat<1.01, bulk+tail ESS>=400, 0 div, >=4 chains), resolution
sensitivity, runtime (whole-run wall + active), and report/packet.pptx. Validate vs an analytical
benchmark and show the antiresonance interlacing before claiming success. You may fail; report blockers.
Stop.
```
