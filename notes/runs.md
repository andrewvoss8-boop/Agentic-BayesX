# Runs

## Format
- Date:
- Trial:
- Command:
- Checker result:
- Key metrics:
- Lessons:

## 2026-06-02 Plain-English multi-agent scaffold
- Trial: create first scaffold where Claude Code is lead and Codex/Cursor can be manually launched as helpers.
  - Commands:
    - `python3 tests/test_multi_agent_scaffold.py`
    - `bash scripts/run_fresh_2dof_statfem_fbs.sh`
    - `python3 tests/test_fresh_2dof_rerun.py`
    - `shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Scaffold checker wrote `artifacts/tests/multi_agent_scaffold_report.json`; fresh 2DOF checker reported `pass = true`; immutable checker hashes all reported `OK`.
  - Key metrics: numeric assumptions = 30; Ch2/Ch3 relative L2 = 0.6739064407171255.
  - Artifacts: `docs/agents/how_to_run.md`, `docs/agents/claude_code_starter_prompt.md`, `.claude/agents/`, `.cursor/agents/`, `.cursor/rules/`, `docs/codex_prompts/multi_agent/`, and `artifacts/reports/multi_agent_first_loop_20260602/`.
  - Lessons: Git was initialized in this previously untracked folder. NUTS/HMC is now documented as the future default sampler, but the existing inference code remains prototype/legacy random-walk/random-scan Metropolis until a checked implementation replaces it.

## 2026-06-02 Sequential vibe/modal/flight research setup
- Trial: create setup packet for a staged rocket dome/tray workflow with smoothline vibe PSD, tray vibe test, dome-only modal test, coupled modal test, first flight, and ten later build/flight updates.
  - Commands:
    - `python3 -m py_compile scripts/sequential_vibe_modal_flight_setup.py tests/test_sequential_vibe_modal_flight_setup.py`
    - `bash scripts/run_sequential_vibe_modal_flight_setup.sh`
    - `shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. New checker wrote `artifacts/tests/sequential_vibe_modal_flight_setup_report.json`; immutable checker hashes all reported `OK`.
  - Key metrics: dome FEM peak response PSD = 0.1 g^2/Hz; smoothline input 3*GRMS = 28.2690 g; first-build tray vibe observed 3*GRMS = 43.9091 g; flight count = 11; later builds = 10; forcing covariance = Matérn-3/2 with log-frequency length scale 0.08; NUTS active = false.
  - Artifacts: `artifacts/reports/sequential_vibe_modal_flight_20260602/`, `scripts/sequential_vibe_modal_flight_setup.py`, `tests/test_sequential_vibe_modal_flight_setup.py`, and `docs/agents/claude_sequential_vibe_modal_flight_prompt.md`.
  - Lessons: the next Claude loop can start from a checked setup packet, but posterior updates still require a real NUTS/HMC implementation. The setup explicitly treats 3 dB flight-to-flight variability as fixed/known and build-to-build plus sensor-noise scales as future learned quantities.

## 2026-05-27
- Initialized run log template.
- Trial: canary harness gate
  - Command: `PYTHONPATH=. python3 harness/driver.py --config harness/configs/canary_trial.json`
  - Checker result: pass
  - Key metrics: canary rmse = 0.0, manifest mismatch = none
- Trial: posterior recovery test
  - Command: `PYTHONPATH=. python3 tests/test_posterior_recovery.py`
  - Checker result: pass
  - Key metrics: acceptance_rate = 0.0167, all tracked relative errors < 0.35
- Trial: MDOF reduced transfer test
  - Command: `PYTHONPATH=. python3 tests/test_mdof_transfer.py`
  - Checker result: pass
  - Key metrics: relative_l2_error = 0.0514

## 2026-05-27 Codex review + sampler fix
- Trial: baseline pipeline before sampler fix
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: posterior recovery acceptance_rate = 0.0167; MDOF relative_l2_error = 0.0514; canary manifest mismatches = none
  - Lessons: all-parameter random-walk MH passed the loose smoke test but had poor sampler movement.
- Trial: targeted posterior recovery after sampler fix
  - Command: `PYTHONPATH=. python3 tests/test_posterior_recovery.py`
  - Checker result: pass
  - Key metrics: acceptance_rate = 0.216; tracked relative errors all < 0.35
- Trial: final full pipeline after sampler fix
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; manifest mismatches before/after = none; posterior recovery acceptance_rate = 0.216; MDOF relative_l2_error = 0.0514; plot manifest lists 6 PNGs
  - Full MCMC artifact: acceptance_rate = 0.2009; post_burn_acceptance_rate = 0.1408; tracked relative errors: k1 = 0.0104, k2 = 0.0210, k12 = 0.1393, force_amp = 0.1163, force_fc = 0.0671, qoi_peak_tray_accel = 0.00303
  - Lessons: inspect both smoke-test metrics and the full inference artifact; the default run needed a smaller proposal scale than the test configuration.

