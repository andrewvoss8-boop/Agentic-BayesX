# Run in Femap / Nastran

1. Open `model/model.bdf` in Femap (or MSC/NX Nastran).
2. Verify SOL 103, EIGRL requests 10 modes, SPC1 fixes translations at foot nodes.
3. Run normal modes; plot first ~6 mode shapes.
4. Record solved frequencies in `results.json` (`solved_by: human`).

Units: SI (m, kg, N). Frame: tray center origin, +z up, tray top z = 0.098 m.
