# Round-2 Review Packet — 2026-06-03

All round-2 outputs now live in the single master repo under `artifacts/reports/`:
- Cursor: `runner_cursor_composer25_round2_20260602/`
- Codex:  `runner_codex_gpt55_round2_20260602/`
- Opus:   `runner_claude_opus48_round2_20260602/`

Round-1 outputs and the round-1 review are in `artifacts/reports/runner_comparison_20260602/`.

## What changed since round 1 (lead snapshot — reviewers must verify, not trust)
- All three produced the previously-missing KEY plot: a per-flight interface-acceleration response
  PSD-vs-spec evolution GIF, plus a flight-forcing overlay and a tray 3*GRMS-vs-vibe-reference plot.
- Codex switched from a custom PyTorch HMC (round 1) to REAL NumPyro NUTS this round.
- All three tracked runtime (active vs elapsed): Cursor ~223 s, Codex ~294 s, Opus ~1268 s active.
- Convergence claims are now strong (Opus 0 div; Codex R-hat 1.007/ESS 1080; Cursor gate < 1.01).
  Reviewers MUST confirm these over ALL sampled variables incl. raw latents, since round-1 runners
  passed checkers while non-converged.

## Provenance / traceability caveats (carry into review)
- Codex round-2 ran in the MASTER repo, not an isolated copy (see the round-1 RAN_IN_MASTER_NOTE
  pattern; same caveat). Its results are usable; treat replay/runtime comparisons with that in mind.
- Cursor's round-1 AND round-2 SOURCE SCRIPTS were lost during a cleanup deletion (only its report
  outputs survive). So Cursor's runs are NOT replayable from source this round; the checker cannot
  re-run Cursor. This is a traceability gap, not cheating.

## Review prompts (run each as a fresh Opus 4.8 session from the master repo root)
- `review_round2_reader.md`     -> writes reader_review.md
- `review_round2_technical.md`  -> writes technical_review.md
- `review_round2_integrity.md`  -> writes integrity_review.md
- `review_round2_checker.md`    -> writes checker_review.md

The lead cannot spawn subagents from its toolset; the human launches them (or asks the lead to run
them inline). After they finish, paste paths back and the lead builds the round-2 comparison matrix.
