# MDOF + Agentic-FEM — Recon & Scope (2026-06-03)

Human direction: advance source & load from SDOF to MDOF; keep a SINGLE interface point between them;
QOI becomes a netCG QOI (interface force / mass). Research question: can an LLM set up and solve a FEM
to find the key transfer functions for the two components? Prefer agentic/autonomous; if truly
impossible, the human will build the component models himself. Decision/cost models are OUT for now.

## Recon findings (sources fetched this session via curl)
- TensorMesh — https://www.tensor-mesh.com , https://github.com/camlab-ethz/TensorMesh (ETH camlab).
  "A fast, differentiable, JIT-free, debugging-friendly finite element library for PyTorch."
  `pip install tensormesh-fem`. README references: Assemble (stiffness), elasticity, tetra/hex, beam,
  shell, 2D/3D, Eigen, Dynamic, Differentiable, PyTorch. => DIFFERENTIABLE FEM that plugs into NUTS/HMC.
- FEBio — https://febio.org , "FEBio Software Suite." Modal/linear/dynamic capability present, but it is
  a standalone (XML .feb) biomechanics/continuum solver, NOT differentiable; heavier to couple to
  Bayesian updating. Fallback only.
- Golestanian & Gomez — DuckDuckGo: "Golestanian, PhD in Computational Mechanics, Purdue"; "Gomez Lab -
  Purdue University Mechanical Engineering"; isogeometric analysis. Methodological reference (IGA /
  computational mechanics) for building component models; not a tool we run directly. (Direct Purdue
  page 404'd; relevance via their IGA work is [TO-VERIFY] in depth.)

## Tool ranking for THIS pipeline (differentiable forward model needed for NUTS)
1. TensorMesh (PyTorch, differentiable) — PREFERRED. Risk: young library; confirm it assembles a MASS
   matrix and supports a frequency-response / generalized-eigen solve, and installs on Python 3.9.6
   with the runners' torch. The spike tests exactly this.
2. First-principles analytical MDOF (lumped N-DOF chain, or modal superposition of a beam/plate) —
   GUARANTEED-FEASIBLE fallback, fully differentiable in torch/jax, fast, easy to validate. If the FEM
   spike fails, this keeps the experiment unblocked and still delivers realistic multi-mode FRFs.
3. scikit-fem / sfepy / FEniCS(dolfinx) — general Python FEM that assemble K,M for modal/FRF; scikit-fem
   is lightweight. Reasonable alternative if TensorMesh's dynamic path is immature.
4. FEBio — only if a true nonlinear-continuum solve is required and the differentiable options fail.

## Engineering scope (the ONLY change: SDOF -> MDOF per component, single interface)
- Source (dome, m1) and Load (tray, m2) each become MDOF (multiple internal modes) instead of SDOF.
- ONE interface DOF couples them (scalar interface force / motion). Coupling via frequency-based
  substructuring / impedance (combine the two components' interface FRFs).
- KEY transfer functions the agent must produce, per component, at the interface DOF:
  - source free-interface accelerance / apparent mass (and/or dynamic stiffness);
  - load interface apparent mass (fixed-base or free as defined);
  - coupled-system interface force under flight forcing.
- Everything else (PSD-space dB, Matern flight forcing, 3 dB f2f, -6 dB pre-data design envelope,
  staged data) carries over unchanged from round 2.

## QOI contract (netCG) — define precisely BEFORE plotting (quantity-contract gate)
- netCG QOI = NET CG ACCELERATION of the load = F_interface(omega) / m_load (rigid-body relation:
  net interface force divided by total load mass gives the load CG acceleration).
- PSD_{a_cg}(f) = PSD_{F_interface}(f) / m_load^2 ; 3*GRMS_netCG = 3*sqrt(integral PSD_{a_cg} df).
- Numerator = net interface force (N); denominator = load mass (kg); excitation = flight force at the
  source; BC = single interface coupling; units = (m/s^2 or g). This is the force-limited-vibration /
  apparent-mass framing (ties to NASA-HDBK-7004 and the narrow-band-exceedance thread).
- Reviewer must confirm: limiting behavior (low-freq -> rigid-body a_cg = F/m_total; resonances of each
  component appear in F_interface; apparent-mass antiresonance/notch behavior), units, and that netCG is
  distinct from the round-2 tray-response 3*GRMS.

## Recommended plan: FEASIBILITY SPIKE FIRST (de-risk before the competitive round)
1. SPIKE (one browser+code agent): attempt a minimal end-to-end FEM with TensorMesh (or scikit-fem):
   build ONE simple component (e.g., a cantilever beam or a plate), assemble K & M, solve modal +
   a single-interface FRF/apparent mass, and VALIDATE against an analytical benchmark
   (Euler-Bernoulli cantilever betaL = 1.875, 4.694, 7.855, ...; or a known lumped MDOF). Report
   honestly: did the LLM set up and solve a correct FEM? install pains? differentiability confirmed?
   Go/No-Go for FEM vs the analytical-MDOF fallback.
2. If GO: scope the two-component MDOF + single-interface coupling + netCG QOI, then run the
   competitive round (runs/round3/<tool>/ layout, PPT deliverable, all round-3 conventions).
3. If NO-GO: use first-principles analytical MDOF for the components (still agentic to BUILD), and
   record FEM-as-too-hard as a finding; the human's self-build is the last resort.

## Verification anchors (references gate)
- FEM/modal results MUST be checked against an analytical benchmark before acceptance (cantilever
  betaL natural frequencies; lumped MDOF eigenvalues). vibrationdata/Irvine MDOF examples are an
  accepted project reference. An LLM-built FEM that is "plausible but unvalidated" is not acceptable.

## SPIKE RESULT (2026-06-03): GO — two validated differentiable paths
Committed under runs/round3/spike/. Honest verdict from the feasibility agent:
- PATH A (recommended default): JAX Euler-Bernoulli beam. Benchmark error < 0.0011%, drive-point FRF
  antiresonance interlacing 4/4, ~0.33 ms/gradient, native to the project's JAX/numpyro NUTS stack.
- PATH B (GO, for continuum geometry): TensorMesh continuum FEM (installs on Python 3.13; P2 quadratic
  elements cure P1 shear-locking -> mode-1 error -0.026% vs EB). Caveats: dense eigen scales poorly
  (P2 @4561 nodes = 154 s; production NUTS needs sparse eigsh), and from_mesh(E=...) detaches the
  material gradient -> FIX: assemble unit K and scale by (E, rho) tensors (matches closed-form to 9e-7);
  geometry gradients are native. Continuum only (Line/Tri/Quad/Tet/Hex) -- a "beam" must be a slender
  2D/3D continuum (no EB beam / C1 shell elements).
- CAVEAT carried forward: only SINGLE simple components validated; the two-component MDOF +
  single-interface coupling + netCG QOI chain is scoped but NOT yet built or checker-backed.
- Round-3 method policy: DEFAULT to Path A (JAX EB / modal-superposition MDOF) for speed +
  NUTS-compatibility; ALLOW Path B (TensorMesh, P2 + E/rho-factoring + sparse eigsh) when a runner
  justifies that continuum/native-shape-gradient geometry is needed. Either way: validate against an
  analytical benchmark and show drive-point antiresonance interlacing before acceptance.

## FEM VISUALIZATION + EXPORT requirement (NEW, human-requested, round 3)
Every runner that builds an FEM/MDOF model must make the mesh INSPECTABLE by the human, via ALL of:
1. A human-readable "card": report/mesh/nodes.csv (node_id, x, y, z) + report/mesh/elements.csv
   (elem_id, type, connectivity node_ids). The simplest thing the human can eyeball / pull into tools.
2. A Femap-importable model: report/mesh/model.bdf -- NASTRAN bulk data (GRID + element cards), written
   via `meshio` (or directly). Femap reads NASTRAN bulk data (.bdf/.nas) and Femap neutral (.neu).
3. A general mesh file for Blender/ParaView: report/mesh/model.vtu (VTK) and/or a surface .obj/.stl,
   via `meshio` (one library converts NASTRAN <-> VTK <-> gmsh .msh <-> Abaqus .inp <-> STL/OBJ).
4. Rendered figures in report/figures/: the undeformed mesh AND the first ~3-5 mode shapes (deformed),
   via pyvista or matplotlib; embed key ones in the PPT.
Recommendation: standardize on `meshio` for (2)+(3) so one export covers Femap + Blender/ParaView, plus
the CSV card (1) and rendered PNGs (4). The runner states units and the coordinate frame. This lets the
human pull any AI-generated mesh into Femap on the other machine or into Blender, and audit it visually.
