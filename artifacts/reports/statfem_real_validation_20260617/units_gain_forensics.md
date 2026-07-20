# Can the units gain be pinned from physics? — forensics + the "no free knob" comparison

Andrew (2026-06-19): "can't we infer the appropriate gain from common unit conversions or info we have about the
sensors?" Short answer: **the deterministic units are already handled; the residual gain is NOT a derivable
sensor/units constant — it's basis-normalization tangled with model-form error — so it can't be fully pinned. But
fixing ONE gain per method (no free knob) is the honest comparison, and under it L5 beats Beck on every split.**

## 1. The deterministic units ARE already handled (verified)
- FEM deck is in **consistent English units**: `MAT1` densities 2.59e-4 / 7.77e-4 lbf·s²/in⁴ (= slinch/in³ for
  Al / steel), and there is **no `WTMASS`** card → mass is already slinch (lbf·s²/in), length inches, force lbf,
  time s. (`extracted/FEM/.../*.dat/*.bdf`.)
- The forward already divides accelerance by g = 386.0886 in/s² → **g/lbf** (`realfrf.fem_logmag`, `/G_IN_S2`).
- The measured H1 is g/lbf (accel in g, hammer force in lbf). So units conversion is complete on both sides.

## 2. The residual offset is NOT a clean units factor (measured at θ=1)
| quantity | value |
|---|---|
| broadband model→measured offset | **×496** (log10 2.70) |
| peak-region offset | **×789** (log10 2.90) |
| per-channel offset scatter | ×2.4 (log10 std 0.37) |
| `V_keep` column norms (basis scale) | 219 – 1490 (NOT mass-normalized) |

Decomposition:
- The **×496 broadband** part = the **inherited reduced basis normalization** (`V_keep` is not mass-normalized;
  column norms 200–1500). It is a fixed global constant but is an artifact of how the basis was built — **not
  derivable from sensor calibration or unit definitions**; you'd need the full FEM mass matrix / basis provenance.
  (It is close-ish to g=386 but not equal, with channel scatter — so not a clean textbook factor.)
- The **×789/×496 = ×1.6 peak-vs-broadband gap** and the **×2.4 channel scatter** are genuine **model-form error**
  (the FEM under-predicts peak amplitude — damping + mode-shape). 

**Conclusion:** the gain cannot be fully pinned from units/sensor info, and the whole-FRF-vs-peak gain ambiguity is a
**symptom of model-form error** (the model's curve shape is wrong), not a units problem.

## 3. The honest "no free knob" comparison (`frf_fixed_gain.py` → `out/frf_fixed_gain_summary.json`)
Fix ONE broadband units constant **per method**, calibrated **once** on a reference split's observed channels — no
per-target, per-split, or per-draw gain fitting; the residual peak bias is NOT re-centered away. 25-split medians:

| method | fixed gain | peak IS | peak cov | band IS | held-out peak BIAS |
|---|---|---|---|---|---|
| **L5** | ×445 | **1668** | 0.90 | 5139 | **×1.83 low** |
| FEM | ×500 | 2031 | 0.84 | 5778 | ×2.07 low |
| Beck | ×1470 | 2496 | 0.87 | 6422 | ×2.63 low |

- **Beck peak IS < L5 in 0/25 splits** — under a fixed (units-honest) gain, **L5 is better on every split**.
- **All three methods under-predict held-out peaks by ~1.8–2.6×** — the FEM amplitude model-form error, now visible
  as honest bias instead of being absorbed by a fitted gain.
- Beck's fixed gain (×1470) ≫ L5's (×445) because Beck unit-normalizes its 12 shapes (a different raw scale) — which
  is exactly why a free peak-gain helps Beck and a fixed/broadband gain does not.

## 4. The complete gain-protocol picture (held-out peak |H| interval score, 25-split medians)
| gain protocol | L5 | Beck | who wins | Beck sharper /25 |
|---|---|---|---|---|
| **fixed units gain (no free knob)** | **1668** | 2496 | **L5** | 0/25 |
| whole-FRF gain (per-split fit) | **1992** | 3641 | **L5** | 0/25 |
| peak gain (per-split fit to peaks) | 1146 | **790** | **Beck** | 25/25 |

**Bottom line.** Beck's shape-field twin beats L5 **only when the gain is freely re-fit to the peaks**. Under any
gain that is not peak-tuned (a fixed physics-style units gain, or a broadband gain), **L5 is at least as good and
usually better**, and every method carries a ~2× held-out peak under-prediction = the FEM amplitude model-form
ceiling. The shape-field MECHANISM (inferred > FEM shapes WITHIN the Beck twin) still holds, but **Beck's advantage
over L5 is fragile to the gain protocol and should not be reported as a robust win.** The real lever for the peak
amplitude is FEM fidelity (a refined mesh / better damping) — i.e., Card D — not the choice of likelihood or gain.
