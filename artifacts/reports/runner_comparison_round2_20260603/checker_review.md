# Round-2 Checker Review (Opus 4.8) — 2026-06-03

Role: CHECKER. I report only what I could PASS, FAIL, or NOT CHECK, with quoted evidence. I do
not infer success from plots. Verified bar used for the convergence read (from the task card /
CLAUDE.md): flag any variable with **R-hat >= 1.01**, **bulk or tail ESS < 100 x chains (= 400 for
4 chains)**, or **any divergence**; default acceptance R-hat <= 1.05 (prefer <= 1.01), divergence
fraction < 2%, >= 4 chains, non-centered parameterization.

## Environment used for replay
- Built `.venv_nuts` per Opus `commands.md` (system Python 3.9.6 had no sampler). Verified:
  `numpyro 0.15.3 | jax 0.4.30 | arviz 0.17.1 | scipy 1.10.1`.
- All committed report folders were backed up before any replay and **restored byte-for-byte
  afterward**; `git status` shows no modified tracked files after the review.

## Immutable checker integrity — PASS
`shasum -a 256 -c harness/checkers/manifest.sha256` returned, both at the start and after every
replay:
```
harness/checkers/verify_artifacts.py: OK
harness/checkers/check_canary.py: OK
tests/test_posterior_recovery.py: OK
tests/test_mdof_transfer.py: OK
```
No immutable checker file was modified during the review.

---

## Consolidated summary

| Item | Opus 4.8 | Codex GPT-5.5 | Cursor Composer 2.5 |
|---|---|---|---|
| Replayable from source in master? | **YES** (exact) | **YES** (headline exact) | **NO — source scripts lost** |
| Sampler | NUTS (NumPyro) | NumPyro NUTS | NUTS (numpyro) |
| Chains | 4 | 4 | 4 |
| Headline fit draws | 8000 (1500w×2000×4) | 3600 (900w×900×4) | 4000 (1000w×1000×4) |
| Non-centered hier. latents | yes (`z_dome`,`z_tray`) | yes (`*_raw`) | yes (`*_raw`) |
| Divergences (headline) | 0 | 0 | 0 (full & peak) |
| Max R-hat (all vars, headline) | 1.00248 (`z_tray[2]`) | 1.00709 (`flight_tray_force_raw`) | 1.00282 (`sigma_sensor_db`) |
| Min bulk ESS (headline) | 2392.9 (`sigma_build_dome`) | 1080.1 (`sigma_build_db`) | 901.5 (`dome_build_raw`) |
| Min tail ESS (headline) | 3173.6 (`z_tray[0]`) | 1199.8 (`sigma_build_db`) | 945.6 (`tray_build_raw`) |
| Headline rests on converged chains? | YES | YES (early GIF frames NOT — see below) | YES |
| Runtime active <= elapsed | 1268.43 <= 2900.0 ✓ | 293.864 <= 293.877 ✓ | 223.218 <= 223.604 ✓ |
| Self-checker | 36/36 pass (reproduced) | status "pass" (reproduced) | status "pass" (read only) |

All three meet the verified convergence bar on their HEADLINE all-flight fit (R-hat < 1.01, ESS >
400, 0 divergences, 4 chains, non-centered). The one substantive convergence caveat is Codex's
early GIF-prefix frames (below). Cross-runner the tray 3·GRMS structural posterior agrees closely
(Codex 99% [1.0056, 1.0608], Cursor 99% [1.0041, 1.0600]).

---

## Opus 4.8 — PASS (fully reproduced)

**Replay.** Ran `R2_SMOKE=1 .venv_nuts/bin/python scripts/runner_claude_opus48_round2.py` (smoke,
intentionally non-converged: "CONVERGED: False ... 1.0176 (log_k1_ratio)"), then the full seeded
run `.venv_nuts/bin/python scripts/runner_claude_opus48_round2.py`. Console:
```
CONVERGED: True worst_rhat {'value': 1.002475887598128, 'variable': 'z_tray[2]'}
min_ess_bulk {'value': 2392.913790582128, 'variable': 'sigma_build_dome'}
min_ess_tail {'value': 3173.6429663045114, 'variable': 'z_tray[0]'} div 0 fit_s 5.1
```
`diff` of replayed vs committed `nuts_diagnostics.json` differs ONLY in `fit_runtime_s`
(5.07 vs committed 5.70); `interface_psd_bands.json` and `resolution_metrics.json` are
byte-IDENTICAL. This is a deterministic, exact reproduction.

