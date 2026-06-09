# ShockSat — Opus Continuation Packet

Lead/runner: Claude Code (Opus) · Date: 2026-06-09
Workspace: `artifacts/reports/shocksat_opus_20260609/`
Replay: `bash artifacts/reports/shocksat_opus_20260609/run_all.sh`
Builds on (does not modify): Codex run `artifacts/reports/shocksat_statfem_runner_20260609/`

## What this run is
A focused correction + extension of the Codex ShockSat foundation. I kept all of
Codex's honest provenance/inventory/launch-definition work and fixed the one
quantitative claim that was driving a wrong conclusion: that the Test07 impact
hammer data has "median coherence ~0.07" and is "not likelihood-ready."

Full review: [review_of_codex_run.md](review_of_codex_run.md).

## Method summary (first-pass, plain English)
- **Data**: NASA/NESC ShockSat1 public release, `Test07_ImpactHammer_990x` — a
  modal hammer (impact) test, +X face. 4 hammer hits, force channel 116 (lbf),
  response accelerometers ch1/50/87 (g), 250,000 samples/s, ~1 s/record.
- **Quantity**: accelerance FRF = acceleration response / input force (g/lbf),
  estimated H1 = `<F*Y>/<F*F>`; coherence `γ² = |<F*Y>|²/(<F*F><Y*Y>)`.
- **Likelihood**: NONE. No StatFEM posterior, no NUTS/HMC. All outputs are
  labeled diagnostic. The FRF is not yet accepted as a likelihood input.
- **Inferred variables**: none. **Fixed**: sensor cal from workbook; fs from MAT
  `dXstep`. **Not inferred**: discrepancy, noise, forcing, build/test variability.

## The bug I fixed
Codex computed coherence with Welch segmenting (`nperseg=32768`) **inside one ~1 s
impact transient**. The hammer pulse fills one short window; the other ~14 Welch
segments are free-decay/noise, so coherence collapses to ~0.07. That is a method
artifact. It also evaluated the **100–10,000 Hz shock band**, but a modal hammer
test correlates against NASA's **SOL 111 free-free FRF, 10–400 Hz**.

Correct impact processing (this run): force window + exponential response window,
one FFT per hit, ensemble H1/coherence **across the 4 hits**, evaluated in 10–400 Hz.

## Headline result (artifact-backed)
`opus_frf_summary.json`, fig `figures/opus_coherence_method_compare_ch1.png`:

| channel | Method A median coh (Codex, per-transient Welch) | Method B median coh (Opus ensemble) | Method B **max** coh (near resonance) |
|---|---:|---:|---:|
| ch1 (grid 9900001, X)  | ~0.056 | 0.307 | **0.887** |
| ch50 (grid 9900016, X) | ~0.049 | 0.236 | **0.828** |
| ch87 (grid 9900028, X) | ~0.056 | 0.387 | **0.838** |

**Interpretation**: the data carry genuine coherent modal information. Near
resonances, corrected coherence reaches ~0.83–0.89. The median stays moderate
(0.24–0.39) because there are only 4 hits at slightly different impact points
(TestLog y = 8.0–8.75, z = 0–1), so between-mode coherence is weak — this is an
honest few-hit limitation, **not** "the data are unusable." The honest few-hit
quality metric is per-hit FRF **repeatability**
([figures/opus_frf_repeatability_ch1.png](figures/opus_frf_repeatability_ch1.png)).

## FEM vs test (resonance-frequency alignment, 10–400 Hz)
I parsed NASA's FEM reference `SOL_111_Free_Free_Force_11101X.pch` (acceleration
FRF, 76 response points) and compared resonance peak frequencies — which are
global for a free-free structure, so they are comparable **before** exact
point/unit matching. Fig: [figures/opus_fem_vs_test_peaks.png](figures/opus_fem_vs_test_peaks.png).

- FEM peaks (Hz): 54.6, 73.5, 88.0, 135.9, 154.5, 184.0, 211.1, 231.0, 252.1, 270.1, 311.9, 373.8
- Test ch1 peaks (Hz): 51.9, 75.9, 119.8, 139.8, 163.8, 219.7, 227.7, 243.7, 279.6, 303.6, 351.5, 367.5

