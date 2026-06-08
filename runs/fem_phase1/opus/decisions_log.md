# Opus builder — Phase-1 hexapod FEM — decisions log

Runner workspace decisions (file is source of truth; chat is a cache).

## 2026-06-08
- HUMAN DECISION (Andrew, chat): "yes run it. work the specific element options
  available in each tool faithfully to best FEM practice in that tool and the actual
  structure." => Build all four tools as the Opus builder; per-tool element choices
  must reflect that engine's best practice and the real hardware, not a lowest-common-
  denominator copy. Implicit approval to install required tools (3 of 4 not present).
- ENVIRONMENT (found): macOS, system Python 3.9.6, pip 21.2.4, no brew, no conda.
  Present: numpy, scipy. Absent: jax, discretize, meshio, pyvista, ccx (CalculiX).
  Network to pypi works.
- DECISION env isolation: create an isolated venv at runs/fem_phase1/opus/.venv for the
  Python tools (jax, discretize, matplotlib). Rendering via matplotlib 3D (reliable,
  headless) instead of pyvista/VTK off-screen. Write a small .frd/.dat parser rather than
  depend on meshio. CalculiX: install via miniforge/conda-forge into an isolated prefix
  under the run dir (no global install). If ccx cannot be installed in-sandbox, label
  CalculiX as deck-built-but-not-solved-here and say so honestly (do NOT fabricate freqs).

## INTEGRITY RULE compliance plan
- Shared INPUTS only (identical, allowed): node coordinates, materials, section props,
  masses, BCs -> placed in a read-only spec each tool imports for raw numbers.
- Each tool INDEPENDENTLY assembles its own K/M and solves. No porting of assembled
  matrices, eigen-results, or frequency tables between tools or agents. No tuning one
  tool to match another. Documented per tool.

## Fidelity choices per tool (to confirm/adjust as build proceeds)
- CalculiX: solid or shell tray (C3D20R / S8R) + B31/B32 beam struts + spring joints
  (SPRING/ DASHPOT or rigid *MPC), *FREQUENCY (Lanczos). Best-practice 3D FE.
- TensorMesh (discretize): structured hex tensor mesh of the solid tray; assemble 3D
  linear-elastic hex K and consistent/lumped M on the node grid; struts as 3D bar
  (truss) members tying tray apex nodes to fixed feet; scipy.sparse.linalg.eigsh
  (shift-invert). Sparse generalized eigensolve.
- JAX: hand-assembled differentiable forward model. 3D Euler-Bernoulli/Timoshenko beam
  struts with spherical end releases (moment release) + stiff joint springs + tray as
  plate/shell mesh (or rigid+lumped if mesh is intractable dense). Dense eigh. Eigensolve
  only this phase (no NUTS).
- Nastran DECK: .bdf SOL 103 EIGRL ~10 modes, CHEXA/CQUAD4 tray + CBAR/CBEAM struts +
  CBUSH joints + SPC base. RUN_IN_FEMAP.md. solved_by: human, freqs null.
