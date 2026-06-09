# ShockSat StatFEM Foundation Packet

## Method Summary

- Engineering decision: decide whether ShockSat1 is ready to become the first real-data StatFEM bridge and define the smallest credible v1 update.
- Current model status: source/data/FEM/instrumentation audit, first measured-data plots, diagnostic hammer-FRF layer, and launch definition only.
- Active StatFEM posterior: `false`.
- Sampler status: no NUTS/HMC or fallback sampler was run.
- Data count: see instrumentation/test-log inventory and first data subset manifest.
- Likelihood status: no likelihood accepted yet; the hammer H1 accelerance estimate is diagnostic because coherence/source-grid alignment are not sufficient.
- Inferred variables: none in this packet.
- Fixed assumptions: README English units, target 100-10000 Hz shock band, sensor calibration from workbook; sample rate is taken from file-specific MAT `dXstep` for plotted subsets, with the README 100000 samples/s value retained as general-release metadata until reconciled.
- Not inferred: model discrepancy, observation noise, sensor calibration uncertainty, forcing, build/test variability.
- Data usage: raw MAT data plotted only if parseable; PSD diagnostics are not FRFs or SRS; H1 hammer accelerance is stored as derived diagnostic data, not calibration data.

## Question Framing

# ShockSat Question Framing

## Engineering Decision

Decide whether the NASA/NESC ShockSat1 public release is ready to serve as the first real-data StatFEM digital-twin bridge for aerospace shock/modal updating, and define the smallest credible v1 update that can be defended with held-out validation.

## Objective / Success Metric

The immediate objective is traceability and comparability, not posterior performance. Success means a reviewer can audit source provenance, FEM metadata, channel/test metadata, first real measured-data plots, quantity contracts, and a realistic StatFEM launch plan from one scoped packet and replay command.

## What the Runner May Choose

The runner may choose:
- which source files to download first, subject to conservative large-file handling;
- which minimal archive subsets to extract;
- which representative measured channels/tests to plot after channel metadata is credible;
- which FEM/test comparisons are honestly supported by fetched files;
- whether a minimal StatFEM stub is justified or must be deferred.

## Fixed Assumptions

- Source originals stay under `sources/`.
- Extracted working files stay under `extracted/`.
- Outputs stay under `artifacts/reports/shocksat_statfem_runner_20260609/`, except project continuity notes required by `AGENTS.md`.
- No sampler is called NUTS/HMC without code, diagnostics, one-command replay, and checker output.

## Human Judgment

Human judgment remains responsible for deciding whether the v1 StatFEM target should prioritize hammer/modal updating, pyro shock validation, interface/QOI channels, or another mission-relevant quantity after the inventory is visible.

## Wrong-Question Trigger

The framing is wrong if the public ShockSat files lack enough channel-location, unit, input-force, or FEM-node mapping metadata to support a test/FEM likelihood. In that case the correct first task becomes metadata recovery or manual NASA documentation review, not Bayesian updating.



## Source Provenance

- Source manifest: `artifacts/reports/shocksat_statfem_runner_20260609/source_manifest.json`
- Download/access log: `artifacts/reports/shocksat_statfem_runner_20260609/download_log.md`
- Source state counts: `{'fetched': 6, 'too_large_deferred': 10, 'partial_download': 1}`

## File Inventory

- File inventory: `artifacts/reports/shocksat_statfem_runner_20260609/file_inventory.md`

## FEM Inventory

- FEM archive status: `fetched`
- FEM inventory: `artifacts/reports/shocksat_statfem_runner_20260609/fem_inventory.md`
![FEM file tree](artifacts/reports/shocksat_statfem_runner_20260609/figures/fem_file_tree.png)
![FEM mesh preview](artifacts/reports/shocksat_statfem_runner_20260609/figures/fem_mesh_preview.png)

## Instrumentation and Channel Map

- Instrumentation status: `parsed`
- Channel map: `artifacts/reports/shocksat_statfem_runner_20260609/channel_map.csv`
- Test-log summary: `artifacts/reports/shocksat_statfem_runner_20260609/test_log_summary.csv`

## First Data Plots

