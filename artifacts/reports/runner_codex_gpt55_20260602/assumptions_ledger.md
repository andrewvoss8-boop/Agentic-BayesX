# Assumptions Ledger

| Assumption | Value | Units | Source | Rationale | Sensitivity | Status |
|---|---|---|---|---|---|---|
| PSD-space dB convention | factor = 10 ** (dB / 10) | dimensionless PSD multiplier | Prompt/setup packet | All dB variability is applied in PSD/power space. | High | fixed |
| Dome/source coordinate | m1 | coordinate label | Prompt | Dome/tank/source is modeled as primary mass. | High | fixed |
| Tray/load coordinate | m2 | coordinate label | Prompt | Tray/load/secondary structure is modeled as secondary mass. | High | fixed |
| Smoothline PSD points | [(20.0, 0.01), (100.0, 0.1), (750.0, 0.1), (2000.0, 0.001)] | Hz, g^2/Hz | Prompt/setup packet | Defines tray vibe input by log-log interpolation. | High | fixed |
| Flight-to-flight forcing variability | 3.0 | dB PSD sigma | Prompt | Known forcing variability; fixed, not learned. | High | fixed |
| Forcing covariance | Matern-3/2 ell=0.08 | natural log frequency | Prompt | Required Matérn forcing GP; RBF not used. | High | fixed |
| Build-to-build variability | learned; synthetic truth 1.5 | dB PSD sigma | Prompt/setup packet | Hierarchical variability over builds. | High | inferred |
| Sensor-noise scale | learned; synthetic truth 0.75 | dB PSD sigma | Prompt/setup packet | Fresh multiplicative PSD/log-FRF sensor noise. | High | inferred |
| Flight mean force offset | -6.0 | dB PSD | Setup packet | Mean force PSD is below original flat force PSD. | High | fixed mean with learned global scale |
| Masses | [1.0, 0.6] | kg | Fresh 2DOF model | Toy dome/tray structural model. | Medium | fixed |
| Likelihood full-data choice | all generated frequency points | categorical | Runner implementation | Uses full log PSD and log FRF magnitude arrays. | High | fixed method choice |
| Likelihood peak-feature choice | soft peak/notch forward features | categorical | Runner implementation | Compares observed hard features to predicted transfer-function features. | High | fixed method choice |
