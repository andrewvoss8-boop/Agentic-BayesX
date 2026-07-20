import os, time
import numpy as np, jax
jax.config.update("jax_enable_x64", True)
import run_ums as R
r, fl = R.run_nuts(False, 400, 200, 1, "medium_probe")
zf = np.percentile(np.cumsum(fl["delta"],1),50,0)
print("posterior f (med):", np.round(zf,2))
print("truth f          :", np.round(R.f_t[:R.NM],2))
print("sig_w med %.3f  sig_th med %.3f  tau med %.4f  len_f med %.2f" % (
  np.median(fl["sig_w"]), np.median(fl["sig_th"]), np.median(fl["tau"]), np.median(fl["len_f"])))
