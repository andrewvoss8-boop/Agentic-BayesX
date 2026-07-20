# decisions_log.md — StatFEM consistency toy (Experiment A)

Runner agent, Agentic BayesX. Lead = Claude Code; human = Andrew Voss; advisor objective = Ilias Bilionis.
Append-only. Newest at bottom of each section. This file is the durable record (chat is a cache).

## Re-grounding line (required first entry)
- 2026-06-16 **goal**: evaluate the StatFEM approach on a minimal 1-D structural-dynamics consistency toy —
  build the consistency/discretization-invariance criterion, then report whichever way the numbers fall
  (Bilionis: "build, evaluate, identify gaps, suggest improvements"; "it may not be working"). **last
  decision**: design fixed (D1–D9 below) — fixed-free axial rod eigenproblem with analytic truth + a
  Winkler-foundation model-form error ε; three constructions M-lik / M-statfem / M-ift sharing the same
  data; marginalized-Gaussian field likelihoods (closed form, NUTS-friendly). **next action**: write the
  IMMUTABLE check.py FIRST, then code, then smoke, then full sweep. **open ambiguities**: none blocking;
  the verdict is deliberately NOT pre-decided.

## FOLLOW-UP E1 (2026-06-16) — second error class, to press into the method differences
- **Why:** the main study's Winkler foundation was θ-like ⇒ all three biased θ similarly (methods looked
  alike). To separate them I added a NON-θ-like error: a localized stiffness defect EA(x)=θ_true(1−depth·
  1[0.4≤x≤0.6]). Truth = high-res variable-EA FE reference solve (n_el=512, NOT analytic; depth=0 matches
  analytic to 2.6e-6). Inference models UNCHANGED (uniform-EA). 12 cells, ALL converged (worst R-hat 1.007).
  Code followup.py/followup_run.py/fig_followup.py; data followup/defect_summary.json; fig figF; note
  followup/FINDINGS.md. Main immutable check.py NOT touched; main checker still YELLOW 60/3/0 with figF
  (image-QA + overlap audited).
- **RESULT (depth 0→0.5):** θ recovery FAILS for all three (1.15→~0.95–0.99) — parameter non-recovery is the
  shared limit, robust to error class. PREDICTION splits SHARPLY: M-lik (fixed σ_r) held-out coverage
  COLLAPSES 1.00→0.71→0.33; M-statfem and M-ift both HOLD 1.00 across all depths. statFEM's σ_d GROWS ~100×
  (0.0007→0.076) — it CATCHES the spatial error (vs flat 0.004 for the θ-like foundation). 
- **SHARPENED VERDICT:** the brittle choice is a FIXED residual treatment in the LIKELIHOOD — under a
  non-θ-like model error it is confidently wrong on PREDICTION (cov 0.33), because fixed σ_r can't widen the
  bands. Both LEARNED model-error terms (IFT's β in the prior, statFEM's additive σ_d) stay predictively
  honest. Recovering the PARAMETER still needs breaking the discrepancy↔parameter confounding (open).
- **NEXT candidate (E2, not yet run):** corrected-model control — add the foundation k_f as a 2nd inferred
  parameter (trivial: a_k=−θd_k+k_f−ω²; statFEM K→θK0+k_f·G−ω²M) to (a) confirm the bias is model-form (all
  recover θ_true,k_f), (b) test whether M-lik STILL drifts with σ_r under the CORRECT model, (c) θ↔k_f
  2-param identifiability per construction.

## COMPLETION (2026-06-16)
- **STATUS: checker OVERALL YELLOW — 60 GREEN / 3 YELLOW / 0 RED (exit 0).** The 3 YELLOWs are the intended
  honest-scope flags (one synthetic realization per cell; Winkler-foundation surrogate error; toy-not-
  universal). `bash run_all.sh` validated end-to-end. 64 NUTS cells, ALL converged (worst R-hat 1.008, min
  ESS 418, 0 divergences). Solver validated rate 2.00, finest err 4e-5. nuts_only compute ≈1288 s.
- **FINAL NUMBERS (out/sweep_summary.json):** C2 spread of posterior θ mean — M-lik vs σ_r **0.084/0.084**
  (ε 0/0.3) = DRIFT; M-lik vs N_c 0.0050/0.0019, M-ift vs N_c 0.0034/0.0045, M-statfem vs h 0.0030/0.0024 =
  all invariant. C1 ε=0 control bias: M-lik 0.0010, M-statfem 0.0005, M-ift 0.0004 (all pass). ε=0.3
  concentrate on biased θ: M-lik 1.269, M-statfem 1.272, M-ift 1.267 (truth 1.15). C3 held-out coverage
  ε=0.3 (finest, n=8): M-lik 0.71, M-ift 0.86, M-statfem 1.00 (statFEM's discrepancy keeps PREDICTION
  calibrated despite biased θ). Identifiability FIM ~4–6e4 (θ well-identified ⇒ ε>0 bias is model-form,
  not unidentifiability).
