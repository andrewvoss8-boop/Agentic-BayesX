# Quantity Contracts — Round 2 (interface response PSD focus)

These contracts are stated BEFORE plotting/fitting, per the Quantity Contract gate. They extend the
round-1 setup contracts (`.../sequential_vibe_modal_flight_20260602/quantity_contracts.md`).

## Interface acceleration RESPONSE PSD (HEADLINE quantity, P1)

- **Plain meaning:** the auto-spectral density of the acceleration measured at the dome/source
  interface DOF of the **coupled** dome(m1)+tray(m2) system, when the system is driven by the flight
  forcing into the dome DOF.
- **Numerator:** interface acceleration-squared spectral density.
- **Denominator:** frequency bandwidth (per Hz).
- **DOF / coordinate:** DOF 0 = dome/source interface (m1) of the coupled 2DOF model.
- **Excitation:** flight forcing PSD into the dome DOF (force into m1), N^2/Hz.
- **Boundary condition:** dome+tray COUPLED (flight configuration), not the standalone tray vibe test.
- **Transfer:** S_interface(f) = |H00(f)/g0|^2 · S_force(f) · exp(dome_build_effect),
  where H00 = (−ω^2 Z^{-1})[0,0] is the interface acceleration/force entry (m/s^2 per N),
  Z = K + iωC − ω^2 M, divided by g0=9.80665 to express acceleration in g.
- **Units:** g^2/Hz (consistent with the smoothline test spec it is compared against).
- **Expected limiting behavior:** rolls off away from resonances; → 0 at very high frequency
  (mass-line of an acceleration/force FRF squared times a band-limited force).
- **Expected resonance behavior:** peaks at the COUPLED natural frequencies ≈ **62.3 Hz and 129.5 Hz**
  (NOT the uncoupled 86.25/93.5 Hz; those are the standalone tray-vibe and dome-only modal peaks).
- **Reference:** GEVS / GSFC-STD-7000 — the test spec must ENVELOPE the flight environment across
  frequency (PSD-envelope comparison is the primary acceptance check).
- **Convention note:** this is a RESPONSE PSD (output acceleration), explicitly NOT the forcing INPUT
  PSD. Round-1 ambiguity ("input spectra") is resolved here: the headline is the response.

## Flight forcing PSD (P2, overlay reference)

- Numerator: force-squared spectral density into m1; Denominator: per Hz; Units: N^2/Hz.
- Mean flight forcing = original forcing PSD × 10^(−6/10) (the project −6 dB offset). The ORIGINAL
  forcing therefore sits +6 dB ABOVE the flight mean.
- Flight-to-flight scatter: Matérn-3/2 GP in ln-frequency, ell=0.08, marginal σ = 3 dB (PSD),
  KNOWN/fixed, not learned.
- **Margin note:** the −6 dB offset is a PROJECT assumption, NOT the GEVS qualification margin (+3 dB),
  and NOT a GEVS "+6 dB/oct" spectral slope.

## Tray 3·GRMS QOI (P3, scalar summary)

- Numerator: 3 × sqrt(∫ tray response PSD df); Units: g.
- **Meaning (verified):** 3·GRMS = 3σ ≈ 99.73% peak estimate of a zero-mean Gaussian response — an
  ESTIMATE, not a hard maximum (random peaks exceed 3σ ~0.27% of the time).
- Compared against: first-build vibe-test tray 3·GRMS = 43.9 g and smoothline input 3·GRMS = 28.3 g.
- This scalar is a SUMMARY only; the P1 PSD-envelope is the primary check (a scalar can hide a
  narrow-band exceedance).

## Half-power bandwidth (resolution driver, P4)

- Δf = f_n / Q = 2ζ·f_n (verified via Irvine/vibrationdata half-power tutorial).
- Coupled mode 1: f_n≈62.3 Hz, numerically measured Δf≈1.8 Hz (effective ζ≈0.015) — narrowest.
- Coupled mode 2: f_n≈129.5 Hz, Δf≈7.8 Hz. Tray-vibe transmissibility: 86.25 Hz, Δf≈3.4 Hz.
