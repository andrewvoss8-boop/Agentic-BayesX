# BLIND Inference Packet — Round 3 (Claude Code Opus 4.8), vs an INDEPENDENT ground truth

**Role:** INFERENCE runner, **BLIND**. A separate agent (Codex) authored an independent, richer
"as-built reality," emitted observations, and SEALED everything else. I consumed ONLY
`runs/round3/codex_truth/dataset/observations.npz` + `data_contract.md` (read-only). I did **not** open the
sealed truth, the generator code, or Codex's report. The **master** scores my posterior against the sealed
truth after this is committed. (Prior, non-blind round-3 packet preserved as
`packet_original_mdof_netcg.md`.)

> **One-line result:** the independent truth carries model-form error **outside my coarse model's span**, so
> the hierarchical StatFEM NUTS inference **does not converge** (multimodal / non-identifiable; the
> sigma_d↔sigma_e ridge), held-out coverage is "**wide-but-covering**," and the netCG QOI is **biased ~5×
> high**. This is the intended outcome of a genuine blind test — recovery is not a tautology, and it breaks.
> **I do NOT claim "NUTS active."**

---

## 1. Method summary (read first)

**Engineering decision supported:** does the qualification test spec envelope the predicted flight netCG /
interface vibration environment (with honest uncertainty), and is there narrow-band exceedance at a coupled
resonance?

**My forward model (coarse, linear, symmetric — a plausible NOMINAL design model, NOT a reverse-engineering
of the hidden structure):** the published per-build 6-DOF *diagonal interface apparent mass* is modeled as

  M_diag(ω) = **M_base6** (lumped rigid dome+interface effective mass/inertia)
            + **hexapod_condensed(ω; k_strut)** (rigid 170 kg tray on 6 equal axial struts → 6 mount modes)
            + **dome axial resonator(ω; f_dome)** (axial bounce, z DOF only).

`M_base6` is read from the measured low-frequency apparent-mass asymptote (≈520–760 kg / kg·m²) — standard
apparent-mass practice, since the low-f asymptote *is* the rigid-body mass; the dynamics are inferred.
Nominal anchors: tray axial mount mode 86.25 Hz, dome bounce 93.5 Hz.

**Likelihood:** whole-curve **log|apparent mass|** (magnitude, log-space) on an adaptive frequency grid
(62 points, 40–115 Hz, built from **data peaks** — true modes unknown blind; fixed during inference). The
40–115 Hz band is the first mode cluster and carries the QOI energy (response peaks 66/96 Hz). Equation
(per build b, DOF c, frequency f): `log|M_obs| = log|M_model(k_strut_b, f_dome)| + d_c(f) + ε`,
`ε ~ N(0, σ_e²)`, `k_strut_b = k_pop·exp(σ_build·z_b)`, `d_c` = per-DOF Matérn HSGP over log-f (rank 3).

**Inferred:** k_strut (population) + per-build scatter σ_build + dome bounce f_dome + sensor noise σ_e +
discrepancy coefficients (σ_d **capped** at 0.3 to break the ridge; ℓ_d fixed 0.45). **Fixed:** rigid
masses, structural loss η=0.04 (magnitude-only → damping not identifiable), forcing model (published).
**Sampler:** NumPyro **NUTS**, 4 chains, 1000 warmup + 1000 draws, non-centered hierarchy, target_accept 0.9.

**Data count:** 8 builds × 6 DOF × 4040 freq complex apparent mass; 11 flights forcing PSD; 8×11 response
PSD + netCG. Build-to-build variation present (~19% log-std, concentrated near resonances).

---

## 2. Headline result — the inference does NOT converge (honest)

| diagnostic | value | gate | pass? |
|---|---|---|---|
| worst rank-split R-hat (over ALL latents incl. z_b, β) | **2.41** (z_b) | < 1.01 | ❌ |
| min bulk ESS / min tail ESS | **5 / 29** | ≥ 400 | ❌ |
| divergences | 0 / 4000 (0.0%) | < 2% | ✅ |
| chains / parameterization | 4 / non-centered | ≥4, NC | ✅ |

**Fast leapfrog steps but no between-chain mixing → genuine MULTIMODALITY** (identical at 150 and
800–1500 warmup, so not under-warming). `σ_e` inflates to **0.62 (log) ≈ factor 1.85 misfit** — the coarse
model fits the data poorly and the noise term absorbs the residual.

**It is not a parameterization artifact** — every variant fails (see `blind_known_failures.md §0`):
flexible learn-σ_d → the σ_d↔σ_e **ridge** (σ_d→2.7, overriding its prior); capped σ_d → R-hat 2.4; +fixed
σ_build → 1.5; minimal (k_strut+σ_e) → 1.5 with a **bimodal** k_strut (the parameter↔discrepancy
degeneracy); **pure physics, no discrepancy → worst (R-hat 2.1, σ_e 0.84)**. The multimodality is intrinsic:
**no single symmetric k_strut fits all 6 DOF** of the as-built (lateral pair wants stiffer, axial softer),
and the as-built shows symmetry-breaking mode splits (x 50.9 vs y 54.3; rx 62.6 vs ry 67.0) my model cannot
represent.

**Best-available marginals (LABELED NOT-YET-CONVERGED; stable across the failing configs — for the master
to score, not to trust):**

