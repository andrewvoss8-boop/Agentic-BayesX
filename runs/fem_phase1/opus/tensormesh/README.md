# Opus / TensorMesh (discretize) — Phase-1 hexapod normal modes

Continuum **solid** tray on a structured `discretize.TensorMesh` grid + **truss** struts;
sparse generalized eigensolve. Units SI; frame: origin at tray center, +z up, tray
mid-plane z = 0.098 m, base z = 0.

## One-command replay
```bash
cd "$(git rev-parse --show-toplevel)/runs/fem_phase1/opus/tensormesh/code"
../../.venv/bin/python build_tensormesh.py
```

## Model (independent re-derivation; shares only shared/spec.py raw inputs)
- **Tray:** solid 6061-T6 plate as **trilinear hexahedra (H8)**, 3-D isotropic elasticity,
  2×2×2 Gauss (full integration), assembled on a `discretize.TensorMesh` (discretize used
  as the structured mesh generator). Non-uniform x/y grid placing nodes exactly on the
  three apex points; 2 cells through the 12.7 mm thickness (mid-plane node layer at
  z=0.098). Emergent mass ≈ 3.086 kg.
- **Struts (×6):** 3-D **bar/truss** (axial two-force member) — the faithful idealization
  of a spherical-rod-end push-rod, which carries axial load only. Consistent mass.
- **Joints:** explicit stiff translational springs (k=1e9 N/m), rigid this phase.
- **BC:** feet fixed; source plate not modeled.
- **Solve:** `scipy.sparse.linalg.eigsh(K, k, M, sigma=0, which='LM')` (shift-invert for
  the smallest eigenvalues). Both K and M are positive definite (translational DOF only,
  fixed base), so this is the natural sparse eigensolver.

## Why this build differs from the JAX build (on purpose)
The integrity rule requires independent re-derivation. This build uses a **solid hex**
tray (vs JAX's flat plate-shell) and **truss** struts (vs JAX's beams). The cross-software
comparison therefore tests element theory rather than a shared assembly.

## Results (this build — results.json)
| mode | Hz | type |
|---|---|---|
| 1 | 84.7 | suspension (rocking) |
| 2 | 85.4 | suspension (pair) |
| 3 | 181.1 | suspension |
| 4 | 293.0 | suspension |
| 5 | 374.5 | tray-flex |
| 6 | 421.8 | tray-flex |

- **Cross-check with JAX:** the four suspension modes agree to < 1 % between the two
  independent idealizations (JAX 84.8/85.3/181.3/291.1 vs here 84.7/85.4/181.1/293.0).
- **Symmetry:** near-degenerate pair at modes 1–2 (0.8 %) ⇒ 120° symmetry intact.
- **Grounding:** fixed-base lowest mode 84.7 Hz ≫ 0 ⇒ no spurious rigid-body mode.
- **Mesh convergence:** suspension modes are nearly mesh-independent; **tray-flex** modes
  shift up to ~16 % (h=20→12 mm) because **trilinear H8 full integration locks in bending
  (shear locking) and converges from above**. The tray-flex frequencies here are therefore
  an over-stiff bound; the JAX plate-shell tray-flex values are more trustworthy for
  bending. Both are reported honestly. (A bending-corrected hex — incompatible modes /
  reduced integration — would lower the H8 tray-flex; the CalculiX build uses C3D8I
  incompatible-mode hexes for exactly this reason.)
- **Rigid joints ⇒ PROVISIONAL UPPER BOUND** for all frequencies.

## What I did / did not run
- DID: discretize mesh; H8 + truss assembly; sparse shift-invert eigensolve; convergence;
  classification; figures.
- DID NOT (Phase-1 out of scope): damping, complex/FRF, force-limiting, source-plate
  coupling, NUTS.

## Integrity
Independent re-derivation; only raw `shared/spec.py` inputs shared; no K/M, eigen-results,
or frequency tables imported from any other tool or agent.
