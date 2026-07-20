# Human-review packet — Schneider 2022 + Das/Debnath 2020 × StatFEM study program
2026-06-12 · Agentic BayesX · lead: Claude Code · human: Andrew · workspace `artifacts/reports/papers_statfem_studies_20260612/`

**One-command replay:** `bash run_all.sh` · **Checker:** `python3 code/check.py` (final counts in `checker_report.json`).
**Deck:** `slides/papers_statfem_studies.pptx`. **Design doc:** `study_program.md`. **Method:** `method_ums.md`.
**Executed (no new data gathered):** Study A (discrepancy A/B) · Phase 1 (control + sweep) · Study C + **C2** (REAL panel,
incl. D19-unblocked mode-shape mapping) · Study D (complex-modal) · **Study G = THE UNIFIED METHOD** (bimodality finding +
evolving-band GIFs) · **Study H = THE CURE A/B** (vision §13.2 executed: all 3 constraints kill the bimodality, R-hat
1.006–1.014 vs 50; coverage NOT restored → identifiability and local-model-error under-coverage are SEPARATE failures) ·
**Study I = UNKNOWN FORCING** (vision §5.0 first experiment: honest double negative — ratios lose physics-pinning level
info, R-hat 61; naive 3-way fails, R-hat 128, 0% force recovery). **Narrative for Girolami/Bilionis/aerospace:**
`research_narrative.md` (3 audiences + vision-goal audit). **One-page arc:** `figures/fig_arc_summary.png`.
**Study J/K (REAL panel, vision §7 centerpiece):** UMS pointed at real mobility CONVERGES (R-hat 1.003) once the
amplitude↔damping ridge is fixed; **per-mode frequency calibration covers ALL 5/5 held-out LDV points** (vs 2/5
global) by correcting the FEA's ~15% low-mode frequency error — the program's strongest real-data result.
Meta-lesson: a 2-chain probe FALSELY rejected this (under-warmed); only the 4-chain gate revealed the 5/5.
**Study L** then shows the 5/5 bands (~4–5× wide) are at the SINGLE-REFERENCE identifiability limit: per-mode
amplitude calibration is non-identifiable (R-hat 14.8) → sharper bands need multi-reference data, not a fancier model.
**Study M (third paper, Yan et al. 2026 sensor faults):** the twin reconstructs MASKED channels and beats spatial
interpolation at high-freq local modes (3.4 vs 8.8 dB, the paper's dB metric) WITH calibrated bands the paper omits.

> **Study G headline (the ambitious ask):** a single unified generative model combining all three was built and
> self-tested (separable likelihood vs dense MVN to 1e-13; residue FRF vs direct solve to 4e-13). Two architectures:
> **UMS-full** (free latent mode shapes, Das/Debnath-style) is a DOCUMENTED NEGATIVE — latent shapes have no data at
> held-out points so they don't generalize (R-hat 364, QOI 0/10, ~1e7× error). **UMS-FEM** (physics-bound shapes from a
> differentiable B×B `eigh K̃(θ)`) **CONVERGES** after a 5-rung sampler-pathology ladder (D14–D23) — but the held-out QOI
> gate honestly catches that the converged twin is OVER-CONFIDENT under LOCAL model error (the soft-damped patch): it
> under-covers, and so does the deterministic FEM. The contribution is the METHOD + the documented "how to make NUTS work
> on dense FRFs" ladder + the honest trust-gate result (convergence ≠ trust; vision §4 confounding, §7 trust gate).

> Status honesty (AGENTS Result-Status Standard): the executed Study A clears its OWN convergence + in-distribution
> coverage gate for the V2 (Schneider) variant (**GREEN** on those gates). The OVERALL is **YELLOW** because of four
> documented non-fatal findings (V1/V3 non-convergence; extrapolation under-coverage; hyperparameter non-recovery) and
> two scope caveats (synthetic plumbing; designed studies unrun). Nothing here is reported as validated science, and no
> durable project file was edited.

---

## 0. Method summary (required gate — read first)
- **Question.** On dense FRF data from a structurally-wrong model, does Schneider's correlated complex error model — used
  AS the StatFEM output-space discrepancy — keep the posterior honest (held-out bands widen and COVER, and sharply) where
  a naive iid likelihood does not?
- **Forward model.** Coupled source/load chain. TRUTH = 3-DOF (source DOF0, load DOF1, **hidden DOF2**); INFERENCE FEM =
  2-DOF (DOF0,DOF1). The omitted 3rd DOF is the structural **model-form error**. Closed-form dynamic-stiffness inverse,
  JAX-differentiable (`code/forward.py`). Observable = accelerance `a_i/F0`, i∈{0,1}; drive-point apparent mass = 1/(a0/F0).
