# Runner Prompt — Phase 1 Hexapod FEM: Normal Modes (3-way build & compare)

Date: 2026-06-08. Source of truth: `docs/lab/FEM_architecture.md` (read the PHASE 1
block first). This is a **deterministic normal-modes (real-eigenvalue) task** — no
damping, no complex data, no force-limiting/coupling, no Bayesian/NUTS. Build the model
in your assigned tool, solve normal modes, visualize, and report for cross-comparison.

## Who runs this (3 agents, each builds ALL FOUR — see FEM_architecture.md "AGENT ASSIGNMENT")
You are ONE of three builder agents: **Opus (Claude Code), GPT (Codex), or Composer
(Cursor).** Each of you independently builds the SAME Phase-1 model in **all four tools**
below. Across the three agents this makes a 3-agent x 4-tool matrix the master will
compare both ways (cross-software and cross-agent). Work only in your own
`runs/fem_phase1/<agent>/<tool>/` (agent in {opus,codex,composer}; tool in
{calculix,tensormesh,jax,nastran_deck}).

**INTEGRITY RULE (do not break — it is the whole point):** use identical INPUTS in all four
builds (the shared node table, materials, masses, BCs below). But build each tool as an
INDEPENDENT re-derivation: do NOT copy your assembled K/M, eigen-results, or frequency
table from one tool into another, and do NOT tune one tool to match another or to match
another agent. The comparison is only meaningful if each engine is exercised on its own.

## Your job (all four tools)
For each tool, build the model, solve (or, for Femap, produce the deck), render the
geometry + first ~6 mode shapes, and write a `results.json` in the common schema.

- **CalculiX (`ccx`, SOLVED):** build a CalculiX `.inp` (solid/shell tray, beam struts,
  spring/rigid joint nodes), run `*FREQUENCY` normal modes, parse `.dat`/`.frd` for the
  first ~10 frequencies + mode shapes. Code + freq table + figures + one-command replay.
- **TensorMesh (`discretize`, SOLVED):** continuum/structured-mesh model (tray as
  plate/solid; struts as bar/spring members), assemble M and K, sparse generalized
  eigensolve (`scipy.sparse.linalg.eigsh`). Code + freq table + figures.
- **JAX (SOLVED):** hand-assembled structural model (beam struts + stiff joint springs +
  plate/lumped tray), assemble K and M, dense generalized eigensolve
  (`jax.scipy.linalg.eigh` or via `scipy`). Structure it as the future differentiable
  forward model, but **only run the eigensolve this phase** — no NUTS.
- **Femap/Nastran DECK (NOT solved by you):** a ready-to-run bulk-data deck (`.bdf`,
  SOL 103, EIGRL for ~10 modes) + a short `RUN_IN_FEMAP.md` so the HUMAN solves and
  visualizes in Femap. Deliver deck + procedure + the expected benchmark to check against.
  Do NOT invent solved numbers — leave the solved-frequency fields empty/null in
  `results.json` and mark `solved_by: human`.

## Shared model spec (identical across all three)
- **Units:** SI (m, kg, N). Coordinate frame: origin at tray center; +z up; tray plane at
  z = 0.098 m; base (ground) at z = 0. State your frame in the report.
- **Configuration:** tray-on-struts, **base ends FIXED** (grounded). Source plate NOT modeled.
- **Tray:** Thorlabs MB3030/M — solid 6061-T6 plate, 300 × 300 × 12.7 mm.
  E = 68.9 GPa, ν = 0.33, ρ = 2700 kg/m³. **Mass case: 3.1 kg** (bare; also report 5.0 kg).
  Shell/plate elements preferred (shows the ~468 Hz tray flex modes); rigid body + lumped
  mass acceptable for low modes only.
- **Struts (×6):** aluminum tube, 196 mm eye-to-eye, **8 mm OD, 1 mm wall (A ≈ 22 mm²,
  nominal — confirm on arrival)**, E = 68.9 GPa, ρ = 2700. Beam preferred (confirm ~370 Hz
  self-mode out of band); bar acceptable. **Spherical end releases** (release 3 rotations).
- **Joints:** RIGID this phase, placed as **explicit joint nodes** (stiff CBUSH k ≈ 1e9 N/m,
  or rigid link) at each strut end — so later compliance is a parameter change.
- **Geometry — true 120° hexapod, struts 30° off horizontal.** Node coordinates (mm):

  | strut | apex (tray, z=98) | foot (base, z=0) |
  |-------|-------------------|------------------|
  | b90+  | (   0, 110, 98)   | ( -65,  267, 0)  |
  | b90-  | (   0, 110, 98)   | (  65,  267, 0)  |
  | b210+ | ( -95, -55, 98)   | (-199, -190, 0)  |
  | b210- | ( -95, -55, 98)   | (-264,  -77, 0)  |
  | b330+ | (  95, -55, 98)   | ( 264,  -77, 0)  |
  | b330- | (  95, -55, 98)   | ( 199, -190, 0)  |

  (3 apex points on the tray at radius 110 mm, 120° apart; 6 grounded feet. All struts
  are 196 mm at 30° elevation.)
- **Solve:** real eigenvalue / normal modes, first ~10 modes. No damping, no forcing.

## Validation (every runner must check)
- Lowest 6 modes vs benchmark (rigid joints, 3.1 kg): **73, 73, 155, 260, 387, 387 Hz**.
- **Degenerate pairs present** (73/73, 387/387) ⇒ symmetry correct (the key check).
- Tray flex modes near **~468 Hz**; if beam struts, strut self-mode near **~370 Hz**.
- Report % difference from the benchmark and flag anything > ~5%.

