# decisions_log.md — Card D: data-driven FEM remodeling of high-error ShockSat regions

Runner: Claude Code (runner agent, Card D). Human: Andrew Voss. Advisor objective: Ilias Bilionis
("evaluate StatFEM, identify gaps, suggest improvements"). Sharper question this card poses:
**can an autonomous agent contribute to FEM correlation by re-meshing/remodeling where the data says
the model is wrong?**

Workspace: `artifacts/reports/shocksat_fem_remesh_20260618/`.

## ONE-LINE STATE (compaction-safe; update before risky steps)
- **goal:** COPY the plain 9-group ShockSat FEM, remodel ONLY the 8 data-flagged high-error regions, and prove
  before/after improvement in per-mode MAC + frequency + FRF/peak at the 8 hard channels WITHOUT degrading global
  correlation; deliver the honest `correlation_contribution.md` verdict.
- **last decision:** D1 DONE — region diagnosis (read-only) written (`region_diagnosis.md`,
  `out/region_diagnosis.json`). PIVOTAL FINDING: the joints at the hard channels are ALREADY finite anisotropic
  CBUSH (PBUSH 801-807, NASA-correlated) and the validation study already found the `joints` group
  NON-identifiable + θ-scaling didn't fix amplitude → "soften the joints" is NOT a fresh lever. The genuine
  re-mesh lever = LOCAL MESH REFINEMENT at under-resolved local-mode regions (dish ch98, impact face ch4/27/38,
  strut base ch92). Also: only 7 of the card's 8 channels are checker-confirmed fails (ch92 strut NOT in
  fail-7 → labeled suspected). Global matched MAC BEFORE = 0.633 (26 modes).
- **STATUS: STUDY COMPLETE (checker GREEN 14/0/0).** Campaign of 10 correlated updates + dish 2× mesh
  refinement done; before/after table + figure + correlation_contribution.md verdict written. HEADLINE: 0/10
  edits cleanly improve (shape-vs-frequency Pareto tradeoff); mesh confirmed converged (+0.0016); re-mesh/
  stiffness NOT the lever — residual = damping + near-field + freq-alignment; real fix = test data. Agent
  contribution = the auditable boundary of remodeling-from-data. SURFACE-only (await Andrew): project_log row;
  replace-FEM claim; durable-rule/checker. NEXT (if Andrew wants more): proceed to remaining hard regions per
  D2 order (already covered strut807/contact902/box-column via campaign), or a damping-retune FRF leg.

## D17 — Andrew (2026-06-19): review statFEM §4.1.5 + Kiran §5; develop a model-class-SELECTION experimental prompt
- Andrew handed the full Girolami statFEM paper + Kiran 2025 review and asked: review statFEM **§4.1.5 (model/mesh
  selection by marginal likelihood + Bayes factor)** and Kiran **§5 (Bayesian model class selection)**; develop an
  experimental prompt to apply these to modeling around the hard-to-correlate measurements — *first fix the other
  parameters at MAP, eventually allow them flexible; different damping forms / local parameterizations are
  competing model classes.* TEXT-ONLY review delivered in chat.
- KEY: this gives the **principled decider** the Card D/E thread kept circling — instead of me declaring whether a
  richer model form helps, the **Bayesian EVIDENCE (marginal likelihood) decides, with Ockham's-razor penalty**.
  statFEM Eq 38 (analytic Gaussian evidence), Eq 52–53 (model posterior + Bayes factor), §4.1.5 result = evidence
  prefers the simplest SUFFICIENT model. Kiran Eq 44 = log-evidence = goodness-of-fit − KL (auto-Ockham); warnings:
  prior-sensitivity, use modal-feature statistics (not raw FRF) as data, TMCMC/nested/BUS-SuS for evidence.
- DELIVERED: `HANDOFF_modelclass_selection.md` (**Card F**) — competing model classes M0 baseline / M1 local
  stiffness split / M2 Rayleigh / M3 non-prop localized viscous (Das-Debnath) / M4 Schneider correlated
  discrepancy / M5 combos; Stage 1 = analytic statFEM evidence at fixed-MAP θ; Stage 2 = TMCMC evidence with θ
  flexible; cross-checked by L5 held-out QOI at the 8 hard accels; identifiability + evidence-sensitivity gates;
  carries the participation÷damping confound, re-pairing-robust metric, evidence≠held-out, and scope-claims
  lessons. **Card F SUBSUMES Card E** (Card E's "does a richer model form sharpen L5?" becomes the candidate
  classes here, with evidence as the Occam-penalized decider). SURFACE-only items unchanged.

