# Notching / force- & response-limiting — findings for future agents

**Standing reference. Read this before doing any force-limiting, response-limiting,
notching, or interface-environment (apparent-mass) work in this project.**

Source of these findings: the verified analytical study in this workspace
(`artifacts/reports/notch_multipoint_7004c_20260611/`, EX-A…EX-E; `bash run_all.sh`
replays, `check.py` is green/yellow/red). Everything here is deterministic
small-matrix structural dynamics anchored to NASA-HDBK-7004C; **no measured data,
no sampler.** Treat numbers as mechanism-grade illustrations, not design values.
Where a claim is checker-backed it says so; where it is reasoning it says so.

Audience note (project convention): structural-dynamics terms used directly;
ML/stats terms defined on first use.

---

## 0. TL;DR for someone setting up notching

1. **Force limiting in 7004C is a scalar, single-interface, in-axis story.** Its
   semi-empirical limit S_FF = C²M₀²S_AA, the simple/complex TDOF charts, and the
   single-node impedance method all assume one interface DOF and "force = in-axis
   acceleration × apparent mass." (7004C p.31 says this explicitly.)
2. **Real hardware has multiple spaced feet and 6-DOF motion.** Then apparent mass
   is a 6×6 matrix, the single notch becomes a frequency-shifted *cluster* living
   in different interface combinations, and **rocking loads are invisible to the
   net in-axis force** the standard method limits (the "resultant trap").
3. **"How far from a foot can you see the notch" is a regime question, not a
   radius.** Low modal overlap in the backing → the notch is global; high overlap
   → it localizes to ≈ λ/4 around the feet.
4. **There IS an empirical path that avoids a coupled forced FEM** (EX-E): the
   impedance method with *measured* interface quantities reconstructs the coupled
   loads exactly. The cost is spatial: 1 foot gives bounce only; ≥3 spaced feet
   recover rocking/moment; a remote control accel works for response limiting only
   if its transmissibility is calibrated in the *integrated* configuration.
5. **A coarse/uncoupled model is still useful — as a prior and for
   extrapolation/residual mass — not as a forced coupled solve.** This is exactly
   where the project's Bayesian "robust apparent-mass twin" (notes §6.1) fits.

---

## 1. The 7004C toolbox in one page (with page anchors)

- **Overtest cause (p.8):** impedance mismatch — the shaker has ~infinite
  mechanical impedance, the flight mount is finite, so a hard-mounted test
  over-drives the interface at the test-item resonances. A SECOND cause (p.8) is
  the *uniformity* of motion the shaker imposes at all attachments vs the
  uncorrelated/differential motion in flight. **Remember the second cause — it is
  the whole multi-point story.**
- **Semi-empirical limit (p.29, Eq 1–2):** F = C·M₀·A (sine), S_FF = C²·M₀²·S_AA
  (random); roll off above a break frequency f_b with exponent n (usually 1). C
  effectively replaces the resonant amplification Q; it "clips" the reaction-force
  PSD at C² instead of Q². Empirical C² ranges (Table 1, Soucy): C²<2 covers 62%
  of *vertical* but only 18% of *lateral* cases — lateral needs bigger limits
  because of rocking/cross-axis. C²<5 covers 80% of all cases.
- **Simple TDOF (p.31, Fig 8, App. B Eq B1–B2):** source oscillator (mass m₁) +
  load oscillator (m₂); the normalized force limit at the lower coupled resonance
  vs the mass ratio m₂/m₁. As m₂/m₁→0, the limit → Q² (no load effect); the gap
  below Q² is the "knockdown."
- **Complex TDOF (p.32, App. C tables):** same idea with effective modal + residual
  masses instead of lumped masses (removes the simple-method ambiguity). Tables are
  image-only in our PDF — not transcribed.
- **Impedance method (p.33–34, Eq 3–4, Fig 9):** A = A_source_free·Ms/(Ms+Ml);
  F = A_source_free·Ms·Ml/(Ms+Ml). Ms, Ml = source/load apparent mass; needs the
  source *free* acceleration (NOT the spec envelope). This is the method the
  empirical path (EX-E) builds on.
