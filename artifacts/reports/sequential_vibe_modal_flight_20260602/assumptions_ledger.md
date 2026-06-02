# Assumptions Ledger

| Assumption | Value | Units | Source | Rationale | Sensitivity |
|---|---|---|---|---|---|
| PSD-space dB convention | factor = 10 ** (dB / 10) | dimensionless PSD multiplier | Human clarification on 2026-06-02 | The smoothline, flight-to-flight, build-to-build, and sensor-noise values are PSD/power quantities. | High |
| Smoothline PSD points | [(20.0, 0.01), (100.0, 0.1), (750.0, 0.1), (2000.0, 0.001)] | Hz, g^2/Hz | Human research plan | Defines the vibe-test input spec by log-log interpolation. | High |
| Flight-to-flight variability | 3.0 | dB, PSD space | Human research plan | Known forcing variability; fixed rather than learned. | High |
| Build-to-build initial variability | 1.5 | dB, PSD space | Human research plan | Initial generated scale; future NUTS/HMC model should learn this scale. | High |
| Sensor-noise initial variability | 0.75 | dB, PSD space | Setup assumption | A concrete starting value is needed for preview data; future NUTS/HMC model should learn it. | High |
| Flight forcing mean offset | -6.0 | dB, PSD space | Human research plan | Mean flight forcing PSD is lower than the pre-data dynamics engineer's original forcing function. | High |
| Flight forcing covariance | Matérn-3/2, ell=0.08 | natural log frequency | Human research plan | Use Matérn, not RBF, with tight frequency correlation. | High |
| NUTS/HMC status | not implemented in this setup | categorical | Project sampler rule | Avoid claiming posterior updates before a checked NUTS/HMC implementation exists. | High |
