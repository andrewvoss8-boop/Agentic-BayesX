#!/usr/bin/env python3
"""Phase B — does PER-MODE measured damping tighten the held-out-sensor QOI CI?

The current L5 held-out QOI (heldout_qoi.py) predicts |H| with a UNIFORM zeta=1%, while the measured single-impact
FRF carries (a) the structure's per-mode modal damping zeta_struct (NASA modal test, measured_modes.npz['damp'],
0.06-1.05%) and (b) the exponential-window artifact zeta_w(f)=1/(2 pi f tau) (0.23-1.22% over the band). That
per-mode mismatch (peak amplitude ~ 1/zeta -> factor ~0.65x..2.4x across modes) is currently dumped into the ~x3
QOI-discrepancy that sets the CI width. Here we predict with the CORRECT per-mode damping and ask: does the
observed-channel amplitude residual sigma_QOI (the CI width driver) SHRINK while coverage holds?

Three arms on the SAME L5 theta posterior (calibration is frequency-based, damping-independent):
  ARM0  uniform zeta=1%            (reproduce current L5 baseline)
  ARM1  uniform zeta=1% + window   (isolate the window correction)
  ARM2  per-mode zeta_struct + window  (full damping correction)
Mode index <-> measured zeta mapped at the FEM MAP modes (stable for small theta variation; caveat noted).
Output: out/dampcorr_qoi_seed<seed>.json.  NOTE: we predict the MEASURED (windowed) held-out quantity, so the
window is part of the apples-to-apples prediction; the structural (de-windowed) QOI is a separate flight quantity.
"""
from __future__ import annotations
import json, sys, time
from types import SimpleNamespace
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq
import score as SC

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
ZETA_NOM = rf.ZETA_NOM


def fem_logmag_batch_permode(R, freqs, theta_batch, resp_rows, drive_row, eta_struct, tau, chunk=200):
    """Batched log|accelerance g/lbf| with PER-MODE total loss factor eta_k = eta_struct_k + 2*zeta_w(f_k(theta)),
    zeta_w(f)=1/(2 pi f tau) (tau=None -> no window). eta_struct: (r,) = 2*zeta_struct per mode INDEX."""
    theta_batch = np.atleast_2d(theta_batch); M = theta_batch.shape[0]
    w = 2 * np.pi * np.asarray(freqs); Nf = len(freqs); Ns = resp_rows.shape[0]
    out = np.empty((M, Nf, Ns))
    for s0 in range(0, M, chunk):
        th = theta_batch[s0:s0 + chunk]
        K = R.A_fix[None] + np.einsum("cg,gij->cij", th, R.A)
        lam, Q = np.linalg.eigh(K); lam = np.clip(lam, 1e-9, None)         # (c,r)
        fk = np.sqrt(lam) / (2 * np.pi)                                    # (c,r)
        zw = (1.0 / (2 * np.pi * fk * tau)) if tau else 0.0                # (c,r) window damping
        eta_tot = eta_struct[None, :] + 2.0 * zw                          # (c,r)
        Us = np.einsum("sm,cmk->csk", resp_rows, Q)
        ud = np.einsum("m,cmk->ck", drive_row, Q)
        g = (1.0 + 1j * eta_tot[:, None, :]) * lam[:, None, :] - (w ** 2)[None, :, None]  # (c,Nf,r)
        H = -(w ** 2)[None, :, None] * np.einsum("csk,ck,cfk->cfs",
                                                 Us.astype(complex), ud.astype(complex), 1.0 / g)
        out[s0:s0 + chunk] = np.log(np.abs(H) / rf.G_IN_S2)
    return out


def build_zeta_struct(R, meas, ch):
    """Per-FEM-mode structural zeta from the matched NASA modal-test damping (measured_modes.npz). Unmatched
    FEM modes get ZETA_NOM. Mapping done at theta=1 (mf.match)."""
    r = R.A.shape[1]
    meas_f, _ = mf.extract_measured_modes(meas, ch)
    pairs, _ = mf.match(R, meas_f)
    mm = np.load(WS / "data" / "measured_modes.npz", allow_pickle=True)
    mm_f, mm_d = mm["freqs"], mm["damp"] / 100.0       # damp is in PERCENT
    zeta = np.full(r, ZETA_NOM)
    used = []
    for fem_idx, mhz in pairs:
        j = int(np.argmin(np.abs(mm_f - mhz)))
        zeta[fem_idx] = float(mm_d[j]); used.append((int(fem_idx), round(mhz, 1), float(mm_d[j])))
    return zeta, used


