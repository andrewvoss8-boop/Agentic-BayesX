# Search-Runner Packet — Modeling-Freedom / Anti-Overfitting Experiment

**Runner:** Claude Code (Opus), SEARCH RUNNER session, scoped to `runner_opus/`.
**Date:** 2026-06-09. **Status:** finalists LOCKED, vault NOT accessed.

> **READ THIS FIRST — NO WINNER IS VALIDATED.** This run is a *methodology* study, not science
> completion. Nothing here is "the best model." The only honest claim is: *I tried N=31
> configurations, here is how they behaved on a held-out dev set and under the convergence gate,
> and here are 3 locked finalists.* The true test happens **only when the human re-downloads the
> sealed vault and runs `../scripts/score_vault.py`** on the locked finalists. I never touched the
> vault, the parked ShockSat science, or the truth generator.

---

## 0. Plain-English orientation (for the ML/stats reader)

A few terms used throughout, defined once with units:

- **Posterior:** after seeing data, our updated probability distribution over unknown model
  parameters. Intuition: start with a prior belief, multiply by how well each parameter setting
  explains the data (the *likelihood*), renormalize.
- **NUTS / HMC (No-U-Turn Sampler / Hamiltonian Monte Carlo):** the gradient-based algorithm we
  use to draw samples from the posterior. It needs a differentiable model. It is our default
  sampler per project rules.
- **Log predictive density (LPD), units = nats (natural-log probability):** how well a fitted
  model predicts *held-out* data. Higher = better. Concrete example: if the model says a held-out
  frequency is N(192 Hz, 1 Hz) and the true held-out value is 192 Hz, the log-density is high; if
  the model predicted N(170 Hz, 1 Hz) it is very negative. We sum LPD over all held-out
  observation units. **This is our selection score ("dev score").**
- **WAIC (Widely Applicable Information Criterion), nats:** an in-sample estimate of held-out
  predictive accuracy that *penalizes* effective model complexity. We report it as a cross-check.
- **R-hat (potential scale reduction):** a convergence diagnostic comparing variance between vs
  within independent MCMC chains. 1.00 = chains agree; > 1.05 = not converged.
- **ESS (effective sample size):** how many *independent* posterior draws our correlated MCMC
  draws are worth. Low ESS = unreliable summaries.
- **Divergence:** an HMC failure flag indicating the sampler could not integrate the posterior
  geometry (often a sign of a pathological/over-flexible model). We track the divergence fraction.
- **Discrepancy / model-form error:** an extra term we add to admit "our physics model is
  imperfect." Intuition: if the model systematically predicts a mode 8% too low, a discrepancy
  term can absorb that 8% so the noise model is not blamed for it.
- **MAC (Modal Assurance Criterion), 0–1, dimensionless:** mode-shape agreement between two mode
  vectors (1 = identical shape, 0 = orthogonal). Standard structural-dynamics quantity.

The **convergence gate** (a hard project rule, not negotiable here): a config is **disqualified**
from finalists if max R-hat > 1.05, OR min ESS < 200, OR divergence ≥ 2%, measured over **all**
sampled variables including raw hierarchical latents — *even if its dev score is great.*

---

## 1. Method summary (the first-pass the contract requires)

### 1.1 Substrate A — synthetic tray (the core of this study)
- **Forward model (my modeling choice; the truth generator was NOT read):** a grounded
  **fixed-free 12-DOF mass-spring chain**, uniform mass `m = 1` (mass matrix `M = I`), 12 springs
  in **4 groups of 3**, each group scaled by a stiffness factor `theta_g` times `k0 = 3.0e6`
  (so `theta` is a length-4 vector, the calibrated parameters). **No cross-link joint** — the
  public config states the candidate model omits it; that omission is the *deliberate model-form
  error* the run must contend with.
  - Verified self-consistency: the model's 8-sensor mode-shape sub-vectors have norm ≈ 0.81–0.86,
    matching the observed mass-normalized data (a 12-vector sliced to 8 DOFs). Best least-squares
    `theta` fit leaves **5–10 % frequency residual and MAC 0.90–0.96** — far above the 0.5 %
    frequency / 0.02 shape noise. That residual *is* the missing joint.
