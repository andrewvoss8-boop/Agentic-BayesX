# decisions_log — ShockSat net-CG force method selection (autonomous runner)

Workspace: `artifacts/reports/shocksat_netcg_method_selection_20260701/`
Runner started: 2026-07-01. Mode: autonomous Stage 0 → Stage 3; HALT only on a true blocker.

## Re-grounding (one line)
GOAL pick, PER QOI (shear high-trust / normal low-trust), the ONE {mesh, formulation, pooling}
updating combo that passes 1-octave-smoothed coverage (hard gate) + leave-modes-out humility (no false
sharpening) then is sharpest, and deliver net-CG FORCE bands + trust map. LAST DECISION Andrew dispatched
this runner prompt (2026-07-01). NEXT ACTION Stage 0 (no NUTS): +Y distilled, QOI mode/sensor weights,
trust table w/ +Y, unmeasured-σ sensitivity, mesh screen, per-QOI validity gate. OPEN AMBIGUITIES normal-QOI
number is likely data-starved even with +Y (deliver covering band + next-test rec); winner's-curse (report N).

## Confirmed facts from re-grounding (files, 2026-07-01)
- AGENTS.md gates read; NUTS/HMC default; convergence = all-variable R-hat<=1.05/ESS>=200/div<2% w/ >=4 chains,
  non-centered for hierarchical variance. Held-out is the only trust arbiter. GREEN/YELLOW/RED per checker.
- Env verified: py3.9.6, jax0.4.30, numpyro0.19.0, scipy1.13.1, numpy1.26.4 (matches prompt §9).
- Disk: 7.6 GB free (96% used) — TIGHT. Avoid caching large eigenvector arrays (past 256MB incident). float64.
- Base workspace reuse = `shocksat_psd_envelope_twin_20260623/code/`: realfrf.py (load_reduced), modal_feature.py
  (L5 NUTS), score.py, qoi_trust_table.py, shape_borrow_diag.py, strut_force_qoi_pilot.py, heldout_qoi.py,
  correlate_all.py, guided_remesh.py, modal_multiref.py, multiref_frf.py — all present.
- FEM = `shocksat_fem_modal_twin_20260609/fem_model.npz` (present).
- 4 canonical modal caches (N=122880, 105 freqs, 111 ch) at psd_envelope `data/multiref_modal/`: m_xpos_990x,
  m_zpos_990z, m_xy_990xy, m_zpos_900z. Backed up to my `data/multiref_modal_backup/` (2026-07-01).

