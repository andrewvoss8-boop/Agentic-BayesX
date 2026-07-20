# decisions_log.md — Confidently-Wrong Model-Form-Error experiment

Workspace `artifacts/reports/confidently_wrong_modelform_20260616/`. Created 2026-06-16.

## One-line re-grounding (restate after any compaction)
GOAL: test Bilionis's "confidently wrong" concern on our FRF testbed — does the NAIVE no-discrepancy
Bayes fit converge confidently + be wrong + give NO warning under genuine model-form error, while the
DISCREPANCY-AWARE fit detects the error (σ_d tracks δ) and stays calibrated (held-out coverage holds)?
Carry the honest limit (coherent confounded bias misses the parameter even with our cure).
LAST DECISION: new experiment extending the E1–E4 prior art (paper_virtual_sensing_uq_toy_20260613).
NEXT ACTION: scaffold + immutable check.py first, then δ×arms NUTS sweep.
OPEN AMBIGUITIES: see §Decisions D3 (coverage target), D5 (E-LIMIT fit), D6 (sensitivity scope).

## Governance
- Autonomy: build the experiment, its own checker, and deck WITHOUT stopping (these are new artifacts).
  STOP for human approval before: any durable-rule / checker-expectation / sampler-standard change, and
  before editing project notes (`notes/memory.md` CURRENT STATE, `notes/runs.md`, `docs/report/project_log.md`).
  Those will be PROPOSED in the packet, not self-applied.
- Anti-cheating active: copied (never edited) the original scaffold `core.py`/`nuts_update.py`; no fabricated
  numbers/figures; no method swap without labeling; checker written before results and not edited to pass.

## Decisions
- D1 (forward model / scaffold): reuse `core.py` UNCHANGED (forward FRF, `make_truth`, `correlated_logfield`,
  `deterministic_update`, QOI helpers). Copy of `nuts_update.py` gets ONE addition: a `learn_discrepancy=False`
  path (σ_d fixed at 0, iid measurement noise only) = the A1 naive strawman. Original files untouched.
