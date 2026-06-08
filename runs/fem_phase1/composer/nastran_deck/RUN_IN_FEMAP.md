# Run In Femap

Deck: `model/model.bdf`

1. Open Femap and import the Nastran bulk-data deck.
2. Confirm units are SI: m, kg, N.
3. Confirm the coordinate frame: origin at tray center, +z up, tray mid-plane at z = 0.098 m, feet fixed at z = 0.
4. Confirm model entities:
   - Tray: `CQUAD4` shell mesh, `PSHELL` thickness 0.0127 m, 6061-T6 material.
   - Struts: six `CROD` axial rods with tube area from 8 mm OD, 1 mm wall.
   - Joints: explicit apex `GRID`s tied to nearby tray shell nodes with `RBE2` translational components `123`.
   - Boundary: six foot nodes fixed in translation with `SPC1,20,123`.
5. Run SOL 103 using `EIGRL,10` for the first 10 modes.
6. Export the first 10 natural frequencies and first six mode-shape plots.
7. Update `results.json` with solved frequencies, mode-type labels from shapes, and mesh/refinement notes if you refine the shell mesh.

Checks to perform after solve: no zero/near-zero modes with fixed feet, report near-degenerate symmetric pairs if present, label suspension versus tray-flex versus strut-self from shapes, and label all rigid-joint frequencies as provisional upper bounds.
# Run in Femap / Nastran

1. Open `model/model.bdf` in Femap (or run MSC Nastran / NX Nastran with this bulk deck).
2. Verify SOL 103, EIGRL requests 10 modes, SPC1 fixes translations at foot nodes F0–F5.
3. Run normal modes. Export first 10 frequencies and plot first ~6 mode shapes.
4. Drop solved frequencies into `results.json` (`solved_by: human`); do not invent numbers before solve.

Units: SI (m, kg, N). Frame: tray center origin, +z up, tray top z = 0.098 m.
Tray: CHEXA solid 6061-T6. Struts: CROD axial, A = 22 mm².
