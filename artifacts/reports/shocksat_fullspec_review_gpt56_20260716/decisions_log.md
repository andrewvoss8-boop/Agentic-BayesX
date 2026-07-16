# Decisions log

## D0 — 2026-07-16 — Audit scope and method

- Goal: independently test the eight high-risk claims in the completed ShockSat full-spectrum FRF study and determine whether its overall YELLOW and S1–S5 conclusions survive.
- Audit: exact-basis S2 flip, arm-B identifiability/sampler interpretation, Gate W validation, FEM ceiling, net-CG S3/S4 gap, arm-C shortcut, model-form action-space limitation, and checker integrity.
- Verification: inspect source code and artifacts, rerun only the immutable checker, recompute cheap headline quantities from lower-level files, and quantify basis/winner-selection sensitivity where saved outputs allow it.
- Open ambiguity: full exact reranking of all 28 remodel candidates may require prohibited eigensolves; if no saved exact scores exist, it will be a CANNOT-VERIFY gap and recommended new compute rather than inferred from the two finalists.
- Human priority: next steps must explicitly assess a broader agent action space containing geometry, element formulation, connectivity, and mesh topology/density edits, not only property scalings or region splits.
- Tool continuity: Cursor can compact chat context; repository files are the continuity record. Claude-specific `/compact` and `@import` behavior is not assumed.

## D1 — 2026-07-16 — RED integrity blocker; stop before broader conclusions

- `code/collect_results.py:45-53` reads `folds[fold]["P1p"]`, but the actual structure is `folds[fold][band]["P1p"]`. This produces non-finite S1/S2 deltas in `out/verdicts.json` and null standard errors throughout `out/arms_bands_table.json`.
- G09 remains GREEN because `check.py:217-260` checks field presence but not finiteness, non-null standard errors, or consistency with the priority contract requiring fold-average ± fold SE.
- `code/collect_results.py:40-42` post-hoc defines F as the highest exact row across A0/A1/B/C/D/R. It therefore writes `F.equals = R`, although the pre-registered rule in `code/arm_f_combine.py:2-6` permits F to combine B/C/D only. No F result exists in `out/exact_freeze_scores.json`.
- Independent fold recomputation: D−A1 = +0.0496706, paired SE 0.0173856, so S1 remains not-met if the eligible set is B/C/D. D−R = −0.0017163, paired SE 0.0093785, so S2 remains not-met.
- But R−A1 = +0.0513869 and 2×paired SE = 0.0485185, with vault direction R 0.4551 > A1 0.4507. If the artifact's F=R row is interpreted literally, S1 flips to met. The report cannot simultaneously exclude R from S1 and present R as F.
- Result: RED under the integrity/fabrication and broken-pipeline standard. Per the runner card, stop for Andrew before drawing broader conclusions.
- Evidence: `out/recomputed_checks.json`, `out/checker_replay.json`, `out/checker_mutation_tests.json`.

## D2 — 2026-07-16 — Andrew authorizes separate repair, rerun, then review

- Andrew selected: repair the collector/checker in a separate authorized task, rerun, then resume the adversarial review.
- The immutable reviewed workspace remains untouched. Repair outputs go to `artifacts/reports/shocksat_full_spectrum_frf_repair_20260716/`.
- Correct arm-F interpretation: the pre-registered sequential rule sees B screening 0.142 < A1 0.145, then C 0.189 > A1, then D 0.179 < C; therefore F = C, not R.
- Repair acceptance: finite exact fold means and standard errors, finite S1/S2 paired statistics, F=C recorded explicitly, a new SHA-locked repair checker that rejects NaN/null statistics and method-identity mismatch, and hashes proving reviewed inputs unchanged.

## D3 — 2026-07-16 — Final review verdict and recommendation

- Overall review = RED. The original OVERALL YELLOW does not hold as a package status.
- Repaired collection = YELLOW, 7 GREEN / 1 YELLOW. S1 and S2 remain not met after finite recomputation.
- Correct S-status statement: S1, S2, and S5 not met; S3 and S4 CANNOT-VERIFY.
- RED claims: global "not under-identified" interpretation, invalid exact arm-C aggregate, missing valid net-CG result treated as closure, and incomplete original result checker.
- Highest-value cheap actions: exact per-fold C refit, exact re-rank all 28 candidates, then validated net-CG reference reproduction.
- Highest-value new study: a stratified discrete model-form loop with fixed quotas for geometry, element formulation, connectivity, mesh topology/density, and property controls. Use exact per-candidate bases and a family/cost-matched random control.
