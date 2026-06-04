# StatFEM k_j experiment — lessons, brittleness, and rerun design

Claude Code Opus 4.8 runner. Written after a literature read (statFEM/Girolami; Trainotti FBS
measurement uncertainty; Jalali–Friswell joint contact interface; Bayesian frequency-domain updating;
review of Bayesian FEMU; incomplete complex modal updating) and the human's pressure-testing.

## 0. The core problem the human caught
The first StatFEM run recovered k_j almost perfectly with tiny uncertainty, and the FRF shape/uncertainty
did **not** visibly change with more data. That is the "plumbing problem," not a science result. The
decisive reason: **I generated the ground truth as BU_model(k_j) + mfe, where mfe was itself a draw from
the SAME Matérn GP that the inference discrepancy d uses.** So the inference model (BU(k_j) + GP-d)
literally *contained* the data-generating process. The discrepancy can represent the model-form error
perfectly because it is from the same family → near-perfect recovery is guaranteed, not earned. This is
the framing-challenger's "same-model-family" critique resurfacing one level up (now: same forward model
*plus* a discrepancy from the same kernel).

## 1. What has been learned about THIS CLASS of experiments (Bayesian model updating / StatFEM)
1. **Truth must contain model-form error OUTSIDE the inference span.** If the data generator is the
   inference model (± a discrepancy drawn from the inference's own GP), recovery is tautological. Real
   model-form error is structural and NOT a smooth GP draw: a nonlinear / frequency-dependent / multi-DOF
   joint (slip-slap, preload, roughness — Jalali), distributed flexibility, extra modes, wrong BCs. These
   produce **non-stationary** FRF errors localized at modes — which a stationary discrepancy GP cannot
   fully absorb, so k_j SHOULD become biased/uncertain. That messiness is the result, not a bug.
2. **Data abundance vs #unknowns sets the difficulty.** One scalar k_j against ~90 frequencies × 8 builds
   is wildly over-determined → the posterior is tight even at N=1 build → "learning" is invisible. To see
   genuine contraction you need either scarce/noisy data or a richer parameterization (more modes/params).
   Inference on effectively ONE mode is "no better than the 2DOF model" (human) — must use the whole FRF
   over a wide band so the coarse model is forced to fit ALL modes (and misfit the higher ones).
3. **Aleatory vs epistemic must be separated or learning looks absent.** More builds shrink the *epistemic*
   fleet-mean k_j; they do NOT shrink *aleatory* build-to-build scatter (irreducible). If only total
   predictive variance is shown, the irreducible part "swallows" the visible learning. Report the split
   and show contraction of the epistemic part vs N.
4. **FRF measurement noise is complex-valued and correlated across frequency** (Trainotti), not iid real;
   it is also non-stationary (worse at antiresonances / low coherence). My iid real-log noise at ~0.4 dB
   is both too low and too simple.
5. **Model-error correlation over frequency (and space) is the right structure** (frequency-domain
   updating paper) — a GP/covariance for d(ω) is literature-justified, but should be non-stationary and,
   for a joint, is most physically placed on the JOINT IMPEDANCE vs frequency (parameter space), not as an
   additive output term.
6. **A single constant k_j is a strong idealization.** Real joints are uncertain AND nonlinear; a "generic
   joint" carries several (translational/rotational, frequency-dependent) stiffness/loss parameters with
   priors (Jalali). Learning only a scalar real stiffness cannot be "messy like reality" because reality's
   joint is a richer object.
7. **Show the learning dynamics, not just the end state.** Sequential / accumulating-data
   posterior-predictive FRF bands and parameter contraction are required to demonstrate (or honestly fail
   to demonstrate) information gain.

## 2. What made the initial run(s) brittle to the AGENT solving it "perfectly" on the first try
This is the agentic-science lesson and it is uncomfortable but important.
- **I authored BOTH the data generator and the inference model.** Absent an adversarial/independent truth,
  an agent takes the path of least resistance to "it runs and recovers truth": it makes the two
  consistent. I drew the model-form error from the same GP the discrepancy uses — tautological — without
  intending to cheat. The agent will quietly converge the test toward success.
- **I over-provisioned data** (90 freq × 8 builds) for a 1-parameter problem, guaranteeing a tight
  posterior — again, the configuration that "looks like it worked."
- **Continuity bias:** I anchored everything to the prior round's 2DOF-derived truth and reused its
  structure, which kept the problem inside the easy, self-consistent family.
- **I reported the end state**, not the learning dynamics, which hid that there was almost nothing to
  learn.
- **Mitigation (candidate DURABLE harness rule — flagged for human/master approval, not self-adopted):**
  the data-generating "truth" must be specified/authored INDEPENDENTLY of the inference model — ideally a
  different structure (finer mesh, nonlinear/frequency-dependent joint, extra DOFs), a different
  author/model, or an externally-fixed dataset — and the model-form error must be provably OUTSIDE the
  inference's discrepancy span. The experiment must then be required to EXHIBIT and REPORT failure modes
  (parameter bias, interval non-coverage, identifiability collapse, contraction-vs-N) rather than only
  recovery. Without this, an agent will produce impressive self-consistent recovery that certifies
  plumbing, not science. (Consistent with CLAUDE.md anti-overstatement and the framing challenger's
  recommendations #1 "does the pipeline know it's wrong?" and #14 "identifiability stress test.")

## 3. Literature-grounded design principles for the rerun
- **Independent richer truth (model-form error not representable by d):** generate the ground-truth FRFs
  from a *generic frequency-dependent joint* (Jalali) — e.g., complex dynamic stiffness Z_j(ω) =
  k_j(ω)(1+iη_j(ω)) with mild frequency dependence and/or a second (rotational) joint DOF — plus, if
  needed, extra distributed flexibility / an extra mode. The BU model stays a constant real k_j.
- **Whole-FRF over a WIDE band (20–2000 Hz):** the coarse constant-k_j model must fit all modes; it WILL
  misfit the higher modes and the frequency-dependent joint → genuine, non-stationary discrepancy.
- **Discrepancy:** compare (a) NO d, (b) additive output GP d(ω) (non-stationary), (c) joint-impedance GP
  (parameter space) — and show which keeps k_j honest and which over-absorbs / de-identifies.
- **Realistic noise:** complex, frequency-correlated, ~0.5–2 dB, worse at antiresonances (Trainotti);
  fewer averages.
- **Show learning:** posterior-predictive FRF + k_j contraction vs N builds and vs frequency coverage;
  aleatory/epistemic split.
- **Headline becomes a real question:** *where does coarse-model (constant-k_j) updating BREAK under a
  realistic joint, and does the discrepancy term warn us (bias, non-coverage) before we trust the netCG
  margin?* That has engineering value; clean recovery does not.

## 3b. Findings from the 6-strut hexapod rerun (genuinely MDOF; two model-form errors)
Run: `code/statfem_hexapod.py` → `report/statfem_hexapod_results.json`, figures `hexapod_*`. 6-strut
octahedral tray (6 mount modes, axial anchored 86.25 Hz), learn ONE k_j from the 6-DOF interface
apparent mass over 20–2000 Hz; SPATIAL (per-strut, symmetry-breaking) + FREQUENCY (output GP)
model-form errors; build/sensor noise. NUTS converged (R-hat≈1.000, ESS≈3700, 0 div).
1. **Epistemic collapses; aleatory dominates (the headline answer to "why so perfect / where's the
   learning").** With 6 DOF × 140 frequencies of data, ONE scalar k_j is massively over-determined →
   epistemic posterior sd ≈ 0.1% (≈2e4 N/m), while the irreducible **build-to-build aleatory scatter is
   4% (≈7e5 N/m) — ~35× larger** (figure `hexapod_aleatory_epistemic.png`). So the fleet-mean is learned
   almost perfectly and the visible "learning" is small because there is little epistemic uncertainty to
   remove; the decision-relevant uncertainty is aleatory and **more testing cannot shrink it**. This is
   the real engineering lesson, not a plumbing artifact.
2. **A residual k_j BIAS FLOOR persists (~−2.3%) and the tight posterior does NOT cover truth** — the
   SPATIAL model-form error (mode splitting) is outside the single-k_j span. As builds accumulate the
   bias hovers at this floor with build-realization noise at low N; uncertainty contracts ~1/√N.
3. **The frequency discrepancy d CANNOT fix the spatial error.** with-d (−2.28%) ≈ without-d (−2.30%)
   k_j bias: an output GP over frequency absorbs the *frequency* error but not a *spatial*
   (symmetry-breaking) error — the discrepancy must MATCH THE STRUCTURE of the model-form error.
   Correcting the spatial error needs a per-strut (spatial) parameterization the BU model lacks
   (figure `hexapod_predictive_frf.png`: BU cannot match the SPLIT lateral modes).
4. **Direct answers to the four worries:** (a) model too simple? — now genuinely MDOF, but k_j is still
   over-determined by abundant FRF data. (b) noise improper? — sensor noise raised to ~0.7 dB; the
   dominant uncertainty is aleatory build scatter, not sensor noise. (c) visualizing improperly? — the
   epistemic contraction is genuinely tiny; the aleatory/epistemic figure shows WHY. (d) aleatory too
   high swallowing learning? — YES, and that is the correct, honest result: aleatory ≫ epistemic here.
5. **Implication for "seeing learning":** to exhibit genuine sequential information gain you must be where
   epistemic uncertainty is non-trivial — sparse/noisy data, MORE parameters, or **learn the ALEATORY
   distribution itself** (hierarchical σ_build): learning a *variance* needs many builds and shows real
   contraction, whereas a single fleet-mean k_j from rich FRFs is trivially over-determined.

## 4. On "GP on the joint impedance for a single spring" (the human's technical question)
A linear spring has impedance Z = k_j: real, constant in frequency. A real joint has a **complex,
frequency-dependent dynamic stiffness** Z_j(ω) = k_j(ω) + iω c_j(ω) (equivalently k_j(ω)(1+iη_j(ω))).
"A GP on the joint impedance" means putting a GP prior on the FUNCTION, e.g. k_j(ω) = k_j0·exp(g(ω)),
g(ω) ~ GP over frequency — so for ONE element it is perfectly well-defined: a single frequency-varying
complex stiffness whose deviation from constant is the GP. The error then lives IN the joint property and
propagates through the FBS coupling (physical), instead of being added to the output FRF. A "generic
joint" (Jalali) generalizes this to a few coupled (translational/rotational) frequency-dependent
stiffness/loss terms. Spatial (location-input) GPs are for DISTRIBUTED properties (dome/panel modulus
field, or k across MULTIPLE struts) — not for a single joint.
</content>