## D16 — Andrew (2026-06-19): "write a new prompt to handoff to a new runner agent."
- Wrote `HANDOFF_richmodel_L5.md` (Card E): does a RICHER MODEL FORM (richer LOCAL stiffness parameterization
  and/or non-proportional damping) run through L5 (the converged Bayesian modal-feature method) SHARPEN the
  held-out-sensor QOI (×2.7 band) at the 8 hard accels without degrading global? Self-contained re-grounding
  (AGENTS + Card D D0-D15 + Card A L5/D11/D12/D22 + source data), carries: what's ruled out (mesh/topology/coarse-
  9θ Pareto-optimal) vs the OPEN lever (richer local params expand the shape family; D22 shape-field already
  sharpened ~19%), the participation÷damping single-impact CONFOUND, the identifiability gate, the ζ-units flag,
  and the LESSONS (scope claims to exactly what's tested; re-pairing-robust metrics; lead with held-out QOI not
  MAC). New workspace shocksat_richmodel_L5_YYYYMMDD; COPY-reuse Card A L5 machinery. Honest-negative also a win.

## D15 — Andrew (2026-06-19): "are we running L5? you say model-form error but we're free to change model forms; no model/damping change can improve the Bayesian updating at these accels?"
- THREE valid challenges; I OVER-CLAIMED again. Corrections:
  1. The joint-frontier/MAC work is DETERMINISTIC eigen-correlation (proxy), NOT L5. L5 = converged Bayesian
     modal-peak-FREQ likelihood (Card A) giving the calibrated-but-wide held-out QOI. The frontier metric (MAC)
     is not the L5 held-out-QOI that actually matters.
  2. "Model-form limit / no change can improve it" = OVER-CLAIM. What's proven is narrower: the COARSE 9-group
     stiffness-MULTIPLIER family is Pareto-optimal. Those knobs only uniformly rescale substructure moduli — they
     CANNOT change LOCAL interface kinematics (what moves a local shape) = a PARAMETERIZATION limit, not
     fundamental. Model form is OURS to change. Untested legit levers: richer LOCAL parameterization (split
     bulkhead/joint regions; per-element t/offset; discrete weld/joint compliance w/ own DOFs); added local
     DOFs/connectivity; non-proportional damping (single-impact confound, never cleanly tested).
  3. POSITIVE prior evidence a richer model helps: Card A D22 (Beck mode-matching-free, infer the shape FIELD)
     SHARPENED held-out amplitude ~19% (671→545, calibrated). So "no change helps" is contradicted by our own result.
- Corrected correlation_contribution.md §1 to the scoped claim. DECISIVE next test (offered): richer LOCAL
  parameterization (or shape-field enrichment) run through L5 / shape-augmented likelihood, scored on held-out
  QOI at the 8 hard accels — does it sharpen the ×2.7 band? Pattern noted: I keep over-claiming negatives;
  must scope to exactly what was tested.

## D14 — Andrew (2026-06-19): "are we assuming the other global parameters are fixed?" → YES (1-D slices); built the JOINT-space answer
- Correct: the group campaign AND local-interface sweep are 1-D slices (vary one param, freeze rest at nominal
  θ=1). So the shape-vs-frequency "tradeoff" + the "frequency cost" are measured in a slice around the
  uncalibrated point — in a JOINT update the other params can COMPENSATE → a both-improve point a 1-D sweep
  can't find. BUILT `code/joint_frontier.py`: scans the FULL 9-θ space in the fast 74×74 reduced model (eigh
  24ms) with the re-pairing-robust TRACKED metric → Pareto frontier (mean|df%| vs hard-region MAC) + any point
  with |df%|≤nominal AND hard MAC>nominal AND global≥nominal. Nominal ref: |df%| 6.07, global MAC 0.726,
  hard-region MAC 0.712 (21 calib modes). Smoke (60 samples) = 0 both-improve; full 6000-sample run launched
  detached (pid 83512).
