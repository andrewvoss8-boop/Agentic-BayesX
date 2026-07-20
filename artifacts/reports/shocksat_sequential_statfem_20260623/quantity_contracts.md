# Quantity contracts

Definitions here inherit the PSD-envelope contracts from `artifacts/reports/shocksat_psd_envelope_twin_20260623/quantity_contracts.md`.

## Q-A. Acceleration time history `a_s(t)`

- Numerator/denominator: response acceleration sample at sensor `s`.
- Units: `g`.
- Coordinate: sensor axis from `channel_map.csv`; free-free modal-hammer boundary condition.
- Excitation: instrumented modal-hammer force from Recorder116.
- Expected behavior: pre-trigger baseline near zero, impulse response ringdown after the hammer hit, resonant content in the 45-260 Hz analysis band.

## Q-B. Hammer force `F_d(t)`

- Units: `lbf`.
- Coordinate/excitation: drive point and direction for Test01/Test02/Test04/Test06.
- Use in this runner: known deterministic input to the modal-state filter; no stochastic forcing posterior is claimed.

## Q-C. Modal state `x_n = [q_n, qdot_n]`

- `q_n`: modal displacement coordinates in the reduced ShockSat modal basis.
- `qdot_n`: modal velocity coordinates.
- Dynamics: damped linear modal oscillator with measured force input plus low-dimensional modal residual/process noise.
- Units: inherited reduced-coordinate units; sensor acceleration output is converted to `g` through the existing reduced response rows and `386.0886 in/s^2 per g`.

## Q-D. Accelerance FRF `H_{s,d}(f)`

- Definition: response acceleration divided by hammer force after applying the same windowing convention to predicted and measured time histories.
- Units: `g/lbf`.
- Expected behavior: resonant peaks and antiresonances across 45-260 Hz.

## Q-E. Response PSD `S_aa,s(f)`

- Definition: `S_aa,s(f) = |H_{s,d}(f)|^2 * S_F0`.
- Force PSD: flat `S_F0 = 1 lbf^2/Hz`, identical for all methods.
- Units: `g^2/Hz`.
- Note: because `S_F0` is common, GRMS ratios depend on `|H|^2`; absolute levels retain the documented unit flat-force convention.

## Q-F. Smoothline envelope `E[S](f)`

- Definition: peak-pick local maxima of PSD in log-frequency/log-level space, then connect peak tops with straight line segments in log-log coordinates.
- Same implementation: inherited `psd_envelope.smoothline_envelope`.
- Units: `g^2/Hz`.

## Q-G. GRMS

- Definition: `sqrt(integral E[S](f) df)` over 45-260 Hz.
- Units: `g`.
- Success ratio: sequential 97.5% envelope GRMS divided by FEM+6 dB envelope GRMS.

## Q-H. Energy-weighted positive dB exceedance

- Definition: positive part of `10*log10(S_data(f)/E_seq(f))`.
- Reported values: maximum positive exceedance in dB and the fraction of measured band energy located at exceeding frequencies.
- Acceptance threshold for this pilot: exceeding energy fraction below 2% is a clean coverage gate; above that is YELLOW or RED depending on the claim.

