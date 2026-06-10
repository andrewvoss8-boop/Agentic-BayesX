# Decisions log — FIM identifiability analysis (file is source of truth, not chat)

## 2026-06-09
- HUMAN GO (Andrew, chat): "execute this item from the to do list" → the pre-test
  sensitivity/FIM identifiability analysis on the Opus tray FEM. This supersedes the
  prior to-do tag "Spec as an Opus runner task (awaiting human go)". Lead executes it
  directly as a bounded, artifact-backed numerical task.
- SCOPE: Fisher-information (local) + profile-likelihood (semi-global) identifiability,
  NOT a posterior sampler run. No NUTS/HMC claimed. Recorded so a compaction can't turn
  this into an overclaim.
- MODEL CHOICE: reuse the Opus Phase-1 JAX build (`runs/fem_phase1/opus/`) via its raw
  inputs `shared/spec.py` and element library `jax/code/fe_elements.py` (copied read-only
  into `inputs/`, SHA256 recorded). Re-expressed the assembly to track per-group stiffness
  contributions K_g; validated that at theta=1 it reproduces the build's nominal modes to
  <0.001 Hz (max |df| = 4.07e-4 Hz vs the published JAX frequencies).
- PARAMETER MENU (5): tray_E, strut_EA (axial), strut_EI (bending+torsion), joint_axial
  (along strut), joint_lateral (perp). Split strut axial/bending and joint axial/lateral
  on purpose — these splits are exactly where a near-axial suspension is expected to be
  sloppy, so they test the method honestly.
- METHOD: exact analytic eigenvalue sensitivities d(omega^2)/dtheta = phi^T K_g phi
  (mass-normalized modes), Fox–Kapoor mode-shape derivatives, FIM = J^T Σ^-1 J, eigendecomp
  for stiff/sloppy combos, column-pivoted QR for a max-independent observable basis,
  prior-regularized marginal posterior sd per parameter (honest per-parameter metric).
  Validated analytic dF against central finite differences (exact match).
- NUMERICAL FIXES (logged so they aren't re-hit):
  1. M is singular (rotational/drilling DOFs have stiffness but no mass) → solve
     M v = mu K v with the positive-definite K as "B" (mirrors build_jax), then mass-normalize.
  2. Profile likelihood: unconstrained least-squares drove theta negative → K indefinite;
     fixed by optimizing in LOG-space (theta = exp z > 0) with the chain-ruled analytic Jacobian.
  3. Profile was too slow with full 677-DOF eigensolves inside the optimizer → projected to a
     40-mode nominal reduced basis; reduction error to the lowest 8 modes = 0.0 Hz (nominal and
     a +20% stiffened case). This also serves the Discretization-Resolution gate.
- NOISE / PRIOR ASSUMPTIONS: freq sd = 1% + 0.5 Hz floor; 1-sensor log-residue sd = 0.15;
  2-sensor ratio rel sd = 0.10; prior sd on each (relative) theta = 0.30. All in
  `assumptions_ledger.md` with rationale; varied in the sensitivity sweep.
- HUMAN CHALLENGE (Andrew, chat): "aren't I and A fixed? why do we need EI and EA?" — correct that
  the tube geometry (A, I) is nominally known. CLARIFICATION (recorded): strut_EA / strut_EI are
  EFFECTIVE-stiffness multipliers, not attempts to infer A or I. They absorb (a) material modulus E,
  (b) end-fitting / joint moment-restraint reality vs the idealized moment-free joint, (c) wall-thickness
  tolerance (which moves A ∝ OD²−ID² and I ∝ OD⁴−ID⁴ by DIFFERENT amounts). Key point: IF the only strut
  unknown were material E with exact geometry, strut_EA and strut_EI collapse to ONE parameter strut_E
  (perfectly collinear). In THIS model they are NOT collinear — posterior correlation ≈ 0.01 — because
  axial stiffness drives the suspension modes (≤180 Hz) and bending stiffness drives the 542/570 Hz modes,
  so a full-band test can in principle separate an axial-stiffness error from a bending one (i.e. tell a
  true E error from an end-fixity/tolerance one). Offered to collapse to a single strut_E on request;
  would drop the structural-param count by one but not change the joints-blind / band-gated story.
- HUMAN Q (Andrew, chat): "would results differ if our prior on the joint were not as stiff?" — ran a
  nominal-joint-stiffness sweep (joint groups scaled, θ=1): softening the PHYSICAL joint from 1e9→1e6 N/m
  makes joint_AXIAL identifiable (marginal sd 0.30→0.023) and drops f1 84.8→21 Hz; joint_LATERAL stays
  blind (two-force-member geometry → ~no lateral joint load at any stiffness). Widening only the
  STATISTICAL prior width does nothing (n_ident stays 3 even at prior_sd=3.0; joint FIM eigenvalues
  ~1e-7/1e-11 are far below any threshold — no information to amplify). Confirms next_prompt.md rec #1.
- HEADLINE RESULT (artifact-backed): 3 identifiable directions / 3 individual structural
  parameters (tray_E, strut_EA, strut_EI) for a band reaching the 542/570 Hz tray-flex modes;
  band-conditional 1 (≤181 Hz) → 2 (≤371 Hz) → 3 (≤570 Hz). Both joint stiffnesses are
  unidentifiable from modal data (near-rigid + moment-free); robust across 0.5×–4× noise.
  Profile likelihood confirms (joints flat across ±30%). Same conclusion for 1-sensor vs
  2-sensor. The chosen payload-transmissibility QOI lies entirely in the identifiable subspace
  (fraction in sloppy subspace = 0.0) — good news, but QOI-specific.
