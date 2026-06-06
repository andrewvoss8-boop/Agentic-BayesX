# Priority Deliverables - Round 3 Codex Truth

Created: 2026-06-04T18:14:16Z

## Role and isolation

Codex is the independent truth author. All created files must stay under `runs/round3/codex_truth/`. I may read only the shared protocol/task/rules files named in the user prompt. I must not open or inspect `runs/round3/opus48/`.

Acceptance: no generated artifact references inference-agent code or model details; all created paths are inside this workspace.

## Published observations

Deliver `dataset/observations.npz` and `dataset/data_contract.md` containing observable-only data:

- Frequency grid over approximately 5-600 Hz with dense coverage around modal features.
- 8 independent as-built units.
- Complex diagonal 6-DOF interface apparent mass for DOFs `{x,y,z,rx,ry,rz}`, with sensor noise applied.
- 11 shared flight forcing draws, reused across builds to expose build and flight variability.
- Per-build/per-flight netCG response PSD in `g^2/Hz` and scalar `3*GRMS`.
- Shared forcing-model parameters only; no hidden truth structure, true scales, or model-form-error description.

Acceptance: schema, units, DOF order, coordinate frame, counts, and forcing convention are documented in `data_contract.md`; hidden model details are absent from `dataset/`.

## Sealed truth

Deliver `sealed_truth/` containing generator code, true parameters, as-built structures, hidden modeling choices and sizes, true noise/build/damping values, and a scoring key with clean/noiseless response truth.

Acceptance: one-command replay regenerates the dataset/report artifacts; sealed files include enough metadata for the master to score bias, coverage, and calibration after inference.

## Validation and review packet

Deliver `report/packet.md`, figures, FEM-style mesh exports, checks, commands, runtime, and logs:

- Analytical benchmark errors, mode list, and apparent-mass antiresonance figure.
- FEM visualization/export in `report/mesh/`: `nodes.csv`, `elements.csv`, `model.bdf`, `model.vtu` and/or `model.obj`.
- Mesh and mode-shape PNGs in `report/figures/`.
- Units/frame documentation, quantity contracts, assumptions ledger, resolution sensitivity, legibility/check report, commands, runtime, and files changed.

Acceptance: generated figures are legible, validation checks pass or limitations are explicitly recorded, and the run is replayable from a single command.

## Explicit non-goals

No inference, no NUTS, no fitting, no GIF/PPT, and no reading of other runners' workspaces.

## Ambiguities and interpretations

- The prompt asks for `N_flights = 11` and per-flight response PSD. I interpret this as 11 flight forcing histories reused for every build, yielding response arrays indexed by both build and flight: `(8, 11, n_frequency)`.
- The prompt asks for a single interface DOF but 6-DOF diagonal apparent mass. I interpret the dynamic coupling and netCG QOI as the main axial `z` interface channel, while the published 6-DOF diagonal apparent masses expose the observable multi-axis interface dynamics of the same as-built unit.
- `report/decisions_log.md` must not reveal hidden truth details. Public decisions are logged there; hidden modeling decisions and true values are sealed in `sealed_truth/hidden_decisions_log.md`.
