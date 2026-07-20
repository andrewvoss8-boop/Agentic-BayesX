# StatFEM consistency toy (Experiment A) — human-review packet

**Run:** `statfem_consistency_toy_20260616` · runner agent (Agentic BayesX) · advisor objective: Ilias Bilionis
**One-command replay:** `bash run_all.sh` → `checker_report.json`, `runtime.json`, figures.
**Status:** see `checker_report.json` (`overall`, GREEN/YELLOW/RED counts). This packet states only what the
checker numbers support; YELLOWs are honest-scope flags, never hidden.

> Reader note (audience): ML/stats terms are defined in plain English on first use; structural-dynamics terms
> (FRF, mode, eigenproblem, FE) are used directly. *Posterior* = the probability distribution of an unknown
> after seeing data (summarised by a mean and a 95% credible interval, the central band holding 95% of the
> probability). *NUTS* = a gradient-based sampler that draws from the posterior; "converged" needs R-hat≈1,
> enough effective samples, few divergences.

## 1. The charge under test (evaluate — do NOT defend or attack)
Bilionis's objective, verbatim: *"evaluate the StatFEM approach… build, evaluate, identify its gaps, and
suggest improvements."* The specific hypothesis (relayed via Andrew): methods that encode **physics through
the likelihood** (residual-as-fictitious-data) give posteriors that **depend on the discretization**
(collocation count `N_c`, residual noise `σ_r`, mesh `h`) and **do not converge to the truth as you refine** —
"inconsistent and incorrect." His cure (IFT/PIFT) puts physics in the **prior** with a learned inverse-
temperature **β**, "independent of any such discretization."

**The decisive, testable question:** as you refine the discretization, does each construction's θ posterior
**converge to the truth** AND stay **invariant** to knobs that carry no real information, or does it **drift**?
The verdict is reported from the numbers, **not pre-decided**. "StatFEM does not work here" is a permitted,
valuable finding.

## 2. Method Summary (where the physics lives; the equations; the data)
**Testbed:** a fixed-free **axial rod** (nondimensional `L=1, ρA=1, EA_nom=1`), inferring a scalar **stiffness
scale θ** with `EA=θ·EA_nom` (θ=1 nominal, **θ_true=1.15**). **Observable = harmonic forced drive-point FRF:**
a uniform unit load drives the rod; the response field `u(x;ω_d,θ)` is measured at **m=7 sensors** for several
**known** drive frequencies (the inhomogeneous forcing makes the field θ-dependent, so all three constructions
identify θ fairly through the SAME data). **Model-form error ε:** the TRUTH has a Winkler elastic foundation
`k_f=ε` (raises `ω²` by `+k_f`); the inference models all **omit** it. `ε=0` is the no-error control where a
correct method MUST converge to θ_true; `ε=0.3` is the model-form error. The foundation shifts the LOW mode
strongly (+5%) and higher modes barely — so a single θ rescale (which moves all modes proportionally)
**cannot** absorb it ⇒ genuine misspecification.

**The three constructions (same data; the construction difference IS the experiment):**

| construction | physics lives in | model-error role | knob swept | likelihood / posterior |
|---|---|---|---|---|
| **M-lik** | the **likelihood** | `σ_r` (FIXED residual noise, arbitrary) | `N_c`, `σ_r` | residual `A(θ)u−f` as fictitious data `≈0` (noise σ_r) + sensor data; field `u` marginalised → `N(0; Au−f, σ_r²)·N(y; Su, σ_u²)` |
| **M-statfem** | likelihood (FE pred + discrepancy) | `σ_d` (LEARNED additive discrepancy) | mesh `h` (`n_el`) | `y = S·u_FE(θ;h) + d + e`, `d~N(0,σ_d²C)` → `N(y; S u_FE, σ_d²C+σ_u²I)` |
| **M-ift** | the **prior** | `β` (LEARNED inverse-temperature) | `N_c` | field prior `∝exp(−β/2‖Au−f‖²)`, β learned; data `N(y; Su, σ_u²)` |

`A(θ,ω)=−θ·c²·D2−ω²·I` is the discrete dynamic-stiffness operator (D2 = cell-centred finite-difference 2nd
derivative for M-lik/M-ift; consistent-mass FE for M-statfem). M-lik and M-ift are deliberately the **same
algebra** differing ONLY in whether the residual weight is a FIXED likelihood noise `σ_r` or a LEARNED prior
precision `β` — exactly Bilionis's distinction, isolated. **Inferred:** θ (+`σ_r` is fixed for M-lik / +`β`
for M-ift / +`σ_d` for M-statfem). **Sampler:** NUTS, 4 chains, 1000 warmup + 1000 draws, all-variable gate
(max R-hat ≤1.05, min ESS ≥200, div-frac <2%). **Data count:** **one synthetic realization per cell**; the
data-growth axis `n` uses `n` independent replicate tests (n∈{1,4,16,64}); no flight-to-flight / build-to-build
variability. Field figure: `figures/figS_schematic.png`.