## 2026-05-29 Aerospace vibration data search
- Trial: web search and source review for real aerospace vibration/modal/flight data
  - Command/source path: Browser/web search; documented results in `references/aerospace-vibration-data-candidates.md`
  - Checker result: not a computational checker trial
  - Key candidates: F-16 GVT benchmark from 4TU, Vibrationdata SR-19/Pegasus/RV acceleration time histories, NASA PIMS/SAMS ISS acceleration archives, BAE T1A Hawk datasets, TU Delft Diana 2 GVT, NASA CRM FEM/modal files
  - Lessons: best primary/secondary public fit is F-16 wing plus dummy payload/pylon interface; best tank/dome-like flight/static-fire signal is Vibrationdata SR-19 forward dome ignition, but it is single-channel acceleration rather than an FRF.

## 2026-05-29 Cursor skills connected to Codex
- Trial: install personal Cursor skills into Codex user skills
  - Command/source path: copied from `/Users/avoss/.cursor/skills/` to `/Users/avoss/.codex/skills/`
  - Checker result: copied folders match source by `diff -rq`; all five `SKILL.md` files have `name` and `description` frontmatter
  - Installed skills: `andrew-voss-voice`, `evergreen-knowledge-work`, `honest-technical-work`, `project-harness`, `stop-slop`
  - Excluded by design: Cursor internal helper skills under `/Users/avoss/.cursor/skills-cursor/` and ME539 `textbook-latex-editor`
  - Lessons: restart Codex before expecting newly copied skills to appear in the session skill inventory.

## 2026-05-29 Milestones 1-2: synthetic packet + channel fix
- Trial: full question-first synthetic StatFEM pipeline
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable manifest mismatches before/after = none; posterior recovery acceptance_rate = 0.216; MDOF relative_l2_error = 0.0514; channel 2/3 clean relative_l2 = 0.6877; review packet completeness pass = true
  - Artifacts: `artifacts/reports/synthetic_statfem_packet.md`, report figures under `artifacts/reports/figures/`, channel report at `artifacts/tests/channel_definitions_report.json`, review packet report at `artifacts/tests/review_packet_report.json`
  - Lessons: channel 2 is now primary-side `F1/a1`, channel 3 is tray-side `F2/a2`; BOED is explicitly framed as useful only after the human chooses the objective and experiment menu.
- Trial: fix review packet image rendering
  - Command: `PYTHONPATH=. python3 scripts/generate_review_packet.py && PYTHONPATH=. python3 tests/test_review_packet.py`
  - Checker result: pass
  - Key metrics: missing_files = none; missing_snippets = none; missing_embedded_images = none; manifest_ok = true
  - Lessons: report Markdown image links need absolute paths wrapped in angle brackets because the local project path contains a space.

## 2026-05-29 GP error exploration
- Trial: inspect and visualize current GP-over-frequency discrepancy model
  - Command: `PYTHONPATH=. python3 scripts/explore_gp_error.py`
  - Checker result: artifact generated; no formal pipeline checker added
  - Key metrics: discrepancy_scale = 0.03; discrepancy_corr_hz = 8.0 Hz; iid real/imag sigma = 0.02; covariance diagonal mean = 0.0009000001; near correlation reference = 0.6199; far correlation reference ~ 0
  - Artifacts: `artifacts/reports/gp_error_exploration/gp_error_exploration.md`, `gp_frequency_covariance.png`, `gp_error_samples.png`, `gp_error_components_ch2.png`, `gp_error_exploration.json`
  - Lessons: the project already uses an additive zero-mean squared-exponential GP over frequency, but the realized discrepancy is not stored separately from iid sensor noise in the main dataset.

## 2026-06-01 Report clarification: 2DOF vs MDOF
- Trial: clarify synthetic packet scope and add experimental workflow walkthrough
  - Command: `PYTHONPATH=. python3 scripts/generate_review_packet.py && PYTHONPATH=. python3 tests/test_review_packet.py`
  - Checker result: pass
  - Key metrics: missing_files = none; missing_snippets = none; missing_embedded_images = none; manifest_ok = true
  - Artifacts: updated `artifacts/reports/synthetic_statfem_packet.md`; added `artifacts/reports/figures/experimental_workflow.png`
  - Lessons: keep the 2DOF StatFEM packet separate from the MDOF transfer-function prototype to avoid implying that the current update is for two MDOF structures.

## 2026-06-01 Linear-unit key FRF review artifact
- Trial: add 2DOF transfer-function plot, summary, checker, and packet section
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; posterior recovery acceptance_rate = 0.216; MDOF relative_l2_error = 0.0514; channel 2/3 clean relative_l2 = 0.6877; key FRFs reported = 9; review packet completeness pass = true
  - Artifacts: `artifacts/plots/key_2dof_transfer_functions_linear.png`, `artifacts/reports/key_frf_summary.json`, `artifacts/tests/key_transfer_functions_report.json`, updated `artifacts/reports/synthetic_statfem_packet.md`
  - Lessons: separate review units by quantity. This first version incorrectly treated drive-point `F/a` as the plotted apparent-mass convention; see the corrected 7004C convention trial below.
