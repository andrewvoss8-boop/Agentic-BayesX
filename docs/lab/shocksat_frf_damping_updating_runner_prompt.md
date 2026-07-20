# RUNNER PROMPT — ShockSat FRF-DOMAIN Agentic Updating with a DAMPING Action Space (FDAC-aligned, vault-scored)

**Status: DRAFT, written by the lead (Fable) 2026-07-10 as the honest successor to the completed TRUE-remodel
loop. NOT yet dispatched — Andrew reviews first, then dispatches in a FRESH autonomous session.** Self-contained:
the runner executes end-to-end with NO human stop-points.

The completed run (`artifacts/reports/shocksat_true_remodel_loop_20260706/`, checker YELLOW 11G/1Y/0R,
"pre-registered claim FALSIFIED") cleanly falsified *modal-selected, shape-changing* remodeling on held-out
FRF correlation. A subsequent correlation-literature review (`references/fem_test_correlation_litreview.md`,
Fable 2026-07) shows that outcome is partly a textbook result AND partly a consequence of THREE levers we
mis-specified for an FRF deliverable. This card gives the loop its FAIR, literature-blessed shot — and, more
importantly, tests the one lever every prior thread and the literature independently name as controlling FRF
amplitude: **damping**. The completed run STANDS; this is the next question, not a re-litigation.

---

## 0. Who you are and the ONE question

Autonomous runner for Agentic BayesX; full authority to execute start to finish with no approvals. Work ONLY
in your own new workspace; never edit durable rules, other studies' checkers, other workspaces, or project
notes (APPEND one runs.md entry + one project_log row at the very end, status copied verbatim from your checker).

**ONE falsifiable question (one run, one question):**
> Can an FRF-DOMAIN agentic updating loop — that (a) SELECTS updating bands and ALIGNS the score by FDAC
> (frequency-shift-aware), (b) has a DAMPING action space (band modal damping / Rayleigh / per-joint loss
> factor) alongside the proven shape/stiffness edits, and (c) refines θ AND damping on FRF residuals over the
> FDAC-selected bands — improve the inherited ShockSat FEM's held-out per-sensor FRF AMPLITUDE prediction
> beyond the modal-only baseline, beyond the completed run's shape-only result, and beyond an equal-budget
> random comparator, confirmed on the vault — AND is any improvement ATTRIBUTABLE to the DAMPING family
> (not the shape family)?

A clean falsification is a VALID, REPORTABLE outcome, labeled "pre-registered claim falsified", never a
pipeline failure. **Pre-registered honest expectation (state it up front, then let the data rule):** from the
completed run + literature, the SHAPE family is expected to stay ~null; the DAMPING family MAY move amplitude
(FRSF) but FDAC-aligned FRAC gains are UNCERTAIN because ShockSat's modal domain is already NASA-correlated and
the hard-region shapes may be sensor-set-unobservable (bounded in Gate O below). Delivering a replacement twin
is NOT this run's job; replace/keep is a human decision surfaced in the packet.

## 1. Re-ground FIRST (read before any work)
1. `AGENTS.md` — every gate applies (priority deliverables, question/decision, assumptions ledger, quantity
   contracts, references + this literature review, Tufte + `tufte_lint.py`, sensitivity, identifiability gate,
   verification, discretization, runtime accounting, Result Status Standard, NUTS/convergence, compute/detached).
2. `docs/compute_protocol.md`.
3. This file, fully. `references/fem_test_correlation_litreview.md`, fully (esp. §2 FRF metrics, §4 sensor
   observability, §5 FRF-based updating + the hybrid strategy, §8 damping).
4. Context (read-only): the COMPLETED run
   `artifacts/reports/shocksat_true_remodel_loop_20260706/{packet.md, findings.md, decisions_log.md,
   out/verdicts.json}` — internalize its S1/S2/S3 falsification, the two evaluation traps it caught
   (reduced-basis score inflation D18/D22; θ_MAP multimodality D19), and the "better modal fit -> worse
   held-out FRF" disconnect. Also `shocksat_netcg_method_selection_20260701/packet.md` (statFEM F(k), the
   +Z@900 shear gap) and `notes/lessons-learned.md` (2026-07-08 entry: the two traps + the disconnect).