- **Data count:** 12 noisy modal realizations total = **8 train + 4 dev** (the sealed vault holds
  6 more + the true `theta`, the true joint, true modes, two QOIs, and the seed). Each realization
  = 6 modal frequencies (Hz) + 6 mode shapes sampled at 8 sensor DOFs.
- **Likelihood (whole modal vector — stated explicitly):**
  - `log f_obs[r,j] ~ Normal( log f_model_j(theta) + d_j , sigma_f )`  (per realization r, mode j)
  - `phi_obs[r,:,j] ~ Normal( s_j · phi_model_sens[:,j] + g[:,j] , sigma_phi )`
  - `d_j` = per-mode frequency discrepancy (shared across realizations); `g[:,j]` = per-mode
    shape discrepancy; `s_j = ±1` deterministic sign alignment of model to a data reference.
  - One ablation swaps to a **frequency-only ("feature/peak summary") likelihood** that drops the
    mode-shape term.
- **Inferred variables:** `theta` (4 stiffness factors), observation noises `sigma_f`,
  `sigma_phi`, discrepancy hyper-scales `tau_f`/`tau_phi`, and the raw non-centered latents
  `d_z`, `g_z`. **Fixed assumptions:** topology, `m = 1`, `k0 = 3e6`, 4-group structure, damping
  `zeta = 0.02`, sensor set. **Non-inferred:** the cross-link joint (intentionally absent).
- **Sampler:** NUTS (numpyro 0.19.0, JAX float64 forced), **4 chains**, **non-centered** for the
  hierarchical discrepancy by default. Diagnostics via `numpyro.diagnostics` (arviz was
  unavailable due to a scipy incompatibility — labeled, not hidden).

### 1.2 Run-specific graphical model (text diagram, not copied from any paper)
```
        priors                          per-mode discrepancy (model-form error)
  log_theta ~ N(0, pw)   tau_f ~ HN(.)   d_j = tau_f·z_j        tau_phi ~ HN(.)   g = tau_phi·zg
        |                                   |                                          |
        v            12-DOF fixed-free      v   (shared across realizations)           v
     theta  ---->  eig(K(theta), I) ---->  f_model_j , phi_model_j  --(+d, +g)-->  predicted modes
                                                                                      |
   sigma_f, sigma_phi ~ HalfNormal  ----------------------------------------------->  Normal likelihood
                                                                                      |
                                              observed: f_obs[r,j] (Hz), phi_obs[r,:,j]  (r=1..8 train)
        QOI = peak |receptance H_{out,in}(w)| over 10–600 Hz, from theta only (NOT from d,g)
```

### 1.3 Substrate B — ShockSat real (secondary, real hardware)
- Observation layer = **free-free modal correlation on the 1101–7105 grids**: test modes
  (`Modes.pch`) vs an analysis **Test-Analysis Model** built from the reduced superelement
  matrices `KAAX`/`MAAX` in `TAM.pch` (I solved `eig(KAAX, MAAX)`; the a-set DOFs *are* the
  translational correlation DOFs, so MAC is computed directly — no expansion needed). The SOL111
  FRF `.pch` was used for **nothing** (it is a frequency-alignment diagnostic only, per the parked
  normalization finding; magnitude FRF overlay would be invalid — different transfer paths).
- I read **only raw data files** granted by `inputs_manifest.json`; I did **not** open any parked
  report/notes/findings. The read-only inputs' SHA256 are unchanged after the run (verified).

---

## 2. The search: N = 31 configs (the garden of forking paths, made visible)

Every config is logged in [results_table.csv](results_table.csv): model form, discrepancy, priors,
hyperparameters, dev-LPD, WAIC, **R-hat / ESS / divergence**, gate pass/fail, query index,
timestamp, posterior `theta`, and QOI. Breakdown: 10 MAIN candidates, 7 mandatory ablations,
14 probe configs (4 per-realization "wild" + 10 adaptive-ramp).

**Reusable-holdout discipline (Thresholdout-style).** Reusing the same dev set to pick among many
configs inflates the dev score above true generalization. I measured the dev-LPD noise: sampler
re-seed scatter ≈ 0.13 nats; the *holdout* statistical scale (spread of per-realization dev-LPD,
≈1.97, → standard error of the 4-realization sum ≈ 1.97·√4 ≈ **3.9 nats**). I set the registration
**threshold = 4.0 nats** and only "register" an improvement if a jittered dev-LPD beats the best
registered by > 4.0. This slows adaptive overfitting; see the `registered_improvement` column.

