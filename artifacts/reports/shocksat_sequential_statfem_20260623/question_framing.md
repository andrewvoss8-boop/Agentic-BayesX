# Question framing

## Engineering decision

Should the ShockSat PSD-envelope program invest in a sequential statFEM elastodynamics implementation, or is the current modal/frequency-domain L5 workflow plus FEM+6 dB still the better near-term path?

## Objective function / success metric

Primary metric:

`GRMS(sequential statFEM 97.5% smoothline envelope) / GRMS(FEM+6 dB smoothline envelope) < 1`

Coverage metric:

Energy-weighted positive dB exceedance of measured held-out response PSD above the sequential envelope. The gate uses exceeding energy fraction rather than binary "any poke fails."

## What the runner may choose

- Which reduced modal modes are used in the state vector, documented from observed modal peak matches.
- A small stiffness subset for the stiffness-updated variant, selected from observed-mode sensitivity/FIM.
- Fixed filter residual/noise hyperparameters for this validity probe, documented in the assumptions ledger.

## What remains human judgment

- Whether same-test held-out-sensor virtual sensing is the right first sequential-statFEM analogue for the broader qualification-spec decision.
- Whether a YELLOW no-improvement result should end this branch or trigger a fuller material-field/state-parameter filter.
- Whether to pay for a full 50-90% split sweep after the first 90% validity probe.

## What would make this the wrong question

- If the mission value is future-flight PSD prediction without same-test observed sensors, this filter is too favorable because it uses observed sensors from the same hammer record.
- If the modal residual/process noise dominates the answer, the method is learning a virtual-sensing map rather than a physically interpretable material/stiffness correction.
- If the held-out sensor's mode-shape participation remains the binding error, sequential state filtering may improve same-test traces while not improving a reusable PSD-envelope twin.

