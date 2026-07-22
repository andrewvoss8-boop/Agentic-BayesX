# Decisions log

## 2026-07-22 — Scope and isolation

- This task authors and audits a runner card; it does not dispatch or execute science.
- The supplied Task Card D, its proposed workspace, the closure-brief workspaces, frozen inputs, and immutable checkers will not be modified.
- New artifacts live only in this directory, apart from the required append-only task-plan entry in the repository `notes/todo.md`.

## 2026-07-22 — Scientific framing

- Literature claim ceiling: the learned frequency×location mean is absent from the two papers checked; no literature-wide novelty claim is allowed.
- Febrianto's nonsensor prediction is not described as kriging a discrepancy posterior mean; its published mean uses the conditioned FE state and adds new-location discrepancy through covariance.
- The independent card uses a staged modular-to-joint design so GP conditioning and a learned mean are compared under a shared covariance before any joint NUTS run.
- A learned mean is reported conditionally as `E[H beta | training]`; analytic marginalization may not erase the distinction between mean and low-rank covariance.

## 2026-07-22 — Human removes approval pauses

- Andrew directed the independent card to remove the requirement for human review and implement the best recommended path using agent judgment.
- Interpretation: revise Card E into an autonomous runner artifact; do not launch it in this card-editing task and do not interfere with Task Card D's separate run.
- The former Stage 1 human checkpoint becomes an immutable automatic decision gate with numerical proceed/stop criteria. Post-run scientific adoption remains human judgment, but it does not pause execution.
