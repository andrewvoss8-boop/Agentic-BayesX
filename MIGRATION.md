# Migration handoff for a new Claude account (2026-11-20)

Read this first, then follow the re-grounding routine in `CLAUDE.md` and `AGENTS.md`. Nothing here depends on chat history from the old account.

## Where everything lives
| What | Location |
|---|---|
| Rules and gates | `AGENTS.md` (canonical), `CLAUDE.md` |
| Lead state, decisions | `notes/memory.md` (CURRENT STATE block at top), `notes/todo.md`, `notes/runs.md`, `notes/lessons-learned.md` |
| Project index | `docs/report/project_log.md` |
| Latest work (Nov 2026) | branch `claude/ecstatic-carson-c3e4f9` of this repo, `artifacts/reports/shocksat_burst_survey_foundation_20261116/` (start at `packet.md`) |
| Work from 2026-07-23 to 2026-08-12 (never pushed here) | PRIVATE repo `andrewvoss8-boop/bayesx-disk-backup-2026-10-02`, branch `claude/ecstatic-carson-c3e4f9`, folder `recovered_text_extract/` (text only, 3,564 files, SHA-256 manifest) |
| Full disk backup (16.5 GB, binaries included) | same private repo, release `backup-2026-10-02`, 31 parts `bayesX.tar.gz.partNNNN`; `RESTORE.md` and `SHA256SUMS.txt` are release assets |

The new account needs GitHub access to both repositories (the backup one is private). `main` of this repo stops at 2026-07-22; merge or check out `claude/ecstatic-carson-c3e4f9` to get the November work.

## Research state in one page

Goal (`notes/project_vision.md`): a trustworthy Bayesian digital twin of aerospace structures, tested on NASA's ShockSat. The binding failure is predicting FRF amplitude at sensors not used for fitting.

Terminal findings up to 2026-08-12 (recovered record; read `recovered_text_extract/.../shocksat_failure_attribution_handoff_20260810/START_HERE_Plain_English_Handoff.md`):
- Frequencies fit well; amplitude does not, even in-sample: Card H median per-curve error 10.0 dB nominal vs 10.0 dB updated over 420 shock-sensor curves.
- Agent model-class selection never beat random (Card I v1.0.3: skill minus random -0.0067 ± 0.0111; Card J: no portable metric correction). These are honest nulls on a 20-candidate single-edit pool with fixed damping over 5 drives, not proof the search space is exhausted.
- A transferable mode-shape field did not beat FEM on held-out sensors (gain +0.136 vs 2SE 0.402).
- Damping is not resolvable from the 2.03 Hz hammer caches (records are 1.0 s with 0.5 s of ring-down); ring-down analysis resolves 14/16 modes at about 0.45 %.
- Handoff recommendation: get higher-quality modal data before more modeling; compare engineer vs agent vs random on a reserved test.

November 2026 work (this repo, `shocksat_burst_survey_foundation_20261116/`, checker YELLOW 14G/4Y/0R, independently reviewed):
- Candidate higher-quality data: NASA's own modal survey inside `FEM_and_CAD.zip`. Exact byte ranges are in `out/fetch_plan.json`; the plan needs 0.73 GB (burst time histories runs 78, 99, 139; run-78 FRF file; documents; 264 NASA test-vs-FEM plots).
- NASA excluded the shaker runs from its own correlation because attachment blocks mass-loaded the modes; any use must model the blocks. NASA's sensor set is weak above 150 Hz.
- Exploratory pilot (two NASA drive-point curves): NASA FEM within 2.7 to 3.1 dB of NASA's test below 150 Hz; project FEM 3.0 to 3.6 dB. Not like-for-like with the 10 dB figure; it only motivates the next test.
- At 0.125 Hz lines (8 s frames) 19 of NASA's 22 modes in 45 to 200 Hz would have resolvable damping; at 2.03 Hz none do.
- Torque sweep exists (`Test_Data_Parametric.zip`: 20 hits, 4 at each of 25 to 125 bolt torque), not yet used.
- A test on the 262 unseen NASA plots is pre-registered and hash-locked (`prereg_gated_analysis.md`, `prereg_lock.json`). Do not change its rules after seeing data.

## Blocker and next action
The old cloud environment refused `mediaex-server.larc.nasa.gov`. In the new account's cloud environment set Network access to Limited and add that host under Allowed domains (keep package managers allowed). Then, in the workspace:

```bash
bash gated_run.sh
```

It fetches 138 MB to `~/.cache/shocksat_burst_survey` (outside the repo), verifies CRCs and the frozen predictions, and scores the 262 plots. Add `WITH_TIME_HISTORIES=1` for the 589 MB burst files, then evaluate gates F1 to F5. Still to build: a decoder for NASA's `.ati`/`.afu` binaries (a probe exists) and a polyreference damping estimator.

## Environment notes
- `bash run_all.sh` replays the workspace offline; it needs numpy, scipy, matplotlib, pillow, requests, openpyxl (set `PYTHON=` to an environment that has them).
- Raw data are never committed; large binaries come from NASA or the backup release.
- To pull more files from the backup without writing the full tarball, see `recovered_text_extract/stream_parts.sh` and the pattern files beside it.
