# Decisions log — shocksat_closure_analyses_20260722 (Task Card A)

## D0 — 2026-07-22 controlling decisions inherited
Andrew's 2026-07-22 adjudication (notes/memory.md) and predecessor decisions D1–D6 of
`shocksat_results_summary_20260721/decisions_log.md` control scope: five analyses on frozen artifacts,
no new physics, no model-form work, hard cap 4 h active. NUTS only for A2.

## D1 — 2026-07-22 A5 resolved at recon: artifact FOUND, no re-derivation
Repo search located the phase diagnostic BEFORE FREEZE:
`statfem_real_validation_20260617/out/phase_likelihood.json` — circular variance 0.8536364 ("~0.854"),
θ-slice rel-contrast complex 0.000127 vs magnitude 0.009355 ("no sharper slice than magnitude").
Context: single-hit phase, 46 channels, 12 matched modes (that study's L4 diagnostic). Deliverable is
provenance + hash; the card's 30-min re-derivation branch is not needed. Note the found diagnostic is
from the single-hit dataset (statfem_real_validation), not the later multiref H1 caches; the packet
will state this scope explicitly.

## D2 — 2026-07-22 A4 source pinned to armB theta-only
"The iid log-magnitude whole-FRF likelihood that failed" = `arm_b_nuts.py --theta-only` in
`shocksat_full_spectrum_frf_20260714` (GP error term dropped ⇒ iid residual), the variant whose NUTS
runs are recorded non_converged_multimodal with R-hat 44.7–75.0 and per-chain draws RETAINED in
`out/armB/theta_only_*.npz`. The GP-correlated variant also failed but is not the card's target.
Chain-location annotation will use those retained draws (no fabrication needed).

## D3 — 2026-07-22 A3 reproduction strategy: import frozen modules read-only
`bakeoff.py`/`heldout_drive.py` depend transitively on `shocksat_psd_envelope_twin_20260623/code`
(realfrf, modal_feature, shape_borrow_diag) and its data + `statfem_shocksat_eval_20260616/data/V_keep.npy`
+ `shocksat_fem_modal_twin_20260609/fem_model.npz`. All added to source_manifest.json (57 files).
Reproduction imports those modules with sys.path pointing at the frozen workspaces and writes ONLY to
this workspace; the cached `theta_post_L5.npz` is loaded (no NUTS rerun for A3). Nothing in any
predecessor workspace is written, moved, or copied.

## D4 — 2026-07-22 scoring conventions fixed pre-science
CRPS ensemble estimator (fair form), energy weighting identical to stored weighted_coverage, FEM+6 dB
envelope conventions (primary log-uniform; sensitivities linear-uniform and Gaussian-95%) — all in
`quantity_contracts.md` C3 before any A3 number was computed.

## D5 — 2026-07-22 A1 block length corrected pre-run (ledger N1)
Stored `convergence_full.json` shows min ESS 232 (not ~1900 as first drafted): worst-variable
autocorrelation time τ̂ ≈ 4000/232 ≈ 17 draws. Block length set to 40 (≈2×τ̂), circular blocks WITHIN
each 1000-draw chain segment. Corrected BEFORE any A1 number was computed.

## D6 — 2026-07-22 checker display note (no gate change)
The SHA-locked checker's a2_reference GREEN message juxtaposes theta max|dev| (0.0066, group
`contact`) with the MINIMUM per-parameter tolerance (0.0060, group `bottom_box`). The pass rule
itself is per-parameter (a2_sweep.py N4) and all 9 groups pass individually (verified: contact dev
0.0066 vs tol 0.0437; bottom_box dev 0.0011 vs tol 0.0060). Checker not modified (immutable);
disclosed here and in the packet.
