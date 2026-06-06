# Blind inference — NUTS convergence diagnostics

Sampler: NumPyro NUTS, 4 chains, 1000 warmup + 1000 draws, non-centered hierarchy, target_accept 0.95.
Gate: rank-split R-hat<1.01, bulk&tail ESS>=400 over ALL latents (incl. raw z_b + discrepancy beta), divergences<2%.

## Main fit (with discrepancy)
- worst R-hat: **2.4114** (var: z_b)
- min bulk ESS: **5**, min tail ESS: **29** (var: z_b)
- divergences: **0 / 4000 (0.00%)**
- **GATE PASS: False**

If the gate FAILS, this is reported as the result (NOT 'NUTS active'); a likely cause is the
sigma_d<->sigma_e ridge under a mis-structured (frequency-only) discrepancy that cannot represent
the spatial/higher-mode model-form error (see decisions_log D19).

## Per-variable (worst over array elements)
| variable | max R-hat | min bulk ESS | min tail ESS |
|---|---|---|---|
| beta | 1.8296 | 6 | 38 |
| f_dome | 1.5815 | 7 | 32 |
| k_strut_pop | 1.8733 | 6 | 42 |
| log_k_strut_pop | 1.8733 | 6 | 42 |
| sigma_build | 1.7542 | 6 | 121 |
| sigma_d | nan | 4000 | 4000 |
| sigma_e | 2.0677 | 5 | 30 |
| z_b | 2.4114 | 5 | 29 |