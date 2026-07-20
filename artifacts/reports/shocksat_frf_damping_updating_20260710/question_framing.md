# Question Framing (pre-registered) — ShockSat FRF-Domain Damping Updating (20260710)

Locked before any dev score. SHA-referenced by `check.py`. Any change after the first dev score is an
integrity violation.

## The ONE falsifiable question
Can an FRF-DOMAIN agentic updating loop — that (a) SELECTS updating bands and ALIGNS the score by FDAC
(frequency-shift-aware), (b) has a DAMPING action space (band modal damping / Rayleigh / per-joint loss
factor) alongside the proven shape/stiffness edits, and (c) refines θ AND damping on FRF residuals over the
FDAC-selected bands — improve the inherited ShockSat FEM's held-out per-sensor FRF AMPLITUDE prediction beyond
the modal-only baseline, beyond the completed run's shape-only result, and beyond an equal-budget random
comparator, confirmed on the vault — AND is any improvement ATTRIBUTABLE to the DAMPING family (not shape)?

A clean falsification is a VALID, REPORTABLE outcome ("pre-registered claim falsified"), never a pipeline
failure.

## Engineering decision supported
Whether to (i) keep the inherited NASA-correlated ShockSat twin, (ii) replace it with a damping-and/or-shape-
updated twin, or (iii) buy more data (>200 Hz, multi-reference) because the residual is sensor-unobservable.
The run informs this decision; the replace/keep/buy call is human (surfaced in the packet).

## Objective / success metric
Primary P1′ = FDAC-aligned FRAC (median over usable channels, FDAC-selected band, 45–260 Hz, fold-averaged).
Higher is better. Secondary P2′ = FRSF amplitude error |FRSF−1| (lower better). Comparability P3 = raw log|H|
correlation (the completed run's metric). Q = net-CG statFEM F(k) coverage/sharpness (finalists).

## What the agent/search is allowed to choose
The candidate edit specs (damping-family parameters: band ζ, Rayleigh α/β, per-joint η; and shape/stiffness/
connectivity edits) and which diagnosed residual hotspot / FDAC band each targets; how spend shifts across
rounds. It may NOT choose: the metrics, the folds, the vault, the budgets, the physical-damping bounds, or any
per-channel/per-mode amplitude or damping knob.

## What remains human judgment
Replace/keep/buy-data decision; whether a falsification changes the program direction; venue/reporting.

## What would make this the WRONG question
If Gate O shows the A0 residual lives predominantly in the sensor-UNOBSERVABLE subspace, then "can updating
improve held-out FRF" is data-limited, not model-limited — no action space (damping or shape) can fix it, and
the right question becomes "what test buys the observability". Gate O is run FIRST and bounds every S1/S4 claim.

## Arms/tracks (all reported, none dropped)
- **A0** modal-only baseline: inherited FEM, multi-start modal-θ_MAP, FIXED ζ=1% (exact-basis). The bar.
- **A0d** damping-updated baseline: inherited FEM (no shape edit) + DAMPING action space fit on train,
  FRF-domain refined. The reference the agent must EXCEED to claim shape value.
- **A1** agent track: closed FRF-domain loop, ≥3 rounds, ≤60 dev queries, action space = damping + shape/
  stiffness + connectivity, FDAC-aligned selection.
- **A2** random track: uniform random from the SAME action space (incl. damping), same budget/scoring, seed
  20260710, no diagnosis/learning.
- Reference bars: inherited uncalibrated (θ=1, ζ=1%); FEM+6 dB (QOI leg); the completed run's shape-only
  winner (a04/a16 exact-basis, ζ=1%) as a labeled prior-result bar.

## Success criteria (pre-registered thresholds — grade honestly)
- **S1 improvement.** Agent-track winner beats A0 on dev P1′ by ≥ +0.05 absolute AND margin ≥ 2× fold SE AND
  vault P1′(winner) > vault P1′(A0). Threshold +0.05 kept from the completed run for continuity (see D5; NOT
  tightened — no fold-SE evidence yet; any tightening would be re-registered here dated before the first dev
  score with the fold-SE evidence).
- **S2 intelligence.** Agent-track winner's dev P1′ > random-track best's (equal budget, same action space).
- **S3 honesty.** Finalists pass H (leave-modes-out widen > 1.0; **physical-damping gate** ζ∈[0.2%,5%], joint
  η≤0.2 — a "win" needing damping outside these is DISQUALIFIED as an amplitude-fit in disguise) AND
  Q-coverage (net-CG shear+normal F(k) coverage ≥ 0.95, energy-weighted exceedance ≤ 0.5 dB).
- **S4 attribution (the real question).** Any S1 improvement is ATTRIBUTABLE to the DAMPING family via
  ablation: damping-only candidates (A0d + agent damping-only) must account for ≥ 2/3 of the winner's P1′
  margin over A0; else headline = "improvement is shape/θ, damping lever unproven"; if nothing improves,
  "no lever cleared the floor". Report the shape-only / damping-only / both decomposition.
- **Overall.** Anything less than S1+S2+S3+S4 = pre-registered claim FALSIFIED (YELLOW/RED, loudly labeled).

## Noise-floor rule (carried from completed run)
Single-fold numbers are never reportable; a claimed margin must be fold-averaged AND exceed 2× the fold-to-fold
standard error. The completed run measured ±0.04–0.08 fold noise on raw P1; P1′ may lower it (quantified, not
assumed).

## Data counts
TRAIN: 33-mode .ash survey (every fold) + the fold's 3 in-fold drives. DEV: 4 leave-one-drive-out folds over
{+X/990x, +Z/990z, +Y/990y, +Z@900z}, ~111 channels/drive, 105 freq lines 45–260 Hz. VAULT: +XY/Test04, one
grade. OFF-LIMITS: the 3.33 GB force-level sweep and pyro data.