**Diagnostics quoted (`nuts_diagnostics.json`).** `"sampler": "NUTS (NumPyro)"`, `"n_chains": 4`,
`"total_post_warmup_draws": 8000`, `"target_accept_prob": 0.99`, `"non_centered": true`,
`"divergences": 0`, `"divergence_fraction": 0.0`,
`"worst_rank_split_rhat": {"value": 1.002475887598128, "variable": "z_tray[2]"}`,
`"min_ess_bulk": {"value": 2392.913790582128, "variable": "sigma_build_dome"}`,
`"min_ess_tail": {"value": 3173.6429663045114, "variable": "z_tray[0]"}`,
`"converged": true`, `"nuts_active": true`, `"n_monitored_scalar_quantities": 29`,
`"raw_latents_included": true`. Per-variable table includes `z_dome[0..10]`, `z_tray[0..10]`
(raw non-centered latents).

**Convergence read vs bar.** No variable flagged: max R-hat 1.00248 < 1.01; min bulk 2392.9 and
min tail 3173.6 both >= 400; 0 divergences; 4 chains; non-centered. **Headline per-flight
interface-PSD bands rest on converged chains.**

**Runtime (`runtime.json`) — PASS.** `"active_runtime_s": 1268.43`,
`"elapsed_wallclock_s": 2900.0` (active <= elapsed). Discarded-run accounting is explicit:
`components_s.discarded_first_full_run_s = 467.94` is INCLUDED in active, and the note documents
"one discarded first full run". `reported_fit_only_s = 5.7`.

**Self-checker.** Re-ran `scripts/check_round2_artifacts.py`: "checks: 36/36 pass;
all_pass=True" (matches committed `checks.json`: `n_checks 36 / n_pass 36 / n_fail 0`).

**Tray 3·GRMS (NOT CHECKED as a credible interval).** Opus's JSON exposes tray 3·GRMS only as
grid point-estimates in `resolution_metrics.json` (`tray_3grms_coarse_g` 1.02909 / `_refined_g`
1.02706 / `_reference_g` 1.02684) — NOT a 95%/99% credible interval. The per-flight tray 3·GRMS
sequence and the 43.9 g (vibe) / 28.3 g (smoothline) references are figure-only
(`figures/flight_qoi_vs_vibe_reference.png`). The 95%/99% bands that DO exist are the per-flight
interface-response PSD bands behind the GIF (`interface_psd_bands.json`, 11 records; 10/11 flights
`frac_freqs_99hi_exceeds_spec = 0.0`, flight 3 = 0.0118).

---

## Codex GPT-5.5 — PASS on headline; documented caveat on early GIF frames + provenance

**Replay.** Ran `.venv_nuts/bin/python artifacts/reports/runner_codex_gpt55_round2_20260602/run_round2.py`.
Final fit console: `[diag] full: rhat=1.0071, bulk=1080.1, tail=1199.8, div=0`; end JSON
`"convergence_pass": true`. The **full all-flight diagnostics block reproduced byte-IDENTICAL**
except `elapsed_seconds` (timing). Replay self-checker printed `"checks_status": "pass"`.

Early GIF prefixes were NOT bit-reproducible: committed `cumulative_1` = `div 4, rhat 1.0098,
bulk 551.9`; my replay = `div 2, rhat 1.0049, bulk 613.5`; `cumulative_4` differs only at the 6th
decimal (1.0048024 vs 1.0048045). Prefixes 2 (`div 4`) and 3 (`div 1`) matched. This is minor
early-frame sampler nondeterminism (Codex installed unpinned numpyro/scipy); it does not affect the
headline. Manifest re-verified OK after replay.

