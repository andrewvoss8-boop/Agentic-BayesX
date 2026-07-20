# decisions_log — EXACT-EVIDENCE COMPLETION (shocksat_fullspec_exact_completion_20260716)

Runner: Claude Code (autonomous, runner card A dispatched by Andrew 2026-07-16).
Workspace: `artifacts/reports/shocksat_fullspec_exact_completion_20260716/`.

## D0 — Re-grounding, goal, next action, open ambiguities (2026-07-16, session start)

**Re-grounded from (read, not remembered):** `AGENTS.md` (all gates), `docs/compute_protocol.md`,
the study `shocksat_full_spectrum_frf_20260714/findings.md` (incl. the 2026-07-16 POST-REVIEW CORRECTION
box) + `decisions_log.md` D11–D17, the review `shocksat_fullspec_review_gpt56_20260716/review.md`, and the
repair `shocksat_full_spectrum_frf_repair_20260716/out/verdicts.json` + `repair_summary.json`.

**GOAL:** close the three cheap evidence holes the accepted review (D17) left open:
- T1: an honest, leakage-free arm-C exact score (per-fold shape-MAP refits on the enriched basis).
- T2: an exact re-rank of ALL 28 loop candidates; S2 reported under BOTH selection conventions.
- T3: corrected, finiteness-hardened verdicts + figures that no longer carry the defective collector output.

**LAST DECISION:** none yet (session start). Card accepted as written; no deviations requested.

**NEXT ACTION:** write `priority_deliverables.md` + `question_framing.md`, then `check.py`, run it RED on the
empty workspace, SHA-lock it, and only then start science.

**OPEN AMBIGUITIES (resolved by assumption, stated here per AGENTS Priority/Clarification Gate — the card
says run autonomously, so I do NOT block on these; each is recorded so a reviewer can overrule):**
1. *Which 28 candidates?* `out/candidate_specs/` holds **29** specs but `out/query_log.jsonl` holds **28**
   rows (14 agent + 14 random). The extra spec `wr3_rnd001` is a recorded build failure
   (`out/random_duds.jsonl`: "split rule selects no elements of pid 102"). **Assumption:** the card's "all 28
   loop candidates" = the 28 rows of `query_log.jsonl`; `wr3_rnd001` is excluded-with-reason (it never
   produced a package or a screening score, so it has no rank to re-order).
2. *Writes into read-only workspaces.* The study's `enrich_wide.enrich()` saves packages into
   `wide_candidates.PKGD` and logs eigensolves into the STUDY's `out/eigensolve_log.jsonl` — i.e. importing
   it read-only is not enough; calling it would WRITE into the reviewed workspace. **Decision:** monkeypatch
   `wide_package.PKGD`, `wide_candidates.PKGD` → MY `data/packages_wide/`, `wide_candidates.log_eig` → MY
   `out/eigensolve_log.jsonl`, and `wscore_wide.SLOG` → MY `out/score_log.jsonl`, in a single shim
   (`code/_common.py`). Base packages are reached via **symlinks** into my package dir (a symlink is a write
   in MY workspace only; the study's bytes are never touched). My checker greps my own code for study-path +
   write-mode, and I hash the study code I reuse into `REUSED_code.sha256` before/after to prove it is
   unmodified.
3. *Arm-C exact θ convention.* The enriched package folds θ_MAP into the projected blocks, so scoring is at
   `θ = ones(9)`. T1 therefore refits the shape field with `map_fold(pkg_enr, ones(9), fold)` — the shape
   field is re-optimized against the EXACT basis, θ held at the study's MAP (folded in). This matches the
   card ("θ=ones convention") and the study's D14/D22 exact-basis rule.
4. *Paired SE convention.* Card-specified: std of the per-fold deltas / √4 (`np.std(..., ddof=1)/2`), the
   same convention the repair used (verified: repair S2 SE 0.0093785 reproduces from its 4 per-fold deltas).
5. *T2 "exact score" for candidates.* The study's loop scored candidates at their own θ_MAP on a θ=1 basis
   (screening). "Exact" = enrich the candidate's OWN package at its θ_MAP (k=200 own-space solve, θ folded
   in) and score at θ=ones — identical machinery to `rescore_freeze.score_exact`, applied to all 28 rather
   than the 2 winners.

**SAMPLER DECISION (AGENTS Sampler Rule/Decision — stated explicitly):** **no sampler runs in this card.**
NUTS/HMC remains the project default for Bayesian updating, but this card computes *deterministic* quantities
only: L-BFGS multi-start MAP refits of a shape field, exact eigenbases, and held-out FRF scores. It makes NO
new posterior/uncertainty claim; it completes held-out *point* evidence for arms whose posteriors the study
already reported as YELLOW/non-converged (arm-B worst R-hat 360.6 / ESS ~2; arm-C fold-1 R-hat 13.95 /
ESS 2). Any MAP-derived number I report is a deterministic optimizer result, not a posterior summary, and is
labeled that way on every figure and in `verdicts_final.json`.

