# Human-review packet — COMPOSITE BAKE-OFF (agentic remodel × shape-in-likelihood × Beck shape-field × F(k))
Workspace `artifacts/reports/shocksat_composite_bakeoff_20260702/` · one-command replay `bash run_all.sh`
· checker `check.py` SHA-locked BEFORE science (`CHECKER.sha256`) · **overall YELLOW** (53G/6Y/0R science).

Audience note (per AGENTS.md): ML/stats terms are defined in plain English on first use; structural-dynamics
terms (FRF, MAC, mode shapes, net-CG apparent-mass force) are used directly.

---

## 0. First-pass method summary (read this first)
- **Question (one line):** does combining (a) agent-generated model-form candidates selected by Bayesian
  EVIDENCE on a shape-inclusive likelihood, (b) shape (frequency+MAC) in the likelihood, and (c) the Beck
  inferred shape FIELD — each carried with the proven statFEM F(k) output discrepancy — beat the proven
  non-Beck baseline on HELD-OUT data?
- **Model form:** reduced 80-dim modal model per candidate, K(θ)=A_fix+Σθ_p A_p (mass=I), θ_p = group
  stiffness multipliers (9 groups; +couple/joint params for connectivity remodels). Modes by eigendecomposition.
- **Likelihood (3 shape-use axes), all with the ALWAYS-ON statFEM F(k) output discrepancy:**
  - **S0** freq only: ω̂²_r ~ N(λ_kr(θ), (σ_w2·ω̂²_r)²) over all matched .ash modes (Kiran Eq 25).
  - **S1** freq+MAC: + (1−MAC_r)²/σ_mac² with MAC (modal assurance criterion = squared-cosine shape match,
    0–1) on the measured survey DOFs; shape derivative Tikhonov-regularized (D11) to avoid the degenerate-
    cluster eigenvector-gradient blow-up.
  - **S2** Beck mode-matching-free: system shapes φ are FREE parameters, pulled to Rayleigh-consistency with
    K(θ) and toward the measured .ash shapes (MAC); the shape FIELD itself is corrected.
- **Data count:** 33-mode .ash EMA survey (76 nodes × 3 axes) = the shape-truth source used by every arm; 5
  tap-test drive FRF caches (+X, +Z/990, +XY, +Z/900, +Y) held OUT as leave-one-drive-out answer keys.
  No flight/build/test-to-test variability data → that variability is NOT modeled (absent), stated (A9).
- **Whole-data vs feature likelihood:** MODAL-FEATURE (matched eigenvalues + MAC), not whole-|H| (which is
  multimodal/near-singular on this structure — prior threads). QOI band via net-CG forward + F(k) MC.
- **Inferred:** θ (and φ for S2), σ_w2, (σ_mac | σ_φ), one global gain per held-out fold. **Fixed:** ζ=0.01,
  tier σ's (A2/A3), F(k) form (A4), tray region z≥55 in, the frozen Hungarian mode pairing. **Not-inferred
  latents:** per-mode true amplitudes (marginalized by tier Monte-Carlo), unmeasured drumhead shapes.
- Run-specific graphical model: `figures/fig_graphmodel.png`.

## 1. The matrix (pre-registered; ALL arms reported, no silent dropping)
| arm | model | shape use | NUTS R-hat | R1 skill / σ | R2 sharpness (X/Y/Z) | R2 covers? | R3 |
|---|---|---|---|---|---|---|---|
| M0S0 | inherited FEM | freq (baseline A) | 1.0009 | −0.78 / 1.08 | 1.84 / 1.98 / 2.54 | yes | DQ* |
| M0S1 | inherited FEM | freq+MAC | 1.0011 | −0.77 / 1.08 | 1.72 / 2.06 / 2.34 | yes | pass |
| M0S2 | inherited FEM | Beck field | 1.0004 | **−0.34 / 0.89** | 1.78 / 2.25 / 1.82 | **no** | pass |
| M1S0 | remodel `rand10` | freq | 1.0008 | −0.75 / 1.10 | 1.94 / 1.66 / 2.42 | yes | pass |
| M1S1 | remodel `rand10` | freq+MAC | 1.0008 | −0.71 / 1.08 | 1.71 / 1.51 / 2.50 | yes | pass |
| M1S2 | remodel `rand10` | Beck field (composite D) | 1.0005 | **−0.37 / 0.91** | 1.60 / 2.18 / 1.57 | **no** | pass |
Sharpness = 95%-band GRMS ratio vs FEM+6dB (lower=sharper); proven statFEM F(k) bars 1.508/2.301/2.526.
R1 skill = held-out-sensor per-point CRPS-skill vs climatology (higher=better); σ = QOI log-amp spread.
*M0S0 DQ is a marginal threshold artifact — see §4. Figures: `fig_matrix_money.png`.

## 2. Headline results (numbers = checker; see findings.md for the full statements)
1. **Agentic remodeling did NOT earn delivery (pre-registered claim FALSIFIED, honest finding).** The
   evidence-selected M1 (`rand10`) won shape-inclusive evidence by **+54 logZ** (P=0.72, prior-robust top) but
   did not beat M0 on held-out R1 or R2 → by the pre-registered R4 rule it is reported, not delivered.
