# Instrumentation and Test-Log Inventory

Generated: 2026-06-09T13:21:21+00:00

## Summary

- Workbook status: `parsed`
- Channel rows after axis expansion: `325`
- Test-log rows parsed: `184`
- Coordinate units: `inch`.
- Acceleration units: `g`, based on workbook calibration columns in `mV/g` and README English-unit statement.
- Hammer force channel units: `lbf`, based on the `Hammer` row calibration in `mV/lb`.
- Sample rate: README states `100000 samples/s` as general acquisition metadata; plotted MAT subsets use file-specific `dXstep` when present.

## Configuration Counts

| Configuration | Expanded channel rows | Unique DAQ channels |
|---|---:|---:|
| frangible_joint | 108 | 108 |
| nsi_nsd_parametric | 108 | 108 |
| tap_impact | 109 | 109 |

## High-Priority Notes

- Accelerometer locations include FEM grid IDs, which is the key bridge for mapping sensors onto FEM nodes/elements.
- Impact/tap instrumentation and pyro instrumentation are not identical; do not use one global calibration map silently.
- Test logs mention bad/caution channels, including channel 101 bad at installation and channels 29-31 with 60 Hz noise in NSI logs.

## Delivered Tables

- Channel map: `artifacts/reports/shocksat_statfem_runner_20260609/channel_map.csv`
- Test log summary: `artifacts/reports/shocksat_statfem_runner_20260609/test_log_summary.csv`
