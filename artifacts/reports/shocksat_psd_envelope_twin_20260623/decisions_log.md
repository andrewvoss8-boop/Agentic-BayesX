# Decisions log — ShockSat PSD-envelope twin (vs FEM+6 dB), multi-reference modal data

Workspace: `artifacts/reports/shocksat_psd_envelope_twin_20260623/`. Lead-as-runner. Re-ground from
`notes/memory.md` CURRENT STATE (2026-06-23) + `../shocksat_multiref_explore_20260623/exploration_findings.md`.

## D0 — THE DELIVERABLE (Andrew, 2026-06-23)
Held-out-SENSOR response-PSD prediction on ShockSat. Over leave-sensors-out splits with 50–90% TRAINING, at
each held-out sensor compare a smooth **envelope over the peaks** of (a) the original FEM PSD **+6 dB** and (b)
the twin's **upper credible band** PSD. **GOAL/WIN:** the twin's upper-band envelope has a **lower GRMS** than the
FEM+6 dB envelope **while still enveloping** the measured held-out data. = the §5.6 less-conservative-yet-defensible
qualification-spec value endpoint / §2.2 response-limit proxy. Honest negative is a valid outcome.

## D1 — Q1..Q5 answers (Andrew, 2026-06-23), LOCKED
- Q1 PSD = **response PSD = |H(f)|² · S_F**, S_F = FLAT input, IDENTICAL for FEM and twin (default). Since S_F is
  flat and common, the GRMS comparison reduces to |H|² envelopes (S_F0 cancels in the ratio; report S_F0 = 1 lbf²/Hz).
- Q2 envelope = **peak-pick + piecewise-linear connect in log–log**, IDENTICAL algorithm for FEM+6 dB and twin.
- Q3 coverage = **report dB-EXCEEDANCE, energy-weighted** (NOT binary cover). A small exceedance where the FRF is
  already low ≈ negligible GRMS contribution = not problematic. Report max exceedance + the GRMS fraction it carries.
- Q4 "upper 95% CI" = **TOP of the 2-sided 95% shaded band = the 97.5th percentile** of the posterior predictive
  PSD (what we have plotted all along; slightly HARDER bar than a one-sided 95th — accepted).
- Q5 splits = **leave-sensors-out, 50→90% training, MC over splits**; eligible = good channels (DR gate). Start 90%.

## D2 — DATA: clean modal multi-reference set, BOTH drive nodes (Andrew "fold in both nodes", 2026-06-23)
Basis = **Test01 (+X, node 990) · Test02 (+Z, 990) · Test04 (+XY, 990) · Test06 (+Z, node 900)**, all ModalHammer,
6 roving hits each, consistent Dytran 5850B force instrument. From `exploration_findings.md`:
- Samples are in ENGINEERING UNITS (accels in g, force in lbf); |H| direct in g/lbf (no per-channel cal / no volts /
  no ×100 gain needed — the ×100 fudge in Card A was an artifact of the noise-limited Test07 tap).
- Records are PRE-TRIGGERED (impact @ ~125,009 samp = 500 ms) → window N = 122,880 (0.49 s ring-down, df ≈ 2.03 Hz).
- 6-hit coherence 0.71–0.93 median / 0.90–0.97 at peaks (clean). DROP SNR-limited impact taps (Test07/08/10) from the
  amplitude basis (a ~1.3 lbf tap is too weak for 100k-g shock accels). Keep Test07 only as a labeled cross-check.
- Each test = a small ROVING cluster (6 nearby impact points) → OK for global frequencies; treat per-hit for
  amplitude/shape. df ≈ 2 Hz is coarse vs a 1% mode's half-power bandwidth (~2 Hz @ 100 Hz) → damping marginally
  resolved (Discretization Gate item; NASA per-mode modal ζ from the .ash modal test is the better damping source).

## D3 — TWIN (reuse, byte-identical; SHA in REUSED_code.sha256)
Reuse the CONVERGED L5/Card G modal-feature pipeline: θ calibrated from matched modal FREQUENCIES (NUTS, converged
in prior cards), held-out prediction by modal superposition from FEM/ash shapes φ + damping + ONE training-global
units-gain c (never per-held-out, never peak-tuned). Multi-reference improves θ (more modes), damping, and drive-side
shapes. **HONEST CEILING (Card G, independent of drive quality):** the held-out SENSOR's own shape φ_s is FEM-only;
multi-reference fixes the DRIVE side, not φ_s. The envelope-GRMS reframe is the lever that CASHES the (real, strong)
frequency skill + damping into less conservatism vs FEM+6 dB — the validity probe decides if it wins.

