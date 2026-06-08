Fem spec v2 · MDCopyHexapod Modal Test Rig — FEM Specification (Rev 2)
Status of this revision: updates the prior spec in response to FEM review. The
hardware/geometry detail is unchanged; the modeling abstraction is substantially
revised. Two review items drove the changes: joint compliance/damping must be
first-class inferred parameters (was under-weighted), and the boundary condition is
a compliant free-free source plate, not a rigid ground. Decisions made by the team
are called out inline as [DECISION].

================================================================================
PHASE 1 (ACTIVE TASK) — NORMAL MODES, MODE SHAPES, VISUAL GEOMETRY ONLY
================================================================================
Lead decision (2026-06-08): the first FEM task is a basic, UNDAMPED normal-modes
model. Build the geometry, solve the real eigenvalue problem, visualize mode shapes.

DEFERRED to later phases — DO NOT implement now: damping / structural loss factor
(§3, §8), complex/frequency-domain data, force-limiting coupling and the free-free
source plate (§2), tray-side base-compliance confounding/identifiability (§4),
two-stage lumped→split modeling (§5), and all Bayesian/NUTS/differentiability work
(§1). Those remain the eventual goal; they are simply not Phase 1.

Phase-1 configuration (deliberately simpler than the coupled run in §2):
- BC: TRAY-ON-STRUTS, FIXED BASE (strut base ends grounded). This is the labeled
  "load-substructure, fixed-base" stage from §2 — NOT the coupled force-limiting
  test. The source plate is not modeled in Phase 1.
- Joints: RIGID for now, but placed as EXPLICIT joint nodes (a stiff CBUSH or rigid
  link at each strut end) so adding finite compliance/loss later (§3) is a parameter
  change, not a remodel.
- Tray: shell/plate elements (6061-T6, 12.7 mm) to show both the rigid-body-on-struts
  modes and the tray's own ~468 Hz flex modes; rigid body + lumped mass acceptable if
  only the low modes are wanted.
- Struts (×6): beam (preferred — confirms the ~370 Hz self-mode is out of band) or bar,
  with spherical end releases (3 rotations released) → two-force members.
- Geometry: true 120° hexapod, struts 30° off horizontal (§6 + coordinate table in the
  runner prompt).
- Solve: real eigenvalue / normal modes (e.g., Nastran SOL 103). No forcing, no damping.

