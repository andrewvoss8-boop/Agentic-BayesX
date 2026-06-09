# Digital Twin Launch Definition

Status: **modal-only v1 active**. This packet now runs a one-parameter stiffness-scale update, but still does not claim a full FRF digital twin.

## Recommended v1
- **Forward Model:** modal surrogate built from the human Femap/Nastran flexible pair means
- **Observations:** measured modal frequencies [97.6, 278, 429, 529] Hz plus coarse digitized FRF peak features
- **Inferred Variables:** global shell stiffness scale; modal-only output discrepancy integrated as fixed covariance; FRF peak QOI uncertainty from digitization uncertainty
- **Fixed Initial Assumptions:** free-free boundary approximation; source thickness/density/geometry from Appendix A; third published FEA mode missing, not imputed
- **Held Out Validation:** mode 4 is held out from the scalar stiffness calibration; the 429 Hz feature remains an unmatched model-class warning
- **Qoi Candidates:** held-out flexible-mode frequency; peak accelerance near a selected measured mode after FRF digitization; modal amplification factor for a chosen response location
- **Discrepancy:** zero-mean output-space GP over mode index for modal-only v1; switch to log-frequency GP when FRF ordinates are available

## Why the FRF twin is still paused
- A modal-only one-parameter update is active, but a full FRF digital twin is not active yet.
- The source FEM was tuned to match the measured fundamental frequency.
- Raw FRF ordinates were not extracted; only coarse peak features are available.
