# Known Failures, Limitations & Residual Risk — Round 3 (Claude Code Opus 4.8 runner)

Honest list of what is approximate, deviating, or not done. A reviewer should be able to find the
mistakes here rather than discover them.

## 1. Inference (data layer) vs PHYSICAL prediction layer  [UPDATED — now physical prediction]
The staged synthetic data is a 2DOF abstract model with EFFECTIVE interface modal masses (dome 1.0 kg,
tray 0.6 kg). Per human direction (round-3 follow-up) the PREDICTION now deviates from this and uses
PHYSICAL masses + a re-derived physical forcing:
- **Inference** still uses the data-consistent effective-mass dynamics (MDOF reduces EXACTLY to the
  round-2 2DOF at the first mode — verified, rel L2 < 1e-9) to learn the FREQUENCIES, DAMPING, and
  build/sensor scatter (scale-independent shape information). The likelihood stays valid/converged.
- **Prediction (netCG, interface PSD, sensitivity)** uses PHYSICAL masses: dome bounce-mode effective
  interface mass ≈225 kg (0.40 × 563 kg cap), load 142 kg. Physical source:load ratio ≈1.59 — close to
  the staged abstract 1.0:0.6 ≈1.67, so the coupling SHAPE is preserved while the SCALE is physical.
- **Residual risk:** the dome bounce-mode effective mass uses a participation factor (0.40, typical
  0.3–0.5) — a 1-D-strip estimate, not a shell modal-mass calc; swept in sensitivity (netCG 0.77–1.15 g
  over particip 0.25–0.55). The inference still rests on the staged 2DOF data.

## 2. netCG forcing is now PHYSICAL (reverse-engineered)  [RESOLVED — was abstract]
Earlier the netCG inherited the staged abstract force scale (~5e-3 N²/Hz) → abstract milli-g. Per human
direction the forcing is now REVERSE-ENGINEERED with the same process as round-2's original force:
the flat ORIGINAL (+6 dB initial) force PSD is set so the DOME-ONLY interface response peaks at
**0.1 g²/Hz at the bounce mode** (orig ≈987 N²/Hz, flight −6 dB ≈248 N²/Hz). netCG is now physically
scaled (~0.9 g), and the absolute level is meaningful (still alongside the SHAPE + narrow-band
exceedance). See results.json `forcing_reverse_engineered` and figures/flight_forcing_overlay.png
(right panel = the 0.1 g²/Hz check).

## 3. netCG low-frequency limit ≠ F/m_total (grounded dome)
The idealized free-free force-limiting limit netCG→F/m_total at ω→0 assumes a free-free vehicle. Our
dome is GROUNDED (k1 to ground, matching the staged 2DOF), so there is no rigid-body mode and netCG→0
as ω→0. The apparent-mass low-freq limit M_L→m_load IS verified. This is a modeling choice inherited
from the staged data, flagged not hidden.

## 4. Dome 93.50 Hz is the global BOUNCE/BREATHING mode (CORRECTED — earlier "local mount mode" was wrong)
**Correction (human review, domain expert):** the ~110 Hz nominal (93.5 Hz as-built = 0.85×110) is the
dome's global axisymmetric **bounce / breathing mode** — the whole top shell translating/breathing
axially — which is exactly the interface-relevant mode for an apex-mounted payload. My earlier framing
("local mount-region mode", "a real dome won't land mode 1 there", "effective interface mass ≈1 kg")
was WRONG and is retracted.
- The real failure is in MY MODEL, not the physics: a 1-D meridional **beam strip underestimates the
  shell's axisymmetric hoop/membrane stiffness** that governs a breathing mode, so the raw strip mode
  is far too low (0.79 Hz at p=0; 17.18 Hz at 3.5 bar) and needs a ~30× stiffness calibration to reach
  93.5 Hz. A proper axisymmetric shell would land near ~110 Hz far more naturally.
- **Effective interface mass:** a bounce mode carries a LARGE effective mass — roughly O(150–250 kg)
  for this cap (cap mass ~500 kg × ~30–50% participation), COMPARABLE to the 142 kg load — NOT the
  1.0 kg used in the code. The 1.0 kg is the ABSTRACT round-2 value baked into the staged 2DOF data
  (see §1); the code still uses it for data-consistency, so this is now a SHARPER caveat: the physical
  source:load effective-mass ratio (~1.4) differs from the staged 1.0:0.6 (~1.67) — close, but the
  absolute source mass is wrong by ~2 orders of magnitude.
- The 1/r² interface residue decay still holds but is RE-JUSTIFIED: axial drive-point participation at
  a central apex concentrates in the axisymmetric bounce mode, while ovalling/lobar modes contribute
  ~0 axial response there — not because it is a "local" mode.
- **Open question for the human (re-run candidate):** rebuild the dome as a proper axisymmetric shell
  bounce mode with physical effective mass (~150–250 kg), which would change the coupling regime
  (source no longer "light") and the netCG coupling. Not done yet — flagged for approval (see chat).

## 5. Dome modeled as a 1-D meridional beam strip (not a shell)
The dome is a 1-D Euler-Bernoulli strip with internal-pressure geometric (tension) stiffening — not a
2-D/3-D shell. It captures pressure-stiffening trend and a multi-mode interface family but NOT shell
ovalling / circumferential modes. The recon policy permits the JAX modal path; TensorMesh continuum
was deemed unnecessary (no continuum-geometry requirement the modal path cannot meet). Residual risk:
true dome modal density/effective mass differ from a shell model.

## 6. MDOF higher modes are EXTRAPOLATION beyond the data
The staged data is 2DOF (single dome mode, single tray mode). The MDOF higher modes (dome 281/473 Hz…,
tray panel 377 Hz…) are physically motivated but NOT constrained by data. The LIKELIHOOD therefore
uses the single-mode (data-matching) reduction; the higher modes appear ONLY in the netCG/interface
PSD PREDICTIONS. They create additional narrow-band features that the spec comparison must judge.

## 7. Modal FRF likelihood uses log-MAGNITUDE (phase dropped)
Carried over from round 2. Documented deviation; phase information is discarded in the 3 modal channels.

## 8. Build-to-build fn/damping scatter is fixed-generative, not inferred
±5% @3σ (σ=1.67%) per-structure fn & damping scatter is a forward generative assumption (the 2DOF data
without replicates cannot separately identify it). It enters the PREDICTION ensembles, not the
likelihood. So σ_build (PSD-level) remains weakly identified (as in round 2).

## 9. Single equivalent interface DOF
Physically there are multiple struts; we collapse to ONE equivalent interface DOF (task-card scope).
Real multi-strut load paths and rotational interface DOF are not modeled.

## 10. One synthetic realization; no replicate tests
No test-to-test variability; results are conditional on the single staged dataset.

## Replay
One command: `PYTHONPATH=.pylibs .venv_nuts/bin/python code/run_pipeline.py` (see commands.md). Full
pipeline, no replay that skips expensive stages.
</content>
