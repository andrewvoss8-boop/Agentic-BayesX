# Decisions log — Schneider+Das/Debnath × StatFEM study program (2026-06-12)

Lead: Claude Code. Human: Andrew. Workspace: `artifacts/reports/papers_statfem_studies_20260612/`.
Write decisions here BEFORE acting (survives compaction). Canonical files win on conflict.

## D0 — Task interpretation (assumption, flagged for Andrew)
Andrew's ask: "review Schneider 2022 + Das/Debnath 2020 + statFEM; review folder work;
design a SERIES of studies combining the two papers' novel techniques with statFEM toward the
project vision; design fully-synthetic or synthetic+data examples using folder data (ShockSat,
MPL stand, suspended panel, hexapod 'tray' FEM); build/update FEMs if needed; do not stop until a
slide deck with figures + gifs (tufte), findings ranked 1–5, comprehensive next steps."
- INTERPRETATION: the primary deliverable is a **designed study program** + a **slide deck**. To keep
  the 1–5 ranking HONEST (not fabricated), I EXECUTE one vision-central, paper-combining synthetic
  study end-to-end (real NUTS + held-out coverage + checker), score it on evidence, and rank the
  remaining DESIGNED studies by readiness/promise with explicit "design-stage, not yet run" labels.
- This respects the project rules: no success/score claim without checker output; designed studies are
  not reported as results. (AGENTS.md Result-Status Standard; vision §13b "one run, one question".)

## D1 — No durable-file edits without Andrew sign-off
I do NOT edit `AGENTS.md`, checkers, sampler standards, or canonical notes (`notes/*`,
`docs/report/project_log.md`) in this task. All output stays inside this workspace. The project_log
row + notes updates are PROPOSED in `packet.md` and await Andrew. (System reminder + memory.md rule.)

## D2 — Headline executed study = "Discrepancy-model A/B for dynamic StatFEM FRF updating"
The vision's central open lever (§4) is the discrepancy covariance specification: too-independent →
false posterior collapse; too-flexible → ridge/non-identifiability. Schneider 2022's novel technique is
exactly a discrepancy model for DENSE FRF data: a multiplicative complex model error with lognormal
magnitude + normal phase, CORRELATED in space and frequency, hyperparameters inferred. So the single
most vision-central, runnable, paper-combining experiment is:
- TRUTH: a 3-DOF coupled source/load apparent-mass system (closed-form, damped). The inference FEM is a
  2-DOF coupled model → STRUCTURAL model-form error (a hidden 3rd DOF) = the "coarse/wrong model"
  robustness setup of vision §6.1.
- OBSERVABLE: drive-point + cross apparent mass M(ω)=F/a at the interface (the load-carrying observable,
  vision §6.1), nmp=2 "locations", Nf log-spaced freqs, with Schneider-structured correlated complex
  model error + small iid noise injected so the test of Schneider's error model is fair.
- A/B/C inference variants, each NUTS (NumPyro, .venv_nuts):
  - V1 iid complex-Gaussian likelihood (R=I) — the naive over-counting straw-man.
  - V2 Schneider correlated complex-lognormal/normal likelihood, hyperparameters (σ_w, σ_θ, ℓ_f, r)
    inferred — the candidate StatFEM discrepancy.
  - V3 frequency-decimated iid (a cheap practitioner baseline) — shows decimation ≈ poor-man's
    correlation handling.
- GATES: all-variable convergence (R-hat/ESS/divergences) + HELD-OUT FRF 95% coverage (trust gate) +
  physical-parameter interval width. Rank 1–5 from coverage + honest widening + convergence.
- WHY this combines BOTH papers: V2 is Schneider's likelihood used AS the StatFEM discrepancy; the
  held-out-coverage trust gate + orthogonal-output-space framing is the project's statFEM backbone; and
  Das/Debnath's complex-data / damping-ID lens motivates the damped-complex observable and the
  mode-matching-free design of the companion modal study (Study D).

## D3 — Forward model is JAX-differentiable, analytic (no FE solve in the loop)
3-DOF/2-DOF closed-form dynamic stiffness inverted in JAX → differentiable for NUTS. Reuses the physics
of `src/twodof/model.py` (verified backbone) but re-implemented in JAX. Keeps runtime to minutes.

## D4 — Synthetic-truth seed + injected error are recorded; held-out split is by FREQUENCY BAND
Truth params, injected discrepancy hyperparameters, and noise are written to `out/` so figures can show
clean-truth-vs-observed (AGENTS plot gate). Held-out = a contiguous high-frequency band excluded from the
likelihood, predicted, and coverage-checked (the honest trust gate; vision §7/§12). One synthetic dataset,
one realization — flight-to-flight variability NOT modeled (stated as a limitation).

## D5 — Real-data use is HONEST and design-stage for the full studies
Suspended-panel LDV FRF (96 pts × 3200 freqs) and hexapod tray FEM ground the DESIGNED studies (C, D) and
appear as real-data characterization figures. A genuine data-provenance finding is surfaced, not hidden:
`coherence.txt` contains COMPLEX values identical to `H1.txt` → it is a mislabeled export (coherence must
be real ∈[0,1]); the `.mat` files are the authoritative source and full ingest is a named follow-on. No
NUTS is run on real data in this task; doing so is the explicit next step.

