# Decisions log — Card G (multi-reference amplitude / participation÷damping confound)

**One-line state:** COMPLETE. check.py OVERALL GREEN (18/0/0). HEADLINE = scoped HONEST NEGATIVE: multi-reference
does NOT raise held-out per-channel amplitude skill above 0 (best −0.11); frequency +0.93 preserved; oracle +0.58
proves the limit is the held-out SENSOR's own shape (verdict iii, earned) + impact-hammer data-quality ceiling
(verdict ii). SURFACE-to-Andrew items pending (project_log row; checker amplitude-tier philosophy; "replace FEM" — none
self-applied). Lead-as-runner, FULL COMPUTE AUTONOMY used end-to-end (no compute checkpoint), non-compute guardrails kept.

## Re-grounding (goal / last decision / next action / open ambiguities)
- GOAL: credible BEFORE(+X single-ref)/AFTER(multi-ref +Z/+Y/900z) test — does multi-reference hammer data raise the
  ShockSat L5 twin's held-out per-channel AMPLITUDE skill vs climatology above the Card F ≈ −1.0 (ideally >0) while
  preserving the +0.93 frequency skill — gated by coherence (data quality), the NUTS convergence gate, and the
  identifiability gate. A rigorous scoped HONEST NEGATIVE is an equally valid win.
- LAST DECISION: Andrew dispatched Card G with FULL COMPUTE AUTONOMY (run Part A → coherence → Part B multi-ref NUTS MC
  end-to-end, detached/resumable/overnight, NO human compute checkpoint). Non-compute guardrails kept (surface only).
- NEXT ACTION: Part A reproduction driver (detached NUTS), then build multi-ref FRF caches + coherence diagnostic.
- OPEN AMBIGUITIES: (1) Test03 is a MODAL hammer (different tip/force spectrum) → handle via per-test gain / analyse
  separately + label on every Test03 conclusion. (2) node-900 drive coords for Test10 (read from FEM/TestLog).
  (3) verify Recorder116 is the force channel for Test08/03/10 (verify from each .mat, not assume).

## D0 — inherited constraints (carried from AGENTS.md + Card A/D/E/F, NOT re-litigated)
- Plain standalone 9-group ShockSat ONLY (no coupled tray). Reduced 74-DOF modal forward K(θ)=A_fix+Σ θ_g A_g.
- COPY-never-edit the Card F `code/` + `data/`. New processing on NEW scripts only (multiref_*.py). check.py + the
  inherited reuse set are SHA-locked; editing inherited code = RED integrity.
- θ is calibrated from MEASURED modal FREQUENCIES only (Kiran Eq 25 eigenvalue likelihood, NUTS). Amplitude is a
  forward prediction from FEM (or .ash-inferred) mode shapes φ + ONE training-only global broadband units-gain c.
- UNITS-GAIN PROTOCOL (Card A `units_gain_forensics.md`): score under ONE fixed/broadband gain per method, fit once on
  the OBSERVED channels (quality-weighted median of log|H_meas|−log|H_fem|), NEVER a per-held-out / per-draw / peak-tuned
  gain (that was the fragile Beck>L5 artifact). All methods under-predict held-out peaks ~1.8–2.6× = FEM amp model-form
  ceiling. Keep this caveat on every amplitude number.
- Convergence gate (NUTS/HMC default): all-variable max R̂≤1.05, min ESS≥200, div-frac<2%, ≥4 chains; else YELLOW
  not-yet-converged (never "NUTS active" just because a sampler ran). Escalate to TMCMC if multimodal.
- Re-pairing-robust mode metrics (tracked continuation / cross-orthogonality), NEVER greedy best-MAC (Card D D12).
- Three-tier every conclusion; a result is only as strong as the held-out score supports. "model-form limit" ≠
  "this parameterization/observable is exhausted" — distinguish, and only claim model-form/QOI-intrinsic if the
  confound is PROVABLY broken yet amplitude stays ≤0.

