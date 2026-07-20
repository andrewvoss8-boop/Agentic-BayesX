"""Study A: discrepancy-model A/B for dynamic StatFEM FRF updating.

V1 iid complex-Gaussian likelihood (naive, treats correlated error as independent).
V2 Schneider correlated complex lognormal/normal likelihood (T-S1+T-S2), hyperparams inferred.
V3 frequency-decimated iid (cheap practitioner baseline).

Truth = 3-DOF coupled source/load; inference = 2-DOF (hidden DOF = model-form error).

Two held-out tests:
  PRIMARY  = INTERLEAVED (every 4th line held out): in-distribution. V2 predicts held-out
             discrepancy by GP-CONDITIONING on neighbour residuals (where T-S2 should beat iid).
  SECONDARY= CONTIGUOUS high-band (top 25%): extrapolation into the unmodelled 3rd-DOF physics
             (an OOD probe; expected to be hard for everyone).
Gates: all-variable convergence + held-out 95% coverage. Outputs -> ../out/.
"""
from __future__ import annotations
import json, math, os, time
import numpy as np
import jax
import jax.numpy as jnp
from jax.scipy.linalg import solve_triangular
import numpyro
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
from numpyro.diagnostics import summary
import forward as F

jax.config.update("jax_enable_x64", True)
numpyro.set_host_device_count(4)
OUT = os.path.join(os.path.dirname(__file__), "..", "out")
os.makedirs(OUT, exist_ok=True)
RNG = np.random.default_rng(20260612)

# ----------------- truth + data generation -----------------
M1, M2, M3 = 1.0, 0.6, 0.25
F1, F2, F3 = 110.0, 75.0, 220.0
Z1, Z2, Z3 = 0.015, 0.020, 0.030
NF = 56
FREQS = np.geomspace(30.0, 200.0, NF)
COORDS = np.array([0.0, 1.0]); NMP = COORDS.shape[0]
SIG_W_STAR, SIG_TH_STAR = 0.12, 0.10
LF_STAR, LZ_STAR, R_STAR = 18.0, 0.6, 0.8     # LF_STAR=18 deliberately off the V2 prior mean (~10)
SIG_IID, ADD_FRAC = 0.03, 0.015

def truth_k_c():
    w1,w2,w3 = 2*math.pi*F1, 2*math.pi*F2, 2*math.pi*F3
    k1=M1*w1**2; k2=M2*w2**2; k3=M3*w3**2
    c1=float(F.zeta_to_c(Z1,k1,M1)); c2=float(F.zeta_to_c(Z2,k2,M2)); c3=float(F.zeta_to_c(Z3,k3,M3))
    return dict(k1=k1,k2=k2,k12=k2,k23=k3,c1=c1,c2=c2,c12=c2,c23=c3)
TK = truth_k_c()
truth_accel = np.array(F.accelerance_3dof(jnp.array(FREQS), TK['k1'],TK['k2'],TK['k12'],TK['k23'],
                                          TK['c1'],TK['c2'],TK['c12'],TK['c23'], M1,M2,M3))

R_inj = np.array(F.schneider_R(jnp.array(FREQS), jnp.array(COORDS), LF_STAR, LZ_STAR, R_STAR))
n = R_inj.shape[0]; Lr = np.linalg.cholesky(R_inj + 1e-10*np.eye(n))
w_inj = SIG_W_STAR*(Lr@RNG.standard_normal(n)); th_inj = SIG_TH_STAR*(Lr@RNG.standard_normal(n))
eps = np.exp(w_inj+1j*th_inj).reshape(NF,NMP)
data = truth_accel*eps
med = np.median(np.abs(truth_accel))
data = data + ADD_FRAC*med*(RNG.standard_normal((NF,NMP))+1j*RNG.standard_normal((NF,NMP)))
data = data + SIG_IID*np.abs(data)*(RNG.standard_normal((NF,NMP))+1j*RNG.standard_normal((NF,NMP)))/math.sqrt(2)
data_mag = np.abs(data)

w1n,w2n = 2*math.pi*F1, 2*math.pi*F2
K1N,K2N = M1*w1n**2, M2*w2n**2; K12N=K2N
PRI = dict(lk_sd=0.18, lz_sd=0.35)
fj, cj = jnp.array(FREQS), jnp.array(COORDS)

