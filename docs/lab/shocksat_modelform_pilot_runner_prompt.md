# Runner card C — MODEL-FORM PILOT: does an agent with GENUINE geometry/element/connectivity/mesh edits
# beat random, and does ANY model-form edit move held-out FRF? (post-review item 5)

**Paste-and-run: you are an autonomous runner agent. Execute end-to-end without stopping for approval. A
falsified pre-registered claim is a VALID outcome. Never fabricate; never claim beyond your checker's
output.** This is the LARGEST of the three post-review cards (~1–2 days incl. detached eigensolves on the
16 GB Mac). Run AFTER cards A and B (their outputs are inputs here); keep all eigensolves SERIAL.

Date issued: 2026-07-16. Author: lead (Claude/Fable), dispatched by Andrew, incorporating the GPT-5.6
review's recommended pilot design (`shocksat_fullspec_review_gpt56_20260716/next_steps.md`).
Workspace (create): `artifacts/reports/shocksat_modelform_pilot_<date>/`
READ-ONLY: the full-spectrum study + review + repair workspaces, the true-remodel loop workspace
(`shocksat_true_remodel_loop_20260706/` — its `actions.py`/`femlib.py` are your reuse base), all locked
checkers, durable rules.

## 0. Re-ground (mandatory)
`AGENTS.md`, `docs/compute_protocol.md`; the study's `findings.md` POST-REVIEW box + D16/D17; the review's
C7 + next_steps pilot spec; the true-remodel loop's `findings.md` (its evaluation traps are your traps);
Card A's `out/exact_rerank.json` (the screening-vs-exact reordering — motivates the scoring rule below).
D0 in your `decisions_log.md`. Verify your tool's compaction behavior.

## 1. The question (pre-registered)
The prior loops never gave the AGENT genuine model-form freedom: the full-spectrum agent proposed only
thickness/scale/split (zero refine/rbe2; D16), and NEITHER track has ever tested element formulation or
geometry. Two hypotheses, each falsifiable:
- **HQ1:** at equal budget and with STRATIFIED proposals across edit classes, an amplitude-compass agent
  beats seeded random on held-out sub-200 P1′, evaluated on EXACT bases (≥1×paired-fold-SE).
- **HQ2:** at least one GENUINE model-form edit class (connectivity/mesh/element/geometry — NOT property
  scaling) produces an exact-basis held-out improvement over the A1 baseline ≥1×paired-fold-SE.
Falsification of both = "model-form freedom does not move held-out FRF here" — the strongest version yet of
the standing negative, and a publishable close-out of the remodeling arc.

## 2. The edit-class menu (executable operators; build ONLY on the validated true-remodel grammar + minimal
new operators — validate every NEW operator before science, V-gates below)
1. **connectivity** — `rbe2_soften` (existing, validated) + NEW `rbe3_convert` ONLY IF you can implement and
   validate it (interpolation constraint replacing rigid spider); if not implementable cleanly, document and
   drop the sub-operator (the class still exists via rbe2_soften).
2. **mesh-density** — `refine` (existing true conforming 2×2/4× subdivision with hanging-node MPCs).
3. **element-formulation** — NEW operator: per-region bending formulation/parameter change via the exposed
   fe_core knobs (e.g. bend_ratio / transverse-shear ts_t per PSHELL region — physically a Kirchhoff↔Mindlin
   stiffness change). Validate on a patch test before use (V-gate).
4. **geometry** — NEW operator, SMALL scope: node-coordinate field edits limited to (a) plate/panel
   flatness/warp (scale z-deviation of a panel's nodes) and (b) joint offset shifts (translate a bracket
   interface line by ≤ element size). Mass/stiffness reassembled from moved coordinates (the existing
   assembly path already does this). Validate: RBM test (6 zero modes preserved) + a known-answer check
   (warping a flat plate must shift its drumhead modes in the analytically-expected direction).
5. **property control** — thickness/scale (existing): the CONTROL class the model-form classes must beat.
V-gates: each NEW operator gets a validation script + `out/vgate_<op>.json` BEFORE any scored use (RED in
your checker if a scored candidate used an unvalidated operator).

