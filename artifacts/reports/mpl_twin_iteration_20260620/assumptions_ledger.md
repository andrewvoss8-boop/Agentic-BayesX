# Assumptions ledger — MPL twin iteration

Values, units, rationale, source, sensitivity priority. Flags: CONFIRMED (Andrew), ESTIMATED, ANDREW-CONFIRM
(defensible default chosen under D-D autonomy; surfaced for confirmation but not blocking).

## Data / observable
| id | value | units | rationale | source | sens. |
|---|---|---|---|---|---|
| A-fs | 10 000 | Hz | sample rate, all CSVs | run_mapping A (CONFIRMED) | low |
| A-axis | OOP of shield = +X | — | sensor axis every test/setup | Andrew A5 (CONFIRMED) | high |
| A-sensor | MMF KS78C, 100 mV/g, ±100 g (rail ≈981 m/s²) | — | gain-free ratio justification | Andrew A6 (CONFIRMED) | med |
| A-acoustic-fixed | speaker pos/volume fixed across ALL acoustic runs | — | makes cross-file |T| valid | Andrew A7 (CONFIRMED) | high |
| A-ref | SHIELD = transmissibility reference (always trained) | — | always-present, well-excited station | D-C (CONFIRMED) | high |
| A-band | QOI band ≈ [3, 260] Hz (refine in observe) | Hz | features resolved here; >260 Hz local/near-field | features.md, L5 lesson | high |
| A-welch | Welch PSD: window/nperseg/overlap from segment length, detrend='constant' | — | spectral-estimate contract (Discretization Gate) | set+documented in mpl_observe.py | high |
| A-seg | acoustic segments (s): interface[14,76] shield[11,71] beam[12,47] valve[29,80] aviL[19,72] aviR[19,64] | s | usable pink-noise windows | run_mapping (CONFIRMED) | med |

## FEM node map (X-DOF = OOP). Defensible defaults; ANDREW-CONFIRM where ambiguous.
| location | FEM grid | xyz (in) | flag |
|---|---|---|---|
| interface (top-center) | 800071 | [61.5,−24,48.5] | CONFIRMED (shield_mount) |
| shield REFERENCE (middle) | 800016 | [61.5,−24,26.83] | ANDREW-CONFIRM (nearest shield grid to shield centroid; "shield middle") |
| beam (top-left post) | 1510 | [60.25,−48,46.55] | CONFIRMED (beam_mount) |
| valve body | valve_panel node nearest frame centroid | ~[50,−12,9] | ANDREW-CONFIRM (which valve node = "valve body"; weak SNR per run_mapping) |
| avi-L (top-left foot) | 800036 | [61.5,−14.4,35.5] | ANDREW-CONFIRM (avi box = electronics_box on shield; LEFT = more −y by "+X view, left=−y") |
| avi-R (top-right foot) | 800034 | [61.5,−4.8,35.5] | ANDREW-CONFIRM (RIGHT = less −y) |

Note: "avi box" = electronics_box (avionics, mounted ON the shield via grids 800024/800034/800036); white_box_upper
(2 frame grids 1 in apart) rejected as the L/R-feet source. The foot accel measures the SHIELD's OOP motion at the
bolt grid (the box itself is a lumped CONM2). Sensitivity: HIGH (defines the held-out QOI) — surfaced to Andrew.

## Forward model
| id | value | rationale | source | sens. |
|---|---|---|---|---|
| F-load | acoustic load shape f = uniform OOP (X) pressure on shield exposed grids | simplest defensible diffuse-field default; γ_i=φ_i^T f; residual absorbed by log-f discrepancy GP | quantity_contracts Q2 | high |
| F-zeta0 | nominal modal damping ζ = 1% all modes | starting damping; a model-class lever (D-F) | L5 default | high |
| F-modes | 184 modes < 500 Hz (use all in band + a margin past 260 Hz for tails) | modal superposition completeness | modes_nominal.json | med |
| F-units | inch-lbf-second (FEM); observable dimensionless ⇒ unit-agnostic | — | meta.json | low |

## Inference
| id | value | rationale | source | sens. |
|---|---|---|---|---|
| I-params | parametric K(θ)=A_fix+Σ θ_g A_g, 14 K-groups + 8 M-groups (θ=1 nominal) | reuse fable per-group assembly | meta.json | — |
| I-sampler | NUTS default (≥4 chains, non-centered); R̂≤1.05, ESS≥200, div<2%; TMCMC for Stage-2/multimodal | AGENTS NUTS + convergence gate | AGENTS.md | high |
| I-disc | discrepancy GP over log-frequency on log\|T\|; iid vs freq-correlated vs region-structured (a lever) | statFEM/Kiran/Schneider | refs | high |
| I-splits | 5 leave-one-location-out over {interface,beam,valve,avi-L,avi-R}; shield always trained | D-C | CONFIRMED | high |

## Coupled-ruler robustness (separate, D-E)
| id | value | source |
|---|---|---|
| R-ruler | pinned: k_tip≈12.9 N/m, EI≈0.122 N·m²; solo f1=3.196 Hz, coupled f1=3.078 Hz (−7.7%) | features.md (CONFIRMED) |
| R-deadmass | coupled dead mass on shield top edge = clamp 417.3 + ruler 43.9 + accel 22.4 = 483.6 g | features.md (Andrew) |

## Data-count / variability
- 13 CSVs, single MMF sensor moved sequentially, single OOP axis, NO instrumented force. 1 acoustic field
  realization per location (n_avg ≈ 20–24 Welch segments WITHIN a location's pink-noise record). Tap records:
  3 taps/group. NO test-to-test repeat except the solo-ruler re-clamp (excellent repeatability).
- Aleatory across-impact / build-to-build variability NOT separately measurable here (single build, single field).
