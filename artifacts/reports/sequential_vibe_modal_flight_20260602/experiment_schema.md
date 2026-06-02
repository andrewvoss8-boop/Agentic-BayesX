# Experiment Stage Schema

The schema is machine-readable in `experiment_schema.json`.

## Stages

1. `pre_data_dome_fem`: dome-only model response to a flat force PSD; scaled so dome response peak is 0.1 g^2/Hz.
2. `tray_vibe_test`: tray/load tested to the smoothline base PSD; first-build tray build effect and fresh sensor noise are included.
3. `dome_modal_test`: dome/source-only modal observation; same first-build dome effect and fresh sensor noise.
4. `coupled_modal_test`: dome plus tray modal observation; interface and tray impacts use the same first-build dome/tray effects.
5. `first_build_flight`: first build flight with fresh Matérn GP forcing sample and fresh sensor noise.
6. `later_builds_and_flights`: ten later builds, each with a tray vibe test and flight, no more modal tests.

## Learning Plan

Future NUTS/HMC inference should learn natural frequencies, damping, build-to-build variability scale, sensor-noise scale, interface acceleration spectra, and tray `3*GRMS` QOI. Flight-to-flight forcing variability remains fixed at 3 dB in PSD space.
