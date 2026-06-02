# Priority deliverables — Cursor Composer 2.5 round 2

## Human priority (restated)

1. KEY: coupled interface acceleration RESPONSE PSD (g^2/Hz), mean + 95% + 99% bands vs smoothline test spec, one frame per flight, animated GIF, log-frequency axis.
2. Forcing: all flight forcing draws overlaid on original forcing PSD (+6 dB above flight mean; project assumption, not GEVS margin).
3. Scalar: flight tray 3*GRMS sequence vs vibe-test references (43.9 g first-build, 28.3 g smoothline); log-y; PSD envelope check remains primary.

## Ambiguity resolved

- Round-1 "input spectra" meant forcing INPUT; round-2 priority is interface acceleration RESPONSE PSD in the coupled flight system.
- Test spec overlay uses `smoothline_psd_g2_per_hz` (tray vibe qualification spec) as the envelope reference for the interface response comparison per task card / GEVS-style envelope question.

## Acceptance mapping

| Priority | Artifact |
|---|---|
| 1 | `figures/07_interface_response_psd_vs_spec_evolution.gif`, `figures/10_interface_response_psd_vs_spec_final.png` |
| 2 | `figures/08_forcing_overlay_discrete_flights.png` |
| 3 | `figures/09_tray_3grms_vs_vibe_test_refs.png` |
| Resolution | `resolution_sensitivity.json`, `figures/11_resolution_peak_zoom.png` |
| NUTS gate | `nuts_diagnostics.json` (all variables incl. `dome_build_raw`, `tray_build_raw`) |
| Runtime | `runtime.json` |
