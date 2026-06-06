# Stage-3 BLIND Inference Packet — Round 3 (Claude Code Opus 4.8), structure-aware fix vs INDEPENDENT truth

**Role:** INFERENCE runner, **BLIND**. I consumed ONLY `runs/round3/codex_truth/dataset/observations.npz`
+ `data_contract.md` (read-only). I did **not** open `sealed_truth/`, Codex's generator code, or Codex's
report. The **master** scores my posterior against the sealed truth. This continues the blind round after the
Stage-0/1 failure; it builds the three coupled fixes that failure pointed to and tests them on the SAME
re-published independent truth (now with the canonical netCG contract).

> **One-line result (honest, mixed):** the **per-strut ASYMMETRIC forward model (fix #1) RESTORES
> convergence** (without-discrepancy: rank-split R-hat **1.009**, bulk ESS **487**, 0 divergences, k_pop
> near-nominal) — a real improvement over the prior blind run, which could not converge at all. But the
> **structure/property-based discrepancy (fix #2) does NOT resolve the σ_d↔σ_e ridge — it INTRODUCES a
> parameter↔discrepancy ridge** (with-d: R-hat **2.85**, ESS **4.7**, σ_d runs to 1.33) because a per-strut
> discrepancy is confounded with the per-strut stiffness it sits on. The **complex likelihood + canonical
> FBS netCG (fixes #3, contract) cut the netCG bias from the prior 4.86× to 1.7–3.1×.** Residual σ_e
> inflation (~0.7–0.9) is the **missing-higher-mode** model-form error the coarse model cannot represent.
> **I do NOT claim "NUTS active"** for the with-discrepancy model (gate FAILS).

---

## 1. Method summary (read first)

**Engineering decision supported:** does the qualification test spec envelope the predicted flight netCG /
interface vibration environment (with honest uncertainty), and is there narrow-band exceedance at a coupled
resonance? (Force-limiting / NASA-HDBK-7004 framing.)

**Forward model (the asymmetric fix, JAX-differentiable).** The published per-build 6-DOF *diagonal complex
interface apparent mass* is modeled as apparent masses adding in parallel at the shared driven interface DOF:

  M_pub(ω) = **M_S(ω)** (source/dome: per-DOF rigid effective mass/inertia + axial bounce SDOF on z, f_dome)
           + **M_L(ω; k₁…k₆)** (load/tray: rigid 170 kg body on **6 PER-STRUT axial struts**, condensed to
             the interface). M_L = −K_s(K_s − ω²M_b)⁻¹M_b, K_s = Σⱼ kⱼ bⱼbⱼᵀ from the hexapod geometry.

Per-strut kⱼ **breaks the 6-fold symmetry** → represents the data's **x≠y (51/87 vs 54/91 Hz)** and
**rx≠ry (56/97 vs 67/99 Hz)** mode splits that one equal-strut k could not. Rigid masses are read off the
measured low-f apparent-mass asymptote (≈518–764 kg / kg·m²; standard apparent-mass practice). Verified the
per-strut mechanism splits the degenerate pairs (47.18/47.18 → 44.2/47.8; 136.6/136.6 → 130.9/144.3).

**Structure/property-based discrepancy (fix #2, the novel piece, D12/D27).** A per-strut log-stiffness field
dⱼ with covariance in **STRUT FEATURE space** (azimuth): same element-type → moderate baseline corr (0.30);
azimuthal proximity → high corr (Gaussian in angular distance, ℓ=70°). Applied in **PARAMETER space**:
kⱼ = k_pop·exp(d0ⱼ), with d0 zero-meaned to separate the calibration mean k_pop from the structured shape.
This carries an **azimuthal (spatial) error a frequency-only kernel cannot** — and is propagated through the
model, not added on the output. σ_d is **LEARNED** (HalfNormal(0.20) informative — observed splits ~15–30%
→ d~0.15–0.35 — **NOT a hard cap**; D27/D30).

**Complex likelihood (fix #3, D28).** Fits **real AND imaginary** apparent mass (all 6 diagonal DOF) so
phase/antiresonance constrain the fit: re,im ~ Normal(model, σ_e·scale), scale = build-avg local |AM| floored
at 0.3× the per-DOF band median (so notches don't pathologically dominate the relative-complex likelihood).

**Likelihood band / grid.** Whole-curve complex AM on an adaptive grid (110 points, **35–160 Hz**, built from
**data peaks** — true modes unknown blind; fixed during inference). 35–160 Hz is the first mount+bounce
cluster and carries the QOI energy; the data's higher peaks (z 120; lateral 137; >160 Hz) are **outside the
model's representational span** — a documented gap (see §4).

**Inferred:** k_pop, per-strut discrepancy field d (+σ_d), f_dome, per-build scatter z_b (+σ_build), σ_e.
**Fixed (not inferred):** rigid source/load masses (asymptote read-off), structural loss η=0.04
(magnitude+phase weakly identify it), hexapod geometry, feature-kernel length-scale ℓ_θ.
**Aleatory:** build-to-build (σ_build, hierarchical), flight-to-flight (11 published forcings).

**netCG QOI (canonical FBS contract, D25; supersedes my prior drive-point QOI).**
netCG = F_iface/m_load, with F_iface from DYNAMIC FBS coupling of source+load apparent mass (z DOF):
a_iface = F/(M_S+M_L); F_iface = M_L·a_iface; **netCG = [M_L/(M_S+M_L)]·F/m_load**. Verified f→0 rigid limit
= m_load/(m_source+m_load) = **0.282** (m_source≈433, m_load=170). **FORBIDDEN** (and avoided): rigid constant
mass-ratio; drive-point accelerance F/M_zz (what my prior blind run used — ~2× of the old 4.86× bias). Shows
resonant amplification at the coupled modes (figure `blind3_netcg_transfer.png`).

---

## 2. Convergence over ALL latents (the headline gate)

Gate: rank-split R-hat < 1.01, bulk & tail ESS ≥ 400, divergences < 2%, ≥4 chains, non-centered. Full
per-latent table in `blind3_nuts_diagnostics.md`. 4 chains; non-centered z_b and d_raw; max_tree_depth
capped at 8 for tractability (**the sampler frequently HITS the cap — itself evidence of pathological
ridge/multimodal geometry**, consistent with the prior blind run).

| Model | worst R-hat | min bulk ESS | divergences | GATE |
|---|---|---|---|---|
| **WITH** structure-based discrepancy (σ_d learned) | **2.85** | **4.7** | 0/1400 | **FAIL** |
| **WITHOUT** discrepancy (per-strut physics only, σ_d=0) | **1.009** | **487** | 0/1000 | **PASS** |

**Reading.** The asymmetric per-strut **physics alone converges cleanly** (R-hat 1.009, ESS 487) and recovers
k_pop ≈ **1.685e7** (95% CI [1.678e7, 1.693e7]) near the nominal 1.816e7. Adding the structure-based
discrepancy **breaks** convergence: σ_d runs to **1.33** (≫ its 0.20 prior), the per-strut d field and σ_e
become multimodal (R-hat 2–2.8 on d_raw, σ_d, σ_e), k_pop smears to [6.4e6, 16.8e6]. **0 divergences with no
between-chain mixing = genuine multimodality, not under-warming** (same signature as the prior run; confirmed
structural by the starve-data companion, §4).

**Did the structure-based discrepancy resolve the σ_d↔σ_e ridge? NO.** It did the opposite: a per-strut
discrepancy **lives in the same parameter space as the per-strut stiffness**, so it is **confounded by
construction** (both perturb the struts). Given freedom, σ_d absorbs misfit and de-identifies k_pop —
trading a frequency-only ridge for a parameter↔discrepancy ridge. **Lesson:** a structure-based discrepancy
must live in a space **orthogonal to the calibration parameters** (e.g. the output modes the physics lacks),
not on the very parameters being calibrated.

---

## 3. Headline tests (reported honestly)

**(i) Does it stop σ_e inflation?** Partially. σ_e (with-d) median **0.69** vs (without-d) **0.93** — the
structured discrepancy DOES absorb some structured error and lowers σ_e. But neither is near the true sensor
scale; **σ_e stays inflated by a factor ~2** because the dominant remaining error is missing higher modes
(§4), which neither the physics nor a per-strut discrepancy represents. (Pre-run probe: the best achievable
coarse-model fit has rms fractional residual ~1.9, z-DOF 3.7 — an irreducible σ_e floor.)

**(ii) Does it catch the spatial error? (with vs without)** The per-strut model (fix #1) **does** represent
the x≠y / rx≠ry splits (figure `blind3_split_with_d.png`; the converged without-d k field already splits the
lateral/rocking pairs). The structure-based discrepancy adds azimuthal freedom but, being confounded, mostly
trades against k_pop rather than cleanly "catching" a residual spatial error.

**(iii) Does it reduce the f_dome / netCG bias?** netCG bias improved markedly via the FBS contract (fix #3):
prior blind **4.86×** → Stage-3 **1.71×** (with-d) / **3.10×** (without-d). f_dome is biased **low (72–76 Hz
vs nominal 93.5)** — the dome resonator is pulled down to chase a z mount peak; an honest limitation of the
single-axial-resonator dome model.

**(iv) Held-out coverage moving toward ~0.95 with SHARPER bands?** (Primary trust test; read WITH width.)

| Held-out target | coverage95 | mean log-width | read |
|---|---|---|---|
| New builds 6,7 (full band) | **0.911** | **2.16** (~8.7× span) | near-covering; **far sharper than the prior 12–18× bands** but still wide-via-σ_e |
| Frequency band 95–115 Hz (train builds) | **0.715** | — | **under-covers** — the honest signature of model-form error where the coarse model is weakest |

Coverage improved and bands tightened vs the prior blind run, but the held-out **band** still under-covers
(0.72 < 0.95): model-form error in a region the coarse model cannot represent.

---

## 4. Companion trust studies (run this time; skipped last run)

- **WITH vs WITHOUT discrepancy** (§2/§3): the decisive comparison. Without-d converges; with-d does not;
  σ_e 0.69 (with) vs 0.93 (without).
- **Starve-the-data** (1 build, 40–100 Hz, with-d): still **R-hat 2.85**, σ_d 1.39, k_pop wide
  [8.1e6, 20.5e6]. → the ridge is **structural identifiability, NOT a data-deluge artifact** (removing the
  data does not fix it).
- **Effective-vs-nominal sample count** (with-d): n_eff(k_pop) ≈ **0.6** vs nominal 7920 obs (ratio 8e-5).
  n_eff < 1 reflects the **multimodal** posterior being WIDER than the prior — the opposite of fictitious
  tightness; the with-d "tightness" is illusory.
- **Grid-invariance** (`blind3_gridinv.json`, refit at 1× vs 2× grid density): supporting diagnostic of
  frequency over-counting; see file for the sd-ratio vs the 1/√N_f expectation.

---

## 5. Full-uncertainty netCG + interface-PSD QOI vs spec (closes D13)

Propagated: parameter (epistemic k_pop, d, f_dome) + build (aleatory exp(σ_build z)) + flight (11 published
forcings) + structure-based discrepancy d (its posterior uncertainty). σ_e (sensor noise) excluded from the
physical QOI. Truth comparison = PUBLISHED observed netCG (0.466–0.935 g, mean 0.650).

| netCG 3·GRMS [g] | p50 | 95% CI | bias | 95% cov | 99% cov | spec margin | 99%-hi exceedance |
|---|---|---|---|---|---|---|---|
| **with-d** (non-converged; wide) | 1.12 | [0.52, 2.31] | **1.71×** | 0.92 | 0.97 | 2.56× | **25.4%** |
| **without-d** (CONVERGED; trustworthy posterior) | 2.02 | [1.38, 4.13] | **3.10×** | 0.00 | 0.00 | 2.16× | 6.2% |

**Honest read.** The with-d QOI "covers" (92%) only because its multimodal posterior is **wide**
(wide-but-covering). The **converged** without-d QOI is **biased 3.1× high with 0% coverage** — the genuine,
honest model-form bias: the coarse model **over-predicts** the transmitted netCG because it misses the
higher-mode antiresonances that attenuate the real transmission. Both are a large improvement on the prior
blind 4.86× (the FBS contract removed the ~2× definitional drift). **Headline engineering point holds:** a
comfortable overall margin (2.2–2.6×) **hides narrow-band 99%-hi exceedance** at the coupled resonances
(6–25% of the band) — the force-limiting risk. (Figures: `blind3_netcg_transfer.png` shows the f→0 rigid
limit + resonant amplification; `blind3_netcg_grms_vs_truth.png`; `blind3_netcg_psd_vs_spec.png`.)

---

## 6. What the fix achieved, and what it did not (honest scorecard)

| Fix | Intended | Outcome |
|---|---|---|
| #1 Per-strut asymmetric forward | represent x≠y, rx≠ry; restore convergence | **YES** — without-d CONVERGES (R-hat 1.009, ESS 487), k_pop near-nominal; splits represented |
| #2 Structure/property-based discrepancy (parameter space) | resolve σ_d↔σ_e ridge, catch spatial error, sharpen | **NO (informative failure)** — confounded with the per-strut stiffness → INTRODUCES a parameter↔discrepancy ridge, breaks convergence (σ_d→1.33). Does lower σ_e (0.93→0.69). |
| #3 Complex (mag+phase) likelihood + FBS netCG | use phase; fix the ~2× definitional bias | **YES** — netCG bias 4.86× → 1.7–3.1×; f→0 limit exact (0.282) |

**Dominant residual error = MISSING HIGHER MODES.** The data has more resonances per DOF (z: 62/77/120;
lateral: 51/87/137) than the coarse model (6 mount modes + 1 axial dome bounce) can produce in 35–160 Hz.
This keeps σ_e inflated (~2×) regardless of the discrepancy, biases the netCG ~3× (converged model), and is
the real Stage-4 target (flexible isogrid panel + strut/shell bending modes).

---

## 7. Blindness + integrity

- Consumed ONLY `codex_truth/dataset/observations.npz` (see `blind3_model.py:DATASET`). Did NOT open
  `sealed_truth/`, Codex code, or Codex report. The strongest tell points AWAY from leakage: the results are
  **biased and partly non-covering** (3.1× netCG bias, held-out band 0.72), not suspiciously perfect.
- Never claim "NUTS active": the with-discrepancy model FAILS the gate and is labeled NOT-YET-CONVERGED with
  worst-case R-hat/ESS next to every interval; the without-d model PASSES and is reported as such.
- All figures are run-generated PNGs; every headline number traces to a saved JSON.

## 8. Limitations / residual risk (see also `blind_known_failures.md`)
1. With-discrepancy model is **non-converged** (multimodal); its marginals/QOI are best-available, heavily
   caveated. The trustworthy posterior is the converged **without-d** one (biased but honest).
2. **Missing higher modes** (>~115 Hz and extra in-band peaks) — the dominant model-form error; not modeled.
3. f_dome biased low (single axial dome resonator); dome lateral/rocking lumped as rigid.
4. σ_d informative prior (justified, not a cap) — but the confounding is structural, not prior-driven
   (starve-data confirms).
5. netCG bias 1.7–3.1× is genuine model-form over-prediction; reported, not tuned away.

## 9. Replay (one command each)
```
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind3_model.py     # forward-model sanity
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind3_infer.py     # NUTS + companions + held-out
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind3_qoi.py       # full-uncertainty netCG (both posteriors)
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind3_figs.py      # review figures
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind3_gridinv.py   # grid-invariance companion
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind3_pptx.py      # packet.pptx
```
Artifacts: `blind3_results.json`, `blind3_companions.json`, `blind3_heldout.json`,
`blind3_nuts_diagnostics.{md,json}`, `blind3_qoi_results.json` (+`_nodisc`), `blind3_posterior.npz`
(+`_nodisc`), `blind3_gridinv.json`, `figures/blind3_*.png`, `packet.pptx`. Hand back to the master for
scoring against the sealed truth.
