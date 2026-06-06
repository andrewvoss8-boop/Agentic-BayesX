#!/usr/bin/env python3
"""Independent recompute of held-out calibration (builds 6,7 full band; band 95-115 Hz train builds)
for the WITH-d posterior, scored vs OBSERVED AM (reproduce self-report) AND vs CLEAN sealed-truth AM."""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, "runs/round3/opus48/code")
import jax; jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import blind3_model as bm

REP = Path("runs/round3/opus48/report")
SEALED = Path("runs/round3/codex_truth/sealed_truth")
HELDOUT_BUILDS = [6, 7]; HELDOUT_BAND = (95.0, 115.0)

obs = bm.load_observations()
M_src6, m_dome, lf = bm.source_rigid_from_asymptote(obs)
P = np.load(REP / "blind3_posterior.npz")
grid = P["grid"]; scale = P["scale"]; grid_j = jnp.asarray(grid)

# interpolate OBSERVED and CLEAN truth AM onto the grid
sk = np.load(SEALED / "scoring_key.npz")
fkey = sk["frequency_hz"]
clean_re = sk["clean_coupled_apparent_mass_real"]; clean_im = sk["clean_coupled_apparent_mass_imag"]
def interp_grid(re_full, im_full):
    nb = re_full.shape[0]; ng = len(grid)
    re = np.zeros((nb,6,ng)); im = np.zeros((nb,6,ng))
    for b in range(nb):
        for j in range(6):
            re[b,j] = np.interp(grid, fkey if re_full.shape[2]==len(fkey) else obs["f"], re_full[b,j])
            im[b,j] = np.interp(grid, fkey if im_full.shape[2]==len(fkey) else obs["f"], im_full[b,j])
    return re, im
obs_re, obs_im = interp_grid(obs["re"], obs["im"])
cln_re, cln_im = interp_grid(clean_re, clean_im)

# posterior-predictive for a NEW build (mirror heldout_calibration exactly)
k_pop = np.exp(P["log_k_pop"]); d0 = P["d0"]; f_dome = P["f_dome"]; sb = P["sigma_build"]
nd = len(k_pop); rng = np.random.default_rng(7)
bf = np.exp(sb * rng.standard_normal(nd))
def predict():
    out = []
    for i in range(nd):
        k = k_pop[i]*bf[i]*np.exp(d0[i])
        out.append(np.asarray(bm.forward_complex(jnp.asarray(k), float(f_dome[i]), M_src6, m_dome, grid_j)))
    return np.stack(out)  # (nd,6,ng)
pred = predict()
sde = P["sigma_e"][:,None,None]*scale[None,:,:]
pr = np.real(pred) + sde*rng.standard_normal(pred.shape)
pi = np.imag(pred) + sde*rng.standard_normal(pred.shape)
lo_r,hi_r = np.percentile(pr,[2.5,97.5],axis=0); lo_i,hi_i = np.percentile(pi,[2.5,97.5],axis=0)
inband = np.ones(len(grid),bool); hb = (grid>=HELDOUT_BAND[0])&(grid<=HELDOUT_BAND[1])
def cover(re_t,im_t,mask):
    cr=(re_t>=lo_r)&(re_t<=hi_r); ci=(im_t>=lo_i)&(im_t<=hi_i)
    return float((cr&ci)[:,mask].mean())
for label, RE, IM in [("OBSERVED", obs_re, obs_im), ("CLEAN truth", cln_re, cln_im)]:
    cov_b = np.mean([cover(RE[b],IM[b],inband) for b in HELDOUT_BUILDS])
    cov_band = np.mean([cover(RE[b],IM[b],hb) for b in range(6)])
    print(f"[{label}] held-out builds 6,7 cov95={cov_b:.4f} | band 95-115Hz cov95={cov_band:.4f}")
# log-width (predictive magnitude span)
magpred = np.sqrt(pr**2+pi**2); mlo,mhi=np.percentile(magpred,[2.5,97.5],axis=0)
floor = 1e-2*np.median(np.abs(np.mean(obs["re"]+1j*obs["im"],axis=0)))
logwidth = float(np.mean(np.log((mhi+floor)/(np.maximum(mlo,0)+floor))))
print(f"mean log-width = {logwidth:.4f}  (~{np.exp(logwidth):.1f}x multiplicative span)")
