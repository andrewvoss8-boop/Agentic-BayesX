# RUNNER PROMPT — ShockSat TRUE Agentic Remodeling Loop (closed-loop, shape-changing, vault-scored)

**Status: READY TO DISPATCH. Self-contained. The runner executes end-to-end WITHOUT human stop-points.**
Written by the lead (Fable) 2026-07-06, approved by Andrew. Andrew's framing: *"For the first time ever we
have agents capable of remodeling FEMs intelligently and a way of selecting the best ones based off data —
that is where the energy needs to go. But we haven't gotten it to work yet."* This run is the first honest
attempt. The patent is NOT a goal of this run; the capability question is.

---

## 0. Who you are and the one question

You are an autonomous runner agent for Agentic BayesX. You have full authority to execute this card start to
finish with NO human approval points. You work ONLY inside your own new workspace (see §12); you never edit
durable rules, checkers of other studies, other workspaces, or project notes (you APPEND a runs.md entry and
a project_log row at the end, status copied verbatim from your checker — nothing stronger).

**ONE falsifiable question (one run, one question):**
> Can a CLOSED-LOOP agent that proposes SHAPE-CHANGING model-form edits (mesh refinement, region splits,
> added DOFs/connectivity, physically correct thickness fields) from training residuals, and selects them on
> BUDGETED held-out (dev) scores, improve the inherited ShockSat FEM's held-out per-sensor FRF prediction —
> confirmed on a PRISTINE never-downloaded vault dataset — and beat a random-search baseline given the same
> action space and budget?

A clean falsification ("no candidate beat baseline on the vault" or "the agent did not beat random") is a
VALID, REPORTABLE outcome — label it loudly as "pre-registered claim falsified", never as pipeline failure.
Delivering a replacement twin is NOT this run's job; whether any winner replaces the inherited FEM is a human
decision surfaced in the packet.

## 1. Re-ground FIRST (read before any work)

1. `AGENTS.md` (repo root) — every gate applies: priority deliverables, question/decision, assumptions
   ledger, quantity contracts, references, Tufte plot gate + `tufte_lint.py`, sensitivity, identifiability
   gate, verification, discretization, runtime accounting, Result Status Standard (GREEN/YELLOW/RED),
   NUTS/convergence gates, compute/detached-launch gate.
2. `docs/compute_protocol.md`.
3. This file, fully.
4. Context (read-only): `artifacts/reports/shocksat_fem_remesh_20260618/{region_diagnosis.md,
   correlation_contribution.md, decisions_log.md}` (Card D — the diagnosis + the parameterization-limit
   verdict), `artifacts/reports/shocksat_composite_bakeoff_20260702/{findings.md, question_framing.md}`
   (evidence≠held-out; rand10 lesson), `notes/lessons-learned.md` (esp. the 2026-06-09 adaptive-overfitting
   BLOG entry, the 2026-06-22 data-ceiling entry, the 2026-06-08 FEM validation entries),
   `artifacts/reports/shocksat_netcg_method_selection_20260701/packet.md` (scoring conventions, statFEM F(k)).

State in one line in your `decisions_log.md` (D0): goal / last decision / next action / open ambiguities.
After ANY compaction, re-ground from this file + your workspace gate files before acting.

## 2. Context you must internalize (why this run exists)

- **Prior "agentic remodeling" was NOT remodeling.** Card D + the composite bake-off only ever applied
  `scale`/`bush_k`/`couple`/`mass_scale` on a FROZEN mesh — parametric stiffness/mass rescaling. The only
  true mesh change (dish 2× refine) was a null control. The bake-off's 151 "candidates" were a fixed
  open-loop menu + a random tranche; the evidence-selected winner was `rand10`, a RANDOM edit, and it lost
  on held-out. Three gaps: (1) the action space could not change mode SHAPES; (2) the loop was never closed
  (no propose→score→learn→propose); (3) selection ran on evidence, and evidence ≠ held-out (proven).
- **The headroom is real.** The vendor correlation covered global frequencies/MAC (low modes 0.88–0.97,
  |df| ~2.5–3.3%) — but per-channel FRF log|H| correlation is ~0.27–0.38 (plateau ~0.4) vs usable ~0.7;
  the 54.2 Hz fundamental is MAC 0.97 on the NASA survey grid but 0.17 on the 84 accel channels; hard-region
  high-frequency local shapes sit at MAC ≈ 0.0 (158–233 Hz). Card D's Pareto-optimality is FAMILY-RELATIVE
  (9-group multipliers only). The dimensions that are broken are exactly the ones only a model-form change
  can move. Statistics-side levers are exhausted (proven across netcg/bakeoff/richmodel/modelclass threads).
