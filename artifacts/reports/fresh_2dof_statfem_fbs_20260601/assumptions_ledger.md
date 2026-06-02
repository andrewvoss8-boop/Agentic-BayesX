# Fresh 2DOF Assumptions Ledger

Date: 2026-06-01

These numerical assumptions were fixed before generating fresh synthetic data, posterior samples, or figures. Revision note: after human review, the observation/discrepancy assumptions were increased, the QOI was changed to `3 * GRMS` of the tray acceleration response PSD, and explicit model-form errors of +/-15% frequency and +/-25% damping were added.

| Assumption | Value | Units | Source | Rationale | Sensitivity priority | Where used |
|---|---:|---|---|---|---|---|
| Primary/dome mass `m1` | 1.000 | kg | Synthetic choice | Keeps apparent-mass-like units easy to audit. | Medium | Model, QOI |
| Tray mass `m2` | 0.600 | kg | Synthetic choice | Secondary tray analog smaller than primary dome analog. | Medium | Model, QOI |
| Nominal dome natural frequency | 110.000 | Hz | User prompt | Required dome analog nominal frequency. | High | Nominal stiffness, priors, reference lines |
| Nominal tray natural frequency | 75.000 | Hz | User prompt | Required tray analog nominal frequency. | High | Nominal stiffness, priors, reference lines |
| Nominal dome stiffness `k1_nom` | 477688.853 | N/m | Derived from `m1 (2 pi f)^2` | Sets prior center for dome stiffness. | High | Priors, model |
| Nominal tray coupling stiffness `k2_nom` | 133239.659 | N/m | Derived from `m2 (2 pi f)^2` | Tray fixed-primary local stiffness; coupled assembly uses one tray-to-primary spring. | High | Priors, model |
| Dome frequency model error | -0.150 | fractional frequency shift | Human review | Synthetic truth shifts dome frequency 15% below nominal from model-form error. | High | Synthetic truth |
| Tray frequency model error | +0.150 | fractional frequency shift | Human review | Synthetic truth shifts tray frequency 15% above nominal from model-form error. | High | Synthetic truth |
| Dome damping model error | +0.250 | fractional damping-ratio shift | Human review | Synthetic truth shifts dome damping 25% above nominal from model-form error. | High | Synthetic truth |
| Tray damping model error | -0.250 | fractional damping-ratio shift | Human review | Synthetic truth shifts tray damping 25% below nominal from model-form error. | High | Synthetic truth |
| True dome stiffness `k1` | 345130.196 | N/m | Derived | Implements -15% dome frequency shift through stiffness. | High | Synthetic truth |
| True tray coupling stiffness `k2` | 176209.450 | N/m | Derived | Implements +15% tray frequency shift through stiffness. | High | Synthetic truth |
| True dome local frequency | 93.500 | Hz | Derived | Check against expected shifted resonance neighborhood. | Medium | Synthetic truth, plot markers |
| True tray local frequency | 86.250 | Hz | Derived | Check against expected shifted resonance neighborhood. | Medium | Synthetic truth, plot markers |
| True dome damping ratio `zeta1` | 0.0225 | ratio | Derived | Implements +25% dome damping model error from nominal 0.018. | High | Synthetic truth, sensitivity |
| True tray damping ratio `zeta2` | 0.0195 | ratio | Derived | Implements -25% tray damping model error from nominal 0.026. | High | Synthetic truth, sensitivity |
| True dome damping `c1` | 26.437 | N s/m | Derived | Uses `2 zeta sqrt(k m)`. | Medium | Synthetic truth |
| True tray damping `c2` | 12.681 | N s/m | Derived | Uses `2 zeta sqrt(k m)`. | Medium | Synthetic truth |
| Coupled assembly boundary | Fixed base; `m1` to base, `m2` to `m1`; no direct tray-to-base spring in coupled assembly | categorical | Fresh modeling choice | Avoids double-counting tray stiffness in the coupled assembly while retaining standalone fixed-base tray test. | High | Model, quantity contracts |
| Frequency grid | 12 to 220, 120 log-spaced points | Hz | Synthetic choice | Covers below/above 75 Hz and 110 Hz features with log review spacing. | Medium | Channels, plots |
| Frequency plot x-axis | Log scaled | categorical | Harness gate | Matches broadband structural-dynamics review default. | High | Plots, checker |
| Magnitude scale | Linear magnitude, not dB | categorical | Harness gate | Keeps units visible for apparent-mass-like and transmissibility plots. | High | Plots, report |
| Observation noise scale | 0.080 times local channel magnitude, with floor | channel units | ECSS/NASA-informed synthetic choice | Earlier 2.5% median-scaled noise failed visual/aerospace gut check; test tolerances and FRF estimation scatter justify a larger stress-test assumption. | High | Synthetic data, likelihood, sensitivity |
| Discrepancy GP scale | 0.200 times local channel magnitude, with floor | channel units | NASA/NESC-informed synthetic choice | Model-form and boundary-condition discrepancy should dominate pure sensor noise in this toy. | High | Synthetic data, likelihood, sensitivity |
| Local error floor | 0.200 times channel median clean magnitude | channel units | Synthetic robustness choice | Prevents uncertainty from disappearing at reciprocal-inertance notches. | High | Synthetic data, likelihood, sensitivity |
| Discrepancy GP covariance | `sigma_d(f) sigma_d(f') exp(-0.5 ((ln f - ln f') / ell)^2)` | channel units squared | Harness convention | Correlates by frequency ratio with local-magnitude scaling. | High | Synthetic data, likelihood, GP figures |
| Discrepancy GP correlation length `ell` | 0.160 | natural-log-Hz coordinate | Synthetic choice | About 17% frequency-ratio correlation length. | High | Synthetic data, likelihood, sensitivity |
| GP real/imag correlation | Independent real and imaginary GP draws | categorical | Simplification | Keeps covariance transparent for toy complex FRFs. | Medium | Synthetic data, likelihood |
| Flight force true amplitude | 1.000 | N/sqrt(Hz) | Synthetic choice | Sets one-sided force PSD level for a visible tray response without claiming hardware realism. | High | Synthetic truth, QOI |
| Flight force true center frequency | 92.000 | Hz | Synthetic choice | Places forcing between tray and dome nominal frequencies. | High | Synthetic truth, QOI |
| Flight force log bandwidth | 0.330 | natural-log-Hz coordinate | Synthetic choice | Broad flight-like band; fixed in the baseline fit. | High | Synthetic truth, QOI, sensitivity |
| Response PSD observation scatter | 0.180 | natural log PSD | ECSS/NASA-informed synthetic choice | Random vibration PSD control/measurement tolerances are naturally dB/log-scale quantities. | High | Synthetic data, likelihood, QOI |
| Response PSD discrepancy | 0.350 | natural log PSD | NASA/NESC-informed synthetic choice | Correlated model-form error in predicted response PSD. | High | Synthetic data, likelihood, QOI |
| Response PSD discrepancy correlation length | 0.180 | natural-log-Hz coordinate | Synthetic choice | Smooth model-form error over neighboring frequency ratios. | High | Synthetic data, likelihood, QOI |
| Flight time grid | 0 to 0.350 in 0.001 increments | s | Synthetic choice | Secondary realization only; QOI is PSD-based. | Medium | Flight data visualization |
| Flight time observation noise | 0.080 times clean standard deviation | m/s^2 | Synthetic choice | Time-domain realization noise for visualization. | Medium | Synthetic visualization |
| Flight time discrepancy | 0.200 times clean standard deviation sinusoid at 7 Hz | m/s^2 | Synthetic choice | Simple model-form drift in secondary time visualization. | Medium | Synthetic visualization |
| Generated dataset count | 1 synthetic realization per measurement class | categorical | Implementation fact | This trial does not simulate repeated flights or repeated tests. | High | Report, checker |
| Flight-to-flight variability modeled | No | categorical | Implementation fact | Repeated-flight scatter is a missing capability and is not included in the posterior. | High | Limitations, human review |
| QOI definition | `3 * sqrt(integral S_a2(f) df)` | g | NASA-STD-5002B random-vibration practice | Converts response PSD to a peak-equivalent random-vibration metric. | High | QOI, posterior, sensitivity |
| Stiffness prior | `log(k/k_nom) ~ Normal(0, 0.18^2)` | log ratio | Synthetic inference choice | Allows roughly +/-20% stiffness variation. | High | Posterior |
| Implied natural-frequency prior | `log(f/f_nom) ~ Normal(0, 0.09^2)` before truncation | log frequency ratio | Derived from stiffness prior | Natural frequency is proportional to `sqrt(k)`, so frequency prior spread is half the stiffness log spread. Approximate untruncated 95% factor is 0.838 to 1.193. | High | Posterior, report |
| Damping prior | `log(zeta/zeta_nom) ~ Normal(0, 0.35^2)` | log ratio | Synthetic inference choice | Damping is positive and weakly known. | High | Posterior |
| Damping prior 95% factor | 0.504 to 1.986 before truncation | damping-ratio multiplier | Derived from damping prior | Shows initial damping uncertainty around nominal zeta values before truncation to [0.004, 0.090]. | High | Posterior, report |
| Force amplitude prior | `log(A/0.85 N/sqrt(Hz)) ~ Normal(0, 0.65^2)` | log ratio | Synthetic inference choice | Broad positive force PSD amplitude uncertainty. | High | Posterior, QOI |
| Force center prior | `log(fc/95 Hz) ~ Normal(0, 0.22^2)` | log ratio | Synthetic inference choice | Allows forcing center to move across tray/dome band. | High | Posterior, QOI |
| Likelihood data usage | Whole complex FRFs and whole log response PSD | categorical | Implementation fact | Uses every frequency point; peak/notch locations are used only for reference checks and plots, not as likelihood summary statistics. | High | Likelihood, report, checker |
| Sampler | Random-walk Metropolis-Hastings in transformed positive variables | categorical | Fresh implementation choice | Simple auditable posterior sampler for toy run. | Medium | Posterior, diagnostics |
| Sensitivity scenarios | noise/discrepancy scale, damping scale, force bandwidth, QOI definition | mixed | Harness gate | Targets assumptions likely to move the QOI or engineering conclusion. | High | Sensitivity artifact |
