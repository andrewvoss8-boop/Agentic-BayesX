# priority_deliverables — validated net-CG QOI port (card B, 2026-07-16)

Each PRIORITY ask from the runner card, restated in my own words, with its interpretation and where it is
delivered. A priority with no delivered artifact is a failure; an "assumed" interpretation is a warning.

| # | Priority ask (card) | My restatement | Interpretation / assumption | Delivered in |
|---|---|---|---|---|
| P1 | §2 Gate N0: reproduce delivered bands 1.51/2.30/2.53 ±0.05 by driving the ORIGINAL `netcg_qoi.py` | Before touching anything arm-related, prove I can re-hit the delivered twin's calibrated band widths using the netcg thread's own code, reduced model and L5 θ posterior | ASSUMED→RESOLVED (D0): the reference numbers are the netcg scorecard's `statfem_Fk` `sharpness_band_grms_ratio_vs_fem6db` = **1.508 / 2.301 / 2.526** (the delivered *conservative assumption-light* winner). normal_Z's *sharpest* method (`hier_pooled`, 2.005) was NOT delivered. Tolerance ±0.05 | `out/n0_reference.json`, `findings.md` §N0, `figures/fig_n0_bands.png` |
| P2 | §2 FAIL path: diagnose, `BLOCKED.md`, S3/S4 permanently CANNOT-VERIFY-pending-human, no constant-fixing | If N0 fails, stop the science, write the exact divergence point + numbers, do not calibration-shop | Interpretation: BLOCKED is a valid reportable outcome, not a failure of the run | `BLOCKED.md` **(not triggered — N0 passed; path retained in `check.py` gate G01)** |
| P3 | §3.1 Bridge gate N1: netcg machinery on the INHERITED model at the study's θ_MAP_wide instead of the L5 posterior median | Quantify how much of any width change is the θ POINT vs the MODEL | Diagnostic only, no pass/fail threshold (card says "no threshold") | `out/n1_bridge.json`, `findings.md` §N1, `figures/fig_n1_theta_bridge.png` |
| P4 | §3.2 Tier update (H4/S4): apply the pre-registered A5b tier rule INSIDE the netcg machinery; report normal-Z width vs 2.53 and coverage. **S4: ≤1.90× AND coverage ≥0.95** | Matched extended-band cluster modes get SD_F 0.06→0.01 and SD_A = observed cross-drive amplitude scatter floored at 0.35 | A5b's own text pre-registers the falsification path: if observed scatter is large, SD_A stays large and the normal band does NOT narrow | `out/verdicts_S3S4.json` (S4), `findings.md` §S4, `figures/fig_s4_tier_update.png` |
| P5 | §3.3 S3 (shear): evaluate repair-corrected finalists; **S3: narrower than 1.51/2.30 while coverage ≥0.95**; held-out-drive coverage, DEV DRIVES ONLY; baseline-through-mapping must reproduce N0 ±0.05; overconfidence audit (hide top-3 → every band widens >1) | Do the finalists actually sharpen the delivered shear band without breaking coverage? | Mapping choice = option (b) relative per-mode perturbation (D2), stated + validated. Finalists = B, D, R (C excluded: review C6 leakage + shares A0's basis). Baseline check is an identity BY CONSTRUCTION → honest limitation stated, plus an added non-identity check | `out/verdicts_S3S4.json` (S3), `out/s3_mapping.json`, `findings.md` §S3, `figures/fig_s3_finalists.png` |
| P6 | §3.4 VAULT RULE: +XY drive NOT read; its QOI answer key stays unbuilt | No `m_xy_990xy` reads anywhere | Enforced by checker grep over my code + a runtime path guard | `check.py` gate G07, `out/vault_guard.json` |
| P7 | §4 Pre-registration BEFORE science + SHA-locked checker proven RED on empty | Gates cannot be tuned to results | Checker run on empty workspace, output retained | `priority_deliverables.md`, `question_framing.md`, `quantity_contracts.md`, `check.py`, `CHECKER.sha256`, `out/checker_red_on_empty.json` |
| P8 | §5 No sampler unless re-driving the existing L5 posterior; reused draws fine if labeled | Reuse the netcg cached NUTS posterior; label as reused; no new posterior | No new sampler run → AGENTS convergence gate inherited from the netcg thread, not re-claimed here | `packet.md` method summary, `out/*.json` `theta_source` field |
| P9 | §5 Deliverables: `packet.md` (method summary first: reused vs mapped vs new), `findings.md`, `out/verdicts_S3S4.json`, ≥3 figures, `decisions_log.md`, `run_all.sh`, checker report, `REUSED_code.sha256` | Full human-review packet | — | all listed files |
| P10 | §5 Continuity: `notes/runs.md` + `docs/report/project_log.md` row, status copied from MY checker | Status never stronger than checker output | — | `notes/runs.md`, `docs/report/project_log.md` |

## Ambiguities flagged (card §0 requires surfacing these)
1. **"1.51 / 2.30 / 2.53" vs scorecard 1.508 / 2.301 / 2.526** — resolved by inspection (D0); the card's
   values are the rounded delivered conservative numbers. No human input needed.
2. **"repair-corrected finalists (repair `verdicts.json`)"** — the repair's verdicts name arms, not model
   files. I map them to the enriched exact bases that exist (`A0_wide__enr`, `B__enr`, `D__enr`, `R__enr`)
   and exclude C with a written reason (D2). ASSUMED — flagged as a warning per the Priority Deliverables
   Gate.
3. **Mapping choice** — the card explicitly delegates this ("state your choice and validate it"). Chosen and
   validated per D2. The baseline validation is an identity by construction; stated as a limitation rather
   than sold as a test.
