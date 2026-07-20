# Card E — richer model form through L5 → does held-out QOI at the 8 hard accels sharpen? — decisions log

**One-line state (update before risky steps / after each human decision):**
2026-06-19 — Re-grounded from AGENTS.md + Card D + Card A. Goal = does ENRICHING the model form (richer LOCAL
stiffness parameterization and/or non-proportional damping), run through the converged L5 modal-feature NUTS
pipeline, measurably SHARPEN the held-out-sensor QOI (interval score/CRPS) at the 8 hard accels while staying
calibrated (cover≈0.95, z-std≈1) WITHOUT degrading other channels, across the ≥25-split MC? Next action =
identifiability gate FIRST (cheap, reduced 74-DOF) on candidate split parameters, before any NUTS/MC.

---

## D0 — Inherited constraints (carried from the card + parent threads; do NOT re-derive)
- **Plain standalone 9-group ShockSat ONLY** (no coupled tray). COPY-never-edit inherited FEM/code; richer
  parameterization applied programmatically on copies.
- **The failure (Card D / Card A):** across a 25-split MC, 7 channels consistently miss the L5 held-out 95% band
  on per-sensor AMPLITUDE — ch4, 27, 38, 40, 52, 69, 98 (impact +X face, box column near bulkheads / bolted
  joint, dish). ch92 (strut) is in the region list but NOT in the confirmed-fail-7 → labeled *suspected*.
  Bad-DAQ ch29–31/101 already excluded. L5 twin = calibrated but WIDE (≈×2.7 amplitude band) there.
- **RULED OUT rigorously (do NOT redo):** (a) finer mesh — FEM already mesh-converged; (b) missing topology —
  bulkheads/bolted joint/struts all present; (c) the COARSE 9-group stiffness-multiplier update — full 9-θ scan
  (6000 samples, re-pairing-robust tracked metric) found 0/6000 improving hard-region shape without a frequency
  penalty (nominal FEM Pareto-optimal in that family; `data/cardD/joint_frontier.json`).
- **The opening (honest scope limit of (c)):** the 9 group multipliers can only *uniformly rescale* existing
  substructure moduli; they CANNOT change LOCAL interface kinematics that set a local mode shape. That is a
  *parameterization* limit, NOT a fundamental model-form limit. The model form is ours to change.
- **Positive prior evidence (Card A D22):** inferring the mode-shape FIELD directly (Beck mode-matching-free on
  the `.ash` shapes) SHARPENED held-out amplitude ~19% (interval 671→545, calibrated, R̂ 1.004, 0 div). Enriching
  the shape representation demonstrably improves held-out-sensor prediction; question = does a *physically-
  parameterized* richer model form do too?
- **THE CONFOUND (state it, design around it):** resonant peak amplitude at sensor s is
  |H_peak| ∝ φ_{s,k} φ_{d,k} / ζ_k = participation ÷ damping. At a SINGLE impact (one drive node) participation
  and damping are CONFOUNDED — a wrong amplitude is explained equally by wrong shape or wrong damping. A single-
  impact fit cannot uniquely attribute the residual; the decisive *data* lever is multi-reference / roving-hammer
  (a 2nd drive varies φ_d, fixes ζ). The MODELING question (can a richer model form sharpen the held-out QOI) is
  still open and is the task — but every result is reported in light of this confound.
- **Damping data hygiene:** `.ash` `damp` (~0.06–1.05% if ÷100) disagrees with authoritative free-free **xlsx**
  damping (0.12–1.76%, bulkhead drum modes most-damped) by ~65× → use the **xlsx** as calibration target,
  documented. (Card D damping gate: damping design matrix is near rank-deficient, cond ~6e6, one near-zero
  singular value → damping params weakly separable; lands on high-SE box/bulkhead/cross shells, NOT joint CBUSH.)

## D1 — How a richer parameterization is built (engineering recipe, verified-reconstructible)
- Reduced model: `K(θ) = A_fix + Σ_g θ_g A_g` (74×74, mass = I), basis `W = T @ V_keep[:, 6:]` (full→74 elastic
  modes; 6 rigid-body removed). Per-group block `A_g = Wᵀ K_g W`. Source: modal-twin `scripts/reduce_model.py`.
- **Per-PID reduced block** `B_pid = Wᵀ K_pid W` (K_pid = per-PID full-order sparse stiffness, modal-twin
  `matrices/K_*.npz`). A richer parameterization just REGROUPS the 26 per-PID blocks into more sub-groups;
  θ=1 reconstructs the identical nominal K (integrity check: Σ_pid B_pid == A_g and Σ all == nominal eigvals).
