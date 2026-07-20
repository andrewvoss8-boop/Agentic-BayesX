# decisions_log.md — Card F: Bayesian MODEL-CLASS SELECTION (parameterization + damping) for the hard ShockSat accels

**One-line state (re-grounding routine, update at each step):**
GOAL = evidence-ranked (Ockham-penalized) comparison of competing model classes M0–M5 for the 8 hard accels,
fixed-MAP θ (analytic statFEM evidence, Stage 1) then flexible θ (TMCMC, Stage 2), cross-checked by L5 held-out
QOI. LAST DECISION = D3 below (observable framing). NEXT ACTION = build Stage-1 analytic-evidence loop on the
reduced 74-DOF model. OPEN AMBIGUITIES = (i) Stage-1-checkpoint vs full autonomous run (surfaced to Andrew);
(ii) M1 per-PID reduced-block construction approach (D5).

Status legend (AGENTS three-tier): GREEN threshold met / YELLOW miss-understood-non-fatal-with-caveat /
RED blocking. A class is "preferred" ONLY if its evidence wins AND the evidence is prior-robust AND the
observable is stated. Evidence ≠ held-out predictive — both reported, never conflated.

---

## D0 — Inherited constraints (carried from Cards A/D/E; do NOT re-open)
- **Subject:** plain standalone 9-group ShockSat ONLY (no tray). Reduced 74-DOF modal model
  `K(θ) = A_fix + Σ_g θ_g A_g`, mass = I, 9 groups (alphabetical): al_welds, angle_brackets, bottom_box,
  contact, cross_beam, joints, plates, steel_welds, top_box. Forward eigensolve ~24 ms (reduced) vs ~290 s
  (full-order, > tool timeout → detached + resumable).
- **COPY-never-edit** inherited FEM/code. Reused code copied byte-identical from
  `statfem_real_validation_20260617/code/` (core, realfrf, modal_feature, heldout_qoi, score, tmcmc,
  schneider_faithful); `data/` small files copied, 252 MB `measured_frf_cache.npz` symlinked read-only;
  Card D diagnosis JSONs copied to `out/cardD_inputs/`. `realfrf.py` reaches sibling workspaces by relative
  path (`WS.parent/...`) — resolves because this workspace is also under `artifacts/reports/`.
- **Validate the BASELINE first** (M0 evidence + L5 held-out QOI reproduced) before any new class.
- **Scope every claim to exactly what was tested.** Forbidden over-claims from Card D/E: "no model change can
  improve it" (only the COARSE 9-group stiffness family was Pareto-optimal), "it's shape not damping" (the
  participation÷damping confound), "e07 improves correlation" (greedy-pairing artifact).
- **Re-pairing-robust** metrics only (tracked continuation / cross-orthogonality), never greedy best-MAC.
  Lead with evidence (logZ ± cross-run stability) + held-out QOI, not MAC.
- **Sampler:** NUTS = multimodality DETECTOR; **TMCMC** = evidence engine (`tmcmc.run_independent` returns
  log_evidence + cross-run R̂/ESS/div). A non-converged or unstable-evidence class is YELLOW, NOT a ranking
  input. Convergence gate: max R̂ ≤ 1.05, min ESS ≥ 200, div < 2%, ≥4 independent runs.
- **Compute:** float64, pin `OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`; reduced model for Stage-1 + fast
  loops; full-order eigensolves and TMCMC DETACHED + resumable; record `runtime.json`.
- **SURFACE to Andrew (do NOT self-apply):** any durable-rule/checker/sampler-standard change; any claim the
  evidence-winning model should REPLACE the inherited FEM; the `docs/report/project_log.md` row. Model classes,
  evidence tables, and diagnoses are study artifacts (no stop).

## D1 — Evidence / Bayes-factor machinery (cite, do not re-derive)
Sources: Girolami–Febrianto–Yin–Cirak 2021 statFEM (CMAME 375:113533) §3.4/§4.1.5; Kiran–Das–Bansal 2025
(Prob. Eng. Mech. 80:103761) §5. (Equation numbers carried from Card A/D `references_reviewed.md`.)
- **Marginal likelihood (evidence):** `p(Y|M_j) = ∫ p(Y|θ,M_j) p(θ|M_j) dθ` (Kiran Eq 43).
- **Analytic statFEM evidence (Gaussian construction):** `p(Y|M_j) = N(ρ P ū, C_d + C_e + ρ² P C_u P^T)`
  (statFEM Eq 38) — cheap, used at fixed-MAP θ (Stage 1). For our **modal-feature** observable the mean is the
  FEM modal frequency vector at θ_MAP and the covariance is (model-prediction variance C_u) + (discrepancy C_d)
  + (extraction/measurement noise C_e); the model class sets the *structure* of these terms.
- **Model posterior + Bayes factor:** `p(M_j|Y) ∝ p(Y|M_j) p(M_j)`; `BF_{12}=p(Y|M_1)/p(Y|M_2)`
  (statFEM Eq 52–53). Flat model priors ⇒ rank by log-evidence; report posterior model probabilities too.
- **Ockham's razor (automatic):** `log p(Y|M_j) = E_post[log p(Y|θ,M_j)] − KL(post‖prior)` (Kiran Eq 44) =
  (avg goodness-of-fit) − (information gain). A richer model wins ONLY if better fit beats added complexity.
  statFEM §4.1.5: the evidence can prefer the SIMPLER model even when a richer one fits better → a principled
  "the richer form does not earn its complexity" is a legitimate WIN.
- **Computing it:** Laplace (Kiran Eq 45) ONLY if globally identifiable; our problem is locally identifiable /
  multimodal (Card A) → TMCMC (returns evidence; `tmcmc.py`). Report cross-run logZ stability (±); an unstable
  logZ is not usable (Card A D10).
- **Evidence pitfalls honored:** (a) evidence is **prior-sensitive** → informative priors + a prior-width
  sweep; a diffuse prior biases toward simpler models. (b) **Large raw data overwhelms the prior and biases
  toward complex models** → use **modal-feature statistics** as the data (Kiran [72,222]) = our L5 observable.
  (c) ARD considered for the new local parameters.

