# question_framing.md — StatFEM ShockSat held-out-QOI evaluation

## The objective (Ilias, verbatim — evaluate, do NOT defend or attack)
> "Your objective should be to evaluate the StatFEM approach. It may not be possible to validate it because it
> may not be working. So, build, evaluate, identify its gaps, and suggest improvements should be your goal."

## The concern under test (do NOT broaden)
HYPOTHESIS (relayed via Andrew; no Bilionis paper found that names StatFEM): a converged StatFEM posterior can be
**confidently wrong** under model-form error, with no warning. We do not assert this is Bilionis's published
position; we test the engineering claim.

Plain-English glossary (terms defined on first use, per CLAUDE.md communication rule):
- **StatFEM** (statistical finite element method): a FEM whose output is corrected by a learned statistical
  *discrepancy* term `d` (a model-form-error function) on top of the physics, so predictions carry uncertainty
  that includes "my physics may be wrong," not just measurement noise.
- **Discrepancy `d`**: the systematic gap between the FEM prediction and reality, modeled as a random function
  (here over frequency and sensor location) — the part of the data the stiffness parameters θ cannot explain.
- **θ_g** (theta, dimensionless): per-part-group stiffness scale factor; θ_g = 1.15 is exactly +15% Young's
  modulus / spring rate of that group (stiffness is linear in E and bush rate k). 9 groups.
- **Coverage**: the fraction of held-out truth values that land inside the predicted 95% credible band. A
  trustworthy ("calibrated") method covers ≈95%; "confidently wrong" = a tight band that misses (low coverage).
- **NUTS** (No-U-Turn Sampler, a form of Hamiltonian Monte Carlo): the gradient-based MCMC we use to draw from
  the posterior. "Converged" requires passing diagnostics (R-hat ≤ 1.05, effective sample size ESS ≥ 200,
  divergence fraction < 2%), not merely that it ran.
- **Held-out QOI**: a Quantity Of Interest (here a shock/vibration response metric) at a sensor that was NEVER
  used in calibration — the trust test.

## The trust test
Calibrate on a FEW sensor channels, predict QOIs at sensors never used, check whether truth lands in the 95%
band. Either verdict can be earned: StatFEM `d` may restore held-out coverage (robust) or fail (brittle). The
direction is the science.

## Engineering decision being supported
Whether a model-form-aware (StatFEM) digital twin of a spacecraft secondary structure can be trusted to predict
a vibration QOI at an un-instrumented location — and, if not, what the gap and the pre-test lever are.

## Objective function / success metric
Primary: held-out-sensor QOI 95% coverage (peak FRF amplitude and a band-GRMS-like metric), reported as a
distribution over 5 truth bias combos. Secondary: θ recovery (covered/not) vs the strain-energy/FIM
identifiability gate; the learned discrepancy scale σ_d as a model-form-error thermometer; over-absorption /
plug-in bias of the discrepancy (Plumlee) measured by θ-bias inflation.

## What optimization/inference is allowed to choose
The posterior over θ (9 stiffness scales), the discrepancy scale σ_d, and (M2/M3) the discrepancy field. NOT the
sensor split, the bias combos, the damping, the band, or the discrepancy structure — those are human-set design
levers, varied only in the sensitivity gate.

## What remains human judgment
Whether the synthetic injected discrepancy is representative of real spacecraft model-form error; the acceptable
coverage/width tradeoff for a flight decision; whether to spend the next test dollar on more sensors vs a
joint-localized test (the identifiability lever).

## What would make this the wrong question
If the real binding constraint were measurement transfer-path mismatch (it is not, here, because truth and
inference share the FEM geometry — D3), or if the QOI of interest lived entirely in the identifiable θ subspace
(then naive calibration would suffice and the discrepancy would be moot). We probe both by spanning identifiable
and unidentifiable bias combos.
