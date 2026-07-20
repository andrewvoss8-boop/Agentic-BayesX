# correlation_contribution.md — Can an autonomous agent contribute to FEM correlation by remodeling from data?

Card D headline deliverable. Runner: Claude Code (agent). Human: Andrew Voss. Advisor objective (Ilias
Bilionis): evaluate StatFEM, identify gaps, suggest improvements. **Every number here traces to
`out/region_diagnosis.json`, `out/before_after.json`, `out/edits/*/result.json`, `out/dish_refined/`, or the
figure `figures/fig_before_after.png`. Read nothing here as stronger than those files.**

> Plain-language note: **MAC** ("modal assurance criterion") = squared cosine between a model mode shape and a
> measured mode shape, in [0,1]; 1 = identical shape. **|df%|** = mean absolute natural-frequency error between
> paired model/measured modes. "Correlated update" = a change to the FEM intended to improve test–analysis
> correlation (classic finite-element model updating).

---

## 1. The question and the honest one-line answer
**Question:** can an agent improve ShockSat FEM correlation by *re-meshing/remodeling where the data says the
model is wrong* — at the 8 hard channels (impact face, bulkheads, bolted joint, strut, dish) that miss the
predictive band on per-sensor amplitude?

**Answer (scoped honestly — corrected 2026-06-19 after Andrew pushed): the COARSE 9-group stiffness-multiplier
update cannot cleanly improve the hard-region correlation (it is Pareto-optimal); but this does NOT mean "no
model change can help." Richer model-form changes are an OPEN, untested lever — and our own prior result (Card A
D22) shows enriching the shape representation DOES help.**
- **What is rigorously established:** scanning the FULL 9-parameter stiffness space (θ∈[0.6,1.4]⁹, 6000 samples,
  reduced 74-DOF model, re-pairing-robust TRACKED metric — `code/joint_frontier.py`,
  `figures/fig_joint_frontier.png`), **0 of 6000** points improve hard-region MAC without a frequency penalty;
  the Pareto frontier passes through the nominal point. So the as-received FEM is Pareto-optimal *within the
  9-group stiffness-multiplier family*, and the shape-vs-frequency trade is real there (not a 1-D-slice or
  greedy-pairing artifact). Earlier "e07 +0.010" was greedy-pairing churn; this supersedes it.
- **What is NOT established (do not over-claim):** that no MODEL-FORM change can help. The 9 group multipliers can
  only uniformly rescale existing substructures' moduli — they CANNOT change the LOCAL interface kinematics that
  set a local mode shape. That is a PARAMETERIZATION limit, not a fundamental one. Untested levers (legitimate,
  the model form is ours to change): (i) a richer LOCAL parameterization (split bulkhead/joint regions into their
  own parameters; per-element thickness/offset; a discrete weld/joint compliance with its own DOFs) that EXPANDS
  the achievable shape family; (ii) added local DOFs/connectivity; (iii) a non-proportional damping model
  (confounded at single impact, never cleanly tested).
- **Prior POSITIVE evidence a richer model helps:** Card A **D22** — inferring the mode-shape FIELD directly
  (Beck mode-matching-free) SHARPENED the held-out amplitude ~19% (interval 671→545, calibrated). So enriching
  the shape representation beyond the FEM's family demonstrably improves held-out-sensor prediction.
- **NOTE on metric:** the frontier uses a deterministic MAC/frequency PROXY, not the L5 Bayesian held-out-QOI
  that actually matters. The decisive Bayesian test = a richer local parameterization (or shape-field
  enrichment) run through L5 / a shape-augmented likelihood, scored on held-out QOI at the hard accels.
The agent autonomously (a) ruled out the two tempting levers (finer mesh; missing/wrong topology) with evidence,
(b) localized the stiffness lever, (c) ran a campaign of correlated updates, all re-solved and re-correlated.
The honest headline (corrected 2026-06-19 after Andrew pushed on an over-strict "clean-win" bar):
- **Mode-shape correlation at the hard regions is PARTLY improvable — but the aggregate MAC gain is muddied by
  mode re-pairing (honesty correction 2026-06-19).** Softening the over-stiff top-box (e07) or joints (e02)
  produces GENUINE local shape gains on some modes (e.g. test mode 8 MAC 0.70→0.94, same pair) — physically
  sensible (FEMs over-stiffen bolted/welded interfaces). BUT a per-mode audit shows the *aggregate* "global MAC
  0.631→0.641" is largely **greedy-MAC RE-PAIRING churn**: softening shifts frequencies → ~half the modes
  re-pair → apparent matched-MAC rises without genuine shape improvement, while the same shift worsens |df%|. So
  the global +0.010 is within re-pairing noise; there are genuine local gains AND genuine local losses
  (test 5/7 MAC drop). A CLEAN professional improvement requires (i) a LOCAL interface parameter (not a coarse
  9-group multiplier, which conflates stiffness LEVEL and DISTRIBUTION) and (ii) a re-pairing-robust metric
  (fixed MAC / cross-orthogonality pairing). NOT YET DONE → do not claim a clean aggregate improvement.
