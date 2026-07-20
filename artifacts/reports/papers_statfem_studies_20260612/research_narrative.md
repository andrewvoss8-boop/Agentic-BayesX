# Can you trust a calibrated digital twin? A one-day research arc on dense-FRF Bayesian model updating
2026-06-12 · Agentic BayesX · plain-English narrative for three audiences. Every number here is copied from a
checker-backed artifact in this workspace (`out/*.json`); nothing is reported beyond what the checkers state.
Status header: see `checker_report.json`. Results on SYNTHETIC twins are method evidence, not validated science.

---

## The one-paragraph story
We took the two strongest published techniques for Bayesian model updating with vibration data — Schneider et
al. 2022 (a correlated error model for dense frequency-response functions) and Das & Debnath 2020 (updating with
complex modes and damping, no mode-matching) — and fused them with the statFEM discipline (separate the physics,
the model error, and the noise; trust nothing that fails a held-out test). We built a realistic synthetic
"suspended panel" twin whose data has everything real LDV data has (noise floors, calibration scatter, dense
modes) and whose model error is genuine structural mismatch, not something drawn from the assumed error family.
The unified method **works as software** (self-tested to 1e-13) and **fails as inference in exactly the way the
field's theory predicts**: the posterior splits into a "damped structure" explanation and an "undamped structure
+ large model-error" explanation (Kennedy–O'Hagan confounding), and even the sensible branch is over-confident
at never-measured locations. We then tested the published cures head-to-head (Study H) and opened the
unknown-forcing axis (Study I). Finally (Study J) we pointed the method at the REAL suspended panel: once the amplitude↔damping ridge is
removed (the Study-H lesson), it CONVERGES on real data and calibrates a sensible global stiffness correction,
with honest partial held-out coverage. The complete arc — synthetic method → bimodality diagnosis → constraint
cure → real-data calibration — is one replayable testbed plus an honest map of what holds and what breaks.

