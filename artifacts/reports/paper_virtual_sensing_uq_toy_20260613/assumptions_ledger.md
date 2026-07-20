# Assumptions ledger

All values are synthetic-toy choices, not measured. Units stated. "Sensitivity priority"
= how likely changing it flips the conclusion.

| ID | Assumption | Value / units | Rationale | Sensitivity |
|----|------------|---------------|-----------|-------------|
| A1 | Modal-ROM forward model | Nm modes, Mr=I (mass-normalized), diagonal Kr0=diag(omega_i^2), Cr0=diag(2 zeta_i omega_i) | Paper Eqs. 4,11,12 | low (definitional) |
| A2 | Modes (E1/E2) | f = [18, 95, 280, 720] Hz; zeta = [0.020,0.015,0.020,0.025] | spread over the [5,1000] Hz optimization window incl. a low- and a high-freq mode | med |
| A3 | Mode-shape matrix Phi (4 channels x Nm) | fixed, distinct rows, channels share all modes | couples channels so observed channels inform masked ones | HIGH (drives transfer of information) |
| A4 | Input distribution / coupling | fixed input vector; gamma0 input-coupling scale | paper gamma ~ 2% | low |
| A5 | Updating parameters | per-mode alpha in [0.5,1.5]; beta in [0.1,10]; gamma in [0.005,0.05] | paper box constraints | med |
| A6 | Truth Sim-to-Real gap | alpha_truth softens high modes (e.g. [0.97,0.90,0.85,0.80]); beta_truth>1; + structured complex discrepancy growing at high freq, OUTSIDE the alpha/beta/gamma span | mimics micro-slip joint softening + un-modeled nonlinearity | HIGH |
| A7 | Measurement noise (observed Ch1/Ch2) | log-amplitude sigma_meas ~ 0.05 (nat log) + phase sigma | sensor noise floor | med |
| A8 | Virtual-target reconstruction error (masked Ch3/Ch4) | correlated complex log field; E1 moderate, E2 swept, calibrated so realized peak error spans the paper's ~8-10 dB; E4 adds a COHERENT bias (peak shift ~10% / amplitude bias) | stands in for FAU output credibility; NOT the FAU network | HIGH |
| A9 | Deterministic updater (A) | scipy least_squares, box-constrained, log-amplitude residual, peak/band weights, virtual target trusted fully (Wch=1) = paper FAU-Up | reproduce paper's choice | low |
| A10 | Bayesian updater (B) | NUTS, >=4 chains; log-amplitude likelihood; masked-channel virtual target down-weighted by an inflated credibility noise (Future-Work #3); learned discrepancy scale sigma_d; E4 adds correlated discrepancy | implements the paper's deferred UQ | HIGH |
| A11 | Data count | ONE synthetic realization per config; no test-to-test / flight-to-flight variability | toy scope | med |
| A12 | Convergence gate | max R-hat <= 1.05, min ESS >= 200, div frac < 2%, >=4 chains | project AGENTS.md | low |
| A13 | Held-out / trust test | TRUE masked-channel FRF + masked-channel peak amplitude QOI, used post-hoc only (paper protocol) | the project's coverage trust test | low (definitional) |

Uncertainty types distinguished in this toy: measurement noise (A7), reconstruction
error / credibility (A8), model-form discrepancy out of the alpha/beta/gamma span (A6),
parameter uncertainty (posterior), and QOI uncertainty (masked-channel peak). Forcing
uncertainty is folded into gamma; aleatory build/test variability is ABSENT (A11) and
flagged as a scope limit.
