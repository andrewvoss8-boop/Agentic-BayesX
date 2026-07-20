# Apples-to-apples held-out FRF comparison — Beck vs L5 (best previous), full 25-split MC

`code/frf_compare.py` → `out/frf_compare_summary.json`; figure `figures/fig_frf_compare.png`. Same channel splits,
same observed-only discrepancy σ, same forward/scoring machinery, **original `score.py` protocol** (score_qoi on
peak |H| + band-GRMS, as `heldout_qoi`/`mc_heldout`; plus the whole-FRF peak-weighted `frf_score`). All three methods
converge (calib_converged_frac 1.0). The only thing that differs between methods is the **forward model**.

## The headline correction (honest, verdict-relevant)
The Phase-1/D22 claim **"Beck ~2.1× sharper than L5 (773 vs 1661)" was NOT apples-to-apples** — it compared **Beck
with a peak gain** against **L5 with a whole-FRF gain**. The global units-gain is a processing choice and must be held
fixed across methods. When it is, the picture is gain-dependent, and the true Beck advantage is ~1.4×, not ~2×.

### Held-out peak |H| interval score (lower = sharper), median over 25 splits
| gain protocol | L5 | FEM | Beck | Beck sharper than L5 (/25) |
|---|---|---|---|---|
| **whole-FRF gain** (original L5 protocol) | **1992** (cov 0.90) | 2468 | 3641 (cov 0.77) | **0 / 25** |
| **peak gain** (QOI-appropriate, same for both) | 1146 (cov 0.90) | 1326 | **790** (cov 0.97) | **25 / 25** |

### Held-out band-GRMS interval score, median over 25 splits
| gain protocol | L5 | Beck | Beck sharper (/25) |
|---|---|---|---|
| whole-FRF gain | 5492 | 9871 | 0 / 25 |
| peak gain | 3015 | **2148** | 23 / 25 |

### Whole-FRF peak-weighted interval score (off-resonance included), median over 25 splits
| gain protocol | L5 | Beck | Beck sharper (/25) |
|---|---|---|---|
| whole-FRF gain | **8.69** | 9.19 | 9 / 25 |
| peak gain | **10.71** | 12.88 | 1 / 25 |

## What this means
1. **Gain matters, and the ranking flips with it.** Beck's twin is a **12-mode modal superposition** — it has no
   off-resonance floor, so a whole-FRF gain over-levels its peaks (peak cov collapses to 0.77) and L5 wins on
   everything (0/25 for Beck). With a **peak gain**, Beck's peaks are set correctly.
2. **Under a matched peak gain, Beck IS robustly sharper than L5 on the QOI** — peak |H| 790 vs 1146 (**~1.45×
   sharper, 25/25 splits**) and band-GRMS 2148 vs 3015 (**~1.40×, 23/25**), with **better coverage** (0.97 vs 0.90).
   The shape-field advantage is **real and robust**, just **~30–45%, not 2×**. The ~2× in Phase 1 was inflated by the
   gain mismatch (L5's whole-FRF gain under-levels its own peaks by ~×1.4, the D12 "+0.72 log" effect).
3. **On the whole FRF (off-resonance), L5 is better** under both gains (1/25 and 9/25 for Beck) — Beck's 12 modes
   cannot represent the broadband FRF. **Beck is a peak/QOI predictor, not a whole-FRF predictor.**
4. **What still stands from Phase 1:** inferring the shape FIELD beats FEM shapes *within* the Beck twin (both
   peak-gained, same forward: 773 vs 1252) — the shape-field **mechanism** is unaffected by this correction. What was
   overstated is the **magnitude of Beck's advantage over L5**.

## Corrected verdict (replaces the Phase-1 "2.1×")
A held-out-sensor twin that is calibrated (cov 0.97) **and ~1.4× sharper than L5 on peak |H| and band-GRMS under
apples-to-apples gain (25/25 and 23/25 splits)**, attributed to the shape-field mechanism — a real, robust, but
**modest** improvement. L5 remains better for whole-FRF (off-resonance) prediction. The win condition (calibrated +
meaningfully sharper than L5 on the QOI, robust over ≥25 splits, named mechanism) is **met**, at ~1.4× not 2×.