Partial alignment at low modes (FEM 54.6≈test 51.9; 73.5≈75.9; 135.9≈139.8), with
clear divergences higher up. **This is the real-data correlation surface** a
StatFEM update would interrogate — exactly what the project vision needs.

## Caveats / limitations (honest)
- 4 hits, slightly different impact points → weak ensemble-coherence statistics.
- Exponential window adds known artificial damping (lowers Q); fine for peak
  location, not for damping extraction.
- Frequency resolution ≈ 4 Hz (frame limited by latest impact at 0.75 s) merges
  close modes; refine frame/select same-point repeats for a final FRF.
- FEM↔test overlay is **resonance-frequency only**: FEM point 1101 ≠ test grid
  9900001, and the SOL 111 force-amplitude unit normalization is still OPEN, so no
  magnitude likelihood is claimed.
- The Codex `nasa_correlation_frf_assets.md` PNG counts come from the archive
  *listing*; no comparison PNGs are extracted. The `.pch` is the usable reference.

## What this proves / does not prove
- **Proves**: Codex's "low coherence ~0.07 / not usable" verdict was largely a
  processing+band artifact; corrected modal-band processing shows near-resonance
  coherence ~0.83–0.89 and a real FEM-vs-test correlation surface in 10–400 Hz.
- **Does not prove**: a calibrated StatFEM twin, active NUTS/HMC, validated
  FEM–test magnitude agreement, or FRF likelihood readiness.

## Normalization remedy (begun) — it is a transfer-path problem, not a scale factor
Full writeup: [opus_normalization_findings.md](opus_normalization_findings.md);
data: `opus_point_reconcile.json` (`scripts/opus_point_reconcile.py`).

I checked whether the each-curve self-normalization can be replaced by a real g/lbf
overlay. The FEM `.pch` **is** already an accelerance (SOL111 applies a flat unit
force: `TABLED1 1001 = 1.0`, `FORCE … 1.0`). But parsing the NASTRAN GRID
coordinates shows the extracted FEM FRF and the Test07 tap FRF are **different
transfer paths**:
- SOL111 drives at grid 11101 = (8.94, −0.50, 2.77) in; nearest hammer impact is
  **2.78 in** away → input point does not match.
- Tap accelerometers (9900xxx) are **~17 in** from any SOL111 response grid
  (1101–7105, the *modal-test* sensor set) → output point does not match.

So a magnitude overlay of this `.pch` vs Test07 is **not achievable from the
extracted files** and I did not fabricate one. The correct remedy is to put the
FEM-vs-test bridge on **modal correlation (MAC + frequencies)** using the
consistent 1101–7105 grid set (`Test_Mode_Shapes/`, `TAM_FF/FB`) — point-consistent
and unit-robust — which is also the right StatFEM v1 observation layer.

## Recommended next path (supports project vision)
1. **Build the StatFEM v1 around the 10–400 Hz free-free modal correlation**
   (FEM SOL111 vs measured hammer FRF / test modes via TAM + MAC), holding the
   **pyro shock (100–10,000 Hz, unknown forcing, force-limiting load QOI)** as the
   downstream held-out validation surface — the project's real novelty axis.
2. Reconcile the point/grid map (test 9900xxx ↔ FEM 1101–7105 ↔ SOL111 force
   11101/11110) by physical XYZ coordinates; read SOL111 force amplitude from the
   `.bdf` to fix the g/lbf normalization → enables a real magnitude overlay.
3. Select same-impact-point repeats (or roving-hammer set) and refine the frame for
   a clean modal FRF before any likelihood.

## Files
- `review_of_codex_run.md` — full review of the Codex run.
- `scripts/opus_hammer_frf.py` — corrected FRF + FEM compare (this run).
- `scripts/check_opus.py` — checker. `checker_report.json` — results.
- `opus_frf_summary.json`, `opus_frf_estimates.npz` — numbers + spectra.
- `figures/` — repeatability, coherence-method-compare, FEM-vs-test.
- `runtime.json`, `logs/run_log.txt`.
