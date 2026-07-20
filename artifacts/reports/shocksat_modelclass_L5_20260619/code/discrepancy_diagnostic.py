#!/usr/bin/env python3
"""Phase C gate — is the per-channel peak-amplitude residual PREDICTABLE from an observable channel feature?
If yes, a feature-keyed (heteroscedastic) discrepancy can keep easy channels TIGHT and only hard ones WIDE =
honest CI tightening (vs the current single iid lognormal sigma_QOI that inflates every channel to cover the
hard-channel tails).

Per channel (theta at L5 MAP, zeta=1%+window, global units-gain c on all eligible): residual r = log(peak_pred) -
log(peak_truth). Correlate |r| with: dynamic range, sensor->FEM-node snap distance, |z|, hard-accel flag
(ch4/27/38/40/52/69/92/98), region (Card D region_diagnosis). Output: out/discrepancy_diagnostic.json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import heldout_qoi as hq
import dampcorr_qoi as dc

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
CARD_A_OUT = WS.parent / "statfem_real_validation_20260617" / "out"
HARD = {4, 27, 38, 40, 52, 69, 92, 98}


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
    theta = rf.core.theta_vector(theta_map)[None, :]

    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rows = ch.rows[elig]
    eta = np.full(R.A.shape[1], 2.0 * rf.ZETA_NOM)
    lm = dc.fem_logmag_batch_permode(R, freqs, theta, rows, ch.drive_row, eta, tau)[0]   # (Nf, n_elig)
    daqs = [ch.daq[p] for p in elig]
    tru = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in daqs])) + 1e-300).T     # (Nf, n_elig)
    wq = np.array([meas["weight"][didx[d]][fb] for d in daqs]).T
    c = hq.wmedian((tru - lm).ravel(), wq.ravel())
    pred = lm + c
    peak_pred = np.array([hq.SC_qoi_peak(np.exp(pred[:, k])) for k in range(len(elig))])
    peak_tru = np.array([hq.SC_qoi_peak(np.exp(tru[:, k])) for k in range(len(elig))])
    r_db = 20 * np.log10(peak_pred / peak_tru)
    abr = np.abs(r_db)

    feat_DR = np.log10(dr[elig])
    feat_snap = np.array([ch.snap_in[p] for p in elig])
    feat_z = np.abs(ch.coords[elig, 2])
    is_hard = np.array([1.0 if ch.daq[p] in HARD else 0.0 for p in elig])

    out = {"n_eligible": int(len(elig)), "gain_c": float(c),
           "residual_db": {"median_abs": float(np.median(abr)), "p90_abs": float(np.percentile(abr, 90)),
                           "max_abs": float(np.max(abr)), "frac_gt3": float(np.mean(abr > 3)),
                           "frac_gt6": float(np.mean(abr > 6))},
           "spearman_absres_vs": {"log_dynamic_range": spearman(feat_DR, abr),
                                  "snap_distance_in": spearman(feat_snap, abr),
                                  "abs_z_in": spearman(feat_z, abr)},
           "hard_accels": {"n_present": int(is_hard.sum()),
                           "present_daqs": [int(ch.daq[p]) for p in elig if ch.daq[p] in HARD],
                           "mean_abs_res_hard_db": float(abr[is_hard == 1].mean()) if is_hard.sum() else None,
                           "mean_abs_res_rest_db": float(abr[is_hard == 0].mean())},
           "note": ("if |residual| correlates with a feature (|rho|>~0.3) OR hard>>rest, a feature-keyed "
                    "heteroscedastic discrepancy can tighten the easy-channel CI while keeping coverage.")}
    OUT.mkdir(exist_ok=True)
    (OUT / "discrepancy_diagnostic.json").write_text(json.dumps(out, indent=2))
    print(f"n_elig {len(elig)} | residual median|{out['residual_db']['median_abs']:.1f}dB p90 "
          f"{out['residual_db']['p90_abs']:.1f} max {out['residual_db']['max_abs']:.1f} | >6dB "
          f"{out['residual_db']['frac_gt6']*100:.0f}%")
    print("Spearman |res| vs:", {k: round(v, 2) for k, v in out["spearman_absres_vs"].items()})
    h = out["hard_accels"]
    print(f"hard accels present {h['n_present']} {h['present_daqs']}: mean|res| hard "
          f"{h['mean_abs_res_hard_db']} dB vs rest {h['mean_abs_res_rest_db']:.1f} dB")


if __name__ == "__main__":
    main()
