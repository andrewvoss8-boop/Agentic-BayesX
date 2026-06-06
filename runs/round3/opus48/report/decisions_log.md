# Decisions Log — Round 3 (Claude Code Opus 4.8 runner)

Append-only record of every clarification/decision agreed with the human, with rationale and where it
landed. **If context is ever compacted, re-read (in this order) before continuing so you don't drift:**
`docs/agents/competitive_full_experiment/round3/task_card_round3.md`, this workspace's
`report/priority_deliverables.md`, this `report/decisions_log.md`, and `commands.md`. Also useful:
`report/statfem_lessons.md` and `report/research_directions_and_proposals.md`.

## Standing facts / anchors (quick re-grounding)
- Workspace = `runs/round3/opus48/` ONLY. Read shared inputs read-only; write nothing outside. Do NOT
  edit immutable checkers (verify `shasum -a 256 -c harness/checkers/manifest.sha256`).
- Sampler = NumPyro NUTS (JAX). Convergence gate: rank-split R-hat<1.01, bulk&tail ESS>=400 (4 chains),
  divergences<2%, non-centered hierarchical latents. Never claim "NUTS active" unless it passes.
- Anchors (hard): dome interface mode 1 = 93.50 Hz (=0.85x110 nominal), tray interface mode 1 = 86.25 Hz.
- Env: `.venv_nuts` (jax 0.4.30, numpyro 0.15.3, numpy 1.26.4); local libs in `.pylibs` (meshio, pptx,
  pypdf) put on PYTHONPATH. Run with `PYTHONPATH="runs/round3/opus48/.pylibs" .venv_nuts/bin/python ...`.
- Terminology: do NOT say "smoke test"; say "quick low-sample test run (not for reporting)".

## Decisions (chronological; append new ones at the bottom)

### D1 (2026-06-03) Dome 93.5 Hz is the BOUNCE/BREATHING mode, NOT a "local mount mode"
- Ambiguity: I initially framed 93.5 Hz as a local mount-region mode with ~1 kg effective mass.
- Decision (human-corrected): it is the global axisymmetric **bounce/breathing mode** (~110 nominal,
  93.5 as-built); effective interface mass is LARGE (~150-250 kg of cap mass), not ~1 kg.
- Rationale: physically the whole top shell translates/breathes axially — the interface-relevant mode for
  an apex-mounted payload. My 1-D meridional-strip model UNDERESTIMATES shell membrane stiffness (raw
  mode ~17 Hz at 3.5 bar -> needed ~30x calibration), so the deficiency is my model, not the physics.
- Where: packet.md, known_failures.md S4, assumptions_ledger rows 14/18.

### D2 (2026-06-03) Deviate from round-2: reverse-engineer the forcing from the 0.1 g^2/Hz dome anchor
- Ambiguity: keep round-2's abstract force scaling vs re-derive.
- Decision: REVERSE-ENGINEER the flat ORIGINAL (+6 dB initial) force PSD so the DOME-ONLY interface
  response peaks at 0.1 g^2/Hz at the bounce mode; flight mean = -6 dB design envelope. Use PHYSICAL
  masses (dome bounce eff mass ~225 kg via 0.40 cap-mass participation; load 142 kg).
