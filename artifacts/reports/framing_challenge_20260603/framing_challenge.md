# Framing Challenge — Sequential Vibe→Modal→Flight Experiment

**Author:** Framing Challenger (Opus 4.8), browsing ENABLED.
**Date:** 2026-06-03
**Role:** critique + propose only. I did **not** edit runner code, durable rules, or checkers.
**Scope reviewed:** `AGENTS.md`, `CLAUDE.md`; setup packet
`artifacts/reports/sequential_vibe_modal_flight_20260602/`; round-2 packets (Opus/Codex/Cursor);
round-1+2 reviews incl. `reader_web_verified_sources.md`; repo PDFs (statFEM, digital-twin-StatFEM,
autonomous engineering design). External sources fetched this session are in [sources.md](sources.md);
every external claim below carries a tag like `[YUNIS]` or `[HDBK7004]` resolved there.

**One-line verdict:** The runners executed the *current* question very well — clean NumPyro NUTS,
passing convergence on raw latents, a decision-relevant PSD-envelope answer, honest resolution and
runtime accounting. **But the current question is mostly a harness/plumbing test wearing a
structural-dynamics costume.** Because the synthetic data come from the *same* parametric forward model
used for inference, tight recovery is near-guaranteed and proves self-consistency, not engineering
value. The reviewers already said this in a "standing caveat"; I am saying it should be the *headline*,
and I propose a backlog that turns this stack into something a real qual/test/loads team would act on.

---

## 1. What decision is this experiment actually serving?

### 1.1 The implied decision and QOI (as built)
From the Opus round-2 packet §0 and the task card, the **stated decision** is:

> *Does the existing random-vibration TEST SPEC (smoothline) envelope the in-flight coupled
> interface-acceleration environment, across frequency and across flights?*

- **QOI(primary):** per-flight coupled **interface acceleration response PSD** vs spec (the
  GEVS-style envelope check) `[GEVS]`.
- **QOI(summary):** tray **3·GRMS** (= 3σ ≈ 99.73% of a zero-mean Gaussian response `[IRVINE]`),
  explicitly labeled "summary only."
- **Inferred:** k1,k2,ζ1,ζ2; sensor-noise scale; build-to-build scales; non-centered per-build effects.
- **Fixed/not learned:** masses, flight-to-flight forcing (3 dB Matérn-3/2 GP, ℓ=0.08), −6 dB flight
  forcing offset, the spec, g0, **and model discrepancy (= 0 by construction).**

That is a coherent, well-posed *Bayesian-updating-on-a-2DOF* problem. The runners nailed it.

### 1.2 Why the current framing is (mostly) the WRONG question

**(a) Same-model data ⇒ this is a harness test, not an engineering result. Say it plainly.**
The truth is drawn from the identical coupled-2DOF forward model used in the likelihood (Opus §0:
*"truth is inside the model family by construction"*; the round-2 technical review's standing caveat
says the same). When the data-generating process equals the inference model, posterior contraction and
envelope agreement are **guaranteed up to noise** — they test code paths, gradients, the sampler, and
plotting, not whether the *engineering* model is right. A real qual decision is dominated by the things
this setup assumes away: **model-form error, joint/preload nonlinearity, fixture/boundary effects,
impedance mismatch between shaker and flight mount, and sparse non-stationary flight data.** So the
current artifact is a **plumbing certification**. That is *valuable* (the harness is the real product of
this phase), but it should be branded as such. Calling tight recovery a "structural-dynamics result"
overstates it.

