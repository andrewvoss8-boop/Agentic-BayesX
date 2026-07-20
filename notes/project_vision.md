# Project Vision — A Digital Bayesian Twin for Aerospace Structures

Status: working vision (living document). Last updated: 2026-06-19.
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
- **(2026-06-19) Added §7.1 — evidence from the real ShockSat that the amplitude bands are too WIDE to
  certify, why, and the path to usable ones** (better/agentic FEM correlation; feature-space discrepancy;
  our own test stand for maximally-informative testing). Two new directions land in §13 next actions.

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

## 2.1 Industry adoption reality — meet the skeptics where they are (Andrew, 2026-06-10)
Big names in industry with major dynamics experience have **not heard of Bayesian FEM updating** and are
skeptical it is "**polishing a turd**" or "**pencil whipping**." Their objections are concrete and partly
fair, and we must address them DIRECTLY rather than out-argue them:
- **Slow / computationally intensive.** Multi-hour NUTS on a full FEM is a non-starter in a real aero
  schedule.
- **Garbage in, garbage out.** Bad test data, a bad model, or bad priors break it — and the user often
  cannot tell which.
- **Assumption-dependent / arbitrary.** It leans on choices like the discrepancy/observation-noise scale
  (sigma_d), priors, etc. that are ultimately arbitrary or unjustified to a practitioner.

**Strategic consequence (foot in the door).** Do NOT lead with a heavy, slow, assumption-laden Bayesian
machine. Aim first for **very simple, borderline empirical / hand-calc-level tools that plug and play
directly into existing aero workflows** — give a practitioner something useful and auditable with their
current data and current process, then earn the right to add the Bayesian layer underneath. This reframes
the project's near-term deliverable away from "a better posterior" and toward "a tool an aero loads
engineer would actually run on Monday." It also raises the bar on our honesty gates: every arbitrary
assumption (sigma_d, priors) must be surfaced with a sensitivity result, and the held-out trust test (§7,
§12) is our direct answer to "GIGO / pencil-whipping."

## 2.2 Response limiting, not force limiting, is the industry-practical QOI (Andrew, 2026-06-10)
In practice industry does **little force limiting**; **response limiting is far more common**. To stay
industry-applicable, use a **response-limit proxy for the force limit**: pick **1-2 sensors (accelerometers)
that are highly correlated with the net-CG response at the high-priority modes** (the modes driving the
net-CG response / interface force), and set an appropriately scaled limit on those sensors as a stand-in
for the interface-force limit. This keeps the 7004C apparent-mass / interface-force story as the physics
backbone (§5.5) while expressing the deliverable in the response-limit language a test/loads team already
uses. NOTE for current work: this directly informs the QOI choice in the in-flight ShockSat × tray coupled
study (per-mount interface load vs net force) — a response-limit-proxy QOI is now a first-class option.

## 3. Core thesis
- Girolami/Duffin et al. created StatFEM and statFEM digital twins, cleanly separating model prediction,
  model-form error (the "discrepancy"), and sensor noise — but demonstrated it only in the benign
  regime: linear-static, FE-matches-truth, hyperparameters point-estimated, no physical parameters
  identified.
- The open, hard, aerospace-relevant regime is **dynamic, physics-identifying, QOI-propagating** inference
  on **assembled-interface** structures with **real data**. That is the "track," and it is largely
  unaddressed.

## 3.5 What we are actually doing — and where novelty can honestly come from (stance, 2026-06-06)
Be honest about the stance: we are NOT claiming a brand-new statistical method up front. We are
**TEST-DRIVING StatFEM and its neighbors** (Bayesian FE model updating, KOH/Plumlee calibration, TMCMC,
hierarchical Bayes, force-limited vibration) on aerospace structural-dynamics problems Andrew is a
genuine expert in. We do as much **scrappy, automated, agentic testing of synthetic AND real examples**
as we can to pressure-test where these tools BREAK. The novel, patentable innovation is **whatever it
takes to make these tools actually WORK in a real aerospace workflow and modeling context** — discovered
AS we test, not pre-claimed. If a fix that makes it work emerges and is defensible -> patent; if not ->
no patent.