- **Andrew's binding principles:** LIMITED DATA, NOT LIMITED MODES (full in-band mode set, all train
  drives); no per-mode amplitude/phase LSQ inside any selection score; frozen one-to-one Hungarian mode
  pairing per model (greedy MAC re-pairing churn is a known historic trap); honest labels beat impressive
  claims, always.

## 3. Assets (exact paths; all read-only to you)

| asset | path |
|---|---|
| Full parsed NASTRAN FEM (67,720 grids, per-PID blocks) | `artifacts/reports/shocksat_fem_modal_twin_20260609/fem_model.npz` |
| Element-level assembly pipeline (CQUAD4 QM6+MITC4, bush, RBE2 elim) | `artifacts/reports/shocksat_fem_remesh_20260618/scripts/{parse_nastran.py, fe_core.py, assemble_fem.py, reduce_model.py, enrich_basis.py, pairing.py, parse_ash.py}` |
| Proven TRUE-refinement example (conforming 2×2 quad subdivision) | `artifacts/reports/shocksat_fem_remesh_20260618/code/remesh_dish.py` |
| Measured modal survey (33 modes, 76 nodes, .ash parsed) | `artifacts/reports/shocksat_fem_remesh_20260618/measured_modes.npz` |
| 5 drive FRF caches (train+dev): +X/990x, +Z/990z, +Y/990y, +XY/990xy, +Z@900 | `artifacts/reports/shocksat_netcg_method_selection_20260701/data/multiref_modal/m_*.npz` (also 4 in `shocksat_psd_envelope_twin_20260623/data/multiref_modal/`) |
| Channel map / obs DOFs / groups | `artifacts/reports/shocksat_psd_envelope_twin_20260623/data/{channel_map.csv, obs_dofs.npy, groups.json}` |
| FRF prediction/scoring conventions + statFEM F(k) | `artifacts/reports/shocksat_netcg_method_selection_20260701/` (realfrf/score/modal_feature/heldout patterns) |
| Bake-off remodel engine + FRF-distillation pipeline pattern | `artifacts/reports/shocksat_composite_bakeoff_20260702/code/rmodel.py`; distillation pattern per netcg D-notes (hit-avg band-limited H1 + coherence) |
| NASA source manifest incl. VAULT zips + access notes | `artifacts/reports/shocksat_statfem_runner_20260609/source_manifest.md` (workshop `https://nescacademy.nasa.gov/workshops/ShockSat/ShockSat1`; files served via mediaex-server.larc.nasa.gov, HEAD + byte-range OK) |

Record SHA256 of every reused read-only source in `REUSED_code.sha256` before science.

## 4. Pre-registered protocol (write `question_framing.md` FIRST, lock the checker against it)

### 4.1 Three-tier data protocol (the core discipline of this run)
- **TRAIN:** within each dev fold, the 4 in-fold drives + the .ash modal survey. Candidates' θ (and any
  hyperparameters) are fit ONLY on train.
- **DEV (steering; budgeted):** leave-one-drive-out over the 5 cached drives (5 folds). For each scored
  candidate: fit on the 4 train drives (θ_MAP + ONE global gain per fold, nothing per-mode/per-channel),
  predict ALL channels of the left-out drive, return SCALAR scores only (§4.3). The proposal loop may read
  train-side residual FIELDS but may NEVER read dev-side residual fields — dev returns numbers, not maps.
  Every dev evaluation is appended to `out/query_log.jsonl` (candidate id, fold set, scores, timestamp,
  track). **HARD BUDGET: ≤ 60 dev-scored candidates for the agent track, ≤ 60 for the random track.** The
  checker counts the log; exceeding the budget is RED.
