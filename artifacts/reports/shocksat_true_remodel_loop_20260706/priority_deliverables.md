# Priority Deliverables — ShockSat TRUE Agentic Remodeling Loop (20260706)

Restatement of the card's priority asks in my own words, each with its interpretation and where it is delivered.
A priority with no delivered artifact is a FAILURE; an "assumed" interpretation is a WARNING (flagged).

| # | Priority ask (my words) | Interpretation | Delivered in |
|---|---|---|---|
| P-1 | Answer ONE falsifiable question: can a closed-loop, shape-changing agent beat the inherited FEM's held-out FRF prediction AND beat random search, confirmed on a pristine vault. | A WIN requires S1 (beat A0 on dev by >=+0.05 AND >=2x fold SE AND beat A0 on vault) + S2 (beat random on dev) + S3 (honesty gates pass). Anything less = pre-registered claim FALSIFIED, reported loudly, not as pipeline failure. | `packet.md` (S1/S2/S3 verdicts), `findings.md`, `out/query_log.jsonl` |
| P-2 | Build a genuinely shape-changing action space (the new capability). | Families 1-4 (true refinement / region splits / correct t-vs-t³ thickness / added DOFs) actually implemented and unit-validated; parametric scales allowed only as ingredients, tagged `parametric_only`. Run is VOID if families are not real. | `code/actions.py`, V1-V5 gate outputs, `out/candidate_specs/` |
| P-3 | Close the loop (propose -> screen -> dev-score -> learn -> propose) for >=3 rounds. | Diagnosis reads TRAIN residual FIELDS only; dev returns SCALAR scores only; each round writes a learn summary showing proposals respond to evidence. | `out/diagnosis_r*.json`, `out/round_r*_summary.md`, `code/loop.py` |
| P-4 | Mandatory random-search comparator on the SAME action space + budget (the S2 intelligence test). | A2 = uniform random proposals, fixed seed 20260706, no diagnosis/learning, <=60 dev queries. Reported, never dropped. | `out/query_log.jsonl` (track=random), `packet.md` S2 |
| P-5 | Three-tier data discipline: TRAIN fits θ; DEV steers under a hard <=60-query budget with a query log; VAULT graded once after finalists are SHA-frozen. | Budget counted from `query_log.jsonl`; no dev-residual-field reads in the loop; vault freeze SHA timestamp precedes vault download; vault touched once. | `out/query_log.jsonl`, `VAULT_FREEZE.sha256`, `check.py` |
| P-6 | Physics-honest metrics: no per-mode/per-channel amplitude LSQ in selection; θ_MAP + ONE global gain per fold; frozen Hungarian pairing per model. | P1 = median per-channel log\|H\| Pearson corr, 45-260 Hz, fold-averaged with spread; single-fold numbers never reportable; margin must clear 2x fold SE. P2 = log-amp RMSE at matched peaks (dB). | `code/score.py`, `out/scores_*.json`, checker no-LSQ grep |
| P-7 | Mechanics validation BEFORE science (V1-V5) — the one place "keep going" yields to "fix first". | V1 baseline reproduction <=1e-8; V2 free-free 6 RBM ~0; V3 refinement null; V4 t vs t³ physics; V5 pairing robustness. Failure BLOCKS science. | `out/mech_gates.json`, `check.py` |
| P-8 | NUTS posteriors for finalists + A0 (4 chains, x64), all-variable convergence; statFEM F(k) bands for the net-CG QOI; honesty audits (leave-modes-out, winner's-curse N, dev-vs-vault gap). | Screening is MAP/deterministic and labeled NO-sampler; only finalists+A0 get NUTS. Non-converged finalist = YELLOW, intervals labeled not-trustworthy. | `out/nuts_*.json`, `out/qoi_*.json`, `out/honesty_*.json` |
| P-9 | Pre-registered, SHA-locked, immutable checker; one-command replay. | `check.py` written + hashed BEFORE any science; `bash run_all.sh` replays; status per Result Status Standard (GREEN/YELLOW/RED). | `check.py`, `CHECKER.sha256`, `run_all.sh`, `checker_report.json` |
| P-10 | Continuity: append-only `notes/runs.md` entry + `docs/report/project_log.md` row, status copied VERBATIM from the checker. | Appended only at the END, status never stronger than checker output. No durable-rule/checker/other-workspace edits. | `notes/runs.md`, `docs/report/project_log.md` |

## Honesty stance carried through every deliverable
- A clean falsification ("no candidate beat A0 on the vault" / "agent did not beat random") is a VALID reportable
  outcome, labeled "pre-registered claim falsified", never as pipeline failure.
- No success/metric claim without checker output. No screen presented as a posterior, no proxy as the metric,
  no modulus scale as a thickness change.
- Delivering a replacement twin is NOT this run's job; whether any winner replaces the inherited FEM is a human
  decision surfaced in the packet.
