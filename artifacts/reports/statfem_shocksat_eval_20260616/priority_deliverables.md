# priority_deliverables.md — StatFEM ShockSat held-out-QOI evaluation

Each priority ask (task card §4) → interpretation → where delivered. A priority with no delivered artifact is a
failure; an "assumed" interpretation without confirmation is a warning.

| # | Priority ask (task §4) | Interpretation | Delivered in |
|---|---|---|---|
| 1 | ShockSat held-out-QOI evaluation across 5 bias combos × discrepancy arms; every NUTS arm gate-converged or labeled not-yet-converged | 5 combos × 4 arms (M0/M1/M2/M3) NUTS sweep, all-variable convergence recorded per cell | `code/run_sweep.py` → `out/cell_*.json`; convergence in each cell + checker `convergence:*` gates |
| 2 | **Held-out-QOI coverage across the 5 combos (money result)** — per-arm coverage of held-out-sensor QOIs as a DISTRIBUTION over the 5 combos | per arm: held-out peak-FRF and band-GRMS QOI coverage at nominal 95%, aggregated over 5 combos (mean / spread / per-combo) | `out/coverage_summary.json`; `figures/figA_heldout_qoi_coverage.png` (the money figure); packet §"Money result" |
| 3 | θ recovery per group (identifiable vs not), tied to strain-energy/FIM identifiability gate | per-group θ posterior vs truth + covered flag; strain-energy table + FRF-FIM eigen-view at the realized σ_d floor | `code/identifiability.py` → `out/identifiability.json`; `figures/figC_theta_recovery.png`, `figE_identifiability.png` |
| 4 | Discrepancy-structure comparison: naive vs StatFEM-iid vs Schneider vs orthogonal | side-by-side coverage / QOI / σ_d / over-absorption across the 4 arms | `out/arm_comparison.json`; `figures/figB_arm_comparison.png`; packet §"Arm comparison" |
| 5 | StatFEM evaluation SCORECARD (claim → evidence → verdict → suggested improvement), folding in prior ShockSat partial-identifiability + Schneider findings | a table of StatFEM claims, the evidence number from this study, GREEN/YELLOW/RED verdict, and a concrete improvement | `out/scorecard.json`; packet §"Scorecard"; deck scorecard slide |
| 6 | Immutable `check.py`, `run_all.sh`, `runtime.json`, tufte packet + slide deck for Ilias (gated on non-RED) | written-first checker; one-command replay; runtime accounting; packet.md; `slides/` (~8–12) | `check.py`, `run_all.sh`, `runtime.json`, `packet.md`, `slides/` |

## Acceptance (from task §11 checker)
GREEN requires ALL: every NUTS arm gate-converged or labeled not-yet-converged; held-out-QOI coverage with
numbers for all arms across all 5 combos; naive shown confidently wrong where injected error is large; StatFEM
`d` coverage quantified; iid/Schneider/orthogonal comparison reported; θ identifiable-vs-not vs strain-energy
gate; reduced FRF validated against a fuller solve; scorecard present.
YELLOW (never "success"): synthetic surrogate error; any parameter-level miss; any not-yet-converged arm; a
combo-dependent (fragile) result.
RED: undocumented non-convergence; a coverage claim without numbers; a missing/fabricated figure;
tufte_lint/image-QA/text-overlap failure; the coupled tray model used; an original scaffold edited in place;
reduced FRF not validated.

## Verdict policy (task §1, §14)
"StatFEM does not work (here)" is a permitted, valuable finding. The checker certifies that the criterion is
BUILT and REPORTED with numbers — it does NOT force StatFEM to win. The direction the numbers fall is the science.
