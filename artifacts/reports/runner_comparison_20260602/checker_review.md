# Round-1 Checker Review — Sequential Vibe/Modal/Flight Runners

Role: CHECKER subagent (model: Opus 4.8). Per `.claude/agents/checker.md`, this report records
only what passed, failed, or was not checked, with quoted evidence. Success is **not** inferred from
plots. A convergence read is reported separately and does not silently pass.

- Date run: 2026-06-02
- Master repo root: `/Users/avoss/Downloads/bayesX/Agentic BayesX`
- Immutable manifest: `harness/checkers/manifest.sha256` (4 files)

## TL;DR per runner

| Runner | Commands reproduced (exit 0) | Immutable hashes | Sampler claim | Divergences | Max R-hat (all vars) | Min ESS (all vars) | Chains converged? |
|---|---|---|---|---|---|---|---|
| Opus 4.8 | YES | OK | NUTS (numpyro) — **active** | 0 / 0 | 1.0024 / 1.0019 | 942 / 1495 | **YES** |
| Codex GPT-5.5 | YES | OK | custom PyTorch fixed-trajectory HMC — **NUTS NOT active** (self-declared) | 3 / 0 | 2.67 / 4.57 | ~6.6 / ~6.3 (approx) | **NO** |
| Cursor Composer 2.5 | YES | OK | NumPyro NUTS — claims active | 0 / 0 | 1.83 / 1.93 | 3.0 / 3.0 (ess_bulk) | **NO** |

R-hat / ESS pairs are reported as `full / peak`. See per-runner sections for quoted fields.

---

## Runner 1 — Claude Opus 4.8

- Workspace: `.` (master). Output: `artifacts/reports/runner_claude_opus48_20260602/`
- Env: self-created `.venv_nuts` (numpyro 0.19.0, jax 0.4.30, numpy 1.26.4, matplotlib 3.9.4) — confirmed by checker.

### Commands re-run (from its `commands.md`)
| Command | Exit |
|---|---|
| `bash scripts/run_runner_claude_opus48.sh` (recreates venv, runs NUTS full+peak, runner checker, hash verify) | **0** |

Console (reproduced): `full: divergences=0 max_rhat=1.002 min_ess=942`; `peak: divergences=0 max_rhat=1.002 min_ess=1495`; runner artifact checker `{"status":"pass","n_checks":48,"n_fail":0}`.

### Immutable hash check
`shasum -a 256 -c harness/checkers/manifest.sha256` → all 4 OK, exit 0 (master, re-run independently and via the script).

### JSON reports — quoted fields
- `nuts_diagnostics.json` → `"sampler": "NUTS (numpyro)"`, `num_chains: 4`, warmup 1000 / samples 1000 (4000 draws).
  - full: `divergences_total: 0`, `max_r_hat: 1.0023681399347368`, `min_n_eff: 941.796` (both at `sigma_build_ln`).
  - peak: `divergences_total: 0`, `max_r_hat: 1.001850105076448`, `min_n_eff: 1495.318` (`sigma_build_ln`).
- `checks.json` → `"status": "pass"` (48 checks, includes `full:is_nuts`/`peak:is_nuts` = "NUTS (numpyro)", `rhat_ok`, `ess_ok`, `divergence_fraction_ok`, dome/tray recovery within CI).
- `results.json` tray 3*GRMS intervals (g):
  - **structural posterior, full**: 95% `[1.0115, 1.0524]`, 99% `[1.0041, 1.0600]`
  - **future-flight predictive, full**: 95% `[0.5923, 1.8145]`, 99% `[0.4898, 2.2315]`
  - structural posterior, peak: 95% `[0.8805, 1.1165]`; predictive peak 95% `[0.5525, 1.7763]`
  - NOTE: Opus reports **two** tray 3*GRMS quantities (structural-only vs future-flight predictive). The predictive interval is the decision-relevant one and is much wider than structural.
- `assumptions_ledger.json` present; fixed flight-to-flight QOI log-sigma `tray=0.1969, iface=0.1495` (also echoed in results.json).

### Convergence read
All 10 reported variables in both models have R-hat < 1.05 and n_eff ≥ 200 (min 942). **Headline intervals rest on converged chains.** `nuts_active` true and the NUTS claim is supported by code + replay + diagnostics + checker output (satisfies the NUTS/HMC rule).

### Not checked / residual
- n_eff here is NumPyro's `numpyro.diagnostics` effective sample size, not ArviZ bulk/tail ESS (arviz absent; documented in `commands.md`). R-hat is NumPyro's, not ArviZ split-R-hat. Adequate but not identical to ArviZ.