## D2 — Candidate MODEL CLASS ladder (parameter vector + prior)
(θ = the 9 global group multipliers, LogNormal(0,0.25); MAP from Card A L5 = bottom_box 0.90, cross_beam 0.81,
top_box 1.05, plates 0.98, rest ≈ 1.0.)
- **M0 (baseline):** as-received reduced FEM, uniform ζ=1%, θ@MAP, statFEM iid discrepancy (σ_d, σ_e).
  REFERENCE class. Reproduce its evidence + L5 held-out QOI first.
- **M1 (richer LOCAL stiffness):** M0 + a *small* set of local interface stiffness params (split
  bolted-joint bush_801 / bulkhead-adjacent / strut PIDs out of the coarse `joints`/`plates`/box groups).
  Tests whether expanding the achievable shape family beyond the 9-group multipliers (proven Pareto-optimal in
  Card D, 0/6000) earns its complexity. Build via per-PID reduced blocks (D5). Prior LogNormal(0,0.25), ARD-able.
- **M2 (Rayleigh damping):** M0 + C = α0 M + α1 K (2 params). Priors informative from Card D measured ζ.
- **M3 (NON-proportional localized damping):** M0 + C = α0 M + Σ_g β_g K_g on identifiable shell groups
  (Card D `damping_gate.json`: damping share lands on top_box 0.32 / plates 0.25 / cross_beam 0.16 /
  angle_brackets 0.14 / al_welds 0.13; bottom_box / steel_welds / joints / contact ≈ 0). Das–Debnath 2020 form.
- **M4 (correlated discrepancy):** M0 + Schneider additive space×freq discrepancy (`schneider_faithful.py`)
  instead of iid. Tests whether structured discrepancy explains the residual better per logZ.
- **M5 (combinations):** evidence-best of {M1,M3,M4} stacked — does stacking earn its complexity?

## D3 — KEY METHODOLOGICAL DECISION: which observable the evidence uses (flagged to Andrew)
The card says rank by evidence on the **modal-feature observable** (the well-behaved data that converges,
Kiran pitfall (b)). But the modal **peak-FREQUENCY** observable is essentially **blind to damping**: the damped
natural frequency is ω_d = ω_n√(1−ζ²), so at the measured ζ = 0.06–1.8% the frequency shift is ~ζ²/2 ≈ 1e-4
(below the ~7% modal-frequency discrepancy floor). Therefore on the FREQUENCY observable:
- **M0 vs M1 vs M4** compete cleanly (stiffness parameterization and discrepancy *structure* move/explain the
  frequencies) — this is where the evidence ranking is decisive and the single-impact confound is weakest.
- **M2/M3 (damping)** are ~indistinguishable from M0 on frequency ⇒ the evidence will Ockham-penalize their
  extra parameters → "damping does not earn complexity *on the frequency observable*." That is the correct,
  principled outcome, not a failure — but it is NOT a statement that damping is unimportant.
- Damping's signal lives in **amplitude**, where the resonant peak ∝ φ_s φ_d / ζ = participation÷damping is
  CONFOUNDED at one drive node (Card E). So M2/M3 are additionally scored on a **peak-AMPLITUDE** modal
  observable AND the **held-out QOI** (where the confound bites), with the confound stated explicitly.
**Plan:** Stage-1 evidence is computed on BOTH a peak-FREQUENCY observable (decisive for M0/M1/M4) and a
peak-AMPLITUDE observable (indicative for M2/M3, confound-limited). The headline evidence ranking is on
frequency; damping conclusions are cross-checked by held-out QOI and labeled confound-limited. Surfaced to
Andrew 2026-06-19; proceeding under this interpretation unless he objects (study-artifact decision, no stop).

## D4 — Workspace + reuse provenance
Created `artifacts/reports/shocksat_modelclass_L5_20260619/`. Smoke-tested: reduced model loads from this
workspace (A_fix 74×74, 9 groups), nominal modes 54.6/73.1/73.7/88.0/104.7/113.8/117.4/122.2 Hz (matches Card A).
Cache symlink resolves (263 MB). Hands OFF Card A/B/D/E workspaces (read-only).

## D5 — OPEN: M1 per-PID reduced-block construction (resolve before Stage-1 M1)
The reduced model only carries the 9 aggregated group blocks A_g. M1 needs finer (per-PID / per-region)
reduced stiffness blocks. Planned approach: project the Card D full-order per-PID K blocks through the reduction
basis (V_keep) once → reduced per-PID blocks; build a one-time cache; Stage-1 M1 loop then stays fast. Verify
Σ(per-PID reduced blocks within a group) == the existing group A_g (machine-zero) as an integrity check.
Alternative if per-PID full blocks are unavailable at reduced level: build M1 at full order detached (~290 s/solve).

