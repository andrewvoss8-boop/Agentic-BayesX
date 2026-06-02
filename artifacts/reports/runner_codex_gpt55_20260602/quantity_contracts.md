# Quantity Contracts

## Smoothline PSD
- Numerator: base acceleration squared.
- Denominator: one-sided frequency bandwidth.
- Coordinate: tray shaker/base input.
- Excitation: commanded random-vibration smoothline.
- Boundary condition: standalone tray/load vibe test.
- Units: g^2/Hz.
- Expected behavior: log-log interpolation through 20, 100, 750, and 2000 Hz points.
- Reference: user task card and setup packet.

## Tray Vibe Response PSD
- Numerator: tray acceleration squared.
- Denominator: one-sided frequency bandwidth.
- Coordinate: tray/load m2.
- Excitation: smoothline base acceleration PSD.
- Boundary condition: standalone tray.
- Units: g^2/Hz.
- Expected behavior: low-frequency transmissibility near unity, resonance peak near tray mode, high-frequency rolloff.
- Reference: existing tray transmissibility convention in fresh 2DOF packet.

## Dome-Only Modal FRF
- Numerator: applied force at dome coordinate.
- Denominator: acceleration at dome coordinate.
- Coordinate: dome/source m1.
- Excitation: dome-only modal impact/shaker.
- Boundary condition: tray uncoupled.
- Units: kg for reciprocal inertance F/a.
- Expected behavior: reciprocal-inertance notch near dome resonance and large low-frequency apparent inertia trend.
- Reference: fresh 2DOF reciprocal-inertance convention.

## Coupled Modal FRFs
- Numerator: applied force at interface or tray drive point.
- Denominator: collocated acceleration.
- Coordinate: interface/primary m1 and tray/load m2.
- Excitation: modal impacts on assembled dome/tray system.
- Boundary condition: coupled 2DOF assembly.
- Units: kg for reciprocal inertance F/a.
- Expected behavior: coupled notches/features affected by both k1 and k2; not identical to uncoupled natural frequencies.
- Reference: fresh 2DOF coupled-channel convention.

## Flight Forcing PSD
- Numerator: input force squared.
- Denominator: one-sided frequency bandwidth.
- Coordinate: force into dome/source m1.
- Excitation: latent flight forcing process.
- Boundary condition: coupled flight assembly.
- Units: N^2/Hz.
- Expected behavior: Matern-3/2 log-PSD variation around the mean force PSD; fixed 3 dB flight-to-flight variability.
- Reference: task card and setup packet.

## Interface Acceleration Spectrum
- Numerator: interface acceleration squared.
- Denominator: one-sided frequency bandwidth.
- Coordinate: dome/interface side m1.
- Excitation: flight force into m1.
- Boundary condition: coupled flight assembly.
- Units: g^2/Hz.
- Expected behavior: shaped by coupled acceleration-over-force H00; resonant amplification near coupled modes.
- Reference: 2DOF acceleration-over-force convention.

## Tray Acceleration Spectrum
- Numerator: tray acceleration squared.
- Denominator: one-sided frequency bandwidth.
- Coordinate: tray/load m2.
- Excitation: flight force into m1.
- Boundary condition: coupled flight assembly.
- Units: g^2/Hz.
- Expected behavior: shaped by cross transfer H10 and forcing PSD; sensitive to damping and build variability.
- Reference: 2DOF acceleration-over-force convention.

## Tray 3*RMS / 3*GRMS QOI
- Numerator: three times the square root of integrated tray acceleration PSD.
- Denominator: not applicable after frequency integration.
- Coordinate: tray/load m2.
- Excitation: flight forcing into m1.
- Boundary condition: coupled flight assembly.
- Units: g.
- Expected behavior: increases with tray PSD energy; 3*RMS and 3*GRMS are equivalent because acceleration is expressed in g.
- Reference: random-vibration GRMS convention used in the fresh 2DOF packet.
