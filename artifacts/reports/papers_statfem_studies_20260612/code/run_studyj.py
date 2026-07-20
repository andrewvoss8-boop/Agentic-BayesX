"""Study J — REAL-PANEL UMS calibration (vision §7 centerpiece; first real-data application).

Physics = the Abaqus FEA modal model (shapes U3 + eigenfrequencies); the LDV mobility H1 is single-
reference (impact at top-right node, 25 response points). Architecture (the Study G lesson):
  * mode SHAPES are FIXED from FEA, interpolated to the 25 LDV points (they generalize spatially).
  * CALIBRATE per-mode frequency scales (pinned by data peaks) + a global damping + a global amplitude.
  * Schneider smooth correlated complex discrepancy on the real mobility (8-60 Hz, good-coherence band).
  * TRUST GATE = hold out 5 of 25 LDV points; predict their mobility + peak-QOI; coverage.
Mobility residue (proportional light damping, mass-normalized FEA modes):
  H_pq(w) = Σ_m φ_p,m φ_q,m / (ω_m² − ω² + 2i ζ_m ω_m ω);  Y_pq = iω · H_pq · g_amp
Outputs -> ../out/studyj_*.  Env J_PROBE=1 -> 2-chain probe.
"""
from __future__ import annotations
import json, math, os, time
import numpy as np
import scipy.io as sio
from scipy.interpolate import griddata
import jax, jax.numpy as jnp
from jax.scipy.linalg import solve_triangular
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS, init_to_value
from numpyro.diagnostics import summary
import ums_model as U

jax.config.update("jax_enable_x64", True); numpyro.set_host_device_count(4)
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "out"); REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
BASE = os.path.join(REPO, "Suspended panel modal testing", "LDV test results", "mat files")
RNG = np.random.default_rng(73)

# ---------------- real data + FEA basis ----------------
H1 = sio.loadmat(os.path.join(BASE, "H1.mat"))["H1"]              # [25,3200] mobility (m/s)/N
FR = sio.loadmat(os.path.join(BASE, "freq.mat"))["freq"].ravel()
Z = np.load(os.path.join(OUT, "study_c2_ritz.npz"))
PTS = Z["pts"]; xyF = Z["fea_xy"]; U3 = Z["fea_u3"]; FEAF = Z["fea_freqs"]
DRIVE = int(Z["drive_row"])
# calibration band (good coherence; below the dense high-mode region)
BAND = (8.0, 60.0); dec = 4
bmask = (FR >= BAND[0]) & (FR <= BAND[1])
FB = FR[bmask][::dec]; YOBS = H1[:, bmask][:, ::dec]              # [25, nf]
nf = len(FB)
# FEA modes used: 5-70 Hz (in-band + tails)
midx = np.where((FEAF >= 5) & (FEAF <= 70))[0]
fFEA = FEAF[midx]; M = len(midx)
# shapes at the 25 LDV points (interp + nearest fallback); mass-normalized FEA
Phi = np.zeros((25, M))
for j, mi in enumerate(midx):
    v = griddata(xyF, U3[mi], PTS, method="linear")
    vn = griddata(xyF, U3[mi], PTS, method="nearest")
    v[np.isnan(v)] = vn[np.isnan(v)]
    Phi[:, j] = v
# zeta base (light); global amplitude init from data/FEA magnitude ratio at first peak
PHI_d = Phi[DRIVE]                                                # [M] shape at drive
# held-out split: 5 spatial points (corners+centre-ish), spread
order = np.argsort(PTS[:, 0] + 1.3 * PTS[:, 1])
HOLD = sorted([int(order[2]), int(order[8]), int(order[12]), int(order[18]), int(order[22])])
HOLD = [h for h in HOLD if h != DRIVE][:5]
OBSP = [p for p in range(25) if p not in HOLD]
co = PTS[OBSP]; ch = PTS[HOLD]
KAP = float(np.quantile(np.abs(YOBS[OBSP]), 0.02))

Phi_j = jnp.array(Phi); PHId_j = jnp.array(PHI_d); fFEA_j = jnp.array(fFEA)
FBj = jnp.array(FB); Yobs_j = jnp.array(YOBS[OBSP]); OBS_j = jnp.array(OBSP)
DF = float(FB[1] - FB[0])

def mvn_sep(Wf, sigma, rho, Lz):
    e0 = Wf[0:1]; rest = (Wf[1:] - rho[:, None] * Wf[:-1]) / jnp.sqrt(1 - rho ** 2)[:, None]
    Ef = jnp.concatenate([e0, rest], 0); E = solve_triangular(Lz, Ef.T, lower=True).T
    n = Wf.size; nff, npp = Wf.shape
    quad = jnp.sum(E * E) / sigma ** 2
    logdet = 2 * n * jnp.log(sigma) + npp * jnp.sum(jnp.log(1 - rho ** 2)) + nff * 2 * jnp.sum(jnp.log(jnp.diag(Lz)))
    return -0.5 * (n * jnp.log(2 * jnp.pi) + logdet + quad)

