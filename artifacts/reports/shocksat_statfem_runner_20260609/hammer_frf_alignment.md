# Hammer FRF Diagnostic and FEM Alignment

Generated: 2026-06-09T13:21:33+00:00

## Status

- FRF status: `computed_multi_hit_low_coherence_diagnostic`
- Comparison status: `not_directly_overlayable_currently`
- Interpretation: this is a derived-data diagnostic. It is not accepted as a StatFEM likelihood input in this packet.

## Quantity and Processing

- estimator: H1_yf = G_fy / G_ff using scipy.signal.csd(force, response) and scipy.signal.welch(force)
- numerator: cross power spectral density between input force f and output acceleration y
- denominator: input force auto power spectral density
- units: g/lbf, using MAT channel units g for response and lb/lbf for hammer force
- coordinate: response channel structural axis from instrumentation workbook
- excitation: Test07 impact hammer force channel 116, nominal 990x test label; exact source grid not yet mapped to SOL 111 force grids
- boundary_condition: as-tested impact hammer configuration; suspension/support interpretation still from NASA test context

## Processing Choices

- baseline_removal: `subtract mean of first 1000 samples from each loaded channel`
- window: `Hann`
- nperseg: `32768`
- noverlap: `16384`
- detrend: `False after explicit baseline subtraction`
- frequency_band_reported_hz: `[100.0, 10000.0]`
- acceptance_note: `Low coherence keeps this out of the StatFEM likelihood; it is a diagnostic transfer estimate.`

## Force Channel

- DAQ channel: `116`
- MAT units: `lb`; workbook units: `lbf`
- Loaded hit count: `4` of `4` available MAT source(s)
- TestLog/archive alignment: TestLog matching found 6 Test07 rows; the available archive/source exposes 4 MAT hit file(s). Treat TestLog rows as source-location metadata, not a one-to-one loaded-hit list, until the NASA file/test mapping is reconciled.
- Baseline-removed maximum peak absolute force over loaded hits: `1.328770289431798` lbf
- Baseline-removed median peak absolute force over loaded hits: `0.7727285608668353` lbf
- Baseline-removed median RMS force over loaded hits: `0.1706606875741703` lbf
- Per-hit summary CSV: `artifacts/reports/shocksat_statfem_runner_20260609/hammer_frf_hit_summary.csv`

## Test-Log Source Metadata

| Filename | Description | Impact point | Comments |
|---|---|---|---|
| `Test07_ImpactHammer_990X_001` | Impact Hammer, +X Face, XYZ=(9,9,0), Normal | `9.0, 8.0, 1.0` | Good Data |
| `2` |  | `9.0, 8.5, 0.5` | Good Data |
| `3` |  | `9.0, 8.5, 0.25` | Good Data |
| `4` |  | `9.0, 8.0, 0.0` | Good Data |
| `5` |  | `9.0, 8.75, 0.25` | Good Data, possible light second hit |
| `6` |  | `9.0, 8.5, 0.5` | Good Data, Small double hit 300ms after first hit |

## Response Channels

| DAQ | FEM grid | Verified in FEM | Axis | Description | Median coherence | Likelihood ready |
|---:|---:|---|---|---|---:|---|
| 1 | 9900001 | True | X | Source +X Face -Y Edge (100k) | 0.0721795754776303 | False |
| 50 | 9900016 | True | X | Steel Box Below Bolted Joint (+X Center) | 0.07063222288097781 | False |
| 87 | 9900028 | True | X | Cross Center | 0.06807039309612166 | False |

## NASA Correlation Asset Status

- Asset index JSON: `artifacts/reports/shocksat_statfem_runner_20260609/nasa_correlation_frf_assets.json`
- Asset index Markdown: `artifacts/reports/shocksat_statfem_runner_20260609/nasa_correlation_frf_assets.md`
- Asset index status: `indexed_from_fem_archive`

## Comparison Blockers

- Test07 shock response channels map to 9900001-style FEM grids; NASA SOL 111 PCH response points are modal-test grids such as 1101/2101/11101.
- Test07 source location from channel 116 is not yet mapped to SOL 111 force grids 11101X or 11110Y.
- H1 estimates have low median coherence across 100-10000 Hz.

## Figures

![Hammer accelerance diagnostic](artifacts/reports/shocksat_statfem_runner_20260609/figures/hammer_frf_accelerance_subset.png)

![Hammer coherence diagnostic](artifacts/reports/shocksat_statfem_runner_20260609/figures/hammer_frf_coherence_subset.png)

![NASA FRF asset summary](artifacts/reports/shocksat_statfem_runner_20260609/figures/nasa_correlation_frf_asset_summary.png)
