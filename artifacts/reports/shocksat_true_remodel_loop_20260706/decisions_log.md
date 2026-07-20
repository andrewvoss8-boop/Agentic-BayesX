# Decisions Log — ShockSat TRUE Agentic Remodeling Loop (20260706)

Runner: lead agent (Fable) acting as autonomous runner, dispatched by Andrew 2026-07-06.
Card: `docs/lab/shocksat_true_remodel_loop_runner_prompt.md` (the runner prompt in this session).
Append-only. Every non-obvious resolution is written HERE before it is acted on (AGENTS.md Context/Compaction rule).

---

## D0 — re-grounding (one line, per card §1)
- **Goal:** answer ONE falsifiable question — can a closed-loop agent proposing SHAPE-CHANGING model-form
  edits from TRAIN residuals, selected on BUDGETED dev scores, beat the inherited ShockSat FEM's held-out
  per-sensor FRF prediction AND beat a random-search comparator, confirmed on a pristine vault dataset.
- **Last decision:** Andrew dispatched the card in-session; lead executes as the autonomous runner (precedent:
  composite bake-off, netcg). Patent is NOT a goal; the capability question is.
- **Next action:** finish pre-registration gate files -> SHA-lock check.py BEFORE any science -> V1-V5 mechanics
  gates -> A0 baseline -> tracks A1/A2 -> finalists+NUTS -> vault -> packet.
- **Open ambiguities:** (1) disk/vault feasibility (resolved in D1 below); (2) exact per-round proposal counts
  (budget-aware, resolved at run time, logged per round).

## D1 — VAULT feasibility / disk constraint (pre-registered fallback engaged; per card §4.1 fallback (a) and §11)
- **Observed constraint (evidence):** at run start `df -h` on the repo volume = **8.7 GiB free, 96% capacity**.
  Prior run (composite bake-off) already hit a 100%-disk incident on this machine (notes/memory 2026-06-26).
  The primary vault `Test08_ImpactHammer_990z.zip` = 626 MB and secondary `Test10_...900z.zip` = 737 MB;
  a zip + its temporary extraction + distilled artifacts must briefly coexist. 8.7 GiB is not a comfortable
  margin for a 626 MB download+unzip+distill cycle, and there is real risk of a disk-full abort mid-run.
- **Decision (pre-registered BEFORE any science, so it cannot be a post-hoc pick):** primary plan is still to
  attempt the never-downloaded `Test08_ImpactHammer_990z.zip` vault AFTER finalists are SHA-frozen, freeing
  space first and deleting the zip immediately after distillation. **If** free space at freeze time is < ~5 GiB
  OR the download/unzip fails OR distillation coherence is unusable (median coherence < 0.6 in 45-260 Hz),
  engage **card-pre-registered fallback (a): the +XY / Test04 cache (`m_xy_990xy.npz`) becomes the vault** and
  is EXCLUDED from all dev queries from the start of the run. To keep this honest and decidable now, I declare
  the Test04 exclusion **now**: dev folds run leave-one-drive-out over the **4 remaining drives** (+X/990x,
  +Z/990z, +Y/990y, +Z@900z); Test04 is touched only at the final vault-grade step. Residual risk (labeled per
  card): prior-run summaries of Test04 exist in the repo (netcg/psd_envelope), so Test04 is "held-out from THIS
  run's selection" but not "never-seen by any run" — this weaker-but-honest guarantee is stated in the packet.
  If the true never-downloaded Test08 vault succeeds, it is reported as the primary grade and Test04 as a
  secondary cross-check.
- **Why pre-register both now:** the card forbids picking the vault after seeing scores. By fixing the dev fold
  set to the 4 non-Test04 drives up front, the winner is chosen without ever touching Test04, so Test04 is a
  legitimate held-out grade regardless of which vault path the disk allows.

