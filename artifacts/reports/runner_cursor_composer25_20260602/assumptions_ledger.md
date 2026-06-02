# Assumptions Ledger (runner inference)

- **PSD-space dB convention**: factor = 10 ** (dB / 10) — The smoothline, flight-to-flight, build-to-build, and sensor-noise values are PSD/power quantities.
- **Smoothline PSD points**: [[20.0, 0.01], [100.0, 0.1], [750.0, 0.1], [2000.0, 0.001]] — Defines the vibe-test input spec by log-log interpolation.
- **Flight-to-flight variability**: 3.0 — Known forcing variability; fixed rather than learned.
- **Build-to-build initial variability**: 1.5 — Initial generated scale; future NUTS/HMC model should learn this scale.
- **Sensor-noise initial variability**: 0.75 — A concrete starting value is needed for preview data; future NUTS/HMC model should learn it.
- **Flight forcing mean offset**: -6.0 — Mean flight forcing PSD is lower than the pre-data dynamics engineer's original forcing function.
- **Flight forcing covariance**: Matérn-3/2, ell=0.08 — Use Matérn, not RBF, with tight frequency correlation.
- **NUTS/HMC status**: not implemented in this setup — Avoid claiming posterior updates before a checked NUTS/HMC implementation exists.
- **Inference sampler**: NumPyro NUTS (HMC) — Project rule requires NUTS/HMC for claimed posterior inference.
- **Flight likelihood form**: scalar tray/interface 3*GRMS only — Dataset stores flight QOI summaries, not full flight PSD curves.