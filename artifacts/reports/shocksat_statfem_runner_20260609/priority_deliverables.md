# ShockSat StatFEM Runner Priority Deliverables

Run date: 2026-06-09  
Scoped workspace: `artifacts/reports/shocksat_statfem_runner_20260609/`

## Acceptance Stance

This run is a traceable source, data, FEM, and instrumentation foundation for a future StatFEM digital twin. It must not claim a calibrated StatFEM twin until the source files, FEM metadata, measured channels, quantity contracts, likelihood inputs, and validation checks exist.

## Priority Deliverables

| ID | Human priority ask | Interpretation for this run | Acceptance evidence | Status |
|---|---|---|---|---|
| P1 | Source manifest and download/access report | Record each known ShockSat1 source URL, retrieval date/time, HTTP result, file size, SHA256 if fetched, local path, and access attempts with browser-like and curl-like user agents when needed. | `source_manifest.json`, `source_manifest.md`, `download_log.md` | delivered; full large-data continuation documented |
| P2 | ShockSat file inventory with sizes, checksums, extraction status | Inventory fetched archives and direct files without extracting multi-GB archives unnecessarily; preserve originals in `sources/` and extracted working files in `extracted/`. | `file_inventory.json`, `file_inventory.md` | delivered; representative partial data archives documented |
| P3 | FEM/CAD inventory | Determine FEM solver/source format, file formats, units, node/element counts if parseable, materials, boundary assumptions, modal/correlation artifacts, and whether accelerometer locations can map to FEM nodes/elements. | `fem_inventory.json`, `fem_inventory.md`, `figures/fem_file_tree.png` | delivered; correlation evidence needs deeper document review |
| P4 | Instrumentation/test-log inventory | Extract accelerometer/channel map, units, sample rates, test IDs, hammer/pyro event metadata, source/input locations, calibration constants if present, and repeats. | `instrumentation_inventory.json`, `instrumentation_inventory.md`, `channel_map.csv`, `test_log_summary.csv` | delivered |
| P5 | First measured-data plots | Plot a small defensible subset only after channel/unit/sample-rate metadata is credible; clearly label time history, PSD, FRF, or SRS and any processing. | `first_data_subset_manifest.json`, `figures/first_time_histories.png`, `figures/first_srs_or_psd.png`, `figures/channel_comparison_overview.png` | delivered; PSD diagnostic only, no SRS claim |
| P6 | First FEM/test alignment assessment | State what can be directly compared now, what cannot, and whether NASA's "well correlated FEM" claim is backed by included files or only asserted. | `fem_test_alignment.md`, `fem_test_alignment.json`, `figures/fem_test_comparison_summary.png` | delivered; no FRF/MAC comparison claimed yet |
| P7 | StatFEM digital-twin launch definition | Define a credible v1 model with observations, inferred variables, discrepancy, noise, QOI, fixed assumptions, and held-out validation. | `statfem_launch_definition.md`, `statfem_launch_definition.json`, `figures/statfem_graphical_model.png` | delivered; definition only, no posterior claim |
| P8 | Checker-backed report packet | Produce a Markdown review packet, machine-readable manifest, checker report, and runtime accounting. | `shocksat_statfem_packet.md`, `manifest.json`, `checker_report.json`, `runtime.json` | delivered; checker passes packet-foundation gates |

## Ambiguities and Assumptions

- Large-file feasibility is unknown at run start. Assumption: attempt conservative headers/ranges/listings first; download one large archive at a time only after disk-space recording.
- File formats inside the archives are unknown at run start. Assumption: parse with local, documented readers only where the format is clear; otherwise document parser gaps rather than fabricating metadata.
- Units for ShockSat channels and FEM coordinates are unknown until source documentation is inspected. Assumption: no time-history plotting or FEM/test comparison claim is accepted before unit/sample-rate/channel metadata is recorded.
