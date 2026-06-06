# Handoff to the master agent — Agentic BayesX round-3 opus48 (StatFEM digital-twin track)

Author: Claude Code (lead/runner), 2026-06-04. Purpose: hand this workspace to a master agent that will
coordinate SUBAGENTS. Self-contained: gives current state, durable findings, a per-stage plan with
concrete next steps + suggested subagent ownership + exit gates, open approvals, and re-grounding pointers.

Workspace: `runs/round3/opus48/` (writes confined here). Re-grounding order if context is lost:
`docs/agents/competitive_full_experiment/round3/task_card_round3.md` -> `report/priority_deliverables.md`
-> `report/decisions_log.md` -> `report/master_plan.md` -> `commands.md`. Background: `report/statfem_lessons.md`,
`report/research_directions_and_proposals.md`, `report/anti_collapse_recommendation_and_study.md`.

---

## 1. One-paragraph state of play
We moved from the original round-3 MDOF/netCG packet (built, converged, delivered) to a StatFEM
*digital-twin* track because the human (correctly) judged the original as "plumbing": the synthetic data
came from the same model used for inference. We rebuilt with (a) an independent richer truth, (b) a
genuinely MDOF 6-strut hexapod tray + bounce-mode dome, (c) two model-form errors (spatial + frequency),
(d) hierarchical learning of the build-to-build scatter, (e) a trust harness (held-out calibration,
effective-sample-count, with/without-discrepancy, starve-data, adaptive frequency grid). Stage 0+1
(learn ALL hyperparameters + trust harness) was executed and **failed the convergence gate** — for an
informative reason: a frequency-only discrepancy cannot represent the spatial error, creating a
non-identifiable sigma_d<->sigma_e ridge. That decisively motivates Stage 3 (a correctly-structured,
property-based spatial discrepancy), which is the recommended next build.

## 2. What exists (code in `runs/round3/opus48/code/`)
- `mdof_forward.py` — JAX MDOF physics: dome bounce-mode modal model + geometric (pressure) stiffening,
  tray modal model, FBS single-interface coupling, netCG QOI, reverse-engineered forcing (dome interface
  response anchored to 0.1 g^2/Hz). Validated (tests/validate_fem.py).
- `tray_hexapod.py` — rigid tray on 6 octahedral two-force struts, RBE'd to ONE interface node; 6 mount
  modes; per-strut spatial stiffness error; interface apparent mass.
- `statfem_hexapod.py` / `statfem_hexapod_hier.py` — StatFEM inference (k_j; then hierarchical k_j_pop +
  sigma_build) on the 6-DOF interface apparent mass; frequency (KL-GP) discrepancy.
- `statfem_sequential_qoi.py` — sequential prior/posterior/truth GIFs for netCG + interface PSD; the
  three-way FRF (truth vs BU(k_j) vs BU(k_j)+d).
- `adaptive_freq.py` — adaptive frequency grid (dense at solved modes, coarse elsewhere) + resolution
  diagnostic; demo.
- `stage01_trust_hyper.py` — Stage 0+1: independent (non-convenient) truth; learn ALL hyperparameters
  (k_j_pop, sigma_build, sigma_e, sigma_d, ell_d via a Hilbert-space GP); trust harness.
