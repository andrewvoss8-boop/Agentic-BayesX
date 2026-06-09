> # ⛔ SUPERSEDED / KILLED — 2026-06-08 (human decision: Andrew)
> The **Stage 0→5 march below is retired.** The 2026-06-08 framing challenge
> ([artifacts/reports/fem_phase1_framing_challenge_20260608/framing_challenge.md](../../../../artifacts/reports/fem_phase1_framing_challenge_20260608/framing_challenge.md))
> identified this staged plan as the **textbook scope-drift pattern** flagged in
> [notes/lessons-learned.md](../../../../notes/lessons-learned.md) (2026-06-05): progressive
> fidelity on a *synthetic* problem that defers the real question (a load QOI under unknown
> forcing, learned at the joint). Andrew approved killing it.
>
> **Replacement = a 2-gate plan** (framing-challenge items A, C, E):
> - **Gate 1 (item A):** swap the rigid joint for ONE compliant + lossy joint (free `k`,
>   structural loss `η`) + forcing + an interface-force QOI on an *independent richer* synthetic
>   truth, with a held-out honesty check — the smallest change that makes the model *learnable*.
>   (The rigid joint to change = `JOINT["k_trans"]=1.0e9` in
>   [runs/fem_phase1/opus/shared/spec.py](../../../../runs/fem_phase1/opus/shared/spec.py).)
> - **Gate 2 (item C — IN WORK):** run the same pipeline on ONE real public dataset = the first
>   actual *validation* (not verification).
> - **Park** Stages 2–4 (more params, property-GP, higher-fidelity FEM) until a *measured*
>   shortfall demands them. Do not execute them on synthetic data by default.
>
> The text below is kept for traceability only. Do NOT execute it as the roadmap.
> ---

# Master plan — toward a trustworthy, realistic aerospace StatFEM digital twin

Claude Code (lead/runner) for runs/round3/opus48. A staged, iterative plan that (1) resolves the
collapse/trust concerns, (2) progressively learns ALL hyperparameters + more physical parameters, (3) adds
a PROPERTY-BASED spatial model-form-error Gaussian process, (4) raises FEM fidelity, and (5) culminates in
ONE big, sequentially-updated master run that mimics a real qualification/loads workflow. Read with
decisions_log.md, statfem_lessons.md, research_directions_and_proposals.md,
anti_collapse_recommendation_and_study.md.

Plain-English note: "held-out calibration" = hide some data, predict it, check the 95% intervals really
contain it ~95% of the time. "starve-the-data" = deliberately use very little data to make over-confidence
visible. "effective sample count" = how many *independent* data points the model truly has (much smaller
than the raw count when errors are correlated). "discrepancy" = the model-error term. "epistemic" =
reducible-by-data uncertainty; "aleatory" = irreducible scatter (build-to-build, flight-to-flight).

## The throughline (applied at EVERY stage — non-negotiable gates)
- **Independent truth.** The data-generating model is authored separately from the inference model and is
  richer (so model-form error is real, not a draw from the inference's own discrepancy). [partially missing
  today — fix in Stage 0/1]
- **Primary trust test = held-out calibration** (hold out whole builds AND whole frequency bands; report
  coverage + posterior-predictive checks). A tight posterior that fails held-out coverage is collapse.
- **Collapse companions:** starve-the-data sweep; effective-vs-nominal sample count; with- vs
  without-discrepancy pair; grid-invariance as a supporting check only.
- **Sampler gate:** NUTS, >=4 chains, rank-split R-hat<1.01, bulk&tail ESS>=400 over ALL latents (incl.
  discrepancy coefficients + every hierarchical per-build/per-flight latent), divergences<2%, non-centered.
- **Resolution:** adaptive frequency grid from data-peak/estimated modes, fixed during inference, sized to
  the plausible mode range (D11/D15); confirm with the grid check.
- **Honesty:** QOI carries epistemic + aleatory + model-form uncertainty; runtime.json; every decision to
  decisions_log.md; nothing overstated; durable-rule changes are PROPOSALS pending approval.

---

## Stage 0 — Trust harness + honest baseline  (small)
Build a reusable trust module and read the CURRENT 6-strut model honestly before adding anything.
- Add: `trust.py` — held-out calibration (leave-out builds & bands), starve-the-data sweep,
  effective-sample-count, with/without-discrepancy, grid-invariance.
- Fix the R8 gap: re-author the truth's frequency error so it is NOT equal to the assumed discrepancy
  (remove the over-convenience flagged in D10).
- Deliverable: a baseline "is our tight posterior honest?" report on today's model.
- Exit gate: held-out coverage measured; collapse/bias quantified. (No new physics yet.)

## Stage 1 — Learn ALL hyperparameters  (small-medium)
Stop fixing things by hand.
- Make inferred (with priors): discrepancy scale & length-scale (sigma_d, ell_d), build-to-build scatter
  (sigma_build), sensor noise (sigma_e); optionally forcing scale.
- Guard the parameter<->discrepancy trade-off: informative priors + report sigma_d/ell_d posteriors; watch
  for ell_d collapsing small (which would re-open over-counting).
- Exit gate: convergence over ALL latents incl. the new hyperparameters; held-out calibration not worse;
  identifiability of sigma_d vs k_j shown.

## Stage 2 — More physical parameters  (medium)
Move beyond a single k_j.
- Add: dome stiffness, tray-panel stiffness, per-PROPERTY strut-group stiffnesses, and modal/loss-factor
  damping (the damping we parked). Keep them physical and differentiable.