## D4 — PLAN: validity probe FIRST (validity-before-rigor, lessons #2)
Build data caches → twin calib at ONE 90%-training split → new PSD-envelope-GRMS QOI + FEM+6 dB + exceedance scorer →
look: does the twin 97.5% envelope beat FEM+6 dB on GRMS anywhere, and where? If flat loss → reframe is cosmetic,
pivot. If wins where FEM over-predicts → proceed to immutable check.py + full 50→90% MC sweep + figures + packet.
NO success claim from the probe (exploratory/YELLOW by default).

## D5 — drive coordinates (from TestLog_Tap impact-point centroids; filename direction reliable, "Face" text = artifact)
Test01 +X ≈ (9, 7.6, 0.6) axis X · Test02 +Z ≈ (9, 7.8, 0.0) axis Z · Test04 +XY ≈ (9, 9, 1.1) axis XY (combined →
handle X & Y components) · Test06 +Z ≈ (9, 0.0, 0.0) axis Z. Mapped to a reduced drive row via realfrf.reduced_row.

## D6 — TWO QOI variants (Andrew, 2026-06-23): per-reference (split out) + ONE combined-correlated
Predict the held-out sensor's response PSD in TWO ways, both scored the same (envelope GRMS vs FEM+6 dB, exceedance):
- **(a) per-reference (split out):** for each drive dᵢ, S_{s,i}(f) = |H_{s,dᵢ}(f)|²·S_F; validated against that
  reference's measured FRF. 4 results per held-out sensor (one per modal reference).
