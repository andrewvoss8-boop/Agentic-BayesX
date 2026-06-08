# Opus / JAX — Phase-1 hexapod normal modes

Hand-assembled, **differentiable** structural model (the future NUTS forward model;
Phase 1 runs the eigensolve only). Units SI; frame: origin at tray center, +z up,
tray mid-plane z = 0.098 m, base z = 0.

## One-command replay
```bash
cd "$(git rev-parse --show-toplevel)/runs/fem_phase1/opus/jax/code"
JAX_PLATFORM_NAME=cpu JAX_ENABLE_X64=1 ../../.venv/bin/python fe_validate.py   # element checks
JAX_PLATFORM_NAME=cpu JAX_ENABLE_X64=1 ../../.venv/bin/python build_jax.py     # full build + figures + results.json
```
(`.venv` was created during setup: `python3 -m venv .venv && pip install numpy==1.26.4
scipy==1.10.1 jax==0.4.30 jaxlib==0.4.30 matplotlib`.)

## Model (independent re-derivation; shares only shared/spec.py raw inputs)
- **Tray:** flat rectangular **shell** = ACM/MZC non-conforming **plate-bending** (12 DOF)
  + **Q4 plane-stress membrane** (8 DOF), per-node DOF [u v w rx ry rz]. Solid 6061-T6,
  300×300×12.7 mm, E=68.9 GPa, ν=0.33, ρ=2700. Mass emergent ≈ 3.086 kg. Non-uniform
  tensor grid whose nodes land exactly on the three strut apex points. Drilling DOF (rz)
  carries no stiffness/mass and is pruned.
- **Struts (×6):** 3-D **Euler-Bernoulli beam** (consistent mass), circular tube
  8 mm OD / 1 mm wall (A≈22 mm², I≈137 mm⁴). **Spherical (moment-free) joints** at both
  ends: the joints are stiff **translational-only** springs (k=1e9 N/m), so beam end
  rotations are free ⇒ moment-free, and joint stiffness is an explicit future parameter.
- **Joints:** explicit stiff translational springs (rigid this phase). The axial-spin
  rigid mechanism of a moment-free two-force member (zero strain energy) is grounded by a
  small torsional spring about each strut axis — pushes that spurious mode to ~kHz without
  affecting structural modes or the spherical bending release.
- **BC:** feet fixed (grounded through the joint springs). Source plate not modeled.
- **Solve:** dense generalized eigensolve. To stay robust with the singular mass matrix
  (massless plate rotations), we solve `M v = μ K v` with the positive-definite K as the
  basis (μ = 1/ω²); massless directions give μ→0 (∞ Hz) and are dropped.

## Element verification (fe_validate.py)
- Cantilever beam 1st bending: **0.005 %** vs `β₁²/(2πL²)·√(EI/ρA)`.
- Simply-supported square plate f₁₁: **0.38 %** vs `π(1/L²)·√(D/ρt)` (12×12 ACM mesh).

## Results (this build — see results.json)
First modes (Hz), **rigid joints = PROVISIONAL UPPER BOUND** (real compliant joints lower them):
| mode | Hz | type |
|---|---|---|
| 1 | 84.8 | suspension (rocking/lateral, strut bending) |
| 2 | 85.3 | suspension (pair of 1) |
| 3 | 181.3 | suspension |
| 4 | 291.1 | suspension (vertical/axial-dominated) |
| 5 | 371.3 | tray-flex |
| 6 | 394.8 | tray-flex |

- **Symmetry check:** near-degenerate pair at modes 1–2 (0.5 % split) and higher pairs ⇒
  the 120° symmetry is intact (no broken-symmetry geometry bug). Small splits come from
  the non-symmetric rectangular tray mesh, not the strut layout.
- **Grounding check:** fixed-base lowest mode 84.8 Hz ≫ 0 ⇒ no spurious rigid-body mode.
  (Free-free is *not* a clean 6-RBM check here — moment-free struts add 6 swing
  mechanisms when ungrounded; see results.json `free_free_note`.)
- **Mesh convergence:** first 10 modes shift ≤ **0.02 %** from h=30 mm → h=20 mm tray grid.
- **Differentiability:** `jax.grad` of the lowest axial-suspension frequency w.r.t. strut E
  computed successfully (df/dE ≈ 2.23e-9 Hz/Pa) — the param→frequency map is autodiff-ready
  for the future NUTS update.

## What I did / did not run
- DID: assemble K, M; dense eigensolve; element verification; mesh convergence; mode
  classification; figures; autodiff gradient demo.
- DID NOT (out of scope Phase 1): damping/loss factor, complex/FRF, force-limiting,
  source-plate coupling, NUTS/Bayesian inference.

## Integrity
Independent re-derivation. Only `shared/spec.py` (raw node/material/section inputs) is
shared. No K/M, eigen-results, or frequency tables were imported from the CalculiX,
TensorMesh, or Nastran builds, or from any other agent.
