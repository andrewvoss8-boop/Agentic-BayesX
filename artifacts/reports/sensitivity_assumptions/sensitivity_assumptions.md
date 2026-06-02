# Sensitivity to Error Assumptions

This first sensitivity artifact varies the synthetic observation-noise and GP-discrepancy assumptions and measures error against the clean synthetic truth.

It is deliberately modest: it does not claim posterior sensitivity, BOED usefulness, or robustness of the engineering conclusion. It documents a miss in the prior packet: uncertainty types were named, but the workflow did not show how outputs change under different assumptions.

![Sensitivity plot](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/sensitivity_assumptions/sensitivity_error_assumptions.png>)

| Scenario | sigma_re | discrepancy_scale | discrepancy_corr_logfreq | median rel error | max p95 rel error |
|---|---:|---:|---:|---:|---:|
| baseline | 0.02 | 0.03 | 0.08 | 0.04407 | 0.7849 |
| high_sensor_noise | 0.05 | 0.03 | 0.08 | 0.07491 | 1.048 |
| high_gp_discrepancy | 0.02 | 0.08 | 0.08 | 0.1148 | 1.915 |
| long_gp_correlation | 0.02 | 0.03 | 0.2 | 0.05644 | 0.5004 |
| low_noise_optimistic | 0.005 | 0.01 | 0.08 | 0.01421 | 0.2512 |

## Next Sensitivity Steps

- Repeat the study through full MCMC posterior summaries, not only synthetic-data error summaries.
- Vary structural assumptions such as damping, source/load convention, and tied versus untied coupling.
- Report whether experiment recommendations or QOI uncertainty rankings change under each assumption set.
