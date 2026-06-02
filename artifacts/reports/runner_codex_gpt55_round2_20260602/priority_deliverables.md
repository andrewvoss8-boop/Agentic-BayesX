# Priority Deliverables — Codex GPT-5.5 Round 2

## Workspace Assertion

- Working directory printed before the run: `/Users/avoss/Downloads/bayesX/Agentic BayesX`.
- Interpretation: this path is the isolated runner workspace supplied in the runner prompt, not the master repo. If this assertion is later found false, this run should be rejected.

## Priority Interpretation

The human's highest-priority request is the coupled-system **interface acceleration response PSD**, not the flight forcing input PSD. I interpret the quantity as acceleration-squared spectral density at the dome/source/interface coordinate `m1` of the coupled dome/tray flight model under latent flight forcing into `m1`, with units `g^2/Hz`.

The engineering comparison is a PSD-envelope check against the original smoothline test spec at every frequency. The tray `3*GRMS` overlay is a scalar summary only and can hide narrow-band exceedances.

## Deliverables And Acceptance Tests

| Priority | Interpretation | Acceptance test | Delivered artifact |
|---|---|---|---|
| Coupled interface acceleration response PSD GIF | For each cumulative flight update, plot posterior/predictive mean plus 95% and 99% credible bands for coupled interface response PSD in `g^2/Hz` against the original smoothline spec on a log-frequency axis. | Animated GIF exists; has one frame per flight; every frame includes smoothline, mean, 95% band, 99% band, units, log-frequency axis, and legend; report states PSD-envelope exceedance metrics. | `figures/interface_response_psd_evolution.gif` |
| Forcing overlay | Plot discrete flight forcing PSD sample curves over the original flat force PSD behind the spec and the mean flight forcing PSD, preserving force units `N^2/Hz`. | Static figure exists; curves are discrete samples, not only quantile bands; original force PSD is shown as the higher reference and the -6 dB flight mean is labeled as a project assumption, not a GEVS qualification margin. | `figures/flight_forcing_samples_overlay.png` |
| Tray `3*GRMS` vs vibe reference | Plot the flight tray `3*GRMS` sequence against the original first-build vibe-test `3*GRMS = 43.9 g` and smoothline input `3*GRMS = 28.3 g`. | Figure exists; all series/reference lines have a legend; axes keep flight and vibe levels visible; report notes `3*GRMS` is a Gaussian 3-sigma estimate, not a hard maximum. | `figures/flight_tray_3grms_vs_vibe_reference.png` |
| Resolution fix | Use `sequential_dataset.json` as the base grid and add mode-local refinement around tray ~86 Hz and dome ~93.5 Hz for response evaluation. | Grid metadata exists; spacing near the half-power bands is reported; sensitivity check compares base vs refined QOI/PSD metrics and reports shifts. | `resolution_sensitivity.json`, `figures/resolution_sensitivity.png` |
| Sampler/convergence fix | Try real NumPyro NUTS in a local venv; use at least 4 chains, longer warmup, non-centered build/flight latent effects, and sample raw latents. | `nuts_diagnostics.json` reports backend, chains, warmup, post-warmup draws, divergences, max R-hat, min bulk ESS, min tail ESS over all variables. Clean NUTS pass requires max rank-normalized split R-hat < 1.01, bulk and tail ESS >= 100 x chains, and zero divergences. | `nuts_diagnostics.json` |
| Plot hygiene | Every generated figure/panel has a legend and frequency-domain plots use log-frequency axes unless explicitly justified. | Checker reports no missing legends for required figures and records image-legibility QA. | `checks.json`, `image_legibility_report.json` |
| Runtime | Track active command runtime and elapsed wall-clock runtime. | `runtime.json` exists and `active_runtime_s <= elapsed_wallclock_s`. | `runtime.json` |

## Ambiguities And Assumptions

- "Original test spec" means the smoothline acceleration PSD from the setup packet, with points `(20 Hz, 0.01 g^2/Hz)`, `(100 Hz, 0.1 g^2/Hz)`, `(750 Hz, 0.1 g^2/Hz)`, `(2000 Hz, 0.001 g^2/Hz)`.
- "All flight forcing draws" means the 11 flight forcing samples represented by the stored build/flight observations and posterior/predictive forcing draws used in this run. I will show the observed/generated flight sample curves as discrete lines and label any posterior-generated forcing curves separately if included.
- "After each flight" means cumulative updates after flights 1 through 11, producing 11 GIF frames.
- The stored setup has no real hardware data; all conclusions are synthetic-harness conclusions, not flight qualification claims for hardware.
