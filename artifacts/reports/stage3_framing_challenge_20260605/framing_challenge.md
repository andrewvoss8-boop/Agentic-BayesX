# Stage-3 Framing Challenge — is this even the right question?

**Author:** Stage-3 Framing Challenger (Opus 4.8), browsing ENABLED.
**Date:** 2026-06-05.
**Role:** challenge the *framing* and propose better ones. I did **not** edit code, durable rules, or
checkers. I wrote ONLY to `artifacts/reports/stage3_framing_challenge_20260605/`.
**Honesty:** I cite only sources I fetched this session ([sources/sources.md](sources/sources.md)); claims
I could not verify from a fetched source are marked `[SPECULATIVE]` or `[OPINION]`. A "the framing is
right / partly right / wrong" verdict are all fine if honest — and my verdict is **partly right, badly
drifted.**

**Plain-English glossary (used throughout, defined on first use):**
- *Calibration* = adjusting a model's unknown numbers (here, strut stiffness `k`) so the model matches
  test data.
- *Identifiability* = can the data pin down a unique value for a parameter? If two different parameter
  values fit equally well, the parameter is *non-identifiable*.
- *Discrepancy term* = an extra function the model is allowed to learn to cover where the physics model
  is simply wrong (the model's "I-know-I'm-missing-something" budget).
- *QOI* = quantity of interest = the number the engineering decision actually rides on. Here `netCG` =
  the net acceleration of the load = (force transmitted across the interface) ÷ (load mass), in g.
- *Held-out calibration* = hide some data, predict it, and check whether the model's 95% uncertainty
  band actually contains the hidden truth ~95% of the time. This is the project's real trust test.
- *Ridge / confounding* = when two knobs do the same thing to the fit, so the data cannot tell them
  apart; the sampler wanders along a "ridge" of equally-good combinations and never settles.
- *NUTS* = the No-U-Turn Sampler, the project's default Bayesian engine; *R-hat* and *ESS* are its
  "did the chains agree / how many independent draws" health checks.

---

## 0. Re-grounding (one line)

**Goal:** a trustworthy StatFEM aerospace digital twin that yields a *decision-relevant load (netCG)* an
aerospace audience will believe, AND a *defensible novel contribution* (thesis + possible patent on a
structure/property-based discrepancy). **Last decision (per `notes/memory.md`):** Stage-3 independently
verified as an honest *mixed* result; default next step = the master's Stage 4 (higher-fidelity FEM +
orthogonal discrepancy). **My job:** ask whether that is even the right next move. **Recorded steering
(human, 2026-06-05):** *the experiment drifted; treat "bigger/more technical plan" as a red flag; prefer
the simplest experiment that answers the real question.* I take that as my mandate, not a footnote.

---

## 1. What Stage 3 is ACTUALLY doing (≤5 plain sentences — sanity-check this against intent)

1. It fits a **deliberately coarse 7-resonance model** (6 strut "mount" modes + 1 axial dome bounce) to
   synthetic 6-direction "apparent mass" data (how heavy the interface feels vs frequency) produced by a
   **richer hidden model** authored by a separate agent.
2. It tries three fixes: (a) let each of the 6 struts have its own stiffness so the model can split modes
   the data shows; (b) add a **per-strut stiffness discrepancy** keyed by strut geometry; (c) fix the
   load QOI definition (`netCG`) so both sides compute it the same way.
3. The asymmetric physics (a) **works** — NUTS converges and recovers stiffness near nominal; the
   discrepancy (b) **fails** — it lives in the *same parameter space* as the stiffness it perturbs, so the
   two are confounded, NUTS breaks (R-hat 2.85), and the noise term `σ_e` balloons to ~150–190× the true
   sensor noise.
4. The converged model then **over-predicts the held-out load `netCG` by 3.1×** with **0% coverage**,
   because the coarse model cannot represent the higher modes / antiresonances that attenuate real
   transmission.
5. In one sentence: **Stage 3 is a synthetic calibration exercise that fits a known-too-simple model to
   data from a slightly-less-simple model, and discovers — honestly — that you cannot patch a
   missing-physics error with a parameter-space discrepancy.**

