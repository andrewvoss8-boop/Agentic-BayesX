# Round 2 summary — diagnosis → class → edit links (agent track)

Diagnosis source: `out/diagnosis_mf_r2.json` — TRAIN-side residuals of the AGENT's round-1 best
(`ma1_prop_tboxxbeam`, exact +0.1765). Track independence kept: the agent does NOT see or diagnose the
random track's candidates (random's r1 best `mr1_conn0` +0.1778 plays no role in these proposals).

## What changed vs round 1
- Bottom_Box still carries the dominant survey-shape defect (0.487; r1's Top_Box-side edits did not
  touch it) → both r2 connectivity slots and one geometry slot point there.
- Peak-curvature ratio FLIPPED below 1 (0.647 sub-200 / 0.52 mid-band): on the r1-best model the
  predicted peaks are too BLUNT — the formulation pointer reverses (stiffen, not soften).
- Pairing df% grew both directions (118.5 Hz −13.0%, 158.2 Hz −15.1% model-soft; 107.0 +12.4%,
  168.0 +7.9% model-stiff) — opposite signs in-band remain the model-form argument.
- Residual-vs-mesh-size corr still ~0 (+0.033), but the r1 refines were the agent's best model-form
  candidates (+0.1692/+0.1666) → mesh slots extend the same refinements rather than chase the
  (absent) global signal.

## Proposals (2 per class; full links in the spec JSONs)
| cid | class | edit | pointer |
|---|---|---|---|
| ma2_conn_rotfree_bbox | connectivity | soften 20 Bottom_Box spiders, k_t=1e6 / k_r=3e3 | keep shear path, release joint ROTATION (wall-bending clamp hypothesis) |
| ma2_conn_rbe3_bbox | connectivity | RBE3-convert 20 Bottom_Box spiders | same region via interpolation constraint |
| ma2_mesh_plates3 | mesh_density | refine 501+601+701 (6392 quads) | extend r1's best model-form lever to the drumhead |
| ma2_mesh_brktxbeam | mesh_density | refine 301+302+401 | brackets lever + Cross_Beam defect rose to 0.098 |
| ma2_form_bboxstiff | element_formulation | br ×1.25 on 101/103 | model-soft pairs + curvature<1 → stiffen bottom-box bending |
| ma2_form_plateskirch | element_formulation | ts_t 5/6→5.0 on 501/601/701 | bracket r1's shear-soften with the Kirchhoff limit |
| ma2_geo_warp102 | geometry | warp bottom cover 102 by 0.20 in | Bottom_Box flatness idealization (r1 tested 202) |
| ma2_geo_jointbbox | geometry | offset 3 bottom-box spiders [0,0.25,0.05] | Y is the worst axis (0.763 dex) |
| ma2_prop_tboxxbeam2 | property_control | thickness 201-203 ×0.85 + xbeam ×1.5 | CONTROL: perturb the r1 winner |
| ma2_prop_xbeam | property_control | xbeam ×1.4 alone | CONTROL: isolate the winner's scale component |

## Round-1 dud follow-ups
- mr1_mesh2/mr1_mesh3 (random refines) FAILED the liveness mech gate (max mode shift 0.0014%/0.0005%
  < 0.05%): refining those regions is a numerical no-op — fresh mesh-convergence evidence. Seeded
  replacements enqueued (attempt-1 seeds in out/seeds.json).
