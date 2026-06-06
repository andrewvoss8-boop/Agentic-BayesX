# Files changed — BLIND inference round (Claude Code Opus 4.8, inference runner)

All writes confined to `runs/round3/opus48/`. The prior (non-blind) round-3 packet was preserved, not
destroyed. The sealed truth / Codex generator code / Codex report were NEVER opened.

## New code (`code/`)
- `blind_model.py` — clean coarse NOMINAL forward model for the published 6-DOF interface apparent mass:
  M_base6 (rigid, from low-f asymptote) + hexapod(k_strut, 6 equal struts) + dome axial resonator(f_dome).
  JAX-differentiable; `__main__` sanity-checks vs the data's gross features.
- `blind_infer.py` — hierarchical StatFEM NUTS inference vs the PUBLISHED observations: learns k_strut +
  σ_build (hierarchy) + f_dome + σ_e + capped low-rank frequency discrepancy; adaptive grid from data peaks;
  held-out calibration (whole builds + whole band) + effective-sample-count; convergence over ALL latents.
  Env flags: R3BLIND_SMOKE, R3BLIND_COMPANIONS, R3BLIND_WARMUP, R3BLIND_DRAWS.
- `blind_qoi.py` — netCG / interface-PSD QOI with FULL uncertainty (epistemic + aleatory build/flight +
  discrepancy) vs a design-level test spec; narrow-band exceedance; vs published observed netCG.
- `blind_pptx.py` — builds report/packet.pptx (review layer).

## New report artifacts (`report/`)
- `packet.md` — BLIND packet (REPLACES the prior packet.md; prior preserved as below).
- `packet_original_mdof_netcg.md` — preserved copy of the prior (non-blind) round-3 packet.
- `packet.pptx` — 8-slide review deck (REPLACED with the blind deck).
- `blind_results.json`, `blind_qoi_results.json` — numeric results (inference, held-out, QOI).
- `blind_nuts_diagnostics.md` / `.json` — convergence over all latents (FAILS the gate; reported honestly).
- `blind_posterior.npz` — posterior draws + model constants for the QOI script.
- `blind_quantity_contracts.md`, `blind_assumptions_ledger.md`, `blind_known_failures.md` — blind docs.
- `manifest.json` — REPLACED with the blind manifest (18 artifacts + sha256).
- `figures/blind_heldout_calibration.png`, `blind_posteriors.png`, `blind_netcg_psd_vs_spec.png`,
  `blind_netcg_3grms.png`.

## Updated
- `report/decisions_log.md` — appended D21–D24 (blind decisions + the non-convergence result).
- `runtime.json` — REPLACED with the blind producing-run timing.

## NOT touched
- The immutable harness checkers; anything outside `runs/round3/opus48/`; the sealed truth and Codex code.
- Prior round-3 code (`mdof_forward.py`, `run_pipeline.py`, `statfem_*`, etc.) left intact.
