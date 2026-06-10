# ShockSat FEM Modal Twin — Human-Review Packet

**Workspace:** `artifacts/reports/shocksat_fem_modal_twin_20260609/`
**Replay:** `bash run_all.sh` (steps 1–18). **Checker:** `python3 check.py` → `checker_report.json`.
**Date:** 2026-06-10. **Sampler:** NumPyro NUTS (No-U-Turn HMC), 4 chains, float64, pinned `.venv_nuts` (jax 0.4.30 / numpyro 0.15.3).

> **Read this first — honesty banner.** This twin is calibratable from the full
> modal dataset (the 18-mode posterior **passes** the convergence gate), but the
> result is a *partial-identifiability* finding, not a clean "everything
> recovered" success. Only ~4 of 9 part-group stiffnesses are informed by the
> data; the held-out **band** and **leave-one-mode-out (LOMO)** designs do **not**
> pass the convergence gate (multimodal posteriors). Held-out *frequency*
> predictions are nonetheless well-calibrated. Every interval below is printed
> next to its worst-case R-hat/ESS. Nothing here is labeled "converged" unless it
> passed the gate. **Checker overall: YELLOW** (15 green / 2 yellow / 0 red) —
> the 2 yellows are the documented non-converged held-out designs, never a
> faked pass (green/yellow/red standard, §10).

---

## 0. Method summary (model form, likelihood, data, what's inferred)

**Forward model (differentiable, reduced).** The NASTRAN deck is assembled from
scratch in Python into per-part-group stiffness blocks and a mass matrix, then
projected onto the 74 nominal elastic modes (mass-normalized, so reduced mass =
identity). Inside NUTS the reduced stiffness is

    K_r(theta) = A_fix + sum_g theta_g * A_g          (74 x 74, mass = I)
    lambda, Q  = eigh(K_r(theta))
    f          = sqrt(lambda) / (2*pi)                 [Hz]

where `theta_g` (g = 1..9) are dimensionless stiffness scale factors on each
part group (`theta_g = 1` is the as-modeled stiffness; `theta_g = 1.15` is
exactly +15 % Young's modulus / spring rate of every element in that group,
because element stiffness is linear in E and in bush rate k).

**Mode tracking.** Each measured test mode is tied to a nominal model mode by a
fixed Hungarian 1:1 pairing (`pairing.py`). Inside the sampler the current model
mode is the eigenvector with maximum overlap to the nominal one; the *index* is
taken with `stop_gradient` (it is piecewise-constant, hence non-differentiable),
so gradients flow through eigenvalues/eigenvectors but not through the integer
assignment. This is the documented non-differentiable-feature handling required
by the NUTS rule.

**Likelihood (whole held-in set of paired log-frequencies — no feature/peak
selection).**

    log f_pred,m  ~  Normal( log f_meas,m , sigma_f )        for every held-in mode m

`sigma_f` is the log-frequency residual scale (≈ relative frequency error),
**inferred**, prior `HalfNormal(0.05)`. Optionally (sensitivity arm only) a
**pseudo-likelihood** on the Modal Assurance Criterion is added:

    MAC_m  ~  Normal( 1 , sigma_mac )    [PSEUDO-likelihood; not a generative shape model]

**Why frequency-only is the primary likelihood (deviation from task card §6).**
The card asked for a frequency **+ shape/MAC** likelihood. We make the primary
likelihood frequency-only and treat MAC as (a) the pairing cost and (b) a
labeled sensitivity arm, for one concrete numerical reason: the 122–125 Hz
cluster contains a near-degenerate eigenvector pair, and eigenvector gradients
are ill-conditioned (∝ 1/(lambda_i − lambda_j)) for near-degenerate modes, which
injects divergences/instability into HMC. Frequencies (eigenvalues) stay
well-conditioned through degeneracies. The MAC pseudo-likelihood is therefore
reported side-by-side as an arm (Section 6), not baked into the headline. MAC is
labeled a *pseudo*-likelihood throughout because it is a similarity score forced
toward 1, not a calibrated generative model of the shape vectors.

