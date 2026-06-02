# NUTS/HMC Backend Choice Note

Status: NUTS/HMC is not implemented in this setup. This file chooses the likely path for the next coding milestone.

## Recommendation

Use NumPyro NUTS first.

## Why

- The future model is hierarchical: structural parameters, build-to-build variability, sensor noise, and repeated flight/vibe observations.
- NUTS needs gradients, so the current NumPy likelihood should be rewritten or wrapped in a differentiable backend.
- NumPyro gives a Python/JAX path for NUTS and posterior predictive samples while keeping command-line artifact generation possible.

## Alternatives

- PyMC: friendlier model syntax, but the current hand-written complex FRF likelihood may need more translation work.
- BlackJAX: good low-level NUTS engine, but more custom plumbing for model definition and diagnostics.
- Stan: robust HMC/NUTS, but adds a separate toolchain and more friction for local agent loops.

## Acceptance Before Claiming NUTS Is Active

- A one-command run exists.
- The run writes sampler diagnostics: divergences, step size, tree depth, ESS, R-hat where applicable.
- The checker fails if NUTS diagnostics are missing.
- The report states which variables are inferred, fixed, and not inferred.
