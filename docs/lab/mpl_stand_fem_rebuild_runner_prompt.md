# Runner Prompt — MPL Test Stand: Parametric FEM Rebuild + Mounted-Mass QOI + Modes + Mode-Shape GIFs

You are a runner agent for Agentic BayesX (this task runs on FABLE — Andrew's explicit 2026-06-11 override
of the "FEM tasks use Opus runners" default; log this in your decisions_log as a human decision). Before doing ANYTHING: read `AGENTS.md` (root, canonical
rules/gates — every gate applies), `docs/agents/how_to_run.md`, and this card. Create your workspace at
`artifacts/reports/mpl_stand_fem_rebuild_<YYYYMMDD>/` with `priority_deliverables.md`, `decisions_log.md`,
an assumptions ledger, `run_all.sh` (one-command replay), `check.py` (green/yellow/red), `runtime.json`,
`manifest.json`, and `packet.md`. Log every non-obvious decision in `decisions_log.md` BEFORE acting on it.

## Context (read, don't re-derive)
- Physical structure: tall blue welded-steel A-frame test stand ("MPL test stand"), front face = thin
  sheet-metal "shield" panel, backside = pneumatic valve panel + cylinders + electronics box (photos:
  `MPL test stand/FEM/test stand photos jun 11 26/IMG_9842..9846.jpeg` — look at them).
- Purpose of this rebuild: this model is the COARSE PRIOR MODEL for a Bayesian robust-twin demo. A scrappy
  modal test (1 single-axis accel, wrench taps, speaker acoustics; matrix in
  `MPL test stand/FEM/test_matrix_20260611.md`) will calibrate a handful of parameters with HIGH assumed
  model discrepancy. The model must therefore be (a) PARAMETRIC in the right knobs, (b) fast to reassemble,
  (c) honest about its coarseness. "Upgrade the FEM but not too well" is the design intent — do NOT refine
  the mesh or chase fidelity; make it parametric and correct.
- Posterior sampling (NUTS) is a FUTURE task, NOT this one. No sampler runs here (state this as the sampler
  decision in the packet). But the assembly must be built so NUTS can use it later — see Deliverable 2.

## Source model
`MPL test stand/FEM/Test Stand FEA.dat` — Femap 2412 / Simcenter Nastran, SOL SESTATIC (linear STATIC,
10,000 lbf thrust strength case; the FORCE/LOAD cards are irrelevant to this task — drop them).
- PARSING CAVEATS: mixed CRLF/CR line endings (normalize first); small-field fixed 8-column format;
  `+` continuation cards (PBEAM has 3-line cards with `YESA` continuation); Nastran shorthand floats
  like `1.-34.7222` field-splitting and `7.324-4` (= 7.324e-4) — write a real fixed-width field parser,
  do not split on whitespace.
- Contents: 1415 GRID; 1288 CBEAM with orientation vectors + 37 PBEAM (only 2 DISTINCT tube sections:
  A=1.353627/Is≈7.45,1.045 and A=3.899984/Is≈4.12,13.73 — group them); 72 CQUAD4 + 1 PSHELL t=0.5
  (PID 39); 70 CBUSH (PID 37, K=1e7 all 6 DOF, CID=0) + 1 PBUSH; 39 RBE2 (123456, mostly 1 dependent
  grid); MAT1 E=2.9e7, nu=0.29, rho=7.324e-4 (inch-lbf-second units: psi, lbf·s²/in⁴ — STATE the unit
  system everywhere; report frequencies in Hz); 4 SPC1 123456 at grids 1, 164, 692, 1212 (the feet);
  CORD2C/CORD2S defined but check whether any GRID actually references them (sample GRIDs show CP=0);
  PARAM K6ROT=100 (shell drilling DOF — replicate or justify your drilling-DOF treatment).

## Deliverables (priority order)
1. **Faithful parse + assembly (Python).** Parse the deck into structured arrays. Assemble global K and M
   (consistent or lumped mass — state which) with: Euler/Timoshenko CBEAM (state shear treatment; the
   tubes are stocky in section but elements look short — justify), CQUAD4 shell (a standard flat-shell
   = membrane + bending with a drilling-DOF treatment is acceptable at this coarseness — document it),
   CBUSH 6-DOF spring, RBE2 via MPC elimination (transformation matrix), SPC1 elimination. Validate the
   ELEMENT LIBRARY against analytic single-element/textbook cases (cantilever tip deflection + first
   frequency for the beam; plate strip bending for the shell) BEFORE the full model — record these as
   checker gates.
2. **Parametric in the calibration knobs, sampler-ready.** Assembly must expose θ → (K(θ), M(θ)) with
   CHEAP reassembly, structured as per-group constant matrices so K(θ) = Σ_g s_g(θ_g)·K_g (the ShockSat
   modal-twin pattern; see `artifacts/reports/shocksat_fem_modal_twin_20260609/` for the precedent).
   Parameter groups (minimum): (a) shield panel thickness/stiffness (PSHELL 39 — the 0.5 in thickness is
   SUSPECT for sheet metal; flag it, keep 0.5 as nominal prior mean ONLY if Andrew doesn't supply the real
   gauge — ASK in the packet), (b) CBUSH joint stiffness (one group, PID 37), (c) the two beam-section
   groups (stiffness scale), (d) foot boundary: implement SPC feet as the nominal, PLUS an optional
   parametric variant with stiff grounding springs so base-flexibility can be calibrated later (state
   which is used for the nominal modes), (e) the new mounted-mass attachment stiffnesses (below). Pure
   numpy/scipy is acceptable for THIS task, but document the path to JAX (or provide a JAX twin of the
   assembly) since NUTS needs gradients later. Pin BLAS threads for dense eigensolves per AGENTS.md.
