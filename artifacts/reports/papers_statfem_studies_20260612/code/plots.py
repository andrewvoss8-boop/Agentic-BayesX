"""Tufte-style figures + GIF for Study A and the real-data motivation (Study C).

Reads ../out/study_a_arrays.npz and ../out/study_a_summary.json. Pure numpy/matplotlib
(no jax) so it runs in .venv_fem_phase1. Frequency axes log; direct labels; provenance
stamps; residual/zoom; no chartjunk. Every numeric figure is SYNTHETIC unless marked REAL.
"""
from __future__ import annotations
import json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager  # noqa

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "out")
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)
A = np.load(os.path.join(OUT, "study_a_arrays.npz"))
S = json.load(open(os.path.join(OUT, "study_a_summary.json")))

freqs = A["freqs"]; coords = A["coords"]; NF = len(freqs); NMP = len(coords)
data_mag = A["data_mag"]; truth = A["truth_accel"]
train_int = A["train_int"]; hold_int = A["hold_int"]
train_c = A["train_c"]; hold_c = A["hold_c"]
ftrue = A["ftrue"]
C_TRUTH="#222222"; C_V1="#9467bd"; C_V2="#1f77b4"; C_V3="#2ca02c"; C_DATA="#d62728"; C_HOLD="#ff7f0e"
plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,
    "axes.grid":True,"grid.alpha":0.25,"grid.linewidth":0.5,"figure.dpi":150,
    "axes.titlesize":11.5,"savefig.bbox":"tight","figure.constrained_layout.use":True})

def stamp(ax, txt):
    ax.figure.text(0.01,0.005,txt,fontsize=7.5,color="#777",ha="left")

# ---------- numpy forward + schneider (for the GIF) ----------
def accel2(freqs,k1,k2,k12,z1,z2,m1=1.0,m2=0.6):
    w=2*np.pi*freqs; c1=2*z1*np.sqrt(k1*m1); c2=2*z2*np.sqrt(k2*m2); c12=c2
    M=np.array([[m1,0],[0,m2]]); K=np.array([[k1+k12,-k12],[-k12,k2+k12]])
    Cc=np.array([[c1+c12,-c12],[-c12,c2+c12]]); out=np.zeros((len(freqs),2),complex)
    for i,wi in enumerate(w):
        Z=K+1j*wi*Cc-(wi**2)*M; H=np.linalg.inv(Z); out[i]=-(wi**2)*H[:,0]
    return out
def schR(freqs,coords,lf,lz,r):
    df=np.abs(freqs[:,None]-freqs[None,:]); Rff=np.exp(-df/lf)
    dz=np.abs(coords[:,None]-coords[None,:]); Rzz=np.exp(-dz/lz)
    return r*np.kron(Rff,np.eye(len(coords)))+(1-r)*np.kron(np.eye(len(freqs)),Rzz)

# =================== FIG 1: clean truth vs observed ===================
fig,axs=plt.subplots(1,2,figsize=(10,3.8))
for j,ax in enumerate(axs):
    ax.loglog(freqs,np.abs(truth[:,j]),color=C_TRUTH,lw=1.6,label="clean truth (3-DOF)")
    ax.loglog(freqs[train_int],data_mag[train_int,j],"o",ms=4,color=C_DATA,label="observed (train)")
    ax.loglog(freqs[hold_int],data_mag[hold_int,j],"s",ms=5,mfc="none",color=C_HOLD,label="held-out (interleaved)")
    ax.set_xlabel("frequency  [Hz]"); ax.set_title(f"accelerance  $|a_{j}/F_0|$  [1/kg]")
    for f0 in ftrue: ax.axvline(f0,color="#bbb",lw=0.7,ls=":")
