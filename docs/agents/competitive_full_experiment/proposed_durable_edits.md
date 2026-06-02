# Proposed Durable Edits (for human approval) — 2026-06-02

These are problem-class-general additions for AGENTS.md and CLAUDE.md, drawn from round-1 evidence and
the four reviews. They contain NO problem-specific content (no dome/tray, no specific plot). They are
NOT yet applied. Approve, edit, or reject. Checker-code changes are described but also not applied
(immutable-checker rules + "no checker change during a trial").

---

## A. Add to AGENTS.md and CLAUDE.md — Sampler convergence gate (extends the NUTS/HMC rule)

> ### Convergence Gate
> - "NUTS/HMC active" requires PASSING convergence diagnostics, not just that a sampler ran. Report
>   R-hat and ESS over ALL sampled variables, including raw hierarchical latents — not only headline
>   marginals.
> - Default acceptance (state and justify any deviation): max R-hat <= 1.05 (prefer <= 1.01 where a
>   primary source supports it), min ESS >= 200 for reported parameters (document nuisance latents),
>   and divergence fraction < 2%. Use >= 4 chains and a non-centered parameterization for hierarchical
>   variance models unless justified otherwise.
> - If convergence fails, the run must NOT report a clean "pass" or "NUTS active"; surface the
>   worst-case R-hat/ESS next to any interval, and label the intervals as not-yet-converged.

## B. Add to AGENTS.md and CLAUDE.md — Sampler decision + honesty

> ### Sampler Decision
> - NUTS/HMC is the default. If the sampler library is unavailable, either install it in an isolated
>   environment or use a clearly labeled alternative WITH a stated reason. Never present a non-NUTS
>   sampler as NUTS. (Honest labeling of a fallback is acceptable; misleading success framing is not.)
> - NUTS/HMC needs a differentiable forward model and likelihood; if features (e.g. peaks/argmax) are
>   non-differentiable, document the smoothing/relaxation used and its effect.

## C. Add to AGENTS.md and CLAUDE.md — Priority-deliverable clarification gate

> ### Priority Deliverables and Clarification
> - At task start, restate the human/master's PRIORITY deliverables and acceptance criteria in your
>   own words, and flag any ambiguous or underspecified ask.
> - If a priority ask is ambiguous, ask for clarification BEFORE building. If you cannot ask mid-run,
>   state the assumption prominently and, where cheap, produce both interpretations.
> - Record a priority_deliverables.md listing each priority ask, its interpretation, and where it was
>   delivered. A priority with no delivered artifact is a failure; an "assumed" interpretation without
>   confirmation is a warning.
> - The harness must NOT encode any specific problem's deliverables; those belong in the task
>   card/runner prompt. The harness only ensures priorities are surfaced, clarified, and met.

## D. Add to AGENTS.md and CLAUDE.md — Discretization-resolution gate (generalizes the freq-axis gate)

> ### Discretization Resolution
> - Treat the analysis grid/resolution (frequency, time, or mesh) as a first-class documented
>   assumption: spacing, log/linear, and a rationale tying it to the features that drive the QOI.
> - Show the QOI-driving features are adequately resolved, OR justify a coarser grid INCLUDING the
>   runtime/accuracy tradeoff (finer is not free and may be intractable).
> - Provide a resolution sensitivity result (refine near the QOI-driving features; report the
>   QOI/posterior shift) or a justified intractability note with a bounded error estimate.
> - The harness does not mandate a fixed points-per-feature number; specific targets belong in the
>   task card.

## E. Add to AGENTS.md and CLAUDE.md — Runtime accounting

> ### Runtime Accounting
> - Record runtime.json with active_runtime_s (sum of per-command execution time) and
>   elapsed_wallclock_s. Cross-runner comparison uses active_runtime_s so human-approval wait does not
>   distort it. active_runtime_s <= elapsed_wallclock_s.

## F. Add to docs/agents/how_to_run.md (operational, not a rule) — Runner isolation + auto-run

> ## Runner Isolation and Auto-Run
> - Each runner works in its own disposable copied workspace and asserts its working directory at
>   start; it refuses to run in the master repo.
> - Because the workspace is disposable and immutable checker hashes are verified afterward, runners
>   may auto-execute within it: Claude Code `--dangerously-skip-permissions`; Codex full-auto/no-approval;
>   Cursor Agent Auto-Run. Never enable auto-run in the master repo. Confirm exact flags in-app.

---

## Proposed checker changes (described; NOT applied during a trial)
- Runner checker should gate on the convergence diagnostics in (A) over all sampled variables.
- Runner checker should verify priority_deliverables.md and runtime.json exist and are well-formed.
- Image-legibility hook should FAIL any figure/panel with >1 series and no legend, and flag dual-axis
  panels without combined labeling.
These touch checker expectations; apply only between trials with explicit approval, and re-hash the
immutable manifest if a protected file changes.

## Note on references
Several thresholds (R-hat 1.01 vs 1.05, ESS floors, points-per-half-power-band, qualification dB
margins) are flagged [TO-VERIFY] by the reader review against primary sources (Stan manual / Vehtari
et al. 2021; GEVS/NASA-STD-7001; Irvine/vibrationdata). Confirm citations before hard-coding numbers.
