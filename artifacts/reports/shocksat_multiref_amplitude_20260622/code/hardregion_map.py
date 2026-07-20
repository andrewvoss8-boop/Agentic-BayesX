#!/usr/bin/env python3
"""'Hard region' map + GENERALIZABILITY test (addresses the over-fitting concern).

Computes, per eligible accel channel, the held-out peak-amplitude residual (theta at L5 MAP, zeta=1%+window,
global units-gain c) AND a-priori FEM-computable features (NO test data needed):
  - drive_dist  = |sensor - impact|         (near-field of the load = hard for a truncated modal model)
  - highmode_frac = fraction of the sensor's in-band modal response from FEM modes NOT in the 27 VALIDATED
                    (data-matched) modes (response dominated by un-validated local/high modes = hard)
Question: is 'hard' predictable from a problem-agnostic FEM feature (=> generalizable heteroscedastic discrepancy),
or only from the hand-labeled 8-channel list (=> bespoke / over-fit)? Saves out/hardregion_map.json + features for the figure.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq
import dampcorr_qoi as dc

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
CARD_A_OUT = WS.parent / "statfem_real_validation_20260617" / "out"
HARD = {4, 27, 38, 40, 52, 69, 92, 98}
REGION = {4: "source_face", 27: "source_face", 38: "source_face", 40: "box_column",
          52: "box_column(bolted joint)", 69: "box_column", 92: "strut_base", 98: "dish"}


def spearman(x, y):
    xr = np.argsort(np.argsort(x)); yr = np.argsort(np.argsort(y))
    return float(np.corrcoef(xr, yr)[0, 1])


def main():
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    tau = -(rf.PROC["N"] - 1) / (rf.FS * np.log(rf.PROC["exp_end"]))
    theta_map = {g: v["med"] for g, v in json.loads((CARD_A_OUT / "modal_feature.json").read_text())["theta_post"].items()}
    theta = rf.core.theta_vector(theta_map)

    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rows = ch.rows[elig]; daqs = [ch.daq[p] for p in elig]; coords = ch.coords[elig]
    eta = np.full(R.A.shape[1], 2.0 * rf.ZETA_NOM)
    lm = dc.fem_logmag_batch_permode(R, freqs, theta[None, :], rows, ch.drive_row, eta, tau)[0]
    tru = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in daqs])) + 1e-300).T
    wq = np.array([meas["weight"][didx[d]][fb] for d in daqs]).T
    c = hq.wmedian((tru - lm).ravel(), wq.ravel())
    peak_pred = np.array([hq.SC_qoi_peak(np.exp((lm + c)[:, k])) for k in range(len(elig))])
    peak_tru = np.array([hq.SC_qoi_peak(np.exp(tru[:, k])) for k in range(len(elig))])
    res_db = np.abs(20 * np.log10(peak_pred / peak_tru))

    # a-priori features
    drive_xyz = np.array(ch.drive_xyz)
    drive_dist = np.linalg.norm(coords - drive_xyz[None, :], axis=1)

    # high-mode fraction: residue magnitude per FEM mode at each sensor; validated = 27 matched FEM indices
    K = R.A_fix + np.einsum("g,gij->ij", theta, R.A)
    lam, Q = np.linalg.eigh(K); lam = np.clip(lam, 1e-9, None)
    fmode = np.sqrt(lam) / (2 * np.pi)
    inband = (fmode >= rf.BAND[0]) & (fmode <= rf.BAND[1])
    meas_f, _ = mf.extract_measured_modes(meas, ch)
    pairs, _ = mf.match(R, meas_f)
    validated = set(int(p[0]) for p in pairs)
    ud = ch.drive_row @ Q                              # (r,)
    Us = rows @ Q                                      # (n_elig, r)
    res_mag = np.abs(Us * ud[None, :])                 # (n_elig, r) residue magnitude per mode
    hi = np.array([k for k in range(len(lam)) if inband[k] and k not in validated])
    ib = np.array([k for k in range(len(lam)) if inband[k]])
    highmode_frac = res_mag[:, hi].sum(1) / (res_mag[:, ib].sum(1) + 1e-30)

    is_hard = np.array([1 if d in HARD else 0 for d in daqs])

    # GENERALIZABLE alternative test: is the residual SPATIALLY CORRELATED? (then a spatial-GP discrepancy
    # transfers warning from observed-high-residual channels to nearby held-out channels, NO hand-label needed)
    n = len(elig)
    D = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1))
    rr = res_db - res_db.mean()
    iu, ju = np.triu_indices(n, 1)
    dpair = D[iu, ju]; gpair = 0.5 * (res_db[iu] - res_db[ju]) ** 2   # semivariance
    edges = np.array([0, 3, 6, 10, 15, 25, 40, 100])
    vario = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (dpair >= a) & (dpair < b)
        if m.sum() >= 5:
            vario.append({"d_lo": float(a), "d_hi": float(b), "semivariance": float(gpair[m].mean()),
                          "n_pairs": int(m.sum())})
    # nearest-neighbor residual correlation (Moran-like): each channel vs mean of its 4 nearest
    nn_pred = np.zeros(n)
    for i in range(n):
        order = np.argsort(D[i]); nb = order[1:5]
        nn_pred[i] = res_db[nb].mean()
    moran_like = float(np.corrcoef(res_db, nn_pred)[0, 1])

    rec = {
        "n_eligible": int(len(elig)), "gain_c": float(c),
        "hard_present": [int(d) for d in daqs if d in HARD],
        "mean_res_db_hard": float(res_db[is_hard == 1].mean()),
        "mean_res_db_rest": float(res_db[is_hard == 0].mean()),
        "spearman_resdb_vs": {"drive_dist": spearman(drive_dist, res_db),
                              "highmode_frac": spearman(highmode_frac, res_db),
                              "log_dynamic_range": spearman(np.log10(dr[elig]), res_db)},
        "generalizability_note": (
            "If an a-priori FEM feature (drive_dist/highmode_frac) correlated strongly with |residual|, a "
            "feature-keyed discrepancy would TRANSFER to new problems. If only the hand-labeled hard flag "
            "separates them, the 2-population split is BESPOKE (over-fit) and must be labeled a demonstration."),
        "spatial_correlation": {"variogram": vario, "nn4_moran_like_corr": moran_like,
            "note": ("nn4 corr = correlation of each channel's |res| with the mean |res| of its 4 nearest "
                     "neighbors; >~0.4 => residual is spatially clustered => a SPATIALLY-CORRELATED (Schneider/M4) "
                     "discrepancy generalizes WITHOUT a hand-label (observed channels warn nearby held-out ones).")},
        "per_channel": [{"daq": int(daqs[i]), "x": float(coords[i, 0]), "y": float(coords[i, 1]),
                         "z": float(coords[i, 2]), "res_db": float(res_db[i]),
                         "drive_dist": float(drive_dist[i]), "highmode_frac": float(highmode_frac[i]),
                         "hard": int(is_hard[i]), "region": REGION.get(int(daqs[i]), "")}
                        for i in range(len(elig))],
        "drive_xyz": [float(v) for v in drive_xyz],
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "hardregion_map.json").write_text(json.dumps(rec, indent=2))
    print(f"n_elig {len(elig)} | mean|res| hard {rec['mean_res_db_hard']:.1f} dB vs rest {rec['mean_res_db_rest']:.1f} dB")
    print("Spearman |res| vs a-priori features:", {k: round(v, 2) for k, v in rec["spearman_resdb_vs"].items()})
    print("hard present:", rec["hard_present"])


if __name__ == "__main__":
    main()