## D2 — reduced-basis policy (card §6 step 3 "reduced-basis trap", confirmed against reduce_model.py)
- `reduce_model.py` builds the reduced model in the FROZEN inherited 74-elastic-mode basis (K_red=Σθ_g A_g,
  M_red=I). Confirmed: this basis is valid ONLY for parametric θ-scaling candidates (family 5), where K stays
  in the original DOF space. **Any candidate that changes mesh / DOF count / connectivity (families 1,2,4, and
  family 3 when it triggers reassembly) is solved in its OWN space** — full-order sparse eigensolve, or a
  per-candidate enriched reduced basis validated <=0.3% frequency error vs full on a spot check. Never score a
  shape-changing edit in the inherited basis. Full-order eigensolve budget <= 80, logged, detached, resumable.

## D3 — thickness physics uses fe_core.py element reassembly, not a K-block modulus proxy (card §5 family 3, gate V4)
- Confirmed `fe_core.qm6_membrane` weights membrane stiffness linearly in `t` and `mitc4_bending` scales bending
  by `t**3 * bend_ratio`. A genuine per-region thickness field therefore reassembles elements with membrane ∝ t
  and bending ∝ t³ SEPARATELY (physically correct). Any candidate that only scales a K-block modulus is tagged
  `modulus` (not `thickness`) and, if it contains only scales, `parametric_only` (the proven-dead family).

## D4 — Andrew's decisions (2026-07-06, in-session): vault + disk + GO
- **Vault:** Andrew: "we don't need test 8 redownloaded" -> the pre-registered fallback (a) is now the PRIMARY
  vault: **Test04/+XY cache (`m_xy_990xy.npz`), excluded from all dev queries from run start** (as declared in
  D1 and question_framing before any science). Dev folds = leave-one-drive-out over the 4 drives +X/990x,
  +Z/990z, +Y/990y, +Z@900z. Residual-risk label stands: prior-run Test04 summaries exist in the repo, so the
  vault guarantee is "held out from THIS run's selection", not "never seen by any run".
- **Disk:** tiers 1-3 raw/download layers deleted with Andrew's approval (~9.6 GiB reclaimed, 4.4->14 GiB free;
  all git-untracked, re-derivable; distilled caches untouched). Vault-freeze disk gate no longer at risk.
- **GO:** Andrew authorized the science phase. Next: SHA-lock check.py, then V1-V5 mechanics gates FIRST.

## D5 — checker lock timing (rationale recorded before locking)
- check.py was written against the full pre-registered artifact schema and verified to produce the honest
  pre-science RED baseline (2G/10R). It is SHA-locked NOW, before any science artifact exists, and is IMMUTABLE
  for the rest of the trial. Any change would void the run (card §11: no fallback for integrity violations).

## D6 — θ_MAP objective, per-fold gain, and diagnosis-field reading under LODO (pre-registered before A0)
- **θ_MAP (per candidate):** MAP of the proven S0 modal-frequency likelihood (rmodel.py conventions):
  lognormal θ prior sd 0.25 per group; Gaussian likelihood on paired eigenvalues, sd = 5% of target λ;
  frozen Hungarian pairing computed ONCE per candidate at θ=1. Fit data = the .ash modal survey, which is
  TRAIN in every fold (drive-independent -> one θ_MAP per candidate, folds differ only in the gain). This
  satisfies "θ fit ONLY on train" with zero dev leakage and keeps the loop tractable.
- **Gain:** ONE global real gain per fold = mean over the fold's 3 TRAIN drives of mean(log|H|_meas - log|H|_pred)
  (closed form, no LSQ). P1 correlation is gain-invariant; the gain only feeds P2 (dB).
- **Diagnosis fields under leave-one-drive-out:** with 4 loop drives each drive is dev in exactly one fold, so
  "train-side fields" cannot mean "fields from drives never used as dev" (no such drive exists; the card's own
  5-drive design has the same property). Reading adopted: the proposal loop may read residual FIELDS on the
  4 loop drives (computed at the drive-independent θ_MAP), NEVER on the vault; dev evaluations return scalars
  only; the protections against steering-leak are the hard query budget + the untouched vault. Recorded as the
  only coherent reading of card §4.1/§6 under LODO.