# ----------------- model pieces -----------------
def model_accel(k1,k2,k12,z1,z2, freqs):
    c1=F.zeta_to_c(z1,k1,M1); c2=F.zeta_to_c(z2,k2,M2)
    return F.accelerance_2dof(freqs, k1,k2,k12, c1,c2,c2, M1,M2)

def phys_params():
    lk1=numpyro.sample("lk1",dist.Normal(math.log(K1N),PRI['lk_sd']))
    lk2=numpyro.sample("lk2",dist.Normal(math.log(K2N),PRI['lk_sd']))
    lk12=numpyro.sample("lk12",dist.Normal(math.log(K12N),PRI['lk_sd']))
    z1=numpyro.sample("z1",dist.LogNormal(math.log(Z1),PRI['lz_sd']))
    z2=numpyro.sample("z2",dist.LogNormal(math.log(Z2),PRI['lz_sd']))
    return jnp.exp(lk1),jnp.exp(lk2),jnp.exp(lk12),z1,z2

def mvn0_logpdf(x,L,sigma):
    nn=x.shape[0]; y=solve_triangular(L,x,lower=True)
    quad=jnp.sum(y*y)/(sigma**2); logdet=2*jnp.sum(jnp.log(jnp.diag(L)))+2*nn*jnp.log(sigma)
    return -0.5*(nn*jnp.log(2*jnp.pi)+logdet+quad)

def model_v1(freqs,d):
    k1,k2,k12,z1,z2=phys_params()
    sig=numpyro.sample("sig_obs",dist.LogNormal(math.log(0.05),0.7))
    A=model_accel(k1,k2,k12,z1,z2,freqs)
    scale=sig*jnp.median(jnp.abs(A))
    numpyro.sample("obs_r",dist.Normal(0.,scale),obs=(jnp.real(d)-jnp.real(A)).reshape(-1))
    numpyro.sample("obs_i",dist.Normal(0.,scale),obs=(jnp.imag(d)-jnp.imag(A)).reshape(-1))

def model_v2(freqs,d,coords):
    k1,k2,k12,z1,z2=phys_params()
    sw=numpyro.sample("sig_w",dist.LogNormal(math.log(0.1),1.0))
    sth=numpyro.sample("sig_th",dist.LogNormal(math.log(0.1),1.0))
    lf=numpyro.sample("len_f",dist.LogNormal(math.log(10.0),0.6))
    r=numpyro.sample("r_split",dist.Uniform(0.,1.))
    A=model_accel(k1,k2,k12,z1,z2,freqs)
    w,th=F.stack_w_theta(d,A)
    R=F.schneider_R(freqs,coords,lf,0.6,r)+1e-8*jnp.eye(w.shape[0]); L=jnp.linalg.cholesky(R)
    numpyro.factor("ll_w",mvn0_logpdf(w,L,sw)); numpyro.factor("ll_th",mvn0_logpdf(th,L,sth))

def run_nuts(model,name,nw=900,ns=900,**kw):
    t0=time.time()
    k=NUTS(model,target_accept_prob=0.92,init_strategy=numpyro.infer.init_to_median)
    mc=MCMC(k,num_warmup=nw,num_samples=ns,num_chains=4,chain_method="sequential",progress_bar=False)
    mc.run(jax.random.PRNGKey(0),**kw,extra_fields=("diverging",))
    s=mc.get_samples(group_by_chain=True); div=int(jnp.sum(mc.get_extra_fields()["diverging"]))
    st=summary(s,group_by_chain=True)
    mr=max(float(np.nanmax(v["r_hat"])) for v in st.values())
    me=min(float(np.nanmin(v["n_eff"])) for v in st.values())
    res=dict(name=name,max_rhat=mr,min_ess=me,divergences=div,div_frac=div/(4*ns),runtime_s=time.time()-t0)
    flat={k_:np.array(v).reshape(-1,*v.shape[2:]) for k_,v in s.items()}
    return res,flat

