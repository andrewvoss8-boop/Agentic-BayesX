# Bilionis direction-check deck — 2026-07-13

An 8-slide update for Prof. Bilionis: where the ShockSat Bayesian FEM-updating project stands,
and the decisions needed to **land the plane in ~1 month**.

- **Deliverable:** `slides/bilionis_update_20260713.pptx`
- **Rebuild:** `python3 code/make_update_deck.py` (needs `python-pptx`)
- **Consolidation only** — no new science. Every figure is a provenance-labeled **copy**
  (`figures/reuse_*`); every number is copied from a study checker, nothing stated stronger.
- **Rev 2 (Andrew):** plain language, short bullets, figures tell the story; internal codes
  (checker triads, study labels) moved out of slide bodies into the small-print footers.

## Slide map
1. Where we are, how to finish (status + the ask).
2. The wall — updating fixes the peaks, not the shapes.
3. What the held-out data said (one win, four failures).
4. Main recent focus: agents remodeling the FEM.
5. What I learned about running AI agents on science (the blog material).
6. Two ways to land — paper vs class module, both drafted.
7. The drafted paper, in one paragraph (plain-language abstract).
8. Your call (module vs paper, blog, one last MPL experiment or write, authorship/AI disclosure, NASA data, ~1 month).

## Figure provenance (all reuse copies)
| file | source workspace |
|---|---|
| reuse_L5_param_locations.png | shocksat_modelclass_L5_20260619 (node cloud, 9 groups) |
| reuse_frf_wall_grid.png | shocksat_psd_envelope_twin_20260623 (frf_comparison_grid) |
| reuse_agentic_funnel.png | shocksat_composite_bakeoff_20260702 (151→29 funnel) |
| reuse_agentic_evidence.png | shocksat_composite_bakeoff_20260702 (evidence winner) |
| reuse_netcg_delivery.png | shocksat_netcg_method_selection_20260701 (delivered bands) |
| reuse_netcg_trust.png | shocksat_netcg_method_selection_20260701 (QOI trust map) |

## Checker statuses cited (copied verbatim)
- netcg_method_selection_20260701 — GREEN 22/0/0 (delivered statFEM F(k) twin)
- composite_bakeoff_20260702 — YELLOW 57/6/0 (agentic remodeling did not earn delivery; Beck per-point vs net-CG split)
- true_remodel_loop_20260706 — YELLOW 11/1/0 (closed-loop shape-changing falsified; 1 YELLOW = pre-registered falsification)
- frf_damping_updating_20260710 — YELLOW 19/2/0 (damping lever tested + closed)
- plate_test_rehearsal_20260701 — RED 28/3/1 (RED = the pre-registered sensor-placement falsification; pipeline intact)
- runner_comparison_{,round2}_20260602/03 — competitive multi-model runners (integrity + convergence findings)

## Referenced drafts (not built here; linked for the two landing options)
- Paper: `artifacts/reports/paper_draft_dce_20260702/paper_draft.md` (v0.3, Data-Centric Engineering target).
- Module: `teaching/bayesian_fem_updating_module/` (DRAFT ipynb; not cleared for student release).

## Honesty / open items surfaced on the slides
- Model-vs-model wording (Fable / Opus 4.8 / GPT-5.5 / Composer 2.5) is a **blog-draft characterization**
  from the runner-comparison runs, not a formal scored benchmark of those exact model versions.
- **NASA ShockSat data-sharing permission** blocks BOTH the paper and the module — same open item as before.
- IP disclosure gate: disclose to the Purdue IP officer before any public Substack post (even though nothing
  looks patentable).

## Not self-applied (needs Andrew)
- Proposed `docs/report/project_log.md` row (T7 reporting/outreach):
  `07-13 | Bilionis direction-check deck (T7) | Built (pending review) | 9-slide update: status, held-out
  1-positive/4-cautionary, agentic-remesh focus, harness/model-comparison, paper vs module landing options +
  abstract, MPL optional push, decisions. Consolidation only; reuse figures; numbers copied from checkers. |
  artifacts/reports/bilionis_update_20260713/ · python3 code/make_update_deck.py`
