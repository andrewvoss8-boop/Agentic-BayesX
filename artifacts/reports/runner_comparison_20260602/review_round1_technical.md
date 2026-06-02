# Round-1 Technical Reviewer Subagent — paste into a fresh Claude Code Opus 4.8 session

Run from the master repo root: `/Users/avoss/Downloads/bayesX/Agentic BayesX`

```text
You are the TECHNICAL REVIEWER subagent for Agentic BayesX (model: Opus 4.8). Read
.claude/agents/reviewer.md first. A checker pass is NOT proof of physics. Be strict and specific.

Runner outputs:
- Cursor:  ../Agentic_BayesX_runner_cursor_composer25/artifacts/reports/runner_cursor_composer25_20260602/
- Opus:    artifacts/reports/runner_claude_opus48_20260602/
- Codex:   artifacts/reports/runner_codex_gpt55_20260602/
Context: artifacts/reports/runner_comparison_20260602/human_feedback.md and evidence_first_pass.md.

For EACH runner, review and write a per-runner verdict (blocking vs non-blocking) covering:
1. SAMPLER + CONVERGENCE. Open each runner's nuts_diagnostics.json (not just the .md summary) and
   report max R-hat and min ESS over ALL sampled variables, INCLUDING raw hierarchical latents
   (dome_raw, tray_raw, x_struct, sigma_build_ln, sigma_sensor_ln). The lead found: Cursor R-hat to
   1.83 / ESS≈3 (2 chains); Codex custom PyTorch HMC R-hat to 4.57; Opus clean on marginals — confirm
   whether Opus's RAW latents also converged or only the monitored marginals. State whether each
   runner's QOI intervals are trustworthy given its diagnostics.
2. NUTS DECISION QUALITY. Was NUTS the right choice, and did each runner justify its choice? Flag any
   case that reports nuts_active=true / passes the checker despite non-convergence (overclaim).
3. FREQUENCY-GRID CHOICE. Find each runner's frequency-grid construction in its script. Report
   spacing, log vs linear, and whether resonance peaks are resolved (points within half-power band).
   The human flagged a clipped tray peak in Codex top-left. Check all runners for clipped peaks.
4. QUANTITY CONTRACTS. Verify PSD-space dB (10**(dB/10)), Matern (not RBF) forcing, dome=m1/tray=m2,
   units, log-frequency axes, and that the full-vs-peak likelihood comparison is valid.
5. KEY PLOT GAP. Confirm none produced the per-flight interface-PSD mean/95/99-vs-spec view/GIF, the
   vibe-RMS overlay, or the 10-forcing-draws-vs-+6dB overlay; note what each WOULD need to add.
6. PLOT HYGIENE. Confirm Codex sequential_observations_truth_vs_observed.png bottom-left lacks a
   legend; scan other figures for missing legends / dual-axis labeling problems.

Write artifacts/reports/runner_comparison_20260602/technical_review.md. Do not rewrite runner code.
```
