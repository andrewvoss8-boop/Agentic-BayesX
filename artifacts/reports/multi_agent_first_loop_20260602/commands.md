# Commands

## Main Payload

```bash
bash scripts/run_fresh_2dof_statfem_fbs.sh
```

Expected output:

- `artifacts/reports/fresh_2dof_statfem_fbs_20260601/checker_report.json`
- `artifacts/reports/fresh_2dof_statfem_fbs_20260601/checker_report_external.json`
- `artifacts/reports/fresh_2dof_statfem_fbs_20260601/fresh_2dof_statfem_packet.md`

## Scaffold Check

```bash
python3 tests/test_multi_agent_scaffold.py
```

Expected output:

- `artifacts/tests/multi_agent_scaffold_report.json`

## Immutable Checker Hash Check

```bash
shasum -a 256 -c harness/checkers/manifest.sha256
```

Expected output:

- Terminal output showing all immutable checker files `OK`.

## Run Log

2026-06-02:

| Command | Exit code | Evidence |
|---|---:|---|
| `bash scripts/run_fresh_2dof_statfem_fbs.sh` | 0 | Printed checker `pass = true`; wrote `artifacts/reports/fresh_2dof_statfem_fbs_20260601/fresh_2dof_statfem_packet.md`. |
| `python3 tests/test_fresh_2dof_rerun.py` | 0 | Printed `pass = true`, `numeric_assumption_count = 30`, `channel_2_3_relative_l2 = 0.6739064407171255`. |
| `python3 tests/test_multi_agent_scaffold.py` | 0 | Printed `pass = true`; wrote `artifacts/tests/multi_agent_scaffold_report.json`. |
| `shasum -a 256 -c harness/checkers/manifest.sha256` | 0 | Immutable checker files reported `OK`. |

These commands verify the scaffold and replay the existing fresh 2DOF workflow. They do not implement NUTS/HMC.
