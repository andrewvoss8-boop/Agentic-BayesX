# Priority deliverables — plate-test rehearsal (synthetic end-to-end validation of the >200 Hz drumhead test design)

Approved by Andrew 2026-07-01: "Good idea. Go ahead and execute it, the original idea."
(= the rehearsal ALONE; the 2x2 M2-prior-vs-IFT ablation was offered as a bundle and NOT taken.)

| # | priority ask (my restatement) | interpretation / where delivered | status |
|---|---|---|---|
| P1 | Prove (or falsify) IN SILICO that the promised plate-test buy-down (normal-Z band 5.4x -> 3.5x at 12 sensors, `shocksat_netcg_method_selection_20260701/out/pretest_design.json`) survives the FULL Bayesian pipeline — actual inference on simulated noisy plate data, not the analytical sigma-downgrade curve. | `out/summary.json` (per-arm band factors + coverage), `figures/fig_buydown_rehearsed.png` (analytic vs rehearsed money figure) | pending |
| P2 | Pre-registered success criteria evaluated by an immutable checker (thresholds in `question_framing.md`, locked before science). | `check.py` + `CHECKER.sha256` + `out/checker_report.json` | pending |
| P3 | Integrity arm: current 1-sensor instrumentation must NOT falsely sharpen (if it does, the rehearsal is circular). | arm A0 in `out/summary.json` | pending |
| P4 | Robustness: graceful degradation under sensor-placement error; sensitivity to the truth-generation amplitude sigma (0.4 / 0.8 / 1.6). | arm A3 + sensitivity rows in `out/summary.json` | pending |
| P5 | Pooling verifiability: show the per-mode drumhead amplitudes become individually data-constrained (posterior sd << prior 0.8) at 12 sensors — i.e. the netcg pooling assumption becomes CHECKABLE with the new data. | `out/summary.json` amp-recovery block + `figures/fig_amp_recovery.png` | pending |
| P6 | Honest deliverable either way: if the claim fails, a REVISED test design + the honest number (falsification accepted up front). | `findings.md` | pending |
| P7 | Full harness gates: NUTS convergence on all variables, Tufte-linted figures, packet, replayable one command, runtime accounting. | `run_all.sh`, `packet.md`, `runtime.json` | pending |

Ambiguities flagged at start (resolved by stated assumption, cheap to revisit):
- "12 well-placed accels" = the greedy captured-energy placement from `pretest_design.py` (same selection logic re-run here). If Andrew wants a different array geometry, re-run with a different candidate set — the pipeline is arm-parameterized.
- Drive = +Y only (the pretest recommendation). +Z(990) arm is a documented deferral (cost control), NOT run.
- The rehearsal validates the MACHINERY + INFORMATION CONTENT claim on synthetic truth; it cannot certify the real drumhead number (only the real test can). Stated in every deliverable.
