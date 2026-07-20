# Decisions Log — MPL Stand Parametric FEM Rebuild (runner: FABLE, 2026-06-11)

Card: `docs/lab/mpl_stand_fem_rebuild_runner_prompt.md`. Every non-obvious decision is
logged here BEFORE acting on it.

- **D1 (human decision, 2026-06-11):** This task runs on FABLE — Andrew's explicit
  override of the 2026-06-08 "FEM tasks use Opus runners" default. Stated in the card
  and confirmed live in chat ("run it as fable. you are now fable."). Logged per card
  instruction.
- **D2 (human decision, 2026-06-11, chat):** Andrew: "Use the pictures to estimate
  properties of the box and valves. We want to make this process with a pretty coarse
  fem." → I estimate mounted-mass properties from the five photos; estimates are
  priors, labeled ESTIMATED + ANDREW-CONFIRM-REQUIRED everywhere; coarseness is
  intentional (no mesh refinement).
- **D3:** Workspace = `artifacts/reports/mpl_stand_fem_rebuild_20260611/`. Pure
  numpy/scipy for this task (allowed by card); JAX path documented in packet, not
  built, since no sampler runs here.
- **D4 (sampler decision):** NO sampler in this task (card: posterior sampling is a
  future task). The assembly is structured K(θ) = Σ_g s_g·K_g, M(θ) = Σ_g m_g·M_g with
  cheap reassembly so future NUTS can consume it. No NUTS/convergence claims anywhere.
- **D5 (photo readings, basis for estimates):** (a) shield = two thin sheet panels,
  screwed at discrete points → 0.5 in PSHELL thickness is NOT credible for the real
  panel; keep 0.5 as deck-nominal, add 16 ga (0.0598 in) variant table per card.
  (b) Backside items identified: pneumatic valve panel on 80/20 subframe (Clippard
  label, black accumulator tanks, ~10+ solenoid valves, manifolds, regulators,
  stainless tubing); white/beige steel enclosure (electronics box) on backside frame;
  white electrical box on upper frame; silver PSU-style box under the top beam.
  (c) Top beam = rectangular steel tube with thin (~1/8 in class) wall, consistent
  with the deck's two tube PBEAM sections.
- **D6:** QOI items (CONM2 + CBUSH for a local mode): valve panel, backside
  electronics box, upper white electrical box. Non-QOI clutter (bare CONM2): silver
  PSU box. Rationale: card names the first two as QOI plus the white upper box; PSU is
  incidental clutter.
- **D7 (parser):** Real fixed-width 8-column parser; normalize CRLF/CR first; handle
  `+` continuations and Nastran shorthand floats (`7.324-4` → 7.324e-4). FORCE/LOAD
  cards dropped (static thrust case irrelevant here, per card).
- **D8 (mass matrix):** LUMPED mass (row-sum / HRZ for shells, half-mass-half-inertia
  endpoint lumping for beams, CONM2 direct). Rationale: coarse prior model, lumped
  keeps M diagonal-block, cheap, and robust for the <500 Hz target; stated in packet.
- **D9 (beam theory):** Timoshenko (shear-deformable) CBEAM using the deck's own
  PBEAM shear factors (parsed: K1=0.2973119, K2=0.6236289). Rationale: elements are
  short segments of welded tube; Euler would overstiffen short elements. Validation
  vs Euler closed form done on a slender cantilever where the two theories agree.
- **D9b (card-context correction):** The card said section A has "Is≈7.45,1.045".
  Properly sliced fixed-width fields give I1=0.4508286, I2=1.045408 (and J=1.003687)
  — the "7.45" was a field mis-slice of ".4508286". The parsed values are
  self-consistent with a 1.5x2.5x~0.1875 in rect tube whose stress-recovery points
  are (±0.75, ±1.25). PARSE WINS over card prose; logged, not a blocker.
- **D10 (shell):** Flat 4-node shell = bilinear isoparametric membrane (plane stress,
  2x2 Gauss) + 12-DOF non-conforming Kirchhoff plate bending (ACM/BFS-style basis with
  exact analytic integration on a rectangle projection)
  + drilling DOF given a small artificial stiffness (PARAM K6ROT-equivalent;
  documented). Acceptable at this coarseness per card; validated on plate-strip
  bending.
- **D11 (RBE2/SPC):** RBE2 via explicit MPC transformation T (dependent DOFs
  eliminated, rigid-arm kinematics); SPC1 via row/col deletion after the T reduction.
