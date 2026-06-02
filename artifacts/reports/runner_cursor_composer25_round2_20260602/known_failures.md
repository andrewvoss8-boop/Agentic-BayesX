# Known failures / limitations

- NUTS converged (all variables): **True**. See nuts_diagnostics.json before using intervals.
- Flight likelihood uses scalar 3*GRMS only; interface PSD bands are posterior predictive, not per-flight observed PSD curves.
- Sequential GIF uses 400/400 per frame (lighter than primary 1000/1000).
- 6 dB flight forcing offset is a project assumption, not a GEVS qualification margin.
