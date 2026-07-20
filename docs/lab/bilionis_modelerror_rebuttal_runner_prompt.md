# Runner prompt — "Does discrepancy-aware updating survive Bilionis's model-form-error concern?"

Status: DRAFT runner prompt (lead-authored 2026-06-16). Bounded experiment + honest deck.
Workspace to create: `artifacts/reports/bilionis_modelerror_rebuttal_20260616/`.
Reuse scaffold (read, do not edit in place — copy into the workspace `code/`):
`artifacts/reports/paper_virtual_sensing_uq_toy_20260613/code/{core.py,nuts_update.py,viz.py}`.

---

## 0. Re-grounding (do this first, before any code)
Read, in order: `AGENTS.md`; this prompt; `notes/memory.md` CURRENT STATE block;
`artifacts/reports/paper_virtual_sensing_uq_toy_20260613/packet.md` (E1–E4 are the prior art you extend);
`.claude/skills/tufte-data-graphics/SKILL.md`. Then write `decisions_log.md` in the new workspace with one
line: goal / last decision / next action / open ambiguities. Re-ground again after any compaction.

## 1. The exact concern you are testing (do NOT broaden it)
Ilias Bilionis's load-bearing concern (from Alberts & Bilionis 2023 arXiv:2301.07609 and Hao & Bilionis
2024 arXiv:2306.02150): **a converged, confident Bayesian posterior can be *confidently wrong* under genuine
model-form error, with no signal that the physics is off**, because the model has no proper mechanism to
express "my physics might be wrong." Verbatim anchor: *"Bayesian MCMC converges to the maximum likelihood
estimator without detecting or accounting for underlying model form errors … NUTs, which is not aware of the
underlying model form error, still produces confident posteriors."*

Their cure: an inverse-temperature β in the prior that quantifies model-form error and is learned.
Our analog: the learned discrepancy scale σ_d (output side) + the held-out trust test. THIS experiment asks,
on our structural-dynamics FRF testbed: **does the naive (no-discrepancy) Bayesian fit actually succumb
(converge confidently + be wrong + give no warning), and does our discrepancy-aware fit detect the error
(σ_d tracks it) and stay calibrated (held-out coverage holds)?** Plus: where does our cure *also* fail
(carry the honest limit).

Scope guardrail (no overclaim): the claim you may earn is **"discrepancy-aware updating detects model-form
error (σ_d) and preserves calibrated predictive/QOI coverage where naive Bayesian calibration is confidently
wrong."** You may NOT claim universal parameter recovery — E4-style coherent confounded bias is a known limit
you must reproduce and report.

## 2. Priority deliverables and clarification gate
Write `priority_deliverables.md`. Priorities, each needing a delivered artifact:
1. A head-to-head, **converged** NUTS comparison across a model-form-error sweep δ: naive-no-discrepancy vs
   discrepancy-aware (iid and correlated). (Both/all arms MUST clear the convergence gate at every δ — the
   whole point is "converged but wrong", so a non-converged naive arm proves nothing.)
2. The two money curves: **held-out coverage vs δ** and **σ_d vs δ** (their Fig 4/5 analogs).
3. The honest-limit result: a coherent confounded-bias case where our cure misses the parameter (QOI may
   still hold), with the stated mechanism and the pre-test cure (break the degeneracy).
4. An immutable checker (`check.py`) encoding acceptance, one-command replay (`run_all.sh`), `runtime.json`.
5. A legible, tufte-compliant slide deck + ≥1 GIF (gated on the checker; see §9).
If any priority is ambiguous, state the assumption prominently in `decisions_log.md` and proceed; do not stall.

## 3. Question / decision gate (state in the packet)
- Decision supported: can we trust a calibrated digital twin under model-form error, and does our UQ warn us
  when we cannot?
- Success metric: (a) held-out predictive + QOI coverage vs nominal; (b) σ_d recovery of injected error;
  (c) convergence of every arm.
- What the method may choose: parameters θ (per-mode α, β, γ), σ_d, discrepancy hyperparameters.
- Human judgment: whether the injected error classes are representative; whether the QOI is the right one.
- What makes this the wrong question: if a real structure's model-form error is dominated by *coherent*
  effects that mimic a parameter (then σ_d cannot save the parameter — that is the limit slide, not a pass).

