# findings — validated net-CG QOI port (runner card B, 2026-07-16)

Every status below is copied from this workspace's immutable checker (`checker_report.json`, checker SHA
`e235e9fc…`, proven RED on the empty workspace before any science, never edited).

> ### ⚠ READ THIS BEFORE THE STATUS LIGHT (D7)
> **Checker OVERALL: GREEN (10 GREEN / 0 YELLOW / 0 RED), exit 0 — but that GREEN certifies INTEGRITY, NOT
> that the success criteria were met.** My pre-registered `check.py` gates process integrity only (reference
> reproduced, statistics finite, mapping validated, no vault reads, figures QA'd, checker unmodified, …). It
> has **no gate that propagates the S3/S4 verdicts into OVERALL** — a limitation I found at reporting time
> and did not paper over by editing the locked checker.
> **The SCIENCE verdicts are: S3 = CANNOT-VERIFY (YELLOW). S4 = NOT MET / falsified (YELLOW).**
> Only **N0 is a GREEN result** (the reference reproduced exactly). Do not read "OVERALL GREEN" as "the
> finalists sharpened the twin" — they did not.

Nothing here is stronger than the checker output.

**Prior state (review C5, accepted by the lead in study D17): S3/S4 = CANNOT-VERIFY.** The full-spectrum
study reimplemented the net-CG band machinery on its wide package and could not reproduce the delivered
twin's calibrated widths. This card's job: reuse the validated machinery to make S3/S4 assessable, or prove
why not.

---

## GATE N0 — reference reproduction: **PASS (GREEN)**

Driving the ORIGINAL `netcg_qoi.py` + its reduced model + the reused L5 θ posterior exactly as the netcg run
did (`bakeoff.py` invocation, `statfem_Fk` = the delivered conservative winner):

| QOI axis | delivered target | this run | \|err\| | tol | coverage |
|---|---|---|---|---|---|
| shear_X | 1.508 | **1.508** | **0.0000** | 0.05 | 0.995 |
| shear_Y | 2.301 | **2.301** | **0.0000** | 0.05 | 0.982 |
| normal_Z | 2.526 | **2.526** | **0.0000** | 0.05 | 0.987 |

(The card's "1.51 / 2.30 / 2.53" are these numbers rounded — resolved in D0 from the netcg scorecard.)

**Gate N0 PASSED → §3 unlocked. `BLOCKED.md` was NOT triggered.** The delivered net-CG twin is reproducible
from its own artifacts, and the machinery is validated for arm work. **S3/S4 are assessable.**

### Why the study could not reproduce it — the C5 cause, corrected
The study's own CAVEAT attributes its failure to *"a marginal-calibration difference in the reimplemented
statFEM F(k)"*. **That attribution is wrong.** The dominant cause is a **quantity-contract divergence**,
pre-registered as hypothesis D3-suspect-1 *before* N0 was run:

- netcg `bakeoff.band_ratio` = `grms(hi − lo) / grms(fem6_hi − fem6_lo)` — the band's **width**, normalised
  by the FEM+6 dB incumbent band's width. **This is the delivered quantity.**
- study `netcg_wide.band_width_ratio` = `grms(smooth(hi)) / grms(smooth(lo))` — an upper/lower **envelope
  ratio** that never references FEM+6 dB.

Computed on the **identical `lo`/`hi` arrays of the identical delivered band**: netcg convention = **1.508**,
study convention = **21.660**. These are different quantities. **No calibration of any constant could have
reconciled 1.51 with an envelope ratio.** Two further real divergences were also identified (not the
dominant term): the study's statFEM marginal is `max(0.25, wfrac)` with a mean-SD `wfrac` (netcg:
`0.25 + (SD_A_U−0.25)·ufrac` with an *unmeasured-energy-fraction* ufrac), and the study's band uses a single
θ point so **θ uncertainty is absent from it entirely**.

**Lesson (for `notes/lessons-learned.md`):** a "we can't reproduce the reference" failure was attributed to
calibration and closed as unassessable. It was a contract mismatch, findable in ~3 lines of diff. The
Quantity Contract Gate exists for exactly this; the study reused netcg's *grid and helpers* but silently
redefined its *headline statistic*.

---

## GATE N1 — bridge (θ point vs model): **diagnostic, no threshold (GREEN)**

All cases use the same reused machinery and the same MC budget (60 θ slots × 40 draws), so nothing here is
MC noise. Group-order bridge validated at runtime (`realfrf.GNAMES` == `theta_map_wide` `free_names`, 9
stiffness groups, 1:1).

| | shear_X | shear_Y | normal_Z |
|---|---|---|---|
| **A** L5 posterior (= delivered) | 1.508 | 2.301 | 2.526 |
| **B** L5 median as a θ POINT | 0.740 | 1.189 | 2.180 |
| **C** study θ_MAP_wide as a θ POINT | 1.720 | 0.744 | 1.727 |
| θ **SPREAD** term (A−B) | +0.768 | +1.112 | +0.346 |
| θ **POINT** term (C−B) | **+0.980** | **−0.445** | **−0.453** |
| study's PUBLISHED width | 8.225 | 3.660 | 5.117 |
| **residual NOT explained by θ** | **+6.505** | **+2.916** | **+3.390** |

**Reading:** swapping in the study's θ point moves shear_X by only +0.21 relative to delivered, and moves
shear_Y/normal_Z in the **wrong direction** (narrower, not wider). **≈0% of the study's 6.5 / 2.9 / 3.4-wide
gap is the θ point.** The gap is the reimplementation (convention + marginal form + absent θ spread). A
secondary finding worth noting: the θ **spread** contributes a large share of the delivered band's width
(+0.77 / +1.11 / +0.35), which the study's single-θ band structurally could not contain.

---

## S4 (H4, tier update) — **NOT MET (YELLOW), falsified along the pre-registered path**

**Rule (card §3.2, verbatim):** normal-Z width **≤1.90×** AND coverage **≥0.95**.

Applying the study's pre-registered A5b tier rule INSIDE the netcg machinery (matched extended-band cluster
modes: SD_F 0.06→0.01; SD_A = observed cross-drive amplitude scatter, floored at 0.35):

