# Round 1 summary — agent track (the "agent intelligence" audit trail)

**A0 bar:** dev P1 = 0.2341, folds [+X 0.323, +Z990 0.560, +Y 0.188, +Z@900 **−0.133**]. Fold-to-fold spread
is huge (SD ≈ 0.29), so per-candidate paired-fold SE is ~0.01–0.07 — the noise floor dominates everything below.

## What the scores said (16 candidates, all dev-scored; margins vs A0, paired-fold)
| rank | cid | family | P1 | margin | ≥+0.05 & ≥2·SE? |
|---|---|---|---|---|---|
| 1 | a16_bb_splits_combo | split×2 (bottom-box face+bulkhead) | 0.2500 | **+0.016** | no |
| 2 | a04_welds_t074 | thickness (welds ×0.74, t/t³) | 0.2442 | +0.010 | no |
| 3 | a02_bb_bulkband | split (bottom-box bulkhead band) | 0.2398 | +0.006 | no |
| 4 | a08_dishmount_soft | connect (dish-mount spiders) | 0.2395 | +0.005 | no |
| 5 | **a15_scale_ctrl** | **parametric-only CONTROL** | 0.2394 | +0.005 | no |
| … | (a06 bolt-stiff, a12 plate-refine, a09 tb-split ~A0) | | ~0.236 | ~0 | no |
| ↓ | a03_welds_t130 (welds ×1.30) | thickness | 0.2126 | −0.022 | no |

## Which hypotheses DIED (evidence-backed)
1. **No shape-changing edit clears the noise floor.** Best margin +0.016 (a16) vs the S1 bar +0.05, and it is
   < 2·SE (0.034). Round 1 does not produce an S1 candidate.
2. **The apparent gains are a θ-refit artifact, not model form — the decisive round-1 finding.** ALL of the
   improvement lives in the +Z@900 fold (A0's failure, −0.133): a16 +0.064, a04 +0.063, a02 +0.077 … **but the
   PARAMETRIC-ONLY control a15 improves that same fold by +0.077** — as much as any shape edit — while losing
   −0.072 on +Z990. So the volatile fold moves under a bare re-parameterization + θ re-fit; the shape edits are
   not buying model-form improvement there, they are riding the same θ wobble. This reproduces Card D / the
   standing "statistics can mask, not fix, a per-node shape defect."
3. **Weld thickness has a clear DIRECTION but small size:** thinner welds (a04, ×0.74) help (+0.010), thicker
   (a03, ×1.30) hurt (−0.022) — a real, physically-interpretable t/t³ signal, but sub-noise-floor.
4. **Joint compliance (the never-touched lever) is neutral-to-slightly-negative:** bolt_soft −0.017,
   bolt_stiff +0.003, mount_soft −0.004, dishmount +0.005. Restoring the bolted-flange DOFs did NOT unlock
   held-out FRF gains — an honest negative on the most-hyped fresh lever.
5. **True refinement is null** (a11 −0.010, a12 +0.002), consistent with V3 (mesh already converged).

## What round 2 proposes DIFFERENTLY (responding to the evidence)
- **Stack the only two positive real-model-form directions** (bottom-box distribution splits + weld-thinning)
  and push the bottom-box split finer/more-aggressively — the one place shape edits nudged above A0 — to test
  whether STACKING finally clears +0.05 / 2·SE, or confirms a ceiling.
- **Add discriminating controls to nail down finding #2:** a multi-group pure-θ arm (more θ freedom, no shape
  change) and a bottom-box modulus-scale arm — if these match the stacked shape edits, the gains are θ, not form.
- **Target the volatile +Z@900 fold's drivers** (bottom-box-dominated 190–235 Hz modes) with a bottom-box
  near-field split, rather than spreading edits over neutral regions (joints/plates/dish) that round 1 showed inert.
- **Drop the proven-inert families** from further spend: dish/mount connect, plate refine, top-box splits.
