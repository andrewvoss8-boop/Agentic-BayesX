# Card C Phases 2–6 — spatial kriging, τ sweep, phase likelihood, cross-dataset, mesh re-validation

Runner session, Card C, continued from Phase 1. All study artifacts; `check.py` UNTOUCHED (immutable); checker still
YELLOW (no regression). Replay commands in each section. "IS" = Winkler interval score of the 95% predictive band
(lower = sharper-AND-calibrated). "cov" → target ≈0.95; "z-std" → ≈1 calibrated, >1 too narrow, <1 conservative/wide.

## Phase 2 — Spatial-kriging held-out discrepancy (the deferred Schneider freq×space transfer)
`code/beck_kriging.py` → `out/mc_beck_kriging_summary.json` (25 splits, fixed Beck calibration). Replaces the
*marginal* (independent) held-out discrepancy with the GP-CONDITIONAL transfer: condition each held-out channel's
discrepancy field on the OBSERVED channels' residual via σ_d²(C_f⊗C_z)+σ_meas²I (C_f = SE over log-Hz, C_z = exp over
3-D sensor distance, length `len_z` swept).

| transfer | len_z | peak IS | peak cov | peak z-std | kriged sharper | band IS |
|---|---|---|---|---|---|---|
| marginal (per-freq, σ_d≈2.0) | — | 6568 | 1.00 | 0.08 | — | 17887 |
| **kriged** | 12 in | **3468** | 0.84 | 1.41 | **25/25** | 13205 |
| **kriged** | 60 in | **3183** | 0.81 | 1.56 | **25/25** | 12740 |

**Finding (nuanced, honest):** the correlated spatial transfer **is informative** — it ~halves the held-out interval
score vs the per-frequency marginal (25/25 splits), and more spatial correlation (larger len_z) sharpens further.
So the Schneider freq×space mechanism works spatially on the real data. **BUT** it costs calibration (coverage 1.00→
0.81–0.84, z-std 0.08→1.4–1.6: the conditional mean transfers a partly-wrong correction at the impact-face hard
channels), AND — the key caveat — **neither per-frequency transfer beats the Phase-1 QOI-LEVEL discrepancy** (peak IS
**773**). Reason: the per-frequency log-mag residual scale σ_d≈2.0 is inflated by peak-FREQUENCY-misalignment spikes
(the whole-FRF pathology, D7), so any per-frequency discrepancy is far wider than applying the discrepancy directly at
the QOI level. **Verdict:** for this coarse FEM, apply the model-form discrepancy at the QOI level (Phase 1); spatial
kriging is a real but secondary improvement over a per-frequency marginal, not over the QOI-level treatment.

## Phase 3 — Quality threshold τ as a swept variable (Andrew D9)
`code/tau_sweep.py` → `out/tau_sweep_summary.json` (hardened Beck INFER_measured, 25 splits). τ = which `.ash`↔FEM
matched modes to keep, by MAC quality.

| τ | modes | MAC≥ | peak IS | peak cov | band IS | band cov |
|---|---|---|---|---|---|---|
| **full20** | 20 | 0.34 | **797** | 0.97 | 2173 | 0.94 |
| mac≥0.5 | 17 | 0.51 | 809 | 0.97 | **2059** | 0.97 |
| mac≥0.7 | 10 | 0.70 | 842 | 0.97 | 2207 | 0.97 |
| top6 | 6 | 0.88 | 1021 | 0.97 | 2830 | 0.97 |

**Finding:** the held-out proper score is **maximized by keeping the full matched-mode set** (peak IS 797), or a light
MAC≥0.5 cut for slightly better band calibration. Aggressively quality-thresholding to only the 6 highest-MAC modes
**worsens** sharpness (peak IS 797→1021, band 2173→2830). Coverage stays ≈0.97 at every τ — restricting modes does
not break calibration, it just discards information and widens. **Pre-test answer:** trust the full MAC-matched mode
set; do not over-restrict to the cleanest few modes.

## Phase 4 — Complex / phase likelihood (L4, Fathi/Zhang Eq 20)
`code/phase_likelihood.py` → `out/phase_likelihood.json` (diagnostic; avoids another multimodal whole-FRF NUTS, the
magnitude version being the documented dead end D7). On the observed channels: (1) phase coherence at the matched
modes = circular variance of [∠Ĥ − ∠H_model] across channels; (2) a 1-D θ-slice NLL for magnitude-only vs complex.

- **Phase circular variance at modes = 0.85** (≈1 = uniform/incoherent): the single-impact measured-vs-model phase is
  largely incoherent across channels — single-hit timing + window + noise, exactly the card's caveat.
- **Complex θ-slice is NOT sharper** than magnitude (rel-contrast 0.00 vs 0.01) — adding phase does not sharpen the
  stiffness minimum.
- **Verdict:** phase adds nothing over magnitude here; magnitude/modal likelihoods retained. (Documented negative.)

## Phase 5 — `.ash` modal survey as a cross-dataset observable
`code/cross_dataset.py` → `out/cross_dataset_summary.json` (25 splits, one common FEM-shape modal-superposition
forward; only the θ/shape calibration SOURCE varies). Calibrate on the INDEPENDENT `.ash` survey, predict the
impact-hammer held-out FRF QOI.

| calibration source | converged | peak IS | peak cov | band IS |
|---|---|---|---|---|
| nominal (θ=1) | yes | 1509 | 0.90 | 3700 |
| `.ash` freq-only | yes (R̂ 1.002) | 1502 | 0.94 | 3680 |
| `.ash` freq+MAC | borderline (R̂ 1.008) | 1501 | 0.90 | 3643 |
| **`.ash` Beck shape-field (inferred)** | yes (R̂ 1.004) | **858** | 0.94 | **2381** |
| L5 (impact-FRF freq) reference | yes | 1661 | 0.94 | 4236 |

**Finding:** the `.ash` survey is a **valid independent calibration source** — `.ash` freq-only θ converges and
predicts the impact-hammer held-out FRF about as well as the impact-FRF-derived L5 (peak IS ~1500 vs 1661), so the two
datasets are consistent. **But** stiffness-θ calibration from *any* modal source (`.ash` or impact-FRF, freq or
freq+MAC) barely moves the held-out amplitude (all ≈1500–1660 ≈ nominal 1509). The amplitude lever is the **shape
field** (Beck, 858), independent of dataset — corroborating the whole study (L6/L10/Sim-B).

## Phase 6 — Re-validate on Card D's refined mesh — BLOCKED (external dependency)
`code/phase6_revalidate.py` → `out/phase6_status.json` = **BLOCKED**. Card D
(`artifacts/reports/shocksat_fem_remesh_20260618`) has so far produced only `region_diagnosis.json`; no refined-mesh
reduced FEM is available. The re-validation harness is written and ready (detects the deliverable, then re-runs L5 +
mc_beck_full + the hard-channel before/after IS table). No numbers fabricated.

## One-line cross-phase synthesis
The hardened Beck **shape-field** twin (Phase 1, peak IS 773 / band 2079, calibrated) is the headline. Every other
phase points the same way: the held-out amplitude is gated by the FEM **mode-shape field**, not by damping (Phase 1),
not by which modal dataset calibrates stiffness (Phase 5), not by phase information (Phase 4); keep the full matched
mode set (Phase 3); and the model-form discrepancy is best applied at the **QOI level** — spatial kriging helps vs a
per-frequency marginal but cannot overcome the peak-misalignment that inflates the per-frequency residual (Phase 2).
The remaining ceiling is FEM mesh fidelity in the hard impact-face regions → Phase 6 (Card D) is the right next lever.