## D1 (2026-07-01) — +Y (Test03/990y) 5th drive: distill to N=122880 canonical format
- FOUND: Test03_ModalHammer_990y.zip (676 MB, at repo root, dated Jul 1 = Andrew's download); an OLD amplitude
  cache ypos_990y_N65536.npz (N=65536, 57 freqs, 84 ch) at shocksat_multiref_amplitude_20260622 — WRONG
  resolution to sit beside the 4 canonical (N=122880). So I re-distill +Y at N=122880 to match.
- `multiref_frf.REFS["ypos_990y"]` already registered → folder Test03_ModalHammer_990y, xyz=(8.5,9.0,1.0),
  axis Y, instrument modal. modal_multiref.py builds N=122880 caches via mr.build_reference. REUSE that,
  BYTE-IDENTICAL windowing, so +Y is processed exactly like the other four (same N, band 45-260, same channel
  set, exp window). Extract the 4 modalhammer .mat hits (001/004/005/006, ~1GB) into MY workspace
  data/extracted_modal/, build m_ypos_990y.npz into MY data/multiref_modal/, then DELETE the .mat to reclaim
  disk (zip retained at repo root = re-extractable). NOTE the Test03 modal hammer has a different tip/force
  spectrum than impact tests → per-test gain expected (handled by per-ref gain in likelihood, like +XY).
- This is NOT "fetching large new data" (guardrail): the zip is already downloaded; prompt §9 explicitly says
  LOCATE + distill +Y. Extraction/build confined to my workspace.
## D2 (2026-07-01) — net-CG FORCE QOI definitions (Quantity Contract)
- QOI = net-CG force on the TOP TRAY/PLATE region = Σ_i m_i a_i = ω²·Σ_i m_i φ_i over the tray-region DOFs,
  band-limited 45-260 Hz (the FEM/measured band; the prompt's 20-2000 Hz delivery band is wider than the
  data band — flagged: outside 45-260 Hz the twin is prior-only, documented in assumptions).
- Tray region = FEM nodes with z >= 55 in (top plate; 4646 kept nodes). Struts z 45-55; box z<45. MOUNT
  center = (0,0,57.75).
- MASS: uniform-mass proxy over the tray region (m_i = const) → net-CG force ∝ ω²·Σφ_i (same convention as the
  validated base_shear functional). Documented proxy; a consistent-mass (shell ρt + conm2) refinement is a
  sensitivity item, not the headline.
- DIRECTIONS reported SEPARATELY (never blended): tray_shear_X (in-plane X), tray_shear_Y (in-plane Y),
  tray_normal_Z (out-of-plane Z, drumhead). Expected per prompt physics: shear driven by measured global box
  modes (high trust), normal driven by unmeasured plate/drumhead modes ~234-254 Hz (low trust). This split is
  VERIFIED empirically by the participation weights (Stage 0), NOT assumed.
- Also compute whole-structure base_shear_X/Y/Z + mount_response(center) for context/continuity with the
  2026-06-24 trust table. Two nearby conventions named: net interface FORCE (used) vs net-CG ACCEL/GRMS.

## D7 (2026-07-01) — CRUX of the bake-off + Stage-2 scope (honest)
- The θ (9 stiffness-group) posterior from L5-style NUTS moves mode FREQUENCIES but does NOT resolve the drumhead
  SHAPE/participation (unmeasured). So a QOI band built from θ-draws ALONE (nominal fixed shapes) is FALSELY
  NARROW on tray_normal_Z = the exact false-sharpening the selection rule disqualifies. The HONEST band must ADD
  the Stage-0 unmeasured-mode discrepancy (tier-1/2 amplitude uncertainty, SD_A_U). This distinction IS what the
  formulations differ on and what leave-modes-out tests: hide measured modes -> does the band widen to cover them.
- Formulation reframing for the bake-off (what actually differs = the QOI uncertainty representation):
  * baseline_fem (theta=1) + fem+6dB = the bars.
  * L5_freq THETA-ONLY = calibrate freq, propagate only theta -> SHARP; predicted to PASS shear coverage,
    FAIL normal coverage + leave-modes-out (false sharpening). The "at-risk" candidate, kept to EXPOSE the trap.
  * L5_freq + unmeasured-mode DISCREPANCY (statFEM-style output-space widening using Stage-0 tiers) = HONEST;
    predicted to cover both, sharp on shear, wide on normal. The predicted survivor.
  * feature_space (peak f0+-X%, amp Y+-Z dB) = per-mode amplitude prior -> naturally carries the unmeasured-amp
    width; predicted graceful. (Run if budget allows.)
- STAGE-2 SCOPE DECISION (autonomy: protect the ONE decision, prune wasteful, report N): the full
  7-formulation x 4-mesh x 3-pooling x 2-QOI x 5-scoring grid under NUTS is not honestly completable in one
  session. I run the DECISIVE subset that answers the binding requirement: {baseline, fem+6dB, L5_theta_only,
  L5_freq+discrepancy}(+feature_space if budget) x {inherited + screened meshes} on {shear, normal} with
  heldout_drive + leave_modes_out. Report N (configs compared) and label deferred cells explicitly. The
  held-out data certifies the ONE per-QOI selection; the sweep breadth is documented as partial, NOT hidden.

## D12 (2026-07-01) — FOLLOW-ONS #1 (real held-out-drive answer key) + #2 (Axis-A formulation breadth). Andrew "run 1 and 2".
- #1 motivation: the bake-off coverage used an epistemic-truth ensemble that shares freq_discrep's tier model
  (partly self-consistent). #1 replaces it with a REAL held-out-DRIVE answer key: reconstruct the per-drive net-CG
  SHEAR force from that drive's MEASURED FRFs (LSQ per-mode complex participation a_i on the 111 sensors, reduced-
  model shapes, measured/matched freq), answer key G_ans(w)=Σ_i a_i·g_i^tray·φ_drive,i·ω²/D_i; twin per-drive band
  = winning method WITH φ_drive; fit ONE global gain (hammer/mass-norm nuisance, input level cancels); 1-oct
  coverage. Exposes real under-coverage if present. IMPORTANT gap #1 forces: the bake-off QOI used a FLAT modal
  drive (no φ_drive); #1 adds the per-drive drive participation (more faithful to the quantity contract "per-drive
  prediction"). Restricted to SHEAR (measured modes carry it -> reconstructable); NORMAL has NO held-out-drive
  answer key (drumhead shape unmeasured) -> stays on leave-modes-out (documented, not a gap).
