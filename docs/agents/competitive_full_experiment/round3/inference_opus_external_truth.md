# Inference Prompt — Claude Code Opus 4.8 (infer against the INDEPENDENT external truth)

Paste into the Opus 4.8 runner. This run replaces your self-authored truth with Codex's independent
ground truth — the real test of whether your StatFEM pipeline is honest when it did NOT design the data.

```text
You are the INFERENCE runner for Agentic BayesX round 3 (Claude Code Opus 4.8), continuing in
runs/round3/opus48/. A separate agent has authored an INDEPENDENT ground truth. Your job is to infer
against it blind and report honestly — expect bias and possible non-coverage; that is the point.

CRITICAL BLINDNESS RULE:
- Consume ONLY the published observations: runs/round3/codex_truth/dataset/observations.* and
  runs/round3/codex_truth/dataset/data_contract.md (read-only).
- You MUST NOT open runs/round3/codex_truth/sealed_truth/ or Codex's generator code under
  runs/round3/codex_truth/code/ (or report/). You do not know the true parameters, the as-built
  structure, or the kind/size of the model-form error. If you peek, the experiment is invalidated.
- Read first: docs/agents/competitive_full_experiment/round3/blind_handoff_protocol.md,
  your report/decisions_log.md + master_plan.md + handoff_to_master.md, the task card, AGENTS.md, CLAUDE.md.
  Re-ground from these after any compaction before acting.

WHAT TO DO:
- Build/keep your OWN clean engineering forward model (coarse, linear, symmetric is fine — a plausible
  design model of the SAME nominal system: dome bounce ~93.5 Hz, tray ~86.25 Hz, 6 struts, single
  interface). Do NOT try to reverse-engineer Codex's structure; model it as a real engineer would from
  the nominal design.
- Inference: hierarchical StatFEM via NumPyro NUTS over the published per-build 6-DOF interface apparent
  mass (+ per-flight interface PSD / netCG). Learn the physical parameter(s) + the hierarchy (build-to-
  build sigma_build) + sensor noise sigma_e + your discrepancy term d (and its hyperparameters if you
  learn them). Single interface; axial component drives the netCG/interface-PSD QOI.
- Because the truth carries genuine model-form error OUTSIDE your model's span, a frequency-only
  discrepancy may NOT be enough (you found this in Stage 0/1: sigma_d<->sigma_e ridge). You may use your
  Stage-3 property/structure-based discrepancy here if ready; either way, REPORT what the discrepancy
  can and cannot represent.

TRUST (this is the headline — do not skip):
- HELD-OUT CALIBRATION as the primary trust test: hold out whole BUILDS and whole FREQUENCY BANDS,
  predict them, report 95% coverage + posterior-predictive checks, read coverage WITH sharpness/sigma_e
  (wide-but-covering is not success). Companions: effective-vs-nominal sample count; starve-the-data.
- Propagate FULL uncertainty into the netCG + interface-PSD QOI: parameter (epistemic) + build/flight
  (aleatory) + discrepancy d (with its uncertainty) — close the D13 gap.
- The MASTER (not you) will score your posterior against the sealed truth (bias / coverage). Your job is
  honest prediction + intervals, and an explicit statement of where you expect to be biased/under-covering.

GATES (unchanged): NUTS, >=4 chains, rank-split R-hat<1.01, bulk&tail ESS>=400 over ALL latents incl.
discrepancy coeffs + hierarchical latents, divergences<2%, non-centered. Never claim "NUTS active"
unless it passes; if it does not (e.g. the ridge returns), report that as the result. Adaptive grid
computed from the DATA peaks (you cannot use true modes); fixed during inference. runtime.json
(whole-run wall + active). Every decision -> decisions_log.md.

DELIVER (in report/): the inference + held-out calibration results, netCG/interface-PSD QOI with full-
uncertainty bands vs the test spec (narrow-band exceedance), convergence diagnostics, a
predicted-vs-observed comparison on the held-out data, known_failures (esp. expected model-form bias),
packet.md, packet.pptx, manifest.json, files_changed.md. Do NOT read the sealed truth. Then stop and
hand back to the master for scoring.
```
