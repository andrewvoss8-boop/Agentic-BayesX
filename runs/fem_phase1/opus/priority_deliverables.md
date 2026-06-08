# Priority deliverables — Opus builder, Phase-1 hexapod FEM

Restated from docs/lab/fem_phase1_runner_prompt.md (my own words) + where each was delivered.
Acceptance: a priority with no delivered artifact = failure; an "assumed" interpretation
without confirmation = warning.

## Priority asks (per the task card)
1. **Build the SAME Phase-1 model in ALL FOUR tools** (CalculiX, TensorMesh, JAX, Nastran
   deck), as the Opus builder, using identical INPUTS but **independent re-derivation per
   tool** (no porting K/M / eigen-results / tables; no tuning between tools or agents).
   - DELIVERED: `calculix/`, `tensormesh/`, `jax/`, `nastran_deck/`, all from
     `shared/spec.py` (raw inputs only). Integrity statement in every README + results.json
     + `COMPARISON_opus_cross_software.md`. Each tool uses a genuinely different element
     family (plate-shell+beam / H8 solid+truss / C3D8I solid+truss / CQUAD4 shell+CROD).
2. **Solve normal modes (first ~10), render geometry + first ~6 mode shapes** (deck:
   geometry render only; human solves shapes).
   - DELIVERED: solved JAX/TensorMesh/CalculiX (frequencies + undeformed mesh + 6 mode-shape
     figures). Nastran deck: geometry render + RUN_IN_FEMAP.md; freqs null, solved_by=human.
3. **results.json in the common schema** (agent, tool, units, frame, mass case, ~10 freqs,
   element/mesh, mesh-convergence shift, per-mode type label).
   - DELIVERED: 4 × `results.json` (nastran null + solved_by=human).
4. **README with one-command replay** (solved tools); assumptions; what I did/didn't run.
   - DELIVERED: 4 × `README.md`; top-level `run_all.sh`.
5. **Self-checks** (no near-zero modes fixed-base; near-degenerate 120° pairs; mesh
   convergence; identify suspension/tray-flex/strut-self from shapes; label rigid-joint
   freqs PROVISIONAL UPPER BOUND).
   - DELIVERED: in each results.json + READMEs + COMPARISON.
6. **files_changed.md** (top level).
   - DELIVERED: `files_changed.md`.

## Interpretations / assumptions (flagged)
- **Joints rigid this phase, "explicit joint nodes":** realized as stiff translational
  springs (JAX/TensorMesh), RBE3-distributed truss ref node (CalculiX, to avoid a
  single-node local-mode artifact), and stiff CBUSH (Nastran deck). All moment-free
  (spherical). Finite compliance is a future parameter change. ASSUMED k_trans=1e9 N/m per
  the spec's "k≈1e9".
- **Strut element per tool (faithful best practice, per human instruction "work the specific
  element options available in each tool"):** beam in JAX (shows strut self-mode out of
  band), truss/rod elsewhere (faithful two-force spherical rod-end; robust in ccx/Nastran).
  This is an honest cross-tool element-theory spread, documented in COMPARISON.
- **No pre-loaded frequency target** (per the task card): solved from spec; agreement judged
  by cross-build convergence, not a typed magnitude.
- **Tray idealization differs by tool on purpose** (plate-shell vs solid hex vs shell): tests
  element theory; the tray-flex divergence is explained (locking vs incompatible-mode).

## Known gaps / residual risk
- CalculiX strut is a truss (no strut self-bending mode); JAX beam covers that check.
- TensorMesh tray-flex is locked-H8 over-stiff (~16 % mesh-sensitive); flagged, not hidden.
- Nastran deck unsolved by design (awaits human Femap solve).
- Mode-type labels are heuristic (rigid-body-fit fraction + strut/tray amplitude); the
  reviewer/MAC step will firm them up.