## D1 — the confound + the multi-reference mechanism (the scientific basis, verified from files)
- Resonant peak: |H_peak(s,k,d)| ∝ φ_{s,k}·φ_{d,k}/ζ_k (sensor participation × drive participation ÷ modal damping).
  At a SINGLE drive d, φ_{d,k} is one fixed number → wrong amplitude is explained equally by wrong φ_{s,k} or wrong ζ_k
  (confounded); a channel-common units-gain absorbs any common scale. Card A: damping is per-mode/channel-common ⇒
  degenerate with the gain ⇒ fixing ζ small didn't help.
- Multi-reference break: with ≥2 drives, |H_{s,k}(d1)|/|H_{s,k}(d2)| = φ_{d1,k}/φ_{d2,k} — independent of sensor s and
  of ζ_k → over-determines ζ_k (reference-invariant) and separates it from participation. THIS card supplies the raw
  multi-drive data the prior runs lacked.
- HONEST PRE-TEST CAVEAT (from Card F D16): the held-out SENSOR's own φ_{s,k} is sensor-specific and only FEM/.ash-known;
  multi-ref drive data cannot directly fix a HELD-OUT sensor's participation. If the dominant held-out error is φ_{s,k}
  (Card F shape-pattern corr ~0.15), the held-out amplitude can stay ≤0 EVEN with the confound broken → that would be
  the EARNED, stronger version of the Card F finding (model-form/QOI-intrinsic, not data). Must be RUN, not argued.