## Deliverables (per tool, in `runs/fem_phase1/<agent>/<tool>/`)
For EACH of your four tools:
- `code/` (calculix/tensormesh/jax) or `model/model.bdf` + `RUN_IN_FEMAP.md` (nastran_deck).
- `figures/`: undeformed mesh render + first ~6 mode-shape plots (nastran_deck: geometry
  render from the deck; mode shapes come from the human's Femap solve).
- `results.json`: agent name, tool name, units, frame, mass case, first ~10 frequencies
  (Hz) (null + `solved_by: human` for nastran_deck), benchmark % diff, element types/mesh,
  mesh-convergence note.
- `README.md`: one-command replay (calculix/tensormesh/jax); assumptions; what you did/
  didn't run.
Plus one top-level `runs/fem_phase1/<agent>/files_changed.md`.

## Comparison (the master will assemble; each agent enables it)
Emit each `results.json` in the common schema so the master can build the 3-agent x 4-tool
frequency table (+ analytical oracle + the human's Femap solve) and MAC matrices on both
axes: CROSS-SOFTWARE (your four tools vs each other) and CROSS-AGENT (your tool vs the
other two agents' same tool). Expect close agreement on the shared synthetic geometry;
explain any divergence (mesh, element theory, lumped vs shell tray, transcription).

## Rules
- No success claim without the frequency table + figures actually produced (nastran_deck:
  deck + procedure only — do not invent solved numbers).
- Label the rigid-joint frequencies as a **provisional upper bound** (drop with joint
  compliance later).
- Declare units, coordinate frame, element types, and mesh density per build.
- Work only in your own `runs/fem_phase1/<agent>/<tool>/`; read this spec and
  FEM_architecture.md read-only; honor the INTEGRITY RULE (independent re-derivation per
  tool, identical inputs, no porting/tuning between tools or agents).
- OUT of scope (do not implement): damping/loss factor, complex/FRF data, force-limiting,
  source-plate coupling, NUTS/Bayesian inference.

---

## Support-agent prompts (applied AFTER the three builds land)

### Reviewer agent (Opus — integrity + technical + gates)
```text
You are the REVIEWER for the Phase-1 hexapod FEM cross-build. Read FEM_architecture.md
(PHASE 1 + AGENT ASSIGNMENT), this runner prompt, the apparent-mass-convention-postmortem
and log-frequency-plot-gp-postmortem, and each builder's runs/fem_phase1/<tool>/. Do NOT
trust reported numbers — recompute/spot-check from saved artifacts. Check and record
PASS/FAIL per item:
1. INDEPENDENCE: inspect code across each agent's four tools AND across agents per tool.
   Inputs must be identical (shared spec), but no agent ported assembled K/M, eigen-results,
   or frequency tables between its own tools or copied another agent's results, and did not
   tune one build to match another. Assemble the 3-agent x 4-tool matrix.
2. Units + coordinate frame stated and consistent; geometry matches the shared node table.
3. First ~10 frequencies recomputed; cross-tool table built; %-diff vs the analytical
   6-DOF benchmark (73,73,155,260,387,387 @ 3.1 kg) computed; anything >5% flagged.
4. Degenerate pairs present (73/73, 387/387) = 120° symmetry; flag if missing.
5. Mode-shape MAC matrix between tools; matched-mode diagonal > 0.9; report mismatches.
6. Tray-flex ~468 Hz and (if beam struts) strut self-mode ~370 Hz located and labeled.
7. Element type + mesh density stated AND a convergence/refinement check shown (refine,
   report frequency shift) — Discretization Resolution gate.
8. Rigid-joint frequencies labeled PROVISIONAL UPPER BOUND.
9. Any FRF-style plot: log frequency axis, no dB; any "apparent mass" carries the
   numerator/denominator/coordinate/BC contract (else FAIL per the postmortem).
10. Method summary present; one-command replay works (B, C); no success claim without the
    table + figures actually produced.
Output: artifacts/reports/fem_phase1_review_<date>/review.md + checks.json (per-gate
PASS/FAIL, recomputed numbers, and the cross-tool table + MAC). Do not fix the builds;
report. Surface the worst disagreement next to any "agreement" claim.
```

### Project-framing agent (Opus)
```text
You are the PROJECT-FRAMING agent for Phase-1 FEM. Read notes/project_vision.md,
notes/research_backlog.md, FEM_architecture.md, and this prompt. In plain English:
- State the engineering DECISION this Phase-1 FEM supports and why a verified normal-modes
  model is the right first step toward the dynamic StatFEM twin + interface-load QOI.
- Confirm the PRIORITY deliverables (geometry render; first ~10 modes + shapes; benchmark
  match incl. degenerate pairs; 3-software comparison) are surfaced and unambiguous; flag
  any ambiguity to the human BEFORE builds run.
- Flag SCOPE DRIFT in either direction: (a) creep INTO later-phase work now — damping,
  complex/FRF data, force-limiting, source-plate coupling, NUTS; (b) a build so reduced it
  cannot show the modes that drive the QOI (e.g., lumped-rigid tray hiding the ~468 Hz
  flex, or bar struts hiding the ~370 Hz self-mode when those matter).
- State what would make Phase 1 the WRONG question (e.g., if the suspension modes the rig
  is built to study fall outside the band of interest at the chosen geometry).
Output: framing.md (decision, objective, in/out of scope, open ambiguities, wrong-question
conditions). Do not build or review numbers; frame.
```
