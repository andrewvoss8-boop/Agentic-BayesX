# Decisions log - ShockSat sequential statFEM elastodynamics pilot

Workspace: `artifacts/reports/shocksat_sequential_statfem_20260623/`.

## D0 - Runner prompt and inherited QOI are locked

Source task card: pasted runner prompt from Andrew, 2026-06-23.

The engineering question is whether a reduced sequential statFEM filter improves the held-out response-PSD envelope decision metric over FEM+6 dB and the existing L5/modal-frequency workflow. Time-domain fit and FRF overlays are diagnostics only. The acceptance score is the inherited PSD-envelope GRMS ratio plus energy-weighted positive dB exceedance.

## D1 - Reduced analogue interpretation

This pilot uses a same-test held-out-sensor virtual-sensing interpretation:

- observed sensors from a modal-hammer record are assimilated sequentially in time;
- held-out sensors from the same reference/test are not used in fitting, hyperparameter selection, residual calibration, or plotting choices;
- the filter's held-out acceleration prediction is converted to an FRF using the measured hammer force, then to response PSD and the inherited smoothline envelope.

This is not a full implementation of Kavrakov et al.'s full-FE stochastic Newmark/material-field filter. It is a reduced modal-state analogue intended to answer whether the sequential assimilation idea is a real ShockSat PSD-envelope lever before spending effort on full material-field filtering.

## D2 - Data and units

Use clean modal-hammer tests from the inherited PSD-envelope thread:

- Test01 `+X` at node 990;
- Test02 `+Z` at node 990;
- Test04 `+XY` at node 990;
- Test06 `+Z` at node 900.

Raw `.mat` files are read from `artifacts/reports/shocksat_multiref_explore_20260623/data/extracted/`. Acceleration samples are treated as `g`; force Recorder116 is treated as `lbf`, consistent with the inherited TestLog-based decision D2.

## D3 - Method labels

The sequential filter is a fixed-prior linear-Gaussian sequential MAP state filter over modal displacement and velocity. It is not NUTS/HMC. The fixed prior covariance keeps this first validity probe replayable; it is a YELLOW caveat, not a full Kavrakov-style covariance recursion.

The stiffness-updated variant uses NUTS/HMC only for a small selected stiffness subset calibrated from observed modal-frequency features. The filter then uses the posterior median stiffness as fixed dynamics. That means the held-out PSD envelope is not a full posterior over stiffness, process, and measurement hyperparameters.

## D4 - Discrepancy comparison

The discrepancy gate is implemented as a same-split comparison:

- `nominal_residual`: nominal stiffness, modal residual/process noise absorbs all response mismatch;
- `stiffness_residual`: small-subset stiffness update from observed modal frequencies, plus the same low-dimensional modal residual form.

If the residual band remains broad or stiffness does not improve the PSD-envelope metric, the packet reports that as a YELLOW modeling finding, not a failed attempt to force a win.