## 3. Solver validation FIRST (gate) — `figures/figV_solver_convergence.png`
Both forward solvers converge to the **analytic** tip-driven rod response under refinement at **2nd order**
(rate ≈ 2.00; finest relative error ≈ **4×10⁻⁵**, far below the inference noise floor). So any posterior drift
is the **method**, not under-resolution. (`out/solver_validation.json`.)

## 4. Results — the consistency criteria (numbers; all NUTS cells converged unless flagged)
*Headline numbers below mirror `out/sweep_summary.json`; the checker certifies they exist for all three
constructions.* Money figure: `figures/figA_money_theta_vs_knob.png`.

- **C1 — concentration (does θ lock onto θ_true as data grow?).** At **ε=0** all three concentrate on
  **θ_true=1.15** (final-`n` |bias| ≤ ~0.005, posterior SD shrinks ~1/√n) → testbed/positive control passes.
  At **ε=0.3** all three STILL concentrate (SD shrinks) but onto a **biased** θ≈1.26 — *confidently wrong*
  under model error. (`figures/figC1_concentration.png`.)
- **C2 — discretization-sensitivity (spread of the posterior θ mean across the knob; smaller = more
  invariant).** ALL three are essentially **invariant to the GENUINE discretization knob**: M-lik vs `N_c`
  spread **0.0050/0.0019** (ε 0/0.3), M-ift vs `N_c` **0.0034/0.0045**, M-statfem vs mesh `h` **0.0030/0.0024**.
  **BUT M-lik DRIFTS with the FICTITIOUS residual noise `σ_r`: spread 0.0836/0.0841** (θ moves ~1.15→1.06 as
  σ_r:0.005→0.5) — a knob carrying no information, with no principled way to set it. M-ift (β learned) and
  M-statfem have **no such extra knob**. (One-to-two orders of magnitude larger than any genuine-mesh spread.)
- **C3 — held-out coverage (95% target).** At ε=0 all three cover 1.00. At **ε=0.3 coverage DISCRIMINATES**
  (finest discretization, n=8): **M-lik 0.71** (under-covers — confidently wrong on prediction too),
  **M-ift 0.86**, **M-statfem 1.00**. statFEM's additive discrepancy keeps the held-out FRF prediction
  calibrated **even though its θ is biased** — i.e. statFEM trades parameter recovery for honest predictive
  coverage (predictive coverage ≠ parameter recovery). (`figures/figC3_coverage.png`.)
- **Identifiability (P5):** θ is well-identified from the forced FRF at both ε (Fisher information ~4–6×10⁴,
  approx posterior SD ~0.005 for one test), so the ε>0 non-recovery is a model-form **bias**, not an
  identifiability failure. (`figures/figI_identifiability.png`.)

## 5. Per-construction VERDICT + gaps + suggested improvements (for Ilias)
The exact verdict strings are generated from the numbers in `out/sweep_summary.json` (`verdicts`). Summary:

- **M-lik (physics in likelihood) — the charge is PARTIALLY supported, and SHARPENED.** It does **converge
  under mesh/N_c refinement** here (so the literal "doesn't converge as you refine" is NOT what bites). What
  bites is the **fictitious residual noise σ_r**: a number with no physical meaning shifts θ by ~0.08, with no
  principled way to choose it. *Secondary pathology found:* when the θ-prior spans a θ where a discrete
  resonance crosses a drive frequency, the field-marginal goes **multimodal** (R-hat≫1) — physics-in-likelihood
  is fragile near resonance crossings. *Gap:* σ_r is an un-calibrated knob. *Improvement:* learn the residual
  weight from data (→ M-ift) or marginalise it; avoid the determinant-evidence multimodality.
- **M-ift (physics in prior, learned β) — best-behaved on the knob axis.** No σ_r knob; θ is **invariant to
  N_c**; β is learned. *Gap found:* in this minimal toy β is **weakly identified** above a threshold (the
  near-resonance shape data don't pin it) — but θ is unaffected, so the IFT promise (discretization-invariant
  θ) holds. *Improvement:* report β's weak identifiability honestly; richer field data would sharpen β.
- **M-statfem (FE + discrepancy) — invariant to the mesh; the discrepancy rescues PREDICTION but not θ.** θ is
  **invariant to mesh h** and there is no σ_r knob; and its held-out coverage is the BEST (1.00 at ε=0.3). BUT
  under ε=0.3 the learned discrepancy `σ_d` stays small and **θ absorbs the model error** (the classic
  Kennedy–O'Hagan / Brynjarsdottir–O'Hagan **discrepancy↔parameter confounding**): θ is confidently biased to
  ≈1.27 while the additive discrepancy keeps the *prediction* honest. *Gap:* additive discrepancy + flexible θ
  ⇒ you get calibrated predictions but a wrong parameter. *Improvement:* if θ itself is the deliverable,
  constrain the discrepancy (orthogonal/physics-bounded), use cut/modular Bayes, or add observables where the
  foundation and θ act differently (a band where the foundation effect ≠ a θ rescale) to break the confounding.

