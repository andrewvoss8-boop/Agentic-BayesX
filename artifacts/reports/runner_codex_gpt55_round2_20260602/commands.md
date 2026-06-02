# Commands

Actual workspace assertion:

```bash
pwd
# /Users/avoss/Downloads/bayesX/Agentic BayesX
```

Venv package repair attempted before the replay script:

```bash
.venv_nuts/bin/pip install --quiet --disable-pip-version-check 'arviz<0.19'
.venv_nuts/bin/pip install --quiet --disable-pip-version-check 'scipy<1.13'
```

One-command replay:

```bash
bash artifacts/reports/runner_codex_gpt55_round2_20260602/run_round2.sh
```

Immutable checker verification:

```bash
shasum -a 256 -c harness/checkers/manifest.sha256
```

Runtime recorded in `runtime.json`: active `293.86` s, elapsed `293.87` s.