**VAULT:** not touched. Dev drives only (`m_xpos_990x`, `m_zpos_990z`, `m_ypos_990y`, `m_zpos_900z`). No
vault read, no `+XY`, no `VAULT_FREEZE.sha256` in this workspace — `wscore_wide.score_vault_wide` would raise
without it, and I never call it.

**COMPUTE:** CPU (Mac, float64) per `docs/compute_protocol.md` §1 — the eigensolves are sequential sparse
shift-invert solves, not parallel-shaped, so no GPU. `OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1` pinned per
the compute protocol (small dense eigh/posterior math thrashes with multi-thread BLAS). T2's ~28 eigensolves
run **detached and SERIALLY** (16 GB box; parallel eigensolves thrash to swap — study D11 lesson), each
resumable (an existing package `.npz` is skip-loaded) and each logged to `out/eigensolve_log.jsonl`.

## D1 — T1 COMPLETE: the honest arm-C exact score REVIVES the number but the "lead collapse" reading was wrong (2026-07-16)

**Ran:** 4 independent per-fold shape-MAP refits on the enriched exact basis `A0_wide__enr`, each on that
fold's 3 TRAIN drives only (`arm_c_score.map_fold` reused read-only, multi-start 4, seed 20260715). Leakage
audit passed: 4 distinct MAP files, no fold trained on its own drive. ~4 s/fold (the card budgeted 1–2 h;
the L-BFGS on 108×19 = 2052 shape parameters is simply fast). No sampler.