- **(b) combined uniform-correlated:** a single coherent input applied at all drives simultaneously, uniform
  magnitude, fully in-phase ⇒ S_{s,comb}(f) = |Σᵢ H_{s,dᵢ}(f)|²·S_F (COHERENT complex sum BEFORE squaring); the
  measured target is the identical coherent sum of the measured FRFs |Σᵢ H^meas_{s,dᵢ}|². The coherent sum needs the
  COMPLEX forward (realfrf.fem_logmag returns magnitude only) → new `psd_forward.py` (validated to match
  realfrf.fem_logmag's |H|). Default drive set for (b) = independent DOFs {990X, 990Z, 900Z} to avoid the +XY/+X
  double-count at 990 (XY available as a labeled alternative). +XY drive row modeled as (X-row+Y-row)/√2 (documented).
This contrasts WHERE the conservatism comparison lives: each single drive vs a realistic multi-point correlated
environment (closer to a flight/qual base-drive). S_F flat & common ⇒ S_F0 cancels in every twin-vs-FEM GRMS ratio.

## D7 — VALIDITY PROBE RESULT (2026-06-23): robust HONEST NEGATIVE (the reframe alone does NOT win)
Probe at seed0/90%-train (8 held-out sensors; calib converged R-hat 1.002, ESS 1758, 0 div, 22 pooled modes;
`out/probe_seed00.json`). Building blocks validated (complex forward = realfrf to 1.8e-15; envelope self-test PASS).
- **Units-gain ≈ +0.05 (×1.05)** — the CLEAN modal FEM is essentially on the right absolute scale (vs the ×100 fudge
  the noise-limited Test07 needed). Good news, and it confirms the noise-tap diagnosis.
- **Per-channel FEM-shape error is the ceiling, quantified (misalignment-free, calibrated model, 336 obs ch×ref,
  `diag_sigma.py`):** all-peak σ=1.60 (MAD 1.49), dominant-peak σ=1.21, **band-GRMS σ=0.97 (≈×2.6/channel)**. The twin's
  honest 97.5% covering band is therefore +27 dB in PSD → GRMS ratio ~10–13× vs FEM+6 dB → **0% win, all references
  and the combined-correlated case.** To WIN the twin needs σ ≲ 0.35 (×1.4); we are at 0.97–1.60. NOT a σ-artifact
  (robust MAD agrees), NOT a sampler/convergence issue, NOT a units issue.
- **FEM+6 dB does NOT envelope the data either:** median exceeding-energy fraction 0.336 (34%), 82% of channels exceed
  >2%. So the user's premise ("beat FEM+6 dB which envelopes the data") does not hold on this structure — the
  per-channel shape error is so large that NEITHER a +6 dB FEM margin NOR a reasonable-width twin covers; only a ~+27 dB
  band covers. Twin and FEM share the SAME held-out-node FEM shapes → the twin cannot be meaningfully tighter than a
  fair FEM+margin (they have the same shape error).
- **VERDICT:** the smoothline/envelope reframe + clean multi-reference data is, for the GRMS-WIN goal, a documented
  HONEST NEGATIVE — confirming/quantifying §7.1 ("the gap is FEM shape fidelity; the fix is a better MODEL, not
  cleverer statistics") and the Card G φ_s ceiling, now on CLEAN data with the aerospace-standard metric. The lever
  that would move it = reduce per-NODE shape error (better FEM / agentic correlation / a per-node shape correction;
  measured-shape interpolation was ~null in Card G D16) — a ~3–5× σ reduction. STOPPED before the full MC/checker/
  figures (no point spending compute to dress up a known negative); SURFACED to Andrew for steer on re-posing.

## D8 — DAMPING lever experiment (`damping_rerun.py`, `out/damping_rerun.json`)
- (A) Global damping is only PARTIALLY gain-absorbed: twin global ζ 1→3→5% (FEM 1%) drops median GRMS ratio
  10.6→7.7→6.5. Real effective damping (~3–4%, from the 25 vs 33 dB dynamic-range gap) helps ~11×→~7×, still loses.
- (B) Per-mode HALF-POWER extraction is resolution-limited at df≈2 Hz (0.5 s modal ring-down) → floors ζ≈1.1%
  (under-reads the true ~3–4%); full-peak-shape / learn-as-parameter resolves it, half-power can't.
- DAMPING APPROACH LADDER (Andrew): (1) half-power extract [coarse, df-limited]; (2) learn-as-parameter via the
  FULL peak shape (Lorentzian/SDOF/circle-fit → posterior, resolves ~3–4%); (3) elemental/material damping in the
  FEM (Rayleigh / structural loss factor / per-PID / CBUSH-joint η); (4) Das–Debnath complex/non-proportional
  (complex modes). The GAIN absorbs GLOBAL damping → the lever the gain CANNOT absorb is NON-UNIFORM (per-mode/
  region/complex) damping = rungs 3–4. VERDICT: damping necessary, ~11×→~7×, NOT sufficient; refine later.

## D9 — PIVOTAL SHAPE DIAGNOSIS (`shape_diag.py`, `out/shape_diag.json`): shapes ARE the reducible lever (clean data)
On the CLEAN +X modal data (seed0, 90% train, 20 matched .ash modes), predicting held-out peak |H| with MEASURED
.ash shapes vs FEM shapes (same construction/split/poles/damping, only the SHAPE differs):
- **held-out peak σ: FEM-shape 1.26 → MEASURED-shape 0.70** (median |err| 18→8.7 dB) ⇒ shapes nearly HALVE σ.
  **This OVERTURNS Card G/D16 ("shapes don't predict amplitude", ~0.15 corr) as a noise-limited-Test07 ARTIFACT.**
- FEM-vs-.ash MAC: median 0.70, min 0.34; 10/20 modes <0.7, 3 <0.5; worst @ 190/196/70/75/158 Hz.
- STRAIN-ENERGY targets (where to remodel): worst-MAC modes 70/75/190/196 Hz are **bottom_box 95–97% SE**; 151/158 Hz
  = top_box 41–80% / plates 29% / joints 19%. ⇒ **bottom_box is the primary remodeling target**, top_box/plates 2nd.
- Floor: measured-shape oracle σ≈0.70 is the best shapes alone can do (residual = near-field/non-modal + meas). To
  WIN need σ≲0.35; shapes (→0.70) + damping (~/2) gets CLOSE (ratio ~1–2×) → remodel + damping, possibly + re-pose
  (iso-coverage / regional). NOTE Card D found θ/mesh-density don't move shapes → remodeling must be ARCHITECTURAL
  (element formulation / connectivity / mass / missing feature in bottom_box), = the agentic-FEM-remodel direction.
- NEXT: agentic remodeling of bottom_box (then top_box/plates) scored on the CLEAN-data MAC + σ + envelope-GRMS
  (not the old noisy MAC). Reuse shocksat_fem_remesh_20260618/edit_solve.py machinery.

## D10 — Remodeling GO (Andrew 2026-06-23) + deck/drawing GROUNDING (frangible joint NOT in modal test)
Andrew: "frangible joint is NOT in the modal test data" (don't model it; bottom_box free at bottom) → GO on the
bottom_box remodeling + "fetch the drawings." FEM_and_CAD.zip (1.89 GB) was ALREADY local
(`shocksat_statfem_runner_20260609/sources/`); extracted 13 drawing PDFs + STEP CAD + the full NASTRAN deck (.blk per
group) to `cad/`. **GROUNDED FEM properties (from the deck, not blind):**
- bottom_box PSHELL thickness: shell_101 0.118″, 102 0.125″, 103 0.118″; cross_beam shell_401 0.125″ (check vs drawings).
- joints PBUSH 801–807 = tuned 6-term K with SOFT rotational DOFs (e.g. 801 rot=12240 among 1e6–1e7) → panel-edge
  fixity already partially released = the knob that sets thin-panel shapes.
- Modal_Test_Instrumentation_092721.blk = 84 CONM2 accel point-masses (≈6.8 g each, 0.635″ standoff) modeled, **but NO
  cable-harness mass** ⇒ Andrew's "cables not strain-relieved" is a REAL, MODELABLE gap (accel chips in, cable bundles
  out) + a non-linearity source (un-modelable → part of the σ≈0.70 floor; at-peak coherence 0.90–0.97 bounds it as modest).
- REMODEL TARGETS (grounded, ordered): (1) cable-harness mass (NEW, from Andrew — add distributed mass along panel
  cable runs); (2) bolted-joint PBUSH 801–807 edge fixity (esp. soft rot terms); (3) panel thickness vs drawings;
  (4) cross-beam connectivity + damping-material mass. Reuse edit_solve.py (per-PID K blocks + M + T, eigsh80,
  ~5 min/solve) EXTENDED for mass edits; score on CLEAN-data MAC + σ (shape_diag) + envelope-GRMS. Launch detached/
  resumable (compute protocol). Drawings = deliverable fetched ✓.

## D11 — wave-1 results, MAC-is-wrong-lens, cable-nonlinearity ID, cable-damping = SIMPLEST (Andrew)
- WAVE-1 campaign DONE (9 variants, `out/edits/*/result.json`). Scored on MAC: cable_mass_hi best GLOBAL MAC
  (0.631→0.657, physically grounded = the missing cable mass), all else trade-offs (joint_soft helps 70/75 0.51→0.56
  but hurts 190; cross shuffles); worst bottom_box modes 70/75 Hz (MAC ~0.50) resist ALL wave-1 edits.
- **ANDREW: "MAC masks major discrepancies in local FRFs — look at the FRFs too."** Built `fig_local_frf.py`
  (`figures/local_frf_overlay.png`, tufte+lint clean): even best channels (log|H| corr 0.73–0.76) have peaks at WRONG
  freq+height; typical ch 0.3–0.5. ⇒ MAC (modal corr 0.6–0.9) MASKS the per-channel FRF error that drives σ. **So
  wave-1's MAC ranking is the WRONG lens for our deliverable; do NOT launch wave-2 on MAC.**
- **CABLE NONLINEARITY ID** (`nonlin_id.py`, `out/nonlin_id.json`): force-normalized FRF over 6 hits (force ×1.4–2):
  modest amplitude dependence — modes SOFTEN + peaks BROADEN (apparent damping RISES) with force, clearest +Z (4/8
  modes, median dDR −1.23 dB/efold); +XY/+X weak/mixed. ⇒ SOME apparent damping IS amplitude-dependent/nonlinear
  (cable/joint friction), but SECOND-ORDER (at-peak coherence 0.90–0.97); most of the 25-vs-33 dB damping gap is
  structural+window. Bounded: force lever ×2 + df 2 Hz = a SCREEN not a definitive ID (needs a controlled amp sweep).
- **CABLE-DAMPING MODELING DECISION (Andrew "simplest choice first"):** use a SINGLE CONSTANT effective modal damping
  taken from the data (lumps structural+window+modest cable), FLAGGED as test-amplitude-specific (won't transfer to
  flight). NO Iwan/Bouc-Wen, NO ζ(amplitude) fit. Simplest; revisit only if it blocks the deliverable.
- **σ RE-SCORE launched** (`rescore_sigma.py`, PID 47116, detached, ~45 min, resumable, saves channel modes): re-solve
  each wave-1 variant, score on the REAL held-out σ (local-FRF, not MAC) [baseline 1.26, oracle 0.70]. Decides
  wave-2-on-σ vs re-pose. Bug fixed pre-launch: ch.nodes is a grid INDEX not GID (dropped a bad G2I lookup).

## D12 — PIVOT to brute-force FEM correlation (Andrew): all data, no held-out/Bayes, 100% damping freedom, chase FRF+MAC
- σ re-score CONFIRMED negative (`out/rescore_sigma.json`): NO wave-1 edit reduces held-out σ (best cross_stiff 1.027
  vs baseline 1.077; oracle 0.70); MAC ANTI-correlated with σ (cable_mass_hi best MAC 0.657, worst σ 1.281). Regional
  coverage RULED OUT by Andrew (tried elsewhere, no gains).
- Andrew "I'm lost — why does nothing match the FRFs?" → gave the physical answer: per-point FRF amplitude = sensitive
  interference of a DENSE modal forest (16–44 modes/band); small per-mode local-shape errors compound; frequencies
  (global) robust, per-point amplitude (local) fragile; MAC (global) masks it. Floor even w/ measured shapes (σ0.70) =
  near-field + cable nonlinearity + mapping.
- Andrew: "remeshing can address some of this; keep working creatively on the FEM, make FRFs AND MAC match; throw out
  train/test + Bayes; BRUTE FORCE a correlated FEM with ALL data + 100% damping freedom."
- **CHECKED Andrew's snap hypothesis (data):** snap is SUB-INCH (median 0.15″, max 0.75″ — channel_map has explicit
  fem_grid; .ash at instrumentation grids 1101+) → nodes-at-sensors remesh won't help. Card D: mesh CONVERGED (0.25″)
  → uniform refinement won't help. ⇒ remeshing helps ONLY by fixing GEOMETRY/FEATURES (joint contact, bolted-cross
  connectivity, welds, accel standoff), NOT density/placement. Lever = MODELING/architecture + full damping.
