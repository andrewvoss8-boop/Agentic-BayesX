# priority_deliverables.md — Card F (model-class selection)

Each PRIORITY ask (restated in my own words), its interpretation, and where it is/will be delivered.
A priority with no delivered artifact = a failure; an "assumed" interpretation without confirmation = a warning.

| # | Priority ask (my words) | Interpretation | Delivered in (artifact) | Status |
|---|---|---|---|---|
| P1 | Define a ladder of competing MODEL CLASSES for the hard accels (different local parameterizations AND damping forms). | M0 baseline / M1 local-stiffness-split / M2 Rayleigh / M3 non-prop localized viscous / M4 correlated discrepancy / M5 combos, each = forward+parameterization+damping+discrepancy with an explicit parameter vector + prior. | `decisions_log.md` D2; `out/model_classes.json` (TODO) | planned |
| P2 | STAGE 1 — fix θ at MAP, screen many classes cheaply with the analytic statFEM evidence (Eq 38) on the modal-feature observable; rank by log-evidence + Bayes factors. | Reduced-model fast loop; evidence on peak-FREQUENCY (decisive for M0/M1/M4) + peak-AMPLITUDE (indicative for M2/M3, confound-limited per D3). | `out/stage1_evidence.json`, `code/stage1_evidence.py` (TODO) | planned |
| P3 | STAGE 2 — RELAX θ (full hierarchical), re-rank the top 2–3 classes with TMCMC (evidence + convergence in one); report all-variable R̂/ESS/div + cross-run logZ stability. | `tmcmc.run_independent` ≥4 runs per class; detached + resumable; non-converged class = YELLOW, not a ranking input. | `out/stage2_tmcmc_<class>.json`, `code/stage2_tmcmc.py` (TODO) | planned |
| P4 | CROSS-CHECK the evidence-winner with the held-out-sensor QOI at the 8 hard accels (interval score / CRPS / coverage / z-std), re-pairing-robust; report BOTH evidence and held-out, reconcile disagreement. | `heldout_qoi.py` + `score.py` for the winner; explicit reconciliation paragraph. | `out/heldout_qoi_winner.json`, `out/scores_winner.json` (TODO) | planned |
| P5 | Modal/Eigenproblem Identifiability gate for every NEW param (M1 strain-energy fraction; M3 damping-dissipation fraction) + FIM/eigen view (how many param COMBINATIONS clear the discrepancy floor). | strain-energy table per new stiffness param; reuse Card D damping gate (`out/cardD_inputs/damping_gate.json`) for damping; FIM eigendecomposition at the realized discrepancy floor. | `out/identifiability_M1.json`, `out/identifiability_M3.json` (TODO) | planned |
| P6 | Evidence-sensitivity gate: log-evidence under ≥2 prior widths per new param; if the ranking FLIPS with the prior → prior-dominated → YELLOW, report both. | sweep prior σ for new params; report rank stability. | `out/evidence_sensitivity.json` (TODO) | planned |
| P7 | Honor the single-impact participation÷damping confound (Card E): use peak-FREQUENCY where confound is weakest; treat amplitude/QOI separately; if M1 and M3 trade participation vs ζ to equal evidence, that IS the finding. | confound stated on every damping conclusion; amplitude/QOI separated from frequency evidence. | `decisions_log.md` D3; packet §confound | planned |
| P8 | WIN CONDITION: an evidence-ranked table (logZ ± stability + Bayes factors + posterior model probs), fixed-MAP then flexible-θ, Ockham trade-off explicit, gated by identifiability + evidence-sensitivity, cross-checked by held-out QOI. Honest "simplest sufficient model wins / data cannot distinguish richer forms (multi-reference needed)" is an equally valid result. | the headline table + a plain-English verdict scoped to the observable/data used. | `out/evidence_ranking.json`, `figures/fig_evidence_ranking.*`, `packet.md` (TODO) | planned |
| P9 | Reproducibility/traceability: immutable check.py FIRST (baseline RED); figures via saved .py + tufte-lint + image-QA; runtime.json; one-command replay; manifest. | check.py written first; run_all.sh; image_qa. | `check.py` (DONE, baseline RED), `run_all.sh` (TODO) | check.py done |

## Acceptance criteria (what makes Card F "done", per AGENTS Done Criteria)
1. Evidence-ranked table exists for fixed-MAP (Stage 1) AND flexible-θ (Stage 2, top classes), with logZ ±
   cross-run stability, Bayes factors, posterior model probabilities, and the observable named.
2. Every new parameter passes (or explicitly fails, with the principled-Ockham-penalty explanation) the
   identifiability gate (strain-energy/dissipation + FIM/eigen) BEFORE any "preferred" claim.
3. Evidence-sensitivity reported under ≥2 prior widths; ranking-flip ⇒ YELLOW + both reported.
4. Evidence-winner cross-checked by held-out QOI at the 8 hard accels; evidence vs held-out reconciled honestly.
5. Every conclusion three-tier-tagged and scoped to exactly what was tested; the confound carried on damping.
6. Replayable from one command; figures tufte-linted + image-QA'd; runtime.json present; check.py exits 0
   only when no RED gate remains.

## Ambiguities flagged to Andrew (priority-clarification gate)
- **A1 (compute commitment):** Stage 1 is fast (reduced model, seconds–minutes); Stage 2 is multi-hour detached
  TMCMC. RECOMMEND: run Stage 1 + baseline validation first, report the screen, THEN commit Stage-2 compute.
  Awaiting Andrew's go (full autonomous run vs Stage-1 checkpoint).
- **A2 (observable framing, D3):** headline evidence on the peak-FREQUENCY observable (damping ~invisible there
  by physics); damping classes judged on amplitude/held-out QOI and labeled confound-limited. Proceeding unless
  Andrew objects.
