# Commands — Claude Opus 4.8 Full Sequential Runner

## Environment resolution (numpyro absent, system Python 3.9.6)

`numpyro`, `jax`, and `pymc` are NOT installed in the system Python 3.9.6
(`numpy`, `scipy`, `matplotlib` are). I created an isolated virtual environment and
installed NumPyro into it. arviz was attempted but removed (its build is incompatible
with the installed scipy: `cannot import name 'gaussian' from scipy.signal`); NumPyro's
own `numpyro.diagnostics` provides ESS and R-hat, so arviz is not required.

```
python3 -m venv .venv_nuts                                   # exit 0
.venv_nuts/bin/pip install numpyro matplotlib                # exit 0
.venv_nuts/bin/python -c "import numpyro,jax;print(numpyro.__version__,jax.__version__)"
#   -> numpyro 0.19.0   jax 0.4.30   (numpy 1.26.x, matplotlib 3.9.4)
```

## One-command replay

```
bash scripts/run_runner_claude_opus48.sh
```

This (re)creates the venv if missing, prints library versions, runs the NUTS inference,
runs the runner checker, and verifies the four immutable checker hashes.

## Individual commands actually run

```
# 1. Verify forward model reproduces dataset clean PSD (rel err ~6.5e-16). exit 0
.venv_nuts/bin/python - <<'PY' ... PY

# 2. MC estimate of fixed flight-to-flight QOI log-scatter (tray~0.197, iface~0.150). exit 0
.venv_nuts/bin/python - <<'PY' ... PY

# 3. Smoke test (2 chains, 80+80) of full and peak models. exit 0, 0 divergences.
.venv_nuts/bin/python - <<'PY' ... PY

# 4. FULL RUN: NUTS 4 chains x (1000 warmup + 1000 samples), both likelihoods. exit 0
.venv_nuts/bin/python scripts/runner_claude_opus48_full_experiment.py
#   full: divergences=0 max_rhat=1.002 min_ess=942
#   peak: divergences=0 max_rhat=1.002 min_ess=1495
#   wrote results.json, nuts_diagnostics.json, posterior_samples.npz, 6 figures
#   wall time ~2m48s

# 5. Runner checker -> writes checks.json
.venv_nuts/bin/python tests/test_runner_claude_opus48_full_experiment.py

# 6. Immutable checker hash verification
shasum -a 256 -c harness/checkers/manifest.sha256
```

## Notes
- Seeds: 20260602 (full), 20260603 (peak), 777 (QOI f2f MC), 2024 (QOI predictive). x64 enabled.
- All outputs land in `artifacts/reports/runner_claude_opus48_20260602/`.
- No immutable checker file was edited (hashes re-verified by step 6 and the runner checker).
