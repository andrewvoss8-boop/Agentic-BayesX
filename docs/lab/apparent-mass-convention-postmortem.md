# Apparent Mass Convention Postmortem

Date: 2026-06-01

Audience: Dr. Bilionis, lab collaborators, future Agentic BayesX agents

## Why This Matters

This was a useful failure. The agent generated a technically clean, reproducible, checker-passing transfer-function artifact that still violated Andrew's domain expectation from NASA-HDBK-7004C. The problem was not dishonesty or fabrication. The problem was semantic drift: the phrase "apparent mass" carried a discipline-specific convention that the workflow had not pinned down.

For this project, that is the point. Agentic workflows in aerospace structural dynamics will fail when a named quantity has several nearby meanings and the harness only checks that a plot exists. A human domain expert caught the mistake because the shape of the curve did not match the force-limited vibration mental model.

## What Happened

Andrew asked for more transfer functions:

- forcing function to key accelerations in accel/force units;
- apparent masses in mass units;
- five or more key FRFs;
- log-scale frequency axis;
- no dB scaling.

The first implementation reported acceleration/force FRFs correctly, but it plotted drive-point `F/a` at the moving mass coordinate and labeled it apparent mass. Those curves did not peak at resonance. They dipped at resonance.

Andrew flagged the mismatch: NASA-HDBK-7004C apparent-mass plots show resonance peaks. That observation was correct.

## Technical Root Cause

The first implementation used:

```text
moving-coordinate reciprocal inertance = F_drive / a_response
```

For a drive-point coordinate, this is the reciprocal of inertance:

```text
inertance = a / F
reciprocal inertance = F / a
```

When `a/F` peaks at resonance, `F/a` has a notch. That is why the first apparent-mass curves lacked peaks.

NASA-HDBK-7004C force-limited vibration work uses apparent mass in the source/load/interface sense:

```text
load apparent mass = interface or base reaction force / interface or base acceleration
```

For a base-driven load, that quantity peaks near the fixed-base resonance. NASA-HDBK-7004C discusses source and load apparent masses as frequency-dependent complex quantities at the interface and uses them in the impedance method. It also notes that force limits should use load apparent mass evaluated at coupled-system resonance frequencies, rather than letting force rise to the fixed-base apparent-mass peak. See [NASA-HDBK-7004C PDF](https://experiorlabs.com/wp-content/uploads/2019/10/NASA-HDBK-7004C-Force-Limited-Vibration-Testing.pdf), section 5.6 and Figure 9.

Andrew then caught a second nuance. Source apparent mass and load apparent mass have different constraints in the impedance-method model. In NASA-HDBK-7004C Figure 9, the source apparent mass has a resonance notch and grows as frequency approaches zero. The load apparent mass has the familiar fixed-base resonance peak. The difference is not only algebraic numerator and denominator. It is the source/load boundary condition at the interface.

## Agentic Workflow Root Cause

The agent made a plausible local choice from algebra, not from the governing engineering convention.

The failure chain:

1. The user said "apparent mass" without specifying numerator, denominator, coordinate, excitation type, or boundary condition.
2. The codebase already had a helper named `apparent_mass_from_drivepoint`, which made the wrong path feel natural.
3. The agent optimized for artifact completion: add plot, add JSON, add checker, update packet.
4. The checker verified generic properties: count, units, finite values, log frequency grid.
5. The checker did not encode the physics expectation: a 7004C-style apparent mass should have an interior resonance peak and amplification above the low-frequency value.
6. The human reviewed the plot using domain taste and rejected it.

This is a clean example of a harness passing an underspecified objective. It mirrors the larger BOED concern: optimization inside the wrong framing can make the wrong answer look disciplined.

## What the Human Caught

Andrew did not need to read the code. He looked at the plot and asked a domain question:

```text
Why don't the apparent masses have peaks?
```

That question did more than identify a plotting issue. It exposed that the workflow had not bound a technical noun to a convention.

This is the human role we want to preserve:

- notice shape-level physical implausibility;
- ask whether the agent used the same definition as the field reference;
- force the workflow to encode the corrected expectation as a test.

## Fix Applied

The workflow now reports source and load categories separately:

- acceleration/force FRFs: `a/F = -omega^2 x/F`;
- 7004C-style source apparent mass: looking back into the fixed-base source/mounting structure, with a resonance notch;
- 7004C-style load apparent mass: load-side reaction force divided by input/interface acceleration, with a fixed-base resonance peak.

The old drive-point `F/a` curves remain in `artifacts/reports/key_frf_summary.json` as `drivepoint_reciprocal_inertance` for traceability, but the plotted apparent-mass panel now separates source and load conventions.

The checker now requires:

- all required FRFs are present;
- units and linear scale are explicit;
- source apparent mass has an interior notch and low-frequency growth;
- load apparent mass has an interior peak and resonant amplification.

Current validation from `bash scripts/run_pipeline.sh`:

- key FRFs reported: 14;
- source apparent masses missing interior notches: none;
- load apparent masses missing interior peaks: none;
- load apparent masses missing resonant amplification: none;
- review packet completeness: pass;
- immutable checker manifest mismatches: none.

## Guardrails Added

For every named structural-dynamics quantity, future agent tasks should require a technical quantity contract:

| Field | Example |
|---|---|
| Quantity name | 7004C-style load apparent mass |
| Numerator | base/interface reaction force |
| Denominator | base/interface acceleration |
| Coordinates | support/interface coordinate, not moving response coordinate |
| Excitation | base acceleration or coupled interface motion |
| Boundary condition | state source-looking-back or load-mounted-on-interface |
| Units | synthetic mass units, or physical mass units when calibrated |
| Expected limiting behavior | low-frequency asymptote near supported mass |
| Expected resonance behavior | load: interior peak; source: interior notch |
| Reference | NASA-HDBK-7004C section 5.6 / Figure 9 |
| Checker | finite values, units, source notch, load peak, limiting behavior |

This contract should be written before the agent generates a plot or acceptance test.

## Lessons for Agentic Engineering Work

- Named quantities are traps. "Apparent mass" is not enough. The workflow needs numerator, denominator, coordinate, excitation, boundary condition, units, and expected shape.
- Artifact existence is not verification. A plot can be reproducible and wrong.
- Checkers need physics expectations, not only software expectations.
- Human review should focus on shape, units, limiting behavior, and convention mismatch. Those are high-leverage interventions.
- References should be used before implementation when the quantity comes from an aerospace practice standard.
- The best agentic output is not "the agent got it right." The best output is a tighter process after a caught mistake.

## Open Questions

- Should the synthetic measurement channels 1-3 be renamed from apparent mass to reciprocal inertance until they are converted to 7004C-style source/load apparent masses?
- Should the toy model add an explicit interface/base coordinate so FBS and 7004C language match the model topology?
- Should every plot-generation task require a one-paragraph "expected shape" section before code changes?
- Should BOED-lite candidate experiments include a convention check before comparing expected information gain?
