# Bilionis review packet — Agentic BayesX / ShockSat consolidation

**Date:** 2026-06-26 · **Lead:** Andrew Voss · **Lead agent:** Claude Code
**Deck:** `slides/shocksat_bilionis_review.pptx` (31 slides) · **Replay:** `bash run_all.sh`

This is a **consolidation** packet: it pulls real numbers from earlier threads and tells one story.
No new science was run. Every headline number cites a saved `out/*.json` in a named workspace.
Status tags follow `AGENTS.md`: **GREEN** met / **YELLOW** documented honest miss / **RED** blocking;
**EXPLORATORY** = figures+numbers but no immutable checker yet; **CHECKER-BACKED** = SHA-locked grader ran.

> Plain-English note (statistics side): *FRF* = frequency-response function |H(f)|, the per-frequency
> ratio of response to input we predict loads from. *Mode shape* = the deflected pattern at a natural
> frequency. *MAC* (modal assurance criterion, 0–1) = how parallel two mode shapes are. *Discrepancy* =
> a learned correction for where the model is wrong (model-form error). *Held-out* = data hidden from the
> fit, used to test trust. *Skill* = 1 − (twin error)/(no-skill-baseline error); >0 means the twin beats
> guessing. *CI* = credible interval (Bayesian "error bar"). *NUTS* = the default gradient sampler;
> *TMCMC* = a multi-modal-capable sampler we escalate to when NUTS cannot mix.

---

## 1. The objective and the scope reset
The vision (`notes/project_vision.md`) is to take **StatFEM** — fusing a physics finite-element model
(FEM) with test data while explicitly modelling that the model is wrong — from the "parking lot"
(linear-static, model matches data) onto the "track": a real **dynamic** aerospace structure, learn
physics from **real** data, push to a load/margin decision, and stay honest under model error.

**Scope reset for this review (Andrew):** no more building a subscale tray experiment — **work the data we
already have.** We inherited a vendor ShockSat FEM (~406k DOF) already correlated to a NASA modal survey by
the usual standards (mode shapes via MAC, natural frequencies). The question is whether Bayesian updating
makes it a **trustworthy and usable** twin in the **FRF regime**.

---

## 2. The inheritance: correlated on modes, wrong on the FRF  *(P2)*
The FEM is genuinely correlated **on modes** but has **large model-form error on the FRF**:

| quantity | value | source | read |
|---|---|---|---|
| matched global MAC | **0.631** | `psd_envelope/out/correlate_all.json` (baseline) | modes look correlated |
| natural-frequency error | **~2.5–3.3 %** | `bayes_update.json` (3.33 % nominal) | frequencies look correlated |
| per-channel log\|H\| correlation | **~0.27–0.30** | `correlate_all.json` (0.296), `frf_comparison.json` (0.269) | **FRF is NOT correlated** |
| median peak-amplitude error | **~15.7 dB** | `correlate_all.json` | per-point level is wrong |

**Why:** |H| = (drive-mode-shape value)×(sensor-mode-shape value)/damping, so it folds **two** local shape
values plus damping. A model that gets global **frequencies** right can still put the per-point **energy**
in the wrong place. (Plain-English: the model hums at the right pitches but predicts the wrong loudness at
each point.) Status: **EXPLORATORY/YELLOW.**

---

## 3. Bayesian updating: converges, but the MEAN moves only minorly  *(P3, P7)*
**New metric (P7) — does updating move the MEAN closer to the data?** Per-channel correlation between the
twin's predicted **mean** log|H| and the measured log|H|, vs the original inherited FEM (apples-to-apples:
deterministic modal participations + one global gain):

- original inherited FEM: **0.269** → Bayesian-updated mean: **0.338** (**+26 %**); **70 % of 84 channels
  improve**. `frf_comparison.json`. Figure `fig_new_metric.png` (+ 12-channel detail `reuse_frf_grid.png`).
- The mean stays far from a usable correlation (~0.7). **Real but minor.** Status: **EXPLORATORY/YELLOW.**

**How much did the parameters move?** NUTS converged cleanly (R-hat 1.0022, ESS 2243, 0 divergences, 4
chains, 22 pooled modes; `bayes_update.json`). Posterior stiffness multipliers θ_g (median; θ=1 is the
inherited FEM):

