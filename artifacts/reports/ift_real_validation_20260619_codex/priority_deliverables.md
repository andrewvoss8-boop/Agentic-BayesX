# priority_deliverables.md

| ID | Priority ask | Interpretation | Delivery location | Status |
|---|---|---|---|---|
| P1 | Faithful IFT twin on real data | Physics is in the field prior, with learned inverse-temperature `beta`; inherited `log|H|` observable uses a documented log-magnitude approximation because exact Gaussian marginalization is not exact after `log(abs(.))`. | `method_ift.md`, `code/ift_arm.py` | Delivered, YELLOW caveat |
| P2 | Head-to-head held-out-sensor QOI scorecard | Compare IFT vs copied L5 and M2 provenance on peak accelerance and band-GRMS using `score.py`; use identical split seeds where results exist. | `out/scorecard.json`, `packet.md` | Delivered |
| P3 | `beta` thermometer and convergence table | Report posterior `beta`, weak/pinned identifiability, all-variable R-hat/ESS/divergence, and any TMCMC escalation. | `out/ift_split_*.json`, `out/convergence_table.json`, `figures/figB_beta_thermometer.png`, `figures/figE_convergence_table.png` | Delivered, YELLOW non-convergence |
| P4 | Immutable checker and one-command replay | Checker enforces provenance identity, verdict generation, figure/deck QA, and red/yellow/green status; replay writes `runtime.json`. | `check.py`, `run_all.sh`, `runtime.json`, `checker_report.json` | Delivered |
| P5 | Legible Tufte-compliant deck and held-out-FRF overlay | Generate numeric figures only from saved scripts; lint/QA/overlap-check every figure; deck claims trace to JSON and checker output. | `figures/`, `slides/ift_real_validation_honest_negative.pptx`, `slides/preview/contact_sheet.png` | Delivered |

## Acceptance Criteria

- Non-RED checker output from `bash run_all.sh`.
- Copied `core.py`, `score.py`, and data are byte-identical to `statfem_real_validation_20260617`.
- Scorecard/verdict comes from numbers, not prose.
- Any approximation, non-convergence, weak `beta`, single-hit/split-only limitation, or coarse-FEM ceiling is surfaced as YELLOW or RED according to the checker.
