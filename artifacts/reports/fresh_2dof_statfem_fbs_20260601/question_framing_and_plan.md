# Fresh 2DOF StatFEM/FBS Rerun: Question Framing and Plan

Date: 2026-06-01

## Question Framing

| Field | Statement |
|---|---|
| Engineering decision | Decide whether the secondary tray analog has acceptable random-vibration response under a flight-like force PSD case after updating a simple fixed-base 2DOF model with synthetic test evidence. |
| Objective/QOI | Estimate the posterior distribution of `3 * GRMS` from the tray acceleration response PSD; success is a traceable posterior/QOI packet with residuals, sensitivity, reference comparison, and checker pass, not a claim of real hardware qualification. |
| Decision variables | A future BOED/optimization loop could choose which synthetic measurement class to acquire next, frequency grid density/range, shaker/impact level, sensor channel set, and flight-like forcing basis parameters. In this run these are fixed enough to build the harness. |
| Fixed assumptions | Two lumped translational DOFs; fixed base; linear viscous damping; scalar coupling spring/damper between dome and tray; synthetic Gaussian observation noise; synthetic log-frequency correlated discrepancy; no real FEM geometry, nonlinear joints, slosh, preload, or controller interaction. |
| Human judgment | Whether this toy QOI is the right proxy for tank/tray risk; whether the apparent-mass-like conventions match intended lab hardware; what safety margin or acceptance threshold would matter; whether the synthetic discrepancy is representative enough to justify BOED. |
| Wrong-question trigger | If reference checks or residuals show the measurement conventions are mismatched, channel classes are not distinguishable, posterior/QOI uncertainty is dominated by arbitrary discrepancy/forcing assumptions, or the fixed-base 2DOF model cannot reproduce the basic resonance/antiresonance structure, then optimizing this toy experiment is the wrong question. |

## Fresh Implementation Plan

1. Inspect repo structure only after this framing is recorded, then choose a new scoped implementation location that does not copy a prior path mechanically.
2. Write quantity contracts before generating plots or fitting: drive-point reciprocal-inertance-like channels, NASA-HDBK-7004C source/load apparent-mass benchmark curves, fixed-base tray acceleration transmissibility, and flight-like `3 * GRMS` tray response PSD QOI.
3. Implement a reproducible synthetic 2DOF workflow with explicit numerical assumptions: masses, natural frequencies, damping, coupling, forcing, observation noise, discrepancy GP in natural log frequency, priors, and QOI grid.
4. Generate Markdown and PNG human-review artifacts: assumptions ledger and plots, schematic/workflow diagrams, truth vs observed channels, absolute injected errors, GP discrepancy samples, posterior fit/residual/zoom plots, sampler diagnostics, QOI samples, and sensitivity.
5. Add checker-backed acceptance conditions for required files, assumptions, reference comparison, channel non-duplication, frequency-axis metadata, QOI samples, checker status, and limitations.
6. Run the workflow from one command, run the checker, then only after fresh outputs exist compare against the prior run and log the run and lessons.