- **Identifiable** (tight, moved a little): bottom_box 0.96 (−4 %), top_box 1.03 (+3 %), plates 1.00 (~0 %).
- **Prior-dominated** (wide, ~unmoved): joints, cross_beam, contact, al/steel welds, angle brackets.
- Held-out frequency error **3.33 % → 2.68 %**. Figure `fig_theta_movement.png`.

**Industry read:** a small, defensible refinement of an already-correlated model — not a transformation.
The data simply does not pin most of the knobs.

**Value vs a no-skill baseline** (`value_eval_seed00.json`, CHECKER-BACKED YELLOW): held-out **frequency**
skill **+0.93** (calibration roughly halves the FEM frequency error); per-channel single-impact
**amplitude** skill **−0.76** (easy) to **−2.79** (hard), i.e. **worse than guessing the population** — but
amplitude **coverage 0.97** (the bands honestly contain the truth). Figure `reuse_value_summary.png`.

---

## 4. The central finding: the bands are too WIDE to certify  *(P4)*
This is the honest wall, and it recurs on every dataset (ShockSat single-impact, clean multi-reference, and
the MPL test stand). From the converged clean-multi-ref probe (`probe_seed00.json`, NUTS R-hat 1.0016, ESS
1758, 0 div):

- amplitude discrepancy σ (log) = **1.60** → 97.5 % covering band ≈ **+27.3 dB (PSD)**.
- That is **~10–13×** the GRMS of the standard **FEM+6 dB** envelope engineers use today (per-ref 9.9–12.7,
  combined 10.2).
- **Premise check:** even FEM+6 dB does **not** cover — it leaks **10–61 %** of the held-out band energy.
  Neither a fair FEM margin **nor** a reasonable twin band is both tight **and** covering.
- To reach a usable band you would need σ ≲ 0.35; we are 3–5× above. Figure `fig_wide_ci.png`,
  `reuse_heldout_frf.png`. (Card C single-impact gave a comparable ~34 dB in |H|; `project_vision.md §7.1`.)

Status: **EXPLORATORY/YELLOW (honest negative).** This width is the honest cost of a coarse model + scrappy
data — the regime the robust-twin vision promises to **survive**; making it **sharp** is the open work.

---

## 5. It always came back to MODE SHAPES  *(P5)*
After frequency and damping were already corrected, we mapped **where** the model is wrong
(`residual_map.json`):

- The fundamental **54.2 Hz** mode has the right **frequency** but the wrong **shape**: best MAC over all FEM
  modes ≈ **0.17**. The model misses the deflected shape even at mode 1.
- Worst residuals: the free **steel bottom corner** and the **150–210 Hz** cluster.
- **Shape-oracle test:** give the twin the *measured* shape at a held-out sensor and the amplitude error σ
  drops **1.26 → 0.70** (`shape_diag.json`) — proof the shape **is** the reducible lever, and it is missing.
- But measured shapes do **not** transfer to held-out sensors from single-impact data (borrow-R² ≈ 0,
  `shape_borrow_diag.json`): per-point single-impact |H| is a near-field quantity, not cleanly modal.

Status: **EXPLORATORY/YELLOW.**

---

## 6. Agentic remeshing + Bayesian updating: done, and how successful  *(P6)*
**Yes, both were done** — an agent diagnosed wrong regions and re-meshed / re-parameterized them, and the
best model was fed into the Bayesian updater.

- **~30 data-guided edits** (`correlate_all.json` + `modelform_sweep.json`): finer mesh, joint/box/plate
  stiffness, weld/contact, cross-beam connectivity, and **steel-vs-aluminium mass distribution**. Each
  re-solved (80 modes) and re-correlated. **IMPORTANT:** the sweep scores every remeshed model with **measured
  per-mode frequency + measured per-mode damping** already applied (the oracle of what Bayesian updating
  estimates) + a per-channel participation fit — so the sweep IS "best shapes + best calibration."
