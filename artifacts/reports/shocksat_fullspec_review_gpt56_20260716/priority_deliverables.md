# Priority deliverables

1. Audit all eight claims with SOUND / OVER-CLAIMED / WRONG / CANNOT-VERIFY verdicts, artifact citations, recomputed values where feasible, and corrected statements.
   - Delivery: `review.md`, `out/claim_audit.json`.
2. Decide whether the study's overall YELLOW and all-S1–S5-falsified/not-met conclusion still holds.
   - Delivery: `review.md`.
3. Recommend prioritized, costed next actions.
   - Delivery: `next_steps.md`.
4. Give special attention to a future agent action space that can alter actual model form: geometry, element type/formulation, connectivity, and mesh form/density.
   - Delivery: `next_steps.md`.
5. Preserve an auditable trail and update the two authorized project logs without modifying the reviewed study.
   - Delivery: `decisions_log.md`, append-only entries in `notes/runs.md` and `docs/report/project_log.md`.

Acceptance: conclusions are no stronger than checker and recomputation evidence; reviewed files and immutable checkers remain untouched; no multi-hour NUTS/eigensolve jobs are run.
