# Arm D — Round 2 summary (amplitude compass)

## Diagnosis (on the round-1 winner wa1_tbox_soft, `diagnosis_r2.json`)
Bottom_Box|Y **still worst** (corr −0.09) after softening the top box; Rectangular_Plates|Y (0.46),
Top_Brackets|Y (0.43). Round-1 winners: tbox_soft 0.171, xbeam_scale 0.170.

## Diagnosis → proposal link (4 agent candidates)
| cid | edit | targets |
|---|---|---|
| wa2_tbox_xbeam | top_box×0.9 + cross_beam×1.4 | stack the two best round-1 edits (additivity test) |
| wa2_bothbox_soft | bottom_box×0.9 + top_box×0.9 | Bottom_Box\|Y persists → move both boxes |
| wa2_bbox_zsplit_tbox | bottom_box lower-half own-θ + top_box×0.9 | shape d.o.f. for the stubborn Y, on the tbox winner |
| wa2_brackets_soft | angle_brackets×0.85 | Top_Brackets\|Y (0.74 resid, corr 0.43) |

## Results (dev sub-200 P1′; A1 bar 0.1454)
| track | candidate | sub-200 | 200-500 |
|---|---|---|---|
| agent | **wa2_brackets_soft** | **0.1794** | 0.188 |
| agent | wa2_bbox_zsplit_tbox | 0.1766 | 0.135 |
| agent | wa2_tbox_xbeam | 0.1680 | 0.205 |
| agent | wa2_bothbox_soft | 0.1514 | 0.135 |
| random | wr2_rnd001 | 0.1657 | 0.184 |
| random | wr2_rnd003 | 0.1612 | 0.204 |
| random | wr2_rnd000 | 0.1490 | 0.062 |
| random | wr2_rnd002 | 0.1414 | 0.167 |

**Round-2 read (H2):** the compass-proposed **bracket softening (0.1794)** now leads the best random
(0.1657) by **+0.014** — the agent found a targeted edit (from the Top_Brackets|Y residual) that random
search did not reach this round. Whether this clears the S2 ≥1×fold-SE bar is decided on the paired-fold
deltas after round 3 (see `out/verdicts.json`).
