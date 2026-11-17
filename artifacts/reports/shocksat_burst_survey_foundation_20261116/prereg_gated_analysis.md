# Pre-registration: tests that run when NASA's files can be downloaded

Registered 2026-11-17, before any of the deciding data were seen. Changing a rule below after seeing tier-4 plots or burst bytes makes the result exploratory and must be logged in decisions_log.md.

## Test 1: does NASA's modal-survey data sit much closer to the FEM than the shock-campaign data?

Data: the 264 PNG plots in `FEM/Correlation/FRF_Verification/{11101X,11110Y}_Impact_Comparison/` (tier 4, 71 MB), NASA test (black) versus NASA FEM (red) for every measured response under two impact drives.

Seen before registration: the two drive-point curves reproduced on deck slides 16 and 17 (11101X to 11101X+, 11110Y to 11110Y+). They are excluded; the confirmatory set is the other 262 curves.

Primary metric M1: per curve, median over 46.79-258.38 Hz of |20 log10(test/NASA FEM)| after power-averaging both curves over 2.03 Hz. Summary: median over curves; 95 % interval by bootstrap over response nodes (2000 resamples, seed 20261117). Code: `code/tier4_study.py` (dry run on synthetic plots recovers M1 within 0.09 dB).

Decision rule (Card H reference: median 10.0 dB, 5th percentile 6.1 dB):
- SUPPORTED if M1 <= 6.0 dB and the interval's upper end < 8.0 dB: on NASA's modal-quality data a correlated FEM is within a factor of 2 at the median curve; the project's 10 dB wall is then largely a property of the shock-campaign data or sensors, not of the FEM.
- NOT SUPPORTED if M1 >= 8.0 dB: the wall persists on modal-survey data; NASA's data would mainly help frequencies and damping.
- INCONCLUSIVE otherwise.

QA (content-free, applied per plot before scoring): gridline-fit residual <= 1 px; panel edges at 10 and 400 Hz within 1 Hz; clipped fraction in band <= 0.10. Excluded plots are counted and reported.

Secondary metric M2: the same against the project FEM, using the frozen predictions `out/frozen_project_fem_predictions.npz` (264 curves, 10-400 Hz at 0.25 Hz, damping interpolated from NASA's impact survey). Array SHA-256: `a6f3bdec1c4c25b00ef84ce9086a946d4645321d782d982b04e88f13001ed484`. Plot level fixed by rounding to a whole decade the median offset between the project FEM and the digitised NASA FEM over 12-40 Hz; plots with an anchor residual above 0.1 decade are dropped from M2 only. Nodes 1106 to 1109 (cylindrical output frame) are reported separately.

Reported strata (not used for the verdict): drive point versus transfer; band below 150 Hz versus 150-200 Hz (NASA's own sensor-set limit); aluminium top box versus steel bottom box; distance from the drive.

## Test 2: are the burst files usable (foundation gates)

Run on tiers 0 to 3 (0.73 GB with time histories).
- F1 intact: every member's CRC-32 and size match the archive directory (zipfetch enforces this).
- F2 decodable: channel list consistent with NASA's instrumentation sheet (132 measured components on 76 nodes, plus force channels); sample rate, record and frame length identified; no non-finite samples. Layout documented in a parser with a byte-level test.
- F3 physically sane: H1 FRFs from run 78 show peaks within 1 % of NASA's run-78 frequencies (test report spreadsheet, tier 0) for at least 20 of NASA's 25 correlated modes, allowing for shaker-block mass loading.
- F4 quality: line spacing <= 0.25 Hz; median multiple coherence >= 0.9 over 45-200 Hz.
- F5 damping: at least 12 of the 22 test modes in 45-200 Hz have >= 3 lines across the half-power width (at 0.125 Hz, 19 of 22 would).
Verdict: foundation REAL if F1 to F4 pass; F5 decides whether damping can be identified from FRFs.

Known limitation stated in advance: NASA did not use shaker data for correlation because the attachment blocks mass-loaded the modes (deck slide 1). Any model fitted to runs 78, 99 or 139 must include the blocks; their masses are expected in the test plan (tier 1).