- #2: add Axis-A formulations to the bake-off on the same harness: feature_space (data-informed per-mode amp
  prior: measured modes tight from measured FRF amp spread, unmeasured wide), statFEM_Fk (frequency-CORRELATED
  additive output discrepancy, not per-mode), hier_pooled (shared-scale/partial-pooled amplitude). Question: does
  any give a covering-but-SHARPER normal band, or do they all confirm freq_discrep + disqualify theta_only?
  Prediction: normal width is amplitude-assumption-dominated -> pooling can't tighten it; expect all confirm the
  wide honest normal + none rescues sharpness there; may tighten shear modestly. Reduces the best-of-N winner's-
  curse (N grows). NUTS reuses the cached theta posterior (fast). Checker (locked) unchanged; new artifacts added.

## D13 (2026-07-01) — #1 RESULT: real held-out-drive answer key HARDENS shear_X, CATCHES a shear_Y gap
- out/heldout_drive.json. Winning method (L5_freq_discrep), per-drive net-CG shear band vs each held-out drive's
  MEASURED-FRF reconstruction (LSQ per-mode participation), 1-oct, one global gain per drive:
  * shear_X: covered 1.00 on ALL 5 held-out drives -> STRONG independent validation (not self-consistent).
  * shear_Y: covered 1.00 on 4/5 drives; on the +Z(900) drive cov=0.63, PEAK coverage=0.00 = a GENUINE
    under-coverage at the dominant peak. Diagnostic REFUTES the low-signal explanation (its answer-key GRMS is
    1.18x the cross-drive median = normal signal), so it is a REAL model-form gap: the twin under-predicts the
    net-CG Y-shear peak for the end (y~0) Z-drive (a cross-axis path the FEM gets wrong). Honest caveat, surfaced
    not hidden -> shear_Y delivery carries a "reliable except the +Z@900 end-drive cross-axis peak" flag.
- VALUE CONFIRMED: the held-out-drive metric is stricter than the epistemic-truth-ensemble coverage (which gave
  all shear ~1.0) and it caught a real gap the self-consistent metric hid. #1 was worth running.
- NOTE: this also upgraded the QOI to per-drive (adds phi_drive participation) — more faithful to the quantity
  contract "per-drive prediction" than the flat-modal-drive bake-off. shear_X conclusion unchanged + strengthened.

## D14 (2026-07-01) — #2 RESULT: Axis-A formulation breadth (N=18) refines the winner + answers RQ3
- Added feature_space (measured-amp pinned 0.20), statFEM_Fk (QOI-aware freq-CORRELATED output discrepancy,
  marginal ramps 0.25->0.80 by local unmeasured participation), hier_pooled (shared amp-scale tau=0.25 + shrunk
  per-mode 0.15/0.55). bakeoff N=18 (5 methods + FEM+6dB, x3 QOI). theta cached; vectorized octave-smooth to a
  matmul (was O(Nf^2) in a hot loop -> 2-min timeout; now fast).
- RESULT: BINDING REQUIREMENT ROBUST — all 4 discrepancy methods COVER + are HUMBLE (leave-modes-out); only
  theta_only FAILS (overconfident). WINNER (sharpest covering+humble): shear_X statFEM_Fk 1.51x, shear_Y
  statFEM_Fk 2.30x (both sharper than freq_discrep 1.93/3.16x and data-anchored -> upgrade). normal_Z nominal
  sharpest = hier_pooled 2.00x BUT flagged: its sharpness rests on a POOLING (shared-amplitude-scale) assumption
  over UNMEASURED drumhead modes = UNVERIFIABLE without the >200 Hz plate test (its per-mode sd 0.60 < truth 0.80;
  1-oct coverage too lenient to penalize) -> conservative honest normal = statFEM_Fk 2.53x. **RQ3 answered:
  pooling CAN tighten the normal band ~20% but only under an unverifiable assumption; on the measured shear it is
  not the sharpest (statFEM F(k) is).**
- Held-out-drive re-run with the SELECTED sharper method (statFEM_Fk): shear_X covered 1.00 on ALL 5 drives;
  shear_Y 1.00 on 4/5, +Z(900) 0.60 (peak 0) = the SAME genuine end-drive cross-axis gap (method-independent,
  0.63 freq_discrep -> 0.60 statFEM) -> real model-form caveat, confirmed, not an artifact of one method.