- Trial: correct apparent-mass convention to match NASA-HDBK-7004C expectation
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; key FRFs reported = 14; apparent_mass_without_interior_peak = none; apparent_mass_without_resonant_amplification = none; review packet completeness pass = true
  - Artifacts: regenerated `artifacts/plots/key_2dof_transfer_functions_linear.png`, `artifacts/reports/key_frf_summary.json`, `artifacts/tests/key_transfer_functions_report.json`, updated `artifacts/reports/synthetic_statfem_packet.md`
  - Lessons: 7004C-style load apparent mass is reaction force over input/interface acceleration and has resonance peaks; drive-point `F/a` at the moving coordinate is reciprocal inertance and has resonance minima.

## 2026-06-01 Apparent-mass mistake postmortem
- Trial: document the caught convention error as an agentic workflow failure case
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; key FRFs reported = 14; apparent_mass_without_interior_peak = none; review packet completeness pass = true
  - Artifacts: `docs/lab/apparent-mass-convention-postmortem.md`, `docs/lab/README.md`, updated `artifacts/reports/synthetic_statfem_packet.md`
  - Lessons: this was a semantic specification failure. The agent produced a reproducible artifact for an underspecified technical noun; the human caught the convention mismatch by inspecting curve shape.
- Trial: correct source vs load apparent-mass convention from NASA-HDBK-7004C Figure 9
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: key FRFs reported = 15; source_apparent_mass_without_interior_notch = none; source_apparent_mass_without_low_frequency_growth = none; load_apparent_mass_without_interior_peak = none; load_apparent_mass_without_resonant_amplification = none; review packet completeness pass = true
  - Artifacts: regenerated `artifacts/plots/key_2dof_transfer_functions_linear.png`, `artifacts/reports/key_frf_summary.json`, updated `docs/lab/apparent-mass-convention-postmortem.md`
  - Lessons: source and load apparent mass are both interface quantities in 7004C, but source and load constraints differ. Source AM can have a resonance notch and low-frequency growth; load AM has the familiar fixed-base peak.
- Trial: add mass and uncoupled-frequency reference lines to key FRF plot
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: mass_reference_ok = true; total_mass_ok = true; natural_frequency_reference_ok = true; key FRFs reported = 15; review packet completeness pass = true
  - Artifacts: regenerated `artifacts/plots/key_2dof_transfer_functions_linear.png`, updated `artifacts/reports/key_frf_summary.json`, updated `artifacts/reports/synthetic_statfem_packet.md`
  - Lessons: mass and uncoupled-frequency guide lines make apparent-mass plots easier to audit against low-frequency mass levels and expected resonance/notch locations.

## 2026-06-01 Coupling, error evidence, and sensitivity artifact
- Trial: tie coupling to tray properties and add missing error/sensitivity evidence to the review packet
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; posterior recovery acceptance_rate = 0.226; MDOF relative_l2_error = 0.0514; channel 2/3 clean relative_l2 = 0.5670; tied_coupling_ok = true; error components reconstruct observed-clean residuals; sensitivity scenarios = 5; review packet completeness pass = true
  - Artifacts: `artifacts/reports/figures/error_hyperparameters.png`, `artifacts/reports/figures/channel_error_vs_truth.png`, `artifacts/reports/figures/parameter_error_summary.png`, `artifacts/reports/sensitivity_assumptions/sensitivity_assumptions.md`, `artifacts/tests/tied_coupling_and_errors_report.json`, `artifacts/tests/sensitivity_artifact_report.json`
  - Lessons: the packet previously named uncertainty categories without showing actual values or realized errors. Sensitivity to assumptions should be treated as a default artifact, and smoke tests must not leave their temporary dataset as the canonical packet input.

