#!/usr/bin/env python3
"""Supplementary animated GIFs for the program deck (D13). NOT embedded in the
pptx (per Andrew); for the talk / Substack / hover.

G1 force_limiting_sweep.gif : uncoupled vs coupled force transfer |T_zz| as the
   mount stiffness sweeps the prior decades -> the 7004C notch appears/moves.
G2 mode_walk_qoi.gif         : chain fixed-base modes walking through the input
   band + the (non-monotonic) peak-Fz QOI, vs mount stiffness (from sweeps.json).
G3 multimodality.gif         : the overnight NUTS chains AGREE in data space
   (predicted frequencies) while SCATTERING in parameter space = the honest
   under-identification negative.

tufte discipline: log axes, direct labels, run/HYPOTHETICAL stamp, minimal ink.
Frames rendered to PNG via the Agg canvas, assembled with PIL (no ffmpeg).
"""
import io
import json
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(WS, "out")
GIF = os.path.join(WS, "slides", "gifs")
os.makedirs(GIF, exist_ok=True)
sys.path.insert(0, HERE)
import models  # noqa: E402
import methods  # noqa: E402
import run_qoi  # noqa: E402

plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 110})
C = dict(unc="#b2453c", cpl="#2c5f8a", ref="0.4", flag="#b2453c")
RUN = "shocksat_tray_coupled_qoi_20260610  |  HYPOTHETICAL methods demo"


