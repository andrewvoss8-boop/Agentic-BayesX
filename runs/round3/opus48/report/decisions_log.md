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

### D13 (2026-06-04) Open gap to close next
- The netCG/interface-PSD QOI predictions propagate only k_j (epistemic) + aleatory (build+forcing); they
  do NOT yet propagate the learned discrepancy d into the QOI. A complete twin predicts the QOI from
  corrected apparent mass = BU(k_j)+d (with d uncertainty), incl. honest band-growth outside the measured
  band. Flagged to implement (recommended next priority).
</content>
