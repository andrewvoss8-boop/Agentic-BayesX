import numpy as np, jax, time
jax.config.update("jax_enable_x64", True)
import numpyro
from numpyro.infer import MCMC, NUTS, init_to_value
from numpyro.diagnostics import summary
import run_ums as R

mc = MCMC(NUTS(lambda: R.ums_model(False), target_accept_prob=0.9, max_tree_depth=9,
               step_size=5e-4, init_strategy=init_to_value(values=R.INIT)),
          num_warmup=450, num_samples=220, num_chains=2, chain_method="sequential", progress_bar=False)
mc.run(jax.random.PRNGKey(3), extra_fields=("diverging",))
s = mc.get_samples(group_by_chain=True)
st = summary(s, group_by_chain=True)
rows=[]
for k,v in st.items():
    r=np.atleast_1d(v["r_hat"]); e=np.atleast_1d(v["n_eff"])
    for idx in np.ndindex(r.shape):
        rows.append((float(r[idx]), float(e[idx]), k, idx))
rows.sort(reverse=True)
print("== top-12 worst R-hat coordinates ==")
for r,e,k,idx in rows[:12]:
    print(f"  {k}{list(idx)}  R-hat {r:8.2f}  ESS {e:6.1f}")
phys=[x for x in rows if x[2] in ("s_g","s_susp","a0","a1","delta","zeta","tau","sig_w","sig_th","sig_add","len_f","len_z")]
print("== worst PHYSICAL/hyper coordinate ==")
r,e,k,idx=max(phys); print(f"  {k}{list(idx)}  R-hat {r:.3f}  ESS {e:.0f}")
inband=[x for x in rows if x[2] in ("cr_off","ci_off") and 2<=x[3][0]<=9]
print("== worst IN-BAND shape coordinate (modes 2..9) ==")
r,e,k,idx=max(inband); print(f"  {k}{list(idx)}  R-hat {r:.3f}  ESS {e:.0f}")
