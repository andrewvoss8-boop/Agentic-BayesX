#!/usr/bin/env python3
"""Cheap, read-only recomputations for the ShockSat full-spectrum review.

The reviewed workspace is never written. Outputs are written beside this script.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr


REVIEW = Path(__file__).resolve().parent
ROOT = REVIEW.parents[2]
STUDY = ROOT / "artifacts/reports/shocksat_full_spectrum_frf_20260714"
OUT = REVIEW / "out"
FIXTURE = REVIEW / "scratch/checker_fixture"
DEV = ["m_xpos_990x", "m_zpos_990z", "m_ypos_990y", "m_zpos_900z"]


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def paired(exact, arm, ref, band="sub200"):
    a = np.array([exact[arm]["exact"]["folds"][k][band]["P1p"] for k in DEV])
    b = np.array([exact[ref]["exact"]["folds"][k][band]["P1p"] for k in DEV])
    d = a - b
    return {
        "arm_mean_from_folds": float(a.mean()),
        "reference_mean_from_folds": float(b.mean()),
        "delta_mean": float(d.mean()),
        "delta_se": float(d.std(ddof=1) / np.sqrt(d.size)),
        "two_se": float(2 * d.std(ddof=1) / np.sqrt(d.size)),
        "per_fold_delta": d.tolist(),
    }


def recompute_exact_scores():
    exact = load_json(STUDY / "out/exact_freeze_scores.json")
    out = {}
    for arm in exact:
        means = {}
        for band in ("sub200", "b200_500"):
            vals = [exact[arm]["exact"]["folds"][k][band]["P1p"] for k in DEV]
            means[band] = {
                "mean_from_folds": float(np.mean(vals)),
                "saved_mean": exact[arm]["exact"][band],
                "raw_fold_se": float(np.std(vals, ddof=1) / np.sqrt(len(vals))),
            }
        out[arm] = means
    out["paired_vs_A1"] = {arm: paired(exact, arm, "A1") for arm in ("B", "C", "D", "R")}
    out["paired_D_vs_R"] = paired(exact, "D", "R")
    out["screening_D_minus_R"] = (
        exact["D"]["screen"]["sub200"] - exact["R"]["screen"]["sub200"]
    )
    out["exact_D_minus_R"] = exact["D"]["exact"]["sub200"] - exact["R"]["exact"]["sub200"]
    out["n_remodel_candidates_exact_rescored"] = 2
    out["n_remodel_candidates_total"] = 28
    return out


def recompute_actions():
    rows = [
        json.loads(line)
        for line in (STUDY / "out/query_log.jsonl").read_text().splitlines()
        if line.strip()
    ]
    by_track = {}
    genuine_ops = {"refine", "rbe2_soften"}
    for track in ("agent", "random"):
        tr = [r for r in rows if r["track"] == track]
        op_counts = Counter()
        genuine_candidates = []
        for r in tr:
            spec = load_json(STUDY / "out/candidate_specs" / f"{r['cid']}.json")
            ops = [op["op"] for op in spec.get("ops", [])]
            op_counts.update(ops)
            if genuine_ops.intersection(ops):
                genuine_candidates.append({"cid": r["cid"], "ops": ops})
        by_track[track] = {
            "n_candidates": len(tr),
            "family_counts_from_query_log": dict(Counter(r["family"] for r in tr)),
            "op_counts_from_specs": dict(op_counts),
            "genuine_model_form_candidates": genuine_candidates,
            "n_genuine_model_form_candidates": len(genuine_candidates),
            "best_screen_sub200": max(r["sub200_P1p"] for r in tr),
        }
    return by_track


def recompute_overlap_and_force():
    wide_dir = STUDY / "data/multiref_wide"
    existing_dir = ROOT / "artifacts/reports/shocksat_psd_envelope_twin_20260623/data/multiref_modal"
    netcg_dir = ROOT / "artifacts/reports/shocksat_netcg_method_selection_20260701/data/multiref_modal"
    rows = {}
    for key in [
        "m_xpos_990x",
        "m_zpos_990z",
        "m_ypos_990y",
        "m_zpos_900z",
        "m_xy_990xy",
    ]:
        wp = wide_dir / f"{key}_wide.npz"
        ep = (netcg_dir if key == "m_ypos_990y" else existing_dir) / f"{key}.npz"
        w = np.load(wp, allow_pickle=True)
        e = np.load(ep, allow_pickle=True)
        fw, fe = np.asarray(w["freqs"]), np.asarray(e["freqs"])
        jj = np.array([int(np.argmin(np.abs(fw - f))) for f in fe])
        hw, he = np.asarray(w["H1"])[:, jj], np.asarray(e["H1"])
        corrs = [
            float(np.corrcoef(np.abs(he[i]), np.abs(hw[i]))[0, 1])
            for i in range(he.shape[0])
        ]
        dlog = np.abs(
            np.log10(np.abs(hw) + 1e-300) - np.log10(np.abs(he) + 1e-300)
        )
        rows[key] = {
            "corr_median_direct_npz": float(np.median(corrs)),
            "corr_min_direct_npz": float(np.min(corrs)),
            "med_abs_dlog10_direct_npz": float(np.median(dlog)),
            "max_abs_dlog10_direct_npz": float(np.max(dlog)),
            "same_hits": list(e["used"]) == list(w["used"]),
        }
    force = load_json(STUDY / "data/force_health.json")
    peaks = [
        h["force_absmax_lb"]
        for drive in force.values()
        for h in drive["hits"]
        if h["status"] == "used"
    ]
    return {
        "drives": rows,
        "used_force_peak_lbf_min": float(min(peaks)),
        "used_force_peak_lbf_max": float(max(peaks)),
        "n_used_hits": len(peaks),
    }


def recompute_fem_ceiling():
    raw = np.load(STUDY / "out/raw_full_eig_theta1.npz")
    kept = np.load(STUDY / "out/full_eig_theta1.npz")
    fr = np.asarray(raw["freqs"])
    fk = np.asarray(kept["freqs"])
    top = float(fr.max())
    plateau = np.abs(fr - top) <= 1e-6 * abs(top)
    cutoff = top - 1.0
    removed = fr >= cutoff
    return {
        "raw_mode_count": int(fr.size),
        "kept_mode_count": int(fk.size),
        "removed_by_1Hz_cut_count": int(removed.sum()),
        "reported_exact_top_plateau_count": int(plateau.sum()),
        "raw_top_hz": top,
        "raw_freq_quantiles_last345_hz": np.quantile(fr[-345:], [0, 0.25, 0.5, 0.75, 1]).tolist(),
        "kept_top_hz": float(fk.max()),
        "kept_count_le_639Hz": int((fk <= 639.0).sum()),
        "scoring_cap_from_639_div_1p25_hz": 639.0 / 1.25,
    }


def recompute_selection():
    arm_e = load_json(STUDY / "out/arm_E.json")
    out = {}
    for sig in (0.15, 0.25, 0.4):
        pairs = [
            (c[f"logZ_sig{sig}"], c["heldout_sub200"])
            for c in arm_e["candidates"]
            if math.isfinite(c[f"logZ_sig{sig}"]) and math.isfinite(c["heldout_sub200"])
        ]
        rho = float(spearmanr([p[0] for p in pairs], [p[1] for p in pairs]).statistic)
        out[str(sig)] = {"n_finite": len(pairs), "spearman_finite_only": rho}
    out["rand10_present"] = any(c["cid"] == "rand10_rebuild" for c in arm_e["candidates"])
    out["n_candidates"] = len(arm_e["candidates"])
    return out


def recompute_misc():
    fim = load_json(STUDY / "out/identifiability.json")
    nuts = load_json(STUDY / "out/nuts_diagnostics.json")["posteriors"]
    ceiling = load_json(STUDY / "out/certified_ceiling.json")
    netcg = load_json(STUDY / "out/netcg_results.json")
    return {
        "fim_min_over_prior_precision": min(fim["fim_eigenvalues"])
        / fim["prior_precision_logtheta"],
        "fim_max_over_prior_precision": max(fim["fim_eigenvalues"])
        / fim["prior_precision_logtheta"],
        "nuts_worst_rhat": max(p["rhat_max"] for p in nuts),
        "nuts_worst_ess": min(p["ess_min"] for p in nuts),
        "high_band_coherence_500_1000": {
            k: v["med_coh_500_1000"] for k, v in ceiling.items()
        },
        "high_band_coherence_500_1000_min": min(
            v["med_coh_500_1000"] for v in ceiling.values()
        ),
        "netcg_width_vs_delivered_factor": {
            "shear_x": netcg["shear_x"]["width_ratio"] / 1.51,
            "shear_y": netcg["shear_y"]["width_ratio"] / 2.30,
            "normal_z": netcg["normal_z"]["width_ratio"] / 2.53,
        },
    }


def load_checker():
    spec = importlib.util.spec_from_file_location("reviewed_checker", STUDY / "check.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def replay_checker_read_only():
    checker = load_checker()
    report = {}
    overall = "GREEN"
    for name, fn in checker.GATES:
        try:
            status, detail = fn()
        except Exception as exc:
            status, detail = "RED", f"gate crashed: {type(exc).__name__}: {exc}"
        report[name] = {"status": status, "detail": detail}
        if checker.RANK[status] > checker.RANK[overall]:
            overall = status
    report["OVERALL"] = overall
    report["invocation_note"] = (
        "Imported and called the immutable gate functions directly so check.py could not overwrite "
        "the reviewed workspace's checker_report.json."
    )
    return report


def checker_fixture_tests():
    (FIXTURE / "code").mkdir(parents=True, exist_ok=True)
    (FIXTURE / "out").mkdir(parents=True, exist_ok=True)
    planted = FIXTURE / "code/planted_selection.py"
    planted.write_text("import numpy as np\nx = np.linalg.lstsq(A, b)\n")
    (FIXTURE / "out/selection_files.json").write_text(
        json.dumps({"files": ["code/planted_selection.py"]})
    )
    checker = load_checker()
    original_ws = checker.WS
    checker.WS = str(FIXTURE)
    g03 = checker.gate03_no_amplitude_lsq()
    (FIXTURE / "out/nuts_diagnostics.json").write_text(
        json.dumps(
            {
                "posteriors": [
                    {"name": "planted_bad", "rhat_max": 2.0, "ess_min": 2, "div_frac": 0.0}
                ]
            }
        )
    )
    g08 = checker.gate08_nuts()
    checker.WS = original_ws
    return {
        "G03_planted_lstsq": {"status": g03[0], "detail": g03[1]},
        "G08_planted_nonconvergence": {"status": g08[0], "detail": g08[1]},
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    recomputed = {
        "exact_scores": recompute_exact_scores(),
        "action_space": recompute_actions(),
        "overlap_and_force": recompute_overlap_and_force(),
        "fem_ceiling": recompute_fem_ceiling(),
        "selection_sensitivity": recompute_selection(),
        "misc": recompute_misc(),
    }
    checker_replay = replay_checker_read_only()
    checker_tests = checker_fixture_tests()
    checker_tests["reviewed_check_sha256"] = hashlib.sha256(
        (STUDY / "check.py").read_bytes()
    ).hexdigest()
    checker_tests["locked_sha256"] = (STUDY / "CHECKER.sha256").read_text().split()[0]
    (OUT / "recomputed_checks.json").write_text(json.dumps(recomputed, indent=2))
    (OUT / "checker_replay.json").write_text(json.dumps(checker_replay, indent=2))
    (OUT / "checker_mutation_tests.json").write_text(json.dumps(checker_tests, indent=2))
    print(json.dumps(
        {
            "checker_overall": checker_replay["OVERALL"],
            "S1_D_vs_A1": recomputed["exact_scores"]["paired_vs_A1"]["D"],
            "S1_R_vs_A1": recomputed["exact_scores"]["paired_vs_A1"]["R"],
            "S2_D_vs_R": recomputed["exact_scores"]["paired_D_vs_R"],
            "fem_ceiling": recomputed["fem_ceiling"],
            "selection_sensitivity": recomputed["selection_sensitivity"],
            "checker_tests": checker_tests,
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
