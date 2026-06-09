# ShockSat Download / Access Log

Generated: 2026-06-09T13:21:19+00:00

Primary log files:

- `artifacts/reports/shocksat_statfem_runner_20260609/logs/fem_and_cad_fetch.log`
- `artifacts/reports/shocksat_statfem_runner_20260609/logs/initial_fetch.log`
- `artifacts/reports/shocksat_statfem_runner_20260609/logs/instrumentation_fetch.log`
- `artifacts/reports/shocksat_statfem_runner_20260609/logs/large_file_header_range_probes.log`
- `artifacts/reports/shocksat_statfem_runner_20260609/logs/large_file_tail_range_listing_attempts.log`
- `artifacts/reports/shocksat_statfem_runner_20260609/logs/nsd_fetch.log`
- `artifacts/reports/shocksat_statfem_runner_20260609/logs/replay_after_test07_alignment_note.log`
- `artifacts/reports/shocksat_statfem_runner_20260609/logs/replay_after_test07_full.log`
- `artifacts/reports/shocksat_statfem_runner_20260609/logs/source_probe_initial.log`
- `artifacts/reports/shocksat_statfem_runner_20260609/logs/test07_full_resume_fetch.log`
- `artifacts/reports/shocksat_statfem_runner_20260609/logs/test07_impact_hammer_fetch.log`

Key finding: direct nescacademy asset URLs returned 404, while the page form route redirected to mediaex-server URLs that support HEAD and byte ranges.
