# HANDOFF — ShockSat FEM Modal Twin (session 1 ended: out of usage credits)

Task card: `docs/lab/shocksat_fem_modal_twin_runner_prompt.md`. Read it + AGENTS.md
gates first. Work ONLY in this workspace. Session 1 active runtime ~35 min
(start epoch in /tmp/twin_t0.txt; cumulative tool time well under wallclock).

## STATUS: Task 0 DONE. FEM parse + element library DONE+VALIDATED. Assembly 90%
## (one RBE2 conflict to fix). No reduction/NUTS/held-out work started.

## What is DONE (all artifact-backed, in this workspace)

1. Workspace + integrity: `inputs_sha256_start.json` (50 read-only inputs hashed).
   MUST re-hash at end and write `inputs_sha256_end.json` (checker gate).
2. TASK 0 RESOLVED — `measured_modes_provenance.md`:
   - MEASURED free-free test modes = `inputs/Final_FF_Test_Shapes_100121.ash`
     (extracted from `../shocksat_statfem_runner_20260609/sources/FEM_and_CAD.zip`;
     the prior runner never unpacked it). Binary format reverse-engineered and
     validated; parser `scripts/parse_ash.py` -> `measured_modes.npz` +
     `measured_modes_summary.json`: 33 modes 54.19-256.79 Hz, damping, shapes on
     76 accel nodes, 132 measured DOFs (basic-frame X/Y/Z; neg-zero = not measured).
     ASET-pattern spot checks pass (1101=Z, 1102=YZ, 1103=XZ, 2101=XYZ).
   - `TAM_FF/Modes.pch` = FEM (SOL SEMODES of April model), NOT test. TAM.pch =
     external-superelement DMIG. TDM = display geometry. Exactly-1.000 MACs the
     prior runner saw = FEM-vs-TAM reduction checks.
3. NASA reference numbers (from `Final_Summary_Documentation_101521_rev1.pptx`,
   slides 21-45) — test vs FINAL (Oct) FEM pairing, needed for forward-model
   validation (also keep in packet):
   test:  54.19 69.98 74.98 85.78 107.03 117.63 118.53 125.0 137.2 142.4 151.2
          158.2 165.9 168.0 172.3 174.8 184.4 188.6 190.2 195.7 197.8 198.9
          203.0 213.9 222.1
   FEM:   54.67 73.51 73.09 87.94 102.23 108.17 113.43 116.9 137.9 154.5 151.8
          135.9 160.4 183.4 185.0 164.5 182.7 189.3 191.0 192.6 191.9 193.5
          191.4 (none) 211.1
   Also: total weight 127.89 lb, CG=(0,0,28.01) in (slide 55). NASA says
   correlation struggles >150 Hz (slide 12); bottom steel box was hardest (slide 8).
4. Deck parse — `scripts/parse_nastran.py` -> `fem_model.npz`,
   `fem_parse_report.json`: 67,720 grids (all CP=CD=0 basic), 67,366 CQUAD4,
   428 CTRIA3, 166 CBUSH (9 PBUSH props), 80 CONM2 (offset accel masses),
   187 RBE2 (CM=123 spiders + 123456), 18 PSHELL, 4 MAT1, CORD2R 801/802 (+CORD2C).
   Units: in/lbf/s, rho already mass density (lbf s^2/in^4). PARAM K6ROT=100.
5. Element library — `scripts/fe_core.py`, VALIDATED by `scripts/fe_validate.py`
   (`fe_validate_report.json`, ALL_OK true): QM6 membrane (cantilever -0.37%),
   MITC4 bending (SS plate -0.47%), CST patch exact, DKT (SS plate -0.33%),
   rigid-tilt residuals ~1e-16 in NASTRAN sign convention.
   HARD-WON LESSONS (already fixed, do not re-break):
   - DKT Batoz Hy,eta entry 8 must be "-1 + r5(1-2eta) + xi(r4-r5)".
   - Mindlin beta->NASTRAN map is bx=-thy, by=+thx (rigid-tilt test V3b/V5c
     catches sign errors that eigenvalue-count tests CANNOT see).
6. Assembly — `scripts/assemble_fem.py` runs in ~15 s: per-PID stiffness blocks
   `matrices/K_shell_<pid>.npz`, `matrices/K_bush_<pid>.npz` (theta scaling =
   exact modulus scaling), lumped M + CONM2 (offset transform), drilling penalty
   K6ROT*1e-6*G*t*A/node. Mass/CG/rigid-energy checks coded but NOT yet reached.

