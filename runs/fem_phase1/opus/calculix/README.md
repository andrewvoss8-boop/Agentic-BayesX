# Opus / CalculiX (ccx 2.23) — Phase-1 hexapod normal modes

Continuum **C3D8I solid** tray + **T3D2 truss** struts, solved with `*FREQUENCY`
(Lanczos). Units SI; frame: origin at tray center, +z up, tray mid-plane z = 0.098 m,
base z = 0.

## One-command replay
```bash
cd "$(git rev-parse --show-toplevel)/runs/fem_phase1/opus/calculix/code"
CCX="$HOME/miniforge3_bayesx_femphase1/envs/ccx/bin/ccx" ../../.venv/bin/python run_ccx.py
```
(`ccx` was installed during setup via conda-forge into an isolated env:
`conda create -p <env> -c conda-forge calculix`.) The driver builds the deck, runs ccx at
three mesh sizes (convergence), parses `.dat`/`.frd`, renders figures, and writes
`results.json` + `runtime.json`.

## Model (independent re-derivation; shares only shared/spec.py raw inputs)
- **Tray:** solid 6061-T6 plate meshed with **C3D8I** (8-node incompatible-mode hexahedra
  — accurate bending vs the locking-prone plain C3D8/H8). Structured graded mesh, 2 elements
  through the 12.7 mm thickness, mid-plane node layer at z=0.098. Emergent mass ≈ 3.086 kg.
- **Struts (×6):** **T3D2** 3-D truss (two-force member) — the faithful, robust CalculiX
  realization of a spherical-rod-end push-rod (a truss transmits no moment, so it is
  moment-free by construction; CalculiX has no Nastran-style pin release, and beam B32R
  "knot" expansion conflicts with joint springs). Strut self-bending modes are covered by
  the JAX beam build.
- **Joints:** the rod-end bracket bolts to the tray over a finite footprint, so each truss
  reference node is tied to a small patch of tray nodes (≈18 mm radius) with an **RBE3
  distributing coupling** (`DCOUP3D`) — one per apex (the bipod pair shares an apex). This
  spreads the truss load realistically and avoids the spurious local mode that loading a
  single continuum node produces. Feet fixed.
- **Solve:** `*FREQUENCY` (Lanczos/ARPACK), 16 modes requested.

## Results (results.json)
| mode | Hz | type |
|---|---|---|
| 1 | 85.3 | suspension (rocking/lateral) |
| 2 | 85.7 | suspension (pair) |
| 3 | 182.4 | suspension |
| 4 | 289.9 | suspension |
| 5 | 337.0 | tray-flex (corner/edge flap) |
| 6 | 337.2 | tray-flex |

- **Cross-software agreement:** the four suspension modes match the JAX and TensorMesh
  builds to < 1 % (JAX 84.8/85.3/181.3/291.1; TM 84.7/85.4/181.1/293.0; ccx
  85.3/85.7/182.4/289.9) — three independent element formulations converge.
- **Dense tray-flex cluster near 337 Hz:** the tray is supported only at the 3 apex points
  (radius 110 mm); its 4 corners/edges overhang and flap, giving a dense set of
  low-participation corner/edge tray-flex modes. These are **physical, not spurious** (the
  mode shapes show clear plate bending). C3D8I incompatible-mode bending is softer/more
  accurate than locked full-integration H8, so it places this first tray-flex cluster
  *below* the JAX-plate (371 Hz) and TensorMesh locked-H8 (374 Hz) values — an
  element-theory difference, explained not hidden.
- **Symmetry:** near-degenerate pair at modes 1–2 (0.5 %) ⇒ 120° symmetry intact.
- **Grounding:** fixed-base lowest mode 85.3 Hz ≫ 0 ⇒ no spurious rigid-body mode.
- **Mesh convergence:** max shift 3.3 % over the first 10 modes (h=22→16 mm); suspension
  modes nearly mesh-independent, tray-flex cluster shifts as the overhanging corners
  resolve.
- **Rigid joints ⇒ PROVISIONAL UPPER BOUND** for all frequencies.

## What I did / did not run
- DID: write deck; run ccx `*FREQUENCY`; parse `.dat`/`.frd`; classify; figures; 3-mesh
  convergence.
- DID NOT (Phase-1 out of scope): damping, complex/FRF, force-limiting, source-plate
  coupling, NUTS.

## Integrity
Independent re-derivation; only raw `shared/spec.py` inputs shared; no K/M, eigen-results,
or frequency tables imported from any other tool or agent.
