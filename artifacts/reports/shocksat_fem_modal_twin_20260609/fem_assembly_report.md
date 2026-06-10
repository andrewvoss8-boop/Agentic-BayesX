# FEM Assembly & Nominal Validation Report — ShockSat Modal Twin

Written by the Claude Code lead session (see decisions D9, D19). All numbers
below are reproduced by `bash run_all.sh` steps 1–7 and live in
`fem_parse_report.json`, `fe_validate_report.json`, `assembly_meta.json`,
`nominal_modes.json`, `nominal_mac_table.json`, `pairing.json`,
`reduction_report.json`.

## 1. What was built
A from-scratch Python assembly of NASA's FEM_20211021 NASTRAN deck (no
pyNastran, no external solver): 67,683 grids / ~406k DOFs, 67,366 CQUAD4,
428 CTRIA3, 166 CBUSH (9 PBUSH properties), 80 CONM2 accelerometer masses,
150 RBE2 (after dropping `Shock_Test_Instrumentation.blk` — decision D10:
that include is 37 grids + 37 massless, stiffness-free response spiders whose
dependent grids collide with the joint spiders). Stiffness is stored as
per-PID blocks so `K(theta) = K_fixed + sum_g theta_g K_g` scales part-group
moduli exactly.

## 2. Element library validation (`fe_validate_report.json`, ALL_OK)
- QM6 membrane cantilever vs beam theory: −0.37%
- MITC4 bending simply-supported plate vs analytic: −0.47%
- DKT bending SS plate: −0.33%; CST patch test exact
- Rigid-tilt residuals ~3e-16 in the NASTRAN sign convention (the test that
  catches sign errors eigenvalue counts cannot see — session-1 lesson D8).

## 3. Assembly checks (`assembly_meta.json`)
| check | ours | reference | err |
|---|---|---|---|
| total weight | 127.783 lb | 127.89 lb (NASA pptx s.55) | −0.084% |
| CG | (−0.0006, −0.0008, 28.014) in | (0, 0, 28.01) in | ~0.004 in |
| rigid translation energy | ~1e-15 rel | 0 | exact |
| rigid rotation energy | ~1.2e-7 rel | 0 | flat-facet residual |
| RBM frequencies | 0, 0, 0.002, 0.43, 0.48, 1.13 Hz | ≈0 | ≪ 54.6 Hz first elastic |

The rigid-rotation residual required reformulating the drilling penalty
(decision D12): a bare diagonal θz penalty is not rigid-rotation invariant
and put spurious ~3–4 Hz "rigid" modes in; the K6ROT-concept penalty on
(θz − membrane in-plane rotation) removed it.

## 4. Nominal modes vs NASA's FINAL FEM — the model-form error measurement
NASA's published FEM column (pptx slides 21–45) is the test-PAIRED subset of
their FEM modes, so ascending-list comparison is only valid for the first few
modes (ours: −0.14%, +0.07%, +0.31%, +0.12% for modes 1–4). The
apples-to-apples comparison is per TEST mode: our MAC-paired partner
frequency vs NASA's published partner frequency.

