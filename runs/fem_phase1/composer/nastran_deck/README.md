# Composer Femap/Nastran Deck

Generate from repo root:

```bash
python3 runs/fem_phase1/composer/nastran_deck/code_generate_nastran.py
```

This build is intentionally not solved by the agent. It emits a ready-to-run SOL 103 deck at `model/model.bdf`, a geometry figure, and `results.json` with null frequency fields and `solved_by: human`.

Model: CQUAD4 shell tray, CROD axial struts, RBE2 translational joint ties, fixed foot translations, bare tray mass case. Rigid-joint frequencies from the human solve should be labeled provisional upper bounds.
