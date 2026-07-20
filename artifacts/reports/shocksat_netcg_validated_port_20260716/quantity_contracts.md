# quantity_contracts — validated net-CG QOI port (card B, 2026-07-16)

Written BEFORE plotting/fitting/scoring (D1, Quantity Contract Gate). **Part A is COPIED VERBATIM from the
netcg thread's `quantity_contracts.md`** (`shocksat_netcg_method_selection_20260701/quantity_contracts.md`,
read-only) — copied, not paraphrased, because reproducing that thread's numbers requires reproducing its
contract exactly. Part B pins the width/coverage statistics that N0 is scored on. Part C is the ONE new
quantity this card introduces: the finalist→netcg mapping.

---

## PART A — net-CG FORCE contract (VERBATIM COPY from the netcg thread)

### QOI: net-CG FORCE on the top tray/plate
- **Definition (numerator).** Net-CG force = Σ_i m_i a_i over the tray's mass = the mass-weighted acceleration
  integral = equivalently the interface base reaction of the tray as a payload. Per frequency:
  `S_F_qoi(ω) = |G_qoi(ω)|² · S_input`, where `G_qoi(ω)` is the modal-sum transfer from the flat input to the
  net-CG force functional and `S_input` is the known flat input PSD (level = human judgment; cancels in all
  band-RATIO metrics, so the delivery ratios are input-level-independent).
- **Modal form.** `G_qoi(ω) = Σ_modes ω² · (Σ_{tray DOFs on axis a} m_i φ_{i}) / D_i(ω)`, with
  `D_i(ω)=ω_i²−ω²+2iζω_iω`. Uniform-mass proxy over the tray region (documented; consistent-mass = sensitivity).
- **Denominator / reference.** Reported as (i) 95%-band GRMS-force RATIO vs the FEM+6 dB incumbent envelope, and
  (ii) interval width. Also the integrated band-RMS (GRMS-force).
- **Coordinate / component.** Tray-CG translational X, Y (SHEAR, in-plane) and Z (NORMAL, out-of-plane), reported
  SEPARATELY, never blended.
- **Tray region.** FEM nodes with z >= 55 in (top plate; 4646 kept-node DOFs). Struts z 45-55; box z<45.
- **Excitation.** 100%-certain FLAT input PSD applied at the hammer-impact drive point. Examine ALL FIVE drives
  (+X/Test01, +Z/Test02, +XY/Test04, +Z@900/Test06, +Y/Test03) — per-drive prediction; the other drives supply
  the held-out-DRIVE answer key. +Y is the main observability lever for the low-trust NORMAL load.
- **Boundary condition.** Free-free modal survey basis (as measured); FEM reduced model K(θ)=A_fix+Σθ_g A_g,
  mass = I (mass-normalized reduced basis).
- **Units.** Force consistent with input (N or lbf); band metrics are dimensionless RATIOS. Frequencies Hz.
- **Band.** Data/FEM band 45-260 Hz (where measured modes + coherence live). The prompt's 20-2000 Hz DELIVERY
  band is wider than the data band; outside 45-260 Hz the twin is prior-only — flagged (assumptions_ledger A?).
- **Expected limiting behavior.** Static/rigid-body limit: as ω->0 the net-CG force -> input × total tray mass
  (rigid-body sanity check). Resonance peaks at the QOI-driving modes; roll-off away from them.
- **Expected resonance behavior.** SHEAR peaks at the measured global box modes (~114-197 Hz); NORMAL peaks at
  the drumhead plate modes (~234-254 Hz).

### Two nearby conventions (named; which we use)
- **net interface FORCE** (apparent-mass / base-reaction convention; NASA-HDBK-7004C) — **USED**.
- **net-CG ACCELERATION / GRMS** (response convention) — NOT used as the deliverable, but the band-RATIO is the
  same up to the (cancelling) tray mass, so GRMS-ratio and force-ratio coincide.

### Answer-key reconstruction (held-out)
- **heldout_drive:** fit the per-mode amplitudes on 4 drives, predict the 5th drive's net-CG force spectrum; the
  5th drive's MEASURED-mode reconstruction is the answer key the twin band must envelope (well-posed for SHEAR;
  for NORMAL the drumhead SHAPE is unmeasured -> the answer key is itself uncertain -> normal falls back to
  leave_modes_out).
- **leave_modes_out:** hide a subset of MEASURED modes, recompute the band; the KNOWN correct answer is that the
  band MUST widen to cover the hidden modes' QOI contribution. A method that stays narrow FAILS (false sharpening).

**Deviation from the copy, stated:** the netcg contract says "Examine ALL FIVE drives". This card's §3.4 VAULT
RULE overrides it: the +XY drive (Test04 / `m_xy_990xy`) is **NOT read** here. DEV drives only (+X/990x,
+Z/990z, +Y/990y, +Z@900/900z). This is a restriction, not a redefinition.

---

## PART B — the scored statistics (pinned so N0 is unambiguous)

These are the netcg thread's own definitions, in code, reused byte-identically. They are written out here
because the study's non-reproduction is hypothesized (D3) to be a divergence in exactly this contract.