- Rationale: makes forcing + netCG physically scaled (~1 g) instead of abstract milli-g; ties the model
  to the 0.1 g^2/Hz dome-response anchor (same process that set round-2's original force).
- Where: mdof_forward.reverse_engineer_force / dome_eff_interface_mass; run_pipeline PHYS layer;
  results.json forcing_reverse_engineered; figures/flight_forcing_overlay.png.

### D3 (2026-06-03) No 2DOF staged data — generate synthetic MDOF observations
- Ambiguity: the staged dataset is 2DOF; the inference was effectively round-2 2DOF.
- Decision: STOP using the 2DOF staged data; GENERATE synthetic MDOF observations carrying the same noise
  structure (sensor noise, build-to-build, flight-to-flight). BU model knows only a coarse FEM / close
  guess of the modes, not the truth.
- Rationale: framing-challenger #1 — same-model-family data makes recovery trivial ("plumbing"); real
  value needs genuine model-form error the inference cannot represent.
- Where: statfem_*.py data generators.

### D4 (2026-06-03) Learn ONLY interface stiffness k_j this run; damping fixed
- Decision: update a SINGLE physical parameter k_j; hold damping fixed (structural loss eta=0.04 only to
  make FRFs finite, NOT learned). Expect (and report) bias from unmodeled effects.
- Rationale: pressure-test the process with one knob; complex/frequency-dependent joint impedance and
  damping deferred to a future run (human direction).
- Where: statfem_hexapod.py / statfem_hexapod_hier.py.

### D5 (2026-06-03) Two distinct model-form errors: SPATIAL + FREQUENCY
- Decision: ground truth carries (A) SPATIAL error = per-strut stiffness varying across azimuth
  (symmetry-breaking, in the physics) and (B) FREQUENCY error = additive output GP on the FRF.
- Rationale: maps to StatFEM (Girolami): (A) = stochastic-forward parameter/field error; (B) = the output
  model-inadequacy term d. They behave differently and stress different parts of the inference.
- Where: tray_hexapod.spatial_error_pattern; statfem_hexapod make_freq_error; statfem_lessons.md.
- Key finding: the frequency-discrepancy d CANNOT fix the spatial error (with-d ~ without-d k_j bias);
  the discrepancy must MATCH THE STRUCTURE of the error.

### D6 (2026-06-03) Tray = 6 two-force struts, octahedral, RBE'd to ONE interface node
- Ambiguity: how to make the tray genuinely MDOF while keeping single-interface FBS.
- Decision: rigid isogrid tray + 136 kg avionics on **6 axial struts** (octahedral hexapod, minimal
  6-DOF constraint), RBE'd at the base to a SINGLE interface node. 6 mount modes; axial anchored 86.25.
  Struts = real constant springs (no complex impedance yet).
- Rationale: physical, statically-determinate mount; single FBS interface preserved; the symmetry gives
  degenerate mode pairs that the spatial error SPLITS (the model-form signature).
- Where: tray_hexapod.py (note: first attempt was under-constrained -> fixed to octahedral pattern).

### D7 (2026-06-03/04) Observe 6-DOF apparent mass for inference; axial (M_zz) for QOI coupling
- Decision: inference uses ALL 6 diagonal components of the interface apparent mass; the netCG/interface-
  PSD QOI coupling uses the axial (z, launch) component.
- Rationale: 6-DOF needed to be genuinely MDOF and to see the spatial split; axial is the FBS force path.

### D8 (2026-06-04) Make it hierarchical: also learn sigma_build (the aleatory scatter)
- Ambiguity: a single k_j is over-determined (epistemic ~0.1%) -> "learning" invisible.
- Decision: HIERARCHICAL model — learn population mean k_j AND build-to-build scatter sigma_build.
- Rationale: a variance genuinely needs repeated builds, so its posterior CONTRACTS build-by-build
  (decision-relevant predict-a-new-build margin). This is the visible, real sequential learning.
- Where: statfem_hexapod_hier.py; figures hier_sigma_build_*; converged (R-hat<=1.003, ESS>=1300; 0 div
  at N=2,8, 0.2% at N=4 -> within gate but reported honestly).

### D9 (2026-06-04) Sequential-assimilation GIFs for the QOI; slow GIFs 5x
- Decision: build slow GIFs walking ONE data point at a time for netCG and interface PSD showing PRIOR vs
  POSTERIOR (95% CI) vs ground truth; show epistemic-only band (collapses) vs total band (stays wide).
  Slow all learning GIFs to ~5x (6.0-6.5 s/frame). Don't overlay all flights (keep frames readable).
- Rationale: visualize learning AND answer "why do QOI bands stay constant" = aleatory-dominated.
- Where: statfem_sequential_qoi.py; figures seq_netcg_*/seq_iface_* gifs; frf_truth_bu_buplusd.png.
- Robustness fix: init NUTS at the prior guess (init_to_value) to stop stuck-high chains (k_j -> 1e10).

### D10 (2026-06-04) StatFEM clarifications recorded
- M_xx = lateral diagonal of the interface APPARENT-MASS matrix (force_x/accel_x).
- sigma_d, ell_d are FIXED constants the likelihood knows (it samples only discrepancy coefficients);
  discrepancy is FREQUENCY-only; NO spatial discrepancy in the inference (spatial error is truth-only).
  Caveat (flagged): truth frequency-error size was set equal to assumed sigma_d -> over-convenient;
  learning sigma_d would remove this.
- build-to-build = hierarchical parameter prior; flight-to-flight = random forcing source term;
  d and e separate (StatFEM mapping).

### D11 (2026-06-04) Adaptive frequency grid = standard for this problem class (PROPOSED hook)
- Decision: use `adaptive_frequency_grid(modes, zetas, fmin, fmax)` (code/adaptive_freq.py) — coarse
  log/octave baseline + dense mode-local clusters derived from the SOLVED modes (no hardcoded freqs).
- HONEST result: ~11x better PEAK fidelity at matched cost; integrated 3*GRMS is grid-robust either way
  (matched-N adaptive can be slightly worse on the integral if baseline starved). Rule: adaptive for
  peak-sensitive outputs; keep adequate log baseline for integrals.
- Approval gate: proposed as a harness/skill HOOK but NOT written to harness/ (durable-rule change +
  workspace isolation). Reference impl + proposal in research_directions_and_proposals.md S A. Awaiting
  human go to place into the harness.

### D12 (2026-06-04) Element-feature-space discrepancy = prioritized novel direction (design only)
- Idea (human): discrepancy correlation by element PROPERTY/TYPE proximity (same property -> high corr;
  same type spring/beam/shell/solid -> moderate; far in both -> low), optionally by stiffness magnitude.
- Decision: prioritize as a novel research direction; START with property/type (+stiffness), parameter-
  space; DEFER the modal-participation variant (that re-enters the frequency domain).
- Rationale: model-form error clusters by which modeling ASSUMPTION is wrong (element tech/property), not
  raw spatial distance; generalizes statFEM's spatial GP kernel. Design in
  research_directions_and_proposals.md S B. Not yet built.

### D14 (2026-06-04) Reprioritize next steps per anti_collapse_recommendation_and_study.md
- Input: report/anti_collapse_recommendation_and_study.md (R1-R8 + factorial collapse study).
- Decision: elevate TRUST DIAGNOSTICS above feature-adding. New recommended order:
  1. **R2 grid-invariance / N_eff test** (cheap, decisive, on the EXISTING model): refine the inference
     frequency grid 1x/2x/4x; if k_j/sigma_build posterior sd keeps shrinking ~1/sqrt(N_f) -> we are
     OVER-COUNTING correlated model error as independent (fictitious tightness); if it PLATEAUS -> honest.
     This validates/invalidates everything we've shown about the tight posteriors.
  2. **R6 held-out calibration** (the decisive collapse detector): hold out whole builds AND frequency
     bands; report 95% CI coverage + posterior-predictive checks. Gates "trust the QOI margin."
  3. **R4/D13 propagate d (+ aleatory build/flight) into the netCG & interface-PSD QOI.**
  4. **R3/A4 parameter-space discrepancy** (joint-impedance GP and/or element-feature per-strut kernel; D12).
  5. **Factorial study or its Minimum Viable Slice** (A1 vs A3 vs A4+A7, truth C2+C3, sweep grid 1x/2x/4x
     and builds {1,4,16}; metrics: collapse curve, bias, held-out coverage, QOI) -> "menu with tradeoffs"
     decision aid + evidence base for proposing R2/R6/R8 as durable checks.
- Rationale: the central question is whether a tight k_j/netCG posterior is TRUSTWORTHY; R2 (cheap) and R6
  (decisive) answer that and recontextualize the prior #1 (d-into-QOI), which remains but drops to step 3.
- Honesty note carried: R8 only PARTIALLY satisfied so far — spatial error is outside the inference span
  (good) but the truth's FREQUENCY error was set equal to the assumed sigma_d (over-convenient, D10); the
  study must author the truth fully independently and require exhibiting bias/non-coverage.
- Approval gates unchanged: R8 as a durable harness rule and R2/R6/R8 as durable checks are [PROPOSAL]s;
  reference implementations stay in-workspace until approved.

### D15 (2026-06-04) Adaptive-grid hook refinement: raw data, computed-once, fixed during inference
- Question (human): the adaptive grid needs known/estimated modes; with RAW data we don't know them. Can
  we compute the spectrum densely once, then downsample to a fixed coarse+refined grid for the expensive
  inference, or will the spectrum move too much per step and be brittle?
- Decision (design): YES, computed-once + FIXED-during-inference is the correct pattern.
  (a) locate resonances cheaply WITHOUT per-step eigensolves: peak-pick the measured data spectrum (its
      peaks ARE the resonances), or use the coarse-FEM/prior mode estimate, or a few eigensolves over the
      prior range; (b) build ONE fixed grid = coarse log baseline + dense zones covering each resonance's
      PLAUSIBLE RANGE (sized to the prior / data-peak width, e.g. +/-15-20% for a +/-25% k_j prior);
      (c) reuse that SAME grid for every NUTS step; (d) confirm density with the grid-invariance check.
- Rationale / brittleness: do NOT recompute the grid each step — a parameter-dependent grid makes the
  likelihood inconsistent step-to-step and breaks HMC gradients (THAT is the brittle option). It is NOT
  brittle if the single fixed grid is dense over the range the resonances can move; modes wander only
  within the parameter range (and the data peaks bound the truth). Posterior is tight so modes barely
  move during sampling; range-sizing covers warm-up exploration.
- Status: extends D11 (adaptive grid). Reference impl `adaptive_frequency_grid` already accepts arbitrary
  mode estimates; a data-peak-pick front-end + range-sizing is the small addition. Still [PROPOSAL] for
  the harness hook (needs approval).

### D16 (2026-06-04) Lead trust-test = HELD-OUT CALIBRATION, not grid-refinement
- Concern (human): with one scalar k_j overwhelmed by data, the posterior is tiny regardless, so refining
  the frequency grid may show little movement even if the tightness is fictitious -> grid check could lull
  us. Valid.
- Why valid: tightness is multi-source (frequency points + 6 DOFs + 8 builds + the sharp peak); the grid
  check wiggles only the frequency axis, so a flat result is NECESSARY but NOT SUFFICIENT. Also epistemic
  tightness is not the decision-relevant quantity (aleatory build/flight scatter is).
- Why grid check still has some value: it reads the RATIO (a 1/sqrt(2) shrink per doubling is detectable
  even at ~0.1% sd), and the WITH-d (should plateau) vs WITHOUT-d (should shrink) contrast exposes
  frequency over-counting. But it only covers one axis.
- Decision: make **held-out calibration** the PRIMARY trust test (it detects fictitious tightness/bias
  regardless of source or whether the interval moves): hold out whole builds AND whole frequency bands,
  predict, check 95% coverage + posterior-predictive checks. Add two cheap companions: (1) a
  STARVE-THE-DATA sweep (1 DOF / 1 build / narrow band) to make over-counting or bias visible by removing
  the deluge; (2) report EFFECTIVE vs NOMINAL independent-sample count (model error is correlated, so
  N_eff << raw point count; the ratio is the over-counting, shown even when sd is tiny). Keep the
  grid-refinement check only as a supporting diagnostic.
- Supersedes the D14 ordering: lead with held-out calibration (+ starve-data + N_eff), then the rest.

### D17 (2026-06-04) Master plan written (report/master_plan.md)
- Decision: adopt a staged, iterative plan culminating in ONE big sequentially-updated master run, with a
  non-negotiable trust throughline at every stage (independent truth; held-out calibration as primary
  trust test; starve-data + N_eff companions; NUTS gate over all latents; adaptive grid; full-uncertainty
  QOI). Stages: 0 trust harness + honest baseline (fix the R8/D10 over-convenience); 1 learn ALL
  hyperparameters (sigma_d, ell_d, sigma_build, sigma_e); 2 more physical parameters (+damping); 3
  PROPERTY-BASED spatial model-form-error GP (the novel element-feature discrepancy, D12); 4 higher-
  fidelity FEM (flexible isogrid panel + shell/refined dome; reduced-order/TensorMesh as needed); 5 MASTER
  RUN = realistic sequential aerospace digital twin (fleet of builds + flights, all params+hyperparams+
  property discrepancy, QOI with epistemic+aleatory+model-form uncertainty, spec-envelope/force-limiting
  decision, build-by-build then flight-by-flight GIFs, held-out calibration throughout).
- Rationale: addresses the collapse/trust concerns (D14/D16) AND the human's targets (learn all
  hyperparameters + more params, property-based spatial discrepancy GP, higher-fidelity FEM, realistic
  aerospace workflow) in dependency order.
