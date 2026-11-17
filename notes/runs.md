# Runs

## Format
- Date:
- Trial:
- Command:
- Checker result:
- Key metrics:
- Lessons:

## 2026-07-21 — MPL existing-data-only conditional ensemble (successor to Stage-0 YELLOW stop)
- Trial: with only the 13 frozen response-only records, which of B0/B1/B2 and a bounded source-supported
  model-form menu remain predictively plausible under complete response-family holdouts, the empirical
  discrepancy floor (0.7172% hard minimum), and 6 dB acoustic forcing-color stress? YELLOW ceiling by
  construction; no vault, no adaptive search.
- Command: `bash artifacts/reports/mpl_existing_data_conditional_20260720/run_all.sh`
- Checker result: **OVERALL YELLOW {GREEN:16, YELLOW:2, RED:0}, exit 0** (SHA-locked pre-science,
  RED-on-empty proven, verified unmodified; paired arithmetic independently recomputed by checker).
- Key metrics: held-out equal-family feature losses 4.5-10% vs 0.72% repeat floor (model discrepancy
  dominates; inter-model gaps <=0.4%). Plausibility set = {B2} by the 2-paired-SE rule, but NOT conditionally
  preferred (2/5 folds vs B1; coverage 0.04-0.36 vs 0.90; acoustic 6 dB reverses 2 families; tau x2 collapses
  and x4 reverses the weights; TMCMC not numerically established under the 3-seed rule — prior ensemble
  retained). B1 adds NO value over B0 (B0 beats B1 by 2SE in 3/5 folds). Negative control N1
  (half shield thickness) posts the BEST raw mean loss (6.41%) => low loss != physical truth here.
  Identifiability: 3/6 FIM combinations clear prior precision; shield_bend dominates (mean SE fraction 0.71);
  shield_mem/plate_bend below floor. 50/120 eigensolves; 126 TMCMC runs; active 6581 s.
- Lessons: (1) the known-answer gate caught a real TMCMC underdispersion (1 move/level) before any real
  interval was reported — mixing fix D6, criteria unchanged; (2) raw-parameter recovery is an identifiability
  test, not a sampler test — revise known-answer criteria to informed directions with strain-energy evidence
  (D5); (3) tempered-sampler acceptance bands must be specified per tempering level (D7); (4) validity-only
  negative controls are the cheapest defense against reading feature-loss rankings as physics.

## 2026-07-20 — MPL Stage-0 observable-validity gate for the agentic remodel + Bayes campaign
- Trial: can any legally supported observable from the 13 sequential single-response MPL CSVs discriminate
  B0, the human D43 B2 control, and four genuine model perturbations beyond measured/matching uncertainty?
  Calibrated FRF and simultaneous transmissibility were acquisition-illegal; frozen alternatives were
  repeated-source acoustic pseudo-transmissibility and response-only location features. No sampler, search,
  DEV query, or vault access occurred because this was the pre-registered first gate.
- Command: `bash artifacts/reports/mpl_agentic_remodel_bayes_20260720/run_all.sh`
- Checker result: **Stage-0 precheck OVERALL YELLOW; science YELLOW; 7 GREEN conduct/integrity gates, 0 RED;
  exit 0.** All 20 candidate/condition/run-state schema objects and figure QA are GREEN. A full science
  checker was intentionally not created after the stop.
- Key metrics: acoustic recovery 0.814 (Wilson lower 0.798 vs chance-null q95 0.25), but B0-B2
  signal/uncertainty 0.270 and qualifying-pair fraction 0.333 (required 2.0 and 0.80). Response-only features
  recover 0.947 (lower 0.937), but B0-B2 is 1.521 and pair fraction 0.600. Therefore no observable was admitted.
- Lessons: gross six-class recovery can look excellent while the actual engineering contrast remains below
  uncertainty; admission must gate on the decision pair and broad pairwise separability, not headline accuracy.
  The technically preferred next test is synchronized hammer force plus simultaneous responses, but Andrew's
  D5 decision rules out new data. The actionable successor is an existing-data-only YELLOW-ceiling ensemble,
  not a forced winner or an unmeasured-regime prediction.

## 2026-07-16/18 — MODEL-FORM PILOT (Card C): stratified agent-vs-random over GENUINE geometry/element/connectivity/mesh edits, all-exact scoring
- Trial: HQ1 = stratified amplitude-compass agent beats seeded random on held-out sub-200 P1′ (exact
  bases, ≥1×paired-fold-SE)? HQ2 = ANY genuine model-form class beats the A1 baseline ≥1×SE? 3 rounds ×
  2/class × 5 classes × 2 tracks = 60 candidates, EVERY score exact-at-θ_MAP (2 eigensolves each);
   4 NEW V-gated operators (rbe3_convert, formulation, warp_panel, joint_offset); finalists get
  per-fold amplitude refits (no cross-fold reuse). NO sampler; NO vault.
- Command: `bash artifacts/reports/shocksat_modelform_pilot_20260716/run_all.sh`
- Checker result: **OVERALL GREEN 12G/0Y/0R, exit 0 (integrity/conduct only; SHA `c26489ae771e`, RED
  on empty proven). SCIENCE: HQ1 NOT MET (falsified), HQ2 MET by all four genuine classes.**
- Key metrics: HQ2 best-vs-A1: formulation +0.0711±0.0120 (5.9×SE), connectivity +0.0641±0.0273,
  mesh +0.0635±0.0214, geometry +0.0597±0.0116 (class MEANS also 1.6–2.9×SE ⇒ not selection noise);
  best-ever edit `mr2_elem5` = zero-DOF formulation stiffening +0.1848 (property best +0.1765), the
  only finalist robust to per-fold refits (+0.1954; +0.0817±0.0296 vs A1). HQ1: best-vs-best
  −0.0077±0.0177; means +0.0028±0.0056; finalist S-test random>agent 3.1×SE. Pipeline repro vs Card A
  3.5e-11. 145 eigensolves, 58.9 h active.
- Lessons: (1) model-form freedom MOVES held-out FRF — the standing negative was an ACTION-SPACE
  limit, not physics; (2) diagnosis-guided hill-climbing backfired every time it extended a winner
  (agent round means declined) — the compass locates regions, not rankings; (3) element formulation is
  the cheapest strong lever (0 DOF/mass); (4) amplitude-trained θ overfits train drives (3rd
  confirmation); (5) V-gates caught 2 real operator defects pre-science (rigid-rotation leak of warped
  facets; hard-cutoff joint offset inverting quads); (6) liveness mech gate turned 2 duds into
  mesh-convergence evidence.

## 2026-07-02 — Plate-test REHEARSAL (synthetic end-to-end validation of the >200 Hz drumhead test design)
- Trial: does the promised normal-Z buy-down (5.4x->3.5x @ 12 plate Z-sensors, netcg pretest_design) survive the
  ACTUAL pipeline? Synthetic truth (signed shape-mixing + out-of-basis fine structure, realized log-amp sd 0.86),
  simulated noisy plate data, JOINT NUTS (theta 9 + shape coeffs 4x12 + sigma_y + sigma_w2), delivered band vs known
  truth. Arms: 1 / 12 / 20 sensors, 12+1.5-in jitter, truth-sigma {0.4,1.6}; 8 seeds main; pre-registered S1-S6;
  checker SHA-locked BEFORE science.
- Command: `bash artifacts/reports/plate_test_rehearsal_20260701/run_all.sh`
- Checker result: **OVERALL RED (28G/3Y/1R) — the RED is S1 = the PRE-REGISTERED claim-falsified tier** (buy-down
  claim blocked), NOT a pipeline failure. S2 coverage GREEN (0.998); S4 integrity GREEN; S3 35/36 NUTS converged
  (A0_s6 pathological, excluded+reported); S5/S6 YELLOW.
- Key metrics: rehearsed medians 1-sensor 6.17x / 12-sensor 6.20x / 20-sensor 6.20x (NO buy-down; analytic promised
  3.5x). Mechanism (post-hoc ablation L0-L7): analytic recipe reproduces (L1 3.05x) but FROZE THETA — carrying the
  +/-4% theta posterior re-mixes the near-degenerate 246-258 Hz drumhead cluster (3.05->4.93x, L2); signed-mixture
  heavy tails add the rest (->5.5x). Perfect 4-target test still ~5.1x (L6); **pinning ALL 12 drumhead-band modes
  recovers 2.81x (L7, oracle bound) = the REVISED test scope.** As-designed test still buys: target amp posterior
  0.80->0.58 sd (mean within 0.08 of truth) = pooling assumption becomes checkable. Truth-sd 1.6 arm: band ~104x
  but coverage 1.0 — degrades by widening, never lying.
- Lessons: (1) analytic pre-test curves computed OUTSIDE the twin's own uncertainty carriage overpromise — rehearse
  through the full pipeline before any hardware ask; (2) near-degenerate cluster eigenvector rotation under theta
  uncertainty is a first-class width source no sensor count fixes — test scope must cover the whole cluster;
  (3) two integrity catches: D8 prior/tier inconsistency fixed pre-campaign (prior-only band must reproduce the
  no-data 5.4-5.8x), D9 uniform NUTS retune policy adopted before headline arms landed; (4) encoding the negative
  answer as checker RED makes falsification unmissable — but distinguish it loudly from pipeline-failure RED.

## 2026-06-23 — ShockSat sequential statFEM PSD-envelope pilot
- Trial: bounded reduced-order analogue of Kavrakov-style sequential statFEM on clean ShockSat modal-hammer
  time histories from Test01/Test02/Test04/Test06. Used the inherited seed-0 90% observed / 10% held-out
  sensor split and scored only the locked PSD-envelope QOI: 97.5% response-PSD smoothline GRMS ratio versus
  FEM+6 dB plus energy-weighted positive dB exceedance.
- Command: `bash artifacts/reports/shocksat_sequential_statfem_20260623/run_all.sh`
- Checker result: **OVERALL YELLOW green=18 yellow=3 red=0**. No red gates. Yellows are: no PSD-envelope
  improvement, fixed filter hyperparameters rather than full posterior/hyperparameter inference, and a large
  residual/discrepancy band.
- Key metrics:
  - Best sequential variant: `stiffness_residual`, median GRMS ratio 2.07 versus FEM+6 dB, clean-win rate 18.8%.
  - `nominal_residual`: median GRMS ratio 2.15, clean-win rate 6.2%.
  - Small stiffness-subset NUTS/HMC calibration converged: max R-hat 1.002, min ESS 1157, divergences 0.
  - Worst training residual 97.5% PSD multiplier: 22.0 dB, so model discrepancy is doing substantial work.
  - L5/modal-frequency PSD-envelope probe reused from `shocksat_psd_envelope_twin_20260623/out/probe_seed00.json`.
- Artifacts: `artifacts/reports/shocksat_sequential_statfem_20260623/packet.md`,
  `checker_report.json`, `out/results.json`, `runtime.json`, and `figures/*.png`.
- Lessons: for the current ShockSat PSD-envelope decision metric, the reduced sequential filter did not beat
  FEM+6 dB. The useful result is an honest negative: time-domain sequential assimilation alone is not a green
  PSD-envelope lever while residual bands remain broad and filter/process hyperparameters are fixed.

## 2026-06-23 — New ShockSat-applicability paper review and runner prompts
- Trial: reviewed three newly pulled PDFs against the current ShockSat project vision and data state: Lu et al. 2026
  multi-level wing digital twin; Kavrakov et al. 2026 sequential statFEM solid dynamics; Kashyap/Nayek latent-force +
  BNN probabilistic digital twin. Created a checked review packet plus three runner prompts.
- Command: `bash artifacts/reports/shocksat_new_papers_review_20260623/run_all.sh`
- Checker result: **OVERALL YELLOW green=41 yellow=1 red=0**. The only yellow is intentional/exploratory:
  runner prompts are hypotheses only; no ShockSat metric improvement is claimed until a future checker-backed run.
- Key metrics:
  - Sequential statFEM solid dynamics: HIGH applicability; best first runner if the goal is direct statFEM continuity
    and time-domain assimilation on clean modal-hammer data.
  - Latent-force + BNN digital twin: MODERATE-HIGH applicability; useful for model-form-error/damping residuals, but
    offline, moderate-scale, and vulnerable to held-out-sensor leakage/extrapolation.
  - Multi-level wing digital twin: MODERATE-LOW applicability; useful as deployable fast-ROM/submodel architecture,
    not a Bayesian/statFEM method and not physically validated for ShockSat stress without measured local truth.
- Artifacts: `artifacts/reports/shocksat_new_papers_review_20260623/paper_applicability_review.md`,
  `bibliography.md`, `checker_report.json`, and `runner_prompts/*.md`.
- Lessons: separate "interesting architecture" from "method that attacks the current ShockSat statistical bottleneck";
  require held-out ShockSat scores before any paper-inspired method is called an improvement.

## 2026-06-13 Schneider × Das/Debnath × Yan(2026) × StatFEM study program — unified method, real-panel calibration, sensor-fault virtual sensing
- Trial: integrate three papers on one replayable testbed (synthetic "suspended-panel" twin + the REAL suspended-panel
  LDV mobility data, 25 pts × 3200 freqs, single impact reference). 13 executed studies A, Phase-1, C, C2, D, G, H, I,
  F-mini, J, K, L, M. NUTS (NumPyro), 4-chain all-variable gate (R-hat≤1.05, ESS≥200, div<2%) + held-out QOI coverage.
- Command: `bash run_all.sh` (probe scale; headline Study G ~25 min at production scale). Two venvs: `.venv_nuts`
  (jax/numpyro), `.venv_fem_phase1` (matplotlib/scipy), system python3 (python-pptx).
- Checker: **OVERALL YELLOW green=76 yellow=22 red=0** (`code/check.py`). No reds; yellows are documented non-fatal
  findings + scope caveats. Nothing reported above its own gate.
- Key metrics (copied from `out/*.json`, not strengthened):
  - A (synthetic): V2 Schneider interleaved R-hat 1.002, ESS 1328, 100% held-out coverage, mean band 0.86; iid
    R-hat 23.9 (fails); extrapolation 57% = honest negative.
  - Phase-1: iid control (no model error) R-hat 1.003 → the iid non-convergence was CAUSED by model-form error.
  - C/C2 (REAL): 22 matched FEA↔test modes, +1.1% stiff, |err| 2.2%, real ℓ_co,f ≈ 2.9 Hz; MAC mapping (low modes 0.98-0.99).
  - D (synthetic): latent complex modes R-hat 1.010, 0 div vs 429 div (eigh-through) at 0.75% mode gap; damping recovered.
  - G (THE UNIFIED METHOD): self-tests 1e-13 (separable vs dense MVN) / 4e-13 (residue vs direct). UMS-FEM converges
    after a 12-rung HMC ladder but shows BIMODALITY R-hat 50 (3 chains gz≈1.2 "damped", 1 chain gz≈0 "undamped+discrepancy")
    = Kennedy-O'Hagan confounding as literal posterior multimodality; held-out QOI under-covers (deterministic FEM fails same).
  - H (cure A/B): H_orth/H_local/H_both all kill the bimodality (R-hat 1.006-1.014) but coverage NOT restored (≤1/10)
    → identifiability and local-model-error under-coverage are SEPARATE failures with separate cures.
  - I (unknown forcing): I_ratio R-hat 61 (transmissibility loses level info); I_joint R-hat 128, 0% force recovery. Honest double negative.
  - J (REAL): converges R-hat 1.003, ESS 1124, 0 div once amplitude↔damping ridge fixed (gamp FIXED); held-out QOI 2/5; global freq scale 0.956.
  - K (REAL, strongest): per-mode freq R-hat 1.007, ESS 258, 0 div, held-out QOI **5/5** (global 2/5); calibrated freqs
    [8.3,10.5,22.4,...] match exp peaks [8.25,10.5,22.12,...]; covers by better LOCATION (medians 1.0-2.0× truth vs global 2.4-3.0×).
  - L (REAL): freq-only control reproduces K (R-hat 1.007, 5/5); +per-mode amplitude FAILS (R-hat 14.8) → ~4-5× band
    width is a single-reference identifiability limit (per-mode FREQUENCY identifiable, per-mode AMPLITUDE not).
  - M (REAL, Yan 2026 sensor faults, no MCMC — reuses K posterior): masked-channel reconstruction, paper's dB main-peak
    metric. HIGH band (local modes) Bayes 3.4 dB vs interpolation 8.8 dB; LOW band interp 2.8 vs Bayes 4.5 dB; Bayes
    82% band-bin coverage, 5/5 peak. Reproduces the paper's aliasing claim with a different method + adds calibrated UQ.
- Lessons (the load-bearing ones): (1) Cheap multi-chain PROBES mislead in BOTH directions — G's 2-chain "converged
  and was wrong" (false positive), K's 2-chain "failed and was wrong" (false negative). ONLY the 4-chain all-variable
  gate decides. (2) Physics-vs-discrepancy confounding shows up in dynamics as posterior BIMODALITY, invisible to a
  single chain. (3) Exact log/wrapped-phase FRF likelihoods freeze HMC; the smooth r=(data−H)/(|H|+κ) form is the price
  of NUTS on dense FRFs (likely why Schneider used gradient-free SuS). (4) Held-out coverage ≠ convergence: a converged
  single basin can be confidently wrong; the held-out gate is the only instrument that catches it. (5) Latent (data-space)
  mode shapes don't generalize spatially — for held-out prediction, shapes must come from the parametric physics.

## 2026-06-12 Buffet dome secondary-structure twin — full fine-region build + QOI + CI + D14 correction
- Trial: 58,662-DOF representative LV fine region (barrel+ring+dome+tray-on-6-struts+8kg avionics
  CONM2 +30kg COPV on mounts); max-q Corcos buffet (D12 buffet-only); 4 QOI groups to 400 Hz; BC
  bracket A/B; CI by prior-propagation MC (no sampler); structural variants.
- Command: `bash run_all.sh` (foundations) + `scripts/run_d14_finalize.sh` (heavy, detached).
- Checker: **OVERALL GREEN 24/0/0** — S1 forcing math, S2 element, S3 model+Donnell, S4 modes+QOI
  (both BCs), S5 CI (both BCs), S6 coupling trust-test, S7 mesh convergence. Active runtime ~4.6 hr
  (CI + eigensolves dominate); variant re-solve adds ~2.5 hr detached.
- S6 COUPLING TRUST-TEST: modal superposition (820 Hz truncation, what all QOIs use) vs DIRECT full
  58k-system complex solve = worst 0.69% on interface QOIs (driven point loads, masked to non-negligible
  response). 2x-band truncation validated. S7 MESH CONV: refined mesh (Nth 240->300) QOI ratios 0.97-1.06.
- S8 RESPONSE-LIMIT PROXY (D15, vision 2.2): avionics accel promoted to a response-limit proxy for the
  tray punch via the random-vib cross-spectrum. Coherence 0.9999 at the 55 Hz controlling (suspension)
  mode; proxy gain alpha=15.1 N/(m/s^2) INVARIANT to damping (0.06% over eta 0.005-0.05) and EXACTLY to
  forcing level -> a_limit=F_allow/alpha is a STRUCTURAL CONSTANT robust to the uncertainties that give
  the load its 5x CI (the response-limit analogue of the robust-twin claim). CG-accel gain = 1.17x
  assembly mass = 7004C effective-mass relation through a sensor. Valid where coherence>0.8 (32-300 Hz,
  77% of punch energy); decouples at the avionics-on-tray local mode (honest band-specificity).
- REFINEMENT: D14-consistent variant re-solve shows substructures are LARGELY (not perfectly) decoupled
  through the shared dome — ~15% cross-talk (soft tray joints nudge COPV punch x1.18); "decoupled"
  wording corrected to "largely decoupled" in packet + narrative. Active compute now ~7.1 hr.
