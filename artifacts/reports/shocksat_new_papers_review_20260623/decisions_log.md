# Decisions log - new ShockSat-applicability paper review

Workspace: `artifacts/reports/shocksat_new_papers_review_20260623/`.

## D0 - deliverable interpretation
Andrew asked for a review of three papers pulled into `references/pdfs/`, with runner prompts when the papers are at least moderately applicable to the ShockSat dataset. I interpret "applicable" as: the paper's contribution can be turned into a falsifiable ShockSat pilot with existing or already-pulled data, a held-out score, and a checker-backed caveat.

## D1 - source boundary
Primary source is the local PDF text under `references/pdfs/`:
- `Multi-level digital twin for real-time deformation and stress analysis of wing structures.pdf`
- `Statistical finite elements for sequential data synthesis in solid dynamics.pdf`
- `probabilistic digital twin for misspecified structural dynamical systems via latent force.pdf`

I used PDF metadata, page-level text extraction, and targeted page reads. `pdftotext` was unavailable; the bundled runtime had `pdfinfo`, `pypdf`, and `pdfplumber`. The latent-force paper contains slow figure/content streams, so I used targeted page reads with timeouts and relied on abstract/method/discussion/conclusion pages rather than full bulk extraction.

## D2 - current ShockSat state used for applicability
I judged applicability against the current ShockSat direction, not the older single-impact-only framing:
- Clean modal-hammer multi-reference data are now preferred over low-SNR impact taps.
- The current near-term QOI is held-out-sensor response PSD, smooth upper envelope, GRMS, and energy-weighted exceedance vs FEM+6 dB.
- Prior amplitude work found a held-out sensor shape ceiling; prompts must not claim multi-reference drive data alone solves held-out sensor amplitude.
- Frequency/modal updating is trustworthy; amplitude/stress/response-level claims require held-out QOI scoring.

## D3 - prompt policy
All three papers are at least moderately applicable, but not equally:
- Sequential statFEM for solid dynamics: HIGH applicability. It is the most direct statFEM extension for transient elastodynamics and data assimilation.
- Latent-force/BNN probabilistic twin: MODERATE-HIGH applicability. It targets model-form error and nonlinear/damping-like residuals, but is offline and demonstrated mostly on low/moderate-order systems.
- Multi-level wing digital twin: MODERATE-LOW applicability. Useful architecture for fast hierarchical ROM/submodel response or stress QOIs, but not a Bayesian/statFEM contribution and not directly validated against ShockSat stress data.

## D4 - status convention
The review artifact can be checker-clean while the scientific status remains YELLOW: every prompt is an exploration prompt, not evidence of ShockSat improvement. Checker yellow is reserved for source/exploration caveats, not broken deliverables.

