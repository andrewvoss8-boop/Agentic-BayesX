import numpy as np, jax
jax.config.update("jax_enable_x64", True)
import run_ums2 as R2
r, fl = R2.run_nuts(False, 800, 400, 2, "probe8_femshapes")
print("2-chain: R-hat %.2f  ESS %.0f  div %d (%.1f%%)"%(r["max_rhat"],r["min_ess"],r["divergences"],r["div_frac"]*100))
P = R2.predictive(fl, False, 200, np.random.default_rng(5))
q = R2.qoi_stats(P)
print("QOI coverage:", q["n_cover"],"/10  (A",sum(q["A"]["cover"]),"/5, B",sum(q["B"]["cover"]),"/5)")
print("truth A:", np.round(R2.QA_true,1)); print("pred med:", np.round(np.array(q["A"]["med"]),1))
print("pred lo :", np.round(np.array(q["A"]["lo"]),1)); print("pred hi :", np.round(np.array(q["A"]["hi"]),1))
print("s_g med:", np.round(np.median(fl["s_g"],0),3))
