# Priority deliverables — restated in my own words (Clarification Gate)

| # | Andrew's priority ask | My interpretation | Where delivered | Status |
|---|-----------------------|-------------------|-----------------|--------|
| P1 | Review Schneider 2022 + Das/Debnath 2020 + statFEM backbone, and prior folder work | Extract each paper's NOVEL techniques and map them to the project vision levers; ground in existing threads | `study_program.md §1–2`; deck slides 2–4 | DONE |
| P2 | Design a SERIES of studies combining the two papers' techniques with statFEM toward the vision | 6 studies (A–F), each with question/observable/forward-model/likelihood/QOI/gate/dataset; ranked by readiness | `study_program.md §3`; deck slides 9–12 | DONE |
| P3 | Use folder data (ShockSat, MPL stand, suspended panel, hexapod "tray" FEM) in fully-synthetic or synthetic+data examples | Study A = fully synthetic (run); C/D/E/F = synthetic+data on suspended panel / tray FEM / ShockSat / MPL stand (designed, grounded in real numbers) | `study_program.md §3`; real-data char. figure | DONE (A run; rest designed) |
| P4 | Build or update FEMs if necessary | Build a JAX-differentiable analytic 3-DOF/2-DOF coupled source/load forward model for Study A; reuse hexapod tray FEM modes for Study D design (no new FE solve needed this task) | `code/forward.py`; `out/hexapod_modes.json` | DONE |
| P5 | Execute enough to rank findings 1–5 HONESTLY (utter failure → smashing success) | Run Study A end-to-end (NUTS + held-out coverage + checker); score it on evidence; score designed studies on readiness with explicit labels | `out/study_a_*`; `checker_report.json`; deck scoreboard | DONE |
| P6 | Slide deck with figures + GIFs (tufte skill), key findings ranked 1–5, comprehensive next steps | PPTX with tufte-linted figures, ≥1 GIF, a 1–5 findings scoreboard, and a phased next-steps slide | `slides/papers_statfem_studies.pptx`; `packet.md` | DONE |

## Ambiguities flagged (could not ask mid-run → assumptions stated, both interpretations where cheap)
- **A1 (scope: design vs execute).** "Design a series ... do not stop until a deck ranked 1–5" mixes a
  DESIGN ask with an EXECUTE/score ask. Assumed: design all, execute the one most vision-central study so
  the ranking is evidence-backed; label designed studies as design-stage. (decisions_log D0.)
- **A2 (which dataset leads).** Picked a FULLY SYNTHETIC headline (controllable truth → honest held-out
  coverage and honest 1–5) and used real data to ground the designed studies. Rationale: vision §13b.5 —
  known-truth synthetic is the right tool to validate a METHOD/detector; real data is for a science claim.
- **A3 (NUTS vs the papers' own samplers).** Schneider uses BUS+Subset-Simulation; Das/Debnath use MAP +
  Hessian. Project rule = NUTS is default. I port Schneider's LIKELIHOOD into a NUTS update (the novel
  technique is the error model, not the sampler) and label it so. (AGENTS NUTS rule.)