- NET: winner upgraded to statFEM F(k) for shear (sharper, held-out-drive-validated 5/5 shear_X) + conservative
  normal; theta_only still the disqualified false-sharpener; the whole conclusion is now robust across 4 honest
  formulations (winner's-curse reduced). Locked checker still valid (checks theta_only FAIL + freq_discrep humble
  on normal + selection recorded = all still true).

## D15 (2026-07-01) — #3 PRE-TEST DESIGN (Andrew "sure"): the >200 Hz plate test that buys down the normal band
- Mesh screen COMPLETE: top 6 edits (incl inherited) TIE at +0.4401 -> NO remesh beats inherited on the shear
  proxy = remesh has no QOI leverage (checker mesh-screen YELLOW now clears).
- #3 = turn "needs a >200 Hz plate test" into a concrete pre-test: identify the drumhead modes (228-260 Hz,
  UNMEASURED) driving normal_Z; show current perimeter sensors sit near the drumhead NODE RING (low modal Z
  amplitude, miss the plate-center antinode); propose a candidate plate sensor grid; greedily place sensors
  (E-optimal on the drumhead-mode subspace FIM Phi^T Phi) to resolve those shapes; compute the normal-QOI band
  buy-down (band factor vs # plate sensors, moving resolved modes unmeasured->measured tier); recommend the drive
  (Stage-0 observability: +Y sees 230.6, +Z/+XY see 233/234, +X/+Z see 251/254 -> a +Z or +XY deck drive + plate
  accels). Cheap, NO NUTS, reduced-model shapes. Output out/pretest_design.json + figures/fig_pretest.png.

## D16 (2026-07-01) — #3 RESULT: the >200 Hz plate pre-test buy-down (out/pretest_design.json, figures/fig_pretest.png)
- Target = the net-CG-normal DRIVERS = partial-cancellation drumhead modes 246.1/249.4/253.9/258.3 Hz (net tray-Z
  participation), NOT the pure 234/252 Hz modes (net~0 -> cancel; this is why net-normal 45% trust beats point
  mount 13%). Their SHAPES are unmeasured; current plate = 1 Z-sensor, off the antinode.
- BUY-DOWN (band factor via MC as drumhead modes move unmeasured->measured tier by captured-energy/EfI placement):
  current 5.4x -> 12 well-placed plate accels 3.5x (~35% reduction) = 73% of the way to the fully-resolved FLOOR
  2.8x. HONEST caveats: (a) even fully resolved the normal floor is 2.8x (never as tight as shear 1.5x -> the
  drumhead net force is intrinsically less certain); (b) the 246-258 Hz net-drivers have FINE spatial structure
  (worst-mode captured only 0.39 at 12 sensors) so full resolution needs a denser array; (c) the modes are NOT
  individually separable by point sensors (sep-min-eig~0) but you only need their NET combination = the QOI.
- RECOMMENDED TEST: a deck plate array (center+rings, >=12 Z accels) + drive +Y (covers the most drumhead peaks
  incl the unique 230.6 Hz; +Z(990)/+XY tie next). This is the concrete "next test dollar" that replaces the
  hand-chosen SD_A_U assumption (the load-bearing one from Stage-0) with data. NO NUTS; reduced-model shapes.

## D17 (2026-07-01) — DIVE-DEEPER #1/#2/#3 (Andrew "run all 3"). Follow-ons; locked checker NOT modified.
- DD1 diag_shearY_gap.py: decompose the +Z(900) shear_Y held-out-drive gap -> which mode's Y-participation the
  FEM mispredicts (measured a_i.g_i^Y.phi_drive,i vs FEM), is it a tray-Y (g) or drive (phi_drive) mismatch, is
  the culprit measured/unmeasured, frequency also off? out/diag_shearY_gap.json + figure.
- DD2 learned_statfem.py: put the statFEM output discrepancy IN the likelihood — infer its marginal sigma_d +
  log-freq correlation length ell via NUTS from the SHEAR held-out-drive residuals (log|G_measured/G_fem|), per-
  drive mean removed. Learned (not assumed) discrepancy -> shear band width inferred. Report sigma_d, ell,
  convergence, and compare band width/coverage to the ASSUMED statFEM F(k). out/learned_statfem.json + figure.
- DD3 data_anchored_sigma.py: use the 5 drives' fitted per-mode modal scales a_i^(d) (drive-independent up to a
  per-drive gain) -> empirical per-mode log-amp spread across drives = a DATA-anchored SD_A_M (vs the assumed
  0.35). Test if measured modes share a common scale (pooling justified) or are independent; re-run the shear/
  normal band with the data-anchored measured sigma. out/data_anchored_sigma.json + figure. NO new hardware.