- Key results (D14 model): BC-A tray punch 45.4 N, COPV punch 37.6 N, COPV per-mount resultant
  40.8 N, avionics 3.53 m/s²(z) ≈0.3 g; BC-B 6–10% lower (= boundary-impedance uncertainty, so the
  first-ring-frame cut is far enough). CI tray punch 5/50/95 = 18/40/87 N (damping+buffet priors).
  Variant sensitivity: substructures decoupled through the dome (mount/joint change moves only its
  own hardware); DOME GAUGE moves every QOI 40–75% (= the quantitative case for resolving the local
  primary host to 400 Hz, not a stick).
- LESSON (logged, important): "it's just a spurious ~0 Hz mode" was WRONG. The image-QA gate caught a
  free COPV spin (two translational mounts); adding physical rotational mount stiffness was
  QOI-invisible for tray/strut/avionics (≤2%) but the COPV net punch dropped 15% AND the per-mount
  in-plane shear ROUGHLY DOUBLED (mounts now carry moment) — the design-driving channel, which the
  free-spin model under-predicted. ALWAYS check the QOI delta of a "harmless" model change; record the
  wrong prediction (replaced the optimistic verdict string with a data-driven one).
- LESSON (process): a resume guard (`[ -f qoi_bcB_summary.json ]`) silently skipped re-running BC-B
  QOI under the corrected model → 0.0% deltas exposed it. Guards must key on the MODEL VERSION, not
  just file existence, when the model changes underneath. Also: editing a running bash pipeline shifts
  byte offsets and can corrupt it — kill+relaunch instead.
- LESSON (forcing physics): Corcos convective joint acceptance is NON-monotone in coherence length at
  high f (aerodynamic coincidence); pure-decay lateral + low-f streamwise are monotone. Production mesh
  rule: ≥6 nodes per lateral coherence length at f_max (tighter than the structural-wavelength rule).

## 2026-06-12 Buffet+acoustic dome secondary-structure twin — foundations (S1 forcing math, S2 element)
- Trial: Representative Terran-R/F9-class dome secondary-structure vibe study. This run = the two
  pre-build VALIDATIONS only (no vehicle FEM, no QOI yet).
- Command: `bash run_all.sh` (workspace `artifacts/reports/buffet_dome_secondary_20260612/`), ~81 s active.
- Checker result: GREEN 13/0/0 (`check.py`). Stage-scoped: certifies forcing math + the added element, NOT a model.
- Key metrics: S1 — Corcos separable fast path == full matrix to 4e-16; response PSD peaks land on analytic
  SS-plate fn (worst 0.4%); integrated RMS vs white-near-resonance closed form 0.99; joint-acceptance grid
  error 2.2% at 400 Hz with ~7 nodes per lateral coherence length → PRODUCTION MESH RULE: ≥6 nodes/Lcoh at
  f_max. S2 — 3D Euler-Bernoulli beam + axial bar: 6 rigid-body modes; worst 0.04% vs analytic
  bending/axial/torsion/simply-supported; rigid-body force residual ~1e-18.
- Lessons: (1) peak-placement checks must use NEAREST-LOCAL-MAX off the mode node lines, not a windowed
  global max (a convectively-loaded even-mode neighbor can dominate a window). (2) Convective Corcos joint
  acceptance is NON-monotone in coherence length at high f (aerodynamic coincidence) — monotonicity only
  holds for the pure-decay lateral kernel and low-f streamwise; encode that as physics, not a bug. (3) Mesh
  the pressure-loaded surfaces to ≥6 nodes per lateral coherence length at f_max, the binding sampling
  constraint (tighter than the structural-wavelength rule at 400 Hz).

## 2026-06-10 ShockSat × tray coupled QOI — method × coupling comparison (propagation, no sampler)
- Trial: HYPOTHETICAL payload-tray-on-ShockSat methods demo (D38 scope): net CG interface load (Fx,Fy,Fz) under {time-history, modal-SRS, PSD/Miles} × {uncoupled, coupled LM-FBS}, propagating theta_S NUTS posterior × tray prior × mount-CBUSH prior × 8 input seeds; mount identifiability gate + response-limit proxy (vision §2.2/D7). NO sampler run (propagation only, D1).
  - Command: `bash artifacts/reports/shocksat_tray_coupled_qoi_20260610/run_all.sh`
  - Checker result (green/yellow/red): overall GREEN = 22 green / 0 yellow / 0 red (`checker_report.json`); verify.py 15/15 green (tray rebuild vs FIM freqs 2.6e-11; RBM-mass-line unit check 9e-5; FBS algebra exact 8.8e-10; Newmark vs FBS 0.6%; exact Woodbury damped apparent mass 4e-6 incl. peaks; 7004C TDOF anchors; SRS filter; input grms/flatness). 13 read-only upstream inputs SHA-pinned, unchanged.
  - Key metrics (all HYPOTHETICAL-labeled): QOI MOUNT-DOMINATED — mount prior ≈ 100% of joint QOI variance, theta_S <1%, theta_T ≤10%, seeds ~7-10%; QOI spans ×5-10 over the mount prior and is NON-monotonic in k (peaks ~1e7 N/m, saturates >1e8 at the fixed-feet-tray answer). Force-limiting over-test factor unc/cpl median 1.27/1.31/1.12 (x/y/z), p97.5 up to 2.2; notch ×1.3 @ 114 Hz (z, nominal). Method vs TH-unc: SRS informed-Q ×0.95-0.98 (machinery ~unbiased), Q=10 ×0.73-0.97, Q=25 ×1.12-1.50, Q=50 ×1.55-2.07 (Q assumption dominates); Miles 3σ informed ×0.74-0.75 = the pre-stated 3σ-vs-~4σ peak-factor shortfall. Identifiability: coupled 87 Hz rocking mode stores 90% SE in the mount; dlnf/dlnk peak 0.449 ≈ 10× the predecessor 4.6% σ_f floor → mount identifiable from a mounted-config modal test (unlike bare-ShockSat joints); ×0.5/×2 mount moves QOI −29…+31%. Proxy: tray-center accel per axis ρ≈1.000, α≈m_tray=3.16 kg (cv 0.3%) — band-specific (tray elastic modes 457+ Hz above the 250 Hz input band). Damping grid moves F_z 362-698 N (≈ method-sized); ShockSat damping ×0.5/×2 <1%. active_runtime_s ≈ 1587.
  - Lessons: (1) diagonal modal damping was NOT acceptable for a peak-force QOI — it missed peak apparent mass by 31% on a near-degenerate mode pair; the rank-6-dashpot Woodbury exact form costs almost nothing (D8); (2) computing the interface force as the net inertial sum (Rᵀ M ü) sidesteps spring/damper force bookkeeping AND is literally the net-CG-load definition — it made the FBS/Newmark cross-checks exact; (3) a calibrated primary buys ~nothing for a coupled QOI when the joint/mount is unconstrained — identifiability findings propagate to QOIs through the interface; (4) eigh(M,K) Cholesky fails on mixed-conditioning coupled assemblies (1e9 springs vs ~7 suspension stiffness) — spectral shift K+σM recovers it exactly; (5) writing the expected Miles peak-factor shortfall into the quantity contract BEFORE running turned a would-be surprise into a confirmation.
- Lead-as-runner; decisions `.../decisions_log.md` D1–D9; packet `.../packet.md`; sign-off pending: D2 input spec, D3 placement, D4 mount values, D7 proxy promotion.

