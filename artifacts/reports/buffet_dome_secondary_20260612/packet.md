# Packet — Representative LV Dome Secondary-Structure Vibe Under Max-Q Buffet

Status at packet write time: foundations + model CERTIFIED (checker GREEN on
S1/S2/S3); modal solves + QOI sweeps + CI running detached (S4/S5 = PENDING
yellow). This file is updated as stages land — every number below is traceable
to a JSON artifact in `out/`. Replay: `bash run_all.sh` (foundations, ~2 min);
heavy stages: `scripts/run_pipeline_tonight.sh`.

**Standing caveats (read first)**
1. BUFFET-ONLY forcing (Andrew decision D12): liftoff/ascent acoustics
   deferred — above the buffet roll-off a real flight environment would be
   acoustic-co-driven, so high-band levels here are LOW relative to flight.
2. Representative vehicle: every geometry/material/forcing number is a
   training-knowledge assumption with a confidence flag and a VERIFY list
   (assumptions_ledger.md) — NO live web this session; nothing is a verified
   Terran-R fact.
3. "Valid to 400 Hz" = the REFRAMED claim (D4): fine region converged to
   400 Hz; far-field stack bracketed (BC-A/BC-B), never deterministically
   modeled. The bracket spread is a REPORTED uncertainty.

## 1. Method summary (gate-required, first)

**Question.** What vibration/interface-load environment do dome-mounted
secondary structures (avionics tray, COPV) see under max-q buffet, with
honest confidence intervals, on a Terran-R/F9-class representative vehicle?

**Model form.** Linear structural FEM, modal superposition random-vibration
analysis in the frequency domain.
- Fine region (58,662 DOF): barrel R=2.25 m × 1.5 m (t=5 mm) + junction ring
  (box 100×60×6) + √2:1 ellipsoidal dome (t=5 mm) + 600 mm tray on 6 struts
  (joint-series axial stiffness 4.1 MN/m each) + 8 kg avionics offset CONM2 +
  30 kg COPV beam-spine on 2 three-axis mounts (1e7 N/m, rigid-arm CBUSH form).
- Elements: REUSED validated ShockSat shells (QM6+MITC4 / CST+DKT + drilling)
  + study-validated 3D beam/bar (`out/beam_validation.json`, worst 0.04%).
- Boundary bracket: BC-A bottom ring fixed; BC-B bottom ring RBE2 → master
  carrying 1e5 kg / 5e6 kg·m² far-field stack (free-flight-like; 6 rigid
  modes physical).

**Forcing (the "likelihood-side" input — no data, so no likelihood).**
Corcos convective wall-pressure CSD on the barrel OML:
`S_pp = Φp(f)·exp(−0.12·ω|Δz|/Uc)·exp(−0.72·ω|Δs|/Uc)·exp(iωΔz/Uc)`,
Uc=210 m/s, Φp from rms-Cp=0.04 × q̄=30 kPa with a flat-to-50-Hz then f⁻²
spectrum (total p_rms = 1200 Pa). Frequency-dependent coherence length =
Andrew's "patches with varied correlation" made precise (fig3).

**Response math (validated chain).** Modal force CSD never formed explicitly:
each QOI is a linear functional row L over modal coordinates; per frequency,
PSD_L = Φp · Σ_pn λx_p λθ_n |Ux^H FFT_θ(F·g)|², g_j = L_j H_j(ω) (×ω² for
accel), H_j structural damping η=0.02. Axial kernel eigendecomposed (64×64),
circumferential kernel diagonalized EXACTLY by FFT (circulant on the
periodic barrel). Fast path == brute-force full-CSD quadratic form to
9.8e-16 (in-script self-check, aborts on mismatch). Load grid 64×720
(19.6 mm arc = 5.9 nodes per lateral coherence length at 400 Hz; S1 rule ≥6
met at band top, G3).

**Data count.** Zero measured datasets. Deterministic nominal + prior
propagation. No sampler anywhere (per AGENTS.md NUTS rule, no posterior or
convergence claim exists in this study).

**Inferred variables.** None (no data). CI = propagation of documented priors:
η, Cp_rms, Uc, Corcos α scale, spectrum corner f0 (ci_mc.py); structural
levers (k_mount, k_joint, t_dome) via discrete re-solves (resolve_variants.py).
Fixed: everything else in the assumptions ledger.

## 2. Validation ladder (all checker-backed, GREEN)

