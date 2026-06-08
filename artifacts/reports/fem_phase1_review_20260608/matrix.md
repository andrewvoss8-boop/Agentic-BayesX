# Phase-1 Hexapod — 3-agent × 4-tool frequency matrix (Hz)

Date: 2026-06-08. Frequencies parsed from each `runs/fem_phase1/<agent>/<tool>/results.json`;
the Femap column is the human Simcenter-Nastran solve (transcribed from screenshots).
EXCLUDED = integrity/independence failure; INVALID = deck failed to solve correctly.
All values are PROVISIONAL UPPER BOUNDS (rigid/stiff joints).

## First modes by cell (Hz)

| Agent / tool | M1 | M2 | M3 | M4 | M5 | M6 | element family |
|---|---|---|---|---|---|---|---|
| **opus** JAX | 84.8 | 85.3 | 181.3 | 291.1 | 371.3 | 394.8 | ACM plate + Euler beam |
| **opus** TensorMesh | 84.7 | 85.4 | 181.1 | 293.0 | 374.5 | 421.8 | H8 solid + truss |
| **opus** CalculiX | 85.3 | 85.7 | 182.4 | 289.9 | 337.0 | 337.2 | C3D8I solid + truss + RBE3 |
| **opus** Femap deck | 84.45 | 84.99 | 180.46 | 288.63 | 366.00 | 380.96 | CQUAD4 shell + CROD + CBUSH |
| **composer** JAX | 82.0 | 83.1 | 182.2 | 298.7 | 381.9 | 458.0 | hex solid (jnp.eigh) |
| **composer** "TensorMesh" | 82.8 | 83.2 | 182.3 | 301.9 | 462.9 | 465.8 | hex solid (scipy.sparse eigsh) |
| **composer** CalculiX | 82.0 | 83.1 | 182.3 | 294.9 | 337.3 | 337.3 | solid + truss |
| **composer** Femap deck | — | — | — | — | — | — | INVALID (missing property; constraints on tray body) |
| **codex** JAX | ~~301.8~~ | ~~355.6~~ | ~~360.0~~ | — | — | — | EXCLUDED (shared scipy solver, not JAX) |
| **codex** TensorMesh | ~~301.8~~ | ~~349.6~~ | ~~362.2~~ | — | — | — | EXCLUDED (shared scipy solver, discretize discarded) |
| **codex** CalculiX | 84.77 | 86.51 | 192.58 | 299.56 | 337.26 | 337.30 | real ccx solid + truss |
| **codex** Femap deck | 75.23 | 82.47 | 173.80 | 286.58 | 366.62 | 382.32 | CHEXA + CROD + CELAS2 (symmetry split flag) |

## Cross-software / cross-agent agreement (legitimate builds only)
Legit builds = opus×4, composer×3 (Python), codex CalculiX, codex Femap deck. (Codex
JAX/TensorMesh excluded; composer Femap invalid.)

| Mode family | Range across legit builds | Notes |
|---|---|---|
| Suspension lateral pair (M1/M2) | 82.0 – 86.5 Hz | tight EXCEPT codex deck splits 75/82 (broken-symmetry flag) |
| Suspension M3 | 173.8 – 192.6 Hz | codex ccx 192.6 is the high outlier (~6%) |
| Suspension M4 (tray-bounce) | 286.6 – 301.9 Hz | ~5% spread |
| First tray-flex | 337 Hz (all 3 solids) vs 366–382 (shell/plate) | element-theory spread (expected) |

## Mode typing (human-confirmed, Andrew 2026-06-08)
- M1/M2 = lateral suspension pair (opus shows the clean 84 Hz near-degenerate pair).
- M4 and M6 = tray-bounce (vertical suspension) type motion.
- ~337/366 Hz = first tray-flex (solid 337; shell/plate 366–375).

## Optional provisional analytical cross-reference
NOT computed this pass. A reproducible analytical rigid-joint 6-DOF script could be added
later as ONE clearly-PROVISIONAL upper-bound column — it is NOT ground truth and must not be
used as a pass/fail bar.
