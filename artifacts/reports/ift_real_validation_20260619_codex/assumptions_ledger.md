# assumptions_ledger.md

| Assumption | Value | Units | Source / rationale | Sensitivity priority |
|---|---:|---|---|---|
| Real data | hit-001 single-impact FRF, 45-260 Hz band | g/lbf | Inherited from `statfem_real_validation_20260617` | HIGH |
| Frequency lines | 173 | count | Native copied measured FRF band | MED |
| Validation axis | observed/held-out channel split only | count | One hit and one impact location are available | HIGH, YELLOW |
| Bad-channel exclusions | ch101, ch29, ch30, ch31 | DAQ channels | Copied `realfrf.py`; TestLog flags | LOW |
| Dynamic-range eligibility | `DR >= 30`, currently 77 channels | count | Copied `heldout_qoi.py`; differs from prompt's 80-channel text | MED |
| Reduced dimension | 74 | DOF | Copied reduced model | HIGH |
| Mass matrix | `I` | reduced units | Copied reduced model | LOW |
| Stiffness form | `K(theta)=A_fix+sum theta_g A_g` | rad^2/s^2 | Copied `core.py` / `realfrf.py` | HIGH |
| Damping | `zeta=0.01`, `eta=2*zeta` | fraction, loss factor | Copied real-data runner value | HIGH |
| Measurement floor | `sigma_meas=0.15` | natural-log magnitude | StatFEM whole-FRF arms | HIGH |
| Gain prior | `c ~ Normal(5.6, 1.5^2)` | natural-log gain | StatFEM whole-FRF arms | MED |
| Theta prior | `log(theta_g) ~ Normal(0, 0.25^2)` | dimensionless | StatFEM prior | MED |
| Inferred theta groups | bottom_box, cross_beam, plates, top_box | dimensionless multipliers | StatFEM strain-energy/FIM gate, 4-of-9 clear the floor | HIGH |
| Fixed theta groups | other five groups at 1.0 | dimensionless multipliers | Fair comparison to identifiable-subset arms | MED |
| IFT beta prior | `log(beta) ~ Normal(log(1e3), 2.0^2)` | inverse residual norm units | IFT consistency toy plus ShockSat scale check | HIGH |
| Log-magnitude marginalization | first-order moment approximation | n/a | Required because `log|H|` is nonlinear | HIGH, YELLOW |
| Log-variance cap | 25 | natural-log variance | Numerical guard at predicted near-zero magnitudes | MED |
| Split seeds | 0-24 | integer | Match L5 MC distribution when available | MED |
| Scorer | copied `score.py` | n/a | Proper interval/Winkler, CRPS, log predictive density | HIGH |

## Uncertainty Types Kept Separate

- Parameter uncertainty: posterior over the four inferred stiffness multipliers.
- Model-form/trust uncertainty: posterior over `beta`.
- Observation noise: fixed `sigma_meas = 0.15` on `log|H|`.
- Field uncertainty: IFT prior covariance induced by finite `beta`.
- Build/test variability: absent; one hit and one impact only.
- QOI uncertainty: posterior predictive distribution of peak accelerance and band-GRMS at held-out sensors.
