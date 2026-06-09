# ShockSat Opus Continuation — Priority Deliverables

Human ask (Andrew, 2026-06-09): "review the work Codex has been doing for shocksat
and the problem framing/assumptions. Start a new folder where you continue shocksat
work as OPUS. Make any tweaks you deem necessary and continue on the path that best
supports the project vision and goals."

Interpretation: (1) audit Codex's run + framing; (2) create an Opus workspace;
(3) fix what is wrong; (4) advance the real-data StatFEM bridge per project vision.

| ID | Priority ask | Interpretation | Acceptance evidence | Status |
|---|---|---|---|---|
| O1 | Review Codex's work + framing/assumptions | Read decisions log, packet, framing; state what to keep and what is wrong, artifact-backed | `review_of_codex_run.md` | delivered |
| O2 | New Opus folder to continue shocksat | Scoped workspace, does not modify Codex's immutable run | `artifacts/reports/shocksat_opus_20260609/` | delivered |
| O3 | Tweaks I deem necessary | Fix the impact-FRF processing bug + wrong band; A/B vs Codex method | `scripts/opus_hammer_frf.py`, `opus_frf_summary.json`, `figures/opus_coherence_method_compare_ch1.png` | delivered |
| O4 | Continue on the best path for project vision | Set up the real FEM-vs-test correlation surface (SOL111) and recommend StatFEM v1 framing | `figures/opus_fem_vs_test_peaks.png`, `packet.md` (next-path), `decisions_log.md` | delivered |
| O5 | Checker + replay + runtime | Artifact-backed gates, one-command replay, runtime accounting | `scripts/check_opus.py`, `checker_report.json`, `run_all.sh`, `runtime.json` | delivered |

## Assumptions / ambiguities surfaced
- "Continue on the best path" is open-ended. ASSUMPTION (stated, needs confirmation):
  the best next step is the **10–400 Hz free-free modal StatFEM** with pyro shock as
  held-out QOI. Building any posterior is deferred for human approval.
- Sensor calibration taken from the instrumentation workbook as-is; calibration
  uncertainty not yet modeled.
- SOL111 force-amplitude unit normalization (g/lbf vs g/N) is UNREAD → no FEM-vs-test
  magnitude likelihood claimed this run.

## Failures / gaps (none silently hidden)
- No StatFEM posterior, no NUTS — by design; flagged as deferred, not done.
- 4-hit ensemble coherence is statistically weak; flagged as a limitation, not passed off.
