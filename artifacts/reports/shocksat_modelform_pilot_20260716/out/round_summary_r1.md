# Round 1 summary — diagnosis → class → edit links (agent track)

Diagnosis source: `out/diagnosis_mf_r1.json` (TRAIN-side residuals of the baseline A0_wide at the
study θ_MAP; windowed forward + measured survey ζ; NO fold scores computed; NO reduced-basis triage).

## What the compass says (round 1, baseline model)
- **Amplitude residuals (region|axis|band):** worst cells are Rectangular_Plates|Y|sub200 (0.901 dex,
  4 ch), Bottom_Box|Y (0.756, 72 ch), Top_Brackets|Y (0.734), Top_Box|Y (0.686), Bottom_Box|Z (0.685).
  Y-axis (lateral) dynamics dominate the misfit.
- **Survey-shape defect by region (NEW model-form diagnostic):** Bottom_Box 0.493, Top_Box 0.392,
  Cross_Beam 0.079 — the box shells carry ~89% of the paired-mode shape error → connectivity/geometry
  levers point there.
- **Residual vs local mesh size (NEW):** corr +0.05 over 104 channels — essentially NO refinement
  signal (consistent with the 2026-07-06 loop's mesh-converged finding). Mesh slots are still filled
  (stratification is the rule), targeted at the locally-coarsest high-residual parts.
- **Peak-width curvature misfit (NEW):** model/measured peak curvature 1.23 (sub-200, n=37) and 3.64
  (200–500, n=3) — model peaks systematically SHARPER than data → formulation/shear-compliance lever.
- **Pairing df%:** mixed signs inside 150–180 Hz (158.2 Hz pair −10.4% soft; 168.0/172.3 Hz pairs
  +7.4/+5.7% stiff) — a uniform stiffness scale cannot fix opposite signs in one band; this is the
  compass's argument for model-FORM redistribution rather than more property scaling.

## Proposals (2 per class × 5 classes; explicit links in each spec's `diagnosis_link`)
| cid | class | edit | link (short) |
|---|---|---|---|
| ma1_conn_rbe3tbox | connectivity | RBE3-convert 20 upper Top_Box spiders (z≥45) | Top_Box +7%-stiff pairs + 0.392 shape defect → de-rigidize wall joints |
| ma1_conn_softbbox | connectivity | soften 20 Bottom_Box spiders (k_t=1e5, k_r=1e4) | Bottom_Box = largest shape defect (0.493) |
| ma1_mesh_brkt | mesh_density | refine 301+302 (768 quads) | no global mesh signal; Top_Brackets 0.734 dex is the coarsest high-residual part |
| ma1_mesh_plates | mesh_density | refine 501+601 (2336 quads) | worst single cell Rectangular_Plates\|Y 0.901 dex |
| ma1_form_tboxwalls | element_formulation | br_scale 0.8 on 201/203 | +7.4/+5.7% too-stiff Top_Box pairs; soften bending w/o mass |
| ma1_form_platesshear | element_formulation | ts_t 5/6→0.35 on 501/601/701 | curvature ratio 3.64/1.23 = model too sharp; thick plates t/L~0.05 |
| ma1_geo_warp202 | geometry | warp top cover 202 by 0.20 in bubble | Top_Box shape defect; flatness is a build idealization (V-gate: stiffens drumhead cluster) |
| ma1_geo_jointbrkt | geometry | offset 4 tray-bracket spiders [0.25,0.15,0] | Top_Brackets\|Y 0.734 dex; interface position tolerance moves wall node lines |
| ma1_prop_tboxxbeam | property_control | thickness 201-203 ×0.9 + cross_beam ×1.4 | CONTROL: verbatim study best-EXACT candidate (0.1765) |
| ma1_prop_bracketsoft | property_control | thickness 301/302 ×0.85 | CONTROL: verbatim study screening winner (exact 0.1634) |

The two controls replay the strongest known property edits from the study's 28-candidate field
(Card A's exact re-rank), so HQ2's "beat the control class" bar is the historical best, not a strawman.

Random track r1: 10 seeded stratified draws (seeds in `out/seeds.json`), same menus, no diagnosis.

## Dud replacements (round 1)
- `ma1_conn_rbe3tbox` DUD: its z≥45 Top_Box spider list included SINGLE-LEG spiders (eids 90000xx),
  for which an RBE3 interpolation is singular (rotation about one master undetermined; cond=inf,
  caught by the operator's own guard). Replaced by `ma1_conn_rbe3tbox2` = the 20 multi-leg (≥3)
  Top_Box wall spiders (eids 2033593…), same diagnosis link. Random-track duds, if any, are replaced
  by the seeded attempt scheme (out/seeds.json).
