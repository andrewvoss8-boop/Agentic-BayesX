# Review todo — statfem_real_validation_20260617

Goal: review the current folder for correctness errors in the NASA ShockSat Bayesian FEM-updating validation.

Priority checks:
- Compare headline claims in `packet.md`, summaries, and decks against `checker_report.json` and result JSONs.
- Audit core code paths for data leakage, scoring/provenance mistakes, wrong sensor/data hygiene, and sampler-labeling issues.
- Verify replay/checker behavior where feasible without modifying immutable checker logic.
- Surface findings with artifact paths, worst-case numbers, and green/yellow/red framing.

Open ambiguity:
- The folder contains both the original Card A validation and later Card C follow-on studies; this review treats both as in scope and flags any claim whose status changed later in `decisions_log.md`.
