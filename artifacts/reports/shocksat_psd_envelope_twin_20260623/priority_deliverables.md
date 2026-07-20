# Priority deliverables — ShockSat PSD-envelope twin

Restating Andrew's PRIORITY ask in my words, with where each is delivered. (AGENTS Priority-Deliverables Gate.)

| # | Priority ask | Interpretation (locked, D0/D1) | Delivered in | Status |
|---|---|---|---|---|
| P1 | Held-out-sensor PSD prediction with a posterior band | Response PSD = \|H\|²·S_F(flat); twin = converged L5/Card G modal-feature twin; predictive 97.5th-pct band | (build) | pending |
| P2 | Compare twin band vs original FEM PSD vs measured held-out data | Per held-out sensor × reference drive, overlay all three PSDs | figures + scorer | pending |
| P3 | Smooth envelope over peaks of FEM+6 dB and of the twin upper band | peak-pick + piecewise-linear log–log, IDENTICAL both (Q2) | `envelope.py` | pending |
| P4 | **WIN test:** twin upper-band envelope GRMS < FEM+6 dB envelope GRMS, while still enveloping data | GRMS ratio < 1 AND no energy-significant exceedance (Q3 = dB-exceedance energy-weighted, not binary) | `score_envelope.py` | pending |
| P5 | Sweep training fraction 50→90% (leave-sensors-out) | MC over splits per fraction; win-rate vs fraction; start at 90% (validity probe) | `run_sweep.py` | pending |
| P6 | Use the (newly pulled) clean multi-reference modal data, both drive nodes | Test01/02/04 (node 990) + Test06 (node 900); drop SNR-limited taps | data caches | in progress |

Acceptance / honesty:
- A priority with no delivered artifact = failure; an "assumed" interpretation without confirmation = warning.
  All five Q answers are CONFIRMED by Andrew (D1), so no unconfirmed assumptions on the deliverable definition.
- Trust gate = held-out coverage expressed as energy-weighted exceedance; GRMS-win is reported only where the twin
  envelopes the data (and FEM+6 dB's own exceedances are reported — where FEM+6 dB fails to envelope, it is not a
  valid spec to "beat").
- Honest-negative is an acceptable outcome (Card G φ_s ceiling is real); the probe (D4) decides before full compute.
