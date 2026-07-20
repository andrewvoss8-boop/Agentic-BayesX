"""Study A — Phase 1 hardening (no new data).

(1) CONTROL: truth = 2-DOF (NO hidden DOF) with the same injected Schneider error.
    Tests the two biggest caveats from Study A:
      - does V1 iid then CONVERGE? (was the non-convergence caused by model-form error, not a bug?)
      - does V2 then RECOVER the injected hyperparameters? (was the 'sponge' caused by model-form error?)
(2) SWEEP: vary the injected frequency-correlation length ℓ_f* (truth=2-DOF) and check that the
    Schneider posterior ℓ_f tracks it -> a calibration curve (the correlation length is learnable).
Outputs -> ../out/phase1_*.  NUTS, 4 chains.
"""
from __future__ import annotations
import json, math, os, time
import numpy as np
import jax, jax.numpy as jnp
from jax.scipy.linalg import solve_triangular
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
from numpyro.diagnostics import summary
import forward as F

jax.config.update("jax_enable_x64", True); numpyro.set_host_device_count(4)
OUT=os.path.join(os.path.dirname(__file__),"..","out"); os.makedirs(OUT,exist_ok=True)

M1,M2,M3=1.0,0.6,0.25; F1,F2,F3=110.0,75.0,220.0; Z1,Z2,Z3=0.015,0.020,0.030
NF=56; FREQS=np.geomspace(30.0,200.0,NF); COORDS=np.array([0.0,1.0]); NMP=2
SIG_TH_STAR=0.10; LZ_STAR,R_STAR=0.6,0.8; SIG_IID,ADD_FRAC=0.03,0.015
w1n,w2n=2*math.pi*F1,2*math.pi*F2; K1N,K2N=M1*w1n**2,M2*w2n**2; K12N=K2N
fj,cj=jnp.array(FREQS),jnp.array(COORDS); PRI=dict(lk_sd=0.18,lz_sd=0.35)

def truth_kc():
    w1,w2,w3=2*math.pi*F1,2*math.pi*F2,2*math.pi*F3
    k1=M1*w1**2;k2=M2*w2**2;k3=M3*w3**2
    c1=float(F.zeta_to_c(Z1,k1,M1));c2=float(F.zeta_to_c(Z2,k2,M2));c3=float(F.zeta_to_c(Z3,k3,M3))
    return dict(k1=k1,k2=k2,k12=k2,k23=k3,c1=c1,c2=c2,c12=c2,c23=c3)
TK=truth_kc()

def gen_data(hidden, lf_inj, sw_inj, seed):
    rng=np.random.default_rng(seed)
    if hidden:
        ta=np.array(F.accelerance_3dof(fj,TK['k1'],TK['k2'],TK['k12'],TK['k23'],
                                       TK['c1'],TK['c2'],TK['c12'],TK['c23'],M1,M2,M3))
    else:
        ta=np.array(F.accelerance_2dof(fj,TK['k1'],TK['k2'],TK['k12'],TK['c1'],TK['c2'],TK['c12'],M1,M2))
    R=np.array(F.schneider_R(fj,cj,lf_inj,LZ_STAR,R_STAR)); n=R.shape[0]
    L=np.linalg.cholesky(R+1e-10*np.eye(n))
    w=sw_inj*(L@rng.standard_normal(n)); th=SIG_TH_STAR*(L@rng.standard_normal(n))
    data=ta*np.exp(w+1j*th).reshape(NF,NMP)
    med=np.median(np.abs(ta))
    data=data+ADD_FRAC*med*(rng.standard_normal((NF,NMP))+1j*rng.standard_normal((NF,NMP)))
    data=data+SIG_IID*np.abs(data)*(rng.standard_normal((NF,NMP))+1j*rng.standard_normal((NF,NMP)))/math.sqrt(2)
    return ta,data

def model_accel(k1,k2,k12,z1,z2,freqs):
    c1=F.zeta_to_c(z1,k1,M1);c2=F.zeta_to_c(z2,k2,M2)
    return F.accelerance_2dof(freqs,k1,k2,k12,c1,c2,c2,M1,M2)