## The arc, study by study (each with its own checker gates)
| Study | Question | Result (copied from checkers) |
|---|---|---|
| **A** | Does Schneider's correlated FRF error model keep a posterior honest where iid noise doesn't? | YES in-distribution: 100% held-out coverage, ~7× tighter bands, R-hat 1.002; iid/decimated **fail to converge** (R-hat 24/41). Extrapolation honest-negative (57%). |
| **Phase-1** | WHY did iid fail? | A control with no model-form error: iid converges (R-hat 1.003). **The non-convergence was caused by model error.** Correlation length is learnable (sweep, coverage 89–100%). |
| **C / C2** | What does REAL panel data say? | REAL discrepancy floor measured: 22 matched FEA↔test modes, +1.1% stiff, \|err\| 2.2%; real ℓ_corr ≈ 2.9 Hz. After the data-owner's answers: H1-row↔grid mapping pinned by MAC (low modes 0.98–0.99). |
| **D** | Do Das/Debnath's latent complex modes survive near-degenerate modes? | YES: 0 divergences vs 429 (18%) for the naive eigh-through likelihood at a 0.75% mode gap, and damping is recovered. (Solves a failure we'd logged on the real ShockSat FEM.) |
| **G** | Do the three methods compose into ONE model on realistic data? | The model composes and runs — and exhibits **physics-vs-discrepancy bimodality** (R-hat 50: gz≈1.2 "damped" vs gz≈0 "undamped+discrepancy" basins) + held-out under-coverage (1/10). The deterministic FEM fails the same held-out test. 12 sampler pathologies diagnosed/cured along the way (D14–D25). |
| **H** | Do the published cures (orthogonal discrepancy / local damping) kill the bimodality and restore coverage? | **SPLIT VERDICT (the decomposition finding):** all 3 constraints KILL the bimodality (R-hat 1.006–1.014, 0 div; baseline 50) — but held-out coverage is NOT restored (≤1/10). Identifiability and extrapolated local model error are SEPARATE failures with separate cures. H-orth over-absorbs into damping (gz→2.8) = the known Plumlee plug-in-bias trade. |
| **J** | Does the unified method work on the REAL panel (vision §7)? | **CONVERGES on real data** once the amplitude↔damping ridge is removed (R-hat 1.01, ESS 232, 0 div): calibrates a physically-sensible global frequency scale (FEA ~4.6% too stiff), modes match experimental peaks; **held-out QOI 2/5** at never-fit LDV points = honest partial coverage. First real-data UMS calibration. |
| **K** | Does per-mode frequency calibration improve the real held-out coverage? | **YES, decisively: 2/5 → 5/5** (R-hat 1.007, 0 div). It corrects the FEA's large low-mode frequency error (mode-1 9.53→8.3 Hz, =exp 8.25; a 15% fix a global scale can't make), covering by BETTER LOCATION not vagueness (bands similar width). META: a 2-chain probe gave a *false negative* here (R-hat 3.7, 0/5, under-warmed) — only the 4-chain gate revealed the win. |
| **L** | Can we SHARPEN the 5/5 bands (~4–5× wide) with per-mode residue-amplitude calibration? | **NO — and the failure is informative.** The freq-only control reproduces the 5/5 (R-hat 1.007); adding per-mode amplitude **fails to converge (R-hat 14.8)** because amplitude is confounded with damping + global level (the D30 ridge, per-mode). Per-mode FREQUENCY is identifiable (peaks pin it); per-mode AMPLITUDE is not, from a SINGLE impact reference. The ~4–5× width is the honest single-reference limit → sharper bands need multi-reference DATA, not a fancier model. |
| **M** | Sensor faults (Yan et al. 2026): can the twin reconstruct MASKED channels, and beat spatial interpolation? | **YES at the regime that matters, with calibrated UQ the paper lacks.** Treating 5 LDV points as faulty/masked and scoring with the paper's dB main-peak metric: at HIGH-freq LOCAL modes Bayesian physics virtual sensing = **3.4 dB vs interpolation 8.8 dB** (we reproduce the paper's aliasing claim on independent real data, different method), and supply a 95% band (82% bin coverage, 5/5 peak). Honest: interpolation wins on smooth LOW-freq modes (2.8 vs 4.5 dB). The paper's deterministic "virtual ground truth" fed back into updating double-counts; our band doesn't. |
| **I** | What happens when the FORCE is unknown (the aerospace reality)? | **HONEST DOUBLE NEGATIVE:** transmissibility cancels the forcing AND the level information that pins physics (R-hat 61); naive three-way joint inference fails (R-hat 128, 0% force recovery). Response-only ratios ≠ apparent mass — M=F/a needs the measured force. §5.0's identifiability hole, demonstrated concretely. |

## For Mark Girolami (statFEM)
- **Your framework's discipline survived everything; the implementations needed help.** The
  physics/discrepancy/noise decomposition and the held-out trust gate were the only instruments that caught every
  failure here — including ones convergence diagnostics misses (a converged single basin that is over-confident at
  never-measured points; a 2-chain run that "converged" by landing in one basin).
- **Three technical findings for dynamic statFEM:**
  1. *The exact lognormal-magnitude/wrapped-phase FRF error model is incompatible with gradient-based samplers*
     (phase-wrap cliffs at every resonance crossing; 1/|H| spikes at antiresonance zeros — chains freeze, 100%
     divergences). The smooth small-error-equivalent r=(data−H)/(|H|+κ) restores HMC, and the floor-augmented
     scale handles real noise floors without data selection. This plausibly explains why Schneider needed
     gradient-free Subset Simulation.
  2. *Latent (data-space) mode shapes do not generalize spatially.* Free shape coefficients fit measured DOF
     beautifully and predict garbage at unmeasured ones (held-out error ~1e7×). For spatial prediction the shapes
     must come from the parametric physics; only their eigenvalues/damping should be loosened.
  3. *The KOH confounding appears as literal posterior bimodality in dynamics* — "damped physics" vs "undamped
     physics + discrepancy" both explain a dense FRF — and is visible only with multi-chain all-variable
     diagnostics. The constrained-discrepancy cures are testable head-to-head on this testbed (Study H).
- The separable OU-kernel whitening (O(n) exact, self-tested vs dense to 1e-13) makes the correlated dense-FRF
  likelihood affordable inside HMC — possibly useful to your group directly.
