# Round-2 Reader / Literature Reviewer — paste into a fresh Claude Code Opus 4.8 session (master repo root, browsing ENABLED if possible)

```text
You are the READER for Agentic BayesX, ROUND 2 (model: Opus 4.8). Read .claude/agents/reader.md first.
Do not cite from memory. Browsing should be ENABLED this session; if it is not, say so and mark
external claims [TO-VERIFY].

Round-2 outputs (all in this master repo):
- artifacts/reports/runner_cursor_composer25_round2_20260602/
- artifacts/reports/runner_codex_gpt55_round2_20260602/
- artifacts/reports/runner_claude_opus48_round2_20260602/
Already-verified thresholds from the round-1 web pass:
artifacts/reports/runner_comparison_20260602/reader_web_verified_sources.md (R-hat<1.01; bulk+tail
ESS>=100x chains; 0 div ideal; GRMS=sqrt(area under PSD), 3*GRMS=3 sigma ~99.73%; half-power BW =
2*zeta*f_n; PSD-envelope is the defensible qual-vs-flight comparison; GEVS qual margin +3 dB; the
"lines per half-power band" number remains a documented assumption, not standardized).

Tasks (focus on whether the runners' METHOD CHOICES align with the verified sources, and close the
remaining gaps):
1. For each runner, check that its qual-vs-flight comparison is framed as a PSD-envelope check (spec
   envelopes flight interface PSD across frequency), with the scalar 3*GRMS as a summary — flag any
   runner that treats the scalar as the sole acceptance check, or that presents the setup's -6 dB
   forcing offset as a GEVS qualification margin (it is a project assumption; GEVS margin is +3 dB).
2. Check that each runner's resolution justification uses the half-power-bandwidth definition and an
   honest sensitivity check rather than an invented standardized line-count.
3. Resolve the still-open [TO-VERIFY] items if browsing is on: (a) a retrievable modal-testing primary
   source for spectral-lines-per-half-power-band; (b) whether any controlled standard defines a +6 dB
   (not +3 dB) qualification/uncertainty margin and its scope; (c) current GEVS revision (GSFC-STD-7000
   A/B) wording vs the 2005 base used last time. Record sources (URL/section) for anything you add.

Write artifacts/reports/runner_comparison_round2_20260603/reader_review.md: per-runner alignment notes,
any newly verified citations, and a short list of remaining [TO-VERIFY] gaps. Do not edit runner code.
```
