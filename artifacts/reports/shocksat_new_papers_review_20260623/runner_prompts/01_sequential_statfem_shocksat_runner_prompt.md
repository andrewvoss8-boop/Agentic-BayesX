# Runner prompt - ShockSat sequential statFEM elastodynamics pilot

You are a runner agent in Agentic BayesX. Build a bounded, checker-backed pilot that asks whether Kavrakov et al.'s sequential statFEM elastodynamics formulation can improve the **current ShockSat PSD-envelope QOI only** over the existing modal/frequency-domain L5 workflow and nominal FEM+6 dB.

## Re-ground first

Read:
1. `AGENTS.md` and obey every gate, especially the three-tier result standard, NUTS/HMC rule, convergence gate, quantity-contract gate, plot/human-review gate, verification gate, and runtime accounting gate.
2. `artifacts/reports/shocksat_psd_envelope_twin_20260623/priority_deliverables.md`, `decisions_log.md`, and `quantity_contracts.md`.
3. `artifacts/reports/shocksat_multiref_amplitude_20260622/packet.md` and `checker_report.json`.
4. The source paper PDF: `references/pdfs/Statistical finite elements for sequential data synthesis in solid dynamics.pdf`.

Restate in one line: goal, last inherited decision, next action, and open ambiguities.

## Engineering question

Can a sequential statFEM filter on clean ShockSat modal-hammer time histories produce a **lower-GRMS 97.5th-percentile held-out response-PSD envelope** than FEM+6 dB, while still satisfying the current energy-weighted exceedance rule, without hiding model-form error in an over-flexible forcing term?

Primary QOI, inherited and locked from `shocksat_psd_envelope_twin_20260623`:
- Response PSD: `S_aa,s(f) = |H_{s,d}(f)|^2 * S_F(f)`, with flat `S_F0 = 1 lbf^2/Hz`, identical for FEM, L5, and sequential statFEM.
- Twin envelope: top of the 2-sided 95% predictive band = 97.5th percentile PSD.
- Smoothline envelope: identical peak-pick plus piecewise-linear log-log envelope algorithm for every method.
- Win metric: `GRMS(sequential statFEM 97.5% envelope) / GRMS(FEM+6 dB envelope) < 1`.
- Coverage metric: energy-weighted positive dB exceedance of held-out measured PSD above the sequential-statFEM envelope. Do not use binary "any poke fails" coverage.

Time-domain acceleration traces and reconstructed FRFs are allowed only as diagnostics or implementation checks. They are not acceptance scores for this runner.

## Method interpretation

Implement a reduced-order analogue of the paper, not a full-FE solver:
- Use the existing ShockSat reduced modal/74-DOF machinery as the state model.
- Use raw or cached clean modal-hammer time histories from Test01, Test02, Test04, and Test06 when available.
- State vector: modal displacement and velocity, with measurement equation to sensor acceleration. Define units explicitly.
- Known input: measured hammer force in lbf, converted consistently. If you treat forcing uncertainty as a GP, label exactly which part is measured-force uncertainty versus model misspecification.
- Model misspecification: start with a low-dimensional Brownian/GP residual in modal coordinates or group-level response space. Do not put an independent residual at every sensor unless you prove held-out generalization.
- Material/stiffness uncertainty: choose at most a small subset of current L5 stiffness groups, justified by strain-energy/FIM sensitivity.

If hyperparameters are optimized by marginal likelihood, label the result `empirical Bayes`, not a full posterior over hyperparameters. If you infer hyperparameters with sampling, use NUTS/HMC and report all-variable R-hat, ESS, and divergence fraction.

## Required deliverables

Create a new workspace: `artifacts/reports/shocksat_sequential_statfem_YYYYMMDD/`.

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
- saved plotting scripts and figures if figures are generated

## Minimum viable pilot

1. Use the clean modal-hammer data and splits from `shocksat_psd_envelope_twin_20260623`; start with the same 90% training validity probe before any broader 50-90% sweep.
2. Run three baselines:
   - FEM+6 dB PSD smoothline envelope;
   - existing L5/modal-frequency PSD-envelope prediction if cheap to reuse;
   - sequential statFEM filter.
3. Convert every method's held-out prediction to the inherited response PSD `|H|^2*S_F`, then apply the identical smoothline envelope algorithm.
4. Score **only** the inherited PSD-envelope metrics:
   - envelope GRMS ratio vs FEM+6 dB;
   - energy-weighted positive dB exceedance vs held-out measured PSD;
   - coverage/sharpness summaries of the 97.5th percentile envelope;
   - optional comparison to existing L5 PSD-envelope on the same split.
5. Report whether the sequential statFEM filter improves the PSD-envelope decision metric relative to FEM+6 dB and L5. Do not present time-domain trace fit or FRF fit as success if PSD-envelope GRMS/exceedance does not improve.

## Gates

- Quantity contract before fitting: acceleration, force, state, FRF, PSD, smoothline envelope, GRMS, and energy-weighted exceedance units. The PSD-envelope contract must match `shocksat_psd_envelope_twin_20260623/quantity_contracts.md`.
- Data split gate: no held-out sensor/reference data may enter filter fitting, hyperparameter optimization, or display tuning.
- Identifiability gate: before freeing stiffness/material fields, report sensitivity/FIM at the realized discrepancy floor.
- Discrepancy gate: compare "all error as forcing" versus "explicit material/stiffness update plus model misspecification" on the same split. The paper's key warning is that treating all discrepancies as forcing can be less accurate.
- Sampler/filter labeling gate: Bayesian filter is not NUTS. Empirical-Bayes hyperparameter optimization is not a posterior.
- Plot gate: all numeric figures must be saved scripts, Tufte-linted, and labeled with run, data split, and any invalidity.
- PSD-only acceptance gate: `check.py` must fail RED if the packet claims success without PSD-envelope GRMS ratio and energy-weighted exceedance on held-out data.
- Overall result: GREEN only if PSD-envelope held-out thresholds are met and the checker says so; YELLOW for documented PSD-envelope no-improvement or empirical-Bayes-only caveats; RED for leakage, fabricated improvement, mismatched units, or success claimed from non-PSD diagnostics.

## Stop conditions

Stop early with a YELLOW packet if:
- raw time histories or force channels cannot be loaded with verified units;
- the reduced state/measurement mapping cannot produce a held-out PSD envelope with the inherited units and smoothline convention;
- the filter improves time-domain traces or FRF overlays but fails the PSD-envelope GRMS/exceedance metric;
- model misspecification absorbs all physics and makes stiffness/material inference uninterpretable.

Honest negative is useful: the goal is to learn whether sequential statFEM is a real ShockSat PSD-envelope lever, not to force a win.