- D2 (the δ sweep): δ = scale of the injected `correlated_logfield` model-form discrepancy. δ ∈
  {0.0, 0.05, 0.10, 0.20, 0.35, 0.50}. Mapping: high-frequency discrepancy std = δ, low-frequency std = δ/6
  (preserves the scaffold's 0.05→0.30 lo/hi growth shape). δ=0 ⇒ zero discrepancy = the no-error CONTROL
  (truth is exactly modal ⇒ naive should also be calibrated there; that is the control that proves the malady
  at δ>0 is model-form error, not a sampler artifact).
- D3 (held-out coverage target — was open): report BOTH, headline = predictive coverage of the held-out NOISY
  masked observation (proper "did my predictive interval cover the held-out measurement"); also report
  clean-truth-line coverage. Masked channels Ch3/Ch4 are NEVER fit in the main sweep; they are predicted from
  the posterior through the fixed coupling Φ and scored post-hoc (the trust test = our analog of Bilionis's
  warning signal). Nominal target 95%.
- D4 (arms, same data per δ): A0 deterministic LSQ (context only, `core.deterministic_update`); A1 Naive-NoDisc
  (NUTS, σ_d≡0, iid σ_meas only — Bilionis's confidently-wrong arm); A2 DiscAware-iid (NUTS, learns σ_d, iid
  discrepancy); A3 DiscAware-correlated (NUTS, learns σ_d + Schneider-style correlated discrepancy on masked-
  relevant residual). Convergence gate per AGENTS.md on EVERY NUTS arm at EVERY δ (≥4 chains, non-centered/
  exp-reparam, max R-hat ≤1.05, min ESS ≥200 ALL vars, div-frac <2%). A non-converged naive arm proves
  nothing → must converge first.
- D5 (E-LIMIT — was open): the honest-limit sub-study mirrors prior-art E4. Use `local_mode_modes()` (mode 4
  is LOCAL to the masked sensors). The masked reconstruction with a coherent +15% peak-frequency shift IS
  included in the fit as a down-weighted "virtual ground-truth" target (the paper's closed-loop updating), so
  the peak-shift≡stiffness confound can bite α4. Test (do NOT assume): A2/A3 keep QOI coverage but MISS α4 at
  the failed sensor (sign flip to apparent hardening); cure = break the degeneracy (sensor that sees the local
  mode), not more discrepancy. Reported as the honest YELLOW limit, never rounded up.
- D6 (sensitivity, error CLASS — was open): second error class = "missing-mode / hidden-DOF" (truth has 4
  modes; the FIT model omits mode 3 → genuine structural model-form error, à la Phase-1). Severity swept by
  scaling the dropped mode's participation in truth. Run A1 vs A2 vs A3 across that severity axis. Also vary
  held-out channel choice and the nominal coverage target as cheap robustness checks. Verdict reported as
  robust or fragile.
- D7 (priors, unchanged from scaffold): log-Normal on α (Normal(0,0.15) on log α per mode), β (Normal(0,0.5)
  on log β), γ (Normal(log GAMMA0, 0.2)); σ_d ~ HalfNormal(0.3) for A2/A3, fixed 0 for A1. σ_meas = 0.05
  (log-amplitude measurement noise). Float64. State, do not silently change.
- D8 (compute): pin OMP/VECLIB threads = 1; resumable sweep (skip finished (δ,arm,class) cells on relaunch,
  keyed on a content hash incl. arm settings); launch detached if the full sweep exceeds the tool timeout;
  monitor with short until-loops. `runtime.json` with active + wallclock.

- D9 (3-mode main sweep — diagnosed, not assumed): the scaffold's default 4-mode set has a 720 Hz HF mode
  that is INTRINSICALLY weakly identified from the 2 observed channels — its (α₄,β₄) posterior goes BIMODAL
  even at δ=0 (NO discrepancy at all): one chain locks onto a second basin (β₄≈1.34 vs 0.96), R-hat≈25, ESS 2.
  That is HF under-identification, a DIFFERENT phenomenon from the model-form-error malady. The task is
  explicit that the naive arm MUST converge (a non-converged naive arm proves nothing). FIX (fair, same for all
  arms): the main "correlated" + "missingmode" classes use a 3-mode well-resolved set (18/95/280 Hz, per-mode
  α and β both kept). Verified: naive A1 converges R-hat ≤1.004, ESS >2000, 0 div across the FULL δ sweep AND
  two seeds. The HF local mode (720→760 Hz) is reserved for E-LIMIT + the identifiability gate, where
  under-identification is the POINT. Diagnostic evidence: per-chain means + per-variable R-hat printed in logs.
- D10 (validation of the 3-mode story, full draws, exact sweep seeds): correlated A1/A2/A3 at δ∈{0,0.20,0.50}
  ALL converge (R-hat ≤1.002, ESS ≥1580). Naive held-out (truth) coverage 1.00→0.07→0.02 as δ grows while α
  intervals stay TIGHT (width 0.002) = confidently wrong, no warning. Disc-aware coverage 1.00→0.93→0.84 (A2)
  / 0.99→0.94→0.86 (A3), QOI 2/2 at every δ. σ_d thermometer 0.01→0.18→0.34 (A2) tracks the band-effective
  injected std (≈ average of δ/6..δ), monotone. δ=0 control: naive ALSO calibrated (cov 1.00, σ_d≈0) ⇒ the
  malady at δ>0 is model-form error, not a sampler artifact. These exact numbers reproduce in the sweep
  (run_cell uses the same deterministic seeds).

- D11 (tufte-lint advisory flags — reviewed, all benign; deliberate-deviation note per AGENTS.md plot gate):
  (1) "no log x-axis" on fig_testbed/fig_limit/gif is a FALSE POSITIVE — those FRF panels ARE log-frequency
  (set via the `viz.style(ax, logx=True)` helper; the heuristic lint greps source for `set_xscale("log")`
  and cannot see the helper indirection). (2) "no log x-axis" on fig_coverage/fig_sigmad/fig_alpha is correct
  behaviour: their x-axis is the injected error δ / missing-mode severity / category, NOT frequency, so a
  LINEAR axis is right. (3) "dB detected" on fig_testbed/fig_limit is justified: dB is used only for FRF
  magnitude DISPLAY (the paper's Eq-21 metric); the LIKELIHOOD and all coverage are computed on log-amplitude
  ln|H| (stated on the figures/packet). No real tufte violations; check.py only fails on real issues.
- D12 (checker result, first real run): OVERALL YELLOW 54 GREEN / 4 YELLOW / 0 RED. The 4 yellows are the
  intended honest-scope flags (single realization; surrogate error model; no universal parameter recovery;
  the E-LIMIT parameter miss). check.py finalized (coverage gates on noisy predictive coverage; thermometer
  on Spearman ≥0.9) BEFORE this run and not edited afterward.

- D13 (DONE): `bash run_all.sh` validated end-to-end → check.py OVERALL **YELLOW 54 GREEN / 4 YELLOW / 0 RED**
  (0 red; the 4 yellows are the intended honest-scope flags). All 38 sweep cells + E-LIMIT present; 29 NUTS
  cells all converged (worst R-hat 1.003, min ESS 1546, 0 div). 7 figures + GIF tufte-linted, pixel-QA ALL_OK,
  text-overlap auditor 0 overlaps. Deck `slides/confidently_wrong_modelform.pptx` (11 slides) built and gated
  on the non-RED checker. runtime.json regenerated by run_all (active ~12 min incl. concurrent-process
  inflation; nuts_only ~566s). Durable-notes updates (memory.md / project_log / runs.md) are PROPOSED in
  packet §9 and NOT self-applied — they await Andrew (human stop point).

## Log
- 2026-06-16: re-grounded from AGENTS.md, notes/memory.md CURRENT STATE, prior-art packet (E1–E4), tufte SKILL.
  Verified `.venv_nuts` (jax 0.4.30 / numpyro 0.15.3 / numpy 1.26.4, x64 ok). Copied scaffold. Wrote this log
  + priority_deliverables + question_framing + assumptions_ledger + quantity_contracts. Writing check.py FIRST.