- **BRUTE-FORCE OBJECTIVE built (`correlate_all.py`):** all 4 modal refs, FULL per-mode MEASURED damping, per-mode
  participation LSQ to ALL channels (no held-out); score FRF log|H| corr + peak-ampl-err + MAC. **BASELINE (full
  damping): FRF corr median 0.30 (28% ch >0.5), 15.7 dB ampl err, MAC 0.631** ⇒ damping freedom does NOT fix FRFs;
  SHAPES are the wall (confirmed from the correlation side).
- **SEARCH LAUNCHED (PID 14260, detached ~65 min):** 13 untried edits — DIRECTIONAL joint stiffness (6-term PBUSH
  ratios: rot/trans soft/stiff — the panel-edge-fixity lever wave-1 never varied) + per-region E (bottom_box/top_box/
  plates) + combos. HONEST PRIOR: parameter edits likely plateau (wave-1 + baseline-full-damping evidence); if so the
  real lever is a GEOMETRY/architecture rebuild from the CAD/STEP (on disk) — escalate there. NO held-out/Bayes/
  durable-rule/checker/project_log/vision edits.

## D13 — Cross-attachment connectivity surgery (the genuinely-new architectural lever)
- Andrew asked "what is the CAD rebuild?" → explained: re-model the FEM's IDEALIZED features (bolted joints, cross,
  welds) from the actual CAD/drawings at higher fidelity. Honest: big effort, no guarantee (already NASA-correlated),
  different philosophy than the robust-coarse twin. Tractable MIDDLE GROUND = connectivity/topology edits in the
  EXISTING mesh; full STEP re-mesh only if a specific feature demands it.
