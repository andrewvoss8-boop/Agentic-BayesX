# Pre-registration: tests that run when NASA's files can be downloaded

Registered 2026-11-17 before any deciding data were seen; revised the same day after an independent review (decisions_log D11), still before any deciding data were seen. Scoring code, this file and the frozen predictions are hash-locked in `prereg_lock.json`; `tier4_study.py` refuses to score if any changed (`--exploratory` labels such a run exploratory).

## Test 1: is NASA's FEM much closer to NASA's modal-survey FRFs than the project's FEM was to the shock-sensor FRFs?

Data: tier 4 of the fetch plan (71 MB): 264 PNG plots in `FRF_Verification/{11101X,11110Y}_Impact_Comparison/` (NASA test in black, NASA FEM in red, every measured response under two impact drives) plus NASA's two numeric FEM FRF files (`SOL_111_*.pch`) and run decks.

Already seen: deck slides 16 and 17 (the two drive-point curves, digitised), slides 18, 19 and 47 to 53 (impact-location and repeatability overlays, modal fit plots), and the .pch files, which the June 2026 runners extracted and partly parsed (the 11101X drive, X components). The two drive-point curves are excluded; the confirmatory set is the other 262.

M1 (primary): per curve, median over 46.79-258.38 Hz of |20 log10(test/NASA FEM)| after power-averaging both curves over 2.03 Hz. Summary: median over curves, 95 % interval by bootstrap over response nodes (2000 resamples, seed 20261117).

M2 (required for SUPPORTED): the same against the project FEM, from frozen predictions (`out/frozen_project_fem_predictions.npz`, array SHA-256 `a6f3bdec1c4c25b00ef84ce9086a946d4645321d782d982b04e88f13001ed484`, re-verified before scoring). The plot's absolute level comes from NASA's own numeric FEM: a unit factor between the .pch magnitudes and the plotted g/lbf is fixed once from the two seen drive-point plots (both estimates must agree within 0.05 decade); per plot the decade is the rounded median offset between that numeric curve and the digitised red curve, and the fractional residual (<= 0.1 decade) is the per-plot digitiser check. The model under test plays no part in anchoring. Responses outside the 76-node frozen set get M1 only. M2 is reported only if at least 85 % of eligible curves pass the anchor check.

Verdict (Card H reference: median 10.0 dB, 5th percentile 6.1 dB):
- SUPPORTED: M1 <= 6.0 dB with interval upper end < 8.0 dB, and M2 <= 6.0 dB.
- NOT SUPPORTED: M1 >= 8.0 dB or M2 >= 8.0 dB.
- INCONCLUSIVE: otherwise; also if more than 15 % of the 262 curves are excluded (QA failures and errors both count), or if either sensitivity (clipped columns imputed at the panel edge; no QA exclusion) changes the verdict.

Interpretation fixed in advance: SUPPORTED means that on NASA's modal-quality data, sensors and drives a correlated FEM sits within a factor of 2 at the median curve, so the project's 10 dB result is associated with the shock-campaign data, sensors, drives or processing rather than with the FEM alone. It is an association across different test set-ups, not a causal attribution, and NASA's FEM was tuned to these same data (in-sample for M1). NOT SUPPORTED means the gap persists on modal-survey data.

QA per plot (content-free): gridline-fit residual <= 1 px; panel edges at 10 and 400 Hz within 1 Hz; clipped fraction in band <= 0.10. Reported strata (no verdict role): band below 150 Hz versus 150-200 Hz; aluminium top box versus steel bottom box; distance from the drive.

## Test 2: are the burst files usable (foundation gates)

Run on tiers 0 to 3 (0.73 GB with the time histories).
- F1 intact: every member's CRC-32 and size match the archive directory (enforced by zipfetch).
- F2 decodable: channels consistent with NASA's instrumentation sheet (132 measured components on 76 nodes plus force channels); sample rate, record and frame length identified; no non-finite samples; layout documented in a parser with a byte-level test.
- F3 physically sane: run 78 H1 FRFs show peaks within 1 % of NASA's run-78 frequencies (test report, tier 0) for at least 20 of NASA's 25 correlated modes, allowing for shaker-block mass loading.
- F4 quality: line spacing <= 0.25 Hz; median multiple coherence >= 0.9 over 45-200 Hz.
- F5 damping: line spacing <= 0.125 Hz (19 of 22 test modes then have >= 3 lines across the half-power width, a necessary condition), and a polyreference damping estimator, still to be built, that recovers the rehearsal's damping within 25 % for at least 80 % of the 27 modes in 45-200 Hz before it is applied.
Verdict: foundation REAL if F1 to F4 pass; F5 decides whether damping can be identified.

Stated in advance: NASA did not use the shaker runs for correlation because the attachment blocks mass-loaded the modes (deck slide 1). Any model of runs 78, 99 or 139 must include the blocks; their masses are expected in the test plan (tier 1).
