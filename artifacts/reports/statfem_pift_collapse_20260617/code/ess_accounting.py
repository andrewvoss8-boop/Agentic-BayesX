#!/usr/bin/env python3
"""Effective-sample-size (N_eff) accounting (NEW file) — the WHY behind collapse vs plateau (card §4.2/§5).

For a Gaussian residual with covariance Σ(s) = σ_meas² I + s·C  (s = σ_d², C = the discrepancy correlation
matrix, eigenvalues Lam), the Fisher information for the residual-variance scale s is
    I(s) = ½ Σ_k [ Lam_k / (σ_meas² + s·Lam_k) ]² ,
and the "effective number of independent observations informing σ_d" is
    N_eff_fisher(s) = 2 (σ_meas² + s)² · I(s)        (= N exactly in the iid case C=I).

  - iid (M0/M1): C = I, every Lam = 1 ⇒ I(s) = ½ N/(σ_meas²+s)² ⇒ N_eff = N. Fisher info ∝ N → σ_d
    posterior collapses, identified-θ variance ∝ 1/(N·J) → 0 (PIFT's (nJ)⁻¹). GROWS with N.
  - correlated (M2/M3): C has a few large eigenvalues (smooth field) ⇒ I(s) is BOUNDED ⇒ N_eff SATURATES.
    We also report the participation ratio PR = (Σ Lam)² / Σ Lam² (= effective # independent discrepancy
    modes; = N for iid, saturates for correlated) and the analytic ceiling = (band in correlation lengths) ×
    (sensor extent in correlation lengths) — the number of genuinely independent freq×space cells.

C_f = exp(-½ (Δ log f / ℓ_f)²), C_z = exp(-|Δx| / ℓ_z); kron eigenvalues factorize so PR = PR_f·PR_z (no need to
form the N×N kron). M3 additionally projects C off the θ→FRF span (P_perp), computed via nuts_arms.build_cov.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WS = HERE.parent
OUT = WS / "out"
sys.path.insert(0, str(HERE))

import core            # noqa: E402
import nuts_arms as na  # noqa: E402
import run_ladder as rl  # noqa: E402

SM2 = core.SIGMA_MEAS ** 2


def pr_1d(Lam):
    Lam = np.clip(np.asarray(Lam, float), 0, None)
    return float(Lam.sum() ** 2 / np.sum(Lam ** 2))


def neff_fisher(Lam, s):
    Lam = np.clip(np.asarray(Lam, float), 0, None)
    I = 0.5 * np.sum((Lam / (SM2 + s * Lam)) ** 2)
    return float(2.0 * (SM2 + s) ** 2 * I)


def main():
    model = core.load_model()
    drive, pool, held, all_ch = rl.layout(model)
    theta_truth = core.theta_vector(core.COMBOS[rl.TRUTH_COMBO]["theta"])

    # analytic independent-cell ceiling
    band_logspan = np.log(core.BAND[1] / core.BAND[0])
    cells_f_ceiling = band_logspan / core.DISC_LEN_LOGF                     # freq independent cells
    coords_pool = model.dof_xyz[np.asarray(pool)]
    z_extent = coords_pool[:, 2].ptp()
    cells_z_ceiling = max(1.0, z_extent / core.DISC_LEN_Z)

    files = sorted(glob.glob(str(OUT / "cell_synth_*.json")))
    by_arm = {"M0": {"N": [], "N_eff": [], "kind": "iid"},
              "M1": {"N": [], "N_eff": [], "kind": "iid"},
              "M3": {"N": [], "N_eff": [], "N_eff_pr": [], "kind": "correlated_orthogonal"}}
    if Path(OUT / "cell_synth_M2_nf160_ns6.json").exists() or any("_M2_" in f for f in files):
        by_arm["M2"] = {"N": [], "N_eff": [], "N_eff_pr": [], "kind": "correlated"}

    proj_cache = {}
    for fpath in files:
        c = json.load(open(fpath))
        arm = c["arm"]; nf = c["N_freq"]; ns = c["N_sensor"]; N = c["N"]
        if arm not in by_arm:
            continue
        s = (c.get("sigma_d", {}).get("med") or 0.08) ** 2
        fidx, observed, _, _ = rl.cell_grids(nf, ns, pool, held)
        freqs = core.freq_grid(rl.NMAX)[fidx]
        coords_obs = model.dof_xyz[np.asarray(observed)]
        if arm in ("M0", "M1"):
            by_arm[arm]["N"].append(N); by_arm[arm]["N_eff"].append(N)
        else:
            Cf = na.corr_freq(freqs, core.DISC_LEN_LOGF)
            Cz = na.corr_space(coords_obs, core.DISC_LEN_Z)
            lam_f = np.clip(np.linalg.eigvalsh(Cf), 0, None)
            lam_z = np.clip(np.linalg.eigvalsh(Cz), 0, None)
            pr = pr_1d(lam_f) * pr_1d(lam_z)            # unprojected participation ratio (separable)
            # projected eigenvalues for M3 (remove θ→FRF span); cache by (nf,ns)
            if arm == "M3":
                key = (nf, ns)
                if key not in proj_cache:
                    _, Lam = na.build_cov("M3", freqs, coords_obs, model=model, observed=observed, drive=drive)
                    proj_cache[key] = np.asarray(Lam)
                Lam = proj_cache[key]
            else:
                Lam = np.kron(lam_f, lam_z)
            by_arm[arm]["N"].append(N)
            by_arm[arm]["N_eff"].append(neff_fisher(Lam, s))
            by_arm[arm]["N_eff_pr"].append(float(pr))

    # saturation summary
    sat = {}
    for arm, d in by_arm.items():
        if not d["N"]:
            continue
        order = np.argsort(d["N"])
        Ns = np.array(d["N"])[order]; Ne = np.array(d["N_eff"])[order]
        if d["kind"] == "iid":
            sat[arm] = {"trend": "grows_linear", "N_eff_at_maxN": float(Ne[-1]), "ratio_maxN_minN": float(Ne[-1] / Ne[0])}
        else:
            sat[arm] = {"trend": "saturates", "N_eff_at_maxN": float(Ne[-1]), "ratio_maxN_minN": float(Ne[-1] / Ne[0]),
                        "plateau_value_est": float(np.median(Ne[Ns >= np.median(Ns)]))}

    out = {"correlation_lengths": {"len_logf": core.DISC_LEN_LOGF, "len_z": core.DISC_LEN_Z},
           "independent_cell_ceiling": {"freq_cells": float(cells_f_ceiling), "space_cells": float(cells_z_ceiling),
                                        "product": float(cells_f_ceiling * cells_z_ceiling),
                                        "note": "analytic ceiling on N_eff for a correlated arm: band-in-ℓ_f × "
                                                "sensor-extent-in-ℓ_z; densifying past this adds redundant info"},
           "definition": "N_eff_fisher = 2(σ_meas²+s)²·I(s), I(s)=½Σ[Lam/(σ_meas²+s·Lam)]² (=N for iid). "
                         "N_eff_pr = (ΣLam)²/ΣLam² participation ratio. iid grows ∝N; correlated saturates.",
           "by_arm": by_arm, "saturation": sat}
    json.dump(out, open(OUT / "ess_accounting.json", "w"), indent=1)
    print("independent-cell ceiling: freq", round(cells_f_ceiling, 2), "× space", round(cells_z_ceiling, 2),
          "=", round(cells_f_ceiling * cells_z_ceiling, 2))
    for arm, d in by_arm.items():
        if d["N"]:
            print(f"  {arm} ({d['kind']}): N {d['N']}  ->  N_eff {[round(x,1) for x in d['N_eff']]}")


if __name__ == "__main__":
    main()
