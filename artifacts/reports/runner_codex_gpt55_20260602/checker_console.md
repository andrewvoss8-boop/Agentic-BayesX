# Checker Console Output

## Runner Checker

Command: `PYTHONPATH=. python3 tests/test_runner_codex_gpt55_full_experiment.py`

Exit code: 0

Summary:

```json
{
  "pass": true,
  "failures": [],
  "report": "runner_checker_report.json"
}
```

## Immutable Checker Hashes

Command: `shasum -a 256 -c harness/checkers/manifest.sha256`

Exit code: 0

```text
harness/checkers/verify_artifacts.py: OK
harness/checkers/check_canary.py: OK
tests/test_posterior_recovery.py: OK
tests/test_mdof_transfer.py: OK
```
