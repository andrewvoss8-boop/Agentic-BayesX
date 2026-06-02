# Fresh 2DOF Quantity Contracts

Date: 2026-06-01

These contracts were written before fresh-run plotting, fitting, or checker acceptance.

Revision note after human review: Ch5 QOI was changed from deterministic time-history peak to `3 * GRMS` of the tray acceleration response PSD. NASA-HDBK-7004C source/load apparent-mass benchmark curves were added as a separate reference quantity so reciprocal inertance is not mistaken for force-limited-vibration apparent mass.

## Ch1 Dome-Only Drive-Point Reciprocal-Inertance / Apparent-Mass-Like Measurement

| Field | Contract |
|---|---|
| Quantity name | Dome-only drive-point `F1/a1`, labeled reciprocal inertance / apparent-mass-like, not NASA load apparent mass. |
| Numerator | Harmonic force applied at dome coordinate `m1`, `F1`, in N. |
| Denominator | Absolute acceleration response at dome coordinate `a1`, in m/s^2. |
| Coordinate | Primary/dome translational DOF only. |
| Excitation | Direct harmonic force on `m1`. |
| Boundary condition | Fixed base; tray absent/disconnected for the dome-only modal analog. |
| Units | kg because N / (m/s^2). |
| Frequency axis | Frequency in Hz, log-scaled for review plots. |
| Expected low/high limit | Magnitude grows approximately as `k1 / omega^2` at low frequency and approaches `m1` at high frequency. |
| Expected resonance behavior | Reciprocal-inertance magnitude has a resonance notch/minimum near the dome-only natural frequency. |
| Reference | Direct SDOF dynamic-stiffness derivation; NASA-HDBK-7004C notes used only to avoid mislabeling this as load apparent mass. |
| Checker | Channel exists, units/contract appear in report, frequency plots are log-x, and channel differs from coupled channels. |

## Ch2 Coupled Primary/Interface Drive-Point Reciprocal-Inertance / Apparent-Mass-Like Measurement

| Field | Contract |
|---|---|
| Quantity name | Coupled primary-side `F1/a1`, used as an interface apparent-mass-like proxy for this 2DOF toy. |
| Numerator | Harmonic force applied at primary/interface coordinate `m1`, `F1`, in N. |
| Denominator | Absolute acceleration response at primary/interface coordinate `a1`, in m/s^2. |
| Coordinate | Coupled system primary-side coordinate `m1`. |
| Excitation | Direct harmonic force on `m1` with tray attached through the tray coupling stiffness/damping. |
| Boundary condition | Fixed base; linear two-mass assembly; tray attached to primary, not directly to base in the coupled assembly. |
| Units | kg. |
| Frequency axis | Frequency in Hz, log-scaled for review plots. |
| Expected low/high limit | Low-frequency magnitude is stiffness dominated; high-frequency magnitude approaches the driven-coordinate effective mass trend. |
| Expected resonance/antiresonance behavior | Resonance notches occur near coupled modes; an antiresonance/shape change can occur due to tray coupling. |
| Reference | Direct 2DOF dynamic-stiffness derivation; vibrationdata-style 2DOF FRF sanity checks for coupled mode and antiresonance behavior. |
| Checker | Clean Ch2 and Ch3 relative L2 distance must exceed a duplicate-channel threshold. |

## Ch3 Coupled Tray Impact/Response Drive-Point Reciprocal-Inertance / Apparent-Mass-Like Measurement

| Field | Contract |
|---|---|
| Quantity name | Coupled tray impact/response `F2/a2`, reciprocal-inertance / apparent-mass-like. |
| Numerator | Harmonic impact force applied at tray coordinate `m2`, `F2`, in N. |
| Denominator | Absolute acceleration response at tray coordinate `a2`, in m/s^2. |
| Coordinate | Coupled system tray coordinate `m2`. |
| Excitation | Direct harmonic force on `m2`. |
| Boundary condition | Fixed base; tray attached to primary through the tray coupling stiffness/damping. |
| Units | kg. |
| Frequency axis | Frequency in Hz, log-scaled for review plots. |
| Expected low/high limit | Low-frequency magnitude is stiffness dominated; high-frequency magnitude approaches the tray driven-coordinate effective mass trend. |
| Expected resonance/antiresonance behavior | Resonance notches occur near coupled modes; response shape should not duplicate Ch2 because the drive/response coordinate is different. |
| Reference | Direct 2DOF dynamic-stiffness derivation; vibrationdata-style 2DOF drive-point FRF checks. |
| Checker | Clean Ch2 and Ch3 relative L2 distance must exceed a duplicate-channel threshold. |

