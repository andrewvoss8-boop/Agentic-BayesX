# Priority deliverables — Task Card E `_Fable`

Restated in my own words, with the interpretation used and where each is delivered.

| # | Priority ask (card) | My interpretation | Delivered in |
|---|---|---|---|
| P1 | Does a **learned discrepancy mean that varies with frequency and sensor location** add transferable held-out value beyond the converged modal posterior + per-drive gain? | Fit `m(f,x,a) = H beta` inside each training fold and score it on data the fold never saw. "Transferable" means it must help at held-out channels, held-out bands, or held-out drives — not at the channels it was fitted on. | `out/stage1_measured_fable.json`, `packet.md` §4, `stage1_checkpoint.md` |
| P2 | Does it add value beyond a **zero-prior-mean GP whose posterior is correctly conditioned at held-out points**? | Arm E1 is the same covariance as E0 with the train-to-test cross-covariance `K_*T` switched on. E2 adds the learned mean under the *identical* covariance. The E2-minus-E1 difference is the only thing allowed to be called mean-model evidence. | `packet.md` §4-5, paired-fold tables |
| P3 | Do not conflate the two mechanisms | `E[H_* beta | train]` and `E[u_* | train]` are computed, stored and plotted **separately** for every held-out point, and reported with their posterior covariance and sum. | `out/stage1_measured_fable.json` (`mean_abs_struct_mean_db`, `mean_abs_gp_mean_db`), figures 3 and 4 |
| P4 | Report an implementation finding / a mean-model finding / a bounded negative result, whichever the evidence supports | The card's interpretation hierarchy is encoded as machine-checked rules in `automatic_decision.json`; I do not choose the verdict, the numbers do. | `out/automatic_decision.json` |
| P5 | Verify the literature claim ceiling directly before coding | Confirm from the two papers that a learned frequency x location **mean** is absent, and refuse any literature-wide novelty claim. | `question_framing.md` §Literature, `packet.md` §2 |
| P6 | Immutable source gate | SHA-256 manifest of every frozen input, RED-on-empty proof, deterministic recomputation of stored numbers, full data inventory; stop if required coordinates or response labels are missing. | `out/source_manifest.json`, `out/known_answer_fable.json`, `out/data_inventory.json`, `out/checker_empty_report.json` |
| P7 | Quantity contract before fitting | `ln(|H1|/H_ref)` with `H_ref = 1 g/lbf`; dB = `20/ln(10) * q`. | `quantity_contracts.md` |
| P8 | Mean basis frozen from design information only | Splines in `log f`, region indicators, k-medoid RBFs, axis one-hots, tensor interaction; all built from coordinates/axes/frequencies, never from residuals. | `out/mean_basis_registry.json`, `code/freeze_fable.py` |
| P9 | Synthetic gates S0–S3, >=20 seeds each, with automatic accept/reject | Null / in-basis / out-of-basis / theta-confounded, on the real geometry and the real split design. | `out/synthetic_fable.json`, `packet.md` §3 |
| P10 | Modal identifiability gate before any per-parameter claim | Strain-energy fractions for all calibration modes and parameter groups + eigendecomposition of `J^T Sigma^-1 J` at the **realized Stage-1 discrepancy floor** + a finite-perturbation check for a low-sensitivity parameter. | `out/identifiability_fable.json`, `packet.md` §6 |
| P11 | Automatic transition after Stage 1 (no human pause) | `stage1_checkpoint.md` + machine-readable `automatic_decision.json` with every threshold, observed value, pass/fail, runtimes and the chosen terminal path. | `stage1_checkpoint.md`, `out/automatic_decision.json` |
| P12 | Stage 2 only on `PROCEED_JOINT` | NUTS/HMC, >=4 chains, full convergence reporting over every raw latent; non-converged = YELLOW and never "NUTS active". | `out/stage2_*.json` if and only if the gate opened; otherwise the decision file records why not |
| P13 | Proposed corrected closure-brief wording, as a separate file | Deliver wording only; do not revise the closure brief itself. | `closure_brief_correction.md` |
| P14 | Figures, checker, runtime accounting, replay | Tufte-linted saved `.py` figure scripts, an immutable SHA-locked checker, `runtime.json` with `active_runtime_s`, `run_all.sh`. | `figures/`, `check_fable.py`, `CHECKER.sha256`, `runtime.json`, `run_all.sh` |

## Ambiguities flagged (assumed, not confirmed)

1. **`_Fable` labelling** — applied as a workspace/file suffix (decisions_log F0).
2. **Cross-drive GP structure** — the card does not say whether `u` is shared or independent across drives.
   Assumed independent (decisions_log F2); the consequence (E1 == E0 in the drive family) is reported, not hidden.
3. **Damping** — assumed the frozen `zeta = 0.01` window-matched value, with a frequency-dependent sensitivity
   (decisions_log F1).
4. **Spatial kernel form** — assumed the frozen exponential form to stay byte-faithful to the in-project
   Schneider implementation (decisions_log F7).

A priority with no delivered artifact is a failure; an "assumed" interpretation without confirmation is a
warning. All four warnings above are live.