- On that generous metric the remesh looks like a **+0.083 (+28%)** gain: inherited shapes
  **0.296 → best-remesh 0.379**. **But we then RAN the literal experiment** (`combine_best.py`): the best remesh
  (al_rho_lo) through the actual modal-feature NUTS, scored on ONE **honest** metric (deterministic participations
  + 1 global gain, no per-channel fitting; self-check reproduced inherited+cal = **0.338** exactly). Result
  (`out/combine_best.json`, figure `fig_combine_best.png`):

  | model (honest metric) | log\|H\| corr |
  |---|---|
  | inherited FEM, no calibration | 0.269 |
  | inherited FEM + calibration | **0.338 (best)** |
  | best remesh + calibration (oracle freq) | 0.267 |
  | best remesh + actual Bayesian θ-posterior | 0.183 |

  **The combination does NOT beat plain calibration — it is worse.** The "+0.08" was a SCORING ARTIFACT: the
  generous metric least-squares-fits one complex amplitude+phase *per mode* (~40–60 knobs) to the *measured* FRFs,
  whereas the honest metric fits one global gain. Remove the fitting and the mass edit worsens the model's own
  predictive shapes; and the Bayesian update (stiffness-group knobs applied to a *mass* error) overfits the
  observed modes, degrading held-out frequency (2.92% → 4.23%; the baseline calibration instead *improves* it,
  3.33% → 2.68%). NUTS
  converged cleanly (R-hat 1.004, ESS 774, 0 div) → a trustworthy negative. **Neither lever nor their combination
  cracks per-point FRF; the wall is mode-shape fidelity — statistics/fitting can mask it, not fix it.**
- **Card D** (CHECKER-BACKED GREEN 14/0/0, `shocksat_fem_remesh_20260618/correlation_contribution.md`): **0 of
  6000** joint-stiffness points improve hard-region shape without detuning frequency — the as-received FEM
  sits on a **shape-vs-frequency Pareto wall**; the mesh is already converged (dish 2× refine moved global
  MAC +0.0016); topology is complete.

**Verdict:** remeshing **cannot** crack per-point FRF here. The honest, valuable contribution is the
**auditable boundary**: an agent *proved* mesh + stiffness are not the lever and redirected effort to data +
shapes. Only a from-scratch geometry rebuild could change the shapes — a major gamble, not recommended.

---

## 7. The consistency concern (Bilionis / Alberts / Kairui), mapped  *(P8)*
**The concern:** for ODE/PDE inverse problems, putting the physics in the **likelihood** can be
**inconsistent** — you choose how many times to evaluate the physics residual (collocation points, mesh
density, frame count), and that count acts like a free knob on the posterior; equivalently the residual is
treated as pseudo-observations with a residual-noise scale **σ_r** set arbitrarily. This is the same family
as the "GIGO / arbitrary σ_d" objection from industry skeptics.

**The map (controlled toy, truth θ=1.15, `statfem_consistency_toy/out/sweep_summary.json`,
CHECKER-BACKED YELLOW):**

| construction | physics in | model-error knob | arbitrary knob? | drift vs mesh? | recovers θ under model error |
|---|---|---|---|---|---|
| Classical (physics-in-likelihood, M-lik) | likelihood | **σ_r** fixed residual "noise" | **YES** — θ drifts (spread 0.084) | ~flat | no (1.15→1.27) |
| StatFEM (M-statfem / our M2) | likelihood (data = FEM + disc) | **σ_d** learned discrepancy | no | ~flat (spread 0.003) | no (θ absorbs error) |
| IFT / PIFT (M-ift) | **prior** | **β** learned trust temperature | no | ~flat (spread 0.003) | no (shared limit) |

**Reading:** the "discretization-dependence" charge is real but **sharpened** — the sensitivity is to the
**fictitious σ_r**, which a **learned** knob (σ_d in StatFEM, β in IFT) removes. **Honest shared limit:**
under genuine model-form error all three bias θ to ~1.27 — none recovers the true parameter; the discrepancy
*absorbs* the error, it does not *flag* it. Figure `reuse_consistency_money.png`.

---

## 8. Side-by-side vs IFT, real ShockSat  *(P9)*
Apples-to-apples on the **same whole-FRF |H| observable** (the hard case): identical data, forward, splits,
scorer (`ift_real_validation/out/scorecard.json`, CHECKER-BACKED YELLOW). The arms differ in where physics
lives **and** in the model-error regularizer — read the correction below the table.