## D6 — Deck built with system python3 (has python-pptx 1.0.2); figures tufte-linted
Plotting in `.venv_fem_phase1` (matplotlib); NUTS in `.venv_nuts` (jax/numpyro); deck in `/usr/bin/python3`.
Every numeric figure runs through `scripts/tufte_lint.py` and carries run/dataset + HYPOTHETICAL/SYNTHETIC
provenance stamps per the AGENTS plot gate.

## D7 — (2026-06-12, Andrew go: "carry on, realistic synthetic + held-out QOIs + evolving-band GIFs + a statFEM+Das/Debnath+Schneider method, be more ambitious")
New centerpiece = **Study G: a unified "modal statFEM" method + a realistic synthetic suspended-panel twin.**
Panel data-source questions are WITH ANDREW (packet §1c); Study C real calibration waits on his answers.
Study G is the dress rehearsal: same structure class (suspended panel, dense FRF), so when answers arrive we
point the same method at the real data.

## D8 — The unified method (what each paper contributes)
Generative model ("unified modal statFEM", code `ums`):
1. Parametric FEM K(θ) (quadrant stiffness groups + suspension scale), Rayleigh C(θ); M fixed.
2. **Das/Debnath layer**: latent complex modes — per mode m a latent eigenvalue λ_m (via ordered f_m, ζ_m)
   and latent shape coefficients c_m in a FIXED Ritz basis Φ0 (nominal-FEM modes, eigh done OFFLINE once —
   no eigensolve and no mode pairing inside NUTS; degenerate-safe per Study D). A soft eigen-residual
   ||(λ²M+λC(θ)+K(θ))Φ0c|| ~ N(0, τ²) ties modes to the FEM; τ is INFERRED = "how wrong is the FEM
   eigenstructure" (the statFEM let-the-data-correct-the-physics lever, in modal space).
3. FRF synthesis from latent modes by complex-mode residues (scale-invariant residue ψψᵀ/(ψᵀ(2λM+C)ψ)).
4. **Schneider layer**: multiplicative complex log-error on the dense FRF, magnitude+phase Gaussian,
   correlated in frequency AND space, hyperparameters (σ_w, σ_θ, ℓ_f, ℓ_z) inferred.
5. **statFEM trust gates**: held-out spatial points + held-out QOIs coverage; all-variable convergence.

## D9 — Tractability deviations from the papers (documented, with self-tests)
- Schneider's correlation split is ADDITIVE (Eq. 19/25). We use the SEPARABLE (multiplicative) Kronecker
  R = R_f ⊗ R_z — the named alternative he contrasts against — because with an exponential (OU/Markov)
  frequency kernel the likelihood whitens in O(n) via AR(1) innovations (no Cholesky of n×n, no eigh in the
  loop). Self-test: separable+scaled likelihood == dense MVN logpdf on a small case (1e-8).
- Noise floor: real LDV FRFs bottom out at antiresonances. We model it with a delta-method per-line variance
  inflation s_i²=1+(σ_add/(σ·|H_pred,i|))² folded INTO the correlated model (cov = σ²S(R_f⊗R_z)S). Exact for
  the scaled-correlation model; approximates correlated+independent-floor; marginal variances match. σ_add inferred.
- Phase residual wrapped to (−π,π] (a.e. differentiable; discontinuity suppressed exactly where s_i is large).

## D10 — Realism: NO injected Schneider error in Study G
The discrepancy the method must absorb is GENUINE structural mismatch: truth = heterogeneous bending field
(smooth variation + a local soft patch) + uneven suspension + NON-proportional damping (local dashpot) +
drive-side mass loading; inference FEM = 4 quadrant groups + one suspension scale + Rayleigh damping only.
Measurement effects injected: additive noise floor, 2% multiplicative sensor noise, per-point ±0.5 dB
calibration gains (generation only; absorbed by σ_w in inference), low-frequency drift junk (display band).
This makes Study G ALSO the adversarial-discrepancy test from the next-steps list (error NOT from the
assumed family).

## D11 — Held-out QOIs (the verification Andrew asked for)
5 of 20 scan points held out entirely. QOI-A = peak |accelerance| 10–200 Hz at each held-out point
(response-limit proxy, vision §2.2); QOI-B = band-RMS at each held-out point (GRMS-flavored). 10 intervals;
gate = ≥8/10 covered by 95% CIs (nominal 95%, small-sample slack stated). Secondary: per-mode ζ recovery vs
truth (Das/Debnath payoff: latent modes can carry per-mode damping even though C(θ) is Rayleigh-only).
Comparators: deterministic nominal FEM (point predictions) and an iid-discrepancy variant (ℓ_f→0, R_z=I).

## D12 — GIFs (evolving predictive bands)
GIF-1 scan accretion: observed points 2→4→6→9→12→15 (LDV raster order — how a real scan accumulates);
GIF-2 band extension: data band 10–60→10–100→10–140→10–200 Hz ("you can't certify what you haven't excited").
Frame runs are REDUCED (2 chains × 500+500) and each frame PRINTS its own R-hat + n_data; the headline run
uses 4 chains with full gates. Frames resumable (skip existing npz).

## D13 — Ordered-frequency parameterization
Latent f_m via positive increments (f_m = Σ δ_k, δ_k LogNormal around nominal gaps) to kill mode-permutation
label switching; shapes prior c_m ~ N(e_m, ·) centered on the nominal mode (deviation = mixing with
neighbors, exactly how FEM error perturbs shapes).