## 2026-06-01 GP samples and QOI samples in packet
- Trial: add concrete GP discrepancy sample paths and posterior QOI sample visualization to the Bilionis packet
  - Command: `python3 -m py_compile src/inference/mcmc.py scripts/generate_review_packet.py tests/test_review_packet.py && bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; posterior recovery acceptance_rate = 0.226; channel 2/3 clean relative_l2 = 0.5670; key FRFs reported = 15; retained QOI samples = 240; review packet completeness pass = true
  - Artifacts: `artifacts/reports/figures/gp_discrepancy_samples.png`, `artifacts/reports/figures/qoi_samples.png`, updated `artifacts/reports/synthetic_statfem_packet.md`, updated `artifacts/inference/twodof_mcmc_result.json`
  - Lessons: QOI uncertainty is easier to audit when shown as actual retained sample values and response spectra. The current posterior QOI samples are visibly biased high relative to the synthetic truth, so the next technical work should include posterior predictive checks and identifiability/sensitivity on the discrepancy model.
- Trial: triage unclear QOI sample figure
  - Command: `PYTHONPATH=. python3 -m py_compile scripts/generate_review_packet.py tests/test_review_packet.py && PYTHONPATH=. python3 scripts/generate_review_packet.py && PYTHONPATH=. python3 tests/test_review_packet.py`
  - Checker result: pass
  - Key metrics: posterior QOI truth = 1190.2531; posterior QOI mean = 1209.3565; mean bias = +19.1034 (+1.605%); retained samples above truth = 100%; missing review-packet snippets/files = none
  - Artifacts: updated `artifacts/reports/figures/qoi_samples.png`, updated `artifacts/reports/synthetic_statfem_packet.md`
  - Lessons: full-scale spectra can look line-on-line while still producing a biased peak QOI. QOI figures should include residual/zoom panels and explicit bias diagnostics.
- Trial: fix error plot communication by separating observed data, absolute error, and relative diagnostic views
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; channel 2/3 clean relative_l2 = 0.5670; key FRFs reported = 15; sensitivity scenarios = 5; review packet completeness pass = true
  - Artifacts: `artifacts/reports/figures/channel_truth_vs_observed.png`, `artifacts/reports/figures/channel_absolute_error.png`, retained secondary diagnostic `artifacts/reports/figures/channel_error_vs_truth.png`
  - Lessons: normalized error is useful for "where does error matter relative to signal?", but should not be the primary evidence for what noise/discrepancy was injected because denominator effects can look like physics.
- Trial: log-frequency axis and GP-coordinate correction
  - Command: `PYTHONPATH=. python3 -m py_compile src/twodof/synthetic_data.py src/inference/mcmc.py scripts/generate_review_packet.py scripts/run_sensitivity_study.py scripts/explore_gp_error.py tests/test_review_packet.py tests/test_tied_coupling_and_errors.py && bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; posterior recovery acceptance_rate = 0.2313; full MCMC acceptance_rate = 0.2323; post_burn_acceptance_rate = 0.2033; channel 2/3 clean relative_l2 = 0.5670; log_frequency_gp_ok = true; review packet axis_metadata_ok = true; QOI mean bias = +18.2866 (+1.536%); retained QOI samples above truth = 100%
  - Artifacts: updated `artifacts/reports/figures/channel_truth_vs_observed.png`, `channel_absolute_error.png`, `channel_error_vs_truth.png`, `gp_discrepancy_samples.png`; `docs/lab/log-frequency-plot-gp-postmortem.md`; updated `artifacts/reports/synthetic_statfem_packet.md`
  - Lessons: the earlier agent did not fail because log axes were hard; it failed because a requirement satisfied in one artifact was not promoted to a durable plotting convention and checker expectation. The GP is now stationary in natural log frequency, which is a more defensible default for broad-band structural dynamics review than fixed-Hz stationarity.
- Trial: broad harness guardrails for fresh 2DOF rerun
  - Command: `python3 tests/test_review_packet.py`; plus `rg` inspection for new guardrail language
  - Checker result: pass for existing review-packet checker
  - Key metrics: review packet missing_files = none; missing_snippets = none; missing_embedded_images = none; manifest_ok = true; axis_metadata_ok = true
  - Artifacts: `docs/harness/agentic-engineering-quality-gates.md`, `docs/codex_prompts/fresh_2dof_rerun.md`, updated `AGENTS.md`, updated `docs/CODEX.md`, updated `docs/codex_prompts/replicate.md`, `review.md`, and `extend.md`
  - Lessons: human feedback should be generalized into gates: assumptions ledgers, quantity contracts, reference/standards comparisons, review-packet evidence, sensitivity, and checker-backed metadata.

## 2026-06-01 Fresh 2DOF StatFEM/FBS rerun
- Trial: fresh scoped 2DOF StatFEM/FBS rerun with question-first artifacts, quantity contracts, synthetic data, posterior/QOI samples, sensitivity, reference comparison, fresh checker, and prior-run comparison.
  - Command: `bash scripts/run_fresh_2dof_statfem_fbs.sh`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with `shasum -a 256 -c harness/checkers/manifest.sha256`.
  - Key metrics: numeric assumptions = 16 machine-readable rows; Ch2/Ch3 clean relative L2 = 0.770745; sampler acceptance_rate = 0.07737; retained posterior samples = 560; QOI peak tray acceleration mean = 59.10375 m/s^2; 5-95% interval = [58.91892, 59.27161] m/s^2; synthetic truth = 59.03368 m/s^2; QOI fraction above truth = 0.732; sensitivity scenarios = 6 posterior/QOI + 5 synthetic-error; reference checks pass.
  - Reference comparison metrics: Ch4 low-frequency transmissibility median = 1.03667; Ch4 high-frequency median = 0.18006; Ch4 peak = 76.90548 Hz vs tray truth 77.58060 Hz; Ch1 notch = 108.28640 Hz vs dome truth 107.77755 Hz.
  - Artifacts: `artifacts/reports/fresh_2dof_statfem_fbs_20260601/fresh_2dof_statfem_packet.md`; figures and JSON manifest under `artifacts/reports/fresh_2dof_statfem_fbs_20260601/`; implementation in `scripts/fresh_2dof_statfem_fbs.py`; one-command runner `scripts/run_fresh_2dof_statfem_fbs.sh`; checker `tests/test_fresh_2dof_rerun.py`.
  - Lessons: the fresh run intentionally uses one tray-to-primary stiffness/damping in the coupled model rather than copying the prior path. Visual QA caught an overlapping reference-comparison title/metric text before final logging. The low-but-nonzero MH acceptance rate is acceptable for this harness artifact but remains a sampler-quality limitation.

