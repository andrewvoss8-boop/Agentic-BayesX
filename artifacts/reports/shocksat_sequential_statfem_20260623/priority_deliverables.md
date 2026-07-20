# Priority deliverables - ShockSat sequential statFEM pilot

Restating Andrew's priority ask in my words, with the artifact that must carry each answer.

| # | Priority ask | Interpretation | Delivered in | Status |
|---|---|---|---|---|
| P1 | Build a bounded sequential statFEM elastodynamics pilot | Reduced modal-state Bayesian filter on clean ShockSat modal-hammer time histories, not a full-FE implementation of Kavrakov et al. | `code/sequential_modal_filter.py`, `packet.md` | delivered - reduced analogue only |
| P2 | Score only the inherited PSD-envelope QOI | Convert held-out predictions to response PSD `S_aa=|H|^2*S_F0`, `S_F0=1 lbf^2/Hz`, then apply the inherited smoothline envelope and GRMS/exceedance metrics. | `out/results.json`, `packet.md` | delivered - no green PSD-envelope win |
| P3 | Compare against FEM+6 dB and existing L5 if cheap | FEM+6 dB is recomputed on the same split; existing L5 probe is reused from `shocksat_psd_envelope_twin_20260623/out/probe_seed00.json`. | `out/results.json` | delivered |
| P4 | Start with the 90% training validity probe | One seed-0 leave-sensors-out split: 90% observed sensors, 10% held out, same split logic as the inherited PSD-envelope probe. | `out/results.json` | delivered |
| P5 | Do not hide model error in over-flexible forcing | Compare nominal all-error-as-modal-residual filtering with stiffness-updated-plus-residual filtering on the same split; report if residuals dominate. | `out/results.json`, `packet.md` | delivered - residual band remains large |
| P6 | Make the result checker-backed and replayable | One-command replay, checker, runtime accounting, source/assumption documentation, and continuity updates. | `run_all.sh`, `check.py`, `runtime.json` | delivered - checker YELLOW 18/3/0 |

Acceptance / honesty:
- GREEN only if a sequential variant has lower 97.5%-envelope GRMS than FEM+6 dB while meeting the energy-weighted exceedance gate, and `check.py` reports no red gates.
- YELLOW if the pilot runs but shows no PSD-envelope improvement, relies on fixed/empirical hyperparameters, or exposes a scoped modeling limitation.
- RED if held-out data leak into fitting, units or PSD conventions mismatch, required artifacts are missing, or success is claimed from time-domain/FRF diagnostics without PSD-envelope metrics.