- Approval gates: durable harness rules/hooks (held-out calibration, independent-truth, adaptive-grid
  check) remain PROPOSALS; no writes outside workspace without approval. Recommend starting Stage 0+1.

### D18 (2026-06-04) Stage 0+1 executed (trust harness + learn all hyperparameters) — preliminary
- Built code/stage01_trust_hyper.py: INDEPENDENT truth (spatial per-strut + NON-Matern Gaussian-bump
  frequency error + build scatter + sensor noise; fixes the D10 over-convenience); learns ALL
  hyperparameters (k_j_pop, sigma_build, sigma_e, and discrepancy sigma_d + ell_d via a Hilbert-space
  reduced-rank GP so ell_d is learnable with a fixed basis); trust harness = held-out calibration
  (leave out builds + a frequency band), effective-vs-nominal sample count, with/without-d, starve-data;
  adaptive frequency grid fixed during inference.
- Validity fix during build: informative ell_d prior + soft lower bound (~0.2 norm-u) stopped the
  discrepancy collapsing to noise-like tiny scales -> divergences went 13 -> 0.
- PRELIMINARY (low-sample quick test; full convergence-grade run launched, results to confirm):
  * sigma_build recovered 0.052 (true 0.050); sigma_e INFLATED 0.22 (true 0.08) -> the frequency-only
    discrepancy cannot represent the SPATIAL error, which leaks into sigma_e (and sigma_d~0.89). This is
    the quantified motivation for Stage 3 (property-based spatial discrepancy): a correctly-STRUCTURED
    discrepancy should absorb the spatial error instead of inflating noise.
  * Held-out 95% coverage ~0.99 (with AND without d) -> OVER-conservative (bands too wide from the
    inflation), NOT collapsed-onto-bias. Lesson: read coverage WITH sharpness/sigma_e, not alone.
  * Effective sample count ~86 vs nominal 1440 (ratio ~0.06) -> tightness is correlation-limited, not
    from independent data (directly answers the data-deluge concern, D16).
  * k_j bias ~2% but COVERED (intervals wide enough) -> with-d does not collapse onto bias here.
