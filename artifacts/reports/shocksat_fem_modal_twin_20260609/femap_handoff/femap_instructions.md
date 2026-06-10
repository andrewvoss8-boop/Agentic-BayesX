# FEMAP Cross-Check Instructions — ShockSat Modal Twin

Purpose: an INDEPENDENT NX Nastran solve of the same model at the same theta,
to expose any assembly/element error in our Python pipeline. You solve, we
compare mode-for-mode.

## Files
- `shocksat_modal_twin_nominal.dat` — theta = 1 everywhere (the as-delivered
  model minus `Shock_Test_Instrumentation.blk`; see decision D10 — that
  include is massless response-point spiders that double-constrain grids).
- `shocksat_modal_twin_posterior.dat` — generated after calibration by
  `python scripts/make_femap_deck.py posterior --theta-json
  femap_handoff/theta_posterior_mean.json` (appears once NUTS lands; the
  theta values are listed in the $-comment header of the deck).

## What to run
1. Import the .dat into FEMAP (File > Import > Analysis Model), NX Nastran.
2. It is a complete SOL 103 deck: EIGRL 1, -1. to 350 Hz, mass-normalized.
   PARAM K6ROT 100 is set (matches NASA's deck).
3. Solve free-free (no SPCs in the deck — that is intentional).
4. Export: the .f06 (or a CSV of mode number, frequency [Hz]) back into this
   folder as `femap_<tag>_freqs.csv`.

## What to expect (nominal deck)
- 6 rigid-body modes < ~0.1 Hz (NX exact integration may differ from our
  sub-Hz flat-facet residual — both must be far below 54 Hz).
- First elastic modes (our Python values; NX CQUAD4 should land within a few
  tenths of a % on low modes, growing to ~1-2% by 200 Hz because our QM6/MITC4
  formulation is not bit-identical to NX CQUAD4):
  54.60, 73.14, 73.74, 88.05, 104.74, 113.80, 117.35, 122.23, 124.38,
  124.59, 124.59, 125.16, 146.60, 151.90, 152.20, 160.61, 168.78, 168.87,
  183.55, 183.88, 185.18, 190.36, 191.56, 192.59, 192.90 Hz ...
- Reference anchor: NASA's own FINAL FEM paired frequencies (pptx slides
  21-45) are reproduced in `fem_assembly_report.md` section 4. Your solve of
  our deck should sit near NASA's values on the low modes (54.67, 73.09,
  73.51, 87.94, 102.23, ...): if it does and our Python values do too, the
  twin's forward model is independently confirmed.
- Total mass check in the .f06 GPWG: ~127.8 lb weight, CG z ~28.01 in.

## Known small differences (not errors)
- Deck floats are written to 6 significant figures (frequency effect < 0.01%).
- Lumped mass (PARAM COUPMASS -1) to match our assembly.
- If FEMAP complains about the unused CORD2C 4, it can be deleted; no element
  references it.

## Where results go
Drop `femap_nominal_freqs.csv` / `femap_posterior_freqs.csv` here; the
comparison script step is `python scripts/compare_femap.py` (written when the
first CSV arrives).