**Priors.** `theta_g ~ LogNormal(0, 0.25)` (median 1; untruncated 95 % range
[0.613, 1.632]); `sigma_f ~ HalfNormal(0.05)`; `sigma_mac ~ HalfNormal(0.2)`.
LogNormal width 0.25 is deliberately wide because NASA hand-tuned the joint
springs — an honest "we don't know the joints well" prior.

**Inferred (11 latents):** 9 `theta_g` + `sigma_f` (+ `sigma_mac` only in the
MAC arm). **Fixed (not inferred):** mass matrix M, geometry, mesh, element
formulation, mode-pairing rule, accelerometer-mount bush stiffness (PBUSH 99 = 1).
**Not inferred, acknowledged latent:** model-form discrepancy beyond what
`sigma_f` absorbs; modal damping (the likelihood does not use it).

**Data counts.** ONE test article. 33 measured free-free modes (frequency +
damping + real shape vectors on 76 accelerometer nodes / 132 measured DOFs) from
an impact-hammer polyreference fit (`Final_FF_Test_Shapes_100121.ash`). 18 of
these are calibration-clean (nominal MAC ≥ 0.5, |df| ≤ 12 %, unique pairing):
test modes [1,3,4,5,6,7,8,10,11,12,13,14,15,16,17,18,21,25]. 9 replicate runs
(3 impact + 6 burst) inform the **noise floor only**; build-to-build variability
is not modeled (one article). The likelihood uses the **whole held-in set** of
paired log-frequencies, not selected peaks/features.

**Run-specific graphical model:** `figures/graphical_model.png`.

---

## 1. Provenance, independence, and the two-session history (integrity)

**Lead-as-runner.** Andrew approved the lead agent doing the runner work itself
(decision D9). That removes the usual lead-review independence layer, so
independence here rests on things the lead did **not** author: (1) NASA's own
published FEM/test numbers (inputs hashed read-only, proven unchanged start↔end;
our Python matches NASA's FEM-vs-test error to ~2.5 pp on 19/24 modes), and
(2) the artifact-backed `check.py` + analytic element-library validation.
A third layer — an **independent second-solver re-solve of our deck** — is
**prepared but deferred** (`femap_handoff/` decks + instructions are ready):
the available FEMAP/NX is a student license whose node cap (~hundreds) cannot
load the 67,683-grid model, so this is logged as an optional follow-up (D32),
NOT claimed as done.

**Two-session history (D16, D19, D20, D21).** Two Claude sessions were
accidentally given the same handoff and worked the same workspace in parallel.
This was fully reconciled in the decisions log: a `run_nuts.py` first draft
flagged as "unaccounted-for" (D16) turned out to be this lead session's own
earlier draft (D19) — no third-party code, no integrity breach; the cautious
"do not adopt unverified code" response was correct procedure, and the canonical
implementation (Hungarian unique pairing, sequential chains, stop-gradient
tracking) is the better one and was kept. One band NUTS job was found running in
**system** python3.9 with an *unpinned* jax (violating the env pin) and burning
~726 % CPU on BLAS thread-thrash; it was killed and relaunched in the pinned
`.venv_nuts` with threads pinned to 1 (D20). Session 3 (this one) re-verified
before touching anything that the in-flight jobs were the correctly pinned venv,
not a repeat of that violation (D24). Full authorship map: `decisions_log.md`
D19 + `manifest.json`.

**Task 0 (provenance gate) — resolved.** Before any modeling, the measured set
was proven to be genuine test data, not FEM output:
`Final_FF_Test_Shapes_100121.ash` = 33 measured modes with real shape vectors;
`TAM_FF/Modes.pch` is the FEM/TAM, not test (`measured_modes_provenance.md`).

---

## 2. The build and its validation (pre-calibration)

From-scratch Python assembly of NASA's `FEM_20211021` deck (no pyNastran, no
external solver): 67,683 grids / ~406k DOFs, 67,366 CQUAD4, 428 CTRIA3, 166
CBUSH, 80 CONM2, 150 RBE2 (after dropping the massless/stiffness-free
`Shock_Test_Instrumentation.blk`, D10). Stiffness is stored per-PID so
`K(theta) = K_fixed + sum_g theta_g K_g` scales part-group moduli exactly.

