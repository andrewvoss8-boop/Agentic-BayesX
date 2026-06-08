# Composer TensorMesh Phase-1 Build

Run from repo root:

```bash
python3 runs/fem_phase1/composer/tensormesh/code/run_tensormesh.py
```

Model: SI units, origin at tray center, +z up, fixed feet at z = 0, bare 6061-T6 tray only. The tray is a structured C3D8-style solid mesh on a `discretize.TensorMesh`; struts are axial truss members because the rod ends are spherical two-force joints. Explicit apex joint nodes are tied to nearby tray top nodes with stiff translational springs, k = 1e9 N/m.

What ran: sparse generalized eigensolve for the first 10 positive modes, mesh refinement from 4 x 4 to 6 x 6 tray cells, undeformed geometry plus first six mode figures. Rigid-joint frequencies are provisional upper bounds.

Limitation: axial truss struts do not capture strut bending self-modes; the solid tray uses one element through thickness, so tray-flex frequencies carry shear-locking/discretization risk.
# Composer / TensorMesh-style (scipy.sparse) — Phase-1

`discretize`/TensorMesh not installed; this build uses an independent TET4 continuum + bar assembly with `scipy.sparse.linalg.eigsh`.

## Replay

```bash
cd runs/fem_phase1/composer/tensormesh/code
../../../../.venv_fem_phase1/bin/python solve.py
```

Element types: TET4 solid tray, 3D bar struts. Rigid apex joints on top-surface nodes. Frequencies are provisional upper bound (rigid joints).