Phase-1 validation benchmark (analytical 6-DOF rigid-tray-on-6-axial-struts, fixed
base, rigid joints — the FEM's lowest 6 modes should match):
| joint stiffness                         | tray mass | lowest 6 modes (Hz)       |
|-----------------------------------------|-----------|---------------------------|
| rigid (k≈5.5 MN/m = tube EA, UPPER bnd) | 3.1 kg    | 73, 73, 155, 260, 387, 387|
| rigid (k≈5.5 MN/m)                      | 5.0 kg    | 58, 58, 122, 204, 305, 305|
Modes come in DEGENERATE PAIRS (73/73, 387/387) — that pairing is the 120°-symmetry
check; no pairs ⇒ asymmetric geometry. Tray flex modes appear separately near ~468 Hz.

HONEST CAVEAT: absolute low-mode frequencies are PROVISIONAL — a rigid-joint upper
bound that will drop once joint compliance is added (a soft k≈1 MN/m joint pulls the
lowest pair to ~31 Hz). Mode SHAPES and the geometry are the robust Phase-1 products.

Phase-1 deliverables: (1) undeformed mesh render; (2) first ~10 natural frequencies +
plotted/animated mode shapes; (3) match to the benchmark (incl. degenerate pairs);
built in THREE tools (Femap/Nastran deck, TensorMesh continuum, JAX) and compared.
Runner prompt: docs/lab/fem_phase1_runner_prompt.md.
================================================================================

================================================================================
PHASE 1 — AGENT ASSIGNMENT AND REVIEW TOPOLOGY  (lead, 2026-06-08)
================================================================================
[DECISION RESOLVED 2026-06-08] FOUR tools: three agent-SOLVED (JAX, TensorMesh,
CalculiX) plus one Femap/Nastran DECK the human runs and visualizes. EACH of the three
builder agents builds ALL FOUR -> a 3-agent x 4-tool matrix (12 builds). Chosen over
deploying 12 single-cell agents: identical comparison matrix, far less human launch/
handoff overhead for a file-mediated POC. Reserve the 12-agent fan-out only if context
bloat degrades an agent's later builds, or a strict per-cell independence claim is wanted.
No agent auto-runs in the master repo; each works only in runs/fem_phase1/<agent>/<tool>/.

Builder agents: Opus (Claude Code), GPT (Codex), Composer (Cursor). Each produces all four:
- CalculiX (ccx)        : .inp; run `ccx` *FREQUENCY; parse .dat/.frd -> first ~10 modes. SOLVED.
- TensorMesh (discretize): assemble M,K; scipy.sparse.linalg.eigsh. SOLVED.
- JAX                   : hand-assembled K,M; dense eigh (future differentiable forward
                          model; eigensolve ONLY this phase). SOLVED.
- Femap/Nastran DECK    : ready-to-run .bdf (SOL 103, EIGRL ~10) + RUN_IN_FEMAP.md. The
                          HUMAN solves + visualizes in Femap. The agent does NOT solve it
                          and must not invent solved numbers.

INTEGRITY RULE (makes the comparison valid). Identical INPUTS across tools are required
and good (same node table, materials, masses, BCs from the shared spec). But each software
build must be an INDEPENDENT re-derivation: do NOT port one tool's assembled K/M, eigen-
results, or frequency table into another tool, and do NOT tune one tool to match another or
to match another agent. Cross-software/cross-agent agreement is only meaningful if each
engine is exercised independently. The reviewer verifies this.

Support agents (applied after the three builds land):
- REVIEWER (Opus; integrity + technical + gates). Recompute the first ~10 frequencies
  from each saved artifact (do not trust the reported table); build the cross-tool
  frequency table and the mode-shape MAC matrix; check: units/coordinate frame stated;
  degenerate pairs present (symmetry); benchmark %-diff honest and >5% flagged;
  rigid-joint frequencies labeled PROVISIONAL UPPER BOUND; element type + mesh density +
  a convergence/refinement check documented (Discretization Resolution gate); frequency
  axis log and no dB on any FRF-style plot, and any "apparent mass" pinned to the
  numerator/denominator/coordinate/BC contract (see apparent-mass-convention-postmortem.md
  and log-frequency-plot-gp-postmortem.md); each build is an INDEPENDENT re-derivation
  (no porting of K/M, eigen-results, or tables between tools or between agents) while
  sharing identical spec inputs; method summary present. Assemble the full 3-agent x
  4-tool matrix. Output review.md + checks.json (PASS/FAIL per gate) under
  artifacts/reports/fem_phase1_review_<date>/.
- PROJECT FRAMING agent (Opus). Confirm this Phase-1 FEM serves the real objective
  (a trustworthy dynamic StatFEM twin + interface-load QOI), restate the engineering
  decision it supports, confirm the PRIORITY deliverables are surfaced, and flag scope
  drift in either direction: adding damping/complex data/force-limiting/NUTS now (that is
  later-phase, explicitly out of scope), OR a build so reduced it cannot show the modes
  that drive the QOI. State what would make Phase 1 the wrong question. Output framing.md.

Comparison and adjudication (master assembles; each builder enables it):
- Oracle = the analytical 6-DOF rigid-tray-on-6-axial-struts benchmark (table above) plus
  the ~468 Hz tray-flex and ~370 Hz strut-self-mode anchors. Agreement is judged against
  the oracle, NOT by majority vote among agents/tools.
- The 3-agent x 4-tool matrix gives TWO comparison axes:
  - CROSS-SOFTWARE (per agent, across JAX/TensorMesh/CalculiX/Femap): physics +
    discretization verification (do the engines agree on identical inputs?).
  - CROSS-AGENT (per tool, across Opus/GPT/Composer): agent-implementation reproducibility
    (do three independent implementations in the SAME engine agree?).
- Products: (1) the 3x4 frequency table (first ~10 modes) + analytical oracle + the human's
  solved Femap result when available, %-diff per mode; (2) MAC matrices for mode-shape
  agreement (diagonal > 0.9 for matched modes), both axes; (3) a short "where they disagree
  and why" note (mesh, element theory, lumped vs shell tray, joint-node idealization,
  agent transcription differences). Disagreements are explained physically, not hidden.
- Honesty: provisional-upper-bound labeling kept; runtime.json per build; no result claimed
  without the table + figures actually produced.
================================================================================

1. Purpose and what the model must deliver
This rig exists to characterize joint/interface compliance and damping in a
coupled, force-limiting configuration, and to feed a Bayesian (NUTS) update that
infers those parameters. The model must therefore:

Produce the measured fundamental from finite interface stiffness, not from
tube EA alone (an ideal spherical joint is translationally rigid and predicts an
upper-bound fundamental with no mechanism to match data).
Carry a damping mechanism (structural loss factor) at the interface.
Keep the forward model parametric and differentiable so it can serve a NUTS update.

A model with rigid spherical joints and no loss has nothing for the update to learn;
that is explicitly out of scope as a final model.

2. Boundary condition / configuration  [DECISION: coupled force-limiting]
This run is the coupled force-limiting test. The source is a compliant,
free-free steel plate; the tray is coupled to it through the six struts. The
free-free plate's apparent-mass notch is the force-limiting mechanism.

The steel source plate is modeled free-free (no grounded DOF). Nothing in this
configuration is "grounded to a frame"; both ends of the strut set are structures.
The earlier spec language "bracket bases grounded to the frame" is withdrawn.
The scoped steel-plate work applies to this coupled configuration.

(If a load-substructure/joint-only characterization is run later, that is a separate,
explicitly-labeled rigid-ground stage. It is not this run.)

3. Joint model — co-located spring-damper  [primary measurand]
Each strut-to-bracket connection is a spherical joint (3 rotational DOF released,
moment-free) co-located with a CBUSH that carries finite stiffness and loss. The
CBUSH is a first-class, parametric, inferred element — not an optional refinement.
Per joint:

Finite axial and radial stiffness (k_axial, k_radial), parametric.
Structural loss factor η at the joint, stated in the frequency domain
(natural for a loss-factor representation), parametric.
Rotational DOF released (the spherical rod-end provides 3R freedom; the ball is the
rotation center).
Keep all CBUSH parameters differentiable w.r.t. the QOIs for the NUTS update.

This is the one place the model deliberately diverges from "rigid pin": spherical
release plus a co-located compliant/lossy element.

4. Tray-side base compliance  [DECISION: model it, do not assert rigid]
The 3.18 mm (0.125") base plate is not treated as rigid. With strut load applied
~16 mm up at the pin, the base bends/peels, adding a series compliance on the tray
side that sits in series with the joint CBUSH. Asserting rigidity would force that
real compliance onto the joint parameters and bias the inference.
Modeling approach:

Represent the base with shell elements capturing plate bending, with the
16 mm pin height as an RBE2 offset so the moment arm that drives base bending
is explicit.
Keep the base stiffness parametric.

Identifiability plan (required, not optional):
The base compliance and joint compliance are in series and partially confounded — many
(k_base, k_joint) pairs reproduce the same fundamental. To keep the joint parameters
identifiable:

Independently characterize the base sub-assembly before/separately from the
coupled test — static load–deflection or a single-bracket FRF with a known load at
the pin — to establish a tight prior on base stiffness. This is the single most
effective step for freeing the joint estimate.
Use that prior in the coupled update so the inference is "base well-constrained,
infer joint," rather than two free series springs.
Monitor the posterior k_base–k_joint correlation as the diagnostic for residual
confounding. Strong anti-correlation indicates the independent characterization is
needed / insufficient.


5. Two-stage modeling plan  [DECISION]
Stage 1 — lumped shakedown model (in-house, first):
Each strut = beam; a single CBUSH at the strut end lumps total tray-side interface
(base + joint) to a tray point. Purpose: stand up the forward model, match the
fundamental, exercise the NUTS pipeline.

Scope honestly as a total-interface / pipeline-shakedown model. It estimates the
sum of base and joint compliance and does not separate the joint — it does not,
by itself, close the joint-characterization objective.
Even when lumped: parameterize the CBUSH as stiffness + structural loss factor per
DOF (axial, radial, and the bending DOF excited by the pin offset), and retain
the RBE2 pin-height offset. This makes the lumped posterior a usable prior on the
total and makes the transition to Stage 2 continuous (not a restart).

Stage 2 — split base + joint model (modeling engineer, production):
Explicit shell base (§4) plus joint CBUSH (§3), with the independent base
characterization providing the prior. This is the model that answers the joint question
and closes the review items.

6. Strut layout  [DECISION: true 120°, rotated for access]
True 120° symmetric arrangement — three bipods (strut pairs) at 90° / 210° / 330°
in plan — for symmetric, well-conditioned, cleanly-separated modal data. Rotate the whole
120° pattern to free whichever edge is wanted for access; do not snap pairs to the
square's edges (three-of-four edges = 90/90/180°, which is asymmetric and splits modal
behavior). True 120° also matches the ~120°-symmetric reference hardware better than an
edge-aligned scheme.