2. **Evidence ≠ held-out** is the central methodological result: even shape-inclusive evidence crowned a
   remodel that does not improve held-out QOI prediction. (Freq-only evidence would have crowned the SAME
   candidate — the MAC block did not re-rank here.)
3. **MAC-as-θ (S1) ~ NULL again** on multi-reference data at the QOI level (reproduces modelclass_L5 §3a).
4. **Beck (S2) is the per-point amplitude champion** (R1 −0.34/−0.37 vs −0.71…−0.78; σ 0.89 vs 1.08) **but
   its confident shapes do NOT safely transfer to the net-CG band** (R2 under-covers; "Beck sharpens held-out
   amplitude" is CONFIRMED for per-point sensors, FALSIFIED for the net-CG normal QOI). See §3.
5. **Delivered twin = inherited FEM (M0) + freq(+MAC) + statFEM F(k)** for both shear and normal — essentially
   REAFFIRMING the proven netcg statFEM F(k) twin; the composite additions did not improve the delivered bands.

## 3. Why Beck helps per-point but fails the net-CG band (the subtle, decision-relevant point)
Beck's free shapes reduce per-point amplitude error (they fit the sensor FRFs better) but they are a CONFIDENT
point-direction. Propagated to the net-CG force (a mass-weighted sum over the tray), that confidence produces a
band that sits off the FEM-shape-based truth ensemble → under-coverage. To avoid a circular-reference trap we
also scored the ARM-INDEPENDENT held-out-DRIVE answer key (net-CG force reconstructed from each drive's MEASURED
FRFs): there Beck **covers shear_X perfectly (1.00)** — so the shear R2 "miss" is largely a truth-reference
artifact. **But normal_Z has no data answer key** (drumhead shapes unmeasured), so Beck's confident normal band
cannot be validated and under-covers the only plausible-truth band (0.23–0.32). **Verdict: do not deliver Beck
for the unmeasured-driven normal QOI; the >200 Hz plate test remains the binding pre-test lever.**

## 4. Integrity, caveats, and the two flagged artifacts (nothing hidden)
- **Both historic metric traps encoded and clean:** (i) NO per-mode amplitude/phase fitting in any selection
  score (LSQ appears ONLY in the arm-independent held-out-drive answer key, D2); (ii) mode pairing by ONE-TO-ONE
  Hungarian assignment, FROZEN per model (not greedy MAC re-pairing). LIMITED DATA, NOT LIMITED MODES: full
  in-band mode set (n=25 matched for M0, 22 for M1), all 5 drives; no mode pruning.
- **M0S0 R3 "disqualification" is a marginal artifact (§6 findings):** it passes both SHEAR QOIs (widen
  1.36/1.29) and only trips normal_Z (widen 1.01 vs 1.03) — where after hiding the top-3 measured modes the
  band STILL covers at 0.993 (not falsely narrow). So M0S0≈M0S1; the delivery pick of M0S1 is not a real S1 win.
- **Sampler incident (fixed, documented):** M0S1's freq+MAC hung ~2 h on the 246–258 Hz degenerate-cluster
  eigenvector gradient (A7 risk realized). Fixed with a Tikhonov-regularized first-order shape derivative
  (δ=1.6×10⁴, D11) — a sampler-stability change, not a result change; the arm then ran in 25 s and converged.
- **Convergence:** all 6 arms R-hat ≤ 1.0011, ESS ≥ 580, 0 divergences (4 chains, x64). This is "NUTS active".
- **Recovered from 1 computer crash** mid tier-2 (11/29 eigensolve packages preserved; resumable).

## 5. Assumptions, references, contracts, runtime
`assumptions_ledger.md` (A1–A17, values/units/sensitivity), `references_reviewed.md` (7004C, Kiran, statFEM,
Beck, Allemang, Fox-Kapoor, Schneider), `quantity_contracts.md` (net-CG force + per-point peak + pairing +
evidence), `decisions_log.md` (D1–D11), `runtime.json` (active 8150 s productive; wallclock 20079 s incl. the
discarded 2 h hang + crash downtime).

## 6. Figures (all Tufte-linted scripts; each states run/dataset + convergence)
- `fig_matrix_money.png` — the money figure: R2 sharpness vs proven bars (x=fails gate), R1 CRPS-skill+σ, R3 widen.
- `fig_evidence.png` — shape-inclusive evidence per class × prior width + freq-only reference.
- `fig_funnel.png` — remodeling funnel 151 → ~30 full eigensolves → evidence winner.
- `fig_heldout_drives.png` — per-drive held-out coverage (arm-independent answer key), shear X/Y.
- `fig_graphmodel.png` — run-specific graphical model / likelihood diagram.

## 7. Bottom line for the decision
Deliver the inherited-FEM net-CG twin with statFEM F(k) (shear band ~1.7–2.1×, held-out-drive validated;
normal band ~2.3–2.5×, unmeasured-driven caveat). The three composite levers did not improve the delivered
net-CG bands: **agentic remodeling did not earn a place in the workflow on this QOI/data**, MAC-in-likelihood is
~null, and Beck's shape field — while the best per-point amplitude predictor — is not safe for the net-CG normal
QOI. The single most informative next test dollar remains a >200 Hz drumhead/plate modal test.