**Literature read (2026-06-06):** Andrew has now read Kiran, Das & Bansal (2025), "A state-of-the-art
review of Bayesian FE model updating techniques for structural systems," Probabilistic Engineering
Mechanics 80:103761 (the "review of Bayesian..." PDF). It sets the honest baseline:
- Bayesian FE model updating is MATURE and thoroughly reviewed: likelihoods in time/frequency/modal
  domains; the Beck-Katafygiotis global/local/un-identifiability taxonomy (= our Stage-3 ridge); model
  errors (Mottershead); prediction-error; model-class selection (evidence/Occam); hierarchical Bayes;
  TMCMC; complex & INCOMPLETE modal data; SHM/damage detection. => Do NOT claim novelty in any of these,
  including "interfaces" / "incomplete complex modal data" updating (already published).
- The review NEVER mentions StatFEM (Girolami). The Bayesian-FE-updating world (Beck/Katafygiotis/
  Yuen/Papadimitriou) and StatFEM (applied math) are SEPARATE literatures -> bringing StatFEM's
  discrepancy formalism into this aerospace dynamic updating context is a genuine literature BRIDGE.
- The review's OWN stated gaps that line up with us: "Bayesian FE model updating using OUTPUT-ONLY
  time-history data has NOT been researched" (the unknown-forcing / operational-modal-analysis white
  space); a GENERALIZED integrated workflow (modal test -> ID -> updating -> damage) as future scope
  (our tech-assisted installed-part workflow); complex modal data still under-explored; surrogate/ML for
  tractability; Bayesian UQ for differential equations (probabilistic numerics, StatFEM-adjacent). It
  does NOT cover aerospace force-limited vibration / load QOIs at all.
- Caution (review ref [184], Schneider et al.): a multiplicative model error "correlated in both SPACE
  and FREQUENCY" already exists -> our discrepancy-correlation idea is adjacent to prior work; more
  reason the defensible novelty is the application + unknown forcing + load QOI, not the correlation
  itself.

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
- Plumlee (2017, JASA 112:1274-1285) [READ IN FULL 2026-06-05]: defines the calibration parameter as the
  MINIMIZER OF A LOSS (KOH never defined it -> their posterior is too broad), PROVES the bias must be
  ORTHOGONAL to the model's parameter-gradient df/dtheta, and builds the bias GP prior by projecting a
  base covariance onto that orthogonal space; when the model is expensive it emulates it + uses
  modularization + a plug-in gradient. IMPORTANT: Plumlee's setting has a KNOWN, CONTROLLED input; the
  bias is a function of that known input.
- Tuo & Wu (2015-16), Sargsyan embedded discrepancy, cut/modular Bayes: other ways to constrain the
  discrepancy to restore identifiability.

## 5. The contribution

### 5.0 Where the novelty actually lies (UNDER RECONSIDERATION, 2026-06-05)
Honest update after reading Plumlee (2017) in full: **orthogonality-to-the-parameter-gradient is
Plumlee's**, and our "GP `F(k)` over elemental stiffness" is essentially a CHOICE OF BASE COVARIANCE that
plugs into his orthogonal projection. So **"orthogonal + GP discrepancy" alone is not our novelty**, and
the stiffness-keying is a structural-prior choice of the kind Brynjarsdottir & O'Hagan already say is
needed. We should NOT lock the patent claim to "property-keyed / orthogonal discrepancy" yet.

