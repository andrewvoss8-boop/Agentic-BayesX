# Round-1 Reader / Literature Review — 2026-06-02

Role: READER subagent (Opus 4.8). Scope: gather repo + paper evidence for the human's round-1
concerns in [human_feedback.md](human_feedback.md). I do not edit runner code.

## Session constraint (read this first)

`WebSearch` / `WebFetch` are **not enabled in this session**. I could not fetch or verify external
primary standards (NASA GEVS / GSFC-STD-7000, MIL-STD-810, NASA-HDBK-7004C, vibrationdata.com /
Tom Irvine tutorials, the Stan reference manual, Hoffman & Gelman 2014, Vehtari et al. 2021).

Per the "do not cite from memory" rule, I therefore split evidence into two tiers:

- **VERIFIED-IN-REPO** — quoted from files in this repo (the three PDFs, the `references/` notes,
  the setup packet, the runner packets). These are the load-bearing citations below.
- **TO-VERIFY (external)** — widely-used conventions I am *flagging*, not asserting as confirmed.
  Each is marked `[TO-VERIFY]` with the exact claim a human or a web-enabled reader must confirm
  before it goes into a checker or task card.

This is itself a round-1 finding: **the headline numeric thresholds the human cares about
(qualification margin in dB, points-per-half-power-band, R-hat/ESS gates) are NOT currently backed
by any primary standard inside this repo.** The `references/` notes are secondary "trace" notes, not
the standards themselves.

---

## A. Sources (every source: what it supports / what it does NOT)

### A1. statFEM.pdf — Girolami, Febrianto, Yin, Cirak, *CMAME* 375 (2021) 113533 (VERIFIED-IN-REPO)
- **Supports:** the StatFEM hierarchical Bayesian structure — observation = scaled FEM mean +
  GP model-discrepancy `d` + iid noise `e`; three-level inference (states → hyperparameters →
  model selection via Bayes factors). Confirms whole-data Bayesian updating as the framing.
- **Sampler evidence (key):** the paper samples the posterior with **random-walk Metropolis MCMC**.
  Quoted: *"the posterior of the statistical generating model parameters … by sampling with the MCMC
  Metropolis algorithm … the logarithm of the posterior is considered … the proposal density we
  choose a normal distribution q(w|v) = N(v, σ²_q I)."* It also names **Metropolis-within-Gibbs** as
  an alternative. So **the source paper does NOT use NUTS/HMC.** The project's NUTS/HMC rule is a
  deliberate *upgrade beyond* the cited literature, which supports labeling existing
  Metropolis/random-scan work as prototype/legacy.
- **Kernel evidence (key for the Matérn requirement):** the discrepancy GP uses a **squared-
  exponential (RBF) kernel**, and the authors explicitly state *"the specific form of the kernel
  cκ(x,x′) is inconsequential for the presented approach."* So the task card's "Matérn, NOT RBF"
  instruction is a project modeling choice, not something this paper mandates or forbids; the paper
  supports kernel choice as a flexible modeling decision.
- **Does NOT support:** anything about random-vibration qualification, PSD/GRMS, 3-sigma test specs,
  dB margins, frequency-grid resolution, or convergence thresholds (no R-hat/ESS discussion). Static
  Poisson/beam elasticity examples, not frequency-domain structural dynamics.

### A2. digital-twinning … statistical finite element method.pdf — Febrianto, Butler, Girolami, Cirak (2022) (VERIFIED-IN-REPO)
- **Supports:** StatFEM on a real self-sensing structure (instrumented bridge). Strong evidence for
  the **whole-data vs per-observation likelihood** question the harness gates care about: quoted
  *"it is possible to consider each time instant t_k independently … This can be very costly … More
  critically, the information content available in one single observation vector y often gives only
  a very poor estimate … Consequently, it is advantageous to consider all observation vectors
  simultaneously."* → literature backing that **whole-data likelihoods beat sparse feature/single-
  observation likelihoods** for identifiability, consistent with the runners' full-FRF-beats-peak
  finding.
- **Sampler evidence:** again **MCMC** (empirical mean of samples as point estimate); **no NUTS/HMC.**
- **Does NOT support:** random-vibration specs, GRMS, dB margin, frequency-grid resolution,
  convergence thresholds.

