# NUTS/HMC Diagnostics

NUTS active: false. HMC active: true. Backend: custom PyTorch fixed-trajectory HMC.

## full

- Divergences: 3
- Final step sizes: [0.00070598948286152, 0.0008767038245184567]
- Tree depth: not_applicable_fixed_trajectory_hmc; fixed leapfrog steps = 10
- Acceptance rates: [0.9789061019016151, 0.9851688369432476]
- ESS approximation: {
  "log_k1_rel": 320.0,
  "log_k2_rel": 47.778860903345326,
  "log_zeta1": 6.640747905730033,
  "log_zeta2": 9.648467512569622,
  "flight_force_offset_ln_psd": 9.135335405970007,
  "log_build_sigma_ln_psd": 12.31795679884642,
  "log_sensor_sigma_ln_psd": 10.503652449736053
}
- R-hat: {
  "log_k1_rel": 0.9969144199324415,
  "log_k2_rel": 1.025276746220452,
  "log_zeta1": 1.036455423723012,
  "log_zeta2": 1.8150701859290244,
  "flight_force_offset_ln_psd": 1.5834919934517626,
  "log_build_sigma_ln_psd": 2.6735248856839684,
  "log_sensor_sigma_ln_psd": 1.5532680021817018
}

## peak_feature

- Divergences: 0
- Final step sizes: [0.0018095136920273159, 0.001769279136639556]
- Tree depth: not_applicable_fixed_trajectory_hmc; fixed leapfrog steps = 10
- Acceptance rates: [0.9435879738154302, 0.9660639721252071]
- ESS approximation: {
  "log_k1_rel": 14.498553148363776,
  "log_k2_rel": 15.269618077557814,
  "log_zeta1": 6.275481251823187,
  "log_zeta2": 8.899891080198948,
  "flight_force_offset_ln_psd": 21.46550479404401,
  "log_build_sigma_ln_psd": 9.209345200270565,
  "log_sensor_sigma_ln_psd": 14.00438941468597
}
- R-hat: {
  "log_k1_rel": 1.0789132328441988,
  "log_k2_rel": 1.1487751461914293,
  "log_zeta1": 1.0097313741775835,
  "log_zeta2": 1.2569081885152995,
  "flight_force_offset_ln_psd": 4.574683650574597,
  "log_build_sigma_ln_psd": 1.1655356722912862,
  "log_sensor_sigma_ln_psd": 1.0492704546871174
}

