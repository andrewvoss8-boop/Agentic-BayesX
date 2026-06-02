# Commands

Working directory: `/Users/avoss/Downloads/bayesX/Agentic BayesX`

## Environment Resolution

- `python3 --version` -> `3.9.6`
- NumPyro installed: `False`
- JAX installed: `False`
- PyMC installed: `False`
- PyTorch installed: `True`

Resolution: numpyro is not installed. JAX, PyMC, and ArviZ are also absent. No package installation was attempted. The run uses a labeled custom PyTorch-autograd fixed-trajectory HMC backend; NUTS is not active.

## Commands To Reproduce

1. `PYTHONPATH=. python3 -m py_compile scripts/run_codex_gpt55_full_experiment.py tests/test_runner_codex_gpt55_full_experiment.py`
   - Exit code: 0
   - Output: no console output.

2. `PYTHONPATH=. python3 scripts/run_codex_gpt55_full_experiment.py`
   - Exit code: 0
   - Output path: `artifacts/reports/runner_codex_gpt55_20260602/`
   - Console summary: self-check pass = true; full-data HMC divergences = 3; peak-feature HMC divergences = 0; full tray `3*GRMS` 95% interval = [1.1272430195867968, 3.0470227919946162] g; peak-feature tray `3*GRMS` 95% interval = [0.929469989994112, 2.4184115544838596] g.

3. `PYTHONPATH=. python3 tests/test_runner_codex_gpt55_full_experiment.py`
   - Exit code: 0
   - Checker report: `runner_checker_report.json`
   - Console summary: pass = true; failures = [].

4. `shasum -a 256 -c harness/checkers/manifest.sha256`
   - Exit code: 0
   - Console output:
     - `harness/checkers/verify_artifacts.py: OK`
     - `harness/checkers/check_canary.py: OK`
     - `tests/test_posterior_recovery.py: OK`
     - `tests/test_mdof_transfer.py: OK`