axs[0].set_ylabel("magnitude")
axs[0].legend(frameon=False,fontsize=8,loc="lower left")
stamp(axs[0],"Study A  ·  SYNTHETIC  ·  injected Schneider error σw*=0.12 σθ*=0.10 ℓf*=18Hz r*=0.8  ·  dotted = coupled fn")
fig.suptitle("Truth vs observed dense FRF — the 2-DOF inference model omits a hidden 3rd DOF (model-form error)",fontsize=11)
fig.savefig(os.path.join(FIG,"fig1_truth_vs_data.png")); plt.close(fig)

# =================== FIG 2: HEADLINE coverage (interleaved holdout, ch0) ===================
b1=A["band_v1"][:,0,:]; b2=A["band_v2"][:,0,:]   # [NF,3] lo/med/hi for channel 0
p=S["primary_interleaved"]
fig,(ax,axr)=plt.subplots(1,2,figsize=(11,4),gridspec_kw={"width_ratios":[2,1]})
ax.fill_between(freqs,b1[:,0],b1[:,2],color=C_V1,alpha=0.18,label="V1 iid 95% band")
ax.fill_between(freqs,b2[:,0],b2[:,2],color=C_V2,alpha=0.30,label="V2 Schneider 95% band")
ax.plot(freqs,b2[:,1],color=C_V2,lw=1.2)
ax.plot(freqs[hold_int],data_mag[hold_int,0],"s",ms=6,mfc="none",mec=C_HOLD,mew=1.6,label="held-out data")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("frequency [Hz]")
ax.set_ylabel("$|a_0/F_0|$  [1/kg]")
ax.legend(frameon=False,fontsize=8,loc="lower left")
ax.set_title("Held-out predictive bands (in-distribution interleaved holdout, drive point)")
txt=(f"V2 Schneider: coverage {p['v2']['coverage']*100:.0f}% · mean band {p['v2']['band_width']:.2f} · "
     f"R-hat {p['v2']['max_rhat']:.3f} ✓\n"
     f"V1 iid:        coverage {p['v1']['coverage']*100:.0f}% · mean band {p['v1']['band_width']:.2f} · "
     f"R-hat {p['v1']['max_rhat']:.1f}  NOT CONVERGED")
ax.text(0.02,0.97,txt,transform=ax.transAxes,fontsize=8.5,va="top",
        bbox=dict(boxstyle="round",fc="white",ec="#ccc"))
# zoom: a held-out cluster, linear, band widths
zlo,zhi=120,175
mask=(freqs>=zlo)&(freqs<=zhi)
axr.fill_between(freqs[mask],b1[mask,0],b1[mask,2],color=C_V1,alpha=0.18)
axr.fill_between(freqs[mask],b2[mask,0],b2[mask,2],color=C_V2,alpha=0.30)
hm=hold_int[(freqs[hold_int]>=zlo)&(freqs[hold_int]<=zhi)]
axr.plot(freqs[hm],data_mag[hm,0],"s",ms=6,mfc="none",mec=C_HOLD,mew=1.6)
axr.set_xlabel("frequency [Hz]"); axr.set_title(f"zoom {zlo}–{zhi} Hz (linear)")
axr.set_yscale("log")
stamp(ax,"Study A · SYNTHETIC · NUTS 4×900 · V2 conditions held-out discrepancy on neighbour residuals (Schneider T-S2)")
fig.savefig(os.path.join(FIG,"fig2_headline_coverage.png")); plt.close(fig)