What is genuinely DIFFERENT from Plumlee / KOH / Surer-Plumlee-Wild / published StatFEM is that they all
assume a **KNOWN, CONTROLLED input**. Aerospace forcing is **UNKNOWN and STOCHASTIC** (the flight
random-vibration environment): we measure RESPONSE, not the input force, so the forcing must be inferred
or marginalized ALONGSIDE the physics and the model-form error. That **three-way problem (physics x
discrepancy x unknown forcing)** has its own identifiability trap (is the response large because the
forcing was large or the structure compliant?), and the methods that must arise to keep it identifiable
AND push it to a force-limiting load QOI may be the real, more-defensible contribution (Andrew's instinct).

Honesty guardrail: "unknown input" is itself a studied field — operational modal analysis (OMA), joint
input-state estimation (Lourens; Maes; Gillijns-De Moor), Bayesian force identification. So the novelty
is NOT "unknown forcing" by itself; it would be the **combination**: dynamic StatFEM (model-form error)
+ unknown stochastic forcing + a force-limiting / apparent-mass LOAD QOI + the honest held-out trust
test. The **apparent-mass framing (`M = F/a`, a structure property independent of forcing LEVEL)** is the
natural bridge for the input/system ambiguity. Treat the novelty LOCATION as OPEN, pending a literature
review (OMA / input-state estimation / force-ID) and a real patent/FTO search.

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

**Relation to Plumlee (read carefully — see 5.0):** orthogonality-to-the-gradient is Plumlee's; the
stiffness-indexed `F(k)` is a CHOICE OF BASE COVARIANCE plugged into his orthogonal projection. So this
is a useful, correct method for our problem, but its STANDALONE novelty is modest. The more defensible
novelty likely lies in the unknown-stochastic-forcing aerospace setting (5.0), not in `F(k)` by itself.

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
  (Papadimitriou's QOI-information-gain optimal sensor placement = PHYSICAL experiment design).
  Established; defensible only tied to the core.
- **Adaptive emulator-run design (different "experiment", a tractability tool).** Surer, Plumlee & Wild
  (2024, Technometrics) [READ 2026-06-05] design WHICH SIMULATION RUNS (parameter settings) to evaluate
  to build an emulator that learns the posterior efficiently (their EIVAR criterion: explore uncertain
  posterior regions + exploit high-density ones). Use this if our FEM is too expensive to sample
  directly. NOTE: this is design over SIMULATION inputs, NOT over physical sensors — distinct from
  Papadimitriou. Established.

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

### 5.5 Substructuring (FBS / CMS): the structural backbone of the 7004C center (2026-06-08)
NASA-HDBK-7004C force limiting IS a two-substructure impedance problem — source apparent mass vs load
apparent mass at the interface — so substructuring is NOT a side branch; it is the native math of this
project.
- **FBS (Frequency-Based Substructuring) = the headline framework.** Data-driven, frequency-domain,
  7004C-native (apparent mass M=F/a is an FBS primitive). It hands you the interface force (the netCG QOI)
  from the coupled admittance, and fits the "characterize source + load by apparent mass, couple, read off
  the interface force" workflow — including when the source is known only as an apparent mass / test
  environment.
- **CMS (Craig-Bampton) = the tractability tool.** Reduce each component FEM to interface + modal DOF so
  the StatFEM calibration stays affordable. Use BOTH: CMS to reduce, FBS to couple.
- **Why this solves several hard problems at once.** FBS lives in measured admittance (OUTPUT) space —
  exactly where the discrepancy must sit (orthogonal to the component stiffness, per 5.2 / Stage 3). It
  also LOCALIZES the model-form error to the interface (where the model is most wrong AND where the load
  lives AND where 7004C operates) -> fewer, physically-meaningful, more-identifiable parameters.
- **Novelty placement (do / don't).** DON'T claim FBS or CMS (mature: Craig-Bampton 1968; LM-FBS de
  Klerk/Rixen/Voormeeren 2008) or "uncertainty in FBS" generally (Trainotti/Haussler/Rixen already
  propagate measurement uncertainty). DO consider: a StatFEM-calibrated model-form discrepancy AT THE
  INTERFACE ADMITTANCE -> a probabilistic, data-updated FORCE-LIMITED interface load (the 7004C endpoint)
  under unknown forcing, held-out validated. This promotes idea C in patent_ideas_ranked.md from a side
  idea to the structural backbone.
- **6-interface-point practicality.** Multi-point interfaces in experimental FBS are handled by the
  Virtual Point Transformation (van der Seijs / Rixen): reduce each interface location's sensor/impact
  cluster to a 6-DOF virtual point (assuming the local interface region is rigid), giving collocated
  forces/responses and the rotational DOF you cannot measure directly; LM-FBS then enforces compatibility
  + equilibrium over ALL interface DOF. The interface inversion (B Y B^T) is the ill-conditioned,
  noise-amplifying weak point -> exactly where the Bayesian/StatFEM uncertainty treatment adds value.
- **Honest caution.** The automotive-NVH joint-impedance reservoir is unsearched; Bayesian/stochastic
  substructuring may have prior art -> needs the targeted scan before any novelty claim.

### 5.6 What we CLAIM vs. the value story (2026-06-08, after Session-3 scan + the Siemens TPA find)
A flight decision (launch go/no-go) and "using a model to set a force limit" are NOT the invention:
- People already set model-based force limits and make launch calls from correlated FEMs every day; the
  Siemens/LMS patent US8731868B2 (Transfer Path Analysis, active ~2030) even claims DETERMINISTIC
  model-based INTERFACE-LOAD characterization from operational data. So "first to use StatFEM/Bayesian for
  an existing task" = obvious substitution (KSR) = NOT patentable; and a decision is not a patentable step
  (and is Sec 101-exposed).
- THE CLAIM is the specific ARTIFACT + the technical effect it delivers that the prior art cannot: a force
  limit (the NOTCH programmed into the shaker controller for a qual test) produced as a CALIBRATED
  POSTERIOR that (a) separates interface model-form error from physics (the orthogonal interface-admittance
  discrepancy), (b) under unknown operational forcing, (c) with uncertainty VALIDATED by held-out coverage
  -> a probabilistic, discrepancy-aware, defensibly-less-conservative notch.
- Non-obviousness is NOT "we added error bars." It is the demonstrated technical effect: deterministic
  (Marchand/Kolaini/C^2) and measurement-noise (Trainotti/Rixen) methods CANNOT separate model error from
  physics, so any naive uncertainty they add is wrong (the confounding/ridge); ours passes held-out
  coverage, enabling a less-conservative-yet-defensible limit. That is the "unexpected result."
- Design-around target = US8731868B2 (Siemens TPA): claim around it by REQUIRING the three things it lacks
  — (1) a calibrated model-form discrepancy at the interface admittance, (2) a probabilistic
  force-limit/apparent-mass output, (3) held-out coverage as the acceptance criterion.
- The flight decision / lighter-and-safer structures stays the WHY-IT-MATTERS (value story), NEVER the
  claim.
- Hard gate: no held-out result on real data -> no patent.

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

## 6.1 Robustness-first restatement of the objective (Andrew, 2026-06-10) — THE primary build target
Andrew re-centered on the ORIGINAL plan and named the headline requirement explicitly: a **LIVE digital
twin of the primary structure in apparent-mass / interface-environment terms that is ROBUST TO MODEL
ERROR**. It must keep providing value with coarse models, large model-form error, sensor nodes not aligned
with the test point, even a WRONG-VERSION model (e.g. a Starship V2 FEM updated against a tap test on a
partially-assembled V3 at different pressurization). It ingests a SCRAPPY frequency/ID apparent-mass test
(coupled OR uncoupled config) and still returns meaningful QOI and vibe-test-plan predictions WITH
confidence intervals carrying BOTH the 7004C apparent-mass effect AND the Bayesian effect. Non-brittle is a
hard requirement: a bad model must WIDEN the intervals (and say so), never give a confident wrong number.

**Honest scope line (backed by our own ShockSat evidence).** Under large model error the QOI /
apparent-mass PREDICTION can stay calibrated (intervals widen but COVER) while the PHYSICAL-PARAMETER
identification degrades gracefully (parameters fall back to prior). We do NOT claim to recover the true
physics of a wrong model (Brynjarsdottir-O'Hagan / Stage-3 confounding). The defensible claim is a
calibrated, HELD-OUT-VALIDATED QOI under model error — NOT "we fixed your wrong FEM." The ShockSat modal
twin already exhibited exactly this: held-out FREQUENCY prediction stayed robust even when identification
was partial and fragile. Make that the headline proof-of-behavior.

**What delivers the robustness (this is where the design effort goes):**
- Observe the interface OBSERVABLE that carries the QOI — drive-point / interface apparent mass M(ω)=F/a —
  not internal mode shapes; the test measures it directly and the load lives there, so interior model
  error barely matters. M=F/a is forcing-LEVEL independent → robust to unknown forcing level too.
- Orthogonal, output-space discrepancy (the F(k) thesis, §5.2) generous enough to ABSORB model error
  without stealing identifiability — robustness IS the discrepancy treatment; a coarse model just makes the
  discrepancy work harder and the bands wider.
- Calibrate only what the data pins (a few effective interface/modal params; FIM downselection); let the
  discrepancy carry the rest.
- Node/sensor-vs-model misalignment handled by an observation operator / virtual-point transformation WITH
  its own uncertainty, not assumed exact.
- Graceful degradation MEASURED by held-out QOI coverage: the trust gate is that the bands cover even when
  wide. This is our direct, demonstrable answer to the "GIGO / pencil-whipping" skeptics (§2.1).

**Reconciles with §2.1 "simple, plug-and-play."** The simplicity is a LOW MODEL/DATA REQUIREMENT (works
from a coarse model + a scrappy apparent-mass test), NOT a dumbed-down method. That low barrier is the foot
in the door; the robust, held-out-validated posterior is the value. The §2.1 hand-calc tool sketches did
NOT resonate; this robust-twin restatement supersedes them as the build direction.

**Two stated companion asks (already partly built):** (1) optimal sensor placement for LOAD-INDICATOR
information gain (Papadimitriou QOI-OSP; the Opus FIM experiment-design already produces best accel/tap
locations); (2) optimal parameter downselection/POOLING for Bayesian updating (Bayesian evidence /
model-class selection + the F(k) partial-pooling discrepancy; FIM already says ~3 identifiable).

**First discriminating experiment (proposed, NOT yet launched — awaiting Andrew scope confirm):** a
deliberately wrong/coarse model + a scrappy apparent-mass test on a "different" truth → show the twin's QOI
interval still COVERS while widening, and a deterministic prediction is confidently wrong. Two open scope
questions for Andrew: (a) prototype on existing ShockSat+Opus-tray assets vs hold for McCallie real tray;
(b) lead with the robustness/coverage-under-wrong-model demo vs the uncoupled→coupled
apparent-mass + vibe-test-plan-with-CIs pipeline.

## 6.2 Discrepancy-prior front-end: a dial / LLM that turns KNOWN config deltas into the error model (Andrew, 2026-06-10)
Idea: let the user either (a) DIAL A KNOB per discrepancy CATEGORY — different config, forcing, build,
pressurization, integration/assembly status, etc. — or (b) just DESCRIBE the differences in plain English to
an LLM, which applies the appropriate knockdowns / mock-ups and tweaks the error assumptions (prior MEANS
AND prior WIDTHS) accordingly. This is the USER-FACING FRONT DOOR of the robustness-first twin (§6.1): the
discrepancy does the heavy lifting, and this is how a (non-Bayesian) engineer TELLS the twin how wrong to
expect the model to be — turning the "arbitrary sigma_d" objection (§2.1) into a defensible ELICITATION from
KNOWN engineering deltas instead of a made-up number. Speaks the existing-workflow language: aero loads
already applies model-uncertainty factors / knockdowns; this automates translating a described config delta
into a discrepancy PRIOR.

Guardrails — these ARE the design, not polish:
- Map each delta to discrepancy STRUCTURE, not a scalar fudge: which modes/bands/DOF, the
  frequency-correlation, and the SIGN/mechanism. Pressurization stiffens membrane modes (banded); a missing
  sub-assembly removes mass + DOF (a mock-up, not just a knockdown); integration status changes the interface
  BC; build-to-build ≈ per-mode random scatter. Key the delta to WHERE it acts physically (modal strain
  energy / the F(k) structure) so it composes with the orthogonal output-space discrepancy.
- Two layers per delta: a prior-MEAN mock-up adjustment AND a prior-UNCERTAINTY inflation. The scrappy
  apparent-mass test narrows from there.
- MUST WIDEN, NOT FALSELY NARROW. Safe direction is conservative. A knob that dials sigma_d DOWN to get a
  tighter answer is the automated pencil-whipping the skeptics fear — gate any TIGHTENING on held-out
  coverage, never on user preference. The dial can make you humbler for free; confidence must be earned by
  data.
- LLM = RETRIEVAL / elicitation front-end over a CALIBRATED knockdown / empirical-delta library
  (config-to-config, build-to-build, pressurized-vs-not deltas observed in real tests), NOT a free
  generator. Every applied knockdown TRACEABLE to a source or explicitly labeled a coarse guess with a wide
  band. An LLM confidently inventing a knockdown is GIGO with extra steps.
- Held-out QOI coverage remains the trust gate over the whole thing.

Novelty caution: knockdown / model-uncertainty factors are standard practice and "LLM-for-engineering" prior
art is emerging fast — do NOT claim novelty in the front-end without an FTO/lit scan. Defensible value stays
the held-out-validated, discrepancy-aware QOI; this is UX / prior-elicitation on top of it.

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

## 7.1 Evidence from the real ShockSat: the bands are too WIDE to certify — why, and the path to usable ones (2026-06-19)
The real-ShockSat validation (Card C, `artifacts/reports/statfem_real_validation_20260617/`) produced a twin that
is HONEST (held-out calibrated, never overconfident — the §6.1 robustness behavior) but whose amplitude / energy
bands are **too wide to be usable for tight aerospace certification**. Andrew's engineering verdict (correct): no one
can accept a 95% band ~6x above the mean in |H| (≈34 dB; even wider in band-GRMS). This is the central, honest GAP —
documented here so it shapes priorities, not buried in a study folder.

**Why the bands are that wide (evidence-backed, not a hunch).** The model-form discrepancy must be this wide to stay
calibrated given how wrong a COARSE FEM is. Three drivers, in order:
1. **Peak-FREQUENCY misalignment dominates.** A few-% error in where the FEM's resonances sit creates giant
   per-frequency residuals at every sharp peak (model tall where data is small and vice-versa), inflating the
   discrepancy sigma even when peak HEIGHTS are right. This is partly an ARTIFACT of measuring the error in the wrong
   space (per-frequency magnitude of a resonant function) — see the feature-space fix below.
2. **Mode-shape PARTICIPATION error.** With a single fixed UNITS gain (no per-channel fitting), the FEM mis-
   distributes band energy across sensors by x0.1-x4.6 — over-predicting at the hard impact-face/joint channels,
   under-predicting elsewhere. A genuine spatial model error.
3. **Single hit / single impact.** One strike → noisy damping, no averaging → part of the width is measurement
   noise this dataset cannot beat.

**The honest meta-finding (the Ilias "find the gap" answer).** StatFEM's discrepancy machinery makes the twin
TRUSTWORTHY but **cannot manufacture sharpness the underlying model does not have.** Card C threw the full kit at the
amplitude width — inferred mode-shape FIELD (Beck/Au/Vanik), measured per-mode damping, spatial freq×space kriging,
more modes, MAC-informed matching — and bought only ~1.4x, and only when the units-gain ambiguity was resolved in
its favor. Under a physics-honest FIXED units gain (no free knob) every method under-predicts held-out peaks ~2x.
**The gap is FEM amplitude/shape fidelity; the improvement is a better MODEL, not cleverer statistics.** (The
gain-ambiguity itself is a symptom: the only reason you must CHOOSE a gain target is that the FEM's peak-to-floor
shape is wrong; a correct model removes the choice.)

**The path to usable bands (priority order):**
1. **A better FEM — and the AGENTIC FEM-CORRELATION opportunity (NEW strategic direction).** The primary lever is a
   model whose peaks land within ~1% and whose mode shapes put energy in the right place; then the discrepancy can be
   SMALL and the bands tight. **Sobering nuance (Andrew):** the ShockSat FEM we used was ALREADY a vendor-correlated
   model of a *relatively simple* structure, yet it still needs refinement to give usable amplitude bands. That is a
   bit concerning for the "works on a coarse model" promise — BUT it is also an **opportunity to explore AGENTIC FEM
   CORRELATION (data-driven re-meshing / model improvement driven by where the data says the model is wrong), an
   essentially unexplored domain** and a natural fit for Bilionis's autonomous-engineering interest. Card D
   (`shocksat_fem_remesh_20260618`) is the first step. Honesty/novelty caution: FEM model-updating / correlation is
   mature; the *agentic automation* of it (an agent diagnosing the wrong regions from held-out residuals and
   re-meshing/re-parameterizing them) is the angle — needs the usual lit/FTO scan before any novelty claim, and the
   held-out trust gate still decides. This complements, not replaces, the orthogonal F(k) discrepancy: a better model
   shrinks the discrepancy; the discrepancy keeps whatever error remains honest.
2. **Feature-space discrepancy (a NEXT experiment — Andrew: "we definitely should do this").** Put the uncertainty in
   FEATURES — "peak at f0 ± X%, amplitude Y ± Z dB per mode" — instead of a per-frequency |H| band. This removes the
   misalignment-driven inflation (driver 1) and turns a x6 vertical band into a narrow frequency wiggle + a modest
   amplitude band: a statement a loads engineer can actually use and certify against. We already have the modal
   machinery; this directly tests how close a USABLE (e.g. +3/+6 dB margin) band is, and how much of the remaining gap
   is the model (lever 1) vs the single-hit data (lever 3).
3. **Maximally-informative testing on OUR OWN stand (data lever).** We CANNOT add data to the ShockSat set — it is not
   ours (one impact, one hit, fixed sensors). The fix is to design our OWN test (the §7 McCallie subscale tray, or a
   dedicated stand) to be MAXIMALLY INFORMATIVE for exactly the limits found here: multi-hit / multi-reference / roving
   excitation to beat single-hit damping noise and pin amplitudes; sensor placement at the high-participation /
   high-discrepancy locations (Papadimitriou QOI-OSP, §5.3); coupled AND uncoupled apparent-mass configs. This turns
   the band-width finding into a concrete TEST-DESIGN requirement, and is where the "spend the next test dollar here"
   guidance (Study L) becomes an actual test plan.

**Scope honesty in the meantime.** As-is, the real-data twin is a CONSERVATIVE screening / flag-when-the-FEM-is-wrong
tool (§6.1 robustness behavior), NOT a tight certification twin. Report it that way — "FEM ± documented model-form,
not yet validated to a tight margin" — never as a sharp predictive twin. The width is the honest cost of a coarse
model + scrappy data, exactly the regime §6.1 promises to survive; making it SHARP (not just honest) is the open work.

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
- **UNKNOWN, STOCHASTIC FORCING:** inferring/marginalizing the excitation (we measure response, not input
  force) jointly with the physics and the discrepancy, and keeping all three identifiable — the aerospace
  reality that the known-input calibration literature (KOH/Plumlee) does not cover. Likely novelty home
  (5.0); overlaps operational modal analysis / input-state estimation, so the contribution is the
  combination, not the bare idea.
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
- **The LOCATION of the novelty is itself open (5.0).** After reading Plumlee in full, orthogonality is
  his and `F(k)` is a base-kernel choice -> modest standalone novelty. The likely-stronger axis
  (unknown stochastic forcing + force-limiting load QOI in dynamic StatFEM) OVERLAPS operational modal
  analysis / input-state estimation / force identification. Do not claim novelty in EITHER direction
  until a literature review of those fields and a real patent/FTO search are done.
- Earlier tight posteriors are NOT trust-validated; held-out calibration is the right gate and is only
  partly done.
- Prior-art read was literature-only; NO patent-database / freedom-to-operate search has been run.
- IP ownership determination is PENDING (Beth). Treat ownership/share statements as provisional.
- Not legal advice; Sec 101 eligibility is the most uncertain area -> attorney review required.

## 13b. Global lessons for how we run autonomous SciML (added 2026-06-09, from the modeling-freedom experiment)
These shape our top-level priorities, not just one run. (Full plain-English write-ups in lessons-learned.md.)
1. **One run, one question.** Each experiment gets a single falsifiable question and a single success
   criterion. Do NOT bundle a method-demonstration with a science deliverable in one run — you get a weak
   version of both (this is exactly how the ShockSat half came out hollow).
2. **Validity before rigor: prove the experiment CAN answer the question before running it.** A run needs
   genuine free choices (parameters/competing models) AND a held-out check that can actually tell good
   models from bad. Ceremony (rules, seals, hashes, scoring) is not validity. Make "can this experiment
   discriminate hypotheses?" a standing gate alongside the convergence gate — our real trust gate
   (held-out calibration on real data) must clear it or it will repeat the hollow ShockSat setup.
3. **A pre-committed hidden answer key is the decisive trust test.** The convergence/quality gate is
   necessary but not sufficient; only an honestly hidden held-out answer caught the gate-passing,
   flexible-model overfit. This validates the project's "held-out calibration is the trust gate" stance —
   and it must be hidden from EVERYTHING the agent can read, including the code/generator that made it.
4. **Honest "I couldn't do this" is the load-bearing safety property** — worth more than any single checker.
   The run stayed truthful only because the worker refused to fake a StatFEM posterior and labeled its
   shock prediction low-confidence. Keep honest-labeling a non-negotiable top-level rule.
5. **Real data is not automatically more valuable — match the data to the question's TYPE.** Known-truth
   synthetic is right for validating a METHOD/detector; real data is required for a SCIENCE claim. Don't
   reach for real data reflexively when the question is methodological.
6. **Out-of-distribution ≠ overfitting test.** Holding out the pyro regime answered "does the modal twin
   extrapolate to new physics?" (no — 99.9% of shock energy sits above its ~152 Hz valid band), NOT "did
   it overfit?". The unknown-forcing/marginalization work must be designed for the regime where the QOI
   lives, not assumed to carry from the modal band.
7. **The orchestrator is now the weak link, not the worker.** The runner executed well; every real failure
   (hollow setup, the truth leak) was in the LEAD's framing. As workers get more capable, risk moves up to
   problem-design — spend disproportionate effort there and treat orchestration mistakes as first-class.

## 13. Immediate next actions
1. **Get real (or realistic-validated) inputs.** (a) Plan/begin the McCallie subscale tray test; and/or
   (b) pick ONE real public apparent-mass / FRF record to run the pipeline against; and (c) raise FEM
   fidelity to a VALIDATED level (benchmarks + real modal data).
   - **(2026-06-19, from §7.1) Design OUR OWN stand for MAXIMALLY-INFORMATIVE testing** (we cannot add data to the
     ShockSat set — not ours): multi-hit / multi-reference / roving excitation, QOI-OSP sensor placement at the
     high-participation/high-discrepancy locations, coupled+uncoupled apparent-mass configs — targeted at the
     amplitude/shape/damping limits §7.1 exposed.
1b. **(NEW, 2026-06-19) Feature-space discrepancy experiment** — report "peak at f0 ± X%, amplitude Y ± Z dB per
   mode" instead of a per-frequency |H| band; quantify how close a USABLE (+3/+6 dB) band is and how much of the gap
   is the model vs the single-hit data. We have the modal machinery; this is a near-term, bounded run.
1c. **(NEW strategic, 2026-06-19) Agentic FEM correlation** — an agent that diagnoses the wrong FEM regions from
   held-out residuals and re-meshes / re-parameterizes them (Card D `shocksat_fem_remesh_20260618` is step one). An
   unexplored automation domain + Bilionis-aligned; complements (does not replace) the orthogonal F(k) discrepancy.
   Honest gate: lit/FTO scan before any novelty claim; held-out coverage still decides; "already-correlated FEM still
   needs refinement" is itself a finding to confront.
2. **The decisive method A/B (cheap, can start on the existing model as a method check):** orthogonal
   output-space `F(k)` vs the same-parameter-space version, gated on **held-out netCG coverage**. This is
   the thesis + patent non-obviousness evidence once run on trusted inputs.
3. Send the Beth email; get the ownership determination in writing.
4. Finalize the Bilionis proposal (Purdue-supported patent framing).
5. Write the dated invention-disclosure / conception record for the orthogonal `F(k)` discrepancy.
6. Run a real patent-database search (Google Patents / Lens.org) or route to an attorney.
