# Priority deliverables — ShockSat advisor closure report

| Priority ask | Interpretation and acceptance | Delivery |
|---|---|---|
| Explain what was done and why | Separate the converged modal-frequency Bayesian FEM update from non-converged response-level StatFEM attempts; define the actual likelihood, priors/discrepancy roles, NUTS diagnostics, data splits, and study sequence for a Bayesian expert new to ShockSat. | Report §§1–3; definitions/data table; method schematic |
| Explain why the original objective was not achieved | Use Task Card A to distinguish under-identification, the data-supported modal residual floor, response-likelihood multimodality, and predictive calibration/width tradeoffs. Do not call the working twin a joint StatFEM posterior. | Report §§4–6; A1–A5 figures/tables |
| Explain the agentic-remodeling pivot | Define current agentic remodeling as a bounded propose–verify–diagnose–revise search over genuine model-form edits; state the preregistered comparison and that this pilot failed to demonstrate an agent advantage. | Report §7 and future-work note |
| Show the useful FRF result simply | Two held-out channels only: DAQ 20 and DAQ 24, with measured data, original FEM, updated median, parameter-only 5–95% band, and total 5–95% predictive band. No hit-quality shading or extra diagnostic curves. | Figure 3 |
| Ask for closure guidance | Retain four concise questions focused on the remaining month, personal lessons, technical contributions, and whether the original problem direction was sound. | Final section |
| Keep the account auditable | ≤9 pages, a clear research sequence, one definitions table containing only terms used later, one work-products-and-limits table, ≥25 numeric source checks, prior DOCX byte preservation, figure legibility/alt text, and a checker that preserves the scientific caveats internally. | `check.py`, checker report, `packet.md`, rendered-page QA |

## 2026-07-22 advisor-context revision

| Priority ask | Interpretation and acceptance | Delivery |
|---|---|---|
| Start from Ilias's actual context | Assume his last project context is the “Stress Testing StatFEM” proposal and his instruction to build/evaluate, identify gaps, and suggest improvements. Explain the research sequence before any result. | Opening two pages and revised method map |
| Remove adversarial posture | Delete “claims I will defend,” “defensible contribution,” evidence-ceiling language, and every GREEN/YELLOW/RED reference from the advisor-facing DOCX/Markdown/figures. | Report-wide prose and figure-caption revision |
| Preserve scientific honesty in normal language | State which samplers converged, which did not, the worst diagnostics, and which intervals cannot be trusted without traffic-light shorthand. | Modal sensitivity, whole-FRF, and limitations sections |
| Ask for direction, not adjudication | Present the work as an understandable account of what Andrew tried and why, then ask Ilias how to use the final month and which lessons/contributions merit documentation. | Opening purpose and closing questions |

No priority interpretation remains ambiguous after Andrew's 2026-07-22 instructions. The report is an advisor update, not a decision-request memo and not an industry-readiness claim.

## 2026-07-22 user-comment rebuild in isolated `_sol` copy

| Priority ask | Interpretation and acceptance | Delivery |
|---|---|---|
| Preserve concurrent work | Do not alter the user-edited source DOCX; build a separate `_sol` DOCX with independent builder, figures, outputs, and checker. | `_sol.docx`; source SHA lock; G2 |
| Explain all methods before results | Replace the single modal-likelihood lead with a ten-row chronology covering modal, MAC, Beck, whole/complex FRF, damping, modular, M2/IFT, evidence, and Schneider options. | Page 2; G4 |
| State why center and width fail | Give the implemented log-amplitude equation; explain the zero-centered discrepancy's mean/covariance effect; state that a structured nonzero mean could move the center but was not implemented. | Page 3; G5 |
| Broaden FRF evidence | Use 25×31 summary evidence and four rule-selected channels spanning improvement, typical improvement, persistent miss, and deterioration; retain only five visual encodings. | Page 4; Figure 1; G6 |
| Report measured load evidence only | Show shear X/Y only and define FEM + 6 dB, coverage, width, CRPS, and log-uniform/linear-uniform/Gaussian-95% conventions. | Page 5; G7 |
| Ask one personal closure question | Replace prescriptive closeout options with Andrew's request about lessons, problem choice, and contributions worth documenting. | Page 7; G9 |

All ten Word comments and both direct edits are mapped into the rebuilt content. The generated `_sol` DOCX has
no unresolved Word comment parts; the source comment state is intentionally untouched.
