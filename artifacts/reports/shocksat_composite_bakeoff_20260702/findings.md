# findings — COMPOSITE BAKE-OFF (numbers never stronger than the locked checker; check.py SHA-locked before science)

Overall checker: **YELLOW** (53 GREEN / 6 YELLOW / 0 RED science; the 6 YELLOW = Beck-S2 net-CG coverage
misses, all documented below). All 6 arms NUTS-converged (R-hat ≤ 1.0011, ESS ≥ 580, 0 divergences).
Winner's curse: every "best" is best-of-N=6 arms; the M1 remodel is best-of-151 candidates.

**Pre-registered falsifications are LABELED LOUDLY as "claim falsified" (honest finding), NOT "pipeline failure."**

## 1. Agentic remodeling did NOT earn delivery (pre-registered claim FALSIFIED — honest finding, not a pipeline failure)
The evidence-selected M1 remodel = **`rand10`** (a random-tranche edit) beat the inherited FEM on the
SHAPE-INCLUSIVE (freq+MAC) evidence by **logZ +54** (P(M|data)=0.72, prior-robust *top* across σ_prior
∈ {0.15,0.25,0.40}). But by the pre-registered **R4** rule it did NOT beat M0 on held-out R1 or R2:
its net-CG sharpness (M1S0 1.94/1.66/2.42×; M1S1 1.71/1.51/2.50×) is not sharper than M0's, and its
per-point R1 skill (−0.75/−0.71) is no better. **Evidence-only wins are reported, not delivered.**
→ On this QOI/data, agentic remodeling did not improve the delivered net-CG twin.

## 2. Evidence ≠ held-out — the central methodological result
Shape-inclusive Bayesian evidence crowned a remodel (+54 logZ, decisive) that does **not** improve held-out
QOI prediction. This is the strongest vindication of the card's insistence on held-out scoring over
evidence-only selection. Secondary: the freq-only evidence reference would have crowned the **same** candidate
(`rand10`, −279.3 vs shape-inclusive −292.3), i.e. the MAC/shape block did **not** materially re-rank the
candidates here — so the "freq-only re-crowns a frequency-fitter" risk did not bite this time, though the
forbidden-selector rule remains sound in principle (freq-only is blind to shape error in general).

## 3. MAC-as-θ-constraint (S1) ~ NULL again, now on multi-reference data at the QOI level (reproduces modelclass_L5 §3a)
S1 (freq+MAC) and S0 (freq-only) are statistically indistinguishable: M0S0 vs M0S1 R1 skill −0.784 vs −0.766,
σ 1.084 vs 1.082; R2 sharpness within ±0.1× per QOI. The pre-registered rule delivers **M0S1**, but ONLY
because M0S0 tripped a marginal R3 widen threshold (§5) — the two are effectively co-equal. **Adding MAC to the
likelihood produced no material θ-improvement.** (S1 used a documented Tikhonov-regularized first-order shape
derivative, δ=1.6×10⁴ (rad/s)², to avoid the 246–258 Hz eigenvector-gradient pathology — D11/A7.)

## 4. Beck shape-field (S2): per-point amplitude CHAMPION, but its confidence does NOT safely transfer to the net-CG band
- **R1 per-point (held-out sensors), CONFIRMS the historical L8b lever:** Beck halves the CRPS-skill deficit
  (M0S2 −0.340, M1S2 −0.366 vs the S0/S1 −0.71…−0.78) and sharpens σ_QOI (0.89/0.91 vs 1.08) — directionally
  the shapefield_lever.json −0.68→−0.25 result, on a stricter non-leaky σ (D9).
- **R2 net-CG band — pre-registered "Beck sharpens held-out amplitude" claim is FALSIFIED at the QOI level:**
  Beck UNDER-covers the net-CG truth-ensemble band (M0S2 shear 0.70/0.57, normal 0.32; M1S2 0.55/0.58/0.23) →
  fails the 0.95 hard gate → **cannot win any net-CG QOI**. Mechanism: Beck's confident inferred shapes shift
  the net-CG modal participation off the FEM-shape truth ensemble.
- **Honest nuance (avoids a circular-reference trap):** on the ARM-INDEPENDENT held-out-DRIVE answer key
  (measured-FRF reconstruction), Beck **covers shear_X perfectly (1.00/1.00, best of all arms)** and is
  comparable on shear_Y (0.81–0.82) — so the shear R2 truth-ensemble "miss" is largely an artifact of the
  truth ensemble being built from the (imperfect) FEM shapes Beck corrects. **But for normal_Z there is NO
  data answer key** (drumhead shapes unmeasured), and Beck's confident shapes under-cover the only available
  plausible-truth band (0.23–0.32) → **do NOT deliver Beck for the normal QOI.** Beck helps where you can
  VALIDATE per-point against sensors; its confidence is unsafe for the unmeasured-drumhead-driven normal QOI.

## 5. DELIVERED TWIN: inherited FEM (M0) + freq(+MAC) likelihood + statFEM F(k), for BOTH shear and normal
- **Shear:** M0S1 (≈M0S0), band ~1.72×(X)/2.06×(Y) FEM+6dB, covers the hard gate, held-out-drive validated
  (shear_X mean-strong 0.92 over 5/5 drives, shear_Y 0.94). **Normal:** M0S1, band ~2.34× FEM+6dB, covering,
  driven by UNMEASURED drumhead modes (no data validation possible — standing caveat carried).
- **This essentially REAFFIRMS the proven netcg statFEM F(k) twin.** The three composite additions
  (agentic remodel, MAC-in-likelihood, Beck shape field) did not improve the delivered net-CG bands.
- **Caveat on the delivery pick (§3):** M0S1 over M0S0 is a marginal-R3-threshold artifact, not a real S1 win;
  the delivered twin is honestly "inherited FEM + F(k)", MAC optional.

## 6. R3 overconfidence audit — one marginal artifact, transparently flagged
M0S0 was R3-DISQUALIFIED, but the disqualification is a threshold artifact: it passes cleanly on both SHEAR
QOIs (widen 1.36/1.29, where measured modes truly drive the load) and only "fails" normal_Z (widen 1.01 vs
1.03 threshold) — where, after hiding the 3 top measured modes (32.7% participation), the band **still covers
at 0.993**. So it is NOT falsely narrow; the F(k) unmeasured-tier already makes the normal band wide. All other
arms pass R3 on all discriminating QOIs. (theta_only-style structural-1.00 overconfidence: none observed.)

## What would change these conclusions
- A per-point R1 that credited Beck AND a net-CG band that used Beck's corrected shapes in BOTH the band and
  the truth ensemble could flip Beck's shear R2 (its held-out-drive coverage already passes). The normal-QOI
  Beck under-coverage would remain (unvalidatable) → the >200 Hz plate test is still the binding pre-test lever.
- A remodel candidate that improved held-out shear sharpness (none of 151 did) would revive the agentic track.