- Parameter search (correlate_all, running): NOT helping — baseline FRF corr 0.296, joints_rot_soft 0.210 (worse).
- **KEY CONNECTIVITY FINDING:** the internal cross (shell_401, 1709 nodes) shares 0 nodes with the walls (NOT welded)
  and is attached by only ~13 points (5 CBUSH pid99 + 8 RBE2 nodes) — yet **68 cross-edge nodes sit coincident (<0.2″)
  on the walls but are LEFT UNCONNECTED.** The real bolted cross (photo bolt-rows) is attached far more ⇒ the FEM
  UNDER-attaches the cross → panels & cross move too independently → wrong local shapes. Parameter-scaling can't fix
  this (it's topology). = the genuinely-new lever.
- BUILT connectivity surgery: `remodel.build_couple_K` adds a 6-DOF spring at each coincident pair; correlate_all
  edits **cross_bolt (k1e6) / cross_weld (k1e8) / cross_bolt_trans (translational only, rot free)** couple the 68
  pairs. Sanity OK (assembles, adds stiffness). **QUEUED after the param search** (chain PID 16004 waits for PID 14260,
  then runs all — skips done param edits, runs the 3 cross edits). The decisive test: does densifying the cross
  attachment raise FRF corr above 0.296 / MAC above 0.631? CHECK out/edits/cross_*/correlate.json next turn.
  Standoff lever DROPPED (geometry: normal-offset × rotation ⟂ normal axis ⇒ ~0 first-order for normal accels).

## D15 — usable-mean + held-out-mean = NO twin advantage; remeshing param-plateau; cross surgery running
- USABLE-MEAN structure spec (`usable_mean.py`): the structure-level MAX-envelope IS robust to per-channel shape
  error (washes out), so a spec is buildable — BUT fair (each model + its margin-to-just-cover): un-updated FEM 59.2
  GRMS (+1.7 dB) < freq+damping-corrected 72.9 (+1.2 dB); the "25% win" was an artifact of FEM+6dB blanket margin.
  Correlation does NOT make the envelope less conservative.
- HELD-OUT MEAN (`heldout_mean.py`, Andrew "run it"; seeds0-1×frac0.7/0.9): NO twin advantage. correlated 55.6 GRMS /
  0.75 cover vs un-updated 20.2 / 0.25 cover — correlated covers more but at far higher GRMS (needs ~9 dB margin
  because correct damping LOWERS peaks → under-predicts worst held-out channel); un-updated lower GRMS but UNDER-covers
  (unsafe). Neither generalizes cleanly (per-channel shape error). **VERDICT: twin/correlation shows NO amplitude/spec
  value across ALL framings tested (per-point CRPS, 97.5% envelope, structure-mean, held-out-mean). Frequency (+0.93)
  is the only demonstrated value. Wall = per-channel mode-shape fidelity, irreducible by available levers.**
- REMESHING correlation campaign (`correlate_all.py`, all-data FRF corr + MAC, full damping): 13 PARAMETER edits done
  → best FRF corr 0.359 (bottombox_E_lo) vs baseline 0.296 = MODEST plateau; joints/combos HURT. **Cross-connectivity
  surgery (cross_bolt/weld/bolt_trans — the genuinely-new architectural lever, densify the under-attached cross)
  NOW RUNNING** (killed the last low-value param combo to unblock it); result ~15–20 min. Check out/edits/cross_*/correlate.json.
- NEXT after cross result: (b) interface apparent-mass/virtual-point (the one untested framing, 7004C endpoint) OR
  consolidate the honest frequency-value + amplitude-wall finding. Recommend (b)-then-consolidate.

## D16 — RESIDUAL-MAP-GUIDED remeshing (Andrew's method) → remeshing line DEFINITIVELY CLOSED
- Andrew: "are we doing a point-by-point, freq-by-freq analysis of how/where the FRFs mismatch to GUIDE remeshing?
  if not, do that." We weren't (aggregate-score blind edits). Built `residual_map.py` (`figures/residual_map.png`):
  residual = log|H_meas|-log|H_FEM| with FEM freq+damping ALREADY corrected → isolates the SHAPE error.
- MAP FINDINGS: WHERE = worst at the FREE bottom −Y corner (ch13/19, z≈2, RMS ~3.0), graded upward (region RMS
  bottom 2.0 → top 1.6); WHICH MODES = 54 Hz fundamental + 150–210 Hz cluster (100–130 Hz is fine); FEM UNDER-predicts
  (too stiff). GEOMETRY: bolted joints are all UP HIGH (bush mean-z 18–57); the worst zone is the FREE END (no joint)
  → free-edge/corner PANEL dynamics, not joint fixity.
- MAP-GUIDED edits (`guided_remesh.py`): soften bottom panels ×0.7/×0.55 → FRF corr 0.329/0.332 — WORSE than the
  blind ×0.85 (0.359). So map-guided targeting does NOT beat the shallow ~0.36 optimum. **Aggregate-blind +
  architectural-cross + MAP-GUIDED remeshing ALL plateau at FRF corr ≈0.36 → remeshing CANNOT crack per-point FRF
  correlation. DEFINITIVELY CLOSED.**
- 54 Hz REAL-GAP check: measured fundamental's best match over ALL FEM modes = MAC 0.12 → no FEM mode reproduces it.
  FEM has right fundamental FREQUENCY (54.6≈54.2) but WRONG SHAPE (right eigenvalue, wrong eigenvector). The FEM's
  shapes are wrong even at the fundamental; only a from-scratch CAD/geometry rebuild could possibly fix shapes (major
  gamble — vendor already correlated; the 54 Hz gap may be suspension/local/intrinsic). NOT recommended next.
- VERDICT (comprehensive): per-point FRF amplitude/shape is unachievable by ANY available means (data quality, damping,
  all remeshing incl. map-guided). Twin's value = FREQUENCY only. NEXT: (b) interface apparent-mass (sidesteps the
  shape wall, 7004C endpoint) + consolidate. Remeshing/FRF-correlation line honestly EXHAUSTED.