| parameter | q50 | 95% CI | nominal | note |
|---|---|---|---|---|
| k_strut [N/m] | 1.42e7 | [1.08e7, 3.29e7] | 1.82e7 | biased low; bimodal high tail |
| f_dome [Hz] | 83.2 | [81.9, 85.1] | 93.5 | pulled below nominal |
| σ_build | 0.20 | [0.02, 0.40] | (5% prior) | bimodal; non-identified vs σ_e |
| σ_e (log) | 0.62 | [0.56, 0.70] | ~0.1 sensor | **inflated** (model-form leak) |
| σ_d (log) | 0.30 | fixed | — | capped to break the ridge |

---

## 3. Trust test — held-out calibration (PRIMARY)

Held out **whole builds** (2 of 8) and a **whole frequency band** (82–95 Hz), then predicted them.

| held-out | 95% coverage | mean log-width | read |
|---|---|---|---|
| new builds (full band) | 0.94 | **2.84** (≈ ×12 multiplicative) | **wide-but-covering — NOT success** |
| frequency band 82–95 Hz | 0.88 | 2.82 | under-covers (target 0.95) |

Coverage looks "ok" ONLY because σ_e is inflated to ~×1.85 — the bands are ~12× wide. Per the trust rule,
read coverage WITH sharpness: this is **not** calibrated success. Figure:
`figures/blind_heldout_calibration.png` (all 6 DOF, predicted 95% band vs the two held-out builds, with the
held-out frequency band shaded).

**Companions.** Effective-vs-nominal independent-sample count: **n_eff(k_strut) ≈ 0.9 vs 1800 nominal points
(ratio 5e-4)** — the posterior barely contracts from the prior (no fictitious tightness; the data deluge is
correlated model error, not independent information). With/without-discrepancy and starve-the-data were
characterized at reduced sample size (the no-discrepancy geometry is pathologically stiff — itself evidence
the discrepancy is needed; see `blind_known_failures.md §0,§7` and `decisions_log.md D24`).

---

## 4. QOI — netCG with FULL uncertainty vs the test spec

QOI mapping (driving-point accelerance, my engineering definition): PSD_acg = PSD_F / (|M_zz|² g0²);
3·GRMS = 3·√(∫ PSD_acg df). Full uncertainty propagated: k_strut (epistemic) + build & flight (aleatory) +
discrepancy d (closes D13).

| netCG 3·GRMS [g] | predicted (full unc.) | published observed |
|---|---|---|
| q50 | **3.16** | mean 0.65 |
| 95% CI | [1.22, 6.08] | range 0.46–0.96 |
| 99% CI | [0.60, 6.38] | — |

**Predicted ~5× high** (≈ 2× from the driving-point QOI mapping, measured on published data, × the inflated/
multimodal posterior). The published low values (0.46 g) fall **below** my 99% CI → honest **over-prediction
/ non-coverage** of the QOI. Narrow-band exceedance: predicted **99%-hi exceeds the spec on 42.75% of the
band** while the **overall scalar margin is 4.5×** — the "large overall margin hides narrow-band exceedance"
headline is demonstrated (though inflated by the wide bands). Figures: `figures/blind_netcg_psd_vs_spec.png`,
`figures/blind_netcg_3grms.png`.

---

## 5. Where I expect to be biased / under-covering (explicit, per the brief)

1. **k_strut biased low and f_dome pulled below nominal**, both non-identified (multimodal) — the master will
   likely find bias and poor coverage vs the sealed truth.
2. **σ_e inflated, σ_build/σ_d non-identified** — the frequency-only discrepancy cannot represent the truth's
   symmetry-breaking + higher-mode error; it leaks into noise and de-identifies the hierarchy.
3. **netCG QOI biased ~5× high** with wide bands; under-covers the published low tail.
4. **Held-out frequency-band coverage 0.88 (< 0.95)** and only "wide-but-covering" on new builds.
5. **Nothing modeled above ~115 Hz**, no asymmetry, no lateral dome dynamics, magnitude-only (no damping).

**This is the experiment working as intended:** an independent, richer truth produced real model-form error
that my coarse design model cannot represent, so blind recovery breaks. The fix is a STRUCTURE-based
(per-strut/property) discrepancy + an asymmetric / higher-fidelity forward model + complex likelihood
(see `blind_known_failures.md` "What would fix it").

---

## 6. Reproduce
```
PYTHONPATH="runs/round3/opus48/.pylibs:runs/round3/opus48/code" .venv_nuts/bin/python runs/round3/opus48/code/blind_model.py   # forward-model sanity vs data
R3BLIND_COMPANIONS=0 PYTHONPATH=... .venv_nuts/bin/python runs/round3/opus48/code/blind_infer.py        # NUTS inference + held-out calibration
PYTHONPATH=... .venv_nuts/bin/python runs/round3/opus48/code/blind_qoi.py                               # netCG / interface-PSD QOI vs spec
```
Artifacts: `blind_results.json`, `blind_nuts_diagnostics.(md|json)`, `blind_posterior.npz`,
`blind_qoi_results.json`, `figures/blind_*.png`. Supporting: `blind_quantity_contracts.md`,
`blind_assumptions_ledger.md`, `blind_known_failures.md`, `decisions_log.md` (D21–D24).