## D7 — full-order eigensolve allocation (card §6 cap = 80 total)
- Agent track <=32, random track <=32 (equal-compute fairness for S2), V-gates + reduced-basis spot-checks <=16.
- Only mesh/DOF/connectivity-changing candidates require own-basis full solves (D2). Family-2 (region split,
  no mesh change) and family-5 (scales) may use the inherited basis WITH >=2 full-order spot-checks (<=0.3%
  matched-frequency error) or they are not dev-scored. Every solve appended to out/eigensolve_log.jsonl.

## D8 — mechanics-gate scopes (pre-registered)
- V1 = re-assemble ALL 27 PID blocks with THIS run's code path; require max relative block deviation <=1e-9 vs
  the stored Card-D blocks AND full eigsh eigenvalues <=1e-8 relative vs matrices/eigvals.npy.
- V2 = free-free 6 RBM at machine zero on a REFINED dish submodel (new-mesh drilling/constraint check).
- V3 = dish 2x refine via THIS run's general refine action (hanging-node MPC ties active if quad/tria edges
  demand them): matched-mode |df| <= 0.3% and global MAC shift <= 0.01 (reference: Card D +0.0016).
- V4 = strip patch test, nu=0: t x2 => membrane stiffness x2 (+-2%), bending x8 (+-3%, thin-strip limit).
- V5 = unit test: frozen pairing invariant under a +10% model frequency shift (pairs identical), while greedy
  re-pairing on the shifted model changes >=1 pair (the churn we forbid).
- Damping convention for all FRF predictions: viscous 2jζω_iω (netcg/rmodel convention), ζ=0.01 (ledger A1).

## D9 — screen proxy + track bookkeeping (pre-registered before any screening)
- **Screen proxy (NO-sampler, train-side only):** proxy = mean matched MAC (frozen pairs, shapes at θ_MAP)
  − 2.0 × mean matched |Δf|/f + 0.02 × n_matched. Higher is better; the n_matched term penalizes edits that
  destroy pairings instead of silently dropping them. Labeled everywhere as a proxy, never as the metric.
- **Query-log tracks:** 'baseline' (A0 θ_MAP), 'reference' (inherited θ=1), 'agent', 'random', later 'vault'.
  Only 'agent'/'random' count against the 60-query budgets (locked checker counts exactly those two).
- **Dev-scoring order:** A0 FIRST (card §4.2) so all agent/random proposals are graded against a frozen bar.

