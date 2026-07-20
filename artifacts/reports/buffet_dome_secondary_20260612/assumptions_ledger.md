# Assumptions Ledger — Representative LV (Terran-R/F9 class)

HONESTY HEADER: this session has NO live web access. "Public" values below are from
the lead model's training knowledge and are flagged by confidence. NOTHING here is a
verified Terran-R fact; the VERIFY list at bottom must be run in a web-capable session
before any external use. Confidence: H = multiple consistent public sources expected;
M = public but possibly mis-remembered; L = engineering assumption, no public source.
Sens = expected QOI sensitivity priority (1 = highest, drives P3 priors).

## A. Vehicle / geometry (representative)
| ID | Item | Value | Units | Conf | Sens | Rationale / source class |
|----|------|-------|-------|------|------|---------------------------|
| A1 | Vehicle diameter | 4.5 | m | M | 2 | Terran-R published diameter ≈ 4.5 m (F9 = 3.66 m); sets dome + barrel scale |
| A2 | Dome shape | √2:1 ellipsoidal cap | – | L | 3 | Common tank-dome practice; Relativity media shows near-ellipsoidal spun/welded dome |
| A3 | Dome equivalent thickness | 5 | mm | L | 1 | NO public value; typical machined Al dome land 3–8 mm; PRIOR in P3 (3–8 mm) |
| A4 | Barrel skin equivalent thickness | 5 | mm | L | 1 | Smeared orthogrid/isogrid equivalent; prior 3–8 mm |
| A5 | Barrel section length to first ring frame | 1.5 | m | L | 2 | Fine-region cut (D5); convergence study grows it |
| A6 | Load-introduction ring | 100×60 mm box, 6 mm wall | mm | L | 2 | Y-ring/frame class; carries dome-barrel junction stiffness |
| A7 | Material (dome/barrel/ring) | Al 2219/Al-Li class: E=71 GPa, ν=0.33, ρ=2800 kg/m³ | – | M | 3 | Relativity moved to largely Al alloy structures; property class standard |

## B. Secondary structures (representative, scaled from program assets + image)
| ID | Item | Value | Units | Conf | Sens | Rationale |
|----|------|-------|-------|------|------|-----------|
| B1 | Avionics tray plate | 600×600×12.7 | mm | L | 2 | Scaled-up cousin of program 300 mm tray; Al 6061 (E=68.9 GPa, ρ=2700) |
| B2 | Tray struts | 6× tube Ø25×1.5 mm wall, L≈300 mm, Al; spherical end releases | – | L | 1 | Hexapod-class mounting per program rig; AXIAL members |
| B3 | Tray strut joint stiffness | 1e7 (axial) | N/m | L | 1 | Lumped joint compliance; prior 1e6–1e8 (program FEM-arch values) |
| B4 | Avionics lumped mass | 8 | kg | L | 1 | Representative avionics box; CONM2 at tray node, 50 mm CG offset |
| B5 | COPV | Ø350 × 700 mm cylinder + heads, 30 kg incl. fluid fraction | – | L | 1 | Image-class red COPVs; shell + end masses; NO public Terran-R COPV data |
| B6 | COPV mounts | 2 cradle/strap stations, 3-axis bushing 1e7 N/m each | N/m | L | 1 | Prior 1e6–1e8; dominant driver of COPV interface loads |
| B7 | COPV wall (overwrap smeared) | 4 mm equiv., E=60 GPa quasi-isotropic equiv., ρ=1600 | – | L | 2 | Composite overwrap smeared; only in-band rigid+first shell modes matter |

## C. Dynamics / damping
| ID | Item | Value | Units | Conf | Sens | Rationale |
|----|------|-------|-------|------|------|-----------|
| C1 | Modal damping (uniform baseline) | η = 0.02 (Q=25, ζ=1%) | – | L | **1** | Standard built-structure assumption; THE top CI driver for resonant random response; P3 prior η ∈ [0.005, 0.05] |
| C2 | Modal solve band | to 800 Hz (2× report band) | Hz | – | – | Truncation margin (D4); residual flexibility in P2 |
| C3 | Report band | 20–400 | Hz | – | – | Andrew's 400 Hz top; 20 Hz floor below first suspension-class mode |

## D. Forcing — LC2 transonic/max-q buffet (Corcos, Q5)
| ID | Item | Value | Units | Conf | Sens | Rationale |
|----|------|-------|-------|------|------|-----------|
| D1 | Dynamic pressure q̄ at max-q | 30 | kPa | M | 1 | F9-class max-q ≈ 30–35 kPa; Terran-R unpublished |
| D2 | Freestream U∞ (transonic, ~10 km) | 300 | m/s | M | 2 | M≈1.0 at altitude |
| D3 | Convection speed Uc | 0.7·U∞ = 210 | m/s | M | 2 | Standard TBL/buffet 0.6–0.8 U∞ |
| D4 | rms Cp (attached/mildly separated barrel) | 0.04 | – | L | 1 | Smooth-body transonic 0.02–0.06; protuberance/flare regions higher — NOT modeled; prior in P3 |
| D5 | Corcos decay α_x / α_y | 0.12 / 0.72 | – | M | 1 | Classic Corcos coefficients; coherence-length sweep is a REQUIRED sensitivity |
| D6 | Buffet PSD shape Φ_p(f) | flat to f0=50 Hz, then (f/f0)^−2 | – | L | 1 | Full-scale buffet energy is low-frequency; corner + slope = documented assumption w/ sensitivity |

## E. Forcing — LC1 liftoff acoustics + internal field (DAF, Q6)
| ID | Item | Value | Units | Conf | Sens | Rationale |
|----|------|-------|-------|------|------|-----------|
| E1 | External OASPL on barrel at liftoff | 155 | dB re 20 µPa | L | 1 | SP-8072-class barrel environment; prior ±6 dB |
| E2 | External spectrum shape | octave peak 63–125 Hz, −3 dB/oct above | – | L | 2 | Typical liftoff shape; documented assumption |
| E3 | Internal compartment OASPL (direct on dome/secondaries) | 140 | dB | L | 1 | ~10–15 dB fill/transmission knockdown; prior ±6 dB |
| E4 | Internal spectrum shape | peak 100–250 Hz | – | L | 2 | Compartment acoustics class |
| E5 | Speed of sound (air, compartment) | 343 | m/s | H | 3 | Standard |

## F. Data count / variability statement (AGENTS.md gate)
- Observed datasets: NONE (synthetic study; no test data enters before P3+).
- Flight-to-flight / build-to-build variability: NOT modeled in P1 (deterministic);
  enters P3 as prior width on forcing level + damping. Stated, not hidden.
- Inferred variables: NONE in P1 (no sampler). P3 = propagation MC over priors
  (labeled; NUTS only if data arrives, per AGENTS.md).

## VERIFY list (run in a web-capable session before external use)
1. Terran-R diameter, length, stage split, GLOM/thrust (Relativity public releases).
2. Terran-R dome construction/material class (Al alloy spun/welded vs printed).
3. Public max-q and ascent acoustic specs for F9-class (SpaceX users guide, NASA).
4. Corcos coefficients + transonic rms-Cp ranges against primary literature
   (Corcos 1963; launch-vehicle buffet refs; NASA SP-8001 lineage).
5. Internal-compartment acoustic knockdown practice (NASA-STD-7001B fill factor).
