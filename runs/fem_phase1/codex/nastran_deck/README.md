# Codex Femap/Nastran Deck

Generate from repo root:

```bash
python3 runs/fem_phase1/codex/nastran_deck/code_generate_nastran.py
```

This cell is not solved by the agent. It emits `model/model.bdf`, a geometry figure, and `results.json` with null frequencies and `solved_by: human`.

The deck uses CHEXA tray solids, CROD struts, and stiff CELAS2 translational joint springs instead of overlapping RBE2 dependent nodes.
