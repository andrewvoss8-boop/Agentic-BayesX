# Card C Phase 1 — Hardened Beck-on-`.ash` mode-shape-field twin (full QOI, fair, mechanism-attributed)

> **⚠️ CORRECTION (see `apples_to_apples_frf_summary.md`, full 25-split MC).** The "~2.1× sharper than L5" headline
> below was NOT apples-to-apples: it compared **Beck (peak gain)** to **L5 (whole-FRF gain)** — different nuisance-gain
> protocols. Under a **matched** gain, Beck is **~1.4× sharper than L5** on peak |H| (790 vs 1146) and band-GRMS
> (2148 vs 3015), 25/25 and 23/25 splits, cov 0.97 — REAL and ROBUST but ~30–45%, not 2×. On the **whole FRF** L5 is
> better (Beck has only 12 modes). The shape-field **mechanism** below (inferred>FEM shapes WITHIN Beck, 773 vs 1252,
> both peak-gained) is UNAFFECTED. Read the headline number below as the (overstated) peak-vs-whole-FRF-gain contrast.


Runner session, Card C. Status light: **GREEN for the headline positive** (calibration converges; sharpening is
robust across 25 splits, survives the fairness fix, and is attributed to a named mechanism), with two **labeling
caveats** carried explicitly (split-independent calibration; the now-removed held-out-σ leak). check.py UNTOUCHED.

Artifacts: `code/modal_beck_full.py`, `code/mc_beck_full.py` → `out/mc_beck_full_summary.json`,
`out/beck_calib_nm{12,20}.npz` (cached calibrations), `out/modal_beck_full.json` (single split).
Replay: `python code/mc_beck_full.py 25` (calibration cached; resumable). Detached run = `logs/mc_beck_full.log`.

## What "interval score (IS)" means (plain English)
IS = the Winkler interval score of the 95% predictive band for a held-out quantity: it ADDS the band width to a
penalty for the truth falling outside. **Lower = better = sharp AND calibrated.** A method cannot win by inflating
its band (penalised on width) or by being too narrow (penalised on misses). "cov" = fraction of held-out channels
whose 95% band contains the measured value (target ≈0.95). "z-std" = spread of standardized residuals (≈1 =
calibrated; >1 = too narrow; <1 = conservative/wide).

## Headline result (held-out impact-channel QOI, 25 channel splits, n_modes = 12)
| twin | peak \|H\| IS (median) | peak cov | band-GRMS IS (median) | band cov |
|---|---|---|---|---|
| **L5** freq-only + QOI-disc (prior headline) | 1661 | 0.94 | 4236 | 0.97 |
| FEM shapes, const ζ (Beck baseline) | 1252 | 0.90 | 3124 | 0.87 |
| **INFER shape field + measured ζ (hardened Beck)** | **773** | **0.97** | **2079** | **0.97** |

**The hardened Beck twin is ~2.1× sharper than L5 on peak \|H\| (773 vs 1661) AND ~2.0× sharper on band-GRMS
(2079 vs 4236), while staying calibrated (coverage 0.97 vs 0.94/0.97).** This is the first arm that is BOTH
calibrated AND meaningfully sharper than L5's ×3 amplitude bands — the Card C win condition — and it survives the
fairness fix below.

## Mechanism attribution (2×2 contrast, per-split peak IS, n_modes 12 / 20)
| contrast | what it isolates | n_splits sharper /25 | IS ratio (median) |
|---|---|---|---|
| INFER_measured vs FEM_const | full effect | 25 / 25 | 0.59 / 0.52 |
| INFER_const vs FEM_const | **shape-field correction** | 24 / 25 | 0.58 / 0.50 |
| FEM_measured vs FEM_const | measured damping alone | **0 / 0** | 1.21 / 1.46 (WORSE) |
| INFER_measured vs INFER_const | damping on top of shapes | 13 / 6 | 1.00 / 1.04 (neutral) |

**The sharpening is the SHAPE-FIELD correction, full stop.** Inferring the system mode-shape field (Beck/Au/Vanik
2001, Rayleigh quotient + orthogonal `.ash`-MAC, no eigenvector gradient) carries essentially 100% of the gain.
**Measured per-mode `.ash` damping does NOT sharpen** — alone it is *worse* (the measured ζ≈0.25–1.05 % is lower
than the constant 1 %, so peaks get taller and the amplitude error grows), and neutral once the shapes are fixed.
This corroborates the Sim-B finding (D15): the held-out amplitude residual is dominated by FEM mode-SHAPE model-form
error, not damping. So the ×3 ceiling is broken by correcting the shape FIELD, not by better damping.

**More matched modes (12 → 20):** marginal. INFER_measured peak IS 773 → 760; band IS 2079 → 1910 (20 modes a bit
better on band energy). Both calibrations converge cleanly (R̂ 1.004 / 1.002, ESS 2384 / 3606, 0 divergences).

## Two honesty findings about the D22 validated headline (SURFACED to lead)
1. **Fairness fix — resolves in Beck's favor.** D22 `mc_beck.py` sized its predictive band σ from the HELD-OUT
   truth (a leak); L5 sizes σ from OBSERVED channels only. `modal_beck_full.py` uses observed-only σ (apples-to-
   apples). Net effect: the fair σ is slightly larger, but the FEM baseline also loses its peek, so the Beck-vs-FEM
   ratio is essentially unchanged (0.59 fair vs 0.63 leaky) and the Beck-vs-L5 advantage HOLDS. The concern is real
   but does not overturn the headline.
2. **Calibration is split-INDEPENDENT.** Beck's NUTS posterior over (θ, shape field φ) uses ONLY the global `.ash`
   modal survey + a fixed seed; it does not see the impact-FRF channel split (hence the identical R̂ across all D22
   splits). The 25-split MC is therefore a held-out-CHANNEL generalization test of ONE global calibration, not 25
   recalibrations. Legitimate, but must be LABELED this way (done in the output `note` field). `modal_beck_full`
   calibrates once per n_modes and reuses it.

## Assumptions / limits (new this phase)
- Measured damping ζ_eff,r = ζ_ash,r (`.ash measured_modes['damp']`, % critical → fraction) + ζ_w(f_r) (exponential-
  window-added damping, `realfrf.measured_zeta_w`). Single impact / single hit (YELLOW data caveat, inherited).
- Gain c fit on OBSERVED-channel peaks per draw (held-out never used for the gain). Same global-units-gain model as L5.
- z-std for the INFER configs is 0.64–0.88 (slightly conservative/wide), vs FEM 1.2–1.9 (too narrow on band) — the
  INFER twin is both sharper and better calibrated, not narrow-and-lucky.

## Remaining in Phase 1 (next action)
(d) Held-out-FRF figure: measured \|H1\| vs the INFER-shape-field band vs L5 vs FEM at the hard channels (tufte +
lint + image-QA per the Plot Gate). Then Phases 2–6 (spatial-kriging transfer, τ sweep, phase likelihood, `.ash`
cross-dataset, mesh re-validation).
