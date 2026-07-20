#!/usr/bin/env python3
"""'Plenty of data' test (Andrew, D15): is the wide held-out CI a METHOD limit (we never used the MEASURED mode
shapes) rather than a data limit? We HAVE a full EMA (.ash: 33 shapes / 76 nodes). Predict held-out sensor peak
|H| using the MEASURED shapes (fused into the reduced basis) and compare the held-out cross-channel error to the
FEM-shape baseline (L5).

Construction: express each matched measured mode in reduced coords  psi_r = pinv(G) @ meas_shape_r   (G: 132
measured DOFs -> 74 reduced). Held-out sensor accelerance  H(s,w) = sum_r a_r (rows_s . psi_r)(drive . psi_r)
(-w^2)/((1+i eta_r) w_r^2 - w^2),  w_r, zeta_r MEASURED (+ exp-window),  per-mode complex scale a_r calibrated by
weighted complex LSQ on OBSERVED channels only. The cross-channel SHAPE is fixed by the measured psi_r; the
held-out channel's amplitude is a genuine prediction (its FRF is never used in the fit). If the held-out error
collapses vs FEM-shape L5 -> the wide CI was a METHOD limit (plenty of data). Output: out/measured_shape_qoi_seed<seed>.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import heldout_qoi as hq

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
CARD_A_OUT = WS.parent / "statfem_real_validation_20260617" / "out"
HARD = {4, 27, 38, 40, 52, 69, 92, 98}


def run(seed=0, obs_frac=0.6, ridge=1e-3, write=True):
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    w = 2 * np.pi * freqs; didx = {d: i for i, d in enumerate(meas["daq"])}
    tau = -(rf.PROC["N"] - 1) / (rf.FS * np.log(rf.PROC["exp_end"]))

    # measured shapes in reduced coords (psi_r) for matched .ash modes + measured zeta
    am = np.load(CARD_A_OUT / "ash_match.npz", allow_pickle=True)
    G = am["G"]; meas_shape = am["meas_shape"]; mfr = am["mfr"]
    pairs = [(int(p[0]), int(p[1]), float(p[2])) for p in am["pairs"]]
    damp = np.load(WS / "data" / "measured_modes.npz", allow_pickle=True)["damp"] / 100.0
    Gpinv = np.linalg.pinv(G)                              # (74,132)
    ridx = [r for (r, k, mac) in pairs]                   # matched .ash mode indices
    psi = np.array([Gpinv @ meas_shape[:, r] for r in ridx]).T          # (74, n_modes)
    wr = mfr[ridx] * 2 * np.pi
    zr = damp[ridx] + rf.measured_zeta_w(mfr[ridx])       # structural + window
    eta = 2.0 * zr; n_mode = len(ridx)

    # split (same protocol as heldout_qoi)
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]

    drive_coef = ch.drive_row @ psi                       # (n_mode,)
    # modal basis at a set of sensor rows: M[f, s, r] = (row_s.psi_r)(drive.psi_r) (-w^2)/((1+i eta_r) w_r^2 - w^2)
    def basis(rows):
        sc = rows @ psi                                   # (Ns, n_mode)
        denom = (1 + 1j * eta)[None, :] * (wr ** 2)[None, :] - (w ** 2)[:, None]   # (Nf, n_mode)
        res = (-(w ** 2)[:, None, None]) * (sc[None, :, :] * drive_coef[None, None, :]) / denom[:, None, :]
        return res                                        # (Nf, Ns, n_mode)

    M_obs = basis(ch.rows[obs_pos]); M_ho = basis(ch.rows[ho_pos])
    H_obs = np.array([meas["H"][didx[d]][fb] for d in obs_daqs]).T          # (Nf, n_obs)
    Wq = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T        # (Nf, n_obs)

    # weighted complex LSQ for a_r on OBSERVED (Nf*n_obs eqns, n_mode unknowns) + light ridge
    A = M_obs.reshape(-1, n_mode); b = H_obs.reshape(-1); sw = np.sqrt(Wq.reshape(-1))
    Aw = A * sw[:, None]; bw = b * sw
    AhA = Aw.conj().T @ Aw + ridge * np.eye(n_mode) * np.real(np.trace(Aw.conj().T @ Aw)) / n_mode
    a_r = np.linalg.solve(AhA, Aw.conj().T @ bw)          # (n_mode,) complex modal scales

    H_obs_pred = (M_obs @ a_r)                            # (Nf, n_obs)
    H_ho_pred = (M_ho @ a_r)                              # (Nf, n_ho)
    H_ho_tru = np.array([meas["H"][didx[d]][fb] for d in ho_daqs]).T

    def peakdb_err(pred, tru):
        pk_p = np.abs(pred).max(0); pk_t = np.abs(tru).max(0)
        return 20 * np.log10(pk_p / pk_t)
    err_obs = peakdb_err(H_obs_pred, H_obs)
    err_ho = peakdb_err(H_ho_pred, H_ho_tru)
    hard_ho = np.array([1 if d in HARD else 0 for d in ho_daqs])

    def stats(e):
        return {"median_abs_db": float(np.median(np.abs(e))), "p90_abs_db": float(np.percentile(np.abs(e), 90)),
                "sigma_log": float(np.std(e * np.log(10) / 20))}   # log-ratio std (compare to L5 sigma_QOI~1.1)

    rec = {"deliverable": "measured-shape-fused held-out QOI (Andrew 'plenty of data' / method-vs-data test)",
           "split_seed": seed, "n_modes_measured_shape": n_mode, "n_observed": len(obs_pos),
           "n_heldout": len(ho_pos), "n_ho_hard": int(hard_ho.sum()),
           "observed_in_sample": stats(err_obs), "heldout": stats(err_ho),
           "heldout_rest": stats(err_ho[hard_ho == 0]),
           "heldout_hard": stats(err_ho[hard_ho == 1]) if hard_ho.sum() else None,
           "baseline_FEMshape_L5": {"heldout_sigma_QOI_log": 1.10, "heldout_median_abs_db_approx": 6.6,
                                    "note": "from dampcorr/discrepancy_diagnostic FEM-shape predictions"},
           "runtime_s": time.time() - t0}
    if write:
        OUT.mkdir(exist_ok=True)
        (OUT / f"measured_shape_qoi_seed{seed:02d}.json").write_text(json.dumps(rec, indent=2))
    print(f"seed {seed}: {n_mode} measured-shape modes; obs {len(obs_pos)} / ho {len(ho_pos)} (hard {int(hard_ho.sum())})")
    print(f"  MEASURED-shape held-out: median|err| {rec['heldout']['median_abs_db']:.1f} dB  "
          f"sigma_log {rec['heldout']['sigma_log']:.2f}  (rest {rec['heldout_rest']['median_abs_db']:.1f} dB)")
    print(f"  FEM-shape (L5) baseline: median|err| ~6.6 dB  sigma_QOI ~1.10")
    print(f"  in-sample (observed): median|err| {rec['observed_in_sample']['median_abs_db']:.1f} dB")
    print(f"  runtime {rec['runtime_s']:.1f}s")
    return rec


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(seed=seed)
