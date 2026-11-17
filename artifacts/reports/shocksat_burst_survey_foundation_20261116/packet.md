# Burst-survey foundation check (2026-11-16 to 2026-11-17)

Status: see `checker_report.json` (expected overall YELLOW). Tooling, provenance and the pre-registration are checker-backed; the foundation question itself is open because NASA's server is blocked from this cloud environment.

## Method summary
- No inference, no likelihood, no sampler. Everything here is measurement and bookkeeping: archive tables of contents, NASA's own documents, curves digitised from NASA's figures, and modal-superposition FRFs of the project's frozen nominal FEM.
- Data: NASA ShockSat archives (directory tails captured 2026-06-09); NASA's correlation deck (76 slides); the project's 2026-07-23 Card H statistics (420 shock-sensor curves, in-sample). One test article; no repeat builds.
- FEM FRF: H_rd(f) = sum over 80 modes of phi_r phi_d (-w^2)/(w_m^2 - w^2 + 2i zeta_m w_m w), in g/lbf; zeta interpolated from NASA's impact-survey fits (0.12 % to 0.89 %).

## Findings
1. The files exist and are exactly locatable. `Correlation/` is 594 members, 1.96 GB compressed (not about 1 GB). What the plan needs is 0.73 GB: run 78 and 99 free-free burst time histories (263 MB each compressed), run 139 fixed-base (62 MB), the run 78 FRF file (53 MB), 27 documents and shape files (3.5 MB), and NASA's 264 test-versus-FEM plots (71 MB). Byte offsets and CRCs: `out/fetch_plan.json`.
2. NASA's own documents set two limits on the plan. NASA did not use the shaker runs for correlation because the attachment blocks mass-loaded the modes (slide 1), so any use of runs 78, 99, 139 must model the blocks. NASA's sensor set separates FEM modes well below 150 Hz but not above (pseudo-orthogonality diagonal median 94 % versus 60 %; NASA: "Correlation will struggle above 150 Hz").
3. NASA's correlation quality, recomputed from its tables: 25 test modes 54 to 222 Hz, median frequency difference 4.3 %, median cross-orthogonality 83 % (93.5 % below 150 Hz, 79 % above).
4. Exploratory pilot (two curves, `figures/fig1_pilot_frf_wall.png`). At NASA's two drive points, NASA's FEM is 2.8 to 3.1 dB from NASA's modal test below 150 Hz and 8.2 to 8.3 dB at 150 to 200 Hz. Over Card H's band and resolution the values are 5.0 and 3.5 dB, against 10.0 dB median (minimum 4.8 dB) for the project FEM on 420 shock-sensor curves. Frequency smoothing to 2.03 Hz changes the NASA values by less than 0.3 dB, so resolution does not explain the gap. The project FEM matches NASA's FEM to 0.5 to 0.9 dB below 150 Hz, so the models are not the difference. Shock sensors within 4 in of the drive still score 9.2 dB median. Caveat: two curves, chosen by NASA, drive points (which usually agree best).
5. NASA's single-impact repeatability (slide 19): median spread 0.4 dB at 45 to 200 Hz, close to the 0.4 dB stroke-width floor of the digitisation.
6. What burst data could resolve (`figures/fig2_burst_resolution.png`, no simulation needed): at the shock caches' 2.03 Hz lines, 0 of NASA's 22 test modes in 45 to 200 Hz have 3 lines across their half-power width (median 0.4); with 8 s frames, 19 of 22 would. The rehearsal on the project FEM shows the multiple-input estimator recovers peaks within 0.02 dB with 8 s frames, while 2 s frames leak (worst peak -0.55 dB). Frame length of NASA's records is unknown until parsed.
7. Torque sweep confirmed: 20 hits, 4 at each of 25, 50, 75, 100, 125 (NASA's log: "Name shows bolted joint torque"), impact at 990X, dated 2022-02-28, the day before the first frangible-joint firing. The configuration (probably with the separation joint and extension box, which the project FEM lacks) is to be confirmed from the files.

## Pre-registered next test
`prereg_gated_analysis.md`: score the 262 unseen NASA plots. SUPPORTED if the median curve is within 6 dB (and its interval below 8 dB), meaning the 10 dB wall is mainly a data or sensor property; NOT SUPPORTED at 8 dB or more. Project-FEM predictions are frozen (hash in the prereg). Then foundation gates F1 to F5 on the burst files.

## How to continue
1. Allow `mediaex-server.larc.nasa.gov` in the cloud environment's network settings.
2. `bash gated_run.sh` (adds `WITH_TIME_HISTORIES=1` for the 589 MB time histories). Data stay outside the repository.
3. `bash run_all.sh` replays everything offline and runs the checker.

## Not done
A polyreference damping estimator (needed for 25 of 27 clustered modes); a decoder for the `.ati`/`.afu` layout (only a structure probe exists, tested on synthetic files); any fitting to NASA data.
