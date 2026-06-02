# NUTS Diagnostics — Round 2 (Claude Opus 4.8)

**Verdict: PASS — converged; NUTS active.**

> 0 divergences — ideal (no divergence-related bias risk flagged).

## Sampler

- Sampler: NUTS (NumPyro); chains: 4; warmup: 1500; draws/chain: 2000; total post-warmup draws: 8000.
- target_accept_prob: 0.99; max_tree_depth setting: 12 (observed max 7.99); mean leapfrog steps/iter: 219.2.
- Parameterization: non-centered hierarchical build effects (build = sigma_build * z).
- Fit runtime (sampling only, excludes compile): 5.7 s.

## Source-backed gate (Stan Reference Manual / Vehtari et al. 2021)

- rank-normalized split-R-hat < 1.01 (1.05 only as labeled early-workflow fallback — NOT used as the pass bar).
- bulk-ESS AND tail-ESS >= 400 (= 100 x 4 chains).
- divergence fraction < 0.02 to avoid FAIL; 0 ideal.

## Worst-case over ALL sampled variables (incl raw latents)

- worst rank-split-R-hat = **1.0025** (z_tray[2]) — PASS
- min bulk-ESS = **2393** (sigma_build_dome) — PASS
- min tail-ESS = **3174** (z_tray[0])
- divergences = **0** (fraction 0.00e+00) — PASS
- monitored scalar quantities (incl every raw z): **29**

## Per-variable table (rank-split-R-hat / bulk-ESS / tail-ESS)

| variable | R-hat | ESS bulk | ESS tail |
|---|---:|---:|---:|
| log_k1_ratio | 1.0001 | 12644 | 6465 |
| log_k2_ratio | 1.0006 | 12296 | 6519 |
| log_zeta1 | 1.0005 | 9291 | 6150 |
| log_zeta2 | 1.0011 | 9586 | 5456 |
| sigma_sensor | 1.0008 | 9852 | 5854 |
| sigma_build_dome | 1.0014 | 2393 | 3502 |
| sigma_build_tray | 1.0008 | 2973 | 3229 |
| z_dome[0] | 1.0012 | 2413 | 3483 |
| z_dome[1] | 1.0003 | 9158 | 5167 |
| z_dome[2] | 1.0017 | 8154 | 5691 |
| z_dome[3] | 1.0009 | 7399 | 5182 |
| z_dome[4] | 1.0016 | 10180 | 5645 |
| z_dome[5] | 1.0003 | 9761 | 5323 |
| z_dome[6] | 1.0013 | 8413 | 5248 |
| z_dome[7] | 1.0002 | 9502 | 5651 |
| z_dome[8] | 1.0005 | 7086 | 5104 |
| z_dome[9] | 1.0002 | 10344 | 5630 |
| z_dome[10] | 1.0007 | 9634 | 5408 |
| z_tray[0] | 1.0007 | 2998 | 3174 |
| z_tray[1] | 1.0002 | 9820 | 5131 |
| z_tray[2] | 1.0025 | 10347 | 5580 |
| z_tray[3] | 1.0014 | 10126 | 5434 |
| z_tray[4] | 1.0010 | 11012 | 5805 |
| z_tray[5] | 1.0008 | 10909 | 5831 |
| z_tray[6] | 1.0010 | 10601 | 5393 |
| z_tray[7] | 1.0013 | 9517 | 5196 |
| z_tray[8] | 1.0003 | 10502 | 5588 |
| z_tray[9] | 1.0012 | 10973 | 5711 |
| z_tray[10] | 1.0006 | 9416 | 5144 |

## Fixed forcing constants (flight-to-flight 3 dB is KNOWN, not learned)

- sigma_q (log-3GRMS scatter from forcing): tray 0.197, interface 0.127; bias_tray 0.077, bias_iface 0.102; MC samples 4000.