- **VERDICT (for Ilias, from the numbers — NOT pre-decided):** Bilionis's MECHANISM is demonstrated and
  ISOLATED — physics-in-likelihood (M-lik) carries a FICTITIOUS residual-noise knob σ_r that moves θ by
  ~0.08 with no principled setting, AND M-lik is worst on held-out prediction (0.71). His stronger phrasing
  ("doesn't converge as you refine the mesh") is NOT observed here: ALL THREE converge under mesh/N_c
  refinement. Under model-form error ALL THREE concentrate on a BIASED θ (parameter non-recovery /
  discrepancy↔parameter confounding) — a shared limit; statFEM trades θ recovery for honest predictive
  coverage. Secondary M-lik pathology: resonance-crossing multimodality.
- **DURABLE EDITS: NONE.** No AGENTS.md / check.py-expectation / sampler-standard / notes/memory.md /
  project_log.md edits by the runner. The proposed project_log row + notes updates are SURFACED in packet.md
  §8 for the lead/Andrew. Prior immutable files unchanged (hash gate GREEN). HANDS OFF the sibling runner
  (statfem_shocksat_eval_20260616) — left its process untouched.

## Decisions (continued — empirical findings from converged smoke tests)
- **D14 (2026-06-16) M-lik secondary pathology + safe-frequency fix.** With the full field-marginalised
  M-lik (faithful: includes the physics pseudo-data EVIDENCE term −½Σ log(τ²a_k²+σ_r²)), the θ posterior
  goes MULTIMODAL (R-hat≈100) when the θ-prior spans a θ at which a discrete resonance ω_n(θ) crosses a
  drive frequency — the evidence term spikes there. This is a genuine secondary pathology of physics-in-
  likelihood (documented in packet), but to measure the σ_r-drift CLEANLY I keep M-lik unimodal by (a)
  drive freqs whose resonance-crossings lie outside the θ-prior bulk, (b) θ prior tightened to
  LogNormal(0,0.20). All three then converge R-hat≈1.00, ESS>500.
- **D15 KEY EMPIRICAL FINDINGS (converged, n=8):** (the verdict is NOT pre-decided — these are the
  measured numbers.)
  - *Discretization-knob INVARIANCE (C2):* ALL THREE are essentially invariant to the GENUINE
    discretization knob — M-lik vs N_c spread ≈0.005 (ε0)/0.002 (ε0.3); M-ift vs N_c ≈0.003/0.004;
    M-statfem vs mesh h ≈0.003/0.003. So the naive "physics-in-likelihood doesn't converge under mesh
    refinement" charge is NOT supported here: all converge under refinement.
  - *M-lik σ_r drift (the real indicted behaviour):* θ moves 1.148→1.064 (ε0) and 1.265→1.181 (ε0.3) as
    the FICTITIOUS residual noise σ_r goes 0.005→0.5 — spread ≈0.08, with NO principled way to set σ_r.
    M-ift (β learned) and M-statfem (no σ_r) have NO such extra knob. ⇒ the charge is PARTIALLY
    supported and SHARPENED: the sensitivity is to the fictitious RESIDUAL-NOISE σ_r, not to the mesh.
  - *Model-error bias (ε=0.3):* ALL THREE converge to a BIASED θ≈1.26 (truth 1.15). statFEM's learned
    σ_d stays TINY (≈0.004) — the Winkler foundation acts θ-like across these drive freqs, so θ ABSORBS
    the error (Brynjarsdottir–O'Hagan / Kennedy–O'Hagan confounding) instead of the discrepancy flagging
    it ⇒ statFEM is confidently wrong on θ here too, just without the σ_r knob-sensitivity. ε=0 control:
    all three recover θ≈1.15 (bias ≤0.005) ⇒ testbed valid.
- **D16 Runtime/memory: chunk the sweep.** Running ~28 NUTS cells in ONE python process OOM-killed
  (exit 137) — jax compilation cache growth. run_sweep.py runs in CHUNKS via --only {mlik_sr, mlik_nc,
  mift_nc, statfem_h, concentration}; run_all.sh calls it once per chunk (fresh process each) so memory
  is freed between chunks; jax.clear_caches()+gc after each cell; resumable (skip finished cells).

