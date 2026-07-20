# Card E — references reviewed (running list; expand as used)

## Parent-thread artifacts (this project)
- **Card D** `shocksat_fem_remesh_20260618/`: `decisions_log.md` (D0–D16 arc), `correlation_contribution.md`
  (scoped verdict: re-mesh/coarse-stiffness NOT the lever; residual = damping + near-field + freq-align),
  `region_diagnosis.md` + `out/region_diagnosis.json` (hard-channel→region/PID map), `damping_indicators.md`,
  `damping_modeling_review.md` (Das&Debnath 2020, Kiran 2025, Schneider 2022 review), `out/joint_frontier.json`
  (0/6000 coarse-stiffness Pareto exhaustion), `out/damping_gate.json` (damping design rank-deficient, cond ~6e6).
- **Card A** `statfem_real_validation_20260617/`: `packet.md` (§1 L5 method, §2 verdict), `decisions_log.md`
  D11 (L5 modal-freq likelihood CONVERGES R̂ 1.002), D12 (held-out-sensor QOI predictor), D20–D22 (mode-shape
  likelihoods; D22 Beck mode-matching-free SHARPENED held-out amplitude ~19%). Code reused: `modal_feature.py`,
  `heldout_qoi.py`, `realfrf.py`, `score.py`, `core.py`.
- **Modal-twin FEM** `shocksat_fem_modal_twin_20260609/`: per-PID K blocks (`matrices/K_*.npz`), reduction
  recipe (`scripts/reduce_model.py` → W = T@V_keep[:,6:], A_g = WᵀK_gW), `groups.json`, `measured_modes.npz`
  (33 `.ash` modes / 76 nodes + damping), `joint_strain_energy.json`.

## External method references (FE updating / StatFEM / damping)
- **Kiran et al. 2025** (FE model updating review) — §4.3.1 Eq 25: the modal/eigenvalue likelihood used by L5;
  "local identifiability" (Beck–Katafygiotis) framing for multimodal whole-FRF likelihoods.
- **Schneider 2022** — additive freq×space correlated discrepancy StatFEM (source of M2/M3 arms).
- **Das & Debnath 2020** — non-proportional damping form C = α0 M + α1 K + Σ_g β_g K_g (the localized
  group-stiffness-proportional damping model for P5).
- **AGENTS.md gates** — Modal/Eigenproblem Identifiability gate (strain-energy fraction + FIM eigen view),
  NUTS/HMC + Convergence gate, Plot/Tufte gate, Verification gate, Result-Status three-tier, Discretization gate,
  Compute/detached-launch gate.

## Authoritative measured damping (calibration target for P5)
- `ShockSat1_Instrumentation_and_TestLog_Simplified_for_Delivery_20220525.xlsx` (project root) — free-free
  modal damping 0.12–1.76% (bulkhead drum modes most-damped). Preferred over `.ash` `damp` (~65× discrepancy).
