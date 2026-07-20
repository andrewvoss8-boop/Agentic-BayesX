import numpy as np, jax
jax.config.update("jax_enable_x64", True)
import run_ums as R
r, fl = R.run_nuts(False, 450, 220, 2, "probe4_gaugefixed")
print("2-chain agreement: R-hat %.3f  ESS %.0f  div %d (%.1f%%)" % (
    r["max_rhat"], r["min_ess"], r["divergences"], r["div_frac"]*100))
print("post f:", np.round(np.median(np.cumsum(fl["delta"],1),0),2))
print("true f:", np.round(R.f_t[:R.NM],2))
print("post zeta[%]:", np.round(100*np.median(fl["zeta"],0),2))
print("true zeta[%]:", np.round(100*R.z_t[:R.NM],2))
