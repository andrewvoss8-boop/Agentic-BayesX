# Task Card — Round 3: MDOF source/load + single-interface coupling + netCG QOI

Date: 2026-06-03. Problem-specific layer; problem-class-general rules live in AGENTS.md/CLAUDE.md.
The ONLY structural change from round 2 is SDOF -> MDOF for each component (single interface retained).
Decision/cost modeling is OUT this round. Sampler stays differentiable + NUTS this round (gradient-free
TMCMC/ABC comparison is a deliberate FUTURE round, not part of this one).

## Step 0 — Priority clarification + decisions log (first)
Write `report/priority_deliverables.md`: restate the priority deliverables (below) and acceptance tests
in your own words; flag any ambiguity and your interpretation before building.
Also start `decisions_log.md` (append-only) in your workspace: log every human clarification and
non-obvious choice with a UTC timestamp + rationale, written before you continue (never left only in
chat). After any context compaction, re-read the task card, `priority_deliverables.md`, and
`decisions_log.md` before acting — only your auto-loaded root rules file survives a compaction.

## Workspace (instruction-only isolation)
Your ENTIRE workspace is `runs/round3/<tool>/`. Put everything you create there:
`code/`, `tests/`, `report/` (packet.md, figures/, mesh/, *.json), `report/packet.pptx`,
`runtime.json`, `files_changed.md`, `priority_deliverables.md`, `.venv*/` (gitignored).
Read shared inputs READ-ONLY (the setup dataset under
`artifacts/reports/sequential_vibe_modal_flight_20260602/`, `src/`, the immutable checkers for shasum,
and the validated spike baseline `runs/round3/spike/`). Write NOTHING outside your workspace
(do not touch notes/, AGENTS.md, CLAUDE.md, other runners' folders, or prior rounds).

## MDOF component models (the core of round 3)
Start from the validated spike beam baseline in `runs/round3/spike/` — do NOT re-derive FEM from
scratch. Extend each component to a multi-mode model. DEFAULT to the differentiable JAX path
(NUTS-compatible); use TensorMesh P2 continuum ONLY if continuum geometry is needed (then use
E/rho-factoring to keep material gradients + sparse eigsh). State which path and why.

### Anchoring (HARD constraint — keeps staged data consistent across rounds)
Calibrate each component so its FIRST (interface-relevant) mode matches the prior-round structural
TRUTH (priors were centered dome 110 / tray 75 Hz, but the data was generated at the truth below;
anchor to the truth — confirm from artifacts/reports/sequential_vibe_modal_flight_20260602/ and
round-2 results.json):
- Dome (source, m1): mode 1 = 93.50 Hz, zeta_1 ~ 0.0225.
- Tray (load, m2):   mode 1 = 86.25 Hz, zeta_1 ~ 0.0195.
Higher modes follow from the MDOF geometry; report the first ~5 modes of each component.
HONESTY: a realistic large pressurized dome will not naturally land mode 1 at 93.50 Hz. Treat
thickness/pressure/mount-location as tuning knobs to hit the anchor, and STATE which physical mode the
93.50 Hz corresponds to (likely a local mount-region / first interface-relevant resonance, not the
global breathing mode). Do not pretend a full dome lands there by itself.

### Tray (load) physical model
- Isogrid aluminum panel carrying ~300 lbm = 136 kg of avionics (distributed over the isogrid OR
  lumped — state which and why). netCG load mass = tray total (panel + 136 kg).
- Minimally constrained on STRUTS to clevises (rod-end / pin-jointed struts; statically-determinate
  style mount), NO mechanical isolators (hard strut mount). Strut stiffness + 136 kg set the
  fundamental — tune strut stiffness so tray mode 1 = 86.25 Hz.
- SOFTEST SPRING + MOST DAMPING AT THE JOINTS: the strut-end interfaces (strut-to-tray and
  strut-to-dome clevis / rod-end joints) are likely the softest springs in the whole system and the
  dominant damping source (pinned/bolted joints govern both compliance and loss). Model the joint
  compliance and joint damping there (e.g., complex/structural-damping interface stiffness or a
  dashpot at the joint), so the tray fundamental (86.25 Hz) AND its damping (zeta_1 ~ 0.0195) are set
  primarily by these joints rather than by the panel or dome material. State the approach.
- Start the tray fundamental at 86.25 Hz. If hitting it forces a physically UNREALISTIC strut/joint
  stiffness, do NOT silently fudge — flag it, report the implied stiffness, and propose the iteration
  (the human expects to iterate the anchor if needed).
- See attached assembly/strut images (black isogrid avionics tray on clevis-mounted struts).

### Dome (source) physical model
- Aluminum, spin-formed (Falcon-9-style). Material: Al 2219 or Al-Li 2198 (state choice; e.g. E~70-73
  GPa, rho~2700-2840 kg/m^3, nu~0.33).
- Geometry ballpark: diameter ~5.5 m (R ~ 2.75 m, 18 ft stage); spun-formed 2:1 ELLIPSOIDAL dome ->
  cap height ~ R/2 ~ 1.4 m (hemispherical ~2.75 m if justified).
- Tank PRESSURIZED -> INCLUDE PRESSURE / STRESS STIFFENING (geometric stiffness from internal-pressure
  membrane prestress) in the modal solve. Operating ullage ~3-6 bar (~45-90 psi; F9 ~3-4 bar). State
  the pressure used and SHOW its effect on the modes (pressure stiffening raises fn). Tune
  geometry/pressure/thickness so dome mode 1 = 93.50 Hz.

### Single interface (unchanged)
Couple source and load at ONE interface DOF (the strut-to-dome attachment as a single equivalent
interface) via frequency-based substructuring / impedance coupling of the two components' interface
FRFs. Physically there are multiple struts; collapse to one equivalent interface DOF for now.

### Key transfer functions to produce (per component, at the interface DOF), VALIDATED
- source free-interface apparent mass / accelerance;
- load interface apparent mass;
- coupled-system interface force under flight forcing.

## QOI = netCG (define precisely before plotting — quantity-contract gate)
netCG = net CG acceleration of the load = F_interface(omega) / m_load, m_load = tray total (~136 kg +
panel). PSD_{a_cg}(f) = PSD_{F_interface}(f) / m_load^2 ; 3*GRMS_netCG = 3*sqrt(integral PSD_{a_cg} df).
State numerator (net interface force, N), denominator (load mass, kg), excitation (flight force at the
source), BC (single-interface coupling), units, and limiting behavior (low-freq -> rigid-body
a_cg = F/m_total; component resonances appear in F_interface; apparent-mass antiresonance). Expose
netCG (and any other requested QOI) as NUMERIC 95% AND 99% intervals, not figure-only.

## FEM visualization / export (REQUIRED — human must be able to inspect any AI-generated mesh)
In `report/mesh/`: (1) nodes.csv (id,x,y,z) + elements.csv (id,type,connectivity) human-readable card;
(2) model.bdf NASTRAN bulk data (GRID + element cards) for Femap; (3) model.vtu and/or .obj/.stl for
ParaView/Blender — use `meshio` for (2)+(3). In `report/figures/`: rendered undeformed mesh + first
~3-5 mode shapes (pyvista/matplotlib). State units and coordinate frame.

## Carried-over round-3 requirements (from rounds 1-2 reviews)
- Likelihood: WHOLE-PSD/FRF is the default for the GIF/decision; peak-feature is a labeled comparison only.
- Convergence (source-backed bar): rank-split R-hat < 1.01; bulk AND tail ESS >= 100 x chains (>=400 at
  4 chains); 0 divergences ideal (>2% fail); >=4 chains; non-centered hierarchical latents; report over
  ALL sampled variables incl raw latents; never report "pass"/"NUTS active" if not converged.
- Build-to-build variability now includes PER-STRUCTURE fn and damping scatter: +-5% at 3-sigma for each
  of dome fn, tray fn, dome zeta, tray zeta (sigma ~1.67%; lognormal), on top of the PSD-level build effect.
- Forcing: Matern flight GP, fixed 3 dB flight-to-flight; -6 dB flight-mean offset is a PRE-DATA
  CONSERVATIVE DESIGN ENVELOPE (6 dB PSD = 4x PSD = 2x GRMS), NOT a GEVS qual margin (+3 dB) and NOT a
  +6 dB/oct slope. Run a sensitivity sweep on the -6 dB offset and the Matern length-scale.
- HEADLINE objective: quantify the narrow-band exceedance risk — show that a large overall (scalar)
  margin can coexist with a narrow-band 99% exceedance at a coupled resonance (the 7004 / force-limiting
  insight). Standardize ONE envelope band definition (central 99%: q0.5-q99.5, AND report the one-sided
  99%-hi exceedance fraction per flight) before quoting any spec-covers-flight verdict.
- Plots: every figure/panel has a legend; log-frequency axes for FRF/PSD; show the drive-point
  ANTIRESONANCE interlacing; no clipped peaks; resolution rationale + sensitivity check (no hard-coded
  lines-per-band).
- Runtime: time the WHOLE producing run start->end in one wall timer (report script_wall_s) AND the
  per-stage active_compute_s; run the FULL pipeline (no post-hoc replay that skips the expensive stage).

## Validation (references gate)
Mode 1 within ~1% of the anchor; report first ~5 modes; drive-point antiresonance interlacing shown;
benchmark the FEM against an analytical case (cantilever betaL or lumped MDOF) before acceptance; the
coupled interface PSD must show the expected antiresonance (cross-runner shape agreement is expected on
the shared synthetic truth).

## Deliverables / report contract (in report/)
packet.md (method/likelihood summary up top), packet.pptx (review layer; embed mesh + mode shapes +
final PSD-vs-spec PNG + key GIF frames), the interface-PSD-vs-spec evolution GIF, forcing overlay,
netCG-vs-vibe-reference, mesh/ exports, nuts_diagnostics.(md|json), resolution_sensitivity, results.json
(numeric QOI intervals), assumptions_ledger, quantity_contracts, known_failures, review_request,
manifest.json, commands.md, files_changed.md, runtime.json, priority_deliverables.md, decisions_log.md, checks.json.

## Not allowed
Editing immutable checkers (verify with shasum -a 256 -c harness/checkers/manifest.sha256); copying
another runner's or reference assets and presenting them as your own (declare any copy); claiming
converged/NUTS-active without it; writing outside your workspace.
