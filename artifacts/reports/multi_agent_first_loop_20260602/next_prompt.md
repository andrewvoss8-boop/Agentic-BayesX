# Next Prompt

After the first proof-of-concept loop passes its scaffold checks, ask the Claude Code lead:

```text
Use the first-loop packet in `artifacts/reports/multi_agent_first_loop_20260602/`.

Summarize:
1. which commands ran;
2. which checks passed or failed;
3. what the reviewer found;
4. what remains human judgment;
5. the single best next loop.

Do not update notes until I approve.
```

Likely next loop: choose a NUTS/HMC implementation path for the fresh 2DOF Bayesian update. Compare PyMC, NumPyro, BlackJAX, and Stan in a short tool-choice note before editing code.

