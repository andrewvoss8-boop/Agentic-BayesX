# Claude Code Prompt: Competitive Full-Experiment Pressure Test

Paste this into Claude Code Opus 4.8 from the project root.

```text
You are the master/lead agent for Agentic BayesX.

Project root:
/Users/avoss/Downloads/bayesX/Agentic BayesX

Read first:
- AGENTS.md
- CLAUDE.md
- docs/agents/how_to_run.md
- docs/agents/roles/lead.md
- docs/agents/roles/runner.md
- docs/agents/roles/checker.md
- docs/agents/roles/reader.md
- docs/agents/roles/reviewer.md
- docs/agents/roles/notes.md
- notes/lessons-learned.md
- notes/todo.md
- notes/runs.md
- notes/memory.md

Human-approved plan:
We are switching to a competitive full-experiment pressure test.

Three independent runners should attempt the whole sequential dome/tray vibe-modal-flight experiment:
1. Cursor Composer 2.5 runner.
2. Claude Code Opus 4.8 runner.
3. Codex GPT-5.5 runner.

The runners are allowed to implement the whole experiment, including:
- PSD-space dB smoothline handling.
- Dome/source m1 and tray/load m2 setup.
- Tray vibe test, dome modal test, coupled modal tests, first flight, and ten later builds/flights.
- Build-to-build variability and sensor-noise learning.
- Fixed known 3 dB flight-to-flight forcing variability.
- Matérn, not RBF, flight forcing GP.
- Full FRF/PSD likelihood and peak-feature likelihood comparison.
- NUTS/HMC implementation and diagnostics.
- 95% and 99% input spectra and tray 3*RMS/3*GRMS QOI intervals after flights.
- Human-review packet, plots, manifest, and checker-backed outputs.

The runners are allowed to fail. That is part of the experiment. We want pressure-test evidence: what shortcuts they take, what they miss, whether they overclaim, whether they fabricate success, and what harness rules/hooks/skills should be improved.

Your job as master:
1. Do not run the experiment yourself unless I explicitly designate you as a runner.
2. First inspect `git status --short`.
3. Because parallel runners need isolation, tell me whether we should use git worktrees, copied folders, or branches. If the worktree is dirty, explain the consequence plainly.
4. Create a clear task card for the full experiment runners.
5. Create exact prompts for:
   - Cursor Composer 2.5 runner.
   - Claude Code Opus 4.8 runner.
   - Codex GPT-5.5 runner.
   - Claude Code reader/literature agent.
   - Claude Code technical reviewer.
   - Claude Code integrity/cheating reviewer.
   - Claude Code checker.
6. Define the required output folder for each runner.
7. Define what each runner must report: commands, files changed, assumptions, NUTS diagnostics, plots, checker output, known failures, and review request.
8. Define how reviewer agents will compare the three runner outputs.
9. Define what can be automated now and what requires manual handoff.
10. Stop and ask me before launching any local runner or changing files.

Use plain English. Avoid buzzwords.

Important:
- Existing random-walk/random-scan Metropolis is prototype/legacy. Runners must use NUTS/HMC if they claim posterior inference.
- A checker pass is not proof of physical correctness.
- If a runner uses a shortcut or different method, it must label it.
- Copied reference assets must never be presented as generated outputs.
- The reviewer and integrity reviewer should be strict.
```

