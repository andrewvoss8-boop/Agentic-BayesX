# Assumptions Ledger — notch_multipoint_7004c_20260611

All values are exact inputs to the scripts (no hidden constants). Sensitivity priority:
H = drives conclusions, M = shifts numbers not conclusions, L = cosmetic.

## EX-A — 7004C TDOF replication (nondimensional, = handbook Fig 7/9 setup)
| # | Quantity | Value | Units | Rationale / source | Sens. |
|---|---|---|---|---|---|
| A1 | M1, M2 (source, load mass) | 1, 1 | - | 7004C p.34 example definition | H (swept in Fig-8 replication: M2/M1 in [1e-3, 10]) |
| A2 | K1, K2 | 1, 1 | - | same | - |
| A3 | Q (both oscillators) | 50 | - | same; Fig-8 replication also uses Q=5, 20 | H |
| A4 | Free base drive Ao | 1 | - | same; Fe=0 | L |
| A5 | Damping model | viscous c=m*omega0/Q | - | handbook SDOF expressions | M |

## EX-B — rigid box on 4 feet, enforced 6-DOF base motion (SI)
| # | Quantity | Value | Units | Rationale | Sens. |
|---|---|---|---|---|---|
| B1 | Payload mass m | 6.0 | kg | instrument-class item; mass ratio vs plate 6/10.8=0.56 -> strong coupling/notch (7004C Fig 8 regime where limiting matters) | H |
| B2 | Box dims for inertia (Lx,Ly,Lz) | 0.30, 0.24, 0.20 | m | uniform box; Ixx=0.0488, Iyy=0.0650, Izz=0.0738 kg m^2 | M |
| B3 | CG height above foot plane h | 0.08 | m | typical box CG; couples lateral <-> rocking (off-diagonal apparent mass) | H |
| B4 | Foot positions (plan, rel. centroid) | (+/-0.09, +/-0.07) | m | geometric spacing -> rocking arms; chosen so rock-x (93.1 Hz), rock-y (103.7 Hz), bounce (120.0 Hz) fixed-base modes are well separated | H |
| B5 | Foot stiffness kz | 8.52e5 | N/m | sets fixed-base bounce = 120.0 Hz (=sqrt(4kz/m)/2pi) | H |
| B6 | Foot stiffness kx=ky | 6.0e5 | N/m | lateral modes in-band | M |
| B7 | Foot damping | hysteretic eta=0.04 (Q=25) | - | freq-domain only; typical bolted-joint Q | M |
| B8 | EX-B is symmetric (CG over centroid in plan) | e=0 | m | isolates clean bounce/rocking taxonomy | - |

## EX-C — payload of EX-B on compliant plate backing (SI)
| # | Quantity | Value | Units | Rationale | Sens. |
|---|---|---|---|---|---|
| C1 | Plate (source) | simply supported rectangular, Lx=1.0, Ly=0.8, t=0.005, E=70e9 Pa, nu=0.3, rho=2700 kg/m^3 | - | analytic modes f_mn -> verifiable; mass 10.8 kg; >=3 source modes (31.0, 67.4, 87.7 Hz) below payload fixed-base fundamental 93.1 Hz, matching the 7004C §5.7 validity context | H |
| C2 | Plate modal damping | zeta=0.02 (Q=25) all modes | - | typical built-up structure | M |
| C3 | Foot centroid on plate | (0.55, 0.45) | m | off-center to avoid symmetry/nodal-line artifacts | M |
| C4 | Feet -> plate coupling | vertical force only, via kz (B5) with eta=0.04; payload DOFs z, thx, thy | - | plate bending carries no membrane motion; lateral payload DOFs not modeled on plate (D4); stated limitation | H (structural) |
| C5 | Excitation | unit point force at (0.18, 0.62), flat spectrum | N | "acoustic-like" distant source; far from feet | M |
| C6 | Frequency grid | 20-500 Hz, 2401 log points + refinement to guarantee >=9 lines per half-power bandwidth at every coupled mode | Hz | discretization gate; notches are narrow | H (checked) |
| C7 | Plate modal truncation | all modes with f_mn <= 1250 Hz (2.5x band top); convergence check vs 2500 Hz set | - | discretization gate; truncation shifts coupling stiffness | H (checked) |
| C8 | Field grid for maps | 81 x 65 points (12.5 mm) | m | < lambda/6 at 500 Hz (lambda=311 mm) | M |
| C9 | Notch-depth metric | dB ratio of bare-plate to loaded-plate acceleration magnitude at the coupled-mode frequency (see quantity_contracts.md Q6) | dB | "effect of the notch" = absorber action of the payload | H |

## EX-D — force-limited shaker test vs flight truth (SI)
| # | Quantity | Value | Units | Rationale | Sens. |
|---|---|---|---|---|---|
| D1 | CG plan offset e_x | 0.03 | m | realistic asymmetry; couples heave<->pitch so a uniform shaker drive excites rocking (the overtest mechanism 7004C p.8 names: uniform attachment motion) | H |
| D2 | Test spec | octave-band peak-hold envelope of flight mean-foot |a|^2, no margin | (m/s^2)^2/Hz | 7004C practice minus margin, keeps comparison clean | M |
| D3 | Semi-empirical C^2 | from Eq B1/B2 at mass ratio 6/10.8, Q=25 -> computed in script (~3.7) | - | 7004C §5.3+§5.4 (Fig 8 used as C^2, p.33); inside Table 1 empirical range (C^2<5 covers 80% of cases) | H |
| D4 | fb, n | fixed-base bounce 120.0 Hz, n=1 | Hz,- | 7004C Eq 2b defaults p.30 | M |
| D5 | Moment limit (arm iii) | octave-band peak-hold envelope of flight |My|^2 PSD | (N m)^2/Hz | 7004C §5.8 coupled-analysis envelope method, applied to the moment channel | H |
| D6 | Shaker | rigid, uniform base motion, single (vertical) axis | - | idealized hard-base test, the 7004C overtest premise | - |

## Data / replication statement (AGENTS.md assumptions gate)
Zero measured datasets. Everything is closed-form/deterministic model output; no noise
is injected, no test-to-test or flight-to-flight variability is modeled, nothing is
inferred (no priors, no posterior, no hyperparameters — D1). "Flight" in EX-D is a
labeled HYPOTHETICAL coupled simulation, not flight data. The only external truth
anchors are the 9 published 7004C numbers (decisions_log D3).

## Known limitations (stated up front)
1. Plate model carries bending only; in-plane (membrane) backing compliance and lateral
   foot loads are absent (D4/C4). The rocking/notch-geography conclusions concern
   vertical/rocking behavior.
2. The complex-TDOF Appendix C tables are not replicated (image-only PDF, D3).
3. Single deterministic damping values; no uncertainty propagation (this study teaches
   mechanisms; the Bayesian layer lives in the main project threads).
4. Simply supported boundary is idealized; real backing impedance varies — EX-C runs a
   plate-thickness sensitivity arm (3.5 mm / 5 mm / 8 mm) to show conclusion robustness.
