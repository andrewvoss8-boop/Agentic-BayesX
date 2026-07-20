# Decisions log — MPL twin iteration (master/orchestrator)

Append-only. Any human clarification or non-obvious decision that changes an action is recorded HERE before
continuing (not only in chat). Re-ground from this + notes/memory.md after any compaction.

## D0 — Launch & scope (2026-06-20)
- Andrew pasted the master prompt (`docs/lab/mpl_twin_iteration_master_prompt.md`); D-A..D-H are SETTLED (do not
  re-litigate). Full autonomy (D-D): run the program; surface ONLY durable-rule / checker-expectation /
  sampler-standard changes and any "replace the inherited FEM" claim.
- No separate subagent-spawn tool is available in this environment → the MASTER (this lead session) builds and
  scores each candidate model class SEQUENTIALLY; each candidate = one `out/class_<id>.json` + one
  `model_registry.json` row + figures, exactly as the per-subagent contract specifies. This is a labeling/
  bookkeeping difference, not a method change; recorded for honesty.

## D1 — Frozen harness FIRST (Phase 0), check.py before anything scoreable
- Workspace `artifacts/reports/mpl_twin_iteration_20260620/`. check.py written FIRST, 3-tier, SHA self-lock +
  asserts `code/score.py` byte-identical to the L5 original; baseline RED until deliverables exist.
- score.py reused BYTE-IDENTICAL (SHA c62c564d024eb59cc48d6daeb70128b73b5bcb0e4e925f8d4234416baeb0934d) — proper
  scores are problem-agnostic.

## D2 — Observable = gain-free output/output transmissibility (D-B), forward derivation
- `|T_a(f)| = sqrt(PSD_a/PSD_ref)`, ref = shield. KEY: under a distributed acoustic load with separable
  spectrum (S_FF(ω)=g(ω) f fᵀ), the response auto-PSD = g(ω)|H(ω)|², so the transmissibility
  `|T_a|=|H_a|/|H_ref|` CANCELS the input spectrum g(ω). Only the load SPATIAL shape f enters (via modal
  participation γ_i=φ_iᵀf). Near resonance i, one mode dominates ⇒ |T_a|→|φ_{a,i}/φ_{ref,i}| (γ_i cancels);
  off-resonance the γ dependence is the model-form error absorbed by the log-frequency discrepancy GP. This is
  exactly the no-force substitute for ShockSat's force-keyed match. Default load shape f = uniform OOP pressure
  on shield exposed grids (assumption F-load, ANDREW-CONFIRM, sensitivity HIGH).

## D3 — Geometry / node map (defensible defaults under D-D)
- Shield is a planar y–z panel at x≈61.5 with normal +X (SVD on 121 shield grids) ⇒ sensor OOP axis = the
  X-translation DOF at each accel node. Confirmed against interface_points.json (mode-1 shield motion X-dominated).
- Node map (X-DOF): interface=g800071, shield-REF=g800016 (nearest shield grid to centroid), beam=g1510,
  avi box=electronics_box on shield → top-LEFT-foot=g800036 (y=−14.4), top-RIGHT-foot=g800034 (y=−4.8) by the
  "+X view ⇒ left=−y" convention (interface_points.json), valve=valve_panel node nearest the frame centroid.
  All flagged ANDREW-CONFIRM in the ledger; not blocking under autonomy.

## D4 — Splits = 5 leave-one-location-out (D-C)
- Hold out exactly ONE of {interface, beam, valve, avi-L, avi-R} per split; train on the rest; shield always the
  fixed reference (in training). A location's taps AND acoustic stay together (leakage control). Coupled-ruler =
  a 6th, separate robustness validation (D-E), NOT one of the 5 LOLO splits.

## D5 — Baseline + climatology = the immutable numbers to beat
- Score the as-received fable rev-3 twin (nominal θ=1 deterministic AND NUTS-calibrated) on all 5 splits.
  Climatology = predict the held-out |T| (and GRMS) from the population of observed-location |T| curves
  (no location-specific info). Recorded before any model-class search round.

