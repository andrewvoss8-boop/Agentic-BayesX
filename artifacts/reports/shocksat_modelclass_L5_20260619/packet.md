# Packet — Calibrated ShockSat L5 twin: where model updating has value, and where it doesn't

**One-line result:** the calibrated L5 twin has **real, demonstrable value for modal FREQUENCIES** (positive
held-out skill vs a no-skill baseline; calibration ~halves the as-received FEM frequency error). For per-channel
single-impact AMPLITUDE it is honestly calibrated but does **not yet beat climatology** — though the **strongest
lever IS a model-form change: inferring the mode-shape FIELD (Beck/L8b) halves the CRPS-skill deficit (−0.68→−0.25)
and sharpens the held-out interval ~43% (coverage→0.97)**. So amplitude is *improved-not-solved* on one impact (a
real partial lever; full skill needs multi-reference data). Status: **YELLOW** — a trustworthy frequency twin plus a
partially-improvable amplitude predictor. (Corrected 2026-06-20 after re-examining likelihood breadth, spatial
structure, and model form per Andrew — see §3a.) Replay: each experiment's `code/*.py`
writes its `out/*.json`; `python3 check_twin.py` gates the deliverables. Figures: `figures/fig_value_summary.png`,
`figures/fig_hardregion.png`.

## 1. Method summary
- **Structure / data:** plain standalone 9-group ShockSat. Single-impact hammer FRF (hit-001, 45–260 Hz,
  df=1.25 Hz, exponential-window) over 115 accel channels (77 high-DR eligible); plus the NASA `.ash` experimental
  modal survey (33 mode shapes / 76 nodes / measured modal damping ζ 0.06–1.05%). Reduced 74-DOF modal forward
  `K(θ)=A_fix+Σ_g θ_g A_g`, copied byte-identical from `statfem_real_validation_20260617` (Card A).
- **Twin / likelihood:** L5 = modal peak-FREQUENCY likelihood (match measured ω̂² to FEM eigenvalues; Kiran Eq 25),
  NUTS, all-variable convergence gate. Held-out QOI = peak accelerance & band-GRMS at held-out sensors via the
  modal-superposition forward (hysteretic loss factor η, + the measurement window), with a global units-gain and a
  log-normal QOI discrepancy. Inferred: 9 group stiffness multipliers θ + σ_w². Fixed: damping (swept), shapes (FEM).
- **Evaluation (the key choice):** held-out **skill vs CLIMATOLOGY** — a no-skill *calibrated* baseline that predicts
  a held-out channel/mode from the population of *observed measured* channels/modes. Skill = 1 − CRPS_twin/CRPS_clim.
  This asks whether the model carries information beyond the population (the right bar; the deterministic FEM point,
  which has no UQ, is a strawman).

