# Stage-3 Inference — Claude Code Opus 4.8 (the fix the blind failure pointed to)

Paste into the Opus 4.8 runner. Stage 0/1 (frequency-only discrepancy) failed honestly against the
independent truth: bias, under-coverage, and a sigma_d<->sigma_e ridge that broke convergence because a
symmetric, one-equal-strut, frequency-only model cannot represent the truth's spatial symmetry-breaking.
Stage 3 builds the fix and tests it on the SAME blind truth.

```text
You are the INFERENCE runner for Agentic BayesX round 3, STAGE 3 (Claude Code Opus 4.8), continuing in
runs/round3/opus48/. Build the structure-aware fix and infer BLIND against the re-published independent
truth. Expect this to either RESTORE honest calibration or fail informatively again.

BLINDNESS RULE (unchanged): consume ONLY runs/round3/codex_truth/dataset/ (observations.npz +
data_contract.md, read-only). MUST NOT open runs/round3/codex_truth/sealed_truth/, /code/, or /report/.
The master scores you against the sealed truth.

READ FIRST: docs/agents/competitive_full_experiment/round3/netcg_quantity_contract.md (CANONICAL netCG
- adopt it exactly), blind_handoff_protocol.md, your report/blind_known_failures.md + decisions_log.md +
master_plan.md + handoff_to_master.md, the independent review
artifacts/reports/blind_round3_review_20260604/review.md (what failed and why), AGENTS.md, CLAUDE.md.
Re-ground from these after any compaction.

BUILD THE FIX (three coupled changes the failure pointed to):
1. ASYMMETRIC / PER-DOF, PER-STRUT FORWARD MODEL: stop using one equal-strut k that cannot fit lateral,
   axial, and rocking modes at once. Allow per-strut and/or per-DOF interface stiffnesses so the model
   CAN represent x!=y, rx!=ry mode splits and the per-DOF stiffness mismatch. Keep it differentiable.
2. STRUCTURE / PROPERTY-BASED DISCREPANCY (the novel piece, D12): a discrepancy whose correlation lives
   in ELEMENT/STRUT FEATURE space (per-strut; same-property high corr, same element-type moderate, far
   low; optional stiffness-magnitude term), applied in PARAMETER space (perturbing element/strut
   properties) and propagated through the model — NOT a frequency-only output GP. It must be able to
   represent the SPATIAL (azimuthal) error the frequency-only kernel could not.
3. COMPLEX (MAGNITUDE + PHASE) LIKELIHOOD on the interface apparent mass: use the published complex
   apparent_mass_real/imag (all 6 diagonal DOFs), not log-magnitude only, so phase / antiresonance
   information constrains the fit.

netCG QOI: compute per netcg_quantity_contract.md (F_iface from DYNAMIC FBS coupling / m_load; FORBIDDEN:
rigid mass-ratio constant transmission, and drive-point accelerance F/M_zz). Show the f->0 rigid limit +
resonant amplification.

INFERENCE: hierarchical NumPyro NUTS learning the per-DOF/per-strut stiffness + the structure-based
discrepancy (+ its hyperparameters) + sigma_build + sigma_e. Guard parameter<->discrepancy
identifiability (informative priors; report sigma_d/sigma_e separately and whether the ridge is gone).
Adaptive grid from data peaks, fixed during inference.

GATES + HEADLINE TESTS (report all, honestly):
- Convergence over ALL latents incl. discrepancy coeffs + per-build/per-strut latents: rank-split
  R-hat<1.01, bulk&tail ESS>=400, divergences<2%, >=4 chains, non-centered. THE headline: does the
  structure-based discrepancy RESTORE convergence (resolve the sigma_d<->sigma_e ridge)? Do NOT cap
  sigma_d to fake it; if you constrain anything, say why.
- Does it (i) stop sigma_e inflation, (ii) CATCH the spatial error (with vs without the structure-based
  discrepancy comparison), (iii) reduce the f_dome / netCG bias, (iv) move HELD-OUT coverage toward ~0.95
  with SHARPER bands (read coverage WITH width; wide-but-covering is not success)?
- RUN THE COMPANION TRUST STUDIES that were skipped last run: without-discrepancy, starve-the-data,
  effective-vs-nominal sample count, grid-invariance.
- HELD-OUT CALIBRATION as the primary trust test (hold out whole builds AND frequency bands).
- Full-uncertainty netCG + interface-PSD QOI: propagate parameter (epistemic) + build/flight (aleatory) +
  discrepancy d (with uncertainty) — close the D13 gap.

DELIVER (report/): the Stage-3 inference + with/without comparison + companion studies + held-out
calibration + full-uncertainty QOI vs spec (narrow-band exceedance), convergence diagnostics, packet.md,
packet.pptx, manifest.json, files_changed.md, runtime.json (whole-run wall + active), decisions_log.md.
Never claim "NUTS active" unless the gate passes over all latents; if it still fails, report that as the
result (it is still informative). Do NOT read the sealed truth. Then hand back to the master for scoring.
```