---

## 3. The headline finding (honest, and a little surprising)

In *this* problem the mode shapes pin `theta` so strongly that **flexible discrepancy terms do not
inflate the dev score** — the dev-LPD climbs only while the discrepancy captures the *real* missing
joint, then **plateaus** (Figure 2 left, Figure 3). So the "dev score quietly creeps up as you add
flexibility" picture is *muted* here. Instead the overfitting shows up two other ways:

1. **`theta` drift caught by the convergence gate.** When I push flexibility past what the data
   support (wide shape discrepancy, fixed-too-tight noise, centered parameterization, or
   per-realization deltas), the softest-group stiffness `theta_4` **drifts from ≈ 0.89 up to
   1.4–1.9** — and *exactly those* configs **fail the convergence gate** (R-hat 10–33,
   divergences 4–18 %). See Figure 2 right. The gate is doing the anti-overfitting work.
2. **The dev score is insensitive to the drift.** The single **highest** dev-LPD in the whole
   search (569.25, config 31) comes from a *drifted, gate-failing* model. If we naively chased dev
   alone we would select a disqualified model whose `theta`/QOI are wrong (Figure 3). This is the
   core argument for keeping an **independent** check — the convergence gate, and the vault's true
   `theta`/QOI — rather than trusting the dev score.

**What the vault will adjudicate.** All three locked finalists have nearly identical `theta`
(≈ [1.30, 0.97, 1.38, 0.89]) and QOI, but very different modal fit. The vault will reveal (a)
whether that `theta`/QOI is actually close to truth, and (b) the **dev-vs-vault gap** — how much our
dev-LPD over-stated generalization. I cannot compute this; the human does, after re-download.

---

## 4. Finalists (LOCKED — see [finalists.json](finalists.json))

| id | discrepancy | dev-LPD | max R-hat | min ESS | div | pred θ (4) | QOI_ref (m/N) | QOI_held (m/N) |
|---|---|---|---|---|---|---|---|---|
| **F1** freqshape (freq+shape disc.) | full modal | **569.13** | 1.015 | 370 | 0 % | 1.303, 0.972, 1.354, 0.891 | 8.23e-6 | 4.60e-5 |
| **F2** freq disc. only | full modal | 389.27 | 1.016 | 448 | 0 % | 1.284, 0.950, 1.368, 0.875 | 8.32e-6 | 4.68e-5 |
| **F3** no discrepancy | full modal | 323.18 | 1.002 | 1054 | 0 % | 1.318, 0.979, 1.383, 0.897 | 8.11e-6 | 4.55e-5 |

All three **pass** the convergence gate over all sampled variables (116 / 19 / 6 scalar latents
respectively, including the raw `d_z`, `g_z`). They were chosen as the top gate-passing configs
spanning the **discrepancy ladder** (none → freq → freq+shape) so the vault can show what each level
of model-form flexibility buys (or costs) on the *true* parameters. F1 matches the observed modes
well; F3 (no discrepancy) misses them by 5–13 % (Figure 7) **yet predicts essentially the same
`theta`/QOI** — the central tension of this experiment.

