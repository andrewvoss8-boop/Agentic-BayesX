# Lead Code Review — pairing.py / run_nuts.py / make_lock.py / sensitivity.py / check.py

Reviewer: Claude Code lead session (decision D19 division of labor).
Status: APPROVED with noted caveats. Nothing blocking found.

## pairing.py — APPROVED
- Global one-to-one Hungarian assignment maximizing MAC with a frequency gate
  (|df|/f > 18% forbidden) fixes the two real pathologies of the earlier
  greedy pairing (partner collisions; spatial aliasing of high model modes
  onto low test modes). Calibration gate MAC >= 0.5 AND |df| <= 12% yields 18
  clean modes — consistent with NASA's own ">150 Hz struggles" statement.
- Nit (non-blocking): forbidden-pair fallback assignments are correctly
  excluded from calibration via `calib_ok`.

## run_nuts.py (canonical, parallel-session version) — APPROVED
- Correct NUTS setup: 4 chains, LogNormal(0, 0.25) theta prior, HalfNormal
  noise scales, x64 asserted, `extra_fields=("diverging",)`, all-variable
  R-hat/ESS via numpyro summary, gate thresholds match AGENTS.md.
- Mode tracking by overlap with nominal eigenvectors with `stop_gradient` on
  the argmax index: gradients flow through eigenpairs, not the assignment.
  Documented as the non-differentiable-pairing handling (NUTS rule). The
  `track_unique` flag in predictions records pairing-switch occurrences.
- CAVEAT for the packet (must be stated): the PRIMARY likelihood is
  frequency-only; MAC enters via (a) the pairing definition and (b) the
  `--mac` pseudo-likelihood sensitivity arm. The task card asked for
  frequencies + shapes/MAC in the likelihood; the deviation is justified
  (eigenvector gradients are ill-conditioned at the near-degenerate
  122–125 Hz cluster -> divergence risk) but it is a deviation and the MAC
  arm result must be shown next to the primary result.
- Runtime risk (non-blocking): LOMO = 18 sequential NUTS runs; if wall time
  explodes, trimming draws for LOMO arms is acceptable IF the convergence
  gate values are still reported per-run.

## make_lock.py — APPROVED with caveat
- The structural guarantee (held-out modes never enter the likelihood) is the
  real protection; the SHA256 of prediction fields prevents retro-fitting
  after grading. CAVEAT: in a single pipeline the actuals were readable
  before the lock; this is procedural honesty, not a blind vault. The packet
  should say so plainly (same limitation as any self-run held-out protocol).

## sensitivity.py — APPROVED
- Arms cover the H-priority ledger items: prior width (A8), MAC likelihood
  on/off (A10), held-in band edge (A12). Reduced draws are labeled as scan
  quality, not headline.

## check.py — APPROVED
- Gates are value-backed (recomputed/read), not existence-backed; failed
  convergence reports as FAIL. Includes the no-FRF-likelihood gate and
  inputs-hash equality.

## Process notes
- D16 integrity flag resolved by D19: the unaccounted `run_nuts.py` draft was
  written by this lead session; no third-party code entered the workspace.
- Two-writer coordination is logged in D18/D19; claims go through
  decisions_log.md before acting.
