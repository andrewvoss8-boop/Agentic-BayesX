# NUTS Convergence Diagnostics — Round 3 (Claude Code Opus 4.8)
**Sampler:** NUTS (NumPyro), 4 chains, 1500 warmup + 2000 draws/chain, non-centered=True, target_accept=0.99.
**Converged / NUTS-active (EARNED):** True
## Gate (Stan Ref Manual / Vehtari et al. 2021)
- rank-split R-hat < 1.01; bulk AND tail ESS >= 400 (>=100×chains); divergence fraction < 0.02.
## Worst-case over ALL 29 monitored scalars (incl every raw z_dome/z_tray latent)
- worst rank-split R-hat = **1.0014** (z_dome[3])  → pass=True
- min bulk ESS = **2458** (sigma_build_dome)  → pass=True
- min tail ESS = **3198** (z_dome[0])
- divergences = **0** (fraction 0.0000)  → pass=True
- max tree depth observed = 8.6 (setting 12); fit runtime 5.2 s

## Per-variable (full table in nuts_diagnostics.json)
| variable | rank-split R-hat | bulk ESS | tail ESS |
|---|---|---|---|
| log_f_dome | 1.0009 | 10288 | 5500 |
| log_f_tray | 1.0002 | 9757 | 6103 |
| log_zeta_dome | 1.0004 | 10103 | 5837 |
| log_zeta_tray | 1.0001 | 9127 | 5448 |
| sigma_sensor | 1.0002 | 10719 | 6045 |
| sigma_build_dome | 1.0002 | 2458 | 3289 |
| sigma_build_tray | 1.0008 | 2811 | 3401 |
| z_dome[0] | 1.0001 | 2492 | 3198 |
| z_dome[1] | 1.0003 | 9655 | 5302 |
| z_dome[2] | 1.0002 | 9475 | 5542 |
| z_dome[3] | 1.0014 | 7387 | 4635 |
| z_dome[4] | 1.0003 | 9993 | 5005 |
| z_dome[5] | 0.9996 | 9388 | 5299 |
| z_dome[6] | 1.0004 | 8526 | 4992 |
| z_dome[7] | 1.0006 | 10546 | 5054 |
| z_dome[8] | 1.0007 | 8556 | 5504 |
| z_dome[9] | 1.0010 | 10577 | 5658 |
| z_dome[10] | 1.0001 | 10927 | 5080 |
| z_tray[0] | 1.0008 | 2808 | 3261 |
| z_tray[1] | 1.0004 | 11105 | 5587 |
| z_tray[2] | 1.0001 | 9977 | 5312 |
| z_tray[3] | 1.0005 | 9861 | 5098 |
| z_tray[4] | 1.0005 | 10457 | 5168 |
| z_tray[5] | 1.0010 | 11079 | 5518 |
| z_tray[6] | 1.0000 | 10725 | 5042 |
| z_tray[7] | 1.0000 | 11438 | 5759 |
| z_tray[8] | 1.0008 | 11220 | 5434 |
| z_tray[9] | 1.0004 | 10901 | 5721 |
| z_tray[10] | 1.0001 | 10095 | 5160 |
