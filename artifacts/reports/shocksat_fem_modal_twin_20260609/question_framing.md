# Question Framing — ShockSat FEM Modal Twin

## The engineering decision being supported
Can this pipeline take a real industrial FEM (NASA/NESC ShockSat, ~67k grids)
plus real free-free modal test data and produce a calibrated, uncertainty-
honest modal twin whose **held-out** predictions are trustworthy? The decision
downstream of that answer: whether a twin built this way is fit to support
load/response predictions on hardware we cannot fully test.

## Objective function / success metric
Held-out predictive accuracy AND calibration:
- per-held-out-mode frequency error (%) of the posterior median, and
- coverage: does the 95% credible interval (CI = the central range containing
  95% of posterior probability) contain the measured value about 95% of the
  time? Systematic miscoverage is the headline finding either way.
NOT in-sample fit quality.

## What the optimizer (the sampler) is allowed to choose
Nine part-group stiffness scale factors `theta_g` (dimensionless multipliers
on the stiffness blocks of each part group; theta=1 is the as-modeled value)
plus the noise-scale latents of the likelihood. Nothing else: mass, geometry,
mesh, element formulation, and the mode-pairing rule are fixed.

## What remains human judgment
- Whether the 9-group parameterization is physically meaningful (it follows
  the deck's include-file part structure; NASA hand-tuned the joint springs,
  so "joints" is a natural group).
- Which measured modes are trustworthy enough to calibrate on (we gate on
  nominal MAC; see assumptions ledger) and whether the twin is fit for any
  downstream use.
- The FEMAP cross-check (independent re-solve at our theta values).

## What would make this the wrong question
- If the measured set were actually FEM output (Task 0 exists to kill this;
  it found the genuinely measured .ash set).
- If model-form error (element formulation, flat-facet shells, lumped mass,
  missing joint physics) dominates the stiffness-scale parameterization: then
  theta absorbs bias, in-sample fit improves, and held-out coverage exposes
  it. That outcome is a finding, not a hidden failure.
- If the data cannot identify 9 groups (sloppy directions): posteriors stay
  prior-shaped; reported per-group.