**(b) Tray 3·GRMS is a proxy that hides what engineers actually act on.**
No qualification engineer signs a unit off on a single 3·GRMS number. The decisions that cost money and
risk are: **overtest vs undertest** (run the part too hard and you induce failures that never occur in
flight; too soft and you miss a flight failure) `[HDBK7004]`; **narrow-band exceedance** at a resonance
(which the scalar GRMS hides — Opus's flight-3 1.2%-of-frequencies exceedance is exactly this);
**fatigue/damage accumulation** over the test duration vs the flight duration (Miner's-rule / GRMS·√time);
and ultimately **pass/fail + margin**. The PSD-envelope QOI is the right *direction* and the best thing
in the packet, but the experiment stops at "does the band poke above the line" and never reaches the
decision: *what do we change — the spec, the test level, a notch, an extra test — and what does it cost?*

**(c) The vibe→modal→coupled→flight "data economy" is plausible; the sequential-update story is not
where the value is.** Opus's own §1 buries the punchline: *"the structural QOI posterior is essentially
stable across cumulative flights (the weak flight scalars add little structural information beyond the
rich build-0 data)."* In plain English: **the sequential flight updates barely move the posterior.** The
rich build-0 vibe+modal curves dominate; 11 scalar flight 3·GRMS values are nearly uninformative about
structure. So the marquee "sequential assimilation" GIF is showing a process that, by the runners' own
numbers, **doesn't change the decision.** The real value is the *opposite* question: **which test is
worth running, and when do we STOP testing?** That is a value-of-information / experimental-design
question, and the current setup doesn't pose it.

**(d) Which fixed assumption, if wrong, flips the decision?**
- **3 dB flight-to-flight (fixed, not learned).** *Defensible* — this is the single best-supported
  number in the whole setup. NASA's Yunis analysis of Shuttle + ELV flight data concludes **"3 dB is a
  conservative and reasonable standard deviation for the source environment and the payload
  environment"** `[YUNIS]`. Keep it — but note that fixing it *and* generating data with it is partly
  why recovery is easy.
- **−6 dB flight mean offset.** *Convenient, not standard.* The verified-sources file already caught
  this: GEVS's qualification margin is **+3 dB** (qual = acceptance/MPE + 3 dB), and the "+6 dB" that
  appears in GEVS tables is a **spectral slope (dB/oct), not a margin** `[GEVS]`. The −6 dB here is a
  bare project assumption. **If it's wrong, the envelope verdict flips directly** — the entire
  spec-envelopes-flight conclusion rides on where the flight mean sits relative to the spec, and −6 dB
  is chosen, not derived. This is the highest-leverage convenient assumption in the build.
- **Matérn-3/2, ℓ=0.08 in log-frequency (fixed).** *Convenient.* The correlation length sets how
  "wiggly" flight forcing is, which controls how often a narrow-band peak pierces the spec. Fixing it
  (rather than learning it from flight data) pre-decides the narrow-band-exceedance answer — the very
  thing the headline figure reports. A wrong ℓ changes the 1.2% exceedance number materially.

**Bottom line for §1:** the experiment answers *"can our pipeline recover parameters and draw an
envelope when we already know the answer?"* (yes). The decision a real team needs is *"given sparse,
model-discrepant, non-stationary flight data, what is the MPE for the next flight/build, is our test
over- or under-conservative, and which test should we run next?"* The current framing doesn't touch
overtest cost, model-form error, or stopping rules — the three things that move money.

---

## 2. First-principles + literature gaps (highest-leverage missing ingredients)

Ranked by how much they separate "plumbing" from "engineering value":

1. **No model discrepancy (the #1 gap).** Real StatFEM exists *because* the FE model is wrong: the whole
   point of the statistical-FEM construction is a Gaussian-process **model-misspecification / discrepancy
   term** `d(x)` between FE prediction and reality (Girolami et al., the repo `statFEM.pdf`; KOH-style
   calibration). This setup sets discrepancy ≡ 0. **Every interesting failure mode of Bayesian
   calibration — discrepancy soaking up parameter error, non-identifiability between θ and d,
   overconfident posteriors — is switched off.** A pipeline that has never seen model-form error cannot
   be trusted to *notice* it. This is the single highest-leverage addition.

2. **No decision/cost layer.** There is no loss function, no dollars, no overtest/undertest asymmetry, no
   "should we run another test" computation. Qualification is fundamentally a **risk vs cost** decision:
   overtesting "may cause failures that would not occur in flight" with a real schedule/$ "penalty"
   `[HDBK7004]`; undertesting risks an escape. Without a loss, the Bayesian posterior is decoration.

3. **Data realities are sanitized.** Flight environments are **sparse** (often <5 measurements `[YUNIS]`),
   **non-stationary** (the level changes through ascent — liftoff acoustics vs transonic vs max-Q), and
   the extrema are **non-Gaussian** (3·GRMS is a Gaussian 3σ convention; real peaks exceed it `[IRVINE]`).
   The setup uses 11 clean flights from a stationary GP with Gaussian noise. The sparse-data regime is
   exactly where Bayesian methods *should* beat the classical **P95/50 normal-tolerance-limit** MPE
   recipe `[YUNIS]` — and the experiment skips it.

4. **The forcing is the QOI but is held fixed.** The flight forcing PSD (mean −6 dB, 3 dB scatter, ℓ=0.08)
   is fixed and *generates* the data, then the pipeline mostly infers structure. But for an MPE decision
   the **forcing/environment is the thing you want to learn** from flights, not the structure. The
   experiment infers the well-constrained thing (structure, from rich curves) and fixes the
   decision-relevant thing (environment). That is backwards relative to the real decision.

5. **No aleatory/epistemic separation in the QOI.** Build-to-build (aleatory, irreducible by more data)
   and parameter uncertainty (epistemic, reducible) are both modeled but the QOI doesn't *report the
   split.* For a fleet decision you must know which uncertainty more testing can shrink (epistemic) vs
   which it can't (aleatory build variability) — otherwise you test forever chasing irreducible scatter.

6. **Higher-fidelity / nonlinear physics absent.** 2DOF linear is fine as a unit test. But the
   decision-flipping physics in vibe qual is **nonlinear**: amplitude-dependent damping, joint
   gapping/preload, and the **impedance mismatch** that drives overtest at resonance `[HDBK7004]`. None
   of these can appear in a linear 2DOF, so the experiment structurally cannot study the dominant
   real-world overtest mechanism.

**Highest-leverage single addition:** inject a **real model-form discrepancy** into the data generator
that is *not* in the inference model, then see whether the pipeline (a) notices (posterior predictive
check / discrepancy term lights up) or (b) silently absorbs it into biased θ with tight, wrong
intervals. That one change converts the harness test into a genuine StatFEM science result.

---

## 3. New experimental questions — ranked backlog

Ranked by **impact × feasibility on this stack** (Python/NumPyro NUTS, days not months). 🚀 = ambitious
moonshot. ⭐ = do next.

| # | Idea | Impact | Feasibility | Tag |
|---|---|---|---|---|
| 1 | Discrepancy-injection "does the pipeline know it's wrong?" | Very high | High | ⭐🚀 |
| 2 | Decision/cost layer: "should we run this test?" with $ | Very high | High | ⭐🚀 |
| 3 | Learn next-flight MPE from a handful of flights; quantify overtest | Very high | High | ⭐ |
| 4 | Force-limited-vibration notch decision under uncertainty | High | Medium | 🚀 |
| 5 | Whole-PSD vs peak/feature likelihood, decision consequences | High | High | |
| 6 | Aleatory vs epistemic split reported in the QOI | High | High | |
| 7 | Learn the forcing/environment (not just structure) | High | Medium | |
| 8 | BOED autonomous test-campaign agent (which test next) | High | Medium | 🚀 |
| 9 | Fleet/build-line transfer learning (hierarchical across units) | High | Medium | |
| 10 | Fatigue/damage QOI instead of single 3·GRMS | Medium-High | Medium | |
| 11 | Non-stationary, sparse, non-Gaussian flight data | Medium-High | Medium | |
| 12 | Swap toy for a real vibrationdata/NASA-NTRS dataset | High | Medium-Low | 🚀 |
| 13 | Prior-sensitivity / robustness of the envelope verdict | Medium | High | |
| 14 | Identifiability stress test (confounded θ vs discrepancy) | Medium-High | High | |

Details for each:

### ⭐🚀 1. "Does the pipeline know it's wrong?" — inject real model-form error
- **Question / decision:** if reality is NOT a clean 2DOF (extra mode, nonlinear softening, joint gap,
  fixture resonance), does our Bayesian update *detect* the misfit, or report tight, confident, wrong
  margins? **Decision served:** whether to *trust* any StatFEM/digital-twin calibration before betting a
  qual sign-off on it. **Whose:** the loads/calibration lead and the chief engineer who signs the risk.
- **Setup change:** generate data from a **3DOF or mildly nonlinear** truth (amplitude-dependent ζ, or a
  Duffing softening term), keep the inference model 2DOF-linear, **add a StatFEM GP discrepancy term**
  `d(ω)` and a posterior-predictive p-value / discrepancy-energy diagnostic.
- **Reasonable assumptions:** discrepancy magnitude calibrated to a believable 1–3 dB local FRF error;
  GP discrepancy with a frequency length-scale; everything else as-is.
- **Expected impact / why it beats current:** this is the *first* result with actual engineering content
  — it tells you when the method fails silently. Directly exercises the repo's own StatFEM literature.
- **Feasibility:** High. NumPyro can add a low-rank GP discrepancy in log-FRF; truth generator is a
  ~20-line change. Days.

### ⭐🚀 2. Decision-theoretic "should we run this test?" with dollars
- **Question / decision:** given the current posterior, is the **expected value of information** of the
  next test (another vibe run / a modal survey / a flight) greater than its **cost**? **Decision:**
  literally whether to spend $X on a test, or stop. **Whose:** program/test manager owning schedule and
  budget; this is where the money is.
- **Setup change:** add a loss with explicit asymmetry — **C_overtest** (induced-failure + schedule hit
  `[HDBK7004]`), **C_undertest/escape** (flight-failure risk × consequence), **C_test** (per test).
  Compute pre-posterior expected loss with and without each candidate test → a STOP/GO recommendation.
- **Reasonable assumptions:** order-of-magnitude costs ($50k test, $5M escape, week of schedule) stated
  as inputs and swept; risk-neutral expected loss baseline + a risk-averse variant.
- **Impact / why better:** converts a posterior into an action with a number attached. This is the thing
  a real PM would change a decision over. It also exposes that the sequential flight updates (§1c) have
  *low* VoI — quantifying the runners' qualitative finding.
- **Feasibility:** High. It's a post-processing layer on existing posterior samples + a sweep. Days.

### ⭐ 3. Learn the next-flight MPE from a handful of flights; quantify overtest risk
- **Question / decision:** from N=3–6 flights, predict the **MPE (P95/50) and Extreme (P99/90)** PSD for
  the *next* flight/build, and compare to the classical normal-tolerance-limit recipe `[YUNIS]`. Is our
  current spec over- or under-conservative, and by how many dB? **Decision:** set/relax the next build's
  test level. **Whose:** environments/loads engineer who owns the spec.
- **Setup change:** make the **forcing/environment the inference target**; produce a posterior-predictive
  P95/50 and P99/90 PSD; overlay the Bayesian MPE vs the frequentist k-factor MPE (Eq. 5 in `[YUNIS]`);
  report dB of margin between spec and predicted MPE per frequency band.
- **Reasonable assumptions:** 3 dB scatter `[YUNIS]`; small-sample k-factor for the classical
  comparison; flights as draws from the hierarchical environment.
- **Impact:** this is the **actual MPE problem the standards solve** — and the Bayesian version should
  give *honest wider* intervals at N=4 than the classical normal-tolerance-limit, which is the selling
  point. Beats current because it targets the decision-relevant quantity (environment) from sparse data.
- **Feasibility:** High. Reuses the GP forcing model; add the predictive + the classical comparison.

### 🚀 4. Force-limited-vibration notch decision under uncertainty
- **Question / decision:** given posterior uncertainty in the coupled impedance, **where and how deep
  should the force-limit notch be** to avoid resonance overtest without undertesting? **Decision:** the
  notch spec for the shaker controller — a routine, high-stakes test-floor decision `[HDBK7004]`.
- **Setup change:** add the **semi-empirical force limit** (e.g. simple/complex two-DOF (TDOF) force
  spec) and propagate posterior impedance uncertainty into the predicted interface force → a notched
  acceleration input with credible bounds; report overtest-margin reduction.
- **Reasonable assumptions:** the published TDOF force-limit form `[HDBK7004]`; impedance from the
  coupled 2DOF posterior. State that 2DOF can't capture nonlinear notch depth — bound the error.
- **Impact:** the *named, dominant* overtest mechanism in real qual is impedance mismatch at resonance
  `[HDBK7004]`; a Bayesian notch with uncertainty bands is genuinely novel and useful.
- **Feasibility:** Medium — needs the force-limit equations and a careful quantity contract for force.

### 5. Whole-PSD vs peak/feature likelihood — decision consequences (the setup's OWN open question)
- **Question / decision:** the task card explicitly asks "how different are posteriors from full PSD vs
  peak-frequency/peak-amplitude likelihoods?" Run it head-to-head and report the **QOI/decision** delta,
  not just posterior widths. **Decision:** how much instrumentation/processing to buy (full FRF vs a few
  extracted features). **Whose:** test engineer deciding measurement fidelity.
- **Setup change:** two likelihoods on the same data; compare interval-width ratios AND the
  envelope/overtest verdict; include a feature-sensitivity map (CLAUDE.md's peak≠fn warning).
- **Impact:** answers a question already in the task card that NO runner actually executed. High, cheap.
- **Feasibility:** High.

### 6. Aleatory vs epistemic split, reported in the QOI
- **Question/decision:** of the QOI uncertainty, how much is **build-to-build aleatory** (more tests
  won't shrink it) vs **epistemic** (tests will)? **Decision:** stop-testing rule + how much margin must
  be carried for irreducible scatter. **Whose:** reliability + program.
- **Setup change:** decompose predictive variance; plot the two contributions vs #flights.
- **Impact:** prevents the classic error of testing forever to chase irreducible variability. High value,
  near-free given the hierarchical model already exists.
- **Feasibility:** High.

### 7. Learn the forcing/environment, not just the structure
- See §2.4. Flip inference targets so flights inform the environment posterior. Medium feasibility
  (identifiability between forcing and structure must be handled — pair with #14).

### 🚀 8. BOED autonomous test-campaign agent
- **Question/decision:** let an agent **choose the next experiment** (which test, which level, which DOF
  to instrument) to maximize expected information about the decision QOI, sequentially. **Decision:** the
  whole test campaign plan. **Whose:** test/program management. Directly realizes the repo's
  `autonomous engineering design.pdf` ambition and CLAUDE.md's BOED gate.
- **Setup change:** EIG/expected-loss-reduction over a candidate test menu; greedy sequential selection;
  compare agent-chosen campaign vs the fixed vibe→modal→flight order.
- **Reasonable assumptions:** small discrete design space (5–8 candidate tests) to keep EIG tractable.
- **Impact:** the marquee "autonomous experiment" story, grounded in a real decision. Beats the current
  *fixed-order* sequential story, which the runners showed is low-VoI.
- **Feasibility:** Medium — nested MC EIG is doable on a small design space; flag runtime.

### 9. Fleet/build-line transfer learning
- **Question/decision:** does a hierarchical model across many units let a **new build** inherit a tighter
  prior (partial pooling), reducing the tests it needs? **Decision:** per-unit test reduction across a
  production line. **Whose:** production + qual. Setup: add a unit-level hierarchy; show shrinkage and
  test-count reduction vs no-pooling. Impact high (qualification-by-similarity is a real practice).
  Feasibility Medium.

### 10. Fatigue/damage QOI
- Replace the single-instant 3·GRMS with **accumulated damage** (Miner's rule, GRMS·√(test duration))
  and ask: does the test *duration* over- or under-accumulate damage vs flight? **Decision:** test
  duration/level trade. Medium-High impact (life is often the binding constraint), Medium feasibility.

### 11. Non-stationary, sparse, non-Gaussian flight data
- Generate ascent-segmented, heavy-tailed, N<5 flight data; test whether the method degrades gracefully.
  Realism upgrade that supports #3. Medium feasibility.

### 🚀 12. Swap the toy for a real dataset
- Use a **real** vibrationdata/NASA-NTRS flight or shaker PSD record (Irvine's tutorials host real PSDs;
  NTRS hosts flight environment data). Even calibrating the 2DOF to one real interface PSD would expose
  model-form error for free. **Impact high** (kills the same-model critique outright); feasibility
  Medium-Low (data wrangling, units, provenance). The honest first step toward real-world value.

### 13. Prior-sensitivity / robustness of the envelope verdict
- Sweep the −6 dB offset and ℓ=0.08 (the two convenient assumptions, §1d) and report when the
  spec-envelopes-flight verdict flips. Cheap, high-honesty. Feasibility High. (Arguably belongs in the
  current packet already — see Kill List.)

### 14. Identifiability stress test
- Deliberately confound a structural parameter with the discrepancy/forcing and show the posterior
  cannot separate them (and that the marginal QOI may still be fine). Teaches the method's limits.
  Feasibility High; pairs with #1 and #7.

**Do-next picks (impact × feasibility):** **#1 (discrepancy injection), #2 (decision/cost layer),
#3 (sparse-data MPE).** Rationale: #1 converts the harness test into real StatFEM science; #2 attaches
a dollar decision to the posterior (the thing a PM acts on); #3 solves the actual MPE problem the
standards solve and plays to the Bayesian sparse-data strength `[YUNIS]`. All three are days-not-months
on NumPyro and reuse the existing forward model and posterior plumbing. #5 and #13 are near-free honesty
upgrades that should ride along.

---

## 4. Kill list — stop doing these as framed

1. **Stop presenting same-model parameter recovery as a structural-dynamics *result*.** It is a
   **plumbing/regression test**. Keep running it as a CI sanity check, but rebrand it honestly; do not
   let "tight posterior" read as "calibrated to reality." (The reviewers' standing caveat should be the
   headline, not a footnote.)
2. **Stop leading with the sequential-assimilation GIF as the value story.** By the runners' own numbers
   the flight scalars barely move the structural posterior (Opus §1). It is a beautiful figure of a
   low-information process. Demote it; lead with a decision (envelope margin in dB, or VoI) instead.
3. **Stop treating tray 3·GRMS as a near-headline QOI.** It is a summary that hides the narrow-band
   exceedance the PSD-envelope already catches. Keep it as one labeled summary line; don't build figures
   around it as if it were the decision.
4. **Stop shipping the −6 dB offset and ℓ=0.08 as unexamined fixed inputs.** Either learn them or run the
   sensitivity sweep (#13). As-is, the two assumptions that most directly set the envelope verdict are
   chosen, not justified — that's a credibility hole `[GEVS]`.
5. **Stop the cross-runner band-definition ambiguity from reaching a "customer" number.** Codex (99% fully
   enveloped) vs Opus (1.2% exceedance) disagree purely on band definition (q99.5 vs 99%-hi). Don't quote
   an envelope verdict until the band is standardized — the technical review flagged this and it's a
   genuine "wrong number to a customer" risk.
6. **Don't expand the 2DOF-linear toy for its own sake.** More flights/builds of the *same* model add no
   engineering information (diminishing, near-zero VoI). Spend effort on discrepancy/decision/real-data,
   not on a bigger clean toy.

---

## 5. Sources

External claims are tagged inline and resolved in [sources.md](sources.md) with URL, HTTP status, and a
content hash fetched THIS session. Quick map:

- `[YUNIS]` — Isam Yunis (NASA KSC), *The Standard Deviation of Launch Vehicle Environments*, NTRS
  20120001364. Confirms **3 dB** flight-to-flight σ as conservative/reasonable from Shuttle+ELV data;
  defines **P95/50 (MPE)** and **P99/90 (Extreme)**; gives the small-sample normal-tolerance-limit
  k-factor; notes data are often "<5" measurements.
- `[HDBK7004]` — NASA-HDBK-7004B, *Force Limited Vibration Testing* (vibrationdata mirror). Confirms
  overtest is caused by **infinite shaker impedance + acceleration control at resonance**; force
  **notching** reduces it; overtest "may cause failures that would not occur in flight" with a real
  penalty; goal is flight-like test with a **specified positive margin**.
- `[GEVS]` — GSFC-STD-7000 (GEVS). Spec must **envelope** the flight environment; **Limit Level = MPE**;
  qual margin **= +3 dB** (NOT +6 dB; the +6 dB in tables is a spectral *slope*); scalar GRMS is a
  summary. (Verified in `runner_comparison_20260602/reader_web_verified_sources.md` §C, re-used here.)
- `[IRVINE]` — Irvine/vibrationdata random-vibration tutorial. GRMS = √(area under PSD); **3·GRMS = 3σ ≈
  99.73%**, an estimate not a hard max (peaks exceed it).
- StatFEM model-discrepancy basis — repo `statFEM.pdf` (Girolami et al.) and the digital-twin-StatFEM
  PDF: the statistical-FEM construction centers on a GP **discrepancy/misspecification** term — the
  ingredient this experiment sets to zero.

### Remaining [SPECULATIVE] items (my hypotheses, not yet source-verified)
- **[SPECULATIVE]** Specific dollar magnitudes for overtest vs escape (used illustratively in #2) — order
  of magnitude only; a real program would supply these.
- **[SPECULATIVE]** That a Bayesian sparse-data MPE gives *honestly wider* intervals than the classical
  k-factor at N=4 — strongly expected from first principles but must be demonstrated (that's the point of
  experiment #3), not asserted.
- **[SPECULATIVE]** That the existing pipeline would *silently absorb* injected model-form error into
  biased θ — this is the hypothesis experiment #1 is designed to test; could go either way.
- **[SPECULATIVE]** Quantitative VoI of each candidate test (#8) — I infer it's low for the flight
  scalars from the runners' "posterior stable across flights" remark, but it has not been computed.
