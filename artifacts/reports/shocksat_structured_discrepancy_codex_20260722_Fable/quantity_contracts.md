# Quantity contracts — Task Card E `_Fable`

Written before any fit output. Every quantity below is defined with numerator, denominator, coordinate,
excitation, boundary condition, units, limiting behaviour and reference.

## 1. Force-referenced accelerance `H1`

| item | value |
|---|---|
| numerator | response acceleration at sensor `i` along its structural axis `a_i`, in `g` (1 g = 386.0886 in/s²) |
| denominator | impact force at drive point `d` along the drive axis, in `lbf` |
| estimator | `H1 = S_xy / S_xx`, averaged **across independent hammer impacts** (4–6 per drive), not across segments of one transient |
| coordinate | sensor coordinates in **inches** in the frozen ShockSat frame (`x`, `y` in the base plane, `z` along the stack axis; origin = the frozen FEM grid origin used by `shocksat_fem_modal_twin_20260609`) |
| excitation | modal hammer, one impact reference per drive; 5 drives (`+X`, `+Y`, `+Z(990)`, `+Z(900)`, `+XY`) |
| boundary condition | as-tested free-ish suspension, identical for all 5 drives (single test campaign, one build) |
| units | `g/lbf` |
| limiting behaviour | `|H1| → 0` as `f → 0` for an accelerance driven by a finite force on a free structure; peaks at resonances, notches at antiresonances |
| reference | the frozen caches `shocksat_netcg_method_selection_20260701/data/multiref_modal/*.npz`, built by `shocksat_psd_envelope_twin_20260623/code/multiref_frf.py` |

## 2. The dimensionless log-ratio actually modelled

```text
H_ref          = 1 g/lbf                                          (reference accelerance, stated explicitly)
q_meas(d,i,s)  = ln( |H1_meas(d,i,f_s)| / H_ref )                 [dimensionless]
q_fem (d,i,s)  = ln( |H1_fem (d,i,f_s; theta, zeta)| / H_ref )    [dimensionless]
r    (d,i,s)   = q_meas - q_fem - c_d                             [dimensionless]
r              = m(f_s, x_i, a_i) + u(f_s, x_i, a_i) + e
e              ~ Normal(0, sigma_e^2)
```

`ln` is taken of a **ratio to a stated reference**, never of a dimensional accelerance. This is the fix the
Codex review raised as a RED issue on Task Card D.

Reporting: every dB number in this packet is `20 / ln(10) * q = 8.6859 * q`. The phrase "log of g/lbf" does
not appear anywhere in this workspace.

## 3. Symbols

| symbol | meaning | units |
|---|---|---|
| `d` | drive (impact reference) index, 5 values | — |
| `i` | response channel index, 84 values | — |
| `s` | frequency-line index, 105 values | — |
| `f_s` | frequency line | Hz |
| `x_i` | sensor coordinates | inches |
| `a_i` | response-axis label (`X`/`Y`/`Z`) — a **categorical input, not a coordinate** | — |
| `theta_g` | stiffness-group multiplier, 9 groups | dimensionless |
| `zeta` | modal damping ratio used in the forward model | dimensionless |
| `c_d` | per-drive log-gain, `c_d ~ Normal(c_bar, tau_c^2)` | dimensionless (log-ratio) |
| `m = H beta` | learned structured conditional mean; `E[delta | beta] = H beta`, generally non-zero | dimensionless |
| `u` | zero-prior-mean residual GP with a frequency x location covariance | dimensionless |
| `e` | observation / spectral-estimation error | dimensionless |
| `sigma_u^2` | residual-GP variance | dimensionless² |
| `sigma_e^2` | homogeneous observation-error variance | dimensionless² |
| `nugget_i` | per-channel excess variance (white in frequency and drive) | dimensionless² |

## 4. Per-drive log-gain `c_d`

`c_d` absorbs hammer-tip / mass-normalisation / units gain that is constant across a drive's channels.

- `c_bar` and `tau_c` are learned from **training drives only**, as the mean and sample variance of the
  per-drive robust residual level.
- In leave-drive-out prediction the held-out drive's `c_d` is **never** estimated from that drive's response:
  it enters the design as an indicator column with no training rows, so its posterior equals its prior
  `Normal(c_bar, tau_c^2)` and contributes `c_bar` to the predictive mean and `tau_c^2` to the predictive
  variance. This is enforced structurally, not by discipline.
- In channel-transfer and band-transfer folds, `c_d` is inferred from the retained training portion of the
  same drive.

## 5. Sharing rules

- `beta` (structured mean) and the residual-GP hyperparameters are shared across drives.
- Only `c_d` is drive specific.
- `u` is an independent realisation per drive (`rho = 0`, decisions_log F2). The measured cross-drive
  residual correlation is reported as the diagnostic for whether the `(f, x)` framing is adequate.

## 6. Spectral-estimation contract (discretisation resolution gate)

| item | value |
|---|---|
| frequency range | 46.79 – 258.38 Hz (frozen analysis band) |
| line spacing | 2.0345 Hz, linear, native cache grid; 105 retained lines |
| frame length | 122 880 samples (0.49 s), impact-aligned, one frame per impact |
| overlap | none |
| force window | 2 ms box on the impact pulse |
| response window | exponential, end value 0.05 over the frame |
| detrending | none (impact-aligned single frame) |
| averaging axis | **across independent hammer impacts** (4–6 per drive) |
| coherence | ordinary multi-hit coherence stored and reported as an independent data-quality diagnostic; it does **not** weight the likelihood in this study |

Why this grid resolves the QOI-driving features: the QOI here is the held-out log-magnitude FRF itself, not a
narrow modal parameter. The raw records are 1.000 s with the impact at 500 ms, so only ~0.5 s of ring-down was
ever recorded and 2.0 Hz is the **best achievable** line spacing from any re-distillation of this data (frozen
finding, `notes/memory.md` 2026-07-14 bandwidth scan). A finer grid is not merely expensive, it is
unobtainable. The exponential window adds `zeta_w(f) = 1/(2 pi f tau)` with `tau = 0.164 s`, i.e. ~1.9% at
50 Hz falling to ~0.4% at 250 Hz; the forward model's fixed `zeta = 0.01` is the band-centre match.

Resolution sensitivity is therefore reported as a **decimation** study (score on every 2nd and every 3rd
frequency line) rather than a refinement study, with the intractability of refinement stated above.

## 7. What "improvement" means

Primary metric: paired change in **held-out median absolute FRF error in dB**, scored at independent-unit
level (drive, spatial cluster, or contiguous band) — never treating dense frequency bins as independent
replicates.

Secondary: CRPS in dB (lower better), 90% predictive coverage, 90% interval width in dB.