| check | ours | reference | result |
|---|---|---|---|
| total weight | 127.783 lb | 127.89 lb (NASA pptx s.55) | −0.084 % |
| CG z | 28.014 in | 28.01 in | ~0.004 in |
| rigid translation energy | ~1e-15 rel | 0 | exact |
| rigid rotation energy | 1.2e-7 rel | 0 | flat-facet residual (D12 K6ROT penalty) |
| 6 rigid-body modes | ≤ 1.13 Hz | ≈ 0 | ≪ 54.6 Hz first elastic |
| element library | QM6 −0.37 %, MITC4 −0.47 %, DKT −0.33 %, CST exact | analytic | ALL_OK |

**Model-form error measurement (`fem_assembly_report.md` §4).** On 19 of 24
NASA-paired modes, our nominal frequency error vs test **matches NASA's own NX
Nastran FEM error** to within ~2.5 percentage points (often a few tenths). That
means the Python element library reproduces NX Nastran on this model, and the
residual test-vs-FEM gap is the genuine discrepancy that calibration targets.
Nothing in the build was tuned toward the test. Nominal correlation figure:
`figures/nominal_correlation.png` (median |err| pre-calibration ≈ 4 %).

---

## 3. Reduction (Discretization-Resolution gate)

Basis = 74 nominal elastic modes (54.6–321.7 Hz). `reduction_report.json`:
- nominal consistency: max relative eigenvalue error **6.4e-10** (exact);
- box modulus split ±20 %: max **0.60 %**, median 0.10 % (42 modes < 280 Hz);
- joints+contact ×0.5 (beyond the 95 % prior range): max **2.7 %**, median 0.50 %.

Multi-snapshot **basis enrichment was abandoned on compute cost** (D18): each
off-nominal full eigensolve is ~10 min and ARPACK convergence degrades at soft
joints, making 6 solves intractable this session. `enrich_basis.py` is kept and
replayable. The loop is instead closed where it matters — **one full sparse
eigensolve at the converged full-run posterior-median theta** compares reduced
vs full for every mode < 280 Hz:

> **Reduced-vs-full at the posterior theta (`posterior_validation.json`):**
> max |df|/f = **0.068 %**, median **0.012 %** over **43** modes < 280 Hz — far
> under the 1 % gate. *(D29: validated at the converged 18-mode `theta_full`
> median, the region the deployed twin uses.)*

**Limitation stated:** away from that point the bound is the ±0.6–2.7 % probe
range; no enriched basis was built.

---

## 4. Inference results — three designs, gate-checked

All runs: NUTS, 4 chains, sequential, dense mass matrix, `target_accept = 0.9`.
Gate (AGENTS.md): max R-hat ≤ 1.05, min ESS ≥ 200 (over **all** sampled
variables incl. raw latents), divergence fraction < 2 %.

| design | held-in / held-out | warmup+draws, tree depth | worst R-hat | min ESS | div | **status** | held-out coverage |
|---|---|---|---|---|---|---|---|
| **Full (headline posterior)** | 18 / — (in-sample) | 1000+1000, d8 | **1.022** | **232** | 0 | **GREEN** | n/a (in-sample) |
| Band extrapolation | 6 (≤120 Hz) / 12 (120–222 Hz) | 2000+2000, d10 | 1.076 | 63 | 0 | **YELLOW** | **10/12** predictive |
| Band — first attempt (kept) | same | 1000+1000, d8 | 1.916 | 3 | 0 | YELLOW (broken, kept as evidence) | 11/12 |
| LOMO (×18) | 17 / 1, each | 1000+1000, d8 | **2.503** | 2.5 | 0 | **YELLOW** | **18/18** predictive |