# =================== FIG 3: convergence + coverage small multiples ===================
fig,(axc,axv)=plt.subplots(1,2,figsize=(10,3.8))
labels=["V2\nSchneider","V1\niid","V3\ndecim."]; keys=["v2","v1","v3"]; cols=[C_V2,C_V1,C_V3]
rh=[S["primary_interleaved"][k]["max_rhat"] for k in keys]
cov=[S["primary_interleaved"][k]["coverage"] for k in keys]
axc.bar(labels,rh,color=cols); axc.set_yscale("log"); axc.axhline(1.05,color="#888",ls="--",lw=1)
axc.text(2.45,1.07,"gate 1.05",fontsize=8,color="#888",ha="right")
axc.set_ylabel("max R-hat (all vars, log)"); axc.set_title("Convergence gate")
for i,v in enumerate(rh): axc.text(i,v*1.1,f"{v:.2f}",ha="center",fontsize=8)
axv.bar(labels,cov,color=cols); axv.axhline(0.95,color="#888",ls="--",lw=1)
axv.text(2.45,0.96,"target 0.95",fontsize=8,color="#888",ha="right")
axv.set_ylabel("held-out coverage"); axv.set_ylim(0,1.05); axv.set_title("In-distribution held-out coverage")
for i,v in enumerate(cov): axv.text(i,v+0.02,f"{v*100:.0f}%",ha="center",fontsize=8)
stamp(axc,"Study A · SYNTHETIC · only V2 (structured correlated likelihood) clears the convergence gate; V1/V3 coverage NOT trustworthy")
fig.suptitle("Only the Schneider-correlated discrepancy mixes; the iid / decimated likelihoods do not",fontsize=11)
fig.savefig(os.path.join(FIG,"fig3_convergence_coverage.png")); plt.close(fig)

# =================== FIG 4: coupled f1 posterior ===================
fig,ax=plt.subplots(figsize=(7,3.6))
f_v2=A["f_v2"][:,0]; f_v1=A["f_v1"][:,0]
ax.hist(f_v2,bins=40,color=C_V2,alpha=0.8,density=True,label="V2 Schneider (converged)")
ax.hist(f_v1,bins=40,color=C_V1,alpha=0.4,density=True,label="V1 iid (NOT converged)")
ax.axvline(ftrue[0],color=C_TRUTH,lw=1.6,ls="-",label=f"truth-projected f1 = {ftrue[0]:.1f} Hz")
ax.set_xlabel("coupled first natural frequency  f1  [Hz]"); ax.set_ylabel("posterior density")
ax.legend(frameon=False,fontsize=8); ax.set_title("Physical-parameter posterior (coupled f1)")
stamp(ax,"Study A · SYNTHETIC · V1 not-converged (R-hat 24) → its spread is a sampler artifact, shown for contrast only")
fig.savefig(os.path.join(FIG,"fig4_param_posterior.png")); plt.close(fig)

# =================== FIG 5: hyperparameter recovery (V2) ===================
fig,axs=plt.subplots(1,4,figsize=(13,3.2))
specs=[("sig_w","σ_w (log-mag sd)",S["v2_hyper_posterior"]["injected_sig_w"]),
       ("sig_th","σ_θ (phase sd, rad)",S["v2_hyper_posterior"]["injected_sig_th"]),
       ("len_f","ℓ_f (freq corr. len, Hz)",S["v2_hyper_posterior"]["injected_len_f"]),
       ("r","r (space/freq split)",S["v2_hyper_posterior"]["injected_r"])]
for ax,(key,lab,inj) in zip(axs,specs):
    arr=A[{"sig_w":"sig_w","sig_th":"sig_th","len_f":"len_f","r":"r"}[key]]
    ax.hist(arr,bins=40,color=C_V2,alpha=0.8,density=True)
    ax.axvline(inj,color=C_DATA,lw=1.8,label=f"injected {inj:g}")
    ax.set_xlabel(lab); ax.legend(frameon=False,fontsize=8)
axs[0].set_ylabel("posterior density")
fig.suptitle("Discrepancy hyperparameters are NOT recovered — the discrepancy is a model-error sponge "
             "(only r is recovered)",fontsize=10.5)
stamp(axs[0],"Study A · SYNTHETIC · σ_θ posterior ≫ injected: phase residual is dominated by 2-DOF-vs-3-DOF model error")
fig.savefig(os.path.join(FIG,"fig5_hyper_recovery.png")); plt.close(fig)

