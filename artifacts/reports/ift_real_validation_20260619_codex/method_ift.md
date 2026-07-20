# method_ift.md - IFT arm for the real ShockSat comparison

## Intuition

The StatFEM whole-FRF arm tried to make the FEM prediction match every measured `log|H|` point through the likelihood. On the real ShockSat, the coarse FEM cannot place all sharp resonances closely enough, so that likelihood became multimodal or absurdly wide.

The IFT arm moves the physics into the prior. For each drive frequency, the unknown reduced response field `u(omega)` is allowed to deviate from the dynamic-stiffness equation, but deviations cost probability according to a learned trust value `beta`. Large `beta` means "trust the FEM equation tightly." Small `beta` means "the data are telling us the physics residual must be loose."

## References

- Hao and Bilionis, "An information field theory approach to Bayesian state and parameter estimation in dynamical systems", arXiv:2306.02150, https://arxiv.org/abs/2306.02150.
- Alberts and Bilionis, "Physics-informed Information Field Theory for Modeling Physical Systems with Uncertainty Quantification", arXiv:2301.07609, https://arxiv.org/abs/2301.07609.

The core adaptation follows their field-prior move: construct a physics-informed prior probability measure over the system response field, connect observations through a measurement model, and infer the trust/model-form-error parameter.

## Field Prior

For each measured drive frequency `omega = 2*pi*f`, define the reduced displacement response field

`u(omega) in C^74`

and dynamic-stiffness residual

`R(u; theta, omega) = Z(theta, omega) u - f_drive`,

where

`Z(theta, omega) = (1 + i eta) K(theta) - omega^2 I`,
`K(theta) = A_fix + sum_g theta_g A_g`,
`eta = 2 zeta`,
`zeta = 0.01`,
and `f_drive` is the copied StatFEM reduced drive row for the same ShockSat impact point.

The IFT prior is

`pi(u | theta, beta) proportional to exp(-(beta/2) ||Z(theta, omega) u - f_drive||^2)`.

For an invertible `Z`, this is a complex Gaussian with mean `Z^{-1} f_drive` and covariance proportional to

`beta^{-1} (Z^H Z)^{-1}`.

The measured accelerance at a response channel is

`H_s(omega) = -omega^2 S_s u(omega) / 386.0886` in `[g/lbf]`,

with the same observation rows and unit conversion as copied `realfrf.py`.

## Likelihood and Adaptation

The inherited apples-to-apples observable is the same whole-FRF magnitude used by the StatFEM field-likelihood arms:

`y_s(omega) = log |H_measured_s(omega)|`.

Because `log|.|` is nonlinear, the Gaussian field marginalization is not exactly closed-form in this observable. The implemented headline arm therefore uses a first-order log-magnitude moment approximation:

`log |H_s| approximately Normal(log |mu_H_s|, 0.5 Var(H_s) / |mu_H_s|^2)`,

and the measurement model

`y_s(omega) ~ Normal(log |mu_H_s(theta)| + c, sigma_meas^2 + sigma_IFT_s(omega)^2)`,

where `sigma_meas = 0.15`, `c` is the same global natural-log units-gain nuisance, and

`sigma_IFT_s(omega)^2 = min(0.5 Var(H_s) / |mu_H_s|^2, 25)`.

The variance cap is a numerical guard for near-zero predicted magnitude points; it prevents one antiresonance from creating infinite log variance. This cap is an adaptation and must be reported.

## Priors

- Identifiable stiffness multipliers: the same four StatFEM identifiable groups are inferred: `bottom_box`, `cross_beam`, `plates`, and `top_box`.
- `log(theta_g) ~ Normal(0, 0.25^2)`, matching the StatFEM prior.
- `c ~ Normal(5.6, 1.5^2)`, matching the empirical StatFEM global gain prior.
- `log(beta) ~ Normal(log(1e3), 2.0^2)` for the headline run. The center is inherited from the consistency toy and checked against the ShockSat log-magnitude variance scale; the sensitivity gate varies this log-standard-deviation by 3x wider and 3x tighter.

## Prediction

For held-out channels, the IFT posterior over `(theta, beta, c)` is pushed through the same copied reduced forward mapping. Predictive samples include the IFT field-induced log-magnitude variance under the same approximation, then peak accelerance and band-GRMS are scored by copied `score.py`.

## Honest Limit

This is a faithful physics-in-prior IFT construction for the linear field, but the headline real-data comparison inherits a nonlinear `log|H|` measurement. The approximation keeps the StatFEM observable identical; an exact complex-field observation would be a separate sensitivity arm, not the apples-to-apples headline.