## 2026-06-01 Fresh 2DOF QOI/noise/7004C correction
- Trial: respond to human review by replacing deterministic peak QOI with `3 * GRMS` from tray response PSD, increasing noise/discrepancy assumptions, and adding NASA-HDBK-7004C source/load apparent-mass benchmarks.
  - Command: `bash scripts/run_fresh_2dof_statfem_fbs.sh`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with `shasum -a 256 -c harness/checkers/manifest.sha256`.
  - Key metrics: numeric assumptions = 19 machine-readable rows; Ch2/Ch3 clean relative L2 = 0.770745; sampler acceptance_rate = 0.49263; retained posterior samples = 560; QOI definition = `3 * GRMS of tray acceleration response PSD`; QOI mean = 9.16652 g; 5-95% interval = [7.70190, 10.63325] g; synthetic truth = 8.25930 g; QOI fraction above truth = 0.8518.
  - Noise/discrepancy metrics: median normalized error diagnostics = Ch1 0.263, Ch2 0.299, Ch3 0.309, Ch4 0.285; 90th-percentile diagnostics = Ch1 0.516, Ch2 0.571, Ch3 0.513, Ch4 0.506; response-PSD absolute log-error median = 0.298 and 90th percentile = 0.641.
  - Reference comparison metrics: NASA-HDBK-7004C `Q=50` benchmark load `M(0.62)=1.62423`, load `M(1)=50.01000`, source `M(1)=0.02000`; Ch4 peak = 76.90548 Hz vs tray truth 77.58060 Hz; Ch1 notch = 108.28640 Hz vs dome truth 107.77755 Hz.
  - Artifacts: updated `artifacts/reports/fresh_2dof_statfem_fbs_20260601/fresh_2dof_statfem_packet.md`; added `noise_qoi_7004c_lit_review.md`; added `figures/nasa_7004c_apparent_mass_benchmark.png`; updated `scripts/fresh_2dof_statfem_fbs.py`, `tests/test_fresh_2dof_rerun.py`, `quantity_contracts.md`, and `assumptions_ledger.md`.
  - Lessons: PSD-domain random-vibration QOI is a better match for aerospace review than the peak of one synthetic time realization. Noise should be scaled locally, with floors near notches, when the goal is to stress-test model updating and produce useful review plots. 7004C values should be plotted as source/load apparent mass benchmarks, while reciprocal inertance remains explicitly separate.

## 2026-06-01 Fresh 2DOF model-error and sensitivity clarity correction
- Trial: respond to human review that the reference pass/fail bar chart was not useful, the sensitivity threshold text was confusing, and model-form frequency/damping errors were still too mild.
  - Command: `python3 -m py_compile scripts/fresh_2dof_statfem_fbs.py tests/test_fresh_2dof_rerun.py && bash scripts/run_fresh_2dof_statfem_fbs.sh && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: numeric assumptions = 27; Ch2/Ch3 clean relative L2 = 0.673906; sampler acceptance_rate = 0.49921; retained posterior samples = 560; QOI definition = `3 * GRMS of tray acceleration response PSD`; QOI mean = 12.12008 g; 5-95% interval = [10.21921, 13.94476] g; synthetic truth = 10.89493 g; QOI fraction above truth = 0.8607.
  - Model-error metrics: synthetic truth now shifts dome frequency from nominal 110 Hz to 93.50 Hz (-15%) and tray frequency from nominal 75 Hz to 86.25 Hz (+15%); damping ratios are zeta1 = 0.0225 (+25% from nominal 0.018) and zeta2 = 0.0195 (-25% from nominal 0.026).
  - Sensitivity metrics: `sensitivity_summary.json` now has `decision_threshold = null`; baseline retained-sample QOI recomputation mean = 12.54073 g; damping 0.75 gives +15.0% mean QOI shift; damping 1.25 gives -10.2%; narrow force bandwidth gives -25.0%; wide force bandwidth gives +15.5%.
  - Reference comparison metrics: value-table figure replaced the green pass/fail bar chart. Ch4 low-frequency median = 1.02946; Ch4 high-frequency median = 0.23074; Ch4 peak = 86.90298 Hz vs tray truth 86.25 Hz; Ch1 notch = 93.51496 Hz vs dome truth 93.50 Hz; NASA-HDBK-7004C Figure 9 load `M(0.62)=1.62423`, load `M(1)=50.01000`, source `M(1)=0.02000`.
  - Artifacts: updated `artifacts/reports/fresh_2dof_statfem_fbs_20260601/fresh_2dof_statfem_packet.md`, `figures/reference_standards_comparison.png`, `figures/sensitivity_qoi.png`, `assumptions_ledger.md`, `assumptions_ledger.json`, `noise_qoi_7004c_lit_review.md`, `reference_comparison.json`, `sensitivity_summary.json`, `checker_report.json`, and `checker_report_external.json`.
  - Lessons: a checker-scoreboard figure is not an engineering review artifact unless it exposes the values, expectations, and meaning behind the booleans. Sensitivity text should say whether it refits the posterior or only recomputes retained samples. Human gut checks on frequency/damping error should become explicit model-form assumptions and checker conditions, not hidden tuning.

## 2026-06-01 Fresh 2DOF Bayes-rule and replicate triage
- Trial: respond to human review requesting graphical Bayes-rule evidence, posterior natural-frequency/damping samples with 95% CIs, prior predictive spectra beside data, and explicit simulation replicate counts.
  - Command: `python3 -m py_compile scripts/fresh_2dof_statfem_fbs.py tests/test_fresh_2dof_rerun.py && bash scripts/run_fresh_2dof_statfem_fbs.sh && python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: numeric assumptions = 27; Ch2/Ch3 clean relative L2 = 0.673906; sampler acceptance_rate = 0.49921; retained posterior samples = 560; QOI mean = 12.12008 g; QOI truth = 10.89493 g; QOI 95% interval = [9.88234, 14.28316] g.
  - Parameter posterior metrics: dome frequency median = 93.4717 Hz, 95% CI = [93.1987, 93.7950], truth = 93.50; tray frequency median = 86.2534 Hz, 95% CI = [86.0418, 86.3982], truth = 86.25; dome damping median = 0.021987, 95% CI = [0.019116, 0.025913], truth = 0.0225; tray damping median = 0.021770, 95% CI = [0.020177, 0.023802], truth = 0.0195.
  - Bayes diagnostics: log likelihood at prior center = -8398.77; at synthetic truth = 166.68; at retained posterior mode = 172.90. Conditional likelihood slices are one-dimensional diagnostics, not marginalized likelihoods.
  - Simulation replicate metadata: one realization per FRF/transfer channel, one flight-like response PSD realization, one secondary time-history realization; flight-to-flight variability is not modeled.
  - StatFEM/noise metadata: generated GP model discrepancy and iid sensor noise are kept separate in `fresh_2dof_dataset.json`; the likelihood uses summed fixed covariance and does not infer the realized discrepancy field or hyperparameters.
  - Artifacts: added `figures/bayes_parameter_update.png`, `figures/parameter_posterior_samples.png`, `figures/prior_predictive_vs_data.png`, `figures/posterior_predictive_spectra.png`, and `bayes_update_summary.json`; updated the packet, dataset metadata, assumptions ledgers, manifest, and fresh checker reports.
  - Lessons: posterior predictive distributions should be shown for spectra, not only posterior-mean curves. Dataset replicate count and flight-to-flight variability must be explicit in the packet and checker. A toy can fit far from nominal when the synthetic truth is still inside the model family; that must be labeled as a plumbing check, not evidence of real-FEM robustness.

