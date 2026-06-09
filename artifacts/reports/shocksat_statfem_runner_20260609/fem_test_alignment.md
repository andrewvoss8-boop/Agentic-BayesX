# FEM/Test Alignment Assessment

Generated: 2026-06-09T13:21:36+00:00

## Directly Comparable Now

- Instrumentation FEM grid IDs can be checked against parsed deck GRID cards; expected shock accelerometer grids are present in the parsed main FEM aggregate.
- Hammer force channel exists in instrumentation map (channel 116, lbf).
- At least one real MAT data subset was plotted with channel metadata.
- A measured Test07 hammer H1 accelerance diagnostic can be computed from force channel 116 to selected response channels.

## Not Comparable Yet / Blockers

- The measured hammer H1 accelerance estimate has low coherence and is not likelihood-ready.
- NASA SOL 111 FRF assets and Test07 shock-channel FRFs are not directly overlayable until source/response grid conventions are reconciled.

## NASA Correlation Claim Status

Tail/full FEM evidence includes FEM/Correlation assets; whether the evidence proves correlation requires inspecting extracted correlation documents.

## Map Status

Instrumentation workbook FEM grids are verified in the parsed main FEM_20211021 aggregate; the expected ShockSat accelerometer grids are present.

![FEM/test comparison summary](artifacts/reports/shocksat_statfem_runner_20260609/figures/fem_test_comparison_summary.png)
