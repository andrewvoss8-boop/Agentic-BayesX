# Human-Review Packet — ShockSat TRUE Agentic Remodeling Loop (2026-07-06 → 07-08)

**HEADLINE (copied in spirit from `out/verdicts.json` + `checker_report.json`; never stronger):**
**The pre-registered claim is FALSIFIED on all three gates.** A closed-loop agent proposing genuinely
shape-changing FEM edits (true refinement, region splits, physical t/t³ thickness fields, RBE2→spring joint
compliance), steered by train-side diagnosis and budgeted dev scores, did NOT improve the inherited ShockSat
FEM's held-out per-sensor FRF prediction beyond its own calibration noise (S1), did NOT beat an equal-budget
random search (S2: tie within noise, letter-fail by 0.0013), and no graded arm passed the net-CG coverage
hard gate on shear (S3). This is the honest, evidence-backed outcome of the capability question — reported
as a falsification, not a pipeline failure. The pipeline itself passed every integrity gate.

Replay: `bash run_all.sh`. Checker: `check.py` (SHA `d9cb1acd…`, immutable; `checker_report.json` is the
status source of truth). All decisions: `decisions_log.md` D0–D23 (append-only).

## 0. First-pass method summary
- **Question (pre-registered, §question_framing.md):** can a CLOSED-LOOP shape-changing remodeling agent beat
  (a) the inherited FEM and (b) equal-budget random search on held-out per-channel FRF log|H| correlation,
  confirmed on a vault dataset touched once?
- **Model form:** full 406k-DOF NASTRAN-parsed ShockSat FEM (QM6+MITC4 shells, CBUSH, CONM2, RBE2), element
  pipeline reused read-only from Card D; V1 reproduces its blocks bit-exactly, eigenvalues to 1.15e-9.
  Candidates = JSON edit specs over families {refine, split, thickness, connect, scale}; mesh/DOF/
  connectivity-changing candidates solved FULL-ORDER in their own space (never the frozen inherited basis).
- **Likelihood / fitting (selection):** θ_MAP of the S0 modal-frequency posterior (lognormal prior sd 0.25;
  Gaussian on paired eigenvalues, sd 5%; FROZEN Hungarian pairing per model, unobservable modes excluded
  D12) + ONE global gain per fold. NO per-mode/per-channel amplitude fitting anywhere in selection
  (checker-audited). θ_MAP is multi-start deterministic (D19). Plain English: each candidate's stiffness
  knobs are tuned to the 33-mode survey only; it is then asked to predict ~90 accelerometer FRF curves for a
  drive location it never fitted.
- **Data:** TRAIN = 33-mode .ash survey (every fold); DEV = leave-one-drive-out over 4 drives (+X, +Z990,
  +Y, +Z@900), scalar scores only, hard budgets (agent 41/60, random 57/60 used; every query in
  `out/query_log.jsonl`); VAULT = Test04/+XY cache, excluded from all selection since run start, graded ONCE
  after `VAULT_FREEZE.sha256` (Andrew declined the Test08 re-download; residual risk that prior-run Test04
  summaries exist in the repo is acknowledged — "held out from THIS run's selection", not "never seen").
- **Inferred / fixed / not inferred:** θ per group (NUTS for finalists: 4 chains, x64, ALL converged,
  worst R-hat 1.004 / ESS 701 / 0 divergences); fixed ζ=0.01, pairing, band 45–260 Hz, free-free BC;
  deliberately NOT inferred: per-mode amplitudes/phases (anti-LSQ rule), input level (absorbed in gain).
- **Metric P1:** median per-channel log10|H| Pearson correlation, 45–260 Hz, fold-averaged with spread;
  noise-floor rule: reportable margins must be fold-averaged AND ≥ 2× the paired-fold SE.

## 1. Verdicts (out/verdicts.json; winner selection = the exact-basis freeze set, D23)
| gate | result | numbers |
|---|---|---|
| **S1 improvement** | **FAIL** | best shape candidate a04_enr (welds t×0.74): dev margin **+0.022** vs A0_enr (needs ≥ +0.05 and ≥ 2×SE_paired = 0.050); vault leg positive (0.476 > 0.438) but the dev leg fails |
| **S2 intelligence** | **FAIL** | agent best 0.2376 (a04_enr) vs random best 0.2389 (rnd003_enr, a bare bottom_box×0.91 scale): random ahead by 0.0013 ≈ 40× below fold noise — an honest tie; the letter gate fails |
| **S3 honesty** | **FAIL** | leave-modes-out widen 1.07 (passes >1.0) for all graded arms, BUT net-CG statFEM F(k) shear coverage 0.69–0.95 < 0.95 hard gate (the known +Z@900 shear-gap class from the netcg thread) |
| **Overall** | **pre-registered claim FALSIFIED** | valid, reportable outcome |

## 2. The mechanism story (why it failed — the run's real contribution)
The three agent rounds + controls isolated WHY shape-changing edits do not move held-out FRF correlation:
1. **Everything rides θ-calibration wobble.** Round 1: every apparent gain concentrated in the volatile
   +Z@900 fold and was matched by a parametric-only control. Round 2: a pre-designed multi-group parametric
   control statistically matched the best shape edit; stacking positive directions made them WORSE.
   Round 3: MAXIMAL split freedom went NEGATIVE (over-parameterized θ overfits the survey at held-out cost).
