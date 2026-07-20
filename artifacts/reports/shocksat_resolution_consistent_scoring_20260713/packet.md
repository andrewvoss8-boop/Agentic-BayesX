# Review Packet — ShockSat Resolution-Consistent FRF Scoring (2026-07-13)

**Checker: OVERALL RED — see `checker_report.json` (the one RED gate is Gate W, the raw-data window
verification; every pipeline/integrity gate is GREEN; the two YELLOWs are the honestly-falsified S1 claim and
the not-confirmed S3 mechanism tier).** One-command replay: `bash run_all.sh`. Card:
`docs/lab/shocksat_resolution_consistent_scoring_runner_prompt.md` (dispatched by Andrew 2026-07-13).

## 0. One-paragraph summary
Processing the model FRF through the SAME frame/window as the measured 2 Hz caches (resolution-consistent
scoring) improved held-out FRF correlation over the incumbent convention by **+0.040** (dev P1′ 0.197 → 0.237,
confirmed directionally on the vault drive 0.420 → 0.473) — but the pre-registered win needed the margin to
also clear **2× the fold-to-fold noise (0.053)**, and it does not, so **S1 is FALSIFIED** under the noise-floor
rule. The attribution decomposition (S2) shows the gain is **the window, not the damping** (window-alone
+0.033 of the +0.040; physical damping alone −0.012; interaction +0.019). **Gate W FAILED**: the re-downloaded
Test07 raw records turn out to have a **dead force channel in all four hits** (~1 lb noise vs 1000–1900 g
responses), making the card's direct H1-recompute physically impossible, and the force-free fallback missed
its pre-registered thresholds — so the window mechanism, although supported by exact provenance, the synthetic
Gate K, and isolated-peak fits, is **not certified against raw data** and S3 fails with it. No sampler was
used (deterministic arms; reused θ_MAP), as declared.

## 1. Method summary (first-pass, plain English)
- **Question (pre-registered):** does window-matching the model FRF let the physically-correct light damping
  (~0.3% of critical) beat the incumbent "naive model + flat 1%" convention on held-out per-sensor FRF, and is
  any gain due to the window, the damping, or their combination?
- **Model form:** the reused exact-basis A0_enr package (80-mode reduced modal superposition, free-free,
  accelerance H in g/lbf), θ fixed at its multi-start MAP (a point estimate reused from the damping run —
  "MAP" = the single best-fit stiffness-parameter vector; nothing is inferred here). Damping enters as fixed
  measured data (survey per-mode ζ, frequency-interpolated; or ERA 4-band; or the flat 1% convention).
  **No likelihood is evaluated and no sampler is run — this is a deterministic scoring study** (stated per the
  AGENTS Sampler Decision rule).
- **The window operator 𝒲 (the new piece):** the caches were distilled with a 0.4915 s frame (122,880 samples
  @ 250 kHz) and an **exponential response window** decaying to 0.05 (source code FOUND, not inferred:
  `modal_multiref.py → multiref_frf.py → realfrf.py`, hashed in `REUSED_code.sha256`). That window adds decay
  rate σ_w = 1/τ (τ = 0.1641 s) to every mode — an added apparent damping ζ_w(f) = 1/(2πfτ):
  **1.62% @ 60 Hz → 0.97% @ 100 Hz → 0.39% @ 250 Hz** (this formula exists in the original workspace as
  `realfrf.measured_zeta_w` — the distillation *documented its own broadening*). 𝒲 is implemented in exact
  closed form (finite geometric sums of the sampled, windowed, frame-truncated modal impulse response;
  equations in `quantity_contracts.md`); with the window and truncation removed it reduces *analytically* to
  the naive FRF, so naive and windowed arms share one formula and cannot drift apart numerically.
- **Data:** 5 measured drive caches (111 channels × 105 bins each, H1 + coherence; 6 hits each): 4 dev drives
  (leave-one-drive-out = score on each drive after fitting the alignment/gain on the other 3 — "fold" = one
  such held-out split) + the +XY vault (read ONCE, post-freeze; **SECOND program read** of that cache — the
  damping run graded it 2026-07-10; mitigation = zero search, the 6 arms were fixed by the card before any
  score). Raw Test07 (+X impact series, 4 hits @ 250 kHz) used ONLY by Gate W.
- **Metrics:** P1′ = FDAC-aligned FRAC (correlation of log-magnitude FRFs after a train-side frequency
  alignment; 1 = perfect, 0 = none), P2′ = |FRSF−1| amplitude error at matched peaks, P3 = raw log|H|
  correlation, P4 (new) = median |peak-height error| in dB at matched peaks (dB is the standard unit for FRF
  amplitude error). Whole-band data for P1′/P3; matched-peak features for P2′/P4 (both reported).
- **Honesty rails carried:** exact-basis packages; one global gain per fold (train-side); NO per-mode or
  per-channel amplitude/damping fitting anywhere (checker-grepped); damping is measured data or the fixed 1%.

