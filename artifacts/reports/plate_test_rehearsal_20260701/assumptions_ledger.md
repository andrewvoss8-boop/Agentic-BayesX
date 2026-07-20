# Assumptions ledger — plate-test rehearsal

Plain-English note: "log-amplitude sigma" = the standard deviation of the natural log of an
amplitude multiplier; sigma 0.8 means the amplitude is uncertain by roughly a factor e^0.8 ~ 2.2
either way. "Posterior" = the probability distribution after seeing data; "prior" = before.

| id | assumption | value / units | type | rationale / source | sensitivity priority |
|----|-----------|----------------|------|--------------------|----------------------|
| A1 | Reduced FEM: K(theta) = A_fix + sum_g theta_g A_g, 74-dim, 9 stiffness groups, mass = I | — | model form | inherited (netcg / psd_envelope realfrf.load_reduced); theta posterior reproduced by same L5 likelihood | fixed (out of scope) |
| A2 | Damping zeta = 0.01 all modes | 1% | fixed assumption | netcg convention | low (band RATIOS insensitive; documented there) |
| A3 | Truth theta_true ~ draws from the existing L5 posterior (`theta_post_L5.npz`) | ±~4% typical | synthetic truth | plausible stiffness truths consistent with the measured global modes | low |
| A4 | Truth drumhead SHAPE = model shape mixed with in-band drumhead basis + OUT-OF-BAND plate modes (fine structure the sensor array cannot fully capture), coefficient scales calibrated so the net-participation log-amplitude sd ~= SD_A_U | SD_A_U = 0.80 main; {0.4, 1.6} sensitivity | synthetic truth (epistemic) | netcg tier-2 value; the fine-structure component is what makes the rehearsal honest (worst-mode captured only ~0.39 at 12 sensors per pretest_design) | HIGH (S1/S2 sensitivity arms) |
| A5 | Truth amps for NON-target modes: measured tier sd 0.35, unmeasured non-drumhead tier sd 0.80 | log-amp | synthetic truth | netcg truth-ensemble convention. DD3 later estimated measured-mode scatter ~0.86 at POINT level; at the 1-oct level used here 0.35 was held-out validated — carried as a stated limit | medium (noted, not re-swept) |
| A6 | The new test measures target drumhead FREQUENCIES at measured-tier sigma (1%) and mode-shape samples at the sensors; identification from the +Y drive succeeds | 1% freq | data model | pretest_design observability (the +Y drive covers the drumhead band incl 230.6 Hz); identification failure is NOT modeled — stated limit | medium |
| A7 | Sensor noise on shape samples: additive Gaussian, sigma_y = 10% of that mode's plate-field RMS; INFERRED in the model (HalfNormal prior) rather than assumed known | 10% | observation noise | hammer-survey realism (coherence ~0.85); inferring sigma_y avoids handing the model the true noise | medium |
| A8 | Placement jitter (arm A3): each sensor relocated to a random plate node within 1.5 in of nominal | 1.5 in | test variability | install tolerance on a ~17-in-radius plate | part of S5 |
| A9 | Inference shape BASIS frozen at theta_MAP (drumhead-band model modes); theta enters only the frequency likelihood | — | model simplification | avoids eigenvector-derivative degeneracy in NUTS on the near-degenerate 234-258 Hz cluster; justified: the theta posterior is tight (±4%) and shapes move little across it | HIGH — checked via basis-frozen-vs-theta_true shape mismatch being INSIDE the truth model already |
| A10 | (REVISED per D8) Un-representable fine structure carried in DELIVERY as explicit out-of-basis draws d ~ N(0, kappa) through g_extra (the same scale the truth generator and the c prior use); shape-coefficient prior c ~ N(e_i, kappa) so prior == truth-generating process == tier model (prior-only band must reproduce ~5.4x — consistency check run before campaign) | kappa (calibrated ~0.106 @ SD 0.8) | uncertainty carriage | without prior/tier consistency the arms are not comparable to the analytic curve (D8: caught in smoke test); without the d-term the posterior would falsely sharpen | HIGH (drives S1 vs S2 trade) |
| A11 | Delivery ensemble: theta posterior draws x shape-coefficient posterior draws x A10 inflation x tier draws for non-target modes | 60 theta x 40 | uncertainty carriage | netcg Method-ensemble convention | — |
| A12 | Frequency grid 45-260 Hz, 400 linear pts + 1-oct smoothing | — | discretization | netcg discretization gate (peaks resolved; documented there); smoothing = the agreed delivery resolution | low |
| A13 | Uniform-mass tray proxy for net-CG participation | — | model form | inherited netcg limit | fixed (out of scope) |

## Data counts
- Synthetic datasets: 8 seeds/arm x 4 arms + 4 sensitivity runs (2 seeds x sigma in {0.4, 1.6}) = 36 runs.
- Per seed: n_target drumhead modes (~4) x n_sensors shape samples + n_target frequencies +
  the 20 existing measured modal frequencies (real .ash/FRF-derived, unchanged from netcg).
- No build-to-build or test-to-test variability beyond A7/A8 (single synthetic build per seed).

## Inferred vs fixed vs latent (per NUTS run)
- INFERRED: theta (9 stiffness multipliers), shape coefficients c_ij (n_target x n_basis),
  sigma_y (sensor noise), sigma_w2 (modal-frequency error scale).
- FIXED: zeta, tier sigmas, basis (A9), grid, tray proxy, inflation rule (A10).
- LATENT NOT INFERRED: out-of-basis truth shape component (carried as A10 inflation, not
  estimated); non-target unmeasured-mode amplitudes (tier prior only).
