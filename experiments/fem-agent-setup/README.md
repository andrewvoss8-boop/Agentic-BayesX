# FEM Agent Setup Prototype (Phase 3)

Purpose: evaluate whether an LLM workflow can reliably set up simple FEM/MDOF transfer-function studies with verifiable outputs.

## Scope
- Start with simple, script-generated matrix models (`src/mdof/reduced_transfer.py`).
- Add external FEM tools only after checker-gated baseline passes.
- Candidate tools to evaluate:
  - FEBIO
  - tensor-mesh (or equivalent mesh/FEM pipeline)

## Required artifacts per trial
- Model setup script(s).
- Generated mass/stiffness/damping matrices.
- Transfer-function outputs.
- Checker reports with deterministic metrics.

## Hard constraints
- No claims based on screenshots/manual interpretation only.
- All outputs must be reproducible from command line.
- Keep tool-specific assumptions and failure modes logged in `notes/runs.md`.