def exp_chol(coords, ell):
    d = jnp.sqrt(jnp.sum((coords[:, None, :] - coords[None, :, :]) ** 2, -1))
    return jnp.linalg.cholesky(jnp.exp(-d / ell) + 1e-8 * jnp.eye(coords.shape[0]))

def mobility(sm, gz, gamp, pts_idx, freqs):
    """Y[p,w] for response points pts_idx (indices into 25), fixed drive."""
    fm = sm * fFEA_j; wm = 2 * jnp.pi * fm
    zeta = jnp.clip(gz * 0.01, 1e-3, 0.1)                          # global damping ~1%*gz
    w = 2 * jnp.pi * freqs
    denom = wm[None, :] ** 2 - w[:, None] ** 2 + 2j * zeta * wm[None, :] * w[:, None]   # [nf,M]
    Pp = Phi_j[pts_idx]                                            # [P,M]
    num = Pp * PHId_j[None, :]                                     # [P,M]
    Hr = jnp.einsum("fm,pm->fp", 1.0 / denom, num)                # receptance [nf,P]
    return (1j * w)[:, None] * Hr * gamp

def model():
    sf = numpyro.sample("sf", dist.LogNormal(0.0, 0.05))   # ONE global freq scale (sqrt(k_eff/k_nom)); discrepancy handles per-mode residuals
    sm = sf * jnp.ones(M)
    gz = numpyro.sample("gz", dist.LogNormal(0.0, 0.25))   # damping; amplitude FIXED (D30: gamp~gz ridge in peak height)
    gamp = jnp.exp(LGAMP0)
    sw = numpyro.sample("sig_w", dist.LogNormal(math.log(0.2), 0.6))
    sth = numpyro.sample("sig_th", dist.LogNormal(math.log(0.3), 0.6))
    lf = numpyro.sample("len_f", dist.LogNormal(math.log(4.0), 0.5))
    lz = numpyro.sample("len_z", dist.LogNormal(math.log(0.3), 0.5))
    Y = mobility(sm, gz, gamp, OBS_j, FBj)                         # [nf, P]
    scale = jnp.abs(Y) + KAP
    r = (Yobs_j.T - Y) / scale                                    # [nf,P]
    rho = jnp.exp(-DF / lf) * jnp.ones(nf - 1)
    Lz = exp_chol(jnp.array(co), lz)
    numpyro.factor("lw", mvn_sep(jnp.real(r), sw, rho, Lz))
    numpyro.factor("lt", mvn_sep(jnp.imag(r), sth, rho, Lz))

# amplitude init: match data peak to FEA-model peak magnitude
def amp_init():
    Y0 = np.array(mobility(jnp.ones(M), jnp.array(1.0), jnp.array(1.0), OBS_j, FBj))
    return float(np.log(np.median(np.abs(YOBS[OBSP]).max(0)) / (np.median(np.abs(Y0).max(0)) + 1e-30)))
LGAMP0 = amp_init()
INIT = dict(sf=jnp.array(1.0), gz=jnp.array(1.0),
            sig_w=jnp.array(0.3), sig_th=jnp.array(0.3), len_f=jnp.array(4.0), len_z=jnp.array(0.3))

def run(nw, ns, nchain):
    t0 = time.time()
    mc = MCMC(NUTS(model, target_accept_prob=0.9, max_tree_depth=10, step_size=1e-3,
                   init_strategy=init_to_value(values=INIT)),
              num_warmup=nw, num_samples=ns, num_chains=nchain, chain_method="sequential",
              progress_bar=False)
    mc.run(jax.random.PRNGKey(1), extra_fields=("diverging",))
    s = mc.get_samples(group_by_chain=True); div = int(jnp.sum(mc.get_extra_fields()["diverging"]))
    st = summary(s, group_by_chain=True)
    mr = max(float(np.nanmax(v["r_hat"])) for v in st.values())
    me = min(float(np.nanmin(v["n_eff"])) for v in st.values())
    flat = {k: np.array(v).reshape(-1, *v.shape[2:]) for k, v in s.items()}
    res = dict(max_rhat=mr, min_ess=me, divergences=div, div_frac=div / (nchain * ns),
               runtime_s=time.time() - t0)
    print("Study J", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()})
    return res, flat