| Stage | What it proves | Result |
|---|---|---|
| S1 plate plumbing | CSD→joint-acceptance→PSD math vs closed forms | fast==full 4e-16; RMS ratio 0.990; peaks ≤0.4%; mesh rule ≥6 nodes/Lcoh |
| S2 beam/bar | new element vs analytic bending/axial/torsion/SS | worst 0.04%; 6 rigid modes; resid 1e-18 |
| S3 model | mass parts vs hand calc; rigid-body invariance; SS-cylinder vs Donnell THROUGH the production composition path | barrel mass exact; K@rigid ~1e-16; Donnell n=3–6 within −3…−6%; degenerate pairs 1e-10 |

Two run-1 lessons kept deliberately in the record (`notes/runs.md`):
peak checks must use nearest-local-max off node lines; convective Corcos
joint acceptance is NON-monotone in coherence length at high f (aerodynamic
coincidence) — encoded as physics, not a bug.

## 3. QOI definitions (contracts pinned in quantity_contracts.md)

Q1 strut/mount loads [N²/Hz + N RMS]; Q2 netCG punch into dome (per assembly,
dome-normal highlighted; ties to 7004C effective-mass below first elastic
mode — checker-tested when QOI lands); Q3 secondary-structure field metric
(spatial max/median accel over tray + COPV nodes); Q4 avionics box-CG accel
(3 axes, includes rotation×offset). All per BC bracket.

## 4. Results (filling as the detached pipeline lands)

- [x] **BC-A modal basis**: 2,019 modes to 842 Hz; 672 modes below 400 Hz
      (`out/modes_bcA_meta.json`; 22 min marching shift-invert, 16 windows).
      High modal density (~3–4 modes/Hz at band top) = the mid-frequency
      regime that motivated the D4 reframe.
- [x] **Nominal QOI RMS, 20–400 Hz, buffet-only, D14 model** (self-check
      9.8e-16; `out/qoi_bc*_summary.json`):
      | QOI | BC-A | BC-B |
      |---|---|---|
      | strut load (worst of 6) | 36.8 N | 32.3 N |
      | tray netCG punch | 45.4 N | 42.6 N |
      | COPV net punch | 37.6 N | 34.6 N |
      | COPV per-mount resultant | 40.8 N | 35.2 N |
      | avionics box accel (z) | 3.53 m/s² | 3.39 m/s² |
      **BC bracket spread ≈ 6–10 %** on all interface loads → first-ring-frame
      cut is far enough that the secondaries barely feel the far field (the
      substructuring argument, demonstrated, not asserted).
      Plausibility: avionics ≈0.3 g RMS is LOW vs typical flight random specs —
      EXPECTED for buffet-only (energy <50 Hz) + smooth-body Cp=0.04; the D12
      caveat is doing its job. The COPV per-mount in-plane shear is the
      design-driving channel (see D14 correction below).
- [x] **CI bands** (144 prior-propagation draws, labeled NO-sampler;
      re-running on the D14 basis; fig6). v1 reference: tray punch RMS
      5/50/95 % = **18 / 40 / 87 N** (~5× span); width dominated by the damping
      and buffet-level priors — the honest-ignorance interval that is the actual
      deliverable. (Tray/strut/avionics bands carry over unchanged from v1; COPV
      bands update with the D14 model.)
- [x] **Sensitivity / variants** (`out/variant_table.md`):

  | variant | strut | tray punch | COPV punch | avionics az |
  |---|---|---|---|---|
  | COPV mount soft (×0.1) | ×1.00 | ×1.00 | **×0.40** | ×1.00 |
  | COPV mount stiff (×10) | ×1.00 | ×1.00 | ×1.10 | ×1.01 |
  | tray joints soft (×0.1) | **×0.20** | **×0.31** | ×1.00 | **×0.31** |
  | dome thin 5→3 mm (model-form) | ×0.57 | ×0.65 | ×0.42 | ×0.74 |
  | refined mesh (Nth 240→300) | _re-solving under D14_ | | | |

  Two physics statements: (1) substructures are **largely decoupled through the
  dome** — a mount/joint change is ~90% local to its own hardware, with a modest
  **~15% cross-talk** through the shared dome (e.g. soft tray joints nudge COPV
  punch ×1.18); (2) the **dome gauge moves everything 40–75 %** = the
  quantitative case for resolving the local primary host to 400 Hz (D4), not a
  stick. (Variant table re-solved D14-consistent; `out/variant_table.md`.)