## 3. Loop protocol (both tracks identical except proposal source)
- **3 rounds. STRATIFICATION IS THE RULE (the review's key fix):** each round, EACH track proposes exactly
  2 candidates per class × 5 classes = 10/round → 30 per track total (60 scored queries; budget ≤80 each,
  G-gate). The agent may not substitute property edits for model-form slots.
- **Agent compass:** TRAIN-side per-channel amplitude residual diagnosis (reuse `diag_wide.py` pattern)
  EXTENDED with model-form-pointing diagnostics: per-region MAC defect vs survey shapes (shape errors point
  at connectivity/geometry), residual-vs-mesh-size correlation (points at refinement), and peak-width misfit
  (points at formulation). Every proposal carries an explicit diagnosis→class→edit link (round summaries).
- **Random control:** same grammar, same stratification quota, seeded (record seeds).
- **SCORING RULE (locks in the D22/D15 lesson): every SCORED number is EXACT-basis.** For each candidate:
  own-space eigensolve k=200 at θ=1 → multi-start θ_MAP (≥5, deterministic) → **enrich at θ_MAP** (second
  solve, exact-by-construction) → score at ones. NO θ=1-basis screening numbers are ever reported as
  scores; if you need cheap triage to pick which 10 of >10 ideas to build, triage on diagnosis only, never
  on a reduced-basis score. ~2 solves × 60 candidates ≈ 120 eigensolves ≈ 12–20 h detached, serial,
  resumable — this is the cost of not repeating the trap. Log every solve.
- **Complexity/runtime penalty (review requirement):** report alongside every candidate its ΔDOF, Δn_params,
  and solve-time ratio vs baseline; the FINAL ranking table shows score AND complexity so a tie goes to the
  simpler model. Pre-register: a candidate whose exact gain < 1×SE while ΔDOF > +10% is labeled
  not-worth-it regardless of sign.
- **Finalists:** top-2 per track get per-fold θ_MAP refits (θ_MAP per fold on train drives only — NO
  cross-fold reuse of any fitted object; the C6 lesson) and the paired-fold S-tests. Vault: NOT read.
  (The +XY vault has been read 3× by this program; a 4th read needs Andrew's explicit pre-registration —
  default is NO vault leg; say so in the packet.)

## 4. Pre-registration + checker (BEFORE any science; the hardened standard)
`priority_deliverables.md`; `question_framing.md` (HQ1/HQ2 verbatim + the scoring/stratification/penalty
rules); `quantity_contracts.md` (P1′ convention copied from the study; paired-SE convention);
`assumptions_ledger.md` (operator specs with numbers). `check.py` run-on-empty (RED), SHA-locked, never
edited, encoding: (1) **finiteness of every reported statistic** (NaN/null = RED); (2) stratification quota
met per round per track; (3) every scored number tagged exact-basis (grep: no score path touches the θ=1
projection); (4) V-gates precede first scored use per operator; (5) no cross-fold reuse of fitted objects
(fold-provenance recorded per finalist refit); (6) budgets + seeds; (7) leakage (train_keys exclude fold;
no vault reads); (8) complexity table present; (9) figures scripted/linted/QA'd; (10) runtime.json;
(11) self-SHA. Empty-workspace run must be RED before lock.

## 5. Sampler rule
The loop scoring is deterministic (multi-start MAP) — declare it per the AGENTS Sampler Decision. Do NOT
run NUTS on candidates (the study established amplitude-posterior multimodality; a non-converged posterior
per candidate adds nothing). IF Andrew later wants posterior bands on the winner, that is a follow-up card
(TMCMC per the compute protocol), not this one.

## 6. Deliverables
`packet.md` (method summary first; the stratified agent-vs-random × class results table is the centerpiece:
5 classes × 2 tracks, exact scores ± fold SE + complexity columns), `findings.md` (HQ1/HQ2 verdicts, per
class, plain English), `out/verdicts.json`, ≥5 figures (class×track table figure; diagnosis→proposal link
map; exact score vs ΔDOF scatter; best-candidate FRF overlay vs data on a held-out drive, log-frequency
axis; run-specific loop schematic), `decisions_log.md`, `run_all.sh`, checker report. Continuity:
`notes/runs.md` + `docs/report/project_log.md` row, status copied from your checker.

## 7. Honest failure modes (expected; report, don't panic)
New operators may fail their V-gates (drop with documentation — a 4-class pilot is still valid, say so).
Geometry edits may be numerically fragile (element quality — check Jacobians, reject bad candidates as duds
with reasons). Model-form classes may ALL lose to the property control (that is HQ2 falsified and is the
headline). The agent may tie random again even stratified (HQ1 falsified → the impotence result finally
covers genuine model-form freedom, closing D16's gap). 120 serial eigensolves will take a long wall-clock
time — checkpoint per candidate, survive laptop sleep, and NEVER trade the exact-basis rule for speed.
