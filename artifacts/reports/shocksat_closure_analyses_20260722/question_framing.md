# Question framing — Task Card A closure analyses

## Engineering decision being supported
Whether the ShockSat advisor report (Task Card B rebuild) can state, with demonstrated rather than
asserted evidence: (1) which stiffness combinations the modal test actually pinned down; (2) that the
~4.6% frequency discrepancy floor is a property of the data/model mismatch, not the prior; (3) that the
delivered statFEM load bands are better-calibrated than the incumbent FEM+6 dB envelope under a proper
score; (4) that the whole-FRF failure is a diagnosed likelihood-geometry problem; (5) that phase
information was tested and adds nothing.

## Objective function / success metric per item
- A1: eigenvalues of the prior-whitened log-θ posterior covariance (ratio of posterior to prior variance
  per direction; <1 = data contracted that direction). Success = match the adjudicated known answer.
- A2: σ_f posterior median/CI stability across 5 priors. Success = the reference rerun reproduces the
  stored posterior AND each variant's floor conclusion is stated with converged (or honestly YELLOW) runs.
- A3: weighted coverage + band-width ratio (known answer) plus CRPS (lower = better). Success = stored
  numbers reproduced, then the proper-score comparison stands on the same channels/drives/grid.
- A4: profile log-likelihood curves (nuisances optimized out). Success = the mono/multimodality of the
  1-D profiles is established with recorded inner-optimizer convergence.
- A5: provenance of the phase diagnostic. Success = hash + citation.

## What search/optimization is allowed to choose
Only: A4 inner nuisance optimization (gain, noise scale) and grid layout per the card; A1 bootstrap
block length (stated with rationale); A2 NUTS settings inherited from the frozen twin. Nothing may
choose new physics, new candidate models, or new data.

## What remains human judgment
Whether these results flip any report narrative (explicit stop point if A3 flips the load conclusion);
how Task Card B frames the thesis; acceptance of YELLOW variants in A2.

## What would make this the wrong question
If the frozen artifacts were themselves wrong (hash mismatch, non-reproducible known answers) the right
move is STOP-and-report, not analysis on top. If Andrew's adjudication is superseded, the card is void.
Science ceiling inherited and unchanged: no direct net-CG answer key (normal-Z is synthetic
self-consistency), one article of measured data, no flight/build variability.
