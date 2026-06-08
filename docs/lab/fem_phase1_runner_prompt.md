# Runner Prompt — Phase 1 Hexapod FEM: Normal Modes (3-way build & compare)

Date: 2026-06-08. Source of truth: `docs/lab/FEM_architecture.md` (read the PHASE 1
block first). This is a **deterministic normal-modes (real-eigenvalue) task** — no
damping, no complex data, no force-limiting/coupling, no Bayesian/NUTS. Build the model
in your assigned tool, solve normal modes, visualize, and report for cross-comparison.

## Agent assignment (one agent, one tool — see FEM_architecture.md "AGENT ASSIGNMENT")
- **Runner A = Composer (Cursor)** — CalculiX (recommended) or Femap/Nastran deck.
- **Runner B = GPT (Codex)** — TensorMesh / discretize.
- **Runner C = Opus (Claude Code)** — JAX hand-assembled FEM.
Work only in your own `runs/fem_phase1/<tool>/`; do not copy another agent's results.

## Your job (one tool per runner)
Build the SAME Phase-1 model in your tool, solve for the first ~10 natural frequencies
and mode shapes, render the geometry, and write a `results.json` so the three tools and
the analytical benchmark can be compared. Results go to the master agent for refinement.

- **Runner A — Composer (Cursor):**
  - *Recommended (CalculiX, agent-runnable):* build a CalculiX `.inp` (solid/shell tray,
    beam struts, spring/rigid joint nodes), run `ccx` *FREQUENCY normal modes, parse the
    `.dat`/`.frd` for the first ~10 frequencies + mode shapes. Deliver code + freq table +
    figures, one-command replay. This gives an independently SOLVED third result.
  - *Alternative (Femap/Nastran deck, human-solved):* produce a ready-to-run Nastran
    bulk-data deck (`.bdf`, SOL 103, EIGRL for ~10 modes) + a short `RUN_IN_FEMAP.md`; the
    human solves in Femap and exports the table + mode images. Deliverable is the deck +
    procedure + expected benchmark. Do NOT claim solved results you did not produce.
  - The human picks CalculiX vs Femap before launch (see FEM_architecture.md DECISION).
- **Runner B — GPT (Codex), TensorMesh:** continuum/structured-mesh model via
  `discretize.TensorMesh` (tray as a plate/solid; struts as bar/spring members), assemble
  M and K, sparse generalized eigensolve (`scipy.sparse.linalg.eigsh`). Deliver code +
  freq table + figures.
- **Runner C — Opus (Claude Code), JAX:** hand-assembled structural model (beam struts +
  stiff joint springs + plate/lumped tray), assemble K and M, dense generalized eigensolve
  (`jax.scipy.linalg.eigh` or via `scipy`). Structure it as the future differentiable
  forward model, but **only run the eigensolve this phase** — no NUTS.

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

## Deliverables (in your isolated workspace `runs/fem_phase1/<tool>/`)
- `code/` (B, C) or `model/model.bdf` + `RUN_IN_FEMAP.md` (A).
- `figures/`: undeformed mesh render + first ~6 mode-shape plots.
- `results.json`: tool name, units, frame, mass case, first ~10 frequencies (Hz),
  benchmark % diff, notes on element types/mesh.
- `README.md`: one-command replay (B, C); assumptions; what you did/didn't run.
- `files_changed.md`.

## Comparison (the master will assemble; each runner enables it)
Emit `results.json` in the common schema above so a side-by-side table (3 tools +
analytical) and a mode-shape comparison (MAC where feasible) can be built. Expect close
agreement on the shared synthetic geometry; explain any divergence (mesh, element theory).

## Rules
- No success claim without the frequency table + figures actually produced (Femap runner:
  deck + procedure only — do not invent solved numbers).
- Label the rigid-joint frequencies as a **provisional upper bound** (drop with joint
  compliance later).
- Declare units, coordinate frame, element types, and mesh density.
- Work only in your own `runs/fem_phase1/<tool>/`; read this spec and FEM_architecture.md
  read-only; do not copy another runner's results and present them as yours.
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
1. Each agent used a DISTINCT software and did not copy another's results (inspect code).
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
