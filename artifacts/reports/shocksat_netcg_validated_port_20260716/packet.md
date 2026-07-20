# Human-review packet — VALIDATED NET-CG QOI PORT
**Runner card B (post-review item 4: make S3/S4 assessable) · 2026-07-16 · commit 9cad98c**
Status is copied from THIS workspace's immutable checker (`checker_report.json`). Nothing below is stronger
than that output.

---

## 1. METHOD SUMMARY FIRST — exactly what was REUSED vs MAPPED vs NEW

The whole point of this card: the full-spectrum study **reimplemented** the net-CG band machinery and could
not reproduce the delivered twin, so the reviewer (C5) ruled S3/S4 **CANNOT-VERIFY**. The fix is not a better
reimplementation — it is **not reimplementing**.

| Layer | Status | What it is |
|---|---|---|
| `netcg_qoi.QOIModel`, `Method`, `truth_ensemble`, `coverage_vs_truth`, `octave_smooth`, `grms`, `FGRID`, `ZETA`, `SD_*` | **REUSED byte-identical** | The delivered twin's band machinery, imported read-only from `shocksat_netcg_method_selection_20260701/code/`. Not copied, not edited. |
| Reduced model (`realfrf.load_reduced()`) | **REUSED byte-identical** | 74-DOF reduced basis, `K(θ)=A_fix+Σθ_g A_g`, mass = I, free-free survey basis. 40 in-band modes (54.6–258.9 Hz), 20 measured via `.ash` matching. |
| L5 θ posterior | **REUSED draws** | 4000 cached NUTS draws over 9 stiffness groups (`out/theta_post_L5.npz`). **No sampler runs in this card** (card §5). Inherited convergence, not re-claimed here: max R̂ 1.0013, min ESS 2646, 0 divergences. |
| `heldout_drive.fit_participation / per_drive_band / answer_key` | **REUSED byte-identical** | Real-data held-out-DRIVE conventions. Driven with **DEV drives only**. |
| `bakeoff.band_ratio` width formula | **COPIED VERBATIM** (3 lines) | `bakeoff.py` is a `__main__` script whose `main()` would **write into the read-only netcg workspace**, so the formula is copied rather than imported. Quoted in `quantity_contracts.md` B1. |
| A5b tier rule | **MAPPED** into the reused machinery | Study's pre-registered tier rule injected via **hook 1** (below). |
| Finalist arms B/D/R | **MAPPED** into the reused machinery | Relative per-mode (δf, a) perturbation via **hook 2** (below). |
| The 3 mapping variants + the MC noise floor + the vault guard | **NEW** | The only genuinely new analysis code. |

### The two injection hooks (and why they cannot silently drift)
The card needed two things netcg does not expose: per-mode amplitude tiers, and per-mode finalist
perturbations. Both are injected through **subclass hooks that provably reduce to the parent**, asserted
numerically at runtime *before any number is produced*:

- **Hook 1 — per-mode amplitude SDs (`TieredMethod`).** netcg's statFEM F(k) marginal is
  `marg(f) = 0.25 + (SD_A_U − 0.25)·ufrac(f)`, where `ufrac` = the UNMEASURED-mode share of |G| energy at
  frequency f. That is algebraically the contribution-weighted form `0.25 + Σ_i (sda_i − 0.25)·w_i(f)` for
  the netcg tier vector `sda_i = 0.25` (measured) / `0.80` (unmeasured). So a **general** per-mode `sda`
  vector is injected by returning an *effective* ufrac from the one method netcg already calls —
  `ufrac_eff = Σ_i (sda_i − 0.25)·w_i / (SD_A_U − 0.25)` — leaving `ensemble()` untouched.
  **Runtime proof:** with the netcg tier vector, `max|ufrac_eff − ufrac| = 5.6e-16` (float rounding) on all
  three axes.
- **Hook 2 — finalist perturbation (`MappedQOIModel`).** Overrides only `modes()` (scale in-band f by δf)
  and `g_axis()` (scale tray participation by a). netcg's `spectrum()`, `_unmeasured_local_frac()` and
  `drive_part()` all route through those two, so the perturbation applies consistently with no other edit.
  δf ≡ 1, a ≡ 1 → the parent exactly.

### Model form and likelihood (plain English first)
- **The QOI** is the **tray net-CG force** — the mass-weighted acceleration integral over the top tray, i.e.
  the interface base reaction the tray would impose as a payload. Per frequency
  `S_F(ω) = |G(ω)|²·S_input`, `G(ω) = Σ_i g_i·ω²/D_i(ω)`, `D_i = ω_i² − ω² + 2iζω_iω`, ζ = 1% for all modes.
  `g_i` = uniform-mass tray-region (z ≥ 55 in) modal participation on the QOI axis. Full contract, including
  the units and the two competing conventions, in `quantity_contracts.md` Part A (copied verbatim from the
  netcg thread).
