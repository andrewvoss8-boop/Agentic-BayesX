# Known Failures And Risks

- No strict convergence failure was detected by the final all-flight diagnostic gate.
- Early cumulative GIF prefix fits 1-3 had divergence warnings; see `nuts_diagnostics.json` and the packet warning before treating early-frame intervals as clean.
- Full flight response PSD observations are absent from the setup dataset; response PSD bands are posterior predictive.
- The round-2 script focuses on the priority full-data likelihood and does not rerun a peak-feature likelihood comparison.