---

## Runner 2 — Codex GPT-5.5

- Workspace: `.` (master). Output: `artifacts/reports/runner_codex_gpt55_20260602/`
- Env: system Python 3.9.6; **numpyro/JAX/PyMC/ArviZ absent, no install attempted** (per its `commands.md`).

### Commands re-run (from its `commands.md`)
| Command | Exit |
|---|---|
| `PYTHONPATH=. python3 -m py_compile scripts/run_codex_gpt55_full_experiment.py tests/test_runner_codex_gpt55_full_experiment.py` | **0** |
| `PYTHONPATH=. python3 scripts/run_codex_gpt55_full_experiment.py` | **0** |
| `PYTHONPATH=. python3 tests/test_runner_codex_gpt55_full_experiment.py` | **0** |
| `shasum -a 256 -c harness/checkers/manifest.sha256` | **0** |

Reproduced console: `self_check_pass: true`, `full_divergences: 3`, `peak_divergences: 0`, `full_tray_3grms_95: [1.1272, 3.0470]`, `peak_tray_3grms_95: [0.9295, 2.4184]` — matches the recorded values exactly.

### Immutable hash check
All 4 files OK, exit 0.

### JSON reports — quoted fields
- `nuts_diagnostics.json` → `backend_note`: *"numpyro is not installed … The run uses a labeled custom PyTorch-autograd fixed-trajectory HMC backend; NUTS is not active."* Both models: `"nuts_active": false`, `"hmc_active": true`, `"sampler": "custom PyTorch fixed-trajectory HMC"`, fixed 10 leapfrog steps, 2 chains, 100 warmup / 160 draws.
  - full: `divergences: 3`. R-hat (max) `log_build_sigma_ln_psd = 2.674`; also `log_zeta2 = 1.815`, `flight_force_offset_ln_psd = 1.583`. `ess_bulk_approx` min `log_zeta1 = 6.64`.
  - peak_feature: `divergences: 0`. R-hat (max) `flight_force_offset_ln_psd = 4.575`; `log_zeta2 = 1.257`. `ess_bulk_approx` min `log_zeta1 = 6.28`.
- `checks.json` / `runner_checker_report.json` → `pass: true`, `failures: []`. (The runner checker checks file existence, self-check, image legibility, and hashes — it does **not** gate on R-hat/ESS convergence.)
- `posterior_results.json` tray 3*GRMS (g):
  - full posterior_summary: 95% `[1.1272, 3.0470]`, 99% `[0.9749, 3.7277]`
  - peak_feature posterior_summary: 95% `[0.9295, 2.4184]`, 99% `[0.8413, 2.5875]`
  - `qoi_interval_contract.tray_3rms_equals_3grms: true`
- `assumptions_ledger.json` present.

### Convergence read — FLAG
- full: 4 of 7 variables R-hat ≥ 1.05 (max 2.67); 6 of 7 ess_bulk_approx < 200 (approximate, local autocorr estimate). 3 divergences.
- peak: 5 of 7 variables R-hat ≥ 1.05 (max 4.57); 7 of 7 ess_bulk_approx < 200.
- **The headline tray 3*GRMS intervals do NOT rest on converged chains.** R-hat up to 2.67/4.57 and single-digit ESS indicate the chains have not mixed; the reported QOI intervals are not trustworthy as posterior summaries.
- Codex itself flags ESS/R-hat as local approximations (not ArviZ) and tree-depth as N/A.

### Sampler-rule status
Per AGENTS.md / CLAUDE.md NUTS rule: Codex **correctly and explicitly labels NUTS as not active** and names the actual sampler (custom fixed-trajectory HMC). It does not claim NUTS. The labeling requirement is satisfied; the convergence quality is not.

---

## Runner 3 — Cursor Composer 2.5

- Workspace: `../Agentic_BayesX_runner_cursor_composer25`. Output: `.../runner_cursor_composer25_20260602/`
- Env: self-created `.venv` (pinned jax 0.4.23 / jaxlib 0.4.23 / numpyro 0.13.2 / scipy 1.11.4 / arviz / pillow per its `commands.md`).

### Commands re-run (from its `commands.md`)
| Command | Exit |
|---|---|
| `bash scripts/run_sequential_vibe_modal_flight_inference.sh` (activates `.venv`, runs NUTS inference, runner checker, hash verify) | **0** |

Reproduced: `Inference complete. nuts_active= True`; hash lines all OK. (NumPyro warning: "not enough devices to run parallel chains: expected 2 but got 1. Chains will be drawn sequentially" — chains still produced.)

