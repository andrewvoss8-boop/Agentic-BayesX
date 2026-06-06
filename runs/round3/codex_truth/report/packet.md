# Round 3 Codex Truth Validation Packet

## Method summary

Codex authored an independent as-built reality model for the shared source/load system. The observable axial netCG response is generated from source/load interface apparent masses with single-interface impedance sharing. The published 6-DOF diagonal apparent-mass observations are complex drive-point interface quantities for the same 8 as-built units. The 11 flight forcing PSD draws are reused across all 8 builds.

No inference, fitting, NUTS, or posterior sampling is performed in this truth-author run. Hidden generator details, exact true parameters, per-build structures, and clean scoring arrays are sealed under `sealed_truth/`.

Data counts: 8 builds, 11 flights, 4040 frequency points from 5 to 600 Hz. Whole-frequency observations are published; no peak-only likelihood or feature-summary data product is used here.

## Validation summary

- Cantilever Euler-Bernoulli benchmark max relative error: 6.247e-05.
- Lumped two-mass benchmark max relative error: 0.000e+00.
- Observable build-0 axial resonance-like features (Hz): [65.84596045, 96.8, 133.68, 182.54].
- Observable build-0 axial antiresonance-like features (Hz): [61.8, 80.75, 125.42, 174.28].
- Antiresonance interlacing check pass: True.
- Resolution sensitivity pass: True; coarse-minus-full relative shift = 3.983e-06.

## Observable scalar response summary

Observed netCG `3*GRMS` over all build-flight combinations:

- Median: 0.6352 g
- Central 95 percent: [0.491, 0.8471] g
- Central 99 percent: [0.4676, 0.9236] g

## Mesh/export status

- Nodes: 409
- Elements: 478
- VTU via meshio: True
- OBJ via meshio: True
- BDF: manual NASTRAN bulk data cards; meshio is used for VTU/OBJ

## Figures

- `figures/apparent_mass_antiresonances.png`
- `figures/response_psd_clean_vs_observed.png`
- `figures/flight_response_overlay_build0.png`
- `figures/netcg_distribution.png`
- `figures/mesh_undeformed.png`
- `figures/mode_shape_1.png` through `figures/mode_shape_5.png`

## Units and frame

SI units are used. The interface frame has `x` and `y` transverse in the tray plane and `z` axial from dome/source toward tray/load. Rotations follow the right-hand rule. Apparent mass is kg for translations and kg*m^2 for rotations. Response PSD is g^2/Hz.

## Hidden-boundary note

This report intentionally does not disclose exact as-built parameter values, hidden imperfection magnitudes, or noise scales. Those are sealed for the master after inference.
