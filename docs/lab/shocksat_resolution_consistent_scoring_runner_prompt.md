# RUNNER PROMPT — ShockSat RESOLUTION-CONSISTENT FRF Scoring with PHYSICAL Damping (window-matched, vault-confirmed)

**Status: DRAFT, written by the lead (Fable) 2026-07-13 as the closing follow-on to the completed FRF-damping
run (`artifacts/reports/shocksat_frf_damping_updating_20260710/`, checker YELLOW 19G/2Y/0R, claim falsified)
and its 2026-07-11 post-run addendum. Andrew reviews, then dispatches. Self-contained; NO human stop-points.**

The damping run falsified the damping lever on the 2 Hz FRF caches and the addendum explained WHY from one
re-downloaded raw drive (Test07/+X, 250 kHz): ShockSat's true damping is LIGHT (~0.3%, ERA median 0.301% vs
survey 0.317%, matched 27/33 modes), but the distilled FRFs were made with a ~0.49 s FFT frame whose spectral
window (~2 Hz main lobe) BROADENS every resonance to an apparent damping of ~1–2.5% regardless of the true
value. So the caches encode WINDOW-broadening, not damping; naive physical ζ scores WORSE (dev P1′ 0.186 vs
A0's 0.197), and a scratch window-convolution recovered ~60% of that deficit in-sample. This card turns that
diagnostic into a clean, pre-registered study.

---

## 0. Who you are and the ONE question
Autonomous runner for Agentic BayesX; full authority start-to-finish. Work ONLY in your own new workspace;
never edit durable rules, other studies' checkers/artifacts, or project notes (APPEND one runs.md entry + one
project_log row at the very END, status copied verbatim from your checker).

**ONE falsifiable question (one run, one question):**
> If the model FRF is processed RESOLUTION-CONSISTENTLY — through the SAME FFT frame/window as the measured
> caches — does the physically-correct light damping (survey/ERA ~0.3%) improve the inherited ShockSat FEM's
> held-out per-sensor FRF prediction over the incumbent convention (naive model FRF + ζ=1%), and is any gain
> attributable to the WINDOW-MATCHING, the PHYSICAL DAMPING, or only their combination?

A clean falsification is a VALID, REPORTABLE outcome ("pre-registered claim falsified"), never a pipeline
failure. **Pre-registered honest expectation:** window-matching + physical ζ should roughly RECOVER the A0
convention's score (the in-sample scratch result: 0.229 naive → 0.238 windowed vs 0.244 A0-1%), because A0's
flat 1% already approximates the frame-equivalent apparent damping; a real WIN (clearing the margin) requires
the window model to capture what a flat 1% misses — the frequency DEPENDENCE of the apparent damping (2.5% @
60 Hz → 0.6% @ 250 Hz). Whether that dependence is worth anything on held-out data is exactly the open
question. Delivering a replacement twin is NOT the job; replace/keep is Andrew's decision, surfaced in the
packet.

**This is a NO-SAMPLER study (stated per the AGENTS Sampler Decision rule):** all arms are deterministic —
fixed pre-registered damping + the reused multi-start θ_MAP; nothing is inferred beyond that reuse, so no
NUTS leg is required or claimed. Any Bayesian follow-up would be a new card.

## 1. Re-ground FIRST (read before any work)
1. `AGENTS.md` — every gate applies (priority deliverables, question/decision, assumptions, quantity
   contracts, references, Tufte + `tufte_lint.py`, sensitivity, verification, discretization, runtime
   accounting, Result Status Standard, compute/detached).
2. This file, fully. Then the completed damping run: `artifacts/reports/shocksat_frf_damping_updating_20260710/
   {packet.md (incl. the 2026-07-11 Addendum), decisions_log.md, quantity_contracts.md}` — internalize P1′/P2′/
   P3 definitions, the exact-basis rule, the physical-damping gate, and the addendum's window findings.
3. Scratch evidence (read-only): `scratch_test07/{era_id.py, era_result.npz, window_rescore.py, rescore.py}` —
   the ERA ζ table and the kernel-convolution prototype this card formalizes.
4. `references/fem_test_correlation_litreview.md` §2 (FRF metrics) and §8 (damping) for context.

State a one-line D0 in your `decisions_log.md`: goal / last decision / next action / open ambiguities. After
ANY compaction, re-ground from this file + your gate files before acting.