Elevation above tray plane: 30° target, 25° hard floor. Below ~25°, out-of-plane
stiffness and conditioning degrade sharply.
V-splay per pair: included angle 40–50° (half-angle 20–25°); ~38.7° computed
earlier is consistent. Splay is what gives each pair its rotational constraint.
Geometry check (196 mm struts, 300 mm tray, ~30° elevation): horizontal reach
≈ 170 mm, vertical rise ≈ 98 mm per strut; tray floats ~100 mm off the source plate;
anchor footprint ≈ 640 mm across. Confirm the source plate can provide anchor points
at those locations.
Expected modal character: shallow elevation makes vertical (out-of-plane) the most
compliant direction; lowest modes are vertical bounce + rocking. Acceptable for a soft
suspension; if suspension modes creep into the band of interest, steepen toward 40°
(cost: package height).


7. Components (dimensions unchanged from Rev 1)
Clevis bracket (×12): double-shear fork, 6061-T6 throughout
(E ≈ 68.9 GPa, ν ≈ 0.33, ρ ≈ 2700 kg/m³, yield ≈ 276 MPa). Three-piece: two ear plates

one base plate, tab-and-slot joints bonded with epoxy (structural adhesive, no HAZ
softening — model bond as compliant/bonded interface if joint fidelity matters).


Ear plates (×2): 6.35 mm (0.250") thick, 32 mm wide × 26 mm tall above base; two
bottom tabs (10 mm × 3.18 mm); pin hole Ø5.2 mm, 16 mm above base top (this is the
RBE2 offset).
Base plate (×1): 3.18 mm (0.125") thick, 72 × 34 mm; four slots (6.65 × 10.30 mm);
two Ø6.5 mm holes at 50 mm spacing. Modeled per §4 (shell, not rigid).
Jaw: 13.0 mm inside gap; rod-end eye (~9.5 mm, confirm by caliper) centered with
rigid metal spacers/shims (~1.75 mm/side nominal — build from on-hand shims, e.g.
1.5 mm spacer ± thin washer; adjust nominal to available parts). Spacers modeled rigid.

Pin: M5 × 30 mm SHCS, 304 SS 18-8 (E ≈ 193 GPa, yield ≈ 210 MPa), fully threaded,
double shear, M5 nylon-insert locknut. Fully-threaded-in-bore is acceptable at modal
loads; a smooth-shank shoulder bolt would pivot more repeatably but is not required.
Struts (×6): delta-printer Al push rods, L196-D8-M3 — 196 mm eye-to-eye, 8 mm tube OD,
male M3-stud spherical rod-end each end. Bar element is fine for the axial QOI; use
beam elements if confirming the ~370 Hz strut self-mode is out of band. The "M3" names
the rod-end stud thread, not the ball bore (~5 mm → M5 pin).
Tray (suspended mass): Thorlabs MB3030/M, solid aluminum (confirmed — resolve the
solid-vs-sandwich caveat to solid plate), 300 × 300 × 12.7 mm, ~3.1 kg bare + payload
(confirm total; ~3–5 kg). M6×1.0 tapped holes, 25 mm grid, 12.5 mm edge offset, 12×12.
Tray's own modes ~468 Hz — acts rigid in the operating band; solid-vs-sandwich barely
affects in-band results.
Tray-side mount: 2× M6×12 SHCS (304 SS) per base at 50 mm spacing, washers under heads,
Loctite 243. (Retained because base is modeled, not thickened — see §4/§5.)

8. Minor modeling notes

Damping: structural loss factor η at the joint, frequency-domain. Keep forward
model differentiable for NUTS.
Strut self-mode: ~370 Hz (beam check) — verify out of band.
Pin-bore contact: fully-threaded pin on spherical bore is a minor nonlinear/contact
source; not modeled in the linear forward model.
RBE2 pin offset (16 mm): present in both Stage 1 and Stage 2 models.


9. Open items requiring measurement / confirmation

Rod-end eye width (sets spacer stack) and ball bore (confirms M5) — caliper on arrival.
Total suspended mass including payload.
Independent base sub-assembly compliance (per §4 identifiability plan).
Source-plate anchor locations vs the ~640 mm footprint (§6).