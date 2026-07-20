# Study program — applying Schneider 2022 + Das/Debnath 2020 to StatFEM
2026-06-12 · Workspace `artifacts/reports/papers_statfem_studies_20260612/`

Audience note (per CLAUDE.md): ML/stats terms are defined in plain words on first use; structural-dynamics
terms (FRF, apparent mass, MAC, mode shape, Rayleigh damping) are used directly.

---

## 1. What is genuinely NOVEL in each paper (the reusable techniques)

### 1.1 Schneider et al. 2022 (MSSP 166:108407) — Bayesian FRF updating with a rational surrogate
The paper's transferable machinery, in priority order for us:
- **T-S1 — a discrepancy (model-error) model for DENSE complex FRF data.** The model error ε is
  MULTIPLICATIVE on the complex FRF: `data = model ∘ ε`. Taking logs, `log ε = log|ε| + iθ`; magnitude
  `|ε|` is lognormal, phase `θ` is normal. So `[w=log|ε|; θ]` is jointly Gaussian (Eq. 18). This is a
  *likelihood you can apply at every frequency line without hand-picking points* — the exact problem we
  hit (over-counting correlated full-FRF data → false collapse, vision §4).
- **T-S2 — model error CORRELATED in space AND frequency, hyperparameters inferred.** The correlation
  matrix is an additive split `R = r(R_ff ⊗ I) + (1−r)(I ⊗ R_zz)` (Eq. 25) with exponential kernels and
  five inferred hyperparameters (σ_w, σ_θ, ℓ_co,z, ℓ_co,f, r). Treating "how wrong, and how correlated the
  wrongness is" as something you LEARN from data is precisely the StatFEM discrepancy lever — and the
  additive (not multiplicative) space/frequency split is a specific, testable structural choice.
- **T-S3 — rational-PCE surrogate of the FRF** (ratio of two polynomial-chaos expansions) for cheap,
  differentiable forward evaluations. Relevant to tractability (vision §10) but NOT our novelty.
- **T-S4 — directional complex error geometry.** The lognormal-mag/normal-phase model gives the
  "kidney-shaped", away-from-origin error cloud (Fig. 1) — multiplicative error never lets the FRF sit at
  zero. Useful intuition for why amplitude-only Gaussian noise is wrong for FRFs.

### 1.2 Das & Debnath 2020 (MSSP 136:106524) — Bayesian updating with INCOMPLETE COMPLEX modal data
- **T-D1 — mode-matching-free complex-modal likelihood.** Treat the system complex mode shapes Φ as
  LATENT optimization variables and split every complex residual into real+imag Gaussian parts (Eqs.
  20–32). Because the system modes are inferred, you never have to pair measured ↔ analytical modes
  (the brittle step that needs an eigensolve every iteration). Directly relevant to our degenerate/near-
  degenerate tray modes (82.9/84.3 Hz pair; 337/337/337 Hz triple) and the ShockSat MAC-divergence we
  logged (eigh backward blows up at near-degenerate pairs).