## Decisions (continued — course correction after smoke tests)
- **D11 (2026-06-16) Smoke-test finding → reformulate observable to the FORCED drive-point FRF.** The
  modal/eigenproblem framing (observe mode shapes + natural frequencies, infer θ + latent ω_i) made
  M-lik and M-statfem converge and recover θ≈1.15, BUT M-ift would NOT converge (R-hat>1.6, ESS~3) and
  its β was weakly identified — because in that framing θ connects to the data ONLY through the
  field-shape PRIOR (the strong frequency signal was carried by free latent ω_i, decoupled from θ),
  and a learned/marginalised β can compensate, leaving θ weakly pinned. Presenting M-ift as
  non-converging would be an UNFAIR strawman (task §7: do not present a construction as failing if it
  merely didn't converge). FIX: switch the observable to a HARMONIC FORCED RESPONSE (drive-point FRF) —
  a unit tip load F at known drive frequencies ω_d; observe the response field u(x;ω_d,θ) at m sensors.
  The inhomogeneous forcing makes u θ-dependent and non-trivial, so ALL THREE constructions identify θ
  fairly through the SAME field data; drive frequencies are KNOWN (no latent ω_i, no mode-ordering),
  leaving only θ (+β or +σ_d) latent ⇒ 1–2-dim NUTS, bulletproof convergence. Task card explicitly
  allows "drive-point FRF". Natural frequencies still appear as FRF resonances ω_n=√(θλ_n+k_f); the
  model omits the foundation k_f (the same ε model-form error). Drive freqs chosen BETWEEN resonances
  (undamped response finite). Held-out C3 = response at held-out drive frequencies.
- **D12 Marginalised forced-BVP likelihoods.** Discrete dynamic stiffness A(θ,ω_d)=θK0−ω_d²M (FE) or the
  FD analogue. Field u latent, integrated out (linear-Gaussian, now with NON-zero mean from the load b):
  M-lik = pseudo-data "A u ≈ b" with FIXED σ_r (physics in likelihood) + sensor data; the σ_r/N_c-
  dependent piece is the pseudo-data evidence logN(b;0,Aτ²Aᵀ+σ_r²I). M-ift = physics in PRIOR
  exp(−β/2‖Au−b‖²) with β LEARNED. M-statfem = FE solve u_FE=(θK0−ω_d²M)⁻¹b + additive discrepancy +
  noise. Same load+data for all three. NUTS over θ(+β/+σ_d).
- **D13 Solver validation = forced-response convergence** of the discrete u(θ,ω_d) at sensors to the
  ANALYTIC tip-driven rod response u(x)=F·sin(kx)/(θ k cos kL), k=√((ω²−k_f)/θ); plus eigenfrequency
  convergence. Both ≈h² (cell-centred FD; consistent-mass FE).

## Decisions
- **D1 Testbed.** Fixed-free axial rod, −(EA u')' = ω² ρA u on [0,L]. Nondimensional: L=1, ρA=1, EA_nom=1
  ⇒ wave speed c_nom²=EA/ρA=1. Inferred scalar = stiffness scale θ with EA=θ·EA_nom (θ=1 nominal).
  θ_true=1.15 (truth is 15% stiffer than nominal so "concentrate on θ_true" is a real test, not at the
  prior centre). Analytic eigenvalues λ_n=((2n−1)π/2L)², mode shapes φ_n(x)=√2·sin((2n−1)πx/2L)
  (mass-normalised). Analytic ω_n=√θ·(2n−1)π/2L (no foundation).
- **D2 Model-form error ε.** TRUTH adds a Winkler elastic-support foundation k_f=ε (Winkler modulus,
  nondim): ω_n,true²=θ_true·λ_n+k_f; mode shapes unchanged (constant foundation ⇒ same sin shapes). The
  INFERENCE models all OMIT the foundation. ε=0 = the no-error control where a CORRECT method must
  converge to θ_true. ε levels {0.0, 0.3}; the foundation shifts mode 1 strongly (+5%) and modes 2,3 barely
  (+0.6%, +0.2%) ⇒ it is NOT absorbable by a single θ scaling ⇒ genuine misspecification. This is the
  decisive feature: a pure θ rescale shifts ALL modes proportionally; the foundation does not.
- **D3 Observables (same data for all 3 constructions — the central tenet).** A modal test of the first
  n_modes=3 modes: each mode shape sampled at m=7 interior sensors (noise σ_φ=0.03 on unit-max shapes) +
  its natural frequency (noise σ_ω,i=1% of ω_i,true). Held-out band for coverage C3 = modes 4,5,6
  frequencies (never used in fitting). Data-growth axis n = number of independent noisy replicate modal
  tests (n∈{1,4,16,64}).
- **D4 Construction M-lik (physics-in-likelihood, the indicted form).** Field φ_i (mode i) is a latent
  nodal vector on an N_c-point grid; the governing-equation residual A_i(θ,ω_i)φ_i with A_i=θc²D²+ω_i²ρA·I
  (D² = FD 2nd-derivative, fixed-free BCs) is imposed as FICTITIOUS data "residual≈0" with residual noise
  σ_r, PLUS the data likelihood (shapes+freqs). The Gaussian field is marginalised in closed form
  (eigenbasis of D²). Knobs swept = N_c and σ_r (both carry NO real information). Per-mode log-lik =
  (physics pseudo-data evidence −½Σ_k log(2π(a_k²τ²+σ_r²))) + (Gaussian on sensor shape with effective
  field cov) + (freq term); a_k=θc²d_k+ω_i². The pseudo-data evidence term is the σ_r/N_c-dependent piece.
- **D5 Construction M-ift (physics-in-PRIOR, IFT/PIFT-style).** SAME residual operator A_i, but the
  physics enters the field PRIOR with precision βA_iᵀA_i+τ_0·I and an inverse-temperature β that is
  LEARNED jointly with θ. No σ_r. Marginal sensor cov = (SV)diag(1/(τ_0+βa_k²))(SV)ᵀ+σ_φ²I. Knob = N_c.
  M-lik and M-ift are deliberately the SAME algebra differing ONLY in: residual weight = FIXED σ_r
  (likelihood) vs LEARNED β (prior). This is exactly Bilionis's distinction, isolated.
- **D6 Construction M-statfem (Girolami et al. 2021).** FE axial-bar model (n_el elements, consistent
  mass): K(θ)=θ·K0 ⇒ eigenvalues scale exactly as ω_FE,i(θ;h)=√θ·ω0,i(h), eigenvectors φ0,i(h)
  θ-independent (so the forward is analytic & differentiable in θ). Observation = FE prediction +
  additive zero-mean discrepancy d + noise: ω_obs,i ~ N(√θ·ω0,i(h)+d_i, σ_ω), d_i~N(0,σ_d²) (statFEM
  additive discrepancy on the modal frequencies); shapes carry measurement noise. Infer θ, σ_d. Knob =
  mesh h (n_el). Hypothesis OPEN — report which way θ goes under refinement.
- **D7 Sampler.** NUTS (NumPyro, .venv_nuts), ≥4 chains, all-variable gate max R-hat≤1.05 / min ESS≥200 /
  div-frac<2% or labelled not-yet-converged (YELLOW). Low-dim per cell (θ, ω_1..3, +β or +σ_d) ⇒ robust.
- **D8 Solver validation FIRST.** Both forward operators (FD D² used by M-lik/M-ift; FE eigensolve used by
  M-statfem) must converge to the ANALYTIC ω_n under refinement (≈h² rate) BEFORE any consistency claim,
  so posterior drift is the METHOD not under-resolution. Gate in check.py.
- **D9 Metrics.** C1 concentration: posterior(θ) mean→θ_true and SD↓ as n grows (per construction, per ε).
  C2 discretization sensitivity = spread (max−min) of posterior θ mean across the knob (a NUMBER per
  construction/knob/ε). C3 held-out modal-frequency 95% coverage. Money figure = posterior(θ) mean ±95% CI
  vs the refinement knob, per construction, with the θ_true line.
- **D10b Checker written (2026-06-16).** `check.py` written FIRST, before any results. Embeds sha256 of
  the prior immutable `confidently_wrong .../check.py` and scaffold `paper_virtual .../nuts_update.py`;
  integrity gate goes RED if either changed (certifies I never edit a prior immutable/scaffold). Gates the
  SCAFFOLDING (numbers exist, solver validated, sampler converged, testbed positive control) but NOT the
  verdict DIRECTION (pre-deciding forbidden). Defines the out/*.json summary schema the code must produce.
- **D10 Anti-cheating.** New testbed ⇒ core.py is written FRESH (rod physics ≠ prior modal-FRF core.py; NOT
  a copy/edit of any scaffold). viz.py text-overlap auditor + image_qa.py patterns are COPIED from
  confidently_wrong_modelform_20260616 (reuse-by-copy, originals untouched). PIFT repo (PredictiveScienceLab/
  pift-paper-2023) is CITED and reimplemented minimally; no results copied. check.py is IMMUTABLE, written
  before results. Verdict NOT pre-decided.
