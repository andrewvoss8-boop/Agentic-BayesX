# Stage-3 BLIND NUTS diagnostics (ALL latents incl. discrepancy + per-build)

band (35.0, 160.0) Hz, 110 grid pts, 4 chains x (350+350); sigma_d LEARNED (not capped)

| latent | R-hat | ESS bulk | ESS tail |
|---|---|---|---|
| d0[0] | 2.8452 | 4.7 | 30.6 |
| d0[1] | 2.8440 | 4.7 | 30.6 |
| d0[2] | 2.8368 | 4.7 | 36.0 |
| d0[3] | 2.3398 | 5.1 | 40.9 |
| d0[4] | 2.8228 | 4.7 | 38.1 |
| d0[5] | 2.8282 | 4.7 | 34.1 |
| d_raw[0] | 1.8460 | 5.9 | 35.1 |
| d_raw[1] | 2.0725 | 5.4 | 34.7 |
| d_raw[2] | 2.5822 | 4.9 | 32.4 |
| d_raw[3] | 2.8353 | 4.7 | 33.2 |
| d_raw[4] | 1.8492 | 5.9 | 30.9 |
| d_raw[5] | 2.1291 | 5.3 | 33.8 |
| f_dome | 2.2233 | 5.2 | 32.9 |
| log_k_pop | 2.1059 | 5.4 | 36.0 |
| sigma_build | 1.8102 | 6.0 | 35.5 |
| sigma_d | 2.0117 | 5.5 | 38.8 |
| sigma_e | 2.0781 | 5.4 | 34.9 |
| z_b[0] | 1.5598 | 7.3 | 32.4 |
| z_b[1] | 1.3549 | 9.6 | 87.4 |
| z_b[2] | 1.1025 | 27.7 | 374.6 |
| z_b[3] | 1.5244 | 7.5 | 60.9 |
| z_b[4] | 1.1742 | 16.9 | 251.6 |
| z_b[5] | 1.0302 | 143.2 | 643.8 |

**worst R-hat 2.8452, min bulk ESS 4.7, min tail ESS 30.6, divergences 0**

Gate (R-hat<1.01, bulk&tail ESS>=400, div<2%): **FAIL**