# Runner prompt - ShockSat latent-force model-form-error pilot

You are a runner agent in Agentic BayesX. Build a bounded pilot inspired by Kashyap and Nayek's GPLFM + BNN probabilistic digital twin. The question is whether a latent-force model-form-error representation learned from clean ShockSat modal-hammer data generalizes to held-out sensors or references.

## Re-ground first

Read:
1. `AGENTS.md`.
2. `artifacts/reports/shocksat_psd_envelope_twin_20260623/priority_deliverables.md`, `decisions_log.md`, and `quantity_contracts.md`.
3. `artifacts/reports/shocksat_multiref_amplitude_20260622/packet.md`.
4. Source paper PDF: `references/pdfs/probabilistic digital twin for misspecified structural dynamical systems via latent force.pdf`.

Restate goal, inherited data decision, next action, and open ambiguities in one line.

## Engineering question

Can model-form error in the ShockSat linear/modal ROM be represented as a low-dimensional latent force that improves held-out response prediction, especially response PSD-envelope GRMS and energy-weighted exceedance, without merely fitting observed channels?

## Method interpretation

Use a reduced modal latent-force model:
- Nominal model: current ShockSat reduced modal dynamics.
- Observations: modal-hammer force and acceleration time histories or band-limited FRFs, with units checked.
- Diagnosis: estimate state and latent model-form-error force using a Gaussian Process Latent Force Model (GPLFM) or a simpler Kalman/smoother equivalent in a low-dimensional modal/group basis.
- Mapping: learn a probabilistic state-to-latent-force map. A Bayesian neural network is optional; a simpler probabilistic regressor is acceptable for the first pilot if labeled.
- Prognosis: do not directly integrate an unconstrained learned nonlinear correction. Generate pseudo-measurements of latent force and assimilate them in a stable filter, matching the paper's core stability idea.

Do not apply a latent force at every full FEM DOF. Start with modal coordinates, physical groups, or a small set of candidate residual locations justified by sensitivity.

## Required deliverables

Create `artifacts/reports/shocksat_latent_force_bnn_YYYYMMDD/`.

Files:
- `priority_deliverables.md`
- `decisions_log.md`
- `question_framing.md`
- `quantity_contracts.md`
- `assumptions_ledger.md`
- `run_all.sh`
- `check.py`
- `runtime.json`
- `packet.md`

## Minimum viable pilot

1. Select one clean reference for diagnosis and one held-out reference or held-out sensor set for prognosis.
2. Fit the nominal linear ROM baseline on the same training data.
3. Estimate latent-force residuals on training data.
4. Train a state-to-latent-force probabilistic map with uncertainty.
5. Predict held-out response with:
   - nominal ROM;
   - current L5/modal-frequency baseline if cheap;
   - latent-force pseudo-measurement model.
6. Score:
   - held-out time-domain acceleration or FRF error;
   - PSD-envelope GRMS ratio vs FEM+6 dB;
   - energy-weighted exceedance;
   - calibration/coverage of predictive intervals.

## Gates

- Observability gate: show which latent-force basis directions are observable from the chosen sensors.
- Sensor-leakage gate: held-out channels cannot train the latent force, BNN/regressor, scaler, or hyperparameters.
- Extrapolation gate: report whether held-out states lie inside the training state range. If not, label the result YELLOW at best.
- History-dependence gate: if residuals show hysteresis or dependence on prior state, state that the paper's static state-to-MFE map is violated.
- Stability gate: demonstrate the pseudo-measurement filtering approach stays numerically stable; direct learned-dynamics integration is optional and must be labeled diagnostic-only.
- Scale gate: report per-iteration or total runtime; no real-time claim without measured runtime.
- NUTS/HMC gate: if doing Bayesian parameter updating beyond filtering/regression, use NUTS/HMC and report diagnostics. Otherwise label the method as filtering/regression, not NUTS.

## Result interpretation

GREEN: latent-force model improves held-out PSD/FRF or time-domain scores and coverage without leakage, with stable propagation and clear observability.

YELLOW: observed-channel fit improves but held-out improvement is absent, extrapolation is significant, the map is history-dependent, or the method is empirical/offline only.

RED: data leakage, per-held-out tuning, unstable predictions hidden from the report, or claims stronger than held-out scores.

An honest negative is valuable: it tells us whether latent-force model-form-error learning attacks the real ShockSat amplitude/PSD limitation or just repackages it.

