# question_framing.md — StatFEM consistency toy (Experiment A)

AGENTS.md Question-and-Decision gate.

## The engineering decision being supported
When you calibrate a structural model (here: a stiffness scale θ of an axial rod) from modal data and your
model is imperfect, WHICH way of injecting the physics gives a trustworthy answer? Specifically: does the
calibrated parameter (and the held-out prediction) converge to the truth as you refine the numerics, and
does it stay put when you change a purely-numerical knob that carries no information? If a method's answer
moves when you change a made-up number (residual noise σ_r, collocation count N_c, mesh h), an engineer
cannot trust that answer.

## Plain-English glossary (ML/stats terms, defined on first use)
- **Posterior** — the probability distribution of an unknown (here θ, the stiffness scale, dimensionless)
  AFTER seeing data; summarised by a mean and a 95% credible interval (CI: the central interval containing
  95% of posterior probability).
- **Consistency** — intuition: "with enough good data the answer locks onto the truth." Precisely: as data
  grow, the posterior concentrates (its spread → 0) on the true value θ_true.
- **Discretization-invariance** — intuition: "turning a knob that is only about how finely you chopped up
  the math should not change your scientific answer." Precisely: the posterior is (nearly) unchanged as a
  purely-numerical knob (N_c, σ_r, mesh h) is refined.
- **Likelihood** — how probable the observed data are for a given θ; **prior** — belief about θ before data;
  posterior ∝ likelihood × prior (Bayes' rule).
- **NUTS** (No-U-Turn Sampler) — a gradient-based Markov-chain Monte Carlo method that draws samples from
  the posterior; "converged" requires diagnostics (R-hat near 1, enough effective samples, few divergences).

## The objective function / success metric
There is no single scalar to optimise; this is an EVALUATION. The success metrics are the three consistency
criteria, reported as NUMBERS for every construction:
- **C1 concentration**: posterior(θ) mean → θ_true and SD ↓ (toward 0) as the number of replicate tests n
  grows. (no-error control ε=0: a correct method MUST pass.)
- **C2 discretization-sensitivity**: spread (max−min) of the posterior θ mean across the numerical knob —
  smaller is better; a large spread is the smoking gun for the indicted behaviour.
- **C3 held-out coverage**: fraction of held-out true modal frequencies inside the 95% predictive interval
  (target ≈ 0.95).

## What the analysis is allowed to choose
Only the posterior (via NUTS) given each fixed construction + data. It does NOT choose the construction, the
knob values, ε, or θ_true — those are the controlled independent variables of the experiment.

## What remains human judgment
Whether the toy is representative enough to inform a real calibration; which construction to adopt in
practice given cost; whether the Winkler-foundation surrogate is the right stand-in for real model-form
error; and the policy decision of how much discretization-sensitivity is tolerable.

## What would make this the WRONG question
- If the forward solver is NOT validated against the analytic truth, any "drift" could be mere
  under-resolution, not a property of the method (mitigated by the solver-validation gate, P4).
- If θ is weakly identified at a given ε (foundation and θ both raise frequencies), "non-concentration"
  would be an identifiability statement, not an inconsistency of the method (mitigated by reporting the
  θ→observable sensitivity and an identifiability view, P5).
- If the result depends on one lucky/unlucky synthetic realization (mitigated by the n-axis and a
  realization-sensitivity note; single-realization cells are flagged YELLOW).
- If the conclusion is read as a universal claim about StatFEM rather than a finding ON THIS TOY.
