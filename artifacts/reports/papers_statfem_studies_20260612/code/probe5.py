import numpy as np, jax
jax.config.update("jax_enable_x64", True)
import run_ums as R
r, fl = R.run_nuts(False, 450, 220, 2, "probe5_zprior")
print("2-chain: R-hat %.3f  ESS %.0f  div %d (%.1f%%)" % (r["max_rhat"], r["min_ess"], r["divergences"], r["div_frac"]*100))
nz = fl["zeta"].reshape(2, -1, R.NM)   # per chain
for ch in range(2):
    print("chain%d zeta[%%]:" % ch, np.round(100*np.median(nz[ch],0),2))
print("true    zeta[%]:", np.round(100*R.z_t[:R.NM],2))