- First data status: `plotted`
![First time histories](artifacts/reports/shocksat_statfem_runner_20260609/figures/first_time_histories.png)
![First PSD diagnostic](artifacts/reports/shocksat_statfem_runner_20260609/figures/first_srs_or_psd.png)
![Channel overview](artifacts/reports/shocksat_statfem_runner_20260609/figures/channel_comparison_overview.png)

## First Hammer FRF Diagnostic

- Hammer FRF status: `computed_multi_hit_low_coherence_diagnostic`
- Hammer FRF comparison status: `not_directly_overlayable_currently`
- Hammer FRF manifest: `artifacts/reports/shocksat_statfem_runner_20260609/hammer_frf_subset_manifest.json`
- Hammer FRF alignment: `artifacts/reports/shocksat_statfem_runner_20260609/hammer_frf_alignment.md`
![Hammer accelerance diagnostic](artifacts/reports/shocksat_statfem_runner_20260609/figures/hammer_frf_accelerance_subset.png)
![Hammer coherence diagnostic](artifacts/reports/shocksat_statfem_runner_20260609/figures/hammer_frf_coherence_subset.png)

## Quantity Contracts

- Quantity contracts: `artifacts/reports/shocksat_statfem_runner_20260609/quantity_contracts.md`

## FEM/Test Comparison

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


## StatFEM Launch Definition

# ShockSat StatFEM Digital-Twin Launch Definition

Generated: 2026-06-09T13:21:37+00:00

## Plain-English v1

Use hammer/modal data first if the hammer force and response channels can be parsed, because that gives a clearer input-output dynamic quantity. Then use pyro NSD shock response as a held-out trust test or QOI layer, not as a first hidden-forcing calibration shortcut.

## Observations

- selected hammer accelerance FRFs or modal frequencies: Hammer force channel exists and supports input-output dynamics before unknown-forcing pyro validation.
- pyro NSD response/SRS features as held-out validation or QOI: Pyro is higher-magnitude shock response but forcing is not directly measured.

## Inferred Variables

- small number of stiffness scales grouped by source box, bolted-joint/interface region, upper structure, or struts
- possibly damping scale only if repeat/FRF metadata support it

## Fixed Variables

- geometry and mass properties from NASA correlated FEM
- sensor calibration from instrumentation workbook unless calibration uncertainty is added later
- file-specific sample interval from MAT dXstep for plotted/test subsets; README 100000 samples/s retained as general-release metadata until reconciled

## Discrepancy, Noise, and QOI

- Discrepancy: output-space discrepancy over log frequency or mode index; do not put discrepancy in the same stiffness parameter space as calibrated stiffness
- Noise: use sensor/test metadata when available; otherwise transparent assumed g/lbf noise with sensitivity priority
- QOI: payload-like, interface/bolted-joint, or far-field panel shock response metric at a held-out channel

## Held-Out Validation

- hold out at least one channel
- hold out one test or one frequency band/mode family
- pyro validation after hammer/modal updating is the strongest trust test

## StatFEM Stub Status

deferred unless raw MAT data, force/FRF inputs, FEM mapping, and held-out validation are all available

![StatFEM graphical model](artifacts/reports/shocksat_statfem_runner_20260609/figures/statfem_graphical_model.png)


## Sensitivity Priorities

- Sensor calibration/noise assumptions by sensor type and range.
- Output-space discrepancy correlation length over log frequency or mode index.
- Choice of hammer/modal observations versus pyro response features.
- Held-out channel/test/band selection.
- Boundary-condition and support/suspension interpretation.

## What This Proves / Does Not Prove

- Proves: fetched-source provenance and first metadata inventories exist for available files.
- Proves: channel map/test logs are parseable enough to identify DAQ channels, units, sample rate, and FEM grid IDs.
- Proves: a first Test07 hammer H1 accelerance diagnostic can be computed and traced to force/response channels.
- Does not prove: calibrated StatFEM, active NUTS/HMC, validated FEM/test agreement, FRF likelihood readiness, or shock-prediction performance.

## Human Reflection Prompts

- Which held-out validation target matters most: channel, test, frequency band, or mode family?
- Should v1 prioritize hammer/modal FRFs or pyro shock QOI validation?
- Which ShockSat location is the payload/interface-like QOI for this project vision?

## Replay

Run: `bash artifacts/reports/shocksat_statfem_runner_20260609/run_all.sh`
