"""Study C (REAL DATA, no new data gathered) — suspended composite panel.

Authoritative source: the .mat files (H1 = 25 points x 3200 freqs, complex; freq 0.125-400 Hz).
FEA model: Abaqus CompPanel_SoftSupports eigenfrequencies parsed from the .dat.

Delivers (all from existing data):
  C1  real |H1| FRF characterization (log-log) with FEA mode lines overlaid.
  C2  FEM-vs-test modal correlation: peak-pick experimental modes, match to FEA modes,
      report % frequency error = the REAL model-form discrepancy floor for this panel.
  C3  Schneider T-S2 readiness: empirical frequency-correlation length of the multiplicative
      log-FRF residual (point-vs-consensus) -> a real measured ℓ_co,f (characterization, not calibration).
Outputs -> ../out/study_c_*  and ../figures/figC*.
"""
from __future__ import annotations
import json, os, re
import numpy as np
import scipy.io as sio
from scipy.signal import find_peaks
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE=os.path.dirname(os.path.abspath(__file__)); REPO=os.path.abspath(os.path.join(HERE,"..","..","..",".."))
FIG=os.path.join(HERE,"..","figures"); OUT=os.path.join(HERE,"..","out")
BASE=os.path.join(REPO,"Suspended panel modal testing","LDV test results","mat files")
DAT=os.path.join(REPO,"Suspended panel modal testing","FEA results","Abaqus Files","CompPanel_SoftSupports.dat")
plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,
    "axes.grid":True,"grid.alpha":0.25,"grid.linewidth":0.5,"figure.dpi":150,
    "savefig.bbox":"tight","figure.constrained_layout.use":True})
C_DATA="#1f77b4"; C_FEA="#d62728"; C_OK="#2a7d2a"; C_HOLD="#ff7f0e"
def stamp(fig,t): fig.text(0.01,0.005,t,fontsize=7.5,color="#777",ha="left")

# ---- load real FRF ----
H=sio.loadmat(os.path.join(BASE,"H1.mat"))["H1"]            # (25,3200) complex
fr=sio.loadmat(os.path.join(BASE,"freq.mat"))["freq"].ravel()
mag=np.abs(H); npts=H.shape[0]

# ---- parse FEA eigenfrequencies (CYCLES/TIME col) from .dat ----
fea=[]
grab=False
for ln in open(DAT,encoding="latin-1",errors="ignore"):
    if "E I G E N V A L U E" in ln: grab=True; continue
    if grab:
        m=re.match(r"\s*(\d+)\*?\s+([-0-9.E+]+)\s+([0-9.E+]+)\s+([0-9.E+]+)",ln)
        if m: fea.append((int(m.group(1)), float(m.group(4))))
        if "***NOTE" in ln and fea: break
# keep the consecutive 1,2,3... block (drops spurious pre-table matches)
start=[i for i,(lab,_) in enumerate(fea) if lab==1][-1]
fea=[f for _,f in fea[start:]]
fea=np.array(fea)
fea_all=fea.copy()                       # index k -> U3 row k (mode k+1)
fea=fea[fea>0]
fea_band=fea[(fea>=5)&(fea<=200)]

# ---- experimental peaks (mean |H1| across points, 5-200 Hz) ----
band=(fr>=5)&(fr<=200); fb=fr[band]; mm=mag[:,band].mean(0)
pk,_=find_peaks(20*np.log10(mm), distance=6, prominence=3)
exp_modes=fb[pk]

# ---- match exp -> nearest FEA, % error (the discrepancy floor) ----
matches=[]
for fe in exp_modes:
    j=int(np.argmin(np.abs(fea_band-fe))); ff=fea_band[j]
    err=(ff-fe)/fe*100.0
    if abs(err)<=12:   # accept as a matched pair
        matches.append((float(fe),float(ff),float(err)))
errs=np.array([m[2] for m in matches])
floor=dict(n_matched=len(matches),mean_abs_pct=float(np.mean(np.abs(errs))),
           median_abs_pct=float(np.median(np.abs(errs))),
           mean_signed_pct=float(np.mean(errs)),max_abs_pct=float(np.max(np.abs(errs))))

