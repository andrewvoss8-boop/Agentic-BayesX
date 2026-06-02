# Known failures / limitations

- Flight likelihood uses scalar 3*GRMS QOIs only.
- Modal/PSD subsampling stride 4/4.
- Forcing QOI uncertainty approximated via MC sigma.
- Some hierarchical build latents show poor R-hat / low ESS (see nuts_diagnostics.json).
- Divergences full=0 peak=0.