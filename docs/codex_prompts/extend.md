# Codex task: EXTEND (one milestone only)

You are in `Agentic BayesX`. Read `AGENTS.md`, `design/statfem-assumptions.md`, and `docs/harness/agentic-engineering-quality-gates.md`.

## Goal
Implement ONE next milestone with harness discipline. Pick exactly one:

**A) Inference quality** — Add posterior credible intervals (e.g. 2.5/97.5 percentiles) for k1, k2/k12, c1, c2/c12, force_amp, force_fc, and qoi_peak_tray_accel. Extend non-immutable checks to assert truth lies inside 95% CI on synthetic data.

**B) Measurement channels** — Make ch2 (interface modal) and ch3 (tray impact) use distinct forward models instead of identical predictions. Update synthetic data + MCMC + plots.

**C) Posterior predictive check** — Add `src/inference/ppc.py` and checker script that generates replicated spectra and a pass/fail metric vs held-out frequency band.

**D) DeweSoft stub** — Add `src/hardware/dewesoft_stub.py` with a fake API (connect, configure, acquire_spectrum) and a harness trial that logs deterministic fake spectra; no real hardware yet.

## Process
1. Write plan in `notes/todo.md` (5-10 lines).
2. For any named engineering quantity, write the quantity contract first: numerator, denominator, coordinate, excitation, boundary condition, units, expected limiting behavior, expected resonance behavior, and reference.
3. Identify relevant standards/benchmarks/references before implementation. If none are obvious, document the reference search and why selected references apply or do not apply.
4. Add or update an assumptions ledger with numerical values, units, rationale, source, and sensitivity priority.
5. Implement smallest correct diff.
6. Add/update tests; do not weaken immutable checkers without human approval.
7. Add human-review plots that expose clean vs observed data, absolute errors, normalized diagnostics, residuals/zoom views, and posterior/QOI samples when applicable.
8. Add at least one sensitivity pass, or document why sensitivity is out of scope and add it to `notes/todo.md`.
9. Run `bash scripts/run_pipeline.sh` or targeted tests.
10. Regenerate plots if inference or channels changed.
11. Log in `notes/runs.md`.

## Done when
- Chosen milestone has code + test/checker + notes.
- All existing tests still pass unless you document intentional breakage.
- Assumptions, references/standards, review figures, and sensitivity status are visible in artifacts.
