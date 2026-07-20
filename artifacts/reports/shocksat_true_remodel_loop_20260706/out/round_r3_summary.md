# Round 3 summary — agent track (final round; the ceiling probe)

**Question:** does MAXIMAL model-form distribution freedom separate from MAXIMAL parametric freedom?

## Scores vs A0 (0.2341); agent budget after r3 = 34/60
| cid | what | P1 | margin |
|---|---|---|---|
| c01_bb_maxsplit | bottom box 5 sub-regions (max split freedom) | 0.2202 | **−0.014** |
| c02_boxes_maxsplit | both boxes, 7 sub-regions | 0.2268 | −0.007 |
| c03_a16_drive | best-r1 splits + drive corner | 0.2373 | +0.003 |
| c04_boltstiff_a16 | connect + splits cross-family | 0.2264 | −0.008 |
| c05_ctrl_allscale | max PARAMETRIC control (9 groups) | 0.2410 | +0.007 |
| c06_tb_xface | top-box +X face split | 0.2476 | +0.014 |

## The three-round arc (the falsification, with mechanism)
1. **Round 1:** no single edit clears the noise floor; every apparent gain concentrated in the volatile
   +Z@900 fold and was MATCHED by a parametric-only control → θ-refit wobble, not model form.
2. **Round 2:** stacking the positive directions made them WORSE (interference through θ_MAP); a
   pre-designed parametric control (b05, 0.2482) statistically matched the best shape edit (a16, 0.2500).
3. **Round 3:** pushing split freedom to its maximum went NEGATIVE (c01 −0.014, c02 −0.007): more
   distribution knobs let the modal-frequency θ_MAP overfit the .ash survey at the EXPENSE of held-out FRF —
   the over-parameterization signature, and the final nail: the ceiling is not "not enough model-form
   freedom", it is that the freedom does not transfer to held-out per-channel FRF under this protocol.

**Final leaderboard (top-5):** a16 split +0.016, b05 PARAM-ONLY +0.014, c06 split +0.013, a04 thickness
+0.010, c05 PARAM-ONLY +0.007. Shape edits and parametric controls are interleaved within ±0.002 — far
inside the ±0.03–0.07 paired-fold noise. **No candidate approaches the pre-registered S1 margin (+0.05).**

## Finalists (feeding NUTS + Q/H + freeze)
Top-3 SHAPE-CHANGING agent candidates by dev P1: a16_bb_splits_combo, c06_tb_xface, a04_welds_t074.
Parametric-only candidates (b05, c05, a15, b04) are CONTROLS by design (card §5: parametric-only reported
separately) and are excluded from the finalist set; their equality with the finalists is itself the headline
finding. Reduced-basis finalists (a16, c06) require passing spot checks (D7) before the freeze.