State a one-line D0 in your `decisions_log.md`: goal / last decision / next action / open ambiguities. After
ANY compaction, re-ground from this file + your gate files before acting.

## 2. Context you must internalize (why this card exists)
- **The completed run's null is real but scoped.** It falsified *modal-θ-selected, shape-changing* edits on a
  *raw* per-channel log|H| correlation. Three literature-named mis-specifications for an FRF deliverable:
  1. **Wrong selection domain.** θ was fit to modal frequencies (.ash eigenvalues), then graded on FRF; §2
     says modal correlation does not guarantee FRF prediction, and §5 says update in the FRF domain for FRF
     deliverables.
  2. **No FDAC frequency-shift accounting.** Raw log|H| correlation over 45-260 Hz is a FRAC without the FDAC
     pre-alignment §2 demands; with 2.5-3.3% modal frequency error, raw FRAC is dominated by peak MISALIGNMENT.
     Empirical proof in the completed run: parametric θ-only controls (which move peaks) swung P1 as much as
     shape edits, and the +Z@900 fold moved +/-0.08 under tiny θ changes — a frequency-alignment signature, not
     a shape signature. The completed run's noise floor may BE frequency-shift sensitivity.
  3. **Frozen damping.** ζ was fixed at 1%; §2/§8 say FRF AMPLITUDE correlation is impossible without a damping
     model. FRF amplitude ~ participation / damping; remeshing cannot touch damping. The completed run tested
     only shape levers (which can't move amplitude) while withholding the lever that can.
- **Andrew's binding principles carry over:** LIMITED DATA not limited modes (full in-band mode set, all train
  drives); NO per-channel/per-mode free amplitude OR free per-channel damping in any selection score (the LSQ
  trap, now extended to damping — see §4.3); frozen one-to-one Hungarian pairing per model; honest labels beat
  impressive claims. **New hard rule:** a damping parameter is a FEW, PHYSICAL, LOW-DIM quantity (band ζ,
  Rayleigh α/β, per-joint-group loss factor η) fit on TRAIN and FROZEN for dev prediction — NOT a per-channel
  amplitude knob in disguise. A model that "wins" by driving ζ or η outside physical bounds is DISQUALIFIED.

## 3. Assets (exact paths; all read-only to you; SHA256 each in `REUSED_code.sha256` before science)
| asset | path |
|---|---|
| Completed-run FE layer (element reassembly, refine/split/thickness/connect, own-basis solve, frozen pairing, exact-basis enrichment) | `artifacts/reports/shocksat_true_remodel_loop_20260706/code/{femlib.py, actions.py, score.py, enrich_candidate.py, enrich_own.py, spot_check.py, nuts_finalist.py, qoi.py, vault.py, verdicts.py, mech_gates.py}` |
| Parsed FEM (67,683 grids) + stored blocks/M/T/V_keep | `artifacts/reports/shocksat_fem_remesh_20260618/{fem_model.npz, matrices/}` |
| Measured modal survey (33 modes, 76 nodes) | `artifacts/reports/shocksat_fem_remesh_20260618/measured_modes.npz` |
| 5 drive FRF caches (per-channel H1 + COHERENCE, ~2 Hz resolution, 45-260 Hz) | `artifacts/reports/shocksat_netcg_method_selection_20260701/data/multiref_modal/m_*.npz` |
| channel map / obs DOFs / groups | `artifacts/reports/shocksat_psd_envelope_twin_20260623/data/{channel_map.csv, obs_dofs.npy, groups.json}` |
| statFEM F(k) conventions for the QOI leg | `artifacts/reports/shocksat_netcg_method_selection_20260701/code/netcg_qoi.py` |
| this literature review | `references/fem_test_correlation_litreview.md` |