| axis | delivered | A5b tier-updated | change | coverage | widen-audit (hide top-3) |
|---|---|---|---|---|---|
| shear_X | 1.508 | 1.519 | +0.011 | 0.995 | 1.407 ✓ |
| shear_Y | 2.301 | 2.319 | +0.018 | 0.982 | 1.317 ✓ |
| **normal_Z** | 2.526 | **2.958** | **+0.432** | **0.989** | 1.040 ✓ |

**Verdict: coverage PASSES (0.989 ≥ 0.95); the WIDTH FAILS (2.958 > 1.90). S4 = NOT MET.** The change
+0.432 far exceeds the measured 2σ MC noise floor of 0.091 → the widening is real, not sampling scatter.

**Why — and why this is an honest result, not a bug.** Exactly **one** measured extended-band cluster matches
a FEM mode inside 45–260 Hz: measured **254.3 Hz ↔ FEM 254.9 Hz** (0.2% mismatch). Its **observed**
cross-drive ln-amplitude scatter is **SD_A = 1.393** (4 dev drives, from the study's
`out/cluster_amp_scatter.json`) — **larger than the 0.80** the delivered twin already assumed for an
*unmeasured* mode. **Measuring that mode's amplitude made it MORE uncertain, not less**, so the band widened.

The study's `assumptions_ledger.md` A5b pre-registered this exact outcome on 2026-07-14, before any QOI
computation: *"if the observed cross-drive amplitude scatter is large, SD_A stays large and the normal band
will NOT narrow — that is an honest H4 falsification path, pre-registered here."* **That is what happened.**

**Consequence:** the delivered 2.526× normal-Z twin **stands**, and is if anything *mildly optimistic* for
that mode. The extended-band (200–1000 Hz) data does **not** buy a sharper normal-Z force band. The physical
reason is unchanged and known: the plate has **1 Z sensor**, so the drumhead **shape** stays unmeasured and
the tray-Z participation `g_i` stays shape-uncertain no matter how well the *frequency* is pinned.

**Note on SD_F:** A5b's SD_F 0.06→0.01 is applied and recorded, but does **not** move the statFEM F(k) band —
netcg's statFEM marginal depends on the per-mode **amplitude** tiers (via the unmeasured-energy fraction),
not on SD_F. Stated rather than hidden (`out/verdicts_S3S4.json` → `S4.a5b_rule_applied.note`).

---

## S3 (shear, finalists) — **CANNOT-VERIFY-through-this-mapping (YELLOW)**

**Rule (card §3.3, verbatim):** narrower than 1.508 / 2.301 while **coverage ≥0.95**, coverage from the
**held-out DEV drives** (D5). Finalists = the study's enriched exact bases **B / D / R**. (**Arm C excluded**:
review C6 — its exact aggregate is leakage-invalid — and per study D14 it shares A0's basis, so it maps to
the baseline identically and carries no model-form signal. **R, the random control, is retained**: the repair
shows S2 not met, D−R = −0.0017 ± 0.0094, so the agent ties random and R is as legitimate a finalist as D.)

**Baseline-through-mapping: 1.508 / 2.301 / 2.526 = N0 exactly (|err| 0.0000).** Honest status: this is an
**identity BY CONSTRUCTION** — the mapping is relative, so A0-vs-A0 gives δf≡1, a≡1. It is a plumbing check,
not evidence of transport fidelity. The added non-inertness gate passes (finalists do move the band).

### The mapping defect I found in my own pre-registration (D4)
The pre-registered amplitude channel `a_i = |g_X,i|/|g_A0,i|` is **INVALID**:
- arm B: **median |ln a| = 2.31** (a 10× median change in per-mode tray participation), **max 10.40**
  (~30,000×) — from a modest property/stiffness edit. Arms D/R: median 1.02 / 0.86.
