# Files changed — FIM identifiability analysis

All new; confined to `artifacts/reports/fim_identifiability_opus_20260609/`. No sibling
workspace or master-repo file was modified. Inputs in `inputs/` are read-only copies
(SHA256 in `inputs/INPUT_SHA256.txt`, re-verified by `check.py`).

## Code (saved .py, lintable/replayable)
- `code/fim_model.py` — parametric group-stiffness assembly + exact modal sensitivities.
- `code/run_fim.py` — FIM, eigendecomposition, QR subset, QOI projection, design sweeps, sensitivity.
- `code/profile_likelihood.py` — profile-likelihood confirmation (40-mode reduced basis).
- `code/make_figures.py` — 7 Tufte-disciplined figures (tufte_lint clean).
- `check.py` — 15 artifact-backed gates → `checker_report.json`.

## Artifacts
- `fim_results.json`, `arrays_fim.npz`, `profile_likelihood.json`, `checker_report.json`,
  `runtime.json`, `manifest.json`.
- `figures/fig1..fig7 *.png`.

## Docs
- `priority_deliverables.md`, `decisions_log.md`, `assumptions_ledger.md`,
  `quantity_contracts.md`, `packet.md`, `next_prompt.md`, `files_changed.md`, `run_all.sh`.

## Outside the workspace (lead continuity only)
- `notes/memory.md` CURRENT STATE block, `notes/todo.md`, `notes/runs.md` updated by the lead.
