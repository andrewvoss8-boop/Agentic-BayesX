# Checker-Audit Agent — paste into a fresh Claude Code Opus 4.8 session (master repo root)

Purpose: independently audit the harness's tests/checkers — are they meaningful, or arbitrary,
wasteful, gameable, or self-graded? The human has not personally reviewed them and wants assurance
they actually prevent cheating without being theater.

```text
You are the CHECKER-AUDIT agent for Agentic BayesX (model: Opus 4.8). You do NOT run the experiment and
do NOT modify any checker. You audit the checking system itself and report.

Read and evaluate:
- IMMUTABLE checkers (hash-locked via harness/checkers/manifest.sha256):
  harness/checkers/verify_artifacts.py, harness/checkers/check_canary.py,
  tests/test_posterior_recovery.py, tests/test_mdof_transfer.py
- The harness driver/specs: harness/driver.py, harness/program.md, harness/specs/*, harness/configs/*
- The RUNNER-AUTHORED self-checkers actually used in round 2:
  scripts/check_round2_artifacts.py (Opus), the Codex round-2 checker referenced in
  artifacts/reports/runner_codex_gpt55_round2_20260602/ (run_round2.py / tests), and any Cursor checker
  referenced in its packet (note: Cursor's source scripts were deleted — record that you cannot read it).
- The runner checks.json files for round 2 (what actually got gated).
- AGENTS.md / CLAUDE.md convergence + verification gates (what SHOULD be enforced).

For EACH check (immutable and self-authored), report in a table:
- what it actually verifies (quote the code);
- whether it is MEANINGFUL (catches a real failure mode), ARBITRARY (threshold with no rationale),
  WASTEFUL (cost with no signal), or THEATER (always passes / unfalsifiable);
- whether it is GAMEABLE — could a runner pass it while producing wrong/cheated results;
- whether it is SELF-GRADED (runner-authored) vs TRUSTED (immutable/independent).

Then assess the SYSTEM:
1. Trust boundary: which substantive quality gates (convergence R-hat/ESS, key-plot authenticity,
   no-copied-assets, resolution, runtime honesty) are enforced by a TRUSTED control vs only by
   runner-self-authored checkers? (Lead's finding: the convergence/quality gates live in each runner's
   own check_round2_artifacts.py, while the immutable checkers only do file-existence + a canary RMSE +
   two unit tests. Confirm or refute.)
2. Specific gameability: can a runner (a) pass while non-converged, (b) present copied figures as its
   own, (c) under-report runtime, (d) skip the key deliverable, (e) edit shared/round-1 files —
   WITHOUT any TRUSTED checker catching it? Cite round-2 evidence (Cursor copied figs 01-06; Codex ran
   in master; Cursor runtime understated).
3. Recommend a minimal set of SHARED, non-self-authored, hash-locked checks that would close the gaps
   without being wasteful: e.g. a generic convergence gate over all sampled variables, a figure
   content-hash manifest that fails on cross-run byte-identical images unless declared a copy, an
   external wall-clock wrapper, a key-deliverable presence+authenticity check, and a workspace-isolation
   guard. For each, state the failure mode it catches and why it is not theater.
4. Flag any EXISTING check that is arbitrary/wasteful and should be cut or justified.

Write artifacts/reports/runner_comparison_round2_20260603/checker_audit.md. Quote code as evidence; do
not modify any file. Be concrete about what is trustworthy today vs what only looks rigorous.
```