- **Cause:** near-degenerate modes. **18 of 44** adjacent in-band A0 pairs sit within **1%** (26 within 2%) —
  e.g. the 140.9/141.1/141.6/141.7/141.7 Hz five-mode cluster. Inside a near-degenerate subspace the
  individual eigenvectors are arbitrary up to rotation: **only the subspace is basis-invariant, per-mode
  participation is not.** A0 and each finalist are different re-solved bases. Aggravated by a **7.0e4**
  dynamic range in per-mode |g| (dividing by a near-zero participation detonates the ratio).
- The **frequency** channel δf is sound (median |δf−1| = 0.005/0.001/0.000; max pairing cost |ln(f_X/f_A0)|
  = 0.165/0.081/0.117).

So S3 is reported across **three variants** and judged on their **agreement** (pre-registered in D4 *before*
the variants were scored):

| | shear_X width (deliv 1.508, 2σ MC 0.021) | shear_Y width (deliv 2.301, 2σ MC 0.071) | any finalist meets rule? |
|---|---|---|---|
| **full** (pre-registered C1; amplitude INVALID) | B 2.040 · D 2.176 · R 9.241 | B 7.954 · D 37.685 · R 2.671 | **no** |
| **freq_only** (δf only — sound) | B 1.511 · D 1.495 · R 1.489 | B 2.276 · D 2.285 · R 2.303 | raw **yes** / beyond MC noise **no** |
| **cluster_amp** (degeneracy-safe amplitude) | B 1.250 · D 1.213 · R 1.339 | B 2.411 · D 2.475 · R 2.238 | **yes** |

**The variants DISAGREE ⇒ S3 = CANNOT-VERIFY-through-this-mapping**, under **both** readings (raw and
MC-significant), so the verdict does not hinge on the noise-floor choice.

### Two findings that survive the mapping defect
1. **`freq_only` shows no real effect at all.** D and R "narrow" shear_X by 0.013 / 0.019 — **below the
   measured 2σ MC noise floor of 0.021**. The finalists' *frequency* changes do essentially nothing to the
   band. Any real effect would have to come through the amplitude channel — the one that is invalid.
2. **The RANDOM control narrows as much as the agent arms.** Under `cluster_amp`, R gives shear_X 1.339 vs
   B 1.250 / D 1.213. **A "narrowing" that the random arm reproduces is not evidence of model quality** —
   it is what a non-informative perturbation of tray participation looks like. This independently reproduces
   the study's S2 result (agent ties random) in the QOI space rather than the scoring space.

**Held-out-DRIVE coverage (real data, 4 DEV drives; the +XY vault was NOT read).** The delivered twin's
baseline reproduces the netcg thread's published numbers exactly: **shear_X min 1.000**, **shear_Y min
0.596** (the known +Z@900 end-drive gap) — an independent validation that the held-out reuse is faithful.
Finalist rows that clear the ≥0.95 shear_Y bar do so by being **wider**, which the joint rule is designed to
catch.

**Overconfidence audit (card §3.3: hide top-3 measured QOI-driving modes → every band must widen >1):** under
the netcg machinery every band widens — tiered 1.407 / 1.317 / 1.040; finalists 1.019–1.349. Compare the
study's reimplementation, which was essentially inert (shear_X 1.000, normal_Z 1.003; review C5). **The
delivered machinery is humble where the reimplementation was not.**

---

## What this means for the deliverable

**The delivered net-CG twin (1.51× shear X / 2.30× shear Y / 2.53× normal Z) stands unchanged.**
- No finalist arm (B, D, or R) is demonstrated to improve OR degrade it.
- The one data-driven tier update available (A5b, H4) **widens** the normal-Z band rather than sharpening it,
  because the data says that mode's amplitude is more uncertain than assumed.
- This is now an *assessed* conclusion resting on a reproduced reference, not an *unassessable* one.

## If reopened — what would actually move S3
1. **A degeneracy-aware transport.** Pair A0↔finalist by **MAC on a common DOF space** (project both onto the
   shared full-order basis) instead of by frequency, or evaluate the QOI at the **subspace** level. That is
   the specific fix for the D4 defect.
2. **Option (a) plumbing done right:** map the wide package's tray/drive rows into the netcg reduced model —
   but note this is the reimplementation path that failed once (C5); it must be gated by N0-style
   reproduction first.
3. **The physics lever for normal-Z is not modelling, it is instrumentation:** more Z sensors on the plate
   (the >200 Hz plate test) would measure the drumhead shape. Until then the normal-Z band is shape-limited
   and no re-modelling of the box will sharpen it.

## Nothing left to run in this card
All deliverables present: `packet.md`, `findings.md`, `out/verdicts_S3S4.json`, `out/n0_reference.json`,
`out/n1_bridge.json`, `out/s3_mapping.json`, `out/mc_noise.json`, `out/vault_guard.json`, 4 figures
(QA-passed), `decisions_log.md` (D0–D6), `run_all.sh`, `runtime.json` (active 96.79 s), `checker_report.json`,
`REUSED_code.sha256` (25 sources verified unchanged), `CHECKER.sha256`.