def run(seed=0, obs_frac=0.6, n_draws=400, warmup=1000, samples=1000, chains=4, write=True):
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    tau = -(rf.PROC["N"] - 1) / (rf.FS * np.log(rf.PROC["exp_end"]))

    zeta_struct, used = build_zeta_struct(R, meas, SimpleNamespace(daq=ch.daq))
    eta_uniform = np.full(R.A.shape[1], 2.0 * ZETA_NOM)
    eta_struct = 2.0 * zeta_struct

    # split + calibrate theta (identical to heldout_qoi)
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    obs_mode_idx = np.array([p[0] for p in pairs]); obs_w_hz = np.array([p[1] for p in pairs])
    theta_post, sigw2, cdiag = mf.calibrate_modal(R, obs_mode_idx, obs_w_hz,
                                                  seed=20260617, warmup=warmup, samples=samples, chains=chains)
    Nd = theta_post.shape[0]; sub = np.linspace(0, Nd - 1, min(Nd, n_draws)).astype(int)
    thsub = theta_post[sub]

    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]
    all_rows = np.vstack([obs_rows, ho_rows]); n_o = len(obs_pos); n_ho = len(ho_pos)
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).T
    wq_obs = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T
    wflat = wq_obs.ravel()
    peak_tru_ob = np.array([hq.SC_qoi_peak(np.exp(tru_obs[:, c])) for c in range(n_o)])
    band_tru_ob = np.array([hq.SC_qoi_band(np.exp(tru_obs[:, c]), freqs) for c in range(n_o)])
    peak_tru_ho = np.array([hq.SC_qoi_peak(np.exp(tru_ho[:, c])) for c in range(n_ho)])
    band_tru_ho = np.array([hq.SC_qoi_band(np.exp(tru_ho[:, c]), freqs) for c in range(n_ho)])

    def one_arm(eta_struct_vec, use_window):
        lm = fem_logmag_batch_permode(R, freqs, thsub, all_rows, ch.drive_row,
                                      eta_struct_vec, tau if use_window else None)
        lm_obs = lm[:, :, :n_o]; lm_ho = lm[:, :, n_o:]
        peak_ho = np.zeros((len(sub), n_ho)); band_ho = np.zeros((len(sub), n_ho))
        peak_ob = np.zeros((len(sub), n_o)); band_ob = np.zeros((len(sub), n_o)); c_draws = np.zeros(len(sub))
        for j in range(len(sub)):
            c = hq.wmedian((tru_obs - lm_obs[j]).ravel(), wflat); c_draws[j] = c
            po = np.exp(lm_obs[j] + c); ph = np.exp(lm_ho[j] + c)
            for k in range(n_o):
                peak_ob[j, k] = hq.SC_qoi_peak(po[:, k]); band_ob[j, k] = hq.SC_qoi_band(po[:, k], freqs)
            for k in range(n_ho):
                peak_ho[j, k] = hq.SC_qoi_peak(ph[:, k]); band_ho[j, k] = hq.SC_qoi_band(ph[:, k], freqs)

        def qoi_disc(pred_obs, tru):
            rlog = np.log(np.median(pred_obs, axis=0) + 1e-300) - np.log(tru + 1e-300)
            return float(np.std(rlog)), float(np.median(rlog))
        sig_pk, bias_pk = qoi_disc(peak_ob, peak_tru_ob)
        sig_bd, bias_bd = qoi_disc(band_ob, band_tru_ob)
        drng = np.random.default_rng(seed + 2)
        peak_ho_d = peak_ho * np.exp(drng.normal(0.0, sig_pk, peak_ho.shape))
        band_ho_d = band_ho * np.exp(drng.normal(0.0, sig_bd, band_ho.shape))

        def score_block(pkd, bdd):
            pk = [SC.score_qoi(pkd[:, k], peak_tru_ho[k]) for k in range(n_ho)]
            bd = [SC.score_qoi(bdd[:, k], band_tru_ho[k]) for k in range(n_ho)]
            return {"peak": hq.aggregate(pk), "band": hq.aggregate(bd)}
        return {"qoi_discrepancy_logscale": {"peak": {"sigma": sig_pk, "bias": bias_pk},
                                             "band": {"sigma": sig_bd, "bias": bias_bd}},
                "gain_c_med": float(np.median(c_draws)),
                "scores_theta_only": score_block(peak_ho, band_ho),
                "scores_theta_plus_qoi_discrepancy": score_block(peak_ho_d, band_ho_d)}

    arms = {"ARM0_uniform1pct": one_arm(eta_uniform, False),
            "ARM1_uniform1pct_plus_window": one_arm(eta_uniform, True),
            "ARM2_permode_struct_plus_window": one_arm(eta_struct, True)}

    rec = {"deliverable": "Phase-B per-mode-damping held-out QOI (does correct damping tighten the CI?)",
           "split_seed": seed, "obs_frac": obs_frac, "n_observed": n_o, "n_heldout": n_ho,
           "tau_s": float(tau), "n_modes_with_measured_zeta": len(used),
           "zeta_struct_used_femidx_hz_zeta": used,
           "calibration_converged": bool(cdiag["converged"]), "calib_diag": cdiag,
           "arms": arms, "runtime_s": time.time() - t0}
    if write:
        OUT.mkdir(exist_ok=True)
        (OUT / f"dampcorr_qoi_seed{seed:02d}.json").write_text(json.dumps(rec, indent=2))
    print(f"seed {seed}: obs {n_o}/ho {n_ho}; calib conv={cdiag['converged']} | {len(used)} modes w/ measured zeta")
    for a, v in arms.items():
        sp = v["qoi_discrepancy_logscale"]["peak"]["sigma"]
        ti = v["scores_theta_plus_qoi_discrepancy"]["peak"]
        print(f"  {a:34s} sigma_QOI_peak={sp:.3f}  PEAK cover={ti['coverage_frac']:.2f} "
              f"interval={ti['interval_score_mean']:.4g} width_db={ti.get('mean_width_db',0):.1f}")
    print(f"  runtime {rec['runtime_s']:.0f}s")
    return rec


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(seed=seed)
