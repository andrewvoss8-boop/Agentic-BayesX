# Multi-reference ShockSat exploration — findings (2026-06-23, read-only, no sampler/FEM)

Data: newly pulled Test01 (+X), Test02 (+Z), Test04 (+XY) ModalHammer at node 990, 6 hits each, 250 kSps,
1 s pre-triggered records (impact lands at ~125,009 samples = 500 ms → ~0.5 s ring-down). Processing replicates
the Card G window (force box ±2 ms + exponential response window, impact-aligned single FFT, multi-hit H1/coherence)
with N reduced to 122,880 (0.49 s, df≈2.03 Hz) to fit the pre-triggered modal records. Script: `code/explore_multiref.py`,
`out/explore_summary.json`. Test03/08/10 raws were deleted after Card G (caches only); Test07 (1 hit) retained.

## 1. The new modal data is CLEAN and a large quality upgrade (GREEN)
| Ref | hits | peakF (lbf) | force −3 dB | coh median | coh 90th | coh at peaks | modal peaks 45–260 Hz |
|---|---|---|---|---|---|---|---|
| Test01 +X modal | 6 | 627 | 804 Hz | 0.931 | 0.985 | 0.97 | 75.3, 138.3, 162.8, 189.2, 199.4, 254.3 |
| Test02 +Z modal | 6 | 734 | 2991 Hz | 0.707 | 0.980 | 0.90 | 99.7, 126.1, 136.3, 172.9, 189.2, 197.3, 234.0, 254.3 |
| Test04 +XY modal | 6 | 805 | 3109 Hz | 0.806 | 0.986 | 0.93 | 75.3, 99.7, 122.1, 136.3, 189.2, 197.3, 234.0, 254.3 |
| Test07 +X impact (old ref) | 1 | 1.28 | 279 Hz | (degenerate, n=1) | — | — | 120.0, 240.1 (poor) |

- Multi-HIT coherence (averaging axis = across the 6 impacts, AGENTS Discretization Gate) is 0.71–0.93 median,
  0.90–0.97 **at the resonance peaks**, well above the uncorrelated floor 1/6 = 0.167. The lower +Z median is the
  expected coherence dip at antiresonances (low response), not a quality problem (at-peaks 0.90).
- The modal hammer drives ~500× harder (500–1080 lbf vs the 1.28 lbf Test07 tap) and excites the full 45–260 Hz band
  (force rolloff ≥ 800 Hz). The original +X reference (Test07) had within-hit coherence ~0.07 (a noise-dominated tap);
  the +X **modal** survey (Test01) is clean (~0.93/0.97). This is a direct upgrade of the very reference the headline
  ShockSat twin was built on.
- Multi-direction modal coverage: union of X/Z/XY peaks ≈ {75, 100, 122, 126, 136, 138, 163, 172, 189, 197/199, 234, 254}
  Hz — different drives light up different modes ⇒ genuinely more identifiable modes than the single +X reference.

## 2. OPEN / MUST-RESOLVE-BEFORE-BUILD: absolute units/gain reconciliation (YELLOW)
The +X **modal** (Test01) and +X **impact** (Test07) FRFs, same node-990 +X drive, do NOT agree:
- per-channel log|H| correlation ≈ **0.00** (3/111 channels > 0.5);
- band-peak |H| median **0.283 g/lbf (modal)** vs **18.3 g/lbf (impact)** = **−36 dB**; median-level offset −44 dB.

Most-likely benign explanation (NOT yet proven): (a) Test07 was a noise-dominated 1.3 lbf tap (coh ~0.07) so it
disagrees with everything; and (b) the ~36–44 dB offset is close to the **known ~×100 (+40 dB) global units-gain**
that the Card A/`realfrf` pipeline already absorbs (D4, "~x100 mass-norm/g constant"). The modal data is internally
self-consistent (40 dB dynamic range, deep antiresonances 0.002 g/lbf, sharp peaks). BUT a 36 dB peak discrepancy is
large enough that the **absolute units/gain convention between the modal `.mat` and the existing pipeline MUST be
reconciled before combining** — the headline twin's gain handling was built around Test07.

