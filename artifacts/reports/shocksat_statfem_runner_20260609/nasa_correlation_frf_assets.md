# NASA Correlation FRF Asset Index

Generated: 2026-06-09T13:21:32+00:00

- Status: `indexed_from_fem_archive`
- Interpretation: NASA correlation FRF assets are indexed here as source evidence. They are not automatically comparable to Test07 shock-channel FRFs unless source and response grid conventions are reconciled.

## SOL 111 Decks

| Deck | Subtitle | Force grid | Force vector | Frequency request |
|---|---|---:|---|---|
| `artifacts/reports/shocksat_statfem_runner_20260609/extracted/FEM/Correlation/FRF_Verification/SOL_111_Free_Free_Force_11101X.bdf` | `11101X` | 11101 | `[1.0, 0.0, 0.0]` | `{'start': 10.0, 'step': 1.0, 'count_increment_value': 390, 'stop_if_n_is_increment_count': 400.0}` |
| `artifacts/reports/shocksat_statfem_runner_20260609/extracted/FEM/Correlation/FRF_Verification/SOL_111_Free_Free_Force_11110Y.bdf` | `11110Y` | 11110 | `[0.0, 1.0, 0.0]` | `{'start': 10.0, 'step': 1.0, 'count_increment_value': 390, 'stop_if_n_is_increment_count': 400.0}` |

## PCH Response Sets

| PCH | Unique response points | Frequency range | Sample response points |
|---|---:|---|---|
| `artifacts/reports/shocksat_statfem_runner_20260609/extracted/FEM/Correlation/FRF_Verification/SOL_111_Free_Free_Force_11101X.pch` | 76 | `10.0`-`400.0` Hz | `[1101, 1102, 1103, 1104, 1105, 2101, 2102, 2103, 2104, 3101, 3102, 3103, 3104, 3201, 3202, 3203, 3204, 3205, 4101, 4102, 4103, 4104, 5101, 5102, 5103, 5104, 5201, 5202, 5203, 5204, 5205, 6101, 6102, 6103, 6104, 7101, 7102, 7103, 7104, 7105]` |
| `artifacts/reports/shocksat_statfem_runner_20260609/extracted/FEM/Correlation/FRF_Verification/SOL_111_Free_Free_Force_11110Y.pch` | 76 | `10.0`-`400.0` Hz | `[1101, 1102, 1103, 1104, 1105, 2101, 2102, 2103, 2104, 3101, 3102, 3103, 3104, 3201, 3202, 3203, 3204, 3205, 4101, 4102, 4103, 4104, 5101, 5102, 5103, 5104, 5201, 5202, 5203, 5204, 5205, 6101, 6102, 6103, 6104, 7101, 7102, 7103, 7104, 7105]` |

## Comparison Plot Groups In Archive

| Group | PNG count | Unique response points | Axis counts |
|---|---:|---:|---|
| `11101X_Impact_Comparison` | 132 | 76 | `{'X': 40, 'Y': 40, 'Z': 52}` |
| `11110Y_Impact_Comparison` | 132 | 76 | `{'X': 40, 'Y': 40, 'Z': 52}` |

![NASA FRF asset summary](artifacts/reports/shocksat_statfem_runner_20260609/figures/nasa_correlation_frf_asset_summary.png)