- **The cost is a genuine Pareto trade, not a failure:** hard-region SHAPE wants *softer* interfaces, global
  FREQUENCY wants *stiffer* — same parameters, opposite directions. So "improve correlation" requires an
  engineering-judgment operating-point choice (shape-priority → e07/e02; frequency-priority → calibrated θ).
  Choosing that point IS the professional deliverable; the agent maps the frontier and recommends the knee (e07).
- **What is NOT cleanly fixable at single impact:** the per-channel FRF peak *amplitude* (the original
  predictive-band misses) is `participation ÷ damping`, which one drive point cannot separate (confound) →
  needs multi-reference / roving-hammer data. Re-meshing finer and topology are independently ruled out (mesh
  converged; topology complete).

## 2. What the agent could diagnose (read-only, evidence-backed)
| claim | evidence | file |
|---|---|---|
| FEM is already **mesh-converged** | uniform 0.25-in mesh; 37–135 elements per plate-bending wavelength at 260 Hz; matches NASA modes <1% | decisions_log D3 |
| **Topology is complete** | bulkheads modeled at Z=12.4/18.4/30.4; bolted joint = CBUSH PID 801; struts present; bulkheads node-merged (welded = correct) | D5, region_diagnosis §3 |
| **Joints already finite & non-identifiable** | PBUSH 801–807 anisotropic, NASA-correlated; Card A found `joints` group non-identifiable; θ-scaling didn't fix amplitude | D1, region_diagnosis §3 |
| modes driven by **box stiffness, not joints** | strain energy: bottom_box 46.8% + top_box 34.9%; joints 3.1%; accel mounts 1e-4% | D6 |
| global shapes **decent**, error is per-sensor amplitude | global matched MAC 0.631; clean low modes 0.88–0.97 | region_diagnosis §0 |

The agent also self-corrected the card's premise where the data contradicted it: the "dish" is the **thick
Top Circular Plate** (t=0.777 in), already finely meshed — not an under-resolved flexible dish; and **ch92
(strut) is not in the checker's consistently-fail-7** (7/8 confirmed), so it is labeled a suspected region.

## 3. What edits it made and why (the campaign)
Baseline reproduces the inherited FEM to **3.6e-10** (eigenfreq, meets the validation-study bar). Each edit =
one targeted, traceable change → full re-assemble of the affected per-PID stiffness block → eigensolve (80
modes) → re-correlate to the 33-mode `.ash` survey. Baseline: global MAC 0.631, |df%| 6.07%, region MACs
source_face 0.466 / box_column 0.659 / strut 0.457.

| edit | what & why | Δ global MAC | Δ\|df%\| | Δ box_column MAC | Δ source_face MAC |
|---|---|---|---|---|---|
| e01 calibrated θ | apply the modal-twin NUTS posterior (the data-driven update) | −0.019 | **−0.32** | +0.004 | +0.068 |
| e02 joints ×0.5 | soften all bolted/contact joints | −0.004 | +0.62 | **+0.118** | **+0.110** |
| e03 joints ×2 | stiffen all joints | −0.019 | +0.42 | +0.013 | −0.006 |
| e04 bottom_box ×0.9 | soften the SE-dominant box | −0.030 | **−0.48** | +0.029 | +0.056 |
| e05 bottom_box ×1.1 | stiffen it | +0.000 | +0.92 | +0.089 | +0.023 |
| e06 top_box ×1.1 | stiffen | −0.006 | +0.32 | +0.013 | +0.111 |
| **e07 top_box ×0.9** | **soften the 2nd SE-dominant box** | **+0.010** | +0.93 | **+0.092** | +0.067 |
| e08 bolted joint 801 ×0.3 | soften ch52 bolted joint | −0.022 | +0.76 | +0.084 | +0.056 |
| e09 strut 807 ×0.3 | soften ch92 strut base | +0.001 | +0.005 | −0.004 | +0.000 |
| e10 contact 902 ×20 | add ch92 plate-contact stiffness | −0.004 | −0.01 | +0.020 | +0.087 |
| (mesh) dish 2× refine | true local refinement (4056→16224 quads, +74592 DOF) | **+0.0016** | — | — | — |

(Full table incl. strut deltas: `out/before_after.json`; figure: `figures/fig_before_after.png`.)

## 4. The measured before/after result — a shape-vs-frequency tradeoff
**Clearest single view: [`figures/fig_tradeoff.png`](figures/fig_tradeoff.png)** — one dot per edit, x = frequency
improvement, y = hard-region (box_column) shape gain, color = global-shape change (blue better / red worse). The
"win" corner (shape *and* frequency better) is reached only by **red** points (global shape worse) → no edit
wins on all three. (`fig_before_after.png` is the per-metric audit view.)

