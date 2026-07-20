# references_and_quotes.md — verified verbatim quotes + reference gate

All PIFT quotes below were extracted directly from the local PDF `references/pdfs/2301.07609v5.pdf` with PyMuPDF
(fitz) and are reproduced VERBATIM (page numbers from the PDF text layer). Math symbols are transcribed as the
text layer renders them; see the PDF for typeset equations.

## PIFT — Alberts & Bilionis (2023), "Physics-informed information field theory…", arXiv:2301.07609v5

**The asymptotic collapse result (p17), verbatim:**
> "Under fairly general assumptions (iid measurements, continuous likelihood as a function of the parameters),
> if σr is kept fixed while the number of collocation points n goes to infinity, then the 'posterior
> distribution of [the field parameters] θ [conditional on the energy parameters λ] approaches normality with
> mean θ0 and variance (nJ(θ0))−1'"

> "In particular, notice that as the number of collocation points goes to infinity the posterior uncertainty
> over θ goes to zero."

> "In other words, the field posterior in B-PINNs collapses to a single function irrespective of the value of σr
> as n →∞."

> "However, a collapsing field posterior is undesirable in cases of model-form uncertainty or in ill-posed
> problems."

**Conclusion restatement (p25), verbatim:**
> "Using results from Bayesian asymptotic analysis we showed that B-PINNs yields field posteriors that collapse
> to a single solution as the number of collocation points goes to infinity."

**Symbol key (from the same section):** `n` = number of collocation points; `σr` = the B-PINN residual
(likelihood) standard deviation — a "fictitious"/modeling residual scale enforcing the PDE, NOT a physical
measurement noise; `θ` = the field parameters being inferred; `J(θ0)` = the per-point Fisher information at the
true parameter; the posterior variance `(nJ(θ0))⁻¹ → 0` as `n → ∞`. THIS is the Fisher-information-∝-n
mechanism we map to our iid FRF likelihood.

## IFT — Hao & Bilionis (2023/24), "An information field theory approach to Bayesian inversion", arXiv:2306.02150
The original Information Field Theory (IFT) inversion framework PIFT builds on (field prior + likelihood +
partition function Z). Cited as the IFT foundation for the residual-field/partition-function machinery the
collapse argument uses. (No collapse-specific quote required for the card; PIFT carries the collapse result.)

## Reference gate (AGENTS.md Reference and Standards Gate) — comparison targets for this study
- **PIFT** arXiv:2301.07609 (Alberts & Bilionis) — the posterior-collapse result we test for (above).
- **IFT** arXiv:2306.02150 (Hao & Bilionis) — IFT foundation.
- **statFEM** `references/pdfs/statFEM.pdf` (Girolami et al. 2021) — the statistical-FEM discrepancy framework
  our arms instantiate (additive model-form discrepancy on the FE solution + measurement noise).
- **Duffin 2020** `references/pdfs/2020_Duffin_Statistical_finite_elements_for_misspecified_models.pdf` —
  statFEM under misspecification (model-form error), directly relevant to the "genuine model-form error" case.
- **Plumlee 2017** `references/pdfs/Bayesian_calibration_of_inexact_computer_models_Plumlee_2017.pdf` — orthogonal
  discrepancy construction (project discrepancy off the calibration-parameter sensitivity span) = the basis of
  the M3 orthogonal-Schneider arm.
- **Kennedy–O'Hagan 2002** `references/pdfs/KennedyOHagan_2002 (1).pdf` — calibration + model discrepancy
  (the identifiability confounding between θ and discrepancy this study lives inside).
