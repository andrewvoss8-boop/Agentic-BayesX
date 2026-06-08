# Composer JAX Phase-1 Build

Run from repo root:

```bash
python3 runs/fem_phase1/composer/jax/code/run_jax.py
```

Model: SI units, origin at tray center, +z up, fixed feet at z = 0, bare 6061-T6 tray only. The tray uses JAX-evaluated C3D8-style dense solid element matrices; struts are axial truss members for spherical rod-end two-force behavior. Explicit apex joint nodes are tied to nearby tray nodes with stiff translational springs, k = 1e9 N/m. The generalized eigenproblem is solved with SciPy after dense assembly.

What ran: dense first-10 normal-mode solve, mesh refinement from the coarser JAX grid to the fine JAX grid, undeformed geometry plus first six mode figures. Rigid-joint frequencies are provisional upper bounds.

Limitation: this is the differentiable-forward-model shakedown path, not a production shell/beam model. Axial struts do not capture strut bending self-modes.
# Composer / JAX — Phase-1 hexapod normal modes

## One-command replay

```bash
cd runs/fem_phase1/composer/jax/code
../../../../.venv_fem_phase1/bin/python solve.py
```

Outputs: `results.json`, `figures/undeformed_geometry.png`, `figures/mode_1.png` … `mode_6.png`.

## Model (independent JAX re-derivation)

- SI units; frame origin at tray center, +z up, tray top z = 0.098 m.
- Tray: C3D8 linear solid hexahedra (6061-T6, bare plate mass emergent from density).
- Struts: 3D truss (axial only; spherical end releases).
- Joints: apex attach points are explicit top-surface mesh nodes (rigid this phase).
- BC: all translations fixed at six grounded foot nodes.
- Solver: `jax.scipy.linalg.eigh` on dense reduced K, M (float64).

## Assumptions

- Strut area A = 22 mm² nominal.
- No damping, no source plate, no ballast.
- Reported frequencies are a **provisional upper bound** (rigid joints).

## Mesh convergence

Coarse target 6×6×2 (+ apex grid lines); refined 12×12×3. Shift recorded in `results.json`.