- **Apparent/effective/residual/asymptotic mass (p.25–26, App. A):** apparent mass
  = F/a (FRF); effective modal mass decomposes it; the sum of effective masses per
  direction = total mass / moment of inertia (p.56). Rocking modes carry rotary
  effective inertia (kg·m²).
- **Multi-point practice (p.10, p.18, p.29):** "in most cases only the total
  in-axis force… needs to be measured and limited"; moments/per-foot "occasionally
  useful." At LOW freq / closely-spaced feet a tap at any foot gives the *total*
  interface apparent mass; at HIGH freq / widely-spaced feet it gives only a
  fraction. **This p.29 sentence is the empirical-path key.**
- **Response limiting / Sweitzer (p.24–25, App. D):** notch the input where a
  response FRF peaks; Fig 4 — a 14 dB notch only halves RMS, and no notch reduces
  RMS by >~factor 3; notching one response helps that point, not the whole article.

---

## 2. What changes with multiple spaced feet + 6-DOF (EX-A→EX-D, checker-backed)

- **Apparent mass → 6×6 matrix** (EX-B). The ω→0 limit equals the rigid-body mass
  matrix exactly (checked 5e-7); modes match closed form (2e-16); per-direction
  effective-mass sums equal the rigid totals (3e-16). Off-diagonals are CG-height /
  geometry coupling (lateral input → vertical foot forces + moment).
- **The resultant-force trap** (EX-B, EX-D). At a rocking mode the per-foot forces
  are large while their *sum* (the limited quantity) is ~0 — exactly 0 in the
  symmetric case, partial cancellation with a CG offset. EX-D: net-force limiting
  cuts the bounce per-foot overtest 204×→5× but leaves the rocking per-foot
  overtest at **221× (23 dB)**; adding a moment limit → 32×.
- **One notch → a shifted cluster** (EX-C). The payload carves several suppression
  dips (−36 to −46 dB) that live in DIFFERENT interface combinations — bounce in
  the mean of the feet, rocking in the differentials — and the notch frequencies
  shift −11% to +6% off the fixed-base modes because backing compliance + coupling
  retune the absorber. **A notch placed at the shaker fixed-base frequency can miss
  the real flight notch.**
- **Single-axis shaker = simultaneous over- and under-test** (EX-D). A uniform
  vertical drive over-tests the coupled pitch-rocking mode and *under-tests* the
  roll channel it cannot excite (exact zero). **NOTE/correction:** that roll-zero
  is specific to one vertical-axis run; a lateral (X/Y) shaker DOES excite rocking
  via CG-height overturning (and lateral axes are the classic rocking case — Table
  1). What NO rigid single-axis translational shaker reproduces is the
  *differential/uncorrelated foot motion* of flight (7004C p.8 mechanism 2). So a
  full 3-axis campaign excites rocking, but the rocking *content* still differs
  from flight.

### Is overtest more or less severe distributed vs single-point?
**More severe, and the extra severity is hidden.** The net in-axis force overtest
is ~the same as single-point (bounce). Distributed feet ADD rocking/moment
overtest in the per-foot and moment channels — more severe (23 dB per-foot here
after standard limiting) AND outside the net-force limit's field of view. They
also add the uniform-motion mismatch (p.8 cause 2) that is identically zero in a
single-point model. The single-point idealization therefore reports the article as
*safer than it is* in the rocking channels.

---

## 3. How far from a foot can you see the notch (EX-C, checker-backed)

The notch is the suppression a payload absorber-mode imposes on the backing. Its
spatial reach is set by the backing's **modal overlap factor** MOF = (half-power
bandwidth) / (modal spacing) at the notch frequency:

- **MOF < 1 (discrete global backing modes — the usual aerospace panel at payload
  frequencies):** the payload retunes whole backing modes; the notch is visible
  structure-wide (to the plate boundary, ~6 foot-spacings here). A control accel
  1–3 foot-spacings away DOES see it.
