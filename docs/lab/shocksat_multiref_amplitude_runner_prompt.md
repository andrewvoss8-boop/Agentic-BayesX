# Runner prompt — Card G: does MULTI-REFERENCE hammer data break the participation÷damping confound and improve the ShockSat L5 twin's held-out AMPLITUDE skill?

You are a **runner agent** in **Agentic BayesX** (structural-FEM / StatFEM / Bayesian-model-updating). Lead = Claude Code;
human = **Andrew Voss**; advisor objective (Ilias Bilionis): *"evaluate the StatFEM approach, identify its gaps, suggest
improvements."* Build for correctness, reproducibility, traceability, continuity. Plain English on ML/stats (define every
term/acronym/symbol with units on first use, lead with intuition + a concrete example); structural-dynamics terms (FRF,
mode shape, participation, modal damping ζ, accelerance, MAC) used directly. **Never claim an improvement without the
held-out score + the checker/figure that proves it, and scope every claim to exactly what you tested. A rigorous, scoped
HONEST NEGATIVE is equally valuable.**

## 0. RE-GROUND FIRST (a new session knows only the files — read before acting)
Read `AGENTS.md` (EVERY gate binds — especially: NUTS/HMC sampler rule, all-variable convergence gate, Modal/Eigenproblem
Identifiability gate, Plot/Tufte gate, Verification gate, Result-Status three-tier, Compute/detached-launch gate, Done
Criteria). Then read, in order:
1. **The experiments you must reproduce then improve — Card F value program**:
   `artifacts/reports/shocksat_modelclass_L5_20260619/` — `packet.md` (READ §2 value table, §3 "every lever run not
   argued", §3a corrections, and §4 — note §4 now carries a **2026-06-22 DATA-SCOPE CORRECTION**), `priority_deliverables.md`,
   `decisions_log.md`, `checker_twin_report.json` (the documented headline), and the code in `code/` + caches in `data/`.
2. **Why this card exists** (the data-scope correction): `notes/lessons-learned.md` (2026-06-22 entry), the lead
   `notes/memory.md` CURRENT STATE (2026-06-22 / 22b), and `artifacts/reports/shocksat_statfem_runner_20260609/source_manifest.md`.
3. **The L5 method + held-out-QOI machinery — Card A**: `artifacts/reports/statfem_real_validation_20260617/packet.md`
   (§1 method, §2 verdict) + `units_gain_forensics.md` (the global units-gain — CRITICAL for why damping was degenerate).
Restate **goal / last decision / next action / open ambiguities** in one line before acting. If anything is missing or
contradictory, ask the lead/Andrew before building.

## 1. WHAT IS ALREADY ESTABLISHED — do NOT re-derive
- **The Card F result you must DUPLICATE first** (`checker_twin_report.json`, value program, single +X drive, MEASURED data):
  | quantity | Card F result (the number to reproduce) |
  |---|---|
  | modal-FREQUENCY held-out CRPS-skill vs climatology | **+0.93**; updating halves freq err **2.10% → 1.07%** |
  | per-channel AMPLITUDE (peak) skill vs climatology | **≈ −1.00** (no skill; worse than guessing the population) |
  | amplitude lever: fitted global ζ-scale | band skill **−1.57 → −0.60** (never positive) |
  | amplitude lever: Beck shape-FIELD inference (L8b) | CRPS-skill **−0.68 → −0.25**, interval ~43% sharper, cov→0.97 (still <0) |
  | amplitude lever: joint topology release | peak skill −0.80→−0.66 (no help) |
  - "skill vs climatology" = `1 − CRPS_twin/CRPS_clim`; **climatology** = a no-skill baseline that predicts a held-out
    channel from the *population of observed measured channels* (skill>0 ⇒ the model carries information beyond the
    population). "CRPS" = Continuous Ranked Probability Score (proper score for a predictive distribution; lower=better).
- **THE CONFOUND (the whole reason for this card).** Resonant peak amplitude at sensor `s`, mode `k`, driven at node `d`:
  `|H_peak| ∝ φ_{s,k} · φ_{d,k} / ζ_k` (participation at the sensor × participation at the drive ÷ modal damping). At a
  **single drive** `d`, `φ_{d,k}` is one fixed number, so a wrong amplitude is explained equally by wrong shape `φ_{s,k}`
  or wrong damping `ζ_k` — **they are confounded**, and a global units-gain absorbs any channel-common scale (see Card A
  `units_gain_forensics.md`: damping is per-mode/channel-common ⇒ degenerate with the gain ⇒ fixing it small didn't help).
- **WHY MULTI-REFERENCE BREAKS IT (your mechanism).** With ≥2 drives `d1, d2` exciting the same mode, the **ratio**
  `|H_{s,k}(d1)| / |H_{s,k}(d2)| = φ_{d1,k} / φ_{d2,k}` is **independent of the sensor `s` and of ζ_k** — a pure
  drive-shape ratio. So multiple references over-determine ζ_k (reference-invariant) and separate it from participation.
  This is exactly the lever Card F / Card E / `lessons-learned #6` named as the cure ("multi-reference / roving
  excitation, not a fancier model") — and which the prior runs never had in raw form. **This card supplies it.**

## 2. THE DATA YOU NOW HAVE (verify every claim from the files yourself)
All from the PUBLIC NASA ShockSat1 delivery; MEASURED, no synthetic truth. 128 recorders, **250 kSps, 250001 samples,
1.00 s**, 127 accels in `g`, **hammer force = Recorder116 ('Ch D20', units lb)** for the IMPACT-hammer tests (VERIFY for
the modal-hammer test — it may differ). Channel→FEM-grid map = `data/channel_map.csv`. Drive coordinates per test are in
`shocksat_statfem_runner_20260609/extracted/Instrumentation_and_TestLog/`.

| Test | Drive | Instrument | Location | Hits available | State on disk |
|---|---|---|---|---|---|
| Test07 | **+X** (990x) | Impact | source (≈9,9,0) | 001–004 | `…/extracted/Test07_ImpactHammer_990x/` (+ baseline cache `data/measured_frf_cache.npz`) |
| Test08 | **+Z** (990z) | Impact | source | 002,004,005,006,007 | `…/extracted/Test08_ImpactHammer_990z/` (extracted) |
| Test10 | **Z @ node 900** (900z) | Impact | **different node** | 001–006 | `Test10_ImpactHammer_900z.zip` (root) |
| Test03 | **+Y** (990y) | **MODAL** | source | 001,004,005,006 | `Test03_ModalHammer_990y.zip` (root) |

- **+X, +Z, +Y at the source span three drive DIRECTIONS** (orthogonal-ish `φ_d`); **900z adds a different drive LOCATION**
  (larger `φ_d` contrast). +X+Z (same instrument, same node) is the cleanest minimal pair to break the confound.
- **CAVEAT (state on every Test03 conclusion):** Test03 is a MODAL hammer, not the IMPACT hammer used for Test07/08/10 —
  a different tip/force spectrum ⇒ a possible systematic gain. Handle (per-test gain, or analyse it separately) and label.
- **⚠ DISK IS CRITICAL: ~3.9 GB free.** Do NOT extract all hits or keep the zips. For each test: extract **2–3 good hits
  only**, build a **BAND-LIMITED** per-reference FRF cache (the analysis band is ~45–260 Hz, df≈1.25 Hz ⇒ ~170 lines, KB-MB,
  not the 263 MB full-resolution cache), then **delete the raw .mat and the zip**. Keep total new footprint < ~1 GB.

## 3. PART A — DUPLICATE the Card F value-program results (integrity + repro baseline; do FIRST)
Stand up the workspace, **COPY (never edit) the Card F `code/` byte-identical** (integrity gate), and **reproduce the
single-+X numbers in §1** from the existing `data/measured_frf_cache.npz` + `data/measured_modes.npz`:
- Re-run `freq_value.py`/`value_eval.py` (freq skill ≈ +0.93; amplitude skill ≈ −1.0) and at least the `modal_beck_ash.py`
  + `shapefield_lever.py` lever (−0.68→−0.25). Confirm your reproduction matches `out/value_eval_seed0*.json`,
  `freq_value_seed00.json`, `shapefield_lever.json`, `checker_twin_report.json` to tolerance.
- **Integrity (run, do NOT pause):** reproduce the Card F headline from the copied code on +X-only FIRST. If it reproduces,
  the integrity gate is GREEN and is the anchor for any "improved" claim. If it does NOT reproduce, mark the integrity gate
  RED, flag it prominently in `packet.md`, and **CONTINUE into Part B (Andrew authorized the full autonomous run)** — but NO
  Part-B "improvement" may be tagged GREEN while Part A is RED. (This is the literal "duplicate the results" deliverable.)

## 4. PART B — ADD the multi-reference data and measure the improvement (the task)
0. **DATA-QUALITY DIAGNOSTIC FIRST (cheap; run it, do NOT stop on it).** Build per-reference FRFs (force=Rec116; reuse
   `realfrf.py` windowing / H1 / `measured_zeta_w` so processing is identical to +X) and report **coherence** at the drive
   point and the 8 hard accels for +Y/+Z/900z → `out/coherence_by_reference.json`. The +X tap coherence was **~0.07**
   (`hammer_frf_subset_manifest.json`). This number does NOT abort the run — it **contextualises** the outcome and is carried
   into every amplitude conclusion: if the new references are also ~0.07 and amplitude skill stays ≤0, the verdict is a
   **data-quality ceiling** (honest negative → pyro is the path); if coherence is decent and skill stays ≤0, the limit is
   model-form/QOI-intrinsic; if skill rises, the confound break worked. Proceed into Part B regardless.
1. **Re-run the SAME methods with multi-reference calibration** (everything else byte-identical to Part A):
   (a) **L5 modal-FREQUENCY twin** — confirm it still gives +0.93 (multi-ref shouldn't hurt frequencies; report it).
   (b) **Held-out AMPLITUDE QOI vs climatology** — the headline. Calibrate using ≥2 references and predict a held-out
       sensor's peak-|H| / band-GRMS; score CRPS-skill / interval score / coverage / z-std. **Does amplitude skill rise
       from ≈ −1.0 toward / above 0?** Report the before(+X-only)/after(multi-ref) table across the SAME seeds/splits.
   (c) **Damping inference** (`damping_inference.py`) and **Beck shape-field** (`modal_beck_ash.py` / `shapefield_lever.py`)
       re-run with the references that now separate participation from ζ — do the levers that were ≤0 on +X become positive?
2. **MECHANISM figure (the proof):** show the per-mode (participation `φ_{s,k}`, damping `ζ_k`) posterior collapse from the
   single-reference RIDGE to a multi-reference POINT, and/or the drive-shape ratio `|H(d1)|/|H(d2)|` recovering `φ_d` ratios.
   Tie every "improves / doesn't" claim to this mechanism, not to a bare score move.
3. **Identifiability gate, re-run WITH multi-reference (AGENTS Modal-Identifiability):** the FIM / strain-energy view that
   on single-impact gave only ~4/9 stiffness directions and confounded amplitude — how many directions now clear the
   realized discrepancy floor? Show the before/after. (This earns the Card E/F "multi-reference is the fix" pre-test claim.)

## 5. GATES & HONESTY (AGENTS binds; Card D/E/F over-claim lessons)
- **NUTS/HMC sampler rule + convergence gate:** all-variable max R̂≤1.05, min ESS≥200, div-frac<2% over EVERY variable, or
  the arm is labeled YELLOW not-yet-converged (never "NUTS active" just because a sampler ran). Escalate to TMCMC if multimodal.
- **Re-pairing-robust** mode metrics (tracked continuation / cross-orthogonality), NEVER greedy best-MAC (Card D D12 artifact).
- **Three-tier** every conclusion (GREEN proven / YELLOW limited / RED). A result is only as strong as the held-out score
  supports. Do NOT say "model-form limit" when you mean "this parameterization/observable is exhausted." If amplitude skill
  is STILL <0 after the confound is provably broken, that is a STRONGER, now-EARNED version of the Card F finding (the limit
  is genuinely model-form/QOI-intrinsic, not data) — report it as such, with the mechanism evidence.
- Carry the **units-gain** caveat (Card A): score under a units-honest fixed gain or one training-only global gain identical
  across methods, NEVER a per-held-out/per-draw peak-tuned gain (that was the fragile Beck>L5 artifact).

## 6. CONSTRAINTS / COMPUTE / WORKSPACE
- **Plain standalone 9-group ShockSat ONLY** (no coupled tray). **COPY-never-edit** the inherited Card F `code/` + `data/`;
  apply new processing on copies. Validate Part A (the BEFORE) before any multi-ref claim.
- **Compute:** pin `OMP_NUM_THREADS=1`, float64; long eigensolves / NUTS / MC **detached + resumable** (reduced 74-DOF model
  ~24 ms/eigh — prototype there). Record `runtime.json` (active vs elapsed). One-command replay (`run_all.sh`) + manifest.
- **Disk hygiene (3.9 GB):** extract 2–3 hits/test → band-limited cache → delete raw .mat + zips. Report footprint in runtime.json.
- **check.py FIRST** (immutable, SHA-locked, baseline RED=not-done; mirror the Card F `check_twin.py` 3-tier+lock pattern).
  Figures via saved `.py` + tufte-lint + image-QA (`out/image_qa.json`).
- Write `decisions_log.md` (one-line state + D0 inherited constraints + the data-scope rationale), `priority_deliverables.md`,
  `references_reviewed.md` from the START. Any human clarification → write to `decisions_log.md` before continuing.
- **COMPUTE AUTONOMY (Andrew, 2026-06-22): run the FULL pipeline end-to-end with NO human checkpoint** — Part A (reproduce)
  → coherence diagnostic → Part B multi-reference **NUTS MC at the full Card-F-matched split/seed count** — detached,
  resumable, overnight OK. **Do NOT pause for compute approval.** Launch every long stage detached (the full-order solve /
  the multi-hour MC) so a tool timeout never kills it; checkpoint partial results so a restart resumes. Record `runtime.json`
  (active vs elapsed, + disk footprint).
- **STILL SURFACE (do NOT self-apply) — these are NOT compute, so autonomy does not cover them:** any durable-rule / checker
  / sampler-standard change; any claim the twin should REPLACE the inherited FEM; the `docs/report/project_log.md` row.

## 7. WIN CONDITION
A credible, auditable BEFORE(+X single-reference)/AFTER(multi-reference) comparison that answers, with the mechanism +
held-out score + figure that prove it: **does adding multi-reference hammer data raise the ShockSat twin's held-out
per-channel AMPLITUDE skill vs climatology above the Card F ≈ −1.0 (ideally above 0), while preserving the +0.93 frequency
skill** — gated by coherence (data quality), the NUTS convergence gate, and the identifiability gate. Equally valid wins:
(i) "YES — multi-reference breaks the confound and amplitude becomes skillful (here is the score + the φ/ζ posterior
collapse)"; (ii) "NO, for a data-quality reason — impact-hammer coherence is too low (here is the evidence; pyro is next)";
(iii) "NO, even with the confound provably broken — so the Card F amplitude limit is genuinely model-form/QOI-intrinsic, now
EARNED (here is the FIM + the still-negative skill)." The deliverable is the honest, scoped answer to whether the data we
were missing actually rescues the digital twin — the direct test of the 2026-06-22 data-scope correction.

## 8. WORKSPACE
Create `artifacts/reports/shocksat_multiref_amplitude_20260622/`. COPY-reuse (never edit in place) from
`shocksat_modelclass_L5_20260619/code/` and `data/`. Hands OFF every Card A/B/D/E/F workspace (copy, don't edit).
First file = `check.py` (locked, baseline RED). Restate goal/last-decision/next-action/open-ambiguities in `decisions_log.md`
before acting.