**Reuse, do not re-derive**, the completed FE layer and its two hard-won guards (exact-basis scoring; multi-start
θ_MAP). You ADD: a damping-augmented forward model, FDAC/FRAC/FRSF metrics, FRF-domain θ+damping refinement, and
the sensor observability pre-check.

**Data-resolution constraint (discretization gate, flag before science):** the distilled caches are ~2 Hz
resolution — TOO COARSE for half-power/circle-fit damping ID (a 1%-damped 54 Hz peak has a ~1.1 Hz half-power
band). Therefore identify/refine damping by FRF-BAND MODEL-FIT (fit the modal FRF magnitude shape over a band
with ζ as a parameter), NOT half-power per peak. The raw time histories were deleted (prior disk cleanup); a
finer re-distillation would require a NASA re-download — do NOT assume it; if the band-fit ζ is unidentifiable
at 2 Hz resolution for a mode, mark that mode's damping NOT-inferred and say so (identifiability gate).

## 4. Pre-registered protocol (write `question_framing.md` FIRST, SHA-lock the checker against it)

### 4.1 Three-tier data protocol (unchanged discipline)
- **TRAIN:** within each dev fold, the in-fold drives + the .ash survey. θ, damping, and any hyperparameters
  fit ONLY on train. **FDAC band selection and the frequency-alignment map are computed on TRAIN drives only**
  (a train-side FIELD, like the completed run's diagnosis) — never on the dev/vault drive.
- **DEV (steering; budgeted):** leave-one-drive-out over the 4 loop drives (+X/990x, +Z/990z, +Y/990y,
  +Z@900z; +XY/Test04 reserved as vault, excluded from all dev queries from run start — same as the completed
  run, D1/D4). For each scored candidate: fit θ+damping on the fold's train drives + .ash, predict ALL channels
  of the left-out drive, return SCALAR scores only (§4.3), appended to `out/query_log.jsonl` (cid, fold set,
  scores, track, timestamp). **HARD BUDGET: <= 60 dev-scored candidates for the agent track, <= 60 for random.**
  Checker counts the log; exceeding is RED.
- **VAULT (grade; touched once):** +XY/Test04 cache, graded ONCE after finalists are SHA-frozen
  (`VAULT_FREEZE.sha256` timestamp precedes any vault read), with the SAME FDAC-aligned metric. Honest label
  identical to the completed run (held out from THIS run's selection, not never-seen-by-any-run; the +XY drive
  is also the "easy" location per the completed run's uniform +0.22-0.27 dev-vs-vault gap — report the gap and
  do NOT read a high vault number as a win).
- OFF-LIMITS: the 3.33 GB force-level sweep and pyro data.

### 4.2 Arms/tracks (all reported, none dropped)
- **A0 modal-only baseline:** inherited FEM, multi-start modal-θ_MAP, FIXED ζ=1% (the completed run's A0_enr,
  exact-basis). The bar to beat. Compute FIRST.
- **A0d damping-updated baseline:** inherited FEM (no shape edit) + the DAMPING action space fit on train
  (band ζ / Rayleigh / joint η), FRF-domain refined. This isolates "what does damping alone buy the baseline"
  and is the reference the agent must EXCEED to claim shape-form value.
- **A1 agent track:** the closed FRF-domain loop, >=3 rounds, <=60 dev queries, action space = damping +
  shape/stiffness + connectivity (§5), FDAC-aligned selection.
- **A2 random track:** uniform random from the SAME action space (incl. damping), same budget, same scoring,
  fixed seed 20260710, no diagnosis/learning.
- Reference bars: inherited uncalibrated (θ=1, ζ=1%); FEM+6dB (QOI leg). The completed run's shape-only winner
  (a04/a16 exact-basis, ζ=1%) carried forward as a labeled prior-result bar.

### 4.3 Metrics and success criteria (FRF-domain, FDAC-aware — the core change)
- **FDAC (train-side):** for each channel, FDAC(ω_a, ω_e) = |Σ H_pred,s(ω_a)·H_meas,s(ω_e)|² normalized
  (improved cosine/phase-sensitive form, [-1,1]); the ridge ω_e(ω_a) is the per-channel frequency-shift map.
  Aggregate to a per-model frequency-warp; SELECT updating bands where the ridge is clean and away from
  resonance/antiresonance. Documented, saved as a train-side field; NEVER computed on dev/vault.
- **P1' (primary) = FDAC-aligned FRAC:** median over usable channels of FRAC between predicted and measured
  log|H| AFTER applying the train-side frequency-alignment warp, over the FDAC-selected band, 45-260 Hz,
  fold-averaged with per-fold spread. This is the metric the completed run lacked: it rewards SHAPE/AMPLITUDE
  agreement independent of the small residual frequency shift. Physics-honest: θ_MAP + damping (train-fit,
  frozen) + ONE global gain per fold; NO per-mode/per-channel amplitude fit, NO per-channel damping fit.
  Noise-floor rule (carry the completed run's ±0.04-0.08 finding): single-fold numbers never reportable; a
  claimed margin must be fold-averaged AND exceed 2x the fold-to-fold SE.
- **P2' (amplitude/damping) = FRSF error:** median over channels of |FRSF - 1| (and dB) at the FDAC-aligned
  matched peaks — the direct measure of what damping updating buys. Lower is better.
- **P3 (raw, comparability):** the completed run's raw log|H| correlation, reported so this run is directly
  comparable to it and so the FDAC-alignment effect is quantified (P1' - P3 = the alignment gain).
- **Q (secondary, finalists only):** net-CG shear+normal statFEM F(k) bands (netcg conventions); coverage hard
  gate weighted >= 0.95, <= 0.5 dB energy-weighted exceedance; sharpness vs the proven bars.
- **H (honesty audits, finalists + A0/A0d):** leave-modes-out widen > 1.0 (else disqualified); **physical-
  damping gate** — inferred ζ within [0.2%, 5%] and joint η <= 0.2 (a "win" needing damping outside these =
  DISQUALIFIED as an amplitude-fit in disguise); winner's-curse N reported; dev-vs-vault gap reported.
- **SUCCESS (grade honestly):**
  - **S1 improvement:** agent-track winner beats A0 on dev P1' by >= +0.05 absolute, margin >= 2x fold SE, AND
    vault P1'(winner) > vault P1'(A0). (Threshold +0.05 kept from the completed run for continuity; if the FDAC
    alignment sharply lowers the noise floor, a tighter data-justified threshold may be pre-registered in
    `question_framing.md` BEFORE any dev score, with the fold-SE evidence — never after.)
  - **S2 intelligence:** agent-track winner's dev P1' > random-track best's (equal budget, same action space).
  - **S3 honesty:** finalists pass H (incl. the physical-damping gate) and Q-coverage.
  - **S4 attribution (NEW — the real question):** any S1 improvement is ATTRIBUTABLE to the DAMPING family via
    ablation — damping-only (A0d and agent damping-only candidates) must account for >= 2/3 of the winner's
    P1' margin over A0, else the headline is "improvement is shape/θ, damping lever unproven" (or, if nothing
    improves, "no lever cleared the floor"). Report the shape-only vs damping-only vs both decomposition.
  - Anything less than S1+S2+S3+S4 = pre-registered claim falsified (YELLOW/RED, loudly labeled).

## 5. Action space (the DAMPING families are the new capability — build them)
**Required damping families (run is void if not genuinely implemented + physics-validated in Gate D):**
1. **Band modal damping** — ζ piecewise-constant over 3-5 frequency bands (physical, low-dim); the FRF forward
   uses per-mode ζ = the band value at that mode's frequency. Prior center from a train-side FRF-band model-fit
   (NOT half-power, per §3 resolution constraint).
2. **Rayleigh proportional** — C = αM + βK (2 params, ζ_i = α/(2ω_i) + βω_i/2). The classical minimal model.
3. **Per-joint-group structural (loss-factor) damping** — complex stiffness K_g(1+iη_g) localized to the CBUSH
   joint groups (`joints`, `contact`); η_g per group. This is the NON-PROPORTIONAL, physically-located
   "damping remodeling" analog the literature (§8) names as the built-up-structure damping source. Implemented
   via a structural-damping term in the FRF resolvent on those groups' reduced blocks.
**Comparator families (from the completed run, carried so the S4 ablation can separate damping from shape):**
4. Shape/stiffness edits (refine / split / thickness / connect) — the PROVEN-NULL family; allowed as candidates
   and REQUIRED in the ablation, but not expected to move P1'.
5. Parametric θ scales — the proven-dead family; tagged `parametric_only`, reported separately (controls).
**Forbidden:** per-channel or per-mode free damping/amplitude (the LSQ trap); damping outside the physical
gate; from-scratch geometry rebuild. Every candidate = JSON edit spec + families + rationale + the diagnostic
evidence that motivated it + the ablation label (damping-only / shape-only / both).

## 6. The closed loop (agent track)
Per round r = 1..R (R >= 3):
1. **Diagnose (train side only):** fit A0/current-best on train (modal-θ then FRF-refine); compute FDAC per
   channel (frequency-shift map), FRSF per channel (amplitude/damping error field), FDAC-selected bands, and
   the region/mode residual structure. Write `out/diagnosis_r{r}.json` + a figure. Dev FRFs are never read
   here (checker greps loop code for dev-cache reads outside the score function).
2. **Propose:** N_r candidates spanning damping + shape families, each tagged with its ablation label and the
   diagnostic finding (which FRSF hotspot / FDAC band) it targets. The loop should demonstrably shift spend
   toward whichever family moved P1'/P2' in the prior round (the S2/"intelligence" evidence).
3. **Screen (cheap, NO-sampler):** rank by a train-side proxy (FDAC-aligned train FRAC + FRSF error at θ_MAP
   + train-fit damping). Reduced-basis-trap rule CARRIES: any mesh/DOF/connectivity change scored in its OWN
   space (full solve) or exact-basis-enriched (<=0.3%); damping-only and scale-only candidates may use the
   inherited/enriched basis (they do not change K's DOF space). Budget: <= 80 full-order eigensolves total,
   logged, detached, resumable.
4. **Dev-score** survivors (scalar P1'/P2'/P3 via §4.1; append to query_log; respect the budget).
5. **Learn:** `out/round_r{r}_summary.md` — what moved P1' vs P2' vs P3, which family, which hypotheses died,
   what round r+1 proposes differently. This is the S2 audit trail.
Random track (A2): steps 3-4 with uniform random proposals (seed 20260710), no steps 1/5.
**Finalists:** <= 3 agent candidates by dev P1' + A0 + A0d + random-best, all EXACT-BASIS (D18/D22 rule).
Full NUTS posterior for each finalist + A0 + A0d (θ AND the low-dim damping params; 4 chains, x64,
all-variable R-hat <= 1.05 / ESS >= 200 / div < 2%; report worst case). statFEM F(k) for Q. Then the vault, once.

## 7. Mechanics + metric validation gates (BEFORE any science; checker-encoded)
Carry the completed run's V1-V5 (reuse `mech_gates.py`; V1 block reproduction, V2 free-free RBM, V3 refinement
null with the participation-masked cross-model re-metric, V4 t/t³ thickness, V5 frozen-pairing churn). ADD:
- **Gate D1 (damping physics):** on a 1-DOF and a 2-mode analytic system, band-ζ / Rayleigh / structural-η
  forward models reproduce the analytic FRF peak height (= 1/(2ζ) at resonance for viscous; loss-factor peak
  for structural) to <= 2%, and Rayleigh ζ_i = α/(2ω_i)+βω_i/2 matches the eigen-damping.
- **Gate D2 (damping identifiability, discretization):** on a synthetic FRF at the caches' 2 Hz resolution,
  the FRF-band model-fit recovers a known ζ to within a stated tolerance for well-separated modes AND FLAGS
  (returns not-identifiable) for a mode whose half-power band < ~1.5 grid spacings. Prove the resolution limit
  is respected, not ignored.
- **Gate F (FDAC/FRAC/FRSF correctness):** on synthetic pairs — (i) identical FRFs -> FRAC=1, FRSF=1, FDAC
  ridge on the diagonal; (ii) a pure frequency shift -> raw FRAC drops but FDAC ridge tracks the shift and
  FDAC-aligned FRAC ~ 1 (proves alignment does its job); (iii) a pure amplitude scale -> FRAC ~ 1 but FRSF =
  the scale (proves FRSF isolates amplitude); (iv) 180-deg phase flip -> improved (cosine) FDAC = -1, not +1.
- **Gate O (sensor observability — NEW, per §4):** compute the self-MAC of the analytical target modes at the
  84-channel sensor set (off-diagonals) and an EfI/Fisher-information rank of the target-mode partition; report
  which measured modes / hard-region shapes are UNOBSERVABLE (rank-deficient) at the delivered sensor set.
  Partition the A0 residual into observable vs unobservable-subspace components. This BOUNDS the reachable
  headroom: residual living in the unobservable subspace cannot be fixed by ANY updating (data-limited, not
  model-limited) — a first-class reported result, and it contextualizes every S1/S4 outcome.
- **Anti-cheat gate (checker grep):** the selection score module contains NO per-channel/per-mode amplitude
  OR damping fit (only global gain + the low-dim physical damping vector); marker `# NO-PER-MODE-LSQ` and
  `# LOW-DIM-PHYSICAL-DAMPING-ONLY` present; damping dimension <= 10 per candidate.
Failures here BLOCK science until fixed.

## 8. Sampler and compute policy
NUTS/HMC (numpyro, x64) ONLY for finalists+A0+A0d posteriors (θ + low-dim damping); all screening MAP/
deterministic and labeled NO-sampler. Damping enters the differentiable FRF likelihood smoothly (structural η
via complex stiffness; keep the resolvent conditioned near degenerate clusters — reuse the completed run's
Tikhonov shape-derivative fix if shapes enter a gradient path). Detached-launch every long job; resumable per
(track, round, candidate); pin BLAS for small dense math; let sparse full-order eigensolves thread normally.
`runtime.json` with `active_runtime_s` + `elapsed_wallclock_s`.

## 9. Workspace, gate files, checker (exact order)
1. `artifacts/reports/shocksat_frf_damping_updating_<YYYYMMDD>/` with `code/ out/ logs/ figures/ data/`.
2. Gate files FIRST: `priority_deliverables.md`, `question_framing.md` (§4 verbatim + any tightening),
   `quantity_contracts.md` (FRAC/FDAC/FRSF definitions with numerator/denominator/units, band, alignment
   convention; damping params with units + physical bounds; net-CG per netcg), `assumptions_ledger.md`
   (ζ bands + priors, Rayleigh α/β, joint η, FDAC band-selection rule, alignment method, resolution limit,
   all with values/units/sensitivity priority), `decisions_log.md` (D0…).
3. `check.py` + SHA-lock (`CHECKER.sha256`) BEFORE science. Encode at minimum: gate files exist; V1-V5 + D1/D2
   + F + O pass; query-budget from query_log; no-dev-FRF-reads grep; exact-basis rule for decision scores;
   no-amplitude/damping-LSQ grep + damping-dim<=10; physical-damping bounds on finalists; vault freeze ordering
   + touched-once; NUTS diagnostics; leave-modes-out present; S4 ablation present; figures + legibility QA;
   runtime.json; statuses per Result Status Standard. IMMUTABLE during the trial. `bash run_all.sh` = one-command.
4. A0 + A0d. 5. Tracks A1/A2. 6. Finalists + NUTS + Q/H + S4 ablation. 7. Vault. 8. Packet.

## 10. Deliverables
- `packet.md` — method summary up front (forward model incl. damping, FRF likelihood, FDAC/FRAC/FRSF
  definitions, data counts, inferred/fixed/not-inferred incl. which damping params are identifiable at 2 Hz),
  run-specific graphical model, S1/S2/S3/**S4** verdicts with numbers, the observability-bound (Gate O), the
  P1'-vs-P3 alignment-gain quantification, dev-vs-vault gaps, winner's-curse Ns, all caveats. ML/stats terms in
  plain English per AGENTS; structural-dynamics terms used directly.
- `findings.md` — headline never stronger than checker output.
- Figures (Tufte + lint, saved .py, run/convergence stamps): money figure (dev P1' trajectory agent vs random
  vs A0 vs A0d, vault overlaid); FDAC ridge + FDAC-aligned-vs-raw FRAC (the alignment effect); FRSF/damping
  field before/after for the winner; observability map (Gate O, observable vs unobservable residual); S4
  ablation bar (shape-only / damping-only / both / A0); funnel; graphical model.
- `out/query_log.jsonl`, `out/round_r*_summary.md`, `out/diagnosis_r*.json`, `VAULT_FREEZE.sha256`,
  `REUSED_code.sha256`, `runtime.json`, `checker_report.json`.
- Continuity (append-only, END only): one `notes/runs.md` entry + one `docs/report/project_log.md` row, status
  copied verbatim from the checker.

## 11. Autonomy rules (no human stop-points)
- Resolve ambiguities yourself using this file's defaults; record every non-obvious resolution in
  `decisions_log.md` BEFORE acting. If two readings are cheap, do both, label both.
- Blocked != stopped: on a component failure, document the exact blocker + evidence, apply the pre-registered
  fallback, continue. Only a violated integrity rule (checker edit, vault ordering, budget, physical-damping
  bound breach presented as a win) has no fallback — that work is withdrawn, not patched.
- Never claim success without checker output. Never present a screen as a posterior, a proxy as the metric, a
  per-channel amplitude/damping fit as physical damping, or a raw FRAC as an FDAC-aligned one. A falsified
  pre-registered claim is a GOOD outcome — report it with the same care as a win.
- Carry the completed run's two hard-won guards as NON-NEGOTIABLE: every decision-relevant score is EXACT-BASIS
  (spot-check <= 0.3%; enrich if it fails), and every θ_MAP / damping-MAP is DETERMINISTIC MULTI-START. The
  completed run showed a parametric control transiently "passing" the S1 threshold purely from these two
  artifacts — do not let it happen again.
- Crash/compaction recovery: re-read this file + your gate files + query_log, restate state in one line in
  decisions_log, resume from partial results.

---
### Lead's honest note to Andrew (delete before dispatch)
This card reframes "can agentic remeshing improve ShockSat" (answered: no) into "can an FRF-domain updating
loop with the RIGHT levers improve held-out FRF AMPLITUDE, and is damping the lever?" It is the fair,
literature-blessed test the completed run did not run, and it finally exercises damping — the lever every prior
thread flagged and never tested. My honest prior: the SHAPE family stays null; the DAMPING family may sharpen
amplitude (FRSF) but FDAC-aligned FRAC gains are uncertain because (a) the modal domain is already correlated
and (b) Gate O may show the hard-region residual is sensor-set-UNOBSERVABLE = data-limited. Any of the four
outcomes is publishable: damping wins (the lever was mis-specified, not the method) / damping sharpens
amplitude but not correlation (the wall is shape, confirmed a third way) / Gate O proves data-limited (buy the
>200 Hz + multi-ref test) / clean null (the strongest "stop remodeling ShockSat" statement yet). Parallel
option: run the SAME loop on the MPL test stand (uncorrelated, real headroom) as the "can an agent correlate
from scratch" demonstration — I recommend ShockSat FIRST (controlled A/B, reuses all infrastructure, directly
tests the literature critique), MPL as the immediate follow-on.
