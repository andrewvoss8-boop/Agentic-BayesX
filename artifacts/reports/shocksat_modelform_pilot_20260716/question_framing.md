# question_framing — MODEL-FORM PILOT (Card C; pre-registered BEFORE any science, 2026-07-16)

## 1. The engineering decision being supported
Whether the lab should keep investing in agentic REMODELING (model-form search: geometry, element
formulation, connectivity, mesh) of the inherited ShockSat FEM to improve held-out FRF prediction — or
close the remodeling arc with the strongest negative yet and move the next dollar elsewhere (sensors,
>500 Hz basis, MPL stand). Prior loops never gave the agent genuine model-form freedom (study D16:
agent proposed 0 refine/rbe2 edits; review C7: NEITHER track ever tested geometry or element
formulation). This pilot closes that gap.

## 2. The two hypotheses (verbatim from the card; each falsifiable)
- **HQ1:** at equal budget and with STRATIFIED proposals across edit classes, an amplitude-compass
  agent beats seeded random on held-out sub-200 P1′, evaluated on EXACT bases (≥1×paired-fold-SE).
- **HQ2:** at least one GENUINE model-form edit class (connectivity/mesh/element/geometry — NOT
  property scaling) produces an exact-basis held-out improvement over the A1 baseline ≥1×paired-fold-SE.

Falsification of both = "model-form freedom does not move held-out FRF here" — the strongest version
yet of the standing negative, and a publishable close-out of the remodeling arc.

## 3. Success metric + what the search may choose + what stays human
- **Metric:** held-out sub-200 Hz P1′ (per-channel Pearson correlation of log10|H| after train-side
  FDAC warp + one global gain per fold; quantity_contracts Q1), 4-drive LODO mean; paired-fold SE for
  all comparisons. 200–500 Hz band reported alongside (secondary, no HQ rule attached).
- **The search chooses:** which candidates to propose within the fixed 5-class grammar and quotas
  (agent: diagnosis-driven; random: seeded uniform draws from the same menus).
- **Human judgment retained:** whether to act on the verdicts (invest/close), whether to re-open the
  vault, any durable-rule changes, and whether a winning candidate warrants a TMCMC posterior card.
- **What would make this the wrong question:** if the sub-200 error is dominated by unmodeled physics
  no mesh/geometry/formulation edit can express (e.g. amplitude-dependent joint damping) or by data
  limits (1 Z sensor, archive-only), then class-level nulls here mean "not reachable by THIS freedom,"
  not "the model is correct." The stop condition from the review spec applies: if rankings are unstable
  across drive folds or model-form effects sit below the discrepancy floor, report data/BC limitation
  rather than escalating search.

## 4. Pre-registered decision rules (locked; the checker verifies verdict-consistency, not outcomes)
- **Scoring rule (all-exact; the D22/D15 lesson):** every SCORED number is EXACT-basis. Per candidate:
  own-space sparse eigensolve k=200 at θ=1 → multi-start θ_MAP (≥5 deterministic starts, survey-.ash
  S0-form objective, femlib.Package.theta_map — no drive data, hence fold-independent) → SECOND
  own-space solve at θ_MAP with θ folded in (enrich; exact-by-construction, self-consistency ≤0.01%) →
  score at θ=ones on the 4 LODO folds. NO θ=1-basis number is ever reported as a score; triage of ideas
  (if >10/round) is on diagnosis only. Query-log records carry `basis:"exact_at_thetaMAP"`; any
  screening-score key is checker-RED.
- **HQ1 PRIMARY:** Δ = (best-exact agent candidate) − (best-exact random candidate), paired per fold
  (4 sub-200 fold deltas); met iff mean(Δ) ≥ 1 × SE(Δ), SE = std(deltas, ddof=1)/√4. Caveat
  pre-registered: both sides are maxima over 30 noisy candidates; a sub-SE gap is a win for neither.
  **HQ1 SECONDARY (reported, not decisive):** per-track mean over all 30 candidates, paired per fold.
- **HQ2:** per class c ∈ {connectivity, mesh_density, element_formulation, geometry}: Δ_c = (best exact
  candidate in c, POOLED tracks, n=12) − A1 exact, paired per fold; HQ2 met iff any Δ_c has mean ≥
  1 × SE. Class MEAN − A1 reported alongside (selection-noise control). property_control is reported in
  the same table but CANNOT satisfy HQ2 (control class).
- **Complexity/runtime penalty:** every candidate reports ΔDOF (%), Δn_params (θ blocks added), and
  solve-time ratio vs the A1-basis solve; ties (within 1×SE) go to the simpler model; a candidate with
  exact gain vs A1 < 1×SE AND ΔDOF > +10% is labeled **not-worth-it regardless of sign**.
- **Stratification (the review's key fix):** each round, EACH track scores exactly 2 candidates per
  class × 5 classes (10/round/track; 3 rounds; 30/track; 60 total). The agent may NOT substitute
  property edits into model-form slots. Budget ≤80 scored queries per track (hard).
- **Finalists (reinforcement, not the HQ verdict):** top-2 per track by exact sub-200 get per-fold
  amplitude-trained θ_MAP refits (train drives only; deterministic multi-start; NO cross-fold reuse of
  any fitted object) + per-fold enrichment at that fold's θ_MAP + paired-fold S-tests vs A1 and vs the
  other track. Divergence between the main table and the finalist refits is reported as-is.
- **Vault:** NOT read (no 4th +XY read without Andrew's explicit pre-registration).

## 5. Sampler declaration (AGENTS Sampler Decision)
NO SAMPLER: the loop scoring is deterministic (multi-start MAPs + exact eigensolves). Reason: the study
established the amplitude posterior here is multimodal with unresolved global identification; per-
candidate non-converged posteriors add nothing to model ranking. NUTS/HMC remains the project default
for Bayesian updating; no posterior/uncertainty claim is made anywhere in this card. Posterior bands on
a winner, if wanted, are a follow-up TMCMC card per the compute protocol.

## 6. Honest failure modes (expected; report, don't panic — card §7)
New operators may fail V-gates (drop with documentation; 4-class pilot still valid). Geometry edits may
be numerically fragile (Jacobian/quality checks; duds recorded with reasons). All model-form classes may
lose to property control (HQ2 falsified = the headline). The agent may tie random even stratified (HQ1
falsified → the impotence result finally covers genuine model-form freedom, closing D16's gap).