- **T-D2 — joint mass + stiffness + DAMPING identification from complex modes.** Updates Rayleigh
  (classical) AND non-classical viscous damping with the complex eigenvalues/eigenvectors. Damping ID is
  the repeated weak spot (Schneider's CLT damping was poorly captured; our modal twins fix damping).
  Complex modes carry damping in their imaginary parts — the lever to identify it.
- **T-D3 — probabilistic damage/change detection** from the posterior parameter mean + Hessian covariance
  (Eq. 75): `P(parameter reduced by ≥ d)`. A decision-facing read-out (cf. our load-QOI read-outs).
- **T-D4 — Hessian (Laplace) uncertainty** as a fast alternative to sampling. Cheap but Gaussian-only;
  our rule keeps NUTS as the trust sampler, with Laplace as a labeled fast screen.

---

## 2. How these map onto the project vision levers and the StatFEM backbone

| Vision lever | Schneider technique | Das/Debnath technique |
|---|---|---|
| §4 discrepancy covariance (the central lever) | **T-S1/T-S2 = a concrete, dense-FRF discrepancy model with inferred space×freq correlation** | T-D1 supplies a complementary MODAL-domain residual structure |
| §6.1 robust twin under model error (widen+cover) | T-S2 inferred correlation is what lets bands widen honestly instead of collapsing | T-D2 keeps damping from soaking up model error as fake stiffness |
| §5.2 orthogonal output-space discrepancy F(k) | T-S1 sits on the OUTPUT (the FRF), where the discrepancy must live | — |
| §5.5 / 7004C interface load QOI (apparent mass) | T-S1 applied to drive-point apparent mass M=F/a (the load observable) | T-D3 change-detection ≈ margin read-out |
| Identifiability is the binding constraint (cross-cut) | inferred correlation length tells you the EFFECTIVE independent-data count | T-D1 avoids the mode-matching failure that masquerades as non-identifiability |
| Unknown stochastic forcing (likely novelty home, §5.0) | apparent-mass M=F/a is forcing-LEVEL independent → composes with T-S1 | complex modes are output-only friendly (OMA-adjacent) |

**Backbone reused:** the project's StatFEM = physics forward model + orthogonal output-space discrepancy +
sensor noise + held-out-coverage trust gate + NUTS convergence gate. Both papers contribute LIKELIHOOD/
DISCREPANCY structure that drops into that backbone; neither changes the backbone.

---

## 3. The series of studies (A–F)

Each study lists: question · decision it supports · observable + quantity contract · forward model/FEM ·
likelihood (paper technique) · QOI · success gate · dataset · what would make it the WRONG question ·
readiness. Studies are ranked by READINESS-TO-RUN, not by assumed success.

### Study A — Discrepancy-model A/B for dynamic StatFEM FRF updating  **[EXECUTED THIS TASK]**
- **Question:** On dense FRF data from a structurally-wrong model, does Schneider's correlated complex
  error model (used as the StatFEM discrepancy) keep the posterior honest — held-out bands widen and
  COVER — where an iid-noise likelihood falsely collapses and mis-covers?
- **Decision supported:** which discrepancy model to standardize for the robust twin (vision §6.1).
- **Observable / contract:** drive-point + cross apparent mass M(ω)=F/a [kg], interface DOF, base-shake
  excitation; limiting behavior M(0)→static mass, peaks at coupled resonances. nmp=2, Nf log-spaced.
- **Forward model:** JAX 2-DOF coupled source/load dynamic-stiffness inverse (inference); 3-DOF truth
  (hidden DOF = model-form error). `code/forward.py`.
- **Likelihood:** V1 iid complex-Gaussian (R=I); **V2 Schneider correlated complex lognormal/normal**
  (T-S1+T-S2, σ_w/σ_θ/ℓ_f/r inferred); V3 decimated-iid baseline. NUTS, 4 chains.
- **QOI:** held-out high-band apparent-mass magnitude (load proxy) + coupled f1.
- **Gate:** all-variable R-hat≤1.05 & ESS≥200 & div<2% (convergence) + held-out 95% coverage ∈[0.9,1.0]
  (trust) + V2 strictly wider-and-covering vs V1's collapse.
- **Dataset:** fully synthetic (controllable truth). **Readiness: RUN.**
- **Wrong-question if:** the injected error exactly matches V2's assumed form (rigged). Mitigation: inject
  error with a DIFFERENT correlation length than V2's prior mean + a non-multiplicative component.

### Study C — Schneider dense-FRF updating of the suspended composite panel  **[design; synthetic+data]**
- **Question:** Can the Schneider likelihood update the Abaqus composite-panel FEM against the real LDV
  FRF (96 pts × 3200 freqs, 0.125–400 Hz) without point-selection, and does inferred ℓ_co,f match the
  visible model error band?
- **Decision:** panel ply-stiffness / support-stiffness calibration; pre-test sensor downselect.
- **Observable:** H1 velocity FRF over a dense grid; apparent-mass-style drive point. **Quantity contract +
  a data-provenance audit first** (coherence.txt is a mislabeled complex copy of H1 — must be resolved;
  `.mat` files are authoritative).
- **Forward model:** the existing Abaqus `CompPanel_SoftSupports` modal model → FRF synthesis (CMS reduce).
- **Likelihood:** Schneider T-S1+T-S2 on the dense FRF; ℓ_co,z over the real (x,y) grid in `XYcoords`.
- **QOI:** held-out spatial-point FRF coverage (hold out a subset of the 96 points).
- **Gate:** held-out point coverage + convergence; ℓ_co,z physically sane vs panel size.
- **Dataset:** REAL (suspended panel). **Readiness: HIGH** (data + FEM in folder; needs `.mat` ingest +
  CMS FRF synthesis). **Wrong-question if** measurement coherence is too low in the band of interest.

### Study D — Mode-matching-free complex-modal twin of the hexapod tray (degenerate modes) **[design; synthetic+data]**
- **Question:** Does Das/Debnath's latent-system-mode likelihood update the tray FEM through its
  near-degenerate clusters (82.9/84.3; 337×3) where eigh-backward MAC likelihoods diverge — and does it
  recover DAMPING the frequency-only twins cannot?
- **Decision:** tray stiffness + joint damping calibration; the symmetry-breaking-observable question
  already open in the coupled-QOI thread.
- **Observable:** complex modes (eigenvalues + partial complex shapes) from a synthetic damped tray; later
  real tap-test modes. **Quantity contract:** mass-normalized complex modes; MAC on invariant subspaces of
  degenerate clusters.
- **Forward model:** hexapod CalculiX/JAX tray (modes already computed: `out/hexapod_modes.json`).
- **Likelihood:** T-D1 real/imag residual split with Φ latent (no mode pairing) + T-D2 damping; under NUTS
  (port of the MAP objective) with the subspace-MAC fix already specced in `notes/todo.md`.
- **QOI:** held-out mode coverage; damping posterior; change-detection P(stiffness↓) (T-D3).
- **Gate:** 0 divergences through the degenerate clusters (the specific failure we logged) + held-out mode
  coverage. **Readiness: HIGH-MED** (FEM in folder; needs the latent-mode NUTS port).
- **Wrong-question if:** the tap test cannot resolve the degenerate pair at all (then it is a test-design,
  not an inference, problem).

### Study E — Schneider interface-admittance discrepancy → probabilistic 7004C notch (ShockSat × tray) **[design; synthetic+data]**
- **Question:** Put the Schneider correlated complex error on the COUPLED interface apparent mass (FBS),
  under unknown forcing; does the held-out-validated interface-load posterior give a less-conservative-yet-
  covering 7004C notch than the deterministic limit?
- **Decision:** the force-limit notch programmed into the shaker (the vision §5.6 claimed artifact).
- **Observable:** interface apparent mass / net-CG load; response-limit-proxy accel (vision §2.2).
- **Forward model:** ShockSat FEM (assembled) + hexapod tray, FBS-coupled (existing coupled-QOI code).
- **Likelihood:** Schneider T-S1+T-S2 at the interface admittance (the orthogonal output space, §5.5).
- **QOI:** probabilistic interface load → notch depth with held-out coverage.
- **Gate:** held-out interface-load coverage; notch defensibly below deterministic with coverage intact.
- **Dataset:** ShockSat real FEM + (later) test. **Readiness: MED** (depends on A succeeding + coupled
  thread sign-off D2/D3/D4). **This is the patent-relevant endpoint — gated on IP disclosure.**

### Study F — Discrepancy-prior front-end stress test (config-delta → Schneider hyperprior) **[design; synthetic]**
- **Question:** Can a known config delta (e.g. pressurization, missing sub-assembly) be turned into a
  Schneider correlation-hyperparameter PRIOR (which bands, which ℓ_co,f, how much σ_w) that WIDENS and
  still covers — never falsely narrows (vision §6.2 guardrail)?
- **Decision:** the user-facing discrepancy-prior dial/LLM front-end.
- **Likelihood:** Schneider T-S2 hyperprior driven by an elicited delta; held-out coverage gates any
  tightening. **Readiness: MED-LOW** (needs A + a small knockdown library). **Wrong-question if** the delta
  cannot be mapped to discrepancy STRUCTURE (then it is a scalar fudge — the thing we must avoid).

### Study B — MPL test-stand damping/stiffness twin from the scrappy taps (Das/Debnath lens) **[design; synthetic+data]**
- **Question:** Do the 13 single-axis MPL tap CSVs support a complex-modal damping+stiffness update of the
  rebuilt MPL stand FEM, mode-matching-free, given the −3.7% ruler-coupling shift already measured?
- **Readiness: MED** (FEM rebuild is YELLOW/pending; data + features exist). Pairs with the in-flight MPL
  train/held-out split already in `notes/todo.md`.

### Readiness ranking (NOT a success score)
RUN: A · HIGH: C, D · MED: B, E · MED-LOW: F. Success scores (1–5) are assigned ONLY to A (executed) and
to designed studies as PROMISE with explicit "design-stage" labels in the deck scoreboard.