# =================== FIG 6: extrapolation honest negative ===================
b2e=A["band_v2_ex"][:,0,:]
fig,ax=plt.subplots(figsize=(8,3.8))
ax.fill_between(freqs,b2e[:,0],b2e[:,2],color=C_V2,alpha=0.25,label="V2 95% band (trained on low band)")
ax.plot(freqs,np.abs(truth[:,0]),color=C_TRUTH,lw=1.2,label="clean truth")
ax.plot(freqs[train_c],data_mag[train_c,0],"o",ms=3,color=C_DATA,label="train (low band)")
ax.plot(freqs[hold_c],data_mag[hold_c,0],"s",ms=6,mfc="none",mec=C_HOLD,mew=1.6,label="held-out (high band)")
ax.axvspan(freqs[hold_c][0],freqs[-1],color="#ffeccc",alpha=0.5)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("frequency [Hz]"); ax.set_ylabel("$|a_0/F_0|$ [1/kg]")
ax.legend(frameon=False,fontsize=8,loc="lower left")
se=S["secondary_extrapolation"]["v2"]
ax.set_title(f"Extrapolation probe: even converged V2 covers only {se['coverage']*100:.0f}% in the high band")
stamp(ax,"Study A · SYNTHETIC · shaded = held-out high band (hidden-DOF physics) · stationary discrepancy can't extrapolate (OOD lesson)")
fig.savefig(os.path.join(FIG,"fig6_extrapolation_negative.png")); plt.close(fig)

# =================== FIG 7: REAL suspended-panel data audit (Study C motivation) ===================
def parse_complex_txt(path,maxtok=400000):
    s=open(path,encoding="latin-1").read().replace("\r","\n")
    toks=[t for t in s.replace("\t"," ").split() if t]
    return toks
try:
    REPO=os.path.abspath(os.path.join(HERE,"..","..","..",".."))   # cwd-independent
    base=os.path.join(REPO,"Suspended panel modal testing","LDV test results","mat files")
    fr=open(os.path.join(base,"frequency.txt"),encoding="latin-1").read()
    fvals=np.array([float(x) for x in fr.replace("\r"," ").split() if x.strip()])
    h1=open(os.path.join(base,"H1.txt"),encoding="latin-1").read().replace("\r","\n")
    coh=open(os.path.join(base,"coherence.txt"),encoding="latin-1").read().replace("\r","\n")
    def first_complex(s,k=12):
        toks=[t for t in s.replace("\t"," ").split("\n")[0].split("\t") if t.strip()]
        if len(toks)<k:  # maybe space-joined complex; fallback grab numbers
            raw=s.split("\n")[0]
            return raw
        return toks[:k]
    def to_c(t):
        return complex(t.replace(" ","").replace("i","j"))
    # first ROW of H1.txt = one measurement point's spectrum over all 3200 frequencies
    row0=[t for t in h1.split("\n")[0].split("\t") if t.strip()]
    h1c=np.array([to_c(t) for t in row0])
    coh0=[t for t in coh.split("\n")[0].split("\t") if t.strip()]
    cohc=np.array([to_c(t) for t in coh0])
    nfq=min(len(h1c),len(fvals)); x=fvals[:nfq]; y=np.abs(h1c[:nfq])
    fig,(axa,axb)=plt.subplots(1,2,figsize=(11,3.9))
    axa.semilogx(x,y,lw=0.7,color=C_V2)
    axa.set_xlabel("frequency [Hz]"); axa.set_ylabel("|H1.txt|, row 1")
    axa.set_title("Real LDV export, point 1 spectrum")
    axa.text(0.02,0.12,f"values bounded in [0,1] with dips →\nlooks like COHERENCE, not an FRF magnitude\n"
             f"(an FRF spans orders of magnitude w/ resonance peaks)",
             transform=axa.transAxes,fontsize=8,va="bottom",color=C_DATA)
    axa.text(0.02,0.96,f"grid: {fvals.min():g}–{fvals.max():g} Hz · df={fvals[1]-fvals[0]:g} · n={len(fvals)} · 96 pts",
             transform=axa.transAxes,fontsize=8,va="top")
    n=min(len(h1c),len(cohc))
    axb.plot(np.abs(h1c[:n]),np.abs(cohc[:n]),".",ms=3,color=C_DATA)
    lim=[0,max(np.abs(h1c[:n]).max(),np.abs(cohc[:n]).max())]
    axb.plot(lim,lim,"--",color="#888",lw=1)
    axb.set_xlabel("|H1.txt|"); axb.set_ylabel("|coherence.txt|")
    axb.set_title("coherence.txt == H1.txt (identical)")
    axb.text(0.04,0.9,"exports are byte-identical →\nmislabeled; use the .mat files\n→ audit BEFORE any likelihood",
             transform=axb.transAxes,fontsize=8,va="top",color=C_DATA)
    stamp(axa,"Study C motivation · REAL DATA (suspended composite panel, LDV) · authoritative source = H1.mat/accel.mat/freq.mat")
    fig.savefig(os.path.join(FIG,"fig7_real_panel_audit.png")); plt.close(fig)
    REAL_OK=True
