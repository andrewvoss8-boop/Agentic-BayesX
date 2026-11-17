# Assumptions ledger

| ID | Assumption | Value / unit | Source | Sensitivity priority |
|---|---|---|---|---|
| A1 | NASA's FEM_and_CAD.zip is unchanged since 2026-06-09 | 2,025,227,962 bytes, ETag "5b4bab6bb79d81:0" | June probe log | high: gated_run.sh refuses to fetch if the size differs |
| A2 | Digitised curves represent NASA's plotted data | pixel = 0.358 Hz, 0.20 dB | figures in deck slides 16, 17 | measured: metric error <= 0.05 dB on the pixel grid, <= 0.32 dB after 2.03 Hz averaging (qa/digitizer_known_answer.json) |
| A3 | Black = test, red = FEM in NASA figures | legend on slides 16-17 | NASA deck | low |
| A4 | Project FEM damping for predictions | zeta(f) interpolated from 33 impact-survey modes, 0.12 % to 0.89 %; rigid modes undamped | measured_modes.npz (values stored in percent) | medium: sensitivity at zeta 0.003 and 0.01 gave 0.5 to 1.2 dB project-vs-NASA FEM changes below 150 Hz |
| A5 | Project FEM basis | 80 modes to 321.7 Hz; no residual flexibility | shocksat_fem_remesh_20260618/matrices | high above 260 Hz, so bands stop at 258.4 Hz |
| A6 | Card H reference | per-curve median 10.02 dB, 420 curves, in-sample, one gain per drive, zeta 0.01 | recovered Card H, checker GREEN | the comparison is between different sensors, drives and processing |
| A7 | Torque labels | file names `Parametric_990x_025ip...` read as 25 to 125 in-lb | NASA test log sheet "Name shows bolted joint torque"; unit inferred | low |
| A8 | Rehearsal shaker locations | stand-ins 5201 Z, 8102 X, 9201 Z for NASA's 5105, 8109, 9206 (not FEM grids) | fem_model.npz grid list | medium: changes which modes are well excited |
| A9 | Rehearsal noise | 1 % output RMS, 0.5 % force RMS, white | assumption | low for the frame-length conclusion |
| A10 | Burst frame length of NASA's records | unknown; 8 s suggested by the 0.125 Hz step of NASA's FEM FRF punch files | June inventory of NASA .pch | decisive for damping; checked on first parse |

Data counts: one test article; NASA impact survey 33 modes (3 impact runs), 6 burst runs (frequency tables only in hand); two digitised FEM-vs-test FRFs; no build-to-build variability. Inferred variables: none (no fitting).