- **VAULT (grade; touched once):** `Test08_ImpactHammer_990z.zip` (626 MB) primary, `Test10_ImpactHammer_900z.zip`
  (737 MB) secondary — NEVER previously downloaded by any run in this repo (verified in source_manifest).
  Ordering is MANDATORY and checker-enforced: (1) freeze ≤3 finalists + baseline + random-best, write their
  full vault-prediction artifacts to `out/finalists_frozen/` and record SHA256 in `VAULT_FREEZE.sha256`;
  (2) ONLY THEN download the vault zips; (3) distill with the SAME H1/coherence pipeline (report coherence);
  (4) score ONCE; (5) report the dev-vs-vault gap for every frozen model. Honest label: the vault tests
  generalization to fresh never-seen test data at known drive locations (990z/900z repeats), not to a new
  drive location — the dev folds cover new-location generalization.
  **Vault fallbacks (pre-registered):** (a) if download is infeasible (network/size), fallback vault =
  the +XY/Test04 cache EXCLUDED from all dev queries from the start of the run (declare this exclusion in
  question_framing before science; label the residual risk that prior-run summaries of Test04 exist in the
  repo); (b) if the vault distillation coherence is genuinely unusable (median coherence at response
  channels < 0.6 in 45–260 Hz), report that with evidence and use fallback (a). If you use fallback (a),
  dev folds run over the remaining 4 drives only.
- The 3.33 GB force-level parametric sweep and pyro data are OFF-LIMITS this run (different question).

### 4.2 Arms/tracks (all reported, none silently dropped)
- **A0 baseline:** inherited FEM, calibrated θ (9-group, same likelihood) — the bar to beat. Compute A0
  under the locked protocol FIRST; all thresholds below are relative to A0.
- **A1 agent track:** the closed loop (§6), ≥3 rounds, ≤60 dev queries.
- **A2 random track (mandatory intelligence comparator):** uniform random proposals from the SAME action
  space (§5), same budget (≤60 dev queries), same scoring — no diagnosis, no learning. Fixed seed.
- Reference bars (not arms): inherited FEM uncalibrated; FEM+6dB for the QOI leg.

### 4.3 Pre-registered metrics and success criteria
- **P1 (primary):** median per-channel log|H| Pearson correlation on the held-out drive, 45–260 Hz, averaged
  over folds — ALWAYS reported with the per-fold values and their spread. Physics-honest: θ_MAP + one global
  gain per fold; NO per-mode or per-channel amplitude fitting anywhere in selection (the LSQ trap); frozen
  Hungarian pairing per model. **Noise-floor rule (from the 2026-07-06 metric-noise study, notes/memory.md):
  single-split correlation numbers on this data carry ±0.04–0.08 split noise — a single-fold number is never
  reportable; any claimed margin must be fold-averaged AND exceed 2× the standard error over folds.**
- **P2:** log-amplitude RMSE at matched measured peaks on the held-out drive (dB), same fit rules.
- **Q (secondary, finalists only):** net-CG shear+normal 95% bands with statFEM F(k) (netcg conventions):
  coverage = hard gate (weighted ≥0.95, ≤0.5 dB energy-weighted exceedance), sharpness reported vs the
  proven bars (1.508/2.301/2.526 × FEM+6dB).
- **H (honesty audits, finalists + baseline):** leave-modes-out widen ratio > 1.0 (hide top-3 QOI-driving
  measured modes; 1.00 = structurally overconfident = disqualified); report winner's-curse N everywhere
  ("best of N"); report the dev-vs-vault gap.
- **SUCCESS (all pre-registered; grade honestly against these):**
  - **S1 improvement:** agent-track winner beats A0 on dev P1 by ≥ +0.05 absolute, with that margin also
    ≥ 2× the fold-to-fold standard error (noise-floor rule above), AND on the vault by any positive margin
    (vault P1(winner) > vault P1(A0)). All required for a WIN claim.
  - **S2 intelligence:** agent-track winner's dev P1 > random-track best's dev P1 (equal budget). If random
    ties/wins, the honest headline is "search space matters, agent reasoning unproven" — report it.
  - **S3 honesty:** finalists pass H and Q-coverage. An arm failing H is disqualified regardless of P1.
  - Anything less than S1+S2+S3 = claim falsified (YELLOW/RED per Result Status Standard, loudly labeled).

## 5. Action space (this is the new capability — build it)

**Required families (the run is void if these are not genuinely implemented):**
1. **True local mesh refinement** — conforming subdivision of selected shell regions (extend the
   `remesh_dish.py` mechanism to regions that share nodes: handle boundary conformity via transition
   elements or region-boundary node sharing; if a region cannot be refined conformally, document and skip).
2. **Region/parameter splits** — split a PID/group into data-driven sub-regions (e.g. bulkhead near-joint
   band vs field), each with its own stiffness/thickness parameter: expands the achievable stiffness
   DISTRIBUTION, not just its level.