## D10 — V2 ARPACK stall incident + fix (compute incident, no science impact)
- First V2 attempt stalled (~89 CPU-min, no progress): eigsh k=10 (ncv=21) with tol=0 on the free-free
  refined-dish pencil — subspace too small for the 6-fold degenerate zero cluster; ARPACK spun at machine
  precision. Fix: k=20, ncv=90, tol=1e-8, sigma=-1e3 (V1's k=80 run had converged for the same reason).
  mech_gates.py is NOT a locked file (only check.py is); V2 had produced no result yet, so nothing is revised.
  Lesson for candidate solves: NMODES=80 keeps ncv large; keep tol default there (V1 converged in ~6 min).

## D11 — V3 failure triage (fix-first in progress; scoped blocking)
- V3 FAILED as specified: the dish-2x refined model inserts FOUR ~62.7 Hz modes absent in A0 (all other modes
  realign; matched-MAC delta +0.0024 passes). The inserted modes have ~zero participation at every survey node
  and sensor (ash/sens rms ~1e-3..0.5 vs ~20 for physical modes) = localized, instrument-invisible. Forensic
  (code/v3_forensic.py, detached) is resolving WHERE they live via per-region kinetic-energy fractions.
- Scoping: V3 gates the REFINE family only (V1/V2/V4/V5 all PASS and cover assembly, T-building, thickness
  physics, pairing — the paths A0/split/scale/connect use). Per card §11 (blocked ≠ stopped), A0 baseline
  scoring proceeds now; NO refine-family candidate may be dev-scored until V3 passes (checker enforces V3
  pass for GREEN regardless).
- Also fixed pre-science: n_rbm threshold 1 Hz -> 10 Hz (numerical drilling-penalty RBMs sit at 0.4-1.2 Hz;
  the 1 Hz counter said 5 and would have wrongly rejected every candidate as a mechanism).

## D12 — pairing/likelihood hygiene: exclude unobservable modes + low-MAC pairs (uniform, pre-P1)
- **Root cause found for V3 (forensic, code/v3_forensic.py + logs/v3_forensic.log):** the model carries a
  4-mode ARTIFACT cluster = accelerometer-mount bush rotational stiffness (k_rot 1e7) reacting against the
  shell DRILLING DOF whose only stiffness is the K6ROT penalty (∝ element area, by construction). In the
  inherited mesh the quartet sits at 124.4-125.2 Hz (Card D's known "degenerate cluster" swap artifact);
  dish 2x refinement quarters the attached element area -> penalty /4 -> artifact modes /2 -> 62.68-62.70 Hz
  (ratio 2.00 observed = exact). Instrument participation ~0 (sens-rms 0.02-0.59 vs median ~10). These are
  penalty-scale artifacts, present in the INHERITED model too — not a refinement bug (V2 free-free clean).
- **Contamination found:** A0's frozen pairing assigned test mode 9 (137.25 Hz) to artifact mode m8
  (MAC 0.425) — an unobservable spatial alias feeding the θ frequency likelihood; other junk pairs exist at
  MAC 0.03-0.28.
- **Rule (uniform for A0 + every candidate + both tracks, decided BEFORE any dev P1 was read under either
  rule):** (a) model modes with sensor-participation rms < 10% of the median sens-rms are EXCLUDED from
  pairing (unobservable/artifact modes are not evidence); (b) only pairs with MAC >= 0.3 enter the θ_MAP/NUTS
  frequency likelihood (Card D's ">0.3 well-paired" convention). The FULL Hungarian table is still stored
  (frozen); the likelihood/P2 use the filtered subset. Superseded A0 query_log records (if any landed from
  the first baseline launch) stay append-only; verdicts.py uses the LAST record per (cid, track).
- Diagnosis figures/tables will show the artifact cluster explicitly so it is not mistaken for physics.

## D13 — V3 re-metric (cross-model matched comparison; supersedes D8's index-aligned df)
- D8's V3 metric compared eigenvalues BY INDEX; a 4-mode artifact insertion shifts all indices and produces
  a fake 40% "df". Re-metric: Hungarian match A0<->refined on cross-MAC over the 228 obs DOFs, restricted to
  PARTICIPATING modes (rule D12a), then max |df| over matches <= 0.3% and |Δ mean matched-to-test MAC| <= 0.01
  (unchanged). This is the honest "refinement moves matched modes only at convergence level" test. mech_gates
  V3 section re-runs (reusing the already-solved v3 package; no new eigensolve); out/mech_gates.json V3 entry
  is overwritten by the re-run with the failure + re-metric history preserved in this log and the packet.

## D13a — exact V3 re-metric thresholds (set before the re-run; aligned to the Card-D reference null)
- Card D's own dish-refine null was "median Δf 0.006%, 36/38 modes < 0.1%, ONE genuine −2.4% shift on a
  10%-dish-participation mode" — so a max-|df| 0.3% gate contradicts the very reference it cites (genuine
  isolated dish-mode convergence shifts are EXPECTED; this run also refines the 336 dish trias, which Card D
  did not). Pass rule: median |df| <= 0.1% AND frac(|df| > 0.5%) <= 10% AND |Δ mean matched-to-test MAC| <=
  0.01 AND >= 45 cross-matched participating modes (cross-match: MAC >= 0.5, |df| <= 5%). V5 re-run under the
  D12 pairing for consistency (cheap; same mechanism).

## D14 — round-1 proposals authored + builds launched (session 2)
- 16 agent proposals (out/proposals_r1.json) authored from diagnosis_r0 + Card D, each with evidence tag:
  a01/a02 bottom-box face+bulkhead splits; a03/a04 weld effective-thickness ±(t,t³); a05/a06 bolted-joint
  RBE2->spring compliance (56 spiders @z18.4, NEVER touched by any prior campaign) soft/stiff bracket;
  a07 mount spiders, a08 dish-mount spiders soften; a09/a10 top-box near-joint/near-bulkhead splits;
  a11 refine top bulkhead+welds(202,204,206), a12 refine plates(501); a13 bolt+tb-split combo; a14 plates
  split; a15 parametric-only control (top_box x0.9); a16 both bottom-box splits combo.
- Random track: out/proposals_random.json (60 specs, seed 20260706, 32 full-solve cap; rnd004 build-fails =
  a degenerate random split that selects 0 elements = honest random dud, logged, unscored).
- Resumability confirmed: session-1 teardown killed both build queues mid-run; relaunch skipped all completed
  packages and continued (loop.py checks data/packages/*.npz). Budget at relaunch: 11/80 eigensolves.
- NEXT after builds: screen (D9 proxy) both tracks -> dev-score top-12 agent (round 1) + top random within
  budget -> spot-check split/scale finalists (D7) -> rounds 2-3 from round-1 evidence -> finalists+NUTS -> Q/H
  -> freeze -> vault(Test04) -> verdicts. All dev queries in out/query_log.jsonl (budget 60/60; A0 done, 0 used).

## D15 — wall-time reality + track scheduling (no protocol change)
- Connect-family full solves take ~14 min (a07 863s, a08 851s): RBE2 release + soft springs (k~1e6) create a
  dense low-frequency spectrum near the shift-invert sigma; refines ~6-8 min; splits/scales/thickness reuse
  the inherited basis (seconds). Random track's 32 full-solve candidates => multi-hour background job.
- Scheduling (NOT a protocol change): the AGENT arm (primary) is advanced to completion first (screen -> dev ->
  rounds 2-3 -> finalists -> NUTS), while the RANDOM arm builds/scoring runs in the background. The vault
  FREEZE waits until BOTH the agent finalists and the random-best are dev-scored (freeze set includes
  random-best + A0). Budgets and seeds unchanged; equal full-solve CAP (32/32) unchanged. Fairness for S2 is
  preserved: identical action space, identical <=60 dev-query budget, identical scoring.

## D16 — refine size guard (uniform build-robustness; not a result change)
- Random draw rnd006 refined pid 201 (whole top box, 26418 quads) -> ~112k new elements -> ~1M-DOF eigensolve
  that hung the random queue ~112 CPU-min at 5 packages. Added a uniform guard in build_candidate: total
  refined quads > 8000 -> raise (dud, logged to build_failures.jsonl), same handling as rnd004's empty split.
  Agent's largest refine (a11 = 202+204+206 = 5664 quads) is UNDER the cap -> agent track unaffected; all
  already-built agent packages unchanged. This is honest: a refine that 4x's an entire substructure is a
  resource bomb, not a targeted remodel. actions.py is not a locked file; the check.py grep audits loop.py
  only. Random build relaunched (resumes; rnd006 now fails fast). D15 scheduling unchanged.

## D17 — finalist rule + round-3 close (before finalists picked)
- Parametric-only candidates are excluded from the finalist set (they are pre-registered CONTROLS; card §5
  requires parametric_only reported separately). Finalists = top-3 SHAPE-CHANGING agent candidates by dev P1:
  a16_bb_splits_combo (+0.016), c06_tb_xface (+0.013), a04_welds_t074 (+0.010). a16/c06 are reduced-basis ->
  spot checks (D7) must pass before freeze; a04 is own-space. Freeze set = finalists + random-best + A0.
- Round-3 ceiling probe result recorded in out/round_r3_summary.md: maximal split freedom NEGATIVE
  (over-parameterized theta_MAP overfits .ash at held-out cost); controls ≈ best shape edits throughout.

## D18 — spot-check FAILURES on reduced-basis finalists -> enriched re-build (card-compliant remedy)
- Spot checks (full solve at θ_MAP vs reduced prediction): a16 0.66%, b11 0.77%, c06 2.23% max relative
  frequency error — ALL exceed the pre-registered 0.3% gate. Cause: split-candidate θ_MAPs run to ~1.7/0.7 on
  the new sub-region knobs, rotating true mode shapes out of the inherited θ=1 span (the enrich_basis lesson;
  the reduced-basis trap caught by our OWN gate). Consequence per D7: these candidates' reduced dev scores are
  demoted (documented bias), and they may NOT be frozen as finalists on those scores.
- Remedy (card §6: "per-candidate enriched reduction validated <=0.3%"): for finalists a16 and c06 — ONE full
  eigensolve at the candidate's θ_MAP; basis = M-orthonormal POD of [inherited θ=1 elastic basis ∪ θ_MAP
  elastic modes]; blocks/rows re-projected; θ_MAP re-fit; validation = enriched-basis eigenvalues at the OLD
  θ_MAP vs the just-computed full solve (free, honest ≤0.3% check); re-dev-scored as new query records
  (cids *_enr, agent track — budget goes 34 -> 36/60). NUTS re-run on the enriched packages.
- Uniformity check: A0 gets the SAME full-solve-at-θ_MAP spot check (its θ_MAP is milder, 0.90-1.31); its
  error magnitude is reported next to the candidates' so the 0.3% gate is applied with context, not selectively.
- Non-finalist reduced candidates (all split/scale dev scores) carry the documented bias caveat in the packet;
  none of their margins (±0.016 max, inside ±0.03-0.07 noise) could cross the S1 bar (+0.05) under any 0.7-2.2%
  frequency correction, so the round conclusions are unchanged.

## D19 — θ_MAP multimodality discovered; multi-start re-fit for the DECISION-RELEVANT leaders (pre-committed)
- Evidence: b04_ctrl_bb_scale (bottom_box x0.90) and rnd003 (x0.9085) are near-identical model classes but
  L-BFGS-from-zeros landed in DIFFERENT basins (eff. bottom_box 0.969 vs 1.026; f1 53.76 vs 55.27 Hz), and
  their dev P1 differ by 0.035. The 9-param modal-frequency MAP is multimodal; single-start basin choice is a
  lottery that currently CONFOUNDS S2 (random's best = a lucky basin, not a better model).
- Remedy (uniform, deterministic, fit uses .ash ONLY -> no dev leakage): θ_MAP becomes multi-start
  (start 0 + 4 lognormal prior draws, fixed seed 20260706; keep lowest NLP). Applied to: A0 (baseline track,
  uncounted) + the top-5 per track + the enriched finalists — re-scored as NEW budget-counted query records
  (agent -> ~39-41/60, random within 60). The FULL leaderboards keep the original single-start protocol
  (documented); the packet reports both. PRE-COMMITTED: S1/S2 verdicts use the multi-start records whatever
  they say; the basin story is reported either way.
- verdicts.py fixed to use the LAST record per (cid, track) (append-only supersede convention, D12).

## D20 — corrected leaderboard + verdict-rule clarifications (recorded BEFORE any vault access)
- Multi-start corrected scores: A0 0.2243 (down from 0.2341 — the lowest-NLP basin fits .ash better and
  predicts held-out FRF WORSE: the freq-fit ⊥ FRF-corr disconnect inside the baseline itself);
  b04 ctrl (bottom_box x0.90, PARAMETRIC-ONLY) 0.2746 = run-wide best (+0.0503, ≥2xSE — numerically at the
  S1 dev threshold); rnd003 (random, parametric-only) 0.2628; b05 ctrl 0.2482; a04 (shape, thickness) 0.2426.
- **S1 rule (per card §0/§5 + D17):** the S1 "agent-track winner" must be a SHAPE-CHANGING candidate
  (parametric-only candidates are the proven-dead family, "reported separately"; the question under test is
  shape-changing remodeling). Parametric-only dev-threshold passes are reported LOUDLY but do not constitute
  the S1 claim. verdicts.py implements the exclusion by reading each candidate's spec ops (all-scale = excluded).
- **S2 rule:** the pre-registered letter ("agent-track winner's dev P1 > random-track best's") makes no family
  exclusion on either side -> S2 gate uses raw best-vs-best INCLUDING parametric candidates (currently b04
  0.2746 vs rnd003 0.2628). The capability-relevant SHAPE-ONLY comparison (agent shape-best vs random best)
  is reported alongside in verdicts.json and the packet — currently the agent's shape candidates LOSE to
  random's parametric draw. Both are stated; no claim stronger than either.
- **Freeze set extended (before vault):** 3 shape finalists + b04 (parametric control, its dev-S1-level pass
  deserves the vault test) + random-best + A0. One vault grade pass for all frozen models (touched once).
- **Bar-softness finding:** b04 = the SAME 9-knob family as A0 with a shifted prior center beating A0 by
  +0.05 on dev means the A0 bar itself is soft at the ±0.05 scale under prior re-centering — the S1 margin
  threshold is comparable to the family's own calibration wobble. Reported as a core honesty caveat.

## D21 — A0 fails the same spot check (0.69%) -> enriched baseline bar (uniformity)
- A0's own θ_MAP sits 0.69% (max, in-band) off the true full-order frequencies in the inherited basis — the
  SAME magnitude as a16's 0.66% failure. The reduced-basis bias is family-uniform, not split-specific
  (c06's 2.2% was genuinely worse). Consequence: the S1 bar must be the ENRICHED A0 (package A0_enr, same
  union-POD remedy), re-scored on the baseline track (uncounted); verdicts.py uses the LAST baseline-track
  record as the bar regardless of cid. Both A0 and A0_enr go into the freeze set (labeled) so the vault
  reports the biased-vs-exact baseline pair transparently.

## D22 — uniform exact-basis rule for the FREEZE set (before vault; last basis decision)
- Bar cascade: A0 0.2341 (single-start, biased basis) -> 0.2243 (multi-start, biased) -> **A0_enr 0.2152**
  (multi-start, exact). Each accuracy improvement to the baseline's own calibration LOWERED its held-out P1:
  fitting the .ash frequencies better predicts held-out FRF worse, coherently (in-family overfitting).
- Since basis bias INFLATES P1 (evidence above and a16/c06 enrichment drops), comparing biased leaders to the
  exact bar would flatter them. Rule: EVERY frozen model is evaluated exact-basis. b04_ctrl_bb_scale and
  rnd003 (scale family, biased) get enriched rebuilds + re-scores (b04_enr agent-track -> 40/60 agent;
  rnd003_enr random-track -> 57/60 random). Freeze set becomes the *_enr versions throughout (plus original
  A0 for the bias-pair report). a04 is own-space at θ=1 but its θ_MAP≠1 evaluation carries the same class of
  bias -> a04 ALSO gets an enriched rebuild (a04's own model M/K differ from baseline: enrichment must solve
  ITS full model at θ_MAP — enrich_candidate currently supports split/scale-only reassembly of the BASELINE
  mesh; a04 (thickness) needs its own blocks. Implemented via its stored own-space package + one full solve of
  ITS assembled K(θ_MAP): extension of the same pattern.)

## D23 — verdict winner-selection = the freeze set (exact-basis); gates fail under EVERY reading
- The S1/S2 "winner" labels must come from the exact-basis freeze set (the models actually vault-graded);
  un-enriched single-start records (e.g. b11 0.2408, b05 0.2482) carry the documented +0.01-0.07 evaluation
  inflation and no vault numbers. verdicts.json also reports the raw whole-track bests with that caveat.
- No outcome depends on this choice: under EVERY candidate reading (raw, corrected, freeze-set), S1 fails
  (all dev margins <= +0.026 << +0.05), S2 fails or ties-within-noise (random rnd003_enr 0.2389 >= agent best
  exact 0.2376; diff 0.0013 ~ 40x below fold noise), and S3 fails (Q shear coverage < 0.95 for every graded
  arm; LMO widen ~1.07 passes). The pre-registered claim is FALSIFIED on all three gates under all readings.
- Vault (graded once): all frozen models 0.44-0.50 vs dev 0.20-0.24 (the +XY location is systematically
  easier: dev-vs-vault gap ~ -0.22 to -0.27 for every model, incl. baselines -> a location effect, not a
  generalization win); original A0 (0.4761) again beats its own exact-basis version (0.4377) out-of-sample =
  the "better .ash fit -> worse held-out FRF" disconnect confirmed on the vault.