- Original round-3 packet pipeline: `run_pipeline.py`, `fem_export.py`, `make_pptx.py`.
Key result artifacts in `report/`: results.json, nuts_diagnostics, validation.json, statfem_*results.json,
stage01_results.json, figures/*, the GIFs, and the docs listed above.

## 3. Durable findings / lessons (carry forward; do not relearn)
1. **Author the TRUTH independently of the inference model**, with model-form error OUTSIDE the
   discrepancy's representational span. Same-family data => trivial recovery ("plumbing"). (The single
   most important coordination rule for the subagent setup — see Section 6.)
2. **The discrepancy must MATCH THE STRUCTURE of the error.** A frequency-curve discrepancy fixes
   frequency-shaped error but NOT a spatial (mode-splitting) error; the spatial error then (i) biases the
   parameter, (ii) inflates the noise term sigma_e, and (iii) — when you also learn sigma_d — creates a
   sigma_d<->sigma_e non-identifiable ridge that breaks NUTS convergence.
3. **Epistemic collapses; aleatory dominates.** One scalar vs a data deluge => epistemic posterior ~0.1%
   (looks "too perfect"); the decision-relevant uncertainty is the irreducible aleatory build/flight
   scatter. Learn the VARIANCE (sigma_build) to get visible, decision-relevant sequential learning.
4. **Trust tests, in priority order:** (a) HELD-OUT CALIBRATION (hide builds + frequency bands; check 95%
   coverage) is primary and survives the data-deluge objection; (b) EFFECTIVE-vs-NOMINAL sample count
   (n_eff ~ (sigma_prior/sigma_post)^2) exposes over-counting as a number even when intervals are tiny;
   (c) STARVE-THE-DATA; (d) grid-invariance is supporting only. **Read coverage WITH sharpness/sigma_e** —
   inflated noise can fake good coverage with useless-wide bands.
5. **Adaptive frequency grid** (dense at solved/estimated/data-peak modes, coarse log baseline elsewhere),
   computed once and FIXED during inference, sized to the resonances' plausible range; do NOT recompute per
   NUTS step (breaks gradients). Wins on PEAK fidelity (~10x); the integrated QOI is grid-robust either way.
6. **StatFEM mapping:** build-to-build = hierarchical parameter prior; flight-to-flight = random forcing
   source term; discrepancy d and sensor noise e are separate; learning sigma_d/ell_d is the level-2
   extension; guard the parameter<->discrepancy identifiability (informative priors / modular updating).
7. **QOI honesty (open gap, D13):** the netCG/interface-PSD predictions must propagate d (with its
   uncertainty) PLUS aleatory build/flight scatter, not just the parameter posterior.

## 4. Per-stage plan with concrete NEXT STEPS, suggested owner, and exit gate
Throughline at EVERY stage: independent truth; NUTS gate (R-hat<1.01, bulk&tail ESS>=400 over ALL latents
incl. discrepancy coeffs + hierarchical latents, divergences<2%, >=4 chains, non-centered); held-out
calibration (+ effective-count, starve-data); adaptive grid; full-uncertainty QOI; runtime.json; log every
decision.

### Stage 0+1 — Trust harness + learn all hyperparameters  [DONE; FAILED convergence -> diagnosed]
- Status: executed (stage01_trust_hyper.py). sigma_build recovered (0.068 vs 0.050); sigma_e INFLATED
  (0.227 vs 0.080); NON-CONVERGED (R-hat 1.54, ESS 7) due to the sigma_d<->sigma_e ridge (finding #2).
- Next step (small, optional): confirm the ridge by FIXING sigma_e (or tightening sigma_d) -> expect
  convergence -> gives a converged baseline with the honest caveat "sigma_e/sigma_d not jointly
  identifiable under a mis-structured discrepancy."
- Owner: Inference subagent + Trust subagent. Exit gate: a converged baseline OR a clear documented
  non-identifiability result.

### Stage 2 — More physical parameters (+ damping)  [next, medium]
- Next steps: add dome stiffness, tray-panel stiffness, per-PROPERTY strut-group stiffness, and
  modal/loss-factor damping (parked earlier). Keep differentiable. Re-run identifiability + held-out
  calibration as each is added (does adding parameters fix the bias floor or just trade with d?).
- Owner: Inference subagent. Exit gate: held-out calibration not worse; convergence over all latents;
  identifiability documented (parameter correlations, prior sensitivity).

### Stage 3 — PROPERTY-BASED spatial model-form-error GP  [the novel piece + the fix; do soon]
- Next steps: implement a discrepancy kernel over ELEMENT FEATURE SPACE (high corr same property; moderate
  same type spring/beam/shell/solid; low far-in-both; optional continuous term on element stiffness),
  applied as a PARAMETER-SPACE discrepancy that perturbs element/strut properties and propagates through
  the FEM. Author truth independently (frequency-dependent/nonlinear joint + spatial per-strut + realistic
  correlated noise). Headline test: does it (i) RESTORE identifiability/convergence (sigma_d vs sigma_e
  separate), (ii) STOP sigma_e inflation, (iii) CATCH the spatial error the frequency-GP could not
  (with/without comparison), (iv) improve held-out coverage to ~0.95 with sharper bands?
- Owner: Inference subagent (kernel) + Truth-author subagent (independent truth) + Trust subagent (gates).
- Exit gate: convergence restored; held-out coverage ~0.95 AND sharper than Stage 0/1; spatial bias floor
  reduced. Defer the modal-participation kernel variant (re-enters frequency domain).

### Stage 4 — Higher-fidelity FEM  [large; tractability risk]
- Next steps: flexible ISOGRID panel (plate bending -> real panel modes); axisymmetric SHELL or
  refined-beam dome so 93.5 Hz is physical (not a 30x calibration knob); struts with bending. Keep NUTS-
  feasible via reduced-order (Craig-Bampton / modal truncation), sparse eigsh + E/rho-factoring, or
  TensorMesh continuum (spike-validated) ONLY where continuum geometry is needed. Adaptive grid throughout.
  Validate vs analytical (betaL, lumped MDOF) AND vs the lower-fidelity model (does fidelity change the
  decision QOI?).
- Owner: Physics/FEM subagent (+ Trust subagent for validation). Exit gate: FEM benchmark passes; QOI shift
  from fidelity quantified; per-NUTS-step cost acceptable; fallback labeled if continuum autodiff too slow.

### Stage 5 — MASTER RUN: realistic sequential aerospace digital twin  [the big iterative run]
- Next steps: couple higher-fidelity dome+tray at the single interface; hierarchical over a FLEET of builds
  + flights; learn all physical parameters (Stage 2) + all hyperparameters (Stage 1) + property-based
  spatial discrepancy (Stage 3); assimilate SEQUENTIALLY two data streams (per-build component apparent
  mass; per-flight interface PSD); predict netCG + interface PSD with FULL uncertainty (parameter +
  aleatory + discrepancy, closing D13); decision layer = does the test spec envelope the predicted flight
  environment per flight (narrow-band exceedance; optional force-limiting notch under uncertainty); GIFs
  walking build-by-build then flight-by-flight; held-out calibration throughout.
- Owner: all subagents under the master. Exit gate (DONE): all throughline gates pass; held-out calibration
  good; QOI bands honest; one-command replay; full report packet + PPTX.

## 5. Open approvals (durable / outside-workspace — NOT self-adopted)
- Make HELD-OUT CALIBRATION, INDEPENDENT-TRUTH, and the ADAPTIVE-GRID resolution check DURABLE harness
  rules/hooks for this problem class (proposals in research_directions + anti_collapse docs).
- Any write outside `runs/round3/opus48/` (notes/, harness/, skills/). Reference implementations + a
  data-peak-pick front-end for the adaptive grid are ready in-workspace pending approval to place.

## 6. Suggested subagent roles for the master protocol (key: separation of duties)
- **Truth-author subagent** — authors the independent ground-truth generator ONLY; must NOT see/share the
  inference model's parameterization. (Enforces finding #1; prevents the tautology that made the original
  run "plumbing." This separation is the single most important protocol rule.)
- **Inference/StatFEM subagent** — forward model, discrepancy structure, hyperparameter priors, NUTS.
- **Trust/verification subagent (independent)** — owns held-out calibration, effective-count, convergence
  gate, grid-invariance; has authority to FAIL a stage. Should be distinct from the inference subagent.
- **Physics/FEM subagent** — higher-fidelity FEM + analytical validation + resolution.
- **Visualization/reporting subagent** — GIFs, packet.md, PPTX, figure standards (legends, log-f, no
  clipped peaks).
- **Decision/framing subagent** — the engineering decision (spec envelope, force-limiting, MPE), and a
  recurring framing-challenge pass (is this the right question?).
Coordination rules: every stage logs to decisions_log.md; durable-rule changes require human approval; the
Trust subagent's gate is binding; runtime.json per producing run; never claim "NUTS active" unless the gate
passes.

## 7. Replay / entry points
- One-command examples in `commands.md` (use `PYTHONPATH="runs/round3/opus48/.pylibs" .venv_nuts/bin/python ...`).
- Quick-test any script with its `*_SMOKE=1` env var (few samples; NOT for reporting).
- Immutable checkers unchanged; verify `shasum -a 256 -c harness/checkers/manifest.sha256`.
</content>

---

## 8. BLIND inference round (appended 2026-06-04) — RESULT for scoring
Executed the blind protocol: built a coarse NOMINAL forward model (blind_model.py) and hierarchical StatFEM
NUTS inference (blind_infer.py) against the PUBLISHED observations ONLY (codex_truth/dataset/). Did NOT open
the sealed truth / Codex code / Codex report.
- **Result: the inference does NOT converge** — multimodal / non-identifiable (worst R-hat 2.41, ESS 5,
  0 div; the sigma_d<->sigma_e ridge + an intrinsic "no single symmetric k_strut fits all 6 DOF"
  multimodality). sigma_e inflates to ~factor 1.85. Every reparameterization fails (D24). I do NOT claim
  "NUTS active".
- **Held-out calibration:** new-build coverage 0.94 but log-width ~2.84 (~12x) = wide-but-covering; held-out
  band coverage 0.88 (<0.95). n_eff(k_strut) ~0.9 vs 1800 points.
- **netCG QOI:** predicted 3*GRMS q50 3.16 g [95% 1.22-6.08] vs published observed 0.46-0.96 g (~5x high);
  driving-point QOI mapping alone ~2x high (measured on published data). Narrow-band 99%-hi exceeds spec on
  ~43% of band; overall scalar margin 4.5x.
- **For the master:** posterior in report/blind_posterior.npz; summaries in blind_results.json; QOI in
  blind_qoi_results.json; packet.md + packet.pptx; diagnostics in blind_nuts_diagnostics.*; expected-bias
  statement in packet.md §5 and blind_review_request.md. The honest headline is that the INDEPENDENT truth
  successfully broke blind recovery (the anti-"plumbing" goal achieved); the fix is the Stage-3 structure-
  based discrepancy + an asymmetric/higher-fidelity model + complex likelihood.

## 9. STAGE 3 (structure-aware fix) — RESULT for scoring (appended 2026-06-04)
Built the three coupled fixes the blind failure pointed to and ran them BLIND on the re-published truth
(canonical netCG contract). Code: blind3_{model,infer,qoi,figs,gridinv,pptx}.py. Packet: packet_stage3.md
+ packet.pptx. Manifest scorecard: manifest.json. Sealed truth NOT opened.
- **Convergence (gate over ALL latents):** WITHOUT discrepancy (per-strut asymmetric PHYSICS only) **PASSES**
  (rank-split R-hat 1.009, bulk ESS 487, 0 div; k_pop 1.685e7 near nominal) — a real gain over the prior
  blind run that could not converge. WITH the structure-based discrepancy it **FAILS** (R-hat 2.85, ESS 4.7,
  sigma_d->1.33): a per-strut discrepancy is CONFOUNDED with the per-strut stiffness -> it INTRODUCES a
  parameter<->discrepancy ridge instead of resolving the sigma_d<->sigma_e one. I do NOT claim "NUTS active"
  for the with-d model. **Lesson:** a structure-based discrepancy must be ORTHOGONAL to the calibration
  parameters (output-mode/participation space), not on the very parameters being calibrated.
- **netCG (canonical FBS contract):** bias 4.86x (prior, drive-point) -> **1.71x** (with-d, wide) / **3.10x**
  (without-d, converged); f->0 rigid limit exact 0.282. The FBS contract removed the ~2x definitional drift.
  Converged without-d QOI is biased 3.1x high (0% cov) = genuine model-form OVER-prediction; with-d covers
  92% only via wide multimodal bands. Narrow-band 99%-hi exceeds spec on 25% of band at 2.56x overall margin.
- **sigma_e:** with-d 0.69 vs without-d 0.93 (discrepancy lowers it) but BOTH inflated ~2x = the dominant
  residual error is MISSING HIGHER MODES (z:62/77/120; lateral:51/87/137), outside the coarse model's span.
- **Held-out (primary trust):** new-build cov95 0.911 (log-width 2.16 ~8.7x, far sharper than prior 12-18x);
  band 95-115 Hz cov95 0.715 (under-covers). Companions: starve-data still R-hat 2.85 (ridge is STRUCTURAL,
  not data-deluge); n_eff(k_pop) 0.6 vs 7920; grid-invariance bounded/intractable under the ridge (a signal).
- **For the master:** posteriors blind3_posterior.npz (with-d, non-converged) + blind3_posterior_nodisc.npz
  (CONVERGED, trustworthy); summaries blind3_results.json + blind3_companions.json; QOI blind3_qoi_results
  (+_nodisc); diagnostics blind3_nuts_diagnostics.*. **Recommended next: Stage-4 higher-fidelity FEM
  (flexible isogrid panel + strut/shell bending modes) = the real fix for the missing-mode floor; and a
  discrepancy ORTHOGONAL to the calibration params (or modular/cut updating).**