# ----------------- conditional / marginal predictive on a holdout -----------------
def predict_coverage(flat, variant, hold_idx, train_idx, S=400):
    """Return dict with coverage + median band arrays over the FULL band for plotting.
    V2 uses GP conditioning of the held-out log-error on the TRAIN residual; V1/V3 iid."""
    idx=RNG.choice(flat['lk1'].shape[0],size=min(S,flat['lk1'].shape[0]),replace=False)
    mags=np.full((len(idx),NF,NMP),np.nan)
    # flat positions for a freq set: pos = s*NMP + i
    def positions(freq_ids):
        return np.concatenate([fid*NMP+np.arange(NMP) for fid in freq_ids])
    tr_pos=positions(train_idx); ho_pos=positions(hold_idx)
    for sdx,i in enumerate(idx):
        k1=math.exp(flat['lk1'][i]); k2=math.exp(flat['lk2'][i]); k12=math.exp(flat['lk12'][i])
        z1=flat['z1'][i]; z2=flat['z2'][i]
        A=np.array(model_accel(k1,k2,k12,z1,z2,fj))            # [NF,2] complex
        pred=A.copy()
        if variant in ('v1','v3'):
            sig=flat['sig_obs'][i]; scale=sig*np.median(np.abs(A))
            noise=scale*(RNG.standard_normal((NF,NMP))+1j*RNG.standard_normal((NF,NMP)))
            pred=A+noise
        else:
            sw=flat['sig_w'][i]; sth=flat['sig_th'][i]; lf=flat['len_f'][i]; r=flat['r_split'][i]
            R=np.array(F.schneider_R(fj,cj,lf,0.6,r))+1e-8*np.eye(NF*NMP)
            lr=(np.log(data)-np.log(A)).reshape(-1)              # full log-error given this draw
            w_tr=np.real(lr)[tr_pos]; th_tr=np.imag(lr)[tr_pos]
            Rtt=R[np.ix_(tr_pos,tr_pos)]; Rht=R[np.ix_(ho_pos,tr_pos)]; Rhh=R[np.ix_(ho_pos,ho_pos)]
            R_inv_tt=np.linalg.inv(Rtt)
            Kc=Rht@R_inv_tt
            mu_w=Kc@w_tr; mu_th=Kc@th_tr
            cov=Rhh-Kc@Rht.T
            cov=(cov+cov.T)/2+1e-9*np.eye(cov.shape[0])
            Lc=np.linalg.cholesky(cov)
            w_h=mu_w+sw*(Lc@RNG.standard_normal(len(ho_pos)))
            th_h=mu_th+sth*(Lc@RNG.standard_normal(len(ho_pos)))
            eps_h=np.exp(w_h+1j*th_h)
            flat_pred=A.reshape(-1).copy(); flat_pred[ho_pos]=A.reshape(-1)[ho_pos]*eps_h
            pred=flat_pred.reshape(NF,NMP)
        mags[sdx]=np.abs(pred)
    q=np.nanpercentile(mags,[2.5,50,97.5],axis=0)               # [3,NF,NMP]
    band=np.transpose(q,(1,2,0))                                # [NF,NMP,3]
    lo,hi=band[:,:,0],band[:,:,2]
    inside=(data_mag>=lo)&(data_mag<=hi)
    ho_freq=np.array(sorted(hold_idx))
    return dict(coverage=float(np.mean(inside[ho_freq])),
                band_width=float(np.mean((hi-lo)[ho_freq])),
                band=band)

# ----------------- run a split -----------------
def run_split(train_idx, hold_idx, tag, variants=('v1','v2','v3')):
    out={}
    if 'v1' in variants:
        r,f=run_nuts(model_v1,f"{tag}_V1",freqs=fj[train_idx],d=jnp.array(data[train_idx]))
        c=predict_coverage(f,'v1',hold_idx,train_idx); r.update(c); out['v1']=(r,f)
    if 'v2' in variants:
        r,f=run_nuts(model_v2,f"{tag}_V2",freqs=fj[train_idx],d=jnp.array(data[train_idx]),coords=cj)
        c=predict_coverage(f,'v2',hold_idx,train_idx); r.update(c); out['v2']=(r,f)
    if 'v3' in variants:
        dec=np.array(sorted(train_idx))[::2]
        r,f=run_nuts(model_v1,f"{tag}_V3",freqs=fj[dec],d=jnp.array(data[dec]))
        c=predict_coverage(f,'v3',hold_idx,dec); r.update(c); out['v3']=(r,f)
    return out

# PRIMARY: interleaved in-distribution holdout
all_idx=np.arange(NF); hold_int=all_idx[1::4]; train_int=np.array([i for i in all_idx if i not in set(hold_int)])
prim=run_split(train_int,hold_int,"interp",('v1','v2','v3'))
# SECONDARY: contiguous high-band extrapolation probe
split=int(round(0.75*NF)); train_c=np.arange(split); hold_c=np.arange(split,NF)
sec=run_split(train_c,hold_c,"extrap",('v1','v2'))

