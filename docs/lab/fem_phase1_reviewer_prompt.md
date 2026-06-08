# Reviewer Prompt — Phase-1 Hexapod FEM Cross-Build (Opus: integrity + technical + gates)

Date: 2026-06-08. Run as a FRESH Opus session AFTER the builder agents (opus, codex,
composer) have written their packets and AFTER the human has solved at least one Femap
deck. You are the single reviewer covering integrity, technical correctness, and harness
gates. You do NOT fix the builds; you recompute, compare, and report. Read the role files
docs/agents/roles/reviewer.md, docs/agents/competitive_full_experiment/reviewer_integrity.md,
and reviewer_technical.md for stance.

```text
You are the REVIEWER for the Phase-1 hexapod-tray normal-modes cross-build. Honesty rules:
recompute from saved artifacts (do not trust a reported number you did not reproduce);
mark anything you cannot verify PENDING, not PASS. Write ONLY to
artifacts/reports/fem_phase1_review_20260608/.

CONTEXT (read first):
- docs/lab/FEM_architecture.md (PHASE 1 + AGENT ASSIGNMENT + the "NO PRE-LOADED BENCHMARK"
  and "BARE TRAY, NO ballast" decisions).
- docs/lab/fem_phase1_runner_prompt.md (shared spec, self-checks, integrity rule).
- docs/lab/apparent-mass-convention-postmortem.md and log-frequency-plot-gp-postmortem.md
  (convention gates — apply if any FRF/transfer-function plot appears; Phase 1 should have
  none, so flag any that do as out of scope).
- Each builder packet: runs/fem_phase1/<agent>/<tool>/ for agent in {opus,codex,composer},
  tool in {calculix,tensormesh,jax,nastran_deck}; plus each agent's decisions_log.md and
  files_changed.md.

KEY STANCE — there is NO ground-truth frequency target. The old analytical 6-DOF hand-calc
was removed on purpose. Judge by CONVERGENCE across independent builds, not by distance to
any typed number. Do NOT reintroduce the hand-calc as a pass/fail bar. You MAY, AFTER
building the table, run your own reproducible analytical 6-DOF script as ONE clearly-
PROVISIONAL cross-reference (rigid-joint upper bound); label it provisional, never "truth".

WHAT TO PRODUCE (artifacts/reports/fem_phase1_review_20260608/):
- review.md: narrative, per-gate PASS/FAIL/PENDING, integrity findings, the disagreement
  interpretation, and a verdict + recommendation.
- checks.json: machine-readable {gate: status, evidence, recomputed_value} per item.
- matrix.json + matrix.md: the 3-agent x 4-tool frequency table (first ~10 modes), plus
  the human-solved Femap column when present, plus your optional provisional analytical
  cross-reference (clearly labeled).
- mac/: MAC matrices (see below) for cross-software and cross-agent comparisons, with the
  node set used.
- recompute_log.md: exactly what you re-ran, the commands, and the env.

STEP 1 — RECOMPUTE (do not trust reported tables).
- For calculix/tensormesh/jax: re-run each agent's one-command replay in an isolated env;
  parse the produced frequencies yourself. If a replay fails or a tool was not installable
  in-sandbox, record PENDING with the exact error, do not infer numbers.
- For nastran_deck: frequencies come from the human's Femap solve (see STEP 5). If a deck's
  results.json still has null frequencies and status deck_generated_not_solved, mark that
  cell PENDING (human solve not yet folded in) — this is expected, not a failure.

STEP 2 — BUILD THE MATRIX (two axes).
- CROSS-SOFTWARE (per agent): do that agent's JAX / TensorMesh / CalculiX / Femap agree on
  identical inputs? Differences expose discretization / element-theory effects.
- CROSS-AGENT (per tool): do opus / codex / composer agree in the SAME engine? Differences
  expose implementation / transcription effects.
- Report per-mode spread (min, max, mean, % spread) across each axis. Sort/align modes by
  ascending frequency AND by mode-type label so you are comparing like with like.

STEP 3 — MAC (mode-shape agreement). MAC (Modal Assurance Criterion) is a 0..1 number: 1 =
identical shape, 0 = orthogonal. It needs the two shapes sampled at the SAME physical
points. Meshes differ across tools, so compute MAC on a COMMON REDUCED node set that all
builds share — the 3 tray-apex/joint nodes plus the 4 tray corners (interpolate to those
points if needed). Where meshes are too dissimilar to map, say so and fall back to
frequency + mode-type agreement, explicitly labeled as a weaker check. Matched-mode MAC
diagonal > 0.9 is the target; report off-diagonal mode-swapping.

STEP 4 — GATE CHECKLIST (PASS / FAIL / PENDING, with recomputed evidence each):
G1. INDEPENDENCE (the comparison's validity). Inspect code across each agent's four tools
    AND across agents per tool. Inputs must be identical (shared node table, materials,
    masses, BCs). FAIL if any agent ported assembled K/M, eigen-results, or a frequency
    table between its own tools or copied another agent's results, or tuned one build to
    match another. Cite the lines you inspected.
G2. UNITS + FRAME stated and consistent; geometry matches the shared node table (apex at
    radius 110 mm, z=0.098 m; 6 feet at z=0). Recompute tray mass from geometry x density
    (~3.086 kg solid); flag if a build used a different mass or any ballast (Phase 1 = bare,
    no ballast).
G3. FIXED-BASE SANITY: with feet fixed there should be NO zero/near-zero modes. Flag any
    rigid-body (~0 Hz) mode as a BC error.
G4. SYMMETRY: report whether near-degenerate mode pairs appear (a consequence of the true-
    120 deg geometry + rigid tray). A missing pair flags a broken-symmetry geometry bug.
    This is a geometry check, NOT a frequency-match check.
G5. MESH CONVERGENCE: each solved build refined the mesh and reported the first ~10-mode
    frequency shift (Discretization Resolution gate). FAIL if absent for a solved tool.
G6. MODE-TYPE BY SHAPE: suspension (tray-on-struts) vs tray-flex vs strut-self modes
    labeled from the SHAPES, not from an assumed frequency. Spot-check at least two labels
    against the mode-shape figures.
G7. PROVISIONAL LABELING: all rigid-joint frequencies labeled a provisional upper bound.
G8. REPRODUCIBILITY: one-command replay works for calculix/tensormesh/jax; nastran_deck
    ships a runnable .bdf + RUN_IN_FEMAP.md; no success claim without the table + figures
    actually produced.
G9. CONVENTION GUARD: if any FRF/apparent-mass/transfer-function plot appears, it must use
    a log frequency axis, no dB, and carry the numerator/denominator/coordinate/BC contract
    (postmortems). Phase 1 should have none; flag any as scope creep.
G10. DECK-vs-DOC CONSISTENCY (nastran_deck): the RUN_IN_FEMAP.md description must match the
    actual .bdf (element types, SPC, RBE2). Flag internal contradictions (e.g., a procedure
    that says both CQUAD4 shell and CHEXA solid for the tray).

STEP 5 — FOLD IN THE FEMAP (human-solved) RESULT. See the human-handoff section in this
file. Expect, per solved deck, in runs/fem_phase1/<agent>/nastran_deck/: a filled
results.json (frequency_hz + mode_type populated, solved_by: human, status solved_human,
solver+version+date), a figures/ with the first ~6 mode-shape images, and an exported
frequency table (csv/txt) and/or the Femap .f06/.op2 (or a screenshot) for traceability.
Add the Femap column to the matrix. The Femap solve is a valuable INDEPENDENT cross-check
but is NOT ground truth (same rigid-joint upper-bound model) — treat it as one more column.

STEP 6 — INTEGRITY FINDINGS. Explicitly state: any copied/fabricated numbers; any silent
method swap from the spec; any "agreement" claimed without recompute; any figure that is
unreadable or mislabeled. If clean, say so plainly.

STEP 7 — DISAGREEMENT INTERPRETATION (physical, not hidden). For each mode where spread
exceeds a few percent, give the likely cause: tray modeled as lumped-rigid vs meshed
shell/solid (changes tray-flex and effective mass); bar vs beam struts (changes strut-self
modes); joint node as rigid link vs stiff CBUSH (changes suspension modes); strut area /
wall assumption (the 5.5 vs ~7.7 MN/m axial-stiffness ambiguity scales suspension modes);
mesh density; element formulation. Distinguish cross-software causes from cross-agent
(transcription) causes.

STEP 8 — VERDICT + RECOMMENDATION. One of: CONVERGED (independent builds agree within a
stated tolerance; report it), DIVERGENT-NEEDS-INVESTIGATION (name the specific builds/modes
and the most likely cause), or BLOCKED (what is missing — e.g., codex packet or Femap solve
not yet in). Recommend the smallest next action. Surface the WORST disagreement next to any
"agreement" statement. Do not overstate.
```

