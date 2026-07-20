# MPL twin iteration — packet (frozen harness + (a)+(b) result)

**Status: Phase-0 harness BUILT & VALIDATED; Andrew steered (a)+(b) (D7); both run. OVERALL = YELLOW honest
result (equally valid per the card): the as-received fable rev-3 FEM is already a TRUSTWORTHY FREQUENCY twin,
and NEITHER stiffness calibration NOR richer transmissibility forms measurably improve held-out scores on this
single-axis, no-force data — the ShockSat data-ceiling, confirmed on the MPL stand.** Harness gates GREEN; the
FREQUENCY twin (F0) CONVERGED on all 5 splits; the whole-curve transmissibility twin (M0) is YELLOW
(non-converged + uncorrelated forward, by mechanism).

## What this study is
A multi-round, evidence-ranked search over FEM MODEL CLASSES to improve the MPL-stand digital twin's HELD-OUT
scores (D-A: CRPS-skill vs climatology, interval/Winkler+coverage, band-GRMS error), on the no-force observable
= gain-free output/output transmissibility |T_a(f)|=√(PSD_a/PSD_shield) (D-B), over 5 leave-one-location-out
splits (D-C). Honest negatives are an equally valid outcome.

## Phase-0 harness (all built, validated, replayable via `run_all.sh`)
| piece | status | evidence |
|---|---|---|
| `check.py` (3-tier, SHA self-locked, baseline RED) | GREEN (locked) | `check_report.json` |
| `code/score.py` byte-identical to L5 | GREEN | SHA c62c564d024e… asserted |
| `code/mpl_fem.py` parametric forward + eigensolve | GREEN | reproduces fable nominal f1..f8 to 4e-4 Hz; ref/ref |T|≡1; load-scale & input-spectrum invariance unit tests PASS |
| `code/mpl_observe.py` gain-free |T| + matching protocol | GREEN | 8/8 unit tests PASS; `observable.json` |
| `code/mpl_splits.py` 5 LOLO splits | GREEN | `splits.json` |
| `code/mpl_calibrate.py` + `mpl_baseline.py` statFEM NUTS + scoring | RUNS (YELLOW: non-converged, see finding) | `baseline_scores.json` (smoke), `class_M0.json` |

Geometry resolved: shield is a y–z panel (normal +X) ⇒ the single OOP sensor axis = the X-translation DOF.
Forward transmissibility T_a=|Σφ_a,iγ_i/D_i|/|Σφ_ref,iγ_i/D_i| (acoustic input spectrum CANCELS in the ratio;
load spatial shape f enters via γ_i=φ_iᵀf, default uniform OOP pressure on the shield). Node map + assumptions
(some ANDREW-CONFIRM-flagged) in `assumptions_ledger.md`.

## KEY FINDING (D6) — the as-received FEM transmissibility forward is UNCORRELATED with measured |T|
`figures/fig_forward_diagnostic.png`, `out/forward_diagnostic.json`:

| held-out location | log-corr(measured, FEM-nominal |T|) |
|---|---|
| interface | +0.05 |
| beam | −0.02 |
| valve | −0.01 |
| avi-L | −0.16 |
| avi-R | −0.12 |

- Robust: log-corr stays ≈0 across load shapes (uniform-shield, uniform-all) AND references (shield, interface);
  |corr| ≤ 0.35 everywhere.
- It is NOT a frequency problem: the FEM HAS modes where the measured peaks are (28 modes in 70–120 Hz, 49 in
  170–260 Hz), and the measured peaks coincide with the tap-spectra modes in `features.json`.
- Mechanism: a DENSE modal forest + an UNKNOWN diffuse acoustic load + single axis + no force ⇒ the
  transmissibility SHAPE is set by the unknown acoustic-load modal participation and the reference point's own
  antiresonances + fine mode-shape error — none of which stiffness calibration can move. This is the SAME data
  ceiling the project documented for ShockSat (per-location single-impact amplitude near-irreducible for any
  global model), now confirmed on the MPL stand with the transmissibility QOI.