**Diagnostics quoted (`nuts_diagnostics.json` → `full` = `cumulative_flights_11`).**
`"sampler_attempted": "NumPyro NUTS"`, `"nuts_sampler_ran": true`, `"num_chains": 4`,
`"post_warmup_draws_total": 3600`, `"max_rank_normalized_rhat": 1.0070877959908062`
(`flight_tray_force_raw`), `"min_bulk_ess": 1080.1242554160233` (`sigma_build_db`),
`"min_tail_ess": 1199.804945010423` (`sigma_build_db`), `"divergences_total": 0`,
`"divergence_fraction": 0.0`, `"convergence_pass": true`, `"variables_checked_count": 22`
(includes `dome_build_raw`, `tray_build_raw`, `flight_tray_force_raw`, `flight_iface_force_raw`,
`sigma_build_*`, `u_k1/u_k2/u_z1/u_z2`).

**Convergence read vs bar.**
- HEADLINE (cumulative_11): no flag — R-hat 1.00709 < 1.01, ESS 1080/1200 >= 400, 0 div. PASS.
- EARLY GIF FRAMES flagged: `cumulative_1` `"convergence_pass": false`, `divergences_total: 4`,
  R-hat 1.0097836 (`tray_build_raw`), min bulk 551.9; `cumulative_2` `div 4`; `cumulative_3`
  `div 1`. Codex's own `checks.json` warning states: "Cumulative GIF prefix fits 1-3 had nonzero
  divergences; final all-flight NUTS fit passed strict convergence." **The early frames of the
  evolution GIF therefore rest on chains with divergences / R-hat at the 1.01 boundary; the
  reported FINAL interval rests on converged chains.**

**Tray 3·GRMS intervals (`results.json` → `q_tray_struct_meanforce`).** median 1.0315305,
95% [q025 1.0113563, q975 1.0530865], 99% [q005 1.0056079, q995 1.0607529].
(`iface` 95% [1.3658835, 1.3917932], 99% [1.3618664, 1.3963687].) GIF `summaries` report
`q995_exceeds_spec_any_frequency: false` for all 11 frames.

**Runtime (`runtime.json`) — PASS.** `"active_runtime_s": 293.864458042`,
`"elapsed_wallclock_s": 293.876639417` (active <= elapsed; very tight — single in-master process,
no human-wait). No discarded runs declared.

**Provenance caveat (NOTED, not a pass/fail of the numbers).** `RAN_IN_MASTER_NOTE.md` states this
round-2 run executed in the MASTER repo, not its isolated copy, and "did not honor the round-2
prompt's 'assert cwd / refuse to run in master' instruction." It also notes Codex had reset round-1
records and rewritten timing in `runner_claude_opus48_20260602/nuts_diagnostics.json`, which the
lead REVERTED. Replay/runtime cross-comparisons should carry this caveat.

---

## Cursor Composer 2.5 — NOT REPLAYABLE; JSON/figures verified + independently recomputed

**Replay — NOT CHECKED (cannot).** `commands.md` points at
`bash scripts/run_runner_cursor_composer25_round2.sh`, which **does not exist**; there are no
`.py`/`.sh` source files in the report folder and no `*cursor*` scripts under `scripts/`. Confirms
the README statement that Cursor's round-1 AND round-2 source scripts were lost in cleanup. **Cursor
cannot be re-run by the checker.** This is a traceability gap, not evidence of cheating.

**Independent cross-check of committed draws (substitute for replay).** I loaded the committed
`posterior_samples.npz` (18 arrays; scalars `(4000,)` and build latents `dome_build*`/`tray_build*`
`(4000, 11)`; 4000 = 4 chains × 1000) and recomputed diagnostics with arviz under a chain-major
reshape over all 58 scalar components:
```
worst R-hat  = 1.00282 (full_sigma_sensor_db)
min bulk ESS = 901.5  (full_dome_build_raw[0])
min tail ESS = 945.6  (full_tray_build_raw[0])
```
These **match the committed `nuts_diagnostics.json`** (`"max_r_hat": 1.0028201622552135`,
`"min_ess_bulk": 901.4619299057999` dome_build_raw, `"min_ess_tail": 945.6197875376464`
tray_build_raw), which supports that the committed diagnostics are genuine and consistent with the
saved samples.