That is a real and useful finding. But notice what it is *not*: it is not a test against real hardware,
it is not a test of the *decision* (overtest/undertest), and it is not even a test of the discrepancy
formulation the patent actually claims (more on that in §9). That gap is the drift.

---

## 2. Blunt verdict — right question, or plumbing?

**Partly the right question; substantially drifted into plumbing and machinery.** Splitting it:

**The science in Stage 3 (keep this):** the **negative result** — a discrepancy living in the *same
parameter space* as the calibration parameter is confounded by construction, and a smooth correction
cannot absorb a missing-resonance error. This is genuine, independently verified, and directly useful to
both the thesis and the patent's non-obviousness story. Good.

**The plumbing / wrong-question parts (stop or reframe these):**
1. **Convergence-chasing on a ridge.** The whole "did NUTS converge over all latents (R-hat < 1.01)?"
   gate is being used as the *trust bar*. On a genuinely non-identifiable problem, NUTS failing is **NUTS
   doing its job** — correctly reporting that the data cannot separate the knobs. Using convergence as
   the trust gate conflates *sampler difficulty* with *model adequacy* (§6).
2. **The error type is unrepresentative.** "Model-form error" here = coarse-FEM-vs-rich-FEM, i.e. *more
   linear modes*. The error the project actually cares about — and the one the patent's value rests on —
   is **FEM-vs-hardware**: joints, preload, nonlinearity, real boundary conditions. Stage 3's truth has
   none of those. It is a tractable-but-unrepresentative error (§4 of attacks).
3. **Calibration obsession vs prediction.** Enormous effort goes into identifying `k` and characterizing
   the parameter↔discrepancy ridge. The decision needs a *trustworthy QOI prediction*, and the converged
   model recovers `k` near-nominal yet **still** over-predicts the QOI 3.1×. So identifying `k` better is
   **not the lever** (§3 of attacks). The experiment is optimizing the wrong target.
4. **The Stage-4 long pole is "more machinery."** Higher-fidelity FEM is the single biggest build in the
   whole plan, and it does **not** test the contribution; worse, it risks the *same* missing-mode trap at
   10× the cost (add some modes, still miss others). That is exactly the "bigger/more technical plan" red
   flag the human flagged.

**Net:** Stage 3 produced one real scientific brick (the confounding negative result). The surrounding
framing — convergence-as-trust, synthetic-mode error, calibration-first, then a giant FEM — is mostly
machinery, and the master's Stage-4 plan doubles down on the machinery half before running the cheap
experiment that would actually answer the human's question.

---

## 3. Attack axis 1 — CALIBRATION vs PREDICTION (adjudicated)

**Intuition first.** Kennedy & O'Hagan's whole point `[KOH]` is that you fit a computer model to data
**plus a discrepancy term plus noise**, and you use the *combination* to predict — "predictions allow for
all sources of uncertainty." A famous consequence: the **prediction can be right even when the calibrated
parameter is wrong/unidentified**, because the discrepancy soaks up the gap. So an obsession with pinning
down `k` (identifiability) can be the *wrong* question if all the decision needs is a good `netCG`.

**But the prompt's counterpoint is real, so adjudicate it.** Here the held-out QOI is *bad* (3.1× over,
0% coverage), so maybe calibration matters after all? **My adjudication: no — and this is the key
insight.** The model that **converged** (without discrepancy) recovered `k_pop` *near nominal* and **still
over-predicts netCG 3.1×**. If sharper calibration were the fix, a near-nominal `k` would have given a
near-right QOI. It did not. The QOI is wrong because the **model class is wrong** (it physically cannot
make the higher modes / antiresonances that attenuate real transmission), not because `k` is mis-identified.

**Conclusion:** the identifiability / confounding obsession is the **wrong question** for the decision.
The right question is *"can any predictor in this model class give a calibrated held-out netCG?"* and
Stage 3's answer is **no** — which points at **model-class adequacy** (more physics, or a discrepancy that
lives where the QOI error lives), *not* at better parameter recovery. KOH's lesson applies, but in the
inverted form: even a *well-identified* parameter does not save a *wrong-class* model.

---

## 4. Attack axis 2 — WRONG TOOL FOR THE ERROR (discrepancy vs fidelity vs model-class)

