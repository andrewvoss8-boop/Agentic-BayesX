# Findings — ShockSat TRUE Agentic Remodeling Loop (20260706)

Status source of truth: `checker_report.json` (immutable checker `d9cb1acd…`). Full detail: `packet.md`.

1. **PRE-REGISTERED CLAIM FALSIFIED (S1+S2+S3 all fail; valid outcome, pipeline intact).** A closed-loop
   agent with a genuinely shape-changing action space (true conforming refinement, region splits, physical
   t/t³ thickness fields, RBE2→spring joint compliance with 3,528 restored DOFs), steered by train-side
   diagnosis over 3 rounds under a 60-query dev budget, did not improve the inherited ShockSat FEM's
   held-out per-channel FRF correlation beyond its own calibration noise (best shape margin +0.022 vs the
   +0.05 pre-registered bar), tied-within-noise against equal-budget random search (0.2376 vs 0.2389), and
   no arm passed the net-CG shear coverage hard gate.
2. **Mechanism: held-out FRF ranking in this regime is dominated by θ-calibration wobble that the baseline
   family itself spans.** Parametric-only controls matched or beat every shape edit at each round; maximal
   split freedom went negative (survey overfitting); stacked "positive" edits interfered.
3. **Better survey-fit ⇒ worse held-out FRF, dev through vault.** The baseline's accuracy cascade
   (single-start→multi-start→exact basis: 0.234→0.224→0.215 dev; 0.476→0.438 vault) lowered held-out scores
   at every step — the modal-frequency objective does not transfer to FRF amplitude prediction.
4. **Two generic evaluation traps caught by our own pre-registered gates BEFORE the vault:** (a)
   reduced-basis score inflation (even A0 fails the 0.3% spot check at its own θ_MAP; exact-basis
   re-evaluation collapsed every inflated leader, incl. a parametric control that had transiently "passed"
   the S1 dev threshold at +0.059 → −0.014); (b) θ_MAP multimodality (identical models, different basins,
   ±0.035 dev-P1) — fixed with deterministic multi-start.
5. **Family-level honest negatives:** bolted-joint compliance neutral; evidence-targeted true refinement
   null (mesh converged, V3); weld thinning the only directionally-consistent shape signal (sub-noise);
   splits a basis mirage. The per-node mode-shape wall (Cards A/D, bake-off) stands under the strongest
   remodeling attack mounted so far.
6. **Vault (Test04/+XY, graded once after SHA freeze):** every model scores 0.44–0.50 there vs 0.20–0.24 on
   dev — a uniform drive-location effect, not a candidate win; ranking preserved nothing actionable.
7. **Deliverable unchanged:** the inherited FEM + statFEM-style honest bands (netcg thread) remains the twin.
   Next dollar: >200 Hz plate/drumhead + multi-reference test data, not further remodeling.