## 2026-06-02 Fresh 2DOF prior/likelihood methodology clarity
- Trial: respond to human review asking whether discrepancy/hyperparameters should be inferred, what "truth inside the model family" means, what prior variances are assumed, and whether the likelihood uses whole FRFs or peak summaries.
  - Command: `python3 -m py_compile scripts/fresh_2dof_statfem_fbs.py tests/test_fresh_2dof_rerun.py && bash scripts/run_fresh_2dof_statfem_fbs.sh && python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: numeric assumptions = 30; Ch2/Ch3 clean relative L2 = 0.673906; prior/likelihood methodology checker = true.
  - Prior metrics: stiffness prior `log(k/k_nom) ~ Normal(0, 0.18^2)` truncated to `[0.55, 1.65]`; implied natural-frequency prior `sigma_log(f/f_nom)=0.09`, untruncated 95% factor `[0.838, 1.193]`; damping prior `log(zeta/zeta_nom) ~ Normal(0, 0.35^2)`, untruncated 95% multiplier `[0.504, 1.986]`.
  - Likelihood metrics: Ch1-Ch4 use all complex FRF/transfer values at 120 log-spaced frequencies, with real and imaginary residual vectors evaluated independently under `K_discrepancy + diag(sensor_noise^2)`. Flight-like response uses all 181 log response-PSD values. Peak/notch locations are reference checks and plots only, not likelihood summary statistics.
  - StatFEM limitation: discrepancy fields and noise/discrepancy hyperparameters remain fixed assumptions; the desired next step is a hierarchical StatFEM model that infers discrepancy fields/hyperparameters, preferably with repeated tests/flights.
  - Artifacts: updated `fresh_2dof_statfem_packet.md`, `bayes_update_summary.json`, `assumptions_ledger.md`, `assumptions_ledger.json`, `checker_report.json`, `checker_report_external.json`, `scripts/fresh_2dof_statfem_fbs.py`, and `tests/test_fresh_2dof_rerun.py`.
  - Lessons: prior variance and likelihood data usage are central methodology and require checker-backed report text. A future agent should never leave "whole FRF vs peak summary" implicit.

## 2026-06-02 StatFEM method graphic and harness rule upgrade
- Trial: respond to human review that the packet must expose the model form, likelihood function, inferred/fixed/not-inferred assumptions, data/replicate count, and whole-FRF versus peak-summary choice from the first review summary.
  - Command: `python3 -m py_compile scripts/fresh_2dof_statfem_fbs.py tests/test_fresh_2dof_rerun.py && bash scripts/run_fresh_2dof_statfem_fbs.sh && python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: numeric assumptions = 30; Ch2/Ch3 clean relative L2 = 0.673906; `method_summary_documented = true`; method graphical model appears in `manifest.json`; QOI mean = 12.12008 g; QOI truth = 10.89493 g; QOI 95% interval = [9.88234, 14.28316] g.
  - Method-summary metrics: report now states one synthetic dataset, one FRF/transfer realization per channel, one flight-like response PSD, one secondary time-history realization, and no flight-to-flight variability. It states `theta = {k1, k2, zeta1, zeta2, force_amp, force_fc}`, fixed noise/discrepancy hyperparameters, non-inferred discrepancy fields/hyperparameters/replicate effects, and a whole-curve likelihood for 120 complex FRF points plus 181 log response-PSD points.
  - Artifacts: added `figures/statfem_likelihood_graphical_model.png`; updated `fresh_2dof_statfem_packet.md`, `manifest.json`, `checker_report.json`, `checker_report_external.json`, `scripts/fresh_2dof_statfem_fbs.py`, `tests/test_fresh_2dof_rerun.py`, `AGENTS.md`, `docs/harness/agentic-engineering-quality-gates.md`, `docs/CODEX.md`, `docs/codex_prompts/fresh_2dof_rerun.md`, and local Codex skills `honest-technical-work` and `project-harness`.
  - Lessons: a report can contain the right facts but still fail review if the statistical model is scattered across sections. Method visibility should be a checker-backed gate: graphical model, likelihood equation, data count, whole-data versus summary-feature choice, and inferred/fixed/not-inferred variables must be visible before posterior plots.