**Intuition.** A StatFEM discrepancy is a **smooth bias function** `[STATFEM]` — good at "the curve is
gently off." A missing resonance is a **sharp, narrow, structural** feature. Asking a smooth GP to
reproduce a missing antiresonance is like asking a slow dimmer switch to reproduce a strobe light: the
shapes don't match, so the GP either fails or contorts and de-identifies the physics (exactly the σ_d→1.33
blow-up Stage 3 saw).

**So what is the honest fix to a missing-mode error?** Three options, in increasing honesty about "we
don't know the right model":
- **(a) Fix the model** (higher fidelity = Stage 4 part i). Legitimate, but: you will add *some* modes and
  still miss others, the σ_e floor persists, and it is the most expensive path. Patch-the-fidelity can be
  self-deception too if you stop the moment one held-out number looks better.
- **(b) Put the discrepancy where the error lives** (output / modal-participation / frequency space,
  *orthogonal* to the calibration parameters = Stage 4 part ii). Cheaper, and it is the actual contribution.
- **(c) Model-class selection / averaging.** Treat "how many modes / which physics" as an explicit
  **menu of candidate models**, compute each one's evidence, and **average the netCG prediction weighted
  by posterior model probability** `[BMA]`. The repo's own TMCMC paper is built for exactly this — it
  "can estimate evidence of the chosen model class … for Bayesian model class selection and model
  averaging" `[TMCMC]`. This is the textbook-correct response to "my model is the wrong class," and it
  gives an *honestly wider* QOI instead of a confidently-wrong one.

**When is discrepancy-patching self-deception?** When the residual is a **structural feature your model
class cannot make** and you absorb it into a smooth bias or an inflated noise term to make coverage look
OK. Stage 3's σ_e at 150–190× sensor noise is precisely that signature. Honest move: **name it as
model-class uncertainty** (option c) or **fix the class** (option a) — do not let a bias term launder it.

---

## 5. Attack axis 3 — is the synthetic error the RIGHT KIND?

**No, and this is the sharpest criticism.** Stage 3's "model-form error" is coarse-FEM-vs-rich-FEM: the
hidden truth is just a **richer set of linear modes**. But the project's *own* `notes/project_vision.md`
§5 says the patent's value is that **"real structural model error jumps at joints/interfaces; it is NOT
smooth in space."** Real FEM-vs-hardware error is joints, preload, contact nonlinearity, real boundary
conditions — things **neither** FEM captures and which are **not** "a few more linear modes."

So Stage 3 is testing a discrepancy method against an error type (extra linear modes) that is **not the
error the contribution is designed to beat** (joint/interface jumps). That is a quiet but serious
mis-specification: even a *success* here would not be evidence for the patent's actual claim, and the
*failure* we got is partly an artifact of choosing a missing-mode error that no parameter-space
discrepancy could ever fix.

**Would real data change the conclusion?** Likely yes — and the project already intends it (the McCallie
subscale tray, vision §7). Calibrating the *same* coarse model to a **real** apparent-mass / interface FRF
record (e.g. a vibrationdata dome ignition record, or a 4TU/NTRS ground-vibration-test dataset) would
expose the *joint/nonlinear* error the method claims to address — for free, and it kills the
"tractable-but-unrepresentative" critique outright. `[OPINION]` This is higher-value than another synthetic
stage.

---

## 6. Attack axis 5 — is the TRUST TEST mis-framed? (convergence vs held-out)

**Yes — promote held-out calibration to the gate; demote NUTS convergence to a diagnostic.**

**Intuition.** A genuinely non-identifiable model *should* be hard to sample — the posterior really is a
ridge. NUTS failing on a ridge is **honest reporting**, not a defect. A tempering sampler like **TMCMC**
would instead happily integrate *along* the ridge and "converge," because it is explicitly built to draw
from "PDFs with flat manifold" and multimodal targets `[TMCMC]`. So "did it converge?" depends on **which
sampler you used**, not on whether the **model is adequate**. Using convergence as the trust bar therefore
distorts the research two ways:
- It can make you **throw away honest flexible models** just because NUTS won't sample them (when the real
  message is "the data can't separate these — say so").
