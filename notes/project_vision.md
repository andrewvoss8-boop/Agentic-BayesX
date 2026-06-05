# Project Vision — A Digital Bayesian Twin for Aerospace Structures

Status: working vision (living document). Last updated: 2026-06-05 (sweeping revision).
Owner: Andrew Voss (lead human). Lead agent: Claude Code (Agentic BayesX).
Communication: written for a beginner-to-intermediate reader (about one year of ML); technical terms
are defined in plain words on first use.

---

## 0. What changed in this revision (read this first)
- **Renamed the core method.** We no longer say "property-keyed." We now describe it plainly as **a
  Gaussian process `F(k)` over elemental stiffness `k`** (see §5) — the model-form error is a smooth
  function of an element's stiffness, so elements of similar stiffness/type share a similar error. It
  must enter on the model OUTPUT, ORTHOGONAL to the calibrated stiffness (not as a stiffness knob).
- **Trust reset.** The synthetic finite-element models (FEMs) and the Stage-3 result are treated as
  **preliminary plumbing, NOT validated science.** A trustworthy result now requires **more realistic,
  validated FEMs and REAL test data**, judged by held-out calibration (§7, §12).
- **Sharpened the contribution** into a novel core (the orthogonal GP discrepancy) plus a supporting
  workflow (evidence-based parameter selection; load-indicator QOIs; QOI-targeted sensor/test
  selection), with honest "novel-candidate vs established" labels (§5).

## 1. The vision in one paragraph (the Porsche framing)
StatFEM (the statistical finite element method — a way to fuse a physics model with test data while
explicitly accounting for the model being wrong) is a track Porsche. The published literature has so
far only driven it at 5 mph around a parking lot — simple, static problems where the model already
matches the data and almost no real physics has to be learned (e.g. the self-sensing-bridge digital
twin). We want to take it onto the track: real dynamic structures, learning the physics from real test
data, and pushing the result all the way to a real engineering decision (a load / margin). Doing that
without crashing requires a few new methods — and that is where the novel, patentable contribution
lives. If the new methods work, there is a patent; if they do not, there is no patent.

## 2. The problem and why it matters
- Aerospace loads prediction and model-updating from test/flight data is slow, inconsistent, and poor
  at accounting for how wrong the models are.
- Launch vehicles are a weakest-link problem: the vehicle fails if any single part is under-designed,
  so teams stack conservatism on every part. Result: structures look marginal on paper yet often have
  ~10x true margins, and mass is wasted everywhere.
- Solve it and structures can be 5-10% lighter WITH more confidence, and the design/test/verification
  process becomes consistent, auditable, and defensible — putting risk where it actually is.

## 3. Core thesis
- Girolami/Duffin et al. created StatFEM and statFEM digital twins, cleanly separating model prediction,
  model-form error (the "discrepancy"), and sensor noise — but demonstrated it only in the benign
  regime: linear-static, FE-matches-truth, hyperparameters point-estimated, no physical parameters
  identified.
- The open, hard, aerospace-relevant regime is **dynamic, physics-identifying, QOI-propagating** inference
  on **assembled-interface** structures with **real data**. That is the "track," and it is largely
  unaddressed.

## 4. The technical heart — the discrepancy lever
When you try to learn real physics (stiffness k, damping c, forcing) from dynamic test data, the model's
ERRORS and the real PHYSICS can look identical to the math. This is a single lever — the discrepancy
covariance specification (how you describe "where and how the model is wrong") — with two failure modes:
- Discrepancy too weak / too independent across frequency -> the inference OVER-COUNTS correlated data ->
  the posterior FALSELY COLLAPSES (over-confident, biased).
- Discrepancy too flexible / wrong-structured -> it COMPETES with the physics -> a non-identifiable
  "ridge" (many parameter+discrepancy combinations fit equally well), multimodality, and the sampler
  will not mix. (We have reproduced this twice: a spatial-only discrepancy gave R-hat ~ 1.5 / ESS ~ 7;
  and a same-parameter-space per-strut discrepancy gave R-hat ~ 2.85.)

Named, rigorous pitfall, not a hunch:
- Kennedy & O'Hagan (2001): discrepancy-augmented calibration; physics/discrepancy confounding.
- Brynjarsdottir & O'Hagan (2014): you cannot recover physics with a flexible discrepancy unless you put
  genuine STRUCTURE (a strong, correct prior) on it.