(GREEN = convergence gate met; YELLOW = documented not-converged finding,
intervals not-trustworthy, never reported as converged — see §10.)

Figure: `figures/convergence_summary.png` (worst R-hat per run vs the 1.05 gate;
ESS annotated; divergences = 0 everywhere).

**Why 0 divergences matters.** Zero divergences with high R-hat means the chains
are *not* hitting pathological curvature — they are sitting in **different
posterior modes**. That is the signature of genuine multimodality /
under-identification, not a sampler bug. More compute (band: depth-10, 4× draws)
moved worst R-hat 1.92 → 1.08 but did **not** close the gap: 6 held-in
log-frequencies cannot identify 9 stiffness groups.

### 4a. Full posterior (the converged headline) — partial identifiability

`theta_full.json`, gate **PASS** (R-hat 1.022, ESS 232, 0 div).
`sigma_f` median = **0.046 (4.6 %)**, 95 % CI [3.4 %, 6.7 %].

> **Read `sigma_f` against the replicate noise floor.** The impact-run frequency
> repeatability is median **0.30 %**, p90 **0.93 %** (`noise_floor.json`). The
> inferred `sigma_f ≈ 4.6 %` is ~5–15× that floor ⇒ the residual is dominated by
> **model-form / element discrepancy**, not measurement noise (exactly the read
> stated up front in assumption A9). The twin is biased at the ~few-percent
> level and the posterior honestly reports it through a large `sigma_f`.

**Which groups the data actually informs** (posterior 95 % CI vs the prior 95 %
range [0.613, 1.632]; figure `figures/theta_posterior_full.png`):

| group | posterior median | 95 % CI | informed? |
|---|---|---|---|
| bottom_box | 0.964 | [0.899, 1.029] | **yes** (tight) |
| top_box | 1.048 | [0.944, 1.141] | **yes** |
| plates | 0.976 | [0.728, 1.279] | **yes** (partial) |
| cross_beam | 1.038 | [0.753, 1.399] | **yes** (partial) |
| joints | 1.093 | [0.681, 1.703] | no — ~prior |
| contact | 0.984 | [0.583, 1.601] | no — ~prior |
| al_welds | 1.019 | [0.624, 1.698] | no — ~prior |
| angle_brackets | 1.010 | [0.624, 1.643] | no — ~prior |
| steel_welds | 1.012 | [0.607, 1.693] | no — ~prior |

**Finding:** only **4 of 9** groups are identifiable from modes ≤ 222 Hz; the
other 5 (including, notably, the NASA-hand-tuned **joints**) sit at the prior —
the modal data below 222 Hz barely constrains them. This **cross-confirms** the
independent pre-test FIM identifiability analysis on a different model
(`artifacts/reports/fim_identifiability_opus_20260609/`), which found only ~3
stiffness parameters identifiable from modal data. The held-out designs go
multimodal precisely because withholding modes removes the few constraints that
pin the identifiable subspace.

**Why — modal strain-energy decomposition (`joint_strain_energy.py` →
`joint_strain_energy.json`; Modal Identifiability Gate).** Identifiability of a
group is governed by the modal strain energy the calibration modes store in it
(`∂λ_i/∂θ_g = φ_iᵀ K_g φ_i = 2·SE`, which is the diagonal of the reduced block
`A[g]`; fractions close to 1.000000). Mean / peak SE fraction over the 18 modes:

| group | mean SE % | peak SE % | identified? |
|---|---|---|---|
| bottom_box | 46.8 | 99.4 | yes |
| top_box | 34.9 | 85.5 | yes |
| plates | 7.1 | 57.7 | yes |
| cross_beam | 5.5 | 49.8 | yes |
| **joints** | **3.1** | **19.0 (mode 12, 147 Hz)** | no (borderline) |
| angle_brackets | 1.2 | 14.3 | no |
| al_welds | 0.7 | 2.1 | no |
| steel_welds | 0.5 | 1.9 | no |
| contact | 0.2 | 1.5 | no |

