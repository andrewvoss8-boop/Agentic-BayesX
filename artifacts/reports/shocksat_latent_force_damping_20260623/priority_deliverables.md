# Priority deliverables — ShockSat time-domain latent-force damping/residual diagnostic

Restating the runner prompt's PRIORITY asks in my words, with where each is delivered (AGENTS Priority-Deliverables Gate).

| # | Priority ask | Interpretation | Delivered in | Status |
|---|---|---|---|---|
| P0 | Reproduce D22's headline (0/9 identified) as the integrity baseline before claiming any improvement | Run the inherited frequency-domain damping inference on the Test07 windowed FRF | `out/d22_reproduction.json` (n_identified=0), `code/cache_builder.py` provenance | DONE (0/9) |
| P1 | **Layer 1 (headline):** does a time-domain decay estimate resolve per-mode ζ that D22 could not? | Band-pass + analytic-signal log-decrement on the clean ring-downs + a NUTS posterior over ζ; compare to D22 0/9, .ash 0.25–0.44%, FEM nominal 1% | `code/decay_core.py`, `code/layer1_damping.py` (14/16 resolved), `code/layer1_nuts.py` (14/16 converged), `figures/fig1,fig2,fig3` | DONE — GREEN |
| P1b | Damping-resolvability gate (τ, T, cycles, SNR, half-power Δf vs FFT df) + finite-perturbation | per-mode resolvability table; `code/finite_perturbation.py` shows ζ moves the QOI but cancels in the win ratio | `out/layer1_damping.json` resolvability, `out/finite_perturbation.json`, `figures/fig1` | DONE |
| P1c | Frequency-domain control on the CLEAN data (isolate domain vs data quality) | D22-style width fit on the clean modal caches (df=2.03 Hz) | `code/freq_control.py` (7/16), `figures/fig3` | DONE |
| P2 | **Layer 2:** estimate a low-dim latent MFE force; decompose damping-correction vs genuine residual | per-mode modal SDOF + random-walk latent force, RTS Kalman SMOOTHER (filter, NOT NUTS); velocity-projection vs residual + nonlinearity diagnostics | `code/layer2_gplfm.py`, `out/layer2_gplfm.json`, `figures/fig4` | DONE (caveated) |
| P3 | **Layer 3 (hard bar):** does a measured-ζ-corrected twin lower the held-out 97.5% PSD-envelope GRMS vs FEM+6 dB while enveloping? | Reuse the inherited PSD-envelope QOI byte-identical; 90% split; three damping framings; held-out GRMS ratio + energy-weighted exceedance | `code/layer3_value.py`, `out/layer3_value_seed00.json`, `figures/fig5` | DONE — HONEST NEGATIVE |
| P4 | Workspace + governance + one-command replay + immutable SHA-locked checker | this workspace | `run_all.sh`, `check.py`, `REUSED_code.sha256`, `runtime.json`, `packet.md` | DONE |

Acceptance / honesty:
- The headline (P1) is a GREEN methodological finding: the time domain resolves ζ where the single windowed FRF could
  not, with a converged NUTS posterior and a passed resolvability table.
- P3 is an HONEST NEGATIVE (a valid outcome per the prompt): damping is a strong ABSOLUTE lever on envelope GRMS but
  CANCELS in the twin/FEM+6 dB win ratio (common-mode, mirrors D8), and the as-built FEM is OVER-damped (1% > measured
  ~0.4%), so a measured-ζ correction makes the twin MORE conservative, not less. The prompt's assumed "under-damped FEM"
  bridge direction is SIGN-FLIPPED here; this is surfaced, not hidden.
- No "replace the FEM" or metric-improvement claim is made beyond what the checker confirms.
