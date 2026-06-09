# Decisions Log (file-based, survives compaction)

- D1 (2026-06-09): Workspace = `artifacts/reports/shocksat_fem_modal_twin_20260609/`.
  CWD asserted: not master repo root. Inputs hashed at start (`inputs_sha256_start.json`, 50 files).
- D2: Task 0 resolved — measured modes = `Final_FF_Test_Shapes_100121.ash`
  (extracted from `sources/FEM_and_CAD.zip` into my `inputs/`; sibling workspace
  untouched). Evidence in `measured_modes_provenance.md`. The card said the
  observation layer is modal correlation; with real shape vectors found, the
  freq+shape likelihood the card asked for is feasible.
- D3: Calibration measured set = impact-hammer .ash (NASA's correlation basis),
  not burst xlsx; burst run-to-run scatter -> noise floor evidence.
- D4: Assembly path = option (a) of the card: parse NASTRAN bulk data and
  assemble in Python (vectorized numpy -> scipy sparse). Reason: gives exact
  per-group K_g, full control of the theta parameterization, no solver-export
  format risk; cost = element-formulation mismatch vs NX Nastran CQUAD4,
  which is measured against NASA's published final-FEM frequencies and reported.
- D5: Element formulations: flat-facet shell = Q4 membrane (+drilling penalty
  mimicking PARAM,K6ROT,100) + MITC4 bending for CQUAD4; CST membrane + DKT
  bending for CTRIA3. Consistent mass from shell density + NSM=0; CONM2 with
  offsets via rigid-offset transform. RBE2 (CM=123 spiders and any 123456) via
  MPC elimination transform T. CBUSH 6x6 springs in CID frames (zero-length).
- D6: theta parameterization: K(theta) = sum_g theta_g K_g with part groups =
  include-file structure (boxes, brackets, cross-beam, plates, circular plate,
  joints, contact). Mass NOT scaled (geometry/density trusted from as-weighed
  checks in NASA pptx slides 54-62).
- D7 (session 1 end, BLOCKER + recommended fix): RBE2 double-dependency found
  during assembly: structure grids (e.g. 2022336) are dependent both in joint
  spider RBE2s (CM=123) and in `Shock_Test_Instrumentation.blk` RBE2s, which use
  the 9900xxx shock-accel grid as INDEPENDENT and 4 structure grids as dependent
  (verified in raw deck, lines 42-69). Recommended: drop that include (massless,
  stiffness-free shock response points, irrelevant to the modal twin) including
  its 37 grids. Not yet implemented — see next_prompt.md.
- D8: Element-sign lesson: Mindlin beta->NASTRAN rotation map is bx=-thy,
  by=+thx; rigid-tilt vector tests added because zero-eigenvalue counts cannot
  detect sign-convention errors (they break box-corner coupling silently).

(Later decisions appended below as they are made.)
