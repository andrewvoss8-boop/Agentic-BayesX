# Adversarial review of the ShockSat full-spectrum FRF study

Overall review status: RED.

The original study is not trustworthy as an OVERALL YELLOW package. Its locked checker still replays YELLOW and most underlying numeric claims reproduce, but four decision-relevant failures remain: the collector emitted non-finite S1/S2 statistics and a post-hoc F=R row; arm C's exact aggregate leaks held-out drives through one reused shape MAP; a local Fisher information matrix cannot establish "multimodal, not under-identified" globally; and the failed net-CG port leaves S3/S4 unresolved rather than falsified. Andrew authorized an isolated repair. That repair restores F=C and finite statistics and checks YELLOW without modifying the reviewed workspace. It confirms S1 and S2 are not met, but it does not repair arm C, net-CG, or the incomplete exact rerank. The defensible conclusion is: S1, S2, and S5 are not met; S3 and S4 are CANNOT-VERIFY; broader claims that remodeling impotence and global identifiability are confirmed are too strong.

## Claim audit

| ID | Claim | Verdict | Gate | Evidence and corrected statement |
|---|---|---|---|---|
| C1 | Exact-basis S2 flip | OVER-CLAIMED | YELLOW | D−R changes from +0.013754 screening to −0.001716 exact, paired SE 0.009379. The two selected winners use identical scoring machinery, but only 2/28 remodel candidates were exact-rescored. The 0.0000% check is algebraic self-consistency after folding theta_MAP into its own eigenbasis. Correct: the selected winners reverse and tie; the full track ranking is unverified pending exact re-rank. |
| C2 | Arm B is multimodal, not under-identified | WRONG | RED | Step sizes 0.5% to 4% and the likelihood covariance all leave 9/9 local FIM directions above prior precision, so the likelihood is locally stiff. This does not prove global parameter identification. R-hat reaches 360.6 and effective sample size is about 2. Multiple separated parameter modes fitting comparably in data space are global under-identification under `AGENTS.md`. Correct: local sensitivity is high, global identification and posterior uncertainty are unresolved; MAP scores are deterministic optimizer results only. |
| C3 | Bit-identical caches close Gate W | OVER-CLAIMED | YELLOW | Direct NPZ recomputation confirms 5/5 overlaps, minimum channel correlation 0.9999999999999998, zero median log-magnitude difference, 28 live-force hits, and 207.4 to 1083.2 lbf peak force. The same hits and same distiller were reused, so equality is expected. Correct: raw provenance and force health are closed; independent processing validation is not. |
| C4 | FEM ceiling near 640 Hz; 500 to 1000 Hz is compute-limited | OVER-CLAIMED | YELLOW | The independent slices validate eigenvalues through 639 Hz and 639/1.25 = 511.2 Hz supports a 500 Hz cap. The raw solve has 560 modes; 345, not 338, fall inside the 1 Hz edge cut, while the summary says 19 clamped. The last 345 occupy only 667.29 to 668.09 Hz, so the pile-up is clearly numerical. All drives have median coherence at least 0.634 in 500 to 1000 Hz. Correct: the attempted basis is credible to 639 Hz and the present 500 Hz cap is sound; 1250 Hz was infeasible for the attempted 16 GB ARPACK configuration, not in general. |
| C5 | Net-CG S3/S4 are not validly assessable | WRONG as a study closure | RED | The reimplementation gives widths 5.45, 1.59, and 2.02 times the delivered references. The report correctly refuses to call this a regression. But unassessable is not falsified or not-met, and the required QOI result is absent. The hide-top-3 audit widens only shear_y by 1.225; shear_x=1.000 and normal_z=1.003. Correct: S3/S4 are CANNOT-VERIFY until A1 reproduces 1.51/2.30/2.53 before arm changes. |
| C6 | Arm C exact score is a representative shortcut | WRONG | RED | `rescore_freeze.py` applies the m_xpos fold's shape MAP to all four folds. That MAP was trained on the other three drives, so 3/4 exact fold scores use a map that saw their held-out drive. The 0.157 aggregate is not held-out. Correct: no valid exact C aggregate exists until four exact fold-specific MAP fits are run. |
| C7 | D16 model-form limitation and H2 impotence | OVER-CLAIMED | YELLOW | Counts reproduce: agent 14 candidates, zero refine/rbe2; random 14 candidates, four with genuine connectivity/refinement, including three rbe2_soften and two refine operations. Neither track tested geometry or element formulation. Correct: the agent tied random in a property/reparameterization-heavy space; actual geometry, element formulation, and agent-proposed mesh/topology edits remain untested. |
| C8 | Checker and continuity mechanics are sound | WRONG | RED | The immutable checker replays YELLOW and G12 is GREEN. A planted selection-path `np.linalg.lstsq` gives G03 RED; planted non-convergence gives G08 YELLOW. But G09 accepts null SE, NaN S1/S2 values, and F=R despite the pre-registered F rule. The isolated repair gives F=C, S1 D−A1=+0.049671, and S2 D−R=−0.001716. Correct: use the repair for S1/S2 and strengthen G09 before calling the package replayable. |

Full machine-readable evidence is in `out/claim_audit.json`.

## Does the study's OVERALL YELLOW / all-S1–S5-falsified conclusion hold?

No.

- Original package: RED because its collector/checker accepted non-finite statistics, a false arm-F identity, an invalid exact arm-C aggregate, and a missing valid net-CG result.
- Isolated collection repair: YELLOW, 7 GREEN / 1 YELLOW. It preserves the original inputs and confirms:
  - S1 not met: eligible best arm D improves A1 by +0.0496706, below +0.05, although it exceeds 2×paired SE = 0.0347712.
  - S2 not met: D−R = −0.0017163 with paired SE 0.0093785.
  - S5 not met at the declared prior width: Spearman −0.3. Sensitivity is fragile, with finite-only Spearman +0.139 at prior 0.15 and +0.367 at 0.40; the pre-registered rand10 candidate is absent.
- S3 and S4: unresolved, not falsified. The net-CG port failed its reference reproduction.
- H1: the exact "C collapses" evidence is invalid; D still misses S1 by 0.0003294.
- H2: selected exact winners tie, but full 28-candidate exact ranking is missing and the agent tried no genuine model-form changes.

## Independent spot checks

- Cache overlap and force: recomputed directly from wide and existing NPZ files, not from `overlap_validation.json`.
- Exact arm means and paired SE: recomputed from the four saved fold records. The repair checker verifies each mean against those folds.
- FEM edge: recomputed from raw and filtered eigensolution NPZ files. The numerical pile-up is real; reported counts are inconsistent.
- FIM: recomputed over four finite-difference steps and with the actual frequency-correlated likelihood covariance. Local rank is robust; the global identification conclusion is not.
- Checker: gate functions replayed read-only; mutation fixtures test G03 and G08; original and repair SHA locks match.

No reviewed-study file was modified. The authorized repair is isolated in `artifacts/reports/shocksat_full_spectrum_frf_repair_20260716/`.
