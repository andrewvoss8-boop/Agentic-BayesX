# Using Codex with Agentic BayesX

Work directory (always start here):

```bash
cd "/Users/avoss/Downloads/bayesX/Agentic BayesX"
export PYTHONPATH=.
```

Codex reads `AGENTS.md` automatically when launched in this folder.

## One-command baseline (human or agent)

```bash
bash scripts/run_pipeline.sh
open artifacts/plots   # macOS: view PNGs
```

Plots land in `artifacts/plots/`:
- `nominal_2dof_frfs.png`
- `key_2dof_transfer_functions_linear.png`
- `synthetic_channels.png`
- `posterior_vs_truth.png`
- `posterior_channel_fit.png`
- `mcmc_traces.png` (if MCMC samples exist)
- `mdof_frf_comparison.png`

Human-review packets land in `artifacts/reports/`:
- `synthetic_statfem_packet.md`
- `key_frf_summary.json`
- `sensitivity_assumptions/sensitivity_assumptions.md`
- `figures/model_schematic.png`
- `figures/experimental_workflow.png`
- `figures/error_taxonomy.png`
- `figures/error_hyperparameters.png`
- `figures/channel_truth_vs_observed.png`
- `figures/channel_absolute_error.png`
- `figures/channel_error_vs_truth.png`
- `figures/gp_discrepancy_samples.png`
- `figures/parameter_error_summary.png`
- `figures/question_framing.png`
- `figures/qoi_uncertainty.png`
- `figures/qoi_samples.png`
- `figures/sampler_diagnostics.png`

Lab-facing workflow notes live in `docs/lab/`:
- `apparent-mass-convention-postmortem.md`: root-cause analysis for a caught apparent-mass convention error.
- `log-frequency-plot-gp-postmortem.md`: root-cause analysis for a missed log-frequency plotting convention and the correction to a log-frequency GP.

Reusable harness guidance lives in `docs/harness/`:
- `agentic-engineering-quality-gates.md`: broad gates for assumptions, standards checks, quantity contracts, plots, sensitivity, and fresh-agent reruns.

## Three Codex modes

Pick one prompt file and paste its contents as your first message in Codex:

| Mode | Prompt file | Goal |
|------|-------------|------|
| Replicate | `docs/codex_prompts/replicate.md` | Re-run pipeline, match checker outputs |
| Review | `docs/codex_prompts/review.md` | Audit code, assumptions, gaps; no big refactors |
| Extend | `docs/codex_prompts/extend.md` | Next engineering steps with harness gates |
| Fresh 2DOF | `docs/codex_prompts/fresh_2dof_rerun.md` | Start the toy workflow again in a new agent using broad quality gates |

Launch Codex (example):

```bash
cd "/Users/avoss/Downloads/bayesX/Agentic BayesX"
codex
# paste prompt from docs/codex_prompts/<mode>.md
```

Optional: use `--dangerously-bypass-approvals-and-sandbox` only if you accept full local execution risk (Bilionis uses this for long autoresearch loops).

## Hard rules for any Codex trial

1. Do not edit files listed in `harness/checkers/manifest.sha256` during a gated trial.
2. Success requires checker exit code 0 and artifacts on disk.
3. Log decisions in `notes/runs.md`.
4. No success claims from plots alone; tests/checkers must pass.
5. For every named structural-dynamics quantity, state numerator, denominator, coordinate, excitation, boundary condition, units, expected limiting behavior, and expected resonance behavior before accepting a plot.
6. Frequency-domain review plots should use log-scaled frequency axes unless the artifact explicitly justifies linear Hz.
7. The current synthetic discrepancy GP is squared-exponential in natural log frequency, not linear Hz.
8. Every run must expose actual numerical assumptions and hyperparameters, preferably in both tables and figures.
9. Every run must include a sensitivity pass or a clear, checker-visible explanation of why sensitivity is out of scope.
10. Every run must identify relevant standards/benchmarks/references; if a prompt mentions one, compare against it before accepting outputs.
11. Probabilistic structural-dynamics packets must start with a method summary and run-specific graphical model that state inferred variables, fixed assumptions, non-inferred latent variables/hyperparameters, data/replicate count, and whether the likelihood uses whole FRF/PSD/time-history data or peak/feature summaries.
12. Generated review figures need image-legibility QA. Text-heavy figures must be checked for readable font size, clipping, overlapping text, and plain underscore/caret equation strings.

## Suggested first session (beginner-friendly)

1. Run `bash scripts/run_pipeline.sh` and open plots.
2. Codex **Review** prompt: ask for a short report on MCMC acceptance rate, identifiability, and what's missing vs StatFEM paper.
3. Codex **Extend** prompt: pick one item only (e.g. posterior credible intervals, or separate ch2/ch3 channels).
4. Open `artifacts/reports/synthetic_statfem_packet.md` for the meeting-ready summary and human reflection prompts.

## What is already done vs what Codex should do

| Done (Cursor bootstrap) | Good Codex tasks |
|-------------------------|------------------|
| Harness + canary checker | Improve harness ergonomics |
| 2DOF synthetic + MCMC prototype | NUTS/HMC, better priors, PPC plots |
| Basic MDOF reduction test | FEM export pipeline stub |
| Static PNG visualizations | Interactive dashboards, LaTeX report |

Human role: choose the problem, interpret plots, decide which extension is worth the summer.

## Multi-agent proof of concept

Plain-English scaffold docs live in `docs/agents/`. Claude Code is the intended lead agent, while Codex and Cursor can be launched manually as helpers for running, checking, reading, reviewing, or notes updates.

Use `docs/agents/claude_code_starter_prompt.md` to start Claude Code. Use prompts in `docs/codex_prompts/multi_agent/` when the lead asks for a Codex helper.

Sampler standard: future Bayesian updating work should use NUTS/HMC by default. Existing random-walk/random-scan Metropolis outputs are prototype/legacy and should be labeled that way.
