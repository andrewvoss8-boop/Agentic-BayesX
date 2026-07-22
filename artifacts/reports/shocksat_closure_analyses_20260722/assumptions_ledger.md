# Assumptions ledger — Task Card A closure analyses

All analyses run on frozen artifacts; the physics assumptions of the predecessors are INHERITED, not
re-decided. This ledger lists (a) inherited assumptions this study depends on, (b) new numerical choices
made here. Sensitivity priority: H = could change a conclusion, M = could change a number, L = cosmetic.

## Inherited (frozen; source hashed in source_manifest.json)
| # | Assumption | Value / units | Source | Sens. |
|---|---|---|---|---|
| I1 | θ prior: 9 part-group stiffness multipliers, log θ ~ N(0, 0.25²) i.i.d. (dimensionless, median 1) | σ_log = 0.25 | modal twin ledger A8, `run_nuts.py` | H (A1 whitening; A2) |
| I2 | Reference σ_f prior | HalfNormal(0.05), log-frequency units | `run_nuts.py` | H (A2 is exactly this sensitivity) |
| I3 | Modal likelihood: 18 paired log-frequencies, Normal, no MAC term | modes: card list, Hz | `run_full.py` | M |
| I4 | Mode tracking: stop-gradient argmax overlap vs nominal eigenvectors | — | `run_nuts.py` | M (documented non-differentiable-pairing handling) |
| I5 | Net-CG QOI model: 74-mode reduced, ζ=0.01 uniform, tray z≥55, FGRID 400 linear pts 45–260 Hz | ζ dimensionless, f Hz | `netcg_qoi.py` | H for A3 levels, L for A3 comparisons (shared by all methods) |
| I6 | Truth-ensemble tiers: measured 1%/0.35, unmeasured 6%/0.80 (freq sd / log-amp sd) | dimensionless | `netcg_qoi.py` | H — this is why normal-Z is synthetic self-consistency only |
| I7 | FEM+6 dB incumbent band = nominal ×/÷ 10^(6/20) | ±6 dB | `bakeoff.py` | M |
| I8 | Per-drive answer key: LSQ complex modal participation, measured modes only, ridge 1e-3, one global gain per drive | — | `heldout_drive.py` | M |
| I9 | Whole-FRF iid likelihood arm (θ-only): log10|H1| on 45–400 Hz, thinning every 2nd bin ≤40 channels, Galerkin sub-basis F_SUB=450 Hz | dex, Hz | `arm_b_nuts.py` (D10/D11) | H for A4 — A4 profiles THIS likelihood |
| I10 | Measured data of record: processed multiref H1 caches (111 ch × 105 pts 45–260 Hz; wide 45–500 Hz); raw extract deleted | g/lbf etc. per cache meta | 2026-07-22 probe, memory.md | H (unfixable; disclosed) |
| I11 | Phase diagnostic context: single-hit measured-vs-model phase, 46 channels, 12 matched modes | dimensionless | `phase_likelihood.json` | L (provenance only) |

## New numerical choices (this study)
| # | Choice | Value / units | Rationale | Sens. |
|---|---|---|---|---|
| N1 | A1 bootstrap: circular block bootstrap WITHIN each 1000-draw chain segment, block length 40 draws, 1000 resamples, seed 0 | draws | Stored convergence_full.json: min ESS 232 over 4000 pooled draws ⇒ worst integrated autocorrelation time τ̂ ≈ 4000/232 ≈ 17 draws; block = 2×τ̂ ≈ 34, rounded to 40 so resampled blocks are approximately independent; blocks never span a chain boundary (pooled draws are chain-ordered 4×1000) | M |
| N2 | A1 eigen-decomposition on sample covariance with N−1 denominator | — | standard unbiased | L |
| N3 | A2 NUTS settings: warmup 1000, draws 1000, 4 chains, target_accept 0.9, dense mass, max_tree_depth 8, seeds 42 (reference) / 101,102,103,104 (variants) | — | identical to frozen twin (D21) so the reference rerun is an apples-to-apples reproduction | M |
| N4 | A2 known-answer tolerance: σ_f median within ±0.005 (abs, log units) of stored 0.046; θ medians within 3× pooled MC standard error | — | MC error of a median over 4000 draws with ESS>2000 | H (gate) |
| N5 | A3 CRPS ensemble sizes: statFEM & param-only n=60 θ-draws (matching `heldout_drive.per_drive_band` n_theta), envelope conventions closed-form/1000-sample | — | match the stored band machinery draw count | M |
| N6 | A3 CRPS FEM+6 dB primary convention: log-uniform between edges; sensitivities: linear-uniform, Gaussian(95%) | — | an envelope states a range, not a density; log-uniform is the least-informative reading in the band's native dB units | H (convention sensitivity reported) |
| N7 | A4 grid: 41 log-spaced points per parameter over exp(±1.96·0.25); nuisances profiled by L-BFGS-B, multi-start (3 starts), gradient tol 1e-8 | dimensionless | card minimum; multi-start guards inner non-convexity | M |
| N8 | A4 sensitivity-based parameter choice: energy-weighted RMS of finite-difference d log10|H|/d log θ_g at θ=1, step 0.01 in log θ | dex | cheap, deterministic, documented | M |
| N9 | Block-bootstrap and NUTS seeds fixed and recorded in outputs | — | replayability | L |

## Data counts (AGENTS gate)
One flight article; one modal survey campaign. A1/A2: 18 paired modal frequencies (single test).
A3: 5 drives × 111 channels × 105 freq pts measured H1 (shear answer keys reconstructable per drive);
truth ensemble n=200 synthetic (normal-Z ONLY self-consistency). A4: measured H1, thinned per I9.
No flight-to-flight, build-to-build, or test-to-test variability is modeled anywhere (single article,
single campaign) — inherited limitation, restated in the packet.

## Uncertainty taxonomy
Parameter uncertainty: θ posterior (A1, A2, A3 param-only). Observation noise + model discrepancy:
σ_f pools BOTH for modal frequencies (A2 tests its prior); tier amplitudes (I6) are the response-level
discrepancy model. Forcing uncertainty: global gain nuisances (A3 per drive, A4 profiled). Aleatory /
build variability: NOT modeled (single article). Boundary condition: fixed (inherited twin).
