# Commands — Round 2 (Claude Opus 4.8 runner)

All commands run from the isolated workspace
`/Users/avoss/Downloads/bayesX/Agentic_BayesX_runner_claude_opus48_r2` (asserted NOT master; no git
remote; path contains `runner_claude_opus48_r2`).

| # | Command | Purpose | Result |
|---|---|---|---|
| 1 | `pwd` ; `git remote -v` | Isolation assertion (P8) | workspace confirmed, no remote |
| 2 | `shasum -a 256 -c harness/checkers/manifest.sha256` | Immutable checker integrity | all 4 OK (start) |
| 3 | `python3 -m venv .venv_nuts` + pip install numpyro==0.15.3 jax==0.4.30 jaxlib==0.4.30 numpy<2 arviz==0.17.1 matplotlib imageio pillow scipy==1.10.1 | NUTS environment (system Py3.9.6 had none) | installed; JAX autodiff verified |
| 4 | `.venv_nuts/bin/python -c "<forward-model validation>"` | Verify JAX 2DOF forward model vs dataset clean curves | vibe & dome PSD rel err = 0.0 |
| 5 | `.venv_nuts/bin/python -c "<coupled mode + half-power>"` | Characterize resonances | coupled 62.3/129.5 Hz; Δf 1.82/7.85 Hz; tray-vibe 86.25 Hz |
| 6 | `R2_SMOKE=1 .venv_nuts/bin/python scripts/runner_claude_opus48_round2.py` | Pipeline smoke test (tiny draws) | end-to-end OK, 0 divergences |
| 7 | `.venv_nuts/bin/python scripts/runner_claude_opus48_round2.py` | FULL run: NUTS 4 chains + all artifacts | see nuts_diagnostics.json / pipeline_run.log |
| 8 | `shasum -a 256 -c harness/checkers/manifest.sha256` | Immutable checker re-verify (end) | (recorded at end) |
| 9 | `.venv_nuts/bin/python scripts/check_round2_artifacts.py` | Runner-local artifact/figure/legend/gate checker | writes checks.json |

## One-command replay
```
.venv_nuts/bin/python scripts/runner_claude_opus48_round2.py
```
(Environment build is a one-time step: `bash scripts/run_runner_claude_opus48_round2.sh` wraps venv
creation + the run + the checker; see that script.)

## Notes
- `R2_SMOKE=1` is ONLY for fast pipeline shakeout; reported numbers come from the full run.
- Two simultaneous runs were accidentally left contending early on; both were killed and a single
  clean full run was used for the reported artifacts (recorded honestly in known_failures.md).