- **MOF ≳ 1 (heavy damping / dense modes / higher bands):** visibility contracts to
  ≈ **λ/4** of the bending wavelength around the feet (measured 0.07–0.09 m vs λ/4
  = 0.08–0.10 m). The naïve "λ/4" first-principles guess holds ONLY here.
- **Rocking notches are more local than bounce**, and can be invisible in a single
  point spectrum entirely (they are differential/moment features — look in the
  differential channel or a moment gauge).

Convergence note: notch *frequencies* shift <0.5% and area-fractions <1.4 pts under
2× modal refinement (robust); the 3-dB "visibility radius" is threshold-sensitive
when suppression hovers near 3 dB — use frequency/area metrics as the converged
ones (this is a documented checker YELLOW).

---

## 4. The empirical path — limiting WITHOUT a coupled forced FEM (EX-E, checker-backed)

**Question:** can you do response/force limiting from data at one foot / a few feet
/ a point 1–3 foot-spacings away, without a full coupled FEM of the forced system?

**Core result — yes, the measurement replaces the coupled solve.** The impedance
method a = (Ms+Ml)⁻¹Ms·A_free, F = Ml·a (7004C Eq 3/4) reconstructs the coupled
interface loads from interface-only quantities, all measurable without solving the
coupled system: load apparent mass Ml (low-level run with force gauges on the
article), source apparent mass Ms (tap test on the disconnected mount), source free
acceleration A_free (flight data / source model). With the **full** interface matrix
the reconstruction is **exact** (checker: max rel err < 1e-9 across regimes). No
coupled forced FEM required.

**The cost is spatial — how much of the matrix you measure (EX-E, soft/low-overlap):**

| measurement | what it recovers | per-foot force error | moment error |
|---|---|---|---|
| **1 foot / single-point condensation** (7004C default) | bounce / net only | **68–91%** | **100% (predicts 0)** |
| **diagonal, N feet independent** | per-foot only where feet decouple | erratic (8–63%) | erratic |
| **rigid-3 (≥3 spaced feet)** | bounce + 2 rocking | **3–17%** | 0–17% |
| **full 4-foot matrix** | everything incl. warping | exact | exact |

So: **one foot → bounce, low-frequency, coherent regime only; ≥3 well-placed feet →
rocking/moment recovered; cross-impedance between feet matters (diagonal-only is
not safe in the coupled regime).** At high frequency (stiff feet / wide spacing)
rigid-3 degrades (per-foot up to ~31%) because the interface starts to warp / feet
decouple — there you shift toward per-foot/diagonal treatment. This is the same
modal-overlap crossover as §3.

**Response limiting via a remote accel (EX-E Part 2):** transmissibility T =
a_remote/a_interface is input-independent, so for a LINEAR system a T calibrated in
a low-level run of the *same (integrated) configuration* is exact at high level,
**at any distance within the visibility regime**. The failure mode is **config
mismatch**: a T calibrated on the bare/un-integrated backing is ~100% wrong
broadband (the payload shifts every backing mode). Operational rule: **calibrate
the response-limit transmissibility with the payload installed** (the standard
low-level run already does this); never transfer a bare-structure transmissibility.

**What the empirical path still needs (not escapable by any method):**
- the source free acceleration / flight environment (an envelope is fine);
- the asymptotic/residual mass above the measured band (apparent mass rolls off —
  mildly model-informed);
- a *rigid-interface* assumption to turn ≥3 foot measurements into a moment/
  rocking limit (a low-order model, not a coupled FEM);
- simultaneous, phase-coherent multi-channel measurement for the differential
  channels (sequential single-sensor is insufficient for rocking — relevant to the
  MPL single-sensor thread);
- linearity (transmissibility-based response limiting assumes it).