## D2 — checker finalized pre-trial (legitimate, logged)
- check.py created → first run created `.check_lock.sha256`. Found a stale entry (`shapefield_lever.py` does not exist
  in Card F; the Beck headline is the 3-seed mean of `modal_beck_ash.py`, aggregated by `fig_shapefield_lever.py` into
  `shapefield_lever.json`). Corrected INHERITED to the true reuse set, deleted the lock, re-ran → clean baseline RED,
  integrity GREEN. This was BEFORE any result existed (zero out/*.json from this study) → pre-trial hardening, not a
  mid-trial checker edit. From here check.py is LOCKED for the trial.

## D3 — data on disk (verified, not assumed)
- Disk: ~15 GB free (the card said 3.9; verified df). Still apply disk hygiene: band-limited caches, delete raw+zips.
- Test07 (+X impact, 990x): hit-001 .mat extracted (256 MB) + +X FRF cache symlinked (Card A, 252 MB, full-res).
- Test08 (+Z impact, 990z): 5 hits extracted (002/004/005/006/007), 256 MB each, force=Rec116 lb (memory 22b).
- Test10 (900z impact, node 900): zip at repo root (772 MB) — extract 2–3 hits, cache, delete.
- Test03 (+Y MODAL hammer, 990y): zip at repo root (676 MB) — MODAL-hammer caveat; extract 2–3 hits, cache, delete.
- Multi-hit coherence is now COMPUTABLE for +Z/+Y/900z (≥4 hits each) — a PROPER multi-average coherence, unlike +X
  where Card A had only hit-001 and used a single-hit quality-weight surrogate (~0.07).

## Decisions appended below as the run proceeds (newest at bottom)

## D4 — Part A REPRODUCES Card F EXACTLY (integrity GREEN); coherence DATA-QUALITY split by INSTRUMENT
- Part A (`out/partA_summary.json`): freq CRPS-skill 0.9307 = Card F 0.9307 (and 2.10%→1.07%); non-hard amplitude
  per-seed [−0.76, −0.84, −1.40] mean −0.9998 ≈ Card F −1.0; Beck FEM −0.680 → INF −0.252 ≈ −0.68 → −0.25 (3 seeds
  all converged). NUTS is deterministic here → byte-faithful reproduction. INTEGRITY/REPRO ANCHOR = GREEN.
- Coherence diagnostic (`out/coherence_by_reference.json`, fair comparison at n=4 hits, uncorrelated floor 0.25):
  AT THE MODAL RESONANCES (where the amplitude QOI lives), median coherence = +Z(impact) 0.28 ≈ floor, 900z(impact)
  0.39, +Y(MODAL) 0.92; drive-point = +Z 0.23 / 900z 0.30 / +Y 0.96. ⇒ the IMPACT-hammer references are near the
  NOISE FLOOR at most resonances (only the top ~10% of modes, p90 0.75, carry signal); the MODAL hammer (+Y/Test03)
  is strongly coherent. The documented +X "~0.07" is a BROADBAND 100-10 kHz Welch number (no hammer energy up there);
  the in-band at-resonance picture is the relevant one and it confirms the impact data is weak.
- CONSEQUENCE for the verdict: the impact-hammer MULTI-REFERENCE set (+X/+Z/900z) is largely incoherent at resonances
  → the confound-break mechanism will be NOISE-LIMITED for the impact set (leans verdict ii, data-quality ceiling).
  The ONE clean amplitude reference is a MODAL hammer (+Y), which (a) is a single reference and (b) carries the
  different-instrument gain caveat — so it is not a clean impact multi-reference SET. CANDIDATE ALT CAUSE to flag,
  not yet ruled out: impact hits may ROVE across the source face (Test07's 4 hits roved (9,8,1)/(9,8.5,0.5)/
  (9,8.5,0.25)/(9,8,0)); roving across hits would also lower multi-hit coherence. Either cause (poor SNR or roving)
  ⇒ the impact multi-hit data is not clean enough to cleanly break the confound. MUST still RUN the mechanism +
  held-out test to confirm (not argue from coherence alone). NEXT: drive-shape-ratio mechanism (use the clean +Y
  where possible; report impact pairs with the noise caveat) → FIM identifiability → held-out amplitude before/after.

## D5 — FINAL RESULTS (all converged; check.py GREEN 18/0/0)
- Mechanism (`drive_shape_ratio.json`): cross-reference peak ratio does NOT cleanly recover the FEM drive ratio
  (best corr 0.32 +Z/900z, median 0.06; large sensor-spread 0.34–0.95) → confound NOT cleanly broken from this data.
- Identifiability (`multiref_identifiability.json`): multi-ref excites 17→23 modes (coverage up) but θ directions
  above the σ_w≈6.9% floor stay 3 (all-modes 4) = stiffness FLOOR-limited; amplitude confound 1 combo/mode → 3
  separable drive-RATIOS (+1 gauge) = broken on the DRIVE side only.
- HEADLINE (`multiref_value.json`, 3 splits, R̂ 1.001–1.003 / ESS≥1414 / 0 div): BEFORE +X FEM −1.00 (N200000) /
  −1.69 (sameN control) → AFTER +X measured residue −0.11; by drive +Z −0.40 / +Y −0.46 / 900z −0.09 (none beat +X);
  shape-ORACLE (held-out sensor shape known) +0.58. Frequency +0.931 preserved (reference-invariant).
- VERDICT = combined (iii)+(ii): measuring the drive residue lifts −1.7→−0.1 but cannot cross 0 because the held-out
  SENSOR's own φ_s is FEM-only (oracle +0.58 proves the QOI is predictable IF the sensor shape were known) — the
  earned, stronger Card F finding; plus the extra IMPACT references are near the noise floor (coherence ~0.28–0.39 at
  resonances vs modal 0.92), so they don't even help the drive side. Multi-reference is the WRONG axis of information
  for held-out per-channel amplitude; the lever is sensor-shape coverage / refined mesh / cleaner excitation.
- Deliverables: check.py GREEN (18/0/0); packet.md; 4 figs tufte+image-QA pass; runtime.json (active 516 s);
  run_all.sh; raw .mat + zips deleted (footprint 2.8 MB caches). Packet scientific tier = YELLOW (documented negative).
- D2-note honored: check.py SHA-locked, NOT edited after results. SURFACED (not self-applied): project_log row;
  whether amplitude gate should be YELLOW-on-no-skill (Card F precedent) vs my GREEN-on-convergence; no "replace FEM".

## D6 — Andrew follow-up (2026-06-23): split count + evolving-posterior GIF
- SPLITS: amplitude headline = 3 train/test splits (seeds 0–2), leave-40%-out over 77 DR≥30 channels = 46 obs / 31
  held-out per split; SAME 3 splits for Part A (FEM/Beck) and Part B (multi-ref ×4 drives) → before/after identical.
  Frequency = 1 split over 27 matched modes (16 obs / 11 held-out). 3 is Card-F-matched/modest; ~25-split MC offered.
- GIF (`figures/evolving_posterior_frf.gif` + `_final.png`, `out/evolving_gif_meta.json`): sequential Bayesian
  updating (frames = +more observed modes) for held-out channel 108; measured + nominal FEM + posterior 95% band;
  title = peak CRPS-skill / coverage / R̂; legend = band-GRMS. HONEST: channel 108 is a SELECTED well-covered example
  (skill +0.71, cov 0.97) = one of the BETTER cases; population-mean amp skill is −1.0 (labeled on the figure +
  packet §7). Not gated by the SHA-locked check.py (added post-lock); referenced in packet §7. NUTS per frame
  converged (R̂≤1.006).

## D7 — Andrew steer (2026-06-23): DROP leave-one-MODE-out (unrealistic for aerospace) — AWAITING GO-AHEAD on reframe
- DIRECTIVE: "lets not do mode leave out, its unrealistic for a traditional aerospace workflow." Correct: a GVT/FEM-
  correlation workflow uses ALL measured modes to correlate+update (freq err + MAC); you never hide a measured natural
  frequency. Leave-one-mode-out is a stats CV, not an engineering validation; reporting +0.93 off it overstates value.
- REALISTIC SUBSTITUTE: (a) frequency = standard correlation on ALL modes (no holdout) — as-received vs calibrated
  |freq err|: median 1.84%→1.48%, mean 2.57%→1.95%, max 11.99%→6.57%, 78%→78% within 3% (NUTS all-modes, R̂1.001).
  ⇒ as-received FEM already well-correlated; updating is MODEST, mainly fixes worst modes. (b) predictive trust =
  leave-a-SENSOR-out (predict untested LOCATION) — which our AMPLITUDE split ALREADY is (−1.0, the realistic held-out).
- IMPACT: the multi-reference AMPLITUDE headline (−1.0→−0.11, oracle +0.58) is UNCHANGED (already leave-sensor-out).
  ONLY the FREQUENCY framing changes: drop the +0.93 mode-CV headline; report the all-modes correlation above; keep
  leave-sensor-out as THE realistic held-out trust test. Story gets cleaner+more decision-relevant: twin correlates
  fine on freqs (modestly improved) but its untested-LOCATION response (amplitude) value is negative; multi-ref no fix.
- NOT YET APPLIED (awaiting Andrew go-ahead, since this reframes a completed packet headline + a validation standard):
  (1) rewrite Card G packet frequency framing + GIF caption; (2) SHA-locked check.py partB.frequency scores the
  (now-deprecated) mode-CV metric — will NOT edit the locked checker, will note deprecation + realistic numbers
  alongside; (3) CROSS-CARD: Card A/F + project validation philosophy use the same mode-CV — SURFACE to Andrew whether
  to flag/revisit (durable, NOT self-applied). Scope question for Andrew: Card G only, or flag the whole ShockSat thread?

## D8 — Andrew follow-up (2026-06-23): GIF should fold in DATASETS (Test3/8/10), not modes
- Built `code/fig_evolving_gif_datasets.py` → `figures/evolving_posterior_frf_datasets.gif`: posterior FRF of HELD-OUT
  sensor 108 as roving-hammer datasets fold into the calibration (prior→+X→+X+Z→+X+Z+Y→+X+Z+Y+900z). Each dataset ADDS
  the modes it excites (FEM φ_d≥10%); SENSOR held out (realistic). Converged R̂1.002. FINDING: modes 0→16(+X)→20(+Z),
  then +Y and 900z add 0 NEW excited modes (their excited modes already covered) → held-out skill FLAT 0.78→0.77→0.77,
  coverage ~0.92→0.96 flat ⇒ multi-reference frequency coverage SATURATES after +X+Z; held-out amplitude unchanged
  (consistent with the −1.0/−0.11 headline). Honest caveat on figure: ch108 selected well-covered (pop-mean −1.0).
  First (mode-accumulation) GIF `evolving_posterior_frf.gif` kept as secondary. packet §7 updated to feature datasets GIF.
- NOTE: these GIFs are post-lock figures (not gated by SHA-locked check.py); referenced in packet §7.
- STILL PENDING from D7 (awaiting Andrew): go-ahead to reframe the FREQUENCY claim (drop mode-CV +0.93 → all-modes
  correlation 1.84→1.48%) + scope (Card G only vs flag Card A/F). Not self-applied.