**Cross-cutting finding:** on THIS toy, the binding failure under model-form error is **parameter
non-recovery, shared by all three** — θ concentrates on a biased value (≈1.27 vs truth 1.15), because the
omitted physics is θ-like in the observable. The constructions differ on two secondary axes: (a) the **knob
axis** — only M-lik carries an un-calibrated `σ_r` that moves the answer (drift ≈0.084); (b) the **prediction
axis** — statFEM's additive discrepancy keeps held-out FRF coverage at 1.00, M-ift 0.86, M-lik 0.71. So
Bilionis's *mechanism* (a fictitious, discretization-flavoured knob changing the physics-in-likelihood answer)
is **demonstrated and isolated to σ_r**; his stronger phrasing ("doesn't converge as you refine the mesh") is
**not** what we observe here — refinement converges for all three; and physics-in-likelihood (M-lik) is also
the **worst on held-out prediction**.

## 5b. Follow-up E1 — a SECOND error class that presses into the differences (figF; followup/FINDINGS.md)
The main error (Winkler foundation) was *θ-like*, so all three biased θ alike. Follow-up E1 adds a **NOT
θ-like** error — a localized stiffness defect `EA(x)=θ_true(1−depth·1[0.4≤x≤0.6])` (truth = high-res
reference solve, depth=0 control recovers θ; all 12 cells converged, worst R-hat 1.007). Result
(depth 0→0.5): **θ recovery fails for all three** (1.15→~0.95–0.99) = parameter non-recovery is robust to
the error class. **PREDICTION splits sharply:** M-lik's held-out 95% coverage **collapses 1.00→0.71→0.33**
(its FIXED σ_r cannot widen the bands), while **M-statfem and M-ift hold 1.00** at every depth — and
statFEM's learned **σ_d grows ~100×** (0.0007→0.076), *catching* the spatial error (vs flat 0.004 for the
θ-like foundation). **Sharpened verdict:** the brittle choice is a fixed residual treatment in the
LIKELIHOOD — it is confidently wrong on *prediction* under non-θ-like model error; LEARNING the model-error
weight (IFT's β in the prior, statFEM's additive σ_d) keeps prediction honest. Recovering the *parameter*
still needs breaking the discrepancy↔parameter confounding. (`figures/figF_followup_defect_class.png`.)

## 6. References (keep the strands separate)
- **StatFEM:** Girolami, Febrianto, Yin, Cirak (2021), *The statistical finite element method*, CMAME —
  arXiv:**1905.06391** (additive GP discrepancy `y=FE+d+e`).
- **PIFT (physics-informed field theory):** Alberts & Bilionis (2023), arXiv:**2301.07609**.
- **IFT inverse problems / learned inverse-temperature β:** arXiv:**2306.02150**. Minimal re-implementation;
  no results copied from `github.com/PredictiveScienceLab/pift-paper-2023`.
- **Probabilistic SOLVERS (a DIFFERENT strand — discretization error, not model error):** Chkrebtii et al.
  (1306.2365), Conrad et al. (1506.04592), Cockayne et al. (1702.03673). Conrad explicitly distinguishes
  **discretization error** from "model error induced by missing physical or inadequate descriptors." Our toy's
  ε (the omitted foundation) is **model error**; `N_c`/`h` are **discretization error**. We keep them separate:
  the solver-validation gate bounds discretization error so the θ findings are about model error + the σ_r knob.

## 7. Honest scope / limitations (carried as YELLOW)
- **One synthetic realization** per cell (the `n`-axis adds replicates); no flight-to-flight / build-to-build
  variability. Single-realization results are realization-dependent.
- The model-form error is a **surrogate** (Winkler foundation), not a measured real-structure discrepancy.
- **One scalar parameter** (θ); a real calibration has many — identifiability is easier here.
- M-lik/M-ift use the **field-marginalised** (Gaussian-integrated) form of the residual model; faithful to the
  residual-as-fictitious-data construction (the field integrates out exactly).
- Verdicts are for **this minimal rod toy**; they evaluate the constructions' behaviour, not a universal proof
  about StatFEM.

## 8. Surfaced for the lead (NOT self-applied — human stop points)
Proposed `docs/report/project_log.md` row (status copied from the checker, never stronger):
> *StatFEM consistency toy (Experiment A)* — `artifacts/reports/statfem_consistency_toy_20260616/` — checker
> OVERALL **<from checker_report.json>**. Builds the consistency/discretization-invariance criterion on a 1-D
> axial-rod forced-FRF toy; three constructions (M-lik/M-statfem/M-ift) on the same data. Findings: all three
> converge under mesh refinement (charge's "doesn't refine" NOT supported here) and concentrate on a BIASED θ
> under model error (confounding); the indicted behaviour isolates to M-lik's fictitious residual noise σ_r
> (θ drift ≈0.08); statFEM's discrepancy does not flag a θ-like model error; M-ift invariant but β weakly
> identified. Solver validated (rate 2.0). NUTS 4-chain all-var converged.

Also propose (await human): a `notes/runs.md` dated entry + a `notes/lessons-learned.md` line ("physics-in-
likelihood's discretization-dependence here is a fictitious-σ_r sensitivity, not a mesh-refinement failure;
additive discrepancy does not rescue θ when the model error is parameter-like — break the confounding").
**No durable rule / checker / sampler-standard / notes edits made by the runner.**
