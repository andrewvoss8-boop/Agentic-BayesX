import numpy as np, jax, jax.numpy as jnp, sys
sys.path.insert(0, 'runs/round3/opus48/code')
import blind_model as bm

P = np.load('runs/round3/opus48/report/blind_posterior.npz')
grid = P['grid']; M_base6 = jnp.asarray(P['M_base6']); m_dome=float(P['m_dome'])
Phi = jnp.asarray(P['Phi']); omega = jnp.asarray(P['omega']); ell_d=float(P['ell_d'])
NDOF=6; M_HSGP=3

def matern32_sdens(om, sigma, ell):
    return sigma**2 * (4.0*(jnp.sqrt(3.0)/ell)**3) / ((jnp.sqrt(3.0)/ell)**2 + om**2)**2

@jax.jit
def one(logk, fdome, sigma_d, beta):
    mu = bm.forward_logmag(jnp.exp(logk), fdome, M_base6, m_dome, jnp.asarray(grid))
    sd = jnp.sqrt(matern32_sdens(omega, sigma_d, ell_d))
    return mu + (Phi @ (sd*beta).T).T

# clean truth apparent mass for held-out builds 6,7, interp log|M| onto grid
sk = np.load('runs/round3/codex_truth/sealed_truth/scoring_key.npz')
ftrue = sk['frequency_hz']
re = sk['clean_coupled_apparent_mass_real']; im = sk['clean_coupled_apparent_mass_imag']
mag_true = np.sqrt(re**2 + im**2)  # (8,6,4040)
logmag_true_grid = np.empty((8,6,len(grid)))
for b in range(8):
    for i in range(6):
        logmag_true_grid[b,i] = np.interp(grid, ftrue, np.log(mag_true[b,i]))

# posterior predictive for NEW build (k from population) -- replicate report
rng = np.random.default_rng(10)
S = P['k_strut_pop'].shape[0]; n=300; idx = rng.choice(S, n, replace=False)
se = P['sigma_e'][idx]
logk = np.log(P['k_strut_pop'][idx]) + P['sigma_build'][idx]*rng.standard_normal(n)
fdome = P['f_dome'][idx]; sigma_d = P['sigma_d'][idx]; beta = P['beta'][idx]
out = np.empty((n,6,len(grid)))
for i in range(n):
    out[i] = np.asarray(one(float(logk[i]), float(fdome[i]), float(sigma_d[i]), jnp.asarray(beta[i])))
draws = out + se[:,None,None]*rng.standard_normal(out.shape)
lo = np.quantile(draws,0.025,axis=0); hi = np.quantile(draws,0.975,axis=0)

band = (grid>=82.0)&(grid<=95.0)
# Held-out builds 6,7 vs CLEAN truth, full band
for label, blist, fmask in [('heldout builds 6,7 (full grid) vs CLEAN', [6,7], np.ones(len(grid),bool)),
                            ('heldout band 82-95 on TRAIN builds 0-5 vs CLEAN', list(range(6)), band)]:
    covs=[]; 
    for b in blist:
        o = logmag_true_grid[b][:,fmask]; L=lo[:,fmask]; H=hi[:,fmask]
        covs.append(np.mean((o>=L)&(o<=H)))
    print('%-50s coverage=%.3f  per=%s  mean_logwidth=%.2f' % (label, np.mean(covs), np.round(covs,3).tolist(), np.mean(hi[:,fmask]-lo[:,fmask])))

# also bias: posterior-median model vs clean truth in held-out band, per DOF (build 6)
med = {k: np.median(P[k]) for k in ['k_strut_pop','f_dome','sigma_d']}
mu_med = np.asarray(one(np.log(med['k_strut_pop']), med['f_dome'], 0.0, np.zeros((6,3))))
print('\nPosterior-median physics-only log|M| residual vs CLEAN truth, build6, band 82-95 (per DOF):')
for i,nm in enumerate(bm.DOF):
    r = (mu_med[i]-logmag_true_grid[6,i])[band]
    print('  %3s mean_resid=%+.3f (truth - too: model %+.3f)' % (nm, np.mean(r), np.mean(r)))