| test | f_test [Hz] | NASA FEM | ours | MAC (ours/test) | d_ours % | d_NASA % |
|---|---|---|---|---|---|---|
| 1 | 54.19 | 54.67 | 54.60 | 0.970 | +0.75 | +0.89 |
| 2 | 69.98 | 73.51 | 73.74 | 0.497 | +5.37 | +5.04 |
| 3 | 74.98 | 73.09 | 73.14 | 0.512 | −2.45 | −2.52 |
| 4 | 85.78 | 87.94 | 88.05 | 0.883 | +2.65 | +2.52 |
| 5 | 107.03 | 102.23 | 104.74 | 0.975 | −2.14 | −4.48 |
| 6 | 117.63 | 108.17 | 122.23 | 0.899 | +3.91 | −8.04 |
| 7 | 118.53 | 113.43 | 113.80 | 0.958 | −3.99 | −4.30 |
| 8 | 125.00 | 116.9 | 117.35 | 0.704 | −6.12 | −6.48 |
| 9 | 137.20 | 137.9 | 124.38 | 0.425 | −9.34 | +0.51 |
| 10 | 142.40 | 154.5 | 151.90 | 0.559 | +6.67 | +8.50 |
| 11 | 151.20 | 151.8 | 152.20 | 0.610 | +0.66 | +0.40 |
| 12 | 158.20 | 135.9 | 146.60 | 0.581 | −7.33 | −14.10 |
| 13 | 165.90 | 160.4 | 160.61 | 0.755 | −3.19 | −3.32 |
| 14 | 168.00 | 183.4 | 183.88 | 0.703 | +9.45 | +9.17 |
| 15 | 172.30 | 185.0 | 185.18 | 0.737 | +7.48 | +7.37 |
| 16 | 174.80 | 164.5 | 168.87 | 0.639 | −3.39 | −5.89 |
| 17 | 184.40 | 182.7 | 183.55 | 0.889 | −0.46 | −0.92 |
| 18 | 188.60 | 189.3 | 190.36 | 0.690 | +0.93 | +0.37 |
| 19 | 190.20 | 191.0 | 193.66 | 0.340 | +1.82 | +0.42 |
| 20 | 195.70 | 192.6 | 192.59 | 0.391 | −1.59 | −1.58 |
| 21 | 197.80 | 191.9 | 196.90 | 0.661 | −0.46 | −2.98 |
| 22 | 198.90 | 193.5 | 192.90 | 0.387 | −3.02 | −2.71 |
| 23 | 203.00 | 191.4 | 191.56 | 0.282 | −5.64 | −5.71 |
| 24 | 213.90 | (none) | 247.50 | 0.035 | +15.71 | — |
| 25 | 222.10 | 211.1 | 211.70 | 0.620 | −4.68 | −4.95 |

Reading: on 19 of 24 NASA-paired modes our error vs test matches NASA's own
FEM error to within ~2.5 percentage points, often to a few tenths (modes 1,
3, 4, 13, 14, 15, 17, 22, 23, 25). That means: (a) the Python element
library + assembly reproduces NX Nastran's behavior on this model faithfully;
(b) the residual error pattern is the genuine TEST-vs-FEM gap NASA also saw —
exactly the thing theta calibration is for. Disagreements at tests 6, 9, 12
are pairing/partner differences in a band where modes are dense and MAC is
weak — NASA also reported correlation struggles >150 Hz (and test 24 has no
credible partner in either FEM). NOT tuned: nothing in the build was adjusted
toward the test values.

## 5. Reduction (Discretization-Resolution gate)
Basis = 74 nominal elastic modes (54.6–321.7 Hz; RBMs excluded).
`reduction_report.json`:
- nominal consistency: max relative eigenvalue error 6.4e-10 (exact);
- box modulus split ±20% probe: max 0.60%, median 0.10% (42 modes < 280 Hz);
- joints+contact ×0.5 (beyond the 95% prior range): max 2.7%, median 0.50%.
Per decision D18 (parallel session), basis enrichment was dropped on compute
cost; instead the reduced model is re-validated by one full solve at the
POSTERIOR-MEAN theta after calibration — the region that matters. Limitation
stated: reduced-model error is bounded by ~0.5–2.7% only at the extreme
joint excursion, and the posterior-mean check closes the loop.

## 6. Caveats
- One eigsh full solve costs ~6 min (400k DOFs, shift-invert) — that priced
  all probe/enrichment decisions.
- The 122–125 Hz cluster (4 modes incl. a degenerate pair) is denser in our
  model than in NASA's paired list; near-degenerate eigh-gradient care is
  handled in the NUTS model (stop-gradient tracking; see run_nuts.py header).
- Lead-as-runner: this session both built and reports this — independence
  comes from NASA's published numbers (untouched inputs), the analytic element
  validation, and the checker. An independent second-solver re-solve of our
  deck (`femap_handoff/`) is PREPARED but DEFERRED (D32): the available FEMAP/NX
  is a student license whose node cap cannot load the 67,683-grid model; full
  NX or MYSTRAN is an optional follow-up.
