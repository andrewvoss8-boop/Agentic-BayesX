# Support Prompt — Reader / Literature Agent (Claude Code Opus 4.8)

Run AFTER the three runners finish. Read-only on runner outputs. Paste the block below and supply
the three runner output folder paths.

```text
You are the READER for Agentic BayesX. Read .claude/agents/reader.md first. Do not cite from memory.

Gather repo + paper evidence for the sequential dome/tray vibe-modal-flight problem from:
- statFEM.pdf
- digital-twinning-of-self-sensing-structures-using-the-statistical-finite-element-method.pdf
- autonomous engineering design.pdf
- any standard relevant to random-vibration PSD specs, GRMS computation, Matern-GP forcing models,
  and 3*RMS/3*GRMS QOI conventions.

For each runner output folder (paths provided by the human), check whether claimed conventions
(PSD-space dB factor = 10**(dB/10), GRMS, Matern vs RBF forcing, 3*RMS QOI, 95%/99% intervals)
match cited sources, units, and boundary conditions.

Output:
- sources.md: every source, what it supports, what it does NOT support.
- A short list of implications and any runner that cited nothing or mismatched units/BCs/conventions.
Do not edit runner code.
```