- **The band** is a 95% interval over an **ensemble of 2400 spectra**: 60 reused θ draws × 40 statFEM F(k)
  discrepancy draws. The discrepancy is a frequency-correlated (1-octave-smoothed) log-amplitude field whose
  local width ramps up where UNMEASURED modes drive the response — that is what "statFEM F(k)" means here.
- **Likelihood data usage: none in this card.** No inference is performed. The θ posterior was fitted
  elsewhere (L5 = modal-frequency **feature** likelihood, i.e. matched eigenfrequencies, *not* whole-FRF);
  this card only **propagates** those draws through the QOI and scores band width/coverage. The one fitting
  operation is the held-out per-mode participation LSQ, which is **answer-key construction, never a
  selection score** (annotated `CHECKER-OK(non-selection)`, grep-gated).
- **Data count:** 4 DEV drives (+X/990x, +Z/990z, +Y/990y, +Z@900/900z). The **5th (+XY) drive is the vault
  and was NOT read** — enforced by a process-wide `np.load` guard that raises, plus a checker grep.
  `out/vault_guard.json`: `xy_files_opened = 0`.
- **Inferred here:** nothing. **Fixed:** ζ=1%, FGRID (45–260 Hz, 400 linear points), tier SDs (SD_F 0.01/0.06,
  SD_A 0.35/0.80), the marginal floor 0.25, all thresholds. **Not inferred (latent):** per-mode amplitudes and
  the drumhead mode shapes — that ignorance is exactly what the band represents.

### The scored quantity (one line, because the study got this wrong)
**Width ratio = `grms(hi − lo) / grms(fem6_hi − fem6_lo)`** — the 95% band's width, normalised by the
FEM+6 dB incumbent band's width. Dimensionless. **1.0 = as wide as the incumbent.** This is
`bakeoff.band_ratio`, and it is the ONLY convention used here.

---

## 2. Headline

**Gate N0 PASSED EXACTLY — so S3/S4 are assessable for the first time, and the answer is: the delivered twin
stands.**

| Gate | Rule (pre-registered, card verbatim) | Result | Status |
|---|---|---|---|
| **N0** | reproduce 1.51/2.30/2.53 ±0.05 via the ORIGINAL netcg machinery | **1.508 / 2.301 / 2.526**, max \|err\| **0.0000** | **GREEN** |
| **N1** | θ point vs model bridge (diagnostic, no threshold) | θ point explains **~0%** of the study's gap | **GREEN** (diagnostic) |
| **S3** | a finalist narrows shear below 1.508/2.301 at held-out coverage ≥0.95 | mapping variants **disagree** → CANNOT-VERIFY-through-this-mapping | **YELLOW** |
| **S4** | normal-Z ≤1.90× AND coverage ≥0.95 | **2.958×** (WIDER than the delivered 2.526×), coverage 0.989 | **YELLOW — not met** |

**Checker: OVERALL GREEN (10 GREEN / 0 YELLOW / 0 RED), exit 0 — INTEGRITY only.**
> ⚠ **That GREEN does NOT mean S3/S4 were met (D7).** My pre-registered checker gates *process integrity*
> (reference reproduced, statistics finite, mapping validated + non-inert, no selection-path fitting, no
> vault reads, figures QA'd, runtime sane, checker unmodified, deliverables + reused-source SHAs, no new
> sampler). It has **no gate that propagates the S3/S4 verdicts into OVERALL** — a limitation I found at
> reporting time and chose to disclose rather than fix by editing the SHA-locked checker.
> **Science verdicts: N0 = GREEN (reference reproduced). S3 = CANNOT-VERIFY (YELLOW). S4 = NOT MET
> (YELLOW).** Read the table above, not the light.

### The three things a reviewer should take away
1. **The review's C5 diagnosis was right, but its stated cause was wrong.** The study's `netcg_results.json`
   CAVEAT blames "a marginal-calibration difference in the reimplemented statFEM F(k)". It is actually a
   **quantity-contract divergence**: on the *identical* `lo`/`hi` arrays of the *identical* delivered band,
   netcg's convention gives **1.508** and the study's `band_width_ratio` gives **21.660**, because the latter
   is an upper/lower **envelope ratio** that never references the FEM+6 dB denominator. No calibration of any
   constant could have reconciled those. (`fig_n0_bands.png`, bottom-right.)
2. **S4 is falsified honestly, exactly along the path A5b pre-registered.** Only one extended-band cluster
   mode matches inside 45–260 Hz (measured 254.3 Hz ↔ FEM 254.9 Hz, 0.2%). Its **observed** cross-drive
   ln-amplitude scatter is **1.393** — *larger* than the **0.80** the delivered twin already assumed for an
   unmeasured mode. Measuring that mode made it **more** uncertain, so normal-Z **widens 2.526× → 2.958×**
   (+0.432, vs a measured 2σ MC noise floor of 0.091 → real). A5b wrote this falsification path down on
   2026-07-14 before any QOI computation. **H4 is falsified, and the delivered 2.526× twin stands** — if
   anything it is mildly optimistic for that mode.
