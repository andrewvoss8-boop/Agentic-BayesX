# Assumptions

| Assumption | Value | Units | Source | Rationale | Sensitivity Priority |
|---|---:|---|---|---|---|
| First loop changes science model | No | n/a | Human request | Keep the first proof of concept focused on coordination. | High |
| Main payload | `bash scripts/run_fresh_2dof_statfem_fbs.sh` | command | Existing repo | Reuses current fresh 2DOF workflow. | High |
| Default future sampler | NUTS/HMC | method | Human request | Avoid vague "MCMC" language and make the intended sampler explicit. | High |
| Current sampler status | random-walk/random-scan Metropolis is prototype/legacy | method | Existing code/docs | Existing outputs should not be mislabeled as NUTS/HMC. | High |
| Helper launch | Manual by human | n/a | Human request | Good enough for first proof of concept. | Medium |
| Claude Code lead | Enabled through `.claude/settings.json` and `.claude/agents/lead.md` | n/a | Scaffold choice | Makes the intended lead explicit for Claude Code sessions that support project agents. | Medium |

