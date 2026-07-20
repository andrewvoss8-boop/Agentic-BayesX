"""Study G figures (figG1-figG6). Runs in .venv_fem_phase1 (numpy/matplotlib/scipy only)."""
from __future__ import annotations
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FIG = os.path.join(ROOT, "figures"); OUT = os.path.join(ROOT, "out")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
D = np.load(os.path.join(OUT, "ums_data.npz"), allow_pickle=True)
H = np.load(os.path.join(OUT, "ums2_headline.npz"), allow_pickle=True)
S = json.load(open(os.path.join(OUT, "ums2_summary.json")))
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5, "figure.dpi": 150,
    "savefig.bbox": "tight", "figure.constrained_layout.use": True})
C_T="#222222"; C_U="#1f77b4"; C_I="#9467bd"; C_DET="#7f7f7f"; C_TR="#d62728"; C_OK="#2a7d2a"; C_H="#ff7f0e"
def stamp(fig,t): fig.text(0.01,0.005,t,fontsize=7.5,color="#777",ha="left")

F_GEN=D["F_GEN"]; F_INF=D["F_INF"]; data_gen=D["data_gen"]; Hc=D["H_clean_gen"]
scan=list(D["scan"]); hold=list(D["hold_nodes"]); obs=list(D["obs_nodes"]); xy=D["xy"]
show_i=scan.index(int(D["showcase"]))
ru=S["unified"]; ri=S["iid"]; qu=S["qoi_unified"]; qi=S["qoi_iid"]

# ---------------- figG1: realism side-by-side (REAL vs SYNTHETIC) ----------------
import scipy.io as sio
base=os.path.join(REPO,"Suspended panel modal testing","LDV test results","mat files")
H1=sio.loadmat(os.path.join(base,"H1.mat"))["H1"]; fr=sio.loadmat(os.path.join(base,"freq.mat"))["freq"].ravel()
fig,axs=plt.subplots(1,2,figsize=(11.5,4),sharey=False)
axs[0].loglog(fr,np.abs(H1[6]),lw=0.5,color=C_U)
axs[0].set_xlim(1,400); axs[0].set_title("REAL: suspended panel LDV |H1|, one point")
axs[0].set_xlabel("frequency [Hz]"); axs[0].set_ylabel("|FRF| (log)")
axs[1].loglog(F_GEN,np.abs(data_gen[:,show_i]),lw=0.5,color=C_TR,label="synthetic data")
axs[1].loglog(F_GEN,np.abs(Hc[:,show_i]),lw=0.8,color=C_T,alpha=0.6,label="clean truth")
axs[1].axhline(float(D["FLOOR"]),color="#999",lw=0.8,ls=":")
axs[1].text(2.2,float(D["FLOOR"])*1.3,"noise floor",fontsize=8,color="#777")
axs[1].axvspan(2,8,color="#f3e2c8",alpha=0.6); axs[1].text(2.6,axs[1].get_ylim()[0]*3,"suspension/\nlow-f junk",fontsize=7,color="#996")
axs[1].set_xlim(2,100); axs[1].set_title("SYNTHETIC: Study G panel twin, held-out point")
axs[1].set_xlabel("frequency [Hz]"); axs[1].legend(frameon=False,fontsize=8,loc="upper right")
fig.suptitle("The synthetic data carries the real data's pathologies: dense modes, antiresonance floor, low-f junk, calibration scatter",fontsize=11)
stamp(fig,"Study G · LEFT REAL (H1.mat pt 7) · RIGHT SYNTHETIC (grid-panel twin, mult. 2% + floor + ±0.5 dB gains + 1/f junk; NO injected Schneider field — model error is genuine structure)")
fig.savefig(os.path.join(FIG,"figG1_realism.png")); plt.close(fig)

# ---------------- figG2: graphical model ----------------
fig,ax=plt.subplots(figsize=(10.5,4.6)); ax.axis("off")
def box(x,y,w,h,t,fc,fs=9):
    ax.add_patch(plt.Rectangle((x,y),w,h,fc=fc,ec="#333",lw=1.1)); ax.text(x+w/2,y+h/2,t,ha="center",va="center",fontsize=fs)
def arr(x0,y0,x1,y1):
    ax.annotate("",xy=(x1,y1),xytext=(x0,y0),arrowprops=dict(arrowstyle="-|>",color="#333",lw=1.2))