- All reuse heldout_drive.fit_participation (per-drive per-mode LSQ) + netcg_qoi. Documented as artifact-backed
  follow-ons in a NEW packet section; checker stays locked (GREEN 22/0/0).

## D18 (2026-07-01) — DIVE-DEEPER RESULTS #1/#2/#3 (a coherent, honest, humbling synthesis)
- DD1 (diag_shearY_gap.json): the ONE caught held-out-drive gap (+Z@900 shear_Y, cov 0.60) localizes to a low
  ~73 Hz mode whose fitted modal scale for +Z(900) is a ~5x OUTLIER vs the other 4 drives (z=1.9) -> DRIVE-SPECIFIC
  reconstruction/observability artifact (that end-Z drive barely/anomalously excites the mode), NOT a systematic
  FEM error. REVISES D13's "genuine model-form gap" -> the shear_Y deliverable is reliable across the well-behaved
  drives; the gap is an end-drive artifact. (Freq err of the culprit only -2.5%.)
- DD3 (data_anchored_sigma.json): the 5-drive cross-scatter of the per-mode fitted modal scale a_i gives an
  EMPIRICAL measured-mode amplitude sigma. NAIVE median 1.03 (inflated by poorly-excited modes = DD1's effect);
  ROBUST (well-excited drives only) median 0.86 (range 0.21-1.44) -- still >> the assumed 0.35. Data-anchored band:
  shear_X 4.5->6.4x, shear_Y 4.4->12.7x, normal 5.4->6.0x. Pooling ICC 0.31 (<0.5) -> drive scatter dominates ->
  a shared amplitude scale (pooling) IS reasonable for measured modes (partly justifies RQ3 pooling).
- DD2 (learned_statfem.json): put the statFEM output discrepancy IN the likelihood; NUTS CONVERGED (R-hat 1.001,
  ESS 2083, 0 div, 7s). LEARNED marginal sigma_d = 0.94 (CI 0.82-1.07), correlation length 0.10 OCTAVES
  (near point-wise). >> assumed 0.25; AGREES with DD3's 0.86. TWO INDEPENDENT ROUTES agree the shear discrepancy
  is ~0.9, not ~0.3.
- **SYNTHESIS (the honest headline refinement):** the shear model-form discrepancy is ~0.9 log-amp (much larger
  than the bake-off assumed 0.25-0.35), BUT it is nearly POINT-WISE (ell 0.10 oct), so it AVERAGES OUT under
  1-octave smoothing -> which is exactly why the #1 held-out-drive coverage PASSED on the SMOOTHED metric. So the
  delivered shear band is trustworthy AT THE 1-OCTAVE-SMOOTHED level (validated) but the POINT-WISE shear amplitude
  is uncertain to ~0.9 -> do NOT over-read the smoothed band as point-wise sharp. This QUANTIFIES the project's
  standing "per-node/point amplitude fidelity is the wall" via two new independent routes and precisely bounds the
  deliverable. Locked checker unchanged (GREEN 22/0/0); DD's are artifact-backed follow-ons + a new packet section.

## D11 (2026-07-01) — FINAL STATE + checker lock
- Checker SHA-locked (CHECKER.sha256 = 3ad847d2...). Run status: OVERALL YELLOW (21 GREEN / 1 YELLOW / 0 RED,
  exit 0). The single YELLOW = mesh screen still running DETACHED (5/12 edits scored; baseline/inherited best at
  +0.440, plates_E_lo +0.433 — confirms inherited best / remesh no QOI leverage). The screen is resumable and will
  write out/mesh_screen_summary.json on completion; RE-RUN check.py then -> that check flips GREEN (the locked
  checker already handles both pending and complete without modification, so locking now is safe).
- Deliverables complete: priority_deliverables / question_framing / quantity_contracts / assumptions_ledger /
  decisions_log / packet / findings / run_all.sh / runtime.json / REUSED_code.sha256 / check.py(+SHA) ;
  code/{build_ypos_cache, stage0, mesh_screen, netcg_qoi, bakeoff, fig_stage0, fig_delivery, fig_graphmodel} ;
  out/{stage0_*, bakeoff_scorecard, leave_modes_out, ypos_cache_summary} ; figures/{fig_stage0_qoi_trust,
  fig_delivery_netcg_bands, fig_graphical_model} ; data/multiref_modal/{5 drive caches incl m_ypos_990y}.
- Lead continuity updated: notes/memory.md CURRENT STATE block + one project_log row appended (checker-exact
  status). No durable-rule / sampler-standard / other-workspace edits.
- HONEST HEADLINE: WINNER per QOI (best of N=9) = L5 freq+DISCREPANCY (shear 1.9-3.2x FEM+6dB validated; normal
  2.55x honest covering, data-starved number); L5 theta-only DISQUALIFIED by leave-modes-out (widen 1.00 =
  overconfident); FEM+6dB under-covers. Next test dollar = >200 Hz plate/drumhead modal test.

## D9 (2026-07-01) — CRITICAL FIX: first bake-off was NON-DISCRIMINATING (would have been a false success)
- First bakeoff run: L5 NUTS converged clean (R-hat 1.001, ESS 2646, 0 div, 75s) BUT every method scored
  coverage=1.0 and leave-modes-out=PASS_humble, incl L5_theta_only on normal_Z. That CANNOT be right (theta_only
  MUST falsely sharpen normal). Two bugs: (1) coverage reference = the method's OWN nominal spectrum -> circular,
  trivially 1.0; (2) leave-modes-out averaged coverage over the WHOLE 45-260 band -> a localized miss at the few
  hidden-mode bins was drowned by the ~400 matching bins. Reporting this would be a fabricated-looking success ->
  REFUSED; scoring reworked before any claim.
- FIX: score coverage against an honest EPISTEMIC TRUTH ENSEMBLE (net-CG spectra with measured modes at tier-0
  freq1%/amp0.35 and unmeasured modes at tier-2 freq6%/amp0.80 = Stage-0 MC as spectra), 1-octave smoothed,
  pointwise coverage AGGREGATED with QOI energy weighting (peaks dominate). A calibrated 95% band covers ~0.95 of
  the truth ensemble at the QOI peaks. Prediction restored: theta_only (nominal amps, narrow) FAILS on normal_Z
  (mostly-unmeasured truth is wide) but passes shear; freq_discrep covers both. leave_modes_out = the same test
  with K measured modes demoted to unmeasured in the TRUTH (their true amp now uncertain) -> humble method widens.
- Checker NOT yet SHA-locked (correct) — lock only after the fixed bake-off gives a trustworthy, discriminating
  result. Do not lock a checker whose expectations were unverified.

## D10 (2026-07-01) — leave-modes-out verdict keys on WIDENING (the honest §5 test) + result reading
- Fixed-scoring run (theta cached, R-hat 1.001): 1-octave-smoothed weighted coverage is a LENIENT metric — the
  theta_only band gains width from FREQUENCY JITTER of the modes (stiffness moves peaks), which fills the octave
  band, so theta_only passes smoothed coverage even on normal (0.97). That is itself an honest methodological
  finding: 1-oct-smoothed coverage alone does NOT catch false sharpening. The DECISIVE signal is leave-modes-out
  WIDENING: when measured modes are hidden, theta_only's band does NOT change (widen_ratio 1.00 exactly — it
  ignores tiers/amplitude, so its uncertainty is INSENSITIVE to what it knows) while freq_discrep WIDENS
  (1.06-1.64). Per §5 "a method that stays narrow FAILS". So verdict = PASS_humble iff widen_ratio>=1.1 AND
  coverage-after-hiding>=0.85; theta_only -> FAIL_overconfident on every QOI (correct disqualification).
