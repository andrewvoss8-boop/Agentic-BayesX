# assumptions_ledger — Assumptions & Uncertainty Gate

Values, units, rationale, source, sensitivity priority. Uncertainty TYPE tagged:
[PAR]=parameter, [OBS]=observation-noise, [DISC]=model-discrepancy, [FORCE]=forcing, [QOI]=QOI/shape,
[BC]=boundary-condition, [BUILD]=build/test variability.

| id | assumption | value / units | type | rationale / source | sensitivity priority |
|----|-----------|---------------|------|--------------------|----------------------|
| A1 | Input PSD | FLAT, level = human judgment | [FORCE] | prompt: 100%-certain flat input at drive point; level cancels in band-RATIO metrics | LOW (cancels in ratios) |
| A2 | Frequency band (data/FEM) | 45-260 Hz | [QOI] | measured coherence + modes live here (realfrf.BAND) | MED |
| A3 | Delivery band (prompt) | 20-2000 Hz | [QOI] | prompt asks 20-2000; OUTSIDE 45-260 Hz twin is PRIOR-ONLY (no data) — flagged, not covered | HIGH (scope limit) |
| A4 | Nominal damping ζ | 1.0% (ZETA_NOM, all modes) | [PAR] | realfrf.py:41; measured .ash 0.25-0.44% (FEM over-damped) — cancels in band-ratio (D8 finding) | LOW for ratio |
| A5 | Tray region | z >= 55 in (top plate, 4646 kept-node DOFs) | [QOI] | FEM geometry (box<45/strut45-55/plate>=55) | MED |
| A6 | Tray mass model | UNIFORM-mass proxy over region | [QOI] | matches validated base_shear functional; consistent-mass (ρt+conm2) = refinement | MED |
| A7 | Reduced model | K(θ)=A_fix+Σ_g θ_g A_g, 9 groups, mass=I, 74-dim | [PAR] | reduced_blocks.npz; realfrf.load_reduced | — |
| A8 | θ prior | log_theta ~ Normal(0, NSIG_THETA) per group | [PAR] | modal_feature/core (proven-converged L5) | MED |
| A9 | Modal-freq likelihood σ (L5) | sigma_w2 ~ HalfNormal(0.15), rel ω² | [OBS] | Kiran Eq25; modal_feature.py | MED |
| A10 | Measured-mode uncertainty | freq SD 1%, log-amp SD 0.35 | [QOI]/[OBS] | qoi_trust_table defaults; consistent w/ .ash spread | MED |
| A11 | UNMEASURED-mode uncertainty | freq SD_F_U 0.06, log-amp SD_A_U 0.80 | [DISC]/[QOI] | HAND-CHOSEN (qoi_trust_table); the drumhead shape is unmeasured | **HIGHEST** |
| A12 | Freq-observed-only tier | freq SD 1% (anchored) + amp SD 0.80 (shape unresolved) | [DISC] | D4: coherent peak anchors freq not shape | HIGH |
| A13 | .ash mode-shape match | MAC >= 0.3 over instrumented DOFs | [QOI] | shape_borrow_diag; Final_FF_Test_Shapes (33 modes x 76 nodes x 3 axes) | MED |
| A14 | Coherence observability threshold | median-channel coh >= 0.70 within ±3 Hz of a peak | [OBS] | Stage-0 observability screen | LOW |
| A15 | Bad channels excluded | DAQ 29,30,31 (60 Hz), 101 (install) | [OBS] | TestLog flags (realfrf.BAD_DAQ) | LOW |
| A16 | Mesh screen proxy | blind shear-band-weighted freq-RMS + MAC (no amp fit) | [QOI] | IMPERFECT PROXY; post-update held-out-QOI selects the twin | MED (screen only) |

## Data counts (Assumptions & Uncertainty Gate)
- Drives: 5 (+X Test01, +Z Test02, +XY Test04, +Z@900 Test06, +Y Test03). +Y = 4 hits, N=122880, coh med 0.85.
- Sensors: 111 accel channels (Recorders 1-115 minus 4 bad). Held-out split over sensors + over drives.
- .ash modal survey: 33 modes on 76 nodes x 3 axes (drive-independent SHAPE data); 20 in-band modes MAC-matched.
- In-band FEM modes: 40 (45-260 Hz). Build/test variability: single build; test-to-test = multi-hit averaged
  per drive (n=4-6 hits); flight-to-flight NOT modeled (single article).

## Inferred vs fixed vs non-inferred
- INFERRED (NUTS): θ (9 stiffness-group multipliers) + sigma_w2 (modal-freq error) [L5 formulations]; plus an
  output discrepancy scale for the +discrepancy / statFEM formulations (Stage 2).
- FIXED: input PSD (flat), ζ_nom=1%, tray region/mass proxy, mode-match MAC threshold, unmeasured-mode σ (A11)
  — these are ASSUMPTIONS, surfaced with sensitivity.
- NON-INFERRED LATENT: the drumhead (234-254 Hz) mode SHAPES / net-CG participations — UNMEASURED; carried as
  discrepancy (A11/A12), the crux of the normal-QOI width.

## Sensitivity result (Stage 0, stage0_sensitivity.json) — the load-bearing assumption
- The tray_normal_Z 95% band factor is driven almost ENTIRELY by SD_A_U (A11), NOT SD_F_U:
  SD_A_U 0.40 -> 2.6x ; 0.80 -> 5.7x ; 1.60 -> 34x  (SD_F_U 0.03->0.12 barely moves it).
- => the normal band width is an ASSUMPTION-dominated quantity. The honest deliverable states this and recommends
  the >200 Hz plate test that would REPLACE A11 with data (resolve the drumhead shape/amplitude).
- Distinguished uncertainty types on the normal QOI: [DISC]/[QOI] (unmeasured drumhead shape, A11) DOMINATES over
  [PAR] (θ posterior) and [OBS] (modal-freq noise). A θ-only band would falsely under-represent this.