- It can tempt you to **over-tighten priors to force convergence** (Stage 0/1 capped σ_d=0.3 to mask a
  ridge), which *hides* the non-identifiability the human needs to see.

**The right trust bar is the one the project already has: held-out QOI calibration** — does the 95% band
for the *load you will report* actually contain the held-out truth? Stage 3's answer (3.1× over, 0%
coverage) is a *clean, sampler-independent* verdict that the model is inadequate. That is worth more than
any R-hat. **Reframe:** keep NUTS R-hat/ESS as a *diagnostic* (and keep the rule that you never *claim*
"NUTS active" without it), but make **held-out netCG coverage the headline gate**. This is consistent with
the project's stated primary trust test and removes the convergence-vs-adequacy confusion.

(Note: this does **not** weaken the sampler standard. The convergence gate stays for *claims that NUTS is
active*. It just stops convergence from masquerading as *model trust*.)

---

## 7. Attack axis 4 — the QOI and the BIAS DIRECTION (reframe around overtest)

**This is the most aerospace-defensible reframe, and it is sitting right there in the result.** The
converged model **over-predicts** transmitted `netCG` by 3.1×. Over-prediction of interface load → you
**overtest** the hardware. The NASA Force Limited Vibration monograph `[FLV]` is *entirely about this
error*: enveloping the peaks of field data "results from the standard practice of enveloping the peaks …
which results in overtesting at resonances of the test item." And the physics of *why* a coarse model
over-predicts is named there too — the **dynamic-absorber effect**: at the payload's resonance, the real
interface motion/force is naturally *notched* ("the motion of the … directly excited oscillator will be
zero at the natural frequency of the secondary oscillator"). A coarse model that **misses those
antiresonances over-predicts the transmitted force** — exactly the 3.1× we see.

**So the decision-relevant framing is overtest/undertest risk + force limiting, not parameter recovery.**
Concretely:
- **The decision:** what random-vibration **test level / notch depth** do we set at the coupled resonance?
- **Whose:** the **environments/loads engineer** who owns the spec, and the **qualification engineer +
  chief engineer** who sign the test risk. (These are real signatures; "what is `k`?" is not a signature.)
- **Why it fits the mission:** force limiting is established NASA practice (`[FLV]`, apparent/effective/
  residual mass), it is `netCG`/apparent-mass-native (vision §6, NASA-HDBK-7004C framing), and it turns
  the project's honest 3.1× *failure* into the *exact quantity the method should help control.*

Yes, `netCG` = interface force / mass is the right decision-relevant quantity, and yes, the 3.1×
**over-prediction matters** — it is dollars of unnecessary test margin and induced-failure risk. Reframe
the headline around it.

---

## 8. Attack axis 6 — the staged 0→5 march

**The long march delays real-world value and hides the one decisive experiment.** The human's real
objective needs two things: (1) a defensible novel contribution, (2) a decision-relevant QOI aerospace
will believe. **Neither requires Stages 4–5 as written.** The decisive scientific question — *does a
property-keyed discrepancy that is **orthogonal** to the calibration parameter beat the **spatial /
same-parameter-space** version?* — can be answered on the **existing coarse model** by changing *where the
discrepancy lives*, with **no new FEM**. Stage 3 already delivered the negative half (spatial fails). The
missing half is one focused A/B, not two more stages.

**What would make Stage 3 the wrong question entirely?** If the real decision is overtest/force-limiting
(§7) and a *calibrated-but-honestly-wide* QOI is acceptable, then the entire fight to *identify* `k` and
to make a flexible discrepancy *converge* is beside the point — you'd go prediction-first (R6 below) and
never calibrate `k` at all.

---

## 9. Attack axis 8 — the CONTRIBUTION / PATENT (pressure-tested, not protected)

Two hard findings the human should hear **before** committing:

**(A) Stage 3 did not test the patent's actual claim.** The vision doc (§5A) names the patent kernel as a
property-keyed discrepancy in the **frequency / output domain** — error organized by *part type*, living
*away from* the calibration parameters. But Stage 3 implemented the discrepancy in **parameter space**
(`k_j = k_pop·exp(d_j)`, per-strut, azimuth-keyed). That is the **spatial, same-parameter-space** version
the vision itself demotes. So Stage 3 is **non-obviousness evidence for the wrong direction**: it shows
the *naive* version fails. It does **not** yet show the claimed *orthogonal* version succeeds. The patent's
positive evidence is still **unbuilt.**

**(B) "Property-keyed" may be the wrong thing to anchor the patent on.** Stage 3 proves that property-
keying *by itself* does **not** break confounding — the per-strut discrepancy *was* property/geometry-keyed
and still confounded, because it sat in the calibration parameter space. The actual confounding-breaker is
**orthogonality** (output space vs parameter space) and/or **modular/cut updating**, which overlaps known
work (Plumlee-style orthogonal GP discrepancy; cut Bayes) `[SPECULATIVE — Plumlee not fetched this
session; from vision §4]`. The genuinely defensible contribution is more likely the **combination**:
*(output-space, frequency-domain, property-keyed, dynamic, FBS-QOI-propagating) discrepancy + held-out-
calibration trust test for aerospace load prediction* — not "property-keying" as a standalone idea. The
held-out-calibration trust methodology itself may be a stronger, cleaner contribution than the kernel.

**(C) Novelty is unverified.** No patent-database / freedom-to-operate search has been run (vision §12).
Do not assert novelty. A real search (Google Patents, Lens.org) and the Sec-101 "method of testing a
physical structure" framing are prerequisites before any patent claim is made.

---

## 10. Ranked backlog — reframings / alternative experiments (value-per-effort)

Format: **the new question → the real decision + whose → setup change → assumptions → expected impact →
feasibility on the NumPyro/JAX stack.** `↓` = reduces scope/complexity. `🚀` = ambitious/borderline.

### R1 ↓ ⭐ — Orthogonal output-space discrepancy A/B (the cheap positive half of the patent experiment)
- **Question:** does a property-keyed discrepancy placed in **output / modal-participation space**
  (orthogonal to `k_pop` by construction — e.g. a zero-mean GP on the residual apparent-mass curve
  constrained orthogonal to the parameter-sensitivity directions, or **cut/modular updating**) (a) keep
  NUTS converging and (b) improve held-out `netCG` coverage, vs Stage-3's confounded parameter-space
  version?
- **Decision + whose:** is the *orthogonal* formulation the real contribution? → the human (thesis/patent
  go/no-go) and the loads engineer (trust the QOI).
- **Setup change:** reuse the **existing coarse model**; only move the discrepancy from parameter space to
  output space + add an orthogonality/cut constraint. No new FEM.
- **Assumptions:** same truth dataset; informative property-keyed kernel; held-out builds 6,7 as now.
- **Impact:** directly answers the human's real scientific *and* legal question; supplies the patent's
  missing positive evidence. **Highest value-per-effort.**
- **Feasibility:** High — days. Pure inference change on existing plumbing.

### R2 ↓ ⭐ — Re-gate on held-out QOI, not on NUTS convergence
- **Question:** if we score the *existing* Stage-3 posteriors purely on **held-out netCG coverage +
  sharpness**, what is the verdict, and does it change which model we'd ship?
- **Decision + whose:** what is our *trust bar*? → lead + trust reviewer.
- **Setup change:** a post-processing scorecard; demote R-hat/ESS to a diagnostic panel (keep them for any
  "NUTS active" claim). No new sampling.
- **Assumptions:** none new.
- **Impact:** removes the convergence-vs-adequacy distortion (§6); honest, cheap, and reframes the
  headline. Near-free.
- **Feasibility:** High — hours.

### R3 — Reframe as overtest/undertest + force-limiting decision
- **Question:** given posterior uncertainty, what **notch depth** at the coupled resonance avoids overtest
  without undertesting, and how many dB of test margin does the 3.1× over-prediction cost?
- **Decision + whose:** the test level / notch spec → **environments-loads engineer + qual sign-off** (a
  real signature). `[FLV]`
- **Setup change:** add the NASA-HDBK-7004 apparent-mass / semi-empirical force-limit layer on top of the
  existing posterior; report overtest-margin reduction with bands.
- **Assumptions:** published force-limit form `[FLV]`; impedance from the coupled posterior; state that the
  coarse model bounds (not nails) notch depth.
- **Impact:** turns an honest failure into the *exact quantity the method should control*; most aerospace-
  defensible. Medium effort (needs a careful force quantity contract).
- **Feasibility:** Medium.

### R4 🚀 — Calibrate to REAL apparent-mass / FRF data (kill the synthetic-error critique)
- **Question:** does the method behave the same against **FEM-vs-hardware** error (joints/nonlinearity) as
  against synthetic missing-mode error?
- **Decision + whose:** is the contribution real outside the sandbox? → human + advisor (Bilionis).
- **Setup change:** swap the synthetic truth for one **real** record (vibrationdata dome-ignition, or a
  4TU/NTRS GVT dataset); keep the coarse model + discrepancy.
- **Assumptions:** documented units/provenance; one interface DOF to start.
- **Impact:** tests the error type the patent actually targets (§5); stepping stone to the McCallie tray
  (vision §7). High.
- **Feasibility:** Medium-Low (data wrangling, units).

### R5 🚀 — Model-class selection / averaging instead of a GP discrepancy
- **Question:** treat "how many modes / which physics" as a **menu of candidate forward models**; compute
  each one's evidence and **average the netCG prediction** weighted by posterior model probability.
- **Decision + whose:** how to honestly report QOI under model uncertainty → loads engineer + reviewer.
- **Setup change:** use the repo's **TMCMC** machinery `[TMCMC]` over 3–4 candidate models (6-mode,
  +panel-bending, +extra-dome-mode). No bias term.
