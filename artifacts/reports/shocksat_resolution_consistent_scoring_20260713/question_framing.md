# Question Framing — PRE-REGISTERED (written before any science; SHA-locked checker enforces)

## The ONE falsifiable question (card §0, verbatim intent)
If the model FRF is processed RESOLUTION-CONSISTENTLY — through the SAME FFT frame/window as the measured
caches — does the physically-correct light damping (survey/ERA ~0.3%) improve the inherited ShockSat FEM's
held-out per-sensor FRF prediction over the incumbent convention (naive model FRF + ζ=1%), and is any gain
attributable to the WINDOW-MATCHING, the PHYSICAL DAMPING, or only their combination?

## Engineering decision supported
Whether ShockSat FRF-correlation work should adopt resolution-consistent scoring (process model like
measurement) + measured physical damping as the standard convention, versus keeping the naive-model + flat-1%
convention. Replace/keep is Andrew's decision; this run supplies the evidence.

## Pre-registered honest expectation (stated before scoring)
Window-matching + physical ζ should roughly RECOVER the A0 convention's score (in-sample scratch: 0.229 naive
→ 0.238 windowed vs 0.244 A0-1%), because A0's flat 1% already approximates the frame-equivalent apparent
damping. A real WIN requires the window model's frequency-DEPENDENT apparent damping (~1.6% @ 60 Hz → ~0.4% @
250 Hz for the exponential window, ζ_w(f)=1/(2πfτ), τ=0.1641 s) to capture what a flat 1% misses. Whether
that is worth anything held-out is the open question. My prior: S3 passes, S1 is a coin flip leaning fail.

## Data protocol (card §3.1, fixed)
- **DEV (grading only):** 4 leave-one-drive-out folds over m_xpos_990x (+X), m_zpos_990z (+Z), m_ypos_990y
  (+Y), m_zpos_900z (+Z@900). NO search loop; the arm set is FIXED a priori. Per-fold numbers reported;
  margins fold-averaged; S1 requires ≥ 2×fold-SE.
- **VAULT (confirmation, touched once):** m_xy_990xy (+XY/Test04), read ONLY after `VAULT_FREEZE.sha256`
  exists. **HONEST LABEL: this is the SECOND program read of this cache** (damping run graded it 2026-07-10).
  Mitigation: zero search — arms fixed by the card before any score; vault is pure confirmation.
- **Damping leakage rule:** PRIMARY physical damping = the .ash survey per-mode ζ (train-side in every fold —
  the survey is independent of all drive caches). ERA ζ (derived from Test07 = the +X drive's raw records) is
  VALIDATION + band fallback; any ERA arm carries a labeled caveat on the +X fold. ERA↔survey agreement is
  itself a reported result.
- OFF-LIMITS: force-level sweep, pyro data, further drive re-downloads.

## Arms (ALL fixed a priori; none added or dropped after the first score)
| arm | forward FRF | damping | role |
|---|---|---|---|
| B0 | naive (analytic modal FRF on cache grid) | flat ζ=1% | incumbent = damping run's A0_enr; must reproduce dev P1′ 0.1969 (Gate R) |
| B1 | naive | physical per-mode survey ζ (~0.3%, freq-interpolated) | control (expected worst) |
| B2 | window-matched | physical per-mode survey ζ | THE CLAIM |
| B3 | window-matched | flat ζ=1% | ablation: window alone |
| B4 | window-matched | ERA 4-band ζ [0.099, 0.301, 0.542, 0.236]% | validation (labeled +X caveat) |
| B5 | as B2 on `c06_tb_xface_enr` | physical survey ζ | does resolution-consistency change the SHAPE-edit conclusion? |

Package for B0–B4 = `A0_enr` (exact-basis A0). All damping is FIXED measured data or the pre-registered 1%
convention — nothing fit. θ = the package's reused multi-start θ_MAP. One global gain/fold (train-side),
exactly as the damping run's scorer.

## Metrics (quantity_contracts.md; P1′/P2′/P3 reused verbatim from the damping run + P4 added)
P1′ = FDAC-aligned FRAC (primary, higher better); P2′ = |FRSF−1| at matched peaks (lower better); P3 = raw
log|H| correlation; **P4 (new) = median |Δpeak height| in dB at FDAC-aligned matched peaks** (window
consistency's first-order effect is peak height/width).

## Success criteria (PRE-REGISTERED; grading thresholds immutable after checker lock)
- **S1 (resolution-consistency wins):** dev P1′(B2) − P1′(B0) ≥ +0.03 absolute AND ≥ 2×fold-SE of the
  difference, AND vault P1′(B2) > vault P1′(B0).
  *Threshold justification (pre-registered): +0.03 not +0.05 because this is a fixed 2-arm comparison with
  zero search — no winner's-curse inflation to guard against (the damping run's +0.05 guarded a 60-query
  search). The 2×fold-SE requirement carries the 2026-07-06 metric-noise-floor rule unchanged.*
- **S2 (attribution):** decompose Δ = P1′(B2)−P1′(B0) into window-alone (B3−B0), damping-alone (B1−B0),
  interaction (B2−B1−B3+B0). The claim "consistent processing lets physical damping be used correctly"
  requires (interaction + damping-alone) ≥ ½·Δ when S1 passes. If window-alone dominates: report "it's the
  window; damping still moot" honestly.
- **S3 (mechanism confirmed, graded independently of S1):** dev P1′(B2) ≥ dev P1′(B1) + 0.02 AND Gate W
  passes. If S1 fails but S3 passes, headline = "mechanism confirmed, no held-out advantage over the 1%
  convention" — a publishable close-out.
- Anything less than S1+S2 = pre-registered claim FALSIFIED (YELLOW, loudly labeled). S3 graded separately.

## What the run may choose vs what stays human
- Runner chooses: implementation details of the window operator (must pass Gates W+K), figure design,
  diagnostics. Runner may NOT add/drop arms, change thresholds, refit damping, or touch the vault twice.
- Human (Andrew): replace/keep the scoring convention; any Bayesian/NUTS follow-up; MPL vs re-distillation next.

## What would make this the wrong question
- If Gate W fails outright (the recovered window model cannot reproduce the measured processing even
  qualitatively), the window operator is wrong and B2–B5 are meaningless → report Gate W failure as the
  result; do NOT interpret arm scores.
- If the caches' binding limitation is not resolution but something else (e.g. channel coherence), the S2
  decomposition will show ~zero window effect — that IS the answer, reported as such.
- If Test01-vs-Test07 drive repeatability is so poor that no processing comparison is meaningful, Gate W's
  labeled fallback documents it and the study degrades to Gate-K-verified (synthetic) consistency + arm scores
  with a widened caveat.

## Sampler statement (AGENTS Sampler Decision rule)
NO-SAMPLER study: every arm is deterministic (fixed pre-registered damping + reused θ_MAP). No NUTS leg is
required or claimed; nothing here is presented as Bayesian inference. Prototype/legacy labels not applicable —
no sampling occurs.