**Mechanism (important nuance):** the joints are **not** out of the load path —
they carry real strain energy (peak **19 % in mode 12**, >5 % in 4 modes, more
than the welds/contact), and the finite ×0.5 joint softening moves frequencies
2.71 % (in-path, near-rigid). They are unidentified because their **per-mode
sensitivity (~3 % mean) sits below the σ_f ≈ 4.6 % model-discrepancy floor** —
signal *below noise*, not signal *absent*. The identifiable groups all clear
~5 %+; the joints are the borderline case, their evidence concentrated in a few
modes (notably mode 12 at 147 Hz — which was itself a band held-out miss). So
the limit is **model-form discrepancy, not joint irrelevance**: a lower-σ_f
forward model or a test that excites the ~147 Hz joint-active band would make
the joints identifiable. This is the pre-test lever, and it matters downstream —
a payload mount is a joint, and joints do drive the 120–185 Hz band.

### 4b. Band extrapolation (calibrate low, predict high) — coverage 10/12

Held-in = 6 modes ≤ 120 Hz; held-out = 12 modes 120–222 Hz. Worst R-hat 1.076,
min ESS 63 — **not converged**; predictions are reported with that caveat.
Predictive coverage **10/12**; the two misses are test 12 (−9.3 %) and test 14
(+9.9 %). Figure: `figures/heldout_qoi_sidebyside_band.png` (thick bar =
parameter CI, thin = +noise predictive; red ♦ = measured). Predictions are
locked before reveal: `heldout_lock.json` (held-out frequencies never enter the
likelihood — structural guarantee, plus a SHA-256 of the prediction fields).

### 4c. LOMO (leave-one-mode-out ×18) — coverage 18/18, but not converged

Each run holds out one of the 18 clean modes and predicts it from the other 17.
Predictive coverage **18/18 (100 %)**, parameter coverage 9/18, worst-over-runs
R-hat **2.503**, min ESS 2.5, 0 div (only mode 8 individually passes the gate:
R-hat 1.015, ESS 442). Figure: `figures/heldout_qoi_sidebyside_lomo.png` (each
row annotated with its own R-hat where > 1.05).

> **The honest headline in one sentence.** The held-out *frequencies* predict
> well (band 10/12, LOMO 18/18) **because** the predictable quantity lives in the
> identifiable subspace, while the *parameters themselves* are multimodal and
> not gate-converged in the withheld-mode designs — wide predictive bands that
> still cover are a feature of an under-identified posterior, not evidence of a
> clean fit.

---

## 5. Held-out QOI tables (both designs, full numbers)

**Band design — held-out (12 modes), `heldout_band.json`:**

| test | f_meas [Hz] | pred median | 95 % pred CI | err % | covered? | MAC |
|---|---|---|---|---|---|---|
| 8 | 125.03 | 120.29 | [110.9, 130.3] | −3.8 | yes | 0.33 |
| 10 | 142.44 | 150.47 | [139.1, 164.0] | +5.6 | yes | 0.48 |
| 11 | 151.19 | 157.64 | [142.2, 171.1] | +4.3 | yes | 0.61 |
| 12 | 158.17 | 143.40 | [132.0, 157.4] | −9.3 | **MISS** | 0.53 |
| 13 | 165.88 | 166.53 | [150.0, 181.2] | +0.4 | yes | 0.75 |
| 14 | 167.99 | 184.57 | [170.8, 199.0] | +9.9 | **MISS** | 0.70 |
| 15 | 172.26 | 185.88 | [172.0, 200.4] | +7.9 | yes | 0.73 |
| 16 | 174.77 | 171.44 | [156.1, 185.4] | −1.9 | yes | 0.69 |
| 17 | 184.36 | 190.39 | [171.2, 207.5] | +3.3 | yes | 0.88 |
| 18 | 188.64 | 197.42 | [178.2, 214.5] | +4.7 | yes | 0.70 |
| 21 | 197.82 | 201.68 | [184.2, 217.8] | +2.0 | yes | 0.65 |
| 25 | 222.17 | 212.50 | [196.7, 228.9] | −4.4 | yes | 0.62 |

