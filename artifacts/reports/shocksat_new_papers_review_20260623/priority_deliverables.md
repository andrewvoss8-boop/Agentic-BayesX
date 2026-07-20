# Priority deliverables - new ShockSat-applicability paper review

Restating Andrew's ask in my words, with delivery locations. This is a literature-to-runner triage, not a claim that any method has improved ShockSat metrics yet.

| # | Priority ask | Interpretation | Delivered in | Status |
|---|---|---|---|---|
| P1 | Review the three newly pulled papers in `references/pdfs/`. | Use the local PDFs as source of truth, not only the user summaries or abstracts. | `paper_applicability_review.md`, `bibliography.md` | done |
| P2 | Consider applicability to the project vision. | Judge fit to the current ShockSat vision: real dynamic structures, held-out trust tests, response-limit/PSD-envelope QOIs, model-form error, unknown/known forcing, and practical aero workflow. | `paper_applicability_review.md` | done |
| P3 | If at least moderately applicable, make a runner prompt to explore application to ShockSat. | Create prompts for all three, but rank them: sequential statFEM and latent-force/BNN are higher-priority; multi-level wing ROM is lower-priority/guarded. | `runner_prompts/*.md` | done |
| P4 | Keep the work artifact-backed and honest. | Add decisions, source boundaries, and a lightweight checker with green/yellow/red status. | `decisions_log.md`, `check_review.py`, `checker_report.json` | done |

Acceptance notes:
- No prompt may claim ShockSat improvement without a future runner's held-out score and checker output.
- If a paper is synthetic-only, offline-only, or lacks direct stress/flight validation, the prompt must carry that caveat.
- NUTS/HMC remains the default for Bayesian parameter-updating work; non-MCMC filtering or empirical-Bayes hyperparameter fitting must be explicitly labeled.

