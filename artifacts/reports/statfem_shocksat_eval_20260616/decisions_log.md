# decisions_log.md — StatFEM ShockSat held-out-QOI evaluation (Experiment B)

Runner: Claude Code (lead-as-runner for Experiment B). Human: Andrew Voss. Advisor objective: Ilias Bilionis.
Workspace: `artifacts/reports/statfem_shocksat_eval_20260616/`.

## RUN STATUS (compaction-safe; update before risky steps)
- 2026-06-16: ALL code + immutable check.py + docs WRITTEN. `bash run_all.sh` launched DETACHED
  (resumable). Stage order: sweep(20 cells) → sensitivity(9) → identifiability → discretization(399k eigsh,
  cached) → aggregate → 6 figures+lint → image_qa → deck → runtime → check.
- VALIDATED so far: forward (numpy≡jax 1e-14, grad finite, 0.71ms); M0 combo1 R-hat 1.001/ESS 2241/cov
  0.21/0.14 (naive confidently wrong ✓); M1 combo1 R-hat 1.001/ESS 2397/cov 0.93/0.57/σ_d 0.069 (iid restores ✓);
  identifiability gate (4/9 strain-energy ✓); fig_schematic+figE render, all 6 fig scripts lint-clean (INFO only),
  text_overlap empty, image_qa OK.
- ALL 4 ARMS VALIDATED (combo1, all converged R-hat≤1.002/ESS≥2149/0 div): M0 cov 0.21/0.14 (confidently wrong);
  M1 iid 0.93/0.57 (peak restored, BAND under-covers); M2 Schneider 0.93/0.86 (BOTH restored — beats iid on the
  structured band QOI via spatial kriging, the headline mechanism); M3 orthogonal 0.93/0.86, σ_d 0.064 (matches
  Schneider coverage with a de-biased θ). M2/M3 ~11-14 min/cell under 2-way share. THE HYPOTHESIS REPRODUCES.
- PENDING: 16 more main cells + 9 sensitivity + discretization eigsh + aggregate + deck + checker. Monitors:
  b04cgeqd1 (run_all done). Full run ~5 hr. Target 20 main + 9 sensitivity cells, then checker_report.json.
