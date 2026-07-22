# Priority deliverables

| Priority ask | Frozen interpretation | Delivery |
|---|---|---|
| Separate GP conditioning from a learned mean | Compare E0 versus E1 with one identical training fit, then E2/E3 versus E1 under that same residual covariance. Store `E[H beta|train]` and `E[u_*|train]` separately. | `out/stage1_results.json`, numeric tables, figures 2–4 |
| Test transfer, not fitted-channel improvement | Use five frozen drive, spatial-cluster, frequency-core, and joint-transfer folds. Score independent folds, never dense bins as replicates. | `split_registry.json`, `out/stage1_results.json` |
| Control false positives and theta confounding first | Run S0–S3 for 20 deterministic seeds on the selected real sensor/frequency geometry; the automatic gate decides whether measured fitting is permitted. | `out/synthetic_results.json`, `automatic_decision.json` |
| Preserve the modal result and identify its limits | Use retained draws from the converged modal posterior modularly; reproduce modal strain-energy evidence and the realized-floor Fisher-information eigensystem before any per-parameter claim. | `out/known_answers.json`, figure 5 |
| Deliver an auditable terminal result | Immutable hashes, RED-on-empty canary, replay, runtime, packet, checker report, figures, and proposed closure-brief wording are required even on an automatic stop. | workspace root, `out/checker_report.json` |

No ambiguity changes the execution path. The card fixes the primary success bar at 2.0 dB median absolute-error reduction or 20% interval narrowing, subject to coverage and CRPS conditions. Scientific adoption after the run remains human judgment.
