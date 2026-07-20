"""Study G GIFs: predictive bands evolving as data accrues (scan order) / band extends.
Each frame prints its own reduced-run R-hat (2-chain animation runs; headline = 4 chains).
Runs in .venv_fem_phase1. Outputs gif_scan_accretion.gif + gif_band_extension.gif"""
from __future__ import annotations
import glob, os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
FIG = os.path.join(ROOT, "figures"); OUTF = os.path.join(ROOT, "out", "frames2")
D = np.load(os.path.join(ROOT, "out", "ums_data.npz"), allow_pickle=True)
F_INF = D["F_INF"]; scan = list(D["scan"]); hold = list(D["hold_nodes"]); xy = D["xy"]
truth_show = np.abs(D["H_clean_inf"][:, scan.index(int(D["showcase"]))])
QA_true = D["QA_true"]
plt.rcParams.update({"font.size": 10.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 110, "figure.constrained_layout.use": True})
C_T="#222"; C_U="#1f77b4"; C_TR="#d62728"; C_H="#ff7f0e"

def render(frames, title, fname, band_mode=False):
    paths = []
    tmp = os.path.join(FIG, "_gtmp"); os.makedirs(tmp, exist_ok=True)
    ymin = truth_show.min()*0.2; ymax = truth_show.max()*8
    for k, fz in enumerate(frames):
        Z = np.load(os.path.join(OUTF, fz), allow_pickle=True)
        fig, (ax, axq) = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [2.1, 1]})
        ax.fill_between(F_INF, Z["lo"], Z["hi"], color=C_U, alpha=0.30, label="95% predictive")
        ax.plot(F_INF, Z["med"], color=C_U, lw=1.0)
        ax.plot(F_INF, truth_show, color=C_T, lw=1.1, label="clean truth (never measured)")
        if band_mode and float(Z["fmax"]) < F_INF[-1]:
            ax.axvspan(float(Z["fmax"]), F_INF[-1], color="#f3e2c8", alpha=0.55)
            ax.text(float(Z["fmax"])*1.03, ymax*0.25, "not yet excited", fontsize=8, color="#996")
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(ymin, ymax)
        ax.set_xlabel("frequency [Hz]"); ax.set_ylabel("|accelerance|")
        ax.set_title(title)
        ax.legend(frameon=False, fontsize=8, loc="lower right")
        cov = float(np.mean((truth_show >= Z["lo"]) & (truth_show <= Z["hi"])))
        ann = (f"points {int(Z['n_pts'])}/15 · band 10–{int(float(Z['fmax']))} Hz · "
               f"line coverage {cov*100:.0f}% · R-hat {float(Z['max_rhat']):.2f} (2-chain anim. run)")
        ax.text(0.02, 0.97, ann, transform=ax.transAxes, fontsize=8.5, va="top",
                bbox=dict(boxstyle="round", fc="white", ec="#ccc"))
        # scan mini-map
        axm = ax.inset_axes([0.035, 0.06, 0.26, 0.30]); axm.set_xticks([]); axm.set_yticks([])
        axm.scatter(xy[:, 0], xy[:, 1], s=7, color="#ddd")
        sub = list(Z["sub_nodes"])
        axm.scatter(xy[sub, 0], xy[sub, 1], s=14, color=C_U)
        axm.scatter(xy[hold, 0], xy[hold, 1], s=20, marker="s", fc="none", ec=C_H)
        axm.scatter(xy[[int(D["showcase"])], 0], xy[[int(D["showcase"])], 1], s=36, marker="s",
                    fc="none", ec=C_TR, lw=1.5)
        # QOI intervals panel
        qA = Z["qA"]                          # [3,5]
        for h in range(5):
            axq.plot([h, h], [qA[0, h], qA[2, h]], color=C_U, lw=4, alpha=0.75)
            axq.plot(h, qA[1, h], "o", ms=4, color=C_U)
            axq.plot(h, QA_true[h], "_", color=C_T, ms=16, mew=2.2)
        axq.set_yscale("log"); axq.set_xticks(range(5))
        axq.set_xticklabels([f"n{n}" for n in hold], fontsize=8)
        axq.set_ylim(QA_true.min()*0.1, QA_true.max()*12)
        axq.set_title("held-out QOI-A: 95% CI vs truth (—)")
        ncov = int(sum(qA[0, h] <= QA_true[h] <= qA[2, h] for h in range(5)))
        axq.text(0.03, 0.03, f"covered {ncov}/5", transform=axq.transAxes, fontsize=9,
                 color="#2a7d2a" if ncov >= 4 else C_TR)
        fig.text(0.01, 0.005, "Study G · SYNTHETIC · unified modal statFEM · reduced 2-chain frame runs "
                              "(headline gates use 4 chains)", fontsize=7.5, color="#777")
        p = os.path.join(tmp, f"f{k:02d}.png"); fig.savefig(p); plt.close(fig); paths.append(p)
    imgs = [Image.open(p) for p in paths]
    seq = imgs + [imgs[-1]] * 3 + imgs[::-1]
    seq[0].save(os.path.join(FIG, fname), save_all=True, append_images=seq[1:], duration=700, loop=0)
    for p in paths: os.remove(p)
    os.rmdir(tmp)
    print("wrote", fname, f"({len(frames)} frames)")

scanf = sorted(glob.glob(os.path.join(OUTF, "scan_*.npz")))
bandf = sorted(glob.glob(os.path.join(OUTF, "band_*.npz")))
if scanf:
    render([os.path.basename(p) for p in scanf],
           "Predictive band at a never-measured point as the LDV scan accrues points",
           "gif_scan_accretion.gif")
if bandf:
    render([os.path.basename(p) for p in bandf],
           "Predictive band as the excitation bandwidth is extended",
           "gif_band_extension.gif", band_mode=True)
print("gifs done")
