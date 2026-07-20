# priority_deliverables.md — Confidently-Wrong Model-Form-Error experiment

Each priority must have a delivered, checker-referenced artifact. "Assumed" interpretations are flagged.

| # | Priority ask (restated) | Interpretation | Delivered in |
|---|---|---|---|
| 1 | Head-to-head **converged** NUTS comparison across a model-form-error sweep δ: naive-no-discrepancy vs discrepancy-aware (iid and correlated). Every arm clears the convergence gate at every δ. | δ∈{0,0.05,0.10,0.20,0.35,0.50}; arms A1 naive / A2 iid / A3 correlated (+ A0 deterministic context), same data per δ; per-cell R-hat/ESS/div over ALL sampled vars. | `code/run_sweep.py`, `out/sweep_*.json`, checker gates `cell_converged:*`. |
| 2 | The two money curves: **held-out coverage vs δ** and **σ_d vs δ** (their Fig 4/5 analogs). | Fig A = held-out predictive coverage vs δ (A1 collapses, A2/A3 hold near nominal), small multiples by error class. Fig B = learned σ_d vs injected δ (A2/A3 monotone tracking; A1 absent/flat). | `figures/figA_coverage_vs_delta.png`, `figures/figB_sigmad_thermometer.png`. |
| 3 | The honest-limit result: a coherent confounded-bias case where the cure misses the parameter (QOI may still hold), with mechanism + the pre-test cure (break the degeneracy). | E-LIMIT: +15% coherent peak shift on the masked virtual target with `local_mode_modes`; α4 miss + QOI hold; FIM eigen-view of the peak-shift↔stiffness degeneracy; sensor-placement lever. | `code/exp_limit.py`, `out/limit_summary.json`, `figures/figD_honest_limit.png`. |
| 4 | Immutable checker encoding acceptance, one-command replay, runtime.json. | `check.py` written FIRST; GREEN/YELLOW/RED per Result Status Standard; `run_all.sh`; `runtime.json` (active + wallclock). | `check.py`, `run_all.sh`, `runtime.json`, `checker_report.json`. |
| 5 | Legible, tufte-compliant slide deck + ≥1 GIF (gated on the checker). | ~8–12 slides, every claim traces to a checker number; GIF 1 = FRF bands as δ rises. | `slides/`, `figures/gif1_frf_bands.gif`. |

## Success metrics (from the task's question/decision gate)
- (a) held-out predictive + QOI coverage vs nominal 95%;
- (b) σ_d recovery of the injected error δ;
- (c) convergence of every arm at every δ.

## Scope guardrail (no overclaim)
The claim we may earn: **"discrepancy-aware updating detects model-form error (σ_d) and preserves calibrated
predictive/QOI coverage where naive Bayesian calibration is confidently wrong."** We may NOT claim universal
parameter recovery — the E4-style coherent confounded bias is a known limit we reproduce and report (Priority 3).
