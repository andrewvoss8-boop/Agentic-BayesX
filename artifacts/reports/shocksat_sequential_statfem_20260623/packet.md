# Packet - ShockSat sequential statFEM PSD-envelope pilot

**Overall checker result: YELLOW 18/3/0.**
This is a documented validity-probe result, not a green replacement claim.

## First-pass method summary

Plain-English statistical terms: a Bayesian filter updates the current state estimate each time a new measurement arrives. Here the state is modal displacement and modal velocity. For replayability this pilot uses a fixed-prior sequential MAP update rather than a full covariance-recursion Kalman filter. NUTS/HMC is used only for the small stiffness-subset calibration; the time-domain filter itself is not NUTS.

- Model form: reduced ShockSat modal dynamics with state `x=[q, qdot]`, measured hammer force input `F_d(t)` in lbf, and sensor acceleration output in g.
- Observation model: `a_obs(t) = C_obs x(t) + D_obs F_d(t) + e(t)`, with fixed Gaussian observation noise `e(t)`.
- Data count: 4 clean modal-hammer references, 6 hits per reference, 84 mapped sensors, 76 observed sensors, 8 held-out sensors for the seed-0 90% split.
- Data usage: whole time-history acceleration samples are assimilated for observed sensors; held-out acceptance uses only PSD-envelope metrics after FRF reconstruction.
- Inferred variables: modal state through the filter; selected stiffness groups by NUTS for the stiffness-updated variant.
- Fixed assumptions: damping ratio 1%, filter rate 2000 Hz, fixed process/observation hyperparameters, flat `S_F0=1 lbf^2/Hz`.
- Non-inferred latent variables/hyperparameters: forcing uncertainty GP, process-noise scale, measurement-noise scale, build/test variability, and a full material field.

## Decision metric

| Variant | Median GRMS ratio vs FEM+6 dB | Clean-win rate | Median exceed-energy | Interpretation |
|---|---:|---:|---:|---|
| `nominal_residual` | 2.15 | 6.2% | 0.00779 | no PSD-envelope win |
| `stiffness_residual` | 2.07 | 18.8% | 0 | no PSD-envelope win |

Best median ratio: `stiffness_residual` = 2.07. The acceptance threshold is `< 1` with low held-out exceedance.

## Baselines

- FEM+6 dB was recomputed on the same split and smoothline convention.
- Existing L5/modal-frequency PSD-envelope probe was reused from `/Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/shocksat_psd_envelope_twin_20260623/out/probe_seed00.json`; combined-correlated median GRMS ratio there was 10.2.

## Discrepancy and identifiability

Selected stiffness groups from observed-mode sensitivity/FIM: bottom_box, top_box.
Small-subset NUTS diagnostics: max R-hat 1.002, min ESS 1157, divergences 0.
Worst training residual band multiplier for the sequential 97.5% PSD envelope: 22.0 dB. Large values mean model discrepancy is doing real work and the result should stay YELLOW.

## Figures

- `figures/fig_method_graph.png`: run-specific filter/likelihood diagram.
- `figures/fig_grms_summary.png`: median GRMS ratio by reference and variant.
- `figures/fig_example_envelope.png`: one held-out PSD/envelope example with the inherited units and smoothline convention.

## Checker gates

- **GREEN** `file.priority_deliverables.md`: present
- **GREEN** `file.decisions_log.md`: present
- **GREEN** `file.question_framing.md`: present
- **GREEN** `file.quantity_contracts.md`: present
- **GREEN** `file.assumptions_ledger.md`: present
- **GREEN** `file.run_all.sh`: present
- **GREEN** `file.check.py`: present
- **GREEN** `file.runtime.json`: present
- **GREEN** `file.out/results.json`: present
- **GREEN** `split.no_leakage`: 76 observed / 8 held-out; disjoint
- **GREEN** `quantity.units`: {'acceleration': 'g', 'force': 'lbf', 'frf': 'g/lbf', 'psd': 'g^2/Hz'}
- **GREEN** `psd.metrics_present`: 64 held-out sensor-reference rows
- **YELLOW** `result.psd_improvement`: no green PSD-envelope win: best stiffness_residual median ratio 2.07, clean-win 0.19
- **YELLOW** `filter.hyperparameters`: process and observation noise scales are fixed validity-probe assumptions, not inferred/posterior
- **GREEN** `stiffness.nuts_subset`: small-subset NUTS converged: R-hat 1.002, ESS 1157, div 0
- **YELLOW** `discrepancy.residual_band`: worst training residual 97.5% PSD multiplier 22.0 dB
- **GREEN** `baseline.l5_reused`: existing L5/modal-frequency probe reused by path
- **GREEN** `runtime.accounting`: active=115.895 elapsed=115.895
- **GREEN** `figures.present`: figures/fig_method_graph.png, figures/fig_grms_summary.png, figures/fig_example_envelope.png
- **GREEN** `figures.image_qa`: {"fig_grms_summary.png": {"width": 1734, "height": 940, "mode": "RGBA", "legible_min_size_px": true}, "fig_example_envelope.png": {"width": 1620, "height": 942, "mode": "RGBA", "legible_min_size_px": true}, "fig_method_graph.png": {"width": 1700, "height": 720, "mode": "RGBA", "legible_min_size_px": true}}
- **GREEN** `figures.tufte_lint`: lint output present

## Replay

Run `bash run_all.sh` from this workspace.
