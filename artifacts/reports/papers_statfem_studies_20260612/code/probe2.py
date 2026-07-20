import numpy as np, jax
jax.config.update("jax_enable_x64", True)
import run_ums as R
r, fl = R.run_nuts(False, 500, 300, 1, "probe2")
zf = np.median(np.cumsum(fl["delta"],1),0)
print("post f:", np.round(zf,2)); print("true f:", np.round(R.f_t[:R.NM],2))
print("post zeta[%]:", np.round(100*np.median(fl["zeta"],0),2))
print("true zeta[%]:", np.round(100*R.z_t[:R.NM],2))
print("sig_w %.3f tau %.4f len_f %.2f len_z %.3f sadd %.4f (floor %.4f)" % (
  np.median(fl["sig_w"]), np.median(fl["tau"]), np.median(fl["len_f"]),
  np.median(fl["len_z"]), np.median(fl["sig_add"]), R.FLOOR))
