# Quantity contracts (define BEFORE plotting/fitting/checking — AGENTS Quantity Contract Gate)

## Q-A. Accelerance FRF  H_{s,d}(f)
- Numerator/denominator: response acceleration (g) / drive force (lbf) ⇒ units g/lbf.
- Coordinate: response = sensor s on its measured axis (channel_map); drive = node 990 or 900 on its axis (D5).
- Excitation: modal-hammer impact (instrumented force, Dytran 5850B); FRF = H1 = S_yf/S_ff, multi-hit ensemble.
- Boundary condition: free-free (bungee-suspended modal test).
- Limiting behavior: |H|→ small/flat off-resonance; deep antiresonances between modes (clean data shows ~40 dB range).
- Resonance behavior: peaks at modal frequencies, height ∝ φ_s(k)·φ_d(k)/(2ζ_k λ_k) (modal superposition).
- Reference: standard EMA accelerance; measured here in g/lbf directly (samples already in g & lbf, D2).

## Q-B. Response PSD  S_aa,s(f)  [the QOI base]
- Definition: S_aa,s(f) = |H_{s,d}(f)|² · S_F(f); S_F = FLAT input force PSD, S_F0 = 1 lbf²/Hz, IDENTICAL for FEM
  and twin (Q1). ⇒ S_aa = |H|² g²/Hz numerically (per unit flat force PSD).
- Units: g²/Hz. Coordinate/excitation/BC: as Q-A, per (sensor s, drive d).
- Limiting/resonance: |H|² ⇒ peaks sharper (²), antiresonances deeper; GRMS dominated by the few tallest modal peaks.
- Note: because S_F is flat & common, S_F0 cancels in every twin-vs-FEM RATIO; absolute level carried by the chosen
  S_F0 (documented, not fit). This is a *predicted response environment shape*, NOT a measured random-vibe PSD
  (ShockSat has no stationary random data — D2 / exploration).

## Q-C. Smoothline envelope  E[S](f)
- Definition: peak-pick local maxima of S (log10 S vs log10 f) above a fixed prominence; connect peak tops with
  straight segments in (log f, dB) ⇒ piecewise-linear E(f) ≥ S at the peaks. IDENTICAL algorithm for both curves (Q2).
- Inputs: (a) FEM PSD then +6 dB [+6 dB in PSD = ×3.98 in g²/Hz = ×2 in GRMS]; (b) twin 97.5th-pct predictive PSD.
- Units g²/Hz. Behavior: upper envelope; does not dip into antiresonances. Reference: MPE / qualification-spec
  drawing practice (straight-line log-log envelope over CLA/FEM peaks). Resolution: native FRF grid df ≈ 2.03 Hz.

## Q-D. GRMS of an envelope
- Definition: GRMS = sqrt( ∫_band E(f) df ), band = 45–260 Hz. Units g (with S_F0 = 1 lbf²/Hz).
- Lower GRMS = less conservative test level. WIN metric = GRMS(twin 97.5 env) / GRMS(FEM+6 dB env) < 1.

## Q-E. Exceedance (the coverage report, Q3)
- Definition: exc(f) = 10·log10( S_data(f) / E_twin(f) ) where positive (measured data above the twin envelope), dB.
- Energy weighting: report max exc (dB) AND the fraction of band GRMS² carried by the exceeding frequencies
  (∫_{exc>0} S_data df / ∫ S_data df). A large exc at a low-S_data frequency is flagged low-significance.
- Also report the SAME exceedance for the FEM+6 dB envelope (so we know where FEM+6 dB itself fails to envelope).

## Verdict (per held-out sensor × drive, then aggregated by training fraction)
- GREEN local win: GRMS ratio < 1 AND twin envelope has no energy-significant exceedance (e.g. exceeding-energy
  fraction < a small threshold to be fixed in check.py).
- YELLOW: covers but GRMS ratio ≥ 1 (no conservatism gain), or wins GRMS but with a documented small exceedance.
- RED (integrity): fabricated/again-stronger-than-numbers claim, peak-tuned gain, non-identical envelope algorithm,
  or a GRMS win claimed where the twin fails to envelope energy-significantly.
