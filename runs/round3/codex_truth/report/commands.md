# Commands

From `runs/round3/codex_truth/`:

```bash
PIP_CACHE_DIR=.pip-cache python3 -m pip install --target .deps meshio
python3 sealed_truth/generate_truth.py --root .
```

The generator writes the public dataset, sealed truth files, validation report, mesh exports, figures, checks, and runtime files.

## Stage-3 netCG republish

From the repository root:

```bash
PYTHONPATH=runs/round3/codex_truth/.deps python3 - <<'PY'
# Recompute canonical dynamic FBS netCG from sealed truth builds plus published forcing,
# overwrite only netCG-derived public/scoring-key arrays, and write
# report/checks/stage3_netcg_republish_checks.json plus runtime.json.
PY
```

No inference, fitting, NUTS, GIF, or PPT command was run.
