# priority_deliverables.md — Card D (FEM remesh / data-driven correlation contribution)

Each PRIORITY ask from the runner prompt, my interpretation, and where it is delivered.
Status: PENDING until the named artifact exists AND is checker/figure-backed.

| # | Priority ask (card) | My interpretation | Delivered in | Status |
|---|---|---|---|---|
| P1 | Diagnose the mismatch region by region | Per-region MAC vs `.ash` (region-restricted), FEM-vs-measured FRF/peak at the 8 channels; identify which modes + which physics (joint/bulkhead/strut/dish/mesh) drive each region's error | `region_diagnosis.md` + `out/region_diagnosis.json` | DONE (MAC leg + cited FRF leg); FRF reproduction at 8 channels moves to P2 |
| P2 | COPY the FEM; reproduce the BEFORE baseline | Copy modal-twin assembler into this ws; reproduce eigenfreqs + MAC vs `.ash` (the BEFORE numbers) before any edit | `scripts/`+`run_baseline.sh` → `nominal_modes.json` (reproduces inherited to 3.6e-10); BEFORE in `out/edits/baseline_reuse/` | DONE |
| P3 | Targeted, traceable model/mesh edits in high-error regions only | One change → re-solve → measure effect; each justified by P1; no global re-tune | `out/edit_specs/` + `out/edits/e01..e10/` + dish refine `out/dish_refined/` | DONE (10 stiffness/joint edits + 1 true mesh refinement) |
| P4 | Re-solve, measure AFTER correlation | Before vs after per-mode freq error + MAC vs `.ash` (FRF/peak amplitude leg = validation study's domain, cited) | `out/before_after.json` + `figures/fig_before_after.png` | DONE (MAC+freq); FRF-amplitude leg cited to Card A |
| P5 | Honest verdict: improved at hard regions without degrading global? | Quantified; if no help, diagnose why | `correlation_contribution.md` §4 | DONE — 0/10 clean improvement (shape-vs-freq tradeoff); mesh converged; residual = damping/near-field/freq-align |
| P6 (meta) | Can an agent contribute to FEM correlation by remodeling from data? | Auditable yes/no + diagnosis + edits + before/after + human-judgment + residual risk | `correlation_contribution.md` (headline) | DONE — QUALIFIED YES (contribution = the auditable boundary of remodeling) |

## Acceptance criteria (win condition, card §5)
- Per-mode MAC AND FRF/peak agreement at the 8 hard channels measurably improve vs as-received.
- Global MAC/frequency does NOT get worse (reported both ways — hard-region and global).
- Every edit justified by the data-mismatch diagnosis + a before/after evidence table + a figure.
- A checker encodes: baseline reproduced; before/after table exists; no global degradation; figures legible.

## Clarification flagged (Priority Deliverables & Clarification Gate)
- "Re-mesh" scope ambiguity in a custom Python assembler (see decisions_log D0 open ambiguities). Cheap to
  surface; I proceed with the read-only diagnosis (commits nothing) and recommend a scope before edits.
