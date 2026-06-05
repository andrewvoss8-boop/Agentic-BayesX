# Stage-3 Independent Reviewer + Scorer — fresh Claude Code Opus 4.8 session (master repo root)

Independent of the truth-author (Codex), the inference runner (opus48), and the master who designed the
experiment. You may read EVERYTHING (incl. the sealed truth) — you are the grader, not a participant.
Write ONLY your review packet; do not edit anyone's workspace.

```text
You are the INDEPENDENT REVIEWER + SCORER for Agentic BayesX round-3 STAGE 3 (Opus 4.8). Read
.claude/agents/reviewer.md and .claude/agents/checker.md first. Honesty rules: quote file evidence; do
not infer success from plots; recompute, don't trust self-report. Write ONLY to
artifacts/reports/blind_round3_stage3_review_20260605/. Do not modify runs/round3/opus48/ or
runs/round3/codex_truth/.

Context: Stage 0/1 (frequency-only discrepancy) failed honestly (sigma_d<->sigma_e ridge; netCG bias
4.86x) — see artifacts/reports/blind_round3_review_20260604/review.md. Stage 3 built three fixes
(per-DOF/per-strut asymmetric model; structure/property-based discrepancy; complex mag+phase likelihood)
and adopted the canonical netCG (docs/.../round3/netcg_quantity_contract.md). The truth was re-published
with canonical netCG. The inference SELF-REPORTS a MIXED result; verify it independently.

Inputs you may read (ALL — you are the grader):
- INFERENCE (Stage 3): runs/round3/opus48/report/blind3_*.{json,log,md}, packet_stage3.md,
  runs/round3/opus48/code/blind3_*.py, the saved posterior draws.
- PUBLISHED data the inference saw: runs/round3/codex_truth/dataset/ (observations.npz, data_contract.md).
- SEALED TRUTH (your key, re-published canonical netCG): runs/round3/codex_truth/sealed_truth/
  (scoring_key.*, true_parameters.json, model_form_imperfections.md) and
  runs/round3/codex_truth/report/checks/stage3_netcg_republish_checks.json.
- The canonical contract: docs/agents/competitive_full_experiment/round3/netcg_quantity_contract.md.

Do these and write a verdict:

0) CONTRACT VALIDITY. Confirm BOTH sides use the canonical netCG: the sealed scoring_key netCG is the
   dynamic-FBS F_iface/m_load (resonant, NOT the frequency-flat rigid 0.28 constant), and the inference
   predicts netCG the same way. Confirm the netCG re-publish changed ONLY netCG arrays (non-netCG
   observations/scoring unchanged — hash/compare). If the comparison is not apples-to-apples, say so.

1) SCORE vs sealed truth (recompute). netCG 3*GRMS bias + 95/99 coverage for BOTH the with-discrepancy
   and without-discrepancy variants (self-report: ~1.71x with-d / 3.10x without-d, 0% cov). Per-build /
   population parameter bias where comparable. Confirm the f->0 rigid limit (~0.282).

2) CONVERGENCE over ALL latents (recompute rank-split R-hat + bulk/tail ESS from saved draws):
   - WITHOUT discrepancy (per-strut asymmetric only): self-report CONVERGES (R-hat 1.009, ESS 487, 0 div,
     k_pop 1.685e7). Verify.
   - WITH the structure/property-based discrepancy: self-report FAILS (R-hat 2.85, ESS 4.7, sigma_d->1.33)
     because the discrepancy is CONFOUNDED with the per-strut stiffness it sits on (same parameter space).
     Verify the ridge and the confounding diagnosis. Confirm the inference did NOT claim "NUTS active" for
     with-d.

3) RESIDUAL ERROR. sigma_e self-reported ~2x inflated in BOTH variants -> dominant residual = MISSING
   HIGHER MODES outside the coarse model span. Verify against true_parameters.json: are there real modes
   (e.g. z ~62/77/120 Hz; lateral ~51/87/137 Hz) the inference band/model cannot represent? Is the
   "missing-mode floor" diagnosis correct (vs the discrepancy or asymmetry being the issue)?

4) HELD-OUT CALIBRATION (recompute vs CLEAN truth): new-build cov95 (self-report 0.911, logwidth 2.16 ~
   8.7x, far sharper than the prior 12-18x) and band 95-115 Hz cov95 (0.715, under-covers). Read coverage
   WITH sharpness.

5) COMPANION TRUST STUDIES (verify they were actually run this time): without-discrepancy, starve-data
   (self-report: still R-hat 2.85 -> ridge is STRUCTURAL, not a data-deluge artifact), effective-vs-
   nominal sample count (n_eff(k_pop) ~0.6 / 7920), grid-invariance (bounded/intractable under the ridge).

6) BLINDNESS + INTEGRITY: confirm no reads of sealed_truth/Codex code/report; figures authentic; no
   fabrication; no overclaim. Strongest tell: bias/non-coverage AWAY from leakage. Note that NOT claiming
   NUTS-active for with-d is the correct honest behavior.

7) HEADLINE VERDICT: Did the structure/property-based discrepancy (the Stage-3 novel piece) RESOLVE the
   ridge and restore honest calibration? (Self-report: NO — same-parameter-space discrepancy is
   confounded with the per-strut stiffness; the per-strut ASYMMETRIC PHYSICS alone is the real gain.) Is
   the runner's prescribed fix correct: (a) make the discrepancy ORTHOGONAL to the calibration parameters
   (output-mode/participation space) or use modular/cut updating, and (b) raise FEM fidelity (flexible
   isogrid panel + strut/shell bending) to remove the missing-mode floor (Stage 4)? State what is now a
   real, defensible gain vs what is still an honest open failure.

Output: artifacts/reports/blind_round3_stage3_review_20260605/review.md (scoring tables + convergence
recompute + held-out + companions + integrity + headline) with evidence inline. Be specific and honest;
either a real gain or an honest failure is fine — overclaim is not.
```
