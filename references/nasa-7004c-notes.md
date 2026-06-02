# NASA-STD-7004C Notes (Trace)

Purpose: capture model credibility and validation discipline for this workflow.

## Planned tie-ins
- Explicit assumptions and validity bounds documented in `design/statfem-assumptions.md`.
- Deterministic checks and reproducible run bundles under `artifacts/runs/`.
- Clear separation of synthetic truth generation vs inference model.
- Apparent-mass conventions must be stated before generating plots or checkers.

## Apparent-mass convention note
- NASA-HDBK-7004C defines source and load apparent masses at the interface junction with source and load disconnected, but the constraints differ.
- In the simple TDOF impedance-method example, source apparent mass has a minimum at the source resonance and grows toward infinity as frequency approaches zero. A normalized SDOF expression is `|1 - r^2 + i r/Q| / r^2`.
- In the same example, load apparent mass has the familiar fixed-base resonance peak. A normalized SDOF load expression is `|1 + i r/Q| / |1 - r^2 + i r/Q|`.
- Drive-point `F/a` at a moving response coordinate can look like source apparent mass or reciprocal inertance depending on the boundary condition. Do not label it only by algebraic form; state the source/load constraint.
- Future FBS/STATFEM plots should state whether a curve is:
  - source apparent mass;
  - load apparent mass;
  - sum of source and load apparent masses;
  - drive-point reciprocal inertance;
  - accelerance or inertance.
- The first Agentic BayesX key-FRF plot made this mistake and was corrected on 2026-06-01. See `docs/lab/apparent-mass-convention-postmortem.md`.

## Current limitations
- No physical test article yet; synthetic-only at this stage.
- Experimental equipment control currently stubbed/simulated.