## D6 — CONCURRENCY CONFLICT with an ACTIVE Card E thread (surfaced to Andrew; HOLDING before compute)
While setting up, `notes/memory.md` gained a **Card E** CURRENT-STATE block: a parallel lead-as-runner thread in
`artifacts/reports/shocksat_richmodel_L5_20260619/` ("does a richer model form SHARPEN the L5 held-out QOI at the
8 hard accels?"). The Card F prompt itself states **"Card F SUBSUMES Card E."** Running both concurrently risks
(a) duplicated/wasted compute, (b) compute thrash if both launch detached NUTS/TMCMC, (c) two overlapping/possibly
conflicting answers. Card E has ALREADY produced artifacts that ARE my open items / gates:
- `out/perpid_reduced.npz` + `code/richmodel.py` — per-PID reduced K blocks (W=T@V_keep[:,6:], B_pid=WᵀK_pidW;
  θ=1 reconstructs nominal to 6e-12/6e-10). = exactly my D5 (M1 construction). REUSE as a read-only input.
- `out/identifiability_rich.json` — the richer-stiffness identifiability gate (strain-energy + FIM): NEW
  identifiable local dirs bottom_box:shell_101 (peak SE-frac 0.94, 21× over the σ_w2≈0.045 floor),
  top_box:shell_201, plates:shell_701/601, cross_beam; bolted-joint CBUSH801 MARGINAL/prior-dominated; welds/
  contact/shells 103/203/501 below floor. = my P5 (M1 identifiability) + corroborates D3's confound point.
- Card E is ITSELF paused at a compute-commitment checkpoint awaiting Andrew (same fork as my A1).
**DECISION NEEDED (Andrew):** (1) fold Card E into Card F — I reuse Card E's perpid_reduced + identifiability as
Card F inputs, Card F's evidence ranking becomes the umbrella deliverable, Card E's "sharpen held-out QOI" becomes
the P4 cross-check; OR (2) keep them separate with an explicit division of labor. Until resolved I will NOT launch
any compute (no thrash, no duplicate). Read-only reuse of Card E artifacts only; HANDS OFF Card E workspace.

## D7 — STAGE-1 analytic-evidence RESULT (stiffness parameterization + M4 discrepancy; `out/stage1_evidence.json`)
Observable = 27 matched measured modal eigenvalues ω̂²; θ fixed at L5 MAP; residual median 2.98% (vs σ_w2≈6.9% floor).
Hyperparameters type-II ML'd; new-stiffness-param prior width σ_prior swept {0.15,0.25,0.40}; ranking ROBUST (no flip,
no top-model flip). type-II-ML'd-hyperparameter BIC correction applied (marginalized stiffness params are NOT
penalized — already Occam-penalized inside the marginal likelihood; only optimized hyperparameters get 0.5·k·ln n).
**BIC-adjusted ranking (P(M|Y)) @ σ_prior=0.25:**
1. **M0_fixed_thetaMAP −331.48 (P=0.906)** — as-received θ-MAP FEM + iid discrepancy = WINNER.
2. M4_corr_discrepancy −333.75 (P=0.093) — RAW logZ is best (−328.8, +1.0 over M0_fixed) but does NOT survive the
   complexity penalty for its 2 extra hyperparameters; drives rmix→0.999, ℓ_f≈4.2 Hz. SUGGESTIVE, not decisive.
3. M1_joint_split −339.14 ≈ 4. M0_base9 −339.28 > 5. M1_box_split −340.16 > 6. **M1_full_rich −340.70 (worst).**
**Findings (scoped to the modal-FREQUENCY observable, fixed-MAP θ):**
- **Richer LOCAL stiffness (M1: box/joint/plates splits, up to 16 params) does NOT earn its complexity** — every M1
  variant ranks ≤ M0_base9; full_rich (16 params) is worst. = Ockham-penalized evidence-based confirmation AND
  EXTENSION of Card D's "coarse 9-group Pareto-optimal" to the LOCAL splits Card D never tested. (statFEM §4.1.5
  "simpler can win" — a legitimate principled WIN.)
