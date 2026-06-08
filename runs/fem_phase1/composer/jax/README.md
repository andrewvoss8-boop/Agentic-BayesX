# Composer / JAX — Phase-1 hexapod normal modes

## Replay

```bash
cd runs/fem_phase1/composer/jax/code
../../../../.venv_fem_phase1/bin/python solve.py
```

Outputs: `results.json`, `figures/undeformed_geometry.png`, `figures/mode_1.png` … `mode_6.png`.

Tray: C3D8 solid. Struts: 3D truss. Solver: `jax.linalg.eigh` (float64). Frequencies are provisional upper bound (rigid joints).