def predict(flat, S, rng):
    """Held-out mobility + peak-QOI at the 5 never-fit points, discrepancy conditioned on observed."""
    idx = rng.choice(flat["sf"].shape[0], size=min(S, flat["sf"].shape[0]), replace=False)
    hold_j = jnp.array(HOLD); obs_j = jnp.array(OBSP)
    nfb = len(FB); magpred = np.zeros((len(idx), 5, nfb)); qoi = np.zeros((len(idx), 5))
    data_h = np.abs(YOBS[HOLD])                                   # truth held-out mobility
    for k, i in enumerate(idx):
        sf = flat["sf"][i]; gz = flat["gz"][i]; gamp = math.exp(LGAMP0)
        sm = sf * jnp.ones(M)
        Yh = np.array(mobility(sm, jnp.array(gz), jnp.array(gamp), hold_j, FBj))   # [nf,5]
        Yo = np.array(mobility(sm, jnp.array(gz), jnp.array(gamp), obs_j, FBj))    # [nf,P]
        r = (YOBS[OBSP].T - Yo) / (np.abs(Yo) + KAP)
        Wo = np.real(r); To = np.imag(r)
        lz = flat["len_z"][i]; lf = flat["len_f"][i]; sw_ = flat["sig_w"][i]; st_ = flat["sig_th"][i]
        dzo = np.sqrt(((co[:, None] - co[None]) ** 2).sum(-1)); dzoh = np.sqrt(((co[:, None] - ch[None]) ** 2).sum(-1)); dzh = np.sqrt(((ch[:, None] - ch[None]) ** 2).sum(-1))
        Rz = np.exp(-dzo / lz) + 1e-8 * np.eye(len(co)); Kz = np.linalg.solve(Rz, np.exp(-dzoh / lz)); Qz = np.exp(-dzoh / lz).T @ Kz
        dfo = np.abs(FB[:, None] - FB[None]); Rf = np.exp(-dfo / lf) + 1e-8 * np.eye(nfb); Qf = np.exp(-dfo / lf) @ np.linalg.solve(Rf, np.exp(-dfo / lf))
        covK = np.kron(np.exp(-dfo / lf), np.exp(-dzh / lz)) - np.kron(Qf, Qz)
        covK = (covK + covK.T) / 2 + 1e-8 * np.eye(covK.shape[0]); Lc = np.linalg.cholesky(covK)
        mw = Wo @ Kz; mt = To @ Kz
        g1 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(nfb, 5); g2 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(nfb, 5)
        Yp = Yh + (np.abs(Yh) + KAP) * ((mw + sw_ * g1) + 1j * (mt + st_ * g2))
        magpred[k] = np.abs(Yp).T; qoi[k] = np.abs(Yp).max(0)
    lo, md, hi = np.percentile(qoi, [2.5, 50, 97.5], 0)
    qtrue = data_h.max(1)
    cover = [bool(l <= t <= h) for l, t, h in zip(lo, qtrue, hi)]
    return dict(magpred=magpred, qoi_lo=lo.tolist(), qoi_med=md.tolist(), qoi_hi=hi.tolist(),
                qoi_truth=qtrue.tolist(), cover=cover, n_cover=int(sum(cover)))

def main():
    probe = os.environ.get("J_PROBE", "0") == "1"
    nw, ns, nchain = (500, 250, 2) if probe else (1000, 500, 4)
    res, flat = run(nw, ns, nchain)
    P = predict(flat, 200, np.random.default_rng(5))
    sf = np.percentile(flat["sf"], [2.5, 50, 97.5])
    sm = np.outer(sf, np.ones(M))
    np.savez(os.path.join(OUT, "studyj_arrays.npz"),
             FB=FB, YOBS=YOBS, HOLD=HOLD, OBSP=OBSP, PTS=PTS, DRIVE=DRIVE,
             fFEA=fFEA, sm_post=sm, magpred=P["magpred"],
             qoi_lo=P["qoi_lo"], qoi_med=P["qoi_med"], qoi_hi=P["qoi_hi"], qoi_truth=P["qoi_truth"])
    out = dict(method="REAL-panel UMS (FEA shapes fixed; calibrate per-mode freq + global damping/amp; Schneider discrepancy)",
               probe=probe, n_modes=int(M), band=BAND, n_obs=len(OBSP), n_hold=len(HOLD),
               drive_row=DRIVE, convergence=res, held_out_qoi=dict(
                   n_cover=P["n_cover"], cover=P["cover"], truth=P["qoi_truth"],
                   med=P["qoi_med"], lo=P["qoi_lo"], hi=P["qoi_hi"]),
               fea_freqs=fFEA.tolist(),
               global_freq_scale=sf.tolist(),
               calibrated_freqs=(sf[1] * fFEA).tolist(),
               scope="REAL data, FIRST real-panel calibration; single impact reference; C2 margin-scan mapping; ONE test/realization; mobility (m/s)/N")
    json.dump(out, open(os.path.join(OUT, "studyj_summary.json"), "w"), indent=2)
    print(f"Study J held-out QOI {P['n_cover']}/5  |  global freq scale {sf[1]:.3f}  |  cal f (Hz): {np.round(sf[1]*fFEA,1)}")
    print("saved studyj_summary.json")

if __name__ == "__main__":
    main()