## 2. Assets (exact paths; read-only; SHA256 the code+data you reuse in `REUSED_code.sha256` before science)
| asset | path |
|---|---|
| Scoring/metrics/damping-forward code to reuse | `artifacts/reports/shocksat_frf_damping_updating_20260710/code/{femdamp.py, metrics.py, score.py}` (which chain to the true-remodel `femlib.py`) |
| Exact-basis packages (A0 + shape comparator) | `artifacts/reports/shocksat_frf_damping_updating_20260710/data/packages/{A0_enr.npz, c06_tb_xface_enr.npz}` + their `out/spot_check_*_enr.json` provenance |
| Measured modal survey incl. per-mode damping (PERCENT critical; D7 of the damping run) | `artifacts/reports/shocksat_fem_remesh_20260618/measured_modes.npz` (`damp`/100 → ζ, median 0.32%) |
| ERA identification result (validation; +X-derived) | `scratch_test07/era_result.npz` |
| RAW Test07 +X impact records (window-verification gate) | `Test07_ImpactHammer_990x.zip` (4 hits × 245 MB, 250 kHz, 1.0 s, 128 accel `g` + 1 force `lb`; hit 001 already extracted in `scratch_test07/`) |
| 5 distilled drive caches (2 Hz, H1 + coherence) | `artifacts/reports/shocksat_netcg_method_selection_20260701/data/multiref_modal/m_*.npz` |
| Distillation provenance (frame N=122880 @ 250 kHz, 6 hits, impact indices) | fields `N, n_hits_used, used, impact_idx` inside each cache |
| netcg distillation code (the ACTUAL window/frame used — find and cite it) | `artifacts/reports/shocksat_netcg_method_selection_20260701/code/` (+ upstream `shocksat_multiref_*` workspaces if the distiller lives there) |

**Reuse, do not re-derive:** P1′/P2′/P3 exactly as the damping run defined them (`quantity_contracts.md`
there), the exact-basis packages, and the frozen-pairing/θ_MAP machinery. You ADD: the measurement-window
model + resolution-consistent forward path, and Gate W below.

## 3. Pre-registered protocol (write `question_framing.md` FIRST, SHA-lock the checker BEFORE science)

### 3.1 Data protocol
- **DEV (grading, fold-averaged):** the same 4 leave-one-drive-out folds (+X/990x, +Z/990z, +Y/990y,
  +Z@900z). NO search loop, NO budget pressure: the arm set is FIXED a priori (below); dev is used only to
  grade it. Per-fold numbers reported; margins fold-averaged with ≥2×fold-SE required (noise-floor rule).
- **VAULT (confirmation; touched once by THIS run):** +XY/Test04 cache, graded ONCE after the arm set is
  SHA-frozen (`VAULT_FREEZE.sha256` precedes the read). **Honest label (stronger caveat than before): this is
  the SECOND program read of this cache** (the damping run graded it 2026-07-10). Mitigation: zero search —
  the arms are fixed by this card before any score, so no selection pressure can exploit the prior read; the
  vault is pure confirmation and is labeled exactly so.