3. **Physically correct thickness/offset field** — per-region t with membrane ∝ t and bending ∝ t³ scaled
   SEPARATELY and correctly (this requires element-level reassembly via `fe_core.py`; the old K-block
   modulus proxy is FORBIDDEN as a "thickness" claim — label any modulus scale as modulus).
4. **Added DOFs / connectivity** — discrete joint/weld compliance with new nodes/springs, strut-base
   attachment re-representation, bracket footprint distribution (RBE3-style) — edits that change the
   kinematic hypothesis, with a physical mechanism stated per edit.
5. Parametric scales (the old family) are ALLOWED as combination ingredients but a candidate consisting
   ONLY of scales is tagged `parametric_only` and reported separately (they are the proven-dead family).

**Forbidden:** from-scratch geometry rebuild (Card D verdict stands); unphysical edits (e.g. softening the
welded bulkhead-to-wall connection below plausible weld compliance — each edit carries a one-line physical
plausibility rationale, and implausible metric-chasers are rejected in the proposal step, not post-hoc).

Every candidate = a JSON edit spec + family + rationale + the diagnostic evidence that motivated it.

## 6. The closed loop (agent track)

Per round r = 1..R (R ≥ 3):
1. **Diagnose (train side only):** fit A0/current-best on train; compute residual structure — region MAC vs
   .ash, per-channel log|H| residual fields on TRAIN drives, strain-energy maps, peak misalignment map.
   Write `out/diagnosis_r{r}.json` + a figure. (Dev residual fields are never read — checker greps your
   loop code for dev-cache reads outside the scoring function.)
2. **Propose:** N_r candidates (your call, budget-aware) from the diagnosis, spanning the required families;
   record for each WHICH diagnostic finding motivated it.
3. **Screen (cheap, labeled NO-sampler):** eigensolve each candidate and rank by a train-side proxy
   (matched-mode Δf + region MAC vs .ash, frozen pairing). **Reduced-basis trap (hard rule):** any candidate
   that changes mesh/DOF count/connectivity MUST be solved in its OWN basis — full-order eigensolve, or a
   per-candidate enriched reduction validated ≤0.3% frequency error against full solves on a spot-check
   sample (`enrich_basis.py` pattern). NEVER score a shape-changing edit in the frozen inherited 80-mode
   basis. Budget: ≤ 80 full-order eigensolves total (log each; detached; resumable).
4. **Dev-score** the round's survivors (scalar P1/P2 via §4.1; append to query_log; respect the budget).
5. **Learn:** write `out/round_r{r}_summary.md` — what the scores said, which hypotheses died, what the next
   round proposes differently. This document is the "agent intelligence" audit trail; S2 is judged partly on
   whether proposals demonstrably respond to evidence.

Random track (A2): same steps 3–4 with uniform random proposals (fixed seed 20260706), no steps 1/5.

**Finalists:** ≤3 candidates by dev P1 (agent track; include random-best and A0 in the freeze). Full NUTS θ
posterior for each finalist + A0 (4 chains, x64, all-variable R-hat ≤1.05 / ESS ≥200 / div <2%; report worst
case; a non-converged finalist is YELLOW and its intervals are labeled not-trustworthy). statFEM F(k) bands
for Q. Then the vault protocol (§4.1), exactly once.

## 7. Mechanics validation gates (BEFORE any science; all checker-encoded)

- **V1 baseline reproduction:** your no-edit reassembly reproduces the inherited model's eigenfrequencies to
  ≤1e-8 relative (Card D achieved 3.6e-10).
- **V2 free-free RBM:** 6 rigid-body modes at machine zero on a free-free variant of an edited submodel
  (catches drilling-DOF and constraint bugs — see 2026-06-11 MPL lesson).
- **V3 refinement null test:** refining a region WITHOUT physics change moves matched modes only by
  convergence-level amounts (reference: dish 2× moved global MAC +0.0016); a big move = a conformity bug.
- **V4 thickness physics:** on a patch/strip test, t-scaling changes membrane stiffness ∝ t and bending
  ∝ t³ independently, against analytic plate values (ν=0 to disambiguate, per MPL lesson).
- **V5 pairing robustness:** the frozen Hungarian pairing is computed once per model and never re-greedied;
  a unit test shows a frequency-shifted model does NOT gain matched-MAC by churn.
- Failures here BLOCK science until fixed — this is the one place "keep going" yields to "fix first".

## 8. Sampler and compute policy