## 2. Arms and scores (dev = 4-fold mean; vault = single post-freeze read)
| arm | forward | damping | dev P1′ | dev P2′ | dev P4 [dB] | vault P1′ |
|---|---|---|---|---|---|---|
| B0 (incumbent) | naive | flat 1% | **0.1969** | 0.855 | 10.9 | 0.420 |
| B1 (control) | naive | survey ζ ~0.3% | 0.1845 | 0.862 | 11.1 | 0.387 |
| **B2 (claim)** | **windowed** | survey ζ | **0.2371** | 0.758 | 10.5 | **0.473** |
| B3 (ablation) | windowed | flat 1% | 0.2302 | 0.735 | 10.3 | 0.491 |
| B4 (validation) | windowed | ERA 4-band ζ | 0.2414 | 0.762 | 10.5 | 0.466 |
| B5 (shape comparator) | windowed | survey ζ (c06 pkg) | 0.2019 | 0.925 | 10.2 | 0.497 |

Gate R (pipeline continuity): B0 reproduces the damping run's frozen A0_enr number to 1.6·10⁻⁷ — the scorer is
bit-level consistent with the prior study. B1 < B0 reproduces the addendum's naive-physical deficit.
Vault caveat: the +XY drive sits +0.22–0.30 above dev in every run of this program (location effect) AND this
is its second read — vault numbers are directional confirmation only, never a win.

