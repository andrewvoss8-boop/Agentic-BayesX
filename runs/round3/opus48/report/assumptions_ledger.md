# Assumptions Ledger — Round 3 (Claude Code Opus 4.8 runner)

Values, units, rationale, source, sensitivity priority. "Inferred" = learned by NUTS; "Fixed" = held.

## Engineering decision being supported
Does the existing random-vibration TEST SPEC envelope the in-flight coupled environment of a
136 kg avionics tray mounted (no isolators) on a pressurized dome, across frequency and flights — and
where does the force-limited netCG QOI peak relative to the spec? Success metric: per-flight
spec-covers-flight verdict using ONE standardized envelope band (central 99% q0.5–q99.5 + one-sided
99%-hi exceedance fraction). What optimization/agent may choose: model form, mode basis, grid,
sampler settings. Human judgment: anchor values, acceptance of the effective↔physical mass mapping,
final qual decision. The framing is WRONG if absolute force scale (abstract in the staged data) is
treated as physical, or if a scalar 3·GRMS margin is used in place of the band check.

## Material / geometry
| # | Quantity | Value | Units | Inferred/Fixed | Rationale / Source | Sens. priority |
|---|---|---|---|---|---|---|
| 1 | Dome material | Al 2219 (E=73.1e9, ρ=2840, ν=0.33) | Pa, kg/m³ | Fixed | spin-formed Al tank dome | low |
| 2 | Dome equatorial radius R | 2.75 (5.5 m dia) | m | Fixed | task card (~18 ft stage) | low |
| 3 | Dome cap height | 1.40 (2:1 ellipsoidal ≈ R/2) | m | Fixed | task card | low |
| 4 | Dome meridian strip length | 2.50 | m | Fixed | quarter-meridian arc estimate | med |
| 5 | Dome wall thickness | 0.0060 (TUNING KNOB) | m | Fixed | tuned with pressure to hit anchor | med |
| 6 | Dome internal pressure | 3.5e5 (3.5 bar, F9-like) | Pa | Fixed | task card (3–6 bar; F9 ~3–4) | **high** |
| 7 | Tray material | Al-Li 2198 (E=70e9, ρ=2700) isogrid | Pa, kg/m³ | Fixed | task card | low |
| 8 | Tray panel size | 0.70 × 0.70 | m | Fixed | representative avionics tray | low |
| 9 | Tray bending eq. thickness t_bend | 0.024 | m | Fixed | isogrid = stiff (flex modes ≫ joint) | med |
| 10 | Tray mass eq. thickness t_mass | 0.0045 | m | Fixed | isogrid = light (panel ≈ 5.95 kg) | low |
| 11 | Avionics mass | 136 (≈300 lbm) | kg | Fixed | task card | med |
| 12 | Load mass m_load (netCG denom) | 141.95 (136 + 5.95 panel) | kg | Fixed | tray total | **high** |
| 13 | Avionics distribution | LUMPED at panel centre | — | Fixed | conservative for 1st flex mode (stated) | low |

## Dynamics (anchors, damping, masses)
| # | Quantity | Value | Units | Inf/Fix | Rationale | Sens. |
|---|---|---|---|---|---|---|
| 14 | Dome mode-1 (interface) | 93.50 | Hz | Inferred (prior @110) | HARD anchor (round-2 truth). CORRECTED: this is the global axisymmetric BOUNCE/BREATHING mode (~110 nominal, 93.5 as-built=0.85×110), whole top shell translating axially — NOT a local mount mode (earlier framing retracted, see known_failures §4) | **high** |
| 15 | Tray mode-1 (joint bounce) | 86.25 | Hz | Inferred (prior @75) | HARD anchor; set by SOFT JOINT + load mass | **high** |
| 16 | Dome ζ₁ | ~0.0225 | — | Inferred | anchor; round-2 truth 1.25×0.018 | med |
| 17 | Tray ζ₁ | ~0.0195 | — | Inferred | anchor; dominated by JOINT loss | med |
| 18 | Dome effective interface modal mass m1_eff | 1.0 (code) / ~150–250 physical | kg | Fixed | ABSTRACT staged-2DOF value used by the code for data-consistency; PHYSICAL bounce-mode effective mass is ~150–250 kg (comparable to load) — WRONG by ~2 orders in the code; flagged re-run candidate (known_failures §4) | **high** |
| 19 | Tray effective interface modal mass m2_eff | 0.6 | kg | Fixed | staged-data effective interface mass | med |
| 20 | Implied joint stiffness k_j | 4.17e7 total (1.39e7/strut, 3 struts) | N/m | Derived | = m_load(2π·86.25)²; ~5× softer than bare strut EA/L (7e7) → plausible compliant clevis/rod-end | **high** |
| 21 | Dome MDOF higher modes | ratios [1, 3.01, 5.06, 7.17, 9.37, 11.66]×93.5 | Hz | Fixed (FEM) | tensioned-membrane (pressure-dominated) mode family | med |
| 22 | Tray panel flex modes | 377, 1632, ... | Hz | Fixed (FEM) | ≫ joint → joint is the softest spring | low |