## 4. Assumptions ledger (`assumptions_ledger.md`, with values + units + rationale + sensitivity priority)
- Forward model: modal-ROM FRF from `core.py` (Eqs 4,11,12), mass-normalized modes; 4 channels, fixed Φ.
- Frequency grid: `core.freq_grid` (160 lines, 5–1000 Hz). Document spacing; show QOI-driving peaks resolved.
- Truth = best-modal-fit × un-modeled discrepancy (`core.make_truth`; `correlated_logfield` is NOT
  representable by modal scalings → genuine model-form error). This is the injected error.
- Measurement noise: σ_meas = 0.05 (log-amplitude). Channels Ch1/Ch2 observed; Ch3/Ch4 held out (masked).
- Inferred: per-mode α (4), β (4), γ, σ_d. Fixed: Φ, mode count, noise floor, box constraints.
- Priors: as in `nuts_update.py` (log-normal on α,β,γ; σ_d ~ HalfNormal(0.3)). State, do not silently change.

## 5. Experiment design
Model-form-error sweep δ ∈ {0.0, 0.05, 0.10, 0.20, 0.35, 0.50} (scale of `correlated_logfield` std; δ=0 is
the no-error control). At EACH δ, run these arms on the SAME data:
- **A1 — Naive-NoDisc (the strawman):** NUTS, iid measurement noise only, σ_d FIXED at 0 (no model-error
  mechanism). You must add a `learn_discrepancy=False` path to a *copied* `nuts_update.py` (do not edit the
  original). This is the arm Bilionis says is confidently wrong.
- **A2 — DiscAware-iid:** NUTS, learns σ_d, iid discrepancy.
- **A3 — DiscAware-correlated:** NUTS, learns σ_d + Schneider-style correlated discrepancy (`correlated=True`).
- **A0 — Deterministic LSQ (context only):** `core.deterministic_update`, ties to the paper's deferred-UQ.

Per arm per δ record: R-hat / min-ESS / div-frac over ALL sampled variables; held-out log-amplitude coverage
(masked channels) at nominal 95%; per-mode α posterior intervals + truth-covered flag; learned σ_d; held-out
peak-amplitude QOI interval + covered flag.

