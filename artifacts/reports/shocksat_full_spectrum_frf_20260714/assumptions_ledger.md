# assumptions_ledger — ShockSat FULL-SPECTRUM FRF study (20260714)

Pre-registered. Columns: value/units, rationale, source, sensitivity priority (H/M/L = how likely a change
flips a decision). Dated addenda only; no silent edits.

## A1. Distillation / window (fixed processing constants — reused verbatim)
| item | value | source | sens |
|---|---|---|---|
| Sample rate fs | 250,000 Hz | raw .mat headers; `wforward.py` | L |
| Frame length N | 122,880 samples (0.49152 s) | `build_ypos_cache.py` / `multiref_frf.py` | L |
| Exponential response window end value | 0.05 (τ = 0.16407 s, σ_w = 6.095 1/s) | `realfrf.py` provenance (resolution run D1) | L |
| Pre-gap (impact sample) | 200 samples | `wforward.py` PRE_GAP | L |
| Window-added apparent damping | ζ_w(f) = 1/(2πfτ): 1.62% @60 Hz, 0.97% @100 Hz, 0.39% @250 Hz, 0.19% @500 Hz, 0.097% @1 kHz | resolution run (Gate K −2%…+0.005%) | M |
| Cache bin spacing Δf | 2.0345 Hz (=fs/N); bins are exact DFT bins | existing caches | L |
| Wide-band re-distillation | SAME N, window, channel set; ONLY the kept band changes: 45 Hz → certified ceiling (existing: 45–260 Hz) | card §4 | H |

## A2. Damping (measured data, never fitted in scores)
| item | value | source | sens |
|---|---|---|---|
| Survey per-mode ζ | 33 modes, `damp` field in PERCENT critical → ratio (÷100); range ≈0.09–1.6%, most ≈0.2–0.5% | `measured_modes.npz` (remesh 20260618); percent convention per damping run D7 | M |
| Mapping mode→ζ | frequency interpolation (end-clamped); modes above 257.6 Hz (survey top) get the survey BAND MEDIAN ζ | card §6 convention; interp-vs-nearest moved B2 by −0.0002 (resolution A3) | M (H above 258 Hz — no measured ζ there; sensitivity run planned) |
| ERA ζ | 4-band time-domain estimates, CROSS-CHECK only | `scratch_test07/era_result.npz` | L |
| A0 arm damping | flat 1% viscous (historical convention) | pinned bar definition | L |
| Structural damping η | 0 (viscous only, all arms) | resolution run A6 | L |

## A3. Bands and splits (pre-registered)
| item | value | source | sens |
|---|---|---|---|
| Legacy scored band | 45–260 Hz (data 46.8–258.4 Hz, 105 bins) | femlib BAND | L |
| Report bands | sub-200 Hz; 200–500 Hz; 500 Hz–certified ceiling | card §7 | — |
| Certified ceiling rule | force-referenced multi-hit coherence ≥ 0.6 (Q6 contract) | card §4 | H |
| Dev folds | LODO over {m_xpos_990x, m_zpos_990z, m_ypos_990y, m_zpos_900z} | card §3.5 | — |
| Vault | m_xy_990xy, entire drive, both bands; frozen; ONE read; 3rd program read (honest label) | card §3.5 | — |
| Coherence channel mask | median in-band coh ≥ 0.6 per channel per drive | wscore COH_MIN (continuity) | M |
| Query budgets | agent ≤80, random ≤80 scored dev queries | card §3.5 | — |

## A4. Priors and likelihood (arm B; numbers)
| item | value | rationale/source | sens |
|---|---|---|---|
| θ (9 group stiffness scalings: al_welds, angle_brackets, bottom_box, contact, cross_beam, joints, plates, steel_welds, top_box) | log-normal, median 1, σ_log = 0.25 | inherited (femlib NSIG_THETA) | M |
| Global gain per train drive | Normal(0, 20 dB) on the log10-offset, one per drive | wide prior; the folds' fitted gains are O(±10 dB) | L |
| Correlated error kernel | squared-exponential in log10(f); σ_e ~ HalfNormal(0.5 dex), ℓ ~ LogNormal(ln 0.1, 0.5) in log10-Hz units | statFEM-style discrepancy; scale set by observed residuals ~0.3–0.8 dex | H |
| iid noise floor | σ_n ~ HalfNormal(0.2 dex) | measurement/hit scatter ~0.09 dex median (resolution Gate W) | M |
| NUTS | NumPyro, 4 chains, float64, target R-hat ≤1.05 (prefer ≤1.01), ESS ≥200, div <2% | AGENTS.md gate | — |
| Channel thinning for likelihood tractability | if needed, an evenly-spaced channel/bin subset for NUTS, stated with counts; SCORING always uses all channels | compute honesty | M |

