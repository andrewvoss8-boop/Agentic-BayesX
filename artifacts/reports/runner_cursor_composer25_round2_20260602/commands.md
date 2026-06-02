# Commands — Cursor Composer 2.5 round 2

```bash
bash scripts/run_runner_cursor_composer25_round2.sh
```

Isolated workspace: `Agentic_BayesX_runner_cursor_composer25_r2` (not master repo).

NUTS via `.venv_nuts` (numpyro). arviz: yes.

Sequential GIF: first pass ran 11 NUTS fits (warmup=400, samples=400 each, ~10 min wall). Final replay skipped sequential MCMC when `07_*.gif` already existed.

`runtime.json` active_runtime_s (~223 s) is the final replay only; see `runtime.json` note for first-pass wall (~783 s including sequential GIF).
