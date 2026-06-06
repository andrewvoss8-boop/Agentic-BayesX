# Public Decisions Log - Round 3 Codex Truth

Append-only. This public log intentionally avoids hidden truth parameters and hidden model-form-error details; those are sealed for the master.

## 2026-06-04T18:14:16Z

- Read only the allowed shared files: `AGENTS.md`, `CLAUDE.md`, `docs/agents/competitive_full_experiment/round3/blind_handoff_protocol.md`, and `docs/agents/competitive_full_experiment/round3/task_card_round3.md`.
- Initialized `runs/round3/codex_truth/` because it did not already exist.
- Interpreted the 11 flight forcing draws as shared across all 8 builds, yielding response arrays with shape `(build, flight, frequency)`. Rationale: this separates build-to-build structural scatter from flight-to-flight forcing scatter and gives the downstream inference agent hierarchical information.
- Interpreted the single-interface coupling channel as axial `z` for the netCG QOI, while publishing diagonal apparent mass for all 6 interface DOFs as observable multi-axis interface measurements.

## 2026-06-05T00:22:46Z

- Changed only the netCG-derived public and sealed scoring quantities to the canonical dynamic FBS definition in `docs/agents/competitive_full_experiment/round3/netcg_quantity_contract.md`: `netCG = F_iface(omega) / m_load`, with `F_iface` the dynamic transmitted load-interface force from source/load apparent-mass coupling and `m_load = load_mass_kg`.
- Removed the forbidden rigid mass-ratio constant transmission from the QOI path; the rigid mass-sharing ratio is retained only as the f -> 0 sanity check.
- Confirmed the f -> 0 rigid limit: max absolute transfer-ratio error versus the rigid limit was `5.551115123125783e-17`.
- Confirmed resonant structure: dynamic transfer amplification over the f -> 0 rigid limit ranged from `5.264312886487024` to `8.113264574477578`, with peak transfer frequencies from `63.75` to `68.1` Hz across build/flight cases.
- Confirmed non-netCG public arrays and non-netCG sealed scoring arrays were unchanged; details are in `report/checks/stage3_netcg_republish_checks.json`.
