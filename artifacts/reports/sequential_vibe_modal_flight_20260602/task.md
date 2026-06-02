# Sequential Vibe/Modal/Flight Task

## Task

Set up a staged synthetic research problem for a rocket company that starts with a dome/tray model, a smoothline vibe spec, no test data, and then gathers tray vibe, modal, and flight data over multiple builds.

## Scope Of This Setup

This setup generates the PSD convention ledger, staged data schema, synthetic preview data, plots, and checker-backed packet. It does not run posterior inference and does not claim NUTS/HMC is active.

## Main Future Inference Questions

- How different are posteriors from full FRF/PSD likelihoods versus peak-frequency/peak-amplitude likelihoods?
- How much do tray vibe data, dome-only modal data, coupled modal data, and flight-only updates change `fn`, damping, interface acceleration spectra, and tray `3*GRMS` QOI?
- How much do repeated builds and flights help learn build-to-build variability and sensor noise?
