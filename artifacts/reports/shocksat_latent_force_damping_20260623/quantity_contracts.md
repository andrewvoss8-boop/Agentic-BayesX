# Quantity contracts (AGENTS Quantity Contract Gate)

## Inherited (reused BYTE-IDENTICAL from the live PSD-envelope twin)
The PSD/envelope/GRMS/exceedance quantities (Q-A accelerance FRF g/lbf, Q-B response PSD = |H|²·S_F flat, Q-C
smoothline envelope, Q-D envelope GRMS, Q-E energy-weighted exceedance) are used UNCHANGED from
`../shocksat_psd_envelope_twin_20260623/quantity_contracts.md` (same `psd_forward.py`, `psd_envelope.py`, `probe.py`;
SHAs in `REUSED_code.sha256`). Layer 3 reports the same Q-D win ratio and Q-E exceedance so it is directly comparable
to the live program. S_F0 = 1 lbf²/Hz, flat and common, so it cancels in every twin-vs-FEM GRMS ratio.

## NEW — Q-Z. Modal damping ratio ζ (the time-domain decay quantity)
- **Definition:** ζ = fraction of critical viscous damping for a mode; for a free ring-down the modal coordinate
  decays as exp(−ζ·2π·f·t), so ζ = −(decay rate)/(2π·f). Units: dimensionless (reported as % of critical).
- **Coordinate/excitation/BC:** per union modal peak f (Hz); excited by a modal-hammer impact (Dytran 5850B, 416–805
  lbf), free-free (bungee). Estimated from the post-impact ring-down acceleration (g), band-passed around f.
- **Numerator/denominator:** decay rate σ = ζ·2π·f [1/s] (numerator) per 2π·f (denominator) → ζ.
- **Expected resonance/decay behavior:** a lightly-damped aerospace panel mode decays over many cycles; expected ζ in
  the 0.2–1% range (cf. NASA `.ash` modal ζ 0.25–0.44%). Heavier ζ → faster decay (shorter τ = 1/(ζ·2π·f)), and a
  WIDER half-power bandwidth Δf = 2·ζ·f in the frequency domain.
- **Reference:** NASA `.ash` modal damping (0.25–0.44%) is the independent comparator; the FEM/L5 forward currently
  assumes ζ = 1.0% structural (realfrf.ZETA_NOM) + an exponential-window ζ_w(f) baked into the windowed FRF.
- **Resolution (Discretization Gate):** the time-domain estimate deliberately dodges the frequency-bin floor. Raw
  fs = 250 kHz; records pre-triggered (impact ≈ sample 125,009 ≈ 500 ms); ring-down ≈ 500 ms; decimated to fs = 2.5 kHz
  for analysis. The half-power Δf = 2·ζ·f is SUB-BIN versus the modal-cache FFT bin df = 2.03 Hz for the light modes
  (e.g. ζ=0.4% @ 138 Hz ⇒ Δf ≈ 1.1 Hz < 2.03 Hz), which is exactly why a windowed FRF (D22, df=1.25 Hz) cannot resolve
  ζ while many cycles of time-domain decay can. The per-mode resolvability table (τ, T_fit, cycles, SNR, Δf vs df) is
  in `out/layer1_damping.json`.
- **Window-artifact note:** the time-domain decay measures the TRUE structural ζ directly (no exponential window),
  whereas the frequency-domain estimate is contaminated by the FRF's exponential-window ζ_w(f). This is a clean
  advantage of the time domain, not just a resolution difference.

## NEW — Q-Y. Latent modal MFE force g(t) and its decomposition
- **Definition:** g(t) = the extra modal force added to a nominal modal SDOF (ζ_nom = 1%) to reconcile it with the
  measured ring-down; estimated by an RTS Kalman SMOOTHER (linear-Gaussian FILTER, not a posterior over parameters).
- **Decomposition:** project g(t) on modal velocity v(t): the velocity-explained part is a viscous DAMPING correction
  (Δζ = −<g,v>/<v,v>/(2π·f)); the residual is genuine non-viscous/nonlinear MFE. Reported with a q_g robustness sweep
  and a cross-check of the recovered ζ against the independent log-decrement (corr ~0.82). The raw variance split is
  process-noise/close-mode-beating contaminated and is reported as such, not as the headline.
- **Nonlinearity diagnostics:** |corr(residual, q²)| (amplitude dependence / hysteresis, AGENTS history-dependence
  gate) and the early/late-decay ζ ratio (non-exponential decay). Both near their linear values here.
