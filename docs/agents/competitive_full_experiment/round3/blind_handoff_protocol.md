# Blind Truth/Inference Handoff Protocol (round 3) — master-owned

Purpose: make the ground-truth model genuinely INDEPENDENT of the inference model, so model-form error
is real (not a draw from the inference's own discrepancy) and recovery is not a tautology.

Roles
- Codex = TRUTH-AUTHOR. Workspace `runs/round3/codex_truth/`. Authors a richer "as-built reality"
  model, emits OBSERVATIONS for the inference, and SEALS everything else. Must NOT read Opus's
  inference code or discrepancy parameterization (`runs/round3/opus48/code/`).
- Opus = INFERENCE. Workspace `runs/round3/opus48/`. Consumes ONLY Codex's published observations +
  the data contract; builds its own clean engineering forward model + StatFEM discrepancy + NUTS.
  Must NOT read `runs/round3/codex_truth/sealed_truth/` or Codex's generator code.
- Master (human + Claude lead) = broker. Holds the reveal; scores bias / 95% coverage / held-out
  calibration against the sealed truth AFTER inference. Neither agent scores itself against truth.

Folder split (instruction-enforced isolation; no chmod)
- `runs/round3/codex_truth/dataset/`      <- PUBLISHED to the inference (observations + data_contract.md).
- `runs/round3/codex_truth/sealed_truth/` <- HIDDEN from the inference (true params, as-built structures,
  generator code, model-form-error description, scoring key).
- `runs/round3/codex_truth/report/`       <- Codex's own validation/figures/mesh (no truth-param leakage
  into anything under dataset/).

Shared, NON-secret design assumptions (both sides may use; these are the nominal engineering model,
NOT the hidden truth)
- Source = pressurized spin-formed Al dome; nominal interface mode 1 ~ 93.5 Hz (global bounce/breathing,
  large effective interface mass). Load = isogrid tray + ~136 kg avionics on 6 struts to clevises,
  RBE'd to ONE interface node; nominal axial mount mode ~ 86.25 Hz. Single interface DOF couples them.
- Flight forcing model is SHARED/known: mean = -6 dB pre-data design envelope (2x GRMS), Matern flight
  GP, fixed 3 dB flight-to-flight. Build-to-build and sensor noise EXIST in the data; their true scales
  are SEALED (the inference learns them).
- PSD-space dB (factor = 10**(dB/10)); SI units; state coordinate frame + DOF order.

What is HIDDEN (sealed): the as-built structure of each build, all true parameter values, the KIND and
size of every model-form imperfection, the true sigma_build / sigma_sensor / damping, and the scoring key.

Reveal: only after Opus's inference + held-out calibration are committed does the master open
`sealed_truth/` and score. This ordering is the experiment.