- TO RESUME after compaction: `bash run_all.sh` (skips finished cells); read this file + priority_deliverables.md;
  after checker GREEN/YELLOW, fill packet.md <!-- RESULTS_* --> from out/*.json (NOT fabricated), then SURFACE
  the project_log row + notes update to the lead (do NOT self-apply).

## Re-grounding (session start 2026-06-16)
- **goal:** evaluate the StatFEM approach on the plain ShockSat FEM via a held-out-sensor-QOI coverage
  trust test across 5 truth bias combos × 4 discrepancy arms (naive / iid / Schneider / orthogonal); report
  whichever way it falls (StatFEM may not work here — that is a permitted, valuable finding).
- **last decision:** (this is session 1) — grounded in AGENTS.md (all gates), the task card, `notes/memory.md`,
  the modal twin (`shocksat_fem_modal_twin_20260609`), today's `confidently_wrong_modelform_20260616`, the
  Schneider code in `papers_statfem_studies_20260612`, and the tufte skill.
- **next action:** write the immutable `check.py` FIRST (before results), then build `core.py` forward FRF.
- **open ambiguities:** none blocking; defaults documented below. Verdict (works/doesn't) deliberately undecided.

## D0 — Plain-ShockSat constraint (Andrew, non-negotiable, task §3)
Use ONLY the plain standalone 9-group ShockSat FEM from `shocksat_fem_modal_twin_20260609`
(`K(θ)=A_fix+Σ_g θ_g A_g`, 9 groups, reduced 74-mode basis, mode shapes at 76 accel nodes / 228 translational
DOFs via `obs_V`). The coupled ShockSat×tray model (`shocksat_tray_coupled_qoi_20260610`) is FORBIDDEN — no
tray, no payload coupling. Verified in code by checker (no tray-model artifacts referenced; data provenance =
reduced_blocks.npz copied from the modal twin).

## D1 — Reuse-by-COPY (anti-cheating, task §14)
All reused FEM assets COPIED into `data/` (reduced_blocks.npz, measured_modes.npz, groups.json, T/M/Kblocks for
the full-order discretization check, sensor_coords.npz extracted from fem_model.npz). Originals NEVER edited.
The forward-model / discrepancy / NUTS structure is re-implemented fresh in `code/`, patterned on (not copied
verbatim from) `confidently_wrong_modelform_20260616/code` and `papers_statfem_studies_20260612/code/forward.py`
(Schneider freq×space Kronecker correlation). No immutable checker of another study is touched.

## D2 — Forward observable = modal-superposition accelerance FRF (quantity contract)
Per-sensor accelerance `H_s(ω;θ,ζ) = a_s/F_d = -ω² Σ_k Φ_obs[s,k] Φ_obs[d,k] / (ω_k² - ω² + 2 i ζ_k ω_k ω)`,
where Φ_obs = obs_V @ Q(θ), Q,λ = eigh(A_fix + Σ_g θ_g A_g), ω_k = sqrt(λ_k), mass-normalized modes
(reduced mass = I). Point-force drive at a documented drive DOF d; response acceleration (g/lbf-style) at each
sensor DOF. Units: accelerance magnitude in (in/s²)/lbf-equivalent (synthetic; we report the QOI ratio, not an
absolute calibrated load). See `quantity_contracts.md`.

## D3 — Why synthetic FRF is VALID here (was NOT for real test data)
Truth and inference share the FEM geometry/mesh/mode shapes, so the test-tap-vs-FEM transfer-path objection
(upstream observation-layer constraint, memory.md 2026-06-09) does NOT apply. The truth FRF is generated from
the SAME reduced model with a biased θ_truth plus an injected output-space discrepancy; the inference model
starts at θ=1. This is a controlled twin with ground truth for the held-out QOIs.

## D4 — Two layers of injected model-form error (task §5)
(1) Parametric bias: θ_truth set to +10–20% offsets on chosen groups (recoverable-vs-not per the 4/9
identifiability finding). (2) Schneider discrepancy: complex, correlated multiplicative model-form error on the
truth FRFs, correlated over log-frequency AND sensor distance (space), NOT representable by any θ scaling. Plus
an orthogonal variant for the M3 arm (discrepancy projected orthogonal to the θ→FRF sensitivity span).

## D5 — Damping ζ (assumption, sensitivity-flagged)
Nominal modal damping ζ = 0.02 (2% critical) for ALL modes — a representative installed-configuration value
(the free-free .ash test damping is artificially light: median 0.32%, range 0.06–1.05%, because it is a bare
free-free article with no joint/interface dissipation). Sensitivity arm: ζ = 0.01 and ζ = measured-mode values.
Rationale: 2% gives resonance half-power bandwidth ~2ζf so peaks are resolvable on a log grid without razor
sharpness; the QOI verdict is tested against ζ in the sensitivity gate.

## D6 — Frequency grid (discretization gate)
Log-spaced grid over a documented band 45–260 Hz (covers the calibration-mode region <222 Hz where 4/9 groups
are identifiable; the 74-mode basis spans 54.6–321.7 Hz). Default n_freq = 160 points (~0.3% spacing). Validate:
(a) reduced 74-mode modal-superposition FRF vs a direct full-order (T'KT, T'MT) complex solve at the dominant
QOI-peak frequencies; (b) modal-truncation refinement (74 vs fewer modes); (c) grid-density refinement (n vs 2n).

## D7 — The 5 bias combos (task §6; same data per combo, all arms)
(1) identifiable-only: top_box ×1.15, bottom_box ×0.90; (2) unidentifiable-only: joints ×1.20, contact ×1.15;
(3) mixed: top_box ×1.15, joints ×1.20, plates ×0.88; (4) large: cross_beam ×1.20, joints ×0.82;
(5) broad-small: ~±10% across several groups. Each combo = one synthetic truth (its own Schneider field
realization, fixed std profile) → 5 distinct realizations spanning identifiable/unidentifiable θ-bias. Coverage
reported as a distribution over the 5 (retires the single-realization caveat).

## D8 — Arms (task §7)
M0 naive (no discrepancy, iid measurement noise only, σ_d=0); M1 StatFEM-iid (additive iid output discrepancy,
learned σ_d); M2 StatFEM-Schneider (complex correlated freq+spatial discrepancy, learned scale, fixed
correlation lengths); M3 StatFEM-orthogonal (Schneider discrepancy projected orthogonal to the θ-sensitivity
span at nominal θ). NUTS, ≥4 chains, all-variable convergence gate (R-hat ≤1.05, ESS ≥200, div-frac <2%).

## D9 — Held-out prediction mechanism (the StatFEM predictive)
Observe a few sensors, hold out the rest. θ posterior predicts ALL sensors (modes are global). Discrepancy at
held-out sensors: M0 none; M1 iid marginal σ_d (no spatial transfer); M2/M3 GP-conditional (krige the held-out
discrepancy from the observed-sensor residuals using the Schneider freq×space covariance). This is the
mechanism by which "Schneider beats iid where the error is structured" — to be TESTED, not assumed.

## D10 — Hysteretic damping via dynamic-stiffness solve (avoids eigh degeneracy in NUTS)
The reduced model has near-degenerate mode clusters (124.6/124.6, 233.7/233.7 Hz). A jax `eigh` in the
differentiable FRF path would produce ~1/(λ_i−λ_j) eigenvector-gradient blow-ups (the modal twin hit this with
its MAC arm: 82 divergences, R-hat 2.97). Fix: synthesize the FRF with constant hysteretic (structural)
damping, loss factor η = 2ζ, via the reduced dynamic-stiffness solve `Z(ω)=(1+iη)K_red(θ)−ω²I`,
`H_s=−ω² obs_V[s] Z⁻¹ obs_V[d]ᵀ`. No eigh in the gradient path; the complex linear solve is smooth and
differentiable in θ. At resonance this matches viscous ζ peak amplitude. Damping sensitivity (task §9) =
constant-η sweep ζ∈{0.01,0.02,0.03}; per-mode measured-ζ would re-require eigh, so it is a documented non-arm.
(eigh is still used OUTSIDE the gradient path for strain-energy / FIM / peak-frequency reporting.)

## D11 — FRF magnitude is highly resonance-sensitive; whole-log-FRF likelihood
Combo-1 (identifiable boxes ±10-15%) moves the FRF strongly (mean |Δlog|H|| ≈ 0.49); combo-2 (joints/contact,
unidentifiable) barely (≈0.095) — confirming FRF amplitude carries far more box-stiffness signal than
frequency-only, while joints stay weak (low strain energy). Likelihood = whole log|H| over all 160 band points
on observed channels (log compresses the resonance peaks; no peak/feature selection). The Schneider field
(std 0.03-0.12, orthogonal to θ) is the dominant unmodeled error that breaks naive coverage in ALL combos.

## D12 — NUTS settings: dense mass, max_tree_depth=6, 4 chains, 1000+1000
The hyper-sensitive FRF magnitude pins identified θ extremely tightly (a stiff posterior direction); uncapped
NUTS saturates at tree depth 10 (1023 steps) chasing it → ~15-25 min/cell. Probe at combo3/M0 (1 chain,
600+400): depth-6 → 56.7s, mean 49 steps, R-hat 1.019, ESS 184; depth-8 → 110s, mean 59, max 255, R-hat 1.020,
ESS 205. Depth 6 is the sweet spot (4-chain×1000-sample ESS ≫ 200, R-hat < 1.05). Settings: dense_mass,
target_accept 0.9, max_tree_depth 6, 4 chains, 1000 warmup + 1000 samples. Per-cell ≈ 3-5 min → full
20-cell sweep ≈ 1.5-2 hr; launch detached + resumable (task §13).

## D13 — Discretization "at QOI peaks" metric = QOI-VALUE error (robust), point-wise reported alongside
The reduced-vs-full FRF check: a point-wise |reduced/full−1| at the resonance flanks is hyper-sensitive to the
tiny (~0.25%) reduced-vs-full peak-FREQUENCY shift amplified on steep high-Q flanks, and overstates the
reduction error for the QOI. The task asks for error "at the QOI-driving peaks" — the QOI is the peak |H| /
band-GRMS VALUE, so `max_rel_err_at_peaks` = max(peak-QOI-value err, band-QOI-value err) (max-over-band taken
independently per model, robust to freq shift). The strict point-wise flank error is reported transparently as
`max_pointwise_rel_err_near_resonance` with the explanation. NOT a checker edit (the immutable checker reads the
field `max_rel_err_at_peaks`); this fixes the MEASUREMENT to match the checker's stated intent.

## D14 — Parallel-runner CPU sharing (sibling = Experiment A)
Confirmed a sibling runner process (`run_sweep.py --only mlik_sr`, different workspace) shares the CPU — the
parallel Experiment-A consistency toy. Per the lead's "hands off other arms" rule, left untouched; my per-cell
NUTS time roughly doubles under 2-way sharing (≈5 min isolated → ≈8-10 min shared). My run is resumable +
detached so this only affects wall time, not correctness. (My OWN earlier zombie procs from timing/probe runs
were correctly killed before relaunch.)

## D15 — Editable PowerPoint (.pptx) added (Andrew ask)
Initially built the deck as PNG slides + DECK.md (matching the repo's prior decks + because the image-QA/tufte
gates operate on PNGs). Andrew asked for an actual PowerPoint. `python-pptx` 1.0.2 is in BASE python3 (not
`.venv_nuts`), so `code/make_pptx.py` runs under python3 and assembles `slides/StatFEM_ShockSat_eval.pptx`
(11 slides, 16:9, 6 embedded figures, every claim traced to a checker number). Wired into run_all.sh as the
`pptx` stage (graceful skip if python-pptx absent). PNG slides retained.

## D16 — Spatial maps on the FEM geometry (Andrew ask)
Built figF_spatial_error (5 combos: structure + observed/held-out/drive sensors + property groups coloured by
injected prior error |θ_truth−1|) and figG_spatial_ident (same + groups coloured by modal strain-energy
identifiability). Built from EXACT FEM geometry (data/group_geometry.npz = subsampled per-group element
centroids; sensor coords from the 76 accel nodes), NOT by registering against the _ShockSat_Overview_20220606.pdf
(avoids error-prone image registration; the PDF is cited as the external context doc). Both pass tufte_lint /
image_qa / text-overlap. Added as 2 slides → pptx now 13 slides. Wired fig_spatial into run_all.sh.

## OPEN DECISION FOR HUMAN (Andrew) — discretization gate
Checker overall RED on ONE gate (discretization:reduced_frf_validated, 8% > 3%). Diagnosed as MODAL TRUNCATION
of the reused 74-mode basis (fmax 321 Hz = 1.2x band; ~5% at nominal, ~8% at joints+20%), NOT a bug — study is
internally exact so StatFEM conclusions unaffected (= YELLOW per Result Status Standard). Awaiting Andrew:
(a) accept documented YELLOW (relax gate to ~10% w/ diagnosis), or (b) rebuild basis to ~450 Hz + re-run (~5-6h).
NOT changing the immutable checker without his call.

## Decisions to be appended as the build proceeds...
