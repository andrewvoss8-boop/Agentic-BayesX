# Blind Round-3 STAGE-3 Independent Review + Score — StatFEM (Opus 4.8 inference vs Codex independent truth)

**Reviewer role:** independent grader/scorer. I am not the truth-author (Codex), the inference runner
(opus48), or the master/lead. I read everything including the sealed truth (I am the scorer). I wrote
ONLY to `artifacts/reports/blind_round3_stage3_review_20260605/`; I did **not** modify
`runs/round3/opus48/` or `runs/round3/codex_truth/`.

**Date:** 2026-06-05. **Inference run (Stage 3):**
[blind3_results.json](../../../runs/round3/opus48/report/blind3_results.json),
[packet_stage3.md](../../../runs/round3/opus48/report/packet_stage3.md). **Sealed truth (my key, canonical
netCG re-publish):** [scoring_key.npz](../../../runs/round3/codex_truth/sealed_truth/scoring_key.npz),
[true_parameters.json](../../../runs/round3/codex_truth/sealed_truth/true_parameters.json),
[stage3_netcg_republish_checks.json](../../../runs/round3/codex_truth/report/checks/stage3_netcg_republish_checks.json).
**Canonical contract:** [netcg_quantity_contract.md](../../../docs/agents/competitive_full_experiment/round3/netcg_quantity_contract.md).

**Method:** I recomputed every headline number from saved artifacts; I did not trust self-report. Scripts
and raw output are in `sources/`. Honesty rule applied: a real gain or an honest failure are both fine;
overclaim is not.

---

## TL;DR verdict

| # | Question | Verdict |
|---|---|---|
| 0 | Contract validity (apples-to-apples netCG) | **PASS.** Sealed truth netCG IS the canonical dynamic-FBS `F_iface/m_load` (resonant 5.3–8.1× over the f→0 rigid limit, peaks 64–68 Hz), NOT the forbidden flat 0.28 constant. Inference predicts netCG the same way. Both f→0 limits agree (truth 0.283 / inference 0.282). Re-publish touched only the netCG family; the **apparent-mass data the inference actually fits is unchanged**. |
| 1 | Score vs sealed truth | **Reproduced exactly.** netCG bias **1.71× with-d** (cov95 0.92) / **3.10× without-d** (cov95 **0.00**, cov99 0.00). f→0 limit **0.282** confirmed. The trustworthy (converged) number is the **3.10× over-prediction with 0% coverage**. |
| 2 | Convergence over ALL latents | **Reproduced exactly.** WITHOUT-d **CONVERGES** (worst R-hat **1.009**, min bulk ESS **487**, 0 div). WITH-d **FAILS** (worst R-hat **2.85**, min bulk ESS **4.7**, σ_d→1.33). Ridge + confounding confirmed. Inference correctly does **not** claim "NUTS active" for with-d. |
| 3 | Residual error / missing modes | **Confirmed.** True sensor noise ≈0.46%; inference σ_e 0.69–0.93 (massively inflated). Truth has 2–3 in-band + 1–3 >160 Hz modes per DOF the coarse model cannot make; the inference's cited data peaks match the sealed truth (x≈50.5/87.2/134.7, z≈61.8/80.8/125.4). Missing-mode floor is the correct dominant-residual diagnosis. |
| 4 | Held-out calibration | **Reproduced.** New-build cov95 **0.911** (0.910 vs CLEAN), logwidth **2.17 (~8.8×)** — far sharper than the prior 12–18× but still wide-via-σ_e. Band 95–115 Hz cov95 **0.715** (under-covers). |
| 5 | Companion trust studies | **All actually run.** starve-data still R-hat 2.85 (structural ridge); n_eff(k_pop) 0.64/7920; grid-invariance honestly labeled BOUNDED/intractable under the ridge with alternate evidence. |
| 6 | Blindness + integrity | **PASS.** No forbidden reads (only negative assertions + the published dataset). Figures authentic. Bias/non-coverage point AWAY from leakage. NOT claiming NUTS-active for with-d is the correct honest behavior. |
| 7 | Headline | **The Stage-3 novel discrepancy did NOT resolve the ridge** (confounded, same parameter space). Real defensible gains: per-strut ASYMMETRIC physics → convergence; canonical FBS netCG → bias 4.86×→3.1× and apples-to-apples scoring. Open failures: confounded discrepancy, 3.1× converged netCG over-prediction, missing-mode σ_e floor. Runner's prescribed Stage-4 fix is correct. |

