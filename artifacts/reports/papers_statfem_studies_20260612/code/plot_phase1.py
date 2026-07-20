"""Phase 1 figures: the control that isolates method behaviour from model-form error,
and the correlation-length calibration sweep. Pure numpy/matplotlib (.venv_fem_phase1)."""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.join(HERE,"..")
FIG=os.path.join(ROOT,"figures"); OUT=os.path.join(ROOT,"out")
P=json.load(open(os.path.join(OUT,"phase1_summary.json")))
SA=json.load(open(os.path.join(OUT,"study_a_summary.json")))
AP=np.load(os.path.join(OUT,"phase1_arrays.npz"))
AA=np.load(os.path.join(OUT,"study_a_arrays.npz"))
plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,
    "axes.grid":True,"grid.alpha":0.25,"grid.linewidth":0.5,"figure.dpi":150,
    "savefig.bbox":"tight","figure.constrained_layout.use":True})
C_V1="#9467bd"; C_V2="#1f77b4"; C_INJ="#d62728"; C_OK="#2a7d2a"
def stamp(fig,t): fig.text(0.01,0.005,t,fontsize=7.5,color="#777",ha="left")

# ---- P1: the decisive control (R-hat with vs without model-form error) ----
fig,ax=plt.subplots(figsize=(8,4))
groups=["V1 iid","V2 Schneider"]
withmf=[SA["primary_interleaved"]["v1"]["max_rhat"], SA["primary_interleaved"]["v2"]["max_rhat"]]
nomf=[P["control"]["V1"]["max_rhat"], P["control"]["V2"]["max_rhat"]]
x=np.arange(2); wd=0.36
ax.bar(x-wd/2,withmf,wd,color=C_V1,label="Study A: WITH model-form error (hidden DOF)")
ax.bar(x+wd/2,nomf,wd,color=C_V2,label="Control: NO model-form error (truth=2-DOF)")
ax.set_yscale("log"); ax.axhline(1.05,color="#888",ls="--",lw=1); ax.text(1.45,1.07,"gate 1.05",fontsize=8,color="#888",ha="right")
ax.set_xticks(x); ax.set_xticklabels(groups); ax.set_ylabel("max R-hat (all vars, log)")
for i,(a,b) in enumerate(zip(withmf,nomf)):
    ax.text(i-wd/2,a*1.1,f"{a:.1f}",ha="center",fontsize=8); ax.text(i+wd/2,b*1.1,f"{b:.3f}",ha="center",fontsize=8)
ax.legend(frameon=False,fontsize=8.5,loc="upper right")
ax.set_title("V1 iid non-convergence is CAUSED by model-form error — remove it and iid converges")
stamp(fig,"Phase 1 · SYNTHETIC control · V1 R-hat 24→1.00 when the hidden DOF is removed; V2 stays well-mixed either way")
fig.savefig(os.path.join(FIG,"figP1_control_convergence.png")); plt.close(fig)

# ---- P2: sponge isolation (sig_w and len_f: control recovers, Study A inflates) ----
fig,(axa,axb)=plt.subplots(1,2,figsize=(11,3.8))
inj=SA["v2_hyper_posterior"]
axa.hist(AP["ctrl_sigw"],bins=40,density=True,color=C_V2,alpha=0.8,label="control (truth=2-DOF)")
axa.hist(AA["sig_w"],bins=40,density=True,color="#bbbbbb",alpha=0.7,label="Study A (hidden DOF)")
axa.axvline(inj["injected_sig_w"],color=C_INJ,lw=1.8,label=f"injected {inj['injected_sig_w']:g}")
axa.set_xlabel("σ_w (log-mag discrepancy sd)"); axa.set_ylabel("posterior density"); axa.legend(frameon=False,fontsize=8)
axa.set_title("σ_w: recovered without model-form error")
axb.hist(AP["ctrl_lenf"],bins=40,density=True,color=C_V2,alpha=0.8,label="control")
axb.hist(AA["len_f"],bins=40,density=True,color="#bbbbbb",alpha=0.7,label="Study A")
axb.axvline(inj["injected_len_f"],color=C_INJ,lw=1.8,label=f"injected {inj['injected_len_f']:g}")
axb.set_xlabel("ℓ_f (freq corr. length, Hz)"); axb.legend(frameon=False,fontsize=8)
axb.set_title("ℓ_f: recovered without model-form error")
stamp(fig,"Phase 1 · SYNTHETIC · the discrepancy 'sponge' = model-form error absorption; with none, V2 measures the injected error correctly")
fig.savefig(os.path.join(FIG,"figP2_sponge_isolation.png")); plt.close(fig)

# ---- P3: correlation-length calibration sweep ----
fig,ax=plt.subplots(figsize=(7.5,4.2))
lfi=AP["lf_inj"]; lfp=AP["lf_post"]   # [:,3] 2.5/50/97.5
ax.plot([0,55],[0,55],"--",color="#888",lw=1,label="y = x (perfect)")
ax.errorbar(lfi,lfp[:,1],yerr=[lfp[:,1]-lfp[:,0],lfp[:,2]-lfp[:,1]],fmt="o",ms=7,
            color=C_V2,capsize=4,label="inferred ℓ_f (median, 95% CI)")
for i,lf in enumerate(lfi):
    ax.annotate(f"{AP['cov'][i]*100:.0f}%",(lfi[i],lfp[i,1]),textcoords="offset points",
                xytext=(8,-2),fontsize=8,color=C_OK)
ax.set_xlabel("injected ℓ_f* [Hz]"); ax.set_ylabel("posterior ℓ_f [Hz]")
ax.set_title("The correlation length is learnable — ℓ_f tracks the injected value")
ax.legend(frameon=False,fontsize=9,loc="upper left")
stamp(fig,"Phase 1 · SYNTHETIC (truth=2-DOF) · green = held-out coverage (89–100% across regimes) · wide CI = ℓ_f is a soft parameter")
fig.savefig(os.path.join(FIG,"figP3_corr_length_calibration.png")); plt.close(fig)
print("phase1 figures written")