- **Assumptions:** small model menu; same data.
- **Impact:** the textbook-correct answer to "wrong model class" (§4); gives an honestly-wider QOI instead
  of a confidently-wrong one; uses machinery already in the repo. High, and genuinely novel framing for
  this problem.
- **Feasibility:** Medium (TMCMC integration, but the paper/code lineage is in-repo).

### R6 🚀↓ — Prediction-first: drop calibration entirely
- **Question:** can we get a **trustworthy held-out netCG without identifying `k` at all** — a flexible
  discrepancy-corrected predictor in the pure KOH-predictive stance `[KOH]`?
- **Decision + whose:** does the decision need a parameter, or just a calibrated QOI? → human.
- **Setup change:** stop reporting/identifying `k`; fit data→QOI with a flexible discrepancy; gate only on
  held-out coverage.
- **Assumptions:** accept an un-identified `k`.
- **Impact:** if it works, the entire identifiability/confounding fight is **moot** for the decision — a
  huge simplification. Borderline-crazy but clarifying.
- **Feasibility:** Medium.

### R7 ↓ — Stop building; write up the negative result + design ONE positive experiment
- **Question:** is the existing Stage 0/1 + Stage 3 evidence *already* a complete, publishable, patent-
  supporting unit (spatial/parameter-space discrepancy is confounded; convergence breaks; held-out QOI
  over-predicts)?
