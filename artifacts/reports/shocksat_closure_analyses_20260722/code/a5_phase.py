#!/usr/bin/env python3
"""A5 — phase-diagnostic recovery. The artifact was FOUND at recon (decisions_log D1);
this script records provenance + hash. No recomputation, no sampler."""
import hashlib
import json
import os
import time

t0 = time.time()
WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(WS, "..", "statfem_real_validation_20260617", "out", "phase_likelihood.json")
CODE = os.path.join(WS, "..", "statfem_real_validation_20260617", "code", "phase_likelihood.py")

d = json.load(open(SRC))
sha = hashlib.sha256(open(SRC, "rb").read()).hexdigest()
sha_code = hashlib.sha256(open(CODE, "rb").read()).hexdigest()

out = {
    "provenance": "found",
    "provenance_note": (
        "Located by repo search BEFORE the card's 30-min re-derivation branch was needed "
        "(search terms: circular/circ_var/phase_resid). This is the ORIGINAL artifact, not a "
        "re-derivation. Scope caveat: computed in statfem_real_validation_20260617 on the "
        "SINGLE-HIT measured dataset (46 obs channels, 12 matched modes), predating the multiref "
        "H1 caches; the negative phase conclusion is documented for that dataset."),
    "source_path": "artifacts/reports/statfem_real_validation_20260617/out/phase_likelihood.json",
    "source_code_path": "artifacts/reports/statfem_real_validation_20260617/code/phase_likelihood.py",
    "sha256": sha,
    "sha256_code": sha_code,
    "circular_variance": d["phase_circular_variance_at_modes"],
    "theta_slice_rel_contrast": {"magnitude": d["theta_slice_magnitude"]["rel_contrast"],
                                 "complex": d["theta_slice_complex"]["rel_contrast"]},
    "original_verdict": d["verdict"],
    "n_obs_channels": d["n_obs_channels"],
    "n_matched_modes": d["n_matched_modes"],
    "runtime_s": round(time.time() - t0, 2),
}
json.dump(out, open(os.path.join(WS, "out", "a5_phase_diagnostic.json"), "w"), indent=1)
print(f"A5 FOUND: circ var {out['circular_variance']:.4f}, sha {sha[:12]}..., "
      f"slice contrast mag {out['theta_slice_rel_contrast']['magnitude']:.4f} vs "
      f"complex {out['theta_slice_rel_contrast']['complex']:.6f}")
