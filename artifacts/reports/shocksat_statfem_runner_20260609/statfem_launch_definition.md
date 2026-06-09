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
