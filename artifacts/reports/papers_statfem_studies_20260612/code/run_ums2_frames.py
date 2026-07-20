"""Study G GIF frames on the CONVERGING UMS-FEM model (run_ums2).
Sequential data accretion (LDV-scan order) + bandwidth extension. Each frame = a reduced 2-chain
run (R-hat recorded + shown per frame). Resumable. Outputs -> ../out/frames2/"""
from __future__ import annotations
import os, numpy as np, jax.numpy as jnp
import run_ums2 as R2, run_ums as R

OUTF = os.path.join(R2.OUT, "frames2"); os.makedirs(OUTF, exist_ok=True)
def raster_key(n): return (n // R.U.NY, n % R.U.NY)
obs_sorted = [R.obs_nodes[0]] + sorted(R.obs_nodes[1:], key=raster_key)
SCAN_SIZES = [2, 4, 6, 9, 12, 15]
BAND_MAXES = [25.0, 35.0, 45.0, 60.0]

def frame_run(tag, sub_nodes, fmax):
    path = os.path.join(OUTF, f"{tag}.npz")
    if os.path.exists(path):
        print("skip", tag); return
    fmask = R.F_INF <= fmax + 1e-9
    freqs = R.F_INF[fmask]
    cols = [R.scan.index(n) for n in sub_nodes]
    data = R.data_inf_all[fmask][:, cols]
    res, fl = R2.run_nuts(False, 600, 250, 2, tag,
                          data=jnp.array(data), freqs=jnp.array(freqs),
                          obs_local=jnp.array(cols), coords=R.xy[sub_nodes])
    # predictive at the 5 held-out nodes (full band, conditioned on this subset)
    P = predictive_subset(fl, freqs, cols, data)
    lo, md, hi = np.percentile(P["show"], [2.5, 50, 97.5], 0)
    qA = np.percentile(P["qoiA"], [2.5, 50, 97.5], 0)
    qB = np.percentile(P["qoiB"], [2.5, 50, 97.5], 0)
    np.savez(path, lo=lo, med=md, hi=hi, qA=qA, qB=qB, max_rhat=res["max_rhat"],
             divergences=res["divergences"], n_pts=len(sub_nodes), fmax=fmax,
             runtime_s=res["runtime_s"], sub_nodes=sub_nodes)
    print("frame", tag, "rhat %.2f div %d %.0fs" % (res["max_rhat"], res["divergences"], res["runtime_s"]))


def predictive_subset(flat, obs_freqs, obs_cols, data_obs):
    """Predictive at the 5 held-out nodes over the FULL band, discrepancy conditioned on this subset."""
    import ums_model as U
    rng = np.random.default_rng(11); S = 120
    idx = rng.choice(flat["s_g"].shape[0], size=min(S, flat["s_g"].shape[0]), replace=False)
    co = R.xy[obs_cols]; ch = R2.coords_hold
    hloc = [R.scan.index(n) for n in R.hold_nodes]; sloc = R.hold_nodes.index(R.SHOWCASE)
    nf = len(R.F_INF); bm = (R.F_INF >= R.BAND[0]) & (R.F_INF <= R.BAND[1])
    fg = np.arange(R.F_INF[0], R.F_INF[-1] + 1e-9, 0.5)
    ofg_idx = [int(np.argmin(np.abs(obs_freqs - f))) for f in fg if f <= obs_freqs[-1] + 1e-9]
    ofg = obs_freqs[ofg_idx]
    show = np.zeros((len(idx), nf)); qoiA = np.zeros((len(idx), 5)); qoiB = np.zeros((len(idx), 5))
    for k, i in enumerate(idx):
        lam, c, a_m, fm, zeta = R2.rebuild(flat, i)
        psi = c @ R2.PhiS.T
        Hh = U.residue_frf_numpy(lam, psi[:, hloc], c @ R2.PhiD, a_m, R.F_INF)
        Hobs = U.residue_frf_numpy(lam, psi[:, obs_cols], c @ R2.PhiD, a_m, ofg)
        r_c = (data_obs[ofg_idx] - Hobs) / (np.abs(Hobs) + R2.FLOOR_EST)
        Wo = np.real(r_c); To = np.imag(r_c)
        lz = flat["len_z"][i]; lf = flat["len_f"][i]; sw_ = flat["sig_w"][i]; st_ = flat["sig_th"][i]
        dzo = np.sqrt(((co[:, None] - co[None]) ** 2).sum(-1)); dzoh = np.sqrt(((co[:, None] - ch[None]) ** 2).sum(-1)); dzh = np.sqrt(((ch[:, None] - ch[None]) ** 2).sum(-1))
        Rz = np.exp(-dzo / lz) + 1e-8 * np.eye(len(co)); Kz = np.linalg.solve(Rz, np.exp(-dzoh / lz)); Qz = np.exp(-dzoh / lz).T @ Kz
        dfo = np.abs(ofg[:, None] - ofg[None]); Rf = np.exp(-dfo / lf) + 1e-8 * np.eye(len(ofg)); Qf = np.exp(-dfo / lf) @ np.linalg.solve(Rf, np.exp(-dfo / lf))
        covK = np.kron(np.exp(-dfo / lf), np.exp(-dzh / lz)) - np.kron(Qf, Qz); covK = (covK + covK.T) / 2 + 1e-8 * np.eye(covK.shape[0]); Lc = np.linalg.cholesky(covK)
        mw = (Wo @ Kz); mt = (To @ Kz)
        g1 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(len(ofg), 5); g2 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(len(ofg), 5)
        fwg = mw + sw_ * g1; ftg = mt + st_ * g2
        fw = np.stack([np.interp(R.F_INF, ofg, fwg[:, h]) for h in range(5)], 1)
        ft = np.stack([np.interp(R.F_INF, ofg, ftg[:, h]) for h in range(5)], 1)
        Hp = Hh + (np.abs(Hh) + R2.FLOOR_EST) * (fw + 1j * ft); mag = np.abs(Hp)
        show[k] = mag[:, sloc]; qoiA[k] = mag[bm].max(0); qoiB[k] = np.sqrt((mag[bm] ** 2).mean(0))
    return dict(show=show, qoiA=qoiA, qoiB=qoiB)


if __name__ == "__main__":
    for k in SCAN_SIZES:
        frame_run(f"scan_{k:02d}", obs_sorted[:k], R.BAND[1])
    for fm in BAND_MAXES:
        frame_run(f"band_{int(fm):03d}", obs_sorted, fm)
    print("frames2 done ->", OUTF)
