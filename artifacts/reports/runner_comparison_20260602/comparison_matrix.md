# Scope Coverage Matrix — 2026-06-02

Lead first pass from file inventories + reports. Cells: yes / partial / no / not-NUTS / gap.
To be confirmed/corrected by the technical + checker subagents.

| Required scope item | Cursor 2.5 | Opus 4.8 | Codex 5.5 |
|---|---|---|---|
| Ran in isolated workspace | yes | NO (master repo) | NO (master repo) |
| PSD-space dB (10**(dB/10)) | partial (verify) | partial (verify) | partial (verify) |
| Dome=m1, tray=m2 | yes | yes | yes |
| Tray vibe + dome modal + coupled modal stages | partial | partial | yes (figure shows all 3) |
| First flight + 10 later builds/flights | yes (11) | yes (11) | yes (11) |
| Learn build-to-build variability | yes (sigma_build) | yes (sigma_build) | yes (sigma_build) |
| Learn sensor-noise scale | yes | yes (poor in peak run) | yes |
| Flight-to-flight fixed at 3 dB | yes | yes (MC scatter from fixed GP) | yes |
| Matérn forcing GP (not RBF) | verify | verify | verify |
| Full FRF/PSD vs peak-feature likelihood compare | yes | yes (both NUTS runs) | yes |
| NUTS/HMC sampler | real NUTS, 2 chains | real NUTS, 4 chains | custom PyTorch HMC (not NUTS) |
| Diagnostics: divergences | 0/0 | 0/0 | 3/0 |
| Diagnostics: R-hat converged (<1.05) | NO (up to 1.83) | yes on marginals (verify latents) | NO (up to 4.57) |
| Diagnostics: ESS healthy | NO (ess≈3) | yes (>=942) | NO (down to ~6) |
| 95% & 99% input spectra | partial (static) | yes (static) | yes (static) |
| Tray 3*RMS / 3*GRMS QOI intervals | yes | yes | yes |
| **KEY plot: per-flight interface PSD mean/95/99 vs spec (GIF)** | NO | NO | NO |
| Flight 3*GRMS overlaid vs vibe-test RMS | NO | NO | NO |
| All 10 forcing draws vs +6 dB mean | NO | NO | NO |
| All figures have legends | verify | verify | NO (≥1 panel missing) |
| Frequency-grid choice justified | stride 4/4, no peak-res check | subsample, verify | not located |
| Runtime tracked | NO | partial (sampler only) | ~18 min (human-reported) |
| Human-review packet (packet.md) | yes | yes | yes |
| manifest.json | yes | yes | yes |
| Immutable checker hashes OK | yes | yes | yes |
| Candid known_failures.md | yes (brief) | yes (detailed) | yes |

## Headline reads (lead, pending reviewer confirmation)
1. **Opus** has the strongest sampler discipline and the most candid limitations writeup; main gaps
   are the missing key plot and confirming raw-latent convergence.
2. **Cursor** ran real NUTS but under-resourced; biggest concern is `nuts_active: true` + checker
   pass despite non-converged latents (overclaim risk the checker missed).
3. **Codex** was honest that it did not run NUTS; main concerns are non-convergence, the no-legend
   figure, and coarse frequency spacing.
4. **All three** miss the human's headline deliverable: the evolving interface-PSD-vs-spec plot/GIF,
   the vibe-RMS overlay, and the 10-forcing-draws overlay.
5. **All three** non-isolation (2 of 3) + no convergence gate + no runtime tracking are HARNESS
   problems more than runner problems.