## CURRENT BLOCKER (fix first, ~30 min)
`build_T()` asserts: grid 2022336 comp 0 dependent twice:
- RBE2 2033600 (Joint_Connections, GN=2033758, CM=123 spider) AND
- RBE2 9900027 (Shock_Test_Instrumentation.blk, GN=9900027, CM=123456).
Cause verified in raw deck: ALL 37 shock-instrumentation RBE2s use the 9900xxx
shock-accel grid as INDEPENDENT (GN) and 4 nearby structure grids as DEPENDENT.
RECOMMENDED FIX: drop `Shock_Test_Instrumentation.blk` from the model entirely
(massless, stiffness-free response-point spiders for the shock test; not needed
for the modal twin; removes its 37 grids too or you get 37x6 spurious zero modes).
Residual risk negligible (4-grid patches already shell-connected); log as a
decision + assumptions-ledger entry. Alternative (more faithful): invert those
37 RBE2s (treat 9900xxx as dependent on the first structure grid, drop the other
3 deps); either is defensible if labeled.

## REMAINING PLAN (in order; follow task card sections 5-16)
1. Fix RBE2, rerun `assemble_fem.py`; require weight ~127.89 lb, CG ~(0,0,28.01),
   rigid energy ~0. Then `scripts/solve_nominal.py` (to write): K0 = sum of all
   K blocks; T'KT, T'MT; scipy eigsh shift-invert sigma=-1e3, k~60; verify 6 RBMs
   ~0 Hz; compare elastic modes vs NASA FEM list above (expect few-% element-
   formulation error; report per-mode in `fem_assembly_report.md`, do NOT tune).
   Build observation operator at the 76 accel grids (basic frame, T maps to
   reduced DOFs; instrumentation grids are CBUSH/CONM2-mounted FEM grids 1101..);
   MAC our-nominal vs measured .ash shapes — pairing should reproduce NASA's
   test<->FEM pairing; this also validates the .ash frame assumption.
2. `scripts/reduce_model.py`: mass-orthonormal elastic basis V (~40-60 modes,
   RBMs projected out); per-PID reduced A_p = V' K_p V (small dense, save npz);
   reduction error: reduced vs full eigsh at nominal AND theta_g=0.8/1.2 probes
   (Discretization Resolution gate; near-degenerate pairs 122/124, 194/195 Hz —
   document eigh-gradient handling, eigenvalues are fine, shapes need care).
3. theta groups (D6 in decisions_log): start with 9: bottom_box(PSHELL 101-103),
   steel_welds(104-106), top_box(201-203), al_welds(204-206), angle_brackets
   (301-302), cross_beam(401), rect_plates(501)+top_brackets(601)+circ_plate(701)
   merged or separate, joints(PBUSH 801-807), contact(902). PBUSH 99 mounts FIXED.
   Grouping is per-PID at reduced level, so regrouping is free (sensitivity lever).
4. NUTS in `.venv_nuts` (jax 0.4.30, numpyro 0.15.3; FORCE jax_enable_x64 and
   assert dtype): likelihood on paired log-frequencies (sd: start 1-2%, ledger)
   + shape components/MAC on 132 DOFs (sd from burst-vs-impact scatter);
   lognormal priors on theta around 1 (width ~0.2-0.3); >=4 chains; convergence
   gate over ALL variables (R-hat<=1.05, ESS>=200, div<2%) or label failed.
   Mode pairing fixed per-iteration by MAC-to-nominal (document; card 5.3).
5. Held-out (card section 7 — THE deliverable): LOMO across elastic modes +
   band extrapolation (calibrate <=120 Hz: test modes 1-7; hold out 120-300).
   HASH predictions before grading (lock-before-reveal, `heldout_lock.json`).
   Output `heldout_qoi_table.csv` + side-by-side figure (median, 95% CI, actual,
   covers?, err%). Honest coverage reporting; misses are findings.
6. Sensitivity (grouping, basis size, noise sd, prior width, held-in band),
   `femap_handoff/` (nominal + posterior-mean theta NASTRAN decks + instructions),
   `check.py`+`checker_report.json`, `run_all.sh` (parse->assemble->solve->reduce
   ->NUTS->heldout->figures->checker), `runtime.json`, `packet.md` (method summary
   up top; tufte skill + scripts/tufte_lint.py on every plotting .py),
   `assumptions_ledger.md`, `quantity_contracts.md`, `question_framing.md`,
   `files_changed.md`, `manifest.json`, re-hash inputs.

## Environment notes (hard-won)
- System python3 (3.9): numpy/scipy/openpyxl OK — used for parse/assembly.
- `.venv_nuts` (repo root): jax 0.4.30/numpyro 0.15.3/numpy 1.26.4/scipy 1.10.1.
  It SEGFAULTS inside the Cursor sandbox — always run outside sandbox.
- Run scripts from the WORKSPACE ROOT: `PYTHONPATH=scripts python3 scripts/x.py`
  (outputs land at workspace root; fe_validate must run with cwd=scripts or fix paths).
- No pyNastran anywhere; not needed (own parser validated).
- CPU is fine for everything so far (assembly 15 s); reduced NUTS will be small.
