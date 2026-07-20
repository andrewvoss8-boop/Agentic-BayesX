# Question Framing (PRE-REGISTERED) — ShockSat TRUE Agentic Remodeling Loop (20260706)

Written BEFORE any science. The SHA-locked `check.py` encodes these definitions. Later tightenings are appended
below the line and dated; nothing above the line is edited once `CHECKER.sha256` is written.

## The one question (one run, one question)
Can a CLOSED-LOOP agent that proposes SHAPE-CHANGING model-form edits (mesh refinement, region splits, added
DOFs/connectivity, physically correct thickness fields) from TRAINING residuals, and selects them on BUDGETED
held-out (dev) scores, improve the inherited ShockSat FEM's held-out per-sensor FRF prediction — confirmed on a
PRISTINE never-downloaded vault dataset — and beat a random-search baseline given the same action space and budget?

A clean falsification is a VALID, REPORTABLE outcome, labeled "pre-registered claim falsified", never as pipeline
failure. Delivering a replacement twin is NOT this run's job.

## Engineering decision supported
Whether the inherited ShockSat FEM should be replaced/augmented by an agent-remodeled variant for held-out FRF
prediction — and, more fundamentally, whether closed-loop shape-changing agentic remodeling is a real capability.
The replace/keep call remains HUMAN judgment; this run only produces the evidence.

## Objective / success metric
Primary objective = held-out per-sensor FRF log|H| Pearson correlation (P1, below). The agent search may choose
edits from the action space (§ Action space) and their θ; it may NOT choose the metric, the fold split, the
budget, or the pairing. Human judgment retains: replace/keep, acceptance of caveats, any downstream use.

## What would make this the WRONG framing
If the vault distillation is not physically usable (coherence too low), or if the inherited FEM's held-out FRF
correlation were already near the usable ceiling (it is not: per-channel log|H| corr ~0.27-0.38 vs usable ~0.7),
or if the action space could not in principle move the broken dimensions (per-node shapes / hard-region local
modes) — then "can remodeling improve held-out FRF" would be ill-posed. Prior threads establish the headroom is
real and shape-bound, so the framing stands; if the run reveals otherwise, that is itself the reported finding.

## 4.1 Three-tier data protocol
- **TRAIN:** within each dev fold, the in-fold drives + the .ash modal survey (33 modes, 76 nodes). Candidate θ
  and any hyperparameters are fit ONLY on train.
- **DEV (steering; budgeted):** leave-one-drive-out over the drives (see fold set below). For each scored
  candidate: fit on the in-fold train drives (θ_MAP + ONE global gain per fold, nothing per-mode/per-channel),
  predict ALL channels of the left-out drive, return SCALAR scores only. The proposal loop may read TRAIN-side
  residual FIELDS but NEVER dev-side residual fields — dev returns numbers, not maps. Every dev evaluation is
  appended to `out/query_log.jsonl` (candidate id, fold set, scores, timestamp, track).
  **HARD BUDGET: <= 60 dev-scored candidates for the agent track, <= 60 for the random track.** The checker
  counts the log; exceeding the budget is RED.
  **Fold set (fixed now, per decisions_log D1):** leave-one-drive-out over the **4 drives** +X/990x, +Z/990z,
  +Y/990y, +Z@900z (Test04/+XY is reserved as the fallback vault and excluded from all dev queries from the
  start). If the never-downloaded Test08 vault succeeds, dev still uses these 4 folds and Test08 is the primary
  grade; Test04 becomes a secondary held-out cross-check.
