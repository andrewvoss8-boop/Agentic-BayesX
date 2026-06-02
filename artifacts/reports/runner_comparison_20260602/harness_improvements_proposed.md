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

## 3. Required KEY deliverable + plot contract
Evidence: all three missed the human's headline plot.
Proposal: task card must explicitly REQUIRE and the checker must verify the existence of:
- per-flight coupled interface-acceleration PSD with mean/95/99 bands vs the original spec, as a
  frame sequence AND an animated GIF;
- a panel overlaying all 10 flight forcing draws vs the +6 dB mean forcing;
- flight 3*GRMS sequence overlaid with the original vibe-test 3*GRMS reference line.

## 4. Runtime tracking (machine-readable)
Evidence: only Codex reported a total (~18 min); Opus partial; Cursor none.
Proposal: every runner writes `runtime.json` with total and per-stage wall-clock seconds; checker
verifies the field exists and is > 0.

## 5. Frequency-grid assumption + sensitivity (problem-class specific)
Evidence: Cursor stride-4 subsampling; Codex coarse grid clipping the tray peak; rationale absent.
Proposal: frequency-grid spacing becomes a first-class ASSUMPTION (value, log/linear, points/decade,
points across each resonance half-power band) AND a required sensitivity item (re-run on a refined
grid, report QOI/posterior shift). Add a peak-resolution check: >= N points within each mode's
half-power bandwidth.

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
