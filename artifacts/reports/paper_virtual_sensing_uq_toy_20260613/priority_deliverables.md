# Priority deliverables

Andrew's ask (2026-06-13): "review this paper for applicability to our project. If
applicability is high, prepare a toy example relevant to our project and test findings,
leveraging the work that has already been done." Follow-up: "go on the toy. start small
and iterate to more ambitious challenges. Run at least 4 experiments before stopping. Do
not stop for my feedback."

| # | Priority ask | Interpretation | Delivered in |
|---|--------------|----------------|--------------|
| P1 | Review paper for applicability | Plain-English review + HIGH/MED/LOW verdict + mapping to our threads | chat review + `packet.md` §1 |
| P2 | Toy "leveraging work already done" | Reuse the `forcing_marginalized_damping_toy` NUTS + checker + image-QA scaffold; reuse the project's discrepancy-aware / held-out-coverage method | `code/`, all experiments |
| P3 | "Test findings" of the paper | Reproduce a paper finding (Interp-Up < Meas-Up < FAU-Up ranking; reconstruction error remains ~8-10 dB) AND test it with our method | E2 (ranking), E1/E4 (coverage) |
| P4 | Start small, escalate, >=4 experiments | E1 (small discriminating) -> E2 (baselines+sweep) -> E3 (trend+identifiability) -> E4 (biased-reconstruction stress) | `code/exp1..exp4`, checker gates each |
| P5 | Honest result tiering | Green/Yellow/Red per gate + overall; UQ value = coverage not point precision; alpha/beta = effective indicators | `check.py`, `packet.md` §honest scope |

Acceptance: each experiment produces a summary JSON + figure(s) + checker gates; one
command `bash run_all.sh` replays all; NUTS runs report all-variable convergence
diagnostics; held-out masked-channel coverage is the trust test; honest-scope caveats are
explicit (no claim to reproduce the FAU network or to recover microscopic joint physics).
A priority with no delivered artifact is a failure.