- Exit-gate status: needs the full run to confirm R-hat<1.01 / ESS>=400 (quick test 1.019/226, 0 div).
- Honest read: Stage 0/1 PASSES the trust intent (no fictitious tightness; over-counting made visible)
  and HANDS the spatial-error problem to Stage 3.
- **UPDATE — full run did NOT converge (see D19); the "preliminary passes" above is superseded.**

### D19 (2026-06-04) Stage 0+1 FULL run FAILED the convergence gate — diagnosis + decision
- Full run (800 warmup + 800 draws, 4 chains, ~72 min): **worst R-hat 1.54, min ESS 7, 1 divergence ->
  NOT converged.** Per CLAUDE.md this is reported as a FAILURE, not "NUTS active". (k_j bias 3.9% covered;
  learned sigma_build 0.068 (true 0.050), sigma_e 0.227 (true 0.080), sigma_d 0.934, ell_d_eff 0.359.)
- Diagnosis: short run (R-hat 1.02) vs long run (R-hat 1.54) inversion + ESS~7 = a NON-IDENTIFIABLE RIDGE.
  Cause: the frequency-only discrepancy cannot represent the SPATIAL error, so that error can be absorbed
  EITHER by sigma_d OR by sigma_e (a sigma_d<->sigma_e trade-off the likelihood barely distinguishes) ->
  chains wander the ridge -> no convergence. This is the R5 theta<->discrepancy identifiability hazard at
  the HYPERPARAMETER level.
