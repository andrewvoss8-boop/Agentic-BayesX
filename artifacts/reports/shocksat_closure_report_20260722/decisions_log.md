# Decisions log — ShockSat advisor closure report

## 2026-07-22 re-grounding and human direction

- Task Card A is complete with checker verbatim: **OVERALL YELLOW {GREEN: 14, YELLOW: 1, RED: 0}, exit 0**. Its single YELLOW is retained: three of five sigma_f prior-sensitivity variants did not converge; their intervals remain not trustworthy.
- This starts Task Card B. It performs document synthesis and figure regeneration only; it will not run new inference, calculate new performance metrics, or strengthen claims.
- The report must distinguish (1) the converged NUTS posterior for modal-frequency Bayesian FEM updating from (2) response-level StatFEM/whole-FRF attempts that did not converge.
- The retained working-twin result is a **two-stage modular predictive construction**: modal-frequency NUTS parameter draws followed by an observed-channel-estimated marginal log-amplitude discrepancy transferred to held-out channels. It is not a jointly converged whole-FRF StatFEM posterior.
- Figure 5.4 is replaced by a two-panel held-out FRF figure with only the measured FRF, original FEM, updated median, parameter-only 5–95% interval, and total 5–95% predictive interval. DAQ 20 is the improving channel; DAQ 24 is the persistent-miss channel. Hit-quality shading and other method curves are prohibited.
- Agentic remodeling is future work in this advisor brief. It means a bounded propose–verify–diagnose–revise loop over genuine mesh/model-form edits, with immutable mechanical/verifier controls and a preregistered agent-versus-random comparison. The completed pilot failed to demonstrate an agent advantage.
- The advisor's requested help is closure guidance for the final month: identify the right personal lessons, decide whether the original problem/direction was well chosen, and document defensible contributions to the field and lab.

## Document design and scope

- Use the documents skill's `standard_business_brief` design preset with the `memo_masthead` header pattern, adapted to a technical advisor brief. This supports a compact ≤9-page document without a decorative cover.
- Use a muted navy/teal/amber palette, direct labels, and restrained tables. A YELLOW label is a scientific caveat, not a success label.
- Define project abbreviations and Bayesian quantities once in a single definitions/data table. Use one claims-and-limits table and at most six defended claims.
- Keep `remodelctl` to future-work context only and no more than three sentences. Runtime accounting remains in the repository, not the advisor document.
- Reuse only checker-backed numbers and repository-verified literature. Prior report DOCX files are immutable and will be SHA-256 locked before building.
- Tufte-lint advisory review: plot background fills are retained only where they encode the nested 5th–95th percentile bands; “FEM + 6 dB” is the name of the project baseline and no plotted axis uses dB. These are deliberate, documented deviations from the heuristic flags.

## 2026-07-22 D3 — advisor context and tone correction

Andrew rejected the reviewer-facing opening. Ilias's last context is the “Stress Testing StatFEM” proposal; he
does not know the later ShockSat experiment sequence or agentic-remodeling program. The advisor brief must
therefore explain what Andrew tried and why before it presents any findings. Remove the “claims I will defend”
section and all advisor-facing GREEN/YELLOW/RED language. This is a progress-and-direction conversation, not a
defense of claims. Preserve the underlying convergence failures, numerical diagnostics, and evidence limits in
plain technical language. Internal checkers keep the repository's required three-tier status; the advisor document
must not expose that harness vocabulary.

## 2026-07-22 D4 — remove unused internal labels from the advisor brief

S1, S3, and S4 appeared only in the definitions table and were never used to explain a method, result, or closure
choice. They are removed from the advisor-facing DOCX and Markdown because Ilias has no project context for the
internal study labels. The underlying acceptance criteria remain in the repository studies and checkers. IFT,
the model-form score, counts, bands, sampler diagnostics, and uncertainty terms remain because they are used later.

## 2026-07-22 D5 — execute user-comment rebuild in an isolated copy

Andrew approved the planned large-scale revision and asked that it be isolated because another agent is also
editing the source document. The user-edited DOCX at SHA-256
`e8e04f40bcc69c03634e5c6d94eb5beee64f5ebdcbe13f7882ab09f16ee01a8f` remains untouched. This work produces
`ShockSat_Bayesian_FEM_StatFEM_closure_brief_sol.docx` from a separate builder, figure directory, output
directory, and checker. The `_sol` brief will implement the ten Word comments and preserve the two direct edits.

## 2026-07-22 D6 — selective comparison with the Fable brief

Andrew asked for obvious improvements from the independently generated Fable brief. Keep the `_sol` structure:
context and method chronology before findings, nine pages, four rule-selected FRFs, measured shear only, and the
single closure request. Do not restore the deleted “I treated that as the research question” sentence, the
six-channel FRF panel, normal-Z appendix, or the result-first opening. Adopt four narrower improvements: an
illustrative location-by-frequency discrepancy-mean example; a proper-score/units definition of CRPS; a sharper
distinction between fully integrated marginal likelihood and the local-linear/type-II-ML evidence calculation;
and a short literature-positioning paragraph near the closure discussion.
