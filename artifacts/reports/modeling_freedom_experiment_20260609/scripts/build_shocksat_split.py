#!/usr/bin/env python3
"""
ShockSat split for the modeling-freedom experiment.

Real NASA/NESC ShockSat data already lives (read-only) in the sibling run
artifacts/reports/shocksat_statfem_runner_20260609/extracted/. We do NOT copy GBs and we do
NOT mutate that folder. Instead we:
  - declare which real files are TRAIN/DEV (read-only inputs for the runner), with SHA256;
  - declare the HELD-OUT regime (pyro NSD) with SHA256, enforced by AUDIT (the checker greps
    the runner's code/logs for the held-out path) + hash-pin (cannot be swapped), since the
    file legitimately remains on disk for the other run and is re-fetchable NASA data.

This is the honest ShockSat holdout: audit-enforced + hash-pinned, NOT physical deletion.
The airtight physical holdout is the SYNTHETIC substrate (vault/tray -> Google Drive + delete).
"""
import hashlib, json, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(HERE))  # repo .../artifacts/reports -> repo root
SS = os.path.join("artifacts", "reports", "shocksat_statfem_runner_20260609", "extracted")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(p):
    return os.path.join(SS, p)


# OBSERVATION LAYER = modal correlation (MAC + frequency) on the consistent 1101-7105 grids.
# Per the parked ShockSat-Opus normalization finding: SOL111 FRF vs Test07 taps are DIFFERENT
# transfer paths, so a magnitude FEM-vs-test FRF overlay is NOT valid. SOL111 FRF is therefore a
# frequency-alignment DIAGNOSTIC ONLY, never a metric/likelihood input.
# Dev is NOT a separate file: dev = leave-one-mode-out cross-validation within the modal set.
TRAIN_DEV = [
    dict(role="train_dev_modal", kind="test_modes_free_free",
         path=rel("FEM/Correlation/Modal_Test_Data_Use_in_Correlation2021/FINAL_FF/TAM_FF/Modes.pch"),
         note="Free-free modal mode shapes on the 1101-7105 grid set (the correlation layer)."),
    dict(role="train_dev_modal", kind="tam_free_free",
         path=rel("FEM/Correlation/Modal_Test_Data_Use_in_Correlation2021/FINAL_FF/TAM_FF/TAM.pch"),
         note="Test-Analysis Model (reduced FEM) for the free-free MAC correlation."),
    dict(role="train_dev_modal", kind="modes_fixed_base",
         path=rel("FEM/Correlation/Modal_Test_Data_Use_in_Correlation2021/FINAL_fixed_base/TAM_FB/Modes.pch"),
         note="Fixed-base modal set (available as additional modal content / alt boundary condition)."),
    dict(role="train_dev_modal", kind="tam_fixed_base",
         path=rel("FEM/Correlation/Modal_Test_Data_Use_in_Correlation2021/FINAL_fixed_base/TAM_FB/TAM.pch"),
         note="Fixed-base Test-Analysis Model."),
    dict(role="train_supplementary", kind="impact_hammer_hit",
         path=rel("Test07_ImpactHammer_990x/Test07_impacthammer_990x_001_5_20_2021_2_32_37 PM.mat"),
         note="Measured modal hammer hit (force ch116 -> accel), 10-400 Hz; frequency content."),
]

# SOL111 FRF: DIAGNOSTIC ONLY (frequency alignment), excluded from the metric by the contract.
DIAGNOSTIC_ONLY = [
    dict(kind="fem_frf_sol111_x",
         path=rel("FEM/Correlation/FRF_Verification/SOL_111_Free_Free_Force_11101X.pch")),
    dict(kind="fem_frf_sol111_y",
         path=rel("FEM/Correlation/FRF_Verification/SOL_111_Free_Free_Force_11110Y.pch")),
]
DEV_SCHEME = "leave-one-mode-out cross-validation within the free-free modal set"

_PYRO = "Pyro_NSI_NSD/NSD1_Test/Pyro_NSD_990x001_10_13_2021_2_20_42 PM.mat"
HELD_OUT = dict(
    regime="pyro_shock_NSD", band_hz=[100, 10000], forcing="unknown (pyrotechnic source)",
    qoi="force-limiting load metric / peak shock response (defined in contract.md)",
    path=rel(_PYRO),
    staged_vault_copy="vault/shocksat/Pyro_NSD_990x001_HELDOUT.mat",
    holdout_mechanism="PHYSICAL (airtight, same as synthetic): staged to vault, uploaded to "
                      "Google Drive, then DELETED from local disk including the parked sibling "
                      "run, until grading. SHA256 pinned; re-download + verify at grading.",
    runner_rule="runner must never read this regime; checker also greps for the path "
                "(defense-in-depth even though the file is physically removed).",
    restoration={"original_path": rel(_PYRO),
                 "refetch": "NASA/NESC ShockSat public release (re-fetchable)",
                 "note": "after the experiment, restore to original_path and verify SHA256; "
                         "this re-enables the parked sibling run's pyro replay."},
    note="Out-of-distribution regime: unknown forcing + load QOI live here, not in the modal "
         "band. Grading this regime tests EXTRAPOLATION from the modal-band fit.",
)


def main():
    def stamp(d):
        d["sha256"] = sha256(d["path"]) if os.path.exists(d["path"]) else "MISSING"
        d["bytes"] = os.path.getsize(d["path"]) if os.path.exists(d["path"]) else 0
    for d in TRAIN_DEV:
        stamp(d)
    for d in DIAGNOSTIC_ONLY:
        stamp(d)
    stamp(HELD_OUT)

    inputs_dir = os.path.join(HERE, "runner_opus", "inputs", "shocksat")
    vault_dir = os.path.join(HERE, "vault", "shocksat")
    os.makedirs(inputs_dir, exist_ok=True)
    os.makedirs(vault_dir, exist_ok=True)

    with open(os.path.join(inputs_dir, "inputs_manifest.json"), "w") as fh:
        json.dump(dict(substrate="shocksat_real",
                       observation_layer="modal correlation (MAC + frequency) on 1101-7105 grids",
                       dev_scheme=DEV_SCHEME,
                       access="read-only (do not copy, do not edit)",
                       train_dev=TRAIN_DEV,
                       diagnostic_only=DIAGNOSTIC_ONLY,
                       diagnostic_note="SOL111 FRF: frequency-alignment diagnostic ONLY; NOT a "
                                       "magnitude likelihood (transfer-path mismatch, per "
                                       "ShockSat-Opus normalization finding)."), fh, indent=2)
    with open(os.path.join(vault_dir, "held_out_manifest.json"), "w") as fh:
        json.dump(dict(substrate="shocksat_real", held_out=HELD_OUT), fh, indent=2)

    print("[shocksat split built — modal-correlation layer]")
    for d in TRAIN_DEV:
        print(f"  {d['role']:18s} {d['kind']:22s} {d['bytes']//1024:>8d} KiB  {d['sha256'][:12]}")
    for d in DIAGNOSTIC_ONLY:
        print(f"  {'diagnostic_only':18s} {d['kind']:22s} {d['bytes']//1024:>8d} KiB  {d['sha256'][:12]}")
    print(f"  {'HELD_OUT':18s} {HELD_OUT['regime']:22s} {HELD_OUT['bytes']//1024:>8d} KiB  {HELD_OUT['sha256'][:12]}")


if __name__ == "__main__":
    main()