- HONEST RESULT READING (all real, checker-backed): FEM+6dB incumbent = tight (ratio 1.0) but UNDER-COVERS the
  epistemic truth (weighted cov 0.87 shear_X / 0.71 shear_Y / 0.74 normal -> it LEAKS). L5_theta_only = tight but
  overconfident (fails leave-modes-out). L5_freq_discrep = WIDER (band ratio ~1.9x shear_X, 3.2x shear_Y, 2.55x
  normal vs FEM+6dB) but COVERS (0.95-1.0) and is HUMBLE (widens under info loss) -> the per-QOI WINNER for BOTH
  shear and normal. So the honest value is NOT "sharper than incumbent" (the twin is ~2-3x WIDER) but
  "held-out-VALIDATED coverage where FEM+6dB leaks", sharp WHERE EARNED (shear tighter than normal), and the
  normal band honestly widest + flagged data-starved (drumhead shape unmeasured; needs the >200 Hz plate test).
  Winner per QOI = L5_freq_discrep (best of N=3 per QOI). Consistent with the program's standing finding that
  honest aerospace bands are wide; the win is coverage + non-overconfidence, not sharpness beating the incumbent.

## D8 (2026-07-01) — leave-modes-out as a coverage-of-plausible-truths test (self-contained, decisive)
- The humility test must have a KNOWN answer without needing the unmeasurable drumhead truth. Design: hide the
  top-K QOI-driving MEASURED modes (demote to the unmeasured tier). The epistemic truth for a truly-unmeasured
  mode is a SPREAD (amplitude ~ LogNormal(0, SD_A_U)). Generate a "plausible-truths" ensemble = full-data net-CG
  spectra where the HIDDEN modes' amplitudes are drawn from that spread (measured modes at nominal). SCORE = the
  fraction of plausible truths the METHOD's post-hiding 95% band covers (1-octave smoothed) near the hidden-mode
  freqs. A humble method WIDENS to cover (PASS); a falsely-sharp method stays narrow (FAIL). Predicted:
  L5_theta_only FAILS (propagates nominal amplitudes -> narrow regardless of what's measured); L5_freq+discrepancy
  PASSES (demoted modes get wide amp tier). This operationalizes the binding requirement + is the normal-QOI
  answer key (its real drumhead truth is unmeasurable).
- heldout_drive (SHEAR): answer key = the held-out drive's net-CG force reconstructed from MEASURED modes; twin
  band (1-oct) must envelope it. Well-posed for shear (measured modes carry it); for normal the key is incomplete
  (drumhead shape unmeasured) -> normal relies on leave_modes_out.
- MESH: given the 5.5-min-per-edit eigensolve, Stage 2 NUTS runs on the reduced K(theta) which is INDEPENDENT of
  the full-order remesh (the remesh changes A_fix/A blocks -> would need per-mesh reduced blocks, not available
  cheaply). SCOPE: run the formulation bake-off on the INHERITED reduced model; the mesh screen result is reported
  as the Axis-B finding (which meshes would be carried) + the honest note that carrying each mesh through NUTS
  needs per-mesh reduced blocks (a documented deferral, not a hidden gap). Prior evidence: remesh has ~no QOI
  leverage (plateau, 0/10 clean-improve), so this deferral is low-risk for the decision.

## D6 (2026-07-01) — MESH SCREEN scope + proxy (Axis B step 1)
- One full-order eigensolve (RS.T.T @ build_K @ RS.T then eigsh k=80) exceeds the 2-min tool timeout -> MUST run
  detached + resumable (compute protocol). 46 edits are cached but only with the IN-SAMPLE FRF-corr artifact
  (§1.1); shapes not saved -> a QOI-relevant proxy needs re-solving.
- SCOPE (autonomy "prune the wasteful"; prior evidence = remesh plateaus ~0.36-0.38, 0/10 clean-improve, box
  edits don't touch drumhead): screen a ~12-edit subset spanning the pool mechanisms — inherited(baseline),
  top in-sample performers (bottombox_E_lo, plates_E_hi, cross_bolt_trans, plates_E_lo, bottombox_E_hi),
  the plate/dish edits that COULD move the drumhead/normal modes (dish_mass_lo/hi, plates_E_lo/hi), and
  mass-distribution levers (al_rho_lo, steelLight_alHeavy). Keep top 3 + inherited = 4 meshes for the bake-off.
- PROXY (cheap, BLIND, QOI-shear-weighted): matched-mode (.ash MAC>=0.3) frequency RMS error, band-weighted to
  the shear band (114-197 Hz where the measured global modes live) + global MAC. NO amplitude LSQ (avoids the
  in-sample artifact). Labeled EXPLICITLY an imperfect PROXY: it does NOT select the twin; the post-update
  held-out-QOI bake-off (Stage 2) does. Also report each screened mesh's shift of the drumhead-mode freqs
  (230-258 Hz) = the "does it degrade NORMAL" check (freq only; amplitude/shape unmeasurable).

## D4 (2026-07-01) — CORRECTION: 3-tier uncertainty; freq-observability != shape-measurement (anti-overconfidence)
- Stage 0 v1 reclassified any coherently-observed mode as "measured" for the +Y scenario -> tray_normal_Z trust
  jumped 45%->96%. WRONG: coherent FRF peak = FREQUENCY observability, NOT the net-CG PARTICIPATION (which needs
  the mode SHAPE at the plate). The 234-254 Hz drumhead modes are freq-observable (peaks in +Z/+XY/+X; +Y uniquely
  adds 230.6 Hz) but their SHAPE is unresolved (2026-06-23: instrumented sensors miss the plate center; perimeter
  sits on the drumhead node ring). Presenting 96% would be the exact false-sharpening the selection rule DISQUALIFIES.
- FIX: 3 uncertainty tiers per mode. (0) shape-measured = .ash MAC-match: freq SD 1% + amp/shape SD 0.35.
  (1) freq-observed only (coherent peak, no .ash shape): freq SD 1% (anchored) BUT amp/participation SD 0.80
  (shape still unmeasured). (2) prior: freq SD 6% + amp SD 0.80. TRUST stays tied to SHAPE knowledge (.ash), so
  tray_normal_Z trust stays ~45% (honest). +Y's REAL value = adds frequency observability (esp. the unique 230.6
  Hz peak) which can tighten a freq-based method's peak PLACEMENT, but does NOT resolve the net-CG amplitude ->
  the normal band stays wide. Report the band under (shape-only / +freq-obs-without-Y / +freq-obs-with-Y) to
  quantify exactly how much +Y buys. This is the honest low-trust-normal story the prompt wants.

## D5 (2026-07-01) — STAGE 0 RESULT (3-tier, honest; stage0_*.json)
- 40 in-band modes; 20 shape-measured (.ash MAC>=0.3); freq-observed 20 (no +Y) -> 23 (with +Y). +Y uniquely
  adds frequency observability at 151.9, 152.2, 230.6 Hz (230.6 = a drumhead-band mode NO other drive saw).
- TRUST (shape-based) / band factor(shape-only -> with +Y freq-obs):
  tray_shear_X 96% / 3.2x->3.2x ; tray_shear_Y 94% / 3.7->3.7 ; tray_normal_Z 45% / 6.6->5.7 ;
  base_shear_X/Y/Z 98/97/99% ; mount_response 13% / 14.6->10.2 (reproduces the known 14.6x wall).
- HONEST distinction the prompt's premise blurred: the NET-CG normal force over the tray (tray_normal_Z, 45%,
  6.6x) is LESS catastrophic than the POINT response at plate center (mount_response, 13%, 14.6x) because the
  net integral partly averages the drumhead; but tray_normal_Z is still ~55% driven by drumhead modes whose
  SHAPE is unresolved -> data-starved for the NUMBER. +Y's value = frequency anchoring (band 6.6->5.7x, ~14%),
  NOT shape resolution.