### B1. Band width ratio — `sharpness_band_grms_ratio_vs_fem6db` (**THE N0 STATISTIC**)
- **Source of truth:** `netcg_method_selection/code/bakeoff.py:54` `band_ratio(band_lo, band_hi, ref_band_grms)`.
- **Numerator:** `grms(hi − lo)` — the GRMS over FGRID of the **pointwise 95% band WIDTH** (upper minus lower
  percentile of the method's net-CG force ensemble). Units: same as |G| (∝√PSD, arb.); cancels in the ratio.
- **Denominator:** `grms(fem6_hi − fem6_lo)` where `fem6_hi = nom·10^(6/20)`, `fem6_lo = nom/10^(6/20)`, and
  `nom = model.spectrum(theta_map, axis)` = the nominal net-CG force spectrum at the θ posterior MEDIAN. So the
  denominator is the **FEM+6dB incumbent band's width**, = `grms(nom)·(1.995 − 0.501) = 1.494·grms(nom)`.
- **`grms(y) = sqrt(mean(y²))` over FGRID** (`netcg_qoi.py:grms`). NO octave smoothing is applied to either
  numerator or denominator for this statistic.
- **Value:** dimensionless. **1.0 = exactly as wide as the FEM+6dB incumbent.** >1 = wider (more conservative)
  than the incumbent; <1 = sharper.
- **Expected limiting behavior:** a method with zero uncertainty → 0. `L5_theta_only` ≈ 1.0–1.2 (θ-only
  uncertainty is small) — and that near-1.0 is the *overconfidence signature*, not a success.
- **CONVENTION COLLISION (named explicitly — this is the C5 root-cause candidate, D3):** a *different*,
  nearby statistic is `grms(smooth(hi)) / grms(smooth(lo))` — the upper/lower **ENVELOPE ratio** on
  octave-smoothed spectra, used by the study's `full_spectrum_frf_20260714/code/netcg_wide.py:159`
  `band_width_ratio(lo, hi)`. **That is NOT this quantity**: it never references the FEM+6dB denominator and it
  is a ratio of levels, not a normalized width. The two cannot agree at any calibration. **This card uses the
  netcg `bakeoff.band_ratio` convention (Part B1) and ONLY that.** Any number I quote against 1.51/2.30/2.53
  is B1.

### B2. Coverage — `weighted_coverage`
- **Source of truth:** `netcg_qoi.py:coverage_vs_truth`, called exactly as `bakeoff.py:84` does.
- **Numerator:** energy-weighted fraction of the plausible-truth ensemble lying inside the method's [lo, hi]
  band, pointwise on FGRID, after **1-octave geometric-mean smoothing** of band and truths (`frac=1.0`),
  with tolerance factors 0.999/1.001.
- **Weights:** `w ∝ median(truths)²` — QOI ENERGY weighting, so misses at the resonances dominate and misses in
  the low-energy floor are negligible. **Denominator:** `Σw` (weights are normalized) → dimensionless ∈ [0, 1].
- **Answer key:** `netcg_qoi.truth_ensemble(model, axis, theta_map, n=200, seed=7)` — measured modes tier-0
  (SD_F 0.01 / SD_A 0.35), unmeasured modes tier-2 (SD_F 0.06 / SD_A 0.80). **This is a SYNTHETIC epistemic
  ensemble from the same model** — it tests self-consistency of the uncertainty representation, NOT truth.
  Stated as a limitation in `question_framing.md`.
- **Expected limiting behavior:** an infinitely wide band → 1.0. The FEM+6dB incumbent → 0.87 / 0.71 / 0.74
  (netcg scorecard) — i.e. the incumbent *leaks*, which is why the twin exists.
- **S3/S4 threshold: ≥0.95** (card). Reported alongside `peak_coverage` and `energy_wtd_pos_dB_exceed`.

### B3. Overconfidence audit — `widen_ratio`
- **Source of truth:** `bakeoff.py:104,114-120`. Hide the **top-3 measured QOI-driving modes** (largest |g_i|
  among measured, per axis), rebuild the band with those modes demoted to the unmeasured tier, and report
  `widen = grms(hi_hidden − lo_hidden) / grms(hi − lo)`. Dimensionless.
- **Expected behavior / pass rule:** removing information must NEVER sharpen a band. **>1 = widens = PASS**
  (card §3.3: "every band must widen (>1)"). `theta_only` gives EXACTLY 1.000 by construction (it ignores
  amplitude tiers → uncertainty invariant to information) = the overconfidence signature.
- Note: the study's audit gave shear_x 1.000 and normal_z 1.003 (review C5) — i.e. essentially inert. Under
  the netcg machinery this statistic is only meaningful for amplitude-carrying methods.

### B4. Grid / damping (Discretization Resolution Gate — INHERITED, not re-chosen)
- **FGRID:** `np.linspace(45.0, 260.0, 400)` — **LINEAR** 0.539 Hz spacing, 400 points (`netcg_qoi.py:35`).
  Inherited frozen from netcg so width ratios stay comparable to 1.51/2.30/2.53 (study ledger A5b makes the
  same choice for the same reason). Linear (not log) spacing is the netcg convention; the *plots* use a log
  frequency axis per the AGENTS Plot Gate.
- **Resolution vs the QOI-driving features:** ζ=1% → half-power bandwidth at a mode f_i is ≈ 2ζf_i = 1.09 Hz at
  54.6 Hz and 5.18 Hz at 258.9 Hz → **≈2.0 to 9.6 points per half-power bandwidth**; the sharpest (lowest-f)
  in-band mode is the least-resolved at ~2 points. Peak amplitudes on a linear grid can therefore be clipped
  at the low-frequency end. This is INHERITED from the delivered twin and is identical for every method and
  every arm compared here, so it **cancels in the width RATIO** (numerator and denominator share the grid) —
  which is exactly why the ratio, not the absolute level, is the deliverable. Resolution sensitivity is
  reported in `out/n0_reference.json` (`grid_sensitivity`) rather than assumed away.
- **ZETA = 0.01** (1% critical damping, uniform, all modes) — inherited `netcg_qoi.py:30`. Not inferred.

---

## PART C — NEW quantity: the finalist→netcg mapping (D2)

The one thing this card adds that no prior thread defines. Contract stated before use.

### C1. Per-mode relative perturbation `(δf_i, a_i)`
- **Definition.** For a finalist package X ∈ {B, D, R} and the wide BASELINE A0_wide (=A1), both evaluated on
  their **enriched exact bases** (`data/packages_wide/{X}__enr.npz`, which fold θ_MAP_wide into the projected
  blocks so `pkg.modes(ones)` reproduces the exact full solve — study D14):
  - `δf_i = f_X,i / f_A0,i` — **dimensionless frequency scale factor** per paired mode. 1.0 = the finalist
    does not move this mode.
  - `a_i = |g_X,i| / |g_A0,i|` — **dimensionless tray-participation amplitude scale factor** per paired mode,
    per QOI axis, where `g = pkg.tray[axis] @ Q[:, inband]` (the wide package's own tray selector, used ONLY
    to form this RATIO). 1.0 = the finalist does not change this mode's net-CG participation.
- **Pairing (A0 ↔ X):** Hungarian assignment on the cost `|ln(f_X,j / f_A0,i)|` over in-band (45–260 Hz)
  modes. Unpaired finalist modes are DISCARDED; unpaired baseline modes get (1, 1).
- **Transport (A0 ↔ netcg):** netcg in-band mode j (of nM=40, `netcg_qoi.QOIModel.fnom`) inherits `(δf, a)`
  from the A0_wide in-band mode nearest in frequency, **accepted only if |f_netcg,j / f_A0 − 1| ≤ 0.02**;
  otherwise `(1, 1)` = "the finalist says nothing about this mode".
- **Application:** the perturbation enters the UNMODIFIED netcg machinery through the two hooks
  `netcg_qoi.QOIModel.spectrum(theta, axis, amp=…, fscale=…)` already exposes. No netcg code is edited.
- **Units:** both dimensionless. **Expected limiting behavior:** a finalist identical to the baseline →
  δf ≡ 1, a ≡ 1 → the band is EXACTLY the N0 band.
- **Expected resonance behavior:** δf shifts peak locations; a scales peak heights. Neither can create,
  destroy, split or reorder a mode — **the stated blind spot of this mapping** (`question_framing.md`).

### C2. Validation of C1 (pre-registered, both are checker gates)
1. **Baseline-through-mapping (card §3.3):** the baseline pushed through the mapping must reproduce N0 within
   ±0.05. **Honest status: this is an IDENTITY BY CONSTRUCTION**, since A0-vs-A0 gives δf ≡ 1, a ≡ 1. It is a
   plumbing check (the hooks are wired right, nothing drifted), **not** evidence that the mapping faithfully
   transports a finalist. Reported as such — not sold as a test it isn't.
2. **Non-identity check (ADDED by me, because C2.1 is weak):** at least one finalist must actually MOVE the
   band — `max_i |δf_i − 1| > 0.001` or `max_i |ln a_i| > 0.001` for ≥1 finalist, and its width ratio must
   differ from N0's. Otherwise the mapping is silently inert, every "S3 not met" would be an artifact of dead
   plumbing, and the S3 verdict is void. This gate can fail and would be reported as such.

### C3. Held-out-drive coverage (S3 real-data check)
- **Conventions reused** from `netcg_method_selection/code/heldout_drive.py` (per-drive net-CG force via
  `QOIModel.spectrum_drive`, which includes the drive-point modal participation φ_drive,i; measured-mode
  reconstruction on the held-out drive = the answer key the band must envelope).
- **DEV DRIVES ONLY:** {`m_xpos_990x`, `m_zpos_990z`, `m_ypos_990y`, `m_zpos_900z`}. **`m_xy_990xy` is NOT
  read** (VAULT RULE). Any per-mode amplitude least-squares here is **answer-key construction only, never a
  selection score** — annotated `CHECKER-OK(non-selection)` in code and grep-gated by `check.py`.