## D17 — MODEL-FORM not exhausted (Andrew pushback, correct): mass/stiffness DISTRIBUTION sweep (CAD/photo-informed)
- Andrew (right): "error is model form, we can change model form, can't be exhausted." I over-claimed "closed";
  we'd only varied stiffness MAGNITUDES (+ one connectivity + damping + map-guided), NOT the deeper model-form space.
- ANNOTATED PHOTO + CAD revealed the structure: **TWO MATERIALS** — heavy STEEL bottom (bottom_box 101-103, MAT1002
  E27e6/ρ7.4e-4) + light ALUMINUM top (top_box 201-203, MAT1001 E9.7e6) — joined by the bolted joint; thick aluminum
  DISH plates (501/601/701, 0.78-1.0″) + struts on top; welded(+damped) bulkheads; shock-source base at bottom.
- DIAGNOSIS reframed: "right fundamental FREQ, wrong SHAPE, worst at the (steel) free bottom" = a mass/stiffness
  DISTRIBUTION error between the steel-bottom and aluminum-top. **We NEVER varied DENSITY/MASS distribution** (only E).
- Andrew "you have CAD+images, make the call or sweep all." MY CALL: implemented a genuine new model-form lever —
  region MASS-scaling (`build_M` mass_scale via D·M·D over shell-group nodes) — and added FUNDAMENTAL-mode MAC tracking
  to the scorer. SWEEP LAUNCHED (`modelform_sweep.py`, PID 86544, ~1 hr, ~14 edits): steel/aluminum E AND ρ balance,
  dish mass, steelLight_alHeavy / steelHeavy_alLight, combined material changes, combo_shift. KEY metric = does the
  54 Hz fundamental MAC climb from 0.12 toward >0.5 (a real shape fix)? FRF corr + global MAC also tracked.