## 3. Implications for the PSD-envelope twin (do not over-claim)
- The new data is the real width lever the prior cards lacked: clean multi-hit (beats single-hit damping noise),
  multi-direction (breaks participation÷damping confound), and it cleans the +X reference.
- It does NOT by itself overturn Card G's finding that the binding limit for held-out per-channel AMPLITUDE is the
  held-out SENSOR's own mode shape φ_s (FEM-only) — multi-reference fixes the DRIVE side, not the held-out node.
  The envelope-GRMS-vs-FEM+6dB reframe is the part that can cash in the (real, strong) frequency skill + damping;
  the validity probe still decides whether it wins.
- The fact that the prior +X amplitude headline rested on a noise-dominated tap is a reason for cautious optimism
  (clean modal +X may tell a different amplitude story) AND a reason to re-examine the prior +X conclusions.

## 2b. UNITS QUESTION RESOLVED via the TestLog (2026-06-23, Andrew's pointer) — NOT a units bug (GREEN)
`ShockSat1_Instrumentation_and_TestLog_Simplified_for_Delivery_20220525.xlsx`:
- Accel channels = 6 sensor types with PER-CHANNEL cal (PCB 350B01/B41/B43/B44/356A04, Dytran; 0.044–1.137 mV/g,
  ranges 5/10/100 kg). The same per-channel cal applies to modal and impact for a given channel ⇒ it CANCELS in the
  per-channel modal-vs-impact comparison, so the −36 dB gap is NOT a cal mismatch.
- Force channel = location 37 / ch 109, a single **Dytran 5850B** (cal 1.03). One force instrument.
- ⇒ The modal-vs-impact disagreement is a DATA-QUALITY (SNR) effect: a ~1.3 lbf impact tap (Test07) is far too weak
  for 100k-g shock accels (0.045 mV/g) → SNR-limited (only the strongest mode ~120 Hz pokes through; coh 0.07);
  the 500–1080 lbf MODAL hammer is the correct instrument and rings in clean (coh 0.9+). The headline twin's +X
  amplitude rested on noise-limited tap data; the modal data is the right basis.

## 2c. The 6 hits/test are a ROVING cluster, not 6 repeats (handle per-hit for amplitude/shape)
TestLog_Tap impact points per test (filename direction is reliable; "Face" text is a known copy-paste artifact):
- Test01 +X @ node 990 (y≈8): 6 hits roving over (9, 7.25–8.0, 0.5–1.0)
- Test02 +Z @ node 990: 6 hits over (9, 7.5–8.0, 0.0)
- Test04 +XY @ node 990 corner: 6 hits over (9, 9, 1.0–1.5)
- Test06 +Z @ node 900 (y≈0): 6 hits over (9, −0.5–0.25, 0.0)
H1 ensemble over a roving cluster ≈ a spatial-average FRF over that face (OK for global poles/frequencies; for
amplitude/shape, treat each hit as its own drive point).

## Clean modal multi-reference set (recommended basis)
Test01 (+X, node 990) · Test02 (+Z, node 990) · Test04 (+XY, node 990) · Test06 (+Z, node 900) — TWO drive
LOCATIONS (990 at y≈8, 900 at y≈0) × directions X/Z/XY/Z, all clean modal-hammer, consistent force instrument.
Drop the SNR-limited impact taps (Test07/08/10) from the amplitude basis (keep only if a cross-check is wanted).

## Pre-build task list (gating)
1. Reconcile absolute units/gain: dig the per-channel sensitivity/units out of the `.mat` Recorder structs (the
   `name/unit` probe came back '?'; the fields are nested elsewhere) and confirm g & lbf scaling vs `realfrf`.
2. Reconcile modal peak frequencies vs the `.ash` measured modes / Card A list (df=2 Hz is coarse; note half-power
   bandwidth of a 1% mode near 100 Hz ≈ 2 Hz ⇒ damping is marginally resolved — a discretization-gate item).
3. Decide drive-row mapping for the +XY combined drive (two-component) for any forward use.