## 2026-06-11 Overnight: synthetic mounted-survey NUTS calibration (VOI experiment) — honest negative
- Trial: D10 value-of-information experiment in the same workspace: SYNTHETIC mounted-config modal survey (27 coupled freqs ≤240 Hz, 0.3% noise, truth = full coupled model with 6×6 OFF-DIAGONAL mount the diagonal inference model can't represent + θ_S posterior-draw-vs-median gap = structured discrepancy; truth SHA-locked, sampler blind) → NUTS (pinned .venv_nuts) on 12 latents → posterior QOI propagation.
  - Command: stages 5–7 of `bash artifacts/reports/shocksat_tray_coupled_qoi_20260610/run_all.sh`
  - Checker result: workspace overall now YELLOW = 27 green / 2 yellow / 0 red; yellows = `convergence_mount_nuts` (base R-hat 5.03, ESS 2, 0 div; auto-remedy 2000+2000 d9 WORSE at 9.74) + `voi_truth_coverage` (Fx truth missed before AND after). Reduced coupled ROM gate green (off-anchor 3.6e-4). Nothing labeled converged.
  - Key metrics: chains agree in DATA space (median cross-chain predicted-freq spread 0.06%, rms residual 3.3–3.5%) but not parameter space = genuine multimodality; σ_f posterior ≈3.7% ≫ 0.3% injected noise (structured discrepancy measured); FIM at the realized floor: 2/6 mount stiffness COMBINATIONS identifiable (k_ry-rocking eig 97, k_tz bounce eig 15; k_rz marginal 0.74 vs prior 0.76) vs 5/6 at the noise-only floor; VOI width ratios after/before 0.93/0.38/0.91 (YELLOW, not credible intervals). active ≈ 9.8 ks (NUTS 7.5 ks).
  - Lessons: (1) "identifiable overall" ≠ "identifiable per-axis" — the strain-energy gate certifies signal-above-floor for a GROUP; the FIM eigen-decomposition is what predicts the parameter-space split (use both, before sampling); (2) auto-remedy with MORE exploration made R-hat WORSE — on multimodal posteriors extra compute finds more modes; budget escalation is not a convergence fix; (3) model-form discrepancy is again the binding constraint (now proven in a controlled synthetic: 2/6 vs 5/6 combos at 3.7% vs 0.3% floors); (4) the QOI-level bands can narrow even under parameter multimodality — but must stay YELLOW; (5) refined pre-test lever: symmetry-breaking observables (shapes/FRF/force gauges), not more frequencies.
- Decisions D10–D11; packet §10; diagnosis `out/multimodality_diagnosis.json`; figure `figures/fig_voi.png` (NOT-CONVERGED flag on-figure).
- POOLED-MOUNT ARM (2026-06-12, D15–D17, Andrew's "6→3" suggestion): pooled FIM + NUTS ladder 6→3→2 params = R-hat 5.03→1.52→1.24 (FIM-predicted order); even 2 params fail STRUCTURALLY — stiff-side saturation (likelihood flat above ~×5 nominal; 2000+2000 d9 remedy WORSE at 2.22, one chain stuck in the tail t_all 2.6–38.8) + t_all↔r_all rocking ridge (corr −0.74; mount↔tray confounding hypothesis tested and REJECTED, corr ≤0.17). Frequencies deliver r_all≈1 + a LOWER bound on t_all only. Local prior-whitened joint FIM said p2 was fine → local-vs-global lesson (D12 gate's profile/posterior companion vindicated). Artifacts: pooled_fim.json, pooled_posterior.json, pooled_diagnosis.json; packet §10a; checker 32g/3y/0r.

## 2026-06-10 ShockSat FEM modal twin — Bayesian calibration (NUTS), held-out designs
- Trial: from-scratch Python assembly of NASA ShockSat FEM_20211021 (~406k DOF) + real free-free impact-hammer modes (.ash); NumPyro NUTS calibration of 9 part-group stiffness scales + sigma_f on log-frequencies; 3 held-out designs.
  - Command: `bash artifacts/reports/shocksat_fem_modal_twin_20260609/run_all.sh ; python3 .../check.py`
  - Checker result (green/yellow/red, D35): overall YELLOW = 15 green / 2 yellow / 0 red (`checker_report.json`); check.py exits 0. The 2 yellows = `convergence_band` + `convergence_lomo` — DOCUMENTED honest not-converged findings (multimodal under-identified posteriors), never faked/green. `convergence_full` = GREEN (R-hat 1.022, ESS 232, 0 div). inputs 0/50 changed.
  - Key metrics: FULL 18-mode posterior CONVERGES; only ~4/9 theta groups informed (bottom_box, top_box, plates, cross_beam); joints + 4 weld/contact groups stay at prior = NOT identifiable from modes ≤222 Hz (cross-confirms the 2026-06-09 FIM result). sigma_f ≈4.6% ≫ 0.3-0.9% replicate floor = model/element discrepancy. Held-out predictive coverage: band 10/12, LOMO 18/18 (frequencies predictable even though parameters aren't). Band remedy depth-10/2000+2000 cut worst R-hat 1.92→1.08 but still fails gate. Sensitivity: MAC pseudo-likelihood arm gets 12/12 coverage but 82 divergences + R-hat 2.97 (near-degenerate eigenvector-gradient hazard); band≤150Hz arm WORSE (R-hat 4.25). Reduced≈full at posterior theta to 0.068%. active_runtime_s ≈ 38099 (LOMO 4-parallel), wall 63791.
  - Lessons: held-out FREQUENCY prediction can be well-calibrated while the PARAMETER posterior is multimodal/under-identified — wide-but-covering bands are a feature of under-identification, not a clean fit; the held-out + convergence gates together are what expose it. 0 divergences + high R-hat = multimodality (mode-hopping), not curvature — diagnose as a DESIGN finding. ps-resolved interpreter ≠ launched interpreter (a venv shows its base python in ps); verify via env + version, not ps path (D24). Hash-integrity gates must compare apples-to-apples schemas (D30). Lead-as-runner: independence = NASA published numbers + FEMAP re-solve + checker.
- Lead-as-runner; full decision trail in `.../decisions_log.md` D1–D30; packet `.../packet.md`.

## 2026-06-09 Pre-test FIM identifiability + experiment design (Opus hexapod tray FEM)
- Trial: lead-executed pre-test Fisher-information + profile-likelihood identifiability study on the Opus Phase-1 JAX hexapod tray FEM (NOT a posterior/NUTS run). Answers "how many params can the scrappy modal test support" with a number + plots, plus where-to-measure/where-to-hit.
  - Command: `bash artifacts/reports/fim_identifiability_opus_20260609/run_all.sh`
  - Checker result: PASS 15/15 (`artifacts/reports/fim_identifiability_opus_20260609/checker_report.json`, `overall_pass=true`).
  - Key metrics: parametric assembly reproduces JAX nominal modes to max |df|=4.07e-4 Hz; analytic eigen-sensitivities match central FD exactly; 40-mode reduced basis error to lowest 8 modes = 0.0 Hz. FIM spectrum (5 params) = 3 large eigenvalues then ~9-order cliff in all 3 designs (freq-only, 1-sensor, 2-sensor). Identifiable = 3 structural params (strut_EA marg sd ~0.011, tray_E ~0.020-0.030, strut_EI ~0.020); joint_axial & joint_lateral stay at prior sd 0.30 (joint_lateral freq-sensitivity exactly 0). Band-conditional count: 1 (≤181 Hz) → 2 (≤371 Hz) → 3 (≤570 Hz, needs the 542/570 Hz strut-bending tray-flex modes; strut_EI sens = 283 Hz/unit at 570 Hz). Count robust to ×0.5-4 freq noise. Profile likelihood: tray_E/strut_EA/strut_EI sharp (sd≈FIM marginal), both joints flat across ±30% → globally unidentifiable. QOI (payload transmissibility, nominal 24.8, ζ=0.02): ∂QOI/∂θ on strut_EA/tray_E/strut_EI, fraction in sloppy subspace = 0.0. Experiment design: best 1-accel z at (x63,y28 mm), worst at edge, log-det FIM spread 20.88; best tap = corner (−150,−150 mm) excites all 8 modes >20% peak. active_runtime_s ≈ 2.83.
  - Lessons: (1) joints are blind spots of MODAL data (near-rigid + moment-free), not a sensor-count problem — 1-sensor vs 2-sensor give the same headline; (2) the 3rd identifiable parameter is band-gated (needs ~570 Hz) — a concrete test-plan requirement; (3) local FIM and global profile agree here, so the cliff is structural not a linearization artifact; (4) discrepancy NOT included → numbers are an upper bound; held-out coverage stays the referee. Numerical: solve M v = mu K v (K p.d.) for singular M; optimize profiles in log-θ to keep K p.d.; reduced basis to keep the profile fast.

## 2026-06-09 ShockSat StatFEM runner continuation
- Trial: resume the interrupted full Test07 impact-hammer archive download, verify the archive, regenerate the ShockSat packet, and upgrade the hammer FRF layer from a single-hit diagnostic to a four-hit averaged diagnostic.
  - Command: `bash artifacts/reports/shocksat_statfem_runner_20260609/run_all.sh`
  - Checker result: pass. `artifacts/reports/shocksat_statfem_runner_20260609/checker_report.json` reports `overall_pass = true` with known blockers preserved.
  - Key metrics: `Test07_ImpactHammer_990x.zip` fetched at 593,859,074 bytes with SHA256 `df104a731f98a8b5429bfd24e4a0bff07b8fce0a567ac8ac02d6922b39c320b6`; ZIP integrity check reported no bad member; archive contains four MAT hammer hits. Multi-hit H1 diagnostic used force channel 116 and response channels 1, 50, and 87 at 250,000 samples/s. Median coherence from 100-10,000 Hz remained low: ch1 = 0.0722, ch50 = 0.0706, ch87 = 0.0681; fraction with coherence >= 0.8 was 0.0 for all three selected channels.
  - Artifacts: updated `shocksat_statfem_packet.md`, `source_manifest.json`, `hammer_frf_subset_manifest.json`, `hammer_frf_alignment.md`, `hammer_frf_hit_summary.csv`, `figures/hammer_frf_accelerance_subset.png`, and `figures/hammer_frf_coherence_subset.png`.
  - Lessons: recovering repeated hammer hits improved provenance but did not make the FRF likelihood-ready. The TestLog has six Test07 rows while the archive exposes four MAT files, so source-location metadata must be reconciled before assuming a one-to-one test-hit map. The next engineering action is a source/response grid mapping audit between Test07 impact points, 9900001-style response grids, and NASA SOL 111 grids 11101X/11110Y.

## 2026-06-08 Vibrationdata conical-shell StatFEM ladder
- Trial: scoped source audit, FEM-vs-published-test comparison, and StatFEM launch definition for the Vibrationdata conical shell only.
  - Command: `bash scripts/run_conical_shell_statfem_ladder.sh`
  - Checker result: pass. Internal `checker_report.json` and external `checker_report_external.json` both report `pass = true`.
  - Key metrics: `conical_shell.pdf` fetched; `conical_shell3.nas` fetched with curl-like user agent; browser-like user agent returned HTTP 406 and is recorded. Parsed source deck: `SOL SEMODES`, 961 GRID nodes, 872 CQUADR, 40 CTRIAR, PSHELL thickness 0.1 inch, no SPC/SPC1 constraints. Published measured modes: 97.6, 278, 429, 529 Hz. Published preliminary FEA modes: 97.6, 274, missing, 523 Hz. FEA-vs-measured errors for available modes: 0.00%, -1.44%, -1.13%.
  - Artifacts: `artifacts/reports/conical_shell_statfem_ladder_20260608/conical_shell_packet.md`, source manifest, Nastran summary, assumptions ledger, quantity contracts, digital-twin launch definition, checker reports, source cache, and figures.
  - Lessons: this is a good public conical-shell sandbox, but not yet an active StatFEM digital twin. The source report says the preliminary FEM material properties were adjusted to match the fundamental, so mode-1 agreement is provenance rather than independent validation. No local shell solver was run; raw FRF ordinates were not extracted.
- Trial update: continued with human Femap/Nastran solve ingestion, coarse FRF peak digitization, modal-only StatFEM v1, and first FRF/QOI layer.
  - Command: `bash scripts/run_conical_shell_statfem_ladder.sh`
  - Checker result: pass. External checker reports `modal_statfem_active = true`, `human_nastran_modes_ingested = true`, `frf_qoi_present_and_labeled = true`, and `statfem_not_overclaimed = true`.
  - Key metrics: human Femap/Nastran modes 1-6 are near-zero free-free rigid-body modes; flexible pair means are 97.6373, 274.0179, 524.2939, 728.9819, 764.5755, 847.8621, 939.8805 Hz. Local solve vs measured errors for matched published modes: +0.04%, -1.43%, unmatched 429 Hz, -0.89%. Modal-only StatFEM v1 uses exact grid quadrature, not NUTS/HMC; posterior stiffness scale median = 1.0130 with 90% interval [0.9663, 1.0609]. Held-out mode 4 observed 529.0 Hz and predictive 90% interval [497.6, 557.8] Hz covers it. First FRF/QOI layer reports coarse visual aft peak accelerance near mode 1 = 17.5 G/LBF with approximate 90% interval [12.56, 22.44] G/LBF.
  - Artifacts added: `human_nastran_solution.json`, `local_solve_comparison.json`, `frf_digitized_features.json`, `modal_statfem_v1_results.json`, `frf_qoi_summary.json`, figures for local solve comparison, modal posterior/holdout, digitized FRF features, and QOI.
  - Lessons: screenshots are valid provenance for frequencies and qualitative mode family, but not machine-readable mode shapes for MAC or mode-shape updating. The 429 Hz measured feature remains an explicit model-class warning rather than something to force-fit with a scalar stiffness scale.

## 2026-06-08 Codex FEM Phase 1 builder
- Trial: GPT-5.5/Codex execution of `docs/lab/fem_phase1_runner_prompt.md` under `runs/fem_phase1/codex/<tool>/`.
  - Command: `PYTHONUNBUFFERED=1 runs/fem_phase1/codex/run_all.sh`
  - Checker result: replay command completed with exit code 0. TensorMesh, JAX, and CalculiX solved. Nastran deck generated for human Femap solve with null frequencies.
  - Key metrics: TensorMesh first three modes = 301.8295, 349.5626, 362.1548 Hz. JAX first three modes = 301.8311, 355.5598, 360.0483 Hz. CalculiX first three modes = 84.7719, 86.5072, 192.5830 Hz. All solved cells report fixed-base no-zero-mode checks in `results.json`.
  - Artifacts: `runs/fem_phase1/codex/tensormesh/results.json`, `runs/fem_phase1/codex/jax/results.json`, `runs/fem_phase1/codex/calculix/model/hexapod_codex.inp`, `runs/fem_phase1/codex/nastran_deck/model/model.bdf`, per-tool figures and READMEs, `priority_deliverables.md`, `decisions_log.md`, `files_changed.md`.
  - Lessons: the initial workspace name was wrong (`composer` instead of `codex`) and was corrected. CalculiX `.dat` parsing must use the cycles/time column, not the final imaginary-frequency column.

## 2026-06-02 Codex GPT-5.5 round-2 sequential vibe/modal/flight runner
- Trial: isolated round-2 Codex runner focused on the priority coupled interface acceleration response PSD GIF, forcing overlay, flight tray `3*GRMS` reference overlay, real NumPyro NUTS, resolution sensitivity, and runtime accounting.
  - Commands:
    - `pwd` confirmed `/Users/avoss/Downloads/bayesX/Agentic BayesX`.
    - `.venv_nuts/bin/pip install --quiet --disable-pip-version-check 'arviz<0.19'`
    - `.venv_nuts/bin/pip install --quiet --disable-pip-version-check 'scipy<1.13'`
    - `PYTHONUNBUFFERED=1 bash artifacts/reports/runner_codex_gpt55_round2_20260602/run_round2.sh`
    - `.venv_nuts/bin/python -m py_compile artifacts/reports/runner_codex_gpt55_round2_20260602/run_round2.py`
    - `shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. `checks.json` reports `status = pass`; immutable checker hashes all reported `OK`.
  - Key metrics: final all-11-flight NumPyro NUTS used 4 chains, 900 warmup, 900 post-warmup samples per chain. Strict all-variable diagnostics passed: max rank-normalized R-hat = 1.0070878 at `flight_tray_force_raw`, min bulk ESS = 1080.12 at `sigma_build_db`, min tail ESS = 1199.80 at `sigma_build_db`, divergences = 0. Early cumulative GIF prefix fits 1-3 had divergences (4, 4, 1 respectively), so those frames are hard-WARN despite the final posterior pass.
  - Priority artifacts: `figures/interface_response_psd_evolution.gif`, `figures/flight_forcing_samples_overlay.png`, `figures/flight_tray_3grms_vs_vibe_reference.png`, `priority_deliverables.md`, `runtime.json`.
  - Interface PSD result: final 99% predictive band did not exceed the smoothline at any frequency; max 99%/spec ratio = 0.59285 at 62.41 Hz.
  - Resolution result: stored grid had 2 points in each half-power band; mode-local refined grid had 75 points near 86.25 Hz and 82 near 93.5 Hz. Median refined-minus-base interface `3*GRMS` shift = -0.000625%.
  - Runtime: `active_runtime_s = 293.864`, `elapsed_wallclock_s = 293.877`.
  - Lessons: the setup dataset did not store full forcing PSD curves; the runner reconstructed them from the setup RNG and verified exact agreement with stored force log-mean/log-sd summaries. A wrapper path bug briefly created `/Users/avoss/Downloads/bayesX/.venv_nuts`; it was removed and the wrapper was patched to use the actual repo root.

## 2026-06-02 Codex GPT-5.5 full sequential vibe/modal/flight runner
- Trial: independent Codex runner attempt at the full staged dome/tray vibe-modal-flight experiment with posterior inference and full-vs-peak likelihood comparison.
  - Commands:
    - `PYTHONPATH=. python3 -m py_compile scripts/run_codex_gpt55_full_experiment.py tests/test_runner_codex_gpt55_full_experiment.py`
    - `PYTHONPATH=. python3 scripts/run_codex_gpt55_full_experiment.py`
    - `PYTHONPATH=. python3 tests/test_runner_codex_gpt55_full_experiment.py`
    - `shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Runner checker wrote `artifacts/reports/runner_codex_gpt55_20260602/runner_checker_report.json`; immutable checker hashes all reported `OK`.
  - Key metrics: NumPyro/JAX/PyMC absent under Python 3.9.6, so the runner used labeled PyTorch fixed-trajectory HMC, not NUTS. Full-data HMC divergences = 3; peak-feature HMC divergences = 0. Full-data tray `3*GRMS` 95% interval = [1.12724, 3.04702] g and 99% interval = [0.974924, 3.72774] g. Peak-feature tray `3*GRMS` 95% interval = [0.929470, 2.41841] g.
  - Artifacts: `artifacts/reports/runner_codex_gpt55_20260602/packet.md`, `manifest.json`, `commands.md`, `checks.json`, `nuts_diagnostics.json`, `posterior_results.json`, `feature_sensitivity.json`, `sequential_full_dataset.json`, and generated figures.
  - Lessons: a real HMC substitute is feasible with available PyTorch, but it should not be called NUTS and the full-data run still has divergences/R-hat concerns. The checker verifies artifact consistency and immutable files, not physical correctness.

## 2026-06-02 Plain-English multi-agent scaffold
- Trial: create first scaffold where Claude Code is lead and Codex/Cursor can be manually launched as helpers.
  - Commands:
    - `python3 tests/test_multi_agent_scaffold.py`
    - `bash scripts/run_fresh_2dof_statfem_fbs.sh`
    - `python3 tests/test_fresh_2dof_rerun.py`
    - `shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Scaffold checker wrote `artifacts/tests/multi_agent_scaffold_report.json`; fresh 2DOF checker reported `pass = true`; immutable checker hashes all reported `OK`.
  - Key metrics: numeric assumptions = 30; Ch2/Ch3 relative L2 = 0.6739064407171255.
  - Artifacts: `docs/agents/how_to_run.md`, `docs/agents/claude_code_starter_prompt.md`, `.claude/agents/`, `.cursor/agents/`, `.cursor/rules/`, `docs/codex_prompts/multi_agent/`, and `artifacts/reports/multi_agent_first_loop_20260602/`.
  - Lessons: Git was initialized in this previously untracked folder. NUTS/HMC is now documented as the future default sampler, but the existing inference code remains prototype/legacy random-walk/random-scan Metropolis until a checked implementation replaces it.

## 2026-06-02 Sequential vibe/modal/flight research setup
- Trial: create setup packet for a staged rocket dome/tray workflow with smoothline vibe PSD, tray vibe test, dome-only modal test, coupled modal test, first flight, and ten later build/flight updates.
  - Commands:
    - `python3 -m py_compile scripts/sequential_vibe_modal_flight_setup.py tests/test_sequential_vibe_modal_flight_setup.py`
    - `bash scripts/run_sequential_vibe_modal_flight_setup.sh`
    - `shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. New checker wrote `artifacts/tests/sequential_vibe_modal_flight_setup_report.json`; immutable checker hashes all reported `OK`.
  - Key metrics: dome FEM peak response PSD = 0.1 g^2/Hz; smoothline input 3*GRMS = 28.2690 g; first-build tray vibe observed 3*GRMS = 43.9091 g; flight count = 11; later builds = 10; forcing covariance = Matérn-3/2 with log-frequency length scale 0.08; NUTS active = false.
  - Artifacts: `artifacts/reports/sequential_vibe_modal_flight_20260602/`, `scripts/sequential_vibe_modal_flight_setup.py`, `tests/test_sequential_vibe_modal_flight_setup.py`, and `docs/agents/claude_sequential_vibe_modal_flight_prompt.md`.
  - Lessons: the next Claude loop can start from a checked setup packet, but posterior updates still require a real NUTS/HMC implementation. The setup explicitly treats 3 dB flight-to-flight variability as fixed/known and build-to-build plus sensor-noise scales as future learned quantities.

## 2026-05-27
- Initialized run log template.
- Trial: canary harness gate
  - Command: `PYTHONPATH=. python3 harness/driver.py --config harness/configs/canary_trial.json`
  - Checker result: pass
  - Key metrics: canary rmse = 0.0, manifest mismatch = none
- Trial: posterior recovery test
  - Command: `PYTHONPATH=. python3 tests/test_posterior_recovery.py`
  - Checker result: pass
  - Key metrics: acceptance_rate = 0.0167, all tracked relative errors < 0.35
- Trial: MDOF reduced transfer test
  - Command: `PYTHONPATH=. python3 tests/test_mdof_transfer.py`
  - Checker result: pass
  - Key metrics: relative_l2_error = 0.0514

## 2026-05-27 Codex review + sampler fix
- Trial: baseline pipeline before sampler fix
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: posterior recovery acceptance_rate = 0.0167; MDOF relative_l2_error = 0.0514; canary manifest mismatches = none
  - Lessons: all-parameter random-walk MH passed the loose smoke test but had poor sampler movement.
- Trial: targeted posterior recovery after sampler fix
  - Command: `PYTHONPATH=. python3 tests/test_posterior_recovery.py`
  - Checker result: pass
  - Key metrics: acceptance_rate = 0.216; tracked relative errors all < 0.35
- Trial: final full pipeline after sampler fix
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; manifest mismatches before/after = none; posterior recovery acceptance_rate = 0.216; MDOF relative_l2_error = 0.0514; plot manifest lists 6 PNGs
  - Full MCMC artifact: acceptance_rate = 0.2009; post_burn_acceptance_rate = 0.1408; tracked relative errors: k1 = 0.0104, k2 = 0.0210, k12 = 0.1393, force_amp = 0.1163, force_fc = 0.0671, qoi_peak_tray_accel = 0.00303
  - Lessons: inspect both smoke-test metrics and the full inference artifact; the default run needed a smaller proposal scale than the test configuration.

## 2026-05-29 Aerospace vibration data search
- Trial: web search and source review for real aerospace vibration/modal/flight data
  - Command/source path: Browser/web search; documented results in `references/aerospace-vibration-data-candidates.md`
  - Checker result: not a computational checker trial
  - Key candidates: F-16 GVT benchmark from 4TU, Vibrationdata SR-19/Pegasus/RV acceleration time histories, NASA PIMS/SAMS ISS acceleration archives, BAE T1A Hawk datasets, TU Delft Diana 2 GVT, NASA CRM FEM/modal files
  - Lessons: best primary/secondary public fit is F-16 wing plus dummy payload/pylon interface; best tank/dome-like flight/static-fire signal is Vibrationdata SR-19 forward dome ignition, but it is single-channel acceleration rather than an FRF.

## 2026-05-29 Cursor skills connected to Codex
- Trial: install personal Cursor skills into Codex user skills
  - Command/source path: copied from `/Users/avoss/.cursor/skills/` to `/Users/avoss/.codex/skills/`
  - Checker result: copied folders match source by `diff -rq`; all five `SKILL.md` files have `name` and `description` frontmatter
  - Installed skills: `andrew-voss-voice`, `evergreen-knowledge-work`, `honest-technical-work`, `project-harness`, `stop-slop`
  - Excluded by design: Cursor internal helper skills under `/Users/avoss/.cursor/skills-cursor/` and ME539 `textbook-latex-editor`
  - Lessons: restart Codex before expecting newly copied skills to appear in the session skill inventory.

## 2026-05-29 Milestones 1-2: synthetic packet + channel fix
- Trial: full question-first synthetic StatFEM pipeline
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable manifest mismatches before/after = none; posterior recovery acceptance_rate = 0.216; MDOF relative_l2_error = 0.0514; channel 2/3 clean relative_l2 = 0.6877; review packet completeness pass = true
  - Artifacts: `artifacts/reports/synthetic_statfem_packet.md`, report figures under `artifacts/reports/figures/`, channel report at `artifacts/tests/channel_definitions_report.json`, review packet report at `artifacts/tests/review_packet_report.json`
  - Lessons: channel 2 is now primary-side `F1/a1`, channel 3 is tray-side `F2/a2`; BOED is explicitly framed as useful only after the human chooses the objective and experiment menu.
- Trial: fix review packet image rendering
  - Command: `PYTHONPATH=. python3 scripts/generate_review_packet.py && PYTHONPATH=. python3 tests/test_review_packet.py`
  - Checker result: pass
  - Key metrics: missing_files = none; missing_snippets = none; missing_embedded_images = none; manifest_ok = true
  - Lessons: report Markdown image links need absolute paths wrapped in angle brackets because the local project path contains a space.

## 2026-05-29 GP error exploration
- Trial: inspect and visualize current GP-over-frequency discrepancy model
  - Command: `PYTHONPATH=. python3 scripts/explore_gp_error.py`
  - Checker result: artifact generated; no formal pipeline checker added
  - Key metrics: discrepancy_scale = 0.03; discrepancy_corr_hz = 8.0 Hz; iid real/imag sigma = 0.02; covariance diagonal mean = 0.0009000001; near correlation reference = 0.6199; far correlation reference ~ 0
  - Artifacts: `artifacts/reports/gp_error_exploration/gp_error_exploration.md`, `gp_frequency_covariance.png`, `gp_error_samples.png`, `gp_error_components_ch2.png`, `gp_error_exploration.json`
  - Lessons: the project already uses an additive zero-mean squared-exponential GP over frequency, but the realized discrepancy is not stored separately from iid sensor noise in the main dataset.

## 2026-06-01 Report clarification: 2DOF vs MDOF
- Trial: clarify synthetic packet scope and add experimental workflow walkthrough
  - Command: `PYTHONPATH=. python3 scripts/generate_review_packet.py && PYTHONPATH=. python3 tests/test_review_packet.py`
  - Checker result: pass
  - Key metrics: missing_files = none; missing_snippets = none; missing_embedded_images = none; manifest_ok = true
  - Artifacts: updated `artifacts/reports/synthetic_statfem_packet.md`; added `artifacts/reports/figures/experimental_workflow.png`
  - Lessons: keep the 2DOF StatFEM packet separate from the MDOF transfer-function prototype to avoid implying that the current update is for two MDOF structures.

## 2026-06-01 Linear-unit key FRF review artifact
- Trial: add 2DOF transfer-function plot, summary, checker, and packet section
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; posterior recovery acceptance_rate = 0.216; MDOF relative_l2_error = 0.0514; channel 2/3 clean relative_l2 = 0.6877; key FRFs reported = 9; review packet completeness pass = true
  - Artifacts: `artifacts/plots/key_2dof_transfer_functions_linear.png`, `artifacts/reports/key_frf_summary.json`, `artifacts/tests/key_transfer_functions_report.json`, updated `artifacts/reports/synthetic_statfem_packet.md`
  - Lessons: separate review units by quantity. This first version incorrectly treated drive-point `F/a` as the plotted apparent-mass convention; see the corrected 7004C convention trial below.
- Trial: correct apparent-mass convention to match NASA-HDBK-7004C expectation
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; key FRFs reported = 14; apparent_mass_without_interior_peak = none; apparent_mass_without_resonant_amplification = none; review packet completeness pass = true
  - Artifacts: regenerated `artifacts/plots/key_2dof_transfer_functions_linear.png`, `artifacts/reports/key_frf_summary.json`, `artifacts/tests/key_transfer_functions_report.json`, updated `artifacts/reports/synthetic_statfem_packet.md`
  - Lessons: 7004C-style load apparent mass is reaction force over input/interface acceleration and has resonance peaks; drive-point `F/a` at the moving coordinate is reciprocal inertance and has resonance minima.

## 2026-06-01 Apparent-mass mistake postmortem
- Trial: document the caught convention error as an agentic workflow failure case
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; key FRFs reported = 14; apparent_mass_without_interior_peak = none; review packet completeness pass = true
  - Artifacts: `docs/lab/apparent-mass-convention-postmortem.md`, `docs/lab/README.md`, updated `artifacts/reports/synthetic_statfem_packet.md`
  - Lessons: this was a semantic specification failure. The agent produced a reproducible artifact for an underspecified technical noun; the human caught the convention mismatch by inspecting curve shape.
- Trial: correct source vs load apparent-mass convention from NASA-HDBK-7004C Figure 9
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: key FRFs reported = 15; source_apparent_mass_without_interior_notch = none; source_apparent_mass_without_low_frequency_growth = none; load_apparent_mass_without_interior_peak = none; load_apparent_mass_without_resonant_amplification = none; review packet completeness pass = true
  - Artifacts: regenerated `artifacts/plots/key_2dof_transfer_functions_linear.png`, `artifacts/reports/key_frf_summary.json`, updated `docs/lab/apparent-mass-convention-postmortem.md`
  - Lessons: source and load apparent mass are both interface quantities in 7004C, but source and load constraints differ. Source AM can have a resonance notch and low-frequency growth; load AM has the familiar fixed-base peak.
- Trial: add mass and uncoupled-frequency reference lines to key FRF plot
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: mass_reference_ok = true; total_mass_ok = true; natural_frequency_reference_ok = true; key FRFs reported = 15; review packet completeness pass = true
  - Artifacts: regenerated `artifacts/plots/key_2dof_transfer_functions_linear.png`, updated `artifacts/reports/key_frf_summary.json`, updated `artifacts/reports/synthetic_statfem_packet.md`
  - Lessons: mass and uncoupled-frequency guide lines make apparent-mass plots easier to audit against low-frequency mass levels and expected resonance/notch locations.

## 2026-06-01 Coupling, error evidence, and sensitivity artifact
- Trial: tie coupling to tray properties and add missing error/sensitivity evidence to the review packet
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; posterior recovery acceptance_rate = 0.226; MDOF relative_l2_error = 0.0514; channel 2/3 clean relative_l2 = 0.5670; tied_coupling_ok = true; error components reconstruct observed-clean residuals; sensitivity scenarios = 5; review packet completeness pass = true
  - Artifacts: `artifacts/reports/figures/error_hyperparameters.png`, `artifacts/reports/figures/channel_error_vs_truth.png`, `artifacts/reports/figures/parameter_error_summary.png`, `artifacts/reports/sensitivity_assumptions/sensitivity_assumptions.md`, `artifacts/tests/tied_coupling_and_errors_report.json`, `artifacts/tests/sensitivity_artifact_report.json`
  - Lessons: the packet previously named uncertainty categories without showing actual values or realized errors. Sensitivity to assumptions should be treated as a default artifact, and smoke tests must not leave their temporary dataset as the canonical packet input.

## 2026-06-01 GP samples and QOI samples in packet
- Trial: add concrete GP discrepancy sample paths and posterior QOI sample visualization to the Bilionis packet
  - Command: `python3 -m py_compile src/inference/mcmc.py scripts/generate_review_packet.py tests/test_review_packet.py && bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; posterior recovery acceptance_rate = 0.226; channel 2/3 clean relative_l2 = 0.5670; key FRFs reported = 15; retained QOI samples = 240; review packet completeness pass = true
  - Artifacts: `artifacts/reports/figures/gp_discrepancy_samples.png`, `artifacts/reports/figures/qoi_samples.png`, updated `artifacts/reports/synthetic_statfem_packet.md`, updated `artifacts/inference/twodof_mcmc_result.json`
  - Lessons: QOI uncertainty is easier to audit when shown as actual retained sample values and response spectra. The current posterior QOI samples are visibly biased high relative to the synthetic truth, so the next technical work should include posterior predictive checks and identifiability/sensitivity on the discrepancy model.
- Trial: triage unclear QOI sample figure
  - Command: `PYTHONPATH=. python3 -m py_compile scripts/generate_review_packet.py tests/test_review_packet.py && PYTHONPATH=. python3 scripts/generate_review_packet.py && PYTHONPATH=. python3 tests/test_review_packet.py`
  - Checker result: pass
  - Key metrics: posterior QOI truth = 1190.2531; posterior QOI mean = 1209.3565; mean bias = +19.1034 (+1.605%); retained samples above truth = 100%; missing review-packet snippets/files = none
  - Artifacts: updated `artifacts/reports/figures/qoi_samples.png`, updated `artifacts/reports/synthetic_statfem_packet.md`
  - Lessons: full-scale spectra can look line-on-line while still producing a biased peak QOI. QOI figures should include residual/zoom panels and explicit bias diagnostics.
- Trial: fix error plot communication by separating observed data, absolute error, and relative diagnostic views
  - Command: `bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; channel 2/3 clean relative_l2 = 0.5670; key FRFs reported = 15; sensitivity scenarios = 5; review packet completeness pass = true
  - Artifacts: `artifacts/reports/figures/channel_truth_vs_observed.png`, `artifacts/reports/figures/channel_absolute_error.png`, retained secondary diagnostic `artifacts/reports/figures/channel_error_vs_truth.png`
  - Lessons: normalized error is useful for "where does error matter relative to signal?", but should not be the primary evidence for what noise/discrepancy was injected because denominator effects can look like physics.
- Trial: log-frequency axis and GP-coordinate correction
  - Command: `PYTHONPATH=. python3 -m py_compile src/twodof/synthetic_data.py src/inference/mcmc.py scripts/generate_review_packet.py scripts/run_sensitivity_study.py scripts/explore_gp_error.py tests/test_review_packet.py tests/test_tied_coupling_and_errors.py && bash scripts/run_pipeline.sh`
  - Checker result: pass
  - Key metrics: canary status = pass; immutable checker manifest mismatches before/after = none; posterior recovery acceptance_rate = 0.2313; full MCMC acceptance_rate = 0.2323; post_burn_acceptance_rate = 0.2033; channel 2/3 clean relative_l2 = 0.5670; log_frequency_gp_ok = true; review packet axis_metadata_ok = true; QOI mean bias = +18.2866 (+1.536%); retained QOI samples above truth = 100%
  - Artifacts: updated `artifacts/reports/figures/channel_truth_vs_observed.png`, `channel_absolute_error.png`, `channel_error_vs_truth.png`, `gp_discrepancy_samples.png`; `docs/lab/log-frequency-plot-gp-postmortem.md`; updated `artifacts/reports/synthetic_statfem_packet.md`
  - Lessons: the earlier agent did not fail because log axes were hard; it failed because a requirement satisfied in one artifact was not promoted to a durable plotting convention and checker expectation. The GP is now stationary in natural log frequency, which is a more defensible default for broad-band structural dynamics review than fixed-Hz stationarity.
- Trial: broad harness guardrails for fresh 2DOF rerun
  - Command: `python3 tests/test_review_packet.py`; plus `rg` inspection for new guardrail language
  - Checker result: pass for existing review-packet checker
  - Key metrics: review packet missing_files = none; missing_snippets = none; missing_embedded_images = none; manifest_ok = true; axis_metadata_ok = true
  - Artifacts: `docs/harness/agentic-engineering-quality-gates.md`, `docs/codex_prompts/fresh_2dof_rerun.md`, updated `AGENTS.md`, updated `docs/CODEX.md`, updated `docs/codex_prompts/replicate.md`, `review.md`, and `extend.md`
  - Lessons: human feedback should be generalized into gates: assumptions ledgers, quantity contracts, reference/standards comparisons, review-packet evidence, sensitivity, and checker-backed metadata.

## 2026-06-01 Fresh 2DOF StatFEM/FBS rerun
- Trial: fresh scoped 2DOF StatFEM/FBS rerun with question-first artifacts, quantity contracts, synthetic data, posterior/QOI samples, sensitivity, reference comparison, fresh checker, and prior-run comparison.
  - Command: `bash scripts/run_fresh_2dof_statfem_fbs.sh`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with `shasum -a 256 -c harness/checkers/manifest.sha256`.
  - Key metrics: numeric assumptions = 16 machine-readable rows; Ch2/Ch3 clean relative L2 = 0.770745; sampler acceptance_rate = 0.07737; retained posterior samples = 560; QOI peak tray acceleration mean = 59.10375 m/s^2; 5-95% interval = [58.91892, 59.27161] m/s^2; synthetic truth = 59.03368 m/s^2; QOI fraction above truth = 0.732; sensitivity scenarios = 6 posterior/QOI + 5 synthetic-error; reference checks pass.
  - Reference comparison metrics: Ch4 low-frequency transmissibility median = 1.03667; Ch4 high-frequency median = 0.18006; Ch4 peak = 76.90548 Hz vs tray truth 77.58060 Hz; Ch1 notch = 108.28640 Hz vs dome truth 107.77755 Hz.
  - Artifacts: `artifacts/reports/fresh_2dof_statfem_fbs_20260601/fresh_2dof_statfem_packet.md`; figures and JSON manifest under `artifacts/reports/fresh_2dof_statfem_fbs_20260601/`; implementation in `scripts/fresh_2dof_statfem_fbs.py`; one-command runner `scripts/run_fresh_2dof_statfem_fbs.sh`; checker `tests/test_fresh_2dof_rerun.py`.
  - Lessons: the fresh run intentionally uses one tray-to-primary stiffness/damping in the coupled model rather than copying the prior path. Visual QA caught an overlapping reference-comparison title/metric text before final logging. The low-but-nonzero MH acceptance rate is acceptable for this harness artifact but remains a sampler-quality limitation.

## 2026-06-01 Fresh 2DOF QOI/noise/7004C correction
- Trial: respond to human review by replacing deterministic peak QOI with `3 * GRMS` from tray response PSD, increasing noise/discrepancy assumptions, and adding NASA-HDBK-7004C source/load apparent-mass benchmarks.
  - Command: `bash scripts/run_fresh_2dof_statfem_fbs.sh`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with `shasum -a 256 -c harness/checkers/manifest.sha256`.
  - Key metrics: numeric assumptions = 19 machine-readable rows; Ch2/Ch3 clean relative L2 = 0.770745; sampler acceptance_rate = 0.49263; retained posterior samples = 560; QOI definition = `3 * GRMS of tray acceleration response PSD`; QOI mean = 9.16652 g; 5-95% interval = [7.70190, 10.63325] g; synthetic truth = 8.25930 g; QOI fraction above truth = 0.8518.
  - Noise/discrepancy metrics: median normalized error diagnostics = Ch1 0.263, Ch2 0.299, Ch3 0.309, Ch4 0.285; 90th-percentile diagnostics = Ch1 0.516, Ch2 0.571, Ch3 0.513, Ch4 0.506; response-PSD absolute log-error median = 0.298 and 90th percentile = 0.641.
  - Reference comparison metrics: NASA-HDBK-7004C `Q=50` benchmark load `M(0.62)=1.62423`, load `M(1)=50.01000`, source `M(1)=0.02000`; Ch4 peak = 76.90548 Hz vs tray truth 77.58060 Hz; Ch1 notch = 108.28640 Hz vs dome truth 107.77755 Hz.
  - Artifacts: updated `artifacts/reports/fresh_2dof_statfem_fbs_20260601/fresh_2dof_statfem_packet.md`; added `noise_qoi_7004c_lit_review.md`; added `figures/nasa_7004c_apparent_mass_benchmark.png`; updated `scripts/fresh_2dof_statfem_fbs.py`, `tests/test_fresh_2dof_rerun.py`, `quantity_contracts.md`, and `assumptions_ledger.md`.
  - Lessons: PSD-domain random-vibration QOI is a better match for aerospace review than the peak of one synthetic time realization. Noise should be scaled locally, with floors near notches, when the goal is to stress-test model updating and produce useful review plots. 7004C values should be plotted as source/load apparent mass benchmarks, while reciprocal inertance remains explicitly separate.

## 2026-06-01 Fresh 2DOF model-error and sensitivity clarity correction
- Trial: respond to human review that the reference pass/fail bar chart was not useful, the sensitivity threshold text was confusing, and model-form frequency/damping errors were still too mild.
  - Command: `python3 -m py_compile scripts/fresh_2dof_statfem_fbs.py tests/test_fresh_2dof_rerun.py && bash scripts/run_fresh_2dof_statfem_fbs.sh && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: numeric assumptions = 27; Ch2/Ch3 clean relative L2 = 0.673906; sampler acceptance_rate = 0.49921; retained posterior samples = 560; QOI definition = `3 * GRMS of tray acceleration response PSD`; QOI mean = 12.12008 g; 5-95% interval = [10.21921, 13.94476] g; synthetic truth = 10.89493 g; QOI fraction above truth = 0.8607.
  - Model-error metrics: synthetic truth now shifts dome frequency from nominal 110 Hz to 93.50 Hz (-15%) and tray frequency from nominal 75 Hz to 86.25 Hz (+15%); damping ratios are zeta1 = 0.0225 (+25% from nominal 0.018) and zeta2 = 0.0195 (-25% from nominal 0.026).
  - Sensitivity metrics: `sensitivity_summary.json` now has `decision_threshold = null`; baseline retained-sample QOI recomputation mean = 12.54073 g; damping 0.75 gives +15.0% mean QOI shift; damping 1.25 gives -10.2%; narrow force bandwidth gives -25.0%; wide force bandwidth gives +15.5%.
  - Reference comparison metrics: value-table figure replaced the green pass/fail bar chart. Ch4 low-frequency median = 1.02946; Ch4 high-frequency median = 0.23074; Ch4 peak = 86.90298 Hz vs tray truth 86.25 Hz; Ch1 notch = 93.51496 Hz vs dome truth 93.50 Hz; NASA-HDBK-7004C Figure 9 load `M(0.62)=1.62423`, load `M(1)=50.01000`, source `M(1)=0.02000`.
  - Artifacts: updated `artifacts/reports/fresh_2dof_statfem_fbs_20260601/fresh_2dof_statfem_packet.md`, `figures/reference_standards_comparison.png`, `figures/sensitivity_qoi.png`, `assumptions_ledger.md`, `assumptions_ledger.json`, `noise_qoi_7004c_lit_review.md`, `reference_comparison.json`, `sensitivity_summary.json`, `checker_report.json`, and `checker_report_external.json`.
  - Lessons: a checker-scoreboard figure is not an engineering review artifact unless it exposes the values, expectations, and meaning behind the booleans. Sensitivity text should say whether it refits the posterior or only recomputes retained samples. Human gut checks on frequency/damping error should become explicit model-form assumptions and checker conditions, not hidden tuning.

## 2026-06-01 Fresh 2DOF Bayes-rule and replicate triage
- Trial: respond to human review requesting graphical Bayes-rule evidence, posterior natural-frequency/damping samples with 95% CIs, prior predictive spectra beside data, and explicit simulation replicate counts.
  - Command: `python3 -m py_compile scripts/fresh_2dof_statfem_fbs.py tests/test_fresh_2dof_rerun.py && bash scripts/run_fresh_2dof_statfem_fbs.sh && python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: numeric assumptions = 27; Ch2/Ch3 clean relative L2 = 0.673906; sampler acceptance_rate = 0.49921; retained posterior samples = 560; QOI mean = 12.12008 g; QOI truth = 10.89493 g; QOI 95% interval = [9.88234, 14.28316] g.
  - Parameter posterior metrics: dome frequency median = 93.4717 Hz, 95% CI = [93.1987, 93.7950], truth = 93.50; tray frequency median = 86.2534 Hz, 95% CI = [86.0418, 86.3982], truth = 86.25; dome damping median = 0.021987, 95% CI = [0.019116, 0.025913], truth = 0.0225; tray damping median = 0.021770, 95% CI = [0.020177, 0.023802], truth = 0.0195.
  - Bayes diagnostics: log likelihood at prior center = -8398.77; at synthetic truth = 166.68; at retained posterior mode = 172.90. Conditional likelihood slices are one-dimensional diagnostics, not marginalized likelihoods.
  - Simulation replicate metadata: one realization per FRF/transfer channel, one flight-like response PSD realization, one secondary time-history realization; flight-to-flight variability is not modeled.
  - StatFEM/noise metadata: generated GP model discrepancy and iid sensor noise are kept separate in `fresh_2dof_dataset.json`; the likelihood uses summed fixed covariance and does not infer the realized discrepancy field or hyperparameters.
  - Artifacts: added `figures/bayes_parameter_update.png`, `figures/parameter_posterior_samples.png`, `figures/prior_predictive_vs_data.png`, `figures/posterior_predictive_spectra.png`, and `bayes_update_summary.json`; updated the packet, dataset metadata, assumptions ledgers, manifest, and fresh checker reports.
  - Lessons: posterior predictive distributions should be shown for spectra, not only posterior-mean curves. Dataset replicate count and flight-to-flight variability must be explicit in the packet and checker. A toy can fit far from nominal when the synthetic truth is still inside the model family; that must be labeled as a plumbing check, not evidence of real-FEM robustness.

## 2026-06-02 Fresh 2DOF prior/likelihood methodology clarity
- Trial: respond to human review asking whether discrepancy/hyperparameters should be inferred, what "truth inside the model family" means, what prior variances are assumed, and whether the likelihood uses whole FRFs or peak summaries.
  - Command: `python3 -m py_compile scripts/fresh_2dof_statfem_fbs.py tests/test_fresh_2dof_rerun.py && bash scripts/run_fresh_2dof_statfem_fbs.sh && python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: numeric assumptions = 30; Ch2/Ch3 clean relative L2 = 0.673906; prior/likelihood methodology checker = true.
  - Prior metrics: stiffness prior `log(k/k_nom) ~ Normal(0, 0.18^2)` truncated to `[0.55, 1.65]`; implied natural-frequency prior `sigma_log(f/f_nom)=0.09`, untruncated 95% factor `[0.838, 1.193]`; damping prior `log(zeta/zeta_nom) ~ Normal(0, 0.35^2)`, untruncated 95% multiplier `[0.504, 1.986]`.
  - Likelihood metrics: Ch1-Ch4 use all complex FRF/transfer values at 120 log-spaced frequencies, with real and imaginary residual vectors evaluated independently under `K_discrepancy + diag(sensor_noise^2)`. Flight-like response uses all 181 log response-PSD values. Peak/notch locations are reference checks and plots only, not likelihood summary statistics.
  - StatFEM limitation: discrepancy fields and noise/discrepancy hyperparameters remain fixed assumptions; the desired next step is a hierarchical StatFEM model that infers discrepancy fields/hyperparameters, preferably with repeated tests/flights.
  - Artifacts: updated `fresh_2dof_statfem_packet.md`, `bayes_update_summary.json`, `assumptions_ledger.md`, `assumptions_ledger.json`, `checker_report.json`, `checker_report_external.json`, `scripts/fresh_2dof_statfem_fbs.py`, and `tests/test_fresh_2dof_rerun.py`.
  - Lessons: prior variance and likelihood data usage are central methodology and require checker-backed report text. A future agent should never leave "whole FRF vs peak summary" implicit.

## 2026-06-02 StatFEM method graphic and harness rule upgrade
- Trial: respond to human review that the packet must expose the model form, likelihood function, inferred/fixed/not-inferred assumptions, data/replicate count, and whole-FRF versus peak-summary choice from the first review summary.
  - Command: `python3 -m py_compile scripts/fresh_2dof_statfem_fbs.py tests/test_fresh_2dof_rerun.py && bash scripts/run_fresh_2dof_statfem_fbs.sh && python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: numeric assumptions = 30; Ch2/Ch3 clean relative L2 = 0.673906; `method_summary_documented = true`; method graphical model appears in `manifest.json`; QOI mean = 12.12008 g; QOI truth = 10.89493 g; QOI 95% interval = [9.88234, 14.28316] g.
  - Method-summary metrics: report now states one synthetic dataset, one FRF/transfer realization per channel, one flight-like response PSD, one secondary time-history realization, and no flight-to-flight variability. It states `theta = {k1, k2, zeta1, zeta2, force_amp, force_fc}`, fixed noise/discrepancy hyperparameters, non-inferred discrepancy fields/hyperparameters/replicate effects, and a whole-curve likelihood for 120 complex FRF points plus 181 log response-PSD points.
  - Artifacts: added `figures/statfem_likelihood_graphical_model.png`; updated `fresh_2dof_statfem_packet.md`, `manifest.json`, `checker_report.json`, `checker_report_external.json`, `scripts/fresh_2dof_statfem_fbs.py`, `tests/test_fresh_2dof_rerun.py`, `AGENTS.md`, `docs/harness/agentic-engineering-quality-gates.md`, `docs/CODEX.md`, `docs/codex_prompts/fresh_2dof_rerun.md`, and local Codex skills `honest-technical-work` and `project-harness`.
  - Lessons: a report can contain the right facts but still fail review if the statistical model is scattered across sections. Method visibility should be a checker-backed gate: graphical model, likelihood equation, data count, whole-data versus summary-feature choice, and inferred/fixed/not-inferred variables must be visible before posterior plots.
- Trial: improve graphical-model equation legibility by replacing plain underscore/caret equation strings with Matplotlib mathtext/LaTeX-style rendering.
  - Command: `python3 -m py_compile scripts/fresh_2dof_statfem_fbs.py tests/test_fresh_2dof_rerun.py && bash scripts/run_fresh_2dof_statfem_fbs.sh && python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: `method_summary_documented = true`; missing files/snippets = none; numeric assumptions = 30; Ch2/Ch3 clean relative L2 = 0.673906.
  - Artifacts: regenerated `figures/statfem_likelihood_graphical_model.png` with readable math notation for `theta`, FRF/PSD residuals, covariance, Bayes update, and the run-specific data model.
  - Lessons: method diagrams should use real math rendering and sufficient font size for equations. Plain text symbols such as `_`, `^`, and long one-line likelihoods are not review-grade even when the underlying content is correct.
- Trial: add image-legibility hook and replace stale/cached unreadable method and reference/checker figures with new filenames.
  - Command: `python3 -m py_compile scripts/fresh_2dof_statfem_fbs.py tests/test_fresh_2dof_rerun.py && bash scripts/run_fresh_2dof_statfem_fbs.sh && python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: image legibility report pass = true; figures checked = 20; strict text-heavy figures = `figures/statfem_likelihood_graphical_model_legible.png` and `figures/reference_standards_comparison_cards.png`; strict method figure min font = 12.5 pt vs required 12.0 pt; strict reference figure min font = 11.5 pt vs required 11.5 pt; overlap/clipping/plain-math issues = none for strict figures.
  - Artifacts: added `image_legibility_report.json`; added cache-busting figures `statfem_likelihood_graphical_model_legible.png` and `reference_standards_comparison_cards.png`; updated report, manifest, internal checker, external checker, harness docs, launch prompt, and local skills.
  - Lessons: figure existence and checker booleans are not enough. The first implementation of the hook failed the run by flagging many edge tick labels, then the stricter text-heavy overlap check caught a real overlap in the reference cards. Blocking legibility checks should be strict for method/table/status figures and lighter for ordinary plot axes.
- Trial: smooth the prior-density plots and compare the full FRF/PSD likelihood against a peak/notch feature likelihood.
  - Command: `bash scripts/run_fresh_2dof_statfem_fbs.sh`; then `python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal checker and `tests/test_fresh_2dof_rerun.py` both reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: numeric assumptions = 33; Ch2/Ch3 clean relative L2 = 0.673906; image legibility report pass = true with 21 figures checked and no failed figures; `peak_feature_likelihood_comparison_present = true`.
  - Prior-plot metrics: prior curves in `bayes_parameter_update.png` and `parameter_posterior_samples.png` are now analytic transformed-prior density evaluations rather than finite-sample histograms. Posterior curves are retained-sample KDE summaries.
  - Peak-feature likelihood metrics: feature residual assumptions are log-frequency sigma = 0.06, FRF log-amplitude sigma = 0.30, and PSD log-amplitude sigma = 0.40. Features are Ch1 dome notch, Ch2 primary notch, Ch3 tray notch, Ch4 tray peak, and Ch5 response-PSD peak.
  - Comparison metrics: full-curve QOI mean = 12.12008 g with 95% interval [9.88234, 14.28316] g; peak-feature QOI mean = 10.31594 g with 95% interval [6.86282, 16.94469] g; synthetic truth = 10.89493 g. Peak-feature/full-curve 95% width ratios: QOI = 2.2909, dome frequency = 21.57, tray frequency = 27.32, dome damping = 1.923, tray damping = 5.790.
  - Sampler metrics: full-curve acceptance = 0.4992 with 560 retained samples; peak-feature acceptance = 0.8542 with 540 retained samples.
  - Artifacts: added `peak_feature_likelihood_summary.json`; added `figures/full_vs_peak_feature_likelihood_comparison.png`; updated `fresh_2dof_statfem_packet.md`, `manifest.json`, `checker_report.json`, `checker_report_external.json`, `scripts/fresh_2dof_statfem_fbs.py`, and `tests/test_fresh_2dof_rerun.py`.
  - Lessons: finite prior samples can make a smooth prior look jagged; plot analytic prior densities when available and label sampled estimates when not. Peak-only likelihoods are lossy and need explicit feature extraction, feature uncertainty assumptions, and side-by-side posterior/QOI interval comparisons against the whole-data likelihood.
- Trial: add a peak/notch feature-map benchmark so feature likelihoods are checked against predicted transfer-function features rather than natural frequencies directly.
  - Command: `bash scripts/run_fresh_2dof_statfem_fbs.sh`; then `shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal and external fresh rerun checkers reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: `peak_feature_mapping_benchmark_present = true`; image legibility report pass = true with 23 figures checked and no failed figures; numeric assumptions = 33; Ch2/Ch3 clean relative L2 = 0.673906.
  - Feature-map metrics: Ch1 clean dome notch = 93.576 Hz versus observed notch = 98.107 Hz, frequency z-score = 0.79; Ch4 clean tray peak = 86.341 Hz versus observed peak = 86.416 Hz, z-score = 0.01. The Ch1 frequency-feature likelihood slice peaks above the synthetic truth because the realized observed notch is shifted high.
  - Feature-sensitivity metrics: Ch1 notch frequency sensitivity is 1.06 to dome frequency and 0.00 to tray frequency; Ch4 peak sensitivity is 0.97 to tray frequency and 0.00 to dome frequency. Ch2 and Ch3 are mixed coupled features with dome/tray frequency sensitivities of approximately 0.41/0.62 and 0.62/0.45. Ch5 response-PSD peak amplitude is strongly force-center-confounded with sensitivity -3.57.
  - Artifacts: added `peak_feature_mapping_benchmark.json`, `figures/peak_feature_mapping_benchmark.png`, and `figures/peak_feature_sensitivity_matrix.png`; updated the report, manifest, internal checker, external checker, and feature-likelihood implementation.
  - Lessons: peak/notch likelihoods should be benchmarked through the same feature extractor used in the likelihood. A feature can be physically meaningful but still falsely informative if the realized observed feature is shifted by discrepancy/noise or if the feature is coupled to multiple parameters.
- Trial: triage remaining jagged prior visuals and encode analytic-plus-MC prior plotting as a SciML reporting rule.
  - Command: `bash scripts/run_fresh_2dof_statfem_fbs.sh`; then `python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal and external fresh rerun checkers reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: prior density MC histogram samples = 80,000; MC histogram bins = 90; prior predictive MC samples = 1,600; numeric assumptions = 33; Ch2/Ch3 clean relative L2 = 0.673906; image legibility report pass = true.
  - Artifacts: regenerated `figures/bayes_parameter_update.png`, `figures/parameter_posterior_samples.png`, and `figures/prior_predictive_vs_data.png`; updated `bayes_update_summary.json`, `fresh_2dof_statfem_packet.md`, `manifest.json`, `checker_report.json`, `checker_report_external.json`, `scripts/fresh_2dof_statfem_fbs.py`, `tests/test_fresh_2dof_rerun.py`, harness docs, and local skills.
  - Lessons: even after adding analytic prior curves, low-sample prior predictive bands and unlabeled prior histograms can still read as jagged or ambiguous. For SciML packets, analytic prior density should be the primary line; a high-sample MC histogram should be shown and labeled as a sampling diagnostic; prior predictive bands need enough MC samples for stable visual review.
- Trial: smooth prior/posterior predictive envelope display for the Ch4 prior predictive panel and related spectra.
  - Command: `bash scripts/run_fresh_2dof_statfem_fbs.sh`; then `python3 tests/test_fresh_2dof_rerun.py && shasum -a 256 -c harness/checkers/manifest.sha256`
  - Checker result: pass. Internal and external fresh rerun checkers reported `pass = true`; immutable checker manifest verified with all entries `OK`.
  - Key metrics: prior predictive MC samples = 4,000; displayed predictive quantile summaries smoothed = true; Gaussian smoothing sigma = 1.8 frequency-grid points; numeric assumptions = 33; image legibility report pass = true.
  - Artifacts: regenerated `figures/prior_predictive_vs_data.png`; updated `bayes_update_summary.json`, `fresh_2dof_statfem_packet.md`, `checker_report.json`, `checker_report_external.json`, `scripts/fresh_2dof_statfem_fbs.py`, and `tests/test_fresh_2dof_rerun.py`.
  - Lessons: a prior predictive envelope is not an analytic prior density. It is a finite-sample, pointwise MC summary of nonlinear forward-model outputs, and sharp moving resonances can make raw quantile curves look jagged even with many samples. If smoothing is used for review readability, label it as display smoothing and record the smoothing parameter.

- 2026-06-02 Claude Opus 4.8 full sequential vibe/modal/flight runner (isolated copy)
  - Command: `bash scripts/run_runner_claude_opus48.sh` (creates .venv_nuts with numpyro 0.19.0/jax 0.4.30; runs NUTS; runs runner checker; verifies immutable hashes).
  - Sampler: NUTS/HMC (NumPyro), 4 chains x (1000 warmup + 1000 draws), x64. NOT Metropolis.
  - Diagnostics: full -> 0 divergences, max R-hat 1.0024, min ESS 942; peak -> 0 divergences, R-hat 1.0019, ESS 1495. Runner checker 48/48 pass; immutable manifest all OK.
  - Key results: full whole-curve likelihood recovers dome fn 93.55 (truth 93.5), tray fn 86.14 (86.25), sensor 0.74 dB (0.75), build 1.75 dB (1.5). Peak-feature likelihood broader/biased and CANNOT identify sensor noise (posterior ~= prior). Tray 3*GRMS structural posterior 95% [1.011,1.052] g; future-build-flight predictive 95% [0.592,1.815] g / 99% [0.490,2.232] g. Peak/full structural QOI width ratio 5.77.
  - Artifacts: artifacts/reports/runner_claude_opus48_20260602/ (packet.md, results.json, nuts_diagnostics.{json,md}, assumptions_ledger.{md,json}, posterior_samples.npz, checks.json, 6 figures, full contract).
  - Lessons: peak/feature-summary likelihoods discard the per-frequency residual scatter needed to identify sensor-noise scale; report that as a finding, not a tuning bug. Flights that store only scalar 3*GRMS inform build effects, not structural curve shape. Inference model == data-generating model here, so recovery is optimistic; real model-form error would widen intervals.

## 2026-06-04 — Round 3 Stage 3 (Opus 4.8 inference, BLIND, structure-aware fix)
Workspace runs/round3/opus48/. Built the three fixes the prior blind failure pointed to and ran BLIND vs
Codex's re-published independent truth (canonical netCG contract). Result (honest, mixed):
- Per-strut ASYMMETRIC forward (fix #1) ALONE CONVERGES: rank-split R-hat 1.009, bulk ESS 487, 0 div;
  k_pop 1.685e7 near nominal. Real gain over the prior blind non-convergence.
- Structure/property-based per-strut discrepancy (fix #2) does NOT resolve the ridge -> CONFOUNDED with the
  per-strut stiffness -> INTRODUCES a parameter<->discrepancy ridge; with-d FAILS gate (R-hat 2.85). No
  "NUTS active" claim for with-d.
- FBS netCG contract (fix #3) cut bias 4.86x -> 1.71x(with-d)/3.10x(without-d converged); f->0 limit exact.
- sigma_e ~2x inflated either way = MISSING HIGHER MODES dominate (Stage-4 higher-fidelity FEM is the fix).
Artifacts: report/packet_stage3.md, packet.pptx, manifest.json, blind3_*.json/npz, figures/blind3_*.png.
Active runtime ~8700s (incl. exploratory/killed restarts); see report/runtime.json.

## 2026-06-10 — statFEM Part 2 (FABLE): frequency-domain extension
- Workspace: runs/statfem_freq_2026-06-10/fable/part2/ ; replay: part2/run_all.sh
  (993 s; checker GREEN, exit 0). NUTS all-green over 5 cases (worst R-hat 1.003,
  min ESS 1143, div 0.15%).
- Design: fixed-free rod stepped-sine response; FE model (10 elem, Rayleigh 3%) vs
  truth (60 elem + unmodeled 50 Hz tip resonator + hysteretic eta=0.04 + 0.85x load);
  y = complex phasors at 2 sensors, 99 freqs, 8 sweeps; w=(rho, sigma_d, ell_d).
- KEY FINDING for the program: under peaky dynamic model-form error the discrepancy
  GP absorbs the FE physics -> rho deflates 0.85->0.29 (control with truth=FE recovers
  0.847). Scalar-rho "model confidence" is NOT interpretable on FRF-like data; a
  stationary frequency kernel also globalizes localized error (flat predictive bands).
  Discrepancy estimate DOES localize model error at the true modes. Full report:
  runs/statfem_freq_2026-06-10/fable/part2/report/part2_report.md

## 2026-06-11 MPL stand scrappy modal test — scan + feature extraction (lead-as-runner)
- Data: 13 CSVs `MPL test stand/FEM/test_data/` (1 ch KS78C ±100g, 10 kHz, out-of-plane axis;
  1 broken-cable file deleted per Andrew). Scan/feature outputs + figures in
  `MPL test stand/FEM/test_data_scan_20260611/` (run_mapping.md = file↔location map w/ Andrew's
  A1-A7; features.md/.json). Scripts: mpl_event_scan.py, mpl_event_zoom.py, mpl_feature_extract.py.
- Ruler: solo f1 3.196 Hz ζ 0.31%, re-clamp 3.196/0.24%; coupled (shield top-center) 3.078 Hz
  ζ 0.27% → coupled shift −3.7% (Welch −7.7% was resolution error; zero-crossing authoritative).
- Saturated drive hits dropped (unloaded-top 24.6 s @ 916 m/s² ≈ rail; top-left-beam 47.1+61.4 s).
- Coupled tappers FLAGGED (accel on ruler tip = ruler-path filtered). Valve acoustic SNR weak.
- NOT a sampler/calibration run; features only. Next: fable FEM rebuild, then train/held-out split.

## 2026-06-11 — MPL stand parametric FEM rebuild (runner: FABLE, lead session)
- Workspace: `artifacts/reports/mpl_stand_fem_rebuild_20260611/`; replay `bash run_all.sh` (241 s); checker OVERALL YELLOW (15 green / 3 yellow / 0 red), exit 0.
- Parsed `Test Stand FEA.dat` (fixed-width, all counts match); discovered PSHELL39 = thrust plate, shield absent → added shield (1.7 mm CONFIRMED, vertical ⊥ thrust, Andrew live) + 3 QOI mounted masses + PSU from photos (all ESTIMATED → yellow).
- Element library validated 9/9 vs closed forms BEFORE the model; free-free gate caught a real drilling-DOF bug (5 RBM → fixed with relative K6ROT-style penalty → 6 RBM exact).
- Nominal 189 modes ≤500 Hz (f1 14.34); no-shield 77; mass closure exact 584.8 lbm; SE identifiability + KE region per mode; interface grids 800071 (shield top-center) / 670 (top-rail back wall); 15 mode GIFs + 5 figures (tufte-linted, QA pass).
- No sampler run (card scope); K(θ)=Σ s_g K_g groups saved sampler-ready in `out/model/`.
- Rev 2 (same day): Andrew round-2 answers (valve panel bolted to stand base → 28 lbm whole assembly; shield WELDED 'a few points' → weld springs ×10; 'probably steel') folded into estimates.py; full replay rerun; checker still YELLOW 15/3/0 exit 0; nominal now 185 modes ≤500 Hz, mode 1 = valve rocking 14.57 Hz, first shield mode 14.92 Hz; packet rev-2 with updated tables + plain-words clamp question.
- Rev 3 (same day): Andrew round-3 + new photos (IMG_9849-9854): silver "PSU" = THE electronics box (double-count merged, 10 lbm est.), mounted ON the shield over the LabJack sticker w/ 3 bolts → mode 1 = box-on-panel 11.9 Hz; beam mount → leftmost vertical post grid 1510; valve assembly on the flat bottom plate (not in deck, flagged). Fixed no-shield variant floating-box 0 Hz artifact (Table B = 71 modes). Checker YELLOW 15/3/0 exit 0.

## 2026-06-11 — 7004C multi-point/6-DOF teaching study (lead-as-runner, Claude Code)
- Workspace: `artifacts/reports/notch_multipoint_7004c_20260611/`; replay `bash run_all.sh` (34 s); checker OVERALL YELLOW (20 green / 2 yellow / 0 red), exit 0; deliverables packet.md + 13 figures + 3 GIFs + 14-slide PPTX. No sampler (deterministic study, D1). No measured data; "flight" = labeled hypothetical coupled sim.
- EX-A: replicated 7004C Fig 8/9 + Appendix B to 0.86% worst over 10 anchors (worst = handbook's own rounding of 1.62²); impedance method == direct coupled solve at 1e-14; scalar force limiting brings test peak to 1.00× flight peak.
- EX-B: 6×6 interface apparent-mass matrix (ω→0 = exact rigid matrix; modes = closed form 2e-16; rotary effective-mass sums 3e-16); resultant trap: net Fz exactly 0 at the 148-Hz rocking mode while per-foot = 9.8 N, |My| = 3.5 N·m.
- EX-C (7 plate/feet/damping variants): notch becomes a shifted CLUSTER (−11..+6%) split across mean vs differential interface channels; visibility = modal-overlap regime (MOF<1 global to plate boundary; MOF≳1 r≈λ/4); rocking notches more local, sometimes invisible in point spectra; convergence: f_notch <0.5%, area-frac <1.4 pts under 2× modal refinement (r_vis threshold-sensitive → documented yellow).
- EX-D: net-force limiting (7004C p.10 default) fixes bounce (204×→5× PSD) but leaves 221× (23 dB) per-foot rocking overtest; §5.8-style moment limit → 32×; roll channel exact-zero undertest. Newton checks 4e-15; C² semi-emp 3.72 vs flight-implied 0.87.
- Mid-run method corrections logged (D8/D9): ratio-based notch detection (bare-plate antiresonances polluted v1), anchored cluster selection (deepest-min flipped under refinement), EX-A test frame = enveloped flight accel, EX-D band-spill fix (93.1/94.1 Hz modes inseparable by band metrics).
- Rev 4 (same day, D34): Andrew gave box mass as "2-4 lb" → made it a LogNormal PRIOR (priors.py, 95%=[2,4]) + prior-predictive forward push (prior_predictive.py, NO sampler). Honest identifiability finding: box owns no clean mode at 2-4 lb (energy veers across 17-45 Hz shield cluster; f1 is valve-dominated, ~0.7 Hz shift over the whole prior, box/valve mass confounded) → next-card lever = sensor on the box. New fig_prior_predictive.png. Checker 16/3/0 exit 0. This is the bridge artifact to the NUTS posterior-update card.

## 2026-06-12 — 7004C study EX-E added: empirical reconstruction without a coupled FEM (lead, Claude Code)
- Same workspace `artifacts/reports/notch_multipoint_7004c_20260611/`; full replay `bash run_all.sh` (42 s); checker now OVERALL YELLOW (24 green / 2 yellow / 0 red), exit 0. No sampler (D1). Andrew directive D10/D11.
- EX-E (`code/ex_e_empirical_reconstruction.py`): tests whether the 7004C impedance method (Eq 3/4) with MEASURED interface quantities can replace a coupled forced FEM. Truth = full coupled plate+payload solve.
- FULL 4-foot matrix impedance reconstruction == coupled truth to 1.8e-12 (verification): a measurement genuinely replaces the coupled solve.
- Sparsity is the cost (soft/low-overlap band-peak errors): single-point/1-foot → moment err 100% (predicts 0), per-foot 76-84% (resultant trap quantified); rigid-3 (≥3 spaced feet) → per-foot 3-5%, moment 0-17% (rocking recovered); diagonal/feet-independent → erratic; full → exact. Rigid-3 degrades at high freq (feet warp/decouple).
- Remote response proxy (1-3 foot-spacings): transmissibility-based limiting exact for a linear system if calibrated IN the integrated config (any distance in visibility regime); bare-config calibration ~100% wrong broadband (payload shifts every backing mode).
- Deliverables for future agents: `notching_findings_for_future_agents.md` (standing reference synthesizing EX-A..E + 7004C + project threads + practical recipe + open Qs) and `lit_review_prompt.md` (self-contained agent prompt for a force/response-limiting + FBS + FTO literature review). 3 new figures (fig_e1/e2/e3); +2 PPTX slides (16 total).

## 2026-06-12 — Notch literature review: multi-point / empirical force- and response-limiting
- Workspace: `artifacts/reports/notch_lit_review_20260612/`; checker `python3 check_review.py`
  reports OVERALL YELLOW (26 green / 1 yellow / 0 red), exit 0. The only yellow is documented
  limited-access source coverage; no fabricated/unverified citation marker.
- Deliverables: `lit_review.md` organized A-H; `bibliography.md`; `novelty_and_fto_notes.md`
  including US8731868B2; `gaps_and_next_experiments.md`; `decisions_log.md`; `priority_deliverables.md`;
  `checker_report.json`; `runtime.json`.
- Headline: generic impedance/FBS coupling, force limiting, response limiting, apparent mass,
  multi-component force/moment measurement, and TPA/blocked-force identification are crowded prior art.
  The likely-open BayesX contribution is narrower: sparse 6-DOF/multi-foot interface measurements,
  explicit net-resultant rocking blind-spot diagnostics, modal-overlap notch-reach rule, and Bayesian
  uncertainty/status-gated limit generation.
- IP caveat: not a legal FTO opinion. Disclose to Purdue/PRF IP officer before public sharing.

## 2026-06-12 — Forcing-marginalized amplitude-dependent damping toy
- Workspace: `artifacts/reports/forcing_marginalized_damping_toy_20260612/`; replay `bash run_all.sh`
  (runtime 13.48 s active, 16 s wall); checker OVERALL YELLOW (20 green / 2 yellow / 0 red), exit 0.
- Purpose: plumbing test for Andrew's question: can a primary/secondary digital twin learn damping-relevant
  information when the forcing function, nonlinear damping formulation, and model-form error are hidden?
- Truth: 3-DOF primary/secondary/hidden-rattler system; hidden complex force spectrum; amplitude-dependent
  slip-like joint damping and mild stiffness softening. Twin: 2-DOF primary/secondary model with inferred
  `zeta_low`, `zeta_high`, stiffness scales, and residual model-error scale.
- Key verification: force cancels in `T21 = a_secondary/a_primary`; hidden-force response-ratio error
  4.28e-16, so the likelihood never learns a force-function parameter.
- NUTS diagnostics: max R-hat 1.000, min ESS 3087, 0 divergences. Damping trend learned:
  P(`zeta_high > zeta_low`) = 0.996. Held-out clean log-ratio coverage 42/46 = 0.91; damping-dependent
  QOI coverage 6/6.
- Honest yellow: equivalent damping intervals miss the hidden physical damping values (low truth 0.0146
  vs interval [0.0148, 0.0562]; high truth 0.0499 vs [0.0532, 0.1057]) because the 2-DOF twin absorbs
  hidden-DOF/stiffness-softening error into damping and residual scale. This identifies equivalent
  damping/QOI behavior, not the Coulomb/microslip law.

## 2026-06-12 — Existing-dataset amplitude-dependent damping / hysteresis scan
- Workspace: `artifacts/reports/amplitude_dependent_damping_scan_20260612/`; replay
  `python3 scripts/scan_amplitude_dependence.py && python3 check_scan.py` from the workspace
  (runtime 3.36 s active); checker OVERALL YELLOW (18 green / 1 yellow / 0 red), exit 0.
- Human ask: do ShockSat, MPL test stand, or suspended-panel datasets show signs of
  amplitude-dependent damping or hysteresis?
- MPL: YELLOW weak signs present. Response-only ruler pull-release screen finds small harmonic
  content consistently larger in the high-amplitude part of decay; coupled-ruler damping/frequency
  shifts are modest (high zeta 0.290%, low zeta 0.357%, high-low frequency shift -0.14%).
  Not a calibrated hysteresis loop because no force/displacement loop was measured.
- ShockSat: YELLOW inconclusive. Test07 hammer has four force-contrast hits (0.718-1.33 lbf,
  max/min 1.85), but selected-channel median coherence is only ~0.054-0.056 over 100-10,000 Hz
  and source/response mapping is unresolved, so per-hit FRF differences are not trustworthy
  nonlinear damping evidence.
- Suspended panel: YELLOW inconclusive. `H1.mat` is 25 response points x 3200 frequency lines
  over 0.125-400 Hz, but no repeated drive-amplitude levels or raw time histories were identified.
- Next measurement: purpose-built amplitude sweep with force/displacement or force/velocity
  loops for MPL; mapped high-coherence hammer/modal sweep for ShockSat; multi-level LDV sweep
  for the suspended panel.
- Rev 5 (D35/D36): deleted 3 stale gif sets (filenames embed freq → reruns accumulated; make_gifs now wipes gifs/ each run). The "symmetric panel modes despite off-center box" Andrew flagged were from an OLD gif set; symmetry diagnostic confirms current shapes carry the off-center mass (shield X-asymmetry index 0.013@0lb → 0.141@3lb → 0.66@30lb; degenerate pairs split). Mirrored valve+e-box to the correct y-side and lowered e-box (CG z 41.5→28) per Andrew; checker 16/3/0 exit 0; mode 1 shield 14.07 Hz. Item positions ANDREW-CONFIRM via fig_geometry.
- Rev 6 (D37): white box co-located behind e-box (same y-z ~(-10.5,33)), both raised; valve y -16→-12 (all per Andrew). Caught + fixed a self-inflicted RED: the box mode now crosses the fundamental near 2-2.5 lb, so the 1/f² prior-predictive fit residual hit 0.12>0.10 → switched forward map to direct monotone interpolation, gate now on physical f1-monotonicity (violation 0.0). Checker 16/3/0 exit 0. Lesson: don't gate a veering-affected forward map on parametric-fit prettiness; gate the physics (monotonicity by interlacing).
- Rev 7 (D38): valve assembly upgraded to a higher-fidelity 80/20 aluminum frame (1515 T-slot, 16 nodes/28 Timoshenko beams + 16 lb tanks/valves lumped + 4-corner bolt; new valve_frame.py + groups K_valveframe/valve_mount/M_valveframe/valvemass). Valve modes move 14 Hz (spurious rigid-rock artifact) → 156/190 Hz (real frame flexure). Extrusion series (1515 assumed) = dominant new knob, ANDREW-CONFIRM. Mass closure exact (independent geometry recompute), 6 RBM, 0 neg; checker 16/3/0 exit 0. Replay ~7 min (heavy concurrent load from another session's git add + statFEM runs made several replays this session slow).
- Rev 8 (D39): pseudo-FRF FEM-vs-test overlay at 3 key locations (no force -> peak-freq-only pseudo-FRF, assumed 1-3% damping, log-mag/log-f standard view, NO sampler). Uncalibrated rev-7 prior matches measured peaks <1% in 50-90 Hz (55.6/66.1/78.4/88.9 Hz) at all 3 locations; consistent ~5-10% low-band (10-25 Hz) offset = estimated box/shield masses + weld stiffness (the yellow knobs). Sharp common ~147/240 Hz acoustic content flagged as speaker/room/mains-or-global. Checker 16/4/0. src/pseudo_frf.py + src/make_pseudo_frf_fig.py + fig_pseudo_frf.png + packet §6b.
- Rev 8 figure revised per Andrew: split the busy 3-curve+comb panel into 6 SEPARATE graphs (3 response locations x {drive-point tap, acoustic}), each exactly 2 curves (FEM vs test), removed the FEM mode comb ("ticks"), clean 2-item legend, no tick marks. fig_pseudo_frf.png (grid) + figures/pseudo_frf/*.png (6 individual). Transfer-FRF combos (tap at A, accel at B) available if wanted; delivered drive-point+acoustic set.
- Rev 8b (D40, Andrew): (1) TAP TRANSFER matrix added — 3x3 (response x tap location among interface/shield-mid/top-left), FEM transfer accelerance H_BA vs test, apples-to-apples (tap=point force). (2) ACOUSTIC made apples-to-apples: FEM now uses a MODELED uniform-shield-pressure forcing (normal-incidence plane wave, low-freq valid, flagged) instead of drive-point accelerance — Andrew's correct point that we weren't applying an acoustic forcing function. (3) SATURATION-WINDOW BUG fixed (Andrew caught): the 6s window on the 20.4s top-center tap swallowed the 24.6s saturated 93g hit; now windows capped before next event + near-rail (>90g) windows rejected -> interface drive-point spectrum clean. Figures: fig_pseudo_frf_transfer.png (3x3) + fig_pseudo_frf_acoustic.png (1x3) + individuals; checker 16/4/0; packet §6b.
- Rev 8c (D41, Andrew): added the QOI-point pseudo-FRFs that were missing — valve (accel on the 80/20 frame, tap @ engine beam + acoustic) and electronics-box FEET (left+right avi-foot files, tap @ engine beam + acoustic). These directly test the higher-fidelity mounted-mass models. fig_pseudo_frf_qoi.png (3x2). Caveats: held-out records; box BODY/top not measured (cable broke) so feet only (both -> rigid-box CONM2 node = repeatability check); valve acoustic weak (RMS 0.019, low SNR); valve's own frame modes 156/190 Hz are above the 5-90 Hz band so this tests the path more than the QOI resonance. Checker 16/4/0.
- Rev 9 (D42/D43, Andrew): DETERMINISTIC FE model updating (point estimate, NOT NUTS/posterior) tuning to the box-foot tap-transfer ONLY, goal set up front, change log kept (tuning_changelog.md). Phase A first: added engine-beam+foot tap columns (foot honestly flagged degenerate under SPC'd feet = model-form gap) + extended valve QOI to 250 Hz (shows the 156/190 Hz frame modes). Phase B tuning: box-foot median |Δf| 6.13%->2.21%, matched 2/4->3/4, held-out stable 8.0% (no overfit). Model-form change D43 = split box mount into separate trans+rot springs -> added the ~27 Hz box rocking mode (matched measured 26.8). MEDIAN goal (<=3%) MET; full 4/4 NOT met = documented 11.4 Hz model-form floor (closing it needs box>4lb above prior or softening confirmed 1.7mm shield -> DECLINED as overfit; honest model-form error for the Bayesian next card). Coordinate-descent tune_correlation.py (~25min, on-demand, detached) + finalize_tuning.py (in replay) + fig_tuning_box_foot.png + check gate. Checker 16g/5y/0r. KEY LESSON: deterministic tuning hit a model-form floor and tried to compensate by pushing box mass below its physical prior = exactly the overfit the robust/Bayesian approach guards against.

## 2026-07-02 — Composite bake-off (agentic remodel × MAC-in-likelihood × Beck × statFEM F(k))
Workspace `artifacts/reports/shocksat_composite_bakeoff_20260702/`; replay `bash run_all.sh`; checker SHA-locked
BEFORE science (`CHECKER.sha256`). **Checker OVERALL YELLOW (57G/6Y/0R, exit 0)** — the 6 YELLOW = Beck-S2
net-CG coverage misses (documented findings). Full pre-registered 2×3 matrix M{0,1}×S{0,1,2} + F(k); all 6 arms
NUTS-CONVERGED (R-hat ≤1.0011, ESS ≥580, 0 div). Funnel: 151 candidates → 29 full 399k-DOF eigensolves → 10
evidence classes → 1 M1 (`rand10`).
- **Agentic remodeling did NOT earn delivery (pre-registered claim FALSIFIED):** `rand10` won shape-inclusive
  evidence +54 logZ (P=0.72, prior-robust top) but did NOT beat M0 on held-out R1/R2 → R4 reports-not-delivers.
- **Evidence≠held-out = central methodological result.** Freq-only evidence would crown the same candidate
  (MAC block didn't re-rank on this data) — forbidden-selector rule sound in principle, didn't bite here.
- **MAC-as-θ (S1) ~NULL again** at the QOI level (reproduces modelclass_L5 §3a); S1≈S0.
- **Beck (S2) per-point amplitude CHAMPION** (R1 −0.34/−0.37 vs −0.71…−0.78; σ 0.89 vs 1.08) **but confident
  shapes don't transfer to the net-CG band** (R2 under-covers). On the arm-independent held-out-DRIVE key Beck
  covers shear_X 1.00 (shear miss partly a FEM-shape-reference artifact); normal has no data key → unsafe.
- **DELIVERED = inherited FEM + freq(+MAC) + statFEM F(k)** both QOIs = REAFFIRMS the proven netcg twin.
- Integrity: both metric traps encoded+clean; full in-band mode set, all 5 drives; M0S0 R3-DQ = marginal
  threshold artifact (normal widen 1.01<1.03 but still covers 0.993 after hiding). Sampler incident D11: S1
  freq+MAC hung ~2h on the 246-258 Hz degenerate-cluster eigenvector gradient (A7) → fixed with a Tikhonov-
  regularized first-order shape derivative (25s, converged). Recovered from 1 computer crash mid tier-2
  (11/29 eigensolve packages preserved; resumable). runtime.json: active 8150s, wallclock 20079s.

## 2026-07-08 — shocksat_true_remodel_loop_20260706 (TRUE agentic remodeling loop, vault-scored)
- **Checker status (verbatim): OVERALL: YELLOW {GREEN: 11, YELLOW: 1, RED: 0}; the 1 YELLOW =
  "s1_s2_s3_verdicts: pre-registered claim FALSIFIED (honest outcome)". Exit 0.**
- One question, one run: closed-loop SHAPE-CHANGING remodeling (true refinement / splits / t-t³ thickness /
  RBE2→spring compliance) vs inherited FEM + equal-budget random search, 3-tier protocol (train / budgeted
  dev LODO / vault Test04 touched once after SHA freeze). RESULT: S1 fail (best shape margin +0.022 < +0.05),
  S2 fail (agent 0.2376 vs random 0.2389 — tie within noise), S3 fail (shear coverage). Mechanisms: θ-wobble
  dominates FRF ranking; reduced-basis score inflation + θ_MAP basin lottery both caught pre-vault by
  pre-registered gates; better .ash fit ⇒ worse held-out FRF (dev AND vault). V1-V5 mechanics all PASS;
  NUTS all-converged (worst R-hat 1.004); budgets respected (41/60, 57/60; 62 eigensolves).
- Workspace: artifacts/reports/shocksat_true_remodel_loop_20260706/ (packet.md, findings.md, verdicts.json,
  decisions_log D0-D23). Replay: bash run_all.sh.

## 2026-07-10 — shocksat_frf_damping_updating_20260710 (FRF-domain DAMPING updating, vault-scored)
- **Checker status (verbatim): OVERALL: YELLOW {GREEN: 19, YELLOW: 2, RED: 0}; YELLOWs = (1)
  "s1_s2_s3_s4_verdicts: pre-registered claim FALSIFIED (honest outcome): S1 FAIL; S2 FAIL; S3 FAIL; S4 FAIL";
  (2) "nuts_finalists: non-converged finalist A0_enr (R-hat 24.8, ESS 2) — theta multimodality/under-
  identification (D19), intervals not-trustworthy". Exit 0.** Checker SHA-locked BEFORE science, never touched.
- Successor to the true-remodel loop: same ShockSat, same 3-tier protocol, but the RIGHT levers — a genuine
  DAMPING action space (band zeta / Rayleigh / per-joint structural loss factor eta via strain-energy-weighted
  composite) + FDAC frequency-shift alignment + FDAC-aligned FRAC metric (P1'), tested vs A0, a fitted damping
  baseline A0d, and equal-budget random. RESULT: S1 FAIL (dev winner a04 shape +0.037 < +0.05, << 2xfold-SE
  0.262), S2 FAIL (random 0.239 > agent 0.234), S3 FAIL (net-CG shear coverage 0.70 < 0.95), **S4 FAIL
  (damping_share -0.105 => "improvement is shape/theta; DAMPING lever unproven"; A0d 0.193 BELOW A0 0.197).**
- MECHANISM (the durable contribution — the damping lever every prior thread flagged, now TESTED and closed):
  the 2 Hz distilled FRFs cannot resolve ShockSat's light damping (survey zeta ~0.3%, half-power bands <=~1
  frequency line; Gate D2: 27% per-mode zeta error). Fitting damping fits the peak-sampling ALIASING => zeta
  railed to 1.5-2.5% (MAP) / 5% gate ceiling (NUTS, ALL finalists), and does not generalize. FDAC global
  alignment gain ~-0.01 (theta_MAP already aligns => the completed run's null is NOT a misalignment artifact;
  control: +0.31 on a synthetic 5% shift, Gate F). Gate O: 93% of measured shape content reachable (not gross-
  unobservable) but sensor set aliases some mode pairs (self-MAC 0.997, Fisher rank 36/40).
- Integrity: V1-V5 mechanics all PASS (blocks bit-exact, eig 1.15e-9); damping physics D1 + metrics F +
  identifiability D2 + observability O all GREEN; exact-basis freeze set (reused _enr packages, spot-check
  ~1e-7); no per-mode/channel amplitude-or-damping LSQ (grep-clean); physical-damping gate held (all finalists
  in [0.2%,5%], eta<=0.2, none disqualified, dim<=10); budgets agent 21/60 random 40/60; vault (+XY) graded
  ONCE after SHA freeze = uniform +0.22..+0.30 dev->vault location effect (no candidate win). CROSS-VALIDATION:
  A0_enr raw P3 0.2152 == the true-remodel run's exact-basis A0. NUTS: a04 (R-hat 1.002/ESS 792) + c06
  (1.005/423) CONVERGED; A0 multimodal (reproduced under Uniform-zeta => not a param artifact). Runtime active
  = elapsed 8722.7 s (~2.4 h; eigensolves + NUTS detached/parallel).
- Reco (human replace/keep/buy-data decision): KEEP inherited twin; to use damping for FRF-amplitude
  correlation, BUY finer frequency resolution (re-distill NASA raw time histories to resolve the half-power
  bands) — not more modeling. The true-remodel run STANDS unchanged; MPL test stand = natural follow-on.
- Workspace: artifacts/reports/shocksat_frf_damping_updating_20260710/ (packet.md, findings.md, verdicts.json,
  decisions_log D0-D12). Replay: bash run_all.sh.

## 2026-07-13 — ShockSat RESOLUTION-CONSISTENT FRF scoring (window-matched model + physical damping, B0-B5)
- **Checker verbatim: OVERALL RED {GREEN: 23, YELLOW: 2, RED: 1}, exit 1.** The RED = Gate W (raw-data window
  verification) FAILED at its pre-registered thresholds; YELLOWs = (1) "S1_margin_rule: PRE-REGISTERED CLAIM
  FALSIFIED (honest outcome): dP1'=+0.0401 vs need >=+0.03 & >=2xSE(0.0263) & vault_B2_gt_B0=True";
  (2) "S3_mechanism: mechanism NOT confirmed (documented finding): B2-B1=+0.0526 (need >=+0.02), gateW=False".
  Every integrity/pipeline gate GREEN. Checker SHA-locked before science, verified unmodified. NO-SAMPLER
  study (deterministic arms, reused theta_MAP), declared per the Sampler Decision rule.
- RESULT: window-matched + physical survey zeta (B2) beats the incumbent naive+1% (B0) +0.0401 dev P1'
  (0.197->0.237; folds +X +0.012 / +Z +0.111 / +Y -0.010 / +Z@900 +0.048), vault direction confirmed
  (0.420->0.473, SECOND read of +XY, labeled) — but below the 2x fold-SE noise bar (0.053) => S1 falsified.
  S2 attribution: window-alone +0.033, damping-alone -0.013, interaction +0.019 => THE GAIN IS THE WINDOW;
  once matched, survey vs ERA vs flat-1% damping differ by less than fold noise.
- DATA DISCOVERY: Test07 raw impact series has a DEAD FORCE CHANNEL in all 4 hits (~1 lb noise vs 1000-1900 g
  responses at ~0.5 s) => the card's direct H1-recompute is physically impossible; retro-explains the
  2026-06-09 "Test07 low coherence" blocker. Gate W's force-free fallback (D8, dated contract addendum) also
  missed thresholds (hit-consistency 0.090 dex vs 0.05; apparent-zeta ratio 1.88 vs 1.25) -> D9: FAIL accepted,
  no third re-basing (threshold-shopping refused). Evidence short of certification, all in gate_W.json:
  distiller source FOUND (exp window end=0.05, N=122880@250kHz; realfrf.measured_zeta_w documents its own
  added damping); Gate K synthetic operator error <=2%; ISOLATED peaks agree +-15% on stored cache AND raw;
  no peak narrower than predicted; Test01<->Test07 shape corr 0.834.
- MECHANISM (working understanding, uncertified): the exp window adds zeta_w(f)=1/(2 pi f tau), tau=0.164 s
  => apparent zeta 1.6%@60Hz..0.4%@250Hz on every mode; flat-1% "worked" because it approximates that curve.
  Windowed forward implemented EXACTLY (closed-form geometric sums; reduces analytically to the naive FRF).
- Gate R: B0 reproduces the damping run's frozen A0_enr dev P1' to 1.6e-7 (bit-level continuity); B1<B0.
- Ops: disk hit 100% mid-run -> D7 streaming extract->process->delete (no .mat persists); Gate K's card
  assumption corrected (D6: exp window, not Hann — a 5% peak drops 16%, reported).
- RECO (Andrew's call): treat 2 Hz cache peak widths as WINDOW, not damping; the one cheap decisive follow-up
  = re-download ONE modal-hammer raw series WITH live force (Test01/02 class) -> direct Gate W + longer-frame
  re-distillation could certify the +0.04. Otherwise the damping arc is closed; MPL next.
- Workspace: artifacts/reports/shocksat_resolution_consistent_scoring_20260713/ (packet.md, findings.md,
  out/verdicts.json, out/gate_{W,K,R}.json, decisions D0-D9). Replay: bash run_all.sh.

## 2026-07-14/15 — ShockSat FULL-SPECTRUM FRF (amplitude-trained updating + remodel + extended band)
- Checker OVERALL **YELLOW** (11G/1Y/0R, exit 0); 1 YELLOW = arm-B/C NUTS non-converged (multimodal,
  R-hat 29-360, ESS~2, reported not-trustworthy, scored at deterministic MAPs). All S1-S5 YELLOW
  (falsified/not-met = valid pre-registered outcome). Checker SHA-locked before science, verified unmodified.
- DATA (durable): all 5 raw modal-hammer drives re-distilled wide-band, validated BIT-IDENTICALLY vs existing
  caches WITH LIVE FORCE -> closes the resolution run's Gate W. FEM twin credible only ~640 Hz (dense local
  modes; 1250 Hz infeasible on 16 GB CPU) -> FRF scoring capped 500 Hz; 500-1000 band FEM/compute-limited.
- METHOD: no lever cleanly beats A1 sub-200 at the noise floor. S1 falsified (C +0.044<0.05/2SE, collapses on
  exact basis). S2 NOT MET (agent ties random on the exact-at-θ_MAP re-eval that OVERTURNED a screening
  +0.0138 -> D22 reduced-basis inflation; vault agrees) = H2 impotence CONFIRMED with the compass. S5 not met
  (selection vs held-out Spearman -0.3). S3/S4 not validly assessable (QOI reimplementation miscalibrated vs
  delivered bands; delivered twin stands). Amplitude-θ + remodel help 200-500 (+0.11..+0.16), not sub-200.
- FIM (sampler-independent): arm-B non-convergence is MULTIMODALITY not under-identification (all 9 θ combos
  >> prior precision at 0.73 dex floor). TMCMC/GPU not used (compute protocol).
- Deliverable UNCHANGED: inherited FEM + statFEM twin. Reco: a machine that solves the FEM to ~1250 Hz is the
  pre-test lever to actually use the >500 Hz data already in hand.
- Workspace: artifacts/reports/shocksat_full_spectrum_frf_20260714/ (packet.md, findings.md, out/verdicts.json,
  out/exact_freeze_scores.json, out/identifiability.json, decisions D0-D15). Replay: bash run_all.sh.

## 2026-07-16 — GPT-5.6 adversarial review of ShockSat FULL-SPECTRUM FRF
- Review status **RED**: original package has four blocking findings. G09 accepted NaN S1/S2 statistics, null exact fold SE, and a post-hoc F=R row; arm C's exact aggregate reuses one fold MAP and leaks 3/4 held-out drives; local FIM rank does not prove global "not under-identified"; failed net-CG reproduction leaves S3/S4 CANNOT-VERIFY, not falsified. Andrew authorized an isolated repair; repair checker **OVERALL YELLOW** (7G/1Y/0R), finite S1 D−A1=+0.049671 and S2 D−R=−0.001716, F=C, original inputs unchanged. Correct status: S1/S2/S5 not met; S3/S4 unresolved. Review replay: `bash artifacts/reports/shocksat_fullspec_review_gpt56_20260716/run_all.sh`. Workspaces: `shocksat_fullspec_review_gpt56_20260716/`, `shocksat_full_spectrum_frf_repair_20260716/`.

## 2026-07-16 — GPT-5.6 adversarial review of the full-spectrum study: ACCEPTED, original package RED
- Review workspace shocksat_fullspec_review_gpt56_20260716 (commit 9cad98c); isolated repair
  shocksat_full_spectrum_frf_repair_20260716. Lead verified C6/C8 directly and accepts RED:
  NaN S1/S2 in shipped verdicts.json + invalid F=R (checker G09 validated presence not finiteness);
  arm-C exact aggregate leaked 3/4 folds (fold-1 shape MAP reused; withdrawn); local-FIM identifiability
  claim over-reached; S3/S4 = CANNOT-VERIFY not "not-met"; "closes Gate W" softened (equality by
  construction). SURVIVES per repair: S1 not met (+0.0497<0.05, >2×SE), S2 not met (−0.0017±0.0094),
  S5 not met (fragile across priors); data provenance/force health; 500 Hz FEM cap.
- Corrections issued as dated addenda (findings.md/packet.md tops); D17. Queued: arm-C per-fold exact
  refits (~0.5-2 CPU-h), corrected arms figure, model-form pilot design (review's next_steps.md).

## 2026-07-16 — VALIDATED net-CG QOI PORT (post-review item 4): S3/S4 made assessable; delivered twin stands
- Workspace `artifacts/reports/shocksat_netcg_validated_port_20260716/` (commit 9cad98c). Replay
  `bash run_all.sh` (active 96.79 s, Mac CPU float64). Checker SHA-locked `e235e9fc…`, proven RED on the
  empty workspace first (10/10), never edited. NO sampler: L5 NUTS posterior = REUSED cached draws.
- **GATE N0 PASS EXACTLY**: driving the ORIGINAL netcg_qoi.py + its reduced model + the reused L5 θ posterior
  reproduces the delivered twin to **1.508 / 2.301 / 2.526, max |err| 0.0000** (tol 0.05). The reference is
  reproducible → **S3/S4 are assessable for the first time** (they were CANNOT-VERIFY per review C5/D17).
- **C5 root cause CORRECTED (pre-registered as D3 before running).** The study's CAVEAT blamed "a
  marginal-calibration difference in the reimplemented statFEM F(k)". It is a **QUANTITY-CONTRACT
  divergence**: on the IDENTICAL lo/hi arrays of the IDENTICAL delivered band, netcg's convention =
  **1.508**, the study's `netcg_wide.band_width_ratio` = **21.660** (an upper/lower ENVELOPE ratio that never
  references the FEM+6 dB denominator). No calibration could reconcile them. Two further real divergences:
  the study's statFEM marginal form differs, and its band uses a single θ → θ uncertainty absent entirely.
- **N1 bridge:** the study's θ_MAP point explains **~0%** of its width gap (moves shear_X +0.21; moves
  shear_Y/normal_Z the WRONG way −0.45/−0.45; residual not explained by θ = 6.5/2.9/3.4). The gap is the
  reimplementation, not the θ point.
- **S4 = NOT MET (YELLOW), falsified along the path A5b pre-registered on 07-14.** Exactly ONE extended-band
  cluster mode matches in 45–260 Hz (measured 254.3 ↔ FEM 254.9 Hz, 0.2%). Its OBSERVED cross-drive
  ln-amplitude scatter **1.393 > the 0.80** the twin already assumed for an unmeasured mode → measuring it
  made it MORE uncertain → normal-Z **widens 2.526×→2.958×** (+0.432 vs 2σ MC noise 0.091 = real);
  coverage 0.989 passes, width fails ≤1.90×. **The delivered 2.526× normal twin stands (mildly optimistic).**
  Physical reason unchanged: 1 Z sensor ⇒ drumhead SHAPE unmeasured; frequency info cannot fix it.
- **S3 = CANNOT-VERIFY-through-this-mapping (YELLOW).** Self-caught defect in my OWN pre-registered mapping:
  per-mode amplitude ratios |g_X|/|g_A0| are INVALID because 18/44 adjacent in-band mode pairs are within 1%
  (near-degenerate subspaces ⇒ eigenvectors arbitrary up to rotation ⇒ per-mode participation not
  basis-invariant; median |ln a| = 2.31 for a modest stiffness edit; |g| dynamic range 7e4). Reported as 3
  variants (full / freq_only / cluster_amp); they DISAGREE under both raw and MC-significant readings ⇒
  CANNOT-VERIFY. Two findings survive: (1) freq_only shows NO effect above the 2σ MC floor (0.021) — the
  finalists' frequency changes do nothing; (2) **the RANDOM control R narrows shear_X as much as the agent
  arms** (1.339 vs 1.250/1.213) = a non-informative narrowing, independently reproducing the study's S2
  (agent ties random) in QOI space.
- Overconfidence audit under the DELIVERED machinery widens on every band (1.04–1.41) vs the study's inert
  reimplementation (shear_X 1.000, normal_Z 1.003) — the delivered machinery is humble where the
  reimplementation was not. Baseline held-out DEV coverage reproduces netcg's published numbers exactly
  (shear_X min 1.000, shear_Y min 0.596) = independent validation of the held-out reuse.
- VAULT: +XY never read (runtime np.load guard raises + checker grep; `xy_files_opened=0`); DEV drives only.
- **Checker OVERALL GREEN (10/10) = INTEGRITY ONLY — NOT "S3/S4 met" (D7).** The checker has no gate
  propagating the science verdicts into OVERALL; disclosed rather than fixed by editing a locked checker.
  Science: N0 GREEN, S3 YELLOW (cannot-verify), S4 YELLOW (not met).
- **NET FOR THE PROGRAM: the delivered net-CG twin (1.51×/2.30×/2.53×) STANDS UNCHANGED**, now as an
  ASSESSED conclusion on a reproduced reference rather than an unassessable one. If reopened: S3 needs a
  degeneracy-aware transport (MAC pairing on a common DOF space / subspace-level QOI); normal-Z needs
  SENSORS (the >200 Hz plate test), not more re-modelling.

## 2026-07-21 — ShockSat advisor results-summary revision

- Workspace: `artifacts/reports/shocksat_results_summary_20260721/`
- Deliverable: `ShockSat_results_summary_revised.docx` (original preserved unchanged).
- Replay: `bash run_revised.sh`.
- Checker: **OVERALL YELLOW 6G/1Y/0R, exit 0**. All six artifact/layout/reference gates GREEN; the YELLOW is
  the inherited science ceiling: no direct normal-force answer key, full-spectrum NUTS worst R-hat 360.6/min
  ESS about 2, and the evidence winner did not earn held-out delivery.
- Communication result: 15 pages/9 figures became 6 pages/2 single-story plots; exact comparisons are tables;
  decision/recommendation appears on page 1; nine references verified against NASA/publisher/DOI/ASME sources.
- QA: Tufte lint 0 heuristic flags; DOCX a11y 0 findings; exactly two embedded images with meaningful alt text;
  all six rendered pages manually GREEN. No inference, sampler, FEM fit, or scientific metric was recomputed.

## 2026-07-21 — ShockSat advisor progress-and-closure rewrite (supersedes the decision-memo framing)

- Workspace: `artifacts/reports/shocksat_results_summary_20260721/`.
- Current deliverable: `ShockSat_StatFEM_progress_and_closure_update.docx`; original and rejected six-page
  intermediate memo preserved. Replay: `bash run_advisor_progress.sh`.
- Checker: **OVERALL YELLOW 10G/1Y/0R, exit 0**. Ten document/context/method/agentic-remodeling/literature/
  figure/render gates GREEN. YELLOW is the science ceiling: no direct net-CG answer key; held-out modal and
  whole-FRF posterior families non-converged; agent did not beat equal-budget random.
- Audience correction: assumes Ilias knows only Bayesian FEM updating/statFEM and his prior evaluation objective.
  Removed `Decision requested`, traffic-light research tables, and undefined “honest shear-load” shorthand.
- Technical content: ShockSat testbed/data counts; intended statFEM equations; actual 9-stiffness modal likelihood,
  priors, inferred/fixed quantities; NUTS chain settings and diagnostics; explicit TMCMC non-result boundary;
  modal, sequential response, net-CG, FRF/damping, evidence, and model-form results.
- Closure content: explains why industry use was not earned, why model-form work followed, agent-vs-random result,
  candidate contributions and personal lessons, four advisor questions, and a proposed three-week closeout.
- Agentic-remodeling clarification: remeshing is one discrete operator family; continuous Bayesian parameters
  stay inside each model class. Section 7 now distinguishes existing candidate schemas/operators/builders,
  verifier gates, split/budget/hash discipline, controls, and exact scoring from the proposed `remodelctl` CLI.
  It separates hard verifier, TRAIN coach, restricted DEV grader, and one-time vault roles and pre-registers a
  no-feedback/pass-fail/structured-diagnostics comparison. The MPL scaffold is labeled infrastructure only,
  not an MPL posterior or remodeling result.
- References: 14 in-report references, 16-source verified ledger using NASA/publisher/DOI/primary pages. QA:
  a11y 0 findings; three inline figures with alt text; 13 rendered pages manually inspected; no traffic-light
  fills. One-command replay passed. Delivered SHA-256
  `a42cb103a791acac80656ea44d986953a5b77dfcaf97ed9063ff64c5375e24af`
  (DOCX package metadata means a rebuild can change the byte hash without changing rendered content).

## 2026-07-21 — ShockSat advisor Bayesian-method audit and comment resolution

- Workspace: `artifacts/reports/shocksat_results_summary_20260721/`.
- Current deliverable: `ShockSat_StatFEM_progress_and_closure_update_bayesian_audit.docx`; replay:
  `bash run_advisor_progress_bayesian_audit.sh`.
- Checker: **OVERALL YELLOW 11G/1Y/0R, exit 0**. Eleven artifact/content/assumption/figure/reference/render
  gates GREEN. YELLOW is the inherited science ceiling: no measured net-CG load; whole-FRF and Beck NUTS
  posteriors non-converged; their shown curves are leakage-safe deterministic MAP points.
- Input audit: preserved the four-comment Word file at SHA-256 `988833dc7034f1a11ebf84459e820d0171b9ad812a0ab383dc0fc1e3a13524da`;
  inspected/rendered the sole `experiment_catalog.xlsx` sheet, input SHA-256
  `e2d631ee54b3f587ea5f69413b058f660f8cccf6b4293c17af494d82f945199b`; reconciled it with later
  modal, whole-FRF, IFT, Schneider/Das, evidence, and model-form workspaces.
- New Bayesian-method table separates ten tested families by observables/likelihood, prior/discrepancy,
  computation/diagnostics, result, and claim limit. It highlights the converged modal-frequency NUTS result,
  converged ShockSat IFT TMCMC result, and the leakage-safe Beck shape reachability point fit without claiming
  that the failed Beck NUTS posterior is trustworthy.
- New held-out +X comparison uses a precommitted rule over 104 coherence-qualified channels. GOOD = DAQ 106:
  mean absolute log10-magnitude error 0.8165 to 0.6256. BAD = DAQ 24: best error 1.1925, about 16x in amplitude.
  Same data/grid and one-model-per-panel small multiples; plot Tufte lint 0 flags.
- Bayesian assumption audit explicitly checks prior scale, local Fisher information, feature information loss,
  iid versus correlated FRF covariance, parameter-discrepancy confounding, sampler geometry, spectral/damping
  resolution, parameter-span adequacy, and population variability before assigning model-form limitation.
- All four comments resolved: evaluation and validation defined, “real evaluation” explained, equations use
  true Word sub/superscripts, and band median versus separate plausible-truth median defined. Final DOCX has
  no comment markup, 17 numbered references/14 DOI entries, three described images, a11y 0 findings, and 14
  visually inspected pages. Delivered SHA-256 `145556925cce68c112b229843e3604124b0e0597064b584bf190ee047a804f30`.

## 2026-07-21 — ShockSat advisor prose recovery and FRF predictive-band revision

- Recovered every substantive direct Word edit by extracting the two editing-session revision IDs from the
  preserved draft. Restored the shorter opening and summary language, evaluation-versus-validation conclusion,
  Net-CG aggregation explanation, and agentic remeshing/remodeling wording. Replaced the user's ShockSat image
  placeholder with a sourced NASA NESC photograph and link.
- Rebuilt Section 5.4 from stored posterior artifacts. The modal column uses a 120-draw parameter-propagation
  envelope from the converged modal NUTS posterior (R-hat 1.022, ESS 232), explicitly not an FRF-calibrated
  predictive interval. The whole-FRF column uses a 120-draw pointwise posterior-predictive band including its
  fitted discrepancy/noise marginal variance, printed NOT TRUSTWORTHY because the +X posterior did not converge
  (R-hat 48.8, ESS 2.0). No Beck band was reconstructed because draws were not retained and its NUTS posterior
  failed (R-hat 13.95, ESS about 2).
- Replay: `bash artifacts/reports/shocksat_results_summary_20260721/run_advisor_progress_bayesian_audit.sh`.
  Tufte lint 0 flags; a11y 0 findings; all 15 rendered pages manually inspected. Checker **OVERALL YELLOW
  12G/1Y/0R, exit 0**. The YELLOW remains the scientific ceiling, not a document defect. Delivered DOCX
  SHA-256 `632362daf581e84d1c6e38da4df9cee0a9af4b184a129485415f1aed1ff3b535`.

## 2026-07-16 — EXACT-EVIDENCE COMPLETION for the full-spectrum FRF study (runner card A)
Workspace: `artifacts/reports/shocksat_fullspec_exact_completion_20260716/` · replay `bash run_all.sh`
**Checker OVERALL GREEN 12G/0Y/0R, exit 0.** SHA-locked (`4a01067c921e`) BEFORE any science, proven RED
science-not-run on the empty workspace, verified unmodified at the end. **NO SAMPLER** (deterministic MAP
refits + exact eigensolves only; no posterior claim). **No vault read.** active 7.48 h ≤ elapsed 7.72 h,
28 eigensolves (median 506 s).

Closed the 3 evidence holes review D17 left open:
- **T1 — honest arm-C exact (Q1 = "C DENTS").** 4 leakage-free per-fold shape-MAP refits on the enriched
  basis → sub-200 **0.1595**, delta vs A1-exact **+0.0458 ± 0.0361 → S1 NOT MET** (misses both +0.05 and
  2×SE=0.0722). Shape wall stands, dented, on valid provenance.
- **T2 — exact re-rank of ALL 28 (Q2 = agent ties random under BOTH conventions).** 28/28 scored, 0 excluded.
  Pipeline reproduces the study's exact D 0.1634 / R 0.1651 to **0.0000**. S2 (a) screening-selected
  −0.0017 ± 0.0094 (reproduces the repair exactly); (b) exact-selected **+0.0115 ± 0.0158** → NOT MET
  (0.73×SE). **H2 impotence now stands on firmer ground**: not "2 winners tie" but "best of 14 agent does not
  beat best of 14 random on the trusted basis."
- **T3 — finiteness-hardened verdicts + 2 corrected figures** (no F=R row; R-hat 360.6/ESS 2.0 on every
  MAP-derived bar; 3 rounds of legibility rework before passing my visual QA).

**TWO NEW FINDINGS THE REVIEW MISSED (D2):** (1) the study's exact arm-C 0.1570 was **right by accident** —
I reproduced their path exactly and decomposed it: **leak +0.0822**, **basis mismatch −0.0847**, net −0.0025.
The mismatch (NEW): shape coefficients fit in the A0_wide θ=1 eigenbasis (r=209, 18 modes, r0=106) applied to
the A0_wide__enr θ_MAP eigenbasis (r=194, 19 modes, r0=108) — incompatible coordinate systems, failed
**silently**. (2) "on the exact basis C's lead collapses" is **wrong as stated**: A1 dropped too, so C's LEAD
is ~unchanged (+0.044 → +0.046); what fails S1 is **precision**, not collapse.

**ALSO WEAKENS THE STUDY'S OWN MECHANISM:** the reduced-basis distortion is real but SMALL (mean inflation
+0.005 agent / +0.009 random; Spearman +0.525 / +0.635). D15's "the agent's screening lead was reduced-basis
inflation" is too strong — it is better described as **selection noise on a 14-candidate field**. But
screening DID crown the wrong agent winner (`wa2_brackets_soft` falls 1st→5th on the exact basis), so
review C1 was well-founded.

**INCIDENTS / SELF-CORRECTIONS:** (D2) I corrected my own D1, which had wrongly concluded "the leak barely
mattered." (D3) **checker-scope miss** — I SHA-locked G05 to require S3/S4 == CANNOT-VERIFY per the card,
but Card B (`shocksat_netcg_validated_port_20260716`) landed in parallel and **falsified S4**; I complied
with the locked gate and attached `superseded_by_card_B` to every S3/S4 block rather than edit a locked
checker. (D4) **T2 thrashed** the 16 GB box to 10.8/12.3 GB swap in one long-lived process — one eigensolve
took 11,187 s vs a 506 s median (22×); killed, restarted with ONE candidate per process (428 s), zero
corruption, science unaffected (the affected candidate reproduces the study to 1e-5).

## 2026-07-21 — ShockSat advisor report consolidated reviewer revision

Implemented the criticisms from the initial review through the later reviewer correction that remain valid
against the repaired project artifacts. The report now separates whole-FRF nonconvergence (R-hat 48.8,
ESS 2.0), the boundary-seeking free-discrepancy fit, and IFT band inflation instead of assigning them one
generic pathology. It adds the nine-group modal posterior-contraction table, prior motivations, exact evidence
target, local-versus-global information limit, runtime accounting, and explicit definitions for +6 dB and the
sequential/Net-CG GRMS ratios.

Corrected model-form reporting now distinguishes selected-best gains from preregistered class-mean controls and
labels the +0.0817 finalist gain as selection-biased. A defect/repair/current-claim ledger records the repaired
arm-C leakage/basis issue, exact reranking of all 28 candidates, the validated Net-CG port, and the locked-checker
scope miss. The model-form section de-emphasizes “agentic” branding: the agent is one bounded proposer inside a
controlled search. Contributions and lessons were narrowed to artifact-backed claims, and the weekly plan was
replaced with a concrete closeout acceptance bar for Ilias to approve or change.

No new inference was run. No Beck band or TMCMC trace was invented where retained draws do not exist. Replay:
`bash artifacts/reports/shocksat_results_summary_20260721/run_advisor_progress_bayesian_audit.sh`.
Tufte lint: 0 flags. Checker: **OVERALL YELLOW 13G/1Y/0R, exit 0**. A11y: 0 findings. All 16 rendered pages
were inspected. Final DOCX SHA-256: `dd4851fa7d957352fefbe7778600be917e79032dce149f9786ba0639a8d25a6a`.

## 2026-07-22 — ShockSat advisor working-twin FRF correction

- Recovered the retained L5 working-twin result omitted from Section 5.4: a converged modal-frequency NUTS
  parameter stage plus a marginal log-amplitude discrepancy estimated on observed channels and transferred to
  held-out channels. The report labels this a two-stage modular predictive construction, not a jointly
  converged whole-FRF StatFEM posterior.
- Replaced the eight-panel method wall with two held-out FRFs from frozen split seed 10. DAQ 20 improves
  (mean absolute log10 error 0.684 to 0.587); DAQ 24 remains far from the data (1.070 to 1.076). Each panel now
  shows only measured data, original FEM, updated median, parameter 5th–95th envelope, and total 5th–95th
  envelope. Removed the hit-quality shading/axis and all failed-method curves.
- Corrected the modal likelihood direction to `log f_meas ~ Normal(log f_pred(theta), sigma_f)`. Separated the
  later converged hardened Beck modal-shape calibration from the older failed exact-basis whole-FRF target.
- New artifact preserved all prior DOCX files:
  `artifacts/reports/shocksat_results_summary_20260721/ShockSat_Bayesian_FEM_and_StatFEM_progress_update_working_twin_revision.docx`.
  Replay: `bash artifacts/reports/shocksat_results_summary_20260721/run_advisor_progress_bayesian_audit.sh`.
  Tufte lint 0 flags; a11y 0 findings; all 16 pages inspected. Checker **OVERALL YELLOW 13G/1Y/0R, exit 0**.
  SHA-256 `4c387e21af74b9cdfa591a83f6bae35added892f628c83f503c29cdf5a376b23`.

## 2026-07-22 — shocksat_closure_analyses_20260722 (Task Card A: four Bayesian audit calcs + phase recovery)

Checker verbatim: **OVERALL YELLOW {GREEN: 14, YELLOW: 1, RED: 0}, exit 0** (immutable check.py
SHA fe77b00b…, RED-on-empty proven exit 1, verified unmodified; 57 frozen inputs hash-verified
unchanged end-to-end). Replay: `bash artifacts/reports/shocksat_closure_analyses_20260722/run_all.sh`
(A2 resume-skips retained draws; full recompute ~75 min). Active runtime 4314 s (< 4 h cap).

- **A1 GREEN (known-answer PASS):** prior-whitened log-θ subspace eigenvalues 0.019/0.029/0.259/0.355
  + five prior-like 0.872–1.166, all within block-bootstrap CI (block 40, 1000 resamples) of Andrew's
  adjudicated values. Contracted directions ≈ pure bottom_box/top_box/plates/cross_beam. Subspace
  claim only.
- **A2 YELLOW (the honest tier):** reference HalfNormal(0.05) rerun reproduces the stored posterior
  (σ_f 0.0460 vs 0.0463; θ per-parameter tolerances all pass; converged R-hat 1.009/ESS 464).
  Floor stable 4.2–4.8% across all 5 priors incl. converged HalfNormal(0.15) ⇒ 4.6% floor is
  DATA-driven. 3/5 variants non-converged (R-hat 1.13–1.42, ESS 4–17) — documented with worst-case
  numbers on figure and table, intervals labeled not trustworthy. Per-chain draws retained
  (out/a2_draws/). Prior predictive 18/18 under all priors; reference PIT ~uniform.
- **A3 GREEN (known-answer PASS, max|dev|=0.000 over 28 numbers):** incumbent FEM+6 dB undercoverage
  0.865/0.706/0.738 + statFEM 2.301×/0.982 + per-drive heldout all reproduced from frozen modules
  read-only. NEW CRPS: statFEM beats FEM+6 dB on MEASURED shear evidence 8/10 drive-axis cells under
  all 3 envelope conventions (losses = 2 cross-axis weakly-excited cells). normal_Z labeled
  self-consistency NOT validation; 2.526 vs 2.958 stated adjacently. Load narrative CONFIRMED (stop
  condition not triggered).
- **A4 GREEN:** iid whole-FRF profile likelihood (bottom_box, top_box; nuisances profiled closed-form,
  gradient-verified at all 82 pts) is severely multimodal (~10 local maxima each); stored separated
  chains (R-hat 44.7) sit in different local modes ⇒ separation is diagnosed likelihood geometry.
- **A5 GREEN (FOUND, not re-derived):** statfem_real_validation_20260617/out/phase_likelihood.json,
  circ var 0.8536, slice contrast complex 0.000127 vs magnitude 0.009355; hashed, scope caveat
  (single-hit dataset) documented.

Inherited ceiling unchanged and restated in packet (no net-CG answer key for normal-Z; one article;
no build/test variability). Incidents: decisions_log D5 (bootstrap block length corrected pre-run),
D6 (checker GREEN message juxtaposes max-dev with min-tol; per-parameter rule verified passing).
NEXT: Task Card B (report rebuild) in a FRESH session per next_prompt.md.

## 2026-07-22 — shocksat_closure_report_20260722 (Task Card B: advisor report rebuild)

Checker verbatim: **OVERALL YELLOW {GREEN: 10, YELLOW: 1, RED: 0}, exit 0**. The single YELLOW is inherited
from Task Card A: 3/5 sigma_f sensitivity variants are non-converged (worst R-hat 1.418, minimum ESS 4.4), so
their intervals remain not trustworthy. Checker SHA `b727a824…`; RED-on-empty proven **11 RED, exit 1**.
Replay: `bash artifacts/reports/shocksat_closure_report_20260722/run_all.sh`.

- Rebuilt the 16-page draft as an exactly 9-page advisor brief and Markdown mirror. The thesis now distinguishes
  converged modal-frequency Bayesian FEM updating from response-level StatFEM attempts that did not converge.
- A1/A2 replace nine marginal contraction claims with four prior-whitened log-theta combinations and an honest
  4.2–4.8% residual-floor prior sensitivity; the loose HalfNormal(0.15) variant converges.
- A4 profile likelihood, the found A5 phase artifact, and the recovered time-domain damping result now support
  one response-level diagnosis. The +54.02 evidence number is demoted for the correct type-II-ML/local-linear/
  conditional-target reasons, not an FRF-bin argument.
- Section 5.4 is a two-channel modular FRF figure with exactly five encodings and no hit-quality shading. It
  separates parameter uncertainty from the observed-channel-estimated model-discrepancy band and labels the
  construction as modular rather than a joint whole-FRF posterior.
- A3 is reported as a measured-shear calibration/width tradeoff: coverage and mean CRPS improve relative to
  FEM + 6 dB, while widths increase to 1.508/2.301. Normal-Z stays synthetic-only; 2.526 and 2.958 are reconciled
  adjacently as delivered-reference versus tier-updated configurations.
- Agentic remodeling is defined as a bounded propose/build/verify/fit/score/diagnose/revise loop. The primary
  best-exact comparison (-0.0077 +/- 0.0177; MDE 0.0177) and secondary track mean (+0.0028 +/- 0.0056) both
  failed to demonstrate an agent advantage.

Verification: 34 numeric source checks; prior six DOCX files byte-identical; four figure alt texts; a11y 0;
all nine pages inspected via contact sheet; active build/render/check runtime 7 s. Final DOCX SHA-256
`1b040b4920dd25801c7d2ede44287cc440293afcde889ca8723e0564b82aeb68`.

## 2026-07-22 — shocksat_closure_report_20260722 advisor-context revision

Andrew rejected the adjudication-style opening because Ilias's last context is only the “Stress Testing
StatFEM” proposal. The final nine-page brief now uses page 1 to restate that proposal, Ilias's build/evaluate/
identify-gaps guidance, the ShockSat choice, and the five-step research chronology. Page 2 explains the data,
modal likelihood, sampler terms, and research sequence before the first results on page 3. The advisor-facing
DOCX, Markdown, and figures contain no traffic-light shorthand, “claims I will defend” section, or unused
S1/S3/S4 labels. Convergence failures, worst diagnostics, and evidence limits remain explicit in ordinary
technical language.

Checker verbatim remains **OVERALL YELLOW {GREEN: 10, YELLOW: 1, RED: 0}, exit 0** because 3/5 sigma_f
sensitivity variants did not converge (worst R-hat 1.418, minimum ESS 4.4); those intervals are labeled not
trustworthy. Checker SHA `224d33ff…`; RED-on-empty exit 1 reproven. Numeric trace 34/34 source-backed; page
count 9; a11y high/medium/low 0/0/0; all nine pages and four figures inspected. Final DOCX SHA-256
`b4327f78728add7859b68889dd22f455229ba91ed197772d6b8b2ff7ed5ac91d`.

## 2026-07-22 — shocksat_closure_report_20260722 isolated `_sol` user-comment rebuild

Andrew approved the ten-comment revision but requested an isolated copy because another agent is editing the
source DOCX. The source remains byte-identical at SHA-256
`e8e04f40bcc69c03634e5c6d94eb5beee64f5ebdcbe13f7882ab09f16ee01a8f`. Replay:
`bash artifacts/reports/shocksat_closure_report_20260722/run_all_sol.sh`.

Checker verbatim: **OVERALL YELLOW {GREEN: 11, YELLOW: 1, RED: 0}, exit 0**. The one YELLOW is the unchanged
science caveat: 3/5 sigma_f sensitivity variants did not converge (worst R-hat 1.418, minimum ESS 4.4), and
their intervals remain labeled not trustworthy. Checker SHA `3d4c36e3…`; RED-on-empty exit 1.

- Replaced the single-likelihood lead with a ten-method chronology before any results.
- Made the Bayesian mechanism explicit: the retained zero-centered discrepancy cannot move the predictive
  center; it adds covariance. A structured nonzero discrepancy mean could move the center but was not
  implemented. The report does not claim the residual is orthogonal to all parameter effects.
- Replaced the two hand-selected FRFs with four frozen-rule small multiples plus all 775 channel/split cases:
  595 improve, median error 0.562→0.541, total interval coverage 0.855.
- Moved modal contraction/prior sensitivity to Appendix A and supplied prior variance 1.0 as the comparator.
- Removed the whole-FRF profile graph and all normal-direction load reporting. Shear X/Y definitions now cover
  FEM + 6 dB, coverage, width, CRPS, and all three envelope probability conventions.
- Expanded conditional modal evidence versus held-out engineering prediction, added section references to the
  work-products table, and retained Andrew's single personal closure question.

Verification: 44 source-backed numeric checks; nine pages; two figures/two alt texts; a11y high/medium/low
0/0/0; every page visually inspected. Final `_sol` DOCX SHA-256
`ea5d30f8b1a5b75b48fbdbfde4bb0b06fe93441495dfaffb7e3fc3a742b3f948`.

## 2026-07-22 — `_sol` comparison against independent Fable brief

Compared both Markdown sources and rendered documents. The Fable version supplied four useful explanatory
details: a concrete location-by-frequency example for a structured discrepancy mean; a full-distribution,
proper-score definition of CRPS with model-internal force units; a distinction between integrated marginal
likelihood and the local-linear/type-II-ML evidence calculation; and a short literature-positioning paragraph.
All four were added to `_sol`.

The Fable result-first opening was rejected because Ilias needs project context and method chronology before
findings. The deleted “I treated that as the research question” sentence, six-channel FRF figure, normal-Z
appendix, and tenth page were also rejected. The `_sol` report remains context-first, measured-shear-only,
four-panel, and nine pages.

Replay/checker: `bash artifacts/reports/shocksat_closure_report_20260722/run_all_sol.sh`; **OVERALL YELLOW
{GREEN: 11, YELLOW: 1, RED: 0}, exit 0**. The inherited 3/5 non-converged sigma_f variants remain the only
caveat. All nine pages inspected after render; a11y 0/0/0. Source DOCX remains SHA-256 `e8e04f40…`; revised
`_sol` SHA-256 `9adce4cf09a52cabe751c29286a98eef6a6fe20860caf05095409e7e677181df`.

## 2026-07-22 — Advisor brief `_fable` revision (comments C0–C9 applied; lead as runner)

Workspace `artifacts/reports/shocksat_closure_report_fable_20260722/`; replay `bash run_all.sh` (PDF render
via Microsoft Word automation; LibreOffice absent). v1 workspace untouched; its commented docx/md are
hash-locked immutable inputs verified by G7. Editorial revision only — no new inference, sampling, or
scoring; all 34 numeric-trace checks resolve to the frozen Task Card A / study artifacts.

Checker verbatim: **OVERALL YELLOW {GREEN: 10, YELLOW: 1, RED: 0}, exit 0**. The one YELLOW is the unchanged
science caveat: 3/5 sigma_f sensitivity variants did not converge (worst R-hat 1.418, minimum ESS 4.4);
their intervals remain labeled not trustworthy. Checker SHA `99c004b0…`.

- Added the CENTRAL FINDING callout with the two required fill-in-the-blank sentences: mean cannot move
  (frequency-only converged likelihood + zero-mean discrepancy, structured-mean discrepancy untested per C3)
  and bands stay wide (zero-mean single-scale discrepancy buys coverage only with width).
- C0: modal likelihood labeled one of eight implemented formulations, inventory enumerated + ledger.
- C1: subspace/σf figure demoted to Appendix A; C2: Q&A answers open with direct No/unresolved-scope answers.
- C4: whole-FRF profile figure deleted (diagnosis kept as text). C5: new six-panel held-out FRF figure with
  preregistered rank rule (decisions_log F2) → DAQs 28, 79, 9, 56, 2, 24; DAQ 24 worst, consistent with v1.
- C6: load table shear-only, normal-Z to Appendix B; C7: CRPS defined; C8: evidence comparison expanded;
  C9: work-products table gained "Where explained" pointers. Closing kept verbatim as Andrew wrote it.

Verification: 34 source-backed numeric checks; ten pages (one section per page, text-extraction verified);
three figures with alt text; figure QA in `out/figure_qa.json`. Final `_fable` DOCX SHA-256
`c908c70a7aa117c2ab127cf115b1609f63a8690d8060197b0ccd405080f02bd0`.

## 2026-07-22 — Independent structured-discrepancy card review (Codex; no science run)

Workspace: `docs/agents/structured_discrepancy_codex_review_20260722/`. Replay:
`python3 docs/agents/structured_discrepancy_codex_review_20260722/check_card.py`.

Checker verbatim: **OVERALL GREEN — static runner-card audit**. This GREEN covers the authored review/card
artifact only; it is not a StatFEM result and no card was dispatched. The supplied Task Card D is reviewed as
**RED as a dispatch artifact, GREEN as a research direction** because it contains four blocking specification
issues: Febrianto propagation attribution, conditional-mean versus marginalized-covariance semantics, a
dimensional logarithm, and underspecified correlated holdout/equal-coverage/orthogonality rules.

Direct sources checked: original 9-page closure brief (all pages rendered and inspected), Febrianto et al. 2022
PDF pp. 7–9 and 18, Schneider et al. 2022 PDF p. 5, frozen Schneider M0–M3 code/JSON, spatial reanalysis, and
discrepancy diagnostic. The independent Card E uses a Stage-1 exact modular E0–E3 comparison with shared
covariance and, after the revision below, an automatic decision gate before any joint Stage-2 NUTS update. Supplied card and predecessor workspaces were
not modified.

### Autonomous revision requested by Andrew

Removed the pre-start and Stage-1 human approval requirements. Checker remains **OVERALL GREEN — static
runner-card audit**; science remains not run. The card now evaluates immutable decision rules in order:
`STOP_SYNTHETIC`, `STOP_CONFOUNDED`, `PROCEED_JOINT`, `STOP_PARTIAL_MEAN`, `STOP_PROPAGATION_ONLY`, then
`STOP_NEGATIVE`. Synthetic thresholds are numerical (S0 ≤1/20 false successes; S1 ≥16/20 recoveries plus
≥85% held-out mean-band coverage; S2 bounded worsening; S3 ≥50% θ-bias reduction, ≥80% empirical θ coverage,
normalized orthogonality residual ≤1e-8). Joint Stage 2 is automatically permitted only when protected E3
transfers across both spatial and frequency folds and fits the remaining runtime; it compares J1 with protected
J3 only. The original Task Card D and its separate run remain untouched.

## 2026-11-17 — NASA burst-survey foundation check (lead, cloud session)
- Trial: can NASA's burst-random modal survey (runs 78, 99 free-free; 139 fixed base), its FRF file and its 264 test-vs-FEM plots serve as the higher-quality data the 2026-08-10 handoff asked for? NASA host blocked, so: exact listings from June directory tails, NASA deck evidence, exploratory two-curve pilot, frozen 264-curve pre-registration, burst rehearsal.
- Command: `bash artifacts/reports/shocksat_burst_survey_foundation_20261116/run_all.sh` (offline; NETWORK=1 adds PyPI ranged-download test and the NASA gate); `bash artifacts/reports/shocksat_burst_survey_foundation_20261116/gated_run.sh` to continue.
- Checker result: OVERALL YELLOW 12G/4Y/0R (Y: digitiser curve-level limit 0.66 vs 0.5 dB with metric-level limits met; damping estimator only for 2 isolated modes; NASA host BLOCKED; foundation question OPEN).
- Key metrics: Correlation folder 594 members 1.96 GB compressed, plan needs 0.73 GB; NASA final correlation median |df| 4.3 %, median cross-orthogonality 83 % (93.5 % <150 Hz, 79 % >=150 Hz); pilot drive points NASA test vs NASA FEM 2.75/3.06 dB <150 Hz, 8.18/8.27 dB 150-200 Hz, 4.98/3.53 dB in Card H band at 2.03 Hz vs Card H median 10.02 dB (min 4.77); project FEM vs NASA FEM 0.52/0.92 dB <150 Hz; NASA modes with >=3 lines across half-power width: 0/22 at 2.03 Hz, 19/22 at 0.125 Hz.
- Lessons: see lessons-learned 2026-11-17.