- **VAULT (grade; touched once):** PRIMARY = `Test08_ImpactHammer_990z.zip` (626 MB, never previously downloaded).
  Ordering MANDATORY + checker-enforced: (1) freeze <=3 finalists + A0 + random-best, write full vault-prediction
  artifacts to `out/finalists_frozen/`, record SHA256 in `VAULT_FREEZE.sha256`; (2) ONLY THEN download the vault
  zip; (3) distill with the SAME H1/coherence pipeline (report coherence); (4) score ONCE; (5) report dev-vs-vault
  gap for every frozen model. Honest label: the vault tests generalization to fresh never-seen test data at a
  known drive location (990z repeat), NOT a new drive location — the dev folds cover new-location generalization.
  **Fallbacks (pre-registered, decisions_log D1):** (a) if Test08 download/unzip is infeasible (disk < ~5 GiB
  free at freeze, network/size failure) the vault = the +XY/Test04 cache excluded from dev from run start
  (residual risk: prior-run Test04 summaries exist in the repo — labeled); (b) if vault distillation coherence
  is unusable (median coherence at response channels < 0.6 in 45-260 Hz), report with evidence and use (a).
- OFF-LIMITS this run: the 3.33 GB force-level parametric sweep and the pyro data (different question).

## 4.2 Arms / tracks (all reported, none silently dropped)
- **A0 baseline:** inherited FEM, calibrated θ (9-group, same likelihood). Computed FIRST under the locked
  protocol; all thresholds are relative to A0.
- **A1 agent track:** the closed loop, >=3 rounds, <=60 dev queries.
- **A2 random track:** uniform random proposals from the SAME action space, same <=60-query budget, same scoring,
  no diagnosis / no learning. Fixed seed 20260706.
- Reference bars (not arms): inherited FEM uncalibrated; FEM+6dB (for the QOI leg).

## 4.3 Metrics and pre-registered success criteria
- **P1 (primary):** median per-channel log|H| Pearson correlation on the held-out drive, 45-260 Hz, averaged over
  folds — ALWAYS reported with per-fold values and their spread. θ_MAP + one global gain per fold; NO per-mode or
  per-channel amplitude fitting anywhere in selection; frozen Hungarian pairing per model. **Noise-floor rule:**
  single-split correlation numbers carry ±0.04-0.08 split noise; a single-fold number is NEVER reportable; any
  claimed margin must be fold-averaged AND exceed 2x the standard error over folds.
- **P2:** log-amplitude RMSE at matched measured peaks on the held-out drive (dB), same fit rules.
- **Q (secondary, finalists only):** net-CG shear+normal 95% bands with statFEM F(k) (netcg conventions);
  coverage = hard gate (weighted >=0.95, <=0.5 dB energy-weighted exceedance); sharpness vs the proven bars
  (1.508/2.301/2.526 x FEM+6dB).
- **H (honesty audits, finalists + A0):** leave-modes-out widen ratio > 1.0 (hide top-3 QOI-driving measured
  modes; 1.00 = structurally overconfident = disqualified); winner's-curse N ("best of N") reported everywhere;
  dev-vs-vault gap reported.
- **SUCCESS (grade honestly against these):**
  - **S1 improvement:** agent-track winner beats A0 on dev P1 by >= +0.05 absolute, that margin also >= 2x the
    fold-to-fold standard error, AND on the vault by any positive margin (vault P1(winner) > vault P1(A0)). All
    three required for a WIN claim.
  - **S2 intelligence:** agent-track winner's dev P1 > random-track best's dev P1 (equal budget). If random
    ties/wins, the honest headline is "search space matters, agent reasoning unproven".
  - **S3 honesty:** finalists pass H and Q-coverage. An arm failing H is disqualified regardless of P1.
  - Anything less than S1+S2+S3 = pre-registered claim falsified (YELLOW/RED per Result Status Standard, loudly
    labeled).

---
## Tightenings (appended after this line; dated; do not edit above)
- 2026-07-06: Band 45-260 Hz confirmed as the P1/P2 correlation band (covers the 54.2 Hz fundamental through the
  158-233 Hz hard-region local modes and the 234-258 Hz drumhead cluster edge); rationale in assumptions_ledger.
- 2026-07-06: "vault touched once" is enforced by the checker as: at most one distilled vault cache per vault
  source, created after the `VAULT_FREEZE.sha256` timestamp.