3. **S3 cannot be settled through this mapping, and I caught that in my own pre-registration.** My
   contract's per-mode amplitude channel is **invalid**: 18 of 44 adjacent in-band mode pairs sit within 1%
   in frequency, so within those near-degenerate subspaces the eigenvectors are arbitrary up to rotation and
   per-mode participation ratios are basis-dependent (median |ln a| = **2.31** — a 10× "change" — for a
   modest stiffness edit). Reported as three variants; they **disagree** → CANNOT-VERIFY. Also note the
   **random control R narrows shear_X as much as the agent arms** (1.339 vs 1.250/1.213), which is what a
   *non-informative* narrowing looks like — consistent with the study's S2 (agent ties random).

---

## 3. What changed for the project

- **Before:** S3/S4 = CANNOT-VERIFY *because no valid reference existed* (review C5). The delivered twin
  could be neither improved nor degraded; the question was unresolvable.
- **After:** the reference reproduces **exactly**, so the machinery is validated and the questions are
  askable. **S4 now has a real, pre-registered answer: NOT MET (falsified).** **S3 is still CANNOT-VERIFY,
  but for a completely different and much narrower reason** — not "we can't reproduce anything", but "the
  finalist→netcg mapping's amplitude channel is defeated by modal degeneracy". That is a specific, fixable
  obstacle with a named cause, not a black box.
- **The delivered net-CG twin (1.51× / 2.30× / 2.53×) stands unchanged.** No arm is demonstrated to improve
  it; the one data-driven tier update we could apply widens rather than sharpens it.

---

## 4. Figures (all scripted, Tufte-linted, image-QA'd — `out/fig_qa.json`, `out/tufte_lint.json`)

| Figure | What it shows |
|---|---|
| `fig_n0_bands.png` | Gate N0: the three delivered bands reproduced to \|err\| 0.0000, **and** the convention collision that explains C5 (1.508 vs 21.660 on the same arrays). |
| `fig_n1_theta_bridge.png` | Gate N1: θ-point vs model decomposition. The study's θ point moves shear_X by +0.21 and moves shear_Y/normal_Z the **wrong way** (−0.45/−0.45) → ~0% of its 6.5/2.9/3.4-wide gap is θ. |
| `fig_s4_tier_update.png` | S4: normal-Z band before/after the A5b tier update (widens), width bars vs the 1.90× rule, coverage bars vs the 0.95 rule. |
| `fig_s3_finalists.png` | S3: finalist widths across the 3 mapping variants vs delivered ±2σ MC, plus real-data held-out-drive coverage bars. |

---

## 5. Honest limitations (read before using any number here)

1. **S3's mapping is not validated for transport fidelity.** The card's required "baseline-through-mapping
   reproduces N0 ±0.05" check passes at |err| 0.0000 — but that is an **identity BY CONSTRUCTION** (the
   mapping is relative, so A0-vs-A0 gives δf≡1, a≡1). It proves the plumbing, not the physics. I added a
   non-inertness gate to compensate; it passes (finalists do move the band).
2. **The mapping is blind to mode reordering/splitting** and does not perturb the drive-point participation
   `φ_drive`. If the finalists' real effect is shape reordering, this card measures the wrong perturbation.
3. **Synthetic-truth coverage is self-consistency, not truth.** The plausible-truth ensemble is built from
   the same model with tier perturbations. Only the **held-out-DRIVE** numbers are real-data evidence, they
   exist for **shear only** (normal-Z has no answer key: the drumhead shape is unmeasured with 1 Z sensor),
   and their answer key itself uses the model's shapes.
4. **The S4 result rests on ONE mode** (254.9 Hz) and one scatter number (1.393, 4 dev drives) inherited from
   the study. It is a 4-sample standard deviation. The *direction* is robust (+0.432 ≫ 0.091 noise); the
   *magnitude* should not be over-read.
5. **Nothing here re-validates the L5 posterior.** Its convergence is inherited from the netcg thread and
   labeled as such; this card ran no sampler and makes no NUTS claim of its own.
6. **The 45–260 Hz band and ζ=1% are inherited, not re-justified.** Grid resolution is ~2 points per
   half-power bandwidth at the lowest in-band mode (54.6 Hz) — it cancels in the width RATIO because
   numerator and denominator share the grid, which is why the ratio is the deliverable (`quantity_contracts.md` B4).
7. **The width ratio is normalised by the FEM+6 dB incumbent.** If that incumbent envelope is wrong, every
   ratio in this packet is wrong.

## 6. Replay
`./run_all.sh` — 97 s active / 97 s wallclock, Mac CPU float64, exit 0. Gate order is enforced in code:
`s3s4_assess.py` asserts `n0_reference.json` status == PASS before touching anything arm-related.
Checker is SHA-locked (`e235e9fc…`), was proven RED on the empty workspace first
(`out/checker_red_on_empty.json`, 10/10 RED), and was never edited. All 25 reused read-only sources are
SHA-pinned in `REUSED_code.sha256` and re-verified by gate G09.