- **JOINT FRONTIER RESULT (DECISIVE, `out/joint_frontier.json`, `figures/fig_joint_frontier.png`): 0 of 6000
  full-space samples improve hard-region shape without a frequency penalty.** Pareto frontier of hard-region MAC
  vs |df%| passes THROUGH the nominal point (6.07%, 0.712) → as-received FEM is already Pareto-optimal in the
  full 9-θ stiffness space; WIN quadrant EMPTY. So the shape-vs-frequency tradeoff is REAL (not a 1-D-slice
  artifact, not greedy-pairing artifact) = a MODEL-FORM limit (FEM mode-shape family can't match test hard-region
  shapes AND frequencies together); NO stiffness update (local/global/joint) cleanly improves hard-region
  correlation. Updated correlation_contribution.md §1 to this definitive NO (supersedes "partially improvable").
  Local single-bush sweep silently produced no output (launch issue) but is SUBSUMED (joints group free in scan).

## D13 — Andrew (2026-06-19): "yes" → do it properly: LOCAL interface parameter + re-pairing-robust (tracked) metric
- BUILT `code/local_interface.py`: (1) LOCAL param = scale a single discrete joint CBUSH (801 bolted joint/ch52,
  807 strut/ch92, 902 contact) → changes interface FLEXIBILITY w/o whole-panel modulus; joints ~3% SE so freq
  should barely move → if SHAPE moves, the lever is DECOUPLED. (2) TRACKED pairing = MAC-track each baseline FEM
  mode to its shape-CONTINUATION in the edited model → each test mode keeps the SAME PHYSICAL FEM partner →
  genuine dMAC w/o greedy re-pairing churn. Metric: genuine dMAC (tracked) + region dMAC (hard channels) +
  |dfreq| of the tracked modes. CLEAN test: shape↑ with freq≈flat = decoupled YES; both≈0 = joints not the shape
  lever; shape↓ = no.
- HONEST SCOPE: local-bush lever exists only for bolted joint (801,ch52) + strut (807/902,ch92); bulkheads
  (ch40/69) are welded/merged (no discrete bush) + source face (ch4/27/38) = shells → would need an inserted
  interface (bigger edit) for a local param. Testing 801×{0.3,2.0} + 807×0.3 (launched detached pid 64843, after
  combos). Report clean yes/no when it lands.

## D12 — Andrew (2026-06-19): "how does it happen that shapes want softer but frequencies want stiffer?" → REAL physics + bigger METRIC ARTIFACT
- Per-mode audit (baseline vs e07, `out/edits/*/result.json` pairs): softening top_box gives GENUINE local shape
  gains on some modes (test 8 MAC 0.70→0.94, same pair) but genuine LOSSES on others (test 5 0.98→0.89, test 7
  0.96→0.85), and **~14 of 29 modes RE-PAIRED** (frequency shift re-assigns greedy best-MAC partners).
- TWO mechanisms: (1) REAL physics — shape = stiffness DISTRIBUTION/relative-interface-stiffness + BC; frequency
  = absolute LEVEL; an over-stiff joint distorts local shape, softening fixes distribution but lowers freq;
  coarse 1-scalar-per-group knobs can't separate level from distribution (a LOCAL interface param could); + dense-
  mode VEERING. (2) METRIC ARTIFACT (larger) — softening shifts freqs → greedy MAC re-pairing raises apparent
  matched-MAC w/o genuine shape gain, while the SAME shift worsens |df%| = two faces of one freq shift through
  two metrics, NOT independent opposition.
- **HONESTY CORRECTION:** my D11 "e07 improves correlation (global MAC 0.631→0.641)" was OVER-STATED — the net
  +0.010 is largely re-pairing churn. Corrected correlation_contribution.md §1 + §4: genuine LOCAL gains exist,
  but a CLEAN aggregate improvement needs (i) a LOCAL interface parameter (not coarse group multiplier) + (ii) a
  re-pairing-robust metric (fixed-MAC/cross-orthogonality pairing) — NOT YET DONE.
- Combos (e11 cal-θ+topbox0.92: global 0.6375/|df%|6.62/box0.738; e12 cal-θ+joints0.7: global 0.602/|df%|5.59/
  box0.695) inherit the same re-pairing caveat. NEXT (offered): do it properly — local interface param + fixed
  pairing — the only way to honestly separate genuine shape improvement from pairing noise.

## D11 — Andrew (2026-06-19): "between damping and remeshing/remodeling can you NOT improve correlation at the hard locations professionally?"
- HONEST REFRAME (I had under-sold it with an over-strict "0/10 clean wins" bar): YES, remodeling DOES improve
  hard-region mode-shape correlation, defensibly. **e07 (soften top_box ~10%): global matched MAC 0.631→0.641
  AND box_column 0.659→0.751 (+0.092), source_face 0.466→0.533 (+0.067), strut 0.457→0.498 (+0.041)** for a
  ~0.9% frequency cost. e02 (soften joints ×0.5): box_column →0.78 (+0.12). Physically defensible (FEMs
  over-stiffen bolted/welded interfaces). Region-MAC thin-DOF caveat noted but global MAC corroborates direction.
