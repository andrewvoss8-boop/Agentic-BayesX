# Assumptions Ledger — ShockSat FEM Modal Twin

Sensitivity priority: H = likely to move the held-out QOI / decision,
M = moderate, L = bookkeeping. "Source" names the file or evidence.

| # | assumption | value / units | source / evidence | prio |
|---|---|---|---|---|
| A1 | Unit system in/lbf/s; MAT1 RHO already mass density | e.g. steel rho 7.324e-4 lbf·s²/in⁴ | deck values + weight check −0.084% | L |
| A2 | `Shock_Test_Instrumentation.blk` dropped (37 GRID + 37 RBE2, zero mass/stiffness) | — | D10; raw deck inspection | L |
| A3 | Element formulations: QM6 membrane + MITC4 bending (CQUAD4), CST + DKT (CTRIA3), flat-facet | benchmark errors ≤0.5% | `fe_validate_report.json`; nominal-vs-NASA-FEM table in packet (0.1–2.5% per mode) | M |
| A4 | Drilling DOF: K6ROT-concept penalty on (θz − membrane rotation), k = 100·1e-6·G·t·A/node | K6ROT=100 (PARAM in Modes.dat) | D12; rigid-rotation energy 1.2e-7 rel | L |
| A5 | Mass: lumped shell mass + consistent CONM2 with offsets; mass NOT scaled by theta | 127.783 lb vs NASA 127.89 (−0.084%); CG z 28.014 vs 28.01 in | `assembly_meta.json`; NASA pptx slide 55 | L |
| A6 | Free-free BC; 6 RBMs (max 1.13 Hz, flat-facet residual) excluded via elastic-only basis | RBMs 0–1.13 Hz vs 54.6 Hz first elastic | `nominal_modes.json` | L |
| A7 | theta parameterization: 9 include-file part groups; accel-mount bushes (PBUSH 99) fixed at 1 | `groups.json` | deck structure; NASA hand-tuned joints (pptx) | **H** (sensitivity: regrouping) |
| A8 | Priors: theta_g ~ LogNormal(median 1, sigma 0.25); untruncated 95% range [0.61, 1.63] | dimensionless | joints were hand-tuned by NASA → wide prior is honest | **H** (sensitivity: width) |
| A9 | Frequency noise scale sigma_f INFERRED, prior HalfNormal(0.05) on log-frequency residual sd | dimensionless (≈ relative freq error) | replicate floor: median 0.30%, p90 0.93% (`noise_floor.json`); sigma_f above ~1% = model discrepancy, stated in packet | **H** (sensitivity: prior scale) |
| A10 | Shape information enters as Gaussian PSEUDO-likelihood on (1 − MAC) with scale sigma_mac INFERRED, prior HalfNormal(0.2) | dimensionless | standard MAC-based updating practice; labeled pseudo-likelihood (not a generative model of shapes) | M |
| A11 | Mode pairing test↔model fixed from nominal MAC pairing (matches NASA's published pairing); inside NUTS modes are TRACKED by argmax of nominal-component (piecewise-constant → non-differentiable at switches; documented per NUTS rule) | — | `nominal_mac_table.json`; switch-collision check at posterior mean | M |
| A12 | Calibration set = paired test modes with nominal MAC ≥ 0.5; low-MAC modes are still predicted and reported | threshold 0.5 | pairing with MAC < 0.5 is not trustworthy (symmetric-pair mixing, spatial aliasing) | **H** (sensitivity: threshold) |
| A13 | Reduction basis = 74 nominal elastic modes (to 321.7 Hz); likelihood band ≤ ~260 Hz | probe errors in `reduction_report.json` | Discretization-Resolution gate | M |
| A14 | Damped natural frequencies treated as undamped | error < 0.02% at ζ ≤ 1.7% | ζ from .ash; 1/sqrt(1−ζ²) | L |
| A15 | Measured .ash shape components are in the basic frame | — | MAC up to 0.97 vs FEM at nominal (a frame error would kill all modes) | L |
| A16 | One test article; replicate evidence = 9 runs (3 impact + 6 burst), frequencies only; NO build-to-build variability modeled | `noise_floor.json` | data inventory | M |

## Data count
- 33 measured modes (frequency + damping + shape on 76 nodes / 132 DOFs), ONE
  test article, one merged polyreference fit (.ash) used as the calibration
  observation; 9 replicate runs inform the noise floor only.
- Inferred: 9 theta_g + sigma_f + sigma_mac (11 variables). Fixed: mass,
  geometry, pairing rule, accel-mount stiffness, element formulation.
- Not inferred (latent, acknowledged): model-form discrepancy field beyond
  what sigma_f absorbs; damping (not used by the likelihood).
