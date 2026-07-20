# Assumptions ledger - forcing-marginalized damping toy

All values are synthetic and chosen for plumbing visibility, not physical fidelity.

| ID | Value | Units | Role | Rationale | Sensitivity priority |
|---|---:|---|---|---|---|
| A1 | `m1 = 1.0` | kg | primary mass | normalized primary structure | medium |
| A2 | `m2 = 0.18` | kg | secondary mass | lightweight attached component | high |
| A3 | `m3 = 0.035` | kg | hidden rattler mass | model-form error absent from twin | high |
| A4 | `f1_nom ~= 55` | Hz | primary-to-ground stiffness scale | keeps modes in aerospace vibe range | medium |
| A5 | `f12_nom ~= 96` | Hz | primary-secondary joint stiffness scale | makes QOIs joint-sensitive | high |
| A6 | `f23_nom ~= 142` | Hz | hidden rattler stiffness scale | creates unmodelled local feature | high |
| A7 | `drive_levels = 0.35, 1.8` | dimensionless | amplitude labels | low/high stepped-sine-like conditions | high |
| A8 | `zeta_joint(A) = 0.006 + 0.060 s(A)` | damping ratio | hidden truth damping law | slip-like amplitude-dependent equivalent damping | high |
| A9 | `k12(A) = k12_nom (1 - 0.10 s(A))` | N/m | hidden truth stiffness softening | crude macroslip-like softening | high |
| A10 | `s(A) = A^1.7 / (1 + A^1.7)` | dimensionless | hidden slip activation | smooth two-level toy surrogate | high |
| A11 | `logmag sigma = 0.035` | log units | ratio measurement noise | small but visible complex FRF noise | medium |
| A12 | `phase sigma = 0.035` | rad | ratio measurement noise | small phase noise | medium |
| A13 | 90 log-spaced frequencies | Hz | data grid | log frequency axis, 25-240 Hz | medium |
| A14 | every 4th frequency held out | index rule | held-out check | interpolation QOI/ratio trust gate | high |
| A15 | one synthetic realization | count | dataset count | plumbing only; no test-to-test variability | high |
| A16 | no absolute force in likelihood | n/a | forcing treatment | force cancels in response ratio | high |

## Variables

- Inferred by the twin: `k1_scale`, `k12_scale`, `zeta_low`, `zeta_high`, `sigma_model`.
- Fixed in the twin: masses, primary damping, frequency grid, observation noise.
- Hidden from the twin: forcing spectrum, hidden third DOF, true amplitude-dependent damping law, true amplitude-dependent stiffness softening.
- Not modeled: flight-to-flight variability, preload uncertainty, actual Coulomb friction, contact state evolution, harmonics, impacts/rattle with clearance.