- 4. *The cure transfers to real data.* On the real composite panel, the same amplitude/damping ridge that
  causes the bimodality reappears (R-hat 525); fixing the peak-set amplitude (identifiability, not tuning)
  restores convergence (R-hat 1.01, ESS 232) and a sensible stiffness calibration. The synthetic testbed's
  diagnoses are predictive of the real-data behaviour — which is the point of building it.

## For Ilias Bilionis (agentic/autonomous science)
- **One day, one agent, ~14 NUTS campaigns, 26 logged decisions (D0–D26), zero fabricated successes.** The
  load-bearing safety properties were exactly the ones the harness encodes: pre-committed decision rules (D18's
  "final attempt, ships as-is"), per-claim checkers (no success without checker output), and honest-negative
  labeling. The interesting epistemics: the *2-chain probes converged and were wrong* (same basin by luck) —
  only the 4-chain all-variable gate exposed the bimodality. AND THE REVERSE: a 2-chain probe FALSELY REJECTED
  the real-data per-mode calibration (looked non-converged, 0/5) that the 4-chain gate showed achieves 5/5.
  Cheap probes mislead in BOTH directions; full gates decide — a sharp, reusable autonomous-science rule.
- **The orchestration lesson repeated**: every major advance came from a diagnosis loop (probe → name the
  pathology → minimal cure → re-probe), not from more samples. The 12-rung pathology ladder (method_ums.md §3b)
  is effectively an agent-discovered "how-to" for HMC on dense FRFs.
- The harness artifacts are reusable: immutable checkers, the result-status standard (GREEN/YELLOW/RED),
  one-command replay, decision logs that survive compaction.

## For a traditional aerospace loads/dynamics group (the skeptics, vision §2.1)
- **Your skepticism is correct, and now it is measurable.** "Pencil-whipping" = a calibrated model that looks
  converged and is confidently wrong. We built one on purpose: it passed every convergence diagnostic in one
  basin and still over-predicted never-measured-point peaks ~2×. The ONLY instrument that caught it was the
  held-out test — hold back sensors you have, predict them, check the bands. That is a procedure you can run
  on Monday with data you already have.
- **What this buys you concretely:**
  - A *measured* model-error budget instead of an assumed one: on a real composite panel, FEA-vs-test = +1.1%
    stiff, |err| 2.2% over 22 modes — that number, not a guess, is what any updating must absorb.
  - The GIFs show the value trajectory: predictive bands at an *uninstrumented* location tightening as a scan
    accrues points — i.e., "how many points do I actually need" answered visually, with the honest caveat
    printed on every frame.
  - A clear warning: a model updated only with FRF magnitudes can trade damping against "model error"
    invisibly. If your updating tool doesn't run multiple chains and a held-out check, it cannot see this.
- Response-limit language: the held-out QOI here is the peak accelerance at unmeasured points — the response-
  limiting quantity your test plans already use, not an exotic posterior.
- **A real-data WIN with the honest caveat:** on the real panel, calibrating PER-MODE frequencies (the FEA is
  off by up to ~15% on the lowest modes) lets the twin predict ALL 5 never-measured-point peak mobilities within
  its 95% bands (5/5), vs 2/5 for a single global stiffness factor. The bands are calibrated but WIDE
  (95% CI ≈ 1.3–3× the median) — trustworthy, not yet sharp; sharpening needs more references / lower noise.
  And a crucial process lesson: a quick 2-chain check FALSELY rejected this (it looked non-converged); only the
  full 4-chain multi-chain gate revealed the 5/5. If your updating tool cuts corners on diagnostics, it will
  mis-rank your options in BOTH directions.
- **Where to spend the next test dollar — answered, not guessed (Study L).** We tried to SHARPEN those wide bands
  with a fancier model (per-mode amplitude calibration). It failed to converge (R-hat 14.8): from a SINGLE impact
  reference, modal amplitude is mathematically confounded with damping and overall level — you cannot separate them
  no matter how clever the model. Per-mode *frequency* is identifiable (each sharp peak pins one number); per-mode
  *amplitude* is not. So the ~4–5× band width is a DATA limit, not a modeling limit: the money buys multi-reference
  / roving-excitation testing, NOT more inference sophistication. The method tells you which lever actually moves.