**Result (sub-200 Hz, P1′ fold-mean):**
- honest arm-C exact = **0.1595** (vs the study's withdrawn LEAKY 0.1570 — a difference of only **+0.0025**)
- vs A1-exact 0.1137 → **delta +0.0458 ± 0.0361** (per-fold [+0.0132, −0.0343, +0.0721, +0.1322])
- **S1 NOT MET** on both criteria: +0.0458 < +0.05, and the delta is 1.27×SE < the required 2×SE (0.0722).
- 200–500 Hz: C 0.0314 vs A1 0.0335 → −0.0021 ± 0.0244 (no effect; C is a sub-200 shape lever, not a
  mid-band amplitude lever — consistent with the study's H1/H3 split).

**TWO FINDINGS, and the second corrects the study's *reading* rather than its number:**
1. **The leak barely mattered numerically** (0.1570 → 0.1595). The review was still right to withdraw the
   number — provenance was invalid and *could* have mattered — but the honest refit does not overturn it.
   Mechanism: fold-1's MAP being the WRONG map for the other 3 folds (a mismatch penalty) roughly cancelled
   the leak's flattery. This is worth carrying as a lesson: a leaky number is not automatically an inflated
   number, and "the number barely moved" is not a defence of leaky provenance.
2. **"On the exact basis C's lead collapses (0.189→0.157)" is WRONG as stated** — and this is NOT something
   the review caught. C's *absolute* score does drop on the exact basis (0.189 → 0.1595), but **A1 drops
   too** (0.145 → 0.1137). C's **lead over A1 is essentially unchanged: +0.044 screening → +0.0458 exact.**
   The exact basis deflated BOTH arms, not C's advantage. What actually fails S1 is **precision, not
   collapse**: the per-fold deltas spread from −0.034 to +0.132, so 2×SE (0.072) exceeds the mean.
   Corrected statement: *amplitude-trained shape inference buys a real, basis-robust ~+0.046 sub-200 gain
   over A1 that is too imprecise across drives to clear the pre-registered bar.*

**Q1 ANSWER (pre-registered readings): "C DENTS"** — delta > 0 but misses S1. The shape wall stands, dented,
now on leakage-free evidence. The study's H1 verdict (wall stands, dented) SURVIVES; its supporting
sentence about C collapsing does not.

**Caveat carried:** this is a deterministic MAP point estimate. Arm C's posterior is unresolved (fold-1 NUTS
R-hat 13.95, ESS 2; D13), so "C gains +0.046" is an optimizer result, not a posterior statement. The fold
spread is also large enough that the honest summary is "drive-dependent benefit", which is exactly the Q1
falsifier I pre-registered — reported, not hidden in the mean.

**NEXT:** T2 running detached (28 eigensolves, ~6.5 min each ≈ 3 h).

## D2 — CORRECTION TO MY OWN D1: the leak was worth +0.082; a SECOND defect (basis mismatch) cancelled it (2026-07-16)

**D1 claimed "the leak barely mattered numerically (0.1570 → 0.1595)". That reading was WRONG** and I am
correcting it before it reaches the packet. What follows is an artifact-backed decomposition
(`out/leak_probe.json`, reproduced by `/tmp/leak_probe2.py`-style diagnostic; both probes re-run from the
saved MAPs).

**What I did:** re-ran the study's arm-C exact path three ways on the same folds/scorer:
| # | path | sub-200 |
|---|---|---|
| 1 | **the study's actual path** — THEIR fold-1 MAP (fit on the θ=1 basis) applied to the ENRICHED basis | **+0.1570** ← reproduces their reported 0.1570 **exactly** |
| 2 | **leak only** — MY fold-1 MAP (fit ON the enriched basis) applied to all 4 folds | **+0.2417** |
| 3 | **honest** — per-fold MAPs, each on the right basis (T1) | **+0.1595** |

**Decomposition: leak = +0.0822. Basis mismatch = −0.0847. Net = −0.0025.**

**The study's exact arm-C number carries TWO defects, not one:**
1. **The leak (review C6, already known):** fold-1's MAP applied to all 4 folds inflates the fold-mean by
   **+0.0822** (per-fold inflation +0.067 / +0.081 / +0.180 on the three leaked folds). So the leak was
   NOT benign — D1's "barely mattered" was an artifact of comparing against the *other* error.
2. **A basis mismatch the review did NOT catch (NEW):** `rescore_freeze.py:78` loads the shape MAP from
   `out/armC/`, which `arm_c_score.py` fit on the **A0_wide (θ=1) basis** (r=209, 18 matched modes, r0=106),
   and applies those raw coefficients to the **A0_wide__enr (θ_MAP) basis** (r=194, 19 matched modes,
   r0=108). The raw coefficients are **coordinates in a specific eigenbasis**; the two bases have different
   eigenvectors, so this transplants coefficients between incompatible coordinate systems. It deflates the
   score by **−0.0847**. It did not crash — the arrays were merely shape-compatible enough to broadcast —
   so it produced a wrong-but-plausible number **silently**.

**Why this matters more than the arithmetic:** the study's 0.1570 was *right by accident*. Two large,
independent errors (+0.082 and −0.085) nearly cancelled, landing 0.0025 from the honest 0.1595. Had the
reviewer "sanity-checked" the leaky number against an honest one and seen agreement, they would have
concluded the leak was harmless — and the basis mismatch would still be in the codebase. **Near-agreement
between a defective and a correct number is not evidence that the defect is harmless.**

**Q1 answer is UNCHANGED** ("C DENTS": +0.0458 ± 0.0361 vs A1-exact, S1 not met) — T1 was always
basis-consistent (I refit ON the enriched basis, per the card's θ=ones convention), so this correction
touches only my *interpretation* of the study's error, not my result.

**D1's second finding STANDS and is reinforced:** "on the exact basis C's lead collapses" is wrong as
stated. C's lead over A1 is +0.044 screening → +0.046 exact (A1 dropped too). What fails S1 is precision
(per-fold deltas −0.034…+0.132), not collapse.

**LESSON (candidate for lessons-learned):** when reduced-basis coefficients are passed between bases, the
basis is part of the datum. A shape field expressed in eigenbasis coordinates is meaningless without the
eigenbasis it was fit in; any code path that loads coefficients fit elsewhere must assert basis identity
(r, matched-mode count, r0 — all three differed here and nothing complained).

## D3 — Card B (net-CG validated port) has OVERTAKEN my card's S3/S4 assumption; my locked checker cannot follow (2026-07-16)

**Discovered while writing continuity:** `artifacts/reports/shocksat_netcg_validated_port_20260716/` (runner
card B, run in parallel today, checker GREEN 10G/0Y/0R, pending Andrew review) has ALREADY made S3/S4
assessable. Its `out/verdicts_S3S4.json`:
- **N0 GREEN**: driving the ORIGINAL `netcg_qoi.py` + reduced model + reused L5 NUTS draws reproduces the
  delivered twin **exactly** (1.508 / 2.301 / 2.526, max |err| 0.0000, tol 0.05). The reference reproduction
  that review C5 said was missing is now DONE.
- **S3 YELLOW = "CANNOT-VERIFY-through-this-mapping"** (the 3 mapping variants disagree on the rule, so the
  verdict would be an artifact of the mapping choice).
- **S4 YELLOW = NOT MET / falsified** (normal-Z width 2.958 vs the 1.9 bar, coverage 0.989; change exceeds
  the MC noise floor 0.091).

**The conflict:** my card §2 T3 instructed "S3/S4 = CANNOT-VERIFY (pointer to Card B)", and my `check.py`
G05 — **SHA-locked before any science, and immutable** — RED-fails unless `S3.status == "CANNOT-VERIFY"`
and `S4.status == "CANNOT-VERIFY"`. As of Card B's result, **S4 = CANNOT-VERIFY is stale**: S4 is now
falsified on validated machinery.

**DECISION (no checker edit — the checker is immutable during a trial, AGENTS rule):**
1. `status` stays `"CANNOT-VERIFY"` in `verdicts_final.json`. This is defensible **only** with its scope
   stated explicitly, which I do: it is the status **from THIS card's evidence**, and this card produces
   **zero** S3/S4 evidence (no net-CG work, per the card and my pre-registration).
2. Every S3/S4 block carries a prominent **`superseded_by_card_B`** field with Card B's ACTUAL verdicts,
   numbers, and workspace path, so no reader can take my stale status as current.
3. `findings.md` states plainly, in the Q-answers and the limitations section, that **S4 is falsified by
   Card B** and that my file's status field is a scope artifact of a checker locked before Card B landed.

**Why not just write the true status?** Because editing a SHA-locked checker mid-trial to accommodate a
result is precisely the failure mode the harness exists to prevent, and the alternative (writing S4 = "NOT
MET" and taking a RED) would make my checker's overall RED signal *misleading* — it would flag a
non-defect. The honest resolution is: comply with the locked gate, and make the staleness impossible to
miss. **Flagged for Andrew: this is a checker-scope miss on my part** — I encoded a card assumption ("S3/S4
are unresolved") as a hard gate rather than encoding the *invariant* the card actually cared about ("this
card must not manufacture S3/S4 evidence"). A better gate would have been "S3/S4 must carry no
newly-computed numbers from this workspace".

**LESSON (candidate for lessons-learned):** do not SHA-lock a gate on the *expected value* of an external
result that a parallel card may change; lock gates on invariants this workspace controls. A checker should
constrain MY conduct, not predict someone else's finding.

## D4 — T2 THRASHED the 16 GB box; restarted with ONE CANDIDATE PER PROCESS (2026-07-16, ~16:45)

**What happened.** T2 ran all 28 candidates inside ONE long-lived python process. Candidates 1–17 took
~530–590 s each as expected. Then it degraded: `wr2_rnd001` took **11,198 s (3.1 h) — a 21x blow-up** — and
the process sat in uninterruptible disk wait (state `U`), CPU 8–100% oscillating, RSS swinging 2 GB ↔ 5.7 GB
every few seconds, with swap at **10.8 / 12.3 GB**. Classic swap thrash: each candidate loads the full model
+ sparse blocks and runs a k=200 shift-invert eigensolve, and the heap never fully returned to the OS
between iterations, so the working set grew until the box fell off a cliff. **This is the study's own D11
lesson (k=650 thrashed to swap) reappearing in a different disguise — I logged the D11 lesson in D0 and
still walked into it**, because I treated "run SERIALLY" as the whole mitigation when the real risk was
*cumulative* memory across a long-lived process, not concurrency.

**Detected by:** a routine progress check showing 17/28 unchanged for 3 hours. The card's detached-launch
gate saved the work — every candidate's record and enriched package is written on completion, so nothing
was lost.

**Response (no science changed):**
1. Killed the process. Verified state: **18/28 records intact, 18/18 enriched packages load cleanly, zero
   corruption** (`enrich()` saves only on completion, so the kill could not truncate a package). The
   in-flight candidate (`wr2_rnd002`) simply left no package — it will be redone.
2. Added `--one` mode to `exact_rerank.py`: process exactly ONE pending candidate, then EXIT, so the OS
   reclaims everything. Driver `code/run_rerank_serial.sh` loops it until `ALL DONE`, then runs the full
   pass (which skip-loads all 28 records and aggregates). Memory is now bounded by ONE candidate's working
   set instead of growing across 28.
3. `run_all.sh` updated to replay via the driver, so the replay matches what actually produced the numbers.

**Verification that the thrash did NOT corrupt the science:** `wr2_rnd001` — the candidate that took 3.1 h —
is the study's random winner R. Its self-consistency is 8.5e-8 % and its exact sub-200 is **0.16507 vs the
study's independently-computed 0.16506** (agreement to 1e-5). A slow solve is still an exact solve; ARPACK
converged to the same eigenpairs. So the thrash cost wall-clock, not correctness.

**LESSON (candidate for lessons-learned):** "run it serially" is not the same mitigation as "bound the
memory". For a long batch of heavyweight independent jobs on a fixed-RAM box, make each job a SEPARATE
PROCESS: it is the only way to guarantee the working set returns to the OS, and it costs nothing because the
jobs are already independent and resumable. Also: a job that is *alive* is not a job that is *progressing* —
monitor throughput (records/hour), not liveness. A 21x slowdown looked identical to "still running" for
three hours.
