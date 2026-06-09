# Remedying the FEM-vs-Test FRF Normalization — Findings

Date: 2026-06-09 · Script: `scripts/opus_point_reconcile.py` · Data: `opus_point_reconcile.json`

## The question
Replace the each-curve-peak self-normalization in `figures/opus_fem_vs_test_peaks.png`
with a real, units-consistent magnitude overlay (g/lbf, FEM vs measured).

## What it takes (three conditions)
1. **FEM force amplitude/units.** SOL111 applies a **flat unit force**:
   `TABLED1 1001 = 1.0` over 0–400 Hz, `FORCE 2001 11101 0 1.0 1.0 0. 0.` So the `.pch`
   acceleration (already in g) **is an accelerance**: g per 1.0 applied force unit. Units
   assumed lbf (consistent with inch geometry; confirm via model PARAM/material). → **MET.**
2. **Matched input (drive) point.** → **NOT met for Test07.**
3. **Matched output point + axis.** → **NOT met for the tap channels.**

## Evidence (parsed NASTRAN GRID coords, inches)
- SOL111 force points: `11101 = (8.94, -0.50, 2.77)` (+X), `11110 = (0.00, -8.94, 2.77)` (+Y).
- Nearest TestLog hammer impact to `11101` is **2.78 in** away (hammer Z≈0 vs FEM Z=2.77);
  to `11110` is **12.6 in** away. **No extracted hammer test drives at the SOL111 point.**
- Tap accelerometers (9900xxx) vs SOL111 response grids (1101–7105): ch1/50/87 are
  **~17 in** from any SOL111 response point. The SOL111 set sits high on the structure
  (Z≈19 in); the tap set is concentrated low/near the source (Z≈2–3 in). **Different sensor
  layouts** — SOL111 uses the *modal-test* grid set; the tap/shock test uses a separate dense set.

## Verdict
A true input-and-output-matched **magnitude** overlay of the extracted SOL111 `.pch` against
the Test07 tap FRFs is **not achievable from the extracted files** — neither the drive point
nor the response points coincide. This is not a scale-factor problem; they are **different
transfer paths**. The self-normalized **peak-frequency** comparison stays valid (resonances are
global for a free-free structure), so `opus_fem_vs_test_peaks.png` remains correct *as a
frequency-alignment diagnostic only*, which is exactly how it is labeled.

## How to actually remedy it (ranked)
1. **Switch the FEM-vs-test axis to modal correlation (recommended).** NASA's "well-correlated
   FEM" is supported by **mode shapes + frequencies** (`Test_Mode_Shapes/`, `TAM_FF`, `TAM_FB`)
   on the consistent 1101–7105 grid set, compared via **MAC** (mode-shape correlation) and
   frequency error. This is point-consistent and unit-robust — no force-amplitude normalization
   needed — and is the right StatFEM v1 observation layer.
2. **Magnitude FRF overlay, if required:** run NASTRAN SOL111 at the *actual* Test07 drive point
   and read out at the 9900xxx response grids (needs a solver + the full `.blk` model, which is
   present but not solved here), OR recover NASA's archived `*_Impact_Comparison` PNGs that
   already overlay FEM vs test at the 11101/11110 points.
3. **Test-internal FRF magnitude checks** (no FEM): hit-to-hit repeatability and driving-point
   reciprocity on the tap channels — already partly shown via the repeatability figure.

## Bottom line for the project
The normalization "remedy" turned into a **transfer-path reconciliation**, and the answer is to
build the FEM-vs-test bridge on **modal correlation (MAC + frequencies)**, not an FRF magnitude
overlay — reinforcing the recommended StatFEM v1 (10–400 Hz modal, pyro shock held out). No
magnitude likelihood is claimed; nothing was fabricated to force an overlay.
