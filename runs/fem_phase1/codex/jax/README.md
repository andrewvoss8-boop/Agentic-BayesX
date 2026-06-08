# Codex JAX Phase-1 Build

Run from repo root:

```bash
python3 runs/fem_phase1/codex/jax/code/run_jax.py
```

Dense solid-tray/truss-strut normal-mode build structured as the Codex JAX forward-model cell. The current eigensolve uses SciPy after assembly; metadata records the JAX version and the path is ready for later differentiable parameterization. Rigid-joint frequencies are provisional upper bounds.
