"""Study D (synthetic, exercises Das/Debnath 2020) — mode-matching-free complex-modal updating
through a NEAR-DEGENERATE mode pair, with damping identification.

Setup: 4-DOF fixed-fixed damped chain, tuned to a near-degenerate mode pair (mirrors the hexapod
tray 82.9/84.3 close pair and the ShockSat eigh-MAC divergence we logged in notes/todo.md).

A/B under NUTS:
  D-eig  : likelihood differentiates through eigh(K(θ),M) + an eigenvector/MAC term -> the
           1/(λ_i−λ_j) eigh-backward blows up at the near-degenerate pair (the logged failure).
  D-latent (Das/Debnath T-D1+T-D2): treat the system complex modes Ψ as LATENT; likelihood =
           eigen-equation residual (λ̂²M+λ̂C(θ)+K(θ))Ψ  +  shape residual ψ̂−LΨ. No eigensolve,
           no mode pairing, no eigh backward -> smooth at degeneracy; recovers stiffness AND damping.
Outputs -> ../out/study_d_*.
"""
from __future__ import annotations
import json, math, os, time
import numpy as np
import jax, jax.numpy as jnp
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
from numpyro.diagnostics import summary

jax.config.update("jax_enable_x64", True); numpyro.set_host_device_count(4)
OUT=os.path.join(os.path.dirname(__file__),"..","out"); os.makedirs(OUT,exist_ok=True)
RNG=np.random.default_rng(20260612)
N=4; M=np.eye(N)

# springs of a fixed-fixed chain: k[0]=ground-1, k[1]=1-2, k[2]=2-3, k[3]=3-4, k[4]=4-ground
K_TRUE=np.array([1000.,1000.,4.,1000.,1000.])       # weaker middle (k[2]=4) -> TIGHTER near-degenerate pair
C_TRUE=np.array([0.6,0.6,0.02,0.9,0.6])             # non-proportional viscous

def assemble(kv,cv):
    K=np.zeros((N,N)); C=np.zeros((N,N))
    for (A,arr) in ((K,kv),(C,cv)):
        A[0,0]+=arr[0]; A[N-1,N-1]+=arr[N]
        for i in range(N-1):
            A[i,i]+=arr[i+1]; A[i+1,i+1]+=arr[i+1]; A[i,i+1]-=arr[i+1]; A[i+1,i]-=arr[i+1]
    return K,C
Kt,Ct=assemble(K_TRUE,C_TRUE)

def state_eig(K,C):
    A=np.block([[np.zeros((N,N)),np.eye(N)],[-np.linalg.solve(M,K),-np.linalg.solve(M,C)]])
    w,V=np.linalg.eig(A)
    return w,V
wt,Vt=state_eig(Kt,Ct)
# pick modes with positive imaginary part, sorted by frequency
pos=[i for i in range(len(wt)) if wt[i].imag>1e-6]
pos=sorted(pos,key=lambda i:abs(wt[i].imag))
lam=np.array([wt[i] for i in pos])                  # complex eigenvalues
fns=np.abs(lam)/(2*np.pi); zns=-lam.real/np.abs(lam)
psi=np.array([Vt[:N,i] for i in pos])               # displacement part of mode shape [nmode,N]
# normalize each shape to unit norm * fix phase (largest comp real+)
for m in range(psi.shape[0]):
    j=np.argmax(np.abs(psi[m])); psi[m]=psi[m]/psi[m,j]; psi[m]=psi[m]/np.linalg.norm(psi[m])
NMODE=3                                              # use first 3 modes (1 held out)
deg=abs(fns[1]-fns[0])/fns[0]                        # near-degeneracy of modes 1&2
print("truth freqs Hz:",np.round(fns[:4],3)," zeta:",np.round(zns[:4],4)," pair gap %.2f%%"%(deg*100))

# measured DOF subset (incomplete) and noise
MEAS=[0,2]
lam_hat=lam[:NMODE]*(1+0.01*(RNG.standard_normal(NMODE)+1j*RNG.standard_normal(NMODE)))
psi_hat=psi[:NMODE][:,MEAS]+0.02*(RNG.standard_normal((NMODE,len(MEAS)))+1j*RNG.standard_normal((NMODE,len(MEAS))))

# ---------- JAX assemble ----------
def jassemble(kv,cv):
    def build(arr):
        A=jnp.zeros((N,N))
        A=A.at[0,0].add(arr[0]).at[N-1,N-1].add(arr[N])
        for i in range(N-1):
            A=A.at[i,i].add(arr[i+1]).at[i+1,i+1].add(arr[i+1]).at[i,i+1].add(-arr[i+1]).at[i+1,i].add(-arr[i+1])
        return A
    return build(kv),build(cv)

KNOM=K_TRUE.copy(); CNOM=C_TRUE.copy()
def kc_params():
    lk=numpyro.sample("lk",dist.Normal(jnp.log(jnp.array(KNOM)),0.2))
    lc=numpyro.sample("lc",dist.Normal(jnp.log(jnp.array(CNOM)),0.5))
    return jnp.exp(lk),jnp.exp(lc)

