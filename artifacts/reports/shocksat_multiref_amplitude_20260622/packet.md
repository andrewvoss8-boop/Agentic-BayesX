# Packet — Does MULTI-REFERENCE hammer data rescue the ShockSat L5 twin's held-out per-channel AMPLITUDE skill?

**One-line answer: NO — and we now know why, at two levels.** Adding multi-reference hammer drives (+Z, +Y, 900z)
does **not** raise the calibrated twin's held-out per-channel amplitude skill above climatology; it stays negative
(best **−0.11**, never crossing 0), while the **+0.93 modal-frequency skill is preserved**. The reason is mechanistic,
not a missing-effort failure: (iii, **earned**) the binding error in a *held-out* sensor's amplitude is that **sensor's
own mode-shape participation `φ_s`**, which is FEM-only and which multi-reference *cannot observe for a held-out
sensor* — proven by a labeled shape-oracle that reaches **+0.58** when the held-out sensor's shape is known; and (ii,
**data-quality**) the new IMPACT-hammer references are near the noise floor at the resonances (at-resonance coherence
~0.28–0.39 vs the modal hammer's 0.92), so they do not even help the *drive* side. The data we were missing
(multi-drive excitation) **breaks the drive÷damping confound on the drive side** but not the sensor-shape error that
actually limits held-out amplitude. **Status: YELLOW** — a rigorous, scoped, mechanism-backed HONEST NEGATIVE (the
direct test of the 2026-06-22 data-scope correction). Replay: `bash run_all.sh`; gate: `python3 check.py`.

Plain-English terms (defined on first use): **CRPS** = Continuous Ranked Probability Score, a proper score for a
probabilistic prediction (lower = better). **skill vs climatology** = `1 − CRPS_twin/CRPS_clim`, where **climatology**
is a no-skill baseline that predicts a held-out channel from the *population of observed channels*; skill > 0 means the
model carries information beyond the population. **coherence γ²(f)** (0–1) = the fraction of the response explained by
the measured force at frequency `f` (a data-quality / signal-to-noise measure). **held-out sensor** = a sensor whose
data is withheld from fitting, then predicted and scored — the honest trust test.

---

## 1. Method summary (what was inferred, what was fixed, what is new)
- **Structure/forward:** plain standalone 9-group ShockSat, reduced 74-DOF modal model `K(θ)=A_fix+Σ_g θ_g A_g`,
  copied **byte-identical** from Card F / Card A (integrity-locked). Resonant peak accelerance at sensor `s`, mode `k`,
  drive `d`: `|H_peak| ∝ φ_{s,k}·φ_{d,k}/ζ_k` (sensor participation × drive participation ÷ modal damping ζ).
- **Calibration:** the 9 stiffness multipliers `θ` are inferred from **measured modal FREQUENCIES** (Kiran Eq 25
  eigenvalue likelihood) by NUTS (the No-U-Turn HMC sampler), 4 chains, all-variable convergence gate. **Frequencies
  are reference-invariant** (a structure's natural frequencies don't depend on where you hit it), so `θ` and the +0.93
  frequency skill are identical before/after. Amplitude is then a **forward prediction** from the mode shapes `φ` + one
  **training-only global units-gain** (never peak-tuned — Card A `units_gain_forensics.md`).
- **THE CONFOUND (why this card exists):** at a *single* drive `d`, `φ_{d,k}` is one fixed number, so a wrong amplitude
  is explained equally by a wrong sensor shape `φ_{s,k}` or wrong damping `ζ_k` — confounded; the gain absorbs any
  channel-common scale. **Multi-reference break:** with ≥2 drives the ratio `|H_{s,k}(d1)|/|H_{s,k}(d2)| =
  φ_{d1,k}/φ_{d2,k}` is independent of the sensor and of ζ — over-determining the drive side.
- **New data (verified from files):** 4 references from the public NASA ShockSat1 delivery — +X (Test07, impact,
  drive (9,8,1)), +Z (Test08, impact, (9,8,0)), +Y (Test03, **modal hammer**, (8.5,9,1)), 900z (Test10, impact,
  (9,0.5,0) — far location). Force = Recorder116 (lb). Per-reference band-limited (45–260 Hz) multi-hit ensemble FRFs
  built with realfrf's exact windowing (force/exponential window, H1 estimator), impact-aligned per hit; common
  resolution **N=65536 (df 3.81 Hz)** fits 4 hits each for +Z/+Y/900z (the +X-matched N=200000 window excludes the
  late-impact modal hits) — a documented trade-off (coarser df, more window damping, but consistent + includes the
  clean modal reference).

## 2. Part A — the Card F value program reproduces EXACTLY (integrity anchor = GREEN)
Re-running the byte-identical copied code on +X-only (`out/partA_summary.json`):

| quantity | Card F documented | reproduced here |
|---|---|---|
| modal-FREQUENCY held-out CRPS-skill | +0.93 (2.10%→1.07%) | **+0.931** (2.10%→1.07%) |
| per-channel AMPLITUDE skill (non-hard, 3 seeds) | ≈ −1.0 (−0.76/−0.84/−1.40) | **−1.00** (−0.76/−0.84/−1.40) |
| Beck shape-FIELD lever (FEM→inferred) | −0.68 → −0.25 | **−0.680 → −0.252** (all 3 seeds converged) |

NUTS is deterministic on this platform → byte-faithful. This is the anchor for every "before/after" claim below.

## 3. Part B — the multi-reference test (the headline)
### 3.1 Data-quality diagnostic FIRST (coherence; `fig_coherence.png`, `out/coherence_by_reference.json`)
At equal averaging (4 hits, uncorrelated noise floor = 1/4 = 0.25), coherence **at the modal resonances** (where the
peak-amplitude QOI lives):

| reference | instrument | at-resonance median γ² | p90 | drive-point γ² |
|---|---|---|---|---|
| +Z (Test08) | impact | **0.28** (≈ noise floor) | 0.75 | 0.23 |
| 900z (Test10) | impact | **0.39** | 0.75 | 0.30 |
| +Y (Test03) | **modal** | **0.92** (clean) | 0.99 | 0.96 |

The documented +X "~0.07" is a **broadband 100–10 kHz** number (dominated by bands with no hammer energy); in-band the
**modal** hammer is coherent while the **impact** hammers sit near the noise floor at most resonances. **Data quality
splits by instrument**, not by direction.

### 3.2 Mechanism — the confound is NOT cleanly broken from this data (`fig_mechanism.png`, `out/drive_shape_ratio.json`)
The drive-shape-ratio test: does the measured `|H_s(d1)|/|H_s(d2)|` at each resonance recover the FEM
`|φ_{d1}|/|φ_{d2}|`, independent of sensor `s`? The FEM predicts large drive-ratio contrast (log-range 4–12), but the
measured ratios do **not** track it: **best pair corr 0.32** (+Z/900z), median 0.06, and the ratio is **not**
sensor-independent (sensor spread 0.34–0.95 in log). With the impact references near the noise floor and the one clean
reference a modal hammer (instrument mismatch), **the participation÷damping confound is not cleanly broken from this
data**.

### 3.3 Identifiability single vs multi (`fig_identifiability.png`, `out/multiref_identifiability.json`)
- **Stiffness θ (from frequencies):** multi-reference excites a larger mode union (**17 → 23** modes), but the
  identifiable θ directions above the realized discrepancy floor (σ_w≈6.9%) stay at **3** (all-modes ceiling = 4) —
  multi-reference adds modal **coverage**, not stiffness identifiability (floor-limited; consistent with Card F's
  "richer stiffness doesn't earn its complexity").
- **Amplitude confound:** single drive = 1 confounded combo/mode (`φ_d/ζ`); 4 drives = **3 separable drive-RATIOS**/mode
  (+1 residual per-mode gauge, the overall `φ_d↔ζ` scale). So multi-reference breaks the confound **on the drive side
  only** — it does not touch a held-out sensor's `φ_s`.

### 3.4 HEADLINE — held-out per-channel amplitude skill, BEFORE/AFTER (`fig_value_multiref.png`, `out/multiref_value.json`)
NON-HARD held-out sensors, 3 splits (seeds 0–2), **all calibrations converged** (R̂ 1.001–1.003, ESS ≥ 1414, 0
divergences). CRPS-skill vs climatology (>0 ⇒ beats guessing the population):

| prediction of the held-out sensor's peak |H| | CRPS-skill |
|---|---|
| BEFORE: +X, FEM drive amplitude `φ_d/ζ` (Card F, N=200000) | **−1.00** |
| BEFORE control: +X, FEM drive amplitude (same N=65536) | −1.69 |
| AFTER: +X, **multi-reference-measured** per-mode residue (operational-modal) | **−0.11** |
| AFTER: +Z measured residue / +Y(modal) / 900z | −0.40 / −0.46 / −0.09 |
| **ORACLE (held-out sensor's OWN shape known — labeled upper bound)** | **+0.58** |

Reading (the crux):
1. **Measuring the per-mode drive residue from the observed channels** (instead of FEM-assuming `φ_d/ζ`) lifts the
   held-out skill from −1.69 → **−0.11** at matched processing — a large gain, so the FEM drive amplitude/damping *was*
   part of the error. **But it cannot cross 0.**
2. **Adding more reference drives does NOT help:** +X-measured (−0.11) is best; +Z/+Y/900z are worse (the impact ones
   are noisier; the modal +Y carries an instrument-gain mismatch). So *multi-reference per se* adds nothing beyond a
   better use of the +X data.
3. **The shape-oracle (+0.58)** — using the held-out sensor's own measured modal residues — proves the residual deficit
   is the **held-out sensor's own shape `φ_s`**, which is FEM-only and which no amount of *drive* data can supply for a
   sensor you are holding out. The QOI *is* predictable if you knew the sensor shape; multi-reference is the wrong axis
   of information for it.
4. **Frequency skill preserved:** +0.931 before = +0.931 after (reference-invariant); multi-reference's frequency
   contribution is modal coverage (17→23), already floor-limited.

## 4. Three-tier status (honest)
- **GREEN:** Part A reproduces Card F exactly (integrity anchor); all multi-reference NUTS calibrations converged
  (R̂≤1.003, ESS≥1414, 0 div); frequency skill preserved (+0.931); figures + image-QA pass; one-command replay.
- **YELLOW (the scientific verdict — a documented, scoped NEGATIVE, not a failure):** multi-reference hammer data does
  **not** raise held-out per-channel amplitude skill above climatology (best −0.11, never >0). This is the *earned*,
  stronger version of the Card F amplitude finding: the limit is **model-form/QOI-structural** (the held-out sensor's
  own shape) plus a **data-quality** ceiling on the impact references — shown by mechanism + identifiability + the
  shape-oracle, not asserted. The modal-hammer caveat (Test03 +Y) and the few-hit-coherence bias are carried below.
- **RED:** none.

> Note on the checker: `check.py` reports its deliverable gates GREEN (reproduction exact, convergence met, figures
> present) — i.e., the *study executed correctly*. The **scientific verdict is the YELLOW negative above**; the
> `partB.amplitude` gate message states it plainly ("+X-only −1.00 → multi-ref −0.11 [still ≤0]"). The checker's
> GREEN-on-convergence tiering is more lenient than Card F's YELLOW-on-no-skill precedent — flagged to Andrew as a
> checker-standard question (§6), not self-applied (the checker is SHA-locked).

## 5. Assumptions / honesty ledger
- **Measured NASA ShockSat1 data throughout; no synthetic truth.** Drive coordinates from `TestLog_Tap` (the 990X/Y/Z
  / 900Z filename = the reliable impact DIRECTION; the "Face" text column is a known copy-paste artifact).
- **Test03 (+Y) is a MODAL hammer**, not the impact hammer of Test07/08/10 — different tip/force spectrum ⇒ a possible
  systematic gain. It is the cleanest data (coherence 0.92) but its held-out amplitude skill (−0.46) is the worst,
  consistent with an instrument-gain mismatch; every +Y conclusion is labeled. It is analysed per-reference (its own
  gain/residue), not blended into a single impact gain.
- **Few-hit coherence is upward-biased** (floor 1/n_hits); reported with n_hits and floor. The instrument split
  (impact ≈ floor vs modal ≈ 0.9) is a *fair* comparison at equal n=4 hits. A candidate alternate cause for the low
  impact coherence — impacts roving slightly across the source face between hits (documented for Test07) — would also
  lower multi-hit coherence; either cause ⇒ the impact multi-hit data is not clean enough to break the confound.
- **Resolution:** N=65536 (df 3.81 Hz) for the multi-reference set (fits 4 hits incl. the modal reference); the
  +X-matched N=200000 (df 1.25 Hz) is reported as the documented BEFORE and as a same-N FEM-forward control to isolate
  the df change from the method change.
- **Units-gain (Card A):** one training-only global/per-mode factor from OBSERVED channels; **no** per-held-out /
  per-draw / peak-tuned gain (that was the fragile Beck>L5 artifact). All methods still under-predict peaks ~2× = the
  FEM amplitude model-form ceiling.
- **The shape-ORACLE uses held-out data** (the held-out sensor's own residues) and is labeled an upper bound — it is a
  diagnostic of the achievable ceiling, never scored as a deliverable twin.
- **Inferred:** θ (9 stiffness multipliers) + σ_w² (NUTS, frequencies). **Measured-as-calibration:** per-mode complex
  drive residue R_{d,k} (operational-modal projection on observed channels). **Fixed:** FEM mode shapes for held-out
  sensors (the binding limit), ζ=1% nominal + window damping.
- **Scope of the damping/Beck levers (card item 1c):** addressed via the per-mode measured residue R_{d,k}, which *is*
  the data-driven `φ_d/ζ` factor separated from the FEM assumption (the FIM in §3.3 confirms multi-reference makes the
  drive ratios separable). The by-drive table (§3.4) is the answer to "do the ζ/drive levers become positive?" — they
  do not (best −0.09…−0.11, none > 0). A *literal* per-mode `damping_inference.py` re-run is expected to remain
  unidentified on the near-noise-floor impact references (the +X run already gave 0/9; coherence here is lower); and
  `modal_beck_ash.py` already infers its shape field from the `.ash` multi-reference modal SURVEY (not the impact FRF),
  so multi-reference *impact* data does not change it — its single-impact deficit (−0.25, Part A) is unchanged. Both
  are therefore consistent with, and subsumed by, the measured-residue + oracle result, not separately re-run.

## 6. Recommendation (SURFACE to Andrew — NOT self-applied)
- Report Card G as a **rigorous scoped NEGATIVE that completes and strengthens the Card F amplitude story**: the held-out
  per-channel single-impact amplitude limit is now shown (not argued) to be the **held-out sensor's own mode-shape**
  (oracle +0.58) plus an impact-hammer **data-quality** ceiling — multi-reference breaks the drive÷damping confound on
  the *drive* side but is the wrong lever for held-out amplitude. The **frequency twin remains trustworthy (+0.93)**.
- **The path that WOULD help held-out amplitude** is information about the held-out *sensor's* shape — denser shape
  coverage / a refined mesh (Card D) / a learned shape field that transfers — or cleaner excitation (the **modal
  hammer is markedly cleaner than the impact hammer**; pyroshock per the README is "cleaner") for the data-quality leg.
  Multi-reference is **not** that lever for this QOI.
- **Do NOT** claim the twin should replace the inherited FEM (no amplitude skill). **Do NOT** present the shape-oracle
  as an achievable twin (it uses held-out data).
- **Checker-standard question (your call):** should the amplitude gate be YELLOW-on-no-skill (Card F precedent) rather
  than GREEN-on-convergence? Plus the `docs/report/project_log.md` row and any durable-rule/sampler change await you.
## 7. Train/test splits, and the evolving-posterior FRF animation
- **Amplitude (the headline QOI): 3 train/test splits** (seeds 0–2), each a leave-40%-out over the **77 DR≥30-eligible
  channels → 46 observed / 31 held-out per split** (obs_frac 0.6). The *same 3 splits* serve Part A (FEM-forward, Beck)
  and Part B (multi-reference, all 4 drives), so before/after are identical splits (~93 held-out channel-predictions
  per method). **Frequency: 1 split** over the 27 matched modes (16 observed / 11 held-out) — the +0.93. (3 amplitude
  splits is Card-F-matched and modest; an ~25-split MC would tighten the error bars — available on request.)
- **`figures/evolving_posterior_frf_datasets.gif`** (the multi-reference animation; + `..._final.png`,
  `out/evolving_gif_datasets_meta.json`): the posterior FRF of a HELD-OUT sensor as the roving-hammer DATASETS are
  folded into the calibration — prior → +X(Test07) → +X+Z(Test08) → +X+Z+Y(Test03,modal) → +X+Z+Y+900z(Test10). Each
  dataset ADDS the modes it excites (no mode held out — the realistic workflow); a SENSOR is held out (the realistic
  predictive test). Shows measured + nominal FEM + evolving 95% band; title = datasets-in / #modes / peak CRPS-skill /
  coverage / R̂; legend = band-GRMS. **Honest finding it visualizes:** modes grow 0→16(+X)→20(+Z), then **+Y and 900z
  add no new well-excited modes** for this split, so the held-out skill is **FLAT** (0.78→0.77→0.77) — multi-reference
  buys frequency coverage that saturates after +X+Z, not held-out per-sensor amplitude. (Channel 108 is a selected
  well-covered case; the population-mean amplitude skill is −1.0 — the GIF illustrates the dataset-folding mechanism,
  not typical amplitude success.)
- **`figures/evolving_posterior_frf.gif`** (secondary): the same held-out sensor as the inference accumulates more
  observed modes within +X (prior → all modes) — shows the peaks snapping into place as θ calibrates while the
  amplitude band stays wide. Superseded as the headline animation by the dataset version above.
```
Replay: bash run_all.sh   |   Gate: python3 check.py   |   Figures: figures/fig_{coherence,mechanism,value_multiref,identifiability}.png + evolving_posterior_frf.gif
```
