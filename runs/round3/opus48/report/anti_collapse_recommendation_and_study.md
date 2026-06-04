# Preventing posterior collapse in MDOF random-vibration Bayesian updating
### Recommendation to agents + a concrete study protocol

Claude Code (lead) for the Agentic BayesX round-3 opus48 workspace. This file is a **design/recommendation
artifact** — no new metrics are claimed here. It extends, and should be read with,
[statfem_lessons.md](statfem_lessons.md) and [research_directions_and_proposals.md](research_directions_and_proposals.md).
Items that would change a **durable** harness rule, checker, or sampler standard are marked **[PROPOSAL —
needs human approval]** per CLAUDE.md; nothing here is self-adopted.

---

## 0. What "collapse" is, precisely

The human's framing is correct: fitting **one scalar `k_j`** against ~6 interface DOFs × ~60–140 frequency
lines × several builds (hundreds–thousands of points) is wildly over-determined, so the **epistemic**
posterior sd shrinks like `σ/√(N_eff)` to ~0.1%. The axial mode position `f ∝ √(k_j/m)` alone nearly pins
`k_j`. That tight posterior is only trustworthy if **three** things are true; collapse is what happens when
any of them fails:

1. **`N_eff` is honest.** If correlated data points are counted as independent, `N_eff` is inflated and the
   posterior is *fictitiously* tight. (This is the Bayesian-bridge / MAC over-counting failure, moved to the
   frequency axis.)
2. **Model-form error is represented.** If systematic model error is buried in an i.i.d. noise term, the
   likelihood reads hundreds of *independent confirmations of a systematic mistake* → the posterior
   collapses **onto a biased value** ("near-delta next to bias" — strictly worse than honest width).
3. **The reported uncertainty is the decision-relevant one.** A collapsed *epistemic* fleet-mean `k_j` is
   not the uncertainty a new build carries; that carries **aleatory** build-to-build scatter, which more
   testing **cannot** reduce.

The hexapod run already showed (2) and (3) (bias floor ≈ −2.3%, posterior not covering truth; aleatory ≈ 35×
epistemic). The recommendation below is to make avoiding all three a *standard, checked* part of this problem
class.

---

## 1. Recommendation to agents (literature-grounded)

**R1 — Always carry a model-discrepancy term; never a discrepancy-free, diagonal-only likelihood.**
Omitting (or under-constraining) discrepancy gives confident, biased parameters — the central result of
Brynjarsdóttir & O'Hagan (2014, *Learning about physical parameters: the importance of model discrepancy*)
and Kennedy & O'Hagan (2001). Report a **WITH-d vs WITHOUT-d** pair every time (as `statfem_kj.py` already
does) so "does the pipeline know it's wrong?" is answered, not assumed.

**R2 — Count information honestly; treat the frequency grid as a *display* choice, not an *information*
knob.** FFT/periodogram ordinates of measurement *noise* are asymptotically independent (the basis of the
Whittle likelihood; Yuen & Katafygiotis frequency-domain Bayesian updating; Au, Bayesian OMA) — but **model
error is strongly correlated across frequency**, so the *effective* independent count over a log-band of
width `L` with correlation length `ℓ` is `N_eff ≈ L/ℓ`, **independent of how many lines you place**. For
PSDs, use the **actual spectral DOF** (number of averages), not the number of plotted bins. *Decisive
diagnostic:* refine the grid 2×/4× — if the `k_j`/QOI posterior keeps shrinking ∝ √N_lines you are
over-counting; if it saturates the covariance is honest. (Operationalizes the CLAUDE.md Discretization
Resolution gate.)

**R3 — Match the discrepancy *structure* to the error *structure*.** The hexapod lesson: an additive
frequency GP `d(ω)` cannot remove a **spatial** (symmetry-breaking) error — with-d ≈ without-d bias. Prefer
a discrepancy placed where the error physically lives: a GP on the **joint impedance** `Z_j(ω) =
k_j(ω)(1+iη_j(ω))` (parameter space, propagated through FBS) for a frequency-dependent joint, and an
**element-feature / per-strut** kernel for spatial error (see research_directions §B). Stationary additive
output GPs absorb only stationary output error.