### A3. autonomous engineering design.pdf — Kumar & Karniadakis, Brown (multi-agent design framework) (VERIFIED-IN-REPO)
- **Supports:** the *agentic/harness* layer only — structured iterative design + review loops across
  multiple agents. Relevant to the round-1 harness proposals (reviewer/checker roles, review gates),
  NOT to the physics.
- **Does NOT support:** any sampler claim, PSD/GRMS, frequency resolution, or Bayesian convergence.
  It contains **no MCMC / HMC / NUTS content at all** (term search: 0 hits). It should **not** be
  cited for concerns #1, #2, or #3. The task prompt listed it as a candidate source; my finding is
  it is **not applicable** to any of the three numeric concerns.

### A4. references/nasa-7004c-notes.md (VERIFIED-IN-REPO, secondary trace note)
- **Supports:** apparent-mass / FRF convention discipline (source vs load apparent mass, drive-point
  reciprocal inertance) and pointers to NASA-HDBK-7004C (force-limited vibration testing) and a
  model-credibility standard. Useful for the Quantity-Contract gate.
- **Does NOT support:** GRMS computation, the 3-sigma/qualification-margin comparison, or frequency
  resolution. It is a *trace note*, not the standard; and it carries a possible **standard-number
  ambiguity** (it labels NASA-STD-7004C as "model credibility," but model-credibility discipline is
  usually NASA-STD-7009; force-limited vibration is NASA-HDBK-7004). `[TO-VERIFY]` the exact numbers.

### A5. references/vibrationdata-notes.md (VERIFIED-IN-REPO, secondary trace note)
- **Supports:** intent to sanity-check resonant behavior, apparent-mass shape, coupled-vs-standalone
  trends against classical 2DOF/MDOF results (Tom Irvine / vibrationdata.com).
- **Does NOT support:** any specific GRMS, dB-margin, or points-per-half-power-band number. No
  quantitative rule is captured in-repo.

### A6. references/aerospace-vibration-data-candidates.md (VERIFIED-IN-REPO)
- **Supports:** that vibrationdata.com (Tom Irvine) and NASA NTRS are the project's intended sources
  for real aerospace vibration data (SR-19 forward-dome ignition, Pegasus drop transient, F-16 GVT).
  Confirms vibrationdata.com is a *recognized* project reference for the dome/flight flavor.
- **Does NOT support:** the specific qualification-margin or frequency-resolution rules; it is a
  dataset shortlist, not a methods standard.

### A7. Setup packet `artifacts/reports/sequential_vibe_modal_flight_20260602/` (VERIFIED-IN-REPO)
- **Supports:** the conventions all runners inherited — PSD-space dB `factor = 10**(dB/10)`; smoothline
  points `[(20,0.01),(100,0.1),(750,0.1),(2000,0.001)]` g²/Hz; flight mean offset −6 dB; flight-to-
  flight 3 dB fixed; build 1.5 dB / sensor 0.75 dB to be learned; Matérn-3/2 forcing GP, ell=0.08 in
  log-frequency; tray `3*GRMS` defined as *"three times root integral of tray acceleration PSD."*
  The setup grid is **260 log-spaced points over 20–2000 Hz** (≈58 pts/decade) for PSD and a separate
  dense modal grid.
- **Does NOT support:** any vibe-vs-flight RMS *comparison* convention, nor any peak-resolution rule.
  The setup defines GRMS but never states how flight 3*GRMS should be compared to the vibe-test
  3*GRMS — which is exactly the gap the human flagged (item C).

### A8. Runner packets (VERIFIED-IN-REPO) — concrete numbers for the implications below
- Opus `nuts_diagnostics.md`: real **NUTS** (NumPyro), 4 chains, R-hat ≤ 1.0024, min ESS 942,
  0 divergences; kept the **full 260-pt PSD / 180-pt modal** grid; **no frequency-grid sensitivity**
  and no points-per-half-power-band rationale.
