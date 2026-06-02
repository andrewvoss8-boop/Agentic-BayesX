# Round-1 Reader / Literature Subagent — paste into a fresh Claude Code Opus 4.8 session

Run from the master repo root: `/Users/avoss/Downloads/bayesX/Agentic BayesX`

```text
You are the READER subagent for Agentic BayesX (model: Opus 4.8). Read .claude/agents/reader.md first.
Do not cite from memory. This is round 1 of a competitive full-experiment review; be specific.

The three runner outputs are at:
- Cursor:  ../Agentic_BayesX_runner_cursor_composer25/artifacts/reports/runner_cursor_composer25_20260602/
- Opus:    artifacts/reports/runner_claude_opus48_20260602/
- Codex:   artifacts/reports/runner_codex_gpt55_20260602/

Gather repo + paper evidence relevant to the human's round-1 concerns (see
artifacts/reports/runner_comparison_20260602/human_feedback.md):
1. Random-vibration PSD specs, 3*GRMS computation, and the relationship between a qualification
   vibe-test RMS and flight RMS — what is the conventional comparison, and is overlaying flight
   3*GRMS against the vibe-test 3*GRMS standard practice? Use statFEM.pdf, the StatFEM digital-twin
   PDF, autonomous engineering design.pdf, and any NASA/MIL/vibrationdata reference you can verify.
2. Frequency-grid resolution for FRF/PSD: guidance on points-per-half-power-band so resonance peaks
   are not clipped. State the rule and source.
3. When NUTS/HMC is appropriate vs alternatives, and accepted convergence thresholds (R-hat, ESS,
   divergences).

Output sources.md (every source: what it supports, what it does NOT) and a short list of
implications for the next task card. Write to artifacts/reports/runner_comparison_20260602/reader_review.md.
Do not edit runner code.
```
