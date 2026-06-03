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