- **D12 (feet):** Nominal = SPC1 123456 at grids 1, 164, 692, 1212 (as deck). ALSO
  built: parametric grounded-spring variant (stiff 6-DOF springs at the feet) for
  later base-flexibility calibration. Nominal modes reported from the SPC variant;
  stated in packet.
- **D13 (CORD2C/CORD2S):** Parser checks every GRID's CP/CD fields; if none reference
  CIDs 1/2 (sample shows CP=0), the cylindrical/spherical frames are dropped with a
  checker-verified count.
- **D14 (BLAS pinning):** All eigensolves run with OMP_NUM_THREADS=1
  VECLIB_MAXIMUM_THREADS=1 per AGENTS.md compute rules.
- **D15 (mounted-mass placement):** Deck has NO grids for the backside items; attach
  locations estimated from photos relative to deck geometry (frame bounding box,
  shield = front face). Each placement is an assumptions-ledger entry,
  ANDREW-CONFIRM-REQUIRED, and a parameter (attach height/offset can be moved without
  re-parsing).
- **D16 (drilling DOF):** Deck uses PARAM,K6ROT,100. I replicate the intent with a
  K6ROT-style drilling stiffness on shell normal-rotation DOFs scaled per element
  (documented in packet §element library); plus AUTOSPC-style removal of any
  残 zero-stiffness DOFs after assembly (tolerance-based), counts reported.
- **D17 (modes):** Report ALL modes 0–500 Hz and at least 30 modes (whichever is
  more). shift-invert scipy.sparse.linalg.eigsh on the reduced (K, M), sigma=0,
  k chosen adaptively; rigid-body check run with SPCs removed (free-free) expecting
  exactly 6 ~0 Hz modes.
- **D18 (deck encoding):** `Test Stand FEA.dat` is ASCII with MIXED CRLF and bare-CR
  line terminators (verified with `file`); parser splits on universal newlines after
  replacing lone CR with LF.
- **D19 (CARD-PREMISE BREAK, parse-backed):** The 72 CQUAD4 / PSHELL 39 (t=0.5 in)
  elements are NOT the sticker shield. All 91 quad grids lie in the single plane
  x=61.49, spanning 12 in (y: −30..−18) × 6.5 in (z: 15.4..21.9), and they are
  exactly the grids loaded by the 10,000 lbf FORCE set (−X). They are the THRUST
  PLATE / mounting pad. t=0.5 in is PLAUSIBLE for a thrust plate, not suspect.
  Consequence: the sticker SHIELD IS NOT IN THE DECK AT ALL, so the card's "#1 knob"
  (shield thickness via PSHELL 39) and the planned dual mode table 0.5-vs-16ga were
  premised on a misidentification. Escalated to Andrew (live chat) before building;
  see D21.
- **D20 (geometry map, parse-backed):** Z is UP (all 4 SPC feet at z=0); footprint
  X∈[−5,84] × Y∈[−48,0] in; height 50.25 in. Side-view profile: low back edge
  (z≈10 at x=−5) → 45° ramp face (plane z−x≈10.7, x −5→~22) → flat plateau z=30
  (x ~25→55) → tower (x≈55-65) carrying the TOP BEAM (x=60.25, z=49.4-50.25,
  spanning full width y 0..−48) and the thrust plate (x=61.49, normal X) → 45° front
  face (plane x+z≈83.2, 96 grids) down to the front feet at x=84. Structure symmetric
  about y=−24. CBUSH GA-GB joint gaps 0.455-2.26 in.
- **D22 (HUMAN ANSWERS, Andrew live chat 2026-06-11 — supersede estimates where given):**
  (1) F-clamp mass = 415.3 g = 0.91557 lbm = 2.3714e-3 lbf·s²/in. CONFIRMED. Ledgered
  for the LATER coupling task; the ruler/clamp are NOT modeled in this task (card
  out-of-scope rule unchanged).
  (2) Sticker shield is COMPLETELY VERTICAL, 90° to the engine thrust direction
  (thrust = −X) → shield lies in a Y-Z plane on the tall front wall (frame planes
  x≈58.7-61.5). My "easel/ramp" reading of the side profile was wrong about the
  shield's face; the ramp/plateau is the BACK support table. CONFIRMED.
  (3) Shield thickness = 1.7 mm = 0.066929 in, CONFIRMED, and the shield MUST BE IN
  THE MODEL → I add it as new coarse CQUAD4s. Material NOT stated: ASSUME STEEL
  (welded-steel stand; painted like the frame) — ANDREW-CONFIRM-REQUIRED. Note:
  steel vs aluminum changes panel frequencies very little (≈ equal E/ρ specific
  bending stiffness) but changes panel MASS ×2.9 → material arm reported in
  sensitivity.
