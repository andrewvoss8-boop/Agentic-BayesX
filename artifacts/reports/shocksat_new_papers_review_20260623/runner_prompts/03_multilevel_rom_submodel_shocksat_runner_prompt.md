# Runner prompt - ShockSat multi-level ROM/submodel architecture pilot

You are a runner agent in Agentic BayesX. Build a bounded architecture pilot inspired by Lu et al.'s multi-level wing digital twin. The goal is not Bayesian updating. The goal is to test whether a hierarchical reduced model can make ShockSat response/QOI evaluation faster while preserving accuracy against the existing higher-fidelity/reduced baseline.

## Re-ground first

Read:
1. `AGENTS.md`.
2. `artifacts/reports/shocksat_psd_envelope_twin_20260623/priority_deliverables.md`, `decisions_log.md`, and `quantity_contracts.md`.
3. Existing ShockSat reduced model assets in the current PSD-envelope workspace.
4. Source paper PDF: `references/pdfs/Multi-level digital twin for real-time deformation and stress analysis of wing structures.pdf`.

Restate goal, inherited data decision, next action, and open ambiguities in one line.

## Engineering question

Can a multi-level ShockSat digital twin architecture evaluate response-limit or local-response QOIs materially faster than the current workflow while matching the existing validated/reduced model within a documented tolerance?

## Method interpretation

Adapt the paper's hierarchy to ShockSat:
- Level 0: global reduced modal ROM for whole-structure response.
- Level 1: component/group-level response maps for major structural regions or stiffness groups.
- Level 2: local submodel or local-response surrogate for a QOI region, such as a sensor neighborhood, interface/mount region, or modal stress proxy.

Use POD or another explicit basis compression only where it reduces real computation or preserves a local QOI. Do not add an architecture layer for aesthetics.

FMI/FMU export is optional. A plain Python interface is acceptable if the purpose is algorithmic validation; label it as not FMI-deployed.

## Required deliverables

Create `artifacts/reports/shocksat_multilevel_rom_YYYYMMDD/`.

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

1. Pick one QOI that current ShockSat work already knows how to compute, preferably response PSD-envelope GRMS for held-out sensors or a local/modal response proxy.
2. Build a Level-0 reduced response evaluator from existing modal assets.
3. If using a Level-2 submodel/surrogate, train it only on model-generated data and label it as FEM-vs-FEM validation unless measured local truth exists.
4. Compare against the current baseline evaluator:
   - runtime;
   - QOI error;
   - peak/resonance placement;
   - envelope GRMS and exceedance if using PSD-envelope QOI.
5. Report whether the hierarchy gives a practical speed/accuracy tradeoff.

## Gates

- Quantity contract before computation: define the QOI, numerator/denominator, units, excitation, boundary condition, and expected limiting/resonance behavior.
- Reference gate: compare to the existing ShockSat baseline, not to a newly invented target.
- Accuracy gate: report max and median QOI error; if the QOI is an envelope, report GRMS ratio and energy-weighted exceedance.
- Runtime gate: record active runtime and wallclock; speedup must be measured on the same machine.
- Validation label gate: if there is no measured local stress/local response truth, call the result FEM-vs-FEM or architecture validation, not physical validation.
- No Bayesian claim gate: this is not statFEM and not posterior updating unless you add a separately labeled Bayesian layer.

## Result interpretation

GREEN: measured speedup plus QOI accuracy/coverage meets the thresholds written in `check.py`, with no hidden units or boundary-condition mismatch.

YELLOW: architecture is replayable and informative, but validation is FEM-vs-FEM only, speedup is marginal, or the useful QOI remains a proxy rather than a measured ShockSat stress/response truth.

RED: a speedup or accuracy claim is made without checker output, the hierarchy changes the QOI convention, or local stress/response validation is presented as physical validation when no measured truth exists.

## Stop conditions

Stop with a YELLOW packet if:
- the hierarchy cannot beat the current reduced workflow in speed;
- local-submodel training data are only synthetic and no useful QOI is validated;
- the architecture obscures units, axes, or boundary conditions;
- it becomes a refactor without a measurable QOI benefit.

Useful negative: "the existing ShockSat ROM is already fast enough, so multi-level architecture is not the next lever" is an acceptable outcome.
