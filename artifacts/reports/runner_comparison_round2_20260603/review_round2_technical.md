# Round-2 Technical Reviewer — paste into a fresh Claude Code Opus 4.8 session (master repo root)

```text
You are the TECHNICAL REVIEWER for Agentic BayesX, ROUND 2 (model: Opus 4.8). Read
.claude/agents/reviewer.md first. A checker pass is NOT proof of physics. Verify claims from the
artifacts and code; do not trust packet headlines.

Round-2 outputs (all in this master repo):
- artifacts/reports/runner_cursor_composer25_round2_20260602/
- artifacts/reports/runner_codex_gpt55_round2_20260602/
- artifacts/reports/runner_claude_opus48_round2_20260602/
Context: artifacts/reports/runner_comparison_round2_20260603/README.md and the round-1 review in
artifacts/reports/runner_comparison_20260602/ (for did-they-fix-it comparison).
Verified thresholds: artifacts/reports/runner_comparison_20260602/reader_web_verified_sources.md
(R-hat < 1.01 rank-normalized split; bulk AND tail ESS >= 100 x chains; 0 divergences ideal;
half-power BW = 2*zeta*f_n; PSD-envelope is the defensible comparison; GEVS qual margin +3 dB).

For EACH runner, write a per-runner verdict (blocking vs non-blocking) covering:
1. KEY PLOT correctness. Open the interface-PSD-vs-spec evolution GIF and its frames. Confirm: it is
   the COUPLED INTERFACE ACCELERATION RESPONSE PSD (not the forcing input); it shows mean + 95% + 99%
   bands; it overlays the original test spec; frames actually differ per flight (not a static frame
   looped); log-frequency axis; legend present. State whether it answers the PSD-ENVELOPE question
   (does the spec envelope the flight interface PSD across frequency).
2. Forcing overlay + QOI-vs-vibe. Confirm discrete flight forcing draws are shown vs the original
   forcing, and flight tray 3*GRMS is overlaid against the vibe-test 3*GRMS reference (43.9 g / 28.3 g).
3. SAMPLER + CONVERGENCE to the source-backed bar. Open each nuts_diagnostics.json (not the .md) and
   report max R-hat and min bulk-ESS AND tail-ESS over ALL sampled variables INCLUDING raw
   hierarchical latents. Confirm whether each truly meets R-hat < 1.01 and bulk+tail ESS >= 100 x
   chains with 0 (or justified) divergences. Round-1 caution: Cursor passed its checker while at
   R-hat 1.83; Opus reported only marginals. Verify the RAW latents this time for all three.
4. RESOLUTION. Read each resolution sensitivity artifact. Confirm the QOI-driving resonances are
   resolved (half-power BW = 2*zeta*f_n), no clipped peaks, and the refine-and-compare shift is
   reported. Flag any runner that still under-resolves or that hard-coded a lines-per-band number
   (it should be a justified assumption, not a magic number).
5. PLOT HYGIENE. Every figure/panel has a legend (round-1 Codex had a legend-less dual-axis panel);
   log-frequency axes; no clipped peaks.
6. RUNTIME sanity: active_runtime_s <= elapsed_wallclock_s; note Cursor/Opus discarded-run accounting.
7. DID-THEY-FIX-IT: for each, state which round-1 blocking issues are resolved vs still open.

Write artifacts/reports/runner_comparison_round2_20260603/technical_review.md. Do not rewrite code.
Note: Cursor's source scripts were lost (see README), so verify Cursor from its outputs only and say so.
```
