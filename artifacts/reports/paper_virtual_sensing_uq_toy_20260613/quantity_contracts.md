# Quantity contracts

Defined before plotting/fitting/checking, per AGENTS.md.

## H_c(omega; theta) — channel FRF (the updated ROM response)
- Numerator/denominator: displacement (or response) per unit input; modal superposition
  H_c = gamma * sum_i Phi_{c,i} (Phi^T B)_i / (alpha_i^2 omega_i^2 + j omega beta_i^2 (2 zeta_i omega_i) - omega^2).
- Coordinate: physical sensor channel c (Ch1..Ch4).
- Excitation: fixed input distribution B, scaled by gamma.
- Boundary condition: free modal model (no extra constraint); modes fixed, parameters scaled.
- Units: complex response amplitude per unit input (arbitrary consistent units); plotted as
  log-amplitude (and dB = 20 log10|H|).
- Limiting behavior: as omega->0, H -> gamma sum_i Phi_{c,i}(Phi^T B)_i / (alpha_i^2 omega_i^2)
  (static-like); as omega->inf, |H| -> 0 like 1/omega^2.
- Resonance behavior: peak near omega ~ alpha_i omega_i (effective natural frequency),
  sharpness set by beta_i^2 zeta_i.
- Reference: paper Eqs. 4, 12.

## Masked-channel main-peak amplitude error (dB) — the paper's metric
- Definition: |20 log10|H_pred,c(omega*)| - 20 log10|H_true,c(omega*)|| at the
  measured-spectrum peak bin omega* in the search window, channel c in {Ch3,Ch4}.
- Reference: paper Eqs. 16,18; Tables 5,7,8.

## Masked-channel peak QOI
- Definition: peak |H_c| over the evaluation band on a masked channel (Ch3/Ch4).
- Truth: from the TRUE masked-channel FRF (post-hoc). Coverage = truth inside the 95%
  posterior-predictive interval (Bayes) vs point value (deterministic).

## Held-out coverage (trust test)
- Definition: fraction of true masked-channel log-amplitude FRF lines contained in the 95%
  posterior-predictive band; and whether the masked-channel peak QOI truth is covered.
- This is OUR added quantity; the paper reports only point error.

## alpha (modal stiffness scaling), beta (modal damping scaling), gamma (input coupling)
- Roles per paper Table 1: alpha = effective modal stiffness correction (alpha<1 = softening);
  beta = effective modal damping correction; gamma = effective input-coupling/transfer.
- Contract: these are EFFECTIVE ROM-level indicators within the selected model form and band,
  NOT microscopic joint contact/friction measurements (paper's own caveat, Limitations).

## FIM identifiability (E3)
- J = d log|H_c|/d theta over (channel, frequency); FIM = J^T Sigma^-1 J at the REALIZED
  discrepancy floor; report eigenvalues / how many parameter combinations clear the prior
  precision and which raw alpha/beta they mix. Distinguishes aggregate-trend identifiability
  from per-mode identifiability.