- Trial: improve graphical-model equation legibility by replacing plain underscore/caret equation strings with Matplotlib mathtext/LaTeX-style rendering.
  - Command: `python3 -m py_compile scripts/fresh_2dof_statfem_fbs.py tests/test_fresh_2dof_rerun.py && bash scripts/run_fresh_2dof_statfem_fbs.sh && python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: `method_summary_documented = true`; missing files/snippets = none; numeric assumptions = 30; Ch2/Ch3 clean relative L2 = 0.673906.
  - Artifacts: regenerated `figures/statfem_likelihood_graphical_model.png` with readable math notation for `theta`, FRF/PSD residuals, covariance, Bayes update, and the run-specific data model.
  - Lessons: method diagrams should use real math rendering and sufficient font size for equations. Plain text symbols such as `_`, `^`, and long one-line likelihoods are not review-grade even when the underlying content is correct.
- Trial: add image-legibility hook and replace stale/cached unreadable method and reference/checker figures with new filenames.
  - Command: `python3 -m py_compile scripts/fresh_2dof_statfem_fbs.py tests/test_fresh_2dof_rerun.py && bash scripts/run_fresh_2dof_statfem_fbs.sh && python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: image legibility report pass = true; figures checked = 20; strict text-heavy figures = `figures/statfem_likelihood_graphical_model_legible.png` and `figures/reference_standards_comparison_cards.png`; strict method figure min font = 12.5 pt vs required 12.0 pt; strict reference figure min font = 11.5 pt vs required 11.5 pt; overlap/clipping/plain-math issues = none for strict figures.
  - Artifacts: added `image_legibility_report.json`; added cache-busting figures `statfem_likelihood_graphical_model_legible.png` and `reference_standards_comparison_cards.png`; updated report, manifest, internal checker, external checker, harness docs, launch prompt, and local skills.
  - Lessons: figure existence and checker booleans are not enough. The first implementation of the hook failed the run by flagging many edge tick labels, then the stricter text-heavy overlap check caught a real overlap in the reference cards. Blocking legibility checks should be strict for method/table/status figures and lighter for ordinary plot axes.
