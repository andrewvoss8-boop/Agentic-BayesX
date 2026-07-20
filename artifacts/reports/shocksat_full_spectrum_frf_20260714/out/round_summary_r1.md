# Arm D — Round 1 summary (the amplitude compass; H2 fair test)

**Compass = TRAIN-side per-channel log|H| residual fields** (`out/diagnosis_r1.json`), the deliverable metric
itself — this is the H2 test the true-remodel loop (2026-07-06) could not make because its compass was
frequency/evidence, uncorrelated with held-out FRF.

## Diagnosis (what the compass points at)
| signal | value | reading |
|---|---|---|
| worst residual cell | Bottom_Box \| Y | corr −0.14, mean\|resid\| 0.76 dex, 72 channels |
| 2nd/3rd | Top_Box \| Y (0.17, n42), Top_Box \| Z (0.22, n43) | box Y/Z response mispredicted |
| worst single (low-n) | Rectangular_Plates \| Y | corr 0.42, resid 0.90 dex, 4 ch |
| survey peaks | 158→142 (−10%), 166→153 (−8%), 168→180 (+7%), 172→182 (+6%) | 150–180 Hz Y-mode cluster **mis-paired**, both signs |
| extended peaks | 254/275/296/342/354/367 Hz all <0.5% df | FEM **frequencies are good** ≥250 Hz; the error is amplitude/shape, not frequency |

**Reading:** the dominant held-out error is the **Y-direction box response** and a mis-ordered 150–180 Hz
Y-mode cluster. Above ~250 Hz the frequencies are accurate, so no frequency-moving edit is warranted there.

## Diagnosis → proposal link (agent track, 6 candidates)
| cid | family | edit | which diagnosis signal it targets |
|---|---|---|---|
| wa1_bbox_stiff | thickness | bottom_box ×1.15 | Bottom_Box\|Y worst cell + mis-paired box Y cluster (raise/reorder) |
| wa1_bbox_soft | thickness | bottom_box ×0.87 | same cell; peak errors both signs → bracket the direction |
| wa1_tbox_soft | thickness | top_box ×0.90 | Top_Box\|Y (0.69) + Top_Box\|Z (0.68) |
| wa1_plates_stiff | thickness | plates ×1.20 | Rectangular_Plates\|Y worst single cell (0.90) |
| wa1_bbox_zsplit | split | bottom_box lower-half own θ | give the Y sub-region a shape d.o.f. for amplitude updating |
| wa1_xbeam_scale | scale (parametric_only) | cross_beam ×1.4 | the honest parametric baseline the shape/thickness edits MUST beat |

## Equal-budget random control
6 random-grammar candidates (same families/menus, seed 20260715) via `actions.random_specs` →
`loop_wide random_round 1 6 20260715`. Same query budget, seed recorded (G05).

Scores (dev sub-200 P1′, fold-averaged) will be appended to `out/query_log.jsonl` and summarized here after
the round runs. **Bar to beat = A1-wide sub-200 0.1454.** The agent-vs-random comparison (S2) uses the
paired-fold-delta SE convention (D2).

## Round 1 RESULTS (dev sub-200 P1′, fold-averaged; A1 bar = 0.1454)
| track | candidate | sub-200 | 200-500 |
|---|---|---|---|
| agent | wa1_tbox_soft | **0.1706** | 0.087 |
| agent | wa1_xbeam_scale (parametric) | 0.1704 | 0.207 |
| agent | wa1_bbox_zsplit | 0.1590 | 0.266 |
| agent | wa1_bbox_soft | 0.1586 | 0.185 |
| agent | wa1_plates_stiff | 0.1499 | 0.227 |
| agent | wa1_bbox_stiff | 0.1453 | 0.198 |
| random | wr1_rnd004 | 0.1656 | 0.180 |
| random | wr1_rnd005 | 0.1634 | 0.170 |
| random | wr1_rnd000 | 0.1511 | 0.197 |
| random | wr1_rnd002 | 0.1507 | 0.239 |
| random | wr1_rnd003 | 0.1395 | 0.249 |
| random | wr1_rnd001 | 0.0773 | 0.113 |

**Round-1 read (H2):** agent best 0.1706 vs random best 0.1656 — agent barely ahead (+0.005), a tie within
fold noise. Almost every edit lifts 200-500 sharply (0.09-0.27 vs A1 0.058) but sub-200 barely moves
(0.15-0.17) — the shape wall again. The parametric_only control (xbeam_scale) is among the very best,
reproducing the true-remodel-loop lesson that parametric edits match shape edits. 6 own-space eigensolves
(top 545-635 Hz, ~194 modes) + projected candidates.
