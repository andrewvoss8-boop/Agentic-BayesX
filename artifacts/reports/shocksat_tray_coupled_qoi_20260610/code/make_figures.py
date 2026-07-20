#!/usr/bin/env python3
"""Figures for the ShockSat x tray coupled-QOI packet (tufte-data-graphics
checklist applied; every DATA figure carries its run/dataset label and the
HYPOTHETICAL flag per the figure-provenance gate; the graphical model is a
pure schematic).

Reads only out/*.json + out/*.npz produced by run_qoi.py / identifiability.py
/ proxy_qoi.py -- no recomputation here.
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(WS, "out")
FIG = os.path.join(WS, "figures")
os.makedirs(FIG, exist_ok=True)

RUN = "run: shocksat_tray_coupled_qoi_20260610"
HYP = "HYPOTHETICAL methods demo - no tray was ever mounted; no hardware-validation claim"
G0 = 9.80665

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": "0.88", "grid.linewidth": 0.5,
    "legend.frameon": False, "figure.dpi": 150, "savefig.dpi": 150,
})
C = dict(unc="#b2453c", cpl="#2c5f8a", srs="#7a5195", miles="#c98a1e",
         ref="0.35", flag="#b2453c")


def stamp(fig, extra=""):
    fig.text(0.005, 0.005, f"{RUN}  |  {HYP}{extra}", fontsize=6.5,
             color=C["flag"], ha="left", va="bottom")


def jload(name):
    return json.load(open(os.path.join(OUT, name)))


# ------------------------------------------------------------- F1 schematic
def fig_graphical_model():
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    ax.axis("off")

    def box(x, y, w, h, text, fc="#eef2f6", ec="0.4", fs=8.5):
        ax.add_patch(plt.Rectangle((x, y), w, h, fc=fc, ec=ec, lw=0.8))
        ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=fs)

    # structure column
    box(0.04, 0.62, 0.24, 0.30, "ShockSat (primary)\nfree-free 74-mode ROM\n"
        "VALIDATED modal twin\n$Y_S(\\omega)$ at node P (6x6)")
    box(0.04, 0.40, 0.24, 0.14, "mount CBUSH (6-DOF)\n$k$ UNCERTAIN (joint)",
        fc="#fdeeee")
    box(0.04, 0.08, 0.24, 0.24, "tray (secondary)\nhexapod FEM (SI)\n"
        "single-point condensation\n$M_{chain}(\\omega)$ (6x6)")
    ax.annotate("", xy=(0.16, 0.40), xytext=(0.16, 0.32),
                arrowprops=dict(arrowstyle="-", lw=1.2))
    ax.annotate("", xy=(0.16, 0.62), xytext=(0.16, 0.54),
                arrowprops=dict(arrowstyle="-", lw=1.2))
    # uncertainty column
    box(0.36, 0.78, 0.27, 0.14, "$\\theta_S$ (9): NUTS POSTERIOR\n"
        "(predecessor, R-hat 1.022)", fc="#e8f0e8")
    box(0.36, 0.60, 0.27, 0.14, "$\\theta_T$ (5): PRIOR LogN(0, 0.25)\n"
        "(tray never tested)", fc="#fdf6e3")
    box(0.36, 0.42, 0.27, 0.14, "mount $k$ (6): PRIOR LogN(ln $k_{nom}$, 1.15)\n"
        "(UNIDENTIFIED joint - hypothesis)", fc="#fdeeee")
    box(0.36, 0.24, 0.27, 0.14, "input $a_{free}(t)$: 8 seeds\n"
        "flat 0.01 g$^2$/Hz, 20-250 Hz", fc="#eef2f6")
    # QOI column
    box(0.72, 0.55, 0.24, 0.30, "QOI: net CG interface load\n"
        "$F = (F_x, F_y, F_z)$ [N]\npeak $|F_d(t)|$ per axis\n"
        "(contract C1)", fc="#e8eaf2")
    box(0.72, 0.12, 0.24, 0.34,
        "methods:\nTIME-HISTORY (reference)\n  uncoupled / coupled (FBS)\n"
        "MODAL-SRS (SRSS+resid, Q sweep)\nPSD/MILES (3$\\sigma$ envelope)",
        fc="#f4f4f4", fs=8)
    for y0 in (0.85, 0.67, 0.49, 0.31):
        ax.annotate("", xy=(0.70, 0.66), xytext=(0.63, y0),
                    arrowprops=dict(arrowstyle="->", lw=0.8, color="0.45"))
    ax.annotate("", xy=(0.72, 0.30), xytext=(0.28, 0.45),
                arrowprops=dict(arrowstyle="->", lw=0.8, color="0.45"))
    ax.text(0.5, 0.97, "Forward propagation only - NO sampler run this task; "
            "no likelihood, no data on the coupled system (it is hypothetical)",
            ha="center", fontsize=8.5, color="0.25")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.text(0.005, 0.005, f"{RUN} | schematic (no data plotted)",
             fontsize=6.5, color="0.4")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_graphical_model.png"))
    plt.close(fig)


# ----------------------------------------------------------- F2 environment
def fig_input_env():
    z = np.load(os.path.join(OUT, "nominal_spectra.npz"))
    cache = np.load(os.path.join(OUT, "srs_cache.npz"))
    a = z["a0"]
    fs = 2048.0
    t = np.arange(len(a))/fs
    fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.2))
    ax = axs[0]
    ax.plot(t[:4096], a[:4096, 2]/G0, lw=0.4, color=C["cpl"])
    ax.set_xlabel("time [s]")
    ax.set_ylabel("base accel z [g]")
    ax.set_title("input record (seed 0, z, first 2 s of 20 s)")
    ax.text(0.02, 0.95, f"grms = {np.sqrt(np.mean(a[:,2]**2))/G0:.2f} g",
            transform=ax.transAxes, va="top", fontsize=8)
    ax = axs[1]
    f, Pxx = _welch(a[:, 2], fs)
    ax.loglog(f[1:], Pxx[1:]/G0**2, lw=0.7, color=C["cpl"],
              label="realized (Welch, 16 segs)")
    ax.loglog([20, 250], [0.01, 0.01], color=C["ref"], lw=1.5)
    ax.text(70, 0.0115, "spec 0.01 g$^2$/Hz", fontsize=8, color=C["ref"])
    ax.set_xlabel("frequency [Hz] (log)")
    ax.set_ylabel("PSD [g$^2$/Hz] (log)")
    ax.set_xlim(10, 500)
    ax.set_ylim(1e-4, 0.05)
    ax.set_title("acceleration PSD, one-sided")
    ax.legend(fontsize=7.5, loc="lower center")
    ax = axs[2]
    fn = cache["fn"]
    S = cache["S"]
    qg = list(cache["Q_grid"])
    for Q, col in zip((10, 25, 50), ("#9dbcd4", "#5b8cb8", C["cpl"])):
        qi = qg.index(Q)
        ax.loglog(fn, S[0, qi, :, 2]/G0, lw=0.9, color=col)
        ax.text(fn[-1]*1.05, S[0, qi, -1, 2]/G0, f"Q={Q}", fontsize=8,
                color=col, va="center")
    ax.set_xlabel("SDOF natural frequency [Hz] (log)")
    ax.set_ylabel("maximax abs-accel SRS [g] (log)")
    ax.set_title("SRS of the record (seed 0, z)")
    ax.set_xlim(10, 1300)
    for a_ in axs:
        a_.grid(True, which="both")
    stamp(fig, " | input is an INVENTED spec (D2), not a measured environment")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(FIG, "fig_input_env.png"))
    plt.close(fig)


def _welch(x, fs, nseg=16):
    N = len(x)//nseg
    win = np.hanning(N)
    U = np.sum(win**2)
    ps = []
    for i in range(nseg):
        seg = x[i*N:(i+1)*N]*win
        X = np.fft.rfft(seg)
        ps.append(2*np.abs(X)**2/(fs*U))
    return np.fft.rfftfreq(N, 1/fs), np.mean(ps, axis=0)


# ------------------------------------------------- F3 apparent masses (7004C)
def fig_apparent_mass():
    z = np.load(os.path.join(OUT, "nominal_spectra.npz"))
    f = z["freqs"]
    mn = jload("mount_node.json")
    cf = z["chain_f"]
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.4), sharey=True)
    notes = {
        "z": ("z: little ShockSat elastic z-participation at the plate "
              "center below 250 Hz ->\nthe source stays near its mass line "
              "(the Fig 9 notch cartoon needs z-active source modes)"),
        "x": ("x: lateral bending modes participate at P -> the source "
              "apparent mass\nNOTCHES at ShockSat resonances (Fig 9 source "
              "behavior)")}
    for ax, (d, axname) in zip(axs, [(2, "z"), (0, "x")]):
        Mch = z["Mch_diag"][:, d]
        Msrc = 1.0/np.maximum(z["Ys_diag"][:, d], 1e-12)
        ax.loglog(f, Mch, color=C["cpl"], lw=1.2)
        ax.loglog(f, Msrc, color=C["unc"], lw=1.2)
        ax.axhline(3.156, color=C["ref"], lw=0.7, ls=":")
        ax.axhline(57.96, color=C["ref"], lw=0.7, ls=":")
        ax.set_xlim(20, 250)
        ax.set_xlabel("frequency [Hz] (log)")
        ax.grid(True, which="both")
        ax.set_title(f"{axname} axis")
        ax.text(0.02, 0.02, notes[axname], transform=ax.transAxes,
                fontsize=7.2, color="0.35")
    ax = axs[0]
    ax.set_ylabel("apparent mass [kg] (log, linear scale - no dB)")
    ax.text(21, 4.0, "tray mass 3.16 kg", fontsize=7.5, color=C["ref"])
    ax.text(21, 47, "ShockSat mass 57.96 kg", fontsize=7.5, color=C["ref"])
    ipk = np.argmax(z["Mch_diag"][:, 2])
    ax.annotate("LOAD apparent mass |M$_{chain}$|\n(mount+tray): PEAKS at the "
                "chain\nfixed-base modes (7004C load curve)",
                xy=(f[ipk], z["Mch_diag"][ipk, 2]),
                xytext=(25, z["Mch_diag"][ipk, 2]*0.5), fontsize=8,
                color=C["cpl"],
                arrowprops=dict(arrowstyle="-", lw=0.6, color=C["cpl"]))
    ax.text(150, 110, "SOURCE |1/Y$_S$|\n(free-free ShockSat at P)",
            fontsize=8, color=C["unc"])
    fig.suptitle("7004C-style source vs load apparent mass at the mount node "
                 f"(gid {mn['node_gid']}); free-free source -> rigid mass "
                 "line at low f (contract C3 deviation from the grounded-"
                 "source Fig 9 cartoon)", fontsize=9)
    stamp(fig, " | data: out/nominal_spectra.npz (theta_S = posterior median)")
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    fig.savefig(os.path.join(FIG, "fig_apparent_mass.png"))
    plt.close(fig)


# ------------------------------------------------------- F4 force limiting
def fig_force_limiting():
    # SMOOTH transfer view: |F_z| per UNIT a_free,z (deterministic transfer
    # magnitudes |M_chain,zz| vs |T_cpl,zz|), NOT one seed's jagged spectrum
    # (that lives in fig_th_sample). Ratio = the 7004C force-limiting factor.
    z = np.load(os.path.join(OUT, "nominal_spectra.npz"))
    f = z["freqs"]
    A = np.load(os.path.join(OUT, "nominal_transfers.npz"))
    Tu = np.abs(A["T_unc_zz"])
    Tc = np.abs(A["T_cpl_zz"])
    cf = z["chain_f"]
    fig, axs = plt.subplots(2, 1, figsize=(7.8, 5.8), sharex=True,
                            gridspec_kw=dict(height_ratios=[2.2, 1]))
    ax = axs[0]
    ax.loglog(f, Tu, color=C["unc"], lw=1.1)
    ax.loglog(f, Tc, color=C["cpl"], lw=1.1)
    ipk = np.argmax(Tu)
    ax.annotate("UNCOUPLED (spec practice):\ntray driven by unmodified $a_{free}$",
                xy=(f[ipk], Tu[ipk]), xytext=(28, Tu[ipk]*0.8),
                color=C["unc"], fontsize=8.5,
                arrowprops=dict(arrowstyle="-", lw=0.6, color=C["unc"]))
    ax.annotate("COUPLED (LM-FBS):\nsource impedance feeds back",
                xy=(f[ipk], Tc[ipk]), xytext=(110, Tc[ipk]*0.12),
                color=C["cpl"], fontsize=8.5,
                arrowprops=dict(arrowstyle="-", lw=0.6, color=C["cpl"]))
    ax.axhline(3.156, color=C["ref"], lw=0.7, ls=":")
    ax.text(21, 3.4, "rigid limit m$_{tray}$ = 3.16 kg", fontsize=7.5,
            color=C["ref"])
    ax.set_ylabel("|F$_z$| per unit $a_{free,z}$ [N/(m/s$^2$)] = kg (log)")
    ax.set_title("force limiting: uncoupled vs coupled force transfer at the "
                 "interface (z, nominal parameters)")
    ax.grid(True, which="both")
    ax = axs[1]
    ratio = Tc/np.maximum(Tu, 1e-12)
    ax.loglog(f, ratio, color="0.3", lw=0.9)
    ax.axhline(1.0, color=C["ref"], lw=0.7, ls=":")
    imin = np.argmin(ratio)
    ax.plot(f[imin], ratio[imin], "v", color=C["cpl"], ms=5)
    ax.text(f[imin]*1.08, ratio[imin]*1.15,
            f"notch x{1/ratio[imin]:.1f} at {f[imin]:.0f} Hz\n"
            "(the 7004C over-test factor at the\nchain resonance)",
            fontsize=8, color=C["cpl"], va="bottom")
    for cfk in cf[cf < 250][:6]:
        ax.axvline(cfk, color="0.85", lw=0.5, ls="--")
    ax.set_xlabel("frequency [Hz] (log)")
    ax.set_ylabel("|T$_{cpl}$|/|T$_{unc}$| (log)")
    ax.set_xlim(20, 250)
    ax.grid(True, which="both")
    ax.text(0.99, 0.06, "dashed: chain fixed-base modes", transform=ax.transAxes,
            ha="right", fontsize=7.5, color="0.45")
    stamp(fig, " | data: out/nominal_transfers.npz (theta_S = posterior median)")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(FIG, "fig_force_limiting.png"))
    plt.close(fig)


# --------------------------------------------------- F5 method comparison
def fig_method_comparison():
    res = jload("qoi_results.json")
    rows = [("th_cpl", "TIME-HISTORY coupled (reference)", C["cpl"]),
            ("th_unc", "TIME-HISTORY uncoupled", C["unc"]),
            ("srs_Qinf", "modal-SRS (informed Q)", C["srs"]),
            ("srs_Q10", "modal-SRS Q=10", C["srs"]),
            ("srs_Q25", "modal-SRS Q=25", C["srs"]),
            ("srs_Q50", "modal-SRS Q=50", C["srs"]),
            ("miles_Qinf", "Miles 3$\\sigma$ (informed Q)", C["miles"]),
            ("miles_Q10", "Miles 3$\\sigma$ Q=10", C["miles"]),
            ("miles_Q25", "Miles 3$\\sigma$ Q=25", C["miles"]),
            ("miles_Q50", "Miles 3$\\sigma$ Q=50", C["miles"])]
    fig, axs = plt.subplots(1, 3, figsize=(11.5, 4.4), sharey=True)
    for d, (ax, axname) in enumerate(zip(axs, "xyz")):
        ref = res["joint_th_cpl"]["median"][d]
        for yi, (k, lab, col) in enumerate(rows):
            s = res[f"joint_{k}"]
            y = len(rows)-1-yi
            ax.plot([s["p2_5"][d], s["p97_5"][d]], [y, y], color=col, lw=1.0,
                    alpha=0.45, solid_capstyle="butt")
            ax.plot([s["p16"][d], s["p84"][d]], [y, y], color=col, lw=3.0,
                    solid_capstyle="butt")
            ax.plot(s["median"][d], y, "o", color=col, ms=4)
            r = s["median"][d]/ref
            ax.text(1.02, y, f"x{r:.2f}", transform=ax.get_yaxis_transform(),
                    fontsize=7.5, va="center", color=col)
        ax.axvline(ref, color=C["cpl"], lw=0.7, ls=":")
        ax.set_xscale("log")
        ax.set_xticks([100, 200, 400, 800, 1600])
        ax.set_xticklabels(["100", "200", "400", "800", "1600"])
        ax.xaxis.set_minor_locator(plt.NullLocator())
        ax.set_xlim(80, 2000)
        ax.set_title(f"peak |F$_{axname}$| [N]")
        ax.grid(True, axis="x", which="major")
        if d == 0:
            ax.set_yticks(range(len(rows)))
            ax.set_yticklabels([r[1] for r in reversed(rows)], fontsize=8)
    fig.text(0.5, 0.035, "x#.## at right of each bar = median ratio vs the "
             "coupled time-history reference (dotted line); SRS/Miles are "
             "inherently UNCOUPLED methods", ha="center", fontsize=8)
    fig.suptitle("method x coupling comparison under joint parameter uncertainty "
                 f"({res['meta']['n_joint']} draws x {res['meta']['seeds']} seeds; "
                 "thick bar 16-84 %, thin 2.5-97.5 %, dot median of seed-medians)",
                 fontsize=9.5)
    stamp(fig, " | data: out/qoi_results.json")
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    fig.savefig(os.path.join(FIG, "fig_method_comparison.png"))
    plt.close(fig)


# ------------------------------------------------ F6 mount sensitivity
def fig_mount_sensitivity():
    sw = jload("sweeps.json")["mount_multiplier"]
    vd = jload("variance_decomposition.json")
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.2))
    ax = axs[0]
    mult = np.array([s["mult"] for s in sw])
    f1 = np.array([s["chain_f"][0] for s in sw])
    lab_dy = {"x": 0.92, "y": 1.08, "z": 1.0}
    for d, axname, col in zip(range(3), "xyz", ("#9dbcd4", "#5b8cb8", C["cpl"])):
        y = np.array([s["th_cpl"][d] for s in sw])
        ax.loglog(mult*2e6, y, "o-", color=col, lw=1.0, ms=3)
        ax.text(mult[-1]*2e6*1.25, y[-1]*lab_dy[axname], f"F$_{axname}$",
                color=col, fontsize=8.5, va="center")
    valid = f1 <= 250.0
    if (~valid).any():
        x0 = mult[~valid][0]*2e6
        ax.axvspan(x0, mult[-1]*2e6*2, color="0.92", zorder=0)
        ax.text(x0*1.1, ax.get_ylim()[0]*1.3,
                "chain f1 > 250 Hz band edge:\nbounce no longer excited "
                "(+ ROM validity <280 Hz)", fontsize=7.5, color=C["flag"])
    ax.axvline(2e6, color=C["ref"], lw=0.7, ls=":")
    ax.text(2e6*1.1, ax.get_ylim()[1]*0.7, "nominal (INVENTED, A1)",
            fontsize=7.5, color=C["ref"], rotation=90, va="top")
    ax.set_xlabel("mount stiffness k$_t$ [N/m] (log; all 6 stiffnesses scaled together)")
    ax.set_ylabel("peak |F$_d$| coupled time-history [N] (log)")
    ax.set_title("QOI vs mount stiffness (deterministic sweep, seed-median)")
    ax.grid(True, which="both")
    ax = axs[1]
    groups = ["mount", "S", "T", "seed_aleatory"]
    labels = ["mount k (prior)", "$\\theta_S$ (posterior)", "$\\theta_T$ (prior)",
              "input seed (aleatory)"]
    cols = ["#b2453c", "#2c5f8a", "#c98a1e", "0.6"]
    width = 0.2
    xs = np.arange(3)
    for gi, (g, lab, col) in enumerate(zip(groups, labels, cols)):
        v = np.array(vd["groups"]["th_cpl"][g])
        ax.bar(xs+(gi-1.5)*width, v, width, color=col, label=lab)
        for x_, v_ in zip(xs, v):
            ax.text(x_+(gi-1.5)*width, v_+0.02, f"{v_:.2f}", ha="center",
                    fontsize=7, color=col)
    ax.set_xticks(xs)
    ax.set_xticklabels(["F$_x$", "F$_y$", "F$_z$"])
    ax.set_ylabel("variance fraction of joint QOI variance")
    ax.set_ylim(0, 1.32)
    ax.set_title("variance decomposition, coupled time-history peak\n"
                 "(OAT main effects; interactions ignored, need not sum to 1)")
    ax.legend(fontsize=8, loc="upper center", ncol=2)
    ax.grid(True, axis="y")
    stamp(fig, " | data: out/sweeps.json, out/variance_decomposition.json")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(os.path.join(FIG, "fig_mount_sensitivity.png"))
    plt.close(fig)


# ------------------------------------------------ F7 identifiability gate
def fig_identifiability():
    mi = jload("mount_identifiability.json")
    rows = [r for r in mi["coupled_mode_se"] if r["f_hz"] <= 160.0]
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.2))
    ax = axs[0]
    fhz = [r["f_hz"] for r in rows]
    xs = np.arange(len(rows))
    parts = [("mount_trans", "#b2453c", "mount translational"),
             ("mount_rot", "#e0907f", "mount rotational"),
             ("tray_sum", "#c98a1e", "tray groups"),
             ("shocksat_total", "#2c5f8a", "ShockSat groups")]
    bot = np.zeros(len(rows))
    for key, col, lab in parts:
        if key == "tray_sum":
            v = np.array([sum(r[f"tray_{g}"] for g in
                              ("tray_E", "strut_EA", "strut_EI",
                               "joint_axial", "joint_lateral"))
                          + r["tray_fixed_antispin"] for r in rows])
        else:
            v = np.array([r[key] for r in rows])
        ax.bar(xs, v, 0.75, bottom=bot, color=col, label=lab)
        bot += v
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{f_:.0f}" for f_ in fhz], fontsize=7, rotation=90)
    ax.set_xlabel("coupled mode frequency [Hz]")
    ax.set_ylabel("strain-energy fraction $f_{i,g}$")
    ax.set_ylim(0, 1.0)
    ax.set_title("where each coupled mode <= 160 Hz stores its strain energy\n"
                 "(Modal Identifiability Gate; closure = 1 per mode; modes "
                 "160-300 Hz are ~all-ShockSat)")
    ax.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.22),
              ncol=4)
    ax = axs[1]
    sens = mi["mount_sensitivity"]
    ax.semilogy([s["f_hz"] for s in sens],
                [max(s["dlnf_dlnk_mount"], 1e-5) for s in sens], "o",
                color="#b2453c", ms=4)
    ax.axhline(mi["verdict"]["sigma_f_floor"], color="0.3", lw=1.0, ls="--")
    ax.text(30, mi["verdict"]["sigma_f_floor"]*1.25,
            "predecessor $\\sigma_f$ = 4.6 % discrepancy floor\n"
            "(bare-ShockSat joints sat BELOW this -> unidentified)",
            fontsize=7.5, color="0.3")
    pk = mi["verdict"]
    ax.text(pk["peak_mode_hz"], pk["peak_dlnf_dlnk"]*1.3,
            f"peak {pk['peak_dlnf_dlnk']:.2f}", fontsize=8, color="#b2453c",
            ha="center")
    ax.set_xlabel("coupled mode frequency [Hz]")
    ax.set_ylabel("d ln f / d ln k$_{mount}$ = SE/2 (log)")
    ax.set_title("mount modal sensitivity vs the discrepancy floor:\n"
                 "mount WOULD be identifiable from a mounted-config modal test")
    ax.grid(True, which="both")
    stamp(fig, " | data: out/mount_identifiability.json (sensitivity statement, no sampler)")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(os.path.join(FIG, "fig_identifiability.png"))
    plt.close(fig)


# ------------------------------------------------ F8 response-limit proxy
def fig_proxy():
    px = jload("response_limit_proxy.json")
    tab = px["channels"]
    chs = sorted(set(t["channel"] for t in tab))
    fig, axs = plt.subplots(1, 3, figsize=(11.5, 4.4), sharey=True)
    for d, (ax, axname) in enumerate(zip(axs, "xyz")):
        rowsd = {t["channel"]: t for t in tab if t["force_axis"] == f"F{axname}"}
        ys = np.arange(len(chs))
        for yi, c in enumerate(chs):
            t = rowsd[c]
            best = c in [p["channel"] for p in px["picks"][f"F{axname}"]]
            col = "#b2453c" if best else "0.55"
            ax.plot([t["rho_bp_worst"], t["rho_bp_med"]], [yi, yi], color=col,
                    lw=2.0, solid_capstyle="butt")
            ax.plot(t["rho_bp_med"], yi, "o", color=col, ms=4)
            if best:
                ax.text(0.02, yi+0.25,
                        f"$\\alpha$={t['alpha_med_N_per_ms2']:.2f} N/(m/s$^2$) "
                        f"(cv {t['alpha_cv']:.2f})", fontsize=7, color=col)
        ax.axvline(1.0, color="0.8", lw=0.6)
        ax.set_xlim(0, 1.05)
        ax.set_title(f"proxy quality for F$_{axname}$")
        ax.set_xlabel("|corr(F$_d$, accel)| in 60-130 Hz band\n(dot median, "
                      "line to worst over 32 draws)")
        ax.grid(True, axis="x")
        if d == 0:
            ax.set_yticks(ys)
            ax.set_yticklabels(chs, fontsize=8)
    fig.suptitle("response-limit proxy (vision 2.2/D7): which accel tracks the "
                 f"net-CG force; ideal $\\alpha$ = m$_{{tray}}$ = "
                 f"{px['m_tray_kg']:.2f} kg; red = top-2 picks", fontsize=9.5)
    stamp(fig, " | data: out/response_limit_proxy.json")
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    fig.savefig(os.path.join(FIG, "fig_proxy.png"))
    plt.close(fig)


# ------------------------------------------------ F9 time-history sample
def fig_th_sample():
    z = np.load(os.path.join(OUT, "nominal_spectra.npz"))
    f = z["freqs"]
    N = 40960
    Fu = np.zeros((N//2+1, 3), complex)
    Fc = np.zeros((N//2+1, 3), complex)
    allf = np.fft.rfftfreq(N, 1/2048.0)
    bi = np.searchsorted(allf, f)
    Fu[bi] = z["F_unc"]
    Fc[bi] = z["F_cpl"]
    fu = np.fft.irfft(Fu[:, 2], n=N)
    fc = np.fft.irfft(Fc[:, 2], n=N)
    t = np.arange(N)/2048.0
    iu = np.argmax(np.abs(fu))
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.4))
    ax = axs[0]
    ax.plot(t, fu, lw=0.3, color=C["unc"], alpha=0.85)
    ax.plot(t, fc, lw=0.3, color=C["cpl"], alpha=0.85)
    ax.set_xlabel("time [s]")
    ax.set_ylabel("F$_z$(t) [N]")
    ax.set_title("interface force time history (z, seed 0, nominal)")
    ax.text(0.02, 0.97, f"uncoupled peak {np.max(np.abs(fu)):.0f} N",
            transform=ax.transAxes, color=C["unc"], fontsize=8.5, va="top")
    ax.text(0.02, 0.88, f"coupled peak {np.max(np.abs(fc)):.0f} N",
            transform=ax.transAxes, color=C["cpl"], fontsize=8.5, va="top")
    ax = axs[1]
    w = slice(max(iu-1024, 0), min(iu+1024, N))
    ax.plot(t[w], fu[w], lw=0.7, color=C["unc"])
    ax.plot(t[w], fc[w], lw=0.7, color=C["cpl"])
    ax.set_xlabel("time [s]")
    ax.set_title("1 s zoom at the uncoupled peak (residual view)")
    ax.grid(True)
    stamp(fig, " | data: out/nominal_spectra.npz")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(os.path.join(FIG, "fig_th_sample.png"))
    plt.close(fig)


# ------------------------------------------ F10 overnight VOI (D10)
def fig_voi():
    voi = jload("voi_results.json")
    conv = voi["convergence"]
    znp = np.load(os.path.join(OUT, f"nuts_mount_{voi['final_tag']}_samples.npz"))
    tm = znp["theta_m"]
    lock = jload("truth_lock.json")["payload"]
    fig, axs = plt.subplots(1, 3, figsize=(11.5, 4.3))

    # panel 1: mount multiplier prior vs posterior vs truth
    ax = axs[0]
    names = ["k_tx", "k_ty", "k_tz", "k_rx", "k_ry", "k_rz"]
    pr = [np.exp(-1.96*1.15), np.exp(1.96*1.15)]
    for j, nme in enumerate(names):
        y = len(names)-1-j
        ax.plot(pr, [y+0.18, y+0.18], color="0.8", lw=3, solid_capstyle="butt")
        lo, med, hi = np.percentile(tm[:, j], [2.5, 50, 97.5])
        ax.plot([lo, hi], [y, y], color=C["cpl"], lw=3, solid_capstyle="butt")
        ax.plot(med, y, "o", color=C["cpl"], ms=4)
        ax.plot(lock["mount_mult_true"][j], y, "x", color=C["unc"], ms=8,
                mew=2)
    ax.set_xscale("log")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(reversed(names))
    ax.set_xlabel("mount stiffness multiplier (log)")
    ax.set_title("mount: prior (gray) vs posterior (blue, 95 %)\nvs truth (x)"
                 " - diagonal-model EFFECTIVE values vs off-diagonal truth")
    ax.grid(True, axis="x", which="both")

    # panel 2: QOI before/after vs truth (coupled time-history)
    ax = axs[1]
    tab = voi["qoi_table"]["th_cpl"]
    for d, axname in enumerate("xyz"):
        y = 2-d
        b, a = tab["before"], tab["after"]
        ax.plot([b["p2_5"][d], b["p97_5"][d]], [y+0.15, y+0.15], color="0.65",
                lw=3, solid_capstyle="butt")
        ax.plot([a["p2_5"][d], a["p97_5"][d]], [y-0.15, y-0.15],
                color=C["cpl"], lw=3, solid_capstyle="butt")
        tq = voi["truth_qoi"]["th_cpl"][d]
        ax.plot(tq, y, "x", color=C["unc"], ms=9, mew=2)
        r = tab[f"axis_{axname}"]["width95_ratio_after_over_before"]
        ax.text(1.01, y, f"width x{r:.2f}", transform=ax.get_yaxis_transform(),
                fontsize=8, va="center", color=C["cpl"])
    ax.set_yticks([2, 1, 0])
    ax.set_yticklabels(["F$_x$", "F$_y$", "F$_z$"])
    ax.set_xscale("log")
    ax.set_xlabel("peak coupled interface force [N] (log)")
    ax.set_title("QOI 95 % bands: BEFORE survey (gray, prior mount)\n"
                 "vs AFTER (blue, posterior mount); truth (x)")
    ax.grid(True, axis="x", which="both")

    # panel 3: force-limiting factor before/after vs truth
    ax = axs[2]
    flb = voi["force_limiting_factor"]["before"]
    fla = voi["force_limiting_factor"]["after"]
    flt = voi["force_limiting_factor"]["truth"]
    for d, axname in enumerate("xyz"):
        y = 2-d
        ax.plot([flb["p2_5"][d], flb["p97_5"][d]], [y+0.15, y+0.15],
                color="0.65", lw=3, solid_capstyle="butt")
        ax.plot([fla["p2_5"][d], fla["p97_5"][d]], [y-0.15, y-0.15],
                color=C["cpl"], lw=3, solid_capstyle="butt")
        ax.plot(flt[d], y, "x", color=C["unc"], ms=9, mew=2)
    ax.set_yticks([2, 1, 0])
    ax.set_yticklabels(["F$_x$", "F$_y$", "F$_z$"])
    ax.axvline(1.0, color="0.85", lw=0.7)
    ax.set_xlabel("force-limiting factor peak$_{unc}$/peak$_{cpl}$")
    ax.set_title("7004C over-test factor:\nbefore (gray) vs after (blue), "
                 "truth (x)")
    ax.grid(True, axis="x")

    if conv["gate_pass"]:
        cv = (f"NUTS gate PASSED: worst R-hat {conv['worst_rhat']:.3f}, "
              f"min ESS {conv['min_ess']:.0f}, div {conv['divergences']}")
        ccol = "0.35"
    else:
        cv = (f"NOT CONVERGED (multimodal): worst R-hat "
              f"{conv['worst_rhat']:.2f}, min ESS {conv['min_ess']:.0f} - "
              "intervals NOT trustworthy")
        ccol = C["flag"]
    fig.suptitle("one SYNTHETIC mounted-config survey (27 modes)  |  " + cv,
                 fontsize=9, color=ccol)
    stamp(fig, " | SYNTHETIC truth (truth_lock.json) | data: out/voi_results.json")
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    fig.savefig(os.path.join(FIG, "fig_voi.png"))
    plt.close(fig)


if __name__ == "__main__":
    fig_graphical_model()
    fig_input_env()
    fig_apparent_mass()
    fig_force_limiting()
    fig_method_comparison()
    fig_mount_sensitivity()
    fig_identifiability()
    fig_proxy()
    fig_th_sample()
    if os.path.exists(os.path.join(OUT, "voi_results.json")):
        fig_voi()
        print("incl. overnight fig_voi")
    print("figures written to", FIG)
