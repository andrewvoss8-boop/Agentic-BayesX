# docs/report — Central Reporting Hub

Purpose: a single, durable place that **logs everything being done** so an
end-of-summer report can be assembled without re-reading the whole repo or
relying on chat memory. This is a reporting/index layer, **not** a new source of
truth — every entry points back to the canonical artifact that proves it.

## Files
- **`project_log.md`** — the master logbook. One indexed, status-tagged row per
  work thread, plus timeline, deliverables catalog, cross-cutting findings, and
  the harness/rule-evolution record. **This is the file you maintain.**
- `README.md` — this file (what the hub is and how to keep it honest).

## Source-of-truth hierarchy (do not duplicate, link)
The log is an *index over* these canonical files; if they ever disagree, the
canonical file wins:
- `AGENTS.md` — rules and gates (canonical).
- `notes/runs.md` — chronological run log (command + checker result + metrics).
- `notes/memory.md` — lead CURRENT STATE / last decision.
- `notes/lessons-learned.md`, `notes/project_vision.md`, `notes/todo.md`.
- `artifacts/reports/<workspace>/packet.md` + `check.py` / `checker_report.json`
  — the per-study evidence and pass/yellow/red status.
- `<workspace>/decisions_log.md` — per-runner decision trail.

## Honesty rules for this log (inherited from CLAUDE.md / AGENTS.md)
1. **No status stronger than the checker output.** Copy GREEN / YELLOW / RED and
   the green/yellow/red counts straight from each study's `checker_report.json`.
   "Complete pending review" is not "accepted."
2. **NUTS "converged" only with all-variable diagnostics.** Never write
   "converged" for a run that failed the convergence gate; note worst R-hat / ESS.
3. **Every claim links to a file.** If there is no artifact, the row says
   "see workspace" — do not invent metrics.
4. **Additive.** This hub does not edit rules, checkers, or sampler standards.

## How to maintain (each time a thread advances or closes)
1. Update or add the thread's row in `project_log.md` §3 (status + headline + links).
2. If it produced a replayable artifact, confirm `notes/runs.md` has the
   command + checker result, then point to it.
3. Move closed/abandoned threads to the relevant status group; keep the timeline current.
4. Keep it high-signal (target the index < ~1 screen per thread).
