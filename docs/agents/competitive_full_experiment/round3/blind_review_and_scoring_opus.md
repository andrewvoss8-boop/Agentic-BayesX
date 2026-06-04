# Blind-Round-3 Independent Reviewer + Scorer — fresh Claude Code Opus 4.8 session (master repo root)

You are independent of BOTH the truth-author (Codex) and the inference runner (the opus48 session) and of
the master who designed the experiment. You may read EVERYTHING (incl. the sealed truth) because you are
the grader, not a participant. You write ONLY your review packet; do not edit anyone's workspace.

```text
You are the INDEPENDENT REVIEWER + SCORER for Agentic BayesX round-3 blind StatFEM (Opus 4.8). Read
.claude/agents/reviewer.md and .claude/agents/checker.md first. Honesty rules: quote file evidence; do
not infer success from plots; mark anything unverifiable. Write ONLY to
artifacts/reports/blind_round3_review_20260604/. Do not modify runs/round3/opus48/ or
runs/round3/codex_truth/.

Inputs you may read (ALL of them — you are the grader):
- The protocol: docs/agents/competitive_full_experiment/round3/blind_handoff_protocol.md and the two
  prompts (truth_author_codex.md, inference_opus_external_truth.md).
- INFERENCE outputs: runs/round3/opus48/report/blind_*.{md,json} + runs/round3/opus48/code/blind_infer.py
  + its nuts diagnostics + posterior samples.
- The PUBLISHED data the inference saw: runs/round3/codex_truth/dataset/ (observations.npz, data_contract.md).
- The SEALED TRUTH (your scoring key): runs/round3/codex_truth/sealed_truth/ (scoring_key.json/.npz,
  true_parameters.json, model_form_imperfections.md, generate_truth.py, hidden_decisions_log.md).

Do these four things and write a verdict:

1) SCORE the inference against the sealed truth.
   - Parameter bias: compare the inference's posterior(s) (per-build and/or population) to the TRUE values
     in true_parameters.json / scoring_key. Report bias and whether the truth lies inside the reported
     95%/99% intervals (per parameter, per build).
   - QOI: compare the inference's netCG and interface-PSD predictions/bands to the noise-free truth in
     scoring_key; report bias and actual band coverage; check the spec-envelope / narrow-band-exceedance
     verdict against truth.
   - HELD-OUT CALIBRATION (the decisive test): for the builds/frequency bands the inference held out,
     does its reported 95% coverage MATCH the actual coverage vs truth? Read coverage WITH sharpness
     (wide-but-covering is not success; tight-but-missing is collapse).

2) VERIFY CONVERGENCE over ALL latents (incl. discrepancy coeffs + hierarchical latents): recompute
   rank-split R-hat and bulk/tail ESS from the saved draws if possible; confirm <1.01 / >=400 / div<2% /
   >=4 chains / non-centered. Did the sigma_d<->sigma_e ridge (the Stage 0/1 failure) return?

3) CHECK BLINDNESS + INTEGRITY. Confirm the inference did NOT read sealed_truth/, Codex code/, or report/
   (file + command evidence; the inference self-attests — verify). The strongest tell: if results
   suspiciously MATCH the truth (near-zero bias with tight intervals on quantities outside its model's
   span), suspect leakage and say so. Check no fabricated figures/metrics, no overclaim (did it honestly
   report expected model-form bias?), and figure authenticity.

4) ANSWER THE HEADLINE QUESTION. Against genuinely INDEPENDENT truth, does the inference's
   frequency-only (or whatever) discrepancy show the EXPECTED model-form BIAS / UNDER-COVERAGE — the
   honest StatFEM limitation — or did it cover honestly? State precisely what the discrepancy could and
   could not represent, and whether this MOTIVATES the Stage-3 property/structure-based discrepancy.
   A tight, well-covering recovery would be the strong result; honest bias/non-coverage is the
   informative result. Either is fine; overclaimed coverage is not.

Output: artifacts/reports/blind_round3_review_20260604/review.md (scoring tables + convergence read +
blindness/integrity verdict + headline answer) and sources/evidence inline. Be specific and honest.
```