- **Why this is cheap + decisive:** for the eigenvalue (L5) likelihood, ∂λ_r/∂θ_g = φ_rᵀ A_g φ_r = λ_r·f_{r,g}
  (Hellmann–Feynman; mass-normalized) — so the modal strain-energy fraction f_{r,g} IS the FIM sensitivity. The
  identifiability gate is therefore directly computable in the reduced 74-DOF space (~24 ms/eigh).
- **Discrete interface compliance (added CBUSH/offset DOFs)** is a genuine topology/model-form change requiring
  full re-mesh + ~290 s full-order re-solve + basis rebuild — flagged as the expensive option; the cheap,
  rigorous path is (a) per-PID split + (optionally) a non-proportional damping model.

## D2 — Identifiability gate run on the richer parameterizations (cheap, reduced 74-DOF) — KEY scoped finding
- **WHAT:** built per-PID reduced blocks (`out/perpid_reduced.npz`), verified reconstruction (`out/integrity.json`:
  group 6.2e-12, nominal eigval 6.4e-10 ≤ 1e-9 → richer params reconstruct nominal EXACTLY), defined 4 variants
  (`out/param_variants.json`: base9 / box_split 13 / joint_split 10 / full_rich 16), ran the AGENTS modal-
  identifiability gate (strain-energy fraction + FIM eigen view + finite-perturbation load-path check) at the
  realized L5 floor σ_w2=0.0446 (`out/identifiability_rich.json`). 27 matched modes (of 44 measured).
- **FINDING (scoped to the L5 FREQUENCY observable, 27 matched modes, 1 impact):**
  - The split is a MIX, NOT a uniform negative. full_rich (16 params): **8 FIM combos clear the prior precision
    (16); 12/16 raw params have peak strain-energy above the floor.** Genuinely NEW identifiable local
    directions appear: `bottom_box:shell_101`, `top_box:shell_201`, `plates:shell_701` (sv 19.5 — a strong new
    direction the coarse "plates" group lumped), `plates:shell_601`, `cross_beam`.
  - **Bolted joint (CBUSH 801) split is MARGINAL/prior-dominated:** its FIM combo singular value is right at the
    prior boundary (sv 4.04 @floor 0.045 → 2.61 @0.069 → 1.80 @0.10; FIM-eigenvalue threshold = 16). It flips
    above/below as the (split-dependent) discrepancy floor moves → NOT robustly identifiable from single-impact
    frequencies. Confirms Card D (joints store ~3% SE). Splitting it cannot robustly sharpen, only widen.
  - **Non-identifiable shells (peak SE < floor, only in weak combos sv<1):** `shell_103`, `shell_203`,
    `plates:shell_501`, `al_welds`, `steel_welds`, `contact` → splitting these adds WIDTH, not sharpness.
  - The FIM combos MIX raw shells (e.g. shell_101 mixes with shell_201) → "16 free params" overstates it; the
    data constrains ~7–8 directions. So a PARSIMONIOUS variant (split only the identifiable locals; lump the
    rest) is the principled cleanest test and avoids the non-identifiable-param width penalty.
- **MECHANISM tie:** ∂λ_r/∂logθ_p = φ_rᵀ A_p φ_r = λ_r f_{r,p} → SE-fraction IS the FIM sensitivity. A param
  below the floor is prior-dominated; its posterior ≈ prior; it widens the held-out prediction.
- **STATUS:** GREEN (gate complete, scoped). It does NOT by itself decide sharpen vs no-sharpen — identifiable-
  from-FREQUENCY ≠ sharper-AMPLITUDE, because the held-out ×2.7 width is set by σ_QOI (the observed-channel
  AMPLITUDE residual = the participation/damping confound), which frequencies don't directly fix. → MUST measure
  the held-out before/after empirically (P3/P4).
- **PRE-TEST LEVER for the non-identifiable params:** multi-reference / roving-hammer data (2nd drive varies φ_d,
  breaks the participation/damping confound) and/or mode-shape (eigenvector) observations — not more
  eigenfrequencies.

## D3 — L5 BASELINE held-out QOI reproduced in this workspace (the BEFORE)
- **WHAT:** ran `heldout_qoi.run(seed=0)` (copied pipeline) from the new ws. Calib CONVERGED R-hat 1.002,
  ESS 1269, σ_w2 0.0446; overall held-out PEAK coverage 0.935, interval 1661, CRPS 100.8 — consistent with
  Card A 25-split baseline (cover 0.879, interval 2132). Hard accels held out this split: ch40 (peak NOT covered,
  interval 5012), ch98 (peak NOT covered, interval 2237). Confirms the "wide-but-MISSING" failure as the BEFORE.
- **STATUS:** GREEN — pipeline reproduces; σ_w2=0.0446 adopted as the realized discrepancy floor for the gate.

## D-template — each subsequent entry: WHAT changed / WHY / EVIDENCE (file) / STATUS (green/yellow/red) / scope
