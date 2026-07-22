# Decisions log

## 2026-07-22 — INIT and isolation

- Dispatch authority is Card E at `docs/agents/structured_discrepancy_codex_review_20260722/task_card_codex_structured_discrepancy.md`.
- Work is isolated to this workspace plus narrow append-only continuity-log updates after checker-backed closure.
- Task Card D's directory, Card D's proposed workspace, and every predecessor workspace are immutable inputs.
- Direct PDF inspection confirmed the narrow two-paper claim ceiling before coding.
- Stage 1 is modular exact-Gaussian work. It does not re-label legacy TMCMC or response-level sampling as NUTS/HMC.
- To keep exact conditioning replayable under the two-hour cap while retaining the full proposed mean basis, the primary grid is 15 design-only channels (one X/Y/Z per physical region) by 87 frequency lines (2.5 Hz). Spatial folds are still coordinate-only k-medoids. This is a bounded selected-channel study, not evidence for all 111 channels.

## Open ambiguities

None blocks execution. Missing spectral metadata or an inability to preserve axis/region balance is surfaced as YELLOW. Missing coordinates/axis labels or source-hash mismatch is RED.

## 2026-07-22 — Preflight serialization restart

- The first S0–S3 computation reached JSON serialization but failed because two gate booleans retained NumPy scalar type. No gate result was read or interpreted and no `synthetic_results.json` was written.
- The incomplete `synthetic_conditionals.npz`, the prior deterministic known-answer output, and the empty synthetic log were quarantined under `qa/preflight_v1/`.
- The repair only casts those two boolean expressions to built-in `bool`. The workspace was then re-frozen with an empty `out/`, the source manifest was regenerated, and the checker RED canary was rerun before the valid science attempt.
