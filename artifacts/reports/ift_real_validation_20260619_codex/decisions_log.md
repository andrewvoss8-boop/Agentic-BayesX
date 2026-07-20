# decisions_log.md - IFT real ShockSat validation (Codex, 2026-06-19)

Runner: Codex. Human: Andrew Voss. Advisor objective: Ilias Bilionis.
Workspace: `artifacts/reports/ift_real_validation_20260619_codex/`.

## CURRENT STATE

- Goal: build a faithful Information Field Theory (IFT) arm, where physics enters the prior through a learned inverse-temperature `beta`, and compare it against the existing StatFEM real-ShockSat held-out-sensor QOI results on the same data, forward model, split protocol, and scoring rules.
- Last decision: reuse the StatFEM real-validation workspace only as read-only provenance; copy required code/data/results into this new workspace and never edit the StatFEM run in place.
- Next action: human review of the generated packet/deck/checker; do not promote any durable project-log row until the lead approves it.
- Open ambiguities / warnings:
  - A1: The lead prompt states "80 dynamic-range-eligible mapped channels", while the copied StatFEM `heldout_qoi.py` and current `measured_frf_cache.npz` yield 77 eligible channels after bad-channel exclusions and `DR >= 30`. Assumption: use the copied StatFEM code/data as source of truth for apples-to-apples scoring; report the count actually used.
  - A2: The prompt's exact Gaussian field marginalization is exact for a linear complex observation of the field `u`; the inherited apples-to-apples observable is `log|H|`, which is nonlinear. Assumption: keep the headline arm on the same `log|H|` observable and use a documented first-order log-magnitude Gaussian moment approximation. This is an adaptation and must be surfaced as YELLOW unless a later exact complex-observation sensitivity is added and clearly labeled non-headline.
  - A3: StatFEM M2 whole-FRF results are already computed for the prior workspace, but not for every one of the 25 L5 split seeds. Assumption: use the copied M2 failure as the direct whole-FRF baseline provenance and do not strengthen it into a 25-split distribution unless the run actually completes.
  - A4: Detached `nohup ... & disown` launch was reaped immediately by this tool session before writing any sampler output. Fallback: run the resumable 25-split IFT sweep in a managed foreground exec session and poll until it completes; record this as a runtime caveat.
  - A5: The discretization-invariance artifact is a split-0 post-hoc QOI frequency-grid diagnostic using the same posterior samples; it does not certify posterior invariance because the headline IFT posterior is non-converged and the sampler was not rerun on each grid.

## Final State (Codex handoff, 2026-06-19)

- One-command replay: `bash run_all.sh`.
- Checker: `OVERALL YELLOW green=19 yellow=5 red=0`.
- Generated verdict: `HONEST_NEGATIVE` from `out/scorecard.json`.
- Main reason: IFT did not satisfy the convergence gate on any of the 25 headline splits (`converged_frac=0.00`; worst R-hat 78.0; min ESS 2.02; beta included).
- Deck: `slides/ift_real_validation_honest_negative.pptx`, 9 slides, rendered previews plus contact sheet under `slides/preview/`.
- Durable project notes were not edited; proposed project-log wording is in `packet.md`.

## Re-grounding Evidence Read

- `AGENTS.md`: status standard, NUTS/HMC and convergence gates, plot/deck gates, detached compute rule, and continuity rules.
- This runner prompt: `runner_prompt_lead.md`, plus the user-provided Codex-specific workspace suffix.
- `notes/memory.md` CURRENT STATE: Card A is the StatFEM real-validation baseline; Card B/PIFT and the consistency toy are separate read-only siblings.
- StatFEM baseline: `artifacts/reports/statfem_real_validation_20260617/packet.md`, especially method summary, verdict, whole-FRF arms, held-out QOI, and limitations.
- StatFEM held-out QOI summary: `phase2_heldout_sensor_qoi_summary.md`.
- IFT reference build: `artifacts/reports/statfem_consistency_toy_20260616/code/nuts_marg.py`, packet method/verdict on `M-ift`, and local PIFT/IFT reference notes.
- Primary references checked from arXiv: Hao & Bilionis, arXiv:2306.02150; Alberts & Bilionis, arXiv:2301.07609.

## Pre-committed Verdict Rule

The checker must generate exactly one of:

- WIN: IFT converges including `beta`, and beats L5 on headline proper scores at equal-or-better calibration.
- ROBUSTNESS-WIN: IFT does not beat L5, but avoids the M2 whole-FRF failure by converging and widening gracefully, with low `beta` documenting reduced physics trust.
- TIE: IFT and L5 are within split-to-split spread on headline proper scores and calibration.
- HONEST NEGATIVE: IFT also hits the coarse-FEM wall through non-convergence, collapsed `beta`, or no useful QOI improvement over L5 plus discrepancy.

No "IFT wins" claim may be written outside this generated verdict.

## Stop Points

Do not self-apply edits to durable project notes (`notes/runs.md`, `notes/memory.md`) or `docs/report/project_log.md`. This run may propose those rows after checker output exists.
