# Decisions log - forcing-marginalized damping toy

## D0 - Task interpretation

Andrew asked for a toy example where forcing, damping formulation, and model-form error are hidden from the digital twin, while the twin learns what it can about damping and damping-dependent QOIs. I interpret this as a checked plumbing artifact, not a mature real-joint claim.

## D1 - Observation choice integrates out forcing

The synthetic truth generates a hidden complex force spectrum `F(f)` and absolute responses `a1(f)` and `a2(f)`. The twin is given only the complex response ratio

```text
T21(f) = a2(f) / a1(f)
```

For a single input force, `a2 = H2F F` and `a1 = H1F F`, so `T21 = H2F / H1F`. The forcing spectrum cancels and is never inferred. This is the toy version of using apparent-mass / transmissibility-style quantities to avoid learning the unknown flight forcing level.

## D2 - Hidden truth is intentionally richer than the twin

Truth = 3-DOF primary / secondary / hidden-rattler model. The primary-secondary joint has amplitude-dependent equivalent damping and mild stiffness softening. The hidden rattler adds local model-form error near the secondary band.

Twin = 2-DOF primary / secondary model. It does not know the hidden DOF, the damping law, or the forcing function. It infers:

- primary stiffness scale,
- joint stiffness scale,
- low-amplitude equivalent joint damping,
- high-amplitude equivalent joint damping,
- residual model-error scale.

## D3 - Damping claim boundary

The twin is allowed to learn equivalent damping at two tested amplitude levels. It is not allowed to claim that it recovered the true nonlinear slip law, Coulomb friction coefficient, preload state, or hidden damping formulation.

## D4 - QOI choice

QOIs are forcing-independent ratios or per-primary-acceleration quantities:

- secondary/primary response-ratio peak,
- secondary/primary response-ratio band RMS,
- primary-secondary interface-force per primary acceleration peak.

These QOIs still depend strongly on damping, but do not require an absolute forcing function.

## D5 - Result status

The checker uses GREEN/YELLOW/RED. A documented inability to recover the hidden nonlinear law is YELLOW, not RED, because it is a designed limitation and the effective-damping/QOI plumbing is still useful.
