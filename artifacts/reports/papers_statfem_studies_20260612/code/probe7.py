import os; os.environ["UMS_REAL"]="1"
import numpy as np, jax
jax.config.update("jax_enable_x64", True)
import run_ums as R
print("REAL_SHAPES =", R.REAL_SHAPES)
r, fl = R.run_nuts(False, 500, 250, 2, "probe7_realshapes")
print("2-chain: R-hat %.2f  ESS %.0f  div %d (%.1f%%)" % (r["max_rhat"], r["min_ess"], r["divergences"], r["div_frac"]*100))
P = R.predictive(fl, False, 150, np.random.default_rng(5))
qa = np.percentile(P["qoiA"],[2.5,50,97.5],0)
cov = sum(qa[0,h] <= R.QA_true[h] <= qa[2,h] for h in range(5))
print("QOI-A held-out coverage: %d/5"%cov)
print("truth A:", np.round(R.QA_true,1)); print("pred med:", np.round(qa[1],1))
print("post f:", np.round(np.median(np.cumsum(fl["delta"],1),0),2))
