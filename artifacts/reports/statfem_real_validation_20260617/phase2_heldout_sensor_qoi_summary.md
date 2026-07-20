# Phase P2a interim summary — L5 → held-out-SENSOR QOI (Card A next-action #1)

One-screen reviewable summary. Status tier per finding in brackets. Full design: `decisions_log.md` D12.
Artifact: `code/heldout_qoi.py` → `out/heldout_qoi_L5.json` (reproducible; 4 chains × 1000+1000, 400 pred draws, 73 s).

## What this set out to do
Push the CONVERGED modal-frequency twin (D11) onto the card's PRIMARY quantity of interest (QOI): peak
accelerance |H| and band-GRMS [g/lbf] at channels we did NOT use to fit — the held-out-SENSOR trust test.
"QOI" = a scalar engineers act on; "calibrated" = the 95% predictive interval covers truth ~95% of the time;
"sharp" = the interval is narrow. "Proper score" (interval/Winkler, CRPS, log-predictive-density) rewards both
at once, so a method cannot win by inflating bands.

## Method (held-out is the SENSOR)
- Split 80 dynamic-range-eligible mapped channels (peak/floor ≥ 30×) into 48 observed / 32 held-out (seed 0).
- Calibrate the 9 group stiffness multipliers θ from modal peak FREQUENCIES extracted from the OBSERVED channels
  ONLY (frequencies are a global structural feature; held-out magnitudes are never seen), 24 matched to FEM modes,
  L5 NUTS eigenvalue likelihood. **Calibration CONVERGED: R̂ 1.0015, ESS 1800, 0 div**; σ_w2 (rel. modal-freq
  error) ≈ 4.4%.
- Amplitude calibration = ONE global units-gain c per draw, fit on OBSERVED channels only (quality-weighted
  median of log|H_meas| − log|H_fem|; c̄ ≈ 6.23 nat-log = ×508). A held-out channel's level is then a genuine
  prediction from FEM mode shape Q(θ) at that node + damping ζ=0.01 + c — none of which used held-out data.
- Two predictive variants: **(i) θ-only** (sharp, no magnitude discrepancy); **(ii) θ + QOI-discrepancy** —
  multiply the predicted QOI by exp(N(0,σ_QOI)), σ_QOI estimated from the OBSERVED channels' QOI residual
  scatter (peak σ≈0.98, band σ≈0.88 log-scale) and transferred to held-out. (A QOI-level log-normal discrepancy,
  NOT iid per-frequency noise — white per-bin noise then max() would spuriously inflate the peak.)

## Findings (artifact-backed; 1 split, smoke→full confirmed)
| variant | QOI | coverage (nom 0.95) | z_std (≈1 = calibrated) | interval score ↓ | CRPS ↓ | logpd ↑ | width |
|---|---|---|---|---|---|---|---|
| θ-only | peak | 0.12 | 13.7 | 4.69e3 | 139 | −690 | 3.8 dB |
| θ-only | band | 0.16 | 10.5 | 1.46e4 | 409 | −466 | 2.8 dB |
| θ+QOI-disc | peak | **0.91** | **1.03** | **1.44e3** | **114** | **−6.3** | 34 dB |
| θ+QOI-disc | band | **0.91** | **0.79** | **3.6e3** | **324** | **−7.3** | 30 dB |

1. **[GREEN finding] The frequency-calibrated twin + a marginal amplitude discrepancy gives CALIBRATED held-out-
   sensor QOI** (coverage 0.91, z_std≈1, PIT-KS 0.30), and every proper score IMPROVES vs θ-only — so the
   discrepancy is genuinely informative, not band-padding (the wide-band-doesn't-win guard holds at the QOI level).
2. **[the honest GAP] Frequency calibration ≠ magnitude calibration.** Without the amplitude discrepancy the twin
   is badly overconfident (coverage 0.12–0.16, z_std 11–14): L5 nails held-out FREQUENCIES (6/6, D11) but its
   bare magnitude predictions at unseen sensors are not trustworthy.
3. **[caveat] Calibrated but NOT sharp.** The amplitude model-form error is large (σ_QOI ≈ ×2.7; gain mis-levels
   the peak by a +0.72 log bias ≈ ×2, FEM under-predicts peak amplitude) → calibrated intervals are wide (≈×50,
   34 dB). This matches Schneider Fig 6 / §5.4 ("amplitudes not well predicted around eigenfrequencies; single
   damping ratio too limited") — calibrated coverage with eigenfrequency-localized misses, not perfection.

## Honest limits / what's next
- 1 split (seed 0); 1 hit / 1 impact (YELLOW, D2/D5); ζ fixed 0.01 (sweep deferred to the sensitivity gate);
  nearest-frequency mode matching (MAC refinement deferred, D11); the +0.72 gain mis-level bias is REPORTED, not
  silently corrected. The ≥25-split MC (next-action #5) will turn these single numbers into distributions.
- This is the **M1-style marginal discrepancy baseline**. The open question for next-action #2 (faithful Schneider
  under TMCMC): can a CORRELATED (freq×space-kriged) discrepancy be SHARPER than this marginal one while staying
  calibrated, and does the M3 orthogonal projection STARVE the discrepancy near the θ-span vs M2?
- Checker unchanged (RED, study in progress): `heldout_qoi_L5.json` is a study artifact; the checker's sharpness
  gate awaits the proper M0-vs-M3 arm comparison in `scores_summary.json` (a later deliverable). No gate regressed.
