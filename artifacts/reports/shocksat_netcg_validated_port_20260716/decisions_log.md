# decisions_log — validated net-CG QOI port (runner card B, 2026-07-16)

Workspace: `artifacts/reports/shocksat_netcg_validated_port_20260716/`. Repo commit at start: `9cad98c`.
Runner: Claude (autonomous, per paste-and-run card B). Filesystem = source of truth.

---

## D0 — Re-grounding complete; goal / last decision / next action / open ambiguities (2026-07-16)

**Re-grounded from (read before acting):** `AGENTS.md` (167 lines, full gate set), `docs/compute_protocol.md`;
study `shocksat_full_spectrum_frf_20260714/findings.md` POST-REVIEW box (D17) + `decisions_log.md` D14/D15 +
STATE SNAPSHOT; review `shocksat_fullspec_review_gpt56_20260716/review.md` C5 (+C6/C8 context); netcg thread
`shocksat_netcg_method_selection_20260701/` (`packet.md`, `run_all.sh`, `code/netcg_qoi.py`, `code/bakeoff.py`,
`out/bakeoff_scorecard.json`); study `code/netcg_wide.py`, `out/netcg_results.json`,
`out/cluster_amp_scatter.json`, `out/theta_map_wide.json`, `assumptions_ledger.md` A5b; repair
`out/verdicts.json`.

- **GOAL:** make S3/S4 assessable by REUSING the validated netcg machinery (not reimplementing it), or close
  them as BLOCKED-with-diagnosis. Post-review item 4.
- **LAST DECISION (inherited, D17 + review C5, accepted):** S3/S4 are **CANNOT-VERIFY**, not falsified — the
  study's wide-package net-CG reimplementation failed to reproduce the delivered twin's calibrated bands.
- **NEXT ACTION:** pre-registration (§4) → SHA-locked checker → Gate N0 reference reproduction.
- **OPEN AMBIGUITIES:** (1) exact delivered reference values — resolved below; (2) which finalists count for
  S3 — resolved below; (3) mapping choice for S3 — resolved in D2.

**Reference values pinned (from netcg `out/bakeoff_scorecard.json`, read-only).** The card's 1.51 / 2.30 /
2.53 are the `conservative_assumption_light_winner` = `statfem_Fk` `sharpness_band_grms_ratio_vs_fem6db`:
shear_X **1.508**, shear_Y **2.301**, normal_Z **2.526**. Note normal_Z's *sharpest* winner is `hier_pooled`
at 2.005, but it was NOT delivered (pooling caveat); the delivered/conservative number is 2.526 → the card's
"2.53" is the conservative statFEM F(k) number. N0 targets 1.508 / 2.301 / 2.526, tolerance ±0.05.

**Feasibility smoke-test (pre-science, logged for honesty):** imported `netcg_qoi.QOIModel()` read-only —
loads in ~2.5 s, nM=40 in-band modes (54.6–258.9 Hz), 20 measured; `out/theta_post_L5.npz` present with
theta_post (4000, 9). The netcg machinery is alive and cheap to drive → N0 is feasible without a sampler.

**Sampler:** NO new sampler. The L5 θ posterior is **REUSED** from the netcg thread's cached
`out/theta_post_L5.npz` (NUTS, its own all-variable convergence gate). Every band I report inherits that
posterior and is labeled **reused draws**, per card §5.

**Vault:** the +XY drive (`m_xy_990xy`) is NOT read. DEV drives only. Checker greps for it.

---

## D1 — Pre-registered gates written BEFORE any science (2026-07-16)

`priority_deliverables.md`, `question_framing.md` (N0/N1/S3/S4 rules verbatim from the card),
`quantity_contracts.md` written first; then `check.py`, run on the empty workspace to prove RED, then
SHA-locked into `CHECKER.sha256` and never edited. Order enforced so no gate can be tuned to a result.

---

## D2 — S3 finalist→netcg mapping: RELATIVE per-mode perturbation (card §3.3 option b) (2026-07-16)

**Choice: option (b)** — per-mode frequency/amplitude perturbations of the netcg reduced model, matched to
each finalist's paired modes — NOT option (a) (re-plumbing wide tray/drive rows into the netcg reduced model).