## 3. Verdicts (pre-registered; `out/verdicts.json`)
- **S1 — FALSIFIED (YELLOW).** Δ(B2−B0) dev P1′ = **+0.0401** ≥ +0.03 ✓; vault B2 > B0 ✓ (0.473 vs 0.420);
  but the paired per-fold deltas are [+X +0.012, +Z +0.111, +Y −0.010, +Z@900 +0.048] → fold-SE ("standard
  error" = spread of the fold deltas ÷ √4, the run-to-run noise of the mean) = 0.0263, and the pre-registered
  rule demands Δ ≥ 2×SE = 0.0527. **+0.040 < 0.053 → falsified by the 2026-07-06 noise-floor rule.** The +Y
  fold is even slightly negative — the gain is not uniform across drives.
- **S2 — attribution: it's the WINDOW.** window-alone (B3−B0) = **+0.0332**; damping-alone (B1−B0) =
  **−0.0125**; interaction = **+0.0193**; total +0.0401. Damping+interaction (+0.0069) < ½·total (+0.0201), so
  "consistent processing lets *physical damping* be used correctly" is NOT supported at the pre-registered
  bar. The positive interaction does mean physical ζ only stops *hurting* once the window is matched — but a
  flat 1% under the window (B3) does essentially as well, and the ERA-band variant (B4, +0.011 over B2's
  survey ζ) is within a fraction of the fold noise. **Damping refinement beyond the window is noise-level.**
- **S3 — mechanism tier: NOT confirmed (YELLOW), because Gate W failed.** The score part passed easily
  (B2 − B1 = +0.053 ≥ +0.02: window-matching recovers the physical-ζ deficit and more); the raw-data gate did
  not (below).

## 4. Gate results
- **Gate K (synthetic operator correctness) — GREEN.** Windowed 1-DOF peak matches the analytic apparent-ζ
  prediction (ζ + ζ_w) to **−1.98%** at ζ=0.3% (the −2% is real frame truncation, correctly captured) and
  **+0.005%** at ζ=5%. D6 correction reported loudly: the card's "broad peak ~unchanged" expectation was a
  Hann-kernel intuition — the ACTUAL exponential window adds ζ_w at every width (a ζ=5% peak drops 16%).
- **Gate R (reproduction) — GREEN** (§2).
- **Gate W (window model vs raw data) — RED, and here is the honest story.**
  1. **Discovery: the Test07 force channel is dead in all four hits** (argmax = ±1 lb noise at random times
     0.01–0.52 s; the true impacts, 1000–1900 g, are at ~0.50 s; a ~1 lb "force" cannot produce a 218 g
     response). The card's direct comparison — recompute the stored +X H1 from raw Test07 — is **physically
     impossible**: H1 needs force. This also retro-explains the 2026-06-09 statfem-runner finding "Test07
     low coherence". The stored caches themselves are unaffected (they were built from the Test01/02/03/06/04
     MODAL-hammer series, which had live force; their raw files were deleted upstream after distillation).
  2. The pre-registered force-free fallback (dated addendum in `quantity_contracts.md`, decisions D8) then
     missed its thresholds: hit-consistency 0.090 dex median (needs 0.05 on ≥80% of channels; sensitivity:
     0.10 dex → 60%, 0.15 dex → 88% — the hits genuinely differ, 002–004 are from the NEXT day) and
     apparent-ζ physics median ratio 1.88 (needs 0.75–1.25).
  3. **What the evidence actually says** (all in `out/gate_W.json`): truly ISOLATED peaks agree with the
     window prediction on BOTH the stored cache and the raw spectra (163.0 Hz ratio 0.88–0.90, 188.5 Hz
     0.84–0.87, 233.1 Hz 1.32); the failures are all peaks that absorb close neighbors at 2 Hz bin spacing
     (ShockSat's modal density defeats a ±3-bin width fit); **no peak is systematically NARROWER than
     predicted** — nothing refutes window-broadening; Test01↔Test07 shape correlation 0.834 (bonus
     repeatability number). A differential window-vs-rect test was designed, run, and found **physically
     uninformative** (rect-frame truncation broadening ≈ ζ_w at these frequencies) — reported, not used (D9).
  4. **Why RED anyway:** the pre-registered thresholds were not met on any comparison actually run, and after
     one data-forced revision (D8) I refused further re-basing (D9) — inventing bases until one passes is
     threshold-shopping. Per the pre-registered interpretation rule this is a *quantitative* gate failure
     (the model reproduces the processing qualitatively), so the arm scores stand as measured, but the
     mechanism certification rests on **provenance + Gate K**, not on the raw-data gate, and S3 falls.

## 5. What this means (mechanism, in plain terms)
The distillation's exponential window makes every resonance in the 2 Hz caches LOOK like a ζ ≈ ζ_true + ζ_w(f)
≈ 0.4–2% mode regardless of the true ~0.3% (fig_apparent_zeta). The incumbent flat-1% convention "worked" all
along because 1% is a decent average of that apparent-damping curve — NOT because ShockSat is 1%-damped.
Window-matching the model recovers the physical-ζ deficit (+0.053 over naive-physical) and beats the incumbent
by +0.040 on dev — a real, directionally vault-confirmed improvement that nevertheless fails the pre-registered
noise-floor margin, chiefly because the +Y fold does not participate. Once the window is matched, WHICH
light-damping table you use (survey per-mode, ERA bands, or even flat 1%) moves the score by less than the
fold noise: **the resolution/processing consistency is the lever; damping refinement at 2 Hz is not.**

## 6. Sensitivity + assumptions (ledger: `assumptions_ledger.md`)
- Survey-ζ mapping (A3): interp vs nearest-mode changes B2 by **−0.0002** (nothing).
- Gate-W hit-consistency threshold (A-sens ii): frac_ok 0.078 / 0.598 / 0.882 at 0.05 / 0.10 / 0.15 dex.
- The decision-driving noise assumption is the fold-SE rule itself: S1's margin (+0.040) sits between the
  "absolute" bar (0.03) and the noise bar (0.053) — shown per-fold on fig_money. A 5th independent drive
  would be the cheapest way to sharpen this comparison.
- Discretization: the analysis grid IS the study object (2.03 Hz cache bins); 𝒲 is exact at those bins;
  fine-grid (0.05 Hz) curves appear only in figures, labeled.

## 7. Figures (`figures/`; all Tufte-linted `out/tufte_lint.txt`, legibility-QA'd `out/fig_qa.json`)
fig_money (arm scores + folds + vault + verdict), fig_s2_decomp (attribution bars), fig_gateW_overlay
(stored-vs-raw overlay + physics scatter + FAIL label), fig_apparent_zeta (the mechanism curve), fig_peak_zoom
(3 matched peaks: naive towers vs windowed matches the 2 Hz data).

## 8. Runtime, disk, cleanup
`runtime.json` (active ≈ sum of executed steps; wall-clock spans the interactive session). Disk hit 100%
mid-run (D7): Gate W now streams one ~245 MB .mat at a time and deletes it; nothing large persists (the 566 MB
Test07 zip at repo root is kept, hash-pinned; extracted .mat files: none remain). **Flag for Andrew: the disk
has ~0.2–0.5 GB free — worth clearing before any future raw-data work.**

## 9. Recommendation to Andrew (decisions are yours)
1. **Convention:** for any future FRF scoring against these 2 Hz caches, use resolution-consistent scoring
   (𝒲 + measured light ζ) or, equivalently pragmatically, keep flat-1%-naive knowing WHY it works. Do not
   interpret cache peak widths as damping.
2. **The one cheap decisive follow-up:** the S1 margin failed on fold noise with 4 folds; the mechanism gate
   failed for want of usable raw data. BOTH would be settled by re-downloading ONE modal-hammer raw series
   with live force (Test01 or Test02 class, ~0.5–1 GB): Gate W direct becomes possible, and a longer-frame
   re-distillation would test the window story end-to-end (and could turn the +0.040 into a certified gain).
3. Otherwise this closes the ShockSat damping arc: damping was never recoverable from these caches; the
   remaining headroom is processing, not physics. MPL (fresh headroom) is the natural next thread.

## 10. Continuity
`notes/runs.md` entry + `docs/report/project_log.md` row appended at the end with the checker status verbatim.
Decisions D0–D9 in `decisions_log.md`; the two dated addenda (quantity_contracts Gate-W revision; this run's
gate files) are append-only. The frozen damping run and its addendum are untouched.
