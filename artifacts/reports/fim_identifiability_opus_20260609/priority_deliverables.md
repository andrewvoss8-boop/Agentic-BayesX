# Priority deliverables — pre-test FIM identifiability + experiment design

Restated (my words) from the to-do item Andrew told me to execute:
> "build the pre-test sensitivity/FIM analysis on the Opus tray FEM — compute each
> candidate parameter's effect on the observable modes and on the load QOI, the FIM
> eigen-directions (which combos are stiff vs sloppy), and the SVD-subset downselect,
> for the 1-sensor and 2-sensor (transmissibility) cases. Turn 'you can support ~1–3
> parameters' from an estimate into a number with a plot, and double as the
> experiment-design (where-to-hit/where-to-measure) result."

| # | Priority ask | Where delivered |
|---|---|---|
| 1 | Candidate parameter menu on the Opus Phase-1 tray FEM | `code/fim_model.py` (`PARAM_NAMES`), `assumptions_ledger.md` |
| 2 | Each parameter's effect on the observable modes | `fim_results.json: freq_sensitivity_Hz_per_unit`, `figures/fig2_sensitivity_heatmap.png` |
| 3 | Each parameter's effect on the load QOI | `fim_results.json: qoi.d_qoi_d_theta`, `figures/fig6_qoi_vs_data.png` |
| 4 | FIM eigen-directions: stiff vs sloppy combinations | `fim_results.json: designs.*.fim_eigenvalues / stiff_direction / sloppiest_direction`, `figures/fig1_fim_eigenspectrum.png` |
| 5 | SVD/QR subset downselect with a condition-number threshold | `fim_results.json: designs.*.qr_subset_param_names` (QR_COND_THRESH=100), `code/run_fim.py: qr_subset` |
| 6 | 1-sensor (auto-spectrum) AND 2-sensor (transmissibility) cases | three designs in `fim_results.json: designs` |
| 7 | "N identifiable params/combinations" as a NUMBER + plot | headline = **3** (band ≤570 Hz); band-conditional **1→2→3**; `figures/fig1`, `fig4` |
| 8 | Experiment design: where-to-measure / where-to-hit | `fim_results.json: experiment_design`, `figures/fig5_experiment_design.png` |
| 9 | Confirm with profile likelihood (honesty: FIM is local) | `profile_likelihood.json`, `figures/fig7_profile_likelihood.png` |
| 10 | Run WITH the model as-is; held-out coverage is the real referee (noted) | `packet.md` §limits |

## Interpretation / scope flags (surfaced up front)
- **"Opus tray FEM" = the Phase-1 hexapod tray** in `runs/fem_phase1/opus/` (a 300×300×12.7 mm
  6061-T6 plate on 6 aluminium-tube struts with stiff moment-free joints, fixed base). I used
  the JAX hand-assembled, differentiable build because it exposes separable per-group stiffness.
- **Lead did this directly** (not handed to an Opus runner) because it is a bounded, fully
  artifact-backed numerical analysis and Andrew said "execute this". The to-do previously tagged
  it "Spec as an Opus runner task"; that tag is superseded by Andrew's go (see `decisions_log.md`).
- **This is NOT a posterior sampler run.** It is a Fisher-information (local) + profile-likelihood
  (semi-global) identifiability study. No NUTS/HMC is claimed or implied. When a real Bayesian
  update is run on this structure, NUTS/HMC remains the default per the sampler rule.
- **Discrepancy not yet included.** This is pre-test design on the nominal FEM; model-form
  discrepancy will only *reduce* practical identifiability. The numbers here are an *upper bound*
  on what the test can resolve. Stated in `packet.md` and `assumptions_ledger.md`.