# ----------------- save -----------------
def coupled_f(flat):
    out=[]
    for i in range(0,flat['lk1'].shape[0],4):
        k1=math.exp(flat['lk1'][i]); k2=math.exp(flat['lk2'][i]); k12=math.exp(flat['lk12'][i])
        K=np.array([[k1+k12,-k12],[-k12,k2+k12]])
        ev=np.linalg.eigvalsh(np.linalg.solve(np.diag([M1,M2]),K))
        out.append(np.sqrt(np.sort(ev))/(2*math.pi))
    return np.array(out)
Ktru=np.array([[TK['k1']+TK['k12'],-TK['k12']],[-TK['k12'],TK['k2']+TK['k12']]])
ftru=np.sqrt(np.sort(np.linalg.eigvalsh(np.linalg.solve(np.diag([M1,M2]),Ktru))))/(2*math.pi)
fpost={v:coupled_f(prim[v][1]) for v in prim}

v2f=prim['v2'][1]; v1f=prim['v1'][1]
def median_model_accel(flat):
    k1=math.exp(np.median(flat['lk1'])); k2=math.exp(np.median(flat['lk2']))
    k12=math.exp(np.median(flat['lk12'])); z1=np.median(flat['z1']); z2=np.median(flat['z2'])
    return np.array(model_accel(k1,k2,k12,z1,z2,fj)), (k1,k2,k12,z1,z2)
model_med_v2, pmed_v2 = median_model_accel(v2f)
model_med_v1, _ = median_model_accel(v1f)
np.savez(os.path.join(OUT,"study_a_arrays.npz"),
    freqs=FREQS,coords=COORDS,truth_accel=truth_accel,data=data,data_mag=data_mag,
    train_int=train_int,hold_int=hold_int,train_c=train_c,hold_c=hold_c,
    band_v1=prim['v1'][0]['band'],band_v2=prim['v2'][0]['band'],band_v3=prim['v3'][0]['band'],
    band_v1_ex=sec['v1'][0]['band'],band_v2_ex=sec['v2'][0]['band'],
    f_v1=fpost['v1'],f_v2=fpost['v2'],f_v3=fpost['v3'],ftrue=ftru,
    sig_w=v2f['sig_w'],sig_th=v2f['sig_th'],len_f=v2f['len_f'],r=v2f['r_split'],
    model_med_v2=model_med_v2, model_med_v1=model_med_v1, pmed_v2=np.array(pmed_v2),
    inj=np.array([SIG_W_STAR,SIG_TH_STAR,LF_STAR,R_STAR]))

def pack(d):
    return {k:d[k] for k in ('max_rhat','min_ess','divergences','div_frac','coverage',
                             'band_width','runtime_s')}
out=dict(
    config=dict(NF=NF,band_hz=[float(FREQS[0]),float(FREQS[-1])],nmp=NMP,
        injected=dict(sig_w=SIG_W_STAR,sig_th=SIG_TH_STAR,len_f=LF_STAR,r=R_STAR,sig_iid=SIG_IID,add_frac=ADD_FRAC),
        truth_freqs_uncoupled=[F1,F2,F3],hidden_dof=True,
        holdout=dict(interp_n=int(len(hold_int)),extrap_n=int(len(hold_c)),target_coverage=0.95)),
    primary_interleaved={v:pack(prim[v][0]) for v in prim},
    secondary_extrapolation={v:pack(sec[v][0]) for v in sec},
    coupled_f1_truth=float(ftru[0]),coupled_f2_truth=float(ftru[1]),
    v2_hyper_posterior=dict(
        sig_w=[float(np.percentile(v2f['sig_w'],q)) for q in (2.5,50,97.5)],
        sig_th=[float(np.percentile(v2f['sig_th'],q)) for q in (2.5,50,97.5)],
        len_f=[float(np.percentile(v2f['len_f'],q)) for q in (2.5,50,97.5)],
        r=[float(np.percentile(v2f['r_split'],q)) for q in (2.5,50,97.5)],
        injected_len_f=LF_STAR, injected_r=R_STAR, injected_sig_w=SIG_W_STAR, injected_sig_th=SIG_TH_STAR))
with open(os.path.join(OUT,"study_a_summary.json"),"w") as fh: json.dump(out,fh,indent=2)
print(json.dumps(dict(primary=out['primary_interleaved'],secondary=out['secondary_extrapolation']),indent=2))
print("saved out/study_a_summary.json + arrays")