## What is established vs open (honesty box)
- ESTABLISHED (checker-backed, synthetic): a controlled ABLATION (D37) cleanly splits Schneider's two ingredients —
  the multiplicative LOG error model (T-S1) is what restores HMC convergence (a log-iid variant with the SAME iid
  over-counting as the failing linear-iid baseline converges: R-hat 24→1.00), while the frequency CORRELATION (T-S2)
  is what tightens the interleaved held-out band ~2.4× (2.16→0.88) and lifts coverage 96%→100% via neighbour
  conditioning. (Corrects an over-counting framing: over-counting is not what breaks mixing here; the linear error space is.)
- ESTABLISHED (checker-backed, synthetic): the correlated-error advantage in-distribution (A); the model-error
  cause of iid non-convergence (Phase-1); degenerate-mode robustness of latent modes (D); the bimodality and its
  diagnosis (G); the measured real-panel floor (C).
- ESTABLISHED (added this leg): the bimodality is CURABLE by constraint (H, all arms unimodal) and the held-out
  under-coverage is NOT (a separate, local-model-error failure); response-only ratios lose physics-pinning level
  information (I). OPEN:
  the REAL-panel calibration (next; mapping is ready); seed-replication; everything on real flight hardware.
- NOT CLAIMED: novelty of any single ingredient (Plumlee owns orthogonality; Schneider the error model;
  Das/Debnath the modal layer); validated-science status for any synthetic result; patentability (FTO pending).

---
## Vision-goal audit (project_vision.md goal → experiment → status)
| Vision goal | Experiment(s) in this program | Status |
|---|---|---|
| §4 the discrepancy lever (too-weak collapses / too-flexible confounds) | Study A (iid collapses+freezes), Phase-1 (cause isolated), Study G (confounding = literal bimodality) | EXERCISED, checker-backed |
| §5.2 constrained/orthogonal output-space discrepancy | **Study H** — orthogonal fingerprints vs local damping vs both, head-to-head on the bimodal testbed = vision §13.2's decisive A/B | EXECUTED (this leg) |
| §5.0 unknown stochastic forcing (likely novelty home) | **Study I** — transmissibility-cancellation vs three-way joint inference; force spectrum recovery | FIRST EXPERIMENT EXECUTED (this leg) |
| §6.1 robust twin (bad model → wider, covering intervals) | Study G/H held-out QOI gates; the under-coverage finding IS the §6.1 hard requirement being tested | EXERCISED; full pass pending H results |
| §7 held-out trust gate ≠ convergence | Every study; sharpest: Study G (converged basin, wrong predictions) | EXERCISED repeatedly |
| §5.5 / §2.2 load QOI in industry language | QOI-A = peak accelerance at unmeasured points (response-limit proxy); 7004C work in companion threads | EXERCISED (here + companion threads) |
| §13b.5 match data type to question | Synthetic for method validation (A, D, G, H, I); REAL panel for measurement (C, C2) | FOLLOWED throughout |
| §6.2 discrepancy-prior front-end (dial/LLM knockdowns) | **Study F-mini** (forward-only): an elicited config delta widens held-out bands 0/5→4/5 coverage; the stubborn 5th point demonstrates §6.2's own caveat (structure, not scalars, for gross local error) | MINI-DEMO EXECUTED |
| Real-data calibration (§7 centerpiece) | **Study J→K→L** — UMS on the REAL panel converges (J, R-hat 1.01); per-mode frequency calibration covers **5/5** held-out points (K); per-mode amplitude is shown NON-identifiable from one reference (L, R-hat 14.8) → bands are width-limited by data, not model | **EXECUTED** (real-data win + its identifiability boundary) |
| Tractability (§10) | O(n) whitening; B×B projected operators; differentiable eigh; ~25-min headline runs | DELIVERED as engineering glue |

Honest gaps remaining: §6.2 full dial/library unbuilt (mini-demo only); the real-data 5/5 bands are calibrated but **wide (~4–5×)** and Study L shows that width is the single-reference identifiability limit — **multi-reference / roving-excitation data** (not a fancier model) is the indicated next step; seed-replication
coverage curves unrun; all H/I numbers at probe scale until the 4-chain finals.