# ---------- D-latent (Das/Debnath) ----------
def model_latent():
    kv,cv=kc_params()
    K,C=jassemble(kv,cv)
    s1=numpyro.sample("s_eig",dist.LogNormal(math.log(0.5),0.7))
    s2=numpyro.sample("s_shape",dist.LogNormal(math.log(0.05),0.7))
    for m in range(NMODE):
        pr=numpyro.sample(f"psr{m}",dist.Normal(0,1).expand([N]))
        pi=numpyro.sample(f"psi{m}",dist.Normal(0,1).expand([N]))
        Psi=pr+1j*pi
        lh=complex(lam_hat[m])
        e=(lh**2)*Psi+lh*(C@Psi)+(K@Psi)                   # (λ²M+λC+K)Ψ ; M=I
        sc=s1*abs(lh)**2                                   # fixed per-mode scale (avoids funnel)
        numpyro.sample(f"er{m}",dist.Normal(0,sc),obs=jnp.real(e))
        numpyro.sample(f"ei{m}",dist.Normal(0,sc),obs=jnp.imag(e))
        sh=Psi[jnp.array(MEAS)]
        numpyro.sample(f"shr{m}",dist.Normal(0,s2),obs=jnp.real(sh)-jnp.real(jnp.array(psi_hat[m])))
        numpyro.sample(f"shi{m}",dist.Normal(0,s2),obs=jnp.imag(sh)-jnp.imag(jnp.array(psi_hat[m])))

# ---------- D-eig (naive eigh-through; undamped) ----------
def model_eig():
    lk=numpyro.sample("lk",dist.Normal(jnp.log(jnp.array(KNOM)),0.2))
    kv=jnp.exp(lk); K,_=jassemble(kv,jnp.array(CNOM))
    s=numpyro.sample("s_obs",dist.LogNormal(math.log(0.03),0.7))
    evals,evecs=jnp.linalg.eigh(jnp.linalg.solve(jnp.array(M),K))   # ascending
    fmod=jnp.sqrt(jnp.abs(evals))/(2*jnp.pi)
    fobs=jnp.array(np.abs(lam_hat)/(2*np.pi))
    numpyro.sample("fr",dist.Normal(0,s*fobs),obs=fmod[:NMODE]-fobs)
    # eigenvector/MAC term at measured DOF (this is where eigh-backward blows up at degeneracy)
    for m in range(NMODE):
        vmod=evecs[jnp.array(MEAS),m]
        vmeas=jnp.array(np.real(psi_hat[m]))
        vmod=vmod/ (jnp.linalg.norm(vmod)+1e-9)
        vmeas=vmeas/(jnp.linalg.norm(vmeas)+1e-9)
        numpyro.sample(f"mac{m}",dist.Normal(0,0.03),obs=(jnp.abs(jnp.dot(vmod,vmeas))-1.0))

def run(model,nw=800,ns=800,ta=0.95):
    t0=time.time()
    mc=MCMC(NUTS(model,target_accept_prob=ta,init_strategy=numpyro.infer.init_to_median),
            num_warmup=nw,num_samples=ns,num_chains=4,chain_method="sequential",progress_bar=False)
    mc.run(jax.random.PRNGKey(1),extra_fields=("diverging",))
    s=mc.get_samples(group_by_chain=True); div=int(jnp.sum(mc.get_extra_fields()["diverging"]))
    st=summary(s,group_by_chain=True)
    mr=max(float(np.nanmax(v["r_hat"])) for v in st.values()); me=min(float(np.nanmin(v["n_eff"])) for v in st.values())
    flat={k:np.array(v).reshape(-1,*v.shape[2:]) for k,v in s.items()}
    return dict(max_rhat=mr,min_ess=me,divergences=div,div_frac=div/(4*ns),runtime_s=time.time()-t0),flat

print("D-latent (Das/Debnath) ..."); rl,fl=run(model_latent)
print("D-eig (naive eigh) ...");     re,fe=run(model_eig)

# damping recovery from D-latent: reconstruct K,C at posterior median, eig, zeta
kmed=np.exp(np.median(fl['lk'],0)); cmed=np.exp(np.median(fl['lc'],0))
Km,Cm=assemble(kmed,cmed); wm,_=state_eig(Km,Cm)
posm=sorted([i for i in range(len(wm)) if wm[i].imag>1e-6],key=lambda i:abs(wm[i].imag))
frec=np.abs([wm[i] for i in posm])[:NMODE]/(2*np.pi); zrec=(-np.array([wm[i].real for i in posm])/np.abs([wm[i] for i in posm]))[:NMODE]

out=dict(
  truth=dict(freqs_hz=[float(x) for x in fns[:NMODE]],zeta=[float(x) for x in zns[:NMODE]],
             near_degenerate_pair_gap_pct=float(deg*100)),
  D_latent=dict(**{k:rl[k] for k in ('max_rhat','min_ess','divergences','div_frac','runtime_s')},
     recovered_freqs_hz=[float(x) for x in frec],recovered_zeta=[float(x) for x in zrec]),
  D_eig=dict(**{k:re[k] for k in ('max_rhat','min_ess','divergences','div_frac','runtime_s')}),
  note="D-eig differentiates through eigh -> divergences at the near-degenerate pair; D-latent (Das/Debnath) avoids it")
json.dump(out,open(os.path.join(OUT,"study_d_summary.json"),"w"),indent=2)
np.savez(os.path.join(OUT,"study_d_arrays.npz"),
   truth_f=fns[:NMODE],truth_z=zns[:NMODE],rec_f=frec,rec_z=zrec,
   lk=fl['lk'],lc=fl['lc'])
print(json.dumps(out,indent=2)); print("saved study_d_summary.json")