## A5. Model/basis (card §5)
| item | value | source | sens |
|---|---|---|---|
| FEM | inherited 67,683 grids ~406k DOF; K(θ)=A_fix+Σθ_g A_g; M=I in reduced basis (mass-normalized) | fem_model.npz + femlib packages | — |
| Eigensolution top | 1.25 × certified band top (target ~1250 Hz; worst-case ≥625 Hz) | card §5 | H |
| Exact-basis rule | decision numbers from full solve at candidate θ_MAP or validated enrichment; spot-check ≤0.3% freq error | true-remodel D22 | H |
| θ_MAP | deterministic multi-start, ≥5 starts | true-remodel D19 | H |
| Mode pairing | Hungarian on full MAC matrix, FROZEN per candidate before scoring | card §5 | M |
| Mode-tier update | 234–258 Hz cluster: unmeasured → amplitude-measured at ~111 sensors, shapes still sparse on plate (1 Z sensor) — tier table addendum HERE once extended band exists | card §5 | H |

## A6. Data counts (Assumptions & Uncertainty Gate)
- 5 measured drives (hammer references), 6 hits each typical, ~111 accel channels, 105 bins legacy / ~470+
  bins wide (to be measured). One article, one test campaign: NO build-to-build or test-to-test variability
  is modeled (single-article data; stated limitation). Hit-to-hit variability enters via H1 averaging and
  coherence. Raw zips: 5 modal-hammer series (645 MB–1.0 GB each), downloaded one at a time.
- Inferred (arm B): θ (9), gain per train drive (3), σ_e, ℓ, σ_n. Fixed: window constants, ζ table, mode
  pairing, channel mask. Latent NOT inferred: true mode shapes (arm C infers a perturbation field
  separately), true damping above 258 Hz, drive-point micro-location.

## A7. Environment / compute
- Python venv: `.venv_nuts` (jax 0.4.30, numpyro 0.15.3, numpy 1.26.4, scipy 1.10.1) for NUTS; system python
  for FEM/eigh. `OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1` for small dense eigh/posterior math. Long jobs
  detached + resumable per (arm, fold). CPU (Mac) only; no GPU (compute protocol: method not yet validated).
- Disk: ~24 GiB free at start; one zip at a time; delete .mat after distilling each hit; delete zip after
  its drive's cache validates. `df` checked before each download (abort < 1.5 GB).

## A5b. Dated addendum 2026-07-14 (post data phase, BEFORE any QOI computation): extended-band mode tiers
- Wide caches confirmed: 11 cross-drive (≥3 dev drives) measured peaks in 200–1000 Hz
  (254.3/274.7/296.5/342.3/354.0/366.9/463.9/545.9/598.1/883.6/975.9 Hz; `out/extended_peaks.json`).
- Tier update for the 234–258 Hz cluster + any matched extended mode (H4): FREQUENCY tier unmeasured→
  measured (SD_F 0.06 → 0.01) where a FEM mode matches a measured cluster peak (≤2% mismatch);
  AMPLITUDE tier becomes DATA-DRIVEN: per matched mode, SD_A = cross-drive std of ln(amplitude scale
  factor) fitted from the wide caches (answer-key-style residue fit — construction only, never a selection
  score), FLOORED at 0.35 (never below the measured-mode tier). Shapes on the plate remain sparse
  (1 Z sensor): the tray-Z participation g_i stays shape-uncertain; if the observed cross-drive amplitude
  scatter is large, SD_A stays large and the normal band will NOT narrow — that is an honest H4
  falsification path, pre-registered here.
- QOI band grid unchanged (FGRID 45–260 Hz, netcg convention) so the width RATIOS remain comparable to the
  delivered 1.51×/2.30×/2.53×.

## A8. Known risks pre-registered as expected findings (card §11)
Downloads fail (fallback ladder §4); arm-B multimodality / error-term absorption (H1-relevant result, report
θ-only contrast); shape wins per-point but fails QOI coverage (sharpens H1); agent ties random (H2 confirmed
with correct compass); everything ties A1 (the "unreachable error" claim, written with the same care as a win).
