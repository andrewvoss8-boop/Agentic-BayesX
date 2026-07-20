# assumptions_ledger — MODEL-FORM PILOT (numerical values, units, rationale, source, sensitivity priority)

## Data / folds (all inherited read-only; no new data possible — ShockSat is archive-only)
| item | value | source | sensitivity |
|---|---|---|---|
| Dev drives (LODO folds) | m_xpos_990x, m_zpos_990z, m_ypos_990y, m_zpos_900z | study `data/multiref_wide/*_wide.npz` (bit-validated vs raw, Gate W provenance) | high — 4 folds is the whole SE budget |
| Vault | m_xy_990xy — NEVER read | card §3 | n/a (guarded) |
| Data count | 4 dev drives × ~100–130 usable channels × 2.03 Hz bins, 45–500 Hz; single test campaign; NO test-to-test/build variability available or modeled | study source_register | high — single-campaign fitting risk is why the stop condition exists |
| Coherence mask | median in-band coherence ≥ 0.6 | study Q1 | low |

## Model / scoring (inherited conventions)
| item | value | source | sensitivity |
|---|---|---|---|
| Baseline FEM | inherited remesh model, 67,683 nodes, 406,098 full DOF, ~399,510 after MPC elimination | fem_remesh workspace | — |
| θ parametrization | 9 group log-stiffness scalings (bottom_box, steel_welds, top_box, al_welds, angle_brackets, cross_beam, plates, joints, contact); bush_99 fixed | psd-twin groups.json | — |
| θ prior | log-normal, σ = 0.25 (dimensionless stiffness scale) | inherited (all runs) | medium — S5 fragility was shown across σ; not re-tested here |
| θ_MAP (loop) | S0-form: Gaussian on paired eigenvalues, sd = 5% of target λ; survey .ash only; 5 deterministic starts (seed 20260706) | femlib.Package.theta_map (validated, D19) | medium |
| Eigensolve | sparse shift-invert eigsh, σ_shift = −1e3 (rad/s)², k = 200 modes (~covers ≥500 Hz), float64, BLAS threads pinned to 1 | study K_OWN / compute protocol | high for runtime, low for score (enrich self-consistency ≤0.01%) |
| Forward | windowed 𝒲 + survey ζ interp (band-median above 257.6 Hz); viscous 2ζωωᵢ convention | wide_forward.py | — |
| Damping ζ | measured survey per-mode (~0.4–2.5%), fixed; NO fitting | survey table | low (H3: not the lever at 2 Hz) |
| RBM split | modes < 10 Hz = rigid (numerical RBMs at 0.4–1.2 Hz; first elastic 54.6 Hz) | femlib | low |

