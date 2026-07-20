# Runner prompt — Card F: Bayesian MODEL-CLASS SELECTION over model forms (parameterization + damping) for the hard-to-correlate ShockSat accelerometers

You are a **runner agent** in **Agentic BayesX** (structural-FEM / StatFEM / Bayesian-model-updating task). Lead =
Claude Code; human = **Andrew Voss**; advisor objective = **Ilias Bilionis**: *"evaluate StatFEM, identify its
gaps, suggest improvements."* This card asks the principled version of the still-open question from Cards D/E:
**among competing MODEL CLASSES — different local parameterizations AND different damping forms — which one best
explains the data at the 8 hard accelerometers, as decided by the Bayesian model EVIDENCE (marginal likelihood),
which penalizes complexity by Ockham's razor?** Start by holding the other (global) parameters FIXED at their MAP
values and selecting over the model-form ingredient; then RELAX them (full hierarchical). The deliverable is an
evidence-ranked, Occam-penalized, held-out-cross-checked answer to *whether a richer model form earns its
complexity at the hard accels* — not another unscoped "it helps / doesn't."

## 0. RE-GROUND FIRST (a new session knows only the files)
Read `AGENTS.md` (all gates — esp. NUTS/HMC sampler rule, convergence gate, **Modal/Eigenproblem
Identifiability gate**, Plot/Tufte gate, Verification gate, three-tier status, Compute/detached-launch gate).
Then read, in order:
1. **The two method papers handed over for this card** (in the chat / references): **Girolami, Febrianto, Yin,
   Cirak 2021, "The statistical finite element method (statFEM)", CMAME 375:113533 — §3.4 + §4.1.5 (model/mesh
   SELECTION by marginal likelihood + Bayes factor)**; and **Kiran, Das, Bansal 2025, "State-of-the-art review of
   Bayesian FE model updating", Prob. Eng. Mech. 80:103761 — §5 (Bayesian model class selection)**. Extract the
   exact evidence/Bayes-factor machinery (below) before building.
2. **The parent threads — Card D/E**: `artifacts/reports/shocksat_fem_remesh_20260618/decisions_log.md` (D0–D16),
   `correlation_contribution.md`, `damping_indicators.md`, `damping_modeling_review.md`, `out/joint_frontier.json`,
   `HANDOFF_richmodel_L5.md` (Card E — this card SUBSUMES Card E: Card E asked "does a richer model form sharpen
   the L5 held-out QOI?"; Card F answers the *which-model-form* question with the EVIDENCE as decider + held-out
   QOI as the operational cross-check).
3. **The L5 method + held-out QOI + scoring — Card A**: `artifacts/reports/statfem_real_validation_20260617/`
   (`packet.md` §1–2; decisions D11 L5-converges, D12 held-out-QOI, D13 faithful-additive-Schneider TMCMC +
   **evidence/logZ**, D20–D22 mode-shape likelihoods/Beck; code `modal_feature.py`, `heldout_qoi.py`, `realfrf.py`,
   `score.py`, `tmcmc.py` which already returns **log-evidence**, `schneider_faithful.py`). 
Restate **goal / last decision / next action / open ambiguities** in one line before acting.

## 1. THE TWO PAPERS' MACHINERY YOU WILL USE (cite, don't re-derive)
- **Evidence / marginal likelihood** `p(Y|M_j) = ∫ p(Y|θ,M_j) p(θ|M_j) dθ` (Kiran Eq 43; statFEM Eq 36/44).
  For the statFEM Gaussian construction it is ANALYTIC: `p(Y|M_j) = N(ρ P ū, C_d + C_e + ρ² P C_u P^T)`
  (statFEM Eq 38) — cheap, evaluate for MANY model classes at fixed θ (Stage 1).
- **Model posterior + Bayes factor**: `p(M_j|Y) ∝ p(Y|M_j) p(M_j)`; `BF_{12} = p(Y|M_1)/p(Y|M_2)` (statFEM Eq 52–53;
  Kiran Eq 43). With flat model priors, rank model classes by log-evidence.
- **Ockham's razor is automatic** (Kiran Eq 44): `log p(Y|M_j) = E_post[log p(Y|θ,M_j)] − KL(post‖prior)` =
  (avg goodness-of-fit) − (information gain). A richer model is preferred ONLY if its better fit outweighs the
  complexity it adds. statFEM §4.1.5 result: the evidence can prefer the SIMPLER model even when a richer one fits
  better — so a "no, the richer model does not earn its complexity" is a legitimate, principled WIN here.
