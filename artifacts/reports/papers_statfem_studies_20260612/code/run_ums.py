"""Study G headline: unified modal statFEM (statFEM + Das/Debnath + Schneider) on a
realistic synthetic suspended-panel twin.  See decisions_log.md D7-D13.

Generates LDV-realistic data ONCE (saved for the frame runs), runs the unified NUTS model
and an iid-discrepancy comparator, and computes held-out QOIs with spatially conditioned
discrepancy.  Env knobs: SMOKE=1 for a tiny timing run.
Outputs -> ../out/ums_data.npz, ums_headline.npz, ums_summary.json
"""
from __future__ import annotations
import json, math, os, time
import numpy as np
import jax, jax.numpy as jnp
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS, init_to_value
from numpyro.diagnostics import summary
import ums_model as U

jax.config.update("jax_enable_x64", True); numpyro.set_host_device_count(4)
OUT = os.path.join(os.path.dirname(__file__), "..", "out"); os.makedirs(OUT, exist_ok=True)
SMOKE = os.environ.get("SMOKE", "0") == "1"
REAL_SHAPES = os.environ.get("UMS_REAL", "1") == "1"   # D20: real mode shapes (default ON)
RNG = np.random.default_rng(20260613)

# ------------------------------------------------ configuration
F_GEN = np.arange(2.0, 100.0 + 1e-9, 0.125)        # display/generation grid (LDV-like df)
F_INF = np.arange(10.0, 60.0 + 1e-9, 0.125)        # inference band
BAND = (10.0, 60.0)                                 # QOI band
NM, B = 13, 17                                      # latent modes / Ritz basis size
DRIVE = 2 * U.NY + 2                                # node (2,2) -- in scan set
HOLD_NODES = [0, 18, 24, 32, 38]                    # corner, centre, top edge, IN-PATCH, right edge
SHOWCASE = 32                                       # held-out node inside the soft patch