except Exception as e:
    REAL_OK=False
    print("real-data figure skipped:",repr(e))

# =================== FIG 8: graphical model (schematic) ===================
fig,ax=plt.subplots(figsize=(9,4)); ax.axis("off")
def box(x,y,w,h,t,fc):
    ax.add_patch(plt.Rectangle((x,y),w,h,fc=fc,ec="#333",lw=1.2))
    ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=9)
def arrow(x0,y0,x1,y1):
    ax.annotate("",xy=(x1,y1),xytext=(x0,y0),arrowprops=dict(arrowstyle="-|>",color="#333",lw=1.3))
box(0.02,0.55,0.20,0.18,"physics θ\n(k1,k2,k12,ζ1,ζ2)","#dbe9f6")
box(0.02,0.18,0.20,0.18,"discrepancy hyper\nσ_w,σ_θ,ℓ_f,r","#fde0c8")
box(0.30,0.55,0.20,0.18,"FEM forward\nM(θ): accelerance","#dbe9f6")
box(0.30,0.18,0.20,0.18,"Schneider error ε\nlog ε ~ N(0,Σ(σ,ℓ,r))","#fde0c8")
box(0.58,0.37,0.18,0.18,"data = M(θ)∘ε\n(dense FRF)","#e8e8e8")
box(0.82,0.37,0.16,0.18,"held-out\ncoverage gate","#d8f0d8")
arrow(0.22,0.64,0.30,0.64); arrow(0.22,0.27,0.30,0.30)
arrow(0.50,0.62,0.58,0.50); arrow(0.50,0.27,0.58,0.42)
arrow(0.76,0.46,0.82,0.46)
ax.text(0.5,0.95,"StatFEM backbone + Schneider correlated complex discrepancy (Study A V2)",
        ha="center",fontsize=11)
ax.text(0.5,0.02,"orthogonal OUTPUT-space discrepancy on the FRF (vision §5.2) · trust gate = held-out coverage (vision §7)",
        ha="center",fontsize=8,color="#666")
ax.set_xlim(0,1); ax.set_ylim(0,1)
fig.savefig(os.path.join(FIG,"fig8_graphical_model.png")); plt.close(fig)