| arm | where physics lives | observable | sampler | converged? | held-out coverage (peak/band) |
|---|---|---|---|---|---|
| **M2** | likelihood, **free** discrepancy | whole-FRF \|H\| | NUTS→TMCMC | **NO** (R-hat 63 NUTS / 129 TMCMC; σ_d→7.4) | 0.42 / 0.39 |
| **IFT** | **prior**, **bounded** learned β | whole-FRF \|H\| (same) | TMCMC (NUTS multimodal) | **YES** (cross-run R-hat 1.0007) | **0.97 / 1.0** |
| **L5** | **likelihood** (modal freq) | modal peak frequencies | NUTS | **YES** (R-hat 1.002) | 0.87 (sharpness bar) |

- **Correction (Andrew, 2026-06-26) — this is NOT "physics-in-likelihood diverges, physics-in-prior
  converges."** L5 is *also* physics-in-the-likelihood and **converges** (R-hat 1.002); the difference is the
  **observable** (modal feature vs whole-FRF magnitude). The narrow, real result: on the **same whole-FRF
  observable**, IFT's **bounded learned β** converges (under TMCMC) where M2's **free σ_d** hits a variance
  singularity. The win is the **bounded regularizer**, not "prior vs likelihood" — an informative σ_d prior is
  the likelihood-side cure (StatFEM thread D10). IFT is *also* multimodal under NUTS (R-hat 264); both need TMCMC.
- IFT does **not beat** the modal twin on overall sharpness (its band interval ≈ 20× wider — L5 band 5.5e3 vs
  IFT 1.1e5; the coarse-FEM ceiling) but is **bounded, convergent, and calibrated** where the likelihood form
  is not. Figure `reuse_ift_scorecard.png`.
- IFT's learned trust **β ≈ 0.17**, about **246× below** the no-data anchor β*≈42.8 — "this coarse FEM
  deserves strong distrust," said quantitatively and **bounded** (vs M2's σ_d→7.4 runaway). Figure
  `reuse_ift_beta.png`. This β is the natural home for a "tell the twin how wrong to expect the model to be"
  front-end (elicit β from known config deltas) instead of a hand-set σ_d.

---

## 9. StatFEM formulations evaluated (≥10)  *(P10)*
The program was a structured search over **where/how** physics, discrepancy, and the observable enter
(`fig_likelihood_inventory.png`; `modelclass_L5` + `papers_statfem_studies`):

- **Converge & useful:** modal peak-**frequency**; inferred mode-shape **field** (Beck); shape-MAC; analytic
  Bayesian evidence.
- **Converge but ~null on one impact:** frequency+MAC-as-constraint; complex **phase**.
- **Non-converged / multimodal:** whole-FRF **magnitude**; peak-**amplitude** feature; free correlated
  discrepancy on the whole FRF.
- **Discrepancy-form arms:** orthogonal **Schneider** (space×frequency-correlated) — ~7× tighter bands
  in-distribution where iid fails to converge; **Das–Debnath** complex latent modes — survives near-degenerate
  modes (0 vs 429 divergences). **Pattern:** the converging, useful observables are **modal**.

---

## 10. Recent related papers  *(P11)*
- **Sequential StatFEM** (Kavrakov et al.) — HIGH applicability; our PSD-envelope pilot was an honest
  negative (did not beat FEM+6 dB; same shape wall). `shocksat_sequential_statfem` YELLOW 18/3/0.
- **Latent-force + Bayesian NN** model-error twin (Kashyap/Nayek) — MODERATE-HIGH for damping/residuals;
  offline + extrapolation caveats.
- **Multi-level wing ROM / submodel** (Lu et al.) — MODERATE-LOW; fast but not Bayesian/StatFEM.
- **Yan et al. 2026 (sensor faults / virtual sensing)** — we reproduced its aliasing claim on independent
  real data with a Bayesian method **and** added calibrated bands its deterministic net lacks (3.4 vs 8.8 dB
  at high-freq local modes). `paper_virtual_sensing_uq_toy` YELLOW 42/2/0.

---

## 11. Evidence-based model selection  *(P12)*
Model classes scored by Bayesian evidence (Occam-penalized) on 27 matched modal frequencies, BIC-adjusted,
prior-robust (`stage1_evidence.json`, CHECKER-BACKED YELLOW):