def frame(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def save_gif(frames, name, ms=420, pingpong=True):
    seq = frames + frames[-2:0:-1] if pingpong else frames
    w = min(f.width for f in seq)
    h = min(f.height for f in seq)
    seq = [f.resize((w, h)) for f in seq]
    seq[0].save(os.path.join(GIF, name), save_all=True, append_images=seq[1:],
                duration=ms, loop=0, optimize=True)
    print("wrote", name, f"({len(seq)} frames {w}x{h})")


# --------------------------------------------------------------- G1
def gif_force_limiting():
    tray = models.build_tray_chain()
    shk = models.ShockSatInterface()
    thetaS, _ = run_qoi.load_posterior()
    th_med = np.median(thetaS, axis=0)
    env = methods.synth_input(0)
    bidx = run_qoi.band_idx(env)
    fb = env["freqs"][bidx]
    mults = np.logspace(np.log10(0.05), np.log10(50), 16)
    knom = {p: models.MOUNT_NOMINAL[p] for p in models.MOUNT_PARAMS}
    # precompute global y-limits
    allT = []
    cache = []
    for m in mults:
        km = {p: knom[p]*m for p in knom}
        chain = models.chain_modal(tray, kmount=km)
        Mch = models.apparent_mass(chain, fb)
        Ys = shk.accelerance(fb, th_med)
        Tc = np.linalg.solve(np.eye(6)[None] + Mch @ Ys, Mch)
        Tu = np.abs(Mch[:, 2, 2])
        Tcz = np.abs(Tc[:, 2, 2])
        cache.append((Tu, Tcz, chain["f"][chain["f"] < 250][:6]))
        allT += [Tu.max(), Tcz.max()]
    ymax = max(allT)*1.6
    frames = []
    for m, (Tu, Tcz, cf) in zip(mults, cache):
        fig, (ax, ax2) = plt.subplots(2, 1, figsize=(7.4, 5.4), sharex=True,
                                      gridspec_kw=dict(height_ratios=[2.3, 1]))
        ax.loglog(fb, Tu, color=C["unc"], lw=1.6)
        ax.loglog(fb, Tcz, color=C["cpl"], lw=1.6)
        ax.axhline(3.156, color=C["ref"], lw=0.7, ls=":")
        ax.text(21, 3.4, "rigid limit 3.16 kg", fontsize=9, color=C["ref"])
        ax.text(0.97, 0.93, "UNCOUPLED (spec)", color=C["unc"], fontsize=11,
                ha="right", transform=ax.transAxes)
        ax.text(0.97, 0.84, "COUPLED (force-limited)", color=C["cpl"],
                fontsize=11, ha="right", transform=ax.transAxes)
        ax.set_ylim(0.5, ymax)
        ax.set_ylabel("|F$_z$| per unit input  [kg]")
        ax.set_title(f"Force limiting (NASA-HDBK-7004C):  mount k = "
                     f"{2e6*m:.2e} N/m   (×{m:.2f} nominal)", fontsize=11.5)
        ratio = Tcz/np.maximum(Tu, 1e-9)
        ax2.semilogx(fb, ratio, color="0.3", lw=1.3)
        ax2.axhline(1.0, color=C["ref"], lw=0.7, ls=":")
        imin = int(np.argmin(ratio))
        ax2.plot(fb[imin], ratio[imin], "v", color=C["cpl"], ms=8)
        ax2.text(fb[imin]*1.06, max(ratio[imin], 0.05),
                 f"over-test ×{1/ratio[imin]:.1f}", color=C["cpl"], fontsize=10)
        for c_ in cf:
            ax2.axvline(c_, color="0.85", lw=0.5, ls="--")
        ax2.set_ylim(0.05, 1.6)
        ax2.set_yscale("log")
        ax2.set_xlim(20, 250)
        ax2.set_ylabel("coupled / uncoupled")
        ax2.set_xlabel("frequency [Hz]")
        fig.text(0.005, 0.005, RUN, fontsize=7, color=C["flag"])
        fig.tight_layout(rect=(0, 0.02, 1, 1))
        frames.append(frame(fig))
    save_gif(frames, "force_limiting_sweep.gif", ms=480)


# --------------------------------------------------------------- G2
def gif_mode_walk():
    sw = json.load(open(os.path.join(OUT, "sweeps.json")))["mount_multiplier"]
    qz = [s["th_cpl"][2] for s in sw]
    qzmax = max(qz)*1.15
    frames = []
    for s in sw:
        fig, (ax, axb) = plt.subplots(1, 2, figsize=(8.6, 4.0),
                                      gridspec_kw=dict(width_ratios=[2.4, 1]))
        ax.axvspan(20, 250, color="#eef3f7", zorder=0)
        ax.text(135, 0.9, "input band 20-250 Hz", ha="center", fontsize=9,
                color="0.45")
        for f_ in s["chain_f"][:6]:
            ax.axvline(f_, color=C["cpl"], lw=2.0, ymax=0.8)
        ax.set_xscale("log")
        ax.set_xlim(10, 600)
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        ax.set_xlabel("frequency [Hz]")
        ax.set_title(f"Chain modes vs mount k = {s['k_tz']:.1e} N/m  "
                     f"(×{s['mult']:.2f})", fontsize=11.5)
        f1 = s["chain_f"][0]
        ax.annotate(f"1st mode {f1:.0f} Hz", xy=(f1, 0.8), xytext=(f1, 0.92),
                    ha="center", fontsize=9.5, color=C["cpl"],
                    arrowprops=dict(arrowstyle="->", color=C["cpl"], lw=0.8))
        axb.bar([0], [s["th_cpl"][2]], color=C["unc"], width=0.6)
        axb.set_ylim(0, qzmax)
        axb.set_xlim(-0.6, 0.6)
        axb.set_xticks([])
        axb.set_title("peak |F$_z$| [N]", fontsize=10.5)
        axb.text(0, s["th_cpl"][2]+qzmax*0.02, f"{s['th_cpl'][2]:.0f}",
                 ha="center", fontsize=11, color=C["unc"])
        fig.text(0.005, 0.005, RUN + "  |  data: out/sweeps.json", fontsize=7,
                 color=C["flag"])
        fig.tight_layout(rect=(0, 0.03, 1, 1))
        frames.append(frame(fig))
    save_gif(frames, "mode_walk_qoi.gif", ms=520)


# --------------------------------------------------------------- G3
def _coupled_freq_fn():
    """Self-contained predicted-frequency function for the survey (no import
    side effects): replicates the reduced forward at the pairing anchor."""
    rom = np.load(os.path.join(OUT, "coupled_rom.npz"))
    pr = json.load(open(os.path.join(OUT, "pairing_coupled.json")))
    calib = [p for p in pr["pairs"] if p["calib_ok"]]
    m_idx = np.array([p["anchor_mode"] for p in calib])
    f_data = np.array([p["f_data"] for p in calib])
    Bf, Bm, Bt = rom["B_fix"], rom["B_mount"], rom["B_tray"]
    Qa = rom[f"anchorQ_x{pr['anchor_mult']}"]

    def freqs(theta_m, theta_T):
        K = (Bf + np.einsum("j,jab->ab", theta_m, Bm)
             + np.einsum("g,gab->ab", theta_T, Bt))
        lam, Q = np.linalg.eigh(K)
        f = np.sqrt(np.clip(lam, 1e-12, None))/(2*np.pi)
        k = np.argmax(np.abs(Qa.T @ Q)[m_idx, :], axis=1)
        return f[k]
    return freqs, f_data


def gif_multimodality():
    z = np.load(os.path.join(OUT, "nuts_mount_base_samples.npz"))
    cv = json.load(open(os.path.join(OUT, "convergence_mount_base.json")))
    nd, nc = cv["settings"]["ndraw"], cv["settings"]["chains"]
    tm = z["theta_m"].reshape(nc, nd, 6)
    tt = z["theta_T"].reshape(nc, nd, 5)
    freqs_fn, fdat = _coupled_freq_fn()
    step = 50
    idxs = list(range(step, nd+1, step))
    cols = ["#b2453c", "#2c5f8a", "#c98a1e", "#3a7d44"]
    frames = []
    for ndraw in idxs:
        fig, (axp, axd) = plt.subplots(1, 2, figsize=(9.2, 4.1))
        for c in range(nc):
            med = np.median(tm[c, :ndraw], axis=0)
            axp.plot(range(6), med, "o-", color=cols[c], lw=1.3, ms=5,
                     label=f"chain {c}")
            fp = freqs_fn(med, np.median(tt[c, :ndraw], axis=0))
            axd.plot(fdat, fp, "o", color=cols[c], ms=4, alpha=0.7)
        axp.set_xticks(range(6))
        axp.set_xticklabels(["k_tx", "k_ty", "k_tz", "k_rx", "k_ry", "k_rz"],
                            fontsize=8, rotation=30)
        axp.set_yscale("log")
        axp.set_ylim(0.05, 12)
        axp.set_ylabel("mount stiffness multiplier")
        axp.set_title("PARAMETER space: chains disagree", fontsize=11)
        axp.legend(fontsize=8, ncol=2)
        lim = [fdat.min()*0.9, fdat.max()*1.1]
        axd.plot(lim, lim, color="0.6", lw=0.8, ls="--")
        axd.set_xlim(lim)
        axd.set_ylim(lim)
        axd.set_xlabel("measured survey freq [Hz]")
        axd.set_ylabel("predicted freq [Hz]")
        axd.set_title("DATA space: chains agree", fontsize=11)
        fig.suptitle(f"Honest negative: under-identified mount (after "
                     f"{ndraw} draws)  |  R-hat {cv['worst_rhat']:.1f}, "
                     "NOT converged", fontsize=11, color=C["flag"])
        fig.text(0.005, 0.005, RUN + "  |  SYNTHETIC survey | out/nuts_mount_"
                 "base_samples.npz", fontsize=7, color=C["flag"])
        fig.tight_layout(rect=(0, 0.03, 1, 0.94))
        frames.append(frame(fig))
    save_gif(frames, "multimodality.gif", ms=360, pingpong=False)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "g1"):
        gif_force_limiting()
    if which in ("all", "g2"):
        gif_mode_walk()
    if which in ("all", "g3"):
        gif_multimodality()
    print("gifs done")