- Trial: smooth the prior-density plots and compare the full FRF/PSD likelihood against a peak/notch feature likelihood.
  - Command: `bash scripts/run_fresh_2dof_statfem_fbs.sh`; then `python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: numeric assumptions = 33; Ch2/Ch3 clean relative L2 = 0.673906; image legibility report pass = true with 21 figures checked and no failed figures; `peak_feature_likelihood_comparison_present = true`.
  - Prior-plot metrics: prior curves in `bayes_parameter_update.png` and `parameter_posterior_samples.png` are now analytic transformed-prior density evaluations rather than finite-sample histograms. Posterior curves are retained-sample KDE summaries.
  - Peak-feature likelihood metrics: feature residual assumptions are log-frequency sigma = 0.06, FRF log-amplitude sigma = 0.30, and PSD log-amplitude sigma = 0.40. Features are Ch1 dome notch, Ch2 primary notch, Ch3 tray notch, Ch4 tray peak, and Ch5 response-PSD peak.
  - Comparison metrics: full-curve QOI mean = 12.12008 g with 95% interval [9.88234, 14.28316] g; peak-feature QOI mean = 10.31594 g with 95% interval [6.86282, 16.94469] g; synthetic truth = 10.89493 g. Peak-feature/full-curve 95% width ratios: QOI = 2.2909, dome frequency = 21.57, tray frequency = 27.32, dome damping = 1.923, tray damping = 5.790.
  - Sampler metrics: full-curve acceptance = 0.4992 with 560 retained samples; peak-feature acceptance = 0.8542 with 540 retained samples.
  - Artifacts: added `peak_feature_likelihood_summary.json`; added `figures/full_vs_peak_feature_likelihood_comparison.png`; updated `fresh_2dof_statfem_packet.md`, `manifest.json`, `checker_report.json`, `checker_report_external.json`, `scripts/fresh_2dof_statfem_fbs.py`, and `tests/test_fresh_2dof_rerun.py`.
  - Lessons: finite prior samples can make a smooth prior look jagged; plot analytic prior densities when available and label sampled estimates when not. Peak-only likelihoods are lossy and need explicit feature extraction, feature uncertainty assumptions, and side-by-side posterior/QOI interval comparisons against the whole-data likelihood.
- Trial: add a peak/notch feature-map benchmark so feature likelihoods are checked against predicted transfer-function features rather than natural frequencies directly.
  - Command: `bash scripts/run_fresh_2dof_statfem_fbs.sh`; then `shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal and external fresh rerun checkers reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: `peak_feature_mapping_benchmark_present = true`; image legibility report pass = true with 23 figures checked and no failed figures; numeric assumptions = 33; Ch2/Ch3 clean relative L2 = 0.673906.
  - Feature-map metrics: Ch1 clean dome notch = 93.576 Hz versus observed notch = 98.107 Hz, frequency z-score = 0.79; Ch4 clean tray peak = 86.341 Hz versus observed peak = 86.416 Hz, z-score = 0.01. The Ch1 frequency-feature likelihood slice peaks above the synthetic truth because the realized observed notch is shifted high.
  - Feature-sensitivity metrics: Ch1 notch frequency sensitivity is 1.06 to dome frequency and 0.00 to tray frequency; Ch4 peak sensitivity is 0.97 to tray frequency and 0.00 to dome frequency. Ch2 and Ch3 are mixed coupled features with dome/tray frequency sensitivities of approximately 0.41/0.62 and 0.62/0.45. Ch5 response-PSD peak amplitude is strongly force-center-confounded with sensitivity -3.57.
  - Artifacts: added `peak_feature_mapping_benchmark.json`, `figures/peak_feature_mapping_benchmark.png`, and `figures/peak_feature_sensitivity_matrix.png`; updated the report, manifest, internal checker, external checker, and feature-likelihood implementation.
  - Lessons: peak/notch likelihoods should be benchmarked through the same feature extractor used in the likelihood. A feature can be physically meaningful but still falsely informative if the realized observed feature is shifted by discrepancy/noise or if the feature is coupled to multiple parameters.
- Trial: triage remaining jagged prior visuals and encode analytic-plus-MC prior plotting as a SciML reporting rule.
  - Command: `bash scripts/run_fresh_2dof_statfem_fbs.sh`; then `python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal and external fresh rerun checkers reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: prior density MC histogram samples = 80,000; MC histogram bins = 90; prior predictive MC samples = 1,600; numeric assumptions = 33; Ch2/Ch3 clean relative L2 = 0.673906; image legibility report pass = true.
  - Artifacts: regenerated `figures/bayes_parameter_update.png`, `figures/parameter_posterior_samples.png`, and `figures/prior_predictive_vs_data.png`; updated `bayes_update_summary.json`, `fresh_2dof_statfem_packet.md`, `manifest.json`, `checker_report.json`, `checker_report_external.json`, `scripts/fresh_2dof_statfem_fbs.py`, `tests/test_fresh_2dof_rerun.py`, harness docs, and local skills.
  - Lessons: even after adding analytic prior curves, low-sample prior predictive bands and unlabeled prior histograms can still read as jagged or ambiguous. For SciML packets, analytic prior density should be the primary line; a high-sample MC histogram should be shown and labeled as a sampling diagnostic; prior predictive bands need enough MC samples for stable visual review.
- Trial: smooth prior/posterior predictive envelope display for the Ch4 prior predictive panel and related spectra.
  - Command: `bash scripts/run_fresh_2dof_statfem_fbs.sh`; then `python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal and external fresh rerun checkers reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: prior predictive MC samples = 4,000; displayed predictive quantile summaries smoothed = true; Gaussian smoothing sigma = 1.8 frequency-grid points; numeric assumptions = 33; image legibility report pass = true.
  - Artifacts: regenerated `figures/prior_predictive_vs_data.png`; updated `bayes_update_summary.json`, `fresh_2dof_statfem_packet.md`, `checker_report.json`, `checker_report_external.json`, `scripts/fresh_2dof_statfem_fbs.py`, and `tests/test_fresh_2dof_rerun.py`.
  - Lessons: a prior predictive envelope is not an analytic prior density. It is a finite-sample, pointwise MC summary of nonlinear forward-model outputs, and sharp moving resonances can make raw quantile curves look jagged even with many samples. If smoothing is used for review readability, label it as display smoothing and record the smoothing parameter.
