# Task Card — Sequential Vibe/Modal/Flight Full Experiment, ROUND 2

Date: 2026-06-02
This is the problem-specific layer. The problem-class-general rules (priority clarification,
convergence gate, runtime tracking, resolution assumption, isolation) live in the harness
(AGENTS.md/CLAUDE.md once approved); they are restated here only so round-2 runners apply them
before the harness edits land.

## Task

Same staged dome/tray vibe→modal→flight Bayesian experiment as round 1, on top of
`artifacts/reports/sequential_vibe_modal_flight_20260602/`, but FIX the round-1 gaps the reviewers
and the human caught. Failure is still allowed; honesty still required.

## Step 0 — Priority clarification (do this FIRST, before building)

Write `priority_deliverables.md` in your output folder that:
- restates, in your own words, the human's PRIORITY deliverables (below) and their acceptance tests;
- flags any ambiguous term and states your interpretation. In particular: "input spectra" in round 1
  was ambiguous. The human's TOP priority is the coupled-system **interface acceleration RESPONSE
  PSD** (not the forcing input). If anything is still unclear, ask before building.

## Priority deliverables (the round-1 misses — get these right)

1. **KEY PLOT (highest priority).** The coupled-system **interface acceleration response PSD**
   (g^2/Hz) with **mean + 95% + 99% credible bands**, plotted **against the original test spec**
   (the smoothline), **one frame per flight**, assembled into an **animated GIF** showing how the
   distribution evolves across the 11 flights. Use log-frequency axis. State the quantity contract
   for "interface acceleration response PSD" (DOF, numerator/denominator, units) before plotting.
2. **Forcing overlay.** All flight forcing draws overlaid on the **original forcing PSD** (which sits
   +6 dB above the flight mean), as discrete sample curves (not just smooth quantile bands).
3. **QOI vs test reference.** Flight tray 3*GRMS sequence overlaid with the **original vibe-test
   3*GRMS reference line** (setup: first-build vibe 3*GRMS = 43.9 g; smoothline = 28.3 g). The large
   qual-vs-flight gap is expected; annotate it and pick axes (e.g. log-y) that keep both visible.

## Round-1 fixes that are now requirements

4. **Resolution.** Consume the shared `sequential_dataset.json` grid; do NOT regenerate your own
   coarser truth unless you justify it. Ensure the QOI-driving resonances (tray ~86 Hz, dome ~93.5 Hz;
   half-power band ~3.4 Hz at zeta~0.02) are resolved — use **mode-local refinement** (extra points
   clustered near each f_n), not just more global points. Document grid spacing + rationale + the
   runtime/accuracy tradeoff, and run a **resolution sensitivity check** (refine near the peaks, report
   the QOI/posterior shift). No clipped peaks.
5. **Sampler + convergence.** NUTS/HMC default. If NumPyro is absent (it is, under Python 3.9.6),
   install it in a venv (Opus and Cursor both did) or use a clearly labeled alternative WITH a stated
   reason — never claim NUTS when it isn't. Use **>=4 chains**, adequate warmup, and a **non-centered
   parameterization** for the hierarchical build/flight latents. Report R-hat and ESS over **ALL
   sampled variables including raw latents**, and self-gate: max R-hat <= 1.05, min ESS >= 200 for
   headline params (documented for nuisance latents), divergence fraction < 2%. If you do not converge,
   say so and do NOT report a clean "pass".
6. **Plot hygiene.** Every figure/panel has a legend (the round-1 Codex dual-axis flight panel did
   not). Log-frequency axes for FRF/PSD. Label dual axes clearly.
7. **Runtime.** Write `runtime.json` with `active_runtime_s` (sum of per-command execution times) and
   `elapsed_wallclock_s`. Active excludes human-approval wait.
8. **Isolation.** At start, print your working directory and ASSERT it is your assigned runner
   workspace, NOT the master repo. Refuse to proceed if you are in the master repo.

## Not allowed

- Editing the four immutable checker files (verify with
  `shasum -a 256 -c harness/checkers/manifest.sha256`).
- Copying setup/reference assets and presenting them as generated.
- Reporting "pass" / "NUTS active" when chains have not converged.

## Output + report contract

Write everything to your runner output folder (see your round-2 runner prompt). Produce the same
contract as round 1 (commands.md, files_changed.md, assumptions_ledger, nuts_diagnostics, figures/,
checks.json, known_failures.md, review_request.md, manifest.json, packet.md) PLUS
`priority_deliverables.md` and `runtime.json`.

## Done

All priority deliverables exist and are correct, convergence is real (or honestly reported as not
achieved), resolution is justified + sensitivity-tested, every figure has a legend, runtime + priority
files exist, and the run was done in the isolated workspace.
