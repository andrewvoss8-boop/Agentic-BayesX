# Opus / Nastran DECK — Phase-1 hexapod normal modes (human solves)

A ready-to-run **SOL 103** bulk-data deck for Femap/Nastran. The agent built the model and
geometry but **did not solve it** — `results.json` keeps `frequencies_hz: null` and
`solved_by: human`. No frequencies were invented.

## Files
- `model/model.bdf` — SOL 103, EIGRL (first 10 modes).
- `RUN_IN_FEMAP.md` — step-by-step human solve + what to record back.
- `figures/nastran_geometry.png` — geometry render.
- `results.json` — schema with null solved fields (human fills after solving).

## Build (one command, generates deck + figure + results stub)
```bash
cd "$(git rev-parse --show-toplevel)/runs/fem_phase1/opus/nastran_deck/code"
../../.venv/bin/python make_bdf.py && ../../.venv/bin/python render_and_results.py
```

## Model (independent re-derivation; shares only shared/spec.py raw inputs)
- **Tray:** CQUAD4 shell (PSHELL t=12.7 mm), MAT1 6061-T6. Bare tray ≈3.086 kg.
- **Struts (×6):** CROD two-force rods (PROD: tube area + torsion J) — faithful moment-free
  spherical rod-end. (CBEAM with pin flags is an alternative; CROD is the clean two-force
  member and avoids the axial-spin DOF bookkeeping.)
- **Joints:** stiff CBUSH (PBUSH K1=K2=K3=1e9, K4=K5=K6=0 ⇒ moment-free), exactly the
  spec's "stiff CBUSH k≈1e9" explicit joint node ⇒ future parametric compliance.
- **Base:** SPC1 123456 at the 6 feet.
- **Solve (human):** SOL 103, EIGRL 10 modes, PARAM,AUTOSPC,YES.

## What I did / did not run
- DID: write the deck; render geometry; write the results schema + Femap instructions.
- DID NOT: solve it (that's the human's Femap run); invent any frequencies.

## Integrity
Independent re-derivation; only raw `shared/spec.py` inputs shared; no K/M, eigen-results,
or frequency tables imported from any other tool or agent.