- **Computing the evidence** (Kiran §5): Laplace/asymptotic (Eq 45) ONLY if globally identifiable; otherwise
  sampling — **TMCMC** (returns evidence directly; our `tmcmc.py` already does), nested sampling, or BUS-SuS
  (Schneider's method). Our problem is locally identifiable / multimodal (Card A) → use TMCMC; NUTS as the
  detector. Report cross-run evidence stability (±) — an unstable logZ is not usable (Card A D10 lesson).
- **EVIDENCE PITFALLS to honor** (Kiran §5; statFEM §3.3): (a) evidence is **sensitive to the prior** → use
  INFORMATIVE priors and report a prior-sensitivity sweep; a diffuse prior biases toward simpler models, an
  over-confident one the reverse. (b) **Large raw data overwhelms the prior and biases toward complex models** →
  prefer **statistics of response characteristics (modal features) as the data** (Kiran [72,222]) — this is
  exactly our L5 modal-feature observable, so the modal-feature likelihood is the right data for clean evidence.
  (c) Consider Automatic Relevance Determination for data-based prior choice on the new local parameters.

## 2. YOUR TASK — define competing model classes, rank them by evidence (fixed-MAP → flexible), cross-check held-out
1. **Define a ladder of candidate MODEL CLASSES** for the hard accels (each = a forward model + parameterization +
   damping form + discrepancy structure). Concrete, justified by the Card D/E diagnosis (the hard-accel residual
   is participation÷damping confounded; coarse 9-group stiffness is Pareto-optimal; bulkhead/cross drum modes are
   the most damped, ζ 0.12–1.76%):
   - **M0 (baseline):** as-received FEM, uniform ζ=1%, θ at MAP, statFEM iid discrepancy (σ_d, σ_e). [reference]
   - **M1 (richer LOCAL stiffness):** M0 + a small set of LOCAL interface stiffness parameters (split the
     bulkhead / bolted-joint-801 / strut regions out of the coarse groups) → expands the achievable shape family
     beyond the 9-group multipliers (which Card D proved Pareto-optimal/insufficient).
   - **M2 (Rayleigh damping):** M0 + α0 M + α1 K proportional damping (2 params).
   - **M3 (NON-proportional localized damping):** M0 + `C = α0 M + Σ_g β_g K_g` on the identifiable shell groups
     (Card D gate found damping lands on top_box/plates/cross, NOT the joint CBUSH); Das & Debnath 2020 complex
     viscous form is the reference (see `damping_modeling_review.md`).
   - **M4 (correlated discrepancy):** M0 + Schneider additive space×freq discrepancy (reuse Card A
     `schneider_faithful.py`) instead of iid.
   - **M5 (combinations):** the evidence-best of {M1,M3,M4} stacked, to test whether stacking earns its complexity.
   Keep edits COPY-applied/traceable; document each model class's parameter vector + prior.
2. **STAGE 1 — fix the other parameters at their MAP, screen many classes cheaply.** Hold θ (and the L5 modal MAP)
   FIXED; vary ONLY the new model-form ingredient + the statFEM hyperparameters (ρ, σ_d, ℓ_d, σ_e and any damping
   params). Compute the **analytic statFEM evidence (Eq 38)** for each model class on the modal-feature observable.
   Rank by log-evidence + Bayes factors. This is the user's "first assume the other parameters are fixed at their
   MAP" step — fast, many classes.
3. **STAGE 2 — RELAX the other parameters (full hierarchical), re-rank the top classes.** For the top-2–3 model
   classes from Stage 1, RELEASE θ and sample the joint posterior with **TMCMC** (evidence + convergence in one),
   reporting all-variable R̂/ESS/divergences and cross-run **log-evidence stability**. Re-rank. (This is the user's
   "eventually allow them to be flexible" step; allowing θ + a new damping form is itself a distinct model class.)
4. **CROSS-CHECK with held-out QOI (the operational test).** The evidence and the held-out predictive can disagree
   (evidence rewards in-sample fit-vs-complexity; held-out tests generalization). For the evidence-winning model
   class, ALSO report the **held-out-sensor QOI at the 8 hard accels** (interval score / CRPS / coverage / z-std
   via `heldout_qoi.py` + `score.py`, re-pairing-robust). Report BOTH; reconcile any disagreement honestly.

## 3. GATES FIRST (do BEFORE concluding any model class wins)
- **Modal/Eigenproblem Identifiability gate (AGENTS):** for every NEW parameter in M1/M3, report the
  parameter→mode sensitivity (strain-energy fraction for stiffness; damping-dissipation fraction ζ_{m,g} for
  damping — Card D `damping_gate.py` already does this) AND the FIM/eigen view (how many parameter COMBINATIONS
  clear the discrepancy floor). A model class whose extra parameters are NON-identifiable from this single-impact
  data will be penalized by the evidence (KL term) — that is the correct, principled outcome; state it.
- **Evidence-sensitivity gate:** report log-evidence under ≥2 prior widths per new parameter (Kiran §5 warning);
  if the model ranking FLIPS with the prior, the result is prior-dominated → YELLOW, report both.
- **Single-impact confound (carry from Card E):** the resonant peak is `|H_peak| ∝ φ_{s,k}φ_{d,k}/ζ_k` =
  participation÷damping, CONFOUNDED at one drive node. So M1 (shape) and M3 (damping) may achieve similar evidence
  by trading participation against ζ — if so, that is the finding (the data cannot separate them; the decisive
  lever is multi-reference data), not a failure. Use the modal-feature (peak-FREQUENCY) observable where the
  confound is weakest, and treat amplitude/QOI separately.

## 4. CONSTRAINTS / HONESTY (the prior runner repeatedly OVER-CLAIMED — do not)
- Plain standalone 9-group ShockSat ONLY (no tray). **COPY-never-edit** inherited FEM/code; apply model edits on a
  copy. Validate the BASELINE (M0 evidence + L5 held-out QOI) before any new class.
- **SCOPE EVERY CLAIM to exactly what was tested.** Card D/E corrections you MUST not repeat: "no model change can
  improve it" (over-claim; only the COARSE 9-group stiffness family was Pareto-optimal); "it's shape not damping"
  (the participation/damping confound); "e07 improves correlation" (greedy-pairing artifact). Use the three-tier
  green/yellow/red; **a model class is only "preferred" if BOTH its evidence wins AND the evidence is
  prior-robust AND it is stated which observable/data the evidence used.** Evidence ≠ held-out predictive — report
  both; never present an evidence win as a held-out win.
- Use **re-pairing-robust** metrics (tracked continuation / cross-orthogonality), never greedy best-MAC. Lead with
  evidence (logZ ± stability) + held-out QOI, not MAC.
- **Sampler:** NUTS as the multimodality detector; **TMCMC** for evidence (Card A standard; returns logZ). Report
  all-variable R̂/ESS/divergences; a non-converged/unstable-evidence class is YELLOW, not a ranking input.
- Compute: pin BLAS threads (`OMP_NUM_THREADS=1`), float64; the reduced 74-DOF model (eigh ~24 ms) for the Stage-1
  analytic-evidence screen and the frontier-style fast loops; full-order eigensolves (~290 s > tool timeout) and
  TMCMC runs DETACHED + resumable. Record `runtime.json`.
- Build an immutable `check.py` FIRST (baseline RED=not-done). Figures via saved `.py` + tufte-lint + image-QA.
- **SURFACE to lead/Andrew (do NOT self-apply):** any durable-rule/checker/sampler-standard change; any claim that
  the evidence-winning model should REPLACE the inherited FEM; the `docs/report/project_log.md` row. Model classes,
  evidence tables, and diagnoses are study artifacts (no stop).

## 5. WIN CONDITION
An **evidence-ranked table of competing model classes** (different local parameterizations AND different damping
forms) for the hard ShockSat accels — log-evidence (±cross-run stability) + Bayes factors + posterior model
probabilities — computed first at fixed-MAP θ (analytic statFEM evidence) then with flexible θ (TMCMC), with the
Ockham trade-off made explicit, gated by identifiability + evidence-sensitivity, and **cross-checked by the
held-out-sensor QOI at the 8 hard accels**. The deliverable is a credible, auditable answer to: *which model form
(if any) earns its complexity for the hard-to-correlate measurements, and does the data even contain enough
information to prefer one model form over another?* A principled **"the simplest sufficient model wins / the data
cannot distinguish the richer forms (multi-reference data needed)"** is an equally valuable result (statFEM §4.1.5
+ the single-impact confound) — and is the honest, Occam-penalized version of the question Cards D/E kept reopening.

## 6. WORKSPACE
Create `artifacts/reports/shocksat_modelclass_L5_YYYYMMDD/`. COPY-reuse (never edit in place) from
`statfem_real_validation_20260617/code/`: `modal_feature.py`, `heldout_qoi.py`, `realfrf.py`, `score.py`,
`tmcmc.py` (log-evidence), `schneider_faithful.py`, `core.py`, and `data/`; and from Card D the diagnosis JSONs
(`out/damping_gate.json`, `out/joint_frontier.json`, `out/region_diagnosis.json`) and `code/joint_frontier.py`
(the reduced-model fast loop to adapt for Stage-1 evidence). Write `decisions_log.md` (one-line state + D0
inherited constraints + the two-paper machinery), `priority_deliverables.md`, `references_reviewed.md` (statFEM
§4.1.5 + Kiran §5 + Das-Debnath + Schneider) from the start. Hands OFF the Card A/B/D/E workspaces (copy, don't edit).
