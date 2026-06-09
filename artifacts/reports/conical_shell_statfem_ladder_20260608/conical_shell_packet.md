# Conical Shell FEM/Test Source Audit and StatFEM Launch Packet

## Method Summary
- **Engineering decision:** Can the Vibrationdata conical-shell example serve as a modest, auditable first real-ish dynamic digital-twin sandbox?
- **Current answer:** Yes for a modal-only v1 digital-twin sandbox; no for a full FRF digital twin yet.
- **Data count:** one published modal-test comparison table, one human Femap/Nastran solve screenshot set, two published FRF figures without raw ordinates, and one source Nastran deck.
- **Likelihood status:** active modal-only likelihood using exact grid quadrature over one stiffness-scale parameter. This is not NUTS/HMC.
- **Inferred variables:** global shell stiffness scale only.
- **Fixed assumptions:** see `assumptions_ledger.md`.
- **Not inferred:** material density, shell thickness, full mode-shape discrepancy field, raw FRF ordinates, and damping curve.
- **QOI:** aft peak accelerance near the first flexible shell mode from coarse visual digitization, with large uncertainty.

## Source Provenance
- StructuralFE index: https://www.vibrationdata.com/StructuralFE.htm
- PDF: `http://www.vibrationdata.com/tutorials_alt/conical_shell.pdf` -> fetched
- Nastran deck: `http://www.vibrationdata.com/tutorials_alt/conical_shell3.nas` -> fetched
- Access quirk: browser-like user agent for the `.nas` returned `406`; curl-like user agent succeeded. This is recorded so future agents do not misdiagnose the source as unavailable.

## Published Test/FEM Comparison
The source report states that the preliminary FEM material properties were adjusted so the FEM fundamental frequency matched the measured fundamental. Therefore mode 1 agreement is useful provenance, not independent validation.

| Mode | Measured Hz | Published preliminary FEA Hz | Error % |
|---:|---:|---:|---:|
| 1 | 97.6 | 97.6 | +0.00 |
| 2 | 278.0 | 274.0 | -1.44 |
| 3 | 429.0 | missing | missing |
| 4 | 529.0 | 523.0 | -1.13 |

![Measured vs published FEA](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/published_modal_frequency_comparison.png>)

![Frequency error](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/published_frequency_error.png>)

## Parsed Source FEM Metadata
- Solution: `SOL SEMODES`
- Nodes: `961`
- Elements: `912` = `872` CQUADR + `40` CTRIAR
- Shell thickness from PSHELL: `0.1` inch
- Boundary-condition interpretation from deck: free-free flexible-mode solve; no SPC/SPC1 constraints found.
- Bounding box in source coordinates: `{'x_min_in': 0.0, 'x_max_in': 45.0, 'y_min_in': -7.0, 'y_max_in': 7.0, 'z_min_in': -7.0, 'z_max_in': 7.0}`

![Parsed source mesh](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/source_nastran_mesh.png>)

## Human Femap/Nastran Solve
The human-supplied solve shows six near-zero free-free rigid-body modes, followed by nearly degenerate shell-mode pairs. The first three flexible pair means agree with the published preliminary FEA values to within about one percent.

| Published mode | Measured Hz | Human Nastran pair mean Hz | Error vs measured % | Notes |
|---:|---:|---:|---:|---|
| 1 | 97.6 | 97.6373 | +0.04 |  |
| 2 | 278.0 | 274.0179 | -1.43 |  |
| 3 | 429.0 | unmatched | unmatched | unmatched measured feature in the published preliminary FEA comparison |
| 4 | 529.0 | 524.2939 | -0.89 |  |

![Human Nastran frequency table](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/human_nastran_frequency_table.png>)

![Local solve comparison](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/local_solve_vs_published_modal_comparison.png>)

## Mode-Shape Evidence Status
The source PDF contains mode-shape figures, and the human screenshots show representative deformed views for modes 7 and 9. This packet records screenshot provenance but does not claim machine-readable mode-shape vectors. A solved mode-shape export remains the next gate.

![Mode-shape status](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/mode_shape_status_not_solver_output.png>)

## FRF Evidence
The report includes accelerance FRF figures in `G/LBF`. This phase adds coarse visual peak features with intentionally large uncertainty. These are secondary digitized data, not raw FRF ordinates.

![Peak evidence](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/published_peak_evidence_log_frequency.png>)

![Digitized FRF peak features](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/digitized_frf_peak_features.png>)

## Modal-Only StatFEM v1
- Model equation: `f_obs_i = sqrt(k_scale) * f_fem_i + discrepancy_i + observation_noise_i`
- Inference method: `exact grid quadrature over one stiffness-scale parameter; not NUTS/HMC`
- Reason for no NUTS/HMC: The v1 posterior has one parameter and is evaluated exactly on a dense grid, which is more transparent than sampling. Do not generalize this to future multi-parameter updates.
- Calibration modes: `[1, 2]`. Mode 1 is included but interpreted cautiously because the source FEM was tuned to the fundamental.
- Held-out mode: `[4]`.
- Posterior stiffness scale median: `1.0130`, 90% interval `[0.9663, 1.0609]`.
- Held-out mode 4 observed `529.0` Hz; predictive 90% interval `[497.6, 557.8]` Hz; covered: `True`.

![Modal StatFEM v1](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/modal_statfem_v1_posterior_and_holdout.png>)

## FRF/QOI Layer
- QOI: aft peak accelerance near first flexible shell mode.
- Median peak accelerance: `17.50` G/LBF.
- Approximate 90% interval: `[12.56, 22.44]` G/LBF.
- Posterior-shifted peak frequency: `98.23` Hz.
- Warning: Amplitude is digitized secondary evidence, not a FEM-predicted accelerance. This QOI is a plumbing artifact until raw FRF or a modal participation model is added.

![FRF QOI](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/frf_qoi_peak_accelerance.png>)

## Digital Twin Launch
![StatFEM launch graphical model](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/statfem_launch_graphical_model.png>)

- Active modal-only StatFEM posterior in this packet: `True`
- Recommended next v2: replace coarse peak digitization with raw FRF curve extraction or manual plot-digitizer traces, then move the discrepancy from mode-index covariance to log-frequency covariance.
- Held-out validation rule: do not validate on mode 1 alone because it was tuned. Continue using mode 4 and the unmatched 429 Hz feature as model-class checks.
- Discrepancy: fixed output discrepancy covariance in v1; output-space GP over mode index/log frequency is the next upgrade.

## What This Proves
- The conical-shell source files are reachable and cacheable.
- The PDF contains enough published modal-test evidence to compare test frequencies with preliminary FEA.
- The source Nastran deck can be parsed for geometry, elements, material/property cards, and boundary-condition metadata.
- The human Femap/Nastran solve reproduces the published preliminary FEA mode pairs.
- A first modal-only Bayesian update can be run and checked from one command.

## What This Does Not Prove
- It does not prove that the preliminary FEM predicts the fundamental from first principles; the report says it was tuned.
- It does not prove damping or FRF amplitude calibration; raw FRF ordinates were not extracted.
- It does not prove full mode-shape agreement; screenshots are provenance, not machine-readable MAC evidence.
- It does not use NUTS/HMC; the v1 posterior is one-dimensional exact grid quadrature.

## Checker Status
- Overall pass: `True`
- See `checker_report.json` for machine-readable evidence.