**Bottom line:** an honest, well-labeled **mixed** result. The inference's self-assessment is corroborated
by my independent recompute on every checked quantity. The self-report does not overclaim; if anything it
*understates* the σ_e inflation (see §3).

---

## 0. Contract validity — apples-to-apples netCG (PASS)

I independently confirmed both sides use the canonical dynamic-FBS netCG (`sources/truth_netcg_verify.py`,
`sources/truth_netcg_verify.txt`):

- **Sealed truth is the resonant FBS netCG, not the forbidden flat 0.28 constant.** From the sealed
  `clean_source/load_apparent_mass` (z DOF), the FBS transmission `T(f)=|M_L/(M_S+M_L)|` has f→0 rigid limit
  median **0.283** (m_source(z)≈432, m_load≈170.5) and **resonant amplification 5.31–8.12× (median 6.57×)**
  with peaks at **63.6–67.9 Hz**. This matches Codex's republish check
  ([stage3_netcg_republish_checks.json](../../../runs/round3/codex_truth/report/checks/stage3_netcg_republish_checks.json):
  min 5.264, median 6.536, max 8.113; peak 63.75–68.1 Hz). It is a resonant transfer, NOT frequency-flat.
- **Inference predicts netCG the same way.** [blind3_model.py:174-178](../../../runs/round3/opus48/code/blind3_model.py#L174-L178)
  / [blind3_qoi.py:62-63](../../../runs/round3/opus48/code/blind3_qoi.py#L62-L63):
  `H = M_L/((M_S+M_L)·m_load·g0)`, `netCG=H·F`, with the f→0 limit `m_load/(m_source+m_load)=0.2818`.
  The two f→0 limits agree to ~0.4% (0.283 vs 0.282).
- **The re-publish changed only the netCG family.** The republish check declares updated public keys
  `{response_psd_g2_per_Hz, netcg_3grms_g}` and scoring keys `{clean_response_psd, clean_interface_force_psd,
  clean_netcg_3grms}`, with `unchanged_(public|scoring)_non_netcg_keys_pass=true` and `changed…=[]`. The
  **apparent-mass arrays the inference actually fits are NOT in that family**; I confirmed `apparent_mass_real`
  is present, shape (8,6,4040), all-finite, and the inference likelihood
  ([blind3_infer.py:116-119](../../../runs/round3/opus48/code/blind3_infer.py#L116-L119)) consumes ONLY
  `apparent_mass_real/imag`. So the netCG re-publish cannot have contaminated the calibration; only the QOI
  scoring target is now canonical.
- **Published-observed == clean for the QOI:** `max|published − clean| netCG = 0.0` (no QOI sensor-noise
  layer), so scoring against published vs clean is identical. The prior-stage ~2× definitional drift is
  removed; residual netCG difference is now genuine model-form error.

**Conclusion: the comparison is apples-to-apples on the canonical netCG.**

---

## 1. Score vs sealed truth (independently recomputed)

I propagated the saved posterior draws through the inference forward model with the same uncertainty stack
(parameter epistemic + new-build aleatory + 11 flight forcings) and scored against the sealed
`clean_netcg_3grms_g` (88 build×flight values; all-builds min/mean/max 0.466/0.650/0.935). Script:
`sources/recompute_netcg.py`, output `sources/netcg_recompute.txt`.

| netCG 3·GRMS [g] | predicted p50 | 95% CI | bias vs clean (all) | cov95 | cov99 |
|---|---|---|---|---|---|
| **WITH-d** (non-converged; wide) | 1.115 | [0.519, 2.307] | **1.715×** | **0.920** | 0.966 |
| **WITHOUT-d** (CONVERGED; trustworthy) | 2.018 | [1.377, 4.132] | **3.102×** | **0.000** | 0.000 |
| WITHOUT-d vs held-out builds 6,7 | 2.018 | [1.377, 4.132] | 3.388× | 0.000 | 0.000 |

These **reproduce the self-report** (`blind3_qoi_results.json` 1.715× / cov95 0.920;
`blind3_qoi_results_nodisc.json` 3.102× / cov95 0.000) to 3 sig figs. **f→0 rigid limit = 0.2818 ≈ 0.282**
confirmed.

**Honest read (same as the runner):** the with-d "coverage" (0.92) is **wide-but-covering on a
non-converged, multimodal posterior** (see §2/§5) — not trustworthy. The **converged** without-d posterior
**over-predicts netCG 3.1× with 0% coverage** — the genuine model-form bias: the coarse model misses the
higher-mode antiresonances that attenuate real transmission. Both are a large improvement over the prior
blind **4.86×** (the FBS contract removed the ~2× definitional drift). **Parameter bias note:** the
inference's per-strut/equal-strut parameterization is not 1:1 comparable to the truth's per-DOF modal banks,
so I score the physically interpretable quantities (netCG, f→0 limit, f_dome). `f_dome` posterior is
72–76 Hz (with-d) / 72.0–72.3 Hz (without-d) vs the truth's z source fundamental ≈92–97 Hz (nominal 93.5) —
**biased ~20 Hz LOW** (single axial dome resonator pulled down to chase a coupled z mount peak; honest
limitation, acknowledged).

---

## 2. Convergence over ALL latents (independently recomputed)

I reshaped the flattened NumPyro draws chain-major to (4, n) and recomputed rank-split R-hat + bulk/tail ESS
over **all** latents with ArviZ 0.17.1 (`sources/recompute_convergence.py`, `sources/convergence_recompute.txt`).
**My numbers reproduce the report exactly.**

**WITHOUT discrepancy (per-strut asymmetric only) — CONVERGES:**

| latent | R-hat (mine) | ESS bulk | ESS tail |
|---|---|---|---|
| log_k_pop | 1.0042 | 898 | 604 |
| f_dome | 1.0081 | 1999 | 778 |
| sigma_build | 1.0028 | 655 | 567 |
| sigma_e | 1.0000 | 2060 | 783 |
| z_b (worst) | 1.0095 | 487 | 460 |
| **worst / min** | **1.0095** | **487** | **460** |

Gate (R-hat<1.01, bulk&tail ESS≥400, div<2%, ≥4 chains, non-centered z_b): **PASS** (0 divergences from
`blind3_results.json`). k_pop posterior is tight [1.678e7, 1.693e7] near the nominal 1.816e7. **This is a
real gain over the prior blind run, which could not converge at all (R-hat 2.41).**

**WITH the structure/property-based discrepancy (σ_d learned) — FAILS:**

| latent | R-hat (mine) | ESS bulk | ESS tail |
|---|---|---|---|
| d0[0] (worst) | **2.8452** | 4.7 | 30.6 |
| d_raw[3] | 2.8353 | 4.7 | 33.2 |
| f_dome | 2.2233 | 5.2 | 32.9 |
| log_k_pop | 2.1059 | 5.4 | 36.0 |
| sigma_d | 2.0117 | 5.5 | 38.8 |
| sigma_e | 2.0781 | 5.4 | 34.9 |
| **worst / min** | **2.8452** | **4.7** | **30.6** |

Gate: **FAIL** (R-hat 2.85 ≫ 1.01; ESS 4.7 ≪ 400). 0 divergences with no between-chain mixing = genuine
**multimodality**, not under-warming.

**Ridge + confounding confirmed.** With-d: σ_d posterior runs to **1.33** (median; 95% [0.92, 1.80]) — far
above its 0.20 prior — and k_pop **smears to [6.43e6, 16.8e6]** (vs the tight without-d [1.678e7, 1.693e7]).
The per-strut discrepancy `k_j = k_pop·exp(d0_j)` lives in the **same parameter space** as the per-strut
stiffness, so the two are **confounded by construction**: σ_d/d absorb misfit and de-identify k_pop. The
discrepancy did **not** resolve the σ_d↔σ_e ridge — it **traded a frequency-only ridge for a
parameter↔discrepancy ridge**. The inference correctly does **not** claim "NUTS active" for with-d and
labels its marginals not-yet-converged with worst-case R-hat/ESS attached.

---

## 3. Residual error — missing higher modes (confirmed against sealed truth)

`sources/missing_modes_check.txt`, true_parameters fields.

- **True sensor noise** (fractional apparent mass): median **0.46%**, p95 1.05%
  (`noise_summary.apparent_mass_fraction_noise_median = 0.00457`). So true σ_e (fractional) ≈ 0.005.
- **Inference σ_e:** with-d median **0.69**, without-d **0.93** — i.e. ~**150–190× the true sensor scale**.
  This confirms σ_e is absorbing **model-form error**, not sensor noise.
- **Missing modes are real.** Counting resonance peaks in the sealed `clean_coupled_apparent_mass` (build 0)
  inside the 35–160 Hz inference band: x = 50.5/87.2/134.7; y = 58.7/91.0/148.2; z = 61.8/80.8/125.4;
  rx = 65.4/98.2; ry = 68.2/101.4; rz = 97.0/124.6 — **2–3 in-band peaks per DOF** plus **1–3 more above
  160 Hz** (z load 168/244/356/505; source 176/266/382/522, etc.). The coarse inference model produces only
  ~6 mount modes (struts) + 1 axial dome SDOF, so it physically cannot place the 3rd+ in-band mode (~120–148
  Hz) or anything >160 Hz. The inference's blind data-peak reading ("lateral 51/87/137; z 62/77/120")
  **matches the sealed truth** (x 50.5/87.2/134.7; z 61.8/80.8/125.4). The "missing-higher-mode floor" is the
  **correct** dominant-residual diagnosis — not the discrepancy or the asymmetry. Even the converged
  without-d model keeps σ_e ≈ 0.93 because the missing modes are irreducible in this model class.

**Minor honesty nitpick (in the conservative direction):** the packet's phrase "σ_e inflated by a factor
~2" is imprecise about its baseline — relative to the true 0.46% sensor noise the inflation is ~150–190×, and
relative to the pre-run probe's coarse-fit floor (~1.9, [decisions D29](../../../runs/round3/opus48/report/decisions_log.md#L376))
σ_e is actually *below*. The number "~2×" is loose, but it **understates** rather than overstates the
problem, and the cause (missing modes) is correct — so it is not an overclaim.

---

## 4. Held-out calibration (recomputed vs CLEAN truth, read WITH sharpness)

I reconstructed the new-build posterior-predictive (mirroring `heldout_calibration`) and scored coverage
against both the OBSERVED and the sealed **CLEAN** complex apparent mass (`sources/recompute_heldout.py`,
`sources/heldout_recompute.txt`).

| Held-out target | reported | my cov vs OBSERVED | my cov vs CLEAN | read |
|---|---|---|---|---|
| New builds 6,7 (full band) cov95 | 0.911 | **0.9106** | **0.9098** | near-covering (<0.95) |
| mean log-width | 2.16 | **2.17 (~8.8× span)** | — | far sharper than prior 12–18×, still wide-via-σ_e |
| Band 95–115 Hz (train builds) cov95 | 0.715 | **0.7148** | 0.7148 | **under-covers** |

Coverage matches vs the sealed truth (sensor noise on AM is tiny), so coverage is "real" but **bought with an
inflated σ_e (~8.8× multiplicative bands)** — the wide-but-covering trap, correctly labeled. The held-out
**band** genuinely under-covers (0.72 < 0.95): the honest signature of model-form error (the missing higher
mode that sits in/near 95–115 Hz). Bands are markedly sharper than the prior blind run (~8.8× vs 12–18×),
which is a real, if partial, improvement.

---

## 5. Companion trust studies (verified they were actually run)

From `blind3_results.json` / `blind3_companions.json` / `blind3_gridinv.json` (all present and self-consistent):

- **WITH vs WITHOUT discrepancy** — the decisive comparison: without-d converges (R-hat 1.009); with-d does
  not (R-hat 2.85); σ_e 0.69 (with) vs 0.93 (without). The structured discrepancy *does* lower σ_e but breaks
  identifiability.
- **Starve-the-data** (1 build, 40–100 Hz, with-d): still **R-hat 2.847**, σ_d median 1.39, k_pop wide
  [8.1e6, 20.5e6]. → the ridge is **structural identifiability, NOT a data-deluge artifact** (removing data
  does not fix it). Verified directly from `blind3_companions.json`.
- **Effective-vs-nominal sample count:** n_eff(k_pop) = **0.64** vs 7920 nominal obs (ratio 8.1e-5). n_eff<1
  means the multimodal posterior is **wider than the prior** → the with-d "tightness" is illusory.
- **Grid-invariance:** honestly labeled `BOUNDED / not completed` — the 2× refit is intractable under the
  with-d ridge (NUTS hits the tree-depth cap every draw). The runner reports the over-counting evidence via
  n_eff and starve-data instead and flags grid-invariance as a supporting-only diagnostic. This is an honest
  intractability note, not a skipped-and-hidden study.

---

## 6. Blindness + integrity — PASS

- **No forbidden reads.** `grep` over `runs/round3/opus48/code/` and report `.md` for
  `sealed_truth|scoring_key|true_parameters|model_form_imperfection|hidden_decision|codex_truth/code|codex_truth/report|generate_truth`
  returns only **negative assertions** ("did NOT open / Does NOT read"). The only `codex_truth` path used in
  code is `codex_truth/dataset/observations.npz`
  ([blind3_model.py:44](../../../runs/round3/opus48/code/blind3_model.py#L44)) — the published dataset only.
  (`sources/` blindness grep inline above.)
- **Strongest tell points AWAY from leakage.** A leak would yield near-zero bias with tight, well-covering
  intervals. Instead the converged model is **biased 3.1× on netCG with 0% coverage**, f_dome is ~20 Hz off,
  and the with-d model fails convergence (R-hat 2.85). Nothing outside the model's span is suspiciously
  well-recovered.
- **Figures authentic.** `figures/blind3_*.png` are real PNGs (43–266 kB, 1176×700 … 1950×1040),
  run-generated, not copied reference assets.
- **No fabricated metrics / no overclaim.** Every headline number I recomputed (R-hat, ESS, netCG bias &
  coverage, f→0 limit, held-out coverage & width, companions) reproduces from the saved artifacts.
- **NOT claiming "NUTS active" for with-d is the correct honest behavior** — the with-d gate genuinely fails
  and is labeled not-yet-converged; only the converged without-d model is reported as passing.

---

## 7. Headline verdict

**Did the structure/property-based discrepancy (the Stage-3 novel piece) RESOLVE the ridge and restore honest
calibration? NO — confirmed.** Because the per-strut log-stiffness discrepancy `k_j = k_pop·exp(d0_j)` lives
in the **same parameter space** as the per-strut stiffness it perturbs, it is **confounded by construction**;
σ_d runs to 1.33, k_pop de-identifies, and convergence breaks (R-hat 2.85). The starve-data companion shows
the ridge is structural, not a data artifact. The self-report's diagnosis is correct and not overstated.

**What is now a real, defensible gain:**
1. **Per-strut ASYMMETRIC forward physics (fix #1)** restores convergence on its own — independently verified
   worst R-hat **1.009**, min bulk ESS **487**, 0 divergences, k_pop near nominal. This is a genuine
   improvement over the prior blind run that could not converge at all.
2. **Canonical FBS netCG contract (fix #3)** makes the scoring apples-to-apples (both f→0 limits ≈0.282) and
   removes the ~2× definitional drift, cutting netCG bias from 4.86× to 3.1× (converged) / 1.7× (wide).
3. **Sharper held-out bands** (~8.8× vs the prior 12–18×).

**What is still an honest open failure:**
1. The novel same-parameter-space discrepancy **does not work** (confounded; with-d fails the gate). Correctly
   not claimed as NUTS-active.
2. The **converged** without-d model **over-predicts netCG 3.1× with 0% coverage** — genuine model-form bias.
3. **σ_e ~150–190× the true sensor noise** and the held-out band under-covers (0.72) — a **missing-higher-mode
   floor** the coarse model (6 mount + 1 dome SDOF) cannot represent (truth has 2–3 in-band + 1–3 >160 Hz
   modes per DOF).
4. f_dome biased ~20 Hz low.

**Is the runner's prescribed Stage-4 fix correct? YES, and well-motivated by this evidence:**
(a) make the discrepancy **orthogonal to the calibration parameters** (output-mode / participation space) or
use **modular / cut updating** so the discrepancy cannot trade against k_pop — this directly addresses the
confounding I verified; and (b) **raise FEM fidelity** (flexible isogrid panel + strut/shell bending modes)
to introduce the missing in-band and >160 Hz modes — this directly addresses the σ_e floor and the 3.1×
netCG over-prediction I verified. Both follow logically from the failure mode.

**Overall:** an honest, well-labeled **mixed** result. No overclaim; the self-report is corroborated by
independent recompute on every checked quantity (and is, if anything, conservative on σ_e). The blind
protocol worked: the real gain (asymmetric physics + canonical QOI) and the real failure (confounded
discrepancy + missing-mode floor) are both clearly attributed and traceable.

---

## Evidence index (`sources/`)
- `recompute_convergence.py` / `convergence_recompute.txt` — independent rank-split R-hat + bulk/tail ESS,
  all latents, both variants.
- `recompute_netcg.py` / `netcg_recompute.txt` — netCG 3·GRMS bias + 95/99 coverage vs SEALED clean truth.
- `recompute_heldout.py` / `heldout_recompute.txt` — held-out coverage vs OBSERVED and CLEAN truth + width.
- `verify_truth_netcg.py` / `truth_netcg_verify.txt` — truth netCG is resonant FBS (not flat 0.28); f→0 limit;
  published==clean; AM data intact.
- `missing_modes_check.txt` — truth resonance-peak count per DOF vs the coarse model's span; sensor-noise scale.

All `runs/...` links above are the audited source artifacts; I did not modify them.