- The cost is a genuine PARETO trade (shape wants softer interfaces, frequency wants stiffer — same params,
  opposite directions) → the professional deliverable = map the frontier + recommend the knee, not a "clean win."
  Per-channel FRF AMPLITUDE stays the participation÷damping confound (single-impact) → multi-ref data.
- ACTION: launched 3 COMBINATION solves (pid 51065, run_combos.sh): calibrated-θ (freq-optimal) base + softened
  interface (top_box 0.92 / joints 0.7 / both) to get the shape gain while LIMITING the frequency cost — the
  balanced update a correlation engineer would deliver. Corrected correlation_contribution.md §1 to lead with the
  e07 improvement (was buried as "closest to a win"). Aggregate + recommend operating point when combos land.

## D10 — Andrew (2026-06-19): "start with (a) [damping identifiability gate] then move to (b) [build L-damp]"
- KEY simplification: for stiffness-proportional localized dampers C_g=β_g K_g, modal damping
  ζ_{m,g}=(β_g ω_m/2)·f_{m,g} where f_{m,g}=φᵀK_gφ/λ = the strain-energy fraction ALREADY computed. So the
  measured per-mode ζ̂_m fit is LINEAR in (α0,α1,{β_g}): ζ_m = α0/(2ω_m)+α1 ω_m/2+Σ_g (β_g ω_m/2) f_{m,g}.
  Identifiability = conditioning/SVD of that design matrix; "does localized damping explain the 0.12-1.76%
  spread" = the NNLS fit residual. Reuses V_keep + per-PID K blocks (NO eigensolve; fast/foreground).
- GATE (a) = `code/damping_gate.py` → which β_g identifiable from 33 modes; does interface-localized damping
  reproduce the non-proportional ζ pattern; which groups carry the damping. THEN (b) build L-damp prototype.
- **GATE (a) RESULT (`out/damping_gate.json`):** (1) cond 6.2e6; 10/11 combos clear; the 1 exact degeneracy =
  α1 ≡ Σβ_g (since Σ_g f_{m,g}=1) → DROP α1 (redundant w/ localized dampers). (2) Damping lands on the HIGH-SE
  shell groups: top_box 32% / plates 25% / cross 16% / al_welds 13% / angle_brackets 14%; **β_joints=β_contact=
  β_bottom_box=0** — stiffness-proportional damping ties dissipation to strain energy, modes store ~none in the
  joint CBUSH (3.1% SE) → joints NOT modal-identifiable as damping sources (the most-damped 107-122 Hz bulkhead+
  cross DRUM modes strain top_box/plates/cross, so damping correctly lands there). (3) Localized stiffness-prop +
  α0 Rayleigh reproduces ζ spread PARTIALLY (fit 0.13-0.78% vs meas 0.06-1.05%) — extremes need a non-stiffness-
  prop (joint-friction) term modal ζ can't pin. zeta-unit caveat (.ash damp÷100) noted; conditioning is
  unit-independent + the group attribution is robust (xlsx bulkhead-modes-most-damped pushes MORE onto top_box).
- **(b) DESIGN (gated):** L-damp damping = α0 M + Σ_{g∈{top_box,plates,cross_beam,al_welds,angle_brackets}} β_g K_g
  (identifiable groups only; joints/contact flagged non-identifiable, need discrete dashpots + multi-ref data).
  Reduced 160×160 state-space complex eig in V_keep basis → FEM complex modes + ζ_m; predict complex FRF at the 8
  hard channels; before(uniform ζ=1%)/after(fitted non-prop C) peak-amplitude at the 8 channels. Building now.