- **Damping leakage rule (pre-registered):** the PRIMARY physical damping is the **.ash survey per-mode ζ**
  (train-side in every fold). The ERA ζ (from Test07 = the +X dev drive's raw records) is a VALIDATION input
  and the band-ζ fallback; any arm using ERA values carries a labeled caveat on the +X fold. ERA↔survey
  agreement (0.301% vs 0.317% median) is itself a reported result.
- OFF-LIMITS: force-level sweep, pyro data, re-downloading further drives (NOT needed for this question).

### 3.2 Arms (ALL fixed a priori; none added or dropped after the first score)
| arm | forward FRF | damping | role |
|---|---|---|---|
| **B0** | naive (analytic modal FRF on the cache grid) | flat ζ=1% | incumbent (= damping run's A0_enr; must REPRODUCE dev P1′ 0.1969 — pipeline cross-check) |
| **B1** | naive | physical per-mode survey ζ (~0.3%) | control (expected worst; reproduces the addendum's 0.186-class deficit) |
| **B2** | **window-matched** | physical per-mode survey ζ | **the claim** |
| **B3** | window-matched | flat ζ=1% | ablation: window alone (separates window from damping) |
| **B4** | window-matched | ERA 4-band ζ [0.099, 0.301, 0.542, 0.236]% | validation arm (labeled +X caveat) |
| **B5** | as B2 on `c06_tb_xface_enr` | physical survey ζ | does resolution-consistency change the SHAPE-edit conclusion? |

Physical-damping honesty gate carried: all ζ within [0.2%, 5%] except that per-mode SURVEY values below 0.2%
are allowed AS MEASURED (they are data, not fit — the gate constrains INFERRED damping; state this in the
assumptions ledger). NO fitting of damping or amplitude anywhere (markers `# NO-PER-MODE-LSQ`,
`# LOW-DIM-PHYSICAL-DAMPING-ONLY` carried; nothing here is fit beyond the reused θ_MAP + one global gain/fold).

### 3.3 Metrics and success criteria
Metrics IDENTICAL to the damping run (`quantity_contracts.md` there, reused verbatim + one addition):
**P1′** FDAC-aligned FRAC (primary), **P2′** |FRSF−1| amplitude error at matched peaks, **P3** raw log|H|
correlation. ADDITION — **P4 (peak-shape leg):** median absolute error of the log|H| peak HEIGHT at matched
peaks (dB), predicted vs measured, since window-consistency's first-order effect is peak height/width. Define
numerator/denominator/units in your `quantity_contracts.md` before coding.
- **S1 (resolution-consistency wins):** B2 beats B0 on dev P1′ by ≥ +0.03 absolute AND ≥ 2×fold-SE, AND vault
  P1′(B2) > vault P1′(B0). (Threshold +0.03 not +0.05: pre-registered here, justified because this is a fixed
  2-arm comparison with no winner's-curse search inflation — state this in `question_framing.md`.)
- **S2 (attribution):** decompose (B2−B0) into window-alone (B3−B0), damping-alone (B1−B0), and interaction
  (B2−B1−B3+B0). The claim "consistent processing lets physical damping be used correctly" requires the
  interaction + damping terms ≥ 1/2 of any S1 gain; window-alone dominating means "it's the window, damping
  still moot" — report whichever honestly.
- **S3 (mechanism confirmed even without a win):** independent of S1 — B2 ≥ B1 + 0.02 on dev P1′ (window-
  matching recovers most of the physical-ζ deficit) AND Gate W passes. This is the addendum's claim made
  formal; if S1 fails but S3 passes, the headline is "mechanism confirmed, no held-out advantage over the 1%
  convention" (a fine, publishable close-out).
- Anything less than S1+S2 = pre-registered claim falsified (YELLOW, loudly labeled); S3 graded separately.

## 4. Validation gates (BEFORE any science; checker-encoded; failures block science)
- **Gate W (window-model verification — the load-bearing new gate):** recompute the +X H1 (and coherence)
  from the RAW Test07 hits using the distillation parameters recovered from the netcg/upstream code and the
  cache metadata (N=122880 @ 250 kHz frame, n_hits averaging, the actual window — FIND the distiller source;
  if truly unrecoverable, fit frame/window type to match and LABEL it inferred). PASS = recomputed log|H|
  matches the stored `m_xpos_990x` cache to median |Δ| ≤ 0.05 dex per channel over 45–260 Hz on ≥ 80% of
  usable channels. Then apply the SAME operator to the model FRF — resolution-consistency by construction.
  Also report the window-equivalent apparent-ζ curve (≈1.5/(2·T·f)) against the scratch numbers.
  NOTE (Test07 vs Test01): the stored cache lists `Test01_modalhammer_990x_*` hits; Test07 is the SAME drive
  point re-downloaded (impact-hammer series). If hit-level differences prevent an exact cache match, match
  against a Test07-recomputed reference AND quantify Test01-vs-Test07 drive repeatability as a bonus result —
  do not silently swap targets; label which comparison Gate W actually passed on.
- **Gate K (kernel correctness, synthetic):** windowing a synthetic 1-DOF FRF of known ζ must reproduce the
  analytic apparent broadening (peak height reduction = |W|-convolution prediction) to ≤ 5%; an already-broad
  (ζ=5%) peak must be ~unchanged (kernel is narrow relative to it).
- **Gate R (reproduction):** B0 reproduces the damping run's A0_enr dev P1′ = 0.1969 to ±0.002, and B1
  reproduces the addendum's naive-physical deficit direction (B1 < B0). Guards against silent pipeline drift.
- Carried: exact-basis provenance (reuse the `_enr` spot-check JSONs), reused-source SHA integrity, no-LSQ
  grep, figures + legibility QA, runtime accounting, Result Status Standard.

## 5. Workspace, order, deliverables
1. `artifacts/reports/shocksat_resolution_consistent_scoring_<YYYYMMDD>/` with `code/ out/ logs/ figures/ data/`.
2. Gate files FIRST: `priority_deliverables.md`, `question_framing.md` (§3 verbatim), `quantity_contracts.md`
   (P1′/P2′/P3 reused by reference + P4 + the window operator defined precisely: frame T, window type, kernel,
   units), `assumptions_ledger.md` (survey-damping interpretation D7 carried; window params; leakage rule;
   sensitivity priorities), `decisions_log.md` (D0…). `REUSED_code.sha256`.
3. `check.py` + SHA-lock BEFORE science. Encode: gate files; Gates W/K/R; arm set fixed (exactly B0–B5 in the
   score log, no extras = no-search audit); no-LSQ grep; freeze-before-vault ordering + touched-once;
   fold-SE margin rule on S1; S2 decomposition present; figures+QA; runtime; statuses per Result Status
   Standard. IMMUTABLE during the trial. `bash run_all.sh` = one-command replay.
4. Gates W/K/R → 5. arms B0–B5 on dev → 6. freeze → vault once → 7. verdicts (S1/S2/S3) → 8. packet/figures.
   Heavy steps (Gate W raw-record processing is the only big one, ~GB-scale .mat loads) detached + resumable;
   pin BLAS for small dense math.
6. **Deliverables:** `packet.md` (method summary up front: the window operator with equations, arm table,
   S1/S2/S3 with numbers, the apparent-ζ curve, dev-vs-vault gaps incl. the second-read caveat, all caveats —
   ML/stats terms in plain English per AGENTS); `findings.md` (never stronger than checker output); figures
   (Tufte + lint, saved .py, run stamps): money figure (dev P1′ B0–B5 with the noise band), S2 decomposition
   bar, Gate W overlay (recomputed vs stored cache), apparent-ζ vs frequency curve with the survey/ERA values,
   one peak-zoom small-multiple (naive vs windowed vs measured at 2–3 representative peaks); `out/verdicts.json`,
   `out/gate_{W,K,R}.json`, `out/score_log.jsonl`, `VAULT_FREEZE.sha256`, `runtime.json`, `checker_report.json`.
   Continuity (END only): one `notes/runs.md` entry + one `docs/report/project_log.md` row, status verbatim.

## 6. Autonomy rules
- Resolve ambiguities yourself using this file's defaults; record every non-obvious resolution in
  `decisions_log.md` BEFORE acting. Blocked ≠ stopped: document the blocker + fallback, continue. Integrity
  rules (checker edit, vault ordering, adding arms after first score, presenting a fit as physical damping)
  have no fallback — withdraw, don't patch.
- Never claim success without checker output; a falsified pre-registered claim is a GOOD outcome. Do not let
  the vault's known "easy location" (+0.22–0.30 uniform gap in both prior runs) read as a win.
- Disk: extract further Test07 hits only if Gate W needs them (hits 002–004, ~245 MB each); clean extracted
  .mat files at the end (keep the zip; note what was cleaned in the packet).
- Crash/compaction recovery: re-read this card + your gate files + `out/score_log.jsonl`; restate state in one
  line in `decisions_log.md`; resume from partials.

---
### Lead's note to Andrew (delete before dispatch)
This is the closing experiment of the ShockSat damping arc: the scratch work showed the mechanism (window-
broadening masquerading as damping); this card tests, with pre-registered honesty, whether FIXING the
processing buys any held-out prediction — and even a clean "no, the 1% convention already absorbs it" (S3-only)
closes the arc with the mechanism formally verified (Gate W). Cheap: no eigensolves, no sampler, one raw-record
processing pass; the only real compute is Gate W's .mat handling. My honest prior: S3 passes, S1 is a coin flip
leaning fail (flat-1% is a decent stand-in for the apparent-ζ curve over one octave-ish of band). Either way,
after this the honest next moves are MPL (fresh headroom) or a longer-frame re-distillation — both new cards.