## D14 — Smooth complex-residual likelihood (the Study G sampler unlock; supersedes part of D9)
Empirical sequence (logs/probe_medium.log, logs/probe2.log):
1. EXACT Schneider form (log|·| + wrapped phase): NUTS frozen at init, 100% divergences — gradient cliffs
   (phase wrap at each resonance crossing; 1/|H| spikes at antiresonance zeros).
2. Floor-INFLATED exact form (delta-method s_i): still frozen (67-100% div) — the cliffs are in the
   residual map itself, not the weights.
3. SMOOTH small-error-equivalent form r = (data − H)/(|H| + κ), κ = inferred floor: 0.3% divergences,
   chain moves, in-band frequencies recover to <0.1 Hz in a 1-chain probe.
DECISION: Study G uses form 3. Honest framing: this is Schneider's multiplicative error to first order
(Re r ≈ log-mag error, Im r ≈ phase error); the directional "kidney" tail geometry is lost; documented in
method_ums.md §3 + deck findings slide. The finding "exact form defeats HMC; Schneider's own SuS choice
sidesteps it" is reported as a methodological result, evidence = the probe logs.
ALSO: peak-picked initialization of latent frequencies (init only, priors unchanged at nominal) — dense-FRF
posteriors are needle-sharp in resonance positions; init misaligned by several half-bandwidths is a cliff.
τ floor 0.004 (the FEM eigenstructure is never exact; bounds the eigen-residual needle).

## D15 — Study G run-1 headline FAILURE + fix (recorded before rerun; archived artifacts)
Run-1 (4 chains, default initial step_size=1.0, ta=0.85): R-hat 236, ESS 2, 56% divergences, QOI 0/10,
predictions 5-10x high — chains scattered into DIFFERENT basins and stuck (the single-chain probe2 with
identical model was healthy: 0.3% div). Mechanism: dense-FRF posteriors are needles in the latent
frequencies/shapes; numpyro's initial step-size search from 1.0 lets early warmup trajectories jump
basins (e.g. shape sign flips: the residue is c-sign-invariant so -c is a true local mode), after which
chains cannot cross back. Archived: out/ums_summary_FAILED_run1.json, out/ums_headline_FAILED_run1.npz.
FIX (run-2): initial step_size=5e-4 (adapts UP via dual averaging), target_accept 0.9, warmup 1000.
Validation: probe3 = 2-chain agreement check BEFORE recommitting the full budget. If run-2 also fails its
gates, Study G ships as a documented YELLOW honest-negative with the failed diagnostics on every figure.

## D16 — Gauge fix: pinned mode-shape normalization (run-2 model change)
Probe3 (small steps): divergences 2% (fixed) but 2-chain R-hat 73 — chains in separate basins ALONG the
per-mode complex-scale gauge valley: the FRF residue psi psi^T / a is invariant to c -> alpha c (any complex
alpha), so each mode carries a 2-D likelihood-flat direction that the prior only weakly pins. Fix = the
standard modal normalization (as in Das/Debnath): the m-th component of each latent shape is FIXED to 1+0i;
only the B-1 off components are sampled (cr_off/ci_off). Removes 26 pure-gauge dims and the valley exactly.
Validation = probe4 (2-chain agreement) before recommitting the full budget.

## D17 — Practitioner damping prior (run-2, after probe4)
Probe4 (gauge-fixed): divergences 0.7% but 2-chain R-hat 215 — the REMAINING multimodality is PHYSICAL:
per-chain zeta medians flip mode-by-mode between ~0.5% (mode kept as physics) and ~7% (mode smeared, the
Schneider field paints its peak instead) = the Kennedy-O'Hagan physics-vs-discrepancy trade-off appearing
PER MODE in the unified model — the vision §4 lever observed in the modal layer. Counter (defensible
engineering knowledge, not tuning-to-truth): a practitioner knows panel modal damping is ~0.4-2% →
zeta ~ LogNormal(log 0.008, 0.4) (95% in [0.36%, 1.8%]). If probe5 still scatters, Study G ships as a
documented honest negative: "mode-level physics/discrepancy multimodality under-identifies the unified
model on dense FRFs at this discrepancy scale" — with per-chain data-space agreement analysis per the
AGENTS identifiability gate (multimodal in parameter space + agreeing in data space = under-identification
finding, not a sampler bug).

## D18 — FINAL Study G attempt (pre-committed: results ship as-is with labels)
Probe6 named the frozen coordinates: in-band shape imaginaries (ci_off modes 6,9) AND s_susp (R-hat 125,
ESS 1.0 = coordinates barely move). Diagnosis: posterior CONDITIONING — needle directions (frequencies,
~1e-4 relative) force a tiny step; flat directions (weakly-identified shapes, the band-uninformed
suspension scale) then mix glacially; 450-step diagonal mass adaptation cannot learn the scale spread.
Fixes (standard, documented): (1) s_susp FIXED at nominal — unidentifiable from the 10-60 Hz band
(suspension modes at 2.2 Hz; honest, like fixing out-of-path params); (2) per-mode shape-prior widths —
out-of-band modes get tight (0.08/0.03) priors; (3) warmup 1500 (mass-matrix windows), max_tree_depth 10.
PRE-COMMITMENT: this is the final attempt today. Pass gates -> full deliverable. Fail -> Study G ships
YELLOW honest-negative with the full diagnosis chain (D14-D18) + per-chain data-space agreement analysis,
per the AGENTS identifiability gate. Either way the frames/GIFs run with the same final model and carry
per-frame labels.