- **Decision + whose:** spend more compute, or bank the result? → human + advisor.
- **Setup change:** **none** — write the paper/invention-disclosure now, then deliberately design R1.
- **Impact:** locks in the verified result, creates the citable artifact + dated conception record, and
  forces a *designed* next experiment instead of an auto-piloted stage. Highest scope-reduction.
- **Feasibility:** High — it is writing, not building.

**Do-next picks (value-per-effort): R7 + R1 + R2.** Bank the negative result, run the orthogonal-vs-spatial
A/B on the existing model with held-out netCG as the gate. All three are days, reuse existing plumbing, and
directly answer the human's real question.

---

## 11. Kill list — stop doing these as framed

1. **Stop using NUTS R-hat<1.01 over all latents as the *trust* gate** on a known-non-identifiable problem.
   It conflates sampler difficulty with model adequacy. Demote to a diagnostic; gate trust on held-out QOI.
2. **Stop putting the discrepancy in the SAME parameter space as the calibration parameter.** Proven
   confounded (R-hat 2.85, σ_d→1.33). Do not re-run variants of it.
3. **Stop testing model-form error as coarse-FEM-vs-rich-FEM (more linear modes).** It is not the
   joint/interface/nonlinear error the contribution targets; it biases the conclusion.
4. **Stop auto-piloting the 0→5 march.** In particular, **do not build the higher-fidelity FEM (the long
   pole) before** running the cheap orthogonal-discrepancy A/B. Higher fidelity is machinery that does not
   test the contribution and may re-trap on missing modes.
