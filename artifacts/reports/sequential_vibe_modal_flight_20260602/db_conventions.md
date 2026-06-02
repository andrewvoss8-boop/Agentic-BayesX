# PSD-Space dB Conventions

All dB values in this setup are interpreted in PSD/power space:

`factor = 10 ** (dB / 10)`

| Item | Value | Meaning |
|---|---:|---|
| Flight-to-flight forcing variability | 3.0 dB | Known PSD-space GP marginal sigma; not learned. |
| Build-to-build initial variability | 1.5 dB | Initial PSD-space scale used to generate build effects; intended to be learned later. |
| Sensor noise initial variability | 0.75 dB | Initial PSD-space sensor/noise scale; intended to be learned later. |
| Flight mean forcing offset | -6.0 dB | Mean flight force PSD is 6 dB below the original force PSD behind the test spec. |

For complex FRFs, PSD is proportional to `|FRF|^2`, so a PSD-space multiplier is applied as the square root multiplier on complex FRF amplitude.