xy = U.node_xy()
scan = sorted([n for n in range(U.NN)
               if ((n // U.NY) + (n % U.NY)) % 2 == 0])         # 20 nodes
assert DRIVE in scan and all(h in scan for h in HOLD_NODES)
obs_nodes = [n for n in scan if n not in HOLD_NODES]            # 15 observed
obs_nodes = [DRIVE] + [n for n in obs_nodes if n != DRIVE]      # drive first (raster ref)
hold_nodes = HOLD_NODES
coords_all = xy[scan]; coords_obs = xy[obs_nodes]; coords_hold = xy[hold_nodes]

# ------------------------------------------------ truth + data generation
truth = U.build_truth()
lam_t, psi_t, f_t, z_t = U.truth_complex_modes(truth)
H_clean_gen = U.direct_frf(truth["K"], truth["C"], truth["M"], truth["drive"],
                           scan, F_GEN)                          # [nf_gen, 20] CLEAN truth
med = np.median(np.abs(H_clean_gen[(F_GEN >= BAND[0]) & (F_GEN <= BAND[1])]))
FLOOR = med * 2e-3                                               # matches real-panel min/med ratio
gains = RNG.normal(0.0, 0.5, len(scan)) * (np.log(10) / 20)      # +-0.5 dB calibration scatter
def cnoise(shape, scale): return scale*(RNG.standard_normal(shape)+1j*RNG.standard_normal(shape))/math.sqrt(2)
data_gen = H_clean_gen * np.exp(gains)[None, :]
data_gen = data_gen * (1.0 + cnoise(data_gen.shape, 0.02))       # 2% multiplicative sensor noise
data_gen = data_gen + cnoise(data_gen.shape, FLOOR)              # additive noise floor
lowf = F_GEN < 8.0                                               # low-frequency junk (display realism)
data_gen[lowf] += cnoise(data_gen[lowf].shape, FLOOR * (8.0 / F_GEN[lowf, None]) ** 1.5 * 30)

sel = np.isin(np.round(F_GEN, 4), np.round(F_INF, 4))
scan_idx = {n: i for i, n in enumerate(scan)}
oi = [scan_idx[n] for n in obs_nodes]; hi = [scan_idx[n] for n in hold_nodes]
data_inf_all = data_gen[sel]                                     # [nf_inf, 20]
H_clean_inf = H_clean_gen[sel]
nfI = len(F_INF)

# ------------------------------------------------ nominal pieces (offline eigh)
nom = U.nominal_inference_pieces()
Phi = nom["Phi"][:, :B]                                          # [NN, B] M-orthonormal
f_nom = nom["f_nom"][:NM]
gaps_nom = np.diff(np.concatenate([[0.0], f_nom]))               # increments (first = f1)
Kt_list = [Phi.T @ Kg @ Phi for Kg in nom["Kg"]] + [Phi.T @ nom["Ks"] @ Phi]
Kt_stack = jnp.array(np.stack(Kt_list))                          # [5, B, B]
Phi_scan = jnp.array(Phi[scan, :])                               # [20, B]
Phi_drive = jnp.array(Phi[DRIVE, :])                             # [B]
A0N, A1N = 0.55, 4.0e-5
FLOOR_EST = float(np.quantile(np.abs(data_inf_all[:, oi]), 0.0015))   # deepest antiresonance bottoms
# Gauge fix (D16): each latent shape's m-th component is FIXED to 1+0i (standard modal
# normalization); only the B-1 off components are sampled. Removes the per-mode complex-scale
# gauge valley that scattered chains in run-1/probe3.
OFFIDX = np.stack([np.array([j for j in range(B) if j != m]) for m in range(NM)])  # [NM, B-1]
ROWIDX = np.arange(NM)[:, None]

# ------------------------------------------------ NUTS model
djnp = jnp.array(data_inf_all[:, oi])                            # observed data [nfI, 15]
fI = jnp.array(F_INF)
DF = float(F_INF[1] - F_INF[0])
OBS_LOCAL = jnp.array([scan.index(n) for n in obs_nodes])

def ums_model(iid=False, data=None, freqs=None, obs_local=None, coords=None):
    """Parametric over data subsets so the GIF frame runs reuse the same model.
    Defaults = the headline configuration (all 15 points, full 10-60 Hz band)."""
    data = djnp if data is None else data
    freqs = fI if freqs is None else freqs
    obs_local = OBS_LOCAL if obs_local is None else obs_local
    coords = coords_obs if coords is None else coords
    df_loc = freqs[1] - freqs[0]
    nf_loc = freqs.shape[0]
    s_g = numpyro.sample("s_g", dist.LogNormal(0.0, 0.2).expand([4]))
    s_su = 1.0   # D18: suspension scale FIXED at nominal -- its modes (~2.2 Hz) are outside the
    # 10-60 Hz band; probe6 showed it frozen (R-hat 125, ESS 1) = unidentifiable, not informative.
    a0 = numpyro.sample("a0", dist.LogNormal(math.log(A0N), 0.7))
    a1 = numpyro.sample("a1", dist.LogNormal(math.log(A1N), 0.7))
    delta = numpyro.sample("delta", dist.LogNormal(jnp.log(jnp.array(gaps_nom)), 0.25))
    fm = jnp.cumsum(delta)                                       # ordered latent freqs
    zm = numpyro.sample("zeta", dist.LogNormal(math.log(0.008), 0.4).expand([NM]))
    # practitioner prior (D17): panel modal damping ~0.4-2%; 95% in [0.36%,1.8%].
    # Suppresses the "kill the mode, let the discrepancy paint the peak" branch.
    # D18: per-mode shape-prior widths -- out-of-band modes (0,1,10,11,12) get tight priors
    # (their shapes are weakly identified by in-band data; loose priors = frozen flat directions).
    sd_cr = jnp.array([[(0.15 if REAL_SHAPES else 0.3) if 2 <= m <= 9 else 0.06] for m in range(NM)])
    cr_off = numpyro.sample("cr_off", dist.Normal(0.0, jnp.broadcast_to(sd_cr, (NM, B - 1))))
    cr = jnp.eye(NM, B).at[ROWIDX, OFFIDX].set(cr_off)           # m-th comp pinned to 1
    if REAL_SHAPES:
        ci = jnp.zeros((NM, B))   # D20: REAL mode shapes; complex-ness via lambda only (light damping)
    else:
        sd_ci = jnp.array([[0.10 if 2 <= m <= 9 else 0.03] for m in range(NM)])
        ci_off = numpyro.sample("ci_off", dist.Normal(0.0, jnp.broadcast_to(sd_ci, (NM, B - 1))))
        ci = jnp.zeros((NM, B)).at[ROWIDX, OFFIDX].set(ci_off)
    tau = 0.004 + numpyro.sample("tau", dist.LogNormal(math.log(0.03), 0.8))
    # 0.004 floor = the FEM eigenstructure is never perfect (jitter; keeps the
    # eigen-residual needle bounded; documented in method_ums.md)
    sw = numpyro.sample("sig_w", dist.LogNormal(math.log(0.15), 0.8))
    sth = numpyro.sample("sig_th", dist.LogNormal(math.log(0.25), 0.8))
    sadd = numpyro.sample("sig_add", dist.LogNormal(math.log(FLOOR_EST), 0.5))
    if not iid:
        lf = numpyro.sample("len_f", dist.LogNormal(math.log(6.0), 0.7))
        lz = numpyro.sample("len_z", dist.LogNormal(math.log(0.15), 0.7))

    Ktil = jnp.einsum("g,gij->ij", jnp.concatenate([s_g, jnp.ones(1) * s_su]), Kt_stack)
    Ctil = a0 * jnp.eye(B) + a1 * Ktil
    wm = 2 * jnp.pi * fm
    lam = -zm * wm + 1j * wm * jnp.sqrt(1.0 - zm ** 2)           # [NM]
    c = cr + 1j * ci                                             # [NM, B]
    # Das/Debnath eigen-residual (projected, normalized) -> soft tie to the FEM
    res = (lam[:, None] ** 2) * c + lam[:, None] * (c @ Ctil.T) + c @ Ktil.T
    scale = (jnp.abs(lam) ** 2 * jnp.linalg.norm(c, axis=1))[:, None]
    res = res / scale
    numpyro.sample("eig_r", dist.Normal(0.0, tau), obs=jnp.real(res))
    numpyro.sample("eig_i", dist.Normal(0.0, tau), obs=jnp.imag(res))
    # complex-mode residue FRF at observed points
    psi_scan = c @ Phi_scan.T                                    # [NM, 20]
    psi_d = c @ Phi_drive                                        # [NM]
    a_m = 2.0 * lam * jnp.sum(c * c, 1) + jnp.sum(c * (c @ Ctil.T), 1)
    Hobs = U.residue_frf_jax(lam, psi_scan[:, obs_local], psi_d, a_m, freqs)
    # Schneider-spirit discrepancy in the HMC-COMPATIBLE form (documented deviation, D9/D14):
    # scaled complex residual r=(data-H)/(|H|+kappa), kappa = inferred noise floor.
    # Small-error equivalent to Schneider's lognormal-mag/normal-phase log-error
    # (Re r ~ w, Im r ~ theta), but SMOOTH everywhere: no log singularity at antiresonance
    # zero-crossings and no wrapped-phase cliffs (the cliffs that defeat gradient-based
    # samplers and are sidestepped by Schneider's own gradient-free BUS-SuS choice).
    # At |H| >> kappa the error is multiplicative/structural; at |H| <~ kappa it degrades
    # gracefully to an additive floor: one field covers both regimes.
    scale = jnp.abs(Hobs) + sadd
    r_c = (data - Hobs) / scale
    w = jnp.real(r_c)
    th = jnp.imag(r_c)
    s_w = jnp.ones_like(w)
    s_t = jnp.ones_like(w)
    if iid:
        rho = jnp.zeros(nf_loc - 1); Lz = jnp.eye(coords.shape[0])
    else:
        rho = jnp.exp(-df_loc / lf) * jnp.ones(nf_loc - 1)
        Lz = U.exp_chol(jnp.array(coords), lz)
    numpyro.factor("ll_w", U.separable_logpdf(w, s_w, sw, rho, Lz))
    numpyro.factor("ll_t", U.separable_logpdf(th, s_t, sth, rho, Lz))

def peakpick_init():
    """Init latent freqs at data peaks (drive point) where they match nominal modes within 8%.
    INITIALIZATION ONLY — priors stay centered at the nominal FEM ladder (documented)."""
    from scipy.signal import find_peaks
    mag = np.abs(data_inf_all[:, oi]).mean(1)                     # mean spectrum, all obs points
    pk, _ = find_peaks(20 * np.log10(mag), distance=int(0.8 / DF), prominence=3)
    fpk = list(F_INF[pk])
    f_init = f_nom.copy()
    order = sorted(range(NM), key=lambda m: min([abs(p - f_nom[m]) for p in fpk] or [9e9]))
    for m in order:                                                # greedy one-to-one matching
        if not fpk: break
        j = int(np.argmin([abs(p - f_nom[m]) for p in fpk]))
        if abs(fpk[j] - f_nom[m]) / f_nom[m] < 0.08 and BAND[0] <= fpk[j] <= BAND[1]:
            f_init[m] = fpk.pop(j)
    f_init = np.maximum.accumulate(f_init + 1e-6 * np.arange(NM))  # keep ordered
    d_init = np.diff(np.concatenate([[0.0], f_init]))
    if np.any(d_init <= 0): d_init = gaps_nom.copy()               # fallback
    return d_init

D_INIT = peakpick_init()
INIT = dict(s_g=jnp.ones(4), a0=jnp.array(A0N), a1=jnp.array(A1N),
            delta=jnp.array(D_INIT), zeta=jnp.full(NM, 0.008),
            cr_off=jnp.zeros((NM, B - 1)), ci_off=jnp.zeros((NM, B - 1)), tau=jnp.array(0.03),
            sig_w=jnp.array(0.5), sig_th=jnp.array(0.5), sig_add=jnp.array(FLOOR_EST),
            len_f=jnp.array(6.0), len_z=jnp.array(0.15))

def run_nuts(iid, nw, ns, nchain, tag, **model_kw):
    """step_size=5e-4 initial: dense-FRF needle posteriors throw chains across basins if early
    warmup steps are large (run-1 failure: R-hat 236, 56% div, chains in different modes while
    a small-step single-chain probe stayed healthy). Start tiny, let dual-averaging adapt UP."""
    t0 = time.time()
    init = {k: v for k, v in INIT.items() if not (iid and k in ("len_f", "len_z"))}
    mc = MCMC(NUTS(lambda: ums_model(iid, **model_kw), target_accept_prob=0.9, max_tree_depth=10,
                   step_size=5e-4, init_strategy=init_to_value(values=init)),
              num_warmup=nw, num_samples=ns, num_chains=nchain,
              chain_method="sequential", progress_bar=False)
    mc.run(jax.random.PRNGKey(3), extra_fields=("diverging",))
    s = mc.get_samples(group_by_chain=True)
    div = int(jnp.sum(mc.get_extra_fields()["diverging"]))
    st = summary(s, group_by_chain=True)
    mr = max(float(np.nanmax(v["r_hat"])) for v in st.values())
    me = min(float(np.nanmin(v["n_eff"])) for v in st.values())
    flat = {k: np.array(v).reshape(-1, *v.shape[2:]) for k, v in s.items()}
    res = dict(tag=tag, max_rhat=mr, min_ess=me, divergences=div,
               div_frac=div / (nchain * ns), runtime_s=time.time() - t0,
               n_draws=nchain * ns)
    print(tag, {k: round(res[k], 4) if isinstance(res[k], float) else res[k] for k in res})
    return res, flat

# ------------------------------------------------ predictive + QOI machinery (numpy)
KtN = [np.array(k) for k in Kt_list]
PhiS = np.array(Phi_scan); PhiD = np.array(Phi_drive)

def rebuild(flat, i):
    sg = flat["s_g"][i]; ssu = 1.0
    Ktil = sum(sg[g] * KtN[g] for g in range(4)) + ssu * KtN[4]
    Ctil = flat["a0"][i] * np.eye(B) + flat["a1"][i] * Ktil
    fm = np.cumsum(flat["delta"][i]); zm = flat["zeta"][i]
    wm = 2 * np.pi * fm
    lam = -zm * wm + 1j * wm * np.sqrt(1 - zm ** 2)
    cr = np.eye(NM, B); ci = np.zeros((NM, B))
    cr[ROWIDX, OFFIDX] = flat["cr_off"][i]
    if not REAL_SHAPES: ci[ROWIDX, OFFIDX] = flat["ci_off"][i]
    c = cr + 1j * ci
    a_m = 2 * lam * np.sum(c * c, 1) + np.sum(c * (c @ Ctil.T), 1)
    return lam, c, a_m

def predictive(flat, iid, S, rng, band=BAND, obs_cols=None, obs_freqs=None, data_obs=None):
    """Posterior predictive at the 5 held-out nodes on the FULL F_INF grid, with the
    discrepancy field conditioned on observed residuals in BOTH frequency and space
    (exact for the separable kernel; field sampled on a 0.5 Hz grid and interpolated —
    the field is smooth by construction, the sharp physics stays on the 0.125 Hz grid)."""
    # obs_cols are ALWAYS indices into the 20-point scan list (explicit contract)
    obs_scan_idx = [scan.index(n) for n in obs_nodes] if obs_cols is None else list(obs_cols)
    if obs_freqs is None: obs_freqs = F_INF
    if data_obs is None: data_obs = data_inf_all[:, obs_scan_idx][np.isin(np.round(F_INF, 4),
                                                                          np.round(obs_freqs, 4))]
    nT = flat["s_g"].shape[0]; idx = rng.choice(nT, size=min(S, nT), replace=False)
    nf = len(F_INF); bm = (F_INF >= band[0]) & (F_INF <= band[1])
    fg = np.arange(F_INF[0], F_INF[-1] + 1e-9, 0.5)               # coarse field grid
    co = xy[[scan[j] for j in obs_scan_idx]]; ch = coords_hold
    hloc = [scan.index(n) for n in hold_nodes]; sloc = hold_nodes.index(SHOWCASE)
    qoiA = np.zeros((len(idx), 5)); qoiB = np.zeros((len(idx), 5))
    show = np.zeros((len(idx), nf)); show_phys = np.zeros((len(idx), nf))
    for k, i in enumerate(idx):
        lam, c, a_m = rebuild(flat, i)
        psi = c @ PhiS.T
        Hh = U.residue_frf_numpy(lam, psi[:, hloc], c @ PhiD, a_m, F_INF)    # [nf, 5]
        kap = flat["sig_add"][i]
        if iid:
            fwg = rng.normal(0, flat["sig_w"][i], (len(fg), 5))
            ftg = rng.normal(0, flat["sig_th"][i], (len(fg), 5))
        else:
            Hobs = U.residue_frf_numpy(lam, psi[:, obs_scan_idx], c @ PhiD, a_m, obs_freqs)
            r_c = (data_obs - Hobs) / (np.abs(Hobs) + kap)
            Wo = np.real(r_c); To = np.imag(r_c)
            lz = flat["len_z"][i]; lf = flat["len_f"][i]; sw_ = flat["sig_w"][i]; st_ = flat["sig_th"][i]
            dzo = np.sqrt(((co[:, None] - co[None]) ** 2).sum(-1))
            dzoh = np.sqrt(((co[:, None] - ch[None]) ** 2).sum(-1))
            dzh = np.sqrt(((ch[:, None] - ch[None]) ** 2).sum(-1))
            Rz_oo = np.exp(-dzo / lz) + 1e-8 * np.eye(len(co))
            Kz = np.linalg.solve(Rz_oo, np.exp(-dzoh / lz))                  # [n_o, 5]
            Qz = np.exp(-dzoh / lz).T @ Kz                                   # [5, 5]
            Rz_hh = np.exp(-dzh / lz)
            df_oo = np.abs(obs_freqs[:, None] - obs_freqs[None])
            df_po = np.abs(fg[:, None] - obs_freqs[None])
            df_pp = np.abs(fg[:, None] - fg[None])
            Rf_oo = np.exp(-df_oo / lf) + 1e-8 * np.eye(len(obs_freqs))
            Kf = np.linalg.solve(Rf_oo, np.exp(-df_po / lf).T).T             # [n_pf, n_of]
            Qf = np.exp(-df_po / lf) @ np.linalg.solve(Rf_oo, np.exp(-df_po / lf).T)
            Rf_pp = np.exp(-df_pp / lf)
            mean_w = Kf @ Wo @ Kz; mean_t = Kf @ To @ Kz                     # [n_pf, 5]
            covK = np.kron(Rf_pp, Rz_hh) - np.kron(Qf, Qz)                   # non-separable
            covK = (covK + covK.T) / 2 + 1e-8 * np.eye(covK.shape[0])
            Lc = np.linalg.cholesky(covK)
            g1 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(len(fg), 5)
            g2 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(len(fg), 5)
            fwg = mean_w + sw_ * g1; ftg = mean_t + st_ * g2
        fw = np.stack([np.interp(F_INF, fg, fwg[:, h]) for h in range(5)], 1)
        ft = np.stack([np.interp(F_INF, fg, ftg[:, h]) for h in range(5)], 1)
        Hp = Hh + (np.abs(Hh) + kap) * (fw + 1j * ft)                        # structural predictive
        mag = np.abs(Hp)
        qoiA[k] = mag[bm].max(0); qoiB[k] = np.sqrt((mag[bm] ** 2).mean(0))
        show[k] = mag[:, sloc]; show_phys[k] = np.abs(Hh[:, sloc])
    return dict(qoiA=qoiA, qoiB=qoiB, show=show, show_phys=show_phys, idx=idx)

# truth + deterministic-nominal QOIs at held-out nodes
bmI = (F_INF >= BAND[0]) & (F_INF <= BAND[1])
Hth = H_clean_inf[:, hi]
QA_true = np.abs(Hth)[bmI].max(0); QB_true = np.sqrt((np.abs(Hth)[bmI] ** 2).mean(0))
K_nomF = nom["K_nom"]; C_nomF = A0N * nom["M"] + A1N * K_nomF
H_det = U.direct_frf(K_nomF, C_nomF, nom["M"], DRIVE, hold_nodes, F_INF)
QA_det = np.abs(H_det)[bmI].max(0); QB_det = np.sqrt((np.abs(H_det)[bmI] ** 2).mean(0))

# ------------------------------------------------ run
def main():
    save_data()
    if SMOKE:
        r, fl = run_nuts(False, 60, 60, 1, "smoke")
        print("smoke ok; ~%.2f s/sample" % (r["runtime_s"] / 60))
        return
    res_u, fl_u = run_nuts(False, 1500, 400, 4, "unified")
    res_i, fl_i = run_nuts(True, 1200, 400, 2, "iid")  # 2-chain comparator (labeled)
    rngp = np.random.default_rng(5)
    P_u = predictive(fl_u, False, 200, rngp)
    P_i = predictive(fl_i, True, 200, rngp)
    q_u, q_i = qoi_stats(P_u), qoi_stats(P_i)
    zpost = np.percentile(fl_u["zeta"], [2.5, 50, 97.5], 0)
    fpost = np.percentile(np.cumsum(fl_u["delta"], 1), [2.5, 50, 97.5], 0)
    np.savez(os.path.join(OUT, "ums_headline.npz"),
             showU=P_u["show"], showU_phys=P_u["show_phys"], showI=P_i["show"],
             qoiA_u=P_u["qoiA"], qoiB_u=P_u["qoiB"], qoiA_i=P_i["qoiA"], qoiB_i=P_i["qoiB"],
             zeta_post=zpost, f_post=fpost,
             tau=fl_u["tau"], sig_w=fl_u["sig_w"], sig_th=fl_u["sig_th"],
             len_f=fl_u["len_f"], len_z=fl_u["len_z"], sig_add=fl_u["sig_add"],
             a0=fl_u["a0"], a1=fl_u["a1"], s_g=fl_u["s_g"])
    js = dict(config=dict(NM=NM, B=B, band=BAND, nf_inf=nfI, n_obs=len(obs_nodes),
                          n_hold=5, floor=FLOOR, floor_est=FLOOR_EST,
                          truth=dict(f=f_t[:NM].tolist(), zeta=z_t[:NM].tolist())),
              unified=res_u, iid=res_i,
              qoi_unified=q_u, qoi_iid=q_i,
              qoi_truth=dict(A=QA_true.tolist(), B=QB_true.tolist()),
              qoi_deterministic=dict(A=QA_det.tolist(), B=QB_det.tolist()),
              hyper=dict(tau=np.percentile(fl_u["tau"], [2.5, 50, 97.5]).tolist(),
                         sig_w=np.percentile(fl_u["sig_w"], [2.5, 50, 97.5]).tolist(),
                         len_f=np.percentile(fl_u["len_f"], [2.5, 50, 97.5]).tolist(),
                         len_z=np.percentile(fl_u["len_z"], [2.5, 50, 97.5]).tolist()))
    json.dump(js, open(os.path.join(OUT, "ums_summary.json"), "w"), indent=2)
    print(json.dumps(dict(unified=dict(rhat=res_u["max_rhat"], ess=res_u["min_ess"],
                                       div=res_u["divergences"], qoi_cover=f"{q_u['n_cover']}/10"),
                          iid=dict(rhat=res_i["max_rhat"], qoi_cover=f"{q_i['n_cover']}/10")), indent=2))
    print("saved ums_summary.json / ums_headline.npz")


def save_data():
    np.savez(os.path.join(OUT, "ums_data.npz"),
         F_GEN=F_GEN, F_INF=F_INF, data_gen=data_gen, H_clean_gen=H_clean_gen,
         data_inf_all=data_inf_all, H_clean_inf=H_clean_inf, scan=scan,
         obs_nodes=obs_nodes, hold_nodes=hold_nodes, oi=oi, hi=hi, xy=xy,
         FLOOR=FLOOR, gains=gains, truth_f=f_t[:NM], truth_z=z_t[:NM],
         f_nom=f_nom, QA_true=QA_true, QB_true=QB_true, QA_det=QA_det, QB_det=QB_det,
         drive=DRIVE, showcase=SHOWCASE, band=np.array(BAND))
    print("data saved; FLOOR %.3e  FLOOR_EST %.3e  n_obs %d  nf_inf %d" %
          (FLOOR, FLOOR_EST, len(obs_nodes), nfI))


def qoi_stats(P):
    out = {}
    for nm_, arr, tru in (("A", P["qoiA"], QA_true), ("B", P["qoiB"], QB_true)):
        lo, mdn, hia = np.percentile(arr, [2.5, 50, 97.5], 0)
        out[nm_] = dict(lo=lo.tolist(), med=mdn.tolist(), hi=hia.tolist(),
                        truth=tru.tolist(), cover=[bool(l <= t <= h) for l, t, h in zip(lo, tru, hia)])
    out["n_cover"] = int(sum(out["A"]["cover"]) + sum(out["B"]["cover"]))
    return out


if __name__ == "__main__":
    main()
