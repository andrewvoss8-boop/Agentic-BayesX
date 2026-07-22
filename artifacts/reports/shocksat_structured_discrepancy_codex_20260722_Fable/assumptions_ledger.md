# Assumptions ledger — Task Card E `_Fable`

Numerical values, units, rationale, source and sensitivity priority. "Priority" = how likely changing it is to
change the decision (H/M/L).

## A. Forward model and physics

| # | assumption | value / units | rationale | source | sensitivity |
|---|---|---|---|---|---|
| A1 | reduced stiffness model | `K(theta) = A_fix + sum_g theta_g A_g`, 74x74, mass = I | frozen reduced twin; 8 ms eigensolve makes 20 folds x 4 arms tractable | `shocksat_modelclass_L5_20260619/data/reduced_blocks.npz` | L (identity re-verified, KA2) |
| A2 | modal damping in the forward | `zeta = 0.01` (dimensionless), constant over 46.8–258.4 Hz | matches the exponential-window added damping `zeta_w(100 Hz) = 0.0097`; used by every frozen predecessor | `realfrf.ZETA_NOM`; window constants `N=122880`, `end=0.05`, `FS` | **H** — SENS-1 |
| A3 | true structural damping | ~0.25–0.38% from the survey (`sensor_coords.npz: damp_pct`) | far below the window-added value, so window damping dominates | frozen survey | M |
| A4 | drive placement | nearest kept FEM DOF to the stored impact point, on the drive axis | frozen `Reduced.reduced_row`; max snap distance 0.75 in | `realfrf.py` | L |
| A5 | combined `+XY` drive | modelled on its **X** row | frozen convention from `modal_multiref.py`; a genuine approximation for a 45-degree corner hit | frozen | M (drive family only) |
| A6 | boundary condition | free-ish suspension, identical for all 5 drives, one build, one test campaign | single ShockSat1 unit; **no build-to-build or flight-to-flight variability is modelled because none was measured** | test log | — (documented gap) |
| A7 | 27 of 111 stored channels are dropped | no coordinates/axis/kept-DOF in the frozen map, plus TestLog-bad 29/30/31/101 | a location-transfer claim needs coordinates | `channel_map.csv` | L |

## B. Statistical model

| # | assumption | value / units | rationale | source | sensitivity |
|---|---|---|---|---|---|
| B1 | discrepancy covariance form | `sigma_u^2 [ r K_f (x) I_x + (1-r) I_f (x) K_x ]` | frozen by the card and by the in-project M2/M3 implementation | Task Card E; `schneider_faithful.py` | **H** — SENS-4 (Schneider's published form differs; see `question_framing.md`) |
| B2 | frequency correlation length | `l_f = 10 Hz` | Schneider posterior `l_co,f = 10.1 Hz` (PDF p. 10) | verified from PDF | M — SENS-3 |
| B3 | spatial correlation length | `l_x = 2000 in` (~50.8 m) | Schneider posterior `l_co,z = 49.8 m` | verified from PDF | M — SENS-3 |
| B4 | additive split | `r = 0.82` | Schneider posterior `r = 0.82` | verified from PDF | M — SENS-3 |
| B5 | `u` independent across drives | `rho = 0` | conservative; the card is silent | decisions_log F2 | **H** (makes E1 == E0 in 2 of 4 families) |
| B6 | coefficient prior | `Lambda_beta` diagonal, 6 dB main / 3 dB interaction | weakly informative on a log-magnitude discrepancy | preregistration §4 | M |
| B7 | `c_d` prior | `Normal(c_bar, tau_c^2)`, both fitted on training drives | card quantity contract | card | M |
| B8 | `sigma_e^2` vs channel nugget | `sigma_e^2 = s_nug * min_i p_i`; `nugget_i = s_nug (p_i - min p_i)` | the two are not separately identified without per-line repeats, and H1 is already impact-averaged | `data_inventory.json` | M |
| B9 | theta uncertainty | propagated as an additive predictive variance at test points; **not** conditioned on training residuals | keeps Stage 1 strictly modular, as the card requires | card | M — SENS-2 |
| B10 | Gaussian residual | assumed | the measured residual is heavy-tailed near resonances (per-drive IQR 17.6–26.1 dB); Gaussian CRPS/coverage are therefore approximations | measured | **H** (documented limitation) |

## C. Actual numerical values used (not placeholders)

| quantity | value |
|---|---|
| analysis band | 46.79 – 258.38 Hz, 105 lines, `df = 2.0345 Hz` |
| response channels | 84 (of 111 stored) |
| drives | 5 (`+X`, `+Y`, `+Z(990)`, `+Z(900)`, `+XY`) |
| impacts averaged per drive | 6, 4, 6, 6, 6 |
| total residual points | 5 x 105 x 84 = 44 100 |
| modal-posterior draws retained | 4000 stored; 60 used for the theta-variance field, all 4000 for known answers |
| `theta_0` (median) | `[1.0186, 1.0104, 0.9636, 0.9836, 1.0383, 1.0928, 0.9761, 1.0120, 1.0475]` for `al_welds, angle_brackets, bottom_box, contact, cross_beam, joints, plates, steel_welds, top_box` |
| `sigma_f` (modal likelihood) | median 0.04626, 95% CI [0.03387, 0.06743] |
| median measured coherence | reported per drive in `out/data_inventory.json` |

## D. Uncertainty taxonomy — what is and is not modelled

| kind | modelled? | how |
|---|---|---|
| parameter uncertainty (`theta`) | yes | propagated from the converged modal posterior into the predictive variance |
| observation / spectral-estimation noise | yes | `sigma_e^2`, inferred (not measured — no per-line repeats survive the H1 average) |
| model discrepancy (structured mean) | yes | `H beta`, the object under test |
| model discrepancy (residual GP) | yes | `u`, zero prior mean, frequency x location covariance |
| channel-specific variation | yes, as **variance only** | per-channel nugget; deliberately given zero predictive mean at unseen channels |
| forcing uncertainty | partly | per-drive log-gain `c_d`; the *shape* of the hammer spectrum is not modelled |
| aleatory / build / test variability | **no** | one unit, one campaign; there is nothing to estimate it from |
| boundary-condition uncertainty | **no** | single suspension configuration |
| QOI uncertainty (shear-load proxy) | reported where the frozen mapping is valid | via the frozen net-CG mapping |

## E. Inferred vs fixed vs not-inferred

- **Inferred (per fold, training only):** `c_d` (5), `beta` (~51–55 kept columns), `sigma_u^2`, `s_nug`,
  `c_bar`, `tau_c^2`, per-channel variance profile `p_i`.
- **Fixed a priori:** `l_f`, `l_x`, `r`, `zeta`, `theta_0`, `Lambda_beta`, spline knots, RBF centres/scale,
  region labels, split membership, all gate thresholds.
- **Latent, present, NOT inferred:** the true per-channel discrepancy realisation at held-out channels (by
  design — it has zero predictive mean); the hammer force spectrum shape; phase (only magnitude is modelled).
- **Hyperparameters that are fixed rather than inferred:** everything in the second bullet. `l_f`, `l_x`, `r`
  become inferred only inside SENS-3.

## F. Graphical presentation of assumptions

Figure 1 (`figures/fig1_graphical_model_fable.png`) is the run-specific graphical model separating `theta`,
the structured mean, the residual GP and observation noise, with the fixed/inferred status printed on each
node. It is drawn for this run; it is not a copied paper figure.