## Human handoff: what to do with the Femap outputs
After you solve a deck in Femap, place the outputs back into that agent's workspace so the
reviewer folds them into the matrix. Per solved deck
(`runs/fem_phase1/<agent>/nastran_deck/`):
1. Edit `results.json`: fill each `frequency_hz` with the solved value, set `mode_type`
   from the SHAPE (suspension / tray-flex / strut-self), set `solved_by: "human"`,
   `status: "solved_human"`, and add `solver`, `solver_version`, `date`, `solved_by_name`.
   Fill `self_checks.fixed_base_no_zero_modes` and `near_degenerate_pair_gaps_percent`.
2. Save the exported frequency table as `femap_export/frequencies.csv` (mode, Hz) and the
   first ~6 mode-shape images to `figures/` (e.g., `mode01.png`).
3. Save a traceability artifact: the Femap `.f06`/`.op2` if small, or a screenshot of the
   frequency table, under `femap_export/`. Note which solver and version produced it.
4. Do NOT edit the `.bdf` to chase a number; if you change the model, say so in
   `decisions_log.md` and re-solve.
You only NEED one solved deck to give the matrix a real-FEA cross-check, but solving each
agent's deck adds a cross-agent check on the decks themselves. The Femap result is an
independent cross-reference, not ground truth (it is the same rigid-joint upper-bound model).