- Run the identifiability/collapse companions as parameters are added (does adding parameters fix the bias
  floor or just trade with the discrepancy?).
- Exit gate: held-out calibration improves vs Stage 1; convergence; identifiability documented.

## Stage 3 — PROPERTY-BASED spatial model-form-error GP  (medium-large; the novel contribution)
Put the discrepancy where the error physically lives (research_directions S B; D12).
- Kernel over ELEMENT FEATURE SPACE: high correlation for same property; moderate for same element type
  (spring/beam/shell/solid); low for far-in-both; optional continuous term on element stiffness magnitude.
  Implemented as a parameter-space discrepancy that perturbs element properties, propagated through the FEM.
- Truth (independent): combine frequency-dependent/nonlinear joint + spatial per-strut/per-property scatter
  + realistic complex, frequency-correlated FRF noise (worse at antiresonances).
- Headline test: does the property-based discrepancy catch the SPATIAL error that the frequency-only GP
  could not (Stage 0/1 with vs Stage 3), and does held-out coverage jump?
- Exit gate: with/without comparison + held-out calibration shows the property-GP removes the spatial bias
  floor (or honestly doesn't); convergence over the GP coefficients.

## Stage 4 — Higher-fidelity FEM  (large; tractability risk)
Raise fidelity while staying differentiable/fast enough for NUTS.
- Tray: flexible ISOGRID PANEL (plate bending -> real panel modes) instead of rigid; struts with bending,
  not just axial; keep the single RBE'd interface.
- Dome: axisymmetric SHELL bounce/breathing (or a refined beam-with-geometric-stiffening) so the 93.5 Hz
  mode and its effective mass are physical, not calibrated by a 30x knob.
- Path: prefer JAX modal-superposition from a finer mesh; use TensorMesh continuum (validated in the spike)
  with sparse eigsh + E/rho-factoring ONLY where continuum geometry is needed; reduced-order (Craig-Bampton
  / modal truncation) to keep the per-NUTS-step cost bounded. Adaptive grid throughout.
- Validate: vs analytical benchmarks (betaL, lumped MDOF) AND vs the lower-fidelity model (does the added
  fidelity change the decision QOI?). Resolution + runtime accounting.
- Exit gate: FEM benchmark passes; QOI shift from fidelity quantified; cost acceptable.

## Stage 5 — MASTER RUN: realistic, sequential aerospace digital twin  (the big one, iterative)
One coherent run that mimics the qualification/loads workflow end to end and updates as data arrives.
- Structure: higher-fidelity coupled dome+tray (Stage 4), single interface, force-limited netCG + interface
  PSD QOIs.
- Inference: hierarchical over a FLEET of builds + flights; learn all physical parameters (Stage 2) + all
  hyperparameters (Stage 1) + the property-based spatial discrepancy (Stage 3), via NUTS.
- Data, two streams assimilated SEQUENTIALLY (the "iterative" master run):
  1. per-build component test (interface apparent mass / FRF, 6-DOF),
  2. per-flight interface acceleration PSD.
- QOI prediction carries the FULL uncertainty: parameter (epistemic) + build/flight (aleatory) + model-form
  (discrepancy) — closing the D13 gap.
- Decision layer (realistic): does the test spec envelope the predicted flight netCG/interface environment,
  per flight, with honest bands; flag narrow-band exceedance; (optional) a force-limiting notch under
  uncertainty.
- Headline artifacts: slow GIFs walking build-by-build then flight-by-flight showing (a) parameter +
  hyperparameter posteriors tightening, (b) the QOI bands and the spec-envelope verdict updating, (c)
  held-out calibration staying honest throughout.
- Exit gate (DONE): all throughline gates pass; held-out calibration good; QOI bands honest; one-command
  replay; full report packet + PPTX.

---

## Risks & mitigations
- **Compute blow-up** (more params + GP coeffs + finer FEM + sequential): reduced-order modal models,
  adaptive grids, fewer-but-decisive sweep cells, run stages in background; budget runtime per stage.
- **Identifiability** (many params vs flexible discrepancy): informative priors, report all posteriors,
  consider modular/cut updating so a flexible discrepancy informs prediction without corrupting calibration.
- **Funnels** (hierarchical variances): non-centered everywhere, higher target_accept, watch divergences.
- **Higher-fidelity differentiability** (continuum eig): E/rho-factoring + sparse solves (spike-validated);
  fall back to modal-superposition if continuum autodiff is too costly — labeled, not silent.
- **Over-fidelity for its own sake:** Stage 4 must show the fidelity changes the DECISION QOI, else keep it
  reduced.

## Needs human approval (durable / outside-workspace)
- Making held-out calibration, independent-truth, and the adaptive-grid resolution check DURABLE harness
  rules/hooks for this problem class (proposals in research_directions + anti_collapse docs).
- Any write outside runs/round3/opus48/ (notes/, harness/, skills/). Until approved, all of the above lives
  in-workspace as reference implementations + proposals.

## Suggested execution order & checkpoints
Stage 0 -> 1 -> 2 -> 3 -> 4 -> 5, each a checkpoint with its exit gate and a decisions_log entry. Stages 0-3
reuse current machinery (days). Stage 4 is the long pole. Stage 5 is the master run. Recommend starting
Stage 0 + Stage 1 together (trust harness + learn hyperparameters) since they share plumbing.
</content>
