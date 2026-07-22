#!/usr/bin/env python3
"""INIT/END hashing for Task Card A (shocksat_closure_analyses_20260722).

Writes source_manifest.json at INIT (mode=init) with the SHA-256 of every frozen
input; at END (mode=verify) recomputes and fails (exit 1) on any mismatch.
Frozen inputs are read-only: nothing is copied, nothing is modified.
"""
import hashlib
import json
import os
import sys
import glob

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REPORTS = os.path.abspath(os.path.join(WS, ".."))

FROZEN = []


def add(rel):
    p = os.path.join(REPORTS, rel)
    assert os.path.isfile(p), f"MISSING frozen input: {rel}"
    FROZEN.append(rel)


# --- modal twin (A1, A2) ---
TW = "shocksat_fem_modal_twin_20260609"
for f in ["nuts_full_samples.npz", "matrices/reduced_blocks.npz",
          "measured_modes.npz", "pairing.json", "theta_full.json",
          "joint_strain_energy.json", "convergence_full.json",
          "scripts/run_nuts.py", "scripts/run_full.py"]:
    add(f"{TW}/{f}")

# --- measured H1 caches (A3, A4, A5 context): data of record ---
for p in sorted(glob.glob(os.path.join(
        REPORTS, "shocksat_netcg_method_selection_20260701/data/multiref_modal/*.npz"))):
    add(os.path.relpath(p, REPORTS))
for p in sorted(glob.glob(os.path.join(
        REPORTS, "shocksat_full_spectrum_frf_20260714/data/multiref_wide/*.npz"))):
    add(os.path.relpath(p, REPORTS))

# --- net-CG posterior + band machinery (A3) ---
NC = "shocksat_netcg_method_selection_20260701"
for f in ["out/theta_post_L5.npz", "out/heldout_drive.json",
          "out/bakeoff_scorecard.json", "out/learned_statfem.json",
          "out/data_anchored_sigma.json",
          "code/bakeoff.py", "code/netcg_qoi.py", "code/heldout_drive.py",
          "code/learned_statfem.py"]:
    add(f"{NC}/{f}")

# --- validated port (A3 cross-reference: 2.526 reference vs 2.958 tier-updated) ---
VP = "shocksat_netcg_validated_port_20260716"
for p in sorted(glob.glob(os.path.join(REPORTS, VP, "out/*.json"))):
    add(os.path.relpath(p, REPORTS))

# --- whole-FRF study (A4): iid-likelihood source + retained per-chain draws ---
FS = "shocksat_full_spectrum_frf_20260714"
for f in ["code/arm_b_nuts.py", "code/wide_package.py", "code/wide_forward.py",
          "out/nuts_diagnostics.json"]:
    add(f"{FS}/{f}")
for p in sorted(glob.glob(os.path.join(REPORTS, FS, "out/armB/theta_only_*.npz"))):
    add(os.path.relpath(p, REPORTS))

# --- phase diagnostic (A5): FOUND artifact ---
add("statfem_real_validation_20260617/out/phase_likelihood.json")
add("statfem_real_validation_20260617/code/phase_likelihood.py")

# --- A3 transitive code/data dependencies (frozen predecessors, read-only) ---
PE = "shocksat_psd_envelope_twin_20260623"
for f in ["code/realfrf.py", "code/shape_borrow_diag.py", "code/modal_feature.py",
          "data/reduced_blocks.npz", "data/obs_dofs.npy", "data/keep_dofs.npy",
          "data/channel_map.csv", "data/measured_modes.npz"]:
    add(f"{PE}/{f}")
add("statfem_shocksat_eval_20260616/data/V_keep.npy")
add("shocksat_fem_modal_twin_20260609/fem_model.npz")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def main(mode):
    manifest_path = os.path.join(WS, "source_manifest.json")
    entries = {rel: sha256(os.path.join(REPORTS, rel)) for rel in FROZEN}
    if mode == "init":
        json.dump({"created": "2026-07-22", "n_files": len(entries),
                   "sha256": entries}, open(manifest_path, "w"), indent=1)
        print(f"INIT: hashed {len(entries)} frozen inputs -> source_manifest.json")
        return 0
    ref = json.load(open(manifest_path))["sha256"]
    bad = [r for r in ref if entries.get(r) != ref[r]]
    missing_new = [r for r in entries if r not in ref]
    out = {"mode": "verify", "n_checked": len(ref), "mismatch": bad,
           "not_in_manifest": missing_new, "ok": not bad}
    json.dump(out, open(os.path.join(WS, "out", "end_hash_verify.json"), "w"),
              indent=1)
    print(f"VERIFY: {len(ref)} files, mismatches={bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "init"))
