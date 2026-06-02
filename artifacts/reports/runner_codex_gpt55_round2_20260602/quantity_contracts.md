# Quantity Contracts

## Coupled Interface Acceleration Response PSD

- Numerator: acceleration squared at the coupled-system interface/source DOF `m1`.
- Denominator: frequency bandwidth.
- Coordinate: coupled dome/tray interface/source coordinate `m1`.
- Excitation: latent flight force PSD into `m1`.
- Boundary condition: dome and tray coupled in flight configuration.
- Units: `g^2/Hz`.
- Expected limiting behavior: acceleration per force tends toward zero at very low frequency for this force-input model; response PSD falls with the dynamic inertance away from resonance.
- Expected resonance/antiresonance behavior: narrow response peaks can occur near the QOI-driving tray/dome coupled modes around 86 Hz and 93.5 Hz; a scalar GRMS can hide a narrow-band exceedance.
- Reference: setup quantity contract plus round-2 task card; GEVS/GSFC-STD-7000 envelope comparison is documented through `runner_comparison_20260602/reader_web_verified_sources.md`.

## Original Smoothline Test Spec

- Numerator: commanded/base acceleration squared.
- Denominator: frequency bandwidth.
- Coordinate: original vibe-test input smoothline for the tray test.
- Excitation: random vibration test specification.
- Boundary condition: qualification/test input, not a flight force input.
- Units: `g^2/Hz`.
- Expected behavior: log-log interpolation through `(20, 0.01)`, `(100, 0.1)`, `(750, 0.1)`, `(2000, 0.001)`.
- Reference: setup packet and human task card.

## Flight Forcing PSD

- Numerator: force squared into `m1`.
- Denominator: frequency bandwidth.
- Coordinate: source/dome input `m1`.
- Excitation: latent flight forcing process.
- Boundary condition: coupled flight configuration.
- Units: `N^2/Hz`.
- Expected behavior: Matern-3/2 log-PSD samples around a mean 6 dB below the original force PSD. The -6 dB value is a project assumption, not a GEVS qualification margin.
- Reference: setup packet and round-2 margin note.

## Tray 3*GRMS QOI

- Numerator: three times the square root of the one-sided PSD integral.
- Denominator: not applicable after PSD integration.
- Coordinate: tray/load `m2`.
- Excitation: flight force for flight sequence, smoothline base acceleration for the vibe reference.
- Boundary condition: stage-specific, labeled in the figure.
- Units: `g`.
- Expected behavior: a zero-mean Gaussian 3-sigma estimate, approximately 99.73%, not a hard maximum.
- Reference: Irvine/vibrationdata verification summarized in `reader_web_verified_sources.md`.