- Lesson (stronger than D5): a mis-structured discrepancy doesn't only bias the parameter / inflate noise
  -- when you try to learn ALL hyperparameters jointly, it DE-IDENTIFIES (sigma_d vs sigma_e) and BREAKS
  CONVERGENCE. "Learn everything with a flexible misspecified discrepancy" is not free.
- Decision options (await human steer):
  (A) Quick interim to get a converged Stage 0/1 baseline: break the ridge by constraining the
      discrepancy -- FIX sigma_e (or tighten sigma_d prior) so sigma_d/sigma_e aren't jointly free;
      "learn all hyperparameters" then carries the honest caveat that sigma_e<->sigma_d are not jointly
      identifiable under a misspecified discrepancy. (~1 run)
  (B) Go straight to STAGE 3 (property-based spatial discrepancy): structure the discrepancy so the
      spatial error IS representable -> sigma_d and sigma_e should separate -> identifiability + convergence
      restored AND sigma_e stops inflating. This is the real fix and Stage 0/1 has now decisively
      motivated it.
- Recommendation: (B), with a small (A)-style confirmation that fixing the structure (not just constraining
  priors) is what restores convergence.

### D20 (2026-06-04) Handoff written for the master agent / multi-subagent protocol
- Wrote report/handoff_to_master.md: state of play, code inventory, durable findings, per-stage next steps
  + suggested subagent ownership + exit gates, open approvals, and suggested subagent roles. KEY protocol
  rule highlighted: the TRUTH-AUTHOR subagent must be SEPARATE from the INFERENCE subagent (prevents the
  same-family tautology that made the original run "plumbing"); the TRUST subagent's gate is binding.

### D13 (2026-06-04) Open gap to close next
- The netCG/interface-PSD QOI predictions propagate only k_j (epistemic) + aleatory (build+forcing); they
  do NOT yet propagate the learned discrepancy d into the QOI. A complete twin predicts the QOI from
  corrected apparent mass = BU(k_j)+d (with d uncertainty), incl. honest band-growth outside the measured
  band. Flagged to implement (recommended next priority).

