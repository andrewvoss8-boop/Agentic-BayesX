# decisions_log.md — Validate the orthogonal-Schneider StatFEM twin on the REAL ShockSat (Card A)

Runner: Claude Code (lead-as-runner, Card A). Human: Andrew Voss. Advisor objective: Ilias Bilionis.
Workspace: `artifacts/reports/statfem_real_validation_20260617/`.

## ONE-LINE STATE (compaction-safe; update before risky steps)
- **goal:** validate the orthogonal-Schneider StatFEM digital twin on the REAL ShockSat (our 9-group FEM +
  measured impact-hammer / modal data) — does it predict held-out-sensor QOIs with uncertainty that is
  calibrated AND sharp under genuine FEM-vs-real model-form error, and where does it break? Either verdict
  is the science.
- **last decision:** D12 BUILT + RUN (next-action #1 DONE). `code/heldout_qoi.py` → `out/heldout_qoi_L5.json`
  (`phase2_heldout_sensor_qoi_summary.md`). Calibration CONVERGED (R̂ 1.0015, ESS 1800, 0 div). RESULT:
  frequency-calibrated twin + marginal QOI-discrepancy = CALIBRATED held-out-sensor QOI (cover 0.91, z_std≈1,
  all proper scores improve) but WIDE (×50, 34 dB); θ-only is overconfident (cover 0.12–0.16, z_std 11–14) =
  the honest gap (freq calibration ≠ magnitude calibration). Matches Schneider Fig 6 (amplitude/damping floor).
- **next action:** STUDY COMPLETE on the checker side. **`checker_report.json`: OVERALL YELLOW, green=12 yellow=1
  red=0** (the 1 yellow = whole-FRF arm cells labeled not-yet-converged — honest, never called converged). DONE:
  A (δ*=1%), B (negative), arms keystone (Q-A/Q-B), MC (25 splits, L5 100% conv, cover 0.88), scoring, paramcount
  (winner fim_downselect: all9 logZ −2697/R̂9.2 vs ident4 −2718/R̂2.6 — raw evidence mildly favors 9 but FIM+
  conditioning pick 4), wideband_demo, 8 figures + QA pass, runtime.json, run_all.sh, packet.md (3-audience).
  REMAINING (optional): editable .pptx (python-pptx, now non-RED so allowed). **SURFACE to lead (NOT self-applied):**
  docs/report/project_log.md row + notes/* updates with status copied from checker = OVERALL YELLOW.
- **CARD C Phase 1 IN FLIGHT (D23):** harden Beck-on-`.ash` onto L5's footing. `code/modal_beck_full.py` +
  `code/mc_beck_full.py` built + smoke-validated; full 25-split × {12,20}-mode MC launched DETACHED (PID 19609,
  `logs/mc_beck_full.log`) → `out/mc_beck_full_summary.json`. NEW vs D22: (peak |H| AND band-GRMS), measured
  per-mode `.ash` damping (ζ_eff=ζ_ash+ζ_w), and a FAIRNESS FIX. NEXT: read summary → mechanism attribution
  (shape-field vs damping vs modes) → figure (Phase 1d) → report 1-screen + SURFACE the fairness/labeling fixes.

## D28 — L5 mode-matching refinement (MAC) + sensitivity to # modes / matching (Andrew 2026-06-19: "refine matching, let MAC inform it; sensitivity to how many modes + how matched")
`code/l5_matching_sensitivity.py` → `out/l5_matching_sensitivity_summary.json`; `code/fig_l5_matching.py` →
`figures/fig_l5_matching.png`. Added a MAC-informed matcher (ODS = complex H across observed channels at each
consensus peak → highest-MAC FEM mode within ±15%). 12 configs × 10 splits, apples-to-apples peak gain.
- **L5 is largely INSENSITIVE to matching & mode count:** peak IS 1068–1284 (full spread ~20%), coverage steady
  ~0.92–0.94 everywhere.
- **MAC barely informs the MATCH:** single-impact ODS-MAC is only 0.10–0.25 (noisy shapes, confirms D20). MAC's
  small value is in SELECTING a clean mode subset, not in pairing: MAC-rank keep-6 (1068) beats freq-support keep-6
  (1129) by ~5%, and beats the deployed `orig` (26 modes, 1108) by ~4%.
- **Fewer, cleaner modes ≥ all modes:** MAC keep-6/8/20 (1068–1100) all beat keep-all-36 (1166); the permissive
  freq-12%-all (1256) and tight freq-5% (1284) are worst. θ is over-determined — ~6 modes pin the 4–9 identifiable
  stiffness params; dumping in loosely-matched modes slightly hurts. Best recipe = MAC-rank, keep ~6–8 clean modes.
- **VERDICT:** refined matching cannot meaningfully sharpen L5 — the ~34 dB amplitude width is FEM model-form error
  (peaks/shapes), NOT a matching artifact. Reinforces §7.1. check.py untouched.

## D27 — UNITS-GAIN forensics + "no free knob" fixed-gain comparison (Andrew 2026-06-19: "can't we infer the gain from unit conversions / sensor info?")
**Deepens D26; verdict-relevant.** `units_gain_forensics.md`, `code/frf_fixed_gain.py` → `out/frf_fixed_gain_summary.json`.
- **Units ARE already handled (verified from the FEM deck):** consistent English units — `MAT1` densities 2.59e-4/
  7.77e-4 lbf·s²/in⁴ (slinch/in³ Al/steel), NO `WTMASS`; code divides by g=386.0886 → g/lbf; measured H1 is g/lbf.
- **Residual offset is NOT a derivable units constant:** ×496 broadband but ×789 at peaks, ×2.4 channel scatter;
  `V_keep` column norms 219–1490 (not mass-normalized). ×496 = inherited-basis normalization (fixed but provenance-
  dependent, NOT from sensor calibration); ×1.6 peak-vs-broadband + ×2.4 scatter = genuine MODEL-FORM error. So the
  gain can't be pinned from units/sensor info; the whole-vs-peak ambiguity is a SYMPTOM of model-form error.
- **"No free knob" comparison (fix ONE broadband units gain per method, calibrated once, no per-target/split/draw
  fitting; bias NOT re-centered), 25-split medians:** L5 peak IS 1668 (bias ×1.83 low) / FEM 2031 (×2.07) / Beck 2496
  (×2.63). **Beck peak IS < L5 in 0/25.** ALL methods under-predict held-out peaks ~1.8–2.6× = the FEM amplitude
  model-form error made VISIBLE (a fitted gain was hiding it).
- **Complete gain picture (peak IS, 25-split median):** fixed-units gain → L5 1668 < Beck 2496 (0/25); whole-FRF gain
  → L5 1992 < Beck 3641 (0/25); peak gain → Beck 790 < L5 1146 (25/25). **Beck beats L5 ONLY under a per-split
  peak-tuned gain.** Under any non-peak-tuned gain, L5 ≥ Beck.
- **CORRECTED VERDICT (further tempered from D26):** Beck's shape-field advantage over L5 is **fragile to the gain
  protocol** — not a robust win; the shape-field MECHANISM (inferred>FEM shapes within Beck) still holds. The real
  amplitude lever = FEM fidelity (Card D), not the likelihood/gain. SURFACE to lead/human + packet. check.py untouched.

## D26 — APPLES-TO-APPLES FRF comparison exposes a GAIN-PROTOCOL artifact in the Phase-1 headline (Andrew 2026-06-19: "apples-to-apples FRF Beck vs best previous, same original scoring protocol, full MC")
**VERDICT-RELEVANT HONESTY CORRECTION — surfaced, must reach the packet.** Built `code/frf_compare.py` (full-FRF
predictive bands for L5 / FEM-nominal / Beck; SAME splits, observed-only σ; scored with the ORIGINAL score.py
protocol: score_qoi peak+band as in heldout_qoi/mc_heldout + whole-FRF frf_score). Running full 25-split MC
detached (PID 22608, `logs/frf_compare.log`) → `out/frf_compare_summary.json`. KEY (1-split smoke, to be confirmed
on the full gate — cheap probes can mislead):
- The Phase-1/D22 claim "Beck ~2× sharper than L5 (773 vs 1661)" compared **Beck with a PEAK gain** against **L5 with
  a WHOLE-FRF gain** — DIFFERENT nuisance-gain protocols, NOT apples-to-apples. The global units-gain is a processing
  choice; the comparison must hold it fixed across methods.
- **CONFIRMED on the full 25-split MC** (`out/frf_compare_summary.json`; all converge): the smoke "tied" reading was a
  cheap-probe artifact (warmup 300×2) — the full warmup gives a CLEAR, robust result:
  - **whole-FRF gain (original L5 protocol):** L5 peak IS 1992 / band 5492 / wholeFRF 8.69; Beck 3641 / 9871 / 9.19.
    **Beck sharper than L5 in 0/25 (peak), 0/25 (band)** — L5 BETTER (Beck's 12-mode FRF over-leveled; cov 0.77).
  - **peak gain (matched, QOI-appropriate):** L5 peak IS 1146 / band 3015; Beck **790 / 2148** (cov 0.97 vs 0.90).
    **Beck sharper than L5 in 25/25 (peak), 23/25 (band)** = ~1.45×/1.40× — REAL, ROBUST, but ~30–45%, NOT 2×.
  - **whole-FRF score (off-resonance):** L5 BETTER under both gains (Beck sharper 1/25 peak-gain, 9/25 whole-FRF-gain)
    — Beck is a PEAK/QOI predictor (12 modes), not a whole-FRF predictor.
- **CORRECTED VERDICT (replaces the Phase-1 "2.1×"):** under apples-to-apples gain, Beck is calibrated (cov 0.97) AND
  ~1.4× sharper than L5 on peak |H| + band-GRMS (25/25, 23/25 splits) — the shape-field win condition is MET, at ~1.4×
  not 2×; L5 better on whole-FRF. The Phase-1 2× was inflated by the gain mismatch (L5's whole-FRF gain under-levels
  its own peaks ~×1.4, the D12 "+0.72 log" effect). The shape-field MECHANISM (inferred>FEM shapes within Beck, 773 vs
  1252, both peak-gained) is UNAFFECTED. Full writeup `apples_to_apples_frf_summary.md`.
- DONE: corrected `phase1_cardC_hardened_beck_summary.md`, the deck (slide 4 + scorecard P1 5★→4★ + new apples slide
  + fig_frf_compare). SURFACED to lead/human as verdict-moving. check.py untouched.

## D25 — Card C STORY DECK with graphs + GIFs + star ratings (Andrew 2026-06-19: "ppt summary with graphs and gifs; 5★..1★ per element")
- `code/cardC_story.py` (tufte skill applied, lint advisory-only) → 6 static story figures (`figures/fig_cardC_
  {mechanism,phase2_kriging,phase3_tau,phase4_phase,phase5_cross,scorecard}.png`) + 2 ANIMATED GIFs
  (`figures/gif_heldout_sweep.gif` = 16 held-out channels, inferred band tracks measured; `figures/gif_tau_band.gif`
  = band widens as modes dropped). All numbers read from out/*.json (traceable; no fabrication). Image-spot-checked
  legible; baselines zeroed; dual-axis removed (single-axis τ plot).
- `code/make_pptx_cardC.py` (base python3 = has python-pptx 1.0.2) → `slides/cardC_hardened_twin_story.pptx`
  (12 slides, 9 pictures incl. both .gif embedded as real media → play in slideshow). Per-phase STAR RATING
  (evidence-tied): P1 ★★★★★ (calibrated + ~2× sharper, 25/25, named mechanism); P3 ★★★★ + P5 ★★★★ (clean decisive
  converged answers); P2 ★★★ + P4 ★★★ (informative results with real caveats); P6 ★ (BLOCKED on Card D, not a
  quality failure — labeled). Honest ratings, not inflated; verdict unchanged.
- check.py UNTOUCHED; checker artifacts unchanged (still OVERALL YELLOW). Deck is a presentation artifact (gated
  non-RED). SURFACE unchanged: project_log/notes/runtime + the D23 fairness/labeling findings remain for lead.

## D24 — Card C Phases 2–6 COMPLETE (kriging, τ sweep, phase L4, cross-dataset; Phase 6 blocked)
All study artifacts; check.py UNTOUCHED; checker still YELLOW (no regression). Summary: `phase2to6_cardC_summary.md`.
- **Phase 1 DONE (D23):** hardened Beck shape-field twin = headline. Held-out peak IS 773 vs L5 1661 (~2.1× sharper),
  band IS 2079 vs 4236 (~2.0×), calibrated cov 0.97, 25/25 splits; mechanism = SHAPE FIELD (measured damping 0/25).
  Figure `fig_cardC_heldout_frf.png` (tufte-lint clean, image-QA OK). Fairness fix (observed-only σ) + split-
  independent-calibration labeling applied. (`modal_beck_full.py`, `mc_beck_full.py`, `fig_cardC_heldout_frf.py`.)
- **Phase 2 — spatial kriging (`beck_kriging.py` → `mc_beck_kriging_summary.json`):** the freq×space GP-conditional
  transfer SHARPENS ~2× vs the per-frequency MARGINAL (peak IS 6568→3468 len_z12 / 3183 len_z60, kriged sharper
  25/25) — the Schneider mechanism works spatially — BUT costs calibration (cov 1.00→0.81–0.84, z-std 0.08→1.4–1.6)
  AND neither per-freq transfer beats the Phase-1 QOI-LEVEL σ (773), because σ_d≈2.0 is inflated by peak-misalignment
  spikes (D7). VERDICT: apply discrepancy at the QOI level; kriging is a real but secondary win over a per-freq marginal.
- **Phase 3 — τ sweep (`tau_sweep.py` → `tau_sweep_summary.json`):** held-out proper score MAXIMIZED by the FULL
  matched-mode set (peak IS full20 797 / mac≥0.5 809 / mac≥0.7 842 / top6 1021); over-restricting to the 6 highest-MAC
  modes WORSENS sharpness; coverage ≈0.97 at every τ. Pre-test answer: keep the full MAC-matched set, don't over-cut.
- **Phase 4 — complex/phase L4 (`phase_likelihood.py` → `phase_likelihood.json`):** single-hit phase circular variance
  at modes = 0.85 (≈incoherent); complex θ-slice NOT sharper than magnitude (rel-contrast 0.00 vs 0.01). VERDICT:
  phase adds nothing over magnitude; magnitude/modal retained. (Documented negative, honors the card's single-hit caveat.)
- **Phase 5 — cross-dataset (`cross_dataset.py` → `cross_dataset_summary.json`):** `.ash` survey is a VALID independent
  calibration source — `.ash` freq-only θ converges (R̂ 1.002) and predicts the impact held-out FRF ≈ as well as L5
  (peak IS 1502 vs 1661) — but stiffness-θ from ANY modal source barely moves amplitude (all ≈1500–1660 ≈ nominal 1509);
  only the inferred shape FIELD sharpens (beck_infer 858). Corroborates the shape-field-is-the-lever thesis cross-dataset.
- **Phase 6 — BLOCKED (`phase6_revalidate.py` → `phase6_status.json`):** Card D (`shocksat_fem_remesh_20260618`) has
  only delivered `region_diagnosis.json`; no refined reduced FEM yet. Re-validation harness ready; no numbers fabricated.
- **SURFACE to lead (unchanged + extended):** the D23 fairness/labeling findings; plus the Phase-2 nuance (QOI-level
  beats per-freq kriging) and Phase-5 cross-dataset consistency are packet/project_log-relevant; NOT self-applied to
  docs/report/project_log.md, notes/*, or runtime.json. No durable-rule/checker/sampler-standard changes made.

## D23 — Card C Phase 1: harden Beck-on-.ash (full QOI + measured damping + fairness fix)
New runner session (Card C), re-grounded from AGENTS.md + decisions_log D0–D22 + packet + notes/memory.
- **Built `code/modal_beck_full.py` (extends, does not edit, `modal_beck_ash.py`) + `code/mc_beck_full.py`.** Scores
  the Beck mode-shape-field twin on L5's full QOI footing: held-out peak accelerance |H| AND band-GRMS [g/lbf],
  proper scores (interval/CRPS/logpd), across ≥25 channel splits, with a 2×2 mechanism contrast per split:
  {FEM, INFERRED shapes} × {const ζ=0.01, measured per-mode ζ} → attributes any sharpening to SHAPE-FIELD vs
  DAMPING vs MODE-COUNT. Measured damping folds in `.ash measured_modes.npz['damp']` (% critical, previously
  UNUSED): ζ_eff,r = ζ_ash,r + ζ_w(f_r) (window damping, `realfrf.measured_zeta_w`).
- **TWO HONESTY FINDINGS about the D22 validated headline (SURFACE to lead — may affect the verdict framing):**
  1. **Fairness fix (the bigger one).** The D22 `mc_beck.py` estimated its QOI-discrepancy band width σ from the
     HELD-OUT truth (`peak_tru_ho`) — a leak letting Beck peek at held-out scatter to size its band — whereas L5
     (`heldout_qoi.qoi_disc`) estimates σ on OBSERVED channels only. So the D22 "Beck sharper than L5 (1366→773)"
     was NOT apples-to-apples. `modal_beck_full.py` estimates σ on OBSERVED channels only (matching L5). Smoke
     shows the fair σ is a bit larger (peak σ ~0.97–1.16 vs the leaky ~0.85) → bands slightly wider but the
     INFER-vs-FEM sharpening direction PERSISTS in smoke (2/2 splits). The full MC will quantify the honest margin.
  2. **Calibration is split-INDEPENDENT.** Beck's NUTS posterior over (θ, φ) uses ONLY the global `.ash` modal
     survey + a fixed PRNGKey — it does not depend on the impact-FRF channel split (this is why every D22 split
     reported the identical R̂ 1.002622952678684). So the "25-split MC, converged 100%" is ONE global calibration
     reused; the MC varies only the held-out channel set + per-config gain. Legitimate held-out-channel
     generalization test, but must be LABELED precisely (not "25 independent recalibrations"). `modal_beck_full`
     calibrates once per n_modes (cached `out/beck_calib_nm{N}.npz`) and labels this in the output.
- check.py UNTOUCHED (immutable). New artifacts validated by internal consistency + the existing checker still
  green/yellow; a separate validation note will accompany them. Study artifacts (no §14 stop) EXCEPT the two
  findings above, which I am surfacing because they touch the headline "Beck sharpens" claim.

### D14 SCORING + FIGURES DONE; D15 A/B SMOKE-VALIDATED + RUNNING
- **scores_summary.json (1 split, n=1500×4):** M0 cover 0.00 IS 5.8e3 (overconfident); M1 σ_w 1.6 cover 1.0 IS 5.4e3;
  M2 σ_w 15.8 R̂ 6.4 IS 4.5e17; M3 σ_w 15.1 R̂ 26 IS 4.0e17 (both "cover" 1.0 but USELESS); L5 ref cover 0.91 IS 1.4e3.
  PUNCHLINE: coverage alone is fooled; only L5 is calibrated AND usable (fig_method_comparison).
- **A smoke (δ=0 vs 20%, n=300×2) VALIDATES the experiment:** δ=0 CONVERGED R̂ 1.001 σ_w 0.03 (reproduces synthetic-
  study convergence — truth=model) ; δ=20% R̂ 1.95 σ_w 4.4 (breaks). Full sweep {0,1,2,5,10,20}% n=2000×4 running.
- **B smoke (warmup 200×2, non-converged R̂ 31) early signal:** σ_a≈3.2 (amplitude log-error ×25), per-mode η barely
  moves from nominal → the modal AMPLITUDE residual is dominated by FEM MODE-SHAPE error, not damping. Full run
  (1000×4) running to confirm. If B doesn't converge / doesn't sharpen, that is itself the finding (mode-shape
  model-form error limits amplitude prediction; eigVECTORS harder than eigVALUES).

### D15 A + B — VERIFIED RESULTS (both DONE)
- **A `out/fem_error_sweep.json` (n=2000×4, synthetic, full sweep):** δ=0% R̂1.000 σ_w0.03 ✅ (control reproduces
  synthetic convergence); δ=1% R̂1.000 σ_w0.44 ✅; δ=2% R̂1.057 σ_w3.76 ❌; δ=5% R̂2.04 ❌; δ=10% R̂4.31 ❌; δ=20%
  R̂1.14 σ_w4.39 ❌. **CONVERGENCE BOUNDARY δ\* = 1%** (boundary 1–2%). σ_w jumps 0.44→3.76 across it. PRE-TEST
  DESIGN NUMBER: the whole-FRF magnitude likelihood is usable only if the FEM aligns peaks within ~1% (~0.5–2.6 Hz
  in 45–260 Hz). Real ShockSat misalignment ≫1% → explains the real-data negative (R̂ 104–129) as FEM coarseness,
  NOT method failure; synthetic study converged because δ=0. Clean, decisive.
- **B `out/modal_amp_feature.json` (NUTS 1000×4): HONEST NEGATIVE.** R̂ 55.8, ESS 2, **174 divergences** — does NOT
  converge; σ_a 3.17 (amplitude log-error ×24); per-mode η stuck near nominal (0.016–0.028); held-out PEAK cover
  0.34 / z-std 15.8 (NOT sharper than L5+marginal's 0.91). VERDICT: per-mode damping does NOT rescue the calibrated-
  but-wide bands — the amplitude residual is dominated by FEM MODE-SHAPE error (not damping), AND the eigenVECTOR-
  based amplitude likelihood is numerically pathological (174 div = eigvec-degeneracy gradient geometry), unlike L5's
  clean eigenVALUES. IMPROVEMENT LEVER for the amplitude gap = mesh/mode-shape refinement, NOT damping. Both A and B
  serve the Ilias "identify gap + suggest improvement" deliverable: A quantifies the gap; B rules out a tempting fix.

## D16 — MC + verdict synthesis (Andrew 2026-06-17: "keep going; is there no hope for real statFEM?")
- **VERDICT SYNTHESIS (for packet):** NOT hopeless. WHOLE-FRF MAGNITUDE = documented dead end on this coarse FEM
  (A: needs ≤~1% peak alignment; we have several %). MODAL-FEATURE (peak-freq) likelihood WORKS (L5 converged,
  held-out 6/6, held-out-sensor QOI calibrated 0.91 / z-std~1 — the only usable method). Ceiling on the working path
  = FEM MODE-SHAPE fidelity (B: damping doesn't sharpen) → calibrated-but-WIDE (×2.7) = FIT-FOR-PURPOSE for a
  conservative widen-when-wrong environment twin; sharp prediction needs a finer FEM.
- **MC (`code/mc_heldout.py`, RUNNING PID 64731 `logs/mc.log`):** ≥25 channel-split configs of the CONVERGED L5
  method → score DISTRIBUTIONS. Split axis ONLY (1 impact, 1 hit; labeled, D2). Whole-FRF arms omitted (non-converged
  + useless QOI; established at 1 split). → out/mc_summary.json (MC gate green). Smoke (2 splits) cov med 0.95.
- **Remaining:** fig_schematic (no compute), fig_heldout_frf (after MC), fig_mc_distributions (from mc_summary),
  figures/{image_legibility,text_overlap}_report.json, packet + pptx + runtime.json + run_all.sh.

## D17 — Comprehensive held-out report PDF (Andrew 2026-06-18: "why show worst case? show all; pdf with all held-out FRFs + improved FEM figs")
- Fair critique: the standalone fig_heldout_frf had picked the HIGHEST-DR held-out channel (101) = a near-worst
  mode-shape mismatch (FEM puts node 101's response at 225 Hz; real structure resonates ~60 Hz at |H| 444 → ~1000×
  gap = MODE-SHAPE participation error, NOT noise/units/frequency; quality wt 0.95-0.99 there = clean signal). Below
  45 Hz not plotted = analysis band 45-260 Hz by design (first mode ~54 Hz; poor single-hit low-freq SNR).
- FIXED standalone fig_heldout_frf → REPRESENTATIVE median-DR channel (95); caption sharpened to "mode-shape
  participation error" + points to the PDF.
- NEW `code/heldout_report.py` → **`out/heldout_report.pdf`** (5 pages): page 1 SETUP (param pooling 9 groups +
  strain energy, inferred element error θ per group with CIs — 4 identifiable tight / 5 at prior width, train/test
  split spatial scatter); pages 2-5 = EVERY one of the 32 held-out channels' FRF (measured |H1| vs twin band + the
  calibrated ±1.96σ_QOI amplitude envelope; peak COVERED/MISS per panel). **30/32 covered** (consistent w/ MC 0.88-
  0.91 → 101 was a tail case, not typical). PNG previews figures/report_setup.png + report_frf_page1.png. One split
  (seed 0), all channels — no cherry-picking. Checker still YELLOW (green=12/yellow=1/red=0). Study artifact, no surface.
- **UPGRADE (Andrew feedback):** (a) page 1 rebuilt per AGENTS §8 (Idea 3+1) using synthetic `group_geometry.npz`
  (read-only): STRUCTURE LOCATOR = real FEM nodes X-Z coloured by INFERRED error |θ_med−1| per group +
  observed(green)/held-out(blue-open)/drive(star) + "area=footprint NOT error" disclaimer, PAIRED with the
  non-spatial one-dot-per-group scatter (x=strain-energy %, y=inferred error %, size=error×participation) +
  inferred-θ CI bars. (b) Every FRF panel now carries its proper-score GRADE (PASS/MISS + interval score + CRPS).
  (c) "calibrated amplitude envelope" = predicted median × exp(±1.96·σ_QOI), σ_QOI≈0.98 (×2.7) = log-amplitude
  model-form scatter estimated on OBSERVED channels → the band that is actually calibrated (θ-only band is
  overconfident). 28/32 peak PASS (≈MC 0.88). Checker still YELLOW; image_qa ALL_OK.
- **BAND RELABEL/FIX (Andrew):** the two FRF bands are now ONE posterior predictive split + labeled "param
  uncertainty" (θ-posterior only) and "total uncertainty (with model-form error)" = param + a per-draw
  frequency-CORRELATED level offset δ~N(0,σ_QOI). SAME δ feeds the TOTAL band and the peak-QOI grade → band and
  PASS/MISS correspond exactly; total ⊃ param (nested). 30/32 PASS. PRIOR NOTE (real run): θ prior = Normal(0,0.25)
  on log θ = LogNormal centered at NOMINAL FEM (θ=1), INDEPENDENT across 9 groups, NO injected error/perturbation
  (no theta_truth on real data — unlike the synthetic 'combos' which injected known top+15%/bottom−10% etc.).
  Posterior moved only the 4 identifiable groups (cross_beam 0.83…); the other 5 stayed at prior width.

## D22 — Mode-shape likelihood test-drive COMPLETE + editable .pptx (Andrew 2026-06-18: "do both")
- **Test-drive verdict (the user's "test a few likelihoods"):**
  - L5 freq-only [baseline]: converges, calibrated, wide.
  - L6 freq+MAC (single-impact ODS): NULL — shape data unusable (MAC 0.04, dense-mode ODS).
  - L10 freq+MAC (`.ash` survey shapes, MAC-matched 0.70, `out/modal_ash_mac.json`): even with GOOD shapes + correct
    matching, MAC does NOT sharpen (IS 1719 vs freq-only 1667) AND freq+MAC does NOT converge → **θ cannot move the
    FEM mode shapes; shapes-in-the-likelihood is structurally incapable of sharpening held-out amplitude.**
  - **L8b Beck-mode-matching-FREE on `.ash` (`code/modal_beck_ash.py`, `out/modal_beck_ash.json`): THE LEVER THAT
    WORKS.** Infers the system mode-shape FIELD as free params (Rayleigh quotient ω²=φᵀKφ/φᵀφ + orthogonal-MAC at
    `.ash` DOFs → no eigvec in gradient). **CONVERGED R̂ 1.004, 0 div** (vs Sim-B 174 div), and reconstructing the
    held-out IMPACT-channel peak from the SAME 12 modes, the INFERRED shapes SHARPEN vs FEM shapes (IS 545 vs 671,
    cover 0.97, σ_QOI 0.86). Mechanism: correcting the shape FIELD transfers to held-out locations; constraining θ
    does not. Modest magnitude (~19% at fixed mode count) but the right mechanism + converges.
- **Editable deck:** `code/make_pptx.py` → `slides/statfem_real_validation.pptx` (14 slides, python-pptx, gated
  non-RED=YELLOW). Reads numbers from out/*.json + checker_report.json (traceable, auto-updates); embeds figures.
- **Packet:** verdict point 3 + assumptions ledger (Section 9, ~50 entries) updated; checker YELLOW (12/1/0).

- **L8b Beck-on-.ash MC (25 splits, `out/mc_beck_summary.json`): SHARPENS in 25/25 splits, converged 100%.** Held-out peak interval median FEM 1366->INFERRED 773 (ratio 0.63=~37% sharper), inferred coverage 0.97. ROBUST positive: inferring the mode-shape FIELD beats the FEM shapes at EVERY split. Beck/Au/Vanik 2001 CACIE 16:1-11.

## D21 — INSTRUMENTATION/TestLog review + bad-channel exclusion (Andrew 2026-06-18: "have you reviewed the instrumentation xlsx?")
- Reviewed `ShockSat1_Instrumentation_and_TestLog_Simplified_for_Delivery_20220525.xlsx` (Instrumentation_Tap +
  TestLog_Tap/NSI). FINDINGS:
  - **Bad sensors flagged:** **ch101 "bad at installation … all tests"** (= the "Mass Top +X" Y-axis = the channel
    I used for the dramatic 1000× FRF example → HONEST CORRECTION: that was largely BAD DATA, not model-form);
    **ch29–31 "60 Hz noise … all tests"** (inside our 45–260 Hz band). Other "bad/clip/double-hit" flags are for
    OTHER tests (NSD/Frangible/PlasticTip) or specific non-001 hits. **hit-001 (Test07) = "Good Data."**
  - **The 7 consistent-fail channels are NOT flagged** + clean raw data (no clip/saturation; ranges 100/10/5 kg
    appropriate). Mapped to the instrumentation list, **ALL 7 are on the +X (impact/source) face at structural
    interfaces**: bulkheads (ch40,69), bolted joint (ch52), strut base (ch92), dish (ch98), source face (ch4,27).
    → the held-out ceiling = JOINT/INTERFACE model-form + near-field dynamics on the impact face (classic StatFEM
    hard part), data-confirmed, not sampler/mapping/data.
- **ACTION (data hygiene):** added `realfrf.BAD_DAQ={29,30,31,101}` → excluded from build_channels (84 mapped, 77
  eligible). RE-RAN: heldout_qoi_L5 (clean: cover 0.94, interval 1.66e3 ≈ unchanged → ch101 wasn't dominating),
  MC + MC-report (detached, PID 82959), figures, packet (ch101 correction + joint/impact-face finding). check.py
  after. The exclusion is unambiguous data hygiene (test-engineer-flagged), not a verdict-moving scoring change.

## D20 — COMPREHENSIVE mode-shape likelihood PLAN + begin (Andrew 2026-06-18: read Bayesian bridge = Argyris Metsovo; reformulate plan + train/test splits; begin sim)
- **Bayesian bridge = Argyris, Papadimitriou, Panetsos, Tsopelas (2020) "Bayesian Model-Updating Using Features of
  Modal Data: Application to the Metsovo Bridge", J. Sens. Actuator Netw. 9:27** (`../bayesian bridge.pdf`).
  - Freq likelihood Eq 3: ω̂²_r=ω²_r(θ)+ε, ε~N(0,(σ_ωr ω̂²_r)²) = OUR L5. Mode-shape: residual ||φ̂_r−β_r(θ)φ_r(θ)||²
    with optimal scale β_r=φ̂_rᵀφ_r/‖φ_r‖² (Eq 6) → ∝ (1−MAC_r) (the MAC complement).
  - **KEY INSIGHT (their thesis):** the MAC value is ONE feature per mode → likelihood is INSENSITIVE to redundant /
    closely-spaced sensors. The conventional per-COMPONENT mode-shape discrepancy vector OVER-counts (N_sensors data
    pts/mode) → "unrealistically thin uncertainty bounds for a large number of sensors." **We have exactly that
    (87 ch, triads 98/99, 100/101/102 at one spot)** → MAC is the right shape feature; per-component needs spatial
    correlation to not over-count.
- **Measured mode shapes WITHOUT a separate dataset:** extract the QUADRATURE operating-deflection shape from the
  single-impact FRF — φ̂_r|_s = Im(H_s(ω̂_r)) at each consensus peak (the imaginary part at resonance ≈ the mode
  shape for light damping; signed). Keeps everything in the impact-hammer dataset + works with held-out channels
  (a held-out channel's measured shape = its FRF at ω̂_r, used ONLY for validation).
- **LIKELIHOOD DIRECTIONS (all keep the freq term + our orthogonal-Schneider SPATIAL discrepancy for held-out
  prediction; vary how shapes enter):**
  - L5 freq-only [baseline, have].
  - **L6 freq + MAC** (Argyris): + Σ_r (1−MAC_r)²/σ²_mac, MAC at OBSERVED ch. 1 feature/mode → redundant-robust.
  - **L7 freq + per-component shape residual, SPATIALLY CORRELATED** (Schneider C_z whitening): tests whether spatial
    correlation cures the over-counting Argyris warns about (the "conventional" form, rescued).
  - **L8 Beck mode-matching-free** (Kiran Eq 27–28): infer φ; Rayleigh-quotient freq + ORTHOGONAL (I−φ̂φ̂ᵀ) MAC term
    → avoids FEM-eigvec gradient (the Sim-B 174-div pathology).
  - **L9 = L6 calibration + orthogonal-Schneider held-out discrepancy** (full): modal+MAC θ, spatial discrepancy transfer.
  - Sampler: NUTS detector → TMCMC if multimodal (MAC uses eigvecs → watch convergence; L8 avoids it).
- **TRAIN/TEST SPLITS (validate that shapes SHARPEN the ×2.7 bands without breaking calibration):**
  - (a) RANDOM channel splits, ≥25 (have harness) → score distributions.
  - (b) SPATIALLY-STRATIFIED / leave-a-region-out splits (held-out far from observed) → honest spatial generalization,
    and the genuine redundant-sensor test (don't let a triad have 2 obs + 1 held-out = trivial).
  - (c) HELD-OUT-MODE split (calibrate low modes, predict high) → modal extrapolation.
  - WIN CONDITION: a shape-augmented likelihood that stays CALIBRATED (held-out coverage ≈0.95, z-std≈1) AND is
    SHARPER (lower held-out interval score) than L5 — i.e. mode-shape info reduces the ×2.7 amplitude bands.
- **BEGIN:** build `code/modal_mac.py` (L6) reusing `modal_feature`/`heldout_qoi`; smoke → run on split0 → held-out
  QOI vs L5 (sharper?). Then L8, L7, L9. Study artifacts (no §14 stop); surfacing only a verdict-moving scoring change.
- **L6 RESULT (verified, full 1000×4, `out/modal_mac.json`):** BOTH converge (L5 R̂1.001; L6 R̂1.003, 2 div — MAC is
  numerically clean, unlike Sim-B 174 div). **MAC does NOT meaningfully sharpen:** held-out peak IS 1386 vs 1422
  (−2.5%, within noise), width 33.3 vs 33.7 dB, σ_QOI 0.99 vs 1.00, cover 0.91 vs 0.88. σ_mac inflates to 0.84 →
  the 4 identifiable STIFFNESS groups have ~no leverage over mode SHAPES (geometry/mass model-form, not stiffness).
  Clean negative for "MAC+stiffness" as the sharpening lever → motivates L8 (infer the shapes themselves).
- **MC PATTERNS (`out/mc_pattern_summary.json`, 25 splits):** failure is LOCATION-specific, not SNR/run-luck —
  7 channels consistently FAIL (pass≤0.34: ch 4,27,40,52,69,92,98), 59 consistently PASS; pass-rate corr vs DR=+0.06
  (≈0), vs z-height=−0.10. `fig_hard_locations.png`: the 7 cluster on the RIGHT EDGE (x≈+9), a vertical column
  co-located with the IMPACT/drive (ch4/27 at the drive) → near-drive / drive-side-edge dynamics, spatially structured.
- **L8 built (`code/modal_beck.py`) + kicked off, but PIVOTAL DATA FINDING stopped it: the single-impact-FRF mode
  shapes are UNUSABLE.** Operating-deflection shapes from Im/|H|/complex H at peaks give MAC ~0.04 (freq-matched)
  and only ~0.19 best-MAC vs FEM — because 24 dense in-band modes make the ODS a superposition, NOT a clean mode
  shape. So L6's null + L8-on-ODS are DATA-limited, not formulation-limited.
- **`.ash` EMA MODE SHAPES (measured_modes.npz, 33 modes × 76 nodes × 3 axes) ARE GOOD** — vs FEM: freq-matched MAC
  ~0.30 but **MAC-matched ~0.73** (clean low modes 0.97/0.88/0.98; most modes best-MAC 0.5–0.96). TWO corrections:
  (1) **the FEM mode shapes are actually DECENT** — my earlier "ceiling = wrong mode shapes" was OVERSTATED; mode-
  shape error is real but partial (MAC 0.5–0.7 for several modes), so the ×2.7 amplitude ceiling is a COMBINATION
  (residual shape error + frequency misalignment near sharp resonances + dense-mode superposition + damping), not
  mainly wrong shapes. (2) **FREQUENCY matching mis-pairs dense modes (mode crossings) → MAC-MATCHING IS ESSENTIAL.**
- **CORRECTED PLAN:** redo the shape likelihood (L6/L8) using the `.ash` EMA shapes + MAC-based matching (not single-
  impact ODS, not freq-matching). That is the viable path; pending Andrew's go. SURFACED: the "wrong mode shapes"
  framing correction is a verdict-relevant honesty update for the packet/notes.

## D19 — REFERENCE REVIEW + mode-shape/MAC likelihood test-drive plan (Andrew 2026-06-18: "review Kiran + Bayesian bridge; test-drive a few likelihoods keeping freq + spatial + orthogonal, adding mode shapes/MAC")
- **Confirmed our likelihoods are FREQUENCY-ONLY:** L5/MC/held-out all use `modal_feature.calibrate_modal` = eigenVALUE
  match only; mode shapes used only in the forward PREDICTION (FEM eigvecs, uncalibrated); MAC used NOWHERE; measured
  `.ash` shapes (76 ch) unused. The amplitude ceiling traces to this.
- **Kiran §4.3 reviewed (PDF `references/pdfs/review of Bayesian...copy.pdf`):**
  - §4.3.1 mode-matching: freq + mode-shape terms with AD-HOC relative weights (the unsolved "weighting factor"
    problem). MAC-value likelihood = **Argyris et al. [80], TMCMC, Metsovo BRIDGE** (← likely Andrew's "Bayesian
    bridge"; that exact paper is NOT in our folder).
  - §4.3.2 mode-matching-FREE (Beck et al. [216], **Eq 27–28**): treat the system mode shapes φ_r as INFERRED
    parameters; model eigenvalue via the RAYLEIGH QUOTIENT ω²_r(θ,φ)=φ_rᵀK(θ)φ_r/φ_rᵀMφ_r; likelihood = freq
    residual (ω̂²−ω²(θ,φ))²/σ²_ω + an ORTHOGONAL mode-shape residual φ_rᵀΓᵀ(I−φ̂_rφ̂_rᵀ)Γφ_r/(σ²_φ‖Γφ_r‖²). The
    (I−φ̂φ̂ᵀ) term = the MAC COMPLEMENT (1−MAC). **KEY ADVANTAGE: φ is a free param → does NOT differentiate FEM
    eigenvectors → sidesteps the Sim-B eigvec-gradient pathology (174 div).** Γ = observation/selection matrix.
- **"Bayesian bridge" NOT FOUND as a file.** The two arXiv PDFs are Bilionis IFT (PIFT 2301.07609 + IFT state/param
  2306.02150), not it. Strong candidate = Argyris MAC-likelihood (Metsovo bridge). SURFACED: ask Andrew to point to it.
- **PROPOSED test-drive matrix (all KEEP the frequency term + our orthogonal-Schneider SPATIAL discrepancy in the
  observable; vary how mode shapes enter):** L5 freq-only [baseline, have]; **L6 freq+MAC** (mode-matching, FEM
  eigvecs, 1−MAC term, simplest); **L7 freq + SPATIALLY-CORRELATED mode-shape residual** (Schneider C_z whitening on
  the shape term — keeps spatial); **L8 Beck mode-matching-free (Eq 27–28)** = freq + ORTHOGONAL MAC term, φ inferred
  (most promising — uses shapes+orthogonal AND avoids the eigvec pathology). Sampler: NUTS detector → TMCMC if
  multimodal. Score on held-out-sensor QOI (does shape info SHARPEN the ×2.7 amplitude bands?). PENDING Andrew confirm
  on matrix + Bayesian-bridge pointer; building can start with L8+L6 (grounded in Kiran, no extra ref needed).

## D18 — #2 mapping sensitivity + NASA deterministic FRF + dB margins (Andrew 2026-06-18)
- **Mapping fidelity re-confirmed:** obs_V reconstruction 2.8e-14 (rel 1.3e-15); reduced-vs-inherited eigenfreqs
  match 9.4e-8 Hz / rel 3.2e-10 over 74 flexible modes (after removing the 6 rigid-body modes — my first compare
  vs eigvals.npy wrongly included them = the "113 Hz" artifact). We did NOT remesh; observation operator = nearest-
  kept-node SNAP (impact 0.11 in; response median 0.15, max 0.75 in; worst ch 98/99 0.75, ch 100/101/102 0.42).
- **#2 (`code/mapping_sensitivity.py` → `out/mapping_sensitivity.json`):** snap vs IDW interpolation on the 8
  worst-mapped channels shifts predicted peak by **median 0.8% (max 13%)** vs measured mismatch 0.1×–4.7× → the
  held-out misses are FEM MODE-SHAPE model-form error, NOT the mapping (ch 101: snap→interp −2.8%, under-predicts
  4.5× either way; ch 98 OVER-predicts 10×). Settles mapping-vs-model-form attribution.
- **NASA deterministic + margins:** NASA SOL111 FRFs exist as assets but are MISMATCHED-PATH (forbidden) → use the
  prior-mean θ=1 matched-path FRF as the "as-received NASA-correlated FEM" line (model reproduces NASA eigenfreqs to
  3e-10). Added to fig_heldout_frf + every report panel: deterministic θ=1 (dash-dot) + **+3 dB (×1.4125) and +6 dB
  (×1.9953) PSD margins** (FRF amplitude = √ of PSD ratio; "smaller increase in FRF space"). Checker YELLOW; QA pass.

### D13 KEYSTONE RESULT — VERIFIED at full n=4000×4 (`out/tmcmc_faithful_{M0,M1,M2}_ident4_n8.json`)
Q-A ANSWER: **faithful additive Schneider PARTIALLY tames it — fixes the EVIDENCE degeneracy but NOT θ-convergence.**
- **M0** no discrepancy: CONVERGED R̂ 1.000, ESS 4716, logZ −105485 (unimodal but catastrophic fit — no discrepancy).
- **M1** iid: R̂ 1.041 (passes), **ESS 47 (<200 → not converged)**, σ_w 1.86 (informative prior HOLDS, no 9.8 runaway), logZ −2859±0.3.
- **M2** faithful additive Schneider: **R̂ 2.577, ESS 1 → NOT converged**; σ_w pinned **12.4** (past the informative prior's
  95%-upper 5.6 → the C_add near-null-space "variance singularity" persists); logZ −2717.5 **±1.0**.
- **TWO real improvements over the D10 unfaithful config (which gave R̂ 129, evidence ±739):** (1) the evidence is now
  STABLE (±1.0 vs ±739) → USABLE for the param-count study; (2) R̂ dropped 129→2.6. But convergence is NOT achieved.
- **Evidence ranking (now stable/usable):** M2(−2717) > M1(−2859) ≫ M0(−105485) → the correlated ADDITIVE discrepancy
  genuinely fits best (Bayes evidence prefers it); iid second; no-discrepancy catastrophic. So the Schneider STRUCTURE
  helps the FIT even though θ stays multimodal. Nuance: the MORE-structured M2 (R̂ 2.6) is HARDER to sample than iid M1
  (R̂ 1.04) — the correlation structure creates the near-singular σ_w direction.
- **VERDICT (corroborates D7/D11):** the whole-FRF MAGNITUDE likelihood is intrinsically multimodal/locally-identifiable
  under real model-form error; faithfulness (additive corr + informative prior + TMCMC) stabilizes evidence + improves
  fit but does NOT confer θ-convergence, because the sharp peak-FREQUENCY-misalignment residual lives in the near-null
  space of ANY smooth discrepancy basis. The demonstrated CURE remains the MODAL/feature likelihood (L5, D11, R̂ 1.002).
  NEXT: M3 (Q-B starvation, running) + held-out-QOI scoring of the arms (YELLOW-labeled for the non-converged ones).

### D13 Q-B RESULT — VERIFIED at full n=4000×4 (`out/tmcmc_faithful_M3_ident4_n8.json`): the orthogonal projection STARVES the discrepancy
Full faithful arm table (n=4000×4, obs 8 ch × 173 f, 4-group θ, informative σ_w prior):
| arm | R̂ | ESS | log-evidence | σ_w |
|---|---|---|---|---|
| M0 no-disc | 1.000 | 4716 | −105485 | — |
| M1 iid | 1.041 | 47 | −2859 ±0.3 | 1.86 |
| M2 Schneider | 2.577 | 1 | **−2717.5 ±1.0** | 12.4 |
| M3 orthogonal | 1.112 | 17 | **−2822.1 ±0.4** | 12.6 |
- **Q-B ANSWER (the sharpened D8 headline): the M3 orthogonal projection STARVES the discrepancy.** M3 evidence
  −2822 vs M2 −2717 → **ΔlogZ ≈ −105 (Bayes factor e^105, DECISIVE preference for plain M2)**: removing the θ→FRF
  span from the discrepancy removes its ability to absorb the dominant misfit (peak amplitude near eigenfrequencies),
  which LIVES in that span → orthogonal-Schneider (the method under validation) fits the real whole-FRF WORSE.
- **The tradeoff D8 predicted, now MEASURED:** orthogonalizing HELPS sampling (M3 R̂ 1.112 < M2 2.577 — de-confounds θ
  from the discrepancy) but HURTS fit (starves it). Neither converges (ESS 17/1 ≪ 200); both σ_w pin ~12.5.
- This is NOT a blanket indictment of orthogonal-Schneider (its purpose is θ de-biasing, Plumlee/Brynjarsdottir–O'Hagan)
  — it is a concrete, evidence-backed GAP for THIS problem class: when the FEM is coarse enough that model-form error
  concentrates in the θ-sensitivity span, the orthogonal projection starves the discrepancy. The Ilias "identify a gap"
  deliverable, quantified. NEXT: held-out-sensor QOI scoring (proper scores: does correlated M2/M3 beat the marginal
  QOI-discrepancy of next-action #1, and how does the starvation show up in held-out QOI?) — needs posterior draws saved.

## D14 — DESIGN: arm held-out-QOI scoring + slide figures + MC status (Andrew 2026-06-17: "proceed with scoring + figs; propose a new sim; how many MC runs?")
- **MC ANSWER: ZERO split-MC configs done.** `out/mc_summary.json` absent; ALL held-out work is a SINGLE split
  (seed 0). Card §7 target ≥25 splits is entirely ahead (deferred until a CONVERGING config existed — L5 now is one).
- **Scoring (`code/score_arms.py`):** calibrate each whole-FRF arm (M0/M1/M2/M3) on OBSERVED channels via the
  faithful TMCMC (draws kept), predict HELD-OUT channels' peak-|H|/band-GRMS via forward(θ)+gain + a QOI-level
  marginal discrepancy exp(N(0,σ_w)) per arm, score with `score.py` → `out/scores_summary.json`
  (headline=interval_score, peak+quality weighted; arms M0/M1/M2/M3 + the L5 reference from heldout_qoi_L5.json).
  Arms are YELLOW (non-converged, ESS 1–17, D13) — labeled. EXPECTED honest result: M2/M3 σ_w≈12 → held-out QOI
  uselessly WIDE (≈e^12); M0 overconfident; only the CONVERGED L5+marginal (σ_QOI≈0.98, next-action #1) is
  calibrated AND usable. Spatial-kriging transfer (conditioning held-out on observed residual) deferred + noted
  (σ_w≈12 + non-convergence → it would not rescue them). n=1500×4 (YELLOW arms; speed).
- **Figures (slide-ready, tufte-compliant, lint+image-QA):** built from data IN HAND — (a) arm convergence+evidence
  comparison (Q-A/Q-B keystone story); (b) held-out-QOI calibration θ-only-vs-+discrepancy (next-action #1);
  (c) error-vs-participation FEM graphic (identifiability strain-energy × inferred θ-deviation). fig_scoring_suite
  from the scoring run; fig_mc_distributions PENDING the MC. All study artifacts (no §14 stop).

### D14 FIGURES DONE (3 of the slide set; `code/figures.py`, tufte-lint clean, image_qa ALL_OK)
- `figures/fig_error_participation.png` (checker-required): one dot/group, x=peak modal strain-energy %, y=L5
  inferred stiffness correction %, area=participation×error. Shows the 4 identifiable groups (blue) carry the
  signal; cross_beam biggest correction (19%); bottom_box/top_box/plates high participation.
- `figures/fig_arms_comparison.png` (Q-A/Q-B keystone): R̂ (only M0 passes), log-evidence-vs-best (M3 starved
  −105 vs M2; M0 off-scale), σ_w (M2/M3 pin ~12.5 vs floor 1.73 / old runaway 9.8).
- `figures/fig_scoring_suite.png` (checker-required): held-out QOI θ-only (overconfident, cover 0.12, z-std 14)
  vs +QOI-discrepancy (calibrated, cover 0.91, z-std ~1, proper score improves).
- PENDING: fig_heldout_frf (predicted |H| band vs measured), fig_schematic (method/observable), fig_mc_distributions
  (needs the MC); + the figures/{image_legibility,text_overlap}_report.json the checker reads (write with all 5).

## D15 — PROPOSAL (Andrew asked "propose a new simulation"): controlled FEM-error sweep to map the convergence boundary
Pending Andrew's pick (a new study DIRECTION → SURFACE, do not self-launch). Motivation: our central negative —
the whole-FRF magnitude likelihood is multimodal/singular on REAL data (NUTS R̂ 104, TMCMC 129, faithful M2 2.58)
while the SYNTHETIC companion CONVERGED (R̂ 1.002) — differs only in the FEM-vs-truth model-form error δ (synthetic
truth came from the SAME model → δ=0). 
- **PRIMARY proposal — synthetic FEM-perturbation sweep:** generate synthetic truth from a PERTURBED twin with a
  CONTROLLED peak-frequency misalignment δ (e.g. shift a subset of modes by δ% ∈ {0,1,2,5,10,20}), then run the
  faithful M2/M3 whole-FRF TMCMC at each δ. QUESTION: at what δ does the whole-FRF magnitude likelihood transition
  from converging (Schneider regime) to multimodal/σ_w-runaway (our real-data regime)? Deliverable: a convergence-
  vs-δ curve + the σ_w(δ) runaway onset = a PRE-TEST DESIGN NUMBER ("the FEM must align peaks within ~δ* Hz for the
  whole-FRF likelihood to be usable"). Cleanly explains our negative as FEM-coarseness, not method failure, and
  bounds when orthogonal-Schneider is safe vs starves.
- **SECONDARY proposal — amplitude/damping modal-feature likelihood:** the positive L5 result is calibrated-but-WIDE
  (×2.7 amplitude error, dominated by single-ζ damping model-form, the Schneider Fig-6 floor). Extend L5 to a
  (peak-frequency + peak-amplitude) modal-feature likelihood that infers θ AND per-mode damping ζ_r from the measured
  peak amplitudes, then predict held-out QOI — does per-mode damping SHARPEN the calibrated bands? Attacks the
  remaining gap in our positive result. Both are within the plain-ShockSat / real-FRF constraints.

### D15 APPROVED (Andrew 2026-06-17: "Run A and B") — build + run BOTH new simulations
- **B (`code/modal_amp_feature.py`) FIRST** (fast NUTS, completes the positive arc): extend L5 to a
  (peak-frequency + peak-AMPLITUDE) modal-feature likelihood inferring θ (4 groups) + per-mode loss factor η_r +
  gain c + σ_a, from observed channels. Amplitude model (on-resonance): |H_peak,r,s| ≈ |φ_{s,r} φ_{d,r}| / η_r · e^c
  (φ = mode shape from Q(θ); |·| removes eigvec sign ambiguity). Predict held-out QOI by modal-superposition FRF
  with the inferred per-mode η_r. Q: does per-mode damping SHARPEN the calibrated-but-wide L5+marginal (×2.7) bands?
- **A (`code/fem_error_sweep.py`) SECOND, detached** (the compute sweep): synthetic truth = FEM(θ=1) with per-mode
  frequency perturbation λ_k→λ_k(1+δ·ξ_k)², ξ_k=±1 fixed-seed (same mode shapes → pure peak-MISALIGNMENT model-form
  error, no global-θ escape). Sweep δ∈{0,1,2,5,10,20}%; faithful M2 whole-FRF TMCMC at each; record cross-run R̂,
  σ_w, logZ vs δ → the convergence boundary δ* + σ_w-runaway onset = the pre-test design number. δ=0 must reproduce
  the synthetic-study CONVERGENCE (R̂≈1) as the control. Labeled SYNTHETIC; plain-ShockSat reduced forward.

### D13 SMOKE PRELIMINARY (superseded by the VERIFIED result above; kept for the false-positive-trap record)
n=300×2 smoke gave M2 R̂ 8.0 (vs full 2.6 — bigger population lowered R̂ but did NOT cross 1.05): small-n inflated R̂,
consistent with D10's "cheap probes mislead." σ_w 12.3 and the evidence ranking matched the full run.
- Fix #2 (informative σ_w prior) WORKS: M1 σ_w settled 1.87 (no 9.8 runaway). M0 (4θ+gain, no discrepancy)
  CONVERGED R̂ 1.001 under TMCMC where NUTS gave R̂ 475 (D7) — parsimony+tempering tames the simplest model.
- **Fix #1 (additive correlation) does NOT obviously tame M2:** smoke R̂ 8.0, σ_w blew to 12.3 PAST the informative
  prior 95%-upper (5.6). Hypothesis: the sharp peak-FREQUENCY-misalignment residual lives in the near-null space
  of ANY smooth discrepancy basis (additive OR Kronecker) → σ_w runs up covering modes it structurally can't →
  named "variance singularity" persists. BUT evidence ranks M2(−2720) > M1(−2860) ≫ M0(−105549): the correlated
  discrepancy hugely improves FIT while the θ posterior stays multimodal. CONSISTENT with D7 (multimodality
  intrinsic to whole-FRF magnitude) + corroborates that the CURE is the modal/feature likelihood (L5, D11), not
  faithfulness alone. DO NOT report as verdict until the n=4000×4 keystone confirms (could flip either way).
- BLAS-matmul whitening fix: M2 317s→42s identical result (reproducible).
- **open ambiguities:** MAC vs nearest-frequency mode matching; whether faithful Schneider (next-action #2)
  tames the whole-FRF pathology vs M3 starving the discrepancy. Verdict deliberately undecided.

## D12 — DESIGN: L5 → held-out-SENSOR QOI predictor (next-action #1; study artifact, no §14 stop)
New runner session (2026-06-17), re-grounded from files. Extends the CONVERGED modal-frequency twin (D11) to
the card's PRIMARY QOI: peak |H| and band-GRMS [g/lbf] at channels we did NOT use to fit, the held-out-sensor
trust test. Module `code/heldout_qoi.py` (self-contained; reuses `realfrf.fem_logmag`, `core.qoi_peak/qoi_band`,
`score.score_qoi`; `modal_feature.py` gets ONE additive helper `calibrate_modal`, existing converged `run()`
untouched). Design + honesty:
- **Held-out is the SENSOR.** Split the DR-eligible mapped channels into observed/held-out (seeded). Calibrate
  θ from modal peak FREQUENCIES extracted from the OBSERVED channels ONLY (frequencies are a global structural
  feature; held-out channels' magnitudes are never seen in fitting) → the L5 NUTS posterior (proven converged).
- **Amplitude calibration = ONE global gain c per draw, fit on OBSERVED channels only** (quality-weighted median
  of log|H_meas_obs| − log|H_fem_obs(θ)|; the ×100 units offset, D4). A held-out channel's predicted level is
  then a genuine prediction from FEM mode shape Q(θ) at that node + damping ζ + the global c — NONE of which
  used held-out data. So this is a real test of FEM **mode-shape + frequency** accuracy at unseen sensors.
- **Two predictive variants (honest width):** (i) θ-only (sharp, expected to UNDER-cover magnitude because L5
  calibrated frequencies, not amplitudes — the gap); (ii) θ + a residual log-mag noise σ_m estimated from the
  OBSERVED-channel residual scatter after gain (an M1-style marginal/iid amplitude-discrepancy floor transferred
  to held-out). Report BOTH; neither is dressed up as the other.
- **Scoring:** `score.score_qoi` per held-out channel → interval(Winkler)/CRPS/logpd HEADLINE + PIT/z + coverage
  SECONDARY; aggregate pit_ks_dev, z_mean/std, mean interval score, coverage frac. Damping ζ=0.01 (rf.ZETA_NOM)
  + window ζ_w (D5); ζ sweep deferred to the sensitivity gate.
- **What this is NOT (yet):** no spatial Schneider discrepancy GP on magnitude here — that is next-action #2
  (faithful Schneider under TMCMC). So L5→held-out-sensor is the "frequency-calibrated twin, gain-corrected, no
  magnitude-discrepancy" baseline; if it is sharp-but-miscalibrated on |H|, that motivates the discrepancy (the
  expected, honest scientific arc). Do NOT pre-decide; the score decides.
- Surfaced items unchanged: only a scoring WEIGHTING that materially changes the verdict, durable-rule/checker
  changes, or notes/project_log rows get a stop. This predictor + the MAC refinement are study artifacts.

### D12 RESULT (full run, `out/heldout_qoi_L5.json`, 73 s; smoke→full confirmed; 1 split seed 0)
- Calibration CONVERGED: R̂ 1.0015 / ESS 1800 / 0 div (L5 modal-freq on the 48 observed channels, 24 FEM matches,
  σ_w2≈4.4%). Global units-gain c̄≈6.23 nat-log (×508).
- **θ-only (no magnitude discrepancy): OVERCONFIDENT** — peak cover 0.12 (z_std 13.7), band 0.16 (z_std 10.5),
  logpd −690/−466; intervals 3–4 dB. Frequency calibration does NOT confer magnitude calibration.
- **θ + QOI-discrepancy (σ_QOI peak 0.98/band 0.88 log, est. on observed, transferred): CALIBRATED** — cover
  0.91/0.91, z_mean ≈0, z_std 1.03/0.79, PIT-KS 0.30, logpd −6.3/−7.3; ALL proper scores improve (peak IS
  4.69e3→1.44e3, CRPS 139→114) → informative, not band-padding. BUT wide (≈×50, 34/30 dB): calibrated-not-sharp.
- Bias diagnostic: the whole-spectrum gain under-levels the peak QOI by +0.72 log (≈×2) — FEM under-predicts
  peak amplitude (damping/mode-shape model-form error), the Schneider Fig 6 amplitude floor. Reported, not corrected.
- This is the M1-style MARGINAL discrepancy baseline. Open: does CORRELATED Schneider (M2/M3, next-action #2) beat
  it on the proper score (sharper-while-calibrated)? Does M3 orthogonal starve it? MC≥25 splits → distributions.

## D13 — DESIGN: faithful Schneider under TMCMC (next-action #2; study artifact, no §14 stop)
Fixes the THREE unfaithfulnesses (D8/D10) of `real_arms.py` M2/M3, then tests Q-A "does faithful Schneider TAME
the whole-FRF pathology that the unfaithful config + NUTS (R̂ 104) + TMCMC (R̂ 129, evidence ±739, D10) could
not?" and Q-B "does M3 orthogonal STARVE the discrepancy vs M2?". Module `code/schneider_faithful.py` (numpy
log-like + log-prior + prior sampler → `tmcmc.run_independent`, ≥4 independent runs, cross-run R̂ + log-evidence
= the SAME checker diag fields). Magnitude (log|H|) first (matches the cached observable + quality weight; single-
hit PHASE is noisy → complex L2 deferred + documented). Fixes:
1. **ADDITIVE correlation** r·(R_ff⊗I)+(1−r)·(I⊗R_zz) [retains correlation when one distance is large] vs the
   old pure-Kronecker C_f⊗C_z [decays to ~0 if EITHER distance large]. The two terms COMMUTE → diagonalize
   EXACTLY in the product eigenbasis U_f⊗U_z with per-mode variance σ_meas² + σ_w²(r·λ_f,i + (1−r)·λ_z,j) →
   M2 is cheap/vectorizable. M3 (orthogonal projection P⊥ off the θ→log|H| Jacobian span) breaks the product
   structure → one-time full eigh of P⊥ C_add P⊥ (kept tractable with a parsimonious channel set, Schneider-style).
2. **INFORMATIVE σ_w prior** = LogNormal centered at OUR FIM-realized discrepancy floor σ_d0≈1.73 (NOT Schneider's
   finer-FEM 0.31; NOT the old HalfNormal(0.3) that ran to 9.8). log_sigma_w ~ Normal(log 1.73, 0.6) → 95%≈[0.5,5.6],
   caps the variance→∞ singularity while staying data-consistent. This is the main convergence lever.
3. **Parsimonious θ** = the 4 SE-identifiable groups [bottom_box=2, cross_beam=4, plates=6, top_box=8]
   (peak-SE>0.3) vs 9 (the param-count study, next-action #4, scores by TMCMC evidence).
Fixed (Schneider posterior values, documented; LEARNING them = batched-eigh extension): freq length l_f≈10 Hz
(LINEAR-freq SE, faithful to Schneider not the old log-freq), spatial length l_z≈2000 in (≫ structure → near-
fully spatially correlated, their l_co,z≈50 m), split r≈0.82, σ_meas=0.15, ζ=0.01. Channels = top-DR Ns≈10
(Schneider kept few clean channels). Params x=[log_theta(nfree), gain c~N(5.6,1.5), log_sigma_w]. KEYSTONE FIRST:
run faithful M2 (cheap) → Q-A; if it converges (cross-run R̂≤1.05, ESS≥200, stable evidence) faithful Schneider
TAMES it (improvement). Then M3 (slower, detached) → Q-B. Watch the D10 false-positive trap (need full n + ≥4 runs).

## D0 — Inherited hard constraints (task §2, non-negotiable)
- Plain standalone 9-group ShockSat ONLY (`shocksat_fem_modal_twin_20260609`). NO coupled tray. Checker-enforced.
- Model-form-error model under validation = ORTHOGONAL-SCHNEIDER discrepancy (synthetic study's M3): complex,
  correlated over frequency AND sensor space, projected orthogonal to the θ→observable sensitivity span. M0
  naive = contrast baseline. M1 iid / M2 plain-Schneider = optional secondary references only.
- COPY-reuse (never edit) prior scaffolds: `statfem_shocksat_eval_20260616/code/{core,nuts_arms,predict,viz,
  image_qa}.py`. Immutable `check.py` written FIRST (before results). Sharpness-aware scoring is the headline,
  NOT coverage. No SOL111/mismatched-path FRF likelihood.

## D1 — OBSERVABLE RESOLUTION (decision #1; SURFACED to Andrew, task §2/§14) — *PENDING HUMAN CALL*

### What the task card prefers
Matched-path REAL FRF: drive at the tap-impact node in OUR FEM, response at accel DOFs →
`H_sd(ω) = -ω² obs_V[s] Z(ω)⁻¹ obs_V[d]ᵀ` (impact-grid rows added to obs_V), compared to the measured H1
[g/lbf]. Fall back to modal synthesis from the `.ash` only if the raw FRF cannot be made consistent, and
say so prominently.

### What the real data actually supports (evidence: `out/observable_investigation.json`)
1. **Prior "low coherence" was a PROCESSING ARTIFACT, not dead data.** The prior runner
   (`shocksat_statfem_runner_20260609`) stored the hammer FRF via scipy Welch/csd with `nperseg=32768` over a
   single ~1 s impact transient and flagged every channel `frf_likelihood_ready=False` (median coherence
   ~0.06–0.075 over 45–260 Hz, max 0.46, **0% of band ≥ 0.5**). That is the classic "averaging segments of one
   transient" pitfall (Discretization-Resolution Gate): the impact is ONE force spike at t≈0.012 s, so most of
   the ~15 Welch segments have force≈0 → cross-spectrum noise → coherence collapses.
2. **A proper single-impact FRF recovers physical resonances.** Reprocessing hit-001 with a force window on the
   pulse + an exponential window on the response (single FFT, N=131072, Δf=1.9 Hz) gives peaks in 45–260 Hz that
   align with the 33 `.ash` measured modes to a **median |error| of 1.5–2.4 Hz** (≈ one freq bin): e.g. ch1
   71/116/168 Hz ↔ modes 70.0/117.6/168.0; ch50 69/74/120 ↔ 70.0/75.0/117.6; ch87 120/139/195 ↔
   117.6/137.2/195.7. So the measured FRF in our band is REAL signal — the matched-path FRF is NOT inherently
   invalid; the SOL111 transfer-path objection is reconciled by driving the same node in the FEM.
3. **BUT the raw FRF cannot support this card's MC requirements.** Hard data-availability facts:
   - only **1 of 4** hammer hits is present as raw `.mat` locally (the other 3 are summary-only) → cannot
     average hits or robustly estimate coherence (coherence needs ≥2 averages); the precomputed 4-hit coherence
     is the Welch artifact and is unusable.
   - only **3 of 326** instrumentation channels were ever turned into FRFs (hit-001 raw has **128** recorders →
     ~127 accel channels reprocessable, but all at the SAME single impact location).
   - The card §7 MC needs ≥25–50 configs over **impact-location × split × hit/realization**. Raw FRF gives ONE
     impact location and ONE hit → only the *split* axis is randomizable; impact-location and hit axes collapse.

### RECOMMENDATION (mine; Andrew decides) — a documented HYBRID
- **Primary held-out observable for the headline (MC ≥25 configs, sharpness suite, parameter-count study) =
  MODAL-SYNTHESIS fallback** built from the `.ash` 33 measured modes / 76 channels / 132 measured components
  (clean, build-to-build rel-std ~0.3% per `noise_floor.json`). Truth = a measured-modal-superposition FRF
  (measured ω, mode shapes, measured damping) driven at a chosen tap node; observe a few channels, hold out the
  rest; the FEM twin must predict held-out-channel QOIs. This is the card's documented fallback and is the ONLY
  observable that supports impact-location × split MC over 76 channels and multiple synthetic drive nodes.
  The "real model-form error" here = genuine FEM-vs-measured-MODE error (frequency + shape), which is exactly
  what the modal twin already quantified (σ_f≈4.6%, 4/9 identifiable).
- **Plus a REAL-FRF amplitude VALIDATION TRACK** on the reprocessed hit-001 channels at the one impact
  location: drive the tap node, hold out channels, score the orthogonal-Schneider twin against the REAL measured
  |H1| (single-impact, force/exp-windowed, coherence-screened by the per-frequency single-hit signal-to-floor).
  This delivers the genuine FEM-vs-real-FRF-amplitude model-form test the card prizes — on the configs the data
  actually supports (splits at one impact) — and supplies the §2(d) matched-path peak-alignment sanity overlay.
  Documented limit: 1 hit → no robust coherence; reported as YELLOW with the caveat.

Rationale: this honors §2's preference for the real FRF *where the data allows*, fixes the spurious
low-coherence blocker honestly, and still meets the ≥25-config MC + sharpness + parameter-count requirements
via the clean modal observable. The alternative pure paths each fail a hard requirement: pure raw-FRF can't do
the MC (1 impact/1 hit); pure modal hides the real-FRF-amplitude error the card most wants to stress.

### ASK to Andrew (do not proceed past P1 until answered)
(a) Accept the HYBRID (modal-synthesis headline + real-FRF amplitude validation track)? or
(b) Insist on real-FRF as the PRIMARY held-out observable (then the MC degrades to split-only at one impact,
    labeled), or
(c) Pure modal-synthesis (drop the real-FRF track)?
Any choice that materially changes the verdict is a §14 surface item — hence stopping here.

## D2 — OBSERVABLE RESOLVED (Andrew, 2026-06-17): ALL-REAL-FRF, single impact location
Andrew's call on D1: **option (b)** — "go all real FRF and use just the 1 impact location."
Consequences locked in:
- **Truth = the REAL measured |H1| [g/lbf]** at held-out accel channels, reprocessed from hit-001 raw as a
  single-impact FRF (force window on the pulse + exponential window on the response, single FFT). NO modal-
  synthesis fallback (dropped per Andrew). NO SOL111. Drive = the physical impact node in OUR FEM (matched path).
- **MC (§7) randomizes the observed/held-out SPLIT only** (≥25 splits over the ~127 reprocessable channels);
  impact-location and hit axes collapse to ONE each (labeled reduction, §11). Drive is fixed = the impact node.
- **θ recovery has NO ground truth on real data** → the parameter-count study (§6) is scored on **held-out QOI**
  (measurable) + θ-posterior concentration / FIM identifiability, NOT θ-recovery-error. Documented adaptation.
- **Coherence weighting (§5):** a single hit cannot give robust ordinary coherence (needs ≥2 averages). Use a
  documented per-frequency single-hit DATA-QUALITY weight (response-power vs pre-impact baseline-noise SNR) +
  band-restriction to the resonance-rich region; labeled YELLOW (1-hit, not multi-average coherence). If this
  weighting materially changes the verdict I will SURFACE it (§14).
- **GATE before calibrating (§2(d), GREEN-required):** verify the FEM matched-path FRF is sane — peak alignment
  AND absolute g/lbf amplitude ballpark vs the measured FRF — and resolve units. Risk: the reduced model's
  mode-shape normalization may not directly give g/lbf; if there is a constant scale offset, add ONE explicit
  global units-gain nuisance (log-additive constant) rather than normalizing amplitude away. If the FRF CANNOT
  be made consistent at all, that contradicts Andrew's all-real-FRF choice → SURFACE before any fallback.

## D3 — impact-node drive + obs_V extension (P1.5 DONE)
- **DOF/geometry mapping (verified):** full DOF id = 6·node_idx + axis (0=X,1=Y,2=Z); node_idx → modal twin
  `fem_model.npz` gids/xyz. The 76 modal sensor nodes = gids[0:76] (1101–1176). The reused reduced model is
  74-dim; the full reduced basis is `V_keep` (399510×80). The map **reduced_row(74) = V_keep[keeprow(dof),:80] @ T**,
  with `T = lstsq(V_keep[obs_dofs,:80], obs_V)` (80×74), reconstructs obs_V to 2.8e-14 and generalizes to
  held-out sensor rows to 2.3e-11 → I can place ANY kept FEM DOF (impact node or real tap channel) in the
  calibration basis. Code: `code/probe_matched_path.py::reduced_row`.
- **Impact drive:** TestLog hit-001 "+X Face, Normal", point (9,8,1) in → nearest kept gid 1023071
  (node idx 22951) at (8.94, 8.0, 1.09), 0.11 in away → drive DOF = X. (Alt (9,9,0) → idx 21512, 0.46 in;
  using the more specific (9,8,1) impact-point column.)
- **Real response channels:** the hammer DAQ channels sit at TAP grids (9900001/16/28), which are NOT real
  gids but each is within 0.15–0.42 in of a kept real FEM node → use the nearest-kept-node DOF on the channel's
  `structural_axis`. Sub-element distance; flagged as an observation-operator approximation.

## D5 — single-hit data-quality weight (the 1-hit "coherence" substitute) + channel set
- Ordinary coherence needs ≥2 averages; with 1 hit it is unavailable (a clean pre-impact baseline is also
  unavailable — the hammer strikes at t≈0.012 s, only ~2758 quiet samples before it). RESOLUTION (baseline-free,
  within-channel): `w(f) = [S_Y/(S_Y+floor_Y)] · [|F|²/(|F|²+5·floor_F)]`, where S_Y=|response FFT|², floor_Y =
  25th-pct of S_Y in band (the inter-peak/noise level for that channel), |F|² = force spectrum, floor_F = its
  high-freq (>8 kHz) roll-off level. This emphasizes informative resonance peaks AND down-weights where the
  hammer force has rolled off — a defensible single-hit coherence analog. Labeled YELLOW (1-hit, not multi-average).
- **Channel set:** 87 of DAQ 1–115 tap_impact accels map to a kept FEM node (snap ≤0.75 in); dynamic range
  (in-band peak/floor) median 147× (21 dB), 89 channels >50×, 68 >100× → ample for held-out splits. Channels
  screened by dynamic range for the MC.
- **Window-added damping:** the exponential response window adds ζ_w(f)=1/(2πf·τ) ≈ 0.99/0.50/0.25 % at
  60/120/240 Hz (τ from exp_end=0.05, N=200000). So measured effective damping ≈ ζ_real(.ash 0.06–1.05%) + ζ_w
  ≈ 0.5–2% → FEM ζ_nom=0.01 is consistent; ζ_w recorded as part of the observation model + a sensitivity item.
- **Likelihood grid:** native measured Δf=1.25 Hz (N=200000), 173 points in 45–260 Hz; peak resolution
  (~1–2 pts/peak at ζ_eff~0.5–1.5%) flagged as a discretization caveat.

## D4 — UNITS + DAMPING resolved; P1.5 §2(d) GATE = **PASS** (`out/matched_path_sanity.json`)
- **Peak alignment (structure sane):** FEM first mode 54.6 Hz ≈ measured/.ash 54.2 Hz; FEM and measured both
  populate 45–260 Hz with several near-matches (e.g. FEM 147↔meas 149; FEM 249↔meas 252) AND genuine
  mismatches (measured 116/133/168/219 not placed by the nominal FEM) = the REAL FEM-vs-structure model-form
  error we calibrate (consistent with the modal twin's σ_f≈4.6%). The matched-path FRF is makeable-consistent
  → honors Andrew's all-real-FRF choice; no fallback.
- **Absolute amplitude = a GLOBAL units-gain.** Smoothed (log-freq) log10(meas/FEM) is **+1.90 to +2.12
  (≈ ×100) across ALL 3 channels and stable across ζ∈{0.003,0.01,0.02}** → it is NOT damping and NOT
  per-channel; it is a global mode-shape mass-normalization/`g` constant in the reused reduced basis (frequencies
  verified exact, reduced-vs-full eigval err 1e-10; likely ≈386×O(1) from a g/slinch convention). **RESOLUTION:
  add ONE global units-gain nuisance** `c` (model log|H| → log|H_fem| + c), weakly-informative Normal prior
  centred on the empirical offset; identified by observed channels, transfers to held-out. Documented assumption,
  does NOT affect model-form/relative conclusions. Residual smoothed-log-ratio std ≈ 0.5–0.8 (3–6×) = the true
  amplitude discrepancy the orthogonal-Schneider arm must cover.
- **Damping:** the offset is units (above), but ζ still sets peak SHAPE/amplitude (the QOI). Free-free .ash ζ is
  0.06–1.05% (median 0.32%) but installed config is stiffer/dampier; nominal ζ=0.01 with a sensitivity sweep
  {0.003,0.01,0.02}. Constant-η differentiable path (D10 reuse); per-mode-ζ would re-require eigh in the
  gradient (D10 forbids) → documented non-arm.
- **Observable LOCKED:** measured truth = single-impact FRF (force window 2 ms on the pulse + exponential
  response window, N=131072, Δf≈1.9 Hz) of hit-001; model = FEM matched-path accelerance g/lbf + global gain;
  likelihood = whole log|H| over observed channels, SNR/coherence-weighted + band-restricted (45–260 Hz).
  (Note: production run uses N=200000, Δf≈1.25 Hz, 173 band points — D5.)

## D6 — SANITY CELL FINDING: naive AND orthogonal both go multimodal on the real FRF (P1 close / P2 open)
Split0 (n_obs=8, ζ=0.01, 4 chains × 1000+1000), `out/cells/split0_n8_z0.01_{M0,M3}.json`:
- **M0 naive: NOT-YET-CONVERGED** R-hat 114.9, ESS 2, **0 div** (multimodal, not pathological geometry); gain 5.56.
- **M3 orthogonal: NOT-YET-CONVERGED** R-hat 104.0, ESS 2, **0 div**; gain 6.67; **σ_d RAN AWAY to 9.82**
  (prior HalfNormal(0.3)) — the discrepancy variance inflates to ~e^9.8 to swallow the residual, flattening θ.
- **Identifiability gate** (`out/identifiability.json`): strain energy → 4 groups peak-SE>0.3 (plates,
  bottom_box, top_box, cross_beam = the modal-twin 4/9); FIM @ realized floor σ_d0=**1.726** → eigvals
  ~1e6–1e7, "9/9 above prior". The FIM (LOCAL) says hyper-identifiable; the posterior (GLOBAL) is multimodal →
  consistent: the FRF-magnitude likelihood is **locally hyper-sensitive but globally multimodal** — many narrow
  θ basins each fit the peaks, no dominant basin because the FEM cannot reach the measured FRF (real model-form
  error). Peak-FREQUENCY misalignment makes huge log|H| residual spikes that the SMOOTH Schneider discrepancy
  can't absorb and the under-identified θ can't cleanly fix → σ_d runaway + multimodality.
- **This is the genuine "it may not be working" (Ilias) finding** — the synthetic study converged (R-hat 1.002)
  only because its truth came from the SAME model so one basin dominated; real model-form error removes that.
- **Per §12 (do NOT call an arm failed for non-convergence), TEST principled fixes BEFORE any verdict**
  (`code/diagnose_convergence.py`, detached → `out/diagnose_convergence.json`): (A) fix σ_d at the realized
  floor 1.726 → kill the runaway; (B) downselect to the 4 SE-identifiable groups [2,4,6,8] → cut excess θ
  dimensions; (C) both; + M0/M1 downselected contrasts. Whichever converges (R-hat≤1.05/ESS≥200/div<2%) becomes
  the P2-scoring + P4-MC configuration; this IS the parameter-count study's (§6) point. Shaping toward a
  YELLOW/negative verdict (twin under-identified on single-impact real FRF) + concrete improvements; not
  pre-deciding — the diagnostic decides.

## D7 — DIAGNOSTIC VERDICT: the multimodality is INTRINSIC to the whole-FRF-magnitude likelihood
`out/diagnose_convergence.json` (split0, 4 chains × 400+400): ALL 5 configs NON-CONVERGED, R-hat 34–475,
ESS 2, ~0 div:
- M3 full9 + σ_d FIXED@floor 1.73 → R-hat 101.6 (fixing σ_d does NOT fix it)
- M3 ident4 + σ_d sampled → R-hat 152 (σ_d runs away to 9.98 again)
- M3 ident4 + σ_d FIXED@floor → R-hat 232.9 (downselect + fix together does NOT fix it)
- **M0 ident4 (4 stiffness θ + gain, NO discrepancy) → R-hat 474.8** ← the smoking gun
- M1 iid ident4 → R-hat 34.8
**Conclusion:** the multimodality is NOT caused by σ_d runaway or excess θ dimensions — even a 5-parameter
stiffness-only model is severely multimodal against the real FRF MAGNITUDE. The whole-log|H| likelihood is
intrinsically multimodal in stiffness under real model-form error: |H(ω;θ)| is a highly nonlinear, oscillatory
function of θ (peaks sweep through each other), so many θ each fit the observed peaks comparably and no basin
dominates (data-space agreement, parameter-space disagreement; the FIM-huge-but-multimodal signature). Robust
negative for the transplanted whole-FRF likelihood.
- The project's OWN prior work already found the cure: MODAL-FEATURE likelihoods (per-mode peak frequencies)
  CONVERGE on this exact structure (modal twin full-18-mode R-hat 1.022; Study K per-mode freq R-hat 1.007,
  5/5 held-out). The whole-FRF-magnitude likelihood was the synthetic study's choice; it does not transfer to
  real model-form error.
- **SURFACED to Andrew (D8 pending): the likelihood/path fork** — (1) attack multimodality directly
  (tempering / SMC / multi-start stacking) to test whether the marginal held-out QOI is calibrated-but-wide
  despite unidentified θ (keeps observable + whole-FRF likelihood; heavy compute); (2) switch to an
  FRF-FEATURE likelihood (peak frequencies/amplitudes from the REAL FRF — still Andrew's real-FRF observable,
  identifiable, proven to converge); (3) report the robust negative + recommend. Changes the core likelihood and
  the verdict → §14 surface; do NOT self-decide.

## D8 — REFERENCE GATE (Andrew supplied 2 papers): our findings are NAMED in the literature; the sampler is the gap
Full notes: `references_reviewed.md`. Papers: Kiran/Das/Bansal 2025 review (Prob Eng Mech 80:103761) + Schneider
et al. 2022 (MSSP 166:108407 = the SOURCE of our M2/M3 discrepancy, ref [184] in the review).
- **Our multimodality = "LOCAL identifiability"** (Beck–Katafygiotis; Kiran §3.2/Fig 1): a FINITE number of
  output-equivalent θ basins. Named, expected — not a bug. **Our σ_d→9.8 = the named likelihood singularity**
  "variance parameters approaching extreme values such as zero or infinity" (Kiran §3.4.2, verbatim).
- **THE SAMPLER IS THE GAP, not (only) the likelihood.** Schneider sampled with **BUS + Subset Simulation (SuS)**,
  chosen because Laplace/gradient methods are "difficult to obtain in MULTIMODAL (non-uniquely identifiable)
  problems." The FE-updating field uses TMCMC/Gibbs/SuS (multimodal/tempered); NUTS is rare. → Our NUTS run is an
  honest DIAGNOSTIC of the multimodality, but NUTS cannot cross modes; the method's own literature uses
  multimodal-capable samplers. **This is a SAMPLER-STANDARD question vs the AGENTS.md NUTS rule → SURFACED for
  human approval (durable-rule stop).** Justification to switch (TMCMC or SuS, for THIS multimodal FRF posterior):
  documented + literature-standard + what the source paper used; NUTS retained as the diagnostic that exposes
  the multimodality.
- **We did NOT implement Schneider faithfully** (so our "negative" is partly OUR simplification): (i) we used
  pure-Kronecker C_f⊗C_z (decays to 0 if either distance large) vs Schneider's ADDITIVE r(R_ff⊗I)+(1−r)(I⊗R_zz);
  (ii) we FIX correlation lengths + learn only σ_d, vs Schneider LEARNS σ_w,σ_θ,l_co,z,l_co,f,r; (iii) Schneider
  restricted to a clean band + dropped low-coherence channels + used 3–4 well-conditioned GLOBAL params (not 9
  groups). Faithful validation must add (i)+(ii) and the parsimonious parameterization (the parameter-count study,
  now grounded in Schneider's shell-vs-solid EVIDENCE comparison + Ockham).
- **The damping-limited peak-amplitude misfit is FUNDAMENTAL and corroborated** (Schneider Fig 6/§5.4, verbatim:
  "amplitudes are not well predicted around the eigenfrequencies... cannot be achieved by a single damping
  ratio... damping model is too limited"). Their σ_w≈0.31 ABSORBS it → ~90% coverage with misses CONCENTRATED at
  eigenfrequencies. So the realistic BEST case here = calibrated coverage with eigenfrequency-localized misses,
  NOT perfection. Our σ_d ran away (not 0.31) because we used the whole band + 9 params + NUTS instead of their
  recipe.
- **Sharpened M2-vs-M3 question:** the orthogonal projection (M3) removes the θ-span from the discrepancy, but the
  dominant misfit (peak freq/amplitude) lives NEAR the θ-span → M3 may STARVE the discrepancy where plain
  Schneider (M2) absorbs it. M2-vs-M3 on real data is now a central, testable result (does orthogonalizing help
  by de-biasing θ, or hurt by starving the discrepancy?).
- **REVISED PLAN (pending Andrew's sampler call):** (a) switch to a multimodal-capable sampler (TMCMC or SuS) for
  the FRF posterior [SURFACE]; (b) implement Schneider faithfully — additive correlation + learned hyperparameters
  + complex (mag+phase) multiplicative error; (c) parameter-count via EVIDENCE incl. a parsimonious global
  parameterization; (d) coherence/quality band+channel restriction (1-hit version); (e) report M0 naive vs M2
  Schneider vs M3 orthogonal under the proper sampler, with the sharpness suite + the honest "eigenfrequency-miss"
  caveat. Keep the NUTS multimodality result as the headline DIAGNOSTIC finding. Cheap multi-start probe (no
  sampler change) still planned to visualize local identifiability (= Katafygiotis–Beck "find all output-equivalent
  optima").

## D9 — Andrew APPROVED (2026-06-17): adaptive sampler + likelihood sweep + threshold-as-variable
Andrew: "Yes. modify our ablation study to move to TMCMC or BUS-SUS if multi-modality is illuminated by NUTS.
Sweep the most promising likelihood methods from the Kiran review and from Schneider. If we quality restrict to
certain peaks/frequency bands, include the threshold we select as another variable that we sweep."
Compliance note: this USES a non-NUTS sampler for THIS study with documented justification (AGENTS.md NUTS rule
allows this — "say why in the task card and report"); NO edit to AGENTS.md, and check.py stays immutable —
TMCMC cells will populate the SAME diag fields (max_rhat from ≥4 INDEPENDENT TMCMC runs, min_ess from the final
weighted population, div_frac=0) so the existing convergence gate applies unchanged.
DESIGN (sweep dimensions):
- **Sampler protocol (adaptive):** run NUTS first (the diagnostic). If it passes the gate → keep it. If it shows
  the local-identifiability signature (R-hat≫1.05, ESS small, ~0 div) → ESCALATE to **TMCMC** (Ching & Chen 2007:
  tempered sequential MC, prior→posterior via β:0→1, CoV-targeted Δβ, resample + RW-Metropolis rejuvenation).
  TMCMC chosen over BUS-SuS because it ALSO returns the model EVIDENCE (∏ stage normalisers) → directly powers
  the parameter-count/§5 model-class-selection study. (BUS-SuS = documented fallback if TMCMC struggles.)
- **Likelihood sweep (most promising from Kiran §4 + Schneider):** (L1) whole log|H| magnitude iid [naive
  baseline / the multimodality diagnostic]; (L2) Schneider complex multiplicative (mag+phase) with ADDITIVE
  space+freq correlation + LEARNED hyperparameters (the faithful M2); (L3) orthogonal-Schneider (M2 + P_perp =
  M3, method under validation); (L4) complex additive circular-Gaussian on Ĥ−H(θ) with covariance Γ
  (Fathi/Zhang Eq 20); (L5) modal peak-frequency feature likelihood (Kiran §4.3 eigenvalue approach — the
  well-behaved modal-domain method). NOT-APPLICABLE-with-1-hit (documented): Yan ratio distribution (Eq 21–23)
  needs spectral expectations over multiple averages.
- **Quality threshold = a SWEPT VARIABLE (Andrew):** τ over the single-hit quality weight / peak-keep level —
  e.g. {full band, w>0.3, w>0.5, top-K peaks K∈{all,12,6}} — report which τ maximises held-out score (the
  "how much to keep / trust" knob). Surfaces the sensor/band-selection payoff.
- **Parameterization:** 9-group vs parsimonious global subset (the param-count study, scored by EVIDENCE from TMCMC).
- **MC over splits** (≥25) on the chosen converged configuration.
- **check.py immutability preserved;** NUTS retained + reported as the diagnostic that exposes multimodality.
KEYSTONE FIRST (this phase): implement TMCMC (`code/tmcmc.py`), prove it RESOLVES the exact split0-M3 cell NUTS
went multimodal on (same fixed-length likelihood; isolate sampler as the only change), with ≥4 independent
runs agreeing (cross-run R-hat) + a stable log-evidence. THEN add L2/L4/L5 + the τ sweep + param-count.

## D10 — KEYSTONE RESULT (honest): sampler swap ALONE does NOT fix the unfaithful configuration
`out/tmcmc_probe_M3.json` (split0 M3, fixed-length pure-Kronecker covariance, free σ_d, 9 params, whole log|H|):
- TMCMC self-test (bimodal toy) = PASS (both modes, R-hat 1.001, evidence std 0.01) → sampler is correct.
- **MINI run (n=400, 2 runs) gave R-hat 1.06 = a FALSE POSITIVE** (the project's recurring "cheap probes mislead
  both ways" lesson; Study G 2-chain false-pos, Study K 2-chain false-neg).
- **FULL run (n=1500, 4 runs, ~50 stages, 992 s): NOT CONVERGED — cross-run R-hat 129.4, ESS≈0, log-evidence
  −17900 ± 739** (runs disagree catastrophically), σ_d 7.41 [1.30, 8.66] (still the variance runaway).
- **Interpretation:** swapping NUTS→TMCMC on the UNFAITHFUL configuration does not rescue it. The free σ_d +
  fixed-length pure-Kronecker covariance creates a near-singular posterior (the named "variance→∞" singularity),
  so even the tempered sampler's importance weights degenerate (huge evidence variance). **The CONFIGURATION, not
  just the sampler, is the problem** — exactly D8's point that we never implemented Schneider faithfully.
- **REDIRECT (do BOTH, not sampler-only):** (i) implement Schneider FAITHFULLY — additive space+freq correlation
  + LEARNED correlation lengths/split (so the discrepancy STRUCTURE matches the residual instead of σ_d blowing
  up) + an INFORMATIVE σ_d prior (Schneider used lognormal mean ~0.1, not HalfNormal(0.3)) to kill the variance
  singularity; (ii) parsimonious parameterization (fewer, better-conditioned params); (iii) LARGER TMCMC
  population (n≥4000–8000) + more rejuvenation; (iv) keep the τ sweep + param-count-by-evidence. The keystone's
  value: it PROVES the fix must be the likelihood configuration + prior, not the sampler alone — and it documents
  a clean false-positive (small-n) vs the 4-run gate truth.
- check.py untouched; NUTS + TMCMC-at-n1500 BOTH now documented as exposing the pathology (not a clean pass).

## D11 — BREAKTHROUGH: modal peak-FREQUENCY feature likelihood (L5) CONVERGES on the real FRF
`out/modal_feature.json`, `code/modal_feature.py`. Peaks extracted FROM the real single-impact FRF (hit-001,
high-DR channels, histogram-of-peaks consensus) → **44 consensus measured modes, 27 matched to FEM modes** (≤12%,
nearest-frequency; low modes align with .ash to ~1–6 Hz). Eigenvalue likelihood (Kiran Eq 25), eigenVALUES are
cleanly differentiable (no eigenvector degeneracy) → NUTS:
- **CONVERGED: R-hat 1.002, ESS 2388, 0 div (60 s)** — clean, exactly as the modal twin (R-hat 1.022) + Kiran §4.3
  predict. Observe 21 modes, hold out 6.
- **Held-out-MODE coverage 6/6 (100%)** — calibrated twin predicts held-out modal frequencies within 95% bands.
- σ_w2 (rel. modal-freq error) ≈ 0.069 (~7%, ≈ the FEM model-form floor σ_f≈4.6%). θ medians: cross_beam 0.81,
  bottom_box 0.90, top_box 1.05, rest ≈1 — modest, sensible corrections.
- **THE VALIDATION ARC RESOLVES (the Ilias deliverable): the whole-|H| MAGNITUDE likelihood is locally-
  identifiable / near-singular on real data (NUTS R-hat 104, TMCMC R-hat 129 — does NOT converge); the MODAL
  peak-FREQUENCY feature likelihood from the SAME real FRF CONVERGES (R-hat 1.002) and predicts held-out features
  (6/6).** Gap identified (whole-FRF magnitude pathological); improvement demonstrated (feature/modal likelihood,
  literature-standard + matches our own modal twin).
- HONEST limits/next: (a) held-out QOI here = held-out modal FREQUENCIES; the card's held-out-SENSOR peak-|H|/GRMS
  QOI still needs the modal-superposition FRF prediction at held-out channels from the calibrated θ+shapes+damping;
  (b) nearest-frequency matching (≤12%) is cruder than MAC — refine with mode shapes (we have them); (c) some of
  the 44 "modes" may be spurious/dense — robust to the 27-matched subset. NEXT: L5 → held-out-SENSOR QOI; then
  faithful Schneider L2 (additive corr + learned lengths + informative σ_d) + complex-additive L4 + τ-threshold
  sweep + param-count-by-evidence + ≥25-split MC + figures/packet/pptx.