# =================== GIF: correlation-length sweep (the lever) ===================
import glob
from PIL import Image
pmed=A["pmed_v2"]; k1,k2,k12,z1,z2=pmed
model=accel2(freqs,k1,k2,k12,z1,z2)            # [NF,2] complex
sw=float(np.median(A["sig_w"])); sth=float(np.median(A["sig_th"])); r=float(np.median(A["r"]))
lf_med=float(np.median(A["len_f"]))
def cond_band(lf):
    R=schR(freqs,coords,lf,0.6,r)+1e-8*np.eye(NF*NMP)
    def pos(ids): return np.concatenate([i*NMP+np.arange(NMP) for i in ids])
    tr=pos(np.sort(train_int)); ho=pos(np.sort(hold_int))
    lr=(np.log(A["data"])-np.log(model)).reshape(-1)
    rng=np.random.default_rng(7); mags=np.zeros((300,NF))
    Rtt=R[np.ix_(tr,tr)]; Rht=R[np.ix_(ho,tr)]; Rhh=R[np.ix_(ho,ho)]
    Kc=Rht@np.linalg.inv(Rtt); cov=Rhh-Kc@Rht.T; cov=(cov+cov.T)/2+1e-9*np.eye(len(ho))
    Lc=np.linalg.cholesky(cov)
    muw=Kc@np.real(lr)[tr]; muth=Kc@np.imag(lr)[tr]
    for s in range(300):
        wh=muw+sw*(Lc@rng.standard_normal(len(ho))); th=muth+sth*(Lc@rng.standard_normal(len(ho)))
        fp=model.reshape(-1).copy(); fp[ho]=model.reshape(-1)[ho]*np.exp(wh+1j*th)
        mags[s]=np.abs(fp.reshape(NF,NMP))[:,0]
    q=np.percentile(mags,[2.5,97.5],axis=0)
    lo,hi=q[0,np.sort(hold_int)],q[1,np.sort(hold_int)]
    dm=data_mag[np.sort(hold_int),0]
    cov_frac=float(np.mean((dm>=lo)&(dm<=hi)))
    width=float(np.mean(hi-lo))
    return q, cov_frac, width
frames=[]
lfs=np.geomspace(2.0,120.0,24)
tmpd=os.path.join(FIG,"_gifframes"); os.makedirs(tmpd,exist_ok=True)
for i,lf in enumerate(lfs):
    q,cov_frac,width=cond_band(lf)
    fig,ax=plt.subplots(figsize=(7.2,4))
    ax.fill_between(freqs,q[0],q[1],color=C_V2,alpha=0.28)
    ax.plot(freqs,np.abs(model[:,0]),color=C_V2,lw=1.0,label="fitted model")
    ax.plot(freqs[hold_int],data_mag[hold_int,0],"s",ms=6,mfc="none",mec=C_HOLD,mew=1.6,label="held-out data")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("frequency [Hz]"); ax.set_ylabel("$|a_0/F_0|$ [1/kg]")
    ax.set_ylim(np.abs(model[:,0]).min()*0.3, data_mag[:,0].max()*3)
    ax.axvline(0,color="none")
    ax.set_title("Correlation length ℓ_f sets the effective independent-data count")
    ax.text(0.02,0.97,f"ℓ_f = {lf:5.1f} Hz   held-out coverage {cov_frac*100:3.0f}%   mean band {width:4.2f}",
            transform=ax.transAxes,fontsize=9,va="top",
            bbox=dict(boxstyle="round",fc="white",ec="#ccc"))
    bar_x=0.02+0.0; # marker for inferred lf
    ax.text(0.02,0.06,f"inferred ℓ_f median = {lf_med:.0f} Hz (injected {S['v2_hyper_posterior']['injected_len_f']:g})",
            transform=ax.transAxes,fontsize=8,color="#666")
    ax.legend(frameon=False,fontsize=8,loc="lower left")
    stamp(ax,"Study A · SYNTHETIC · Schneider T-S2 conditional predictive · small ℓ_f → wide bands; large ℓ_f → oversmooth")
    fp=os.path.join(tmpd,f"f{i:02d}.png"); fig.savefig(fp,dpi=110); plt.close(fig); frames.append(fp)
imgs=[Image.open(f) for f in frames]
seq=imgs+imgs[::-1]
seq[0].save(os.path.join(FIG,"gif_corr_length_sweep.gif"),save_all=True,append_images=seq[1:],
            duration=260,loop=0)
for f in frames: os.remove(f)
os.rmdir(tmpd)

print("figures written to", FIG)
print("REAL_OK", REAL_OK)
