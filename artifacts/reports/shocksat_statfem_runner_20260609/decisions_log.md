# ShockSat Decisions Log

## 2026-06-09 — Start With Provenance, Not Calibration

Decision: Treat this run as source acquisition, inventory, metadata extraction, first measured-data plotting, and launch definition. Do not implement a StatFEM posterior unless the likelihood inputs and held-out validation surface are sufficient.

Rationale: The user explicitly asked for a traceable foundation and warned against making a pretty result. The project memory also says real data is now the trust bridge, and synthetic FEM results are not validated science.

Alternatives considered: Jumping directly to a Bayesian update from any loaded data. Rejected because channel units, locations, sample rates, FEM mapping, and comparison quantities are not yet established.

## 2026-06-09 — Large Archive Handling

Decision: Fetch `_README.txt`, `_ShockSat_Overview_20220606.pdf`, and `Instrumentation_and_TestLog.zip` first. Before any multi-GB archive download, record disk space and attempt non-destructive header/range/listing strategies. Download large archives one at a time only when the session can do so safely.

Rationale: The user specified this acquisition order and asked for conservative handling of multi-GB packages.

Alternatives considered: Download all known archives immediately. Rejected because it would risk time/disk failures and reduce traceability if interrupted.

## 2026-06-09 — First Hammer FRF Layer Is Diagnostic, Not a Likelihood

Decision: Add a measured Test07 hammer accelerance estimate from force channel 116 to selected response channels, but label it as a low-coherence diagnostic until additional valid hits, source mapping, and NASA correlation response conventions are reconciled.

Rationale: The first extracted Test07 MAT record has the required force and acceleration channels, but the cross-spectral H1 estimator has low median coherence across the 100-10,000 Hz band. The NASA SOL 111 correlation assets use force grids such as 11101X/11110Y and response grids in the modal-test grid family, while the ShockSat shock channels use 9900001-style accelerometer grids. These are not safely interchangeable.

Alternatives considered: Overlaying the measured Test07 FRF on NASA SOL 111 PCH curves as if the source/response conventions matched. Rejected because it would fabricate a comparison contract that the current maps do not support.

## 2026-06-09 — Full Test07 Archive Recovery Does Not Remove the FRF Gate

Decision: Resume and verify the full `Test07_ImpactHammer_990x.zip` archive after an interrupted download, process the four MAT hammer hits it contains, and keep the result labeled as a low-coherence diagnostic rather than a StatFEM likelihood.

Rationale: The completed archive passes ZIP integrity checks and contains four MAT hit files, but the averaged H1 estimates still have median coherence of only about 0.07 from 100 to 10,000 Hz for selected channels. The TestLog has six matching Test07 rows while the archive exposes four MAT files, so TestLog rows are source-location metadata, not a one-to-one loaded-hit list until file/test mapping is reconciled.

Alternatives considered: Treating the multi-hit average as likelihood-ready because repeated hits were available. Rejected because repeated low-coherence transfer estimates do not satisfy the FRF quantity contract or the held-out validation gate.