# ---- C3: frequency-correlation length of multiplicative log-FRF residual ----
# consensus = median complex FRF across points; residual r_p(f) = log(H_p) - log(consensus)
band2=(fr>=8)&(fr<=200); f2=fr[band2]
cons=np.median(np.real(H[:,band2]),0)+1j*np.median(np.imag(H[:,band2]),0)
res=np.log(H[:,band2])-np.log(cons)[None,:]              # (25, Nb) complex
w=np.real(res)                                            # log-magnitude residual
# empirical frequency autocorrelation averaged over points (normalized)
def autocorr_len(sig, f):
    sig=sig-sig.mean()
    ac=np.correlate(sig,sig,"full"); ac=ac[ac.size//2:]; ac=ac/ac[0]
    df=f[1]-f[0]
    # correlation length = first lag where ac<exp(-1)
    below=np.where(ac<np.exp(-1))[0]
    return (below[0]*df) if len(below) else (len(ac)*df)
lcf=np.median([autocorr_len(w[p],f2) for p in range(npts)])
sig_w_real=float(np.std(w))

summary=dict(
  data=dict(source="H1.mat (authoritative); .txt exports were mislabeled coherence",
            quantity="MOBILITY velocity/force, (m/s)/N; impact hammer on panel BACK at TOP-RIGHT node (Andrew, D19)",
            n_points=int(npts),n_freq=int(len(fr)),band_hz=[float(fr[0]),float(fr[-1])],
            mag_range=[float(mag.min()),float(mag.max())]),
  fea=dict(source="Abaqus CompPanel_SoftSupports.dat",n_modes_lt200=int(len(fea_band)),
           first_flexible_hz=float(fea_band.min())),
  exp_modes_hz=[float(x) for x in np.round(exp_modes,2)],
  discrepancy_floor=floor,
  schneider_real=dict(freq_corr_length_hz=float(lcf),log_mag_residual_sd=sig_w_real,
     note="measured point-vs-consensus multiplicative residual = measurement+spatial variability (characterization, not FEM calibration)"),
  matches=matches)
json.dump(summary,open(os.path.join(OUT,"study_c_summary.json"),"w"),indent=2)

# ============ FIGURES ============
# C1 real FRF + FEA lines
fig,ax=plt.subplots(figsize=(11,4))
for p in range(0,npts,6): ax.loglog(fr,mag[p],lw=0.5,color="#bcd",alpha=0.7)
ax.loglog(fb,mm,lw=1.3,color=C_DATA,label="mean |H1| (25 pts)")
for fe in fea_band: ax.axvline(fe,color=C_FEA,lw=0.6,ls=":",alpha=0.7)
ax.plot(exp_modes,mm[pk],"v",ms=6,color=C_OK,label="experimental peaks")
ax.set_xlim(5,200); ax.set_xlabel("frequency [Hz]"); ax.set_ylabel("|H1| mobility  [(m/s)/N]")
ax.legend(frameon=False,fontsize=9,loc="lower right")
ax.set_title(f"Real LDV FRF of the suspended composite panel — {len(fea_band)} FEA modes (red ⋮) in 5–200 Hz")
stamp(fig,"Study C · REAL DATA (H1.mat, 25 pts × 3200 freqs) + Abaqus FEA · authoritative .mat (the .txt exports were coherence)")
fig.savefig(os.path.join(FIG,"figC1_real_frf.png")); plt.close(fig)

# C2 FEM-vs-test matched modes
fig,(axa,axb)=plt.subplots(1,2,figsize=(11,4),gridspec_kw={"width_ratios":[1.3,1]})
fe_e=[m[0] for m in matches]; fe_f=[m[1] for m in matches]
axa.plot([0,200],[0,200],"--",color="#888",lw=1)
axa.plot(fe_e,fe_f,"o",ms=6,color=C_DATA)
axa.set_xlabel("experimental mode [Hz]"); axa.set_ylabel("matched FEA mode [Hz]")
axa.set_title(f"FEM vs test ({len(matches)} matched modes)")
axb.hist(errs,bins=12,color=C_FEA,alpha=0.8)
axb.axvline(0,color="#333",lw=1)
axb.axvline(floor['mean_signed_pct'],color=C_OK,lw=1.6,label=f"mean {floor['mean_signed_pct']:+.1f}%")
axb.set_xlabel("FEA−test frequency error [%]"); axb.set_ylabel("count")
axb.set_title(f"Discrepancy floor: |error| mean {floor['mean_abs_pct']:.1f}%, max {floor['max_abs_pct']:.1f}%")
axb.legend(frameon=False,fontsize=9)
stamp(fig,"Study C · REAL · FEA consistently stiff (positive mean error) = the real model-form discrepancy this panel needs a discrepancy term to absorb")
fig.savefig(os.path.join(FIG,"figC2_fem_vs_test.png")); plt.close(fig)

# C3 residual correlation length (Schneider T-S2 on real data)
fig,(axa,axb)=plt.subplots(1,2,figsize=(11,3.8))
p0=0; sig=w[p0]-w[p0].mean(); ac=np.correlate(sig,sig,"full"); ac=ac[ac.size//2:]/np.dot(sig,sig)
lags=np.arange(len(ac))*(f2[1]-f2[0])
axa.plot(lags[:400],ac[:400],lw=1,color=C_DATA,label="empirical (point 1)")
axa.plot(lags[:400],np.exp(-lags[:400]/lcf),lw=1.4,color=C_FEA,ls="--",label=f"exp(−Δf/ℓ), ℓ={lcf:.1f} Hz")
axa.axhline(np.exp(-1),color="#999",lw=0.7,ls=":")
axa.set_xlabel("frequency lag Δf [Hz]"); axa.set_ylabel("log-mag residual autocorr.")
axa.set_title("Measured frequency-correlation of the model/measurement error"); axa.legend(frameon=False,fontsize=8)
axb.plot(f2,w[p0],lw=0.6,color=C_DATA)
axb.set_xlabel("frequency [Hz]"); axb.set_ylabel("log|H1| − log(consensus)")
axb.set_title(f"Multiplicative residual (σ_w ≈ {sig_w_real:.2f})")
stamp(fig,"Study C · REAL · this is exactly the T-S2 quantity Schneider infers — measured here ≈ %.0f Hz (characterization, not calibration)"%lcf)
fig.savefig(os.path.join(FIG,"figC3_corr_length.png")); plt.close(fig)

print("Study C done. matched modes:",len(matches),
      "| discrepancy floor mean|err| %.2f%% (signed %+.2f%%)"%(floor['mean_abs_pct'],floor['mean_signed_pct']),
      "| real ℓ_co,f ≈ %.1f Hz"%lcf)
