# Human-review packet — plate-test rehearsal (synthetic end-to-end validation of the >200 Hz drumhead test design)

Run: `artifacts/reports/plate_test_rehearsal_20260701/` · replay `bash run_all.sh` · checker `python3 check.py` (SHA-locked BEFORE science; `CHECKER.sha256`)
Audience: aerospace loads (advanced) + Bayesian updating (plain English). NUTS = No-U-Turn Sampler, a
gradient-based MCMC drawing from the posterior; R-hat = between/within-chain agreement (want <= 1.05);
ESS = effective sample size (want >= 200); "posterior sd" = the +/- width of what the data left uncertain.

STATUS: FINAL. All numbers from `out/summary.json` / `out/checker_report.json` / `out/ablation.json` /
`out/decomposition.json`. **Checker OVERALL RED = the pre-registered S1 claim-falsified tier (the
buy-down claim is blocked), NOT a pipeline failure — see findings.md first.** Falsification was
accepted up front; this is the rehearsal doing its job before a hardware ask.

## 1. Method summary (read this first)
- **Decision supported.** Whether to propose the >200 Hz drumhead plate test (12+ Z-accels, +Y drive) on
  the strength of the promised normal-Z band buy-down 5.4x -> 3.5x (netcg `pretest_design.json`) — or to
  revise that design first. Falsification was accepted up front (question_framing.md, pre-registered S1-S6).
- **What is new vs the analytic curve.** The pretest curve never ran inference: it downgraded a per-mode
  sigma by a captured-energy fraction. THIS run simulates the test end-to-end: synthetic truth (with fine
  structure the array cannot fully capture), noisy sensor data, the ACTUAL joint NUTS posterior, the
  delivered band, and calibration against the known truth.
- **Model form.** Reduced FEM K(theta) = A_fix + sum_g theta_g A_g (9 stiffness groups, 74-dim); QOI =
  tray net-CG NORMAL-Z force spectrum (7004C force convention; 45-260 Hz, 400 pts, 1-oct smoothing).
- **Likelihood (data-usage choice, explicit).** TWO feature likelihoods, jointly: (i) modal FREQUENCY
  (Kiran Eq 25) on the 20 existing measured modes + the 4 target drumhead modes (the new test measures
  them, 1% tier); (ii) mode-SHAPE samples at the plate sensors, y ~ N(Phi_s c, sigma_y) with the basis
  frozen at theta_MAP (A9/D4) — NOT a whole-FRF likelihood (multimodal; standing program finding).
- **Inferred (one joint NUTS, 4 chains, x64):** theta (9), sigma_w2, shape coefficients c (4 targets x
  12 drumhead-basis modes), sigma_y. **Fixed:** zeta = 1%, tier sigmas, frozen basis, kappa (truth-mix
  scale, calibrated so tier-consistency holds — D8). **Latent, not inferred:** out-of-basis fine
  structure d (6 above-band plate modes) — carried in the DELIVERY as prior-scale draws, never fitted.
- **Truth generator does NOT share the inference simplifications** (theta_true from the L5 posterior;
  true shapes mix the basis AND the out-of-basis modes; sensors get 10% RMS noise; arm A3 adds 1.5-in
  placement jitter the inference is not told about). Realized truth log-amp spread 0.86 (heavy-tailed,
  robust 0.56; target 0.80) — coincidentally near the real-data DD3 estimate 0.86.
- **Integrity guard (D8).** The first smoke run exposed a prior/tier inconsistency in MY code (band 7.96x
  from a mis-scaled shape prior); fixed BEFORE any recorded run; prior-only (no-sensor) delivery now
  reproduces 5.81x vs the analytic 5.4x (the honest heavy-tail difference); the pre-fix artifact was
  deleted; check.py was locked before all of this and never touched.

