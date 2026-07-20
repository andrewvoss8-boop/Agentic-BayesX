# Card D — data-driven FEM remodeling of the high-error ShockSat regions

**Question:** can an autonomous agent contribute to FEM correlation by re-meshing/remodeling where the data says
the model is wrong (the 8 hard channels that miss the band on per-sensor amplitude)?

**Answer (headline):** QUALIFIED YES — the contribution is a rigorous, auditable diagnosis that re-meshing and
stiffness re-tuning are **not** the lever for this already-well-correlated model; the residual is damping +
near-field + frequency-misalignment, resolvable only by better test data. See
[`correlation_contribution.md`](correlation_contribution.md).

## Read in this order
1. [`correlation_contribution.md`](correlation_contribution.md) — the meta-deliverable / verdict.
2. [`region_diagnosis.md`](region_diagnosis.md) — Phase-1 diagnosis (mesh converged, topology complete, joints
   finite & non-identifiable; the three levers ruled out before editing).
3. [`out/before_after.json`](out/before_after.json) + [`figures/fig_before_after.png`](figures/fig_before_after.png)
   — the campaign of 10 correlated updates re-solved and re-correlated (shape-vs-frequency tradeoff, 0/10 clean).
4. [`decisions_log.md`](decisions_log.md) — D0–D7, every decision/finding/Andrew steer.
5. [`checker_report.json`](checker_report.json) — OVERALL GREEN 14/0/0.

## Reproduce
- `bash run_baseline.sh` — assemble + eigensolve the copied FEM (reproduces inherited modes to 3.6e-10).
- `bash run_campaign.sh` — the 10 correlated-update edits (resumable; ~5 min/solve, BLAS-pinned float64).
- `python3 code/remesh_dish.py && bash run_dish_refined.sh` — true local dish 2× mesh refinement.
- `python3 code/aggregate.py && python3 code/make_figure.py` — before/after table + figure.
- `python3 check.py` — checker.

## Honest scope
- Plain 9-group ShockSat only (no coupled tray); COPY-never-edit the inherited FEM (edits applied
  programmatically on the parsed model / per-PID blocks; inherited NASTRAN deck untouched).
- Card D correlation metric = eigen-MAC + frequency vs the 33-mode `.ash` survey. The per-sensor FRF-amplitude
  failure itself is the validation study's domain (`statfem_real_validation_20260617`), cited not re-derived.
- 7 of the 8 card channels are checker-confirmed consistent fails; ch92 (strut) labeled suspected.
- SURFACED to lead/Andrew (not self-applied): `docs/report/project_log.md` row; any "replace the inherited FEM"
  claim; any durable-rule/checker change.
