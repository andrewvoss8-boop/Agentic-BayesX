# ShockSat FEM updating packet — mods, FRF comparisons, and Bayesian updating

Workspace: `artifacts/reports/shocksat_psd_envelope_twin_20260623/`. Reference: +X modal hammer (Test01, node 990,
6 hits), 45–260 Hz, 84 good accelerometer channels. All numbers from the cited `out/*.json`; figures are linted
(tufte-data-graphics) and visually QA'd. Deterministic comparisons use **physics modal participations (φ_s·φ_d) +
ONE global units-gain, NO per-channel fit** ("straight up"). NUTS results report all-variable convergence.

## 1. Executive summary (honest)
- **The FEM gets natural FREQUENCIES about right and mode SHAPES partly wrong.** Updating that corrects frequencies +
  damping (+ a top-mass mass correction) measurably improves the FRFs, but the **per-channel mid-band (70–196 Hz)
  mode-shape error is a hard wall** that no model-form change we tried brings to a tight match.
- **Two real, defensible wins:** (1) **modal-frequency** updating (held-out freq error 3.33%→2.68%, converged NUTS);
  (2) a **model-form correction — the FEM's top mass (aluminum section + dish) is too heavy** (lightening it is the
  single best FRF-correlation edit). 
- **The deliverable that does NOT work** on this structure: a tight per-point response-PSD band / spec — because it
  requires per-channel mode-shape fidelity the model can't reach. (Quantified across 7 levers, §2.)

## 2. The mods that were made (model-form campaign)
Scored on all-data FRF log|H| correlation (median over 84 channels; baseline = 0.296) + .ash MAC. Full data in
`out/modelform_sweep.json`, `out/edits/*/correlate.json`.

| lever | best edit | FRF corr | note |
|---|---|---|---|
| baseline (as-received FEM) | — | 0.296 | reference |
| **mass distribution (NEW)** | **al_rho_lo: lighten aluminum top ρ×0.8** | **0.379** | best overall — "top mass too heavy" |
| mass distribution | dish_mass_lo: lighten dish ×0.6 | 0.365 | corroborates top-mass |
| shell modulus | bottombox_E_lo: soften steel ×0.85 | 0.359 | |
| material E | al_stiff: aluminum E ×1.25 | 0.349 | |
| combined winners | lighten aluminum + dish | 0.245 | corrections do NOT stack |
| cross connectivity | cross_bolt / cross_weld (couple 68 coincident pairs) | 0.31 | lowers global MAC |
| joint stiffness | directional 6-term PBUSH (rot/trans soft/stiff) | 0.21–0.30 | mostly hurts |
| map-guided | bottom softening ×0.7/×0.55 | 0.33 | worse than blind ×0.85 |
| rigid-link flexibility (NEW) | strut RBE2 release, swept | MAC trade-off | low3 MAC 0.52→0.66 but global MAC↓, spurious low modes |
| damping | full per-mode measured ζ | — | sets peak heights; doesn't fix shapes |

**Read:** every lever plateaus at FRF corr ≤ ~0.38. The one robust positive is the **top-mass correction** (lighten
the aluminum top/dish). New capabilities built for this: region **mass/density scaling** (`build_M` mass_scale) and
**RBE2 flexibilization** (rebuild the constraint operator T with rigid struts released → finite springs; validated to
reproduce the baseline T exactly). The 54 Hz "fundamental gap" I initially flagged was a metric artifact (operating-
deflection-shape at one bin); the proper .ash modal MAC of the fundamental is 0.97 — corrected.

## 3. FRF comparisons — original FEM vs data vs updated FEM
**Figure: `figures/frf_comparison_grid.png`** (12 channels spanning the agreement; `out/frf_comparison.json`).
- "Original FEM" = FEM frequencies + nominal 1% damping. "Updated FEM" = **measured frequencies + measured per-mode
  damping** (the validated calibration), same shapes/gain.
- **Median log|H| correlation 0.269 → 0.338; 70% of channels improve.** The update **aligns the peaks** (frequency)
  and **sets the peak heights** (damping). The residual per-channel **shape** error remains (e.g. ch63/ch104) — the
  documented wall. Supporting diagnostics: `figures/residual_map.png` (where/which-modes), `figures/local_frf_overlay.png`.

## 4. Bayesian updating on the updated FEM (best available)
**`out/bayes_update.json`** — modal-feature NUTS (Kiran Eq-25 eigenvalue likelihood), 9 stiffness groups θ calibrated
from the POOLED clean multi-reference modal frequencies; held-out-mode validation (leave 20% of matched modes out).
- **Converged (gate-passing): R-hat 1.002, min ESS 2243, 0 divergences, 4 chains.**
- **Held-out modal-frequency coverage 0.75**; held-out frequency error **3.33% (nominal) → 2.68% (calibrated)**.
- θ posterior (2.5/50/97.5%): identifiable groups tighten (e.g. top_box 0.95/1.03/1.10, plates 0.93/1.00/1.05);
  others stay prior-wide (steel_welds 0.63/1.02/1.69 — not identifiable from frequencies; cf. strain-energy dilution).
- (Per-channel amplitude/PSD updating was tried extensively and adds no skill over the FEM — see §5 / prior cards.)

## 5. What does NOT work, and why (the wall — quantified)
Per-point response-FRF/PSD **amplitude** at a sensor is the interference of a dense mode set; small per-mode local-
shape errors compound. Confirmed irreducible across: clean multi-reference data, full damping freedom, parameter /
cross-connectivity / map-guided / **mass-distribution** / **rigid-link** remeshing, and at the integrated/band/held-
out-mean level. The frequency-shift (FDAC) check shows the residual is amplitude (not frequency); modal-overlap is low
(MOF<1, so it is NOT a statistical/SEA regime) — it is genuine per-channel shape-fidelity error. The only untried
model-form lever is a **from-scratch CAD re-mesh** (major effort; the model is already vendor-correlated — a gamble).

## 6. Bottom line for use
- Use the updated FEM as a **frequency + damping** twin (validated, converged) and apply the **top-mass correction**.
- Do **not** rely on it for a tight per-point amplitude spec; that needs either a higher-fidelity remodel or a
  **different QOI** — the interface **apparent-mass / 7004C** quantity (integrated, coupled-DOF), which *sidesteps*
  the per-channel shape wall and is the recommended next study.

## Files
Figures: `figures/{frf_comparison_grid, residual_map, local_frf_overlay, heldout_psd_examples, usable_mean_spec}.png`.
Results: `out/{frf_comparison, bayes_update, modelform_sweep, residual_map, diag_reframe, usable_mean, heldout_mean}.json`,
`out/edits/*/correlate.json`. Code: `code/*.py` (reused L5/Card-G toolkit byte-identical + new model-form levers).
Decisions/provenance: `decisions_log.md` (D0–D19).
