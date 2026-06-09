# files_changed.md — SEARCH RUNNER (modeling-freedom experiment)

All paths under `runner_opus/`. The runner wrote ONLY here; it did not modify `notes/`, the
vault, the frozen contract/splits, or any other run. Read-only ShockSat inputs were verified
unchanged (SHA256 match the manifest pins) before and after.

## Code (`src/`)
- `forward.py`     — jax differentiable 12-DOF fixed-free chain: K assembly, modes, receptance/QOI.
- `data.py`        — load + mode-shape sign-alignment of synthetic train/dev; resolution coarsen.
- `model.py`       — numpyro config-driven model (disc: none/freq/freqshape/probe; like full/freq;
                     centered/non-centered); vectorized dev-LPD + WAIC prediction.
- `fit.py`         — NUTS runner; R-hat/ESS/divergence over ALL sampled vars; gate check; QOI.
- `search.py`      — orchestrator: MAIN + ablations + probe; results_table.csv; reusable-holdout;
                     finalist selection; finalists.json; saves finalist draws + convergence JSON.
- `shocksat.py`    — Nastran .pch parser (test modes + DMIG KAAX/MAAX); modal MAC + freq error;
                     leave-one-mode-out self-estimate; writes shocksat_predictions.json + table.
- `figures.py`     — figures 01-07.

## Deliverables (workspace root)
- `results_table.csv`            — every config (N=31): form, disc, priors, dev, R-hat/ESS/div, etc.
- `finalists.json`               — <=3 finalists (schema for vault scorer). [gitignored by lead design]
- `finalists.sha256`             — LOCK: sha256(finalists.json + shocksat_predictions.json). COMMITTED.
- `shocksat_predictions.json`    — committed modal correlation + OOD pyro QOI (before pyro redownload).
- `shocksat_mode_table.csv`      — per-mode MAC + frequency error.
- `packet.md`                    — human-review writeup.
- `priority_deliverables.md`     — priority asks -> interpretation -> artifact map.
- `decisions_log.md`             — append-only decisions (survives compaction).
- `run_all.sh`                   — one-command replay (asserts CWD, verifies manifest, locks hash).
- `runtime.json`, `runtime_search.json` — active vs wallclock runtime.

## Subdirs
- `ablations/`      — ablation_results.csv + README (also rows in results_table, stage ABL_*).
- `overfit_probe/`  — probe_curve.csv (naive vs reusable-holdout dev-chasing).
- `diagnostics/`    — per-finalist *_convergence.json (R-hat/ESS over all vars) + *_draws.npz.
- `figures/`        — 01_observed_data, 02_overfit_picture, 03_probe_curve, 04_ablations,
                      05_convergence_traces, 06_shocksat_correlation, 07_finalist_modes.

## NOT done by runner (by rule)
- Did not access/score the vault (truth on Google Drive); did not read the truth generator,
  parked packets, ../notes, or score_vault.py.
- Did not declare a best model; the dev-vs-vault gap is computed by the human after re-download.