2. **Two evaluation-inflation mechanisms were caught by our own pre-registered gates (pre-vault):**
   (a) *Reduced-basis bias* (D18/D21/D22): scoring in the inherited basis inflates P1; even A0 fails the
   0.3% spot check at its own θ_MAP (0.69%). Exact-basis (enriched, validated to ~1e-7) re-evaluation
   collapsed the leaderboard: a16 0.250→0.227, c06 0.248→0.220, b04 0.275→0.201, rnd003 0.263→0.239.
   (b) *θ_MAP multimodality* (D19): identical model classes land in different posterior basins with dev-P1
   differences of ±0.035; fixed with deterministic multi-start.
3. **Better survey-fit ⇒ worse held-out FRF, coherently.** The baseline's own accuracy cascade — A0 0.2341
   (single-start, biased basis) → 0.2243 (multi-start) → 0.2152 (exact basis) — LOWERED held-out P1 at every
   step, and the original A0 also beats its exact twin on the vault (0.476 vs 0.438). Within this family,
   deeper .ash frequency optima transfer WORSE to held-out FRF amplitude curves. The S1 margin bar (+0.05)
   is comparable to this in-family calibration wobble — the "bar softness" caveat.
4. **Family-by-family honest negatives:** bolted-joint RBE2→spring compliance (the never-before-touched
   kinematic lever; 56 spiders, 3528 restored DOFs) = neutral-to-negative. True refinement = null at every
   evidence-targeted region (mesh converged; V3). Weld t/t³ thinning = the only directionally-consistent
   shape signal (+0.02, sub-noise). Splits = basis-bias mirage. The per-node shape wall stands.

## 3. Vault (graded once; out/vault_scores.json)
All frozen models score 0.44–0.50 on the +XY vault vs 0.20–0.24 on dev — a uniform location effect
(gap −0.22 to −0.27 for every model incl. baselines), NOT a generalization win for any candidate. Vault
ranking: rnd003_enr 0.497, c06_enr 0.496, a16_enr 0.489, a04_enr 0.476, A0 0.476, b04_enr 0.475, A0_enr
0.438. Median in-band vault coherence 0.923 (usability gate 0.6 passed). Honest label: the vault tests a
never-selected-on drive location using a cache distilled by a prior run; it is not a never-seen-by-any-run
dataset (D1/D4).

## 4. Mechanics validation + integrity (all GREEN in checker)
V1 blocks 0.00e+00 / eig 1.15e-9; V2 RBM 2.9e-12; V3 refinement null (median |df| 0.0083%, re-metriced per
D13 after the accel-drilling artifact diagnosis — ΔMAC +0.010 borderline, flagged); V4 membrane×2.000 /
bending×7.992 under t×2; V5 frozen pairing churn-proof. Budgets: 41/60 agent, 57/60 random queries;
~52/80 eigensolves. No dev-residual reads in the loop; no amplitude LSQ in scoring (both checker-audited).
Freeze SHA preceded the single vault read.

## 5. Winner's curse and reporting discipline
Every "best" above is best-of-N: agent N=41 queries (16+12+6 candidates over 3 rounds + re-scores),
random N=57. All top margins are ≤ +0.026 with paired-fold 2×SE ≈ 0.03–0.07 — nothing is distinguishable
from the bar; the falsification does not hinge on any single comparison (D23: gates fail under EVERY
candidate-selection reading).

## 6. Caveats (complete list)
- Vault = Test04 fallback (Andrew's call), weaker-than-Test08 guarantee, labeled throughout.
- Dev folds = 4 drives; the +Z@900 fold dominates fold variance (its Bottom_Box channels anti-correlate
  for every model — a genuine model-form failure of the whole family at that drive).
- a04's NUTS/Q/H ran on its own-space (θ=1-basis) package (~0.7%-class bias, labeled); its dev/vault
  scores use the exact a04_enr package.
- V3's ΔMAC +0.010 sits exactly at the 0.01 threshold (borderline, flagged, direction favorable).
- Reduced-basis dev scores of NON-frozen candidates retain the documented +0.01–0.07 inflation; only the
  freeze set was exact-basis re-evaluated (budget); no conclusion depends on the un-corrected records.
- Q-coverage grading used 4-drive answer keys with this run's tier assumptions; the shear failures are the
  same +Z@900 gap class netcg documented (a real caveat of the family, not an artifact of this run).
- The parametric-only control b04's transient "+0.059 dev pass" was entirely evaluation artifact — retained
  in the log (append-only) and reported here so the correction chain is auditable.

## 7. What this run delivers (for the replace/keep human decision)
No candidate earns replacement of the inherited FEM — the inherited model with honest statFEM-style bands
remains the deliverable twin (unchanged from the netcg thread). The durable contributions: (i) the first
genuinely closed-loop, shape-changing remodeling campaign with airtight three-tier evaluation — and its
clean falsification; (ii) two generic evaluation traps (reduced-basis score inflation; θ_MAP basin lottery)
now documented with detection recipes; (iii) the coherent "survey-fit ⊥ held-out-FRF" disconnect,
reproduced from dev through vault. Next-lever recommendation is unchanged and now better-evidenced:
the wall is per-node shape fidelity + interface damping — buy DATA (>200 Hz plate/drumhead modal test,
multi-reference), not more remodeling of a converged, topologically-complete model.