- Codex `nuts_diagnostics.md`: **NUTS active: false; custom PyTorch fixed-trajectory HMC**; R-hat up
  to **2.67 (full)** and **4.57 (peak)**, ESS as low as **~6**, 3 divergences; grid **56 PSD / 48
  modal points** (coarsest → matches the human's clipped-tray-peak observation).
- Cursor (per comparison matrix): real **NUTS**, **2 chains**, R-hat up to **1.83**, ESS ≈ 3;
  **stride-4** subsample of the 260-pt grid (~65 pts).

---

## B. Concern #1 — Vibe-test RMS vs flight 3*GRMS: what is the conventional comparison?

**What the repo verifiably supports:** GRMS is defined in the setup as `3 × sqrt(∫ PSD df)` over the
tray acceleration PSD (A7). The dB convention is power-space `10**(dB/10)` (A7). vibrationdata.com is
an accepted project reference for this class of problem (A5, A6). None of the three PDFs address
random-vibration qualification at all (A1–A3).

**What is NOT in the repo (the actual gap):** there is **no in-repo source** stating the standard
comparison between a qualification vibe-test level and a flight environment. The headline plot the
human wants (flight interface-accel PSD mean/95/99 **vs the original test spec**, and flight 3*GRMS
**vs the vibe-test 3*GRMS reference line**) has **no documented convention backing it in this repo.**

**`[TO-VERIFY]` external conventions to confirm before they enter a checker/task card:**
- `[TO-VERIFY]` **GRMS = sqrt(area under the acceleration PSD)**; for a zero-mean Gaussian random
  response, 1σ = GRMS and **3σ ≈ 99.73%** peak coverage → "3*GRMS" is the conventional 3-sigma peak
  estimate. (Standard random-vibration result; confirm against Irvine/vibrationdata or a textbook.)
- `[TO-VERIFY]` **Conventional comparison is in PSD/spectrum space, not just the scalar:** the
  qualification (vibe) **test spec PSD should envelope the flight Maximum Predicted Environment (MPE)
  PSD**, typically with a margin. The standard practice the human is gesturing at — overlaying each
  flight's interface PSD (with CI bands) against the original test spec, and checking the spec still
  envelopes flight — is, to my knowledge, **standard MPE-vs-qualification practice**, but I cannot
  cite a primary source this session. Confirm against **NASA GSFC-STD-7000 (GEVS)** and/or
  **NASA-STD-7001**.
- `[TO-VERIFY]` **Qualification margin:** GEVS-style practice typically sets qualification ≈ **MPE
  + 3 dB** (and protoflight/acceptance at lower margin), with **+6 dB** sometimes used for
  uncertainty/limited-data cases. The setup's **−6 dB flight mean offset** below the original forcing
  is consistent with "flight runs below the +margin test spec," but confirm the exact dB numbers and
  which standard.
- `[TO-VERIFY]` Whether overlaying a **flight 3*GRMS scalar against the vibe-test 3*GRMS scalar** is
  itself "standard practice." My read: the scalar overlay is a reasonable *summary*, but the
  **defensible** comparison is the **PSD-envelope** comparison (spec must envelope flight across
  frequency); a single GRMS number can hide a narrow-band exceedance. This nuance should be stated in
  the task card.

**Implication:** the human's requested overlay is well-motivated and consistent with standard MPE/
qualification thinking, but the repo must **acquire and cite a primary standard** (GEVS / NASA-STD-
7001 / Irvine) before a checker enforces any dB margin or "spec envelopes flight" rule. Until then,
treat the margin numbers (43.9 g / 28.3 g setup values, +6 dB) as **project assumptions, not
standards.**

---

## C. Concern #2 — Frequency-grid resolution so resonance peaks are not clipped

**What the repo verifiably supports (strong, concrete):** this problem is demonstrably grid-
sensitive. Setup grid = 260 log points, 20–2000 Hz. Near the tray/dome modes (~86 / ~93.5 Hz, per
Opus packet), log spacing gives Δf ≈ f·ln(2000/20)/260 ≈ **1.5 Hz/point at 86 Hz**. Codex's 56-point
grid gives Δf ≈ **7 Hz/point at 86 Hz**, which is **coarser than a lightly-damped half-power
bandwidth** → this is the mechanism behind the human's observation that Codex's tray peak was clipped
(A8). So the repo data themselves demonstrate the failure mode; no external source is needed to
establish that the problem class is grid-sensitive.

**What is NOT in the repo:** no runner documented a **points-per-half-power-band** target, and **none
ran a frequency-grid sensitivity study.** No in-repo source states the rule.

**`[TO-VERIFY]` external rule to confirm:**
- `[TO-VERIFY]` **Half-power (−3 dB) bandwidth** of a mode: `Δf_HP = f_n / Q = 2·ζ·f_n`. (Standard
  SDOF result; confirm against Irvine/vibrationdata or any vibration text.)
- `[TO-VERIFY]` **Resolution rule of thumb:** keep **≥ ~5 spectral lines within each mode's
  half-power bandwidth** to avoid clipping the peak / under-estimating GRMS (some practitioners cite
  a minimum of ~3, with 5–10 preferred). Equivalent random-vibration-test statement: analysis
  bandwidth `B` should satisfy `B ≤ Δf_HP/5` near resonance. **Confirm the exact number and source**
  (Irvine "Equivalent Static Loads / GRMS" tutorials, or shock & vibration handbook).
- Concrete consequence to flag (computed from repo data, not external): with ζ≈0.02, f_n≈86 Hz →
  Δf_HP≈3.4 Hz. The "≥5 lines" rule needs Δf ≤ ~0.7 Hz near the peak. **Even Opus's densest 260-pt
  grid (~1.5 Hz) gives only ~2 lines across the half-power band** — borderline; Codex (~7 Hz) gives
  **< 1 line** — clipped. So the rule, if adopted, would flag *all three* runs near resonance, with
  Codex worst. A **mode-local refinement** (extra points clustered around each f_n) is likely needed,
  not just more global points.

**Implication:** frequency-grid spacing must become a **first-class assumption AND a required
sensitivity item**, with a **peak-resolution check** (`≥ N lines within each mode's half-power band`)
once `N` is confirmed against a primary source. This directly supports harness proposal #5.

---

## D. Concern #3 — When NUTS/HMC is appropriate, and accepted convergence thresholds

**What the repo verifiably supports:** the project rule (CLAUDE.md / AGENTS.md) is **NUTS/HMC as the
default**, with Metropolis/random-scan labeled prototype/legacy. The two StatFEM PDFs both used
**random-walk Metropolis / Metropolis-within-Gibbs** (A1, A2) — i.e., the literature baseline is
exactly the "legacy" sampler, so the NUTS rule is a justified upgrade, not a contradiction of the
sources. Runner diagnostics (A8) give the concrete spread: Opus = real NUTS, converged (R-hat
≤ 1.0024, ESS ≥ 942, 0 div); Cursor = real NUTS but under-resourced (2 chains, R-hat 1.83, ESS≈3);
Codex = **not NUTS** (custom fixed-trajectory HMC), non-converged (R-hat up to 4.57, ESS≈6).

**When NUTS/HMC is appropriate (synthesis; mark `[TO-VERIFY]` for the precise wording/source):**
- `[TO-VERIFY]` NUTS/HMC is the right default for **continuous, differentiable** posteriors of
  moderate-to-high dimension with **correlated parameters** (exactly this hierarchical model: log
  stiffness/damping ratios, GP forcing latents, build/sensor scales) — gradient-based proposals
  mix far better than random-walk Metropolis here. Confirm against the **Stan reference manual** /
  Betancourt's HMC conceptual introduction.
- `[TO-VERIFY]` HMC/NUTS is **not** applicable to discrete parameters without marginalization, and
  can struggle with hierarchical "funnels" unless **non-centered parameterization** is used — a
  likely cause of Cursor's/Codex's poor latent mixing. Confirm against Stan docs.
- A **custom fixed-trajectory HMC (Codex) is not NUTS** and should not be reported as satisfying a
  "NUTS default" rule without an explicit labeled justification — which Codex did honestly state
  ("NUTS active: false").

**`[TO-VERIFY]` convergence thresholds to confirm before they become a checker gate:**
- `[TO-VERIFY]` **R-hat:** modern guidance (Vehtari et al. 2021, *rank-normalized split-R̂*) is
  **R-hat < 1.01** for all quantities; the older **< 1.05 / < 1.1** is weaker. Opus passes even the
  strict 1.01 bar; Cursor (1.83) and Codex (4.57) fail any bar.
- `[TO-VERIFY]` **ESS:** require **bulk-ESS and tail-ESS ≳ 100 per chain** (so ≥ 400 for 4 chains);
  some use ≥ 400 bulk total as the practical floor. Opus passes (≥ 942); Cursor (≈3) and Codex (≈6)
  fail badly.
- `[TO-VERIFY]` **Divergences:** target **0**; any nonzero divergence count is a warning that the
  posterior geometry isn't being explored faithfully (bias risk), not just inefficiency. Codex's 3
  divergences should fail/hard-warn, not pass silently.
- `[TO-VERIFY]` **Chains ≥ 4** to make split-R-hat meaningful (Cursor's 2 chains is below the usual
  recommendation).
- Important nuance for the gate: thresholds must be checked over **ALL sampled variables including
  raw hierarchical latents**, not just headline marginals — both Cursor and Codex "passed" because
  only summaries were inspected. This supports harness proposal #1.

**Implication:** a convergence gate is justified and the per-variable failure is already
demonstrated in-repo. The exact numeric thresholds (1.01 vs 1.05; ESS floor) must be pinned to a
primary source (Stan manual / Vehtari 2021) before they are hard-coded, but the *direction* is
unambiguous from the runner data.

---

## E. Implications for the next task card (short list)

1. **Acquire and cite primary standards before writing checkers.** The repo currently has **no
   primary source** for (a) qualification-vs-flight RMS comparison and dB margin, (b) points-per-
   half-power-band, or (c) R-hat/ESS thresholds. A web-enabled reader pass (or human upload) must add
   verified citations: **GEVS / GSFC-STD-7000 + NASA-STD-7001** (margin & spec-envelopes-flight),
   **Irvine/vibrationdata** (GRMS, half-power resolution), **Stan manual + Vehtari et al. 2021 +
   Hoffman & Gelman 2014** (NUTS, R-hat, ESS). Until cited, label all such numbers "project
   assumption," not "standard."
2. **Frequency grid → first-class assumption + required sensitivity + peak-resolution check.** State
   spacing (log/linear, pts/decade, **lines within each mode's half-power band**), and require a
   refined-grid re-run reporting QOI/posterior shift. The repo data show even the densest 260-pt grid
   is borderline near 86 Hz, so favor **mode-local refinement**, not just more global points.
3. **KEY deliverable must be named explicitly** and checker-verified: per-flight coupled interface-
   acceleration PSD with **mean/95/99 bands vs the original test spec** (frame sequence + GIF), the
   **10 flight forcing draws vs the +6 dB mean**, and the **flight 3*GRMS sequence overlaid on the
   vibe-test 3*GRMS reference line** — and state that the **PSD-envelope** comparison (spec envelopes
   flight across frequency) is the defensible check, with the scalar overlay as a summary only.
4. **Convergence gate over ALL variables (incl. raw latents):** fail/hard-warn on max R-hat ≥ (1.01
   pending source; 1.05 fallback), min ESS below floor, or any divergence; require **≥4 chains** and
   a **non-centered parameterization** note for the hierarchical latents.
5. **Sampler-identity honesty:** "NUTS default" means NUTS; a custom fixed-trajectory HMC or
   Metropolis must be **labeled with a reason** (Codex did this correctly; Cursor's `nuts_active:true`
   + checker pass despite non-convergence is the overclaim risk to close).
6. **Drop `autonomous engineering design.pdf` as a physics source** — it is relevant only to the
   agent/harness layer, not to concerns #1–#3.

---

## F. Honesty / limitations of this review
- Web access was unavailable; the `[TO-VERIFY]` items are flagged conventions, **not** verified
  citations. They must be confirmed by a web-enabled pass or human before entering any durable rule
  or checker.
- All quoted PDF text and all runner numbers above were read directly from repo files this session.
- I did not edit any runner code or any durable rule file. Findings are evidence for the next task
  card and for [harness_improvements_proposed.md](harness_improvements_proposed.md), pending human
  approval.
