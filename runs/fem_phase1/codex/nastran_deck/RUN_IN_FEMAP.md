# Run In Femap

Deck: `model/model.bdf`

1. Import the deck into Femap/Nastran.
2. Confirm SI units: m, kg, N.
3. Confirm frame: origin at tray center, +z up, tray mid-plane z = 0.098 m, base feet fixed at z = 0.
4. Confirm the joint idealization: each strut apex uses three stiff `CELAS2` translational springs to the nearest tray solid node. There should be no overlapping RBE2 dependent-node fatal.
5. Run SOL 103 with `EIGRL,10`.
6. Export first 10 frequencies and first six mode-shape plots.
7. Update `results.json`; leave rigid-joint frequencies labeled as provisional upper bounds.

Post-solve checks: no zero/near-zero fixed-base modes, near-degenerate symmetric pairs if present, mode-type labels from shapes, and mesh/refinement notes.
