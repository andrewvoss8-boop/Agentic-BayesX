# Composer agent — FEM Phase 1 (recreated 2026-06-08)

- `jax/` — C3D8 + truss, JAX eigh
- `tensormesh/` — TET4 + scipy.sparse eigsh
- `calculix/` — hexapod.inp + ccx solve via `.conda_calculix`
- `nastran_deck/` — model.bdf + RUN_IN_FEMAP.md (human solve)

Independent re-derivation per tool; identical spec inputs.
