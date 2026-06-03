# Round-3 Runner Prompt — Claude Code Opus 4.8

Open Claude Code on the master repo root, Opus 4.8, `--dangerously-skip-permissions` (your work is
confined to your workspace), paste:

```text
You are the RUNNER for Agentic BayesX, ROUND 3 (Claude Code Opus 4.8). Runner only, NOT master.

Your ENTIRE workspace is runs/round3/opus48/ — put everything you create there (code/, tests/,
report/ incl. report/mesh/ and report/packet.pptx, runtime.json, files_changed.md,
priority_deliverables.md, .venv*). Read shared inputs READ-ONLY and write nothing outside your
workspace (not notes/, AGENTS.md, CLAUDE.md, other runners, or prior rounds).

Read first:
- AGENTS.md, CLAUDE.md
- docs/agents/competitive_full_experiment/round3/task_card_round3.md  (the full spec — follow it)
- artifacts/reports/mdof_femagent_scoping_20260603/recon_and_scope.md  (tools, QOI, viz/export)
- runs/round3/spike/  (your validated FEM baseline — start here, do NOT re-derive from scratch)
- artifacts/reports/sequential_vibe_modal_flight_20260602/  (staged data, conventions, anchors)

Do Step 0 (priority_deliverables.md) then build the round-3 experiment: MDOF dome (source) + MDOF tray
(load) coupled at a SINGLE interface; netCG QOI = interface force / load mass. Anchor first modes to
dome 93.50 Hz / tray 86.25 Hz (honestly state which dome mode that is). Tray = isogrid + 136 kg on
struts/clevis, no isolators. Dome = spin-formed Al, ~5.5 m dia, 2:1 ellipsoidal, pressure-stiffened
(~3-6 bar). Default to the JAX/numpyro NUTS path; TensorMesh P2 only if continuum geometry is needed.
Deliver the FEM viz/export (CSV card + NASTRAN .bdf + .vtu/.obj via meshio + mode-shape PNGs), the
interface-PSD-vs-spec evolution GIF, the narrow-band-exceedance quantification, numeric netCG 95/99
intervals, convergence over all latents (R-hat<1.01, bulk+tail ESS>=400, 0 div), resolution sensitivity,
runtime (whole-run wall + active), and report/packet.pptx. Validate vs an analytical benchmark + show
drive-point antiresonance interlacing before claiming success. You may fail; report blockers exactly.
Then stop.
```
