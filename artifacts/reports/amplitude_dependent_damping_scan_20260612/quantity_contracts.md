# Quantity Contracts

## Response Amplitude
- Numerator: measured acceleration or velocity magnitude from a named response channel.
- Denominator: none unless converted to FRF by force.
- Coordinate: dataset-specific measurement axis; do not mix axes unless mapped.
- Units: raw file units, usually acceleration (`m/s^2` or `g`) for MPL/ShockSat and velocity/acceleration/FRF for LDV panel products.
- Expected limiting behavior: for a linear system, modal frequency and damping estimates should not systematically change with response amplitude, apart from noise and estimator variance.

## Damping Ratio `zeta`
- Numerator/denominator: dimensionless fraction of critical damping estimated from local decay envelope or modal bandwidth.
- Coordinate/excitation/boundary condition: dataset-specific; must be stated with each result.
- Expected amplitude behavior: linear viscous damping gives approximately amplitude-independent `zeta`; friction/contact/joint hysteresis can make effective `zeta` vary with amplitude.

## FRF / Accelerance
- Numerator: response acceleration or velocity spectrum.
- Denominator: input force spectrum where available.
- Units: acceleration/force, velocity/force, or source-file units.
- Expected limiting behavior: for a linear time-invariant system, repeated FRFs at different amplitudes overlay within noise/coherence; amplitude-dependent damping/hysteresis can alter peak height, bandwidth, phase, and sometimes resonance frequency.

## Hysteresis Evidence
- Numerator/denominator: paired force-response loop or equivalent nonlinear energy-dissipation signature.
- Units: force vs displacement/velocity/acceleration-derived quantity.
- Expected behavior: true hysteresis requires cycle-dependent path/energy evidence or a repeated-amplitude signature that cannot be explained by forcing, windowing, clipping, or boundary changes.
