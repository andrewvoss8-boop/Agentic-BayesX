# Agentic BayesX

Harness-first workflow for agentic scientific computing in structural dynamics.

## Structure
- `AGENTS.md` / `CLAUDE.md`: persistent agent contract.
- `harness/`: immutable checker-gated trial runner.
- `src/twodof/`: 2DOF FBS/StatFEM synthetic model + data generation.
- `src/inference/`: full-MCMC prototype for parameter/posterior recovery.
- `src/mdof/`: reduced-order MDOF transfer-function prototype.
- `tests/`: deterministic validation scripts.
- `notes/`: continuity memory and run logs.

## Quick start
From repo root:

```bash
export PYTHONPATH=.
bash scripts/run_pipeline.sh          # tests + MCMC + plots
python3 scripts/visualize_results.py  # plots only
open artifacts/plots                  # macOS
```

The full pipeline also writes a human-review packet at
`artifacts/reports/synthetic_statfem_packet.md` with companion figures under
`artifacts/reports/figures/`. Key 2DOF FRFs are also summarized in
`artifacts/reports/key_frf_summary.json` and plotted in linear units at
`artifacts/plots/key_2dof_transfer_functions_linear.png`, including
7004C-style source and load apparent masses.

Codex: see [docs/CODEX.md](docs/CODEX.md) and `docs/codex_prompts/{replicate,review,extend}.md`.

Multi-agent proof of concept: see [docs/agents/how_to_run.md](docs/agents/how_to_run.md).

Sampler note: future Bayesian updating work should use NUTS/HMC by default. Existing random-walk/random-scan Metropolis artifacts are prototype/legacy outputs unless a later checker-backed run says otherwise.

Lab-facing agentic workflow notes live in [docs/lab/](docs/lab/), including the
[apparent mass convention postmortem](docs/lab/apparent-mass-convention-postmortem.md).

## Policy
- No claim without checker output.
- No mutable checker loopholes.
- Assumptions and limitations must be documented.