**Diagnostics quoted (`nuts_diagnostics.json`).** full: `"sampler": "NUTS (numpyro)"`,
`"num_chains": 4`, `"divergences_total": 0`, `"max_r_hat": 1.0028201622552135`,
`"min_ess_bulk": 901.4619299057999`, `"min_ess_tail": 945.6197875376464`,
`"converged_all_variables": true`. peak: `"max_r_hat": 1.0027049644228427`,
`"min_ess_bulk": 1471.09`, `"min_ess_tail": 1299.22`, `"divergences_total": 0`.

**Convergence read vs bar.** No variable flagged: max R-hat 1.00282 < 1.01; min bulk 901.5,
min tail 945.6 >= 400; 0 divergences (full and peak); 4 chains; non-centered (`*_raw`).
**Headline intervals rest on converged chains.**
CAVEATS: (1) the `param_table` lists vector latents (`dome_build_raw`, `tray_build_raw`) as single
aggregated entries rather than per-component, so per-component coverage is not transparent in the
committed file — my recompute fills that gap and the worst component still passes. (2) Cursor's
saved set has NO per-flight forcing latents (it fixes `fixed_flight_to_flight_qoi_log_sigma`:
tray 0.19690, iface 0.14949), so "all variables" is narrower than Codex's; this is a modeling
choice, not a failure.

**Tray 3·GRMS intervals (`results.json`).** `tray_3grms_structural_posterior`: median 1.0315226,
95% [q025 1.0114931, q975 1.0523621], 99% [q005 1.0041365, q995 1.0599659].
`tray_3grms_future_flight_predictive` (wider, includes build/forcing scatter): median 1.0335798,
99% [q005 0.4897775, q995 2.2315045]. `iface_3grms_structural_posterior` 99% [1.3612344,
1.3958664].

**Runtime (`runtime.json`) — PASS with caveat.** `"active_runtime_s": 223.218`,
`"elapsed_wallclock_s": 223.604` (active <= elapsed). CAVEAT: the note states active is the "Final
artifact-completion replay (skipped 11 sequential NUTS frames because GIF already existed)"; the
first full pass including the 11 sequential MCMC fits was ~783 s wall and is NOT included in
`active_runtime_s`. So Cursor's `active_runtime_s` UNDERSTATES the true compute and is not directly
comparable to Opus/Codex active times.

**Self-checker — read only (cannot re-run).** Committed `checks.json` `"status": "pass"` (28
checks incl. immutable hashes, files, figures, `full_is_nuts`, `has_convergence_gate`,
`reports_all_param_table`).

---

## What did NOT reproduce / NOT checked (explicit)
- **Cursor: entire run is NOT replayable** (source scripts lost). Verified only by reading
  committed JSON/figures plus an arviz recompute of the saved draws.
- **Codex early GIF prefixes (cumulative_1..3) did not bit-reproduce** and carry divergences /
  R-hat near the 1.01 line; headline full fit reproduced exactly. Codex ran in MASTER, not isolated.
- **Opus tray 3·GRMS is not exposed as a credible interval in JSON** (figure + grid point-estimates
  only); the JSON 95%/99% bands are the per-flight interface-PSD bands.
- Cursor recompute assumes chain-major ordering of the flattened draws; the exact match to the
  committed numbers supports that assumption but it is an assumption.

## Bottom line
- Immutable checkers: **PASS** (unchanged throughout).
- Opus: **PASS** — exactly reproduced, converged over all 29 monitored quantities incl. raw latents,
  honest discarded-run accounting.
- Codex: **PASS on the reported final interval** (headline reproduced exactly, converged); GIF early
  frames are diverged/borderline and are labeled as such by Codex; in-master provenance caveat.
- Cursor: **NOT REPLAYABLE**; committed diagnostics are internally consistent and pass the bar per an
  independent recompute, with the runtime-understatement and aggregated-latent-reporting caveats.
