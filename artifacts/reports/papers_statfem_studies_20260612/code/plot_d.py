"""Study D figure: Das/Debnath latent-mode (0 div + damping) vs eigh-through (diverges at degeneracy)."""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.join(HERE,"..")
FIG=os.path.join(ROOT,"figures"); OUT=os.path.join(ROOT,"out")
D=json.load(open(os.path.join(OUT,"study_d_summary.json")))
plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,
    "axes.grid":True,"grid.alpha":0.25,"grid.linewidth":0.5,"figure.dpi":150,
    "savefig.bbox":"tight","figure.constrained_layout.use":True})
C_LAT="#1f77b4"; C_EIG="#d62728"; C_T="#222"
def stamp(fig,t): fig.text(0.01,0.005,t,fontsize=7.5,color="#777",ha="left")

fig,(axa,axb)=plt.subplots(1,2,figsize=(11,4),gridspec_kw={"width_ratios":[1,1.25]})
# A: divergence fraction with gate
names=["D-latent\n(Das/Debnath)","D-eig\n(eigh-through)"]
dfrac=[D["D_latent"]["div_frac"]*100, D["D_eig"]["div_frac"]*100]
ndiv=[D["D_latent"]["divergences"], D["D_eig"]["divergences"]]
bars=axa.bar(names,dfrac,color=[C_LAT,C_EIG]); axa.axhline(2,color="#888",ls="--",lw=1)
axa.text(1.45,2.2,"gate 2%",fontsize=8,color="#888",ha="right")
axa.set_ylabel("divergence fraction [%]")
gap=D["truth"]["near_degenerate_pair_gap_pct"]
axa.set_title(f"NUTS divergences at a {gap:.2f}% near-degenerate pair")
for i,(d,nd) in enumerate(zip(dfrac,ndiv)): axa.text(i,d+0.4,f"{nd} div",ha="center",fontsize=9)
# B: damping recovery
tz=np.array(D["truth"]["zeta"])*100; rz=np.array(D["D_latent"]["recovered_zeta"])*100
tf=np.array(D["truth"]["freqs_hz"]); rf=np.array(D["D_latent"]["recovered_freqs_hz"])
x=np.arange(len(tz)); wd=0.36
axb.bar(x-wd/2,tz,wd,color=C_T,alpha=0.8,label="truth ζ")
axb.bar(x+wd/2,rz,wd,color=C_LAT,label="D-latent recovered ζ")
axb.set_xticks(x); axb.set_xticklabels([f"mode {i+1}\n{tf[i]:.2f} Hz" for i in range(len(tz))])
axb.set_ylabel("damping ratio ζ [%]"); axb.legend(frameon=False,fontsize=9)
axb.set_title("Das/Debnath recovers damping (mode-matching-free)")
for i in range(len(tz)):
    axb.text(i+wd/2,rz[i]+0.03,f"f={rf[i]:.2f}",ha="center",fontsize=7,color=C_LAT)
stamp(fig,"Study D · SYNTHETIC · latent complex modes (no eigensolve, no pairing) → 0 div + damping; eigh-backward 1/(λi−λj) diverges at degeneracy")
fig.savefig(os.path.join(FIG,"figD_complex_modal.png")); plt.close(fig)
print("figD written; D-latent div", D["D_latent"]["divergences"], "D-eig div", D["D_eig"]["divergences"])
