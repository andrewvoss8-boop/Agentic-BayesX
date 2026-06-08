# Decisions Log

## D1: Correct agent workspace

This is the GPT-5.5/Codex builder run, so all artifacts belong under `runs/fem_phase1/codex/<tool>/`.

## D2: Element choices

- TensorMesh and JAX: solid tray cells plus axial truss/two-force struts, fixed base feet, explicit apex joint nodes, and distributed stiff translational ties to nearby tray nodes.
- CalculiX: C3D8 solid tray plus T3D2 truss struts, with distributed `*EQUATION` ties at apex nodes.
- Femap/Nastran deck: CHEXA tray, CROD struts, CELAS2 translational joint springs, fixed foot translations. CELAS2 avoids the overlapping-RBE2 dependent-node fatal seen in the earlier Composer deck.

All rigid-joint frequencies are provisional upper bounds.

## D3: CalculiX parser correction

CalculiX `.dat` frequency rows contain mode, eigenvalue, rad/time, cycles/time, and imaginary rad/time. The parser uses the cycles/time column. A temporary parse of the final imaginary column produced near-zero fake frequencies and was corrected before final validation.