**Why:** the netcg reduced model (`realfrf.load_reduced()`, psd_envelope_twin thread) and the study's wide
package (`full_eig` θ=1 basis of the inherited FEM, `wide_package.py`) are different reductions with
different DOF orderings, sensor/drive row conventions and tray selectors. Re-plumbing (a) would be a NEW
implementation of exactly the kind that already failed once (review C5) — it re-introduces the reimplementation
risk this card exists to eliminate. Option (b) keeps 100% of the band machinery (`NC.Method`, `NC.QOIModel`,
octave smoothing, coverage, the `bakeoff.band_ratio` width convention) byte-identical and injects the
finalist ONLY through the two hooks `netcg_qoi` already exposes: `amp` and `fscale`.

**Definition (contract in `quantity_contracts.md`):** for finalist X vs the wide BASELINE A0_wide (=A1), both
evaluated on their enriched exact bases at θ_MAP_wide:
  δf_i = f_X,i / f_A0,i  and  a_i = |g_X,i| / |g_A0,i|   (g = tray-region net-CG participation, per QOI axis)
for in-band (45–260 Hz) modes paired A0↔X by Hungarian match on |Δln f|; then netcg mode j inherits (δf, a)
from the A0_wide mode nearest in frequency (≤2% mismatch, else δf=1, a=1 = "finalist says nothing here").

**Honest limitation, stated up front:** this mapping is RELATIVE, so the baseline maps to δf≡1, a≡1 and
reproduces N0 **exactly, by construction** — the card's "baseline-through-mapping within ±0.05" check is
therefore an identity/plumbing check (it proves the perturbation hooks are wired correctly and nothing else
drifted), NOT independent evidence that the mapping transports a finalist faithfully. I add a second,
non-trivial check to compensate: a **non-identity sanity check** — at least one finalist must actually move
the band (δf/a not all ≈1), otherwise the mapping is silently inert and S3 is meaningless. Both are checker
gates. What this mapping CANNOT capture: mode-shape changes that reorder/split modes, and any finalist mode
with no baseline partner within 2%.

**Finalists:** the enriched exact bases that exist are `A0_wide__enr` (=A1 baseline), `B__enr`, `D__enr`,
`R__enr`. Arm **C is excluded**: per review C6 (accepted, RED) its exact aggregate is leakage-invalid, and per
study D14 it shares A0_wide's basis (it is a shape-MAP arm, not a model edit → δf≡1, a≡1 → it maps to the
baseline identically and carries no model-form information). So S3 finalists = **B, D, R** vs baseline A1.
R (random control) is retained deliberately: per the repair, S2 is not met (D−R = −0.0017 ± 0.0094), i.e. the
agent ties random, so R is as legitimate a finalist as D.

---

## D3 — Divergence hypotheses logged BEFORE running N0 (2026-07-16)

