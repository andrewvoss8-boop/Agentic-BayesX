"""Q1 gap closures, RUN (not argued): #2 damping inference (does fitted damping help the band-GRMS QOI, or is a
global scale just confounded with the gain?) and #3/#4 a JOINT TOPOLOGY alternative (soften/release the bolted
joint bush_801 -> does it improve held-out amplitude skill?). All scored as CRPS-skill vs climatology (the right
bar) on held-out channels, reusing ONE L5 theta calibration. Output: out/gap_closure_seed<seed>.json.
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
import dampcorr_qoi as dc
import cardE_richmodel as rm
import score as SC

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
HARD = {4, 27, 38, 40, 52, 69, 92, 98}


def topo_logmag(R, freqs, theta_batch, resp_rows, drive_row, tau, B801, soften, theta_joint_idx=5):
    """Forward with bolted joint bush_801 SOFTENED by `soften` (0=released, 1=nominal): K = A_fix + sum theta_g A_g
    - theta_joints*(1-soften)*B801. (joints is GNAMES index 5.) Uniform zeta=1% + window."""
    theta_batch = np.atleast_2d(theta_batch); M = theta_batch.shape[0]
    w = 2 * np.pi * np.asarray(freqs); eta = 2.0 * rf.ZETA_NOM
    out = np.empty((M, len(freqs), resp_rows.shape[0]))
    for j in range(M):
        th = theta_batch[j]
        K = R.A_fix + np.einsum("g,gij->ij", th, R.A) - th[theta_joint_idx] * (1 - soften) * B801
        lam, Q = np.linalg.eigh(K); lam = np.clip(lam, 1e-9, None)
        fk = np.sqrt(lam) / (2 * np.pi); zw = 1.0 / (2 * np.pi * fk * tau)
        et = eta + 2 * zw
        Us = resp_rows @ Q; ud = drive_row @ Q
        g = (1 + 1j * et[None, :]) * lam[None, :] - (w ** 2)[:, None]
        H = -(w ** 2)[:, None] * np.einsum("sk,k,fk->fs", Us.astype(complex), ud.astype(complex), 1.0 / g)
        out[j] = np.log(np.abs(H) / rf.G_IN_S2)
    return out


def run(seed=0, obs_frac=0.6, n_draws=300, warmup=1000, samples=1000, chains=4, write=True):
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    tau = -(rf.PROC["N"] - 1) / (rf.FS * np.log(rf.PROC["exp_end"]))
    pp = rm.build_perpid(); B801 = rm.block_of(pp, "bush_801")
    eta = np.full(R.A.shape[1], 2.0 * rf.ZETA_NOM)

    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm))); obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs)); pairs, _ = mf.match(R, meas_f)
    theta_post, _, cdiag = mf.calibrate_modal(R, np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs]),
                                              seed=20260617, warmup=warmup, samples=samples, chains=chains)
    sub = np.linspace(0, theta_post.shape[0] - 1, min(theta_post.shape[0], n_draws)).astype(int); thsub = theta_post[sub]
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]; allr = np.vstack([obs_rows, ho_rows]); n_o = len(obs_pos)
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).T
    wflat = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T.ravel()
    hard_ho = np.array([1 if d in HARD else 0 for d in ho_daqs])

    def qoi_arm(lm, qfun):
        ob = np.zeros((len(sub), n_o)); ho = np.zeros((len(sub), len(ho_pos)))
        for j in range(len(sub)):
            c = hq.wmedian((tru_obs - lm[j, :, :n_o]).ravel(), wflat)
            po = np.exp(lm[j, :, :n_o] + c); ph = np.exp(lm[j, :, n_o:] + c)
            for k in range(n_o): ob[j, k] = qfun(po[:, k])
            for k in range(len(ho_pos)): ho[j, k] = qfun(ph[:, k])
        tru_ob = np.array([qfun(np.exp(tru_obs[:, k])) for k in range(n_o)])
        tru_h = np.array([qfun(np.exp(tru_ho[:, k])) for k in range(len(ho_pos))])
        sig = float(np.std(np.log(np.median(ob, 0) + 1e-300) - np.log(tru_ob + 1e-300)))
        dd = np.random.default_rng(seed + 5).normal(0, sig, ho.shape)
        draws = ho * np.exp(dd)
        nh = hard_ho == 0
        ct = np.mean([SC.score_qoi(draws[:, k], tru_h[k])["crps"] for k in np.where(nh)[0]])
        cc = np.mean([SC.score_qoi(tru_ob, tru_h[k])["crps"] for k in np.where(nh)[0]])
        cov = np.mean([SC.score_qoi(draws[:, k], tru_h[k])["covered"] for k in np.where(nh)[0]])
        return {"nonhard_crps_skill_vs_clim": float(1 - ct / cc), "nonhard_coverage": float(cov), "sigma_log": sig}

    peak = rf.core.qoi_peak; band = lambda h: rf.core.qoi_band(h, freqs)
    lm_base = dc.fem_logmag_batch_permode(R, freqs, thsub, allr, ch.drive_row, eta, tau)

    arms = {}
    # #2 damping: baseline band + global zeta-scale variants (show global scale ~ gain-confounded -> band skill unchanged)
    arms["baseline_peak"] = qoi_arm(lm_base, peak)
    arms["baseline_band"] = qoi_arm(lm_base, band)
    for s in (0.5, 2.0):
        eta_s = np.full(R.A.shape[1], 2.0 * rf.ZETA_NOM * s)
        lm_s = dc.fem_logmag_batch_permode(R, freqs, thsub, allr, ch.drive_row, eta_s, tau)
        arms[f"band_zeta_x{s}"] = qoi_arm(lm_s, band)
    # #3/#4 topology: bolted joint bush_801 softened
    for soften in (0.3, 0.0):
        lm_t = topo_logmag(R, freqs, thsub, allr, ch.drive_row, tau, B801, soften)
        arms[f"topo_joint_soften{soften}_peak"] = qoi_arm(lm_t, peak)

    rec = {"deliverable": "Q1 gap closures RUN: damping inference (band-GRMS) + joint topology alternative",
           "split_seed": seed, "calib_converged": bool(cdiag["converged"]), "n_heldout_nonhard": int((hard_ho == 0).sum()),
           "arms": arms, "runtime_s": time.time() - t0}
    if write:
        OUT.mkdir(exist_ok=True); (OUT / f"gap_closure_seed{seed:02d}.json").write_text(json.dumps(rec, indent=2))
    print(f"seed {seed} (calib {cdiag['converged']}); NON-HARD CRPS-skill vs climatology (<0 = no value):")
    for a, v in arms.items():
        print(f"  {a:30s} skill {v['nonhard_crps_skill_vs_clim']:+.2f}  cover {v['nonhard_coverage']:.2f}  sigma {v['sigma_log']:.2f}")
    print(f"  runtime {rec['runtime_s']:.0f}s")
    return rec


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(seed=seed)