box(0.01,0.62,0.18,0.24,"FEM θ (statFEM)\ns_g(4) group stiffness\na0,a1 Rayleigh","#dbe9f6")
box(0.25,0.62,0.21,0.24,"eigh K̃(θ) (B×B)\n→ shapes c, freqs f\n(PHYSICS-BOUND,\ngeneralize spatially)","#d8f0d8")
box(0.01,0.30,0.18,0.20,"global damping gz\n→ complex λ_m (D/D)","#d8f0d8")
box(0.01,0.04,0.18,0.20,"discrepancy (S)\nσ_w,σ_θ,ℓ_f,ℓ_z","#fde0c8")
box(0.52,0.55,0.21,0.22,"residue FRF H(ω)\n(no eigensolve loop)","#d8f0d8")
box(0.50,0.16,0.25,0.22,"data = H + (|H|+κ)·r\ncorrelated complex r (S)","#fde0c8")
box(0.80,0.34,0.18,0.22,"held-out QOI\ncoverage GATE\n(statFEM trust)","#f6dcdc")
arr(0.19,0.74,0.25,0.74); arr(0.46,0.70,0.55,0.66)
arr(0.19,0.40,0.55,0.60); arr(0.19,0.14,0.50,0.24)
arr(0.62,0.55,0.62,0.38); arr(0.75,0.27,0.80,0.40)
ax.text(0.5,0.95,"UMS-FEM (production) — physics-bound shapes + Das/Debnath damping + Schneider discrepancy",ha="center",fontsize=11)
ax.text(0.5,0.90,"(free-latent-shape variant 'UMS-full' did NOT generalize — documented negative)",ha="center",fontsize=8.5,color="#a33")
ax.set_xlim(0,1); ax.set_ylim(0,1)
stamp(fig,"Study G · method schematic · D/D=Das/Debnath, S=Schneider · full definition in method_ums.md")
fig.savefig(os.path.join(FIG,"figG2_graphical_model.png")); plt.close(fig)

# ---------------- figG3: headline held-out showcase ----------------
lo,md,hi=np.percentile(H["showU"],[2.5,50,97.5],0)
lop,mdp,hip=np.percentile(H["showU_phys"],[2.5,50,97.5],0)
truth_show=np.abs(D["H_clean_inf"][:,[scan.index(n) for n in hold][hold.index(int(D["showcase"]))]])
truth_show=np.abs(D["H_clean_inf"][:,scan.index(int(D["showcase"]))])
fig,(ax,axq)=plt.subplots(1,2,figsize=(12,4.2),gridspec_kw={"width_ratios":[2.2,1]})
ax.fill_between(F_INF,lop,hip,color=C_OK,alpha=0.18,label="physics-only 95% (latent modes)")
ax.fill_between(F_INF,lo,hi,color=C_U,alpha=0.30,label="physics+discrepancy 95%")
ax.plot(F_INF,truth_show,color=C_T,lw=1.1,label="clean truth (never measured)")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("frequency [Hz]"); ax.set_ylabel("|accelerance|")
ax.set_title(f"Held-out point INSIDE the soft patch (node {int(D['showcase'])}) — prediction at a never-measured location")
ax.legend(frameon=False,fontsize=8,loc="lower right")
inside=float(np.mean((truth_show>=lo)&(truth_show<=hi)))
ax.text(0.02,0.97,f"line coverage {inside*100:.0f}% · R-hat {ru['max_rhat']:.3f} · ESS {ru['min_ess']:.0f} · div {ru['divergences']}",
        transform=ax.transAxes,fontsize=8.5,va="top",bbox=dict(boxstyle="round",fc="white",ec="#ccc"))
# grid mini-map
axm=ax.inset_axes([0.04,0.06,0.25,0.32]); axm.set_xticks([]); axm.set_yticks([])
axm.scatter(xy[:,0],xy[:,1],s=8,color="#ddd")
axm.scatter(xy[obs,0],xy[obs,1],s=14,color=C_U,label="observed")
axm.scatter(xy[hold,0],xy[hold,1],s=22,marker="s",fc="none",ec=C_H)
axm.scatter(xy[[int(D["showcase"])],0],xy[[int(D["showcase"])],1],s=40,marker="s",fc="none",ec=C_TR,lw=1.6)
axm.scatter(xy[[int(D["drive"])],0],xy[[int(D["drive"])],1],s=30,marker="*",color=C_T)
axm.set_title("scan map",fontsize=7)
# QOI panel
qA=H["qoiA_u"]; tA=D["QA_true"]
for h in range(5):
    loq,mq,hq=np.percentile(qA[:,h],[2.5,50,97.5])
    axq.plot([h,h],[loq,hq],color=C_U,lw=3,alpha=0.7)
    axq.plot(h,mq,"o",color=C_U,ms=5)
    axq.plot(h,tA[h],"_",color=C_T,ms=16,mew=2)
    axq.plot(h,D["QA_det"][h],"x",color=C_DET,ms=7)
axq.set_xticks(range(5)); axq.set_xticklabels([f"n{n}" for n in hold],fontsize=8)
axq.set_yscale("log"); axq.set_ylabel("peak |accelerance| 10–60 Hz")
axq.set_title("held-out QOI-A: interval vs truth (—) vs nominal FEM (×)")
cov=qu["A"]["cover"]; axq.text(0.03,0.03,f"covered {sum(cov)}/5 (A) · {sum(qu['B']['cover'])}/5 (B)",transform=axq.transAxes,fontsize=8.5,color=C_OK if sum(cov)>=4 else C_TR)
stamp(fig,"Study G · SYNTHETIC · unified modal statFEM · discrepancy spatially+frequency conditioned on observed residuals")
fig.savefig(os.path.join(FIG,"figG3_headline_holdout.png")); plt.close(fig)

