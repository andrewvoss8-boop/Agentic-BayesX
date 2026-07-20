# Files changed — shocksat_tray_coupled_qoi_20260610 (single session, 2026-06-10)

All files below were CREATED this session by the lead-as-runner inside this
new workspace. **No file outside this workspace was modified except** the
three shared notes listed at the bottom. **No upstream input was modified**
(SHA-pinned in `inputs_sha256_start.json`, re-verified by `check.py`); the
predecessor and FIM workspaces were read-only sources.

## Created — planning / governance
- `priority_deliverables.md`, `question_framing.md`, `quantity_contracts.md`
  (C1–C9 + convention-collision table), `assumptions_ledger.md` (A1–A20),
  `decisions_log.md` (D1–D9)

## Created — code (`code/`)
- `models.py` — tray base-point condensation build (adapted from the FIM
  workspace's fim_model.py, foot springs re-routed to the condensation
  point), exact Woodbury damped apparent mass, ShockSat interface ROM rows
  + SI conversion, LM-FBS coupling
- `methods.py` — input synthesis, Smallwood SRS, modal-SRS force, Miles
- `verify.py` — gates V1–V9
- `run_qoi.py` — nominal/srscache/mc/sweeps stages (resumable, checkpointed)
- `identifiability.py` — coupled-mode SE decomposition + finite perturbation
- `proxy_qoi.py` — response-limit proxy (D7)
- `make_figures.py` — 9 figures (tufte-linted; regenerated after visual QA:
  method-comparison caption/ticks, force-limiting switched to smooth
  transfers, apparent-mass z+x small multiples, identifiability ≤160 Hz)

## Created — outputs (`out/`, `figures/`, `logs/`)
- `out/verification.json` (15/15 green), `out/mount_node.json`,
  `out/srs_cache.npz`, `out/nominal_spectra.npz`, `out/nominal_transfers.npz`,
  `out/qoi_nominal.json`, `out/mc_checkpoint.npz`, `out/qoi_results.json`,
  `out/variance_decomposition.json`, `out/sweeps.json`,
  `out/mount_identifiability.json`, `out/response_limit_proxy.json`,
  `out/image_qa.json`
- `figures/fig_*.png` (9), `logs/*.log`

## Created — packet / bookkeeping
- `packet.md`, `check.py`, `run_all.sh`, `checker_report.json`,
  `inputs_sha256_start.json`, `runtime.json`, `manifest.json`,
  `session_start_epoch.txt`, this file

## Created — overnight VOI experiment (D10/D11, 2026-06-10 → 06-11)
- `code/build_coupled_rom.py` (O1), `code/make_truth.py` (O2),
  `code/run_nuts_mount.py` (O3, pinned .venv_nuts),
  `code/posterior_qoi.py` (O4), `code/diagnose_multimodality.py`
- `out/coupled_rom.npz`, `out/coupled_rom_report.json`,
  `out/survey_data.npz`, `out/truth_lock.json`, `out/pairing_coupled.json`,
  `out/nuts_mount_{base,remedy}_samples.npz`,
  `out/convergence_mount_{base,remedy}.json`, `out/mount_posterior.json`,
  `out/posterior_qoi_draws.npz`, `out/voi_results.json`,
  `out/multimodality_diagnosis.json`, `figures/fig_voi.png`,
  `logs/o1_rom.log` … `logs/o4_voi.log`
- Modified: `models.py` (apparent_mass_direct gains 6×6 Km option),
  `make_figures.py` (+fig_voi), `check.py` (+8 overnight gates),
  `run_all.sh` (stages 5–7), `packet.md` (§10), `quantity_contracts.md`
  (C10), `assumptions_ledger.md` (A21–A28), `decisions_log.md` (D10, D11)

## Created — program deck for collaborators (D12/D13, 2026-06-12)
- `code/make_deck_figs.py` (6 tufte deck figures), `code/make_gifs.py`
  (3 supplementary GIFs), `code/make_deck.py` (python-pptx builder)
- `slides/shocksat_program_deck.pptx` (14 slides, Girolami/Bilionis/Yunis),
  `slides/README.md` (talk track + scorecard),
  `slides/figs/deck_*.png` (arc, force_limiting, mount_dominance,
  identifiability, scorecard, method, graphical_model, voi),
  `slides/gifs/{force_limiting_sweep,mode_walk_qoi,multimodality}.gif`
- Modified: `check.py` (+4 deck gates), `decisions_log.md` (D12, D13)

## Modified OUTSIDE the workspace (durable, Andrew-approved + shared notes)
- `AGENTS.md` — Modal/Eigenproblem Identifiability Gate extended with the
  FIM-eigen / parameter-combination requirement for per-parameter claims (D12,
  Andrew "I agree, make the change")
- `docs/report/project_log.md` — §3 thread row, §5 deliverables, §7 harness
  evolution updated for the deck + harness change
- `notes/lessons-learned.md` — overnight under-identification BLOG entry

## Modified OUTSIDE the workspace (shared notes only)
- `notes/memory.md` — lead CURRENT STATE block (session start + end)
- `notes/todo.md` — task plan checklist (+ Andrew's mid-run D7 ask was added
  there by Andrew)
- `notes/runs.md` — run record appended at session end
