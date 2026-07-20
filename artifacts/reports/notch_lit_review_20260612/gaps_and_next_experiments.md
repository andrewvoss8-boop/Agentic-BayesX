# Gaps and Next Experiments

Status: YELLOW. These are engineering follow-ons suggested by the literature
review, not completed experiments.

## What the Literature Leaves Open

1. The standards formalize scalar force-limit methods, while practice can measure
   six resultant forces/moments. The missing middle is a sparse, standards-facing
   6-DOF quantity contract for "which interface channels must be limited."

2. FBS and TPA already show how measured FRF/impedance matrices replace a coupled
   forced solve. The open aerospace question is how sparse the interface
   measurement can be before rocking, per-foot loads, or remote response limits
   become untrustworthy.

3. NASA-HDBK-7004C warns that wide, lightweight, acoustically excited structures
   have uncorrelated attachment motion, and SEA defines modal-overlap regimes.
   The missing test evidence is a direct map from modal overlap and bending
   wavelength to notching visibility distance around a payload foot.

4. Response limiting is standard, but the source set did not give a clean
   criterion for choosing a remote accelerometer that protects a desired interface
   force/moment QOI. That is exactly where ShockSat x tray can contribute.

5. Bayesian FEM updating and statFEM handle model uncertainty, but the searched
   sources did not connect them directly to force-limit/response-limit generation
   with sparse 6-DOF interface measurements.

## ShockSat x Tray Experiment Menu

| Experiment | Question answered | Minimum artifact |
|---|---|---|
| Single-node vs 4-foot CBUSH interface comparison | Does a single resultant-force model miss per-foot/moment overtest on the real-ish coupled tray? | Frequency-domain force/moment QOI table plus checker for net/per-foot/moment channels. |
| Sparse interface measurement sweep | How much error remains for 1 foot, 2 feet, >=3 feet, full per-foot, and full 6-DOF measurement? | Reconstruction-error curves by channel and band; label any unobservable rocking channels. |
| Modal-overlap visibility sweep | Does notch reach transition from global to wavelength-local as modal overlap crosses about 1? | Controlled plate/tray variants with modal spacing, damping, lambda/4 estimate, and measured response suppression radius. |
| Integrated vs bare transmissibility response limit | How wrong is a response-limit accelerometer calibrated without the payload installed? | Side-by-side predicted/actual critical response and interface QOI, with integrated and bare transmissibility. |
| Bayesian sparse-data wrapper | Does sparse empirical data widen intervals enough to cover full-interface truth? | NUTS/HMC or justified alternative with all-variable diagnostics; held-out per-foot/moment coverage gate. |
| Patent/FTO claim-chart pass | Which combinations are crowded versus potentially claimable before public disclosure? | Attorney-ready claim chart for US8731868B2, US11187619B2, US12050125B2, NASA/ISO prior art, and BayesX candidate claims. |

## Recommended Next Step

Run the first two experiments in one deterministic ShockSat x tray card before
any sampler: compare single-node, rigid-3, per-foot, and full matrix
reconstructions against the coupled truth for net force, per-foot forces, and
moments. Acceptance should be three-tier: GREEN only if the claimed sparse
measurement set protects the stated QOI; YELLOW if misses are documented and
bounded; RED if a net-force claim is used to imply per-foot/moment protection.
