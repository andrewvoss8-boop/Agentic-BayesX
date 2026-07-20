# Card E — Priority deliverables (restated in my own words) + where delivered

Advisor objective (Ilias): *evaluate the StatFEM approach, identify its gaps, suggest improvements.*
This card's sharp question: **does ENRICHING the model form (richer LOCAL stiffness parameterization and/or a
non-proportional damping model), run through the converged L5 modal-feature Bayesian likelihood, measurably
SHARPEN the calibrated-but-wide (≈×2.7) held-out-sensor QOI at the 8 hard ShockSat accelerometers, WITHOUT
degrading the global prediction?** A rigorous, scoped HONEST NEGATIVE is equally valuable.

| # | Priority ask | My interpretation | Acceptance criterion | Where delivered |
|---|---|---|---|---|
| P1 | Build a RICHER LOCAL parameterization | Regroup the 26 per-PID reduced blocks into finer sub-groups (split high-SE boxes per-shell; split bolted-joint bush_801; bulkhead shells) so the update can change LOCAL interface flexibility, not just whole-group level. θ=1 must reconstruct nominal exactly. | per-PID blocks projected + integrity check Σ==nominal ≤1e-9; ≥1 richer parameterization defined with rationale tied to hard-channel regions | `code/richmodel.py`, `out/perpid_reduced.npz`, `out/param_variants.json` (TBD) |
| P2 | Identifiability gate FIRST (AGENTS Modal-Identifiability) | For every new local stiffness param: modal strain-energy fraction f_{i,g} per matched mode + FIM eigen view (combos clearing the realized σ_w² discrepancy floor; which raw params each mixes). For damping params: dissipation fraction ζ_{m,g}. | gate run BEFORE any sharpen/no-sharpen conclusion; each param classified identifiable/not vs the realized floor; pre-test lever stated for non-identifiable params | `out/identifiability_rich.json`, `figures/fig_identifiability.png` (TBD) |
| P3 | Run the richer model through L5 (converged Bayesian), not a deterministic proxy | `modal_feature.calibrate_modal` (NUTS; all-var R̂/ESS/div per convergence gate; escalate to TMCMC if multimodal) with the richer θ vector. | all-variable R̂≤1.05, ESS≥200, div<2% reported; non-converged labeled YELLOW, never "NUTS active" | `out/l5_rich_calib.json` (TBD) |
| P4 | Score the held-out QOI before/after at the 8 hard accels | Held-out-SENSOR peak-\|H\| / band-GRMS via `heldout_qoi.py`+`score.py`: interval score / CRPS / coverage / z-std (NOT MAC), re-pairing-robust. Compare richer-model vs L5 baseline (×2.7 band) across ≥25-split MC. | before/after interval-score + CRPS at the 8 hard accels + the OTHER channels (no degradation), aggregated over ≥25 splits; SHARPEN claim only if lower interval/CRPS AND calibrated | `out/heldout_before_after.json`, `figures/fig_before_after.png` (TBD) |
| P5 | Optional non-proportional damping model | Das&Debnath C = α0 M + α1 K + Σ_g β_g K_g localized to identifiable groups; xlsx damping as target; gate dissipation-fraction identifiability first. | only pursued if P2 shows damping params identifiable; otherwise documented honest negative w/ the rank-deficiency evidence | `out/damping_rich.json` (TBD, conditional) |
| P6 | Scoped, auditable verdict | Three-tier green/yellow/red; scope every claim to exactly what was tested; lead with held-out QOI not MAC; state the participation/damping confound. | `packet.md` verdict generated from checker numbers, never stronger than checker output | `packet.md`, `check.py` (TBD) |

## Honesty guardrails (Card D lessons — prior runner repeatedly over-claimed)
- Do NOT say "model-form limit" when I mean "this parameterization is exhausted."
- Use re-pairing-robust metrics (tracked continuation / cross-orthogonality), never greedy best-MAC.
- A result is only as strong as the held-out-QOI score supports; checker output required before any improvement claim.

## SURFACE-to-Andrew (do NOT self-apply)
- Any durable-rule / checker / sampler-standard change.
- Any claim the richer model should REPLACE the inherited FEM.
- The `docs/report/project_log.md` row (propose at end).
- Decision point before committing the multi-hour ≥25-split NUTS MC (compute).