- NUTS/HMC (numpyro, x64) ONLY for finalists+A0 posteriors; all screening is MAP/deterministic and labeled
  NO-sampler. Never call a screen "Bayesian updating".
- Detached-launch every job that could exceed the tool timeout (`nohup … > logs/x.log 2>&1 & disown`;
  monitor with chained until-loops). Everything resumable per (track, round, candidate): write partial
  results, skip finished work on relaunch. Pin BLAS (`OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`) for
  small dense eigh; let the full-order sparse eigensolves use their normal threading. Known incident to
  avoid: eigenVECTOR gradients at the 246–258 Hz degenerate cluster hang NUTS — reuse the bake-off's
  Tikhonov-regularized shape-derivative fix (D11, δ=1.6e4) if shapes enter any gradient path.
- Disk: vault zips are 0.6–0.7 GB each — check free space first, delete zips after distillation (keep the
  distilled .npz + SHA256 + listing), never commit them.
- `runtime.json` with `active_runtime_s` and `elapsed_wallclock_s`.

## 9. Workspace, gate files, checker (exact order)

1. Create `artifacts/reports/shocksat_true_remodel_loop_<YYYYMMDD>/` with `code/ out/ logs/ figures/ data/`.
2. Write gate files FIRST: `priority_deliverables.md`, `question_framing.md` (§4 verbatim + any tightening),
   `quantity_contracts.md` (FRF log|H| per channel: numerator/denominator/units g/lbf, drive/BC, band,
   limiting behavior; net-CG per netcg contracts; matched-peak definition), `assumptions_ledger.md`
   (ζ=0.01, tier σs, F(k) form, gain rules, band 45–260 Hz + rationale, coherence threshold, all with
   values/units/sensitivity priority), `decisions_log.md` (D0…).
3. Write `check.py` and SHA-lock it (`CHECKER.sha256`) BEFORE any science. It must encode at minimum: gate
   files exist; V1–V5 pass; query-budget counts from query_log; the no-dev-residual-reads grep; vault freeze
   ordering (finalists SHA timestamp precedes vault download log); vault touched once; no per-mode amplitude
   LSQ in selection code paths; NUTS diagnostics for finalists; leave-modes-out present; figures exist +
   image-legibility QA; runtime.json; statuses per Result Status Standard. Checker is IMMUTABLE during the
   trial. `bash run_all.sh` = one-command replay.
4. Baseline A0 under the locked protocol. 5. Tracks A1/A2. 6. Finalists + NUTS + Q/H. 7. Vault. 8. Packet.

## 10. Deliverables

- `packet.md` — first-pass method summary up front (model form, likelihood, data counts, whole-data vs
  feature choice, inferred/fixed/not-inferred), run-specific graphical model figure, the S1/S2/S3 verdicts
  with numbers, dev-vs-vault gaps, winner's-curse Ns, all caveats. Plain-English ML terms per AGENTS.md
  communication style; structural-dynamics terms used directly.
- `findings.md` — headline results, never stronger than checker output.
- Figures (Tufte skill + lint, saved .py, run/dataset + convergence stamps on-figure): money figure
  (dev P1 trajectory per round: agent vs random vs A0, vault points overlaid), diagnosis maps (before/after
  for the winner), funnel (proposed→screened→dev-scored→finalists→vault), bands vs held-out for finalists,
  graphical model.
- `out/query_log.jsonl`, `out/round_r*_summary.md`, `VAULT_FREEZE.sha256`, `REUSED_code.sha256`,
  `runtime.json`, `checker_report.json`.
- Continuity (append-only): one `notes/runs.md` entry + one `docs/report/project_log.md` row, status copied
  verbatim from the checker.

## 11. Autonomy rules (no human stop-points)

- Resolve ambiguities yourself using this file's defaults; record every non-obvious resolution in
  `decisions_log.md` BEFORE acting on it. If two readings are cheap, do both, label both.
- Blocked ≠ stopped: if a component fails (download, refinement conformity, a hung sampler), document the
  exact blocker + evidence, apply the pre-registered fallback, and continue. Only a violated integrity rule
  (checker edit, vault ordering, budget) has no fallback — that work is withdrawn, not patched.
- Never claim success without checker output. Never present a screen as a posterior, a proxy as the metric,
  or a modulus scale as a thickness change. A falsified pre-registered claim is a GOOD outcome — report it
  with the same care as a win.
- Crash/compaction recovery: re-read this file + your gate files + query_log, restate state in one line in
  decisions_log, resume from partial results.