def phys():
    lk1=numpyro.sample("lk1",dist.Normal(math.log(K1N),PRI['lk_sd']))
    lk2=numpyro.sample("lk2",dist.Normal(math.log(K2N),PRI['lk_sd']))
    lk12=numpyro.sample("lk12",dist.Normal(math.log(K12N),PRI['lk_sd']))
    z1=numpyro.sample("z1",dist.LogNormal(math.log(Z1),PRI['lz_sd']))
    z2=numpyro.sample("z2",dist.LogNormal(math.log(Z2),PRI['lz_sd']))
    return jnp.exp(lk1),jnp.exp(lk2),jnp.exp(lk12),z1,z2
def mvn0(x,L,s):
    nn=x.shape[0];y=solve_triangular(L,x,lower=True)
    return -0.5*(nn*jnp.log(2*jnp.pi)+2*jnp.sum(jnp.log(jnp.diag(L)))+2*nn*jnp.log(s)+jnp.sum(y*y)/s**2)
def model_v1(freqs,d):
    k1,k2,k12,z1,z2=phys(); sig=numpyro.sample("sig_obs",dist.LogNormal(math.log(0.05),0.7))
    A=model_accel(k1,k2,k12,z1,z2,freqs); sc=sig*jnp.median(jnp.abs(A))
    numpyro.sample("or",dist.Normal(0.,sc),obs=(jnp.real(d)-jnp.real(A)).reshape(-1))
    numpyro.sample("oi",dist.Normal(0.,sc),obs=(jnp.imag(d)-jnp.imag(A)).reshape(-1))
def model_v2(freqs,d,coords):
    k1,k2,k12,z1,z2=phys()
    sw=numpyro.sample("sig_w",dist.LogNormal(math.log(0.1),1.0))
    sth=numpyro.sample("sig_th",dist.LogNormal(math.log(0.1),1.0))
    lf=numpyro.sample("len_f",dist.LogNormal(math.log(10.0),0.6))
    r=numpyro.sample("r_split",dist.Uniform(0.,1.))
    A=model_accel(k1,k2,k12,z1,z2,freqs); w,th=F.stack_w_theta(d,A)
    R=F.schneider_R(freqs,coords,lf,0.6,r)+1e-8*jnp.eye(w.shape[0]); L=jnp.linalg.cholesky(R)
    numpyro.factor("lw",mvn0(w,L,sw)); numpyro.factor("lt",mvn0(th,L,sth))
def run(model,nw=800,ns=800,**kw):
    t0=time.time()
    mc=MCMC(NUTS(model,target_accept_prob=0.92,init_strategy=numpyro.infer.init_to_median),
            num_warmup=nw,num_samples=ns,num_chains=4,chain_method="sequential",progress_bar=False)
    mc.run(jax.random.PRNGKey(0),**kw,extra_fields=("diverging",))
    s=mc.get_samples(group_by_chain=True); div=int(jnp.sum(mc.get_extra_fields()["diverging"]))
    st=summary(s,group_by_chain=True)
    mr=max(float(np.nanmax(v["r_hat"])) for v in st.values()); me=min(float(np.nanmin(v["n_eff"])) for v in st.values())
    flat={k:np.array(v).reshape(-1,*v.shape[2:]) for k,v in s.items()}
    return dict(max_rhat=mr,min_ess=me,div_frac=div/(4*ns),runtime_s=time.time()-t0),flat

