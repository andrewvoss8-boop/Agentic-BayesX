# Decisions Log — ShockSat FRF-Domain Damping Updating (20260710)

Append-only. Every non-obvious resolution is written here BEFORE acting (autonomy rule, card §11).

**D0 (re-grounding, 2026-07-10).** GOAL: answer one falsifiable question — can an FRF-domain agentic loop with
a DAMPING action space (band ζ / Rayleigh / joint η) + FDAC-aligned scoring beat the modal-only baseline, the
prior shape-only result, and an equal-budget random comparator on held-out per-sensor FRF amplitude, confirmed
on the vault, AND is any gain attributable to damping (S4)? LAST DECISION: Andrew dispatched the card
("run this prompt after grounding, use best judgement"); lead executes as autonomous runner. NEXT ACTION:
write gate files + SHA-locked checker before science, then run the compute-light validation gates.
OPEN AMBIGUITIES: (a) whether band-fit ζ is identifiable at 2 Hz resolution (resolved empirically by Gate D2);
(b) how much residual lives in the sensor-unobservable subspace (resolved by Gate O). Both are first-class
reported results, not blockers.

**D1 (data protocol — carried verbatim from the completed true-remodel run, Andrew's D1/D4 there).**
DEV = leave-one-drive-out over the 4 loop drives {m_xpos_990x (+X), m_zpos_990z (+Z990), m_ypos_990y (+Y),
m_zpos_900z (+Z@900)}. VAULT = m_xy_990xy (+XY / Test04 cache), excluded from ALL dev queries from run start,
graded ONCE after finalists are SHA-frozen. Honest label carried: the vault is "held out from THIS run's
selection", NOT never-seen-by-any-run; +XY is also the "easy" location (completed run's uniform +0.22–0.27
dev-vs-vault gap) — report the gap; a high vault number is not by itself a win. Rationale: identical discipline
to the completed run enables a clean A/B on the same infrastructure (the card's stated design intent).

**D2 (reuse the completed FE layer read-only; do not re-derive).** femlib.py + fe_core.py + the stored reduced
blocks are the forward-model substrate; the new damping model EXTENDS `predict_logH`, it does not replace the
element pipeline. All 57 reused sources hashed in REUSED_code.sha256 before science. The completed run's two
hard-won guards are carried as NON-NEGOTIABLE: (i) every decision-relevant score is EXACT-BASIS (spot-check
≤0.3%, enrich if it fails); (ii) every θ_MAP / damping-MAP is DETERMINISTIC MULTI-START.

**D3 (damping enters the forward model at the modal resolvent).** Reused `predict_logH` uses a single fixed
viscous ζ=0.01 in `D = ωᵢ² − ω² + 2j·ζ·ωᵢ·ω`. The three damping families map to per-mode effective damping:
(1) band modal ζ: ζ_i = ζ(band containing f_i); (2) Rayleigh: ζ_i = α/(2ωᵢ) + βωᵢ/2; (3) structural per-joint
loss factor η_g: composite per-mode loss factor η_i = Σ_g η_g·SE_{i,g}, SE_{i,g} = (Qᵢᵀ A[g] Qᵢ)/(Qᵢᵀ K(θ) Qᵢ)
= modal strain-energy fraction stored in group g (the package already carries A[g] and A_fix), with the
structural resolvent D = ωᵢ²(1 + i·η_i) − ω². This is low-dim, physically located, and smooth/differentiable
for NUTS. Combined viscous+structural allowed for a candidate but capped at ≤10 damping params total.

**D4 (damping fit on TRAIN, frozen for DEV).** All damping parameters are fit on the fold's TRAIN drives + the
.ash survey and FROZEN when predicting the left-out dev drive — never a per-channel or per-mode free knob (the
LSQ trap, extended to damping). The selection score carries ONE global gain per fold plus the low-dim physical
damping vector; markers `# NO-PER-MODE-LSQ` and `# LOW-DIM-PHYSICAL-DAMPING-ONLY` present; damping dim ≤10.

**D5 (S1 threshold NOT tightened — kept at +0.05 for continuity).** The card allows a data-justified tighter
threshold ONLY if pre-registered in this file BEFORE any dev score, with fold-SE evidence. I have no fold-SE
evidence yet, so I keep +0.05 absolute AND ≥2× fold-to-fold SE (the completed run's noise-floor rule). If the
FDAC alignment demonstrably lowers the fold noise floor, any re-registration will be logged here with the
measured fold-SE and dated BEFORE the first dev score — never after.

**D6 (FDAC / band selection is TRAIN-side only).** The per-channel frequency-alignment warp and the FDAC-
selected updating bands are computed from TRAIN drives (+ .ash) only, saved as a train-side field, and NEVER
recomputed on the dev/vault drive. The loop's diagnosis code reads no dev cache outside the score function
(checker greps for this).

**D7 (measured modal damping = PERCENT; 2 Hz caches under-resolve damping — a first-class finding).** The
survey `damp` array (measured_modes.npz) has median 0.317 and max 1.05; read as critical-damping RATIO these
are impossible (32% and >100% for sharp measured resonances). Read as PERCENT they are physical: ζ = damp/100
∈ [0.06%, 1.05%], median 0.32%. DECISION: interpret `damp` as percent critical damping; ζ prior center = 0.30%
(≈ survey median), hard physical gate bound [0.2%, 5%] (a few very-light modes measure below 0.2% — the gate
constrains the INFERRED band ζ, not the survey). NOTE: the completed run's fixed ζ=1% is ~3× the survey median
— a documented mismatch that A0d (damping baseline) can correct. RESOLUTION FINDING (feeds Gate D2 + the
Discretization gate): at 2 Hz line spacing the half-power bandwidths 2ζf = 0.20–2.49 Hz (median 1.05 Hz) span
only 0.10–1.25 frequency lines (median 0.53); ALL 33 in-band modes have HP-bandwidth < 3 Hz and 28/33 < 2 Hz.
=> per-mode / narrow-band ζ is NOT reliably identifiable from these caches (peaks under-sampled; true peak
height 1/(2ζ) not captured on the grid); only a band-AVERAGE ζ may be weakly constrained by the off-resonance
magnitude envelope. Gate D2 will quantify this on synthetic FRFs; modes/bands that fail the identifiability
test are marked NOT-inferred and reported. This is a genuine data-resolution wall parallel to Gate O and it
sharpens the honest prior: the damping lever may be only weakly usable from THIS data — itself a reportable
outcome, not a failure.

**D8 (damping band structure).** 4 geometric bands over 45–260 Hz with edges [45, 69.8, 108.2, 167.7, 260] Hz
(≈ equal log-width; mode counts 1/4/8/20). Band ζ = piecewise-constant, one value per band (≤4 params). This
is the low-dim physical parameterization; per-mode ζ is NEVER free.

**D9 (validation-gate results — checker-verified 2026-07-10, all GREEN).**
- Gate D1 (damping physics, out/gate_D1.json): viscous 1/(2ζ) err 0.045%, structural 1/η err 0.18%, Rayleigh
  ζ_i err 0.0%, all ≤2% → the damping forward model is physically correct (run NOT void).
- Gate F (metrics, out/gate_F.json): all 4 sub-tests pass. KEY real-mechanism demo: a 5% frequency shift drops
  raw FRAC to 0.69, FDAC recovers the shift (ρ_est 0.9526 vs true 0.9524), alignment restores FRAC to 0.997 =
  **+0.31 alignment gain**. This is direct evidence a large part of the completed run's low raw P1 is frequency
  MISALIGNMENT, not shape error (the card's hypothesis 2).
- Gate D2 (identifiability@2Hz, out/gate_D2.json): at 2 Hz + realistic noise σ_log=0.06, per-mode ζ recovery
  error in the survey's light-damping regime = 27% (median) vs 14% best-resolved → per-mode/narrow-band ζ NOT
  identifiable; only a band-AVERAGE ζ is weakly constrained. Corrected my own too-easy first draft (noiseless
  single mode recovers ζ regardless of resolution — the checker caught it). Bounds the damping lever.
- Gate O (observability, out/gate_O.json): at the delivered 132-DOF sensor set, self-MAC max off-diag = 0.997
  (≥1 analytical mode pair indistinguishable at the sensors), Fisher rank 36/40, but only **7% of measured
  in-band shape content is unobservable** (93% representable/reachable) with 1 shape hole. Honest reading: the
  A0 residual is NOT dominated by an unobservable subspace (reachable headroom exists) — so the wall is shape
  fidelity + amplitude, not gross unobservability; the sensor set does alias some mode pairs. Contextualizes
  every S1/S4 outcome.
- NET honest prior after gates: FDAC alignment (P1′) will likely raise the reported number a lot vs raw P3;
  the SHAPE lever stays null; the DAMPING lever is only weakly usable from THIS 2 Hz data (band-average, not
  per-mode). The most probable overall outcome is a partial-improvement-from-alignment with damping/shape
  contributing little beyond it — to be graded honestly by S1–S4 on real data.

**D11 (A0 baseline BUILT + scored on real data; a warp bug caught + fixed; first real-data finding).**
A0 package built via reused femlib (full-order eigensolve 270.8 s, out/eigensolve_log.jsonl). θ_MAP (multi-start):
joints 0.52 (softened), cross_beam 1.52, plates 1.30, top_box 0.83, angle_brackets 1.17, others ~1.
- PIPELINE CROSS-VALIDATED: A0 raw P3 = 0.238 reproduces the completed run's A0 raw P1 (0.234–0.238) → my
  FRF scoring path matches the established one.
- WARP BUG CAUGHT (integrity): my first FDAC global-scale estimator gave nonphysical ρ = 1.24–1.63 (24–63%
  "shifts") because the unconstrained ridge collapsed onto the dominant resonance, and one fold's band
  selection collapsed to 4 lines (inflating P1p to 0.73 on 4 points). P1′ was NOT trustworthy. FIXED:
  physical shift window |fe/fa−1|≤6%, weighted-MEDIAN ρ (resists dominant-peak pull), min-band fallback to
  full band. Gate F still passes (+0.31 on a true 5% shift). Post-fix ρ = 0.98–0.99 (physical ~1% residual),
  folds stable [0.37,0.52,0.16,−0.14].
- REAL-DATA FINDING (trustworthy): FDAC global-scale alignment does NOT improve A0's held-out FRF correlation
  (P1′ 0.2255 vs P3 0.2383, alignment_gain −0.013, within fold noise). Because θ_MAP already aligns the modal
  frequencies to the survey, the predicted FRF peaks are already frequency-aligned → a global warp has ~nothing
  to correct. This PARTIALLY FALSIFIES the card's hypothesis 2 (that the completed run's low P1 is dominated by
  frequency misalignment): for a global-scale warp on the θ_MAP-aligned model it is NOT. A per-band/per-channel
  warp remains to be tested in the loop before hypothesis 2 is fully ruled out.
- AMPLITUDE: A0 |FRSF−1| ≈ 0.73 (FRSF≈1.7, measured/predicted amplitude ~1.7× off) — a real amplitude gap
  damping could address, but the A0d-lite preview (ζ 1%→0.32%) made P2′ WORSE, consistent with 2 Hz peak
  aliasing making the data look MORE damped (D2/D7). Naive damping-down is wrong; any amplitude fix must
  respect the physical-damping gate. Fitted A0d (next phase) will test this properly.

**D12 (RUN COMPLETE — checker OVERALL YELLOW, 19G/2Y/0R; pre-registered claim FALSIFIED on S1/S2/S3/S4).**
Exact-basis dev P1' (FDAC-aligned FRAC): A0 0.197, A0d(damping) 0.193, shape c06 0.228, shape a04 0.234
(dev winner), shape+damping 0.226, random rnd003 0.239. VERDICTS: S1 FAIL (winner margin +0.037 < +0.05 and
<< 2xfold-SE 0.262); S2 FAIL (random 0.239 > agent 0.234); S3 FAIL (net-CG shear coverage 0.70 < 0.95, the
+Z@900 gap class; lmo + physical-damping OK); S4 FAIL (damping_share -0.105 => "improvement is shape/theta;
DAMPING lever unproven"; A0d BELOW A0). MECHANISM: (a) damping unidentifiable at 2 Hz (D2) => A0d fit rails
zeta to 1.5-2.5% (MAP) / 5% gate ceiling (NUTS, all finalists), chasing peak-sampling aliasing, does NOT
generalize; (b) FDAC global alignment gain ~-0.01 (theta_MAP already aligns) => completed run's null NOT a
misalignment artifact; (c) Gate O: 93% shape reachable (not gross-unobservable), sensor aliasing self-MAC 0.997.
VAULT (once, +XY): uniform +0.22..+0.30 dev->vault location effect for ALL finalists (not a generalization win;
S1 dev leg fails regardless). NUTS: a04 (rhat 1.002/ess 792) + c06 (1.005/423) CONVERGED; A0 rhat 24.8/ess 2
NON-converged = theta MULTIMODALITY (D19 basin lottery; reproduced under Uniform-zeta => not a param artifact;
reported as under-identification per AGENTS, YELLOW, intervals labeled not-trustworthy). CROSS-VALIDATION: A0_enr
raw P3 0.2152 == completed true-remodel run's exact-basis A0. Budgets agent 21/60, random 40/60. Runtime active
= elapsed 8722.7 s (~2.4 h; heavy legs detached). Deliverables: packet.md, findings.md, verdicts.json, 5 Tufte
figures + fig_qa, vault_scores, ablation, honesty_*, nuts_*, qoi_*, runtime.json, checker_report.json. RECO to
Andrew: keep inherited twin; to use damping for FRF-amplitude correlation, BUY finer frequency resolution
(re-distill NASA raw time histories) — not more modeling. The completed true-remodel run STANDS unchanged; this
successor answers the damping question and closes it with a resolution-limited mechanism. MPL = natural follow-on.

**D10 (execution phasing / honest scope).** This session completed, checker-verified: all pre-registration
gate files, REUSED_code.sha256 (57 sources), SHA-locked immutable checker, and the 4 new validation gates
(D1/F/D2/O GREEN) + the damping forward model (femdamp.py) + FDAC/FRAC/FRSF metrics (metrics.py). REMAINING
(next phase, heavy compute, launch detached + resumable per compute protocol): mech gates V1–V5 (reuse
mech_gates.py), A0/A0d package builds (full-order eigensolve), the FDAC train-side field + band selection, the
closed loop (≥3 rounds, ≤60 dev queries) + random track, finalists + NUTS(θ+damping) + Q/H + S4 ablation,
vault-once, packet/figures. NOT claimed complete; overall checker status remains RED "science not run" until
those legs produce artifacts. No fabrication; a falsification remains a valid outcome.