## D6 — KEY FINDING (2026-06-20): as-received FEM transmissibility forward is UNCORRELATED with measured |T|
- Phase-0 harness BUILT + VALIDATED: check.py (locked, baseline RED), score.py byte-identical (SHA c62c564…),
  mpl_fem.py (forward reproduces fable nominal f1..f8 to 4e-4 Hz; ref/ref |T|≡1; load-scale & input-spectrum
  invariance unit tests PASS), mpl_observe.py (gain-free |T| from acoustic CSVs, all 8 unit tests PASS),
  mpl_splits.py (5 LOLO). The end-to-end calibrate+score pipeline RUNS.
- DIAGNOSTIC (numeric, cheap): nominal-FEM-predicted |T_a(f)| vs measured |T_a(f)| over [20,260] Hz has
  log-correlation ≈ 0 at EVERY held-out location (interface +0.05, beam −0.02, valve −0.01, avi-L −0.16,
  avi-R −0.12). Predicted dominant peaks 34–68 Hz; measured dominant peaks 78–110 & 180–254 Hz. The measured
  peaks coincide with real modes (match the tap-spectra in features.json) AND the FEM HAS modes there (28 modes
  70–120 Hz, 49 modes 170–260 Hz) — so it is NOT a frequency problem.
- ROBUSTNESS: log-corr stays ≈0 across load shapes (uniform-shield, uniform-all) AND references (shield,
  interface) — |corr|≤0.35, mostly ~0. So it is NOT a tunable load/reference choice.
- MECHANISM: a DENSE modal forest + an UNKNOWN diffuse acoustic load + single axis + no force ⇒ the
  transmissibility SHAPE is dominated by (a) the unknown acoustic-load modal participation γ_i and (b) the
  reference point's own antiresonance pattern and fine mode-shape error — none of which stiffness calibration
  can fix. This is the SAME data ceiling the project documented for ShockSat (per-location single-impact
  amplitude near-irreducible for any global model), now confirmed on MPL with the transmissibility QOI.
- CONSEQUENCE: launching a multi-hour NUTS/TMCMC calibration of a forward that is uncorrelated with the data
  would be burning compute on a broken premise (and NUTS is multimodal here — θ→1.8, ζ→0.15, R̂ 23 — the
  documented whole-curve-magnitude multimodality). DECISION: STOP before that; build the diagnostic FIGURE +
  Stage-1 FREQUENCY evidence screen (the IDENTIFIABLE part the card wants), and SURFACE to Andrew with options:
  (a) run the model-class search anyway as a rigorous DEMONSTRATION of the ceiling + test whether any richer
  load/discrepancy/likelihood/shape-field form recovers skill (honest-negative expected, equally valid per card);
  (b) pivot the SCORED held-out QOI toward the identifiable per-location modal-FREQUENCY (+ damping where
  resolvable), with transmissibility shape reported as a diagnostic; (c) reconsider the observable (coherent
  averaging / sub-bands / infer the acoustic load as a latent field, IFT-style). SURFACED because it questions
  the central observable/forward premise (near-durable), not a routine within-run modeling choice.

## D7 — Andrew steer (2026-06-20): proceed (a)+(b) HYBRID
- Andrew: "a+b". → (b) PIVOT the HEADLINE scored held-out QOI to the IDENTIFIABLE part: per-location modal
  FREQUENCY content (which modes are alive at the held-out node + their values) + damping where resolvable, with
  the transmissibility SHAPE reported as a diagnostic (not the headline). (a) Run a BOUNDED model-class search of
  richer TRANSMISSIBILITY forms (infer acoustic-load participation as a latent; region/frequency-correlated
  discrepancy; near-resonance |φ_a/φ_ref| matching; shape-field) ONLY to document whether any recovers held-out
  transmissibility-shape skill — honest-negative expected and equally valid.
