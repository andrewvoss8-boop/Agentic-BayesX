# Findings — plate-test rehearsal (checker verdict first; read nothing stronger)

## Checker verdict
**OVERALL RED under the pre-registered criteria — the headline claim is FALSIFIED.** S1 encoded
"A1 median >= A0 median" as RED = "no buy-down"; the result is exactly that (A1 6.20x vs A0 6.17x).
The RED is the pre-registered answer tier doing its job: it BLOCKS the "12 sensors buys 3.5x" claim
from ever being made. The pipeline itself is intact (coverage ~1.0 everywhere; 35/36 NUTS runs
converged; integrity arm clean). Falsification was accepted up front (question_framing.md, D2).

## The headline (what a partner must be told)
**The promised buy-down (normal-Z band 5.4x -> 3.5x at 12 plate sensors) does NOT survive the
actual Bayesian pipeline.** Rehearsed medians: 1 sensor 6.17x -> 12 sensors 6.20x -> 20 sensors
6.20x (pairwise by seed: mixed, no consistent improvement). The analytic design curve was NOT
arithmetic error — its recipe reproduces inside this framework (ablation L1: target sigma 0.35
gives 3.05x). It failed because it omitted two things the honest delivery must carry:

1. **The theta posterior (the dominant omission).** The analytic curve froze stiffness at
   theta_MAP. Carrying the actual +/-4% theta posterior re-mixes the NEAR-DEGENERATE drumhead
   cluster (246-258 Hz eigenvectors rotate under tiny stiffness changes), scattering every band
   mode's net-Z participation. Ablation: adding theta draws alone un-buys most of the gain
   (3.05x -> 4.93x, L2).
2. **The amplitude-error distribution.** Signed shape-mixing truth (net participations can
   partially cancel or flip sign — physically real for drumhead modes) has heavy tails a pure
   lognormal tier does not; it adds the rest (4.79x -> 5.5x, L4).

Even a PERFECT test of the 4 target modes (participations pinned absolutely) leaves ~5.1x (L6):
the width no longer lives in the 4 targets — it lives in the OTHER 8 drumhead-band modes, whose
participations also scatter under theta.

## The constructive result (the revised design — P6)
**Pinning ALL 12 drumhead-band modes (228-260 Hz) recovers the full floor: 2.81x median (L7,
range 2.0-4.0 over truths).** "Partial cancellation" is not a stable property across the theta
posterior — the 234/252 Hz "pure-cancel" modes re-mix with the net-drivers under stiffness
uncertainty, so the test must resolve the WHOLE band cluster, not the 4 nominal drivers.
Revised recommendation to carry into any hardware ask:
- Test SCOPE: identify + measure all ~12 drumhead-band modes (shapes AND frequencies), not 4.
- This is a harder identification job (denser array and/or multiple drives; the 4-target greedy
  12-sensor layout was designed for the wrong objective) — sensor count/placement must be
  re-optimized for 12-mode separability and CONFIRMED by a follow-up rehearsal with a 12-mode
  inference model before promising numbers. Do NOT promise 2.8x yet; L7 is an oracle bound.
- Honest expectation management: with the as-designed test, the realistic delivered improvement
  is the amplitude-recovery one (below), not a band-factor buy-down.

## What the as-designed test DOES buy (real but modest)
- Per-target amplitude posterior: prior sd 0.80 -> 0.58 (12 sensors; S6 YELLOW "partially
  constrained"), with posterior mean within ~0.08 log-amp of truth — the drumhead amplitudes
  become individually estimable, so the netcg pooling assumption becomes CHECKABLE (RQ3).
- Target frequencies move to the measured tier (small band effect, L3: ~3%).

## Pre-registered criteria — final (from out/checker_report.json; numbers from out/summary.json)
| # | result | status |
|---|---|---|
| S1 buy-down | A1 6.20x vs target 3.5x; >= A0 6.17x | **RED (claim falsified — the pre-registered negative answer)** |
| S2 calibration | A1 mean weighted coverage 0.998; 8/8 seeds >= 0.85 | GREEN |
| S3 convergence | 35/36 converged (A0_s6 pathological: R-hat 1.14 after retune at 0.98; excluded+reported) | YELLOW (A0 7/8), GREEN others |
| S4 integrity | A0 median 6.17x >= 4.5x — no false sharpening | GREEN |
| S5 jitter robustness | band 6.54x (> 4.2x threshold — that threshold assumed the 3.5x regime), coverage 1.0 | YELLOW (documented: threshold miscalibrated to a regime that never materialized; coverage clean) |
| S6 pooling checkable | median eta posterior sd 0.579 in (0.40, 0.60] | YELLOW (partially constrained) |

Sensitivity arms (pipeline assumption held at 0.8): truth sd 0.4 -> band 5.72x (little sharper —
non-target width dominates); truth sd 1.6 -> band ~104x but STILL COVERS (coverage 1.0) — the
pipeline degrades by widening, not by lying. (Analytic curve said 34x at 1.6; heavy tails triple it.)

## Honest limits
- SYNTHETIC truth: fine structure = FEM plate modes above the band; if the real drumhead error is
  outside the FEM shape family entirely, coverage numbers here are optimistic. The rehearsal
  certifies machinery + information content, never the real number.
- The mechanism work (decomposition, ablation L0-L7) is POST-HOC (not pre-registered), no NUTS —
  clearly labeled; the L7 2.81x is an oracle bound, not a rehearsed delivery.
- The NUTS inference model only carried the 4 target modes' shapes (as designed); a 12-mode
  inference rehearsal is the required follow-up before revising the hardware ask.
- theta_true drawn from the same L5 posterior used in delivery (theta not under test); +Y drive
  identification assumed to succeed; uniform-mass tray proxy; A0_s6 excluded (reported).
- D8 pre-campaign fix and D9 uniform retune policy are in decisions_log; checker SHA-locked
  before science and never modified (CHECKER.sha256).

## One-line
"The rehearsal falsified the 3.5x plate-test promise BEFORE the hardware ask — the analytic curve
had frozen theta and assumed lognormal amplitudes; carrying the real posterior re-mixes the
near-degenerate drumhead cluster and the buy-down vanishes (6.2x at 12 AND 20 sensors, coverage
intact) — and it found the fix: resolve ALL 12 drumhead-band modes (oracle bound 2.8x), which is
a different, harder test than the one we almost proposed." — backed by the checker; the RED is
the pre-registered claim-falsified tier, not a pipeline failure.