5. **Stop calling the Stage-3 discrepancy "the patent kernel."** It is the parameter-space spatial version
   the vision doc itself demotes. The kernel (orthogonal/output-space) is **untested**; say so.
6. **Stop reading "wide-but-covering" as trust.** σ_e at 150–190× sensor noise buying coverage with huge
   bands is the failure signature, not success.
7. **Stop asserting novelty / patentability** until a real patent-DB + freedom-to-operate search and a
   Sec-101 attorney read exist.

---

## 12. Simplest-path option (cheapest experiment that answers the real question)

**R7 → R2 → R1, in that order, no new FEM:**
1. **Write up the verified negative result now** (Stage 0/1 + Stage 3): "a property/geometry-keyed
   discrepancy placed in the calibration parameter space is confounded, breaks convergence, and a coarse
   model over-predicts the held-out load 3.1× (overtest direction)." This is done, independently scored,
   and patent-/thesis-relevant. Cost: writing only.
2. **Re-score the existing posteriors on held-out netCG coverage** as the headline trust metric (R2). Cost:
   hours.
3. **Run the one decisive A/B** (R1): move the property-keyed discrepancy to **output space (orthogonal /
   cut updating)** and ask whether it converges *and* improves held-out netCG coverage vs the confounded
   version — on the **existing coarse model.** Cost: days.

That sequence answers the human's real scientific question (*does orthogonal property-keyed discrepancy
beat spatial?*), supplies the patent's missing positive evidence, and reframes trust around the decision —
all **without** the Stage-4 FEM long pole or a Stage-5 mega-run.

---

## 13. Recommendation on the human's actual fork (one paragraph for a tired human)

**Pick (ii) reframe — but specifically: SPLIT the master's Stage 4 and do only the cheap half first.**
Do **not** build the higher-fidelity FEM yet (it is the long pole, it does not test your contribution, and
it risks the same missing-mode trap at high cost). Instead: (1) write up the already-verified negative
result now (it is real and patent-relevant); (2) make **held-out netCG coverage** your trust gate and
demote NUTS-convergence to a diagnostic (your current gate conflates "the sampler struggled" with "the
model is wrong"); (3) run the **one** experiment that actually matters — put the property-keyed discrepancy
in **output/modal space, orthogonal to the stiffness** (cut/modular updating), on the **existing** model,
and check whether it both converges *and* fixes held-out coverage versus Stage-3's confounded version. That
single A/B is your thesis result and your patent's missing non-obviousness evidence. Only if it works
should you spend on higher fidelity — and when you do, frame it as **overtest/force-limiting** (your 3.1×
over-prediction is the textbook overtest error `[FLV]`), because *that* is the decision an aerospace
audience will actually sign. Beware: Stage 3 tested the *parameter-space* discrepancy, which your own
vision doc demotes — so the patent's positive evidence does not exist yet, and "property-keyed" alone did
**not** break confounding (orthogonality did the work). Bank the negative, run the orthogonal A/B, keep the
FEM in your pocket.

---

## 14. Sources

See [sources/sources.md](sources/sources.md) for URLs, HTTP status, byte sizes, and SHA-256 prefixes of
every file fetched this session. Tag map: `[FLV]` NASA Force Limited Vibration monograph (overtest /
dynamic-absorber / apparent mass); `[YUNIS]` launch-environment 3 dB / MPE; `[STATFEM]` Girolami statFEM
(data = FE + misspecification + noise); `[KOH]` Kennedy & O'Hagan calibration+discrepancy+error; `[TMCMC]`
Ching & Chen model-class selection/averaging + multimodal/flat-manifold sampling; `[BMA]` Bayesian model
averaging definition; `[DTSTATFEM]`/`[DT]` digital-twin practice. `[SPECULATIVE]`/`[OPINION]` tags mark
claims not verified against a fetched source this session (notably Brynjarsdottir & O'Hagan and Plumlee,
which I could not fetch — attributed to the project's own `notes/project_vision.md` §4).
</parameter>
</invoke>
