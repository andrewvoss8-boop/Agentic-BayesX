# Priority Deliverables

Source prompt: `docs/lab/fem_phase1_runner_prompt.md`.

Interpretation: run the GPT/Codex builder cell under `runs/fem_phase1/codex/<tool>/`, with identical raw inputs and independently generated per-tool artifacts. No damping, FRF, force limiting, source plate, Bayesian updating, or pre-loaded frequency target.

Delivered:

- TensorMesh solved build: `tensormesh/` with code, figures, `results.json`, mesh convergence, and README.
- JAX solved build: `jax/` with code, figures, `results.json`, mesh convergence, and README.
- CalculiX solved build: `calculix/` with `.inp`, `ccx` output, geometry figure, parsed frequencies, `results.json`, and README.
- Femap/Nastran deck: `nastran_deck/` with `model/model.bdf`, `RUN_IN_FEMAP.md`, geometry figure, and null solved-frequency fields for human solve.
- Cross-comparison enablement: each `results.json` records agent/tool/units/frame/mass case/elements/mesh/frequencies/checks.
