# Ablations (contract S5) — re-scored through the SAME dev/CV pipeline

Each ablation was run through the identical NUTS fit + held-out dev-LPD pipeline as the main
search (`src/search.py`, stages `ABL_*`). Full numbers in `ablation_results.csv`; figure in
`../figures/04_ablations.png`. Summary:

| Ablation | dev-LPD | gate | finding |
|---|---|---|---|
| Drop discrepancy (none) | 323.2 | pass | discrepancy earns ~246 nats -> real model-form error |
| Prior width 0.1 | 569.1 | pass | theta well-identified; prior width negligible |
| Prior width 0.7 | 568.9 | pass | likelihood dominates prior |
| Coarsen to 4 modes | 377.9 | pass | fewer obs -> lower LPD; theta shifts |
| Coarsen to 3 modes | 279.8 | pass | QOI-driving high modes lost |
| Centered param. | 562.2 | **FAIL (R-hat 33)** | non-centered is required for the hierarchical variance |
| Non-centered (ref) | 569.1 | pass | the working default |

Key: the centered-vs-non-centered ablation isolates the parameterization — same model, the
centered version is disqualified by the convergence gate. The drop-discrepancy ablation quantifies
that the model-form error (missing joint) is real and worth ~246 nats of held-out predictive
density.