- **No edit improves a hard-region metric without degrading global MAC or frequency: 0 of 10**
  (`before_after.json` n_improved=0). Every edit that improves hard-region mode-**shape** correlation (softening
  joints/boxes: e02, e07, e08, e05, e06) **detunes the frequencies** (Δ|df%| +0.3 to +0.9%); every edit that
  improves **frequency** (e01 calibrated θ, e04) does **not** improve — and usually slightly worsens — global
  shape MAC. Softer structure fits the local interface *shapes* better but pushes the *frequencies* away.
- **Closest to a win:** e07 (top_box ×0.9) raised global MAC (+0.010) **and** all three region MACs (box +0.092,
  source_face +0.067, strut +0.041) — but cost +0.93% in frequency. Whether a ~1% frequency detune is worth the
  shape gain is an engineering/design-intent call (§6), not something the data decides cleanly.
- **The strut/contact joints (e09, e10) have ~no leverage** (Δ everything ≈ 0), matching their tiny strain
  energy — re-tuning them cannot move the correlation.
- **True mesh refinement does essentially nothing:** the dish 2× refinement changed global matched MAC by
  +0.0016. 36 of 38 modes are unchanged to <0.1% (median Δf 0.006%); the only genuine dish-related shift is
  −2.4% on a 10%-dish-participation mode (an apparent +17% partner is a degenerate-cluster mode-swap artifact at
  124.5–125.2 Hz, 1% dish participation — **not** a real refinement effect, reported so it is not mistaken for
  one). This **confirms the mesh is converged** — refining cannot improve correlation.

**Interpretation.** The as-received NASA-correlated FEM sits near a **Pareto-optimal compromise** between mode
shape and frequency. This sharpens Card A's "joints non-identifiable" finding: the joint/box stiffness *does*
have leverage over the hard-region shape, but in a direction that trades against frequency — which is *why* the
data cannot pin a clean optimum. The residual per-sensor amplitude error at the 8 channels is therefore **not a
stiffness/mesh/topology defect** the agent can remodel away; it is the interface **damping** + near-drive
**near-field** response + **frequency-misalignment near sharp resonances** that Card A localized — none of which
a real-eigenvalue/MAC correlated update can fix.

## 5. Where human FEM judgment was still required
- **Accepting a tradeoff.** Deciding whether e07's +0.93% frequency detune is an acceptable price for better
  shape correlation is a design-intent judgment (what the model will be *used* for). The agent surfaces the
  frontier; it should not unilaterally pick a point on it.
- **Physical plausibility of edits.** The agent flagged that softening the welded bulkhead-to-wall connection
  would be unphysical (welded construction), and that the joints are already NASA-correlated — a human/agent
  with structural judgment must keep "improves a metric" from overriding "is physically real."
- **Premise correction.** The card assumed a coarse mesh / under-resolved dish; the agent had to recognize from
  the data that this premise did not hold and redirect — a judgment a naive "just refine it" loop would miss.
- **Replacement decision.** Whether any remodeled FEM should *replace* the inherited one is explicitly **out of
  the agent's authority** (surfaced to the human; not self-applied).

## 6. Residual risk and honest limits
- **Metric thinness.** Region-restricted MAC uses only 1–3 measured DOFs per region (the `.ash` survey measures
  few axes there), and greedy best-MAC re-pairing adds jitter; small region-MAC deltas (≲0.02) are within noise.
  The robust signals are the larger box_column/source_face improvements (~0.09–0.12) and the *direction* of the
  tradeoff, not any single decimal.
- **Amplitude leg.** The Card D correlation metric here is eigen-MAC + frequency (what the agent's pipeline
  computes natively). The per-sensor **FRF amplitude** failure itself is the validation study's domain; its
  conclusion (amplitude ceiling not fixable by stiffness/damping; needs finer model + better data) stands and is
  consistent with this negative.
- **What would actually resolve the residual** (the pre-test/design lever, not a remesh): a **multi-reference /
  roving modal test** to identify per-region mode shapes and per-joint **damping** directly — i.e., spend the
  next dollar on data, not on re-meshing an already-converged, already-topologically-complete model.

## 7. Bottom line for the advisor objective
A credible **gap + improvement-boundary** result: an autonomous agent *can* meaningfully contribute to FEM
correlation by remodeling-from-data — here it delivered an auditable diagnosis that **re-meshing and stiffness
re-tuning are not the lever** for ShockSat's hard-region amplitude error (with a quantified shape-vs-frequency
tradeoff and a converged-mesh proof), and redirected effort to damping + test data. The contribution is the
**honest, evidence-backed boundary of what remodeling can achieve**, which is exactly the "identify the gap"
deliverable — not a polished but unverifiable "improved" FEM.
