# priority_deliverables.md — StatFEM consistency toy (Experiment A)

Restating the task-card priorities in my own words, my interpretation, and where each is delivered.
(AGENTS.md Priority-Deliverables gate: a priority with no delivered artifact is a failure; an "assumed"
interpretation without confirmation is a warning.)

| # | Priority ask (task card) | My interpretation | Delivered in |
|---|---|---|---|
| P1 | EVALUATE StatFEM (don't defend/attack); build the criterion, report whichever way numbers fall | Build a consistency + discretization-invariance criterion on a minimal toy; state a per-construction verdict from numbers only | `check.py`, `packet.md` §verdict, `out/sweep_summary.json` |
| P2 | The decisive testable question: as you refine, does each construction's θ posterior CONVERGE to truth AND stay INVARIANT to numerical knobs, or DRIFT? | C1 concentration on θ_true; C2 discretization-sensitivity number; C3 held-out coverage — for all 3 constructions | `figures/figA_money_theta_vs_knob.png`, `out/sweep_summary.json`, `check.py` consistency gates |
| P3 | Three constructions on the SAME data: M-lik (physics-in-likelihood), M-statfem, M-ift (physics-in-prior, learned β) | Three numpyro models sharing one synthetic dataset; method summary states where physics lives + what plays the model-error role (σ_r / d / β) + the equations | `code/nuts_marg.py`, `code/statfem.py`, `packet.md` Method Summary, `figures/figS_schematic.png` |
| P4 | Solver-validation FIRST (forward → analytic truth under refinement) | Convergence-rate study of FD operator (M-lik/M-ift) and FE eigensolve (M-statfem) to analytic ω_n | `code/solver_validation.py`, `figures/figV_solver_convergence.png`, `check.py` solver gate |
| P5 | Sampler NUTS ≥4 chains, all-variable convergence gate or labelled YELLOW; identifiability θ→observable sensitivity | NUTS per cell with R-hat/ESS/div recorded; dω/dθ sensitivity reported; weak-identifiability flagged at high ε | `out/cell_*.json`, `figures/figI_identifiability.png`, `check.py` convergence + identifiability gates |
| P6 | Discretization-resolution gate CENTRAL (discretization is the independent variable) | Knob (N_c, σ_r, h) is the x-axis of the money figure; documented as a first-class assumption | `assumptions_ledger.md`, `figA`, `quantity_contracts.md` |
| P7 | IMMUTABLE check.py written FIRST; GREEN/YELLOW/RED per AGENTS.md; consistency criterion with NUMBERS for all 3 | Checker enumerates the consistency verdict per construction with the C1/C2/C3 numbers; exits non-zero only on RED | `check.py`, `checker_report.json` |
| P8 | Figures: money figure + held-out coverage + construction schematic; each tufte_lint + image-QA + text-overlap auditor; log-frequency axes; provenance + flags on figures | All figures via saved .py + lint + pixel QA + bbox overlap auditor | `code/fig_*.py`, `logs/tufte_*.txt`, `out/image_qa.json`, `out/text_overlap.json` |
| P9 | Short deck (~6–8) gated on non-RED checker: charge / 3 constructions / verdict / gaps+improvements / scope | python-pptx deck built after checker, every claim traces to a checker number | `code/make_deck.py`, `slides/statfem_consistency_toy.pptx` |
| P10 | runtime.json (active + wallclock); OMP/VECLIB=1, float64; resumable | run_all.sh accounts runtime; cells skip finished work | `run_all.sh`, `runtime.json` |
| P11 | References: statFEM 1905.06391, PIFT 2301.07609, IFT 2306.02150; keep probabilistic-solver strand (Conrad/Chkrebtii/Cockayne) separate | Cited in packet with the discretization-error vs model-error distinction stated | `packet.md` §References |
| P12 | Per-construction verdict + gaps + suggested improvements written for Ilias; surface project_log row + notes updates (do NOT self-apply) | Verdict + gaps + improvements section; a proposed project_log row surfaced for the lead | `packet.md` §For Ilias, §Surfaced-for-lead |

Honest scope flags (carried as YELLOW, never hidden): one synthetic realization per cell unless the n-axis
is the variable; the model-form error is a surrogate (Winkler foundation), not a measured real-structure
discrepancy; the verdict is for THIS toy, not a universal proof about StatFEM.