## D19 — ANDREW ANSWERED the panel data-source questions (2026-06-12, mid-run)
1. Excitation: IMPACT HAMMER on the BACK of the panel at the TOP-RIGHT node (yellow in his photo).
2. H1 = velocity / force = MOBILITY, units (m/s)/N  ->  NOT accelerance. CORRECTION REQUIRED:
   figC1 ylabel + study_c.py quantity contract said "accel/force"; fix to mobility. (Peak-match
   conclusions unaffected: peak FREQUENCIES of |mobility| vs |accelerance| differ negligibly at
   these dampings; the discrepancy-floor numbers stand.)
3. Photo: 5x5 = 25 measurement points (matches H1.mat 25 rows); drive = top-right grid node.
4. Low-frequency coherence loss: rigid-body modes at low f (as assumed; inference band starts ~8-10 Hz).
REMAINING small unknowns: row-ordering of H1.mat's 25 rows vs the photo grid (assume raster, verify by
MAC vs FEA shapes); physical panel dimensions (extract from FEA xy.xlsx). UNBLOCKED: real-panel UMS
calibration (Study C -> UMS) once Study G's final run reports. FEA mode shapes available in
FEA results/Output/u1.xlsx u2.xlsx u3.xlsx + xy.xlsx (per readMe) -> Ritz basis at measured points.

## D20 — Full-ambition UMS = documented HONEST NEGATIVE; pivot to REAL-SHAPES production variant
Final full run (4x1500+400, all fixes D14-D18): R-hat 364, ESS 2, div 1.1% (divergences FIXED, mixing NOT);
held-out QOI 0/10, predictions ~10x biased high (med 595 vs truth 55; deterministic FEM 66 is closer).
ROOT CAUSE (probe6): the free IMAGINARY mode-shape components (ci_off) are the worst-conditioned coords
(R-hat 130-176, ESS 1) — 13 modes x 16 complex Ritz coeffs is over-parameterized for 15 spatial points;
multimodal shape space -> chains in different basins -> mispredicts held-out points.
Archived: out/ums_summary_FULL_ambition.json, ums_headline_FULL_ambition.npz (the negative, kept for the deck).
PIVOT: REAL-SHAPES production variant (UMS_REAL=1) -- mode shapes REAL (drop ci_off, -208 dims), complex-ness
of each mode comes ONLY from its complex eigenvalue lambda_m (the standard lightly-damped / proportional-shape
approximation, valid here: zeta<2%). Tighter in-band shape prior sd 0.15. Still combines all three papers
(statFEM held-out gate + Schneider discrepancy + Das/Debnath latent modes/freqs/damping, no eigensolve).
Probe 2-chain BEFORE committing the full budget.

## D21 — Study C2 real-panel prep RESULT (unblocked by D19; honest scope)
Extracted FEA node coords (924) + U3 normal-displacement mode shapes (46 modes) from the Output xlsx
(comma-suffixed text cells). Measured operating shapes = H1 rows at the 8 strongest 8-60 Hz peaks.
MAC(measured, FEA-interp-to-grid) over 8x(margin,ordering) hypotheses -> BEST ordering "ymajorfx" margin 0.12,
mean MAC 0.49 but per-mode MAC = [0.98, 0.99, 0.99, 0.78, 0.0, 0.15, 0.02, 0.0]: the FIRST 4 modes
(8.2/10.5/22.1/24 Hz) map with MAC ~0.8-0.99 = the H1-row<->grid mapping and panel scale are PINNED for the
low band. Higher modes (>=40 Hz) are NOT MAC-resolvable on a 5x5 grid (fine spatial detail aliases) - expected,
honest. Mean-MAC weakly discriminates raster DIRECTION among symmetric hypotheses (caveat). Saved
study_c2_mapping.json + study_c2_ritz.npz (Ritz pieces for the real-panel UMS). This makes the real-panel UMS
RUNNABLE for the low/well-resolved modes; exact LDV coordinates from the source would supersede the margin scan.