- **Winner:** as-received FEM + one global discrepancy, posterior model probability **0.906**.
- A richer **16-parameter local-stiffness** model is the **worst** (does not earn its complexity).
- Only suggestive structure: a space×frequency-**correlated discrepancy** (M4), P≈**0.093** — a hint that
  *structuring the discrepancy* (not adding stiffness knobs) is the lever if any.
- Damping is **frequency-blind** here (damped-frequency shift 5.5e-5 ≪ 7 % discrepancy floor), so frequency
  evidence cannot rank damping models. **Don't add knobs — the inherited model is already Occam-optimal.**

---

## 12. The most potent, publishable finding(s)  *(P13)*
See `publishable_findings.md` for the full version. In brief, ranked:

1. **Trustworthy-but-not-sharp on a real, already-correlated aerospace FEM** (most defensible). StatFEM stays
   calibrated under large model error (held-out frequency coverage good, +0.93 skill) but the FRF-amplitude
   bands are irreducibly too wide to certify; the binding limit is per-node mode-shape fidelity — a **model**
   problem no statistical lever or agentic remeshing closed.
2. **The OBSERVABLE and the model-error REGULARIZER — not "where the physics lives" — decide well-posedness**
   (the method contribution). Physics-in-the-likelihood converges fine for a MODAL observable (L5, R-hat 1.002);
   the whole-FRF MAGNITUDE is the hard, multimodal observable for everyone (IFT also fails under NUTS, R-hat 264).
   On that hard observable, a BOUNDED learned regularizer (IFT's β — or an informative discrepancy prior) gives a
   convergent, calibrated posterior where a FREE discrepancy variance (σ_d→∞) does not.
3. **A LEARNED model-error knob answers the consistency concern (Bilionis/Alberts/Kairui).** StatFEM's σ_d and
   IFT's β both remove the arbitrary "residual-noise / number-of-physics-samples" knob (the toy: the drift is to
   the fictitious σ_r, not the mesh). Honest shared limit: none recovers θ under genuine model error.

Cross-cutting (for autonomous engineering): **convergence ≠ trust** — only a held-out gate (and a full
4-chain run) detects an over-confident or under-identified twin; cheap probes mislead both ways; the agentic
deliverable is the **auditable boundary** of data-driven remodeling.

---

## 13. Recommended next direction  *(P14, decide at the review)*
- **Option A (RECOMMENDED, lowest new-compute):** write up findings #1 and #2 from data we already have —
  the boundary result + the IFT/consistency method.
- **Option B:** **feature-space discrepancy** — put uncertainty in features ("peak at f0 ± X %, amplitude
  Y ± Z dB per mode") instead of a per-frequency |H| band; removes the misalignment-driven width and tests
  how close a usable +3/+6 dB band is. Bounded, near-term, machinery exists.
- **Option C:** a **maximally-informative own test** — multi-reference / roving excitation + QOI-optimal
  sensor placement designed to beat the single-impact shape/damping limits. Highest ceiling; needs hardware.
- **NOT recommended:** more whole-FRF stiffness remeshing (Pareto wall) or a from-scratch geometry rebuild.

---

## 14. Status, provenance, and what is surfaced for approval
- **Checker-backed (SHA-locked, OVERALL YELLOW honest negatives / GREEN integrity):** IFT real-validation,
  consistency toy, model-class selection (L5), FEM-remesh Card D, papers studies.
- **Exploratory (figures + numbers, no checker yet):** the FRF-correlation, remeshing-sweep, new-metric,
  wide-CI work (`shocksat_psd_envelope_twin_20260623`). Labeled EXPLORATORY/YELLOW throughout the deck.
- New figures from a single tufte-linted `code/make_review_figs.py`; deck from `code/make_deck.py`; deck QA
  from `code/qa_deck.py` (no overflow / table-width / spill flags). Samplers labeled (NUTS / TMCMC / non-conv).
- **Surfaced for Andrew's approval, NOT self-applied:** a `docs/report/project_log.md` row for this
  consolidation; promoting any EXPLORATORY result to checker-backed; any "replace the inherited FEM" claim;
  durable-rule / sampler-standard edits. The only durable file touched to build this packet is the lead
  CURRENT-STATE block in `notes/memory.md`.