## 2. Pre-registered criteria and results (checker-backed)
| # | criterion | threshold (GREEN) | result | status |
|---|---|---|---|---|
| S1 | A1 (12 sensors) median band factor | <= 3.5x | **6.20x, >= A0 6.17x** | **RED — claim falsified (the pre-registered negative-answer tier)** |
| S2 | A1 coverage (mean energy-wtd, 1-oct) | >= 0.90 and >= 6/8 seeds >= 0.85 | 0.998; 8/8 >= 0.85 | GREEN |
| S3 | NUTS convergence, all runs | R-hat <= 1.05, ESS >= 200, div < 2% | 35/36 (A0_s6 pathological after retune; excluded+reported) | YELLOW (A0 7/8); GREEN others |
| S4 | A0 (1 sensor) integrity — no false sharpening | median >= 4.5x | 6.17x | GREEN |
| S5 | A3 (12 + jitter) robustness | band <= 4.2x and cov >= 0.85 | 6.54x / cov 1.0 | YELLOW (threshold assumed the 3.5x regime; coverage clean) |
| S6 | pooling checkable: target amp posterior sd | <= 0.40 (prior 0.80) | 0.579 | YELLOW (partially constrained; mean within 0.08 of truth) |

Sensitivity (assumption-mismatch, pipeline held at 0.8): truth sigma 0.4 -> 5.72x; truth sigma 1.6 ->
~104x but coverage 1.0 — the pipeline degrades by WIDENING, never by lying.

## 2b. Mechanism (post-hoc ablation, `out/ablation.json` + `out/decomposition.json` — labeled, no NUTS)
Ladder from the analytic recipe to the honest delivery (median band factor):
`L0 repro 6.25x -> L1 analytic floor (target sigma 0.35) 3.05x -> L2 + THETA POSTERIOR 4.93x ->
L3 + measured target freqs 4.79x -> L4 signed-mixture truth 5.53x -> L5 + out-of-basis 5.48x`.
The analytic curve failed because it FROZE theta at MAP: the +/-4% stiffness posterior rotates the
near-degenerate 246-258 Hz drumhead eigenvectors and scatters every band mode's net-Z participation.
Even a PERFECT 4-target test leaves ~5.1x (L6); **pinning ALL 12 drumhead-band modes recovers 2.81x
(L7, oracle bound)** — the revised test scope. See findings.md for the revised recommendation.

## 3. Figures
- `fig_buydown_rehearsed.png` — the money figure: rehearsed per-seed band factors vs the analytic curve.
- `fig_bands_vs_truth.png` — delivered band vs truth spectrum (small multiples, seed 0).
- `fig_amp_recovery.png` — per-target amplitude recovery, truth vs posterior.
- `fig_sensor_data.png` — clean truth vs observed noisy sensor samples (the data the twin sees).
- `fig_graphical_model.png` — run-specific model schematic.

## 4. Honest limits (carry with every number)
- SYNTHETIC truth: the fine structure lives in FEM plate modes above the band. If the REAL drumhead error
  is outside the FEM's shape family entirely (the program's shape-wall finding says it can be), rehearsed
  coverage is optimistic. The rehearsal certifies MACHINERY + INFORMATION CONTENT, never the real number.
- Identification from the +Y drive is assumed to succeed (A6); identification failure not modeled.
- theta_true is drawn from the same L5 posterior used in delivery (A3) — theta is not under test here.
- Single drive arm (+Y); +Z(990) arm deferred (D6). Uniform-mass tray proxy (A13).
- Mode-order bookkeeping across theta_true draws can swap near-degenerate cluster members (noted, truth-side only).

## 5. Gate coverage
| gate | where |
|---|---|
| Priority deliverables | priority_deliverables.md |
| Question/decision + pre-registration | question_framing.md |
| Quantity contracts | quantity_contracts.md |
| Assumptions ledger | assumptions_ledger.md (A1-A13; data counts; inferred/fixed/latent) |
| Identifiability | captured-energy per target + subspace min-eig (pretest) + per-target posterior sd (S6) |
| References | pretest_design.json (claim under test), 7004C convention, Kiran Eq 25; netcg contracts inherited |
| Plots | figures/ (Tufte-linted `code/figs.py`, 0 flags; convergence + synthetic status on every figure) |
| Sensitivity | S_sd04/S_sd16 arms + A3 jitter |
| Discretization | inherited netcg grid (A12); 1-oct = the delivery resolution |
| Verification | check.py (SHA-locked pre-science) -> out/checker_report.json |
| Runtime | runtime.json (active vs wallclock; ~36 NUTS runs) |
| Convergence | per-run in out/runs/*.json; worst-case reported in summary + on figures |
