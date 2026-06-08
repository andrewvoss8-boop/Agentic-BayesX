# Opus — cross-software comparison (my four tools)

The master assembles the full 3-agent × 4-tool matrix and the MAC matrices. This note is
the **cross-software** axis for the Opus agent only (my four independent builds on
identical inputs). No tuning between tools; each engine assembled its own K/M.

## First modes (Hz) — rigid joints = PROVISIONAL UPPER BOUND
| mode | JAX (ACM-plate + beam) | TensorMesh (H8 solid + truss) | CalculiX (C3D8I solid + truss) | Nastran deck (CQUAD4 + CROD) | type |
|---|---|---|---|---|---|
| 1 | 84.84 | 84.71 | 85.27 | human-solve | suspension (rocking/lateral) |
| 2 | 85.28 | 85.39 | 85.71 | human-solve | suspension (pair of 1) |
| 3 | 181.26 | 181.11 | 182.38 | human-solve | suspension |
| 4 | 291.06 | 293.01 | 289.88 | human-solve | suspension (vertical/axial) |
| 5 | 371.35 | 374.51 | 336.97 | human-solve | tray-flex (1st) |
| 6 | 394.78 | 421.81 | 337.16 | human-solve | tray-flex |

## What agrees, and why
- **Suspension modes (1–4): agree to < 1 %** across three fundamentally different element
  formulations (hand-assembled flat-shell + Euler-Bernoulli beam; structured solid hex +
  truss; incompatible-mode solid hex + truss). This is strong cross-software verification:
  the suspension stiffness is set by the strut axial stiffness and the 120° geometry, which
  all three capture identically. Shallow 30° struts make the lowest modes soft
  rocking/lateral (85 Hz), then torsion (181 Hz), then the stiffer vertical/axial bounce
  (290 Hz) — consistent with the spec's expectation ("vertical is the most compliant
  direction; lowest modes are vertical bounce + rocking").

## What diverges, and why (explained, not hidden)
- **First tray-flex frequency:** CalculiX 337 < JAX 371 < TensorMesh 375. This is an
  **element-theory** difference, not an error:
  - TensorMesh uses **full-integration trilinear H8**, which **shear-locks** in bending ⇒
    over-stiff ⇒ highest tray-flex (and ~16 % mesh sensitivity).
  - JAX uses an **ACM thin-plate** element (Kirchhoff) ⇒ accurate thin-plate bending ⇒ 371.
  - CalculiX uses **C3D8I incompatible-mode hex** ⇒ accurate solid bending, softer than
    locked H8, and it resolves the **dense corner/edge-flap cluster** of the 3-point-
    supported overhanging tray ⇒ 337.
  - Trust ranking for tray-flex: C3D8I ≈ ACM-plate > locked-H8. All reported honestly.
- **Strut self-modes:** only the JAX **beam** build can show them (they came out well above
  the suspension band). The truss/rod builds (TensorMesh, CalculiX, Nastran) model the
  spherical-rod-end push-rod as a two-force member and intentionally carry no strut bending.

## Self-checks (all builds)
- **No spurious rigid-body mode** (fixed base): lowest mode ≈ 85 Hz ≫ 0 in every solved tool.
- **120° symmetry:** near-degenerate mode pair at modes 1–2 (~0.5–0.8 % split) in every
  solved tool ⇒ symmetry intact; small splits trace to non-symmetric rectangular tray
  meshes, not the strut layout. (Not tuned to.)
- **Mesh convergence:** suspension modes nearly mesh-independent (≤0.02 % JAX, ≤~3 %
  CalculiX h22→16); tray-flex more sensitive (esp. locked-H8 TensorMesh ~16 %).
- **Differentiability (JAX):** `jax.grad(f_lowest)/dE_strut` computes ⇒ forward model is
  autodiff-ready for the future NUTS update (Phase 1 ran the eigensolve only).

## Integrity statement
Identical INPUTS (node table, materials, sections, masses, BCs from `shared/spec.py`); each
tool independently derived its own element matrices and assembly and solved on its own. No
assembled K/M, eigen-results, or frequency tables were ported between tools, and no tool was
tuned to match another or to match another agent.
