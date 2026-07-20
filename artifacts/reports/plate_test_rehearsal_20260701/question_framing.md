# Question & decision framing — plate-test rehearsal

## The engineering decision being supported
Whether to ask the partner for hardware time to run the >200 Hz drumhead plate modal test
(12+ Z-accelerometers, +Y drive) — on the strength of the promised normal-Z band buy-down
(5.4x -> 3.5x). A failed rehearsal REVISES the test design before the ask; a passed rehearsal
hardens it.

## The question
Does the promised buy-down survive the ACTUAL Bayesian pipeline — synthetic-but-realistic plate
data, joint NUTS inference, honest un-representable fine structure — or was it an artifact of the
analytical sigma-downgrade curve (which never ran inference)?

## Objective function / success metrics — PRE-REGISTERED (locked with the checker BEFORE science runs)
All on the tray net-CG NORMAL-Z force QOI, 1-octave-smoothed, 45-260 Hz (netcg conventions).
Main truth-generation amplitude sigma SD_A_U = 0.80 (the netcg tier value), n_seed = 8 per arm.

| # | criterion | GREEN | YELLOW (honest miss, documented) | RED |
|---|---|---|---|---|
| S1 headline buy-down | arm A1 (12 sensors): MEDIAN delivered 95% band factor over seeds | <= 3.5x | > 3.5x but < A0 median (real but smaller buy-down; report the honest number) | >= A0 median (no buy-down) or missing |
| S2 calibration | arm A1: mean energy-weighted 1-oct coverage of the true spectrum over seeds AND per-seed floor | mean >= 0.90 AND >= 6/8 seeds >= 0.85 | mean >= 0.80 (under-coverage understood + reported) | mean < 0.80 (the band lies) |
| S3 convergence | ALL NUTS runs used in headline numbers | max R-hat <= 1.05, min ESS >= 200 (all variables), div < 2% | isolated failures excluded + reported, >= 6/8 seeds clean | headline uses non-converged runs |
| S4 integrity (no false sharpening) | arm A0 (1 sensor): median band factor | >= 4.5x (stays near the current 5.4x) | 3.5-4.5x with a documented mechanism | < 3.5x (circularity — withdraw) |
| S5 robustness | arm A3 (12 sensors + placement jitter): median band factor and mean coverage | band <= 4.2x AND coverage >= 0.85 | worse but monotone/understood | coverage < 0.70 (design fragile — revise) |
| S6 pooling checkable | arm A1: per-target-mode log-amplitude posterior sd (median over seeds/modes) | <= 0.40 (vs prior 0.80) | 0.40-0.60 (partially constrained) | ~0.80 (data adds nothing) |

Overall: RED if any criterion RED; else YELLOW if any YELLOW; else GREEN. The checker
(`check.py`, SHA-locked) evaluates these mechanically from `out/summary.json`.

## What the run may choose (automated)
Seeds, NUTS tuning within the stated config, greedy sensor placement (same algorithm as
pretest_design), figure layout.

## What remains human judgment
Whether a YELLOW S1 (e.g. 3.9x honest buy-down) still justifies the hardware ask; whether to
fund a denser array; whether to run the deferred +Z(990)-drive arm; anything touching the real
test proposal.

## What would make this the wrong question
- If the partner's decision does not actually hinge on the normal-Z band (then rehearse the QOI it
  does hinge on).
- If the real test would measure something structurally different from "drumhead mode shapes at N
  plate points + their frequencies" (e.g. only ODS at fixed lines) — then the simulated data model
  is wrong and must be re-scoped.
- If the truth-generation model is too kind: our synthetic truth's fine structure lives in FEM
  plate modes above the band. If the REAL drumhead error is dominated by physics entirely outside
  the FEM's shape family (the program's own shape-wall finding says this is possible), the
  rehearsal's coverage numbers are optimistic. This is the standing caveat on every synthetic
  result; stated in findings.md and on the figures.
