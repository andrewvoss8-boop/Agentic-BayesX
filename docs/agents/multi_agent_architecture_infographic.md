# Multi-Agent Architecture Infographic

Infographic:

![Agentic BayesX multi-agent architecture](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/multi_agent_architecture_20260602.svg>)

## Roles

- **Human lead:** chooses the research question, approves plans, and decides what to trust.
- **Master agent:** turns the human goal into tasks, starts helper agents, compares results, and asks before changing project rules.
- **Experiment runners:** Cursor Composer 2.5, Claude Code Opus 4.8, and Codex GPT-5.5 each try the whole experiment in their own workspace.
- **Literature reader:** finds useful sources and explains what each source supports.
- **Technical reviewer:** checks physics, assumptions, units, plots, and whether the evidence matches the claim.
- **Integrity reviewer:** looks for copied outputs, hidden method changes, weak checks, and overconfident claims.
- **Framing challenger:** reviews runner results and asks whether the whole experiment is serving the right engineering decision. It proposes better questions, stronger QOIs, and higher-value next experiments, then reports back to the master.
- **Shared evidence folder:** where each runner leaves reports, commands, plots, diagnostics, checker output, and known failures.

The aim is not for every runner to be right. The aim is to make mistakes visible so the harness can improve.