- VALIDITY: tray_shear_X/Y = PASS_NUMBER (held-out drives discriminate); tray_normal_Z = PARTIAL (number partly
  data-starved; keeps its bake-off place via the leave-modes-out mechanism test per §5). Autonomy rule: do NOT
  stop on normal; deliverable = covering band + leave-modes-out validation + >200 Hz plate-test recommendation.
- SENSITIVITY (stage0_sensitivity.json): unmeasured-mode sigma swept /2,x1,x2 on SD_F_U(0.06) & SD_A_U(0.80);
  the normal band factor is load-bearing on SD_A_U (amplitude) more than SD_F_U (freq) -> the amplitude
  assumption is the one to surface. (Read exact grid from JSON for the ledger.)

## D3 (2026-07-01) — "+Y folded in" = observability, not new shapes
- The .ash Final_FF_Test_Shapes mode set (drive-independent) anchors mode SHAPES; a mode is "measured-shape"
  if MAC-matched to an .ash mode (as in qoi_trust_table). +Y (a new DRIVE) does not add .ash shapes; it adds
  OBSERVABILITY: does some drive coherently excite/measure a mode? Stage 0 reports per-drive coherence-at-mode
  for all 5 drives and a "+Y-folded" trust scenario (measured = ash-matched OR coherently observed by >=1 drive
  incl +Y). Directly answers "does +Y lift NORMAL trust / observe the 232-254 Hz modes." +Y cache already shows
  coherent peaks at 231.9 & 254.3 Hz (build result) — Stage 0 quantifies whether that is enough.

- RESULT (build_ypos_cache.py, 7s): m_ypos_990y.npz built — 4 hits, N=122880, df 2.03 Hz, 105 freqs, 111 ch,
  coherence median 0.850 (good). Modal peaks [97.7, 138.3, 152.6, 162.8, 189.2, 197.3, 231.9, 254.3] Hz.
  KEY: +Y shows peaks at 231.9 & 254.3 Hz = ENERGY IN THE UNMEASURED NORMAL-MODE BAND (~234-254 Hz drumhead).
  This is the observability lever the prompt hoped for → Stage-0 trust table must quantify whether +Y actually
  OBSERVES those modes (coherence at those peaks) enough to lift NORMAL trust. Large .mat deleted (disk 7.9GB);
  zip retained at repo root (re-extractable). All 5 drive caches now in data/multiref_modal/.