## D22 — UMS-FEM (physics-bound shapes) = the PRODUCTION method (run_ums2.py)
Nominal sanity check (pre-sampling): FEM-shape held-out QOI-A reproduces the direct-FEM solve EXACTLY
(66.4 vs 66.5) and sits ~20% above truth (the model-form error to be reduced) = the architecture GENERALIZES
spatially. Smoke2: R-hat 290->4, 6x faster, 0.6% div. Shapes = eigh(K_tilde(theta)) (B x B, differentiable,
in-band modes separated; NM=11 avoids the 85 Hz degenerate pair); damping zeta_m latent (Das/Debnath);
Schneider discrepancy + held-out gate unchanged. ~22 params. probe8 (2-chain 800+400) validates before the
4-chain headline. THE FRAMES/GIFS will use run_ums2's model. The full deliverable now has BOTH:
UMS-full (documented negative: latent shapes don't generalize) and UMS-FEM (the working method).

## D23 — Converging config + the HONEST held-out finding (final Study G science)
UMS-FEM converges with: ONE global damping scale gz (per-mode zfac removed = the ridge source),
FIXED noise floor, tighter priors. R-hat 1.01, ESS 167, 0 div (4-chain headline pending).
HELD-OUT QOI UNDER-COVERS (~1/10): held-out peaks predicted ~2-3x too high. ROOT CAUSE is genuine
MODEL-FORM error, NOT a sampler/prior problem -- the DETERMINISTIC nominal FEM ALSO over-predicts the
held-out truth peaks badly (in-patch node 73 vs truth 36 = 2x; the truth's soft+damped patch + heterogeneity
locally reduce response, UNREPRESENTABLE by 4 uniform quadrant groups + proportional damping). The smooth
multiplicative discrepancy is CALIBRATED ON OBSERVED nodes (where the FEM is less wrong) and cannot
extrapolate the LOCAL held-out error -> over-confident at held-out points. Widening damping prior made it
WORSE (gate-chasing rejected). THIS IS THE RESULT: the held-out gate catches an over-confident twin =
the gate WORKING (vision §7 "convergence is a diagnostic; trust gate is held-out QOI"; §4 physics-vs-
discrepancy confounding). Spatial analog of Study A's extrapolation negative. Report per-node coverage
(covers interpolatable nodes, misses the patch/corner = informative). NO coverage fabrication.

## D24 — Study G final deliverable scope (decisive, end of this leg)
Study G ships HONEST with: (1) the unified method (3 papers, self-tested); (2) UMS-full = documented
over-parameterization negative (free latent shapes don't generalize, R-hat 364); (3) UMS-FEM = the
production method that CONVERGES (R-hat 1.01) -- the sampler-pathology ladder D14-D23 is a real
methodological contribution; (4) the held-out-QOI honest negative (converges but under-covers under LOCAL
model-form error). GIFs (bands evolving as data accrues) built on UMS-FEM. Real-panel prep (C2/D21) unblocked
by D19. This is a rich, vision-central, HONEST result; no fabricated success.

## D25 — Study G FINAL honest result: physics-vs-discrepancy BIMODALITY (the project's central problem, posed)
4-chain all-variable gate: R-hat 50.8, ESS 2 (the 2-chain probes converged by LUCK = same basin).
Per-chain diagnostic (out/ums2_bimodality.json), BOTH parameter AND data space:
  chain0: gz=0.01 (zero-damping basin) -> QOI-A med [330,109,327,450,229] (huge undamped peaks)
  chains1-3: gz~1.1-1.3 (damped basin) -> QOI-A med ~[101,48,91,114,78] (consistent, ~2x over truth)
  truth QOI-A [54.6,32.8,48.9,35.6,38.1]
=> The same FRF is explained EITHER as "damped structure" OR "undamped structure + large discrepancy"
   = Kennedy-O'Hagan physics-vs-discrepancy confounding (vision §4), reproduced in the unified method.
   NUTS finds BOTH basins (R-hat 50) -- this is the under-identification finding, NOT a sampler bug
   (AGENTS identifiability gate). AND even the sensible basin over-predicts held-out QOI ~2x (local
   model-form error at the soft patch + confounding biasing damping low) -> under-coverage 1/10.
DECISIVE STANCE (after 10 probes + 3 full runs): STOP chasing convergence. This IS the result. Study G
ships YELLOW honest-negative that SHARPLY POSES the project's central open problem with a working,
self-tested unified testbed. The cure = CONSTRAIN the discrepancy (orthogonal/cut-Bayes, vision §5.2) so
the "undamped+discrepancy" basin is forbidden -> the explicit next research step. NO fabricated success.
This is the strongest HONEST outcome and directly advances the research program.

## D26 — (Andrew go: "move on to that; do not stop; iterate until meaningful experiments on ALL vision goals +
## documentation interesting to Girolami, Bilionis, and traditional aerospace companies")
PLAN (this leg):
- STUDY H = THE CURE / THE DECISIVE A/B (vision §13.2 "orthogonal output-space F(k) vs same-space, gated on
  held-out QOI coverage" — never run until now; Study G's bimodality is the perfect testbed):
  - H-orth (Plumlee-lite): precompute parameter FINGERPRINTS t_j = d(residual)/d(log θ_j) at init (plug-in
    gradients, as Plumlee does); add a tight Gaussian factor on the residual's projection onto each
    fingerprint -> the discrepancy CANNOT absorb what a parameter can explain -> the "undamped+discrepancy"
    basin should die. (Minor documented double-count: 7 directions of ~24k.)
  - H-local: per-quadrant damping gz_g (hierarchical, partially pooled) mapped to modes via kinetic-energy
    fractions -> the soft+damped patch becomes locally representable -> held-out over-prediction should drop.
  - Arms: G-baseline (run) vs H-orth vs H-local vs H-orth+local. Gates: 4-chain convergence (bimodality
    dead?) + held-out QOI coverage. THIS is the thesis/patent non-obviousness experiment shape.
- STUDY I = UNKNOWN STOCHASTIC FORCING (vision §5.0, the likely novelty home; first experiment on this axis):
  same twin, response-only data with an UNKNOWN smooth random force spectrum. A/B: (a) joint inference of a
  coarse log-F GP (three-way physics x discrepancy x forcing) vs (b) TRANSMISSIBILITY observable a_p/a_drive
  (forcing cancels exactly — the apparent-mass logic). Compare identifiability + structural QOI recovery.
- DOCS: research_narrative.md (plain-English arc for the three audiences) + deck audience slides + checker.

## D27 — Study H + Study I results (probe scale, 2-chain, labeled)
STUDY H (constrained-discrepancy A/B, vision §13.2): ALL three constraints KILL the bimodality —
H_orth R-hat 1.009 (gz->2.76 both chains), H_local 1.006 (gz~0.90), H_both 1.014 (gz~1.0); 0 divergences
everywhere. The identifiability half of the thesis CONFIRMED: constraining the discrepancy (orthogonal
fingerprints OR spatially-local damping) removes the physics-vs-discrepancy basin structure. BUT held-out
QOI coverage NOT restored (1/0/0 of 10) -> the under-coverage is a SEPARATE failure (local patch model
error unreachable by a smooth field calibrated on observed nodes) that identifiability fixes cannot touch.
DECOMPOSITION FINDING: bimodality (identifiability) and held-out under-coverage (extrapolated local model
error) are distinct failure modes with distinct cures. Note: H_orth over-absorbs into damping (gz 2.76 >
truth-consistent ~1.2) = the known Plumlee plug-in-bias trade, reported as-is.
STUDY I (unknown forcing, vision §5.0 first experiment): HONEST DOUBLE NEGATIVE — I_ratio
(transmissibility) R-hat 61: dividing by the drive-point response cancels forcing BUT ALSO the level
information that pinned the physics -> identifiability collapses (response-only ratios are NOT apparent
mass; M=F/a needs the measured FORCE). I_joint (3-way physics x discrepancy x forcing) R-hat 128, logF
coverage 0%: naive joint inference fails at this difficulty. => §5.0's identifiability hole demonstrated
concretely; the cure direction = force-side observables (measured interface force / apparent mass) or
multi-reference data, exactly the vision's apparent-mass framing.
SCOPE DECISION: vision goals now each have a meaningful executed experiment (audit table in
research_narrative.md); remaining budget goes to finishing CRISP documentation, not more sampler campaigns.

## D28 — (Andrew "proceed") STUDY J: REAL-PANEL UMS calibration (vision §7 centerpiece; the synthetic→real step)
First application of the UMS method to REAL data. Inputs already staged:
- H1.mat = 25-pt mobility (m/s)/N, impact at top-right (D19); C2 mapping ymajorfx pins H1-row↔grid (low modes MAC 0.98-0.99).
- Abaqus FEA: 924 nodes, 46 U3 mode shapes, eigenfrequencies (parsed). These ARE the physics basis (no synthetic FEM).
METHOD (UMS-FEM ported to real data):
- Ritz basis Phi0 = FEA U3 shapes interpolated to the 25 LDV points (griddata); the 'parametric FEM' = a few
  global stiffness/density scales on the FEA modal model (we have shapes+freqs, not element matrices -> calibrate
  modal frequencies via per-mode-group scale + a global density scale; damping = global gz on a light Rayleigh).
- Likelihood = Schneider smooth complex residual on real H1 over a clean band (8-60 Hz, where coherence is good).
- TRUST GATE = hold out 5 of 25 LDV points; predict their mobility + peak-QOI; coverage.
HONEST SCOPE (state loudly): single impact reference (mobility, not apparent mass -> forcing the SAME for all
points cancels in row-normalization only if we work per-column; here forcing IS measured so it's fine); mapping
is margin-scan (exact LDV coords would supersede); REAL = first real-data calibration but still ONE test, ONE
realization, no flight relevance. Expect (per Study G/H lessons) the held-out gate to be the story whether it
covers or not. Outputs -> ../out/studyJ_*. Probe 2-chain before 4-chain.

## D29 — Study J real-data iteration (probe scale)
First probe (11 per-mode freq scales): R-hat 3.6, 5.4% div, QOI 0/5 — per-mode freq + amplitude + discrepancy
= a ridge (freqs drifted). REVISED to ONE global frequency scale sf (Study C showed FEA uniformly ~+1-2%
stiff -> a global stiffness scale captures most; discrepancy handles per-mode residuals) + tightened amplitude
prior around the data/FEA peak-matched init (Normal(LGAMP0,0.5), was Normal(0,3)) + smaller step. Architecture
keeps Study G's lesson: FEA mode SHAPES FIXED (generalize spatially); calibrate only global freq + global
damping + global amplitude + Schneider discrepancy = 7 params. probe2 pending. HONEST: real-data calibration
is the §7 centerpiece but inherits all the synthetic identifiability lessons; expect the held-out gate to be
the story (cover or not) on REAL data.

## D30 — Study J real-data: the multimodality is FUNDAMENTAL (appears on real data too)
probe2 (global freq scale): R-hat 526, 0 div, ESS 1 -> chains in DIFFERENT basins (each smooth, no crossing) =
the SAME amplitude/damping-vs-discrepancy multimodality from Study G, now confirmed on REAL data. The peak
mobility height ~ gamp*phi^2/(2*zeta*wm) so gamp (amplitude) and zeta (damping gz) are CONFOUNDED in peak
height -> a ridge. FIX (Study H lesson applied to real data): FIX the amplitude at its peak-matched value
(remove from sampling), infer only damping with a tighter prior (gz~LogNormal(0,0.25)). 6 params. probe3 pending.
HONEST HEADLINE either way: the real-panel calibration reproduces the project's central identifiability finding
on REAL data (not a synthetic artifact) -- which is itself the §7 result worth reporting. global freq scale ~1.06
(physically sensible) is recovered even amid the multimodality.

## D32 — (Andrew "continue") STUDY K: per-mode frequency calibration on real data (refine Study J's 2/5)
Study J (global freq scale) converged but only 2/5 held-out coverage. Study C showed per-mode FEA freq errors
vary 0-6% -> a single global scale leaves held-out peaks at the wrong frequency. Now that amplitude is FIXED
(the ridge that broke the first per-mode probe), per-mode freq scales should be identifiable (each pinned by
its sharp peak, the Study D lesson). A/B: K-global (=Study J) vs K-permode, both amplitude-fixed, on REAL data.
Gates: 4-chain convergence + held-out QOI coverage. Honest hypothesis: per-mode freqs help coverage (peaks land
right) OR they don't (the limit is shapes/discrepancy, not frequency) -- either is a real finding. Outputs -> ums5/studyk.

## D34 — CORRECTION of D33: per-mode freq calibration DOES help (5/5 on REAL data) — the probe misled
D33 (based on the 2-chain PROBE: per-mode R-hat 3.75, QOI 0/5) concluded "per-mode does NOT help." The
rigorous 4-chain run REVERSES this: K_permode R-hat 1.0066, ESS 258, 0 div, held-out QOI **5/5** (vs global 2/5).
The 2-chain probe was UNDER-WARMED (500 vs 1000 warmup) -> false negative. CORRECTED FINDING:
- Per-mode frequency calibration CONVERGES on real data AND achieves 5/5 held-out coverage.
- It covers by BETTER LOCATION, not vagueness: per-mode bands similar width to global (rel-bw ~1.3-3.0 both),
  but per-mode median/truth = 1.0-2.0x vs global 2.4-3.0x.
- WHY: FEA low-mode freq errors are LARGE (mode1 FEA 9.53 vs exp 8.25 = +15%); a single global scale can't fix
  per-mode errors, so global leaves held-out peaks at wrong frequencies -> miss. Per-mode lands them right.
- Per-mode calibrated freqs [8.3,10.5,22.4,25.1,39.2,...] match exp peaks [8.25,10.5,22.12,24,39.88,...] well.
META-LESSON (reinforces Bilionis epistemics, now in REVERSE): cheap probes mislead in BOTH directions — Study G's
2-chain "converged and was wrong" (false positive); Study K's 2-chain "failed and was wrong" (false negative).
ONLY the 4-chain all-variable gate decides. This is the single strongest HONEST real-data result of the program:
the unified method, properly configured (FEA shapes fixed + per-mode freq + fixed amplitude + Schneider
discrepancy), predicts ALL 5 never-measured-point peak mobilities on the REAL panel within calibrated bands, AND
corrects a 15% FEA frequency error. CAVEATS: bands wide (calibrated not sharp); pt-5 median still 3.3x (covers);
ONE test/realization, single reference, margin-scan mapping -> real-data EVIDENCE, not validated flight science.


## D35 — Study L: can we SHARPEN the Study-K real-data bands? (no new data)
**Context.** Study K covers 5/5 held-out real points but with WIDE bands (95% CI ~1.3-3x median). Honest open
question I flagged to Andrew: is that width fundamental, or can per-mode residue-amplitude calibration sharpen it?
**Design (REAL-panel A/B, builds on study_k per-mode freq = the 5/5 winner):**
  L_freqonly = Study K per-mode frequency only (am=1)            -> reproduce 5/5, wide (control).
  L_freqamp  = per-mode frequency + per-mode residue amplitude a_m ~ LogNormal(0,0.2), global damping, gamp fixed.
**Hypothesis / risk.** a_m scales modal peak height, which the global damping gz and gamp also scale -> a partial
amplitude ridge (the D30 pathology, now per-mode). PASS = R-hat<=1.05, coverage stays >=4/5 AND median band ratio
drops materially. FAIL (ridge) = R-hat blows / coverage drops -> finding: width is the amplitude/shape limit, needs
multi-reference data. Either result honest. Decision = 4-chain all-variable gate ONLY (D34 lesson; probe = crash test).


### D35 RESULT (4-chain gate)
- **L_freqonly** (= Study K per-mode freq, control): R-hat **1.007**, ESS 258, 0 div, **QOI 5/5**, band 4.83x.
  INDEPENDENTLY REPRODUCES the Study K win (robustness confirmed on a re-run).
- **L_freqamp** (per-mode freq + per-mode residue amplitude a_m): R-hat **14.76**, ESS 2, 0 div, 19-min runtime
  (sampler fighting a ridge). NON-CONVERGED -> its 0/5 is a non-convergence SYMPTOM, not a coverage result.
- **VERDICT (honest negative, physically meaningful):** you CANNOT sharpen the bands by adding per-mode amplitude
  freedom from a SINGLE impact reference. Per-mode FREQUENCY is identifiable (each sharp peak pins one frequency);
  per-mode AMPLITUDE is confounded with damping + global amplitude (the D30 ridge, now per-mode) -> non-identifiable.
  The ~4-5x band width is the honest SINGLE-REFERENCE limit. Sharper bands require MORE data (multi-reference /
  roving excitation), NOT a fancier model. This is the concrete "where to spend budget" answer for aerospace.
- Artifacts: out/studyl_summary.json, figures/figL_sharpen_ab.png. No success claim beyond the converged control.


## D36 — Study M: virtual sensing under SENSOR FAULTS (new paper: Yan et al. 2026, AST) — calibrated physics-Bayes vs spatial interpolation
**Paper.** Yan, Zhang, Zhou, Sun, Wang, Liu, "Physics-Informed Digital Twin for Spacecraft Structures under Sensor
Faults: Virtual Sensing via a Frequency Attention U-Net and Closed-Loop Model Updating," Aerospace Sci. & Tech. 2026.
Core problem: reconstruct MASKED (faulty) sensor channels' frequency responses by fusing a ROM physics prior with a
neural operator (FNO-gated U-Net), then drive closed-loop FEM updating. Their baseline (SPATIAL INTERPOLATION) fails
by up to 48 dB at high-frequency LOCAL modes (spatial aliasing); their FAU limits masked-channel error to 8-10 dB.
Headline metric: log-amplitude main-peak error in dB.
**Gap their method leaves (what our Bayesian backbone fills).** Their reconstruction is a DETERMINISTIC point estimate
with NO uncertainty, and the closed loop feeds reconstructed "virtual ground truth" back as if it were measured data
(circular / double-counting -> overconfidence; the Kennedy-O'Hagan / Brynjarsdottir-O'Hagan trap our framework avoids).
**Study M (REAL panel, NO new data, NO new sampling).** Reuse Study K's converged per-mode posterior (studyk_permode.npz
magpred at the 5 held-out = "masked" LDV channels) + the real complex mobility. Treat the 5 held-out points as FAULTY
(masked) sensors (paper's protocol: masked measurements retained only for POST-HOC eval). Reconstruct them two ways:
  (1) SPATIAL INTERPOLATION baseline (paper's): per-frequency griddata(observed 20 pts -> masked 5 pts) on complex FRF.
  (2) BAYESIAN physics virtual sensing (ours): Study K posterior-predictive median + 95% band.
**Port the paper's exact metrics (dB):** main-peak amplitude error E_amp=|HdB_pred(w*)-HdB_meas(w*)| (w* = measured-peak
bin); channel RMSE in dB; SPLIT low band 8-25 Hz (global modes) vs high band 25-60 Hz (local modes) to test the paper's
"interpolation fails at high-freq local modes" claim on INDEPENDENT real data. PLUS our differentiator the paper lacks:
COVERAGE of the Bayesian 95% band (peak QOI = K's 5/5; + fraction of freq bins covered). Double-counting hazard reported
as a discussion caution (NOT a fabricated re-calibration number).
**Pre-registered honest outcomes.** (a) Bayes beats interp in dB esp. at HIGH band -> confirms paper's claim + adds UQ.
(b) Interp competitive/better at LOW band (smooth, well-sampled) -> honest: physics-Bayes wins specifically in the
aliasing regime, as the paper argues; not universally. Decision artifacts: out/studym_summary.json, figures/figM_*.png.


## D37 — Study A ablation: isolate the correlation knob (Andrew's fairness check on slide 6)
**Question.** Study A's V1(linear-additive iid) vs V2(log-multiplicative correlated) changes THREE things at once
(error space linear->log; iid->correlated; 1 nuisance scale -> 4, incl. separate mag/phase). So it's an A/B of two
complete discrepancy recipes, NOT a controlled ablation. Add the missing variant to attribute the effect.
**V2-iid ("log-iid").** V2's EXACT error model (multiplicative log error w+i.theta, separate sig_w/sig_th) but with the
Schneider kernel REPLACED by identity (drop len_f, r). Held-out prediction = marginal iid (NO neighbour conditioning).
Same data (seed 20260612, verbatim gen), same 2-DOF physics + priors, same NUTS (4 chains 900/900, key 0), same
interleaved split. Run V1, V2-iid, V2 together in one script for a fair internal comparison.
**Pre-registered reads.** If V2-iid CONVERGES -> the log transform (not correlation) fixes mixing, and correlation's job
is specifically the tight+calibrated interleaved BANDS (via conditioning). If V2-iid STILL FAILS -> correlation is
load-bearing for convergence too. Either is a real, honest finding. Artifacts: out/study_a_ablation.json (+fig).


### D37 RESULT — clean attribution (it REVISED the earlier over-counting story)
Same data/split/physics-priors/sampler; only the discrepancy model changes (interleaved hold-out):
| variant | R-hat | ESS | held-out coverage | band width |
|---|---|---|---|---|
| V1 linear-iid | 23.9 (FAILS) | 2 | 86%* | 6.25* |
| V2-iid log-iid (correlation OFF) | 1.001 | 2299 | 96% | 2.16 |
| V2 log + correlation | 1.002 | 1328 | 100% | 0.88 |
- **CONVERGENCE is fixed by the LOG (multiplicative) error model, NOT the correlation.** V2-iid over-counts EXACTLY
  like V1 (same iid diagonal, same data count) yet converges. So V1's non-convergence is error-SPACE misspecification
  (linear-additive likelihood on an FRF spanning orders of magnitude), not over-counting. This CORRECTS the verbal
  "over-counting → non-convergence" explanation given mid-conversation; the ablation shows over-counting is not the
  operative cause of the mixing failure.
- **The CORRELATION's specific job is the tight, calibrated held-out BANDS:** V2-iid→V2 tightens the band 2.16→0.88
  (~2.4×) and lifts coverage 96%→100% by conditioning the held-out discrepancy on neighbouring observed lines.
- Clean decomposition of Schneider's two ingredients: **T-S1 (multiplicative log error) = convergence; T-S2
  (frequency correlation) = band sharpness.** (Phase-1 still holds: model-form error is the NECESSARY trigger — with
  none, even linear-iid converges. The ablation adds: GIVEN model error, the linear error space is what makes iid choke.)
- Artifacts: out/study_a_ablation.json, figures/figAB_ablation.png, deck slide 7b. NOT a durable-science claim.