all_idx=np.arange(NF); hold=all_idx[1::4]; train=np.array([i for i in all_idx if i not in set(hold)])
def cov_v2(flat,data,S=300):
    def pos(ids):return np.concatenate([i*NMP+np.arange(NMP) for i in ids])
    tr,ho=pos(np.sort(train)),pos(np.sort(hold)); idx=np.random.default_rng(1).choice(flat['lk1'].shape[0],S,False)
    mags=np.zeros((S,len(hold),NMP))
    for s,i in enumerate(idx):
        A=np.array(model_accel(math.exp(flat['lk1'][i]),math.exp(flat['lk2'][i]),math.exp(flat['lk12'][i]),flat['z1'][i],flat['z2'][i],fj))
        sw=flat['sig_w'][i];sth=flat['sig_th'][i];lf=flat['len_f'][i];r=flat['r_split'][i]
        R=np.array(F.schneider_R(fj,cj,lf,0.6,r))+1e-8*np.eye(NF*NMP)
        lr=(np.log(data)-np.log(A)).reshape(-1)
        Rtt=R[np.ix_(tr,tr)];Rht=R[np.ix_(ho,tr)];Rhh=R[np.ix_(ho,ho)];Kc=Rht@np.linalg.inv(Rtt)
        cov=Rhh-Kc@Rht.T;cov=(cov+cov.T)/2+1e-9*np.eye(len(ho));Lc=np.linalg.cholesky(cov)
        rng=np.random.default_rng(s)
        wh=Kc@np.real(lr)[tr]+sw*(Lc@rng.standard_normal(len(ho))); thh=Kc@np.imag(lr)[tr]+sth*(Lc@rng.standard_normal(len(ho)))
        fp=A.reshape(-1).copy(); fp[ho]=A.reshape(-1)[ho]*np.exp(wh+1j*thh); mags[s]=np.abs(fp.reshape(NF,NMP))[np.sort(hold)]
    q=np.percentile(mags,[2.5,97.5],axis=0); dm=np.abs(data)[np.sort(hold)]
    return float(np.mean((dm>=q[0])&(dm<=q[1]))), float(np.mean(q[1]-q[0]))

# ---- (1) CONTROL truth=2DOF ----
SW=0.12; LF=18.0
ta,data=gen_data(hidden=False,lf_inj=LF,sw_inj=SW,seed=101)
r1,f1=run(model_v1,freqs=fj[train],d=jnp.array(data[train]))
r2,f2=run(model_v2,freqs=fj[train],d=jnp.array(data[train]),coords=cj)
c2,bw2=cov_v2(f2,data)
control=dict(
 V1=dict(max_rhat=r1['max_rhat'],min_ess=r1['min_ess'],div_frac=r1['div_frac']),
 V2=dict(max_rhat=r2['max_rhat'],min_ess=r2['min_ess'],div_frac=r2['div_frac'],coverage=c2,band_width=bw2,
   sig_w=[float(np.percentile(f2['sig_w'],q)) for q in (2.5,50,97.5)],
   sig_th=[float(np.percentile(f2['sig_th'],q)) for q in (2.5,50,97.5)],
   len_f=[float(np.percentile(f2['len_f'],q)) for q in (2.5,50,97.5)],
   r=[float(np.percentile(f2['r_split'],q)) for q in (2.5,50,97.5)]),
 injected=dict(sig_w=SW,sig_th=SIG_TH_STAR,len_f=LF,r=R_STAR))

# ---- (2) SWEEP injected len_f (truth=2DOF) ----
sweep=[]
for lf_inj in [6.0,12.0,18.0,30.0,48.0]:
    _,d=gen_data(hidden=False,lf_inj=lf_inj,sw_inj=SW,seed=200+int(lf_inj))
    rr,ff=run(model_v2,freqs=fj[train],d=jnp.array(d[train]),coords=cj)
    cc,bb=cov_v2(ff,d)
    sweep.append(dict(lf_inj=lf_inj,lf_post=[float(np.percentile(ff['len_f'],q)) for q in (2.5,50,97.5)],
                      sw_post=float(np.median(ff['sig_w'])),coverage=cc,band_width=bb,max_rhat=rr['max_rhat']))

out=dict(control=control,sweep=sweep,
  note="truth=2-DOF isolates METHOD behaviour from model-form error (the hidden-DOF case is Study A)")
json.dump(out,open(os.path.join(OUT,"phase1_summary.json"),"w"),indent=2)
np.savez(os.path.join(OUT,"phase1_arrays.npz"),
  lf_inj=np.array([s['lf_inj'] for s in sweep]),
  lf_post=np.array([s['lf_post'] for s in sweep]),
  cov=np.array([s['coverage'] for s in sweep]),
  bw=np.array([s['band_width'] for s in sweep]),
  ctrl_sigw=f2['sig_w'],ctrl_lenf=f2['len_f'],ctrl_r=f2['r_split'],ctrl_sigth=f2['sig_th'],
  inj=np.array([SW,SIG_TH_STAR,LF,R_STAR]))
print(json.dumps(out,indent=2)); print("saved phase1_summary.json")
