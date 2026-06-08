# RUN_IN_FEMAP — Phase-1 hexapod normal modes (human solves this deck)

This is a **ready-to-run** MSC/NX Nastran deck. The Opus agent built the model but did
**not** solve it — there are no agent-invented frequencies. You run SOL 103 in Femap (or
Nastran directly), then fill the solved numbers into `results.json`.

## Files
- `model/model.bdf` — the bulk-data deck (SOL 103, EIGRL, first 10 modes).
- `figures/nastran_geometry.png` — geometry render for a quick visual sanity check.

## Model summary (so you can audit it before solving)
- **Units:** SI (m, kg, N). **Frame:** origin at tray center, +z up, tray plane z=0.098 m,
  base z=0.
- **Tray:** CQUAD4 shell, PSHELL t=12.7 mm, MAT1 6061-T6 (E=68.9 GPa, ν=0.33, ρ=2700).
  Bare tray, no ballast (≈3.086 kg).
- **Struts (×6):** CROD two-force rods (PROD: A≈22 mm², J for the 8 mm OD / 1 mm wall tube).
  A rod is moment-free, i.e. the spherical rod-end.
- **Joints:** stiff CBUSH (PBUSH K1=K2=K3=1e9 N/m, K4=K5=K6=0 ⇒ moment-free) between each
  tray apex grid and the coincident rod-top grid. This is an explicit joint node, so later
  you can drop K to a finite value to add joint compliance.
- **Base:** SPC1 123456 at the six feet (grounded).
- **PARAM,AUTOSPC,YES** removes the massless rod-top rotational DOF (expected; harmless).

## Solve in Femap (one path)
1. **File → Import → Analysis Model**, choose `model.bdf` (or **File → Open** the .bdf).
2. Confirm Femap created: the shell tray, 6 CROD struts, 6 CBUSH joints, SPC at the feet,
   one EIGRL (10 modes), and the SOL 103 analysis set.
3. **Model → Analysis** → verify the analysis type is **Normal Modes/Eigenvalue (SOL 103)**
   and the eigen method (Lanczos) requests 10 modes; **Analyze**.
4. When it finishes, **PostProcessing**: step through modes 1–10, set deformation animation.
5. (Optional) **List → Output → Results** to dump the eigen-frequencies.

## What to record back into results.json
For each of the first ~10 modes:
- `frequencies_hz` — the solved natural frequencies (Hz).
- `mode_type` — from the shape, label each: **suspension** (tray moves ≈ rigidly on the
  struts), **tray-flex** (the tray plate bends; expect a dense corner/edge-flap set), or
  **strut-self** (a single strut vibrating — not expected with CROD, which has no bending).
- `near_degenerate_pairs` — the true-120° symmetry should give **near-degenerate mode
  pairs**; report them. A missing pair would flag a broken-symmetry geometry bug.
- `mesh_convergence` — re-mesh finer in Femap (smaller element size) and report the shift
  of the first ~10 modes.

## Sanity checks (no pre-loaded frequency target — on purpose)
- **No zero/near-zero modes** (base is fixed). If you see ~0 Hz modes beyond what AUTOSPC
  removes, the model lost a constraint.
- **Near-degenerate pairs present** (120° symmetry).
- The Opus solved builds (for cross-reference, **not** a target to match): the four
  **suspension** modes landed at ≈ **85, 86, 182, 290 Hz** across three independent engines
  (CalculiX C3D8I solid + truss, TensorMesh H8 solid + truss, JAX ACM-plate + beam). The
  first **tray-flex** appeared at 337 Hz (CalculiX C3D8I) / 371 Hz (JAX plate) / 374 Hz
  (TensorMesh locked H8) — element-theory spread. Expect your shell-tray result to sit in
  that family; **explain** any large divergence (mesh, shell vs solid, element theory)
  rather than tuning to it.

## Labels / honesty
All rigid-joint frequencies are a **PROVISIONAL UPPER BOUND** — real compliant joints lower
them. Out of Phase-1 scope: damping, complex/FRF, force-limiting, source-plate coupling, NUTS.
