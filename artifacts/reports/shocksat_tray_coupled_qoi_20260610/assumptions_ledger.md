# Assumptions ledger — shocksat_tray_coupled_qoi_20260610

Sensitivity priority: H = swept/varied in this study; M = probed or bounded;
L = documented, not varied (justified). INVENTED = no measurement or design
document behind it; exists to make the methods demo concrete.

| id | assumption | value (units) | rationale / source | prio |
|---|---|---|---|---|
| A1 | Mount CBUSH nominal stiffness (INVENTED) | k_tx=k_ty=k_tz = 2e6 N/m; k_rx=k_ry=k_rz = 2e4 N·m/rad | puts chain bounce/rock at ~95–130 Hz: in-band, ROM-valid, in the predecessor's joint-active 120–185 Hz band (D4) | **H** (prior + decade sweep 1e5–1e9 N/m) |
| A2 | Mount stiffness prior | independent LogNormal per axis, median = nominal, sigma_ln = 1.15 (95 % ≈ ×/9.5) | a payload mount is a joint; predecessor: joints unidentified from modal data → wide honest prior | **H** (it IS the hypothesis under test) |
| A3 | Mount damping | viscous; zeta_mount = 5 % referenced to nominal bounce mode (c = 2·0.05·sqrt(k_nom·m_eq) per axis) | typical bolted/elastomer-less joint guess; INVENTED | **H** (swept 2/5/10 %) |
| A4 | Tray structural damping | zeta_struct = 1 % all tray modes | typical bare machined-aluminum assembly | **H** (swept 0.5/1/2 %) |
| A5 | ShockSat modal damping | measured per-mode (.ash, 0.1–1.7 %) where paired via pairing.json; median of measured for unpaired ROM modes; RBMs zeta = 2 % (inconsequential: ≤1.13 Hz vs 20 Hz band edge) | predecessor measured data; assignment by nominal pairing | M (×0.5 / ×2 arm) |
| A6 | Rotational base input = 0 | a_free rotations ≡ 0 | net CG translational force is translation-dominated; no measured rotational environment exists anyway | L (logged gap; moment QOIs out of scope per D38) |
| A7 | Base input spec (INVENTED) | flat 0.01 g²/Hz, 20–250 Hz, 3 indep axes, T=20 s, fs=2048 Hz, 8 seeds | D2; linear-valid moderate random; Miles gets the analytic PSD so no SRS→PSD conversion knobs exist in this study (the card's SRS→PSD H-item is N/A by construction — stated, not skipped) | **H** (level is linear-scale-free; band edges probed; seed spread reported) |
| A8 | SRS Q | Q ∈ {10, 25, 50} | D38 "sweep Q"; Q is the method's assumption, decoupled from true chain ζ | **H** |
| A9 | Tray placement (INVENTED) | mount node = Top_Circular_Plate center (node id in out/mount_node.json); tray axes ≡ global axes | D3; natural top deck; footprint mismatch (20.8 in feet circle vs 18 in plate) noted — methods demo only | **H** (alternate edge-node arm) |
| A10 | Single-point 6-DOF condensation | all 6 tray feet rigidly tied to one massless virtual base point at (0,0,0) tray frame, CBUSH from there to P | D38 locked: sufficient for net CG force; per-mount loads/moments NOT recoverable | L (scope-locked) |
| A11 | Condensation hardware massless | no bracket/adapter mass | simplest demo; real adapter would add mass + lower chain modes | M (bounded: +0.5 kg probe in sweep) |
| A12 | Tray theta prior | LogNormal(0, 0.25) on 5 FIM stiffness multipliers | tray never tested → prior only; width matches ShockSat practice (FIM used sd 0.30 Gaussian — difference ledgered, immaterial vs A2 width) | M (varied jointly in MC) |
| A13 | ShockSat theta | 4000-draw converged NUTS posterior (predecessor theta_full, R-hat 1.022) reused as-is | the validated piece of the chain | M (varied jointly in MC; posterior-vs-nominal arm) |
| A14 | ShockSat config | FREE-FREE (validated test config), not flight-mounted | only validated configuration; C3 states the consequence for source apparent mass | L (config-specific conclusions flagged) |
| A15 | Linear regime | all components linear; input moderate (1.5 grms) | D38: linear-valid regime by construction; no pyro/nonlinear claim | L |
| A16 | Trusted band | 20–250 Hz (ROM validated <280 Hz; input zero outside) | C4 | M (df and band-edge probes) |
| A17 | Mode truncation | chain: ALL mass-carrying modes of the small tray model (full eigh, completeness sum rule); ShockSat: all 74 ROM elastic + 6 RBM | exactness within models; truncation lives in the ROM validity bound (A16) | L |
| A18 | Time-history reference = frequency-domain synthesis | zero-padded FFT convolution, edges discarded; Newmark cross-check <2 % | exact for LTI; D5 | M (verification artifact) |
| A19 | Unit conversion | 1 snail = 175.126835 kg, 1 in = 0.0254 m, g = 9.80665 m/s² (SI) / 386.088 in/s² (deck) | C8 + RBM mass-line checker | L (checker-backed) |
| A20 | Mount linearity | CBUSH linear spring-dashpot (no friction/gapping) | linear-regime scope; real joints micro-slip — out of scope | L |

### Overnight addendum (D10) — synthetic mounted-survey calibration

| id | assumption | value (units) | rationale / source | prio |
|---|---|---|---|---|
| A21 | truth mount stiffness (SYNTHETIC) | diagonal ~ one seeded draw from the A2 prior; PLUS off-diagonal coupling rho=0.15 on (tx,ry),(ty,rx), 0.05 on (tx,ty), as rho*sqrt(ki*kj); SPD-checked | real bolted interfaces couple translation/rotation; gives the inference model a feature it CANNOT represent = structured model-form discrepancy | **H** (it IS the discrepancy injection) |
| A22 | truth tray theta (SYNTHETIC) | one seeded draw from LogNormal(0,0.25) | tray never tested | M |
| A23 | truth theta_S (SYNTHETIC) | one seeded predecessor-posterior DRAW (row fixed in truth_lock) | honest remaining primary uncertainty | M |
| A24 | inference fixes theta_S at the posterior MEDIAN | 9 values folded into B_fix | keeps the sampler at 12 latents; the truth-vs-median gap (~posterior width) is real unmodeled variation absorbed by sigma_f — documented limitation, NOT inferred | M |
| A25 | survey noise | freq 0.3 % rel (predecessor impact-replicate floor median), shapes 2 % (pairing only), ONE realization | scrappy single modal survey | M |
| A26 | reduced coupled basis | union of full coupled modes <=350 Hz at mount multipliers {0.05,0.25,1,4,20}, M-orthonormalized, capped ~160 vectors; reduction gate <=0.5 % on modes <=300 Hz at anchors + truth point | spans the x/9.5 mount prior; keeps NUTS eigh tractable (~(nb/74)^3 x predecessor cost) | **H** (checker-gated) |
| A27 | pairing anchor | the mount-grid anchor {0.05,0.25,1,4,20} with max total MAC to the survey shapes ("engineer's coarse pre-match"), then Hungarian unique pairing, calib filter MAC>=0.5, abs(df)<=12 % | wide prior makes nominal-only pairing fragile; mirrors real practice | M (pairing report saved) |
| A28 | self-blinding is structural, not adversarial | run_nuts_mount.py reads ONLY survey_data.npz; truth params live in truth_lock.json (SHA-pinned), revealed only in posterior_qoi.py | single agent wrote both — stated honestly; no vault used | L |

**Data counts (Assumptions & Uncertainty Gate).** Zero measured datasets are
used as likelihood data in this task (no inference run). Inherited data:
ShockSat posterior (1 test article, 18 calibration modes, predecessor);
tray = pre-test FEM only (0 tests). Input environment = 8 synthetic seeds
(aleatory forcing realizations). Build-to-build / flight-to-flight
variability: ABSENT (no fleet exists; hypothetical single configuration).

**Uncertainty taxonomy as propagated.** Parameter uncertainty: theta_S
(posterior, 9), theta_T (prior, 5), mount k (prior, 6). Forcing/aleatory:
8 input seeds. Observation noise: none (no observations here). Model
discrepancy: NOT propagated as a term — the predecessor's sigma_f ≈ 4.6 %
frequency-level discrepancy is REPORTED next to results as a floor/caveat
(packet §8); QOI uncertainty bands are therefore parameter+forcing only and
are likely UNDER-estimates. Boundary-condition uncertainty: free-free source
fixed (A14). Inferred variables: none this task. Fixed-not-inferred: all of
A1–A20.
