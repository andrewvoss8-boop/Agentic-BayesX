# Codex task: REVIEW (read-only audit first)

You are in `Agentic BayesX`. Read `AGENTS.md`, `design/statfem-assumptions.md`, `docs/CODEX.md`, and `docs/harness/agentic-engineering-quality-gates.md`.

## Goal
Produce a technical review of the bootstrap implementation. Prefer reading and running checks over large rewrites.

## Steps
1. Run `bash scripts/run_pipeline.sh` (or confirm artifacts already exist).
2. Open and interpret plots in `artifacts/plots/`.
3. Read:
   - `src/twodof/model.py`, `src/twodof/synthetic_data.py`
   - `src/inference/mcmc.py`
   - `tests/test_posterior_recovery.py`
4. Write `notes/reviews/codex-review-YYYY-MM-DD.md` covering:
   - Physics/FBS fidelity: what is correct vs simplified?
   - Quantity conventions: for every FRF/apparent-mass term, identify numerator, denominator, coordinate, excitation, boundary condition, units, and expected shape.
   - StatFEM alignment: discrepancy model, identifiability, MCMC quality (acceptance rate ~0.02 is low)
   - Assumptions ledger quality: actual numerical values, units, sources, and graphical evidence.
   - Reference/standards alignment: which standards/benchmarks were used, what comparisons were made, and what is missing.
   - Plot/review quality: log-frequency axes, clean-vs-observed plots, absolute errors, normalized diagnostics, residuals, posterior/QOI samples.
   - Sensitivity quality: what assumptions were varied, what remains fragile, and whether QOI/decision conclusions move.
   - Harness anti-cheating: gaps or loopholes
   - Top 5 prioritized extensions (ranked, with effort estimate)

## Constraints
- Do not modify immutable checker files during this review pass.
- If you find bugs, list them in the review file before fixing (separate commit/trial).

## Deliverables
- `notes/reviews/codex-review-YYYY-MM-DD.md`
- Optional: small fixes only if a test is objectively broken; re-run tests and log in `notes/runs.md`
