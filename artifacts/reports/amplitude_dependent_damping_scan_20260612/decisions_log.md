# Decisions Log

## 2026-06-12 -- Triage, Not Final Nonlinear ID

Decision: Treat the human question as a reproducible triage screen for amplitude-dependent damping/hysteresis across three existing datasets.

Rationale: The folders contain heterogeneous data products: MPL has raw time-history CSVs, suspended panel has mostly frequency-domain LDV results, and ShockSat has archived/preprocessed modal and shock/hammer assets with known channel-map and coherence caveats. A single full nonlinear identification method would not be valid across all three without new metadata and test planning.

Assumption: If a dataset lacks repeated input levels or calibrated paired force-response histories, the honest result is "inconclusive," not "linear."

## 2026-06-12 -- Evidence Ranking

Decision: Rank evidence strength as:
1. repeated calibrated force-response or response-only ringdowns at different amplitudes;
2. paired force/response FRFs at multiple drive amplitudes;
3. response-only repeated events with stable mode extraction;
4. single FRF/coherence or modal-shape products only.

Rationale: Amplitude-dependent damping and hysteresis are nonlinear claims. They require amplitude contrast and a way to separate damping changes from forcing, boundary-condition changes, clipping, and windowing artifacts.