## Edit-class grammar (menus shared by BOTH tracks; numbers pre-registered here)
| class | operator | parameter ranges (units) | rationale / source |
|---|---|---|---|
| connectivity | rbe2_soften (existing, validated) | 1–20 spiders of 150; k_trans ∈ 10^[4,7] lbf/in; k_rot ∈ 10^[3,6] in·lbf/rad | true-remodel loop grammar (unchanged) |
| connectivity | rbe3_convert (NEW) | 1–20 spiders; uniform master weights; reference DOFs → least-squares rigid fit of master translations (linearized standard RBE3) | review next_steps item 6 family 2/3; V-gate Q6 |
| mesh_density | refine (existing) | 1–2 shell PIDs; conforming 2×2 quad / 4× tria; hanging-node MPC ties; ≤8000 refined quads | true-remodel loop (validated V2/V3) |
| element_formulation | formulation (NEW) | per-PID: bend_ratio scale ∈ [0.7, 1.4] (–), and/or ts_t set ∈ {0.35, 5/6, 5.0} (–; 5/6 = Mindlin default, 0.35 = shear-soft, 5.0 → Kirchhoff-limit); mass unchanged | exposed fe_core knobs (mitc4_bending Db ∝ bend_ratio, Ds ∝ ts_t); V-gate Q6. NOTE: all 18 PSHELLs currently 1.0 / 0.8333 (verified) |
| geometry | warp_panel (NEW) | pid ∈ flat panels {102, 106, 202, 206, 401, 701} (rms plane dev = 0, verified); bubble-shaped normal displacement, amp: \|amp\| ≤ min(2·t_pid, 0.25) in, zero at panel boundary (shared nodes unmoved) | plate flatness/warp within plausible build tolerance; V-gate Q6 |
| geometry | joint_offset (NEW) | translate a bracket/joint interface node set (chosen RBE2 spiders' nodes + nodes within r = 0.75 in of each reference) by vector \|d\| ≤ 0.35 in (≈1 element edge, pid 701 edge ≈ 0.28 in). DATED NOTE 2026-07-16 (D2, pre-science): displacement cosine-BLENDS from full inside 0.75 in to zero at 3.0 in — the first V-gate run showed a hard cutoff inverts boundary quads | joint placement tolerance; V-gate Q6 |
| property_control | thickness (existing) | 1–3 PIDs; t_scale ∈ [0.6, 1.6] (membrane ∝ t, bending ∝ t³, mass ∝ t) | control class (the one the model-form classes must beat) |
| property_control | scale (existing) | group stiffness factor ∈ [0.5, 2.0] | control class |

## Inferred vs fixed
- **Inferred (deterministic MAPs only):** 9(+extra-block) θ stiffness scalings per candidate (survey
  S0-form); finalists additionally get per-fold amplitude-trained θ_MAP (train drives only).
- **Fixed:** damping (measured), mass except where physics dictates (thickness/geometry reassembly),
  window operator, warp/gain machinery, grammar menus, quotas, seeds.
- **Latent, NOT inferred:** posterior uncertainty on θ (NO SAMPLER — see question_framing §5); model
  discrepancy (absorbed by the correlation metric's shape-only reading); forcing uncertainty (H1
  estimator, force-referenced).
- **Uncertainty types:** parameter (θ MAP-only, unquantified), observation noise (coherence-masked),
  model-form discrepancy (THE quantity under test), aleatory/build variability (absent — single build,
  single campaign; stated limitation).

## Random track
Seeded stratified sampler over the SAME menus: seed_base = 20260716; per round r and class slot i,
seed = 20260716 + 1000·r + i (recorded per candidate in `out/seeds.json` + query log). No diagnosis,
no learning.

## Compute assumptions
16 GB Mac, CPU float64, serial, 1 candidate per process; expected ~500–950 s per k=200 eigensolve at
~400k DOF (Card A measured mean 950 s incl. swap events); ~120 scoring solves + V-gates + ~16 finalist
fold solves ⇒ ~20–32 h wall, detached, resumable per candidate. Runtime accounting per AGENTS gate.

## Finalist per-fold amplitude refit (dated addendum 2026-07-16, written BEFORE the finalist stage ran)
| item | value | rationale |
|---|---|---|
| Objective | per-channel log10\|H1\| Gaussian residual on the 3 TRAIN drives, whole certified band, coherence-masked; ONE global gain per drive PROFILED out (mean offset — the Q1 gain convention) | arm-B likelihood form at MAP; no per-channel/per-mode fitting |
| σ_e | 0.5 dex, FIXED | order of the study's realized model-form floor (0.73 dex) minus alignment; fixed to keep the refit deterministic |
| Prior | lognormal σ = 0.25 on θ_total = θ_MAP,survey · θ′ | inherited program prior, applied to the TOTAL scaling |
| Starts | 5 deterministic (zeros + 4 from rng(20260716), sd 0.1 in ln θ′) | multimodality guard |
| Basis for fitting | the candidate's enriched (exact-at-survey-θ_MAP) reduced basis; SCORING uses a fresh per-fold EXACT enrichment at θ_total | fitting is train-side; scored numbers stay exact-basis |

## Sensitivity priorities (what most likely changes the decision)
1. Selection convention for HQ1/HQ2 (best-of vs mean) — both pre-registered and reported.
2. Fold instability (4 folds only) — per-fold deltas printed for every headline number; stop condition.
3. Operator ranges (e.g. warp amplitude cap) — class verdicts state the tested range; a null is "null
   within the pre-registered range," never "null in general."
4. θ_MAP multimodality — deterministic multi-start (≥5) per candidate; finalists re-fit per fold.
