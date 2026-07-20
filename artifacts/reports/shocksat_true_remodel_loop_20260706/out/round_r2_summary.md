# Round 2 summary — agent track

**Design:** stack the two positive round-1 directions (bottom-box splits + weld-thinning), push each harder,
add two DISCRIMINATING parametric-only controls (b04 bottom-box scale, b05 multi-group scale), target the
volatile +Z@900 fold (b11 drive-corner split). 12 candidates, all dev-scored (agent budget now 28/60).

## Scores vs A0 (0.2341)
| cid | what | P1 | margin |
|---|---|---|---|
| b11_bb_drivecorner | split @ drive corner | 0.2408 | +0.007 |
| b12_bb3band_weld | bb 3-band + steel-weld thin | 0.2407 | +0.007 |
| **b05_ctrl_multiscale** | **PARAMETRIC-ONLY control** | **0.2482** | **+0.014** |
| b04_ctrl_bb_scale | parametric control (bb only) | 0.2347 | +0.001 |
| b06/b07/b09 weld curve | ×0.60/×0.85/Al-only | 0.233–0.236 | ~0 |
| b01_stack_bb_weld | the round-1 winners STACKED | 0.2235 | −0.011 |
| b10/b08 steel-weld stacks | | 0.209–0.212 | −0.02 |

## What died / what this establishes
1. **Stacking FAILED to compound.** a16 (+0.016) + a04 (+0.010) stacked = b01 (−0.011). The positive
   directions interfere through the θ_MAP re-fit rather than adding — classic signature of noise-riding, not
   of two independent model-form corrections.
2. **The discriminating control is decisive: b05 (parametric-only, multi-group) = 0.2482 ≈ a16 = 0.2500**
   (difference 0.002, noise floor ~0.03-0.07). The best shape-changing candidate is statistically
   INDISTINGUISHABLE from pure stiffness-multiplier freedom. Round-1 finding #2 is now confirmed by a
   pre-designed control, not just post-hoc reading.
3. **Weld-thickness curve is flat** (×0.60/0.74/0.85, steel-only, Al-only all within ±0.01 of A0): the
   round-1 "direction signal" does not sharpen into a usable lever.
4. Best round-2 fold-3 fix: b11 drive-corner split (−0.038 vs A0's −0.133) — but its global margin (+0.007)
   is still noise.

## Round 3 (final): the ceiling probe
The remaining honest question is not "which edit wins" (none has) but "does ANY amount of model-form
distribution freedom clear the floor where parametric freedom cannot?" Round 3 therefore: (i) maximal
split freedom (both boxes, 5-7 sub-regions) vs (ii) maximal parametric freedom (all-group scale control) —
if (i) ≈ (ii) ≈ A0, the family ceiling under this protocol is established and S1 is falsified with a clean
mechanism; plus the two best cross-family combos not yet tried (bolt_stiff+splits, splits+gentle-weld).
