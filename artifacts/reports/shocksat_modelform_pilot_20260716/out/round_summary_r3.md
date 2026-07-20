# Round 3 summary — diagnosis → class → edit links (agent track)

Diagnosis source: `out/diagnosis_mf_r3.json` — TRAIN-side residuals of the AGENT's best MODEL-FORM
candidate (`ma2_geo_jointbbox`, exact +0.1734; the agent's overall best remains the r1 control replay
`ma1_prop_tboxxbeam` +0.1765 whose residual field was diagnosed in r2). Track independence kept: the
agent never sees the random track's specs or scores.

## What the round-2 within-track evidence + round-3 diagnosis say
- The two agent levers that IMPROVED in r2 were both genuine model-form: bbox joint offset (geometry,
  +0.1464→+0.1734 across variants) and plate refinement (mesh, +0.1692→+0.1710). r3 extends both.
- Perturbing the property winner HURT (+0.1765→+0.1080): the control class is at/near its local
  optimum — consistent with every prior loop's stacking-interference lesson.
- Diagnosis signature is STABLE across models (Bottom_Box 0.479 / Top_Box 0.389 shape defect;
  158.2 Hz −15.2% soft vs 168.0 Hz +9.9% stiff; mesh-size corr ~0): the misfit the compass sees is
  structural, not an artifact of one candidate.

## Proposals (2 per class; full links in spec JSONs)
| cid | class | edit | pointer |
|---|---|---|---|
| ma3_conn_soft_traypath | connectivity | soften 20 tray-path spiders (top+angle brackets) | Top_Brackets\|Y 0.702 dex; r2's joint result points at the tray interface |
| ma3_conn_rbe3_angle | connectivity | RBE3-convert 16 angle-bracket spiders | 20-leg rigid ties sit where the +9.9/+7.9% stiff pairs live |
| ma3_mesh_covers | mesh_density | refine 202+501+601 (7166 quads) | extend the improving refine lever to the top cover |
| ma3_mesh_welds | mesh_density | refine all 6 weld strips (1966 quads) | never refined by ANY track; welds were the prior loop's only directional shape signal |
| ma3_form_tboxstrong | element_formulation | br ×0.75 on 201/203 | push r1's tbox-wall softening harder (+9.9% stiff pairs persist) |
| ma3_form_brktshear | element_formulation | ts_t 5/6→0.35 on 301/302 | bracket shear-softening (agent's best r1 formulation knob, new region) |
| ma3_geo_jointbbox2 | geometry | offset 6 different bbox spiders [0,0.30,0] | extend the agent's best model-form lever along its winning axis (Y) |
| ma3_geo_warp401 | geometry | warp cross-beam plate 0.20 in | geometry counterpart of the winning cross_beam stiffening |
| ma3_prop_xbeam16 | property_control | cross_beam ×1.6 | CONTROL: probe the xbeam response curve |
| ma3_prop_brktxbeam | property_control | brackets ×0.85 + xbeam ×1.4 | CONTROL: combine the two strongest historical property levers |

Round-2 dud follow-up: `mr2_conn1` (random rbe3 draw hit a single-leg spider again — singular by
construction) replaced by the seeded attempt-1 draw. Duds total 4 (2 dead refines, 2 singular rbe3).