## Ch4 Standalone Fixed-Base Tray Shaker-Table Acceleration Transfer

| Field | Contract |
|---|---|
| Quantity name | Standalone tray absolute acceleration transmissibility `a_tray/a_base`. |
| Numerator | Absolute acceleration of tray mass in m/s^2. |
| Denominator | Prescribed base acceleration in m/s^2. |
| Coordinate | Tray-only SDOF coordinate relative to shaker base. |
| Excitation | Harmonic base acceleration. |
| Boundary condition | Tray mounted to a fixed/base-driven table; primary/dome absent. |
| Units | Dimensionless complex acceleration ratio. |
| Frequency axis | Frequency in Hz, log-scaled for review plots. |
| Expected low/high limit | Magnitude approaches 1 at low frequency and decays toward 0 at high frequency for absolute acceleration transmissibility with viscous damping. |
| Expected resonance/antiresonance behavior | Resonance peak near the fixed-base tray natural frequency, approximately 75 Hz nominal before synthetic truth perturbation. |
| Reference | Standard SDOF base-excitation transmissibility; vibrationdata-style fixed-base shaker-table checks. |
| Checker | Frequency plot metadata must state log x-axis; report must identify the linear magnitude convention. |

## Ch5 Flight-Like Tray Response and QOI

| Field | Contract |
|---|---|
| Quantity name | Flight-like tray acceleration response PSD and QOI `3 * GRMS`. |
| Numerator | One-sided tray acceleration response PSD `S_a2(f)` in `g^2/Hz`, computed from `|a2/F1|^2 S_F1(f)`. |
| Denominator | None for the QOI; force input is a parametric one-sided force PSD `S_F1(f)` in `N^2/Hz`. |
| Coordinate | Tray coordinate `m2` acceleration. |
| Excitation | Unknown random force PSD on primary coordinate `m1` with inferred amplitude in `N/sqrt(Hz)` and center frequency; fixed log-frequency bandwidth in the baseline. |
| Boundary condition | Fixed base; coupled linear 2DOF assembly. |
| Units | `g` for `GRMS` and `3 * GRMS`; `g^2/Hz` for response PSD. |
| Frequency/time axis | PSD uses positive Hz on a log-scaled frequency axis. A time realization may be shown only as a secondary visualization. |
| Expected low/high limit | Response PSD follows `|a2/F1|^2 S_F1(f)`; integrated GRMS should be sensitive to forcing overlap with coupled modes and to damping. |
| Expected resonance/antiresonance behavior | Response PSD peaks when force PSD overlaps coupled resonances; `3 * GRMS` decreases when damping increases or forcing is moved off resonance. |
| Reference | NASA-STD-5002B random-vibration RMS/sigma practice; direct 2DOF PSD propagation; vibrationdata-style random-vibration sanity checks. |
| Checker | Posterior QOI samples and summary must exist; sensitivity must vary forcing/damping/QOI assumptions or log a justified gap. |

## NASA-HDBK-7004C Source/Load Apparent-Mass Benchmark

| Field | Contract |
|---|---|
| Quantity name | NASA-HDBK-7004C Figure 9 normalized source and load apparent mass. |
| Numerator | Interface force magnitude in the source/load apparent-mass convention. |
| Denominator | Interface acceleration magnitude. |
| Coordinate | Interface junction of source and load, with source/load disconnected for individual apparent masses. |
| Excitation | Harmonic interface excitation; benchmark uses the simple two-identical-oscillator impedance-method example. |
| Boundary condition | Source and load apparent masses are evaluated with the compatible source/load constraints described in NASA-HDBK-7004C, not as moving-coordinate reciprocal inertance. |
| Units | Normalized mass magnitude for benchmark; kg for fresh source/load-style curves. |
| Frequency/time axis | Frequency ratio `r = f/f0` for the normalized benchmark; log-scaled Hz for the fresh curves. |
| Expected low/high limit | Source apparent mass grows at low frequency; load apparent mass has fixed-base load resonance behavior. |
| Expected resonance/antiresonance behavior | For `Q = 50`, source apparent mass has a notch near `r = 1` of about `0.02`; load apparent mass has a peak near `r = 1` of about `50.01`; load apparent mass at `r = 0.62` is about `1.62`. |
| Reference | NASA-HDBK-7004C Figure 9 impedance-method example. |
| Checker | Reference comparison JSON must include the `Q = 50` benchmark values and pass tolerances for `M_load(0.62)`, `M_load(1)`, and `M_source(1)`. |
