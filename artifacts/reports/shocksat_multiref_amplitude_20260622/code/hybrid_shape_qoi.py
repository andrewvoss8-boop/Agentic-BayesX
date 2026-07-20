#!/usr/bin/env python3
"""Fair test of 'use the measured shapes we have' (D15): a COMPLETE modal-superposition model over all in-band
modes, with per-mode complex scales fit on OBSERVED channels, in two arms:
  FEM_ALL : FEM eigenvector shape for every in-band mode (flexible all-FEM modal model)
  HYBRID  : MEASURED shape (reduced-coord psi_r) for the 20 matched modes, FEM shape for the rest
Identical fitting + scoring -> the held-out cross-channel error difference is EXACTLY what substituting the
measured shapes buys. (The pure 20-mode measured model failed only because it covers 20/44 peaks; this is complete.)
Output: out/hybrid_shape_qoi_seed<seed>.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
CARD_A_OUT = WS.parent / "statfem_real_validation_20260617" / "out"
HARD = {4, 27, 38, 40, 52, 69, 92, 98}


def run(seed=0, obs_frac=0.6, ridge=1e-2, write=True):
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]; w = 2 * np.pi * freqs
    didx = {d: i for i, d in enumerate(meas["daq"])}

    am = np.load(CARD_A_OUT / "ash_match.npz", allow_pickle=True)
    G = am["G"]; ms = am["meas_shape"]; mfr = am["mfr"]
    pairs = [(int(p[0]), int(p[1]), float(p[2])) for p in am["pairs"]]
    damp = np.load(WS / "data" / "measured_modes.npz", allow_pickle=True)["damp"] / 100.0
    Gpinv = np.linalg.pinv(G, rcond=1e-3)
    K = R.A_fix + R.A.sum(0); lam, Q = np.linalg.eigh(K); lam = np.clip(lam, 1e-9, None)
    femf = np.sqrt(lam) / (2 * np.pi)

    matched_fem = set(k for (r, k, mac) in pairs)
    # build mode list: matched (measured shape) + unmatched in-band FEM modes
    modes = []   # (shape_vec(74,), wn_rad, zeta, src)
    for (r, k, mac) in pairs:
        psi = Gpinv @ ms[:, r]
        zeta = damp[r] + float(rf.measured_zeta_w(mfr[r]))
        modes.append({"psi_meas": psi / (np.linalg.norm(psi) + 1e-30), "psi_fem": Q[:, k],
                      "wn": mfr[r] * 2 * np.pi, "wn_fem": np.sqrt(lam[k]),
                      "zeta": zeta, "zeta_fem": rf.ZETA_NOM + float(rf.measured_zeta_w(femf[k])), "matched": True})
    for k in range(len(lam)):
        if k in matched_fem:
            continue
        if rf.BAND[0] <= femf[k] <= rf.BAND[1]:
            modes.append({"psi_meas": Q[:, k], "psi_fem": Q[:, k], "wn": np.sqrt(lam[k]),
                          "wn_fem": np.sqrt(lam[k]), "zeta": rf.ZETA_NOM + float(rf.measured_zeta_w(femf[k])),
                          "zeta_fem": rf.ZETA_NOM + float(rf.measured_zeta_w(femf[k])), "matched": False})
    nM = len(modes)

    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    hard_ho = np.array([1 if d in HARD else 0 for d in ho_daqs])

    def basis(rows, use_meas):
        cols = []
        for m in modes:
            psi = m["psi_meas"] if use_meas else m["psi_fem"]
            wn = m["wn"] if use_meas else m["wn_fem"]
            zeta = m["zeta"] if use_meas else m["zeta_fem"]
            sc = rows @ psi; dc = ch.drive_row @ psi
            denom = (1 + 1j * 2 * zeta) * wn ** 2 - w ** 2
            cols.append((-(w ** 2)[:, None]) * (sc[None, :] * dc) / denom[:, None])   # (Nf, Ns)
        return np.stack(cols, -1)                                                     # (Nf, Ns, nM)

    H_obs = np.array([meas["H"][didx[d]][fb] for d in obs_daqs]).T
    H_ho_t = np.array([meas["H"][didx[d]][fb] for d in ho_daqs]).T
    Wq = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T

    def fit_predict(use_meas):
        Mo = basis(ch.rows[obs_pos], use_meas); Mh = basis(ch.rows[ho_pos], use_meas)
        A = Mo.reshape(-1, nM); b = H_obs.reshape(-1); sw = np.sqrt(Wq.reshape(-1))
        Aw = A * sw[:, None]; bw = b * sw
        AhA = Aw.conj().T @ Aw; reg = ridge * np.real(np.trace(AhA)) / nM
        a = np.linalg.solve(AhA + reg * np.eye(nM), Aw.conj().T @ bw)
        Hop = Mo @ a; Hhp = Mh @ a
        def perr(p, t): return 20 * np.log10(np.abs(p).max(0) / np.abs(t).max(0))
        eo = perr(Hop, H_obs); eh = perr(Hhp, H_ho_t)
        return eo, eh
    eo_fem, eh_fem = fit_predict(False)
    eo_hyb, eh_hyb = fit_predict(True)

    def st(e): return {"median_abs_db": float(np.median(np.abs(e))), "sigma_log": float(np.std(e * np.log(10) / 20))}
    rec = {"deliverable": "hybrid (measured-shape) vs all-FEM modal model, held-out QOI (D15 method-vs-data test)",
           "split_seed": seed, "n_modes_total": nM, "n_measured_shape_modes": len(pairs),
           "n_observed": len(obs_pos), "n_heldout": len(ho_pos), "n_ho_hard": int(hard_ho.sum()), "ridge": ridge,
           "FEM_ALL": {"in_sample": st(eo_fem), "heldout": st(eh_fem),
                       "heldout_rest": st(eh_fem[hard_ho == 0]),
                       "heldout_hard": st(eh_fem[hard_ho == 1]) if hard_ho.sum() else None},
           "HYBRID_measured": {"in_sample": st(eo_hyb), "heldout": st(eh_hyb),
                               "heldout_rest": st(eh_hyb[hard_ho == 0]),
                               "heldout_hard": st(eh_hyb[hard_ho == 1]) if hard_ho.sum() else None},
           "runtime_s": time.time() - t0}
    if write:
        OUT.mkdir(exist_ok=True)
        (OUT / f"hybrid_shape_qoi_seed{seed:02d}.json").write_text(json.dumps(rec, indent=2))
    print(f"seed {seed}: {nM} modes ({len(pairs)} with measured shape); obs {len(obs_pos)} / ho {len(ho_pos)}")
    for tag in ("FEM_ALL", "HYBRID_measured"):
        r = rec[tag]
        print(f"  {tag:16s} in-sample {r['in_sample']['median_abs_db']:5.1f}dB | held-out {r['heldout']['median_abs_db']:5.1f}dB "
              f"(sigma_log {r['heldout']['sigma_log']:.2f}, REST {r['heldout_rest']['median_abs_db']:.1f}dB)")
    print(f"  runtime {rec['runtime_s']:.1f}s")
    return rec


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(seed=seed)