- Plan: (1) `mpl_freq.py` — measured peak freqs per location (from features.json tap spectra + acoustic) + FEM
  alive-mode gating (OOP amplitude at node) ; matched-eigenfrequency NUTS calibration (reuse the λ(θ)
  eigen-sensitivity forward — converges, per project Study K/L5) ; held-out per-peak frequency CRPS-skill vs
  climatology (climatology = predict held-out peaks from the pooled observed-location peaks) + interval/coverage.
  (2) carry-forward baseline = calibrated frequency twin. (3) bounded richer-transmissibility search (a). (4)
  registry + figures + packet. Node-map defaults (avi=electronics_box L=800036/R=800034, shield-mid=800016,
  valve=910008) stand pending confirmation (non-blocking).

## D8 — RESULT (2026-06-20): (a)+(b) run; OVERALL YELLOW honest negative (simplest-sufficient model wins)
- (b) FREQUENCY headline `freq_baseline.json` + `fig_freq_result.png`: matched-eigenfrequency NUTS calib (6
  K-groups) on training-location alive modes, held-out per-peak scoring, 5 LOLO splits. **ALL 5 CONVERGED**
  (R̂ 1.001–1.002, ESS ~3000, coverage 0.93). CRPS-skill vs pooled-ensemble climatology **+0.91** (the WEAK,
  wide bar). BUT calibrated twin median |Δf| **2.76%** ≈ nominal FEM **2.47%** ≈ nearest-pooled-peak fair clim
  **2.51%** → calibration adds NO held-out frequency value; dense modal forest (29–71 alive modes/node) makes
  frequency a weak discriminator.
- (a) richer-transmissibility decisive cheap RUN `near_resonance.json`: at resonance |T|→|φ_a/φ_ref| (load
  cancels); measured peak height vs FEM |φ_a/φ_ref| log-corr **+0.26** (n=21) → transmissibility-shape residual
  is LOAD-INDEPENDENT mode-shape error ⇒ inferring the acoustic load (the obvious richer-form lever) cannot
  recover held-out shape skill; a multi-hour latent-load NUTS arm is moot (residual is load-free) → not run.
- VERDICT (YELLOW, equally valid per card §6): as-received fable rev-3 FEM is a TRUSTWORTHY MPL FREQUENCY twin;
  neither stiffness calibration nor richer transmissibility/load/discrepancy forms improve held-out scores on
  this single-axis, no-force data — the ShockSat per-loc-amplitude DATA CEILING confirmed on MPL. Pre-test lever
  that WOULD resolve it: instrumented force (apparent mass) + multi-axis/multi-reference shapes.
- check.py OVERALL YELLOW 13G/2Y/0R exit0 (2Y = whole-curve transmissibility non-converged/uncorrelated [M0] +
  the honest program verdict). run_all.sh replays; runtime active ~905s. Figures tufte-linted + image-QA pass.
- SURFACE-only to Andrew (NOT self-applied): docs/report/project_log.md row; runs.md entry; any "replace
  inherited FEM" claim; node-map ANDREW-CONFIRM defaults. NO durable-rule/checker/sampler edits.

## D9 — Deck (2026-06-20, Andrew request "create a pptx with key findings and figures")
- Built `code/fig_story.py` (5 new story figures: geometry/sensor map, statFEM likelihood schematic, measured |T|,
  dense modal forest, strain-energy identifiability, near-resonance scatter) — tufte-linted + image-QA pass (9
  figures total). `code/make_deck.py` → `slides/mpl_twin_findings.pptx` (13 slides), numbers pulled from out/*.json
  (no hand-typed metrics). Story: setup→method→data→Finding-1(uncorrelated transmissibility)→why(dense forest)→
  frequency twin→load-free near-resonance→identifiability→registry→verdict(YELLOW)→scope/integrity. No renderer
  (libreoffice) to QA the pptx itself, but every embedded figure was visually + image-QA verified. check.py
  unaffected (still YELLOW 13G/2Y/0R exit0).

(rounds appended as they run)