- **Likelihood (the three variants).**
  - **V1 iid:** `Re(data−model), Im(data−model) ~ N(0, σ_obs²)` iid over freq×point (the naive over-counting baseline).
  - **V2 Schneider (T-S1+T-S2):** `log(data)−log(model) = w + iθ`; `[w;θ] ~ N(0, blockdiag(σ_w²R, σ_θ²R))` with
    `R = r(R_ff⊗I) + (1−r)(I⊗R_zz)`, exponential kernels, **(σ_w,σ_θ,ℓ_f,r) inferred**.
  - **V3:** V1 on every 2nd frequency line (decimation).
- **Data count.** ONE synthetic dataset, ONE realization, Nf=56 log-spaced 30–200 Hz, nmp=2 points. No flight/build/test
  variability. Two held-out schemes: **interleaved** (every 4th line, in-distribution) and **contiguous high band**
  (top 25%, extrapolation).
- **Inferred:** k1,k2,k12,ζ1,ζ2 (all variants) + σ_w,σ_θ,ℓ_f,r (V2 only). **Fixed / not inferred:** masses (known),
  the hidden 3rd DOF (the model-form error, unmodelled on purpose), forcing level (cancels in M=F/a), ℓ_z (fixed 0.6).
- **Sampler.** NumPyro NUTS, 4 chains, 900 warmup / 900 samples, target_accept 0.92, init_to_median, non-centered priors.
- **Gates.** All-variable convergence (R-hat≤1.05, ESS≥200, div<2%) + held-out 95% coverage.
- **Graphical model:** `figures/fig8_graphical_model.png` (run-specific).

## 1. Results (copied from `out/study_a_summary.json`)
| Variant | split | max R-hat | min ESS | div | held-out coverage | mean band |
|---|---|---|---|---|---|---|
| **V2 Schneider** | interleaved | **1.002** | **1328** | 0 | **100%** | **0.86** |
| V1 iid | interleaved | 23.9 ✗ | 2 | 0 | 86%* | 6.33 |
| V3 decimated | interleaved | 22.8 ✗ | 2 | 0 | 93%* | 2.16 |
| V2 Schneider | extrapolation | 1.002 | 1755 | 0 | 57% (negative) | 3.21 |
| V1 iid | extrapolation | 41.1 ✗ | 2 | 0 | 68%* | 11.8 |

\* not trustworthy — these variants did not clear the convergence gate (labeled on every figure).

- **Headline:** the Schneider-correlated discrepancy (V2) is the only variant that mixes (R-hat≈1.00, ESS≫200, 0 div) and
  it gives **100% in-distribution held-out coverage with bands ~7× tighter than iid** by conditioning held-out lines on
  neighbouring residuals (T-S2). `figures/fig2_headline_coverage.png`, `fig3_convergence_coverage.png`.
- **Hyperparameters (V2):** σ_w [0.21,0.25,0.31] (inj 0.12); σ_θ [2.2,2.8,3.7] rad (inj 0.10); ℓ_f [25,46,92] Hz (inj 18);
  r [0.67,0.81,0.90] (inj 0.80). Only **r** is recovered → the discrepancy is a **model-error sponge** (it absorbs the
  2-DOF-vs-3-DOF error on top of the injected error). `fig5_hyper_recovery.png`.

## 1b. Phase 1 / Study C / Study D results (the new work)
**Phase 1 (control + sweep, `out/phase1_summary.json`).** Control truth = 2-DOF (no model-form error):
V1 iid R-hat **1.003** (vs 23.9 in Study A) → the iid non-convergence was *caused by* model-form error. V2 recovers
σ_w (median 0.128 vs injected 0.12) and ℓ_f (median 22 vs 18); σ_θ/r stay weakly identified (honest). Sweep over injected
ℓ_f ∈ {6,12,18,30,48} Hz: posterior ℓ_f tracks it (corr > 0.5), coverage 89–100% throughout. (figP1, figP2, figP3.)