Coverage 10/12; median |err| ≈ 4.3 %. (Worst R-hat 1.076 — intervals not
gate-converged.)

LOMO per-mode table with per-run R-hat: `heldout_lomo.json` (18 rows) and
`figures/heldout_qoi_sidebyside_lomo.png`.

---

## 6. Sensitivity arms (`sensitivity.py` → `sensitivity.json`)

Varies the assumptions most likely to move the held-out QOI (band design,
600+600 draws — decision scan, not the headline). Arms: prior width `NSIG ∈
{0.15, 0.25, 0.40}`; likelihood frequency-only vs frequency+MAC; band edge
≤120 Hz vs ≤150 Hz.

**Arm results (`sensitivity.json`):**

| arm | held-in | prior sd | likelihood | held-out coverage | median \|err\| | worst R-hat | div | **status** |
|---|---|---|---|---|---|---|---|---|
| prior_sd_0.15 | 6 (≤120) | 0.15 | freq | 0.83 (10/12) | 4.05 % | 1.103 | 0 | YELLOW |
| baseline_sd_0.25 | 6 (≤120) | 0.25 | freq | 0.83 (10/12) | 4.51 % | 1.157 | 0 | YELLOW |
| prior_sd_0.40 | 6 (≤120) | 0.40 | freq | 0.75 (9/12) | 4.01 % | 1.348 | 0 | YELLOW |
| **freq+MAC** | 6 (≤120) | 0.25 | **freq + MAC** | 1.00 (12/12) | 3.66 % | **2.971** | **82** | YELLOW (divergent) |
| band ≤150 Hz | 8 (≤150) | 0.25 | freq | 0.70 (7/10) | 5.91 % | **4.252** | 0 | YELLOW |

(These arms use 600+600 draws — a decision scan, not the headline run; every arm
is non-converged = YELLOW, which is itself the point.)

**What the arms show:**
- **Prior width:** widening the prior (0.15→0.40) loosens coverage (0.83→0.75)
  and worsens R-hat (1.10→1.35), exactly because the unidentified groups have
  more room to wander into a second mode. The identified-group medians move
  little. Conclusion robust to prior width within the multimodal regime.
- **MAC pseudo-likelihood:** coverage rises to 12/12, but with **82 divergences
  and R-hat 2.97** — the near-degenerate eigenvector-gradient hazard predicted
  in Section 0 materializes. The MAC term buys apparent coverage at the cost of
  a broken sampler; this is exactly why it is an arm, not the headline.
- **Band ≤150 Hz:** adding two more (lower-MAC) held-in modes makes things
  **worse** — coverage 0.70, R-hat 4.25. The band-extrapolation gap is
  **identifiability-limited, not data-quantity-limited**: more low-MAC modes
  deepen the multimodality rather than pin the parameters.

**Decision-sensitivity verdict:** the held-out QOI in the band design is
*fragile* and dominated by under-identification / model discrepancy, not by
prior choice. The converged full-data posterior (Section 4a) is the stable
result; the held-out designs are the honest stress test that exposes the
fragility.

---

## 7. Independent second-solver cross-check — PREPARED, DEFERRED (optional)

`femap_handoff/` contains self-contained normal-modes decks at **nominal** theta
(`shocksat_modal_twin_nominal.dat`) and at the **converged posterior-mean** theta
(`shocksat_modal_twin_posterior.dat`, from `theta_full.json` `theta_mean`), plus
`femap_instructions.md`. Re-solving our deck in an independent NASTRAN-class
solver and diffing the first ~25 elastic frequencies against `nominal_modes.json`
/ the posterior predictions would be the cleanest independent check of the Python
assembly and the calibrated stiffness.

