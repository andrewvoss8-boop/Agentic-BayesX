# Packet - forcing-marginalized damping toy

2026-06-12. Workspace `artifacts/reports/forcing_marginalized_damping_toy_20260612/`.

**One-command replay:** `bash run_all.sh`. **Checker:** `python3 check.py`.

## Method summary

This is a synthetic primary/secondary plumbing study for amplitude-dependent joint damping. The truth is a 3-DOF primary/secondary/hidden-rattler system. Its forcing spectrum, hidden rattler, amplitude-dependent damping law, and amplitude-dependent stiffness softening are not given to the digital twin.

The twin sees only the complex response ratio

```text
T21(f, A) = a_secondary(f, A) / a_primary(f, A)
```

Because both responses come from the same hidden input force, the force cancels. The likelihood never contains a force-function parameter.

The twin is a 2-DOF equivalent model. It infers primary stiffness scale, joint stiffness scale, a low-amplitude equivalent damping ratio, a high-amplitude equivalent damping ratio, and a residual model-error scale.

Data count: one synthetic realization, two amplitude conditions, 90 frequency lines, 67 training lines and 23 held-out lines per condition. There is no test-to-test or flight-to-flight variability in this toy.

## Results

- Forcing cancellation check: max relative error between response-derived `a2/a1` and the direct transfer ratio is **4.28e-16**.
- NUTS diagnostics: max R-hat **1.000**, min ESS **3087**, divergence fraction **0.000**.
- Damping learned: `P(zeta_high > zeta_low) = 0.996`.
- Low-amplitude physical truth `zeta = 0.0146`, equivalent-twin posterior 95% interval [0.0148, 0.0562] -> **misses** the hidden physical value.
- High-amplitude physical truth `zeta = 0.0499`, equivalent-twin posterior 95% interval [0.0532, 0.1057] -> **misses** the hidden physical value.
- Residual model-error scale: median **0.467** log/phase units, 95% interval [0.434, 0.504].
- Held-out clean log-ratio coverage: **42/46 = 0.91**.
- Damping-dependent QOI coverage: **6/6 = 1.00**.

## Figures

- `figures/fig1_forcing_cancellation.png`: hidden forcing exists, but the response ratio cancels it.
- `figures/fig2_ratio_fit.png`: posterior response-ratio bands against train and held-out points.
- `figures/fig3_damping_posterior.png`: low/high equivalent damping posterior.
- `figures/fig4_qoi_posterior.png`: held-out QOI intervals versus synthetic truth.

## Honest interpretation

GREEN claim: the toy demonstrates the plumbing for detecting an amplitude-dependent damping shift and predicting damping-sensitive, force-normalized QOIs while integrating out the forcing function.

YELLOW caveat: the equivalent damping values are biased upward relative to the hidden physical damping because the 2-DOF twin is also absorbing hidden-DOF and stiffness-softening error. The twin does **not** identify the hidden nonlinear slip law, Coulomb friction coefficient, preload, or contact state. A real rattly aerospace joint study would need amplitude sweeps, preload variation, or an explicit friction/contact model before claiming physical joint-law recovery.