**Study C (REAL DATA, `out/study_c_summary.json`).** Authoritative `H1.mat` = 25 points × 3200 freqs, |H1| spans 5 orders
of magnitude (a real FRF — the `.txt` exports were mislabeled coherence). Abaqus FEA has 45 modes < 200 Hz. Peak-picked 22
experimental modes match FEA modes with |error| mean **2.2%** (signed **+1.1%**, FEA consistently stiff), max 5.9% — the real
model-form discrepancy floor for this panel. Measured frequency-correlation length of the multiplicative log-FRF residual
(Schneider's T-S2 quantity) ≈ **2.9 Hz**. (figC1, figC2, figC3.) No NUTS calibration was run on the panel — that is the next step.

**Study D (synthetic, Das/Debnath, `out/study_d_summary.json`).** 4-DOF damped chain, near-degenerate pair at 0.75% gap.
Das/Debnath latent-complex-mode likelihood: R-hat **1.010**, ESS 280, **0 divergences**, recovers freqs (3.10/3.12/7.91 vs
3.11/3.13/8.15) and damping (ζ 0.58/0.65/1.53% vs 0.63/0.70/2.09%). Naive eigh-through likelihood: **429 divergences (18%,
fails gate)** — the `1/(λ_i−λ_j)` eigh-backward blows up at degeneracy (the logged ShockSat MAC-divergence). (figD.)

## 1c. A question for the data source (you asked me to flag this)
I proceeded with the suspended-panel data that is already in the repo. To turn Study C from a *characterization* into a
trustworthy *calibration*, a ~10-minute note from whoever ran the LDV test would help: (1) what exactly is `H1` (accel/force?
velocity/force? units?), (2) the excitation point and the 25-point measurement DOF/orientation map (the `XYcoords` header),
(3) why coherence is poor below ~8 Hz (suspension rigid-body band? low SNR?), and (4) which FEA file holds the mode SHAPES at
the measured points (for an FRF synthesis / MAC). None of this blocks the work done so far.

## 1d. Study G — THE UNIFIED METHOD (statFEM × Das/Debnath × Schneider) — see the headline box at the top
**Method** (`method_ums.md`): parametric FEM K(θ) → mode SHAPES from a differentiable B×B `eigh K̃(θ)` (physics-bound →
they generalize spatially) → complex-mode-residue FRF with latent damping (Das/Debnath) → Schneider correlated
multiplicative complex discrepancy (smooth HMC form; σ_w,σ_θ,ℓ_f,ℓ_z inferred; O(n) OU whitening) → trust gate =
held-out QOI coverage. Self-tested (1e-13 / 4e-13). ~22 parameters.

**Realistic data** (figG1): 8×5 panel-twin FRF with the REAL LDV pathologies — dense modes, antiresonance noise floor
(matched to the real panel's 2.3e-3 min/median), ±0.5 dB calibration scatter, 2% multiplicative, low-f junk. **No
Schneider field injected**: the error is genuine structural mismatch (soft+damped patch + heterogeneity + uneven cables
+ mass loading) vs a 4-quadrant + proportional-damping FEM = the adversarial test. 5/20 points held out (one in-patch);
QOI-A = peak |accelerance| 10–60 Hz, QOI-B = band RMS.

**What happened (the honest arc, numbers from `out/ums2_summary.json` + `ums_summary_FULL_ambition.json`):**
1. **UMS-full (free latent shapes):** documented NEGATIVE — latent shapes have no data at held-out points → don't
   generalize (R-hat 364, QOI 0/10, held-out predictions ~1e7× too high).
2. **The sampler-pathology ladder D14–D23** (each rung diagnosed + cured + probe-log evidence): exact Schneider
   log/wrapped-phase likelihood freezes NUTS (→ smooth residual r=(data−H)/(|H|+κ); plausibly why Schneider used
   gradient-free Subset Simulation); tiny init step; shape-gauge fix; practitioner damping prior; fix unidentified
   out-of-band params; **physics-bound shapes**.
3. **UMS-FEM (production):** CONVERGES (4-chain, R-hat ~1.0, ~0 div) — the sampler problem is solved. **But the held-out
   QOI gate honestly catches an OVER-CONFIDENT twin: it under-covers**, because the held-out points carry LOCAL
   model-form error (the soft damped patch) that a discrepancy calibrated on observed nodes cannot reach — and the
   deterministic FEM mispredicts too (in-patch ~73 vs truth ~36). Widening priors made it worse (gate-chasing rejected).
4. **GIFs** (`gif_scan_accretion.gif`, `gif_band_extension.gif`): predictive bands evolve as the scan accrues points /
   the band extends; each frame re-runs inference on that subset with its own labeled (reduced 2-chain) R-hat.

**The takeaway:** the three papers DO compose into one model, and we found exactly what it costs (the ladder) and where
it breaks (free shapes don't generalize; a smooth output discrepancy can't fix LOCAL physics error → convergence ≠
trust). This is the project's central thesis (vision §4 confounding, §7 trust gate, §5.2 the discrepancy must be
constrained) reproduced inside a unified method — a strong, honest result, not a polished success.

## 2. Findings scoreboard (ranked 1 = utter failure → 5 = smashing success)
**Executed (checker-backed):**
- ★★★★★ (5) **Phase-1 control:** V1 iid's non-convergence is *caused by model-form error* — remove the hidden DOF and
  V1 converges (R-hat 1.003 vs 23.9); the structured V2 is robust either way. Resolves Study A's biggest caveat decisively.
- ★★★★☆ (4) **Study A:** Schneider correlated discrepancy → calibrated + ~7× sharper in-distribution held-out coverage,
  clean convergence (R-hat 1.002), where iid does not mix.
- ★★★★☆ (4) **Phase-1 sponge+sweep:** with no model-form error V2 *recovers* σ_w (CI [0.11,0.15] vs injected 0.12) and ℓ_f;
  across an injected-ℓ_f sweep the posterior ℓ_f tracks it, coverage 89–100% → the correlation length is learnable.
- ★★★★☆ (4) **Study C (REAL data):** measured discrepancy floor on the suspended panel = 22 matched modes, FEA |error|
  mean 2.2% (signed +1.1%, consistently stiff), max 5.9%; measured real ℓ_co,f ≈ 2.9 Hz (Schneider's T-S2 quantity on real data).
- ★★★★☆ (4) **Study D (Das/Debnath):** latent complex modes give **0 divergences vs 429 (eigh-through)** at a 0.75%
  near-degenerate pair, *and* recover damping mode-matching-free — the logged ShockSat eigh-MAC divergence, solved.
- ★★★☆☆ (3) **Honest negative (Study A):** held-out EXTRAPOLATION into unmodelled physics fails even for converged V2 (57%).
- ★★★☆☆ (3) **Honest caveat (Study D):** higher-mode damping under-estimated ~27% (limited modes/DOF/1 dataset).

- ★★★★☆ (4) **Study H (the §13.2 A/B):** all three discrepancy constraints KILL the bimodality (R-hat 1.006–1.014, 0 div
  vs baseline 50) — and the persisting under-coverage proves identifiability and local model error are SEPARATE failures.
- ★★★☆☆ (3) **Study I (the §5.0 first experiment):** honest double negative — transmissibility cancels physics-pinning level
  information (R-hat 61); naive three-way inference fails (R-hat 128, 0% force recovery). The identifiability hole, demonstrated.

- ★★★★★ (5) **Study K (REAL data):** per-mode frequency calibration on the real panel converges (R-hat 1.007) and
  predicts ALL 5/5 never-measured-point peak mobilities within calibrated bands (vs 2/5 global), fixing a ~15% FEA
  frequency error — by better LOCATION, not vagueness. Bands wide-but-honest; one test/realization (real-data EVIDENCE).
- ★★★★☆ (4) **Study J (REAL data):** first real-panel UMS calibration; converges; honest partial coverage that Study K then lifts.
- ◐ **Study L (REAL data, honest negative):** tried to SHARPEN the K bands (~4–5× wide) with per-mode amplitude
  calibration → fails to converge (R-hat 14.8): amplitude is non-identifiable from one impact reference (the D30
  ridge, per-mode). Per-mode FREQUENCY identifiable, per-mode AMPLITUDE not → band width is a DATA limit (needs
  multi-reference), not a model limit. The concrete "where to spend the next test dollar" answer.
- ★★★★☆ (4) **Study M (REAL data, third paper — Yan et al. 2026 sensor faults):** virtual sensing of MASKED/faulty
  channels. Scored with the paper's dB main-peak metric, Bayesian physics virtual sensing beats spatial interpolation
  at high-freq LOCAL modes (3.4 vs 8.8 dB — reproduces the paper's aliasing claim on independent real data, different
  method) AND supplies a calibrated 95% band (82% bin cover, 5/5 peak) the paper's deterministic FAU lacks. Honest:
  interpolation wins on smooth low-freq modes. No new data/sampling (reuses Study K posterior).

**Designed (promise / readiness — NOT a result):**
- ★★★★☆ (4) Study E — probabilistic 7004C notch (patent endpoint) — high value, GATED on IP disclosure.
- ★★★☆☆ (3) Study B — MPL-stand damping twin from scrappy taps.  ★★★☆☆ (3) Study F — config-delta → Schneider hyperprior front-end.

## 3. Real-data readiness + an honest data audit
`figures/fig7_real_panel_audit.png` (REAL suspended-panel LDV): `coherence.txt` and `H1.txt` are **byte-identical** and both
look like **coherence** (∈[0,1] with dips), NOT an FRF magnitude → the `.txt` exports are mislabeled; the `.mat` files are
authoritative. This audit must precede any likelihood — it is exactly the GIGO step the skeptics fear, surfaced not hidden.

## 4. Honest limitations (what would change the conclusion)
- Study A is **synthetic plumbing**, not validated science (vision §12). One realization, no test/flight/build variability.
- The clean V1-vs-V2 coverage A/B is **muddied by V1's non-convergence**: the defensible claim is "V2 converges and is
  calibrated+sharp; iid is fragile", NOT "iid under-covers (as a converged result)".
- Injected error is Schneider-structured (with an anti-rig non-multiplicative term + an off-prior ℓ_f=18 vs prior≈10). A
  truly adversarial, non-multiplicative discrepancy could still break V2 — the Phase-1 grid will test this.
- M=F/a cancels forcing LEVEL but not forcing SHAPE; the unknown-stochastic-forcing problem (vision §5.0) is not yet addressed.
- Deck legibility QA: figures were lint-checked and visually QA'd; the PPTX itself was built with bounded text boxes but not
  rendered (no LibreOffice in env) — recommend a quick visual pass in PowerPoint.

## 5. Next steps (also on deck slide 12)
1. **Phase 1 (1–2 d):** diagnose iid/decimated multimodality; add a truth=2-DOF control (expect V2 to then recover
   hyperparameters → isolates sponge vs noise); ℓ_f×σ grid → calibration curve (coverage vs band width).
2. **Phase 2 (~1 wk) Study C:** ingest the panel `.mat` files, fix provenance, build Abaqus-panel CMS→FRF forward model,
   Schneider likelihood with ℓ_co,z over the real (x,y) grid, hold out spatial points, report coverage.
3. **Phase 3 (~1 wk) Study D:** port Das/Debnath latent-mode likelihood to NUTS with the degenerate-safe subspace-MAC fix
   (already specced in `notes/todo.md`); recover tray damping through the 82.9/84.3 and 337×3 clusters.
4. **Phase 4 (gated) Study E:** only after A is solid AND IP disclosure — Schneider discrepancy on the FBS interface
   admittance → probabilistic 7004C notch with held-out coverage (the patent endpoint).

## 6. Durable-file updates — APPLIED 2026-06-13 with Andrew's explicit sign-off
The original staged rows were stale (5 studies, A–G). Andrew signed off ("you can modify those logs"), so accurate
entries reflecting the FULL 13-study program (A, Phase-1, C, C2, D, G, H, I, F-mini, J, K, L, M; three papers) were
written to the durable files:
- `docs/report/project_log.md` — one row at the top of "Active / built, pending Andrew review": three papers on one
  replayable real-panel testbed; OVERALL YELLOW 76/22/0; the bimodality→cure→real-data 5/5→identifiability-limit arc
  + Study M sensor-fault virtual sensing. Status copied from the checker, never strengthened.
- `notes/runs.md` — dated run entry: commands, per-study headline numbers (copied from `out/*.json`), the five
  load-bearing lessons.
- `notes/todo.md` — program marked COMPLETE (13 studies); the open item is Andrew's call on multi-reference data
  (the Study-L "where to spend the next test dollar" answer); LATER items (4-chain finals, double-counting demo).
- `notes/lessons-learned.md` — 7 lessons (probes mislead both ways; KOH confounding as bimodality; convergence≠trust;
  exact-FRF likelihoods freeze HMC; latent shapes don't generalize; the K→L identifiability budget; the reconstruction
  double-counting trap).
- Still NOT edited (no sign-off sought/needed): `AGENTS.md`, checkers (`code/check.py`), sampler standards. The
  CURRENT-STATE block of `notes/memory.md` is maintained per its standing purpose.

## 7. File map
- `study_program.md` (design A–F) · `decisions_log.md` · `priority_deliverables.md` · `assumptions_ledger.md`
- `code/`: `forward.py` (JAX physics + Schneider R) · `run_study_a.py` (NUTS) · `plots.py` (figures+GIF) ·
  `make_deck.py` · `check.py`
- `out/`: `study_a_summary.json` · `study_a_arrays.npz` · `figures/` (8 PNG + 1 GIF) · `slides/papers_statfem_studies.pptx`
- `checker_report.json` · `runtime.json` · `manifest_sha256.txt` · `run_all.sh`
