# Composer CalculiX Phase-1 Build

Run from repo root:

```bash
python3 runs/fem_phase1/composer/calculix/code/run_calculix.py
```

Model: SI units, origin at tray center, +z up, fixed feet at z = 0, bare 6061-T6 tray only. The generated CalculiX input uses C3D8 solid tray elements and T3D2 truss struts for spherical rod-end two-force behavior. Explicit apex joint nodes are tied to nearest tray top-surface nodes with `*EQUATION` translational constraints.

What ran here: input deck generation, undeformed geometry figure, and solver availability check.

What did not run: `ccx`/`ccx_2.21` was not available on this machine, so no CalculiX frequencies or mode-shape figures were produced. `results.json` marks this honestly as blocked, not solved.

Rigid-joint frequencies, once solved, are provisional upper bounds.
# Composer / CalculiX — Phase-1

## Replay

```bash
cd runs/fem_phase1/composer/calculix/code
../../../../.venv_fem_phase1/bin/python build_and_run.py
```

Uses `ccx` from repo-local conda env `.conda_calculix` (install once):

```bash
$HOME/.local/miniconda3/bin/conda create -y -p .conda_calculix -c conda-forge calculix=2.23
```

Deck: `model/hexapod.inp` (C3D8 tray + T3D2 struts, `*FREQUENCY` 10 modes). Frequencies parsed from `hexapod.dat`.
