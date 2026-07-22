#!/usr/bin/env python3
"""Create design-only registries, data inventory, and immutable source manifest."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

from common import REPO, WS, kmedoids, region_labels, sha256, write_json


SRC_RF = REPO / "artifacts/reports/shocksat_modelclass_L5_20260619/code/realfrf.py"
SRC_DATA = REPO / "artifacts/reports/shocksat_modelclass_L5_20260619/data"
WIDE = REPO / "artifacts/reports/shocksat_full_spectrum_frf_20260714/data/multiref_wide"
CARD = REPO / "docs/agents/structured_discrepancy_codex_review_20260722/task_card_codex_structured_discrepancy.md"


def main() -> None:
    start = time.time()
    rows = {
        int(r["daq_channel"]): r
        for r in csv.DictReader((SRC_DATA / "channel_map.csv").open())
        if r["configuration"] == "tap_impact" and r["structural_axis"] in {"X", "Y", "Z"}
    }
    drive_files = sorted(WIDE.glob("*_wide.npz"))
    if len(drive_files) != 5:
        raise RuntimeError(f"expected five drive caches, found {len(drive_files)}")
    common = None
    drive_meta = []
    for p in drive_files:
        z = np.load(p, allow_pickle=True)
        daq = set(map(int, z["daq"]))
        common = daq if common is None else common & daq
        f = np.asarray(z["freqs"], float)
        drive_meta.append({
            "id": p.stem.replace("_wide", ""),
            "source": str(p.relative_to(REPO)),
            "drive_xyz_in": np.asarray(z["xyz"], float).tolist(),
            "drive_axis": str(z["axis"].item()),
            "label": str(z["label"].item()),
            "instrument": str(z["instrument"].item()),
            "native_frequency_count": int(len(f)),
            "native_frequency_min_hz": float(f.min()),
            "native_frequency_max_hz": float(f.max()),
            "native_frequency_spacing_median_hz": float(np.median(np.diff(f))),
            "response_channel_count": int(len(z["daq"])),
            "n_hits_used": int(z["n_hits_used"].item()),
            "independent_realizations": "retained impact hits averaged inside source cache",
            "window": "inherited source cache; exact window metadata not stored in NPZ",
            "frame_length": int(z["N"].item()),
            "overlap": "not stored",
            "detrending": "not stored",
            "averaging_axis": "impact hits",
        })
    eligible = sorted(d for d in common if d in rows and d not in {29, 30, 31, 101})
    coords = np.array([[float(rows[d]["x_in"]), float(rows[d]["y_in"]), float(rows[d]["z_in"])] for d in eligible])
    axes = np.array([rows[d]["structural_axis"] for d in eligible])
    mu = coords.mean(axis=0)
    sd = coords.std(axis=0)
    sd[sd == 0] = 1.0
    all_regions = region_labels(coords)
    selected = []
    impossible = []
    region_order = ["impact", "bolted_joint", "strut", "dish", "bulkhead"]
    for reg in region_order:
        idx = np.where(all_regions == reg)[0]
        center = coords[idx].mean(axis=0)
        chosen = []
        for ax in ("X", "Y", "Z"):
            cand = idx[axes[idx] == ax]
            if len(cand):
                chosen.append(int(cand[np.argmin(np.linalg.norm(coords[cand] - center, axis=1))]))
            else:
                impossible.append({"region": reg, "missing_axis": ax})
        for j in idx[np.argsort([eligible[q] for q in idx])]:
            if len(chosen) >= 3:
                break
            if int(j) not in chosen:
                chosen.append(int(j))
        selected.extend(chosen[:3])
    selected = np.array(selected, int)
    sdaq = [eligible[i] for i in selected]
    scoords = coords[selected]
    saxes = axes[selected].tolist()
    smu, ssd = scoords.mean(axis=0), scoords.std(axis=0)
    ssd[ssd == 0] = 1.0
    med_idx, scl = kmedoids((scoords - smu) / ssd, 5)
    centers = ((scoords - smu) / ssd)[med_idx]
    cd = np.linalg.norm(centers[:, None] - centers[None, :], axis=2)
    scale = float(np.median(cd[cd > 0]))
    freqs = np.arange(45.0, 260.0 + 1e-9, 2.5)
    x = np.log(freqs)
    interior = np.linspace(x[0], x[-1], 4)[1:-1]
    full_knots = np.r_[np.repeat(x[0], 4), interior, np.repeat(x[-1], 4)]

    # Contiguous cores and guards.
    bands = []
    for j, idx in enumerate(np.array_split(np.arange(len(freqs)), 5)):
        lo, hi = float(freqs[idx[0]]), float(freqs[idx[-1]])
        score = idx.tolist()
        train = np.where((freqs < lo - 10.0) | (freqs > hi + 10.0))[0].tolist()
        bands.append({"fold": j, "core_hz": [lo, hi], "score_frequency_indices": score,
                      "train_frequency_indices": train, "guard_hz": 10.0})
    digest = hashlib.sha256(CARD.read_bytes()).digest()
    perm = np.argsort(np.frombuffer(digest[:5], dtype=np.uint8)).tolist()
    joint = [{"fold": j, "spatial_cluster": j, "frequency_core": int(perm[j])} for j in range(5)]

    mean_reg = {
        "created_unix": time.time(),
        "response_values_read_before_freeze": False,
        "frequency": {
            "degree": 3,
            "degrees_of_freedom": 6,
            "analysis_endpoints_hz": [45.0, 260.0],
            "interior_knots_log_hz": interior.tolist(),
            "full_knot_vector_log_hz": full_knots.tolist(),
        },
        "location": {
            "region_order": ["impact", "bolted_joint", "strut", "dish", "bulkhead"],
            "standardize_mean_in": smu.tolist(),
            "standardize_sd_in": ssd.tolist(),
            "rbf_medoids_selected_row": med_idx.tolist(),
            "rbf_centers_standardized": centers.tolist(),
            "rbf_scale_standardized": scale,
        },
        "axis": {"labels": sorted(set(saxes)), "categorical": True},
        "interaction": "frequency basis tensor location basis; no channel identity interaction",
        "rank_tolerance": 1e-10,
        "selected_daq": sdaq,
        "selected_coords_in": scoords.tolist(),
        "selected_axes": saxes,
        "selected_regions": region_labels(scoords).tolist(),
    }
    split_reg = {
        "created_unix": time.time(),
        "response_values_read_before_freeze": False,
        "frequency_grid_hz": freqs.tolist(),
        "drives": drive_meta,
        "spatial": [{"fold": j, "heldout_cluster": j,
                     "heldout_selected_rows": np.where(scl == j)[0].tolist()} for j in range(5)],
        "frequency": bands,
        "joint": joint,
        "axis_region_balance_impossibilities": impossible,
        "selection_rule": "three channels per frozen physical region, one X/Y/Z each where possible; nearest to region centroid; DAQ tie-break; spatial holdouts remain coordinate-only k-medoids",
    }
    inventory = {
        "measured_vs_synthetic": {"measured_drive_caches": 5, "synthetic_cases": 4, "synthetic_seeds_per_case": 20},
        "eligible_common_response_channels": len(eligible),
        "selected_response_channels": len(sdaq),
        "selected_daq": sdaq,
        "selected_axis_counts": {a: saxes.count(a) for a in sorted(set(saxes))},
        "selected_region_counts": {r: int(np.sum(region_labels(scoords) == r)) for r in sorted(set(region_labels(scoords)))},
        "analysis_frequency_lines": len(freqs),
        "analysis_range_hz": [float(freqs[0]), float(freqs[-1])],
        "analysis_spacing_hz": 2.5,
        "drives": drive_meta,
        "response_labels_present": True,
        "coordinates_present": True,
        "repeat_variability_modeled": False,
        "repeat_note": "source H1 averages retained impacts; this study has no separate repeat-level likelihood",
    }
    write_json(WS / "mean_basis_registry.json", mean_reg)
    write_json(WS / "split_registry.json", split_reg)
    write_json(WS / "data_inventory.json", inventory)

    source_roles = {
        CARD: "controlling task card",
        REPO / "references/pdfs/digital-twinning-of-self-sensing-structures-using-the-statistical-finite-element-method.pdf": "direct literature check",
        REPO / "references/pdfs/Bayesian parameter updating in linear structural dynamics with frequency transformed data using rational surrogate models.pdf": "direct literature and covariance reference",
        REPO / "artifacts/reports/shocksat_modelclass_L5_20260619/code/schneider_faithful.py": "frozen M0-M3 likelihood implementation",
        SRC_RF: "frozen reduced FRF forward and channel map loader",
        REPO / "artifacts/reports/shocksat_modelclass_L5_20260619/code/core.py": "transitive reduced-model helpers",
        SRC_DATA / "channel_map.csv": "response coordinates and axes",
        SRC_DATA / "reduced_blocks.npz": "reduced stiffness blocks",
        SRC_DATA / "obs_dofs.npy": "reduced model observation mapping",
        SRC_DATA / "keep_dofs.npy": "reduced model retained DOFs",
        REPO / "artifacts/reports/statfem_shocksat_eval_20260616/data/V_keep.npy": "reduced basis",
        REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609/fem_model.npz": "FEM coordinates",
        REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609/nuts_full_samples.npz": "converged modal posterior draws",
        REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609/theta_full.json": "modal posterior summary",
        REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609/joint_strain_energy.json": "modal strain-energy evidence",
        REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609/sensitivity.json": "modal sensitivity evidence",
        REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609/matrices/reduced_blocks.npz": "modal stiffness blocks for independent strain-energy reproduction",
        REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609/pairing.json": "calibration-mode pairing for strain-energy reproduction",
        REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609/reduction_report.json": "finite-perturbation reference",
        REPO / "artifacts/reports/statfem_real_validation_20260617/data/measured_frf_cache.npz": "legacy eight-channel selection quality data",
        REPO / "artifacts/reports/shocksat_modelclass_L5_20260619/out/discrepancy_diagnostic.json": "frozen residual known answer",
        REPO / "artifacts/reports/shocksat_modelclass_L5_20260619/out/spatial_reanalysis.json": "frozen spatial known answer",
    }
    for p in drive_files:
        source_roles[p] = "measured multireference H1 cache"
    for arm in ("M0", "M1", "M2", "M3"):
        p = REPO / f"artifacts/reports/statfem_real_validation_20260617/out/tmcmc_faithful_{arm}_ident4_n8.json"
        source_roles[p] = f"frozen legacy {arm} summary"
    for name, role in [("preregistration.md", "preregistration"), ("split_registry.json", "split registry"),
                       ("mean_basis_registry.json", "mean basis registry"), ("quantity_contracts.md", "quantity contract"),
                       ("check.py", "immutable checker")]:
        source_roles[WS / name] = role
    for p in sorted((WS / "code").glob("*.py")):
        source_roles[p] = "runner source code"
    source_roles[WS / "run_all.sh"] = "one-command replay"
    source_roles[WS / "CHECKER.sha256"] = "checker lock record"
    manifest = {"created_unix": time.time(), "files": []}
    for p, role in sorted(source_roles.items(), key=lambda kv: str(kv[0])):
        if not p.exists():
            raise FileNotFoundError(p)
        manifest["files"].append({"path": str(p.relative_to(REPO) if p.is_relative_to(REPO) else p),
                                  "sha256": sha256(p), "size": p.stat().st_size, "role": role})
    write_json(WS / "source_manifest.json", manifest)
    write_json(WS / "runtime.json", {"active_runtime_s": time.time() - start, "elapsed_wallclock_s": time.time() - start,
                                      "stage1_cap_s": 7200, "stage2_additional_cap_s": 21600,
                                      "total_cap_s": 28800, "commands": [{"name": "freeze", "active_s": time.time() - start}]})
    print(f"FREEZE: {len(sdaq)} channels x {len(freqs)} frequencies, {len(drive_files)} drives")


if __name__ == "__main__":
    main()
