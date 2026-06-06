# Commands — Round 3 (Claude Code Opus 4.8 runner)

All commands run from the master repo root `Agentic BayesX/`. Workspace = `runs/round3/opus48/`.
Interpreter: the project's NUTS env `.venv_nuts` (jax 0.4.30, numpyro 0.15.3, numpy 1.26.4, scipy
1.10.1, arviz, matplotlib, imageio). `meshio` + `python-pptx` are installed locally into the workspace
(`runs/round3/opus48/.pylibs`, no numpy so the venv's numpy 1.26.4 is kept) and put on PYTHONPATH.

## Environment setup (one-time; local libs, no shared-env mutation)
```
.venv_nuts/bin/pip install --target runs/round3/opus48/.pylibs --no-deps \
    meshio python-pptx rich lxml Pillow XlsxWriter typing_extensions
```

## One-command replay (FULL pipeline — NUTS + prediction + all figures + results)
```
PYTHONPATH="runs/round3/opus48/.pylibs" .venv_nuts/bin/python runs/round3/opus48/code/run_pipeline.py
```
Writes: report/nuts_diagnostics.json, results.json, interface_psd_bands.json, resolution_metrics.json,
sensitivity.json, posterior_samples.npz, runtime_pipeline.json, pipeline_summary.json, and all figures
(interface_netcg_psd_vs_spec.gif + frames, netcg_psd_headline.png, component_frfs.png,
netcg_vs_vibe_reference.png, flight_forcing_overlay.png, sensitivity_offset_ell.png,
resolution_sensitivity.png, posterior_recovery.png). Smoke: prefix `R3_SMOKE=1` (NOT for reporting).

## Forward-model self-test (bases + pressure-stiffening demo)
```
PYTHONPATH="runs/round3/opus48/.pylibs" .venv_nuts/bin/python runs/round3/opus48/code/mdof_forward.py
```

## Validation / references gate (betaL cantilever, lumped MDOF, FBS==round2, antiresonance, anchors)
```
PYTHONPATH="runs/round3/opus48/.pylibs" .venv_nuts/bin/python runs/round3/opus48/tests/validate_fem.py
# -> report/validation.json ; exit 0 only if ALL pass
```

## FEM mesh export + mode-shape/assembly figures
```
PYTHONPATH="runs/round3/opus48/.pylibs" .venv_nuts/bin/python runs/round3/opus48/code/fem_export.py
# -> report/mesh/{nodes.csv,elements.csv,model.bdf,model.vtu,model.msh,model.obj,mesh_summary.json}
#    report/figures/{mesh_assembly.png,modeshapes_dome.png,modeshapes_tray.png}
```

## Review packet (PPTX)
```
PYTHONPATH="runs/round3/opus48/.pylibs" .venv_nuts/bin/python runs/round3/opus48/code/make_pptx.py
# -> report/packet.pptx
```

## Immutable-checker integrity (must be unchanged pre/post)
```
shasum -a 256 -c harness/checkers/manifest.sha256
```
</content>

## BLIND inference round (vs Codex independent truth) — one-command replay
```
# (env: repo-root .venv_nuts; local libs on PYTHONPATH)
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind_model.py        # forward-model sanity vs published data
R3BLIND_COMPANIONS=0 PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind_infer.py   # NUTS + held-out calibration
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind_qoi.py          # netCG/interface-PSD QOI vs spec
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind_pptx.py         # packet.pptx
# Companions (slow, optional, diagnostic): R3BLIND_COMPANIONS=1 ... code/blind_infer.py
```

## STAGE 3 (structure-aware fix) — one-command replay (env: repo-root .venv_nuts; .pylibs+code on PYTHONPATH)
```
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind3_model.py    # forward-model sanity vs data
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind3_infer.py    # NUTS(with-d) + without-d + starve + held-out + n_eff
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind3_qoi.py      # full-uncertainty netCG (with-d + converged without-d)
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind3_figs.py     # review figures
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind3_gridinv.py  # grid-invariance companion
PYTHONPATH=".pylibs:code" ../../../.venv_nuts/bin/python code/blind3_pptx.py     # packet.pptx
# Quick low-sample test (NOT for reporting): prefix R3_SMOKE=1
```