- [!] **D14 correction (honest, evidence-driven — the headline lesson of this
  leg).** The fig2 image-QA gate caught a ~0 Hz COPV spin (two purely-
  translational mounts → free rotation about the mount line); fix = add
  rotational mount stiffness (1e4 N·m/rad). I *expected* this to be
  QOI-invisible. The data (`out/d14_compare.json`) say three different things:
  1. **tray/strut/avionics: ≤2 %** — invisible, as predicted (the spin mode is
     genuinely unforced for them).
  2. **COPV net dome-normal punch: −15 %** (45→38 N) — rotation redistributes
     the normal reaction.
  3. **COPV per-mount in-plane shear: roughly DOUBLES** (Fx 12→25 N; Fy 2.5→16
     N) — the mounts now carry moment. **This is the design-driving channel**,
     and the v1 free-spin model badly *under-predicted* it.

  So the v1 COPV mount numbers were non-physical and are SUPERSEDED; k_mount_rot
  is promoted to a sensitivity variable (krlo 1e3 / krhi 1e5); CI re-runs on the
  D14 basis. This is a worked example of the image-QA gate forcing a *physics*
  correction — and of recording a wrong prediction honestly instead of burying
  it (the optimistic verdict string was replaced with a data-driven one).

## 4b. Coupling / truncation trust-test (P2, `out/coupling_validation.json`)

The one structural claim that needed independent verification: do our QOIs,
built by **modal superposition truncated at 820 Hz**, equal the **direct full
58k-system complex frequency response** (no truncation)? Driving each
substructure with a point load and masking near-zero frequencies:

| QOI | mode-displacement vs direct (max / median) |
|---|---|
| tray net punch | 0.29% / 0.18% |
| COPV net punch | 0.68% / 0.37% |
| COPV mount Fx | 0.69% / 0.19% |
| avionics accel z | 0.54% / 0.06% |

**Worst 0.69%** → the 2×-band modal truncation reproduces the exact response;
the residual flexibility from >820 Hz modes is negligible for these interface
QOIs. (Process note: the first attempt used a uniform barrel pressure that
barely loads the secondaries → near-zero forces → meaningless tiny/tiny
relative errors; fixed with driven point loads + masking. Logged, not buried.)

## 4c. Mesh convergence (Discretization gate)

Refined mesh (Nth 240→300, Nz 16→20, Nu 24→30): 671 modes below 400 Hz vs 672
nominal; QOI RMS ratios 0.97–1.06 — the production mesh is converged for every
QOI.

## 4d. Response-limit proxy (S8 — vision §2.2 / D7; promoted on request)

Industry response-limits (cheap accelerometers), it does not force-limit (rare
interface force gauges). We formally promote the avionics-box acceleration to a
response-limit proxy for the tray interface "punch" load, via the random-vibration
cross-spectrum (`out/response_limit_proxy.json`, fig7):
- **Controlling mode 55 Hz** (tray suspension, where the punch PSD peaks);
  **coherence between avionics accel and punch = 0.9999** there.
- **Proxy gain α = 15.1 N/(m/s²)** is **invariant to damping** (0.06% over
  η = 0.005–0.05) and **exactly invariant to the buffet level** (α cancels the
  forcing). So the response limit `a_limit = F_allow/α` is a **structural
  constant — robust to the very damping and forcing uncertainty that gives the
  QOI its 5× CI.** This is the response-limit analogue of the robust-twin claim.
- **7004C tie:** the tray-CG-accel gain = 1.17 × the assembly mass (20.3 kg) —
  i.e. F_punch ≈ m_eff · a_CG, the effective-mass relation read through a sensor.
  A single avionics sensor approximates the CG accel in-band.
- **Validity:** coherence > 0.8 over **32–300 Hz, holding 77% of the punch
  energy**; the proxy **decouples at the avionics-on-tray local mode** (don't
  response-limit there). Honest band-specificity, stated.

## 5. Figures (Tufte-linted; 2 documented lint deviations)

fig1 geometry (3-D schematic — justified); fig2 mode gallery; fig3 buffet
coherence patches + length-scale law; fig4 QOI PSD brackets; fig5 validity
bookkeeping; fig6 confidence bands; fig7 response-limit proxy (coherence + gain
+ effective-mass tie). Lint "dB" hit = the `RdBu` colormap string (false
positive). All 7 pass image-QA.

## 6. Vision-goal mapping (D13)

- Robust-twin honesty: boundary bracket + variant spread WIDEN intervals and
  are reported as uncertainty, not hidden (vision §6.1).
- Response-limit proxy: av_acc channels are the response-limit candidate
  (vision §2.2) — promotion needs Andrew sign-off.
- Coupling trust test: P2 monolithic-toy cross-check queued as the held-out
  analogue before any coupled claim is strengthened.
- NUTS readiness: modal basis + QOI rows are the differentiable-forward
  ingredients a future calibration would consume; nothing claimed now.
