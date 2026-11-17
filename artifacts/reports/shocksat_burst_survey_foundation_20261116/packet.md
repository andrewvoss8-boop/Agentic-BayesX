# Burst-survey foundation check (2026-11-16 to 2026-11-17)

Status: `checker_report.json`, overall YELLOW. Tooling, provenance and the pre-registration are checker-backed and were independently reviewed (decisions_log D11). The foundation question is open: NASA's server is refused by this cloud environment's network policy.

## Method summary
No inference, likelihood or sampler. Inputs: NASA archive directory tails (captured 2026-06-09); NASA's correlation deck; the project's Card H statistics (420 shock-sensor curves, in-sample). FEM FRFs by modal superposition of the frozen nominal model (80 modes to 321.7 Hz, damping interpolated from NASA's impact survey, 0.12 % to 0.89 %). One test article.

## Findings
1. Files located exactly. `Correlation/` is 594 members, 1.96 GB compressed (not about 1 GB). The plan needs 0.73 GB: burst time histories for runs 78 and 99 (263 MB each) and fixed-base run 139 (62 MB), the run-78 FRF file (53 MB), 27 documents and shape files (3.5 MB), and tier 4 (71 MB: 264 comparison plots plus NASA's two numeric FEM FRF files). Offsets and CRCs: `out/fetch_plan.json`.
2. NASA's documents limit the plan. NASA left the shaker runs out of its correlation because the attachment blocks mass-loaded the modes (slide 1), so runs 78, 99 and 139 need the blocks modelled. NASA's sensor set separates FEM modes below 150 Hz but not above (pseudo-orthogonality diagonal median 94 % versus 60 %).
3. NASA's correlation, recomputed: 25 test modes, 54 to 222 Hz; median frequency difference 4.3 %; median cross-orthogonality 83 % (93.5 % below 150 Hz, 79 % above).
4. Exploratory pilot, two curves (`figures/fig1_pilot_frf_wall.png`). At NASA's two drive points NASA's FEM is 2.7 to 3.1 dB from NASA's modal test below 150 Hz and 8.2 to 8.3 dB at 150 to 200 Hz. The project FEM is 3.0 to 3.6 dB from the same test below 150 Hz and 3.7 to 5.2 dB over Card H's band. Card H's median for the project FEM on shock sensors is 10.0 dB (minimum 4.8). This is not like-for-like: shock versus modal accelerometers, 0.49 s windowed hammer records with a fitted gain versus NASA's ~10-hit averages, transfer FRFs (median 18.5 in from the drive) versus drive points, which usually agree best, and NASA's FEM was tuned to NASA's data. The pilot motivates the pre-registered test; it attributes nothing.
5. NASA's single-impact repeatability (slide 19): median spread 0.4 dB at 45 to 200 Hz, near the 0.4 dB digitisation floor.
6. Damping resolvability (`figures/fig2_burst_resolution.png`, from NASA's measured frequencies and damping): at the shock caches' 2.03 Hz lines, 0 of 22 test modes in 45 to 200 Hz have 3 lines across their half-power width; with 8 s frames, 19 of 22 would. Rehearsal on the project FEM with stand-in shaker locations and 50 % bursts: median FRF error 0.45 dB with 2 s frames versus 0.17 dB with 8 s; median peak error 0.01 dB at 8 s (range -0.02 to +0.72 dB over 27 modes). Clustered modes (25 of 27) need a polyreference estimator that is not built. NASA's frame length is unknown until the files are parsed.
7. Torque sweep: 20 hits, 4 at each of 25, 50, 75, 100, 125 ("Name shows bolted joint torque"), impact at 990X, 2022-02-28, the day before the first frangible-joint firing; configuration to be confirmed.
8. Correction to my 2026-11-14 report: June work did use NASA's burst-run frequency tables (noise floor) and extracted the fixed-base model files; the raw burst files (.ati, .afu) were never used.

## Pre-registered next test (`prereg_gated_analysis.md`, hash-locked)
Score NASA's 262 unseen plots. SUPPORTED if NASA's FEM and the project FEM are both within 6 dB of NASA's test at the median curve; NOT SUPPORTED at 8 dB or more; exclusion cap and sensitivities can force INCONCLUSIVE. Then foundation gates F1 to F5 on the burst files.

## To continue
1. Allow `mediaex-server.larc.nasa.gov` in the cloud environment's network settings.
2. `bash gated_run.sh` (138 MB; add `WITH_TIME_HISTORIES=1` for the 589 MB time histories). Data stay outside the repository.
3. `bash run_all.sh` replays everything offline and runs the checker.

## Not done
Decoder for `.ati`/`.afu` (a structure probe exists, tested on synthetic files); polyreference damping estimator; any fitting to NASA data.