3. **Add backside mounted masses (NEW, the QOI items).** From the photos: pneumatic valve panel (multiple
   valves on an 80/20-style subframe) and an electronics box mounted on the backside, plus the white
   electrical box on the upper frame. Model: each QOI item = CONM2 (mass + rough inertia) attached through
   a CBUSH/spring to the nearest frame grids (so each has a LOCAL mode — a bare rigid CONM2 cannot carry an
   acceleration QOI distinct from the frame). Non-QOI clutter may be bare CONM2. MASSES AND LOCATIONS ARE
   NOT PROVIDED: estimate from the photos (typical Clippard valve manifold, steel enclosure boxes), put
   every estimate in the assumptions ledger with value/units/rationale/sensitivity-priority, mark them
   ANDREW-CONFIRM-REQUIRED, and make them parameters (they will be priors, not facts). Do NOT silently
   guess: the packet must list the exact questions for Andrew (each item's mass, attach location, bracket
   type).
4. **Modal solve.** SOL-103-equivalent: generalized eigensolve of the reduced (K, M), report ALL modes
   0–500 Hz (at least 30 modes). Sanity gates (checker-backed): (i) total mass vs Σ element+CONM2 mass;
   (ii) with SPCs removed, exactly 6 rigid-body modes at ~0 Hz; (iii) no negative eigenvalues; (iv) modes
   with the SUSPECT 0.5 in panel vs a thin-gauge variant (e.g. 16 ga ≈ 0.06 in) — report BOTH mode tables
   so the thickness sensitivity is visible (Sensitivity Gate, this is the #1 knob). Also report each
   mode's dominant region (panel / frame / mounted mass) via modal effective mass or strain/kinetic-energy
   fractions — this feeds the later identifiability work (Modal Identifiability Gate).
5. **Interface-point identification (small but required).** The physical test mounts a ruler (secondary
   structure, NOT modeled in this task) at two locations; find and REPORT the nearest grid(s) to each so the
   later coupling task has named interface nodes: (a) SHIELD MOUNT = middle of the shield panel at its TOP
   edge (top-center of the sticker-covered front panel); (b) BEAM MOUNT = viewed from the logo/shield side,
   the TOP-LEFT region — on the BACK wall (rear face) of that top steel beam. Identify grid IDs + coordinates,
   mark both points in the geometry/mode figures, and report the panel-vs-frame motion at each across the
   mode set (these two points are where coupled-vs-uncoupled behavior will be measured; the joint hardware
   at both = a Jorgensen F-clamp, mass to be ledgered when Andrew supplies it). If the deck's geometry makes
   "top-left/back wall" ambiguous, state your interpretation with a figure and flag it ANDREW-CONFIRM-REQUIRED.
6. **Mode-shape GIFs.** Animated GIFs (matplotlib, 3-D wireframe: beams as lines, quads as patches,
   CONM2 as markers) for at least the first 10–15 flexible modes: oscillating deformation, frequency +
   mode number + run/dataset stamp ON the figure, fixed feet marked. Plus one static small-multiples PNG
   of all mode shapes. Apply the `tufte-data-graphics` skill + `scripts/tufte_lint.py` to the plotting
   script (a saved .py, not a heredoc); run the image-legibility QA. Undeformed geometry overlay (light)
   so deformation is readable; normalize displacement scale per mode and PRINT the scale factor (these
   are shapes, not amplitudes — say so on the figure).
7. **Packet + checker.** `packet.md` with method summary up front (what was parsed, element formulations,
   unit system, what's parametric, what's estimated-pending-Andrew), the two mode tables, GIF index,
   assumptions ledger, the explicit Andrew-question list, and honest limitations (coarse mesh deliberate;
   no test data yet; no sampler; SESTATIC heritage). `check.py` green/yellow/red per AGENTS.md Result
   Status Standard; estimated masses w/o confirmation = at best YELLOW on those gates, never green.

## Hard rules (repeat of canonical gates that bite here)
- NO fabricated numbers: if a mass/location is estimated, it is labeled estimated everywhere it appears.
- NO NUTS/convergence claims — there is no sampler in this task.
- NO mesh refinement crusade — coarseness is intentional; spend effort on correctness + parametrization.
- Reference checks: beam/plate element validation vs textbook closed forms; frequencies must satisfy
  limiting behavior (panel thickness ↓ → panel modes ↓ roughly ∝ t for bending).
- Discretization gate: document the mesh as-inherited and why it's adequate for <500 Hz QOI features
  (or bound the error with one cheap h-refinement spot-check on the panel).
- If the full eigensolve or GIF rendering exceeds tool timeout, use the detached-launch protocol.
- Done = artifacts exist + check.py runs + replay works (`bash run_all.sh`), not prose.

## Out of scope (do NOT do)
Ruler/secondary modeling; coupling the test data; NUTS/sampling; OSP/FIM (next task, uses your mode set);
editing AGENTS.md/CLAUDE.md or anything outside your workspace except reading.
