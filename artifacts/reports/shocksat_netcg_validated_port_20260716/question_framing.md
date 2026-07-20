# question_framing — validated net-CG QOI port (card B, 2026-07-16)

Written BEFORE any science (D1). The N0/N1/S3/S4 rules below are quoted **verbatim from the runner card**
and are pre-registered: they are not editable after results exist (`check.py` is SHA-locked).

## The engineering decision being supported
Whether the ShockSat tray net-CG force band we DELIVER to the customer should change — specifically, whether
any full-spectrum-study finalist model (arm B / D / R) lets us **sharpen** the delivered shear bands, and
whether the extended-band (200–1000 Hz) measured-mode information lets us **sharpen** the delivered normal-Z
band — without losing coverage of plausible truth. Sharper band = less conservative qualification force =
real mass/cost. The incumbent deliverable is the netcg thread's statFEM F(k) twin (1.51× / 2.30× / 2.53× the
FEM+6dB envelope). **The prior state of this question is CANNOT-VERIFY** (review C5, accepted): the study's
reimplementation could not reproduce the reference, so it could neither improve nor degrade it.

## Objective function / success metric
Band **width ratio vs the FEM+6dB incumbent envelope** (`sharpness_band_grms_ratio_vs_fem6db`, contract in
`quantity_contracts.md`), subject to a **coverage** floor against the epistemic plausible-truth ensemble.
Lower width at adequate coverage = better. Coverage without sharpness is the incumbent; sharpness without
coverage is overconfidence and is disqualifying.

## Pre-registered rules (VERBATIM from the card)

> **Gate N0 (§2, HARD, first):** Reproduce the delivered twin's band widths **1.51 / 2.30 / 2.53 (±0.05
> each)** by driving the ORIGINAL `netcg_qoi.py` + its reduced model + the L5 θ posterior exactly as the
> netcg run did. **PASS →** proceed to §3. **FAIL →** diagnose, write `BLOCKED.md` with the exact divergence
> point and numbers, mark S3/S4 permanently CANNOT-VERIFY-pending-human, and finish with the checker. Do NOT
> "fix" constants until the reference matches — that is calibration-shopping.

> **Bridge gate N1 (§3.1):** evaluate the netcg machinery's band for the INHERITED model at the full-spectrum
> study's θ_MAP (its `out/theta_map_wide.json`) instead of the L5 posterior median — quantify how much of any
> width change is the θ point vs the model. Report; no threshold (diagnostic).

> **Tier update (H4/S4) (§3.2):** apply the pre-registered A5b tier rule from the study's
> `assumptions_ledger.md` (matched extended-band cluster modes: SD_F 0.06→0.01; SD_A = cross-drive amplitude
> scatter from the study's `out/cluster_amp_scatter.json`, floored at 0.35) INSIDE the netcg machinery.
> Report normal-Z width vs 2.53× and coverage vs the netcg plausible-truth ensemble. **S4 rule
> (pre-registered): ≤1.90× AND coverage ≥0.95.**

> **S3 (shear) (§3.3):** evaluate the repair-corrected finalists. **S3 rule: narrower than 1.51/2.30 while
> coverage ≥0.95.** Held-out-drive coverage via `heldout_drive.py` conventions, DEV DRIVES ONLY.
> Baseline-through-your-mapping must reproduce N0 within ±0.05. Overconfidence audit: hide the top-3 measured
> QOI-driving modes → every band must widen (>1).

> **VAULT RULE (§3.4):** the +XY drive is NOT read. Its QOI answer key stays unbuilt. Dev drives only.

Resolution of the reference numbers (D0): the card's 1.51 / 2.30 / 2.53 are the netcg scorecard's delivered
`statfem_Fk` values **1.508 / 2.301 / 2.526**. N0 is scored against those with tolerance ±0.05.

## What the optimization / agent search is allowed to choose
**Almost nothing, deliberately.** There is no optimizer, no search and no sampler in this card. The agent
(me) chooses only: (i) the finalist→netcg mapping *form* (card delegates this explicitly; chosen in D2 and
validated); (ii) which finalists have valid enriched bases (D2, with written reasons); (iii) presentation.
All thresholds (±0.05, ≤1.90×, ≥0.95, widen >1), all tier constants (SD_F 0.06→0.01, SD_A floor 0.35), the
grid (FGRID 45–260 Hz), damping (ZETA=1%) and the width/coverage definitions are INHERITED and frozen —
either from the card, from netcg `netcg_qoi.py`, or from the study's A5b ledger entry. Nothing here is tuned.

## What remains human judgment
- Whether to actually change the delivered twin on the strength of these numbers (this card only makes S3/S4
  *assessable*; it does not ship a new deliverable).
- Whether the A5b tier rule is the right physics for a 1-Z-sensor plate (it is pre-registered, not proven).
- Whether an S3/S4 verdict earned through the relative-perturbation mapping (D2) is strong enough to act on,
  given the mapping's stated limitations (no mode reordering/splitting; unpaired modes inert).
- Whether to spend a run on the +XY vault answer key (NOT touched here).
- If N0 had failed: whether to fund a re-derivation of the netcg calibration.

## What would make this the WRONG question
- **If the band width ratio is the wrong objective.** It is normalized by the FEM+6dB incumbent, so it is a
  *relative* conservatism measure. If the incumbent envelope itself is wrong, every ratio here is wrong.
- **If coverage against a SYNTHETIC epistemic truth ensemble is the wrong answer key.** The plausible-truth
  ensemble is built from the SAME model with tier perturbations — it can only test self-consistency of the
  uncertainty representation, not correctness against reality. The held-out-DRIVE check (real data, dev
  drives) is the only real-data coverage evidence, and it exists for shear only (no normal-Z answer key).
- **If the tray net-CG force is not the QOI the customer qualifies to.** Contract in `quantity_contracts.md`.
- **If mode-shape error (not frequency/amplitude error) dominates.** The delivered normal-Z band is driven by
  UNMEASURED drumhead modes with 1 Z sensor; the mapping in D2 transports frequency+amplitude only. If the
  finalists' real effect is shape reordering, this card measures the wrong perturbation and would understate
  their impact — I would see this as δf/a ≈ 1 with the band barely moving.
- **If S3/S4 are the wrong success criteria.** They ask "can we sharpen?" A defensible answer is "no, and the
  delivered twin stands" — that is a pre-registered, honest outcome, not a failure of the run.