- **(b) PROTOTYPE BUILT + RUN (`code/ldamp.py`, `out/ldamp_prototype.json`, `ldamp_prototype.md`):** COPY-reused
  Card A 74×74 reduced model + measured complex FRF + 8-channel mapping; added per-mode non-prop ζ_k in the FRF
  denominator. PRELIMINARY NEGATIVE: held-out peak |H| error mean 1.498→2.184, **1/8 channels better** (only ch52
  bolted joint). CAVEATS (run did NOT fairly test the over-damped-bulkhead hypothesis): fitted ζ_k collapsed to
  0.075-0.77% (all <1%, localized β→0 in the REDUCED basis; gate had β≠0 in V_keep) + used .ash÷100 ζ (not the
  authoritative xlsx 0.12-1.76% w/ the bulkhead bump). ROBUST SIGNAL: hard-channel amplitude errors are factor
  2-25. **CORRECTION (Andrew caught circularity 2026-06-19):** I had wrongly concluded "gap is shape not damping"
  via a bad order-of-magnitude argument ("damping moves peaks ~factor 2"). RETRACTED — measured ζ spans 0.06-1.76%
  (factor ~30) so damping CAN produce factor 2-25 swings; damping is NOT ruled out, and the prototype's negative
  is confounded by its degenerate fit. **REAL RESOLUTION:** resonant peak |H| ∝ φ_s φ_d / ζ_k = participation ÷
  damping → at a SINGLE impact, participation and damping are CONFOUNDED (same likelihood). That is why BOTH the
  Card-D shape/re-mesh attempts AND the damping prototype are inconclusive — the single-impact data is
  under-determined on exactly this trade-off, NOT because the answer is "shape" or "damping." Lever that breaks
  the confound = MULTI-REFERENCE / roving-hammer data (2nd drive varies φ_d, fixes ζ). Corrected ldamp_prototype.md.
  SURFACED: (i) run clean single-impact L-damp anyway (will likely confirm the confound) or (ii) close thread on
  the multi-reference-data conclusion. Note: did NOT edit Card A's ws; only COPIED its reduced model + FRF cache.

## D9 — Andrew (2026-06-19): review Das&Debnath2020 + Kiran2025 (+Schneider) for modeling complex damping w/ Bayesian updating
- Wrote `damping_modeling_review.md` + `references_reviewed.md`. SYNTHESIS = proposed method **L-damp**:
  (1) [DD20] localized NON-PROPORTIONAL damping C(θ)=α0 M+α1 K+Σ_g θ3_g C_g with C_g on the bulkhead/bolted-
  joint/cross interface groups (where our damping localized); mode-matching-FREE complex eigen-equation
  (λ²M+λC+K)Ψ=0 on measured complex eigenvalues λ̂=−ζ̂ω̂+iω̂√(1−ζ̂²) — ω̂,ζ̂ already in `.ash`; NUTS-safe (same
  fix as our L8b, no eigvec gradient); reduced 160×160 state-space solve in V_keep. (2) [S22] complex (mag+PHASE)
  FRF held-out likelihood = our Card A faithful-additive Schneider + a NEW phase channel + the DAMPED FRF.