- Plumlee (2017), Tuo & Wu (2015-16), Sargsyan embedded discrepancy, cut/modular Bayes: existing ways to
  constrain the discrepancy to restore identifiability.

## 5. The contribution

### 5.1 Plain definitions
- **Calibration parameter** = a knob inside the model you adjust to match data, claiming to be the true
  physical value (e.g. an element/group stiffness `k`).
- **Model-form error / discrepancy** = an extra correction the model learns because the model itself is
  wrong in a way no parameter value can fix. It corrects the OUTPUT; it is not a physical claim.
- **Identifiability** = can the data pin down a unique value? If two knobs do the same thing to the fit,
  they are confounded / non-identifiable (a "ridge").
- **Orthogonal** = built so the correction can only point in directions a parameter change CANNOT
  already produce — so the correction cannot impersonate (and steal identifiability from) the parameter.

### 5.2 The novel core: a Gaussian process `F(k)` over elemental stiffness, entering ORTHOGONALLY
**What it is.** Model the discrepancy as a Gaussian process (a flexible function with a chosen
correlation structure) `F` indexed by **elemental stiffness `k`** (optionally also element type/material
and frequency). "Indexed by `k`" means two elements with similar stiffness get a high prior correlation
in their error: *elements that are similar are similarly too stiff/compliant.* Its realized value is the
frequency-dependent model-form error contribution.

**Why it is NOT just "make each element stiffness a free parameter."** Three differences:
1. **Correlated/pooled, not free knobs.** You are not estimating one independent number per element
   (hopelessly underdetermined; overfits). The GP correlation pools the error across similar elements, so
   you learn a LOW-DIMENSIONAL error field ("elements near this stiffness are ~X% off, +/- Y") that is
   **identifiable from sparse data** (statisticians call this partial pooling). This is exactly the
   "genuine structure" Brynjarsdottir & O'Hagan show you MUST have.
2. **An error-correction, not a physical claim.** It says "my model is wrong by this much for
   elements like this," not "this element's true stiffness is X."
3. **It must be ORTHOGONAL to the calibrated stiffness (the crucial part).** If `F` modifies the
   stiffness itself (parameter space, e.g. `k_j = k*exp(F)`), it IS just another stiffness knob and it
   confounds (proven in Stage 3). To work, `F` must enter on the OUTPUT (the predicted apparent-mass
   curve / residual), in a direction the stiffness cannot already move.

**How to make it orthogonal (three mechanisms, increasing strength):**
- (a) **Output-space placement** — correct the predicted apparent-mass curve, not the stiffness knob.
- (b) **Orthogonal projection** (Plumlee-style) — project `F`'s prior into the null space of the
  parameter's output "fingerprint" `dM(omega)/dk`, so `F` literally cannot imitate a stiffness change.
- (c) **Cut / modular updating** — first identify `k` from the data that genuinely pins it (the sharp
  resonance frequencies) WITHOUT letting `F` vote on `k`; then fit `F` to the residual with `k` fixed.

**The novel twist over Plumlee:** index/correlate `F` by **elemental stiffness (and type)** — a physical
structural prior — not by gradient geometry alone. Orthogonal placement + stiffness-indexed correlation
together is the candidate-novel core. (Subject to a real patent search; see 5.4.)

**Honest status of the core:** Stage 3 only showed the SAME-parameter-space (spatial) version
**confounds**. The orthogonal output-space `F(k)` version is **UNTESTED**. The A/B "orthogonal `F(k)`
beats same-space" — on a validated FEM and real data — is BOTH the thesis result and the patent's
non-obviousness ("unexpected result") evidence.

### 5.3 Supporting workflow (use it; mostly established -> dependent claims / paper, not the spearhead)
- **Evidence-based selection of which / how many parameters to update.** Frame "which knobs to free" as
  a menu of candidate models scored by Bayesian evidence (the marginal likelihood, which penalizes
  needless complexity — Occam's razor), then select or average (Beck's Bayesian model selection; Ching &
  Chen TMCMC model-class selection/averaging). Guided by identifiability/sensitivity (Fisher information,
  profile likelihood) and validated by held-out calibration + effective-sample-count. This is the
  principled way to "ride the line" between underdetermined (too many knobs -> ridges) and
  artificially-collapsed (over-counting correlated full-FRF/mode-shape data).
- **Load-indicator QOIs.** The decision quantity is a force-limiting / apparent-mass / net-CG load
  indicator (NASA-HDBK-7004C), e.g. netCG = transmitted interface force / load mass.
