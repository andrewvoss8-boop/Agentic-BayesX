# quantity_contracts.md — Confidently-Wrong Model-Form-Error experiment

State numerator/denominator/coordinate/excitation/BC/units/limits/reference BEFORE plotting or checking.

## Q1 — FRF channel amplitude |H_c(ω;θ)|
- Numerator: channel-c response (mass-normalized modal output). Denominator: input coupling γ·Binput (force-like).
- Coordinate: channel index c∈{1..4}; Ch1/Ch2 observed, Ch3/Ch4 masked/held-out.
- Excitation: fixed input distribution Binput=[1,0.6,0.3,0.2] through γ. BC: fixed via the modal model (Φ,f,ζ).
- Units: the likelihood is on **log-amplitude** ln|H| (dimensionless log of the response/force ratio). Plots use
  linear magnitude on a log-frequency axis (project rule), or log|H| where the likelihood space is the point.
- Limiting behavior: away from resonances |H|→ quasi-static modal sum; at each f_i a peak whose height ∝ 1/(2ζ_i).
- Reference: Yan et al. (2026) Eqs 4,11,12,21 (their log-magnitude / dB metric). Scaffold `core.frf_np`.

## Q2 — Injected model-form-error scale δ (the sweep variable)
- Definition: the high-frequency standard deviation (in log-amplitude units) of the injected
  `correlated_logfield` multiplicative discrepancy on the truth; low-freq std = δ/6; correlation length 0.25 in
  ln(f). δ=0 ⇒ truth is exactly modal (no model-form error) = the control.
- Units: dimensionless log-amplitude std. Reference: this study (synthetic injected truth).

## Q3 — Learned discrepancy scale σ_d (the thermometer)
- Definition: posterior of the model-discrepancy std the method learns (HalfNormal(0.3) prior). A1: fixed 0.
- Contract: σ_d should be ~0 at δ=0 and rise monotonically with δ (a thermometer for unmodeled physics). It is an
  EFFECTIVE output-side scale, not the literal injected field; we compare its trend/level to δ, not claim equality.
- Units: dimensionless log-amplitude std. Reference: Hao & Bilionis (2024) Fig 5 analog (their learned β).

## Q4 — Held-out predictive coverage (the money quantity)
- Numerator: number of held-out (masked) frequency lines where the TRUTH (or the held-out noisy observation)
  falls inside the posterior predictive 95% band. Denominator: number of held-out lines (masked channels × freq).
- Coordinate: masked channels Ch3/Ch4 over 10–900 Hz band. Excitation/BC: as Q1.
- Units: fraction (0–1). Nominal target 0.95. Two flavors reported: (i) predictive coverage of the held-out
  NOISY observation (headline); (ii) clean-truth-line coverage.
- Expected behavior: A1 (naive) coverage collapses below nominal as δ grows (the malady); A2/A3 stay near nominal.
- Reference: Alberts & Bilionis (2023); Hao & Bilionis (2024) Fig 4 analog (held-out / out-of-sample test).

## Q5 — Held-out peak-amplitude QOI
- Numerator: max |H_c| over the 10–900 Hz band on a masked channel (`core.peak_qoi`). Denominator: as Q1.
- Coordinate: per masked channel. Units: linear amplitude (same as |H|). Covered flag = truth peak inside the
  posterior predictive 95% QOI interval.
- Expected resonance behavior: the QOI is the response at the dominant held-out resonance.
- Reference: the paper's main-peak dB metric (Eq 21) on held-out channels.

## Q6 — Per-mode stiffness scaling α_i posterior (confidently-wrong vs honest)
- Definition: posterior 95% interval of α_i (the i-th mode's stiffness scaling; f_i,eff = α_i f_i). Truth-covered
  flag against α_true.
- Contract: A1 expected TIGHT + biased (confidently wrong, especially for the mode the discrepancy distorts);
  A2/A3 WIDEN and stay honest. A peak shift ≡ a stiffness scaling (α_i² multiplies ω_i² in the denominator), which
  is exactly why the coherent-bias limit (E-LIMIT) confounds α with the masked peak.
- Units: dimensionless. Reference: Hao & Bilionis (2024) Fig 4 analog.

## Q7 — Identifiability: modal participation / FIM eigen-view (E-LIMIT)
- Modal participation per channel: part_i = (Φᵀ Binput)_i and the channel weight Φ_{c,i}·part_i links each α_i to
  the observed vs masked channels (the strain-energy/sensitivity analog for this modal-ROM).
- FIM eigen-view: J = ∂(log|H|_observed)/∂θ at the realized discrepancy floor; eigen-decomposition of JᵀΣ⁻¹J shows
  the peak-shift↔α (stiffness) degeneracy for the local mode seen only by the masked sensor.
- Reference: AGENTS.md Modal/Eigenproblem Identifiability Gate.