**Net judgment:** the path forward is "no coupled forced FEM," not "no model." Use a
coarse/uncoupled model as a regularizing prior (residual mass, rigid-interface
reconstruction, extrapolation), update it with a scrappy interface measurement
(apparent mass + integrated-config transmissibility), and propagate uncertainty so
sparse data widens the limit instead of producing a confident wrong number — the
project's robust apparent-mass twin (notes §6.1). The project already has
supporting evidence: the ShockSat × tray study (D7) found a tray-center accel
tracking the net-CG interface response with ρ≈1.000 in band — a working
response-limit proxy.

---

## 4a. Template — a rocking-aware response-limit test plan from POOR, FIXED inputs

Use this when you cannot get better data or models and must still produce a
defensible, rocking-aware response-limited test plan. It is a reasoning template
(not checker-backed); it follows directly from §2–§4.

**The exact inputs this is written for** (a real, common situation):
1. an *outdated/coarse* model of the primary (mounting) structure;
2. a *single-point* measured apparent-mass curve from roughly the right region;
3. *fixed-base normal modes* of the payload from a stress model (e.g. Ansys);
4. *one flight accelerometer* near the feet but not right at a foot.

**The core move:** stop trying to MEASURE rocking (you can't, from one point).
Split modes into "what I can see" (bounce/pumping) and "what I'm blind to"
(rocking/see-saw); take real relief on the first, and BOUND + INSTRUMENT the
second. The only thing you genuinely lack for rocking is how hard the mount
resists a see-saw at the feet (its rotational impedance) — that is the one quantity
to bracket.

**The asymmetry that sets the safe default:** NOT notching = conservative (harsh
but safe — the classic over-test). NOTCHING a mode that is actually hot in flight =
under-test = the dangerous error. So for any channel you cannot see, the default is
full level (no notch); relief must be earned.

### Steps
1. **Sort the modes (from the normal-modes run — your most reliable input).** Tag
   each in-band mode pumping-type vs see-saw-type from its shape; record rocking
   frequencies and rotary effective inertia. Free and trustworthy.
2. **Bounce modes → notch for real.** Set the response limit on the pumping modes
   from the single-point apparent mass + the flight accel (the §4 single-point
   path). This is the part your data supports — take the relief.
3. **Rocking modes → bracket, don't guess.** Build a best/worst pair for the mount's
   rocking resistance: soft end (deep natural notch) and stiff end (≈ hard mount,
   least relief). Anchor it with what you DO have — the magnitude of the single-
   point curve, the foot spacing, and the SHAPE from the outdated model — but keep
   the band wide (the model is stale, so inflate, don't trust). Evaluate the
   **worst case** (stiff = least relief = highest response):
   - worst case ≤ hardware capability → **run those frequencies at full level, no
     notch** (safe, nothing lost);
   - worst case > capability → notch only to the **least-relief (most conservative)**
     end of the bracket. NEVER notch a rocking band deeper than the bracket and the
     live test support.
4. **Make the TEST see rocking — the part you control.** You can't improve the
   flight data or models, but the test setup is yours: put ≥2 control accels across
   the feet (and force/strain gauges if available) so a see-saw shows up live as
   two feet out of phase. Require a **mandatory low-level run first**, and set/confirm
   any rocking notch from THAT live data, not the blind prediction. The test is
   where you finally see what you couldn't beforehand. (Standard FLVT practice:
   verify on the shaker before full level.)
5. **Make the rocking guard its own channel.** A limit on the pumping channel does
   NOT protect rocking — the see-saw loads cancel in any summed/single signal (the
   resultant trap, §2). The rocking guard must be an explicit channel: a difference
   between two foot sensors, or a moment/differential gauge — never an afterthought.
6. **Write the governance in.** State for every notch whether it is *data-backed*
   (bounce), *bracket-backed and conservative* (rocking), or *full-level by worst-
   case* — and the live-test gates allowed to change it (e.g. "if the low-level run
   shows the see-saw mode below X, deepen to Y; else full level"). Keeps relief
   honest and over-test minimized without ever flying blind.

### Honest tradeoff and residual risk
With blind prediction you cannot be both maximally un-conservative AND safe on
rocking — you buy safety in prediction by staying conservative on rocking, and buy
the relief back in execution with spaced sensors + the low-level run. Residual
risks to state in the plan: (a) the "near but not close" flight accel only
represents the feet where that region moves as one piece (§3 coherence check —
distance vs bending wavelength); (b) the bracket can be wrong if the true mount
rotational impedance falls outside it — widen if unsure; (c) nonlinearity /
level-dependence breaks the low-level-to-full-level transfer — check level
linearity in the low-level run.

---

## 5. Practical decision guide for an agent asked to set up notching

1. **State the QOI first** (net interface force? per-foot force? a critical response
   accel? a moment?) and the limited quantity. Force limiting ⇒ interface force;
   response limiting ⇒ a response accel + a flight-predicted level there.
2. **Diagnose the regime** from data: tap two different feet, compare apparent
   masses (7004C p.29). Agreement ⇒ coherent/low-overlap ⇒ sparse measurement OK and
   the notch is global. Disagreement ⇒ differential regime ⇒ instrument ≥3 feet and
   expect locality.
3. **Pick the measurement set** by §4: ≥3 spaced feet if any rocking mode carries
   significant effective inertia in band; one foot only if you have justified
   coherence and only care about bounce.
4. **For response limiting, calibrate transmissibility in the integrated config**,
   and put the control accel where the controlled mode has real amplitude (not on a
   nodal line) and inside the visibility regime (§3).
5. **Check the rocking/moment channel explicitly** — do not trust a net-force limit
   to protect against rocking (the resultant trap). Add a moment or per-foot limit
   if any rocking mode is in band.
6. **Wrap in uncertainty** (the Bayesian twin): report the limit with intervals;
   gate any tightening on held-out coverage, never on convenience.
7. **Anti-overclaim:** "NUTS active" only with all-variable convergence; never
   present a non-converged posterior as calibrated; never fabricate a notch depth.

---

## 6. Open questions / not settled here

- The **middle regime** (foot spacing ≈ wavelength, MOF ≈ 1) is where both
  single-point and per-foot fail and the dangerous rocking modes often live — it
  needs the most spatial info and is the least forgiving. Not deeply characterized.
- **Lateral-axis force limiting on the compliant backing** is not yet modeled
  faithfully (the plate carries bending only; lateral foot loads need a membrane/
  in-plane reaction). A lateral EX-D arm is an open build.
- **Nonlinearity** (joint, level-dependence) breaks the transmissibility-exactness
  argument — untested here.
- **Complex-TDOF Appendix C tables** not replicated (image-only PDF).
- **Real-hardware confirmation** on the ShockSat × tray coupled models (distributed
  6-DOF CBUSH feet vs single-point condensation) is the natural next step.
- **IP/novelty:** the "Bayesian 7004C" notch is a flagged candidate claim
  (`docs/proposal/patent_ideas_ranked.md`, design-around target US8731868B2). Any
  publication is GATED on the disclose-before-disclosure IP sequence (notes).

---

## 7. Pointers

- This workspace: `code/common.py` (verified models), `code/ex_[a-e]_*.py`,
  `results/ex_[a-e]_results.json`, `figures/` (16 PNG + 3 GIF), `packet.md`,
  `quantity_contracts.md` (Q1–Q12), `assumptions_ledger.md`, `decisions_log.md`,
  `7004c_multipoint_notch_summary.pptx`, `check.py`, `run_all.sh`.
- Reference: `references/NASA-HDBK-7004C-Force-Limited-Vibration-Testing.pdf`
  (anchors pp.25–38, 55–62; quotes pp.8, 10, 29, 31, 48).
- Related project threads: ShockSat × tray coupled QOI
  (`artifacts/reports/shocksat_tray_coupled_qoi_20260610/`, mount-dominated QOI,
  D7 response-limit proxy); robust apparent-mass twin vision (notes/project_vision
  §6.1/§6.2); MPL stand coupled/uncoupled modal test (the live 7004C-shift data).
- Literature: see `lit_review_prompt.md` in this folder — run it before claiming
  novelty or finalizing a method.