- **QOI-targeted sensor placement + quick frequency/modal-ID tests.** Choose accelerometer locations and
  cheap system-ID modal tests that maximize what the digital twin learns about the load indicators
  (Papadimitriou's QOI-information-gain optimal sensor placement). Established; defensible only tied to
  the core.

### 5.4 Prior-art read (literature-only, NOT a cleared patent search)
- A. Orthogonal, stiffness-indexed (`F(k)`) model-form discrepancy in DYNAMIC StatFEM: novelty
  Medium-High; the strongest, most defensible patent spearhead. (Distinguish from Plumlee's
  gradient-orthogonality by the physical stiffness/type indexing + dynamic/FBS-QOI context.)
- B. Confounding-breaking shared-invariant discrepancy + experiment design: more crowded (Plumlee,
  cross-experiment calibration, BOED-under-misspecification) -> dependent/defensive claim or paper.
- C. QOI / load-indicator sensor placement: Papadimitriou's QOI-OSP covers most; defensible only tied to A.

Patentability strategy:
- Subject-matter eligibility (Sec 101 / Alice): claim a concrete TECHNICAL PROCESS ("a method of
  vibration-testing / model-updating / determining a design margin for a physical structure, comprising
  ...") producing a tangible output, NOT "a method of computing a posterior."
- Non-obviousness (Sec 103): the demonstrated unexpected result — the same-space/spatial approach fails
  (non-convergence / over-prediction) where the orthogonal `F(k)` approach succeeds. The planned
  real-data experiment IS the legal evidence.
- Claim family: independent claim (A inside a testing/updating workflow) + dependents (B orthogonality
  trick, C placement, force-limit/apparent-mass use case).

## 6. Scope — the singular objective
Per Bilionis's mandate (one objective, not ten loosely connected things):
> Take StatFEM onto the track: build and validate a dynamic digital twin of a realistic aerospace part
> (a small-scale source/load "tray"), learn its physical properties from REAL vibration data, produce an
> honest (non-collapsed) estimate of the load that matters, and develop the orthogonal `F(k)` discrepancy
> method that keeps it from crashing.

In scope: dynamic StatFEM, the orthogonal `F(k)` discrepancy, the subscale tray experiment with REAL
data, honest-uncertainty (held-out) validation, propagation to a load/QOI, NASA-HDBK-7004C apparent-mass
framing.
Out of scope / back burner: full BOED close-the-loop, geometry optimization, segmentation, the full
rocket digital twin (also SpaceX prior art).

## 7. Approach — realistic FEMs + REAL data as the trust foundation
**Trust comes from REAL data + held-out calibration — not synthetic parameter recovery, and not NUTS
convergence by itself.** The current synthetic FEMs and the Stage-3 result are preliminary plumbing
(§12); they are not yet evidence.
- **Realistic, validated FEMs.** Build the differentiable forward model at enough fidelity to represent
  the real modes/antiresonances that drive the load, and VALIDATE it — against analytical benchmarks AND
  against real modal data — documenting its fidelity and known gaps. A "plausible but unvalidated" FEM is
  not acceptable.
- **Real data (the centerpiece).** The McCallie self-funded subscale source/load tray, tested under
  different excitations and assembly levels. As a cheaper stepping stone, also exercise the pipeline on a
  REAL public record (e.g. a vibrationdata dome-ignition record or a 4TU/NTRS ground-vibration-test
  dataset) to expose the joint/nonlinear / FEM-vs-hardware error the method is meant to handle.
- **Agentic harness.** Builds the differentiable forward model, runs NUTS/HMC Bayesian updating, and
  validates trustworthiness via held-out calibration (predict held-back data; check the 95% bands really
  contain the truth ~95% of the time). This automation is also the piece most useful to Bilionis's
  autonomous-engineering interests.
- **Sampler standard (project rule).** NUTS/HMC is the default; report R-hat and ESS over ALL sampled
  variables (incl. raw hierarchical latents), divergence fraction, >= 4 chains, non-centered for
  hierarchical variance models. Do not claim "NUTS active" without passing diagnostics + one-command
  replay + checker output. Convergence is a DIAGNOSTIC; the TRUST gate is held-out QOI calibration.

## 8. Stakeholders (and honest tensions)
- Andrew (lead): StatFEM/structural-dynamics digital twin + 7004c; industry expertise. NOTE: the
  rocket-twin / secondary-structure methods from SpaceX are SpaceX prior art -> credibility, not patent.
- Dr. Ilias Bilionis (advisor): agents, harnesses, autonomous engineering; wants ONE objective,
  transferable lessons on closing the loop, would accept a patent as a deliverable. Substack writing
  planned (he must approve; sponsor-confidentiality gate).
- Relativity: lighter trays, nonlinear joint/"rattlebasket" damping, max-info vibe testing across
  assembly levels, 7004c. Back-burner unless funded; strengthens the patent's commercial story.
- Dr. Todd Doehring: hyperstructures, BGO, AI segmentation (not Andrew's expertise) -> collaboration,
  not the patent.
The unifying object that serves almost everyone: the subscale tray testbed with real data.

## 9. IP path (DECIDED 2026-06-05)
- Decision: Andrew will NOT chase sole personal ownership. He will use Purdue/PRF support (they
  pay/prosecute the patent).
- Keeps regardless: NAMED INVENTOR credit, plus a discretionary ~1/3 creator share of net proceeds.
- Consequences that simplify the work: collaborate fully with Bilionis (co-invention OK); accept
  compute/hardware reimbursement; use Purdue resources.
- The discipline that does NOT relax: DISCLOSE to the Senior IP Officer BEFORE any public disclosure
  (Substack, paper, talk). Sequence: disclose -> PRF files (>= provisional) -> then publish.
- Pending: Beth Siple determination (Purdue IP vs I.A.1 exception; research credits as "a University
  course"; University Resources). PRF must CHOOSE to invest (~180 days) -> the aerospace value story
  matters.
- TODO: file a provisional early; document a dated conception record for the orthogonal `F(k)`
  discrepancy; attorney read on the Sec 101 framing.

## 10. Knowledge gaps being addressed
- StatFEM not yet taken into aerospace data classes (random, transient, shock) or assembled-interface
  (CMS/FBS) problems where the QOI lives, with REAL data.
- Honest, tractable likelihoods that do not artificially collapse the posterior.
- Separating real physics from model error (the lever) in dynamic inference.
- Propagating the posterior all the way to a load/QOI/margin.
- Computational tractability on full-size models; automating the workflow agentically.

## 11. Deliverables
- Bilionis proposal doc: big problem -> prior work -> gaps -> objective -> approach, patent section in the
  Purdue-supported framing.
- Invention disclosure for the orthogonal `F(k)` discrepancy (also the dated conception record), in the
  "method of testing/updating a physical structure" Sec 101 framing.
- A paper/conference target.
- Substack write-up of the agentic work (after disclosure/filing, with approval).
- The subscale tray experiment (REAL data) + agentic StatFEM harness + held-out-calibration trust result.

## 12. Honest status — what is NOT trusted / proven (do not overclaim)
- **The current FEMs and the Stage-3 result are NOT trusted as science.** They are coarse synthetic
  models (a coarse inference model fit to a slightly-less-coarse synthetic "truth"); a real, defensible
  result needs **realistic, validated FEMs and REAL data**, judged by held-out calibration.
- The orthogonal `F(k)` discrepancy advantage is a HYPOTHESIS. Stage 3 only showed the same-parameter-
  space (spatial) version confounds; the orthogonal output-space version is UNTESTED. That A/B (on a
  validated FEM + real data) is the science and the patent's non-obviousness evidence.
- Earlier tight posteriors are NOT trust-validated; held-out calibration is the right gate and is only
  partly done.
- Prior-art read was literature-only; NO patent-database / freedom-to-operate search has been run.
- IP ownership determination is PENDING (Beth). Treat ownership/share statements as provisional.
- Not legal advice; Sec 101 eligibility is the most uncertain area -> attorney review required.

## 13. Immediate next actions
1. **Get real (or realistic-validated) inputs.** (a) Plan/begin the McCallie subscale tray test; and/or
   (b) pick ONE real public apparent-mass / FRF record to run the pipeline against; and (c) raise FEM
   fidelity to a VALIDATED level (benchmarks + real modal data).
2. **The decisive method A/B (cheap, can start on the existing model as a method check):** orthogonal
   output-space `F(k)` vs the same-parameter-space version, gated on **held-out netCG coverage**. This is
   the thesis + patent non-obviousness evidence once run on trusted inputs.
3. Send the Beth email; get the ownership determination in writing.
4. Finalize the Bilionis proposal (Purdue-supported patent framing).
5. Write the dated invention-disclosure / conception record for the orthogonal `F(k)` discrepancy.
6. Run a real patent-database search (Google Patents / Lens.org) or route to an attorney.
