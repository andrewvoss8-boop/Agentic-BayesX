# Sequential Vibe/Modal/Flight — Runner Packet (Cursor Composer 2.5)

## Method summary (first pass)

- Forward model: fresh 2DOF coupled dome (m1) / tray (m2); PSD dB factor = 10**(dB/10).
- Forcing: Matérn-3/2 GP in log PSD; flight-to-flight sigma = 3 dB fixed (not learned).
- Likelihood: tray vibe log-PSD + modal FRF real/imag + flight tray/interface 3*GRMS scalars.
- Flight term is QOI-only, not full flight PSD curves.
- Subsampling: PSD stride 4, modal stride 4.
- Inferred: fn, damping, sigma_build, sigma_sensor, hierarchical build log effects.
- Sampler: NumPyro NUTS (2 chains).
- Comparison: whole-curve vs peak/notch feature likelihood.

## NUTS active: True

- Divergences: 0
- Step size (median): 0.06681409478187561
- Max tree depth: 10

## QOI 95% width ratio peak/full: 0.5191

## Tray 3*GRMS 95% CI: [0.354, 1.567] g