- Sampler note: whole-curve magnitude NUTS is multimodal here (θ→1.8, ζ→0.15, R̂≈23–96) — the documented
  whole-FRF-magnitude multimodality, reported YELLOW per the convergence gate.

## (b) FREQUENCY headline — RAN (`freq_baseline.json`, `fig_freq_result.png`)
Matched-eigenfrequency NUTS calibration of 6 K-groups on TRAINING-location alive modes; held-out per-peak
scoring across the 5 LOLO splits. **All 5 splits CONVERGED** (R̂ 1.001–1.002, ESS ~3000, coverage 0.93).

| | mean over 5 splits |
|---|---|
| calibrated twin median per-peak \|Δf\| | **2.76 %** |
| nominal FEM median \|Δf\| | **2.47 %** |
| nearest-pooled-peak (fair climatology) \|Δf\| | **2.51 %** |
| CRPS-skill vs pooled-ensemble climatology (weak bar) | **+0.91** (coverage 0.93) |

Honest reading: the twin is well-calibrated and localizes each measured peak far better than the no-info pooled
ensemble (+0.91) — but calibration does NOT beat the nominal FEM, and neither beats the trivial nearest-pooled
peak, because a DENSE modal forest (29–71 alive modes/node) puts a mode near every measured peak. So the
frequency QOI is a WEAK discriminator here and calibration adds no held-out frequency value.

## (a) Richer transmissibility forms — RAN the decisive load-free test (`near_resonance.json`)
At a resonance the transmissibility → \|φ_a/φ_ref\| (the unknown acoustic LOAD cancels). Measured peak height vs
FEM \|φ_a/φ_ref\| at the nearest alive mode: **log-corr +0.26 (n=21)** — only a faint signal. Therefore the
transmissibility-shape residual is LOAD-INDEPENDENT mode-shape error, so the obvious richer-form lever (infer the
acoustic load as a latent / region-frequency-correlated discrepancy) provably CANNOT recover held-out shape skill
— the limiting error is the FEM mode shapes themselves, which single-axis, no-force data cannot re-infer (the
project's shape-pattern lesson). A multi-hour latent-load NUTS arm is therefore moot and was not run.

## Overall verdict (YELLOW — equally valid)
The as-received fable rev-3 FEM is a TRUSTWORTHY MPL FREQUENCY twin (converged, well-covered, ~2.5 % per-peak).
Within this single-axis, no-force dataset, NEITHER richer stiffness calibration NOR richer transmissibility/
load/discrepancy forms improve held-out scores, because (i) the dense modal forest makes frequency a weak
discriminator and (ii) the transmissibility SHAPE is limited by fine mode-shape error + unknown acoustic load,
neither calibratable here. = the ShockSat per-location-amplitude data ceiling, confirmed on the MPL stand.
**Pre-test lever that WOULD resolve it:** instrumented force (calibrated apparent mass) + multi-axis / multi-
reference mode shapes — the same data the project has repeatedly identified as the missing ingredient.

## Deck & figures
`slides/mpl_twin_findings.pptx` (13 slides) tells the story: setup → method (statFEM schematic) → the data →
Finding 1 (uncorrelated transmissibility) → why (dense modal forest) → frequency twin → load-free near-resonance
test → identifiability → registry → verdict → scope/integrity. Nine figures (all tufte-linted + image-QA pass):
`fig_geometry`, `fig_graphical_model`, `fig_measured_transmissibility`, `fig_forward_diagnostic`,
`fig_modal_forest`, `fig_freq_result`, `fig_near_resonance`, `fig_strain_energy`, `fig_registry`.

## Replay
`bash run_all.sh` (Phase-0 harness, BLAS-pinned). FREQUENCY headline: `.venv_nuts/bin/python code/mpl_freq_baseline.py`
(~37 s, converges). Diagnostics: `code/near_resonance_test.py`, `code/fig_forward_diagnostic.py`,
`code/fig_freq_registry.py`. The whole-curve transmissibility calibration (`mpl_baseline.py`) stays SMOKE/
non-converged by design (D6: uncorrelated forward).