## ===== BLIND INFERENCE ROUND (vs Codex independent truth) — 2026-06-04 =====
Role now: INFERENCE runner, BLIND, against runs/round3/codex_truth/dataset/ (observations.npz +
data_contract.md, read-only). MUST NOT open codex_truth/sealed_truth/, /code/, or /report/. Master scores
my posterior vs the sealed truth after I commit. Protocol: blind_handoff_protocol.md.

### D21 (2026-06-04) Published data is the COUPLED interface apparent mass (read from the asymptote)
- Inspected observations.npz (read-only, allowed): 8 builds x 6 DOF x 4040 freq (5-600 Hz) complex
  apparent mass; 11 flights forcing PSD; response_psd_g2_per_Hz (8x11x4040) + netcg_3grms_g (8x11);
  load_mass_kg=170, g0 stored. forcing model published (mean -6 dB, Matern-3/2 in log10 f, ell=0.28,
  f2f 3 dB) — matches the shared design assumptions.
- Finding: low-frequency |apparent mass| asymptotes are LARGE (x~518, y~524, z~603 kg; rx/ry~763, rz~607
  kg*m^2). That is the RIGID-BODY mass/inertia the interface drives = dome large effective bounce mass +
  load (170 kg) + interface hardware all moving together at low f. So the published channel is the COUPLED
  interface apparent mass, NOT the load alone (my old hexapod-only model gives ~142 kg -> 4x too small).
- Decision: model the published apparent mass as M_diag(w) = M_base6 (lumped rigid dome+interface effective
  mass/inertia, gives the low-f asymptote) + tray-on-hexapod condensed apparent mass (k_strut, mount modes)
  + an axial dome-bounce resonator on z (f_dome~93.5). Reading the rigid-body mass off the low-f asymptote
  is STANDARD apparent-mass practice (a direct measurement), NOT reverse-engineering the hidden structure.
- Honesty: my model is COARSE/linear/symmetric (6 equal struts, single axial dome mode, fixed damping).
  Data peaks (z ~62/77/120/163; x ~51/87/137; rz ~95) are richer/shifted vs nominal 86.25/93.5 -> genuine
  model-form error OUTSIDE my model's span. Expect bias + non-coverage; that is the experiment.

### D22 (2026-06-04) Learnable parameters + hierarchy + discrepancy for the blind fit
- Physical (population + per-build lognormal scatter where aleatory): k_strut (sets the 6 mount modes;
  primary as-built stiffness, hierarchical with sigma_build), m_scale (one multiplicative scale on the
  rigid M_base/M_tray to absorb nominal-vs-as-built mass error; population-level), f_dome (dome bounce
  freq, prior ~N(93.5, 8 Hz)). Damping eta FIXED (only to make FRF peaks finite; not identifiable from
  magnitude-only without phase weighting -> documented limitation).
- Hyperparameters: sigma_build (build-to-build k_strut scatter, aleatory), sigma_e (sensor noise, log),
  sigma_d (frequency discrepancy magnitude). ell_d FIXED informative (per D19: jointly learning
  sigma_d+ell_d+sigma_e under a mis-structured discrepancy de-identifies -> the sigma_d<->sigma_e ridge
  that broke convergence). Discrepancy = per-DOF Matern HSGP over log-freq (reuse Stage-0/1 machinery).
- Likelihood: WHOLE-CURVE log|apparent mass| on the adaptive grid (magnitude, log-space), per DOF/build.
  State: magnitude-only (phase not fitted this run) -> damping/loss weakly identified; flagged.
- If the sigma_d<->sigma_e ridge returns (R-hat>1.01 / ESS<400 / divergences), I REPORT THAT as the result
  (do NOT claim "NUTS active"), per CLAUDE.md. The ridge itself is an honest finding about misspecification.

### D23 (2026-06-04) Trust = held-out calibration (PRIMARY), grid from DATA peaks
- Adaptive frequency grid computed ONCE from the DATA peaks (peak-pick build-averaged |AM| per DOF; I do
  NOT know true modes) + coarse log baseline; FIXED during inference (per D11/D15). Focus band where modes
  live; do not over-extend.
- Held-out calibration: hold out whole BUILDS and a whole FREQUENCY BAND; report 95% predictive coverage +
  posterior-predictive checks; read coverage WITH sharpness/sigma_e (wide-but-covering != success).
  Companions: effective-vs-nominal sample count; starve-the-data; with/without-d.
