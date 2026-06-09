# Priority Deliverables — Search Runner (modeling-freedom / anti-overfitting)

Restating the master/contract priority asks in my own words, the interpretation, and where each
is delivered. A priority with no artifact = failure; an "assumed" interpretation = warning.

| # | Priority ask (my words) | Interpretation | Delivered in |
|---|---|---|---|
| P1 | Make the "garden of forking paths" visible: log EVERY config tried | One row per (model form, discrepancy, priors, hyperparams) with dev score, R-hat/ESS/div, query idx, timestamp | `results_table.csv` |
| P2 | Reusable-holdout discipline on dev scores | Round/jitter dev LPD to a stated noise threshold; only register improvements above it | `results_table.csv` (registered flag) + packet threshold section |
| P3 | Mandatory ablations through SAME pipeline | drop discrepancy; vary prior width; coarsen modal resolution; centered vs non-centered | `ablations/` + results_table rows |
| P4 | Deliberate-overfit probe (synthetic) | over-flexible per-mode-per-realization additive discrepancy, many adaptive queries, no restraint; plot dev vs query | `overfit_probe/` (csv + figure) |
| P5 | Convergence gate as HARD disqualifier | report R-hat/ESS/div over ALL sampled vars incl. raw latents; disqualify failures from finalists | `diagnostics/` + per-finalist tables/plots |
| P6 | Lock <=3 finalists + sha256 BEFORE any vault access | exact schema for synthetic vault scorer | `finalists.json`, `finalists.sha256` (git-committed) |
| P7 | Committed ShockSat OOD prediction BEFORE pyro re-download | held-in modal MAC + freq error (leave-one-mode-out self-estimate) + predicted PYRO-regime QOI | `shocksat_predictions.json` (in finalists.sha256) |
| P8 | Human-review packet | search summary (N), overfit picture, ablations, convergence, explicit "NOT vault-tested" | `packet.md` |
| P9 | One-command replay + runtime accounting | run_all.sh, runtime.json (active vs wallclock), files_changed.md | repo root of runner_opus |

AMBIGUITIES flagged (assumptions stated, not silently guessed):
- A-amb1: forward-model masses/topology not in public config -> assumed fixed-free uniform-mass
  chain (decisions_log A1-A3). pred_theta absolute scale depends on this. WARNING-level.
- A-amb2: vault QOI scalar definition not readable -> committed peak-|H| over band (decisions_log).
  Cross-finalist overfit ranking robust; absolute qoi error may not be. WARNING-level.
- A-amb3: ShockSat pyro QOI is a genuine OOD extrapolation from a modal-band twin -> committed
  with wide uncertainty + stated method. Not a validated number.

SUCCESS for THIS run = honest "N configs tried, here is dev-vs-vault gap + which guardrail caught
the overfit", NOT a polished best model. No winner is validated until the human runs the vault.
