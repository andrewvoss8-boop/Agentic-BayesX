# Proposed Harness / Skill / Hook Improvements — 2026-06-02

PROPOSALS ONLY. Per project rules, durable files (AGENTS.md, CLAUDE.md, checkers, notes) are NOT
edited without explicit human approval. This list is evidence for the next iteration.

## 1. Convergence gate in the checker (highest priority)
Evidence: 2 of 3 runs "passed" with non-converged posteriors (Cursor R-hat 1.83 / ESS≈3; Codex
R-hat up to 4.57). The checker only checks artifact existence + hashes + a `nuts_active` boolean.
Proposal: the runner checker must FAIL (or hard-WARN) when, over ALL sampled variables including raw
hierarchical latents: max R-hat >= 1.05 OR min ESS_bulk < a threshold (e.g. 200 for headline params,
documented for nuisance latents) OR divergence fraction >= 2%. Report per-variable, not just summary.

## 2. NUTS decision skill / card
Evidence: three different sampler choices, unclear when NUTS is "the right choice." 
Proposal: a short decision card — (a) NUTS/HMC default; (b) if the sampler library can't be installed,
the runner must say so, and either install in a venv (Opus/Cursor did) or use a labeled alternative
with a stated reason (Codex did) — never claim NUTS when it isn't; (c) define "converged enough"
(ties to gate #1); (d) require chain count >= 4 unless justified (Cursor used 2).

## 3. Priority-deliverable clarification gate (problem-class general — replaces any problem-specific plot rule)
Evidence: the human's single most-wanted figure (a coupled response-vs-spec view) was never produced
because the written ask ("input spectra") was ambiguous and no agent confirmed priorities. Per human
direction, the harness must NOT hard-code that specific plot or any problem-specific deliverable.
Problem-class-general rule instead:
- At task start, the runner restates, in its own words, the human/master PRIORITY deliverables and
  acceptance criteria, and explicitly flags any ambiguous or underspecified ask.
- If a priority ask is ambiguous (e.g. "input spectra" could mean the forcing INPUT or the system
  RESPONSE), the runner asks for clarification BEFORE building; if it cannot ask mid-run, it states
  the assumption prominently and, where cheap, produces both interpretations.
- The checker verifies a `priority_deliverables.md` exists listing each priority ask, its
  interpretation, and where it was delivered. A priority marked "assumed" without confirmation is a
  hard-WARN; a listed priority with no delivered artifact is a FAIL.
- WHERE PROBLEM SPECIFICS LIVE: the exact plots/quantities (e.g. the per-flight interface-PSD-vs-spec
  GIF) belong in the RUNNER PROMPT / task card for a given problem, never in the harness.

## 4. Runtime tracking (machine-readable, fair across tools)
Evidence: only Codex reported a total (~18 min); Opus partial; Cursor none. Cursor was slowest mostly
because it waited on per-command human approval, which is not compute and should not penalize it.
Proposal: every runner writes `runtime.json` with:
- `active_runtime_s`: sum of command/compute execution time. Wrap each command with start/end
  timestamps and sum the durations — this naturally EXCLUDES idle time waiting on human approvals,
  because that wait happens BETWEEN commands, not inside them.
- `elapsed_wallclock_s`: end-to-end, for reference.
- `human_wait_s` (optional): elapsed minus active.
Cross-runner comparison uses `active_runtime_s` so permission-wait does not distort the result.
Checker verifies the fields exist and `active_runtime_s <= elapsed_wallclock_s`. (See proposal #9 for
removing the stalls at the source.)

## 5. Discretization-resolution assumption + sensitivity (problem-class general, runtime-aware)
Evidence: Codex's coarse self-generated grid clipped the tray resonance; Cursor's stride-4 subsample
under-resolved it; none justified the choice or tested it. But a fixed "N points per band" rule would
be wrong as a HARNESS rule: for some problems denser sampling makes runtime intractable, and the
right resolution depends on which features drive the QOI.
Proposal (general to FRF/PSD/modal/time/mesh discretization; no hard-coded number):
- Treat the analysis grid/resolution as a first-class, DOCUMENTED assumption: spacing, log/linear,
  and a rationale tying it to the features that drive the QOI (resonances, notches, bandwidths,
  transients).
- The runner must show the QOI-driving features are adequately resolved, OR justify a coarser grid
  explicitly INCLUDING the runtime/accuracy tradeoff (denser is not free).
- Require a resolution sensitivity check: re-run (or a bounded sub-study) at finer resolution near the
  QOI-driving features and report the QOI/posterior shift. If refinement is intractable, document why
  and bound the expected error.
- The checker verifies that a resolution assumption + rationale + sensitivity result (or a justified
  intractability note) EXIST. It does NOT mandate a specific points-per-band number.
- Problem-specific targets (e.g. "resolve the tray half-power band", points-per-band values, the
  refinement strategy reviewers recommended) belong in the RUNNER PROMPT for that problem.

## 6. Plot-hygiene hook
Evidence: Codex figure had a legend-less, dual-axis panel.
Proposal: extend the image-legibility hook to FAIL any figure/panel that has >1 plotted series and
no legend, and to flag dual-axis panels lacking axis-color/series labels.

## 7. Workspace isolation enforcement
Evidence: 2 of 3 runners ran in the master repo, not their copy.
Proposal: each runner prompt must begin by asserting and printing its working directory, and refuse
to proceed if it is not the assigned runner workspace. Consider a guard file the runner must detect.

## 8. Synthetic-truth honesty banner (reinforce)
Evidence: tight posteriors ride on same-model synthetic data (Opus flagged this well).
Proposal: require every packet's top summary to state "synthetic, no model-form error; intervals are
optimistic vs real hardware" — Opus did this; make it mandatory + checker-verified string.

## 9. Reduce human-permission stalls for runners (fairer runtime, faster loops)
Evidence: Cursor/Composer was the slowest mainly because it waited on per-command human approval, not
compute. Each runner already works in an ISOLATED, disposable copied workspace, and the immutable
checker hashes are verified after the run, so auto-execution inside that sandbox is reasonable.
Proposal: allow runners to auto-run within their isolated copy:
- Claude Code runner: launch with `--dangerously-skip-permissions` (isolated copy only).
- Codex runner: use its full-auto / no-approval mode (e.g. `--full-auto`, or approval-mode "never" /
  "dangerously-bypass-approvals-and-sandbox") (isolated copy only).
- Cursor Composer runner: enable Agent Auto-Run (the auto-execute-terminal / "YOLO" setting under
  Cursor Settings -> Agent), ideally with a command allowlist/denylist (isolated copy only).
Safety bounds: acceptable ONLY because the workspace is a throwaway copy with no secrets and the four
immutable checker files are hash-verified after the run. NEVER enable auto-run in the master repo.
Exact flag/menu names vary by app version — confirm in-app before relying on them.
This both removes the unfair runtime penalty (proposal #4) and speeds the whole loop.
