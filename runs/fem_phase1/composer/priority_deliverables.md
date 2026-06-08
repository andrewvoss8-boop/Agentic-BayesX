# Priority Deliverables

Source prompt: `docs/lab/fem_phase1_runner_prompt.md`.

Interpretation: run the Composer/Cursor builder cell for Phase 1 under `runs/fem_phase1/composer/<tool>/`, using identical physical inputs but tool-appropriate element choices. No damping, FRF, force limiting, source plate, Bayesian updating, or pre-loaded frequency target.

Deliverables:

- TensorMesh solved build: delivered in `tensormesh/` with code, figures, `results.json`, mesh convergence, and README.
- JAX solved build: delivered in `jax/` with code, figures, `results.json`, mesh convergence, and README.
- CalculiX build: delivered in `calculix/` with generated `.inp`, geometry figure, README, and blocked solver status because `ccx` was not available.
- Femap/Nastran deck: delivered in `nastran_deck/` with `model/model.bdf`, `RUN_IN_FEMAP.md`, geometry figure, and null solved-frequency fields for human solve.
- Cross-comparison enablement: all available `results.json` files use a common schema with agent/tool/units/frame/mass case/elements/mesh/frequencies/checks.

Acceptance warning: CalculiX is not a solved cell until `ccx` is installed and the generated deck is run.