### Immutable hash check
All 4 files OK (in regenerated `checks.json.shasum_stdout` and in the replay log), exit 0.

### JSON reports — quoted fields
- `nuts_diagnostics.json` → `"nuts_active": true`, sampler NumPyro NUTS, 2 chains, `max_tree_depth: 10`.
  - full_curve: `divergences: 0`. Per-variable R-hat up to **1.83** (`dome_raw[0]`, `sigma_build_ln`, `sigma_sensor_ln`, `tray_raw[0]`, all `x_struct[*]`); ess_bulk as low as **3.0** for those same variables.
  - peak_feature: `divergences: 0`. R-hat up to **1.93** (`tray_raw[1]`); ess_bulk down to **3.0**; many feature/tray vars 1.1–1.6.
- `checks.json` → `pass: true`, `failures: []`, `shasum_ok: true`, `nuts_active: true`. (This checker gates on file existence + hashes + nuts_active flag; it does **not** gate on R-hat/ESS.)
- `summary.json` → `nuts_active: true`, `sampler: "NumPyro NUTS"`, flight-to-flight sigma 3 dB PSD known/not-learned, Matérn-3/2 forcing (ell_log_freq 0.08), learned `sigma_build_db median 3.906`, `sigma_sensor_db median 3.102`.
- `posterior_predictive_summary.json` tray 3*GRMS (g): 95% `[0.3540, 1.5666]`, 99% `[0.3157, 1.7913]`, median 0.678. interface 3*GRMS 95% `[1.0888, 1.8919]`, 99% `[1.0310, 2.2706]`.
- `packet.md` headline: "Tray 3*GRMS 95% CI: [0.354, 1.567] g"; "QOI 95% width ratio peak/full: 0.5191".
- `assumptions_ledger.json` present.

### Convergence read — FLAG
- full_curve: 16 of 28 variables R-hat ≥ 1.05 (max 1.83); 23 of 28 ess_bulk < 200 (min 3.0).
- peak_feature: 30 of 36 variables R-hat ≥ 1.05 (max 1.93); **36 of 36** ess_bulk < 200 (min 3.0).
- **The headline tray 3*GRMS intervals do NOT rest on converged chains.** Despite `nuts_active: true` and 0 divergences, R-hat ≈ 1.8–1.9 and ess_bulk = 3 mean the chains are effectively stuck/unmixed; the QOI CI is not a reliable posterior summary. Zero divergences here is misleading (it does not imply mixing).

### Sampler-rule status
NUTS is genuinely the engine (NumPyro NUTS, arviz-style ess_bulk/ess_tail/r_hat reported), so the NUTS claim is technically supported by code+replay+diagnostics. **However**, the diagnostics themselves indicate non-convergence, so "NUTS active" should not be read as "NUTS converged."

---

## Cross-runner observations (report only)

1. **Headline tray 3*GRMS intervals disagree materially** and partly because the quantity is not defined identically across runners:
   - Opus structural-posterior 95% `[1.01, 1.05]` vs Opus future-flight predictive 95% `[0.59, 1.81]`.
   - Codex full 95% `[1.13, 3.05]`.
   - Cursor 95% `[0.35, 1.57]`.
   These are not directly comparable until numerator/denominator/excitation/units and structural-vs-predictive scope are pinned per a quantity contract. This is a quantity-contract gap, not a checker pass/fail.
2. **Only Opus presents converged chains.** Codex and Cursor both produce passing artifact checkers while carrying R-hat ≥ 1.8 and ESS in the single digits. The runner checkers do not encode a convergence gate — a harness gap worth flagging to the human (do not change checkers during the trial).
3. **All three** pass the immutable hash check; no immutable checker file was modified.

## What I could not reproduce / not checked
- Could not run ArviZ-grade diagnostics uniformly: Opus's venv has no arviz (uses NumPyro diagnostics); Codex has no JAX/NumPyro at all (uses local autocorr ESS / split-free R-hat, self-labeled approximate); only Cursor's stack includes arviz. ESS/R-hat definitions therefore differ across runners and are not strictly comparable.
- I did not independently re-derive the 3*GRMS QOI from raw posterior samples; values are quoted from each runner's own JSON (and the regenerated runs matched the recorded console for Opus and Codex).
- Figure legibility was not re-rendered by me; I quoted Codex's `checks.json` image-legibility block as-is.
- Convergence "pass/fail" is reported, not enforced: per the checker role I flag R-hat ≥ 1.05 / ESS < 200 but do not change runner verdicts.
