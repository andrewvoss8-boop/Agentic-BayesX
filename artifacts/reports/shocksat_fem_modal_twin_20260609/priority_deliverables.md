# Priority Deliverables (restated in my own words)

Task card: `docs/lab/shocksat_fem_modal_twin_runner_prompt.md`. Date 2026-06-09.

| # | priority ask | my interpretation | delivered where |
|---|---|---|---|
| P0 | Task 0: resolve measured-mode provenance BEFORE modeling; stop if no genuine test set | Prove which file is test vs FEM vs TAM with evidence; parse the real measured modes | `measured_modes_provenance.md`, `scripts/parse_ash.py`, `measured_modes.npz` — RESOLVED: `Final_FF_Test_Shapes_100121.ash` = 33 measured modes w/ shapes on 76 nodes |
| P1 | Full parametric FEM of ShockSat from the provided NASTRAN deck, stiffness scaled by a small set of per-part-group theta_g | Parse `FEM_20211021` bulk data, assemble K_g per include-file part group + M in Python; K(theta)=sum theta_g K_g | `scripts/parse_nastran.py`, `scripts/assemble_fem.py`, `fem_assembly_report.md` |
| P2 | NUTS-feasible differentiable reduced forward model + reduction error reported | Project onto nominal modal basis; reduced eigh in JAX float64; compare reduced vs full sparse eigensolve at nominal and perturbed theta | `scripts/reduce_model.py`, packet section "reduction error" |
| P3 | Bayesian calibration with NUTS (>=4 chains), likelihood on measured modal frequencies + shapes/MAC at the 1101-7105 grids; full convergence gate over ALL variables | NumPyro NUTS; freq + shape-component likelihood; R-hat/ESS/divergences reported for every sampled variable | `scripts/run_nuts.py`, `convergence_report.json`, packet |
| P4 | THE deliverable: held-out QOI side-by-side — posterior median + 95% CI vs measured actual, coverage and error %; lock-before-reveal | Leave-one-mode-out CV + low->high frequency-band extrapolation; predictions hashed before grading | `heldout_qoi_table.csv`, `figures/heldout_qoi_sidebyside.png`, lock hashes in `heldout_lock.json` |
| P5 | FEMAP cross-check handoff | Normal-modes deck at nominal and posterior-mean theta + instructions | `femap_handoff/` |
| P6 | Checker + one-command replay | `check.py`, `checker_report.json`, `run_all.sh` | workspace root |
| P7 | Standard gates: assumptions ledger, quantity contracts, sensitivity, Tufte plots, runtime accounting | per AGENTS.md | respective .md files |

## Ambiguities flagged up front
1. "mode shapes / MAC on the 1101-7105 grids": the measured shape file actually
   covers 76 nodes from 1101 to 11112 (incl. 8101-11112), 132 measured DOFs.
   INTERPRETATION: use all measured channels (more information, same source);
   the 1101-7105 phrase in the card came from the earlier runner's partial view.
2. Two measured sets exist (impact vs burst). INTERPRETATION: impact-hammer set
   (NASA's correlation basis). Burst set used as noise-floor evidence.
3. "Joint connections" are CBUSH springs whose stiffness NASA hand-tuned;
   they are natural theta groups alongside part-stiffness scales.
4. The card's pinned env (jax 0.4.30/numpyro 0.15.3) is the repo `.venv_nuts`;
   using it as-is.
