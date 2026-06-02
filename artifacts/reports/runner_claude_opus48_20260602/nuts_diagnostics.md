# NUTS/HMC Diagnostics

Sampler: **NUTS (NumPyro 0.19.0 / JAX 0.4.30)**, real run. Not random-walk/random-scan
Metropolis. Machine-readable values in `nuts_diagnostics.json`. Two independent inferences
were run on the same staged data: a **full FRF/PSD likelihood** and a **peak-feature likelihood**.

Settings: 4 chains, 1000 warmup + 1000 samples per chain (4000 post-warmup draws),
`target_accept_prob=0.9`, `max_tree_depth=10`, x64 enabled, seed 20260602 (full) / 20260603 (peak).

| Diagnostic | Full FRF/PSD | Peak feature | Gate | Result |
|---|---:|---:|---|---|
| Sampler | NUTS (numpyro) | NUTS (numpyro) | must be NUTS/HMC | pass |
| Divergences (total) | 0 | 0 | < 2% of draws | pass |
| Divergence fraction | 0.000 | 0.000 | < 0.02 | pass |
| Final adapted step size | 0.0521 | 0.0367 | reported | pass |
| Mean accept prob | 0.949 | 0.892 | ~target 0.9 | pass |
| Max leapfrog steps | 127 | 255 | < 2^10−1 | pass |
| Max observed tree depth | 7 | 8 | < 10 (no saturation) | pass |
| Min ESS (n_eff) | 942 | 1495 | > 200 | pass |
| Max R-hat | 1.0024 | 1.0019 | < 1.05 | pass |
| Wall time | 57.6 s | 83.6 s | — | — |

ESS/R-hat were computed by `numpyro.diagnostics.summary` over chain-grouped draws for the
monitored quantities: `dome_hz`, `tray_hz`, `zeta1`, `zeta2`, `sigma_build_ln`,
`sigma_sensor_ln`, `sigma_build_db`, `sigma_sensor_db`, `q_tray_struct_meanforce`,
`q_iface_struct_meanforce`. Tree depth is reported as the implied depth `log2(num_steps+1)`
from the recorded per-iteration leapfrog `num_steps`; no chain reached the depth-10 cap.

## Interpretation
- Both runs mixed cleanly (no divergences, R-hat ~1.00, healthy ESS), so the posterior
  summaries are trustworthy *as samples of the stated model*. This is a sampler-quality
  statement, not a proof the model/physics is correct.
- The peak-feature run needed deeper trees and a smaller step size (the feature posterior is
  flatter/less identified), consistent with the lossy likelihood discarding information.
