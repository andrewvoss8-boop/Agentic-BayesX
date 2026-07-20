# Priority deliverables - forcing-marginalized damping toy

| # | Andrew's priority ask | Interpretation | Delivered in | Status |
|---|---|---|---|---|
| P1 | Prepare a toy example to explore the plumbing | Build a replayable synthetic primary/secondary example, not a prose-only sketch | `run_all.sh`, `code/run_toy.py`, `packet.md` | DONE |
| P2 | Hide the forcing function from the digital twin | Generate a hidden complex force spectrum, but fit only force-normalized secondary/primary response ratios so the force cancels analytically | `out/summary.json`, `figures/fig1_forcing_cancellation.png` | DONE |
| P3 | Hide the damping formulation from the digital twin | Truth uses amplitude-dependent slip-like damping and stiffness softening; twin only infers one equivalent viscous joint damping ratio per amplitude level | `decisions_log.md`, `assumptions_ledger.md`, `out/summary.json` | DONE |
| P4 | Hide model-form error from the digital twin | Truth has a third hidden "rattler" DOF; twin uses only a 2-DOF primary/secondary model plus an inferred residual scale | `quantity_contracts.md`, `packet.md` | DONE |
| P5 | See what it can learn about damping from data and damping-dependent QOIs | Report posterior damping intervals, probability high-amplitude damping exceeds low-amplitude damping, held-out response-ratio coverage, and QOI coverage | `packet.md`, `checker_report.json` | DONE |

## Acceptance criteria used

- Forcing cancellation gate: response-ratio data computed with the hidden force must match direct transfer ratios to numerical precision.
- Sampler gate: report all-variable NUTS diagnostics; R-hat <= 1.05, ESS >= 200, divergence fraction < 2% for a GREEN posterior-use claim.
- Damping-learning gate: posterior probability that high-amplitude effective damping exceeds low-amplitude effective damping should be >= 0.95.
- QOI gate: damping-dependent held-out QOIs should cover the synthetic truth when intervals are claimed.
- Honesty gate: report that the nonlinear slip/friction law itself is not identified; only equivalent damping at the tested amplitude levels is learned.