- **Structured/correlated discrepancy (M4) has the best RAW evidence** → a real hint the residual is structured, not
  iid — but NOT decisive at fixed θ once its hyperparameters are penalized → the rigorous test is Stage-2 TMCMC with
  proper hyperpriors + θ free. This is the candidate "improvement" lever (structure the discrepancy, don't add FEM DOFs).
- **Damping M2/M3 are provably FREQUENCY-BLIND** (damped-freq shift 5.5e-5 ≪ 0.069 floor) → judged on amplitude /
  held-out QOI only (confound-limited), per D3.
**Caveat:** Stage 1 holds θ FIXED so M1 can only inflate covariance (conservative for richer classes). Stage-2 TMCMC
(θ free) lets the mean move = the rigorous re-rank. Stage-1 = a cheap conservative screen, prior-robust.

## D8 — STEERING (Andrew) + interface-CBUSH damping identifiability gate (`out/identifiability_M3_cbush.json`)
Andrew (2026-06-19): DEFER evidence-based selection (PAUSE Card F Stage-2 + Card E richer-stiffness); prioritize
(1) damping methods — "complex damping parameter in CBUSHes at interfaces" — and (2) shape-driven topology-
alternative agentic remodeling. Stage-1 evidence kept as the logged baseline. Ran the cheap GATE-FIRST step (AGENTS
Modal Identifiability gate) for the CBUSH-damping idea — structural loss factor η_g on interface bushes, modal
contribution ζ_k += 0.5 η_g f_{k,g} (f = SE fraction), observable = un-confounded half-power bandwidth Δf=2ζf.
RESULT: **FRF df=1.25 Hz; typical ζ=0.32%, max 1.05%; half-power width at 100 Hz ≈0.6 Hz ≪ 2.5 Hz needed →
bandwidth NOT resolvable for the light modes.** Interface SE (peak over modes): **bush_801 (bolted joint) 0.150 @
151 Hz (near ch52 "Al box above bolted joint") — the highest**; bush_802 0.087, bush_902(contact) 0.058, rest <0.06;
803/807 below floor. Group context: joints peak 0.198 @151 Hz (typical ~3% = Card D), vs shells plates 0.998 /
bottom_box 0.988 / top_box 0.896. **VERDICT: NO interface CBUSH clears identifiability from THIS single-impact FRF**
— two compounding blockers: (a) SE-dilution (most bushes store little SE), (b) FRF resolution can't resolve the
un-confounded bandwidth for light ζ. The idea is PHYSICALLY sound (bush_801 IS in the 151 Hz load path), the blocker
is the OBSERVABLE/data, not zero SE. CAVEATS: reduced-model SE (indicative; full-order is rigorous); bw check used
TYPICAL ζ not per-mode (the 151 Hz joint mode may be more damped — refine). Connects to the data-information ceiling.

## D9 — AUTONOMY GRANT + broadened scope (Andrew 2026-06-19): "run it all, do not stop for permission, fully
explore the space; goal = an honest calibrated digital twin with CIs that TIGHTLY capture the held-out data
BETTER than the original FEM." Scope of THIS workspace broadens from Card-F evidence-selection to the integrating
**calibrated-twin TIGHTENING program**. Card F evidence (Stage-1) kept as a logged baseline; its `check.py` stays
locked (paused thread). New deliverables get a NEW immutable checker `check_twin.py`. STILL surface (no self-apply):
durable-rule/checker/sampler-standard changes; any "replace the inherited FEM" claim; project_log row.
PROGRAM PLAN (execute autonomously, gate-first, detached where heavy, three-tier honesty, scope every claim):
- **Phase A — DAMPING FEASIBILITY (cheap, decisive):** A1 per-mode measured ζ + per-mode bandwidth resolvability
  (not typical); A2 per-mode complex SDOF circle-fit on the real FRF (phase curvature → ζ even sub-bin) with
  cross-channel spread + fit-quality; A3 full-order joint/CBUSH SE (rigorous, detached ~290s if warranted).
  VERDICT = which modes/CBUSHes support a credible damping inference.
- **Phase B — DAMPING TWIN (if A supports):** complex-mode / Das-Debnath localized structural loss factors where
  SE-supported (η_801 + global background), inferred from the per-mode-ζ observable; NUTS→TMCMC, convergence gate;
  held-out QOI — does pinning ζ TIGHTEN the peak-amplitude CI vs L5-freq-only while keeping coverage?
- **Phase C — SHAPE-DRIVEN TOPOLOGY:** degenerate-safe subspace-MAC likelihood + joint connectivity/topology
  alternatives (partial-bond / local flexibility), scored by HELD-OUT QOI (never in-sample MAC).
- **Phase D — INTEGRATION + GOAL:** best combined twin (damping + shape/topology where each earns it) vs the
  original FEM, held-out QOI coverage AND sharpness; VOI/data-ceiling (what the 3 un-used hits / multi-ref buy);
  figures + packet + check_twin + runtime.

## D10 — PHASE A+B DAMPING VERDICT (decisive, honest PIVOT): damping is NOT the lever for the wide held-out CI
**Phase A (feasibility):** (1) damping is FREQUENCY-blind (Stage-1, shift 5.5e-5). (2) The un-confounded damping
observable (half-power bandwidth Δf=2ζf) is UNRESOLVABLE in our FRF: df=1.25 Hz, and the FRF carries an exponential
WINDOW adding ζ_w(f)=1/(2π f τ), τ=0.267 s = **0.23–1.22% over the band — comparable to or LARGER than the structure's
real modal damping** (NASA .ash measured_modes ζ 0.06–1.05%). So apparent damping ≈ window; per-mode ζ not extractable
from this single windowed hit (peaks ~1 bin). (3) Interface-CBUSH attribution is SE-diluted (`identifiability_M3_cbush.json`:
bush_801 peaks 0.150 SE @151 Hz — highest but still bw-unresolvable; rest <0.09). → We can't INFER damping here; but we
already HAVE NASA per-mode modal ζ.
**Phase B (`dampcorr_qoi_seed00.json`, 3 arms on the same L5 θ posterior; mapping verified 120 Hz→1.05%, 172 Hz→0.058%):**
- ARM0 uniform ζ=1%: σ_QOI_peak 1.112, PEAK cover 0.94, interval 1703, width 37.9 dB (= L5 baseline reproduced).
- ARM1 uniform ζ=1% **+ window**: σ_QOI 1.107, cover 0.97, interval **1306** (−23%), width 37.7 → the known window
  artifact modestly improves CENTERING/coverage (keep it as a measurement-model fix).
- ARM2 **per-mode measured ζ + window**: σ_QOI 1.167 (WORSE), cover 0.94, interval 2279 (WORSE) → injecting the NASA
  structural ζ HURTS, because the windowed/df=1.25 Hz FRF UNDER-RESOLVES the light modes (measured peaks are lower than
  the structural ζ would predict; measurement effective-damping ≠ structural ζ).
**DECISIVE:** σ_QOI ≈ 1.1 (≈×3) regardless of damping arm. σ_QOI is the **cross-CHANNEL** scatter of the peak error =
per-sensor **mode-SHAPE** error; damping is per-mode (channel-common) → absorbed by the global gain → CANNOT tighten a
cross-channel CI. **The ~38 dB held-out amplitude CI is a MODE-SHAPE error, not a damping error.** Vindicates a careful
version of Andrew's CBUSH-damping intuition (physically real) while showing it is neither identifiable here NOR the CI lever.
**PIVOT:** Phase C (shape-driven topology, scored by held-out QOI) is the real lever for the GOAL; Phase D the data ceiling.
Keep the window correction (ARM1, free centering gain). NEXT: confirm Phase B over seeds 1–3; build Phase C.

## D11 — PRIOR shape-calibration result (Card A L6/L10) + refined σ_QOI-ceiling picture + Phase C/D/E plan
Card A ALREADY tested mode-SHAPE-augmented calibration (must not re-discover): **L6** (freq+MAC, single-impact
quadrature shapes, 4 groups) σ_QOI 0.998→0.992, interval 1422→1386 = negligible sharpening; **L10** (freq+MAC on the
proper .ash EMA shapes, MAC-matched) did NOT converge (R̂ 1.026, ESS 95) and σ_QOI 1.106→1.126 = slightly WORSE.
So σ_QOI ≈ **1.0 (factor ~2.7×)** now holds across: damping arms (Phase B), frequency-only (L5), AND mode-shape
(MAC) calibration (Card A L6/L10) → strong evidence the held-out amplitude CI is a near-irreducible **data/parameter-
ization CEILING** (single impact + coarse FEM), matching the project's standing "band width is a DATA limit" finding
(Study L, cross-cutting). The GENUINELY UNTRIED model-form lever = **richer-LOCAL stiffness + shape likelihood**
(Card E's identifiable local params shell 701/101/201 were built + gated on FREQUENCY but never combined with the
MAC shape likelihood + held-out QOI). REFINED PLAN:
- **Phase C (model-form exhaustion, held-out-QOI-scored):** C1' richer-local-stiffness + MAC shape + held-out QOI
  (reuse Card A `modal_mac.py` + Card E local params); C2 1–2 joint topology alternatives (the 151 Hz / bush_801
  15%-SE mode near ch52). Honest prior: LOW (coarse stiffness+shape already failed; floor looks like data) — test anyway.
- **Phase D (the data ceiling / VOI = the high-value honest deliverable):** D1 ORIGINAL-FEM baseline (nominal θ,
  ζ=1%, deterministic point) held-out QOI = the "beat this" baseline → show the calibrated twin COVERS where the FEM
  MISSES; D2 σ_QOI-floor table (stable ~1.0 across all levers); D3 synthetic multi-REFERENCE VOI (only hit-001 raw
  exists; same-location repeats only cut noise not the confound → simulate roving drive on the FEM → how much would
  multi-reference tighten σ_QOI? = "what test data buys").
- **Phase E:** best twin (L5 freq + window correction + any C lever that earns it) vs original FEM — coverage +
  sharpness; honest GOAL verdict ("tight as one impact allows; here is what more data buys"); figures + packet +
  immutable check_twin.py + runtime.
GOAL status forming: the twin (L5+window) COVERS held-out data (94–97%) where the deterministic FEM gives a
confidently-wrong point ⇒ "better than the original FEM" in CALIBRATION; "tightly" is data-ceiling-limited (quantify via D3).

## D12 — PHASE D1 (FEM baseline) + Phase-B seed aggregate + the heavy-tailed/feature-keyed-discrepancy lever
**Phase-B aggregate (seeds 0,1,2; `dampcorr_qoi_seed0{0,1,2}.json`):** ARM0 uniform1% σ_QOI 1.094±0.027 / interval
1986±210 / cover 0.97; ARM1 +window σ_QOI 1.087±0.021 / interval **1526±160** / cover 0.98 (window = robust small
gain, KEEP); ARM2 +per-mode-struct-ζ σ_QOI 1.133±0.028 / interval 2891±433 / cover 0.94 (robustly WORSE). Confirms:
σ_QOI ~1.1 damping-immune; damping is not the CI lever.
**Phase D1 (`fem_baseline_qoi_seed00.json`):** ORIGINAL FEM (nominal θ, ζ=1%, deterministic, units-gain only) misses
held-out peak by median |err| **6.7 dB** (5.4 dB with window), **77% of channels off >3 dB, 58% off >6 dB**, max 24 dB.
Calibrated twin (L5+window) COVERS **97%**. ⇒ **GOAL "better than the original FEM" MET on calibration** (FEM =
confidently-wrong point; twin = honest CI that covers). Open issue = WIDTH (38 dB).
**NEW LEVER (honest):** the per-channel residual is HEAVY-TAILED (35% of held-out <3 dB, 45% >6 dB) → a single iid
lognormal σ_QOI must inflate EVERY channel's CI to cover the hard-channel tails. A **discrepancy keyed to a
predictable channel feature** (the 8 hard accels are known; DR / region / snap-distance / shape-quality) would keep
easy channels TIGHT and only hard ones WIDE = honest tightening (no mean change; held-out coverage keeps it honest).
Ties to Card F M4 (structured discrepancy was the raw-best Stage-1 hint). This is the most promising remaining lever
for the GOAL — more than richer-local stiffness (which Stage-1 + Card A L6/L10 say won't move the mean). Diagnostic
gate first: does per-channel residual correlate with a predictable feature? (`discrepancy_diagnostic.py`).

## D13 — PHASE C: feature-keyed (hard-region vs rest) discrepancy — honest CI TIGHTENING for the well-modeled bulk
Diagnostic (`discrepancy_diagnostic.json`): generic features (DR ρ=−0.05, snap −0.02, |z| 0.14) do NOT predict the
per-channel residual; but the 8 a-priori-hard accels average **17.5 dB** error vs **6.5 dB** rest → the residual is
predictable by the KNOWN hard-region flag. Two-population discrepancy (`heteroscedastic_qoi_seed00.json`, seed 0,
calib converged): σ_QOI(log) pooled 1.11 → **rest 0.95 / hard 1.66**. Held-out scoring:
- POOLED: overall cover 0.97 int 1298; REST(n29) int 1228; HARD(n2) int 2318.
- TWOPOP: overall cover 0.97 int 1347; **REST(n29) int 953 (−22%, cover 0.97 held)**; HARD(n2) int 7072 (honestly wider).
→ The two-population discrepancy **tightens the well-modeled ~90% of channels ~22% while keeping coverage**, and
honestly widens the 8 known hard regions. Overall mean ticks up only because the 2 held-out hard channels dominate a
small sample (per-population reporting is the honest view). This is the project's "discrepancy-by-known-region"
vision realized + ties to Card F M4 (structured discrepancy). HONEST LIMIT: even REST channels keep σ≈0.95 (≈±5.5 dB
1σ) — the coarse FEM + single-impact amplitude error is substantial across the board; the hard 8 are data-ceiling-
limited (→ Phase D VOI). NEXT: confirm seeds 1–3; Phase D (multi-reference VOI) + Phase E integration/packet.

## D14 — OVER-FITTING CHECK on the two-population discrepancy (Andrew's concern) = CONFIRMED; figure made
Andrew flagged the hard/rest split as likely over-fit / non-transferable. Tested it (`hardregion_map.json`,
`figures/fig_hardregion.png`, tufte-linted [2 advisory flags: dB stated/standard; "freq-plot" = false positive],
image-QA ok 1500×1110):
- Hard 8 avg |err| **17.5 dB** vs rest **6.5 dB** = strongly heteroscedastic (real).
- BUT NO a-priori FEM feature predicts which channels are hard: drive-distance (near-field) ρ=+0.09,
  high-mode/locality fraction ρ=−0.17, log-DR ρ=−0.05 — all ≈0. The hard set is separable ONLY by the
  hand-labeled list, which itself came from PRIOR FEM-vs-test comparison (Card D) → circular for a from-scratch tool.
- AND the residual is only WEAKLY spatially correlated: nearest-4 Moran-like corr 0.24, semivariogram ~flat
  (high nugget from d→0) → even a spatial-GP (Schneider/M4) discrepancy would NOT transfer; the error is a
  channel-specific near-field/coarse-FEM NUGGET you only learn by measuring that channel.
**VERDICT: Andrew is right — the two-population tightening (seeds 0–3: REST interval pooled 1578 → twopop 1137,
−28%, coverage 0.99→0.97 held) is REAL on this data but OVER-FIT / NOT a transferable method.** It is a
DEMONSTRATION that the discrepancy is heteroscedastic AND that, IF you have prior region characterization (a
knockdown library — the project vision §6.2), you can tighten the rest. It is NOT a claim you can predict hard
regions from the FEM alone (you can't, per the figure). Generalizable tightening ⇒ more/better DATA
(multi-reference, Phase D VOI), not a discrepancy reparameterization on one impact. Reinforces the data-ceiling story.

## D15 — STEERING (Andrew): "this is plenty of data." → DROP the more-data/VOI framing. We HAVE a full
experimental modal survey (NASA .ash: 33 mode shapes on 76 nodes×3 axes = inherently multi-reference). So the wide
held-out CI is a **METHOD limit, not a data limit**: we predict held-out sensor amplitudes from the FEM shapes
(MAC≈0.63, wrong) while the MEASURED shapes sit unused (L5 used only freqs; L6/L10 added a weak MAC term, not the
shapes themselves for prediction). DECISIVE TEST = fuse the measured shapes into the held-out predictor and see if
σ_QOI (cross-channel shape error) collapses. Construction (`measured_shape_qoi.py`, reuse `ash_match.npz`): express
each matched measured mode in reduced coords ψ_r = pinv(G)·meas_shape_r (G:132 meas DOFs→74 reduced); held-out
sensor accelerance H(s,ω)=Σ_r a_r (rows_s·ψ_r)(drive·ψ_r)(−ω²)/((1+iη_r)ω_r²−ω²) with measured ω_r, ζ_r(+window),
per-mode complex scale a_r calibrated by complex LSQ on OBSERVED channels (cross-channel SHAPE fixed by measured ψ_r,
held-out amplitude is genuine prediction). If σ_QOI drops vs FEM-shape L5 → method limit (Andrew right; plenty of
data). Phase D (VOI) CANCELLED.

## D16 — 'PLENTY OF DATA' RESOLVED: measured shapes don't tighten the CI because the QOI isn't cleanly modal
Tested using the measured shapes we HAVE (D15), carefully (rejected a buggy free-per-mode-scale modal forward that
was ill-conditioned, in-sample 25 dB; rejected a complex-MAC metric that under-stated). Clean, well-conditioned
test (`shape_pattern_test.json`): per matched mode, log-amplitude correlation of the |shape| pattern vs the measured
peak-|H| pattern across 77 channels (this is exactly where σ_QOI lives):
- ALL 20 modes: FEM-shape **0.140**, measured-shape **0.117**; well-isolated 10: FEM 0.165, measured **0.186**;
  best single mode corr ~0.3–0.5; measured beats FEM by >0.1 on only 3/10 isolated modes.
**Neither the FEM shape NOR the proper measured .ash mode shape predicts the single-impact per-channel peak-|H|
pattern (corr ~0.15).** So using the measured shapes does NOT tighten σ_QOI. The wide CI is therefore NOT "we
ignored the shape data we have" — the shapes (FEM or measured) simply don't predict THIS observable. **Root cause:
a single-impact peak accelerance at an arbitrary channel is a near-field/local/sensor-mounting/mode-overlap
quantity, NOT a clean modal quantity → no global modal model (FEM or measured EMA) predicts it well.** (Also partly
channel↔FEM-node snap error up to 6 in.) Consistent with: L5 nails held-out modal FREQUENCIES (6/6) but the
per-channel single-impact AMPLITUDE (peak AND band, both ~34–38 dB) is intrinsically wide.
**SYNTHESIS (the honest answer to all 4 of Andrew's points + 'plenty of data'):** the calibrated twin is
GREEN/tight on the modally-predictable quantity (frequencies) and BEATS the original FEM on calibration (covers 97%
vs FEM confident 5–7 dB misses); but the per-channel single-impact peak/band AMPLITUDE is poorly predicted by ANY
global modal model regardless of damping, FEM shapes, MEASURED shapes, stiffness, or discrepancy structure — so its
~38 dB CI is intrinsic to that QOI from a global model, NOT a closable data or method gap. CONSTRUCTIVE: report the
twin's tight, trustworthy predictions on the modal quantities; label per-channel single-impact amplitude as
intrinsically uncertain; the over-fit two-population result is a labeled demonstration only.

## D17 — VALUE of L5 updating on NON-HARD sensors (Andrew Q2): NEGATIVE amplitude skill vs climatology
The right value test = skill vs a CALIBRATED no-skill baseline ("climatology" = guess each held-out channel from
the population of OBSERVED MEASURED channel peaks), not just vs the deterministic FEM point (a strawman with no UQ).
`value_eval_seed00.json` (calib converged, pooled QOI-disc σ=1.11):
- **NON-HARD (n29): twin coverage 1.00 but CRPS-skill vs climatology = −0.76** (twin CRPS 69 > clim 39). FEM-point
  miss median 4.6 dB (41% >6 dB).
- HARD (n2): skill −2.79 (much worse). ALL (n31): skill −0.93.
**The amplitude twin adds NO value over climatology even on the easy sensors** — because the FEM shapes carry ~no
channel-specific amplitude info (corr ~0.15, D16) and the wide σ makes the predictive distribution worse than the
tight empirical population. (Partly the σ is over-dispersed [z_std~0.4] → a better-calibrated σ could reach ~0 skill,
but the shape gives no path to POSITIVE amplitude skill.) IMPLICATION: "beats the original FEM" (a confident wrong
point) was too weak a bar; against a calibrated baseline the amplitude updating is valueless for THIS observable.
The twin's genuine value is in the MODAL quantities — held-out FREQUENCY (6/6) where the FEM+calibration carries
real info climatology lacks; CONFIRM frequency skill (expected strongly POSITIVE) + the band-GRMS QOI + ≥2 more seeds.
This sharpens D16: the per-channel single-impact AMPLITUDE is not just intrinsically wide — the model adds no skill
over climatology for it.

## D18 — COMPLETE value picture (Q2 answered): twin value is REAL for FREQUENCY, NEGATIVE for AMPLITUDE
Amplitude (`value_eval_seed0{0,1,2}`): NON-HARD CRPS-skill vs climatology −0.76/−0.84/−1.40 (mean **−1.0**),
coverage 1.00 → the per-channel amplitude twin is worse than guessing the observed-channel population, even on
the easy sensors. Frequency (`freq_value_seed00`, held-out 11 modes): twin vs climatology CRPS-skill **+0.93**
(twin 2.1 Hz vs clim 30.2 Hz, coverage 0.82); value of UPDATING vs nominal FEM = freq error **2.10%→1.07%**
(calibration ~halves it). **ANSWER to Andrew Q2: the value of L5 updating is concentrated entirely in the MODAL/
FREQUENCY domain (strong positive skill + calibration halves freq error); for per-channel single-impact AMPLITUDE
it has negative skill (no value) even on non-hard sensors, because the FEM shapes carry ~no per-channel amplitude
info (D16) and the discrepancy is wider than the population.** Minor: freq coverage 0.82 (slightly overconfident,
could widen). This is the honest, complete framing for the deliverable: trustworthy + valuable FREQUENCY twin;
amplitude is for honest UQ/coverage only, with no skill over climatology.

## D19 — Q1 GAPS CLOSED BY RUNNING (not argued): damping + topology + snap all confirm no amplitude value
- **Snap-vs-shape (`hardregion_map`+snap):** FRF-channel→FEM-node snap is tiny (median 0.15 in, max 0.75 in);
  Spearman(|amp error|, snap)=−0.02 → the ~0.15 shape failure is GENUINE shape error, NOT a mapping artifact.
- **#2 damping inference (`gap_closure_seed00`):** band-GRMS NON-HARD CRPS-skill vs climatology = −1.02 (peak −0.80);
  a global ζ-scale moves band skill (ζ×0.5 −1.57, ×1 −1.02, ×2 −0.60) — damping IS weakly informative for band
  energy but even the best scale stays NEGATIVE → no QOI value; confirms #2 by running (a damping fit picks higher ζ
  but can't reach positive skill).
- **#3/#4 topology alternative (`gap_closure_seed00`):** softening the bolted joint bush_801 (soften 0.3) and fully
  RELEASING it (0.0) move peak skill only −0.80→−0.74→−0.66 — still firmly negative → a joint connectivity/topology
  change does NOT improve held-out amplitude; confirms #4-topology by running.
**Q1 ANSWER (now run, not argued):** every lever — damping, FEM shapes, MEASURED shapes, richer/local stiffness,
joint topology, discrepancy structure — fails to give the per-channel single-impact AMPLITUDE positive skill vs
climatology. The twin's value is FREQUENCY-only (D18: +0.93 skill, calibration halves freq err). Investigation
COMPLETE + thorough. NEXT: integrate (summary figure + immutable check_twin.py + packet + runtime), honest framing.

## D20 — DECK delivered (Andrew request, 2026-06-20): `slides/shocksat_L5_twin_deck.pptx` (18 slides, 14 figs).
Covers: exec summary + value; setup/sensors (hard vs easy); 9 calibration params (locations); strain energy
(joints SE-diluted); train/test split; scoring system; held-out FRF hard vs easy; band-GRMS; scores hard vs easy;
value (freq +0.93 vs amp −1.0); roadblocks damping / re-mesh-stiffness / likelihood; hard-region over-fit caution;
synthesis; ideal-additional-data + experiment series; status/repro. Figures (saved .py, tufte-lint [1 justified
advisory each: dB/freq-label], image-QA pass 13/13): fig_value_summary, fig_sensor_map, fig_param_locations,
fig_strain_energy, fig_train_test_split, fig_scoring_schematic, fig_frf_examples, fig_grms, fig_scores_hard_easy,
fig_roadblock_{damping,remesh,likelihood}, fig_hardregion. FRF figure uses θ-MAP + 95% discrepancy band (no NUTS;
the predictive width is the discrepancy, not the narrow θ posterior). Bug fixed: infinite while-loop when <3 hard
held out (seed 0 had 2) → now up-to-3 hard + fill easy.
**COMPUTE NOTE (surfaced to Andrew):** the IFT thread's M2 confirmation job (pid 68092, run_sweep.m2_split, launched
2026-06-19 14:28) was STUCK ~14 CPU-hours at 100% CPU on the non-converging M2 arm (whose divergence is already
documented: M2-TMCMC R̂ 129, σ_d→7.4). It was starving this machine. I terminated it (IFT runs are resumable by
design; M2 seeds confirmation can be relaunched). Did NOT edit the IFT workspace.

## D21 — ANDREW PUSHBACK (2026-06-20), all 3 valid; corrected deck+packet (no over-claim)
(1) **Likelihood breadth:** deck showed 2, program ran ≥10 (`fig_likelihood_inventory.json/png`): modal peak-FREQ
(conv, twin), INFERRED shape field L8b (conv, helps amplitude), shape-MAC L8 (conv), analytic evidence; freq+MAC-as-θ
L6/L10 (~null/non-conv), complex PHASE L4 (single-hit incoherent); whole-FRF mag (R̂104/129), peak-AMPLITUDE feature
(R̂55.8), Schneider correlated (R̂9.2). Added inventory slide.
(2) **Spatial pattern (`spatial_reanalysis.json`):** re-examined with PHYSICAL features (dist to impact/joint/strut/
dish/bulkhead) + region-categorical. MILD concentration (bolted-joint region worst 12.3 dB; dish/strut elevated) =
physically sensible, partly confirms Andrew — BUT weak predictor (region R²=0.04; proximity doesn't predict hardness).
Honestly fixed the figure title (I had pre-written "DO follow a pattern"; data says weak). Added spatial slide.
(3) **Model form — the big correction:** I WRONGLY excluded the INFERRED-shape-FIELD model form (Beck/L8b,
`modal_beck_ash.py` + climatology-skill added). 3 seeds: interval ~43% sharper, coverage→0.97, σ_QOI 0.92→0.86,
**CRPS-skill −0.68(FEM)→−0.25(inferred)** = HALVES the deficit (still <0 on one impact). `shapefield_lever.json/png`.
Corrects deck's "no model-form lever helps amplitude". Damping full inference (per-mode/complex) still a to-do.
DECK now 21 slides (added likelihood-inventory, shape-field-lever, spatial-reanalysis; corrected exec/synthesis/
over-fit). packet.md §3a corrections added. image-QA pass 16/16. Reused Card A modal_beck_ash/modal_ash_mac/modal_mac
+ ash_match.npz (copied, read-only). HONEST REVISED HEADLINE: freq value real (+0.93); amplitude IMPROVED-not-solved
(shape-field model form is a real partial lever, full skill needs multi-reference data).

## D22 — FULL per-mode/complex DAMPING INFERENCE (Andrew chose (a); closes the to-do by RUNNING)
`damping_inference.py`: per-mode multi-channel SDOF resonance fit — for each matched mode, shared (f_r, ζ_r) across
high-DR channels, per-channel complex residues marginalized by LSQ, EXACT 2-D (f,ζ) profile posterior (grid =
exact for 2 nonlinear params; strictly better than NUTS, documented). RESULT: **0 of 9 fittable modes give an
IDENTIFIED apparent ζ** — posteriors prior-dominated (48.8 Hz: ζ 0.06–5.84%) or railed to the resolution floor
(resonances sub-bin sharp). The resonance WIDTH (the only un-confounded damping signal) is below the df=1.25 Hz +
exp-window resolution for these lightly-damped modes. Since per-mode ζ is unidentifiable, the complex/non-prop
localized-CBUSH (Das–Debnath) attribution is moot (also SE-diluted, D8). → **damping is NOT recoverable from this
single windowed FRF, confirmed by RUNNING a proper Bayesian inference** (not argued). Cannot improve the amplitude
QOI (consistent with per-mode-ζ-injection-hurts + global-ζ-no-help). `fig_damping_inference.png` (tufte+QA),
deck slide 12b added → DECK now 22 slides. The honest pre-test takeaway: identifying damping needs finer-resolution /
multi-reference data (longer records / zoom-FFT / stepped-sine), the same data lever as the amplitude skill.

## Log
- 2026-06-20 D22: per-mode/complex damping inference RUN → 0/9 identified (unrecoverable from this FRF); to-do closed.
  Deck 22 slides. NO durable-rule/checker/project_log edits.
- 2026-06-20 D21: Andrew's 3 pushbacks all valid → corrected deck (21 slides) + packet. Key: inferring the shape
  FIELD halves the amplitude skill deficit (model form DOES matter; earlier over-claim fixed). Spatial = weak-but-real.
- 2026-06-20 D20: PowerPoint deck delivered (18 slides). Killed stuck IFT M2 job to free CPU (surfaced; resumable).
- 2026-06-19 D19: Q1 gaps closed BY RUNNING (damping/topology/snap all confirm no amplitude value). Investigation
  complete. Moving to integration (figure + check_twin + packet).
- 2026-06-19 D18: complete value picture — FREQUENCY skill +0.93 (calibration halves freq err), AMPLITUDE skill
  −1.0 (no value vs climatology, non-hard incl.). Q2 answered. Strong honest stopping point. Still owe the #2/#4
  run-it gap closures (Q1) but value-eval shows amplitude value is ≤0 regardless, so they confirm-by-running.
- 2026-06-19 D17: value-vs-climatology = NEGATIVE amplitude skill on non-hard sensors (twin worse than guessing the
  population). Confirming over seeds + adding frequency/band skill. Also owe Andrew the #2/#4 run-it gap closures
  (damping inference + complex-CBUSH; shape-driven local calib; a topology alternative; snap-vs-shape decomposition).
- 2026-06-19 D16: measured-shape fusion tested cleanly → does NOT tighten (shapes don't predict single-impact
  per-channel amplitude, corr ~0.15 for both FEM and measured). 'Plenty of data' resolved: not a data/method gap,
  the QOI isn't modally predictable. This is a strong honest stopping point; ready to integrate + packet.
- 2026-06-19 D15: Andrew "plenty of data" → reframed wide CI as METHOD limit; building measured-shape-fused
  held-out QOI (use the .ash shapes we have). Cancelled VOI.
- 2026-06-19 D14: over-fitting concern CONFIRMED + figure delivered. Two-pop is a (real) demonstration, not a
  transferable method. Pivots the remaining work to Phase D (data-ceiling VOI = the honest generalizable answer).
- 2026-06-19 D13: Phase C two-population discrepancy tightens REST channels ~22% (coverage held); hard 8 stay wide
  (data ceiling). Confirming seeds 1–3 detached. Next: Phase D VOI + Phase E packet/check_twin.
- 2026-06-19 D12: FEM baseline (twin beats FEM on calibration) + Phase-B aggregate; identified heavy-tailed/
  feature-keyed discrepancy as the prime CI-tightening lever. Building the feature-correlation diagnostic.
- 2026-06-19 D11: incorporated Card A L6/L10 (shape calibration already ~null); σ_QOI ceiling confirmed across
  damping/freq/shape; refined Phase C/D/E plan. Building FEM baseline (D1) + richer-local+shape (C1') next.
- 2026-06-19 D10: Phase A+B done. Damping ≠ CI lever (CI is shape-driven); window correction = small free gain;
  structural-ζ injection hurts (under-resolution). Confirming over seeds, then pivoting to Phase C (shape/topology).
- 2026-06-19 D9: autonomy granted; program plan written; starting Phase A (damping feasibility).
- 2026-06-19 D8: Card F PAUSED per Andrew (defer evidence selection). CBUSH-damping identifiability gate run = the
  reality-check seeding the next DAMPING study. Reported to Andrew with the design implications + shape/topology sketch.
- 2026-06-19 D7: Stage-1 analytic evidence DONE (2 s, reduced model). check.py now 6 GREEN / 9 RED (stage1.evidence
  + evidence.sensitivity + ident.M3_damping + integrity GREEN; remaining = stage2/identifiability_M1/heldout/verdict/
  figures/packet/runtime). Reported to Andrew at this phase boundary before committing Stage-2 compute.
- 2026-06-19 D0–D5 written at task start. Workspace set up, foundation smoke-tested. check.py written
  (baseline RED 4G/0Y/11R; integrity GREEN). D6 added: discovered ACTIVE concurrent Card E thread; HOLDING
  before any compute pending Andrew's fold-in-vs-separate decision and the Stage-1-checkpoint-vs-full-run fork.