**Honest-limit sub-study (E-LIMIT):** repeat at one δ with a **coherent +15% peak-frequency shift** on the
masked truth (E4's bias). Expectation to TEST (not assume): A2/A3 keep QOI coverage but miss α at the failed
sensor (sign flip) — confounding, cured by breaking the degeneracy, not by more discrepancy.

Convergence gate (AGENTS.md): ≥4 chains, non-centered, max R-hat ≤ 1.05 (prefer ≤ 1.01), min ESS ≥ 200 all
vars, div-frac < 2%. If any arm fails to converge, that arm is YELLOW (not-yet-converged), fix it before
using it as evidence — a non-converged naive arm cannot demonstrate "converged but wrong."

## 6. Identifiability gate (required — you infer per-element/per-mode parameters)
Before any "α is/is not identifiable" claim, report the modal strain-energy / parameter→observable
sensitivity that links each α to the modes, and (for the per-mode claim under the coherent-bias limit) the
FIM eigen-view showing the peak-shift↔stiffness degeneracy at the realized discrepancy floor. Tie the
failed-sensor under-identification to mechanism + the pre-test lever (which sensor sees the local mode).

## 7. Sensitivity gate
Vary the assumption most likely to change the verdict: (a) the error CLASS — also run a structural
"missing-mode / hidden-DOF" error (drop one mode from the fit model, à la Phase-1) as a second δ-axis point;
(b) the held-out channel choice; (c) the nominal coverage target. Report whether the naive-vs-discrepancy
verdict is robust or fragile.

## 8. Verification gate — immutable `check.py` (write FIRST, then make it pass honestly)
Encode, with explicit numbers, GREEN/YELLOW/RED per the Result Status Standard:
- GREEN requires ALL: every NUTS arm converged at every δ; A1 held-out coverage falls materially below
  nominal as δ grows (malady reproduced) while staying converted/confident (tight α intervals); A2 AND A3
  held-out coverage within tolerance of nominal across the δ sweep (no-succumb); σ_d (A2/A3) recovers the
  injected δ within tolerance, monotone (thermometer); E-LIMIT reported with the parameter-miss + QOI-hold.
- YELLOW (documented, never "success"): single synthetic realization; surrogate error model; parameter-level
  miss under coherent bias; any arm needing extra warmup.
- RED: any undocumented non-convergence; a coverage/σ_d claim without the numbers; a missing/fabricated
  figure; tufte_lint or image-QA / text-overlap auditor failure; the original scaffold edited in place.
Checker exits non-zero only on RED. Also check: duplicate channels, units/axes, log-frequency axes, absolute
injected error shown separately from normalized diagnostics, method-summary + data/replicate count present.

## 9. Plot & deck gate (apply tufte skill; NO text-on-text)
For EVERY figure: write the plotting code to a saved `.py` (not inline), run
`python .claude/skills/tufte-data-graphics/scripts/tufte_lint.py <script>.py`, and run the image-legibility +
**text-overlap auditor** (bbox-collision check at save time, as in the buffet-dome thread) — record JSON per
figure. Frequency axes log-scaled; linear magnitude unless dB justified; direct line labels over legends;
caption carries quantity/units/data-count/synthetic-flag/takeaway; every figure states its run + flags any
not-yet-converged or honest-limit status ON the figure.

Required figures/animations (each its own saved script + lint + QA):
- **Fig A (money):** held-out coverage vs δ — A1 collapses, A2/A3 hold near nominal. Small multiples by error class.
- **Fig B (thermometer):** learned σ_d vs injected δ for A2/A3 (monotone tracking) with A1's absent/flat σ_d
  for contrast. The Hao-Bilionis Fig 5 analog.
- **Fig C:** per-mode α posterior intervals vs δ — A1 tight + biased (confidently wrong), A2/A3 widen + honest.
  Fig 4 analog. Show truth line.
- **GIF 1:** FRF overlay (truth, observed, A1 confident band that *excludes* truth at held-out points, A2/A3
  band that grows to cover) animated as δ rises — the visceral "confident-wrong vs honest-uncertain".
- **Fig D (honest limit):** E-LIMIT — coherent bias confounded with failed-sensor stiffness; α miss vs QOI hold.
- Optional GIF 2: σ_d thermometer rising with δ.

Deck (`slides/`, ~8–12 slides, gated on a non-RED checker; do NOT build claims the checker did not certify):
1. The concern (verbatim quotes; physics-in-likelihood vs physics-in-prior; σ_d↔β; held-out test = our warning).
2. Testbed + the model-form error we inject (clean truth vs observed; absolute injected error).
3. Fig A — the money slide.
4. Fig B — the thermometer.
5. Fig C — confidently-wrong vs honestly-uncertain parameters.
6. GIF 1 — FRF bands as error grows.
7. Fig D — the honest limit (where σ_d does NOT save the parameter; cure = break degeneracy).
8. Verdict + scope: what we proved (predictive/QOI coverage + error detection), what we did NOT (universal
   parameter recovery), and the "~15° trim, not a pivot" framing. Every claim traces to a checker number.

## 10. Runtime accounting & compute
Write `runtime.json` (`active_runtime_s`, `elapsed_wallclock_s`). Pin `OMP_NUM_THREADS=1
VECLIB_MAXIMUM_THREADS=1`. If the full δ × arms NUTS sweep exceeds the tool timeout, launch detached
(`nohup … > logs/run.log 2>&1 & disown`) and monitor with short until-loops; make it resumable (skip finished
(δ,arm) cells on relaunch). Float64 only.

## 11. Not allowed / anti-cheating
- Do NOT edit the original virtual-sensing scaffold or any immutable checker; copy into the new workspace.
- Do NOT fabricate coverage/σ_d numbers or figures; do NOT copy a paper figure as a generated result.
- Do NOT present the naive arm as failing if it actually did not converge (that would be a sampler artifact,
  not the malady) — make it converge first.
- Do NOT hide the E-LIMIT negative or round a YELLOW up to GREEN.

## 12. Done criteria
Done only when: artifacts exist; `check.py` passes (non-RED) via `bash run_all.sh`; assumptions + limits
documented; every figure tufte-linted + image-QA + overlap-audited; the deck's every claim traces to a
checker number; `decisions_log.md` complete; and the relevant row in `docs/report/project_log.md` is PROPOSED
for the lead to add (do not edit durable notes yourself — surface the proposed status copied from the checker).

## Human stop points (lead handles these)
Stop for human approval before changing any durable rule, checker expectation, sampler standard, or the
project notes/vision. This experiment + its own checker + deck are new artifacts and do not require that stop,
but the project_log row and any memory.md update do.