- KEY: [S22] hit our EXACT amplitude ceiling (single global η can't match peaks → absorbed into σ_w≈0.31, ×2.7);
  the experiment = model damping physically (localized C) → does σ_w SHRINK + held-out complex-FRF coverage
  sharpen at the 8 hard channels? [K25] §8(a) names "complex modal data + non-classical damping on real-life
  structures" as THE open gap = ShockSat = the Ilias deliverable.
- GATE FIRST: damping-dissipation-fraction table ζ_m=(φᵀCφ)/(2ωφᵀMφ) per group (damping analog of our SE table)
  → which C_g are identifiable from 33 modes (expect bulkhead/cross/joint only). LIMITS: `.ash` shapes are REAL
  (proportional fit) → complex shapes inferred not observed; single impact caps identifiability; Card A Sim-B
  (single per-mode η didn't sharpen) ≠ this lever (per-INTERFACE C + phase) but success is empirical.
- SURFACE to Andrew before building (new method + new phase likelihood channel). No code built — design review only.

## D8 — Andrew Q (2026-06-19): "indicators of complex damping at the hard locations?" → YES (indirect)
- `code/damping_indicators.py` → `out/damping_indicators.json`, `damping_indicators.md` (+ tradeoff figure
  fig_tradeoff.png made earlier this session as the clearest before/after view).
- AUTHORITATIVE NASA FF modal summary xlsx: measured ζ spans **0.124–1.76% crit (14× spread)**; the top-damped
  modes are ALL bulkhead/cross "drum modes" (122.3Hz 1.76% Al+steel bulkheads+cross; 118.5Hz 0.83% bulkheads
  OUT OF PHASE; 107.5Hz 0.51% cross). Joint/bulkhead modes mean ζ 0.56% vs panel/other 0.27% = **2.1× more
  damped**. Damping tracks WHICH interface flexes, not frequency → textbook NON-PROPORTIONAL (complex) damping
  localized at the bolted-joint/bulkhead interfaces = the hard channels.
- CAVEAT: .ash stored REAL normal modes (proportional-damping fit) → direct complex-shape content discarded;
  this is interface-localized damping MAGNITUDE (strong indirect indicator), not directly-measured complex
  shapes. DATA-HYGIENE FLAG: modal-twin parsed .ash 'damp' (0.25–1.05) mislabeled vs authoritative (×65);
  real ζ=0.12–1.76%. Card A used uniform ζ=1% (over-damps panels, under-damps bulkheads).
- IMPLICATION: explains the residual the remesh campaign couldn't fix → the data-justified improvement is a
  non-proportional/complex damping model (per-mode/per-interface ζ), a DAMPING+DATA lever, not mesh/stiffness
  → reinforces the Card D boundary. SURFACE: the .ash damp mislabel is a data-hygiene note for Andrew/lead.

## D7 — CAMPAIGN COMPLETE + verdict (2026-06-18/19): shape-vs-frequency tradeoff; 0/10 clean improvement
- 11 solves done + dish 2× refinement. `out/before_after.json`, figure `figures/fig_before_after.png`,
  `correlation_contribution.md`, checker GREEN 14/0/0. RESULT: **NO edit improves a hard-region metric without
  degrading global MAC or frequency (0/10).** Every shape-improving edit (soften joints/boxes: e02 box+0.118/
  src+0.110, e07 box+0.092/src+0.067, e08 box+0.084) DETUNES frequency (|df%| +0.3..+0.9); every freq-improving
  edit (e01 calibrated-θ −0.32, e04 bottombox −0.48) doesn't help/slightly hurts shape MAC. Closest to a win =
  e07 top_box×0.9 (global MAC +0.010 AND all regions up) but +0.93% freq cost. Strut/contact (e09,e10) ~inert
  (low SE). DISH 2× refine: global MAC +0.0016 (36/38 modes unchanged <0.1%; the +17% partner = degenerate-
  cluster mode-swap artifact at 124.5-125.2Hz/1% dish participation, NOT real; only genuine dish shift −2.4%)
  → mesh CONFIRMED converged. VERDICT (correlation_contribution.md): as-received NASA FEM sits at a Pareto
  shape-vs-freq compromise; re-mesh/stiffness is NOT the lever; residual = damping + near-field + freq-align;
  real fix = data (multi-reference test + per-joint damping), not remodeling. Agent contribution = the rigorous
  auditable BOUNDARY of what remodeling can achieve (the Ilias "identify the gap" deliverable).
- SURFACE-only items NOT self-applied (await Andrew): docs/report/project_log.md row; any "replace inherited
  FEM" claim; durable-rule/checker changes. runtime.json: active ~3853 s (~64 min compute, 13 eigensolves).
- **open ambiguities:** (1) "re-mesh" scope in a custom Python assembler — literal local element subdivision
  (hard/risky) vs data-supported model edits (joint CBUSH/PBUSH stiffness, RBE2 bulkhead/bolted-joint
  connectivity, strut/dish local model, interface stiffness+damping). RECOMMEND: lead with high-leverage
  interface/connectivity edits; attempt true local refinement only where clearly feasible (dish, strut base,
  impact-face panel). Surface to Andrew with diagnosis evidence. (2) Damping (ch52 bolted joint) is an FRF lever,
  not an eigen/MAC lever — keep stiffness/connectivity/mesh as headline, note damping separately.

## D6 — Andrew steer (2026-06-18): "keep iterating until legitimate exhaustion of reasonable correlated-update attempts"
- Mandate: actually RUN edit->re-solve->measure attempts (not read-only), exhaust reasonable correlated FEM
  updates. BUILT: copied assembler pipeline into ws; baseline reproduced (max rel Δf 3.6e-10 vs inherited =
  meets 3e-10 bar; max ΔMAC 1.3e-8). BEFORE global matched MAC ≈0.63. Built `code/edit_solve.py` (per-PID
  block edit -> reduce -> eigsh80 -> global+region MAC + |df%| vs .ash; ~290 s/solve, detached+resumable).
- SE decomposition (modal twin joint_strain_energy.json): modes dominated by bottom_box 46.8% + top_box 34.9%;
  joints only 3.1% (near-rigid, in-path, weak lever); accel mounts 1e-4% (irrelevant). Bulkheads node-merged
  (welded — physically correct). CONM2 accel mounts out-of-band (~25 kHz).
- Data-driven update available = modal-twin NUTS posterior θ (CONVERGED R̂1.022, ESS232, 0div): bottom_box
  0.964, top_box1.048, cross_beam1.038, joints1.093, plates0.976, others ~1.0-1.02. Applying it IS the
  correlated update -> test if it improves MAC/region/amplitude (expect freq better, MAC ~unchanged per D22).
- Campaign queued: e01 calibrated-θ; e02 joints×0.5+contact×0.5; e03 joints×2; e04/e05 bottom_box×0.9/×1.1;
  e06/e07 top_box×1.1/×0.9; e08 bolted-joint801×0.3; e09 strut807×0.3; then a true local MESH-refinement
  attempt. next action: launch campaign detached, aggregate before/after.

## D5 — TOPOLOGY AUDIT RESULT (2026-06-18): topology is COMPLETE → the third lever is also ruled out
- Bulkheads PRESENT at expected Z (read-only `fem_model.npz` audit): Bottom_Box horizontal deck at Z=12.4
  (4896 elem) + Z=18.3 (1656); Top_Box bolted-joint interface at Z=18.4-18.5 (~1668) + bulkhead at Z=30.4
  (5104). ch40 (Z10.4 "below bulkhead"), ch52 (Z19.1 "above bolted joint"), ch69 (Z28.7 "below bulkhead")
  each sit immediately adjacent to a modeled bulkhead/interface.
- Bolted joint PRESENT as CBUSH PID 801 at the steel↔aluminum interface (Z=18.4).
- Strut region PRESENT/rich: Top_Box extends to Z≈57; Cross_Beam (Z42.4), Rectangular_Plates (Z39-48),
  Top_Brackets (Z45-57), Angle_Brackets (Z41-42); ch92 strut base richly meshed.
- VERDICT FORMING: all THREE candidate data-driven levers are ruled out by evidence — (1) finer mesh (D3:
  already converged 37-135 elem/wavelength), (2) missing/wrong topology (D5: complete), (3) joint stiffness
  (D1: finite, NASA-correlated, non-identifiable, θ-scaling didn't fix amplitude in Card A). → the per-sensor
  amplitude misses are NOT a re-meshable defect; residual = interface/joint DAMPING + near-drive/near-field
  local response + frequency-misalignment near sharp resonances (Card A evidence).
- next action: SURFACE to Andrew; propose to make the negative AUDITABLE with one before/after demonstration
  (stand up baseline copy + one representative data-motivated connectivity edit → re-solve → show no
  correlation improvement), then write `correlation_contribution.md` honest verdict.

## D4 — Andrew steer (2026-06-18): "2" = pivot to the topology/connectivity lever (not mesh density)
- Mesh refinement ruled out (D3); joint re-stiffening ruled out (D1). Andrew picks the ONE legitimate remaining
  "remodel from data" lever: TOPOLOGY/CONNECTIVITY — is a real bulkhead MISSING from the box column
  (ch40/52/69 "below/above bulkhead"), or is the strut-base attachment (ch92) topologically wrong? Adding/
  correcting a missing member genuinely changes mode SHAPES (unlike θ-scaling or finer mesh).
- next action: read-only topology audit of Bottom_Box/Top_Box internal structure (are bulkheads present at the
  expected Z?), the steel↔al bolted-joint interface, and the strut-base attachment. If something is missing/
  misconnected, that is the data-driven edit to make + measure before/after. If all present/correct, that is
  itself the finding (the error is damping/near-field, not topology).

## D3 — DECISIVE PRE-EDIT FINDING (2026-06-18): the inherited FEM is already mesh-converged → "re-mesh finer" is NOT the lever
- The whole model is UNIFORMLY meshed at ~**0.25 in edge length everywhere** (Bottom_Box, Top_Box, dish/
  Top_Circular_Plate, Cross_Beam, brackets, +X impact face — all 0.25 in median; 67k shells / 406k DOF).
- The "dish" = Top_Circular_Plate (PID 701) is at Z=57.75, **thick (t=0.777 in)** and already finely meshed
  (4056 elem, edge 0.16-0.25 in) — NOT a coarse/under-resolved flexible dish.
- Points-per-wavelength (plate bending, band top 260 Hz, `code`-reproduced): **37-135 elements per bending
  wavelength** (h=0.06->37, h=0.125->54, h=0.777->135) vs the ~6-10 needed for convergence → mesh converged
  by a 4-13x margin. Corroborated: the inherited model already matches NASA modes <1% (modes 1-4) and the
  element library validated <0.5% vs beam/plate theory.
- **IMPLICATION:** local mesh REFINEMENT provably cannot move the <260 Hz mode shapes/frequencies → it cannot
  be the data-driven lever for the per-sensor amplitude misses. Combined with D1 (joints already finite &
  non-identifiable), the card's two obvious levers (finer mesh; soften joints) are BOTH ruled out by evidence.
- This is a VERDICT-SHAPING finding that contradicts the card's premise → SURFACED to Andrew (not self-applied)
  before building any refinement, with a proposed honest revised plan. Pending his steer.

## D2 — Andrew scope call (2026-06-18): "start with A and proceed to others after"
- APPROVED option (A): focused TRUE local mesh refinement at the **dish (ch98)** + **impact/source face
  (ch4/27/38)** first (highest-confidence under-resolved local-mode regions), with honest before/after; THEN
  proceed to the others (strut base ch92; box-column/bulkhead connectivity ch40/52/69) after.
- Order locked: (1) reproduce BEFORE baseline in the copy; (2) dish local refinement; (3) impact-face local
  refinement; (4) strut base; (5) box-column (lowest expected payoff — may report honest negative).
- COMPUTE NOTE: full eigensolve ≈383 s (>120 s default tool timeout) → every eigensolve MUST be launched
  DETACHED + resumable per AGENTS detached-launch gate; pin BLAS threads; float64.

## D0 — Inherited hard constraints (task card §0,§4; non-negotiable)
- Plain standalone 9-group ShockSat ONLY (source = `shocksat_fem_modal_twin_20260609`). NO coupled tray.
- **COPY-never-edit** the inherited FEM. Validate the BEFORE baseline (eigenfreqs + MAC) before ANY edit.
- Every "improved correlation" claim needs the before/after MAC+frequency table AND a figure.
- Do NOT overfit the mesh to the 8 sensors at the expense of global correlation (report global MAC both ways).
- If re-reduce: reduced-model fidelity must match full-FEM eigenfreqs to ~3e-10 (the validation study's bar).
- Compute: pin BLAS threads (OMP_NUM_THREADS=1 etc.), float64, long solves detached + resumable.
- SURFACE (do NOT self-apply): any durable-rule/checker change; any claim the remodeled FEM should REPLACE the
  inherited one; the `docs/report/project_log.md` row. Mesh edits + diagnoses are study artifacts — no stop.

## D0.1 — Inherited evidence the diagnosis must respect (from validation study D18/D20/D22, packet §2)
- As-received FEM gets global FREQUENCIES well (modes 1-4 within ~0.1-0.3%) and shapes mostly well
  (MAC-matched ≈0.73 vs `.ash`; clean low modes 0.88-0.98). The error is PER-SENSOR AMPLITUDE at the 8
  interface/impact-face channels.
- The 8 hard channels (ch4,27,38,40,52,69,92,98) are clean raw data (not bad-DAQ; ch29-31/101 already excluded),
  and the miss is NOT a node-mapping artifact (snap→interp <1%). It is genuine model-form error at joints/
  interfaces/near-field.
- KEY LEVER FINDING (D22): scaling θ stiffness does NOT move the FEM mode shapes (L6/L10 MAC-in-likelihood did
  not sharpen); inferring the mode-shape FIELD (Beck) DID sharpen. Implication for Card D: a genuine MESH/
  CONNECTIVITY change alters φ itself (unlike θ-scaling) → it is the right class of lever to test, but success
  is NOT guaranteed (ceiling is a combination: residual shape error + freq misalignment + dense-mode
  superposition + damping). Honest negative + diagnosis is an acceptable deliverable per the card.

## D0.2 — Tooling inventory (from `shocksat_fem_modal_twin_20260609`)
- From-scratch Python NASTRAN assembler (no pyNastran, no external solver): `scripts/parse_nastran.py`,
  `assemble_fem.py` (per-PID K blocks: K(θ)=K_fixed+Σ θ_g K_g), `solve_nominal.py` (eigsh, 80 modes ~383 s),
  `fe_core.py` (element library: QM6 membrane, MITC4/DKT bending, CST, CBUSH, RBE2, CONM2; validated).
- FEM model: 67,683 grids / ~406k DOF, 67,366 CQUAD4, 428 CTRIA3, 166 CBUSH (9 PBUSH), 80 CONM2, 150 RBE2.
- Measured: `measured_modes.npz` = 33 modes × 76 nodes × 3 axes + damping (`.ash` EMA survey).
- CalculiX available in `.conda_calculix` (alternative solver if needed; document if used).