- QOI: propagate FULL uncertainty (k_strut epistemic + build/flight aleatory + discrepancy d w/ its
  uncertainty) into netCG (3*GRMS) and the interface response PSD vs the test spec (narrow-band
  exceedance). Closes D13 for this run.

### D24 (2026-06-04) BLIND RESULT: the inference does NOT converge — multimodal/non-identifiable (HONEST)
- After building the coarse model + hierarchical StatFEM NUTS and validating the pipeline, the MAIN fit and
  EVERY reparameterization I tried FAIL the convergence gate (rank-split R-hat ~1.5-2.8, bulk ESS ~5,
  0 divergences, fast steps but NO between-chain mixing => genuine MULTIMODALITY, not under-warming;
  confirmed at warmup 150/800 alike). sigma_e inflates to ~0.6-0.85 (log) = factor ~2 misfit.
- Variants tested (all FAIL the gate): (a) full hierarchical + flexible learn-sigma_d (R-hat~2.7, sigma_d->2.7
  overrides its prior = the D19 sigma_d<->sigma_e RIDGE returns); (b) capped sigma_d=0.3, low-rank
  discrepancy (R-hat~2.4); (c) + fixed sigma_build=0.05 (R-hat~1.5); (d) minimal: learn k_strut+sigma_e,
  fix f_dome+sigma_build, capped low-rank d (R-hat~1.54, k_strut CI [1.9e7,8.7e7] BIMODAL = the
  parameter<->discrepancy degeneracy: a "very stiff struts -> modes leave band -> discrepancy explains
  everything" second mode); (e) PURE physics, no discrepancy (R-hat~2.1, sigma_e~0.84 = WORST). So the
  multimodality is INTRINSIC: no single symmetric-hexapod k_strut fits all 6 DOF of the as-built truth.
- Honest interpretation (this IS the experiment's result): the INDEPENDENT truth carries model-form error
  genuinely OUTSIDE my coarse symmetric model's span (6 equal struts, single axial dome mode, magnitude-
  only). Recovery is therefore NOT a tautology -- it BREAKS (multimodal + ridge). This is exactly what
  round 2's "plumbing" critique predicted and what the blind protocol was designed to expose. The
  frequency-only discrepancy CANNOT represent the (apparent spatial/asymmetry + higher-mode) error; it
  de-identifies the physics. Per CLAUDE.md I do NOT claim "NUTS active".
- Decision: report the FULL hierarchical model (learn k_strut, f_dome, sigma_build, sigma_e, capped
  low-rank discrepancy) as the primary, LABELED NOT-YET-CONVERGED, with worst-case R-hat/ESS next to every
  interval; document all 5 variants as evidence it is not a parameterization artifact; give the master the
  (stable-across-configs) marginal medians as best-available, heavily caveated. Held-out coverage is
  "achieved" only via ~12x-wide bands (wide-but-covering != success) and under-covers held-out frequency
  bands (~0.6-0.84). QOI ~2x biased vs published, very wide. Recommends Stage-3 property/structure
  discrepancy + higher-fidelity / asymmetric model as the fix.
- Tractability decisions logged: max_tree_depth 11->9 (deep trees were the cost); index-masking instead of
  obs_mask (avoid imputed latents bloating the gate); companions (without_d, starve, flexible-ridge)
  bounded + env-gated (no-d geometry is pathologically stiff = itself evidence the d is needed); jitted
  single-sample predictor for fast coverage.
</content>

## ===== STAGE 3 (structure-aware fix) — 2026-06-04 =====
Role: INFERENCE runner, BLIND, continuing vs codex_truth/dataset/ (re-published with the CANONICAL netCG
contract). MUST NOT open sealed_truth/code/report. Build the three coupled fixes the blind failure pointed
to; report convergence + calibration honestly either way. Code: blind3_model.py, blind3_infer.py,
blind3_qoi.py, blind3_figs.py, blind3_gridinv.py. Replay in commands.md.

### D25 (2026-06-04) Adopt the CANONICAL netCG contract (FBS impedance sharing) — fixes the ~2x def bias
- netcg_quantity_contract.md is master-owned and SUPERSEDES my earlier QOI. netCG=F_iface/m_load, with
  F_iface from DYNAMIC FBS coupling: a_iface=F/(M_S+M_L); F_iface=M_L*a_iface; netCG=[M_L/(M_S+M_L)]F/m_load.
  FORBIDDEN: rigid constant mass-ratio; drive-point accelerance F/M_zz (what my blind run used -> ~2x of
  the 4.86x bias was THIS definitional drift, per review.md). My model gives M_S (dome) and M_L (load)
  separately, so the FBS coupling is internal + differentiable. Verified f->0 limit = m_load/(m_src+m_load)
  = 0.282 numerically (contract sanity). m_source(z)~433, m_load=170 (matches review's truth M_source~430).

### D26 (2026-06-04) Fix #1 = ASYMMETRIC per-strut forward model (represents x!=y, rx!=ry)
- Replaced the single equal-strut k with 6 PER-STRUT axial stiffnesses via the existing hexapod geometry
  (tray_hexapod.assemble), vectorized in JAX (batched complex solve over all freqs). Verified per-strut
  variation SPLITS the degenerate pairs: symmetric 47.18/47.18 & 136.56/136.56 -> 44.17/47.75 & 130.86/
  144.29 at 25% azimuthal variation. This is the mechanism the data needs (x:51/87, y:54/91; rx:56/97,
  ry:67/99). M_pub = M_S(dome rigid + axial bounce on z) + M_L(load on 6 struts); apparent masses ADD at
  the shared driven interface DOF. Rigid masses read off the measured low-f asymptote (standard practice).

### D27 (2026-06-04) Fix #2 = STRUCTURE/PROPERTY-BASED discrepancy in PARAMETER space (the novel piece, D12)
- Discrepancy = per-strut log-stiffness field d_j with a FEATURE-SPACE (azimuth) covariance: same element-
  type -> moderate baseline corr (0.30); azimuthal proximity -> high corr (Gaussian in angular distance,
  ell=70 deg). k_j = k_pop*exp(d0_j), d0 zero-meaned so k_pop (calibration mean) and d (structured shape)
  are separated. This carries the AZIMUTHAL (spatial) error a frequency-only kernel could not, applied in
  parameter space and propagated through the model. sigma_d is LEARNED (HalfNormal(0.20) informative, NOT
  a hard cap; rationale: observed splits ~15-30% -> d~0.15-0.35). Headline test: does it resolve the
  sigma_d<->sigma_e ridge / restore convergence and stop sigma_e inflation?

### D28 (2026-06-04) Fix #3 = COMPLEX (real+imag) likelihood; magnitude-relative noise with a floor
- Likelihood fits real AND imag apparent mass (all 6 diagonal DOF) so phase/antiresonance constrain the
  fit. Noise sd = sigma_e * scale(DOF,freq), scale = build-avg local |AM| floored at 0.3x the per-DOF band
  median (so antiresonance notches don't pathologically dominate the relative-complex likelihood, while
  phase still counts). sigma_e free (HalfNormal(0.5)); we EXPECT inflation and report it.

### D29 (2026-06-04) Decisive pre-run probe: coarse model has a sigma_e FLOOR ~1.9 (missing modes)
- Best achievable fit (Nelder-Mead over k_pop, f_dome, full per-strut d) on band-averaged complex data has
  rms FRACTIONAL residual ~1.94 (z-DOF 3.7). The data has MORE resonances per DOF than the model produces
  (z: 62/77/120; model: mount + bounce only). So sigma_e inflation is largely UNAVOIDABLE and dominated by
  MISSING HIGHER MODES, not the azimuthal split. Honest nuance: the structure-based discrepancy fixes the
  error it is structured for (x!=y/rx!=ry splits) but a DIFFERENT model-form error (missing modes) remains.
  Inference band restricted to 35-160 Hz (first mount+bounce cluster, carries QOI energy); higher data
  peaks (>160) are a documented representational gap.

### D30 (2026-06-04) Identifiability guards (informative priors, justified — NOT caps) + runtime
- log_k_pop ~ N(log 1.816e7, 0.15) [data mount peaks clearly 50-90 Hz -> guards the degenerate soft-strut
  mode where modes leave the band]; f_dome ~ TN(93.5,8) [design bounce anchor]; sigma_build ~ HN(0.05);
  sigma_d ~ HN(0.20); sigma_e ~ HN(0.5). NUTS init at the nominal best-fit (good warmup, does not bias the
  posterior). Vectorized chains (vmap, 4 chains) + batched complex solve for tractability; max_tree_depth 9.
  Companions in one run: WITHOUT-d (sigma_d=0), STARVE-DATA (1 build, 40-100 Hz); plus blind3_gridinv.py
  (grid-invariance / over-counting) and effective-vs-nominal sample count. Held-out = builds 6,7 + band
  95-115 Hz, coverage read WITH log-width.