- If fundamental MAC climbs → found the model-form fix (mass distribution). If not → distribution levers genuinely
  tried (honest). NEXT after: RBE2 flexibilization (struts/bolt connections, needs T-rebuild) + damping-layer +
  geometry/element-formulation — the remaining untried model-form space. CHECK out/modelform_sweep.json next turn.

## D18 — Model-form DISTRIBUTION sweep result + the 54 Hz PHANTOM correction (honest)
- **SELF-CORRECTION:** the "54 Hz fundamental shape gap (MAC 0.12/0.17)" I chased was a METRIC ARTIFACT — it came
  from the residual_map operating-deflection-shape at one freq bin / nearest-freq pairing, NOT the proper .ash modal
  MAC. The .ash fundamental MAC is **0.97 and ROBUST** across all sweep edits (opposite directions both 0.97), and
  shape_diag had already shown the worst .ash modes were 70–196 Hz, not 54. The fundamental was never the gap; the
  real shape error is the MID-BAND (70–196 Hz) modes (low3 MAC ~0.48–0.52). My interpretation error, flagged.
- DISTRIBUTION sweep (`modelform_sweep.py`, 13 edits; new build_M mass_scale lever): BEST = **al_rho_lo (lighten
  ALUMINUM top ρ×0.8) FRF corr 0.379**, dish_mass_lo (lighten dish) 0.365, al_stiff 0.349 — i.e. **the FEM's TOP MASS
  is too heavy; lightening the aluminum top + dish is a real, physical model-form correction** and the first to beat
  the prior 0.359. BUT modest (0.30→0.38, still far from usable ≫0.5); steel ρ-up/down and heavy-top edits worse.
  Fund MAC 0.97 throughout.