Pre-registering my diagnosis so it cannot be retrofitted to whatever N0 prints. From reading
`netcg_wide.py` against `bakeoff.py`/`netcg_qoi.py`, the study's non-reproduction is predicted to be a
**quantity-contract divergence, not a calibration difference** (the study's own CAVEAT blames "a
marginal-calibration difference"). Three concrete suspects, in expected order of impact:

1. **WIDTH CONVENTION (predicted dominant).** netcg `bakeoff.band_ratio` = `grms(hi − lo) / grms(fem6_hi −
   fem6_lo)` — a band WIDTH normalized by the FEM+6dB band width. Study `netcg_wide.band_width_ratio` =
   `grms(smooth(hi)) / grms(smooth(lo))` — an upper/lower ENVELOPE RATIO that never references FEM+6dB at
   all. These are different quantities; they cannot agree, at any calibration.
2. **statFEM F(k) marginal.** netcg: `marg = 0.25 + (SD_A_U − 0.25) * ufrac`, ufrac = UNMEASURED-mode energy
   fraction. Study: `marg = max(0.25, wfrac)`, wfrac = contribution-weighted MEAN SD_A over all modes.
   Different functional form → different width.
3. **θ ensemble.** netcg `statfem_fk` loops 60 θ draws × n_disc=40 = 2400 spectra (θ uncertainty IN the
   band). Study `fk_band` uses a SINGLE θ (θ_MAP_wide) × 400 draws → θ uncertainty absent from the band.

If N0 passes, I will diff these three quantitatively (N0-diagnostic) rather than assert. If N0 fails, §2's
BLOCKED path applies and I do NOT touch constants.

---

## D3b — GATE N0 PASSED; D3 hypothesis 1 CONFIRMED quantitatively (2026-07-16)

`out/n0_reference.json`: shear_X **1.508**, shear_Y **2.301**, normal_Z **2.526** vs targets 1.508 / 2.301 /
2.526 → **max |err| = 0.0000** (tol ±0.05). Exact reproduction. The reused L5 posterior reports its inherited
convergence: max R-hat 1.0013, min ESS 2646, 0 divergences, 4000 draws. **Gate N0 = PASS → §3 unlocked.**
S3/S4 are no longer CANNOT-VERIFY for want of a reference.

**D3 suspect 1 CONFIRMED, and it is decisive.** Computed on the SAME `lo`/`hi` arrays of the SAME delivered
statFEM F(k) band: netcg's `bakeoff.band_ratio` convention = **1.508**; the study's
`netcg_wide.band_width_ratio` convention = **21.660**. These are not the same quantity — the study's is an
upper/lower ENVELOPE ratio that never references the FEM+6dB denominator. The study's own CAVEAT attributes
its non-reproduction to "a marginal-calibration difference in the reimplemented statFEM F(k)". That
attribution is **wrong**: it is primarily a **quantity-contract divergence**. No calibration of any constant
could have reconciled 1.51 with an envelope ratio.

---

## D4 — VALIDITY DEFECT FOUND IN MY OWN PRE-REGISTERED MAPPING (C1 amplitude channel) (2026-07-16)

**Found while diagnosing an implausible first S3 result** (arm B: shear_Y 7.95× vs delivered 2.301×,
synthetic-truth coverage 0.028). I am NOT reporting that number as a finding without establishing whether it
is physics or plumbing. Diagnosis:

- Per-mode amplitude ratios from contract C1 (`a_i = |g_X,i| / |g_A0,i|`) are **not physical**: arm B gives
  **median |ln a| = 2.31** (a 10× median change in per-mode tray participation) and **max |ln a| = 10.40**
  (a ~30,000× change) — from a modest property/stiffness edit. Arms D/R: median 1.02 / 0.86, max 9.53 / 15.42.
- **Cause (structural dynamics, not a coding bug): near-degenerate modes.** 18 of 44 adjacent in-band A0
  mode pairs sit within **1%** in frequency (26 within 2%) — e.g. the 140.9/141.1/141.6/141.7/141.7 Hz
  five-mode cluster, plus 73.1/73.7, 237.9/238.3/239.1, 247.1/247.5, 251.3/251.9. Within a near-degenerate
  subspace the individual eigenvectors are arbitrary up to rotation: **only the subspace (and the summed
  spectral response) is basis-invariant; per-mode participation is not.** A0 and each finalist are *different
  reduced bases* (`enrich_wide.py` re-solves K(θ_MAP) per finalist), so their per-mode g's are rotated
  differently inside each cluster.
- **Aggravator:** per-mode |g| spans a **7.0e4 dynamic range** (min 9.8e-02, max 6.8e+03). Dividing by a
  near-zero |g| detonates the ratio.
- The **frequency channel δf is comparatively sound**: median |δf−1| = 0.005/0.001/0.000 for B/D/R, max
  Hungarian pairing cost |ln(f_X/f_A0)| = 0.165/0.081/0.117. Frequencies are physical and pair well.

**Decision (chosen BEFORE looking at what each variant does to the S3 verdict — verified: I ran the
diagnosis on δf/a distributions only, not on band widths):** do not silently patch C1, and do not quietly
drop it. Report **three mapping variants** and judge S3 on their AGREEMENT (AGENTS Sensitivity Gate — "report
when conclusions are fragile"):
1. **`full`** — the pre-registered C1 (δf + per-mode a). Reported *as registered*, and labelled
   **amplitude channel INVALID** by the diagnosis above.
2. **`freq_only`** — δf only (a ≡ 1). A strict subset of C1; the sound channel.
3. **`cluster_amp`** — δf + a aggregated over near-degenerate clusters (1% frequency gaps):
   `a_cluster = sqrt(Σ_cluster |g_X|² / Σ_cluster |g_A0|²)`, assigned to every member. Sums over a degenerate
   cluster ARE basis-invariant, so this is the physically defensible amplitude channel.

**Verdict rule (pre-registered here, before the variants are scored):** if all three variants agree on the
pre-registered S3 rule (narrower than 1.508/2.301 with coverage ≥0.95), S3 is reported with that verdict and
the mapping caveat. **If they disagree, S3 = CANNOT-VERIFY-through-this-mapping** and I say so. The card's
required baseline-through-mapping check (±0.05 of N0) is satisfied by all three (all are identities at the
baseline).

**Honest status of C1:** my pre-registration was defective. Catching it by diagnosis rather than shipping
arm B's 7.95× as a "finding" is the point of the check. This is written down before the fix, per CLAUDE.md.

---

## D5 — S3 coverage measure: held-out-drive (real data), per the card (2026-07-16)

The card's S3 text specifies the coverage source: "**Held-out-drive coverage via `heldout_drive.py`
conventions, DEV DRIVES ONLY.** S3 rule: narrower than 1.51/2.30 while coverage ≥0.95." So the S3 coverage
gate is scored on the **real-data held-out-drive** answer key, not on the synthetic epistemic truth ensemble
(the synthetic ensemble is the card's stated coverage source for **S4** only: "coverage vs the netcg
plausible-truth ensemble"). Both are reported for every finalist regardless, because they answer different
questions — and note a wider band trivially scores better on either, which is exactly why the rule is a
JOINT narrower-AND-covering test.

Caveat recorded: the synthetic-truth coverage of a *perturbed* model is scored against an ensemble built at
the *unperturbed* netcg baseline, so a finalist that genuinely moves the modes will score low there by
construction. That number diagnoses "how far did the finalist move", not "is the finalist wrong". The
held-out-drive check is the real-data one, and it self-calibrates a single global gain per drive
(netcg convention).

## D6 — Arm packages carry different parameter counts (2026-07-16)
`A0_wide__enr`/`B__enr` have 9 free groups; `D__enr` has 10 (adds `brackets085`), `R__enr` has 10 (adds
`rthick2`) — genuine model edits. `modes(ones)` must therefore use each package's OWN `len(free_names)`
(the enriched bases fold θ_MAP in, so `ones` = that package's θ_MAP). Fixed; no scientific content.

---

## D7 — CHECKER LIMITATION FOUND AT REPORTING TIME: OVERALL GREEN ≠ "S3/S4 met" (2026-07-16)

The final checker returns **OVERALL GREEN (10 GREEN / 0 YELLOW / 0 RED)**. My draft packet/findings had
*predicted* "OVERALL YELLOW (8G/2Y)" on the assumption that the S3/S4 science verdicts would flow into the
checker's overall light. **They do not.** I corrected the reports to copy the checker's ACTUAL output, per
the rule that status is copied from the checker and never written from expectation.

**The limitation, stated plainly:** my pre-registered `check.py` gates **process integrity** (N0 reproduced,
statistics finite, mapping validated + non-inert, no selection-path LSQ, no vault reads, figures QA'd,
runtime sane, checker unmodified, deliverables + reused-source SHAs, no new sampler). It has **no gate that
propagates the S3/S4 verdicts into OVERALL**. So a reader glancing at "OVERALL GREEN" could mistake it for
"S3/S4 were met". **They were not: S3 = CANNOT-VERIFY (YELLOW), S4 = NOT MET (YELLOW)**, both recorded in
`out/verdicts_S3S4.json`.

This is the same *class* of defect the review caught in the study (C8: gate G09 validated key-presence, not
finiteness, so NaN headline numbers passed). Mine is less harmful — it under-specifies rather than certifies
something false, and both YELLOW verdicts are pre-registered outcomes that a checker arguably should NOT
call RED — but the ambiguity is real.

**Action taken:** I did NOT edit the SHA-locked checker (forbidden mid-trial, and editing it to change a
status would be exactly the anti-pattern). Instead every report states the split explicitly:
**"Checker OVERALL GREEN = all ten INTEGRITY gates pass; the SCIENCE verdicts are S3 YELLOW / S4 YELLOW."**

**Recommendation for the next card's checker (durable-rule candidate — needs human approval, NOT applied
here):** any checker that pre-registers success criteria should carry a gate that reads its own
`verdicts.json` and reflects each criterion's status into OVERALL, so the headline light cannot read greener
than the science. Logged for `notes/lessons-learned.md`.