**Status: not yet run (D32).** The available FEMAP/NX is a **student license**
whose node cap cannot load the 67,683-grid model, so this step is **deferred as
an optional follow-up**. Paths when convenient: (a) Purdue full NX Nastran/FEMAP
(no cap) = gold-standard independent-operator solve; (b) MYSTRAN (free, no cap,
our deck is self-contained) = different-code check. Until then, independence
rests on NASA's published NX numbers (§2) and the analytic element validation —
this packet does **not** claim a completed independent re-solve.

---

## 8. Runtime accounting (`runtime.json`)

`runtime.json`: **active_runtime_s = 38,099 s** (sum of per-command execution
times — the cross-runner metric; excludes human-approval wait) vs
**elapsed_wallclock_s = 63,791 s** (task calendar span incl. the overnight
human-approval gap). Largest components: 18 LOMO runs (21,573 s command-sum, run
**4-way parallel** so ~1.5 h wall), the depth-10 band remedy (8,430 s), the
sensitivity arms (4,215 s), the full calibration (885 s), failrun1 band (855 s),
the posterior-validation full eigensolve (251 s), plus the session-2 build/probe
work (~1,770 s). All processes single-threaded (OMP/VECLIB pinned to 1);
`active_runtime_s <= elapsed_wallclock_s` holds against the calendar span.

---

## 9. Limitations and what would change the conclusion

- **Partial identifiability is the core result.** ~4/9 groups informed; the
  joints (hand-tuned, physically interesting) are **not** identified by modes
  ≤ 222 Hz. A higher-frequency or joint-localized test, or a coarser
  parameterization (fewer groups), would be needed to identify them — this is a
  pre-test design recommendation, not a fitting failure.
- **`sigma_f ≈ 4.6 %` ≫ 0.3–0.9 % noise floor** ⇒ model-form discrepancy
  dominates; `theta` is partly absorbing element/flat-facet bias. The held-out
  coverage is the detector that keeps this honest.
- **Band and LOMO are not gate-converged** (multimodal). Their coverage numbers
  are reported with worst-case R-hat/ESS attached and must not be read as
  converged credible intervals.
- **No enriched reduction basis** (cost); validated only at nominal and at the
  posterior theta.
- **MAC is a pseudo-likelihood**, used for pairing and as a sensitivity arm, not
  as the primary likelihood (near-degenerate eigenvector-gradient hazard).
- **One test article; no build-to-build variability** modeled.
- **No independent second-solver re-solve yet** (D32): the prepared FEMAP decks
  cannot run on the available student license (node cap vs 67,683 grids).
  Independence currently rests on NASA's published NX numbers + analytic element
  validation; a full-license/MYSTRAN solve is an optional follow-up.

## 10. Checker — green / yellow / red

`check.py` reports each gate and the overall result on a three-tier light
(AGENTS.md "Result Status Standard"): **GREEN** = threshold met; **YELLOW** =
threshold not met but documented, understood, non-fatal, usable only with the
stated caveat (never "converged"/success); **RED** = blocking.

**Overall: YELLOW — 15 green, 2 yellow, 0 red** (`checker_report.json`):
- **GREEN (15):** inputs unchanged, Task 0, mass/CG/rigid-energy, 6 RBMs,
  nominal-vs-NASA, reduction nominal-exact + at-posterior-θ, **`convergence_full`**
  (R-hat 1.022, ESS 232), both held-out tables, lock, modal-only, figures.
- **YELLOW (2):** `convergence_band` (R-hat 1.076, ESS 63) and
  `convergence_lomo_worst_over_runs` (worst R-hat 2.503, ESS 2) — the **documented
  multimodality findings** of Section 4. Worst-case R-hat/ESS are surfaced here,
  on the figures, and next to every interval; these intervals are labeled
  not-trustworthy and are **never** reported as converged.
- **RED (0).**

No convergence gate was relaxed to manufacture a pass — the yellow tier is an
honesty label, not a softened pass. Because overall is yellow (not red),
`check.py` exits 0 so the one-command replay completes; a red would block.
</content>
</invoke>
