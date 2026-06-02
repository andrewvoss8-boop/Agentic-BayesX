# Quantity Contracts

## Smoothline PSD

- Numerator: acceleration-squared spectral density.
- Denominator: frequency bandwidth.
- Coordinate: commanded/base vibe input for the tray test.
- Excitation: smoothline random vibration specification.
- Boundary condition: tray tested as standalone load article.
- Units: `g^2/Hz`.
- Expected behavior: log-log interpolation through the four specified points.
- Reference: human research plan.

## Dome FEM Response PSD

- Numerator: dome acceleration-squared spectral density.
- Denominator: frequency bandwidth.
- Coordinate: dome/source `m1`.
- Excitation: simple flat broadband force PSD.
- Boundary condition: dome-only, uncoupled from tray.
- Units: `g^2/Hz`.
- Expected behavior: peak scaled to `0.1 g^2/Hz`.
- Reference: human research plan.

## Tray Vibe Response PSD

- Numerator: tray acceleration-squared spectral density.
- Denominator: frequency bandwidth.
- Coordinate: tray/load `m2`.
- Excitation: smoothline base acceleration PSD.
- Boundary condition: standalone tray/load vibe test.
- Units: `g^2/Hz`.
- Expected behavior: smoothline shaped by tray transmissibility, plus first-build tray effect and fresh sensor noise.
- Reference: existing fresh 2DOF tray transmissibility convention.

## Dome-Only Modal FRF

- Numerator: force at dome coordinate.
- Denominator: acceleration at dome coordinate.
- Coordinate: dome/source `m1`.
- Excitation: modal impact/shaker on dome only.
- Boundary condition: dome-only, uncoupled from tray.
- Units: kg, reciprocal inertance style `F/a`.
- Expected behavior: notch near the dome mode for reciprocal inertance.
- Reference: existing fresh 2DOF quantity contracts.

## Coupled Modal FRFs

- Numerator: impact force at interface or tray coordinate.
- Denominator: acceleration at the same coordinate.
- Coordinates: interface/primary side and tray/load side.
- Excitation: modal impacts at the interface and on the tray.
- Boundary condition: dome and tray coupled.
- Units: kg, reciprocal inertance style `F/a`.
- Expected behavior: coupled features depend on both dome and tray parameters.
- Reference: existing fresh 2DOF coupled-channel convention.

## Flight Forcing PSD

- Numerator: force-squared spectral density into `m1`.
- Denominator: frequency bandwidth.
- Coordinate: source/dome input `m1`.
- Excitation: latent flight forcing process.
- Boundary condition: coupled dome/tray flight configuration.
- Units: `N^2/Hz`.
- Expected behavior: Matérn-3/2 GP in log PSD around a mean 6 dB below the original force PSD.
- Reference: human research plan.

## Interface Acceleration Spectrum

- Numerator: interface acceleration-squared spectral density.
- Denominator: frequency bandwidth.
- Coordinate: source/interface side of the coupled model.
- Excitation: flight forcing into `m1`.
- Boundary condition: coupled dome/tray flight configuration.
- Units: `g^2/Hz`.
- Expected behavior: shaped by coupled transfer from `m1` force to interface acceleration.
- Reference: current 2DOF coupled transfer convention.

## Tray `3*GRMS` QOI

- Numerator: three times root integral of tray acceleration PSD.
- Denominator: not applicable after PSD integration.
- Coordinate: tray/load `m2`.
- Excitation: vibe-test base input or flight forcing, as labeled.
- Boundary condition: stage-specific.
- Units: `g`.
- Expected behavior: increases with response PSD energy and is sensitive to damping/forcing assumptions.
- Reference: random vibration review convention used in the fresh 2DOF packet.
