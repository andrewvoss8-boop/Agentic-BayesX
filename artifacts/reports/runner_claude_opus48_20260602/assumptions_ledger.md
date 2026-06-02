# Assumptions Ledger — Claude Opus 4.8 Full Sequential Runner

Machine-readable copy in `assumptions_ledger.json`. Dome = `m1` (1.0 kg), tray = `m2` (0.6 kg).
PSD-space dB: `factor = 10**(dB/10)`; on complex FRF amplitude the multiplier is `exp(0.5*log_effect)`.

## Inferred (learned) variables

| Variable | Maps to | Prior | Units | Sensitivity priority |
|---|---|---|---|---|
| `u_k1 = log(k1/k1_nom)` | dome natural frequency | TruncatedNormal(0, 0.18, log[0.55,1.65]) | ln ratio | High |
| `u_k2 = log(k2/k2_nom)` | tray natural frequency | TruncatedNormal(0, 0.18, log[0.55,1.65]) | ln ratio | High |
| `u_z1 = log(zeta1)` | dome damping ratio | TruncatedNormal(log0.018, 0.35, log[0.004,0.090]) | ln | High |
| `u_z2 = log(zeta2)` | tray damping ratio | TruncatedNormal(log0.026, 0.35, log[0.004,0.090]) | ln | High |
| `sigma_build_ln` | build-to-build variability scale | HalfNormal(0.5) | ln-PSD sigma (also dB) | High |
| `sigma_sensor_ln` | sensor-noise scale | HalfNormal(0.3) | ln-PSD sigma (also dB) | High |
| `dome_build[0..10]`, `tray_build[0..10]` | per-build log-PSD effects (22 latent, non-centered) | Normal(0, sigma_build_ln) | ln-PSD | Medium |

## Fixed / not inferred

| Item | Value | Rationale |
|---|---|---|
| Flight-to-flight forcing variability | 3.0 dB (ln-sigma 0.691) | Known per task card; **not learned**. Enters flight QOI likelihood as fixed log-sigma. |
| Flight forcing covariance | Matérn-3/2, ell=0.08 (log freq) | Task requires Matérn, **not RBF**. |
| Flight mean force offset | −6.0 dB vs original flat force PSD | From setup packet. |
| Masses | m1=1.0, m2=0.6 kg | Fixed model masses. |
| Smoothline base input PSD | log-log interp (20,0.01),(100,0.1),(750,0.1),(2000,0.001) g²/Hz | Vibe-test input spec. |
| `force_amp`, `force_fc` | not used / not inferred | Staged data uses smoothline base input, modal impacts, and Matérn forcing GP — the parametric force model is not part of this likelihood. |
| Per-flight realized forcing PSD | integrated out | Only scalar 3*GRMS flight data exists; realized forcing is captured via fixed f2f QOI scatter. |

## Fixed flight-to-flight QOI log-scatter (derived, reported)

`sigma_qoi_tray = 0.197`, `sigma_qoi_iface = 0.150` (ln-3*GRMS). Estimated by MC of the fixed
3 dB Matérn-3/2 forcing GP propagated to 3*GRMS at prior-center structure (4000 draws, seed 777).
Sensor noise contributes <1% because per-bin iid noise averages out over 260 PSD bins — documented
limitation rather than a learned quantity.

## Data counts

- Tray vibe PSD: 260 points (whole curve). Modal FRF: 180 points × 3 channels.
- Flights: 11 (builds 0–10, 1:1), 2 scalar QOI observations each (tray + interface 3*GRMS).
- Build-to-build variability: modeled, scale learned. Flight-to-flight: modeled, **fixed** at 3 dB.
- Test-to-test replicates: none (single vibe + modal campaign on build 0). This is a known
  identifiability limit; build 0 effect and sensor scale lean on the rich per-frequency curves.

## Uncertainty taxonomy

- Parameter uncertainty: `k1,k2,zeta1,zeta2`.
- Observation noise: `sigma_sensor` (learned).
- Build/test variability: `sigma_build` + 22 per-build effects (learned).
- Forcing uncertainty: 3 dB Matérn GP (fixed/known).
- QOI uncertainty: tray/interface 3*GRMS structural-posterior and future-build-flight predictive.
