# Project status deck — 2026-07-01

**Deliverable:** `slides/project_status_20260701.pptx` (19 slides)
**Replay:** `bash run_all.sh` (copies reused figures → builds deck → heuristic QA)
**Type:** CONSOLIDATION — no new science was run. Every number on every slide traces to a
saved file in an existing workspace, cited in that slide's footer.

## Purpose
Andrew's ask (2026-07-01): "throw together some slides on the project status with telling
figures on project status and next steps. Want to meaningfully contribute to aerospace
workflows and the bayesian fem updating literature."

## Story arc (19 slides)
1. Title
2. The project in one slide (goal → wall → proof → pivot → delivery → next)
3. The two contribution targets (aerospace workflows / literature)
4. PART 1 divider — status
5. The wall: per-point FRF bands honest but +27 dB (fig: wide_ci)
6. The defect: local mode-shape fidelity, 0.97-vs-0.17 MAC contrast (fig: residual_map)
7. Agentic remeshing: competently executed, decisively unfruitful (fig: combine_best)
8. PART 2 divider — the pivot
9. Stage-0 QOI trust map (fig: stage0_qoi_trust)
10. The delivery: held-out-drive-validated net-CG bands (fig: delivery_bands)
11. Method-selection table (coverage hard gate; leave-modes-out disqualifier)
12. Precise honesty: ~0.9 point-wise discrepancy, averages out at 1 octave (fig: learned_statfem)
13. PART 3 divider — contributions & next steps
14. Aerospace "Monday tools" table
15. Literature contributions #1–#4 (fig: consistency_money)
16. ShockSat's position among the literature's physical test cases
17. The next test dollar: >200 Hz drumhead plate test (fig: pretest)
18. Next steps / decision asks (proposals, not decided)
19. Status, provenance, honest limits

## Figure provenance (ALL copies — none generated here)
| local file | source |
|---|---|
| reuse_netcg_delivery_bands.png | shocksat_netcg_method_selection_20260701/figures/fig_delivery_netcg_bands.png |
| reuse_netcg_stage0_qoi_trust.png | shocksat_netcg_method_selection_20260701/figures/fig_stage0_qoi_trust.png |
| reuse_netcg_pretest.png | shocksat_netcg_method_selection_20260701/figures/fig_pretest.png |
| reuse_netcg_learned_statfem.png | shocksat_netcg_method_selection_20260701/figures/fig_learned_statfem.png |
| reuse_bil_wide_ci.png | shocksat_bilionis_review_20260626/figures/fig_wide_ci.png |
| reuse_bil_combine_best.png | shocksat_bilionis_review_20260626/figures/fig_combine_best.png |
| reuse_bil_residual_map.png | shocksat_bilionis_review_20260626/figures/reuse_residual_map.png (orig: shocksat_psd_envelope_twin_20260623) |
| reuse_bil_consistency_money.png | shocksat_bilionis_review_20260626/figures/reuse_consistency_money.png (orig: statfem_consistency_toy) |

## Status labels used in the deck (per AGENTS.md)
- CHECKER-BACKED: netcg method selection (GREEN 22/0/0), FEM-remesh Card D (GREEN 14/0/0),
  IFT real-validation / consistency toy / model-class L5 (YELLOW honest negatives).
- EXPLORATORY: FRF-correlation, remesh-sweep, wide-CI work — flagged on slides 5 and 19.
- Checker GREEN certifies integrity + convergence + honest flagging, NOT the normal-Z number
  (three carried caveats — slide 19).

## QA
`code/qa_deck.py` (heuristic overflow/table-width/spill check; no renderer available on this
machine): **no flags** at 19 slides. Not a substitute for opening the file.

## Known limitations of this deck
- Slide 16's literature positioning beyond the Kiran reading notes needs a citation pass
  before any external use (flagged on the slide itself).
- Slide 18 priorities are a PROPOSAL for discussion, not decided.

## Revision 2026-07-02
Slides 2, 14, 17, 18 revised after the plate-test rehearsal (`plate_test_rehearsal_20260701`,
checker OVERALL RED = pre-registered claim-falsified tier): the §9 analytic 3.5x buy-down is
FALSIFIED (12 sensors -> 6.2x); slide 17 now carries the rehearsed money figure
(`reuse_rehearsal_buydown.png`) and the revised 12-mode test scope (oracle 2.81x, follow-up
rehearsal approved before any hardware ask). netcg packet carries a matching dated erratum (§10).
