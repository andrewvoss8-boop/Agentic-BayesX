# TASK 0 — Measured-Mode Provenance (gates everything downstream)

Date: 2026-06-09. Author: FEM modal twin runner.

## Question
Which file holds the genuinely MEASURED free-free test modes, vs FEM analysis
modes, vs the reduced TAM? The prior runner flagged that `FINAL_FF/TAM_FF/Modes.pch`
was labeled "test" but looked like FEM (SOL SEMODES deck, MAC values exactly 1.000).

## Verdict (each claim has file evidence below)

| file | what it actually is |
|---|---|
| `FINAL_FF/TAM_FF/Modes.pch` | FEM analysis modes (NOT test). Punch output of `Modes.dat`, a `SOL SEMODES` run on the April model `ShockSat_04292021.blk`. First eigenvalue 2.179e-4 (rad/s)^2 = 0.0023 Hz = rigid-body mode; its 24 elastic frequencies (59.19, 80.71, 81.36, 97.09, ...) match the "FEM" column of the test report xlsx exactly. |
| `FINAL_FF/TAM_FF/TAM.pch` | Reduced FEM: external-superelement DMIG punch ("STANDARD PUNCH FOR EXTERNAL SUPERELEMENT 100", KAAX/MAAX/MUG1T). Not test data. The exactly-1.000 MACs the prior runner saw are FEM-vs-FEM reduction-fidelity checks (full FEM vs its TAM), which is why they are perfect. |
| `Test_Mode_Shapes/TDM_FF_091721.blk` | Test Display Model: geometry only (80 GRID + display CTRIA3/CBAR/CQUAD4, FEMAP-generated). No mode data inside. |
| `Test_Mode_Shapes/Final_FF_Test_Shapes_100121.ash` | THE MEASURED FREE-FREE TEST MODES. ATA/OPoly binary shape file (extracted from `sources/FEM_and_CAD.zip`, which the prior runner had not unpacked into `extracted/`). 33 modes, 54.19-256.79 Hz, frequency + damping + mode-shape components on 76 accelerometer nodes (132 measured DOFs). |
| `FF_Final_Data/*.xlsx` | Measured-mode summary tables (frequencies, damping, descriptions) from burst runs 73-78 and impact runs 09/10/11, plus test-vs-April-FEM cross-orthogonality/MAC tables. Used here as cross-checks. |

## Evidence chain for the .ash = measured claim
1. Internal strings: per-mode source records name the modal-test fit files
   `ShkSat_09_imp_1101_Zm_VJS.afu`, `ShkSat_10_imp_2101_Xm`, `ShkSat_12_imp_11101_Xm`,
   `ShkSat_13_imp_11110_Yp`, `ShkSat_35_imp_5201_Zm.ati` ... fitted with
   "OPoly v7.5.0 r159" (ATA polyreference curve fitter) by user `jwinkel`,
   dated 20-Sep-21 / 01-Oct-21. These are impact-hammer TEST runs (NASA's
   correlation pptx slide 1: "Only utilized impact hammer test data").
2. Frequencies match NASA's published TEST frequencies in
   `Final_Summary_Documentation_101521_rev1.pptx` slides 21-45 exactly
   (54.19, 69.98, 74.98, 85.78, 107.03, 117.63, 118.53, 125.0, 137.2, 142.4,
   151.2, 158.2, 165.9, 168.0, 172.3, 174.8, 184.4, 188.6, 190.2, 195.7,
   197.8, 198.9, 203.0, 213.9, 222.1 Hz), and are consistent with the burst-run
   xlsx values (run-to-run scatter < 0.3%).
3. Measured-component pattern matches the published sensor map: pptx ASET slides
   65-76 say node 1101 measures Z only, 1102 measures Y+Z, 1103 X+Z, 2101 XYZ;
   the parsed .ash has exactly those components live (checker in
   `scripts/parse_ash.py` prints these spot checks).
4. The shapes CANNOT be FEM output: 33 modes extend to 256.8 Hz while every FEM
   solve in the archive cuts off at 225 Hz (EIGRL V2=225 in `FEM_20211021/Modes.dat`)
   or 300 Hz (April `Modes.dat`); damping values are mode-specific measured
   fractions (0.13%-1.7%), not the uniform placeholder 1% in the FEM tables.

## Binary format (reverse-engineered, validated by checks 2-3 above)
- word 640: channel table, 76 x int32 triplets (node, node, seq 1..76).
- per-mode records found by int32 signature [mode_index, 76, 250, 1, 3]:
  freq f32, damping f32, then at +251 words a 228-float32 block = 76 nodes x
  (X,Y,Z); IEEE negative zero = component not instrumented; 132 live DOFs.
- Parser: `scripts/parse_ash.py` -> `measured_modes.npz`, `measured_modes_summary.json`.

## Two measured mode sets in the archive (decision)
- Impact-hammer set (THIS .ash): used by NASA for correlation; 54.19 Hz first mode.
- Burst-random set (xlsx runs 73-78): same modes within ~0.3-2% (e.g. 115.7 vs
  117.63 Hz mode 6 - amplitude/suspension differences between test types).
DECISION: calibrate against the impact-hammer .ash set (it is the set NASA's
correlation and the TAM cross-orthogonality used; it has full shape vectors).
Burst-vs-impact frequency differences inform the noise floor in the
assumptions ledger.

## Caveats (honest)
- The .ash layout was reverse-engineered; risk of a subtle component-frame error
  remains. Mitigations: ASET pattern check passed; MAC of parsed test shapes vs
  our FEM modes at nominal theta is checked downstream (packet) - a frame error
  would destroy MAC for all modes at once.
- Test shapes are unscaled modal vectors (arbitrary per-mode scale): only
  MAC / normalized components are used, never absolute shape magnitude.
- Nodes 1106-1109 (and any TDM grid with CD=4 cylindrical) may be stored in a
  local output frame; the observation operator must use the SAME frame on the
  FEM side (handled in the observation-operator script; verified via MAC).