**R4 — Separate epistemic from aleatory with a hierarchical (population) model, and put the aleatory + the
discrepancy uncertainty into the decision QOI.** Build-to-build `k_b ~ p(k|θ_pop, σ_build)`; learn `θ_pop`
(shrinks with builds) **and** `σ_build` (irreducible). This is hierarchical Bayesian model updating
(Behmanesh, Moaveni, Lombaert & Papadimitriou, 2015). The netCG/interface-PSD QOI must propagate
`BU(k_j)+d` (with d's uncertainty) **plus** aleatory build + flight scatter — not the epistemic fleet-mean
alone (closes the gap flagged in research_directions §D).

**R5 — Guard the θ↔d identifiability trade-off, in both directions.** A too-flexible discrepancy de-identifies
`k_j` (soaks up the signal); a too-rigid/misspecified discrepancy biases `k_j` (Arendt, Apley & Chen 2012;
Brynjarsdóttir & O'Hagan 2014). Constrain `d` with a physically-motivated, informative kernel/prior, and
consider **modular / cut-Bayes** updating (Bissiri–Holmes–Walker general Bayes; Plummer 2015) so a flexible
`d` informs prediction without corrupting the calibration of `k_j`. Report `k_j` *and* `ℓ_d`, `σ_d`
posteriors; watch for `ℓ_d` collapsing small (re-opens R2 over-counting).

**R6 — Validate by held-out coverage, not by recovery.** Hold out **frequency bands and whole builds**;
report credible-interval coverage / calibration and posterior-predictive checks. A tight posterior that
fails held-out coverage **is** collapse-onto-bias. This is the single most reliable collapse detector and
should gate "trust the QOI margin."

**R7 — Honest fallbacks when misspecification is real.** Two literature options, each *labeled* with its
tradeoff: (a) **feature/peak likelihood** (modal freqs, peak amplitudes, antiresonance notches, MAC) — the
direct Bayesian-bridge remedy that caps information by reducing data dimension, at the cost of discarding the
broadband shape and needing peak-picking (non-differentiable → smoothing for the NUTS standard); (b)
**tempered / power posterior (SafeBayes; Grünwald)** — down-weight the likelihood to a defensible `N_eff`
under suspected misspecification. Never present either as a free lunch.

**R8 — Author the data-generating truth INDEPENDENTLY of the inference model.** The original "perfect
recovery" was tautological because the model-form error was a draw from the same GP the discrepancy uses
(statfem_lessons §0/§2). For any collapse study the truth must be a *different, richer* object (frequency-
dependent/nonlinear joint, extra modes, spatial scatter, realistic complex correlated noise — Trainotti FBS;
Jalali–Friswell joint) and the experiment must be required to **exhibit** bias/non-coverage, not only
recovery. **[PROPOSAL — needs human approval]** as a durable harness rule for this problem class.

**Sampler note (standard, not optional):** keep NUTS/HMC with the convergence gate — report R-hat/ESS over
**all** latents including the discrepancy KL coefficients and the non-centered hierarchical per-build/per-
flight latents, ≥4 chains, divergence fraction <2%, and record `runtime.json`. Differentiability: feature/
peak likelihoods (R7a) need a documented smoothing/relaxation.

---

## 2. A specific study: "Collapse, bias, and calibration in MDOF random-vibration updating"

**Question (engineering decision it supports):** *When is a tight `k_j`/netCG posterior trustworthy, and
which likelihood/discrepancy approach keeps the decision QOI honest (calibrated, unbiased-enough) under
realistic model-form error, noise, and build/flight variability?* Success metric = **held-out calibration of
the QOI**, not recovery. What stays human judgment: whether the chosen QOI and joint idealization are the
right question at all.

Reuse the existing MDOF machinery ([mdof_forward.py](runs/round3/opus48/code/mdof_forward.py),
[statfem_hexapod_hier.py](runs/round3/opus48/code/statfem_hexapod_hier.py)). It is a **factorial sweep** of
three things, with collapse/bias/calibration measured in every cell.

### Factor A — inference approach (the "different possible approaches")
| ID | Approach | What it tests |
|----|----------|---------------|
| A1 | Full-spectrum, **diagonal i.i.d.**, no discrepancy | Cautionary baseline — should collapse **and** lose coverage |
| A2 | **Correlated noise only** (non-diagonal Σ / Whittle DOF), no discrepancy | Does honest info-counting alone fix collapse? (no — bias remains) |
| A3 | StatFEM **additive output GP** `d(ω)` (current default) | Fixes frequency error; not spatial |
| A4 | **Parameter-space discrepancy** — GP on joint impedance `Z_j(ω)` and/or per-strut element-feature kernel | Error in the right place |
| A5 | **Feature/peak likelihood** (freqs + peak amp + antiresonance; MAC analogue) | Information-capping remedy + its information loss |
| A6 | **Tempered / SafeBayes** power posterior on A3 | Robustness under misspecification |
| A7 | **Hierarchical** population over builds (on top of A4) | Epistemic/aleatory split; the recommended "full" model = A4+A7 |

### Factor B — information knobs (to *provoke* collapse)
- B1 frequency grid density `N_f` ∈ {1×, 2×, 4×} (the R2 invariance test);
- B2 measured interface DOFs `n_y` ∈ {1, 3, 6};
- B3 builds `B` ∈ {1, 4, 16} and flights;
- B4 band coverage ∈ {single mode, wide 20–2000 Hz multi-mode}.

### Factor C — truth (authored independently of the inference model — R8)
- C1 well-specified (sanity); C2 frequency-dependent/nonlinear joint (Jalali); C3 spatial symmetry-breaking
  per-strut scatter; C4 missing mode / wrong BC; C5 realistic **complex, frequency-correlated** FRF noise,
  worse at antiresonances (Trainotti). Run the headline under C2+C3+C5 combined.

### Metrics per cell (all artifact-backed)
1. **Collapse curve:** epistemic posterior sd of `θ_pop` vs `N_f`, `n_y`, `B`. Slope ≈ −1/2 on log–log ⇒
   over-counting; **plateau** ⇒ honest. Also report implied `N_eff` vs nominal point count.
2. **Bias:** posterior median `k_j` − independent truth (%).
3. **Calibration (the decisive one):** 95% CI **coverage on held-out builds** and **held-out frequency
   bands**; posterior-predictive p-value / energy score.
4. **Decision QOI:** netCG 3·GRMS median + 95%, and whether the interval covers the true *fleet* QOI
   distribution (not a single build).
5. **"Knows it's wrong" flag:** predictive interval covers held-out data while `k_j` is biased?
6. **Convergence:** worst R-hat / min ESS over **all** latents (incl. d-coeffs and hierarchical latents),
   divergences, runtime.

### Expected/falsifiable outcomes (what the plots should show)
- **A1** collapses (sd ∝ 1/√N) *and* fails held-out coverage under C2–C4 → the cautionary picture.
- **A2** stops the fictitious shrink (sd plateaus) but stays biased → info-counting ≠ discrepancy.
- **A3** fixes C2 but not C3 (reproduces hexapod with-d ≈ without-d for spatial error).
- **A4+A7 (recommended)** plateaus under refinement, keeps held-out coverage ≳90%, and yields a QOI interval
  that covers the true fleet QOI — at the cost of more parameters / weaker `k_j` identifiability (show the
  R5 trade-off).
- **A5/A6** trade information for robustness — quantify how much interval widening buys how much coverage.

**Deliverable:** a one-page **"menu with tradeoffs"** table (approach × {collapse-safe?, bias, coverage,
QOI-honest?, cost}) plus the collapse curves and held-out calibration plots — a reusable decision aid for
this problem class, and the evidence base for any **[PROPOSAL]** to make R2/R6/R8 durable checks.

### Minimum viable slice (if compute-bound)
A1 vs A3 vs A4+A7, under truth C2+C3, sweeping only B1 (grid 1×/2×/4×) and B3 (B∈{1,4,16}), reporting metrics
1–4. That alone demonstrates collapse, the bias floor, and the calibration fix in a few NUTS runs.