- **D23 (dual-mode-table adaptation, replaces the card's dead premise):** Card gate
  (iv) demanded mode tables for "0.5 in panel vs 16 ga panel" — premised on PSHELL 39
  being the shield (D19: it is the thrust plate; real shield t now CONFIRMED 1.7 mm).
  Honest replacement delivering the same intent (show the #1 knob's effect): TABLE A =
  deck + shield @1.7 mm steel (nominal rebuild); TABLE B = deck WITHOUT shield
  (as-given model). Plus cheap scalar sensitivity arms: shield t ×0.5/×2 (limiting
  behavior: bending panel modes ∝ t), shield-attachment stiffness ×0.01/×100,
  aluminum-material arm. Thrust plate t=0.5 stays parametric but is no longer
  labeled suspect.
- **D24 (shield modeling):** Shield = vertical CQUAD4 mesh at the front-wall surface
  plane, t=0.066929 in, MAT1 steel (same E/nu/rho as frame), TWO pieces with a gap
  band at the thrust-plate height (photos show two panels with exposed blue frame
  between, around the engine area): upper panel (large, stickers) + lower panel.
  Exact extents estimated from photos + frame geometry; ledger entries,
  ANDREW-CONFIRM-REQUIRED. Attached to nearest front-wall frame grids by stiff
  6-DOF springs at discrete screw locations (own parametric group k_shield_att —
  now a top calibration knob). Mesh deliberately coarse (~6-8 elements across) per
  Andrew's "pretty coarse fem"; discretization gate covered by one h-refinement
  spot-check on the upper panel.
- **D25 (beam groups, parse-backed adaptation):** PBEAM PID 38 (A=3.9, I2=13.7 flat
  bar) is defined but used by ZERO CBEAMs — all 1288 beams use the single
  1.5x2.5x0.187 tube section (36 duplicate PIDs, Femap artifact). The card's "two
  beam-section groups" knob therefore collapses. Honest replacement with equal knob
  count: split beams SPATIALLY into (i) `beam_wall` = members of the front wall
  region (both nodes x∈[58,63]) incl. the top rail — the structure the test taps —
  and (ii) `beam_rest` = back table/braces/legs. Two distinct PBEAM K1/K2 pairs
  exist: (0.297,0.624) tube (used), (0.854,0.850) on unused PID 38.
- **D26 (interface-point geometry, parse-backed):** "Top steel beam" = the only
  full-width top member: the z=48.5 rail at x=60.75 spanning y=0..−48 (the corner
  posts continue 1.75 in higher as short stubs — IMG_9846's open tube end). Viewed
  from the logo (+X) side looking −X with Z up, viewer-left = −y, so TOP-LEFT region
  = y near −48. BEAM MOUNT candidate grid = nearest rail grid to ~5 in from the left
  post, on the BACK (−X) wall of the rail; exact grid + neighbors reported by
  `interface_points.py`, marked on figures, ANDREW-CONFIRM-REQUIRED.
  SHIELD MOUNT = top-center of the (new) shield mesh top edge ≈ (61.5, −24, ~50);
  the nearest frame grid on the z=48.5 rail at y≈−24 is also reported.
- **D27 (drilling bug caught by gate):** First free-free run gave 5 rigid-body
  modes, not 6 — the absolute diagonal drilling spring stored energy under rigid
  rotation about X (all shell normals along X) at frame-coupled shell nodes,
  corrupting that RBM to 2.66 Hz. Fixed by implementing the K6ROT-style RELATIVE
  penalty (normal rotation tied to the membrane in-plane rotation at the element
  center) — free-free now exactly 6 RBMs (max 0.0026 Hz vs first elastic 14.7 Hz).
  Lesson: the free-free gate caught a real formulation error; logged for
  lessons-learned.
- **D28 (validation-test bugs, not element bugs):** Initial beam-static FAIL was
  an off-by-one tip-node index in the TEST (element nodally exact once fixed);
  plate-strip FAIL was reference ambiguity (narrow strip sits between E and
  E/(1-nu^2) limits) — gate now uses nu=0 where the closed form is unambiguous.
- **D29 (figure QA fix):** side-view interface labels overlapped (mounts nearly
  coincide in x-z); per-view label offsets applied, figures regenerated, QA
  re-run PASS.
- **D30 (final status):** `bash run_all.sh` replay COMPLETE in 241 s; checker
  OVERALL YELLOW (15 green / 3 yellow / 0 red), exit 0. Yellows = estimated
  mounted-mass values, assumed shield material, beam-mount station
  interpretation — all ANDREW-CONFIRM-REQUIRED by design, never claimable green
  without his numbers. No sampler run; no convergence claims.
- **D31 (HUMAN ANSWERS round 2, Andrew live 2026-06-11):** (1) valve panel is
  BOLTED TO THE BASE OF THE STAND → it is stand-mounted INCLUDING the 80/20
  subframe + black tanks: mass re-estimated 12 → 28 lbm, CG lowered to
  (52,−24,10), attachment springs re-pointed to BASE grids via new
  `attach_near` key (k_att 1e5 lbf/in per point, bolts into base rails).
  (2) Box masses: "no idea, guess based on the photos" — photo guesses
  AUTHORIZED but remain ESTIMATED/YELLOW (card rule). (3) Shield "probably
  steel" and "welded on at a few points" → attachment springs re-labeled WELD
  SPOTS, k_t 1e5→1e6 lbf/in, k_r 1e3→1e4 in·lbf/rad (no screw compliance);
  steel kept, still yellow until "probably" is firm. (4) Clamp-station question
  re-asked in plain words with the geometry figure (red stars).
- **D32 (drilling-penalty legitimacy, answered to Andrew):** the relative
  drilling penalty is the Hughes–Brezzi (1989) variational formulation — a
  principled regularization (frame-invariant, convergence theory, preserves
  RBMs), conceptually what Nastran's K6ROT=100 in this very deck does; NOT an
  ad-hoc patch (the ad-hoc absolute spring was rejected after the 6-RBM gate
  caught it, D27). Verified exposure: penalty ×100 moves first-20 modes ≤0.32%.
  Honest limit: the drilling DOF carries no real physics — if a future task
  applies a genuine point torque about the shield normal, upgrade to an
  Allman-type membrane.
- **D33 (HUMAN ANSWERS round 3, Andrew live 2026-06-11 + new photos IMG_9849-9854):**
  (1) "PSU box" IS the electronics box — I had double-counted one object as two
  (silver fan box + phantom beige ebox at (30,−40,27)). MERGED into ONE
  electronics box. (2) It mounts ON THE SHIELD PANEL, lower than my old PSU
  placement, ON TOP OF the LabJack sticker, with exactly 3 mounting-feet bolts
  (visible in IMG_9853/9842) → modeled as CONM2 on 3 springs to the nearest
  SHIELD grids around the LabJack sticker region (upper-left quadrant of the
  upper panel; sticker row reads LabJack/Relativity/Hermeus left→right from
  the logo side, so LabJack y≈−38). This mass-loads the 1.7 mm panel — the box
  QOI is now directly coupled to shield physics. Exact bolt triangle estimated
  ±4 in, ANDREW-CONFIRM. (3) BEAM MOUNT correction: "top left beam" = the
  LEFTMOST VERTICAL post (y=−48, x=60.25), top region, NOT the top crossbeam
  → interface_points.py reworked. (4) Valve assembly sits UNDERNEATH that box,
  mounted to the FLAT BOTTOM PLATE (visible IMG_9844; plate is NOT in the deck
  → attachment springs go to the nearest base-rail grids, noted as a coarse
  stand-in). (5) The beige box on the back blue panel (IMG_9843/9844/9845)
  remains a separate item = white_box_upper. IMG_9854 = ruler-on-mill solo
  test, not stand geometry. IMG_9853 also shows the test accelerometer taped
  mid-panel below Relativity (useful later for observation-point mapping).
- **D34 (HUMAN, Andrew 2026-06-11 round 4):** electronics box mass = "between 2
  and 4 pounds" → make it a STATISTICAL PRIOR, not a point. Implemented:
  (a) nominal point (for the deterministic mode table) = 3.0 lbm (range
  midpoint, was a 10 lbm over-guess); (b) PRIOR = LogNormal with median 2.828
  (= geometric mean of 2 and 4, so the interval is symmetric in log-mass,
  natural for a positive multiplicative quantity) and sigma_ln = 0.1767 chosen
  so [2,4] lbm = the 2.5/97.5 percentiles. Recorded in NEW `src/priors.py`
  (the prior registry the future NUTS task will import) + `out/priors.json`.
  SCOPE: this task STILL runs NO sampler. I added a PRIOR-PREDICTIVE forward
  propagation only (`src/prior_predictive.py`): sample the box-mass prior →
  cheap M(theta) reassembly → mode-1 (box-on-panel) frequency distribution.
  That is a forward push of the prior, NOT a posterior/update (the "update it
  as a posterior" step = the next card, which consumes these same groups +
  the tap-test frequencies as the likelihood). Honest labeling kept:
  prior-predictive ≠ posterior; no convergence claims.
- **D35 (stale GIFs):** GIF filenames embed the mode frequency, so each replay
  (rev1/2/3/4) left a fresh set and 4 sets accumulated in gifs/. Andrew: delete
  the old ones. Fix: make_gifs.py now WIPES gifs/ before writing; stale sets
  deleted. Only the current rev-4 set remains. (Andrew confirmed the symmetric-
  looking panel modes he saw were from an OLD gif set, not a bug — the current
  shapes DO carry the off-center box mass; my symmetry diagnostic confirmed
  asymmetry grows with box mass: e.g. mode 1 X-asymmetry index 0.013@0lb ->
  0.141@3lb -> 0.66@30lb, and degenerate panel pairs split.)
- **D36 (HUMAN, Andrew round 5):** the valve panel AND electronics box are on
  the WRONG SIDE in y -- "they are on the other side" -- and the e-box "should
  be lower" in z. From IMG_9842 (front view): the white e-box sits LOW on the
  panel toward the base, not high. FIX: mirror both items about the panel
  centerline y=-24 (e-box y -38 -> -10; valve y -32 -> -16) and lower the e-box
  (CG z 41.5 -> 28; bolts z 44/44/35.5 -> 32/32/24). My y-sign convention for
  these two placements was mirrored vs reality. Beam mount (y=-48) was NOT
  flagged, so it stays. New positions marked ANDREW-CONFIRM and shown in the
  geometry figure for visual check.
- **D37 (HUMAN, Andrew round 6):** (1) white_box_upper and electronics_box
  should share the SAME y-z location (front box on the shield, back box
  directly behind it) and both sit a little HIGHER in z. → set both to
  y=-10.5, z raised 28->33 (e-box CG (58.5,-10.5,33), bolts z+5; white box CG
  (55,-10.5,33), x behind on the frame). (2) valve assembly y "a bit higher":
  interpreted as toward the boxes' side, y -16 -> -12 (flagged: 'higher' on a
  signed lateral axis is ambiguous; shown on the figure for confirmation). All
  ANDREW-CONFIRM via fig_geometry.
- **D38 (HUMAN, Andrew round 7 + new photo):** replace the single rigid-CONM2
  valve lump with a HIGHER-FIDELITY model that includes the 80/20 aluminum
  T-slot EXTRUSION FRAME. Scope note: this exceeds the card's "don't chase
  fidelity" guidance, but is justified+human-directed because valve accel is a
  QOI (QOI items earn fidelity). PLAN: model the 80/20 cage as Timoshenko-beam
  members (reuse the validated beam element) in ALUMINUM (E=1.0e7 psi, nu=0.33,
  rho=2.54e-4 lbf*s^2/in^4 for 6105-T5) with PUBLISHED T-slot section props
  (A, I, J per series); hang the 4 black accumulator tanks + valve manifolds +
  regulators as CONM2 nodes on the frame; bolt the cage to the stand at its
  feet via CBUSH. New parametric groups: K_valveframe (+M_valveframe) and the
  tank/valve masses. This gives the assembly REAL internal modes (frame
  bending/rocking, tank-on-rail) instead of one rigid rock. BLOCKING UNKNOWN =
  extrusion series (1010 1"x1" vs 1515 1.5" vs 40mm change A/I ~10x) -> asked
  Andrew before building. Photo (round 7) shows a ~3-bay rectangular cage,
  ~4-5 verticals, black tanks low, manifolds/valves across, bolted to the
  blue frame. ESTIMATES pending his confirm: ~22Lx12Wx14H in, 1.5" extrusion,
  4 tanks ~3 lb ea, valves/manifold ~8 lb distributed.
- **D21 (clarification question to Andrew, asked live 2026-06-11):** Which face(s)
  does the physical sticker shield cover, and should I ADD it to the model as an
  estimated thin panel (it is the tap-test/ruler-mount surface but is absent from
  the deck)? Options presented: (a) 45° ramp face, (b) 45° tower-front face,
  (c) plateau, (d) combination. My recommendation: add it coarse (16 ga steel
  estimated, screwed at discrete frame points) because the test taps the shield
  middle and clamps the ruler at the shield top-center — without it those QOI points
  do not exist in the model. AWAITING ANSWER before building the shield; everything
  not blocked (element library, validation, frame assembly) proceeds meanwhile.