## 2. Headline value (figures/fig_value_summary.png)
| QOI | held-out CRPS-skill vs climatology | value of UPDATING vs nominal FEM |
|---|---|---|
| **modal frequency** | **+0.93** (twin 2.1 Hz vs population 30 Hz; coverage 0.82) | freq error **2.10% → 1.07%** (halved) |
| amplitude, peak (non-hard) | **−1.00** mean over 3 splits (coverage 1.00) | ≈ 0 (θ doesn't move amplitude) |
| amplitude, band-GRMS (non-hard) | **−1.02** | ≈ 0 |

**The twin's value is entirely in the modal/frequency domain.** For per-channel single-impact amplitude it is
*honest* (covers ~100%) but has *negative skill* — worse than guessing the population — even on the non-hard sensors.

## 3. Why amplitude can't be tightened — every lever, run not argued
- **Damping (#2):** frequency-blind (damped-freq shift 5.5e-5 ≪ 7% floor); its only un-confounded observable
  (half-power bandwidth) is unresolvable here (df=1.25 Hz + exponential-window ζ_w 0.23–1.22% ≈ the real ζ);
  interface-CBUSH loss factors are strain-energy-diluted (`identifiability_M3_cbush.json`). σ_QOI is a *cross-channel*
  scatter; damping is *per-mode/channel-common* → absorbed by the gain. RUN: per-mode measured ζ injection *hurts*
  (windowed FRF under-resolves light modes); a fitted global ζ-scale moves band skill (−1.57→−0.60) but never positive.
- **Shapes (#4) — two distinct things, corrected:** (a) using shapes only to CONSTRAIN θ (L6/L10 MAC) or the
  per-mode |shape| pattern does NOT predict the single-impact amplitude (~0.15 corr; `shape_pattern_test.json`);
  but (b) **inferring the shape FIELD itself (Beck/L8b: free system shapes pulled to the .ash MAC + Rayleigh) DOES
  help** — 3 splits: interval ~43% sharper, coverage→0.97, σ_QOI 0.92→0.86, **CRPS-skill −0.68→−0.25**
  (`modal_beck_ash.json`, `shapefield_lever.json`). Still <0 (single impact), but a real model-form lever. Not a
  mapping artifact (snap ≤0.75 in, ρ=−0.02). My earlier "no model-form lever helps amplitude" was wrong.

## 3a. Corrections after Andrew's pushback (2026-06-20)
- **Likelihood breadth:** ≥10 formulations were evaluated, not 2 (`fig_likelihood_inventory.png`): modal
  peak-FREQUENCY (converges, the twin), INFERRED shape field (converges, sharpens amplitude), shape MAC, analytic
  evidence; freq+MAC-as-θ and complex-PHASE (~null / single-hit-incoherent); whole-FRF magnitude, peak-AMPLITUDE
  feature (R̂ 55), correlated discrepancy (non-converged). The converging+useful ones are MODAL.
- **Spatial pattern:** re-examined (`spatial_reanalysis.json`). There IS a mild physical-region concentration —
  bolted-joint region worst (12.3 dB), dish/strut elevated — but it explains only R²=0.04; proximity does not
  predict hardness. So a physical-region discrepancy prior is justified but weak; the dominant variation is a
  channel-specific near-field nugget. (Andrew partly right: real but weak.)
- **Model form / damping:** the shape-field inference (above) is the strongest amplitude lever; damping (fitted
  global ζ / topology release) still gives no amplitude skill. Full damping inference (per-mode/complex) remains a
  documented to-do.
- **Topology (#4, run):** softening then fully *releasing* the bolted joint (bush_801) moves peak skill only
  −0.80→−0.74→−0.66 (`gap_closure_seed00.json`) — no help.
- **Stiffness richness / evidence (Card F Stage 1, paused):** richer LOCAL stiffness (up to 16 params) does not earn
  its complexity on the frequency observable (Ockham/BIC; `stage1_evidence.json`); prior-robust.
- **Discrepancy structure:** a two-population (hard-region vs rest) discrepancy tightens the well-modeled ~90% by
  ~28% (coverage held) — but it is **over-fit**: the hard set is separable only by a hand-label derived from prior
  FEM-vs-test, with NO a-priori FEM feature predicting it (ρ≈0) and only weak spatial correlation (nn-4 0.24). It is
  a **labeled demonstration, not a transferable method** (`fig_hardregion.png`).

## 4. Assumptions / honesty ledger
- Single impact, single drive node; only hit-001 raw exists (the other 3 hits = 3 channels each). Per-channel
  amplitude/level carries a single-reference participation÷damping confound (absorbed by the gain). MEASURED data
  throughout (no synthetic truth). Window ζ_w(f) modeled. Frequency-coverage 0.82 is slightly overconfident
  (a minor calibration caveat). The reduced model represents the matched measured modes to ~5% (G-reconstruction).
- DATA-SCOPE CORRECTION (2026-06-22, raw-delivery audit; SUPERSEDES the earlier "plenty of data / NOT a
  data-quantity gap / intrinsic amplitude limit" framing). The amplitude observable used ONE drive point — Test07
  +X impact hammer, the ONLY excitation zip the runner downloaded (`../shocksat_statfem_runner_20260609/source_manifest.md`).
  The PUBLIC NASA delivery (NESC Academy ShockSat1, byte-range-served) ALSO lists, marked `too_large_deferred` and
  NEVER downloaded: multi-direction modal-hammer drives Test01 990x / Test02 990z / Test03 990y / Test04 990xy /
  Test06+Test10 900z / Test08 ImpactHammer 990z, a force-level `Test_Data_Parametric.zip` (3.33 GB), and a
  frangible-joint set; pyro NSI/NSD was only PARTIALLY downloaded (251 MB of 1.41 GB → truncated, one NSD run usable).
  Multi-DIRECTION drives (+X/+Y/+Z/+XY) are exactly the multi-reference excitation that breaks the
  participation÷damping confound. ⇒ The amplitude ceiling is SCOPED to the single-drive QOI we chose; it is NOT
  shown intrinsic, and the confound-breaking raw data EXISTS and is OBTAINABLE (public), just un-downloaded.
  This also corrects "only hit-001 raw exists (other 3 = 3 channels each)": all FOUR Test07 runs are full 256 MB /
  128-channel, distinct-CRC same-+X repeats (useful for noise/repeatability, NOT for breaking the confound).
  Caveat: the +X tap's impact-face channels have low coherence (median ~0.07 over 100-10k Hz,
  `hammer_frf_subset_manifest.json`) — a separate data-quality limit; the README notes the pyro data is "higher in
  magnitude and a little cleaner."

## 5. Three-tier status
- **GREEN:** frequency value (skill +0.93, calibration halves error); integrity (reused code byte-identical to Card A).
- **YELLOW (documented limitations, not failures):** per-channel single-impact amplitude has no skill vs climatology
  (all levers ≤0); frequency coverage 0.82 (slightly overconfident); two-population discrepancy is over-fit
  (demonstration only); Card F evidence Stage-1 only (Stage-2 TMCMC paused per Andrew).
- **RED:** none.

## 6. Recommendation (SURFACE to Andrew — not self-applied)
- Report the twin as a **trustworthy, valuable modal-FREQUENCY twin** + an honestly-calibrated-but-no-skill amplitude
  predictor for single-impact per-channel response.
- Do NOT claim the twin should replace the inherited FEM (no amplitude skill); do NOT present the two-population
  tightening as a method. Any `docs/report/project_log.md` row and durable-rule/sampler-standard change await Andrew.
- If tighter *amplitude* CIs are a goal, the honest path is a QOI the data supports (modal/energy) or multi-reference
  excitation — not a richer single-impact global model.