# ---------------- figG4: QOI coverage, unified vs iid vs deterministic ----------------
fig,axs=plt.subplots(1,2,figsize=(11.5,4))
for ax,(key,tru,det,lab) in zip(axs,[("A",D["QA_true"],D["QA_det"],"QOI-A peak |H|"),
                                      ("B",D["QB_true"],D["QB_det"],"QOI-B band RMS")]):
    qU=H[f"qoi{key}_u"]; qI=H[f"qoi{key}_i"]
    for h in range(5):
        for off,arr,c in ((-0.18,qU,C_U),(0.18,qI,C_I)):
            loq,hq=np.percentile(arr[:,h],[2.5,97.5])
            ax.plot([h+off,h+off],[loq,hq],color=c,lw=4,alpha=0.75)
        ax.plot(h,tru[h],"_",color=C_T,ms=18,mew=2.2)
        ax.plot(h,det[h],"x",color=C_DET,ms=8)
    ax.set_yscale("log"); ax.set_xticks(range(5)); ax.set_xticklabels([f"n{n}" for n in hold],fontsize=8)
    ax.set_title(lab)
axs[0].set_ylabel("QOI value (log)")
axs[0].legend(handles=[plt.Line2D([0],[0],color=C_U,lw=4,label=f"unified ({qu['n_cover']}/10 cover)"),
                       plt.Line2D([0],[0],color=C_I,lw=4,label=f"iid ({qi['n_cover']}/10, R-hat {ri['max_rhat']:.1f})"),
                       plt.Line2D([0],[0],color=C_T,lw=2,label="truth"),
                       plt.Line2D([0],[0],color=C_DET,marker="x",lw=0,label="nominal FEM")],
              frameon=False,fontsize=8,loc="upper left")
stamp(fig,"Study G · SYNTHETIC · 95% intervals at the 5 never-measured points; iid labeled with its convergence status")
fig.savefig(os.path.join(FIG,"figG4_qoi_coverage.png")); plt.close(fig)

# ---------------- figG5: per-mode damping recovery ----------------
fig,ax=plt.subplots(figsize=(8.5,4.2))
zp=H["zeta_post"]*100; fp=H["f_post"]; NMg=zp.shape[1]
tz=D["truth_z"][:NMg]*100; tf=D["truth_f"][:NMg]
band=(tf>=10)&(tf<=60)
a0s=H["a0"]; a1s=H["a1"]
fgrid=np.linspace(10,60,80)
zr=np.array([(a0s[None,:]/(2*2*np.pi*fgrid[:,None]))+ (a1s[None,:]*2*np.pi*fgrid[:,None]/2)])[0]*100
lo_r,hi_r=np.percentile(zr,[2.5,97.5],1)
ax.fill_between(fgrid,lo_r,hi_r,color="#cccccc",alpha=0.5,label="Rayleigh-only capability (posterior a0,a1)")
ax.errorbar(fp[1][band],zp[1][band],yerr=[zp[1][band]-zp[0][band],zp[2][band]-zp[1][band]],
            fmt="o",ms=6,capsize=4,color=C_U,label="UMS-FEM ζ = proportional × global gz (95% CI)")
ax.plot(tf[band],tz[band],"_",color=C_T,ms=16,mew=2.2,label="truth ζ (NON-proportional, w/ patch dashpot)")
ax.set_xlabel("frequency [Hz]"); ax.set_ylabel("damping ratio ζ [%]")
ax.set_title("LIMITATION: production damping is proportional (global scale) — cannot match the truth's mode-to-mode spread")
ax.legend(frameon=False,fontsize=8)
stamp(fig,"Study G · SYNTHETIC · the per-mode latent damping was dropped (it was the convergence-ridge source, D23) → proportional damping is the honest tradeoff")
fig.savefig(os.path.join(FIG,"figG5_zeta_recovery.png")); plt.close(fig)

# ---------------- figG6: discrepancy diagnostics ----------------
fig,axs=plt.subplots(1,5,figsize=(13.5,3))
sg=H["s_g"]
panels=[("s_g0","group-1 stiffness s_g",sg[:,0]),("s_g3","group-4 stiffness s_g",sg[:,3]),
        ("sig_w","σ_w (rel. residual sd)",H["sig_w"]),("len_f","ℓ_f [Hz]",H["len_f"]),("len_z","ℓ_z [m]",H["len_z"])]
for ax,(k,lab,vals) in zip(axs,panels):
    ax.hist(vals,bins=36,color=C_U,alpha=0.85,density=True); ref=None
    if ref is not None:
        ax.axvline(ref,color=C_TR,lw=1.6,label=f"true {ref:.3g}"); ax.legend(frameon=False,fontsize=7)
    ax.set_xlabel(lab); ax.set_yticks([])
axs[0].set_ylabel("posterior")
fig.suptitle("Discrepancy/looseness hyperparameters — all inferred (red line = injected floor, for reference)",fontsize=10.5)
stamp(fig,"Study G · SYNTHETIC · τ/σ_w/ℓ have no injected 'truth' (model error is genuine structural mismatch); κ may sit above the floor (absorbs crossover error)")
fig.savefig(os.path.join(FIG,"figG6_hyper.png")); plt.close(fig)
print("Study G figures written")
