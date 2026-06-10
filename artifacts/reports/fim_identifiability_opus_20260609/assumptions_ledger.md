# Assumptions ledger — FIM identifiability analysis

All values are inputs to the analysis; the sensitivity sweep (`fim_results.json: sensitivity`)
varies the ones most likely to change the conclusion (resolved band, frequency noise).

## Parameters being studied (the inferred-in-a-future-test variables)
Each is a **dimensionless multiplier on a physical stiffness, nominal 1.0** (e.g. `strut_EA`=1.1
means struts 10% axially stiffer than nominal CAD). They are what a Bayesian update would infer;
here we only ask *how well could a test constrain them*.

| symbol | physical meaning | units | nominal | prior sd (relative) | sensitivity priority |
|---|---|---|---|---|---|
| `tray_E` | tray plate bending+membrane stiffness (∝ Young's modulus E) | – | 1.0 | 0.30 | high |
| `strut_EA` | strut axial stiffness E·A (the hexapod load path) | – | 1.0 | 0.30 | high |
| `strut_EI` | strut bending+torsion stiffness E·I, G·J | – | 1.0 | 0.30 | medium |
| `joint_axial` | joint translational stiffness along the strut axis | – | 1.0 | 0.30 | test (expected sloppy) |
| `joint_lateral` | joint translational stiffness perpendicular to strut axis | – | 1.0 | 0.30 | test (expected null) |

Prior sd 0.30 = a "scrappy" 30% relative prior knowledge of each stiffness scale (log-normal in
spirit). Identifiability thresholds derive from it: a direction is "identifiable" when the data
shrink its posterior sd below the prior (FIM eigenvalue > 1/0.30² = 11.1); "well-identified" when
below 0.10 (eigenvalue > 100).

## Fixed model inputs (from `inputs/spec.py`, NOT inferred)
- Tray: 6061-T6 aluminium, E=68.9 GPa, ν=0.33, ρ=2700 kg/m³, 0.300×0.300×0.0127 m plate, mid-plane z=0.098 m.
- Struts (×6): aluminium tube OD 8 mm, wall 1 mm, A≈2.199e-5 m², I≈1.374e-10 m⁴, J≈2.749e-10 m⁴, E=68.9 GPa, ~196 mm eye-to-eye.
- Joints: stiff translational springs k=1e9 N/m, moment-free (spherical); fixed tiny anti-spin torsional ground 1e2 N·m/rad (not a parameter).
- Boundary condition: strut feet fixed (grounded). Source plate not modelled.
- **Mass M is fixed** (not parametrized): this study infers stiffness only. Density/thickness changes are out of scope and would add identifiability coupling (noted as a limitation).

## Observation / noise model (the test design assumptions)
| quantity | symbol | value | rationale |
|---|---|---|---|
| frequency noise sd | σ_f | 1% of f_i, floor 0.5 Hz | typical modal-ID frequency repeatability on a scrappy test |
| 1-sensor residue noise | σ_logRes | 0.15 (log units) | drive-point residue (amplitude²) estimates are noisier than frequencies |
| 2-sensor ratio noise | σ_ratio | 0.10 (relative) | mode-shape ratio / transmissibility amplitude noise |
| modes kept | N_MODES | 8 (≤570 Hz) | candidate observable elastic modes (fixed-base → no rigid-body modes) |
| modal damping (QOI only) | ζ | 0.02 | assumed 2% critical for the transmissibility QOI |

## Numerical / discretization assumptions
- Tray mesh target h = 30 mm (matches the Opus build; 798 total DOF, 677 free after pruning massless drilling DOFs).
- Reduced basis for the profile likelihood: 40 nominal modes; reduction error to the lowest 8 modes = 0.0 Hz (nominal and +20% stiffened) — see `profile_likelihood.json`.
- Eigen-sensitivities are exact (analytic), validated against central finite differences.
- QR subset selection condition-number threshold = 100.

## Uncertainty types distinguished
- **Parameter uncertainty** (the 5 θ's) — the thing the FIM/posterior constrains.
- **Observation noise** (σ_f, σ_logRes, σ_ratio) — set above; varied ×0.5–×4.
- **Model discrepancy** — NOT included here (pre-test, nominal FEM). Stated as the main caveat:
  real discrepancy can only lower practical identifiability, so these counts are an upper bound.
- **QOI uncertainty** — propagated qualitatively via d(QOI)/dθ projected onto identifiable vs sloppy subspaces.
