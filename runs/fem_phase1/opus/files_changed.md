# Files changed — Opus builder, Phase-1 hexapod FEM (2026-06-08)

All work is isolated under `runs/fem_phase1/opus/`. No files outside this directory were
modified except the lead's notes (`notes/memory.md`, `notes/todo.md`) and this runner's
`decisions_log.md`. The task card and FEM_architecture.md were read-only.

## Environment (created during setup, outside the repo)
- `runs/fem_phase1/opus/.venv/` — isolated venv: numpy 1.26.4, scipy 1.10.1, jax/jaxlib
  0.4.30, discretize 0.10.0, matplotlib. (git-ignored binary env)
- `~/miniforge3_bayesx_femphase1/envs/ccx/` — CalculiX 2.23 via conda-forge (isolated,
  outside the spaces-containing repo path because miniforge refuses spaces). (outside repo)

## Shared inputs (identical across tools; RAW NUMBERS ONLY, no assembly)
- `shared/spec.py` — node coords (mm→m), materials, sections, masses, BCs.

## JAX (solved): flat-shell tray (ACM plate + Q4 membrane) + 3-D beam struts + joint springs
- `jax/code/fe_elements.py` — beam3d + shell4 (ACM plate + Q4 membrane), jax.numpy.
- `jax/code/fe_validate.py` — element verification vs textbook (beam 0.005 %, SS plate 0.38 %).
- `jax/code/build_jax.py` — assembly, dense generalized eigensolve, classification,
  convergence, figures, jax.grad differentiability demo, results.json, runtime.json.
- `jax/figures/jax_undeformed_mesh.png`, `jax/figures/jax_mode_shapes.png`
- `jax/results.json`, `jax/runtime.json`, `jax/README.md`

## TensorMesh (solved): solid H8 tray on discretize.TensorMesh + truss struts
- `tensormesh/code/build_tensormesh.py` — H8 + truss assembly, sparse eigsh (shift-invert),
  convergence, figures, results.json, runtime.json.
- `tensormesh/figures/tensormesh_undeformed_mesh.png`, `.../tensormesh_mode_shapes.png`
- `tensormesh/results.json`, `tensormesh/runtime.json`, `tensormesh/README.md`

## CalculiX (solved): C3D8I solid tray + T3D2 truss + RBE3 bracket coupling
- `calculix/code/make_inp.py` — deck generator (C3D8I, T3D2, DCOUP3D, *FREQUENCY).
- `calculix/code/parse_ccx.py` — .dat/.frd parser, classification, figures, results.json.
- `calculix/code/run_ccx.py` — one-command driver (build + ccx + parse + 3-mesh convergence
  + runtime.json).
- `calculix/model/hexapod.inp` (+ hexapod_c.inp, hexapod_f.inp convergence decks).
- `calculix/figures/calculix_undeformed_mesh.png`, `.../calculix_mode_shapes.png`
- `calculix/results.json`, `calculix/runtime.json`, `calculix/README.md`

## Nastran DECK (human solves): CQUAD4 shell + CROD + CBUSH, SOL 103 EIGRL
- `nastran_deck/code/make_bdf.py` — bulk-data deck generator.
- `nastran_deck/code/render_and_results.py` — geometry render + results.json (null freqs).
- `nastran_deck/model/model.bdf`, `nastran_deck/model/deck_meta.json`
- `nastran_deck/figures/nastran_geometry.png`
- `nastran_deck/results.json` (solved_by=human), `nastran_deck/RUN_IN_FEMAP.md`,
  `nastran_deck/README.md`

## Top-level
- `decisions_log.md` — human decision + per-tool fidelity/integrity decisions.
- `priority_deliverables.md` — each priority ask, interpretation, where delivered.
- `COMPARISON_opus_cross_software.md` — my four-tool cross-software comparison + divergence
  explanations (the master assembles the full 3-agent × 4-tool matrix + MAC).
- `run_all.sh` — one-command replay of all four builds.
- `runtime.json` — aggregate runtime accounting.
- `files_changed.md` — this file.

## Headline result (rigid joints = PROVISIONAL UPPER BOUND)
Suspension modes agree to < 1 % across three independent engines:
~85, 85, 182, 290 Hz. First tray-flex: 337 (CalculiX C3D8I) / 371 (JAX plate) /
375 (TensorMesh locked H8) — an explained element-theory spread. Nastran deck awaits the
human Femap solve.