## Uncertainty / variability (rounds 1–2 carry-over + new)
| # | Quantity | Value | Units | Inf/Fix | Rationale | Sens. |
|---|---|---|---|---|---|---|
| 23 | Flight-to-flight forcing | 3.0 | dB(PSD) | Fixed | known; Matérn-3/2 GP in log-PSD | med |
| 24 | Matérn length scale ℓ | 0.08 (log-freq) | — | Fixed | staged data; **sensitivity swept** (0.04/0.08/0.16) | **high** |
| 25 | Flight-mean forcing offset | −6.0 | dB(PSD) | Fixed | pre-data conservative DESIGN ENVELOPE (6 dB PSD=4×PSD=2×GRMS), NOT GEVS +3 dB, NOT +6 dB/oct; **swept** | **high** |
| 25b | ORIGINAL (+6 dB) flat force PSD | ~987 (flight −6 dB ≈ 248) | N²/Hz | Derived (reverse-engineered) | chosen so DOME-ONLY interface response peaks at 0.1 g²/Hz at the bounce mode (same process as round-2 original force, now on the physical dome). DEVIATES from round-2 abstract 0.0201/0.00506 | **high** |
| 25c | Dome bounce-mode participation | 0.40 (eff mass ≈225 kg of 563 kg cap) | — | Fixed | axial effective-mass fraction of the bounce mode (typical 0.3–0.5); **swept** (0.25/0.40/0.55 → netCG 0.77/0.90/1.15 g) | **high** |
| 26 | Build-to-build PSD effect | σ_build (HalfNormal 0.50 prior) | ln-PSD | Inferred | per-build dome & tray log-PSD offsets (non-centered) | med |
| 27 | Build-to-build fn scatter (per structure) | ±5% @3σ → σ=0.0167 lognormal | — | Fixed (generative) | NEW this round; applied to dome fn AND tray fn in PREDICTION | **high** |
| 28 | Build-to-build damping scatter (per structure) | ±5% @3σ → σ=0.0167 lognormal | — | Fixed (generative) | NEW this round; dome ζ AND tray ζ in PREDICTION | med |
| 29 | Sensor noise | σ_sensor (HalfNormal 0.30 prior) | ln | Inferred | per-channel measurement scatter | low |
| 30 | Flight forcing-induced QOI scatter σ_q | iface/tray (MC-integrated, fixed) | ln | Fixed | 3 dB GP integrated out by 4000-sample MC | med |

## Data count
- 1 tray vibe PSD curve (260 bins, build 0) + 3 modal FRF curves (180 bins each, build 0) + 11 flights
  × 2 scalar 3·GRMS (tray, interface). ONE synthetic realization (the staged 2DOF dataset).
- Build-to-build IS modeled (11 builds; PSD effect learned; fn/damping scatter fixed-generative).
  Flight-to-flight forcing IS modeled (fixed 3 dB GP). NO replicate vibe/modal tests (no test-to-test
  variability). netCG higher modes are NOT in the data (extrapolation beyond the data-informative band).

## Inferred vs fixed vs not-inferred (summary)
- **Inferred (NUTS):** f_dome, f_tray, ζ_dome, ζ_tray, σ_sensor, σ_build_dome, σ_build_tray,
  11×2 non-centered build latents (z_dome, z_tray).
- **Fixed:** masses (effective & physical), pressure, geometry, material, 3 dB f2f, −6 dB offset,
  Matérn ℓ, per-structure fn/damping build scatter (1.67%), MDOF mode ratios, g0.
- **Not inferred (latent, not learned):** model discrepancy (the staged truth is inside the 2DOF model
  family by construction); MDOF higher-mode amplitudes (FEM-fixed); absolute force scale (abstract).

## Uncertainty taxonomy
- Parameter uncertainty: f, ζ posteriors. Observation noise: σ_sensor. Model discrepancy: NOT separately
  modeled (in-family). Forcing uncertainty: 3 dB f2f GP (aleatory). Build/test variability: σ_build +
  fn/ζ scatter (epistemic+aleatory). BC uncertainty: dome grounded (fixed). QOI uncertainty: netCG
  intervals propagate parameter + build + forcing.
</content>
