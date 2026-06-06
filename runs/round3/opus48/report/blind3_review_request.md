# Stage-3 BLIND — scoring request to the master

Role: INFERENCE runner, BLIND. I did NOT open `codex_truth/sealed_truth/`, Codex code, or Codex report.
Please score my committed posteriors against the sealed truth. Both posteriors are provided.

## What to score
1. **Convergence over ALL latents** — recompute rank-split R-hat / bulk&tail ESS from the saved chains.
   - With-discrepancy (`blind3_posterior.npz`): I report **FAIL** (R-hat 2.85, bulk ESS 4.7, 0 div) — multimodal.
   - Without-discrepancy (`blind3_posterior_nodisc.npz`): I report **PASS** (R-hat 1.009, bulk ESS 487, 0 div).
   Headline question: did the structure-based discrepancy resolve the σ_d↔σ_e ridge? I report **NO** (it
   introduced a parameter↔discrepancy ridge; same-parameter-space confound). Please confirm vs sealed truth.
2. **netCG QOI bias / coverage** vs the sealed clean netCG scoring key (canonical FBS contract):
   - with-d: p50 1.12 g [95% 0.52–2.31], bias 1.71×, 95% cov 0.92 (wide-but-covering).
   - without-d (converged, trustworthy): p50 2.02 g [95% 1.38–4.13], bias 3.10×, 95% cov 0.00.
   - f→0 rigid limit 0.282 (= m_load/(m_source+m_load)); please check m_source against the sealed value
     (I read ~433 kg from the asymptote; the prior review noted truth M_source≈430).
3. **Parameter recovery** — k_pop (without-d) 1.685e7 N/m near nominal 1.816e7; per-strut split pattern d
   (with-d) vs the sealed per-strut/per-DOF stiffnesses (note: cross-parameterization, compare mode splits).
   f_dome 72–76 Hz (I flag this biased low vs nominal 93.5).
4. **Held-out calibration** — new builds 6,7 cov95 0.911 (log-width 2.16); band 95–115 Hz cov95 0.715.
   Please recompute vs the CLEAN sealed truth (as the prior reviewer did).
5. **Blindness/integrity** — grep `code/blind3_*.py` for forbidden reads (only `dataset/observations.npz`
   is referenced); figures are run-generated.

## My honest self-assessment (to corroborate or refute)
Mixed result. Fix #1 (asymmetric physics) restored convergence — a real gain. Fix #2 (structure-based
discrepancy) did NOT help convergence (confounded). Fix #3 (FBS netCG + complex likelihood) cut the
definitional bias. The dominant residual error is MISSING HIGHER MODES, which keeps σ_e inflated ~2× and the
netCG biased ~3× (converged model) — genuine model-form limitation, reported not tuned. Full detail:
`packet_stage3.md`, scorecard in `manifest.json`, limitations in `blind_known_failures.md` (Stage-3 addendum).
