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
