# ShockSat Question Framing

## Engineering Decision

Decide whether the NASA/NESC ShockSat1 public release is ready to serve as the first real-data StatFEM digital-twin bridge for aerospace shock/modal updating, and define the smallest credible v1 update that can be defended with held-out validation.

## Objective / Success Metric

The immediate objective is traceability and comparability, not posterior performance. Success means a reviewer can audit source provenance, FEM metadata, channel/test metadata, first real measured-data plots, quantity contracts, and a realistic StatFEM launch plan from one scoped packet and replay command.

## What the Runner May Choose

The runner may choose:
- which source files to download first, subject to conservative large-file handling;
- which minimal archive subsets to extract;
- which representative measured channels/tests to plot after channel metadata is credible;
- which FEM/test comparisons are honestly supported by fetched files;
- whether a minimal StatFEM stub is justified or must be deferred.

## Fixed Assumptions

- Source originals stay under `sources/`.
- Extracted working files stay under `extracted/`.
- Outputs stay under `artifacts/reports/shocksat_statfem_runner_20260609/`, except project continuity notes required by `AGENTS.md`.
- No sampler is called NUTS/HMC without code, diagnostics, one-command replay, and checker output.

## Human Judgment

Human judgment remains responsible for deciding whether the v1 StatFEM target should prioritize hammer/modal updating, pyro shock validation, interface/QOI channels, or another mission-relevant quantity after the inventory is visible.

## Wrong-Question Trigger

The framing is wrong if the public ShockSat files lack enough channel-location, unit, input-force, or FEM-node mapping metadata to support a test/FEM likelihood. In that case the correct first task becomes metadata recovery or manual NASA documentation review, not Bayesian updating.