- COMPUTE-HYGIENE BUG (logged): killed "86120" earlier = the shell wrapper, NOT its python child (86126) → orphaned
  buggy sweep ran alongside the fixed one (86544) → 2 concurrent 400k shift-invert factorizations → memory thrash
  (~80 min/edit). Killed 86126 → sweep unblocked (~5–8 min/edit). LESSON: pkill -f / kill the child, not the echoed PID.
- CHAINED `combo_followup.py` (PID-chain after 86544): combine the WINNERS — lighten aluminum + lighten dish
  (lighten_top / _strong / _alstiff) — the sweep never combined them. Does combining push past 0.38? CHECK out/edits/
  lighten_*/correlate.json next turn. VERDICT FORMING: distribution lever gives a real top-mass-too-heavy correction
  but the same ~0.38 plateau; mid-band shapes remain the wall. Next deeper model-form: RBE2 flexibilize + damping-layer.

## D19 — LAST model-form lever built: strut-RBE2 flexibilization (`rbe2_flex.py`)
- RBE2 classification: all 150 are STRUCTURAL (0 instrumentation — safe to release); 94 in the top (z>24, struts/dish,
  some CM=123456 FULLY RIGID), 56 mid (joint/bulkheads). The photo shows the struts are SLENDER → modeling them as
  rigid spiders is a real model-form simplification, and it's connected to the top-mass-too-heavy finding (rigid struts
  = dish is a rigid lump; flexible struts let it move).
- BUILT `rbe2_flex.py`: replicate assemble_fem.build_T with an EXCLUSION set (release the 94 top strut RBE2 → their GM
  DOFs become independent) + reconnect each released GN->GM with a finite-stiffness CBUSH (offset B-matrix), swept
  rigid→soft (1e7/1e5/1e3). VALIDATED: build_T_excluding(set()) reproduces the saved T EXACTLY (399,510 cols);
  releasing struts frees 3,060 DOFs; CBUSH assembles. Scores MAC + fundamental MAC + mode freqs (FRF-corr would need
  the forward re-wired through the new T; MAC is the clean shape metric for the go/no-go).
- CHAINED (PID 34794) after sweep+combo (sequential, no contention). HONEST EXPECTATION: struts are TOP, worst residual
  is BOTTOM, and 6 prior levers all hit ~0.38 → breakthrough unlikely, but it's the genuine last untried model-form
  change + builds on the top-mass positive. Full model-form queue (~55 min autonomous): distribution → combo → strutflex.
  After this: model-form genuinely exhausted → consolidate OR (b) interface apparent-mass. CHECK out/edits/strutflex_*/correlate.json.

## D20 — PACKET delivered (Andrew request): mods + FRF comparisons + Bayesian updating on the updated FEM
- Strut-flex result (last lever, complete): rigid limit recovers baseline (MAC 0.631, validates build); softening
  helps mid-band low3 MAC 0.52→0.66 but lowers global MAC (→0.557) + spurious 10 Hz modes → trade-off, no win.
  Combining the distribution winners (lighten Al+dish) → FRF 0.245 (WORSE, doesn't stack). Best stays al_rho_lo 0.379.
- `packet.md` written. Three parts: (1) MODS table (model-form campaign; best = top-mass-too-heavy / lighten aluminum
  top, 0.379; honest plateau ≤0.38 across 7 levers); (2) FRF COMPARISONS `figures/frf_comparison_grid.png` +
  `out/frf_comparison.json` (original vs data vs updated [measured freq+damping]; median log|H| corr 0.269→0.338, 70%
  of channels improve, peaks aligned + heights set, residual shape wall honest); (3) BAYESIAN UPDATING
  `out/bayes_update.json` — modal-feature NUTS, CONVERGED (R-hat 1.002, ESS 2243, 0 div), held-out modal-freq coverage
  0.75, freq err 3.33%→2.68% vs nominal. Built deterministic FRF synth (physics participations + 1 gain, no per-ch fit).
- VERDICT (packet §1): frequency+damping twin + top-mass model-form correction = real/validated; per-point amplitude
  spec = unachievable (per-channel mid-band shape wall, 7 levers). Next = (b) interface apparent-mass (sidesteps wall)
  or accept. NO durable-rule/checker/project_log/project_vision edits (packet is workspace-local; project_log row +
  vision update still SURFACE to Andrew).

## Status
Phase 0 in progress: workspace + governance + toolkit copied byte-identical (SHA manifest) + data wired + Test06
extracted. NEXT: modal data layer + band-limited caches → QOI/scorer → validity probe. NO durable-rule/checker/
project_log/project_vision edits.
