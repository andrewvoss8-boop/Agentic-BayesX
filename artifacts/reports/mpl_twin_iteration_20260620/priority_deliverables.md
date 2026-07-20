# Priority deliverables — MPL twin iteration (master/orchestrator)

Restated in my own words from the master prompt (`docs/lab/mpl_twin_iteration_master_prompt.md`) and
Andrew's confirmed decisions D-A..D-H. A priority with no delivered artifact is a failure; an "assumed"
interpretation without confirmation is a warning.

| # | Priority ask (my words) | Interpretation | Delivered where | Status |
|---|---|---|---|---|
| P1 | **Improve the MPL digital twin's held-out scores** by searching FEM MODEL CLASSES over several rounds, ranked by Bayesian evidence + held-out scores. Honest "simplest sufficient wins / data can't distinguish" is an equally valid result. | Multi-round search; each candidate = {mesh/elements, modeling approach, damping model, likelihood, params+priors}; ranked by Stage-1 evidence + held-out scores over 5 LOLO splits; Stage-2 TMCMC on top 1–2/round. | `out/model_registry.json`, `packet.md` round narrative | PENDING (Phase 1+) |
| P2 | **Frozen harness FIRST** (Phase 0) before any candidate: check.py SHA-locked, score.py byte-identical, observable+matching protocol, 5 splits, baseline+climatology. | Phase 0 deliverables below. | this workspace | IN PROGRESS |
| P3 | **THREE held-out scores per split + mean±spread (D-A):** (1) CRPS-skill vs CLIMATOLOGY, (2) interval/Winkler + coverage, (3) band-GRMS error kept un-blurrable (gain-free on \|T\|, or ONE training-only global gain identical across twin/clim/baseline; check.py gates). | `score.py` reused byte-identical; GRMS on the dimensionless ratio \|T\| ⇒ no per-channel gain. | `code/score.py`, `code/mpl_score_qoi.py`, check.py gate | PENDING |
| P4 | **Observable = FULL transmissibility SPECTRA (D-B), no force.** Whole-curve peak-weighted likelihood + held-out QOI on \|T(f)\| (+ gain-free GRMS). Frequency-match allowed ONLY as a Stage-1 evidence screen. Absolute g / apparent mass OUT of scope. | `\|T_a(f)\| = sqrt(PSD_a/PSD_ref)`, ref=shield; whole-curve `frf_score`; freq-match → Stage-1 only. | `code/mpl_observe.py` | IN PROGRESS |
| P5 | **5 splits = leave-ONE-accel-location-out (D-C)** over {interface, beam, valve, avi-L, avi-R}; shield = fixed \|T\| reference (always trained). Coupled-ruler = SEPARATE robustness validation (D-E). | Leakage-controlled (a location's taps + acoustic stay together). | `code/mpl_splits.py` | PENDING |
| P6 | **Baseline + climatology numbers** = score as-received fable rev-3 twin (nominal AND calibrated) on all 5 splits = the numbers to beat; record the climatology no-skill bar. | Immutable reference for improvement-vs-regression. | `out/baseline_scores.json`, `out/climatology.json` | PENDING |
| P7 | **NUTS convergence-gated calibration** on every class (≥4 chains, non-centered, all-variable R̂/ESS/div); non-converged = YELLOW, never "calibrated/converged". | Default NUTS; escalate to TMCMC for Stage-2 / multimodal. | `code/mpl_calibrate.py` | PENDING |
| P8 | **Identifiability gate** for every NEW parameter (strain-energy fraction + finite-perturbation; for damping, dissipation fraction) vs the realized discrepancy floor, BEFORE calling it identifiable. | Reuse modal SE decomposition (modal.py) + FIM eigen-view. | per-class `out/class_<id>.json` | PENDING |
| P9 | **Discretization gate first-class** (mesh/element is a search variable): element-library validation vs a textbook closed form + a refinement/convergence note tying resolution to the <~250 Hz QOI-driving features. | Reuse fable element validation; add per-change note. | per-class | PENDING |
| P10 | **Documentation = a real lab notebook:** model_registry (one row/attempt), per-class FRF/PSD comparison figs (scores+GRMS in legend), FEM geometry + diff graphics, mode-shape GIFs, round narrative; every figure stamped run/split + convergence; tufte-linted + image-QA'd. | Plot gate applied to every saved plotting .py. | `figures/`, `gifs/`, `packet.md` | PENDING |

## Phase 0 frozen-harness checklist (MASTER builds before any candidate)
- [ ] `check.py` FIRST, 3-tier, SHA self-lock + score.py byte-identical assert; baseline RED until deliverables exist.
- [ ] `code/score.py` byte-identical copy of L5 `score.py` (SHA c62c564…) — DONE.
- [ ] `code/mpl_observe.py` — observable + matching protocol (CSV→Welch PSD→\|T_a\|; FEM node map; forward transmissibility; unit tests).
- [ ] `code/mpl_splits.py` — 5 leave-one-location-out splits, leakage-controlled.
- [ ] `out/baseline_scores.json` + `out/climatology.json` — the numbers to beat.
- [ ] `run_all.sh`, `manifest.json`, `runtime.json`, governance docs (this file, decisions_log, assumptions_ledger, question_framing, quantity_contracts, references_reviewed).

## Honest-outcome tiers (win condition)
- GREEN: a class improves held-out CRPS-skill (and/or sharpens calibrated intervals at held coverage) over the carry-forward baseline on ≥4/5 splits, positive prior-robust BIC-adjusted Bayes factor, passes identifiability, mechanism explained.
- YELLOW (equally valid): simplest sufficient class wins / data can't distinguish richer forms (state what extra data would resolve); evidence-positive but held-out-neutral (reconciled); non-converged classes (reported, not ranked).
- RED: fabricated/missing artifacts, integrity break (edited check.py / non-byte-identical score.py), or any claim beyond the no-force scope.
