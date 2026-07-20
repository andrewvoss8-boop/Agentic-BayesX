# Runner prompt — 12-MODE plate-test rehearsal (follow-up to plate_test_rehearsal_20260701)

Approved by Andrew 2026-07-02 ("both"). Self-contained; a fresh agent executes autonomously.
Re-ground first: read `AGENTS.md` (ALL gates), this card, then the parent workspace
`artifacts/reports/plate_test_rehearsal_20260701/` (findings.md, decisions_log.md D1-D9, code/).

## Question (one line)
Can a plate test that identifies + measures ALL ~12 drumhead-band modes (228-260 Hz) actually
deliver a normal-Z band near the 2.81x ORACLE bound (parent L7) through the full joint-NUTS
pipeline — and what sensor count / placement / drive set does that identification require?

## Context you must not re-derive wrong
- Parent rehearsal FALSIFIED the 4-target 3.5x promise (12 sensors -> 6.2x; checker RED =
  pre-registered claim-falsified tier). Mechanism: the +/-4% theta posterior rotates the
  near-degenerate drumhead cluster; only pinning ALL 12 band modes recovers ~2.8x (oracle).
- Parent machinery to reuse: `code/rehearsal.py` (Setup, truth generator, joint NUTS, delivery,
  tier constants), netcg reduced FEM via `netcg_qoi`, D8 prior/tier-consistency convention
  (prior-only band must reproduce ~5.8x), D9 uniform retune policy.

## Design (differences from parent — everything else inherited)
1. INFERENCE extends to ALL 12 basis modes: c becomes (12 x n_basis_inf) with the same
   kappa-scaled prior; observations = shape samples for every IDENTIFIED band mode + its
   frequency (measured tier).
2. IDENTIFICATION IS NOT FREE (the parent assumed it; this run must model it): a band mode
   counts as identified for a given {array, drive set} only if it passes a stated separability
   criterion (e.g. sensor-sampled MAC distinguishability / min-eig threshold of the sensed
   subspace — state and justify the criterion, Modal Identifiability Gate). Unidentified modes
   stay at the unmeasured tier. Report which modes each arm identifies.
3. Arms (>= these; seeds >= 6 each): (a) parent 12-sensor greedy array (shows its 12-mode
   identification shortfall); (b) array re-optimized for 12-mode separability, n in {16, 24};
   (c) best array + TWO drives (+Y and +Z990) if single-drive identification falls short;
   (d) placement jitter on the best arm. Sensitivity: truth sigma {0.4, 1.6} at 2 seeds.
4. Truth generator: parent's (signed mixture + out-of-basis fine structure) — unchanged, so
   results are directly comparable.

## Pre-registered criteria (encode in check.py; SHA-lock BEFORE science; falsification accepted)
- R1 headline: best-arm median band factor <= 3.5x (GREEN) / < parent 6.2x (YELLOW w/ number) /
  >= 6.2x (RED = the 12-mode route also fails; report as the decisive negative).
- R2 calibration: mean energy-wtd 1-oct coverage >= 0.90 (GREEN) / >= 0.80 (YELLOW) / else RED.
- R3 convergence gate per AGENTS (all variables; retune policy = parent D9).
- R4 identification honesty: an arm may NOT claim a mode it fails the separability criterion for;
  checker verifies the identified-mode list drives the tier assignment.
- R5 integrity: parent 12-sensor array under the 12-mode model must NOT beat re-optimized arrays
  while identifying fewer modes (else the identification model is leaking).
- Deliverable either way: the sensor/drive spec a hardware ask could quote, WITH its rehearsed
  band number and caveats — or the honest "12-mode route fails too" negative.

## Guardrails (identical to parent)
Own workspace `artifacts/reports/plate_test_rehearsal12_<date>/` only; no durable-rule /
checker / other-workspace edits; NUTS default + convergence gate; detached resumable compute,
threads pinned; Tufte-linted figures incl. an updated buy-down money figure overlaying parent
arms; packet + findings numbers never stronger than checker output; runs.md + project_log row
copied from checker; update the lead via decisions_log, not chat-only.

## STATUS NOTE (2026-07-02, lead): PARKED, and RENAME on dispatch
Andrew reprioritized: the next experiment is the composite remodel/Beck/discrepancy bake-off (see
notes/memory.md CURRENT STATE). This card stays queued for the pre-hardware-ask phase. On dispatch,
rename to "full-cluster rehearsal": the 12 modes = ALL modes in the 228-260 Hz drumhead band (the
complete cluster in the reduced model), NOT a cap — the parent's failure was representing only 4.
Principle to preserve: limited data, never limited modes.
