# Codex CalculiX Phase-1 Build

Run from repo root:

```bash
python3 runs/fem_phase1/codex/calculix/code/run_calculix.py
```

The script writes `model/hexapod_codex.inp`, renders the undeformed geometry, and runs `ccx` if it is available either on `PATH` or at `$HOME/miniforge3_bayesx_femphase1/envs/ccx/bin/ccx`.

Model: C3D8 solid tray, T3D2 axial truss struts, fixed foot translations, and explicit apex joint nodes constrained to distributed tray nodes. Rigid-joint frequencies are provisional upper bounds.
