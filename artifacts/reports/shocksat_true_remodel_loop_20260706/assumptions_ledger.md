# Assumptions Ledger — ShockSat TRUE Agentic Remodeling Loop (20260706)

Value, units, rationale, source, sensitivity priority (HIGH = likely to change the S1/S2 verdict; MED; LOW).
Distinguish parameter uncertainty vs observation noise vs model discrepancy vs forcing vs BC uncertainty.

| # | Assumption | Value / units | Rationale | Source | Sensitivity |
|---|---|---|---|---|---|
| A1 | Modal damping ratio | ζ = 0.01 (1%) all elastic modes | Consistent with prior ShockSat twin work; screening/selection is on log\|H\| SHAPE correlation, weakly sensitive to a uniform ζ (peak heights move together, corr near-invariant). | psd_envelope/netcg threads | MED |
| A2 | Selection likelihood gain | ONE global real gain g per fold, fit on train by least squares on log\|H\|; NO per-mode/per-channel amplitude or phase fit | Card §4.3 physics-honest rule; the per-mode LSQ "trap" inflates apparent fit (notes/memory 2026-06-26). | card §4.3 | HIGH (the anti-cheating rule) |
| A3 | Correlation band | 45-260 Hz | Covers 54.2 Hz fundamental, 158-233 Hz hard-region local modes, 234-258 Hz drumhead edge; below 45 Hz is rigid-body/suspension, above 260 Hz is out of the reliably distilled band. | netcg band choices; cache freq vectors | MED |
| A4 | Frozen Hungarian pairing | 1:1, DF_forbid 0.18, computed ONCE per model | pairing.py; prevents greedy MAC re-pairing churn (historic trap, card §2). | pairing.py | HIGH (churn = false gains) |
| A5 | Reduced basis validity | Frozen 74-elastic-basis ONLY for parametric-θ (family 5); shape-changing edits full-order or per-candidate enriched basis validated <=0.3% | reduce_model.py is inherited-basis; card §6 reduced-basis trap. | decisions_log D2 | HIGH (scoring shape edits in wrong basis = fabricated gain) |
| A6 | Thickness physics | membrane stiffness ∝ t, bending ∝ t^3, scaled SEPARATELY via fe_core element reassembly; modulus-only scale tagged `modulus` not `thickness` | fe_core.qm6_membrane (∝t) + mitc4_bending (∝t^3). | decisions_log D3; fe_core.py | HIGH (family-3 validity) |
| A7 | Dev observation model | per-channel log\|H\| residual treated iid-Gaussian across freq for the global-gain fit; scoring is correlation (scale/offset invariant) | keeps selection cheap + scale-free; correlation ignores the gain, so the gain only affects P2 (dB). | this run | LOW |
| A8 | statFEM output discrepancy F(k) | netcg form (QOI-aware, freq-correlated); σ_d, ell as inferred in netcg | reused only for the finalist Q leg. | netcg packet.md | MED (Q leg only) |
| A9 | Vault coherence usability gate | median coherence at response channels >= 0.6 in 45-260 Hz | below this the distilled vault FRF is not trustworthy -> fallback (a). | card §4.1(b) | HIGH (vault validity) |
| A10 | Free-free BC | soft-suspension free-free; 6 rigid-body modes excluded from the elastic superposition | matches modal survey; V2 checks 6 RBM ~ machine zero. | measured_modes, fe_validate | HIGH (V2 gate) |
| A11 | Random-track seed | 20260706 (fixed) | reproducible S2 comparator. | card §4.2 | LOW |
| A12 | Full-order eigensolve budget | <= 80 total, logged, detached, resumable; each ~6 min sparse eigsh | reduce_model docstring (~6 min); card §6 step 3. | reduce_model.py | MED (runtime) |

## Data counts (Assumptions/Uncertainty Gate)
- Drives available as distilled caches: 5 (m_xpos_990x, m_zpos_990z, m_ypos_990y, m_xy_990xy, m_zpos_900z).
  Dev fold set uses 4 (Test04/+XY reserved as fallback vault); each cache is hit-averaged (n_hits 4-6) per-channel
  H1 with coherence. Channels: 111 (+X cache) up to ~228 observed translational DOFs across 76 instrumented nodes.
- Modal survey: 33 measured modes on 76 nodes (measured_modes.npz), used TRAIN-side only.
- Variability modeled: test-to-test enters via the leave-one-DRIVE-out folds (drive-location generalization) and
  the vault (fresh test at a known drive). Build-to-build / flight-to-flight variability is NOT modeled (single
  article, single build) — stated as a scope limit.

## Inferred vs fixed vs not-inferred
- **Inferred (finalists+A0, NUTS):** 9-group θ (stiffness/thickness multipliers), statFEM F(k) hyperparameters
  (σ_d, ell) for the Q leg.
- **Inferred (selection, MAP/deterministic, NO-sampler):** θ_MAP per candidate per fold, one global gain per fold.
- **Fixed:** ζ = 0.01; frozen pairing; band 45-260 Hz; accelerometer-mount group (bush_99) θ=1; free-free BC.
- **Not inferred (latent, held fixed):** per-mode amplitudes/phases (deliberately NOT fit — the anti-LSQ rule);
  input force magnitude (absorbed into the global gain); mesh geometry of unedited regions.

## Uncertainty taxonomy (which is which, per AGENTS gate)
- Parameter uncertainty: 9-group θ posterior. Observation noise: per-channel FRF measurement + coherence.
  Model discrepancy: statFEM F(k) (the irreducible per-node shape error, the standing "wall"). Forcing: flat
  known input PSD for the QOI; impact force absorbed into gain for P1/P2. BC uncertainty: free-free suspension
  (small). QOI uncertainty: net-CG band. Aleatory build/test variability: NOT modeled (single build) — scope limit.
