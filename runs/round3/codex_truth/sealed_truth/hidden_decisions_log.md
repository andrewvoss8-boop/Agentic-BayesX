# Hidden Decisions Log

Append-only hidden log for the master. Public report logs intentionally do not disclose these details.

## 2026-06-04T18:14:16Z

- Selected a sealed reduced-order apparent-mass model rather than a clean symmetric FEM so the inference task sees genuine model-form error.
- Used source/load impedance sharing for the axial single-interface QOI: interface force into the load is `M_load / (M_source + M_load)` times the applied source-side forcing.
- Used a fixed netCG normalization mass of 170 kg: 136 kg avionics plus a 34 kg tray/panel allowance.
- Used per-build lognormal fundamental frequency and damping scatter with sigma approximately 5 percent / 3 in log units, plus strut/joint spatial scatter.
- Reused the same 11 flight forcing PSD draws across all 8 builds.