**QOI definition (committed; the vault's exact definition was not readable):** QOI = peak receptance
magnitude `max_w |H_{out,in}(w)|` over 10–600 Hz, `H_jk(w)=Σ_n φ_jn φ_kn /(ω_n²−ω²+2iζω_nω)`,
mass-normalized modes, `ζ=0.02`, units m/N; `ref` path = DOF 11←0, `heldout` path = DOF 5←8.
*Limitation:* the QOI is computed from the `theta`-model receptance and does **not** propagate the
discrepancy `d`,`g`; so all finalists share the same missing-joint QOI bias. If the vault scorer
uses a different scalar, absolute QOI error will not be comparable, but the cross-finalist ranking
will. Flagged in [decisions_log.md](decisions_log.md) and [priority_deliverables.md](priority_deliverables.md).

---

## 5. Mandatory ablations (same dev pipeline) — see `ablations/` rows in results_table & Figure 4

| Ablation | dev-LPD | gate | reading |
|---|---|---|---|
| Drop discrepancy (none) | 323.2 | pass | discrepancy earns ~246 nats → real model-form error exists |
| Prior width 0.1 (narrow) | 569.1 | pass | `theta` well-identified; prior width barely matters |
| Prior width 0.7 (wide) | 568.9 | pass | same — likelihood dominates the prior |
| Coarsen to 4 modes | 377.9 | pass | fewer observations → lower LPD; `theta` shifts (resolution matters) |
| Coarsen to 3 modes | 279.8 | pass | further drop; QOI-driving high modes lost |
| **Centered** parameterization | 562.2 | **FAIL** (R-hat 33) | non-centered is *necessary* for the hierarchical variance |
| Non-centered (reference) | 569.1 | pass | the default that works |

The centered-vs-non-centered ablation is a clean hit: same model, only the parameterization
differs, and the centered one is **disqualified** by the gate — exactly the project rule that
hierarchical variance models use non-centered parameterization.

---

## 6. Deliberate-overfit probe (`overfit_probe/`, Figure 3) — testing the guardrails

Two arms, both required to *try* to overfit:

- **Arm A — per-realization "wild" discrepancy** (`delta[r,j]`, one per realization×mode, weak/wide
  priors, no restraint): this is the over-flexible additive per-mode discrepancy the contract asks
  for. Result: it does **not** improve dev-LPD (per-realization deltas can't transfer to held-out
  realizations) **and it fails the convergence gate** (divergences 4–7 %, R-hat up to 17.6). Caught.
- **Arm B — adaptive garden-of-forking-paths:** 10 queries that greedily grow flexibility while
  peeking at dev. The naive "best dev so far" climbs 323 → 382 → 569 and then nudges up to **569.25
  at a GATE-FAILING config**. The reusable-holdout (Thresholdout) curve registers only the real
  jumps and then flattens at 568.7. Figure 3 marks the gate-failing endpoint with an open circle:
  **naive dev-chasing walks you straight into a disqualified model; the gate + reusable-holdout
  hold the line.**

This is the wanted outcome: overfitting *appeared*, and two guardrails (convergence gate;
reusable-holdout + the forthcoming vault) surfaced it. We still need the vault to quantify the
dev-vs-vault gap on the true parameters.

---

## 7. Convergence table (all finalists, all sampled variables) — `diagnostics/`, Figure 5

| finalist | # sampled scalars (incl. raw latents) | max R-hat (worst var) | min ESS (worst var) | divergence |
|---|---|---|---|---|
| F1 freqshape | 116 (incl. `d_z`×6, `g_z`×48) | 1.015 | 370 | 0.0 % |
| F2 freq | 19 (incl. `d_z`×6) | 1.016 | 448 | 0.0 % |
| F3 none | 6 (`log_theta`, σ's) | 1.002 | 1054 | 0.0 % |

Per-variable R-hat/ESS JSON and theta trace/posterior plots are saved per finalist. **No finalist
is reported as "converged" unless it passes; the gate-failing configs in §3/§5/§6 are labeled
disqualified, not passes.** NUTS/HMC was active and is the only sampler used (no fallback needed).

---

## 8. ShockSat real-data result (`shocksat_predictions.json`, Figure 6)

Genuine free-free modal correlation, test (`Modes.pch`) vs analysis TAM (`KAAX`/`MAAX`):
- **Physics check passes:** exactly **6 rigid-body modes < 1 Hz** (free-free, as required);
  first elastic mode 59.19 Hz (test) vs 59.55 Hz (TAM), MAC = 1.00.
- **Held-in modal self-estimate (leave-one-mode-out; each mode an independent correlation, no
  parameters fit to it):** 38 elastic modes paired, **MAC median 0.956**, 66 % above 0.9,
  **|frequency error| median ≈ 1 %** in the low band, **growing to ~10–23 %** at high modes. The
  twin is validated to ≈ **152 Hz** (contiguous MAC>0.9 & error<5 %).
- **Committed PYRO-regime QOI = out-of-distribution extrapolation, LOW CONFIDENCE.** The exact
  pyro-NSD QOI definition lives in the held-out (forbidden) manifest, which I did not read, and a
  modal-band twin carries no absolute pyro-shock levels. So I commit a *labeled placeholder*: the
  twin's frequency-error trend extrapolated upward, plus the **directional prediction that the twin
  under-resolves the pyro regime** (modal truncation + rising high-mode error → it will
  under-predict pyro response). This is a methodology commitment, not a validated science number.

---

## 9. Assumptions ledger (numbers, units, rationale, sensitivity)

| # | Assumption | Value/units | Rationale | Sensitivity |
|---|---|---|---|---|
| A1 | Chain topology | fixed-free, grounded one end | "grounded 12-DOF chain"; sensor sub-norm ≈0.85 matches data | HIGH — wrong topology biases all θ |
| A2 | Masses | uniform `m=1` (M=I) | config gives no masses; natural nondimensional choice | HIGH — global θ scale trades with m |
| A3 | Spring grouping | 4 groups × 3 springs | config says 4 stiffness groups | MED |
| A4 | Damping | `zeta=0.02` (config) | given | LOW for modes; affects QOI peak height |
| A5 | Obs noise | `sigma_f≈0.005`, `sigma_phi≈0.02` (inferred, prior from config) | calibration | MED (we infer it) |
| A6 | Discrepancy prior | `tau_f,tau_phi ~ HalfNormal(0.05)` default | weakly-informative | MED — wide values trip the gate (§3) |
| A7 | θ prior | `log_theta ~ N(0, 0.3)` default | θ≈1 scale factors | LOW (ablation: 0.1–0.7 negligible) |
| A8 | QOI scalar | peak \|H\| over 10–600 Hz, m/N | standard receptance summary | flagged: may differ from vault def |
| A9 | Missing joint | not inferred | the model-form error under test | the whole point |

**Uncertainty types present:** parameter uncertainty (θ posterior), observation noise
(σ_f, σ_phi), **model discrepancy** (the missing joint, partly absorbed by d/g), test-to-test
variability (12 realizations). **Absent/important:** the joint is not structurally modeled; QOI
ignores discrepancy (§4). Data count: 8 train + 4 dev realizations (6 vaulted).

---

## 10. What would make this the wrong question
If the vault's true `theta`/QOI differ *a lot* across the three finalists' predictions — they don't,
they're nearly identical — then dev-LPD selection among them would matter more and the gap analysis
would be richer. Because the mode shapes over-determine `theta`, the *interesting* failure mode here
is convergence-gate-caught drift, not dev-score inflation. If the experiment wanted a large
dev-vs-vault gap, a harder, less mode-shape-constrained design (fewer sensors, frequency-only data)
would expose it; I note that as a design lesson, not a result.

---

## 11. Reproduce & files
- One command: `bash run_all.sh` (asserts CWD, verifies manifest, runs search + ShockSat +
  figures, writes `runtime.json`, locks `finalists.sha256`). JAX float64 forced; CPU only.
- Runtime: synthetic search active ≈ 428 s over 31 NUTS fits (4 chains each); see `runtime.json`.
- Deliverables: `results_table.csv`, `ablations/` (rows + Figure 4), `overfit_probe/probe_curve.csv`
  + Figure 3, `diagnostics/` (per-finalist convergence JSON + draws + Figure 5), `finalists.json`,
  `shocksat_predictions.json`, `finalists.sha256`, `figures/01–07`, `decisions_log.md`,
  `priority_deliverables.md`, `files_changed.md`.

## 12. Honest limitations
- dev-vs-vault gap is **not computed by me** (vault is off-limits); §3 explains the *expected*
  mechanism only.
- QOI ignores the discrepancy and uses a self-chosen scalar (A8) — absolute QOI error may not match
  the vault scorer.
- ShockSat pyro QOI is a labeled OOD placeholder (§8), not validated.
- arviz unavailable; diagnostics via numpyro (split-R-hat, ESS) — equivalent quantities, labeled.

**Bottom line:** N=31 configs searched under broad freedom; the convergence gate disqualified every
over-flexible (θ-drifting) config, and naive dev-chasing led to a disqualified model — so the
guardrails fired. **No model is declared best; the vault is the next and decisive step.**
