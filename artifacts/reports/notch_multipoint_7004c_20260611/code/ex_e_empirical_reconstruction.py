"""
EX-E: Is there an empirical path to (response/force)-limited vibration WITHOUT a
coupled forced FEM — using interface measurements at one foot / a few feet / a
point 1-3 foot-spacings away?

Idea (7004C impedance method, Eq 3/4): the coupled interface response is
  a_coupled = (Ms + Ml)^-1 Ms A_free  ;  F = Ml a_coupled
where Ms (source apparent mass), Ml (load apparent mass), A_free (source free
acceleration) are all MEASURABLE at the interface WITHOUT solving the coupled
system. So a measurement can replace the coupled FEM — IF you can measure enough
of the (matrix) interface quantities. This script quantifies the error of sparse
measurement against the full coupled solve (ground truth), across regimes.

Reconstructions (Q11):
  FULL   4x4 vertical matrix         -> exact-coupling verification
  SCALAR single-point condensation   -> 7004C idealization: net/bounce only, moment=0
  RIGID3 z/thx/thy projection (>=3 ft)-> bounce+rocking, misses warping
  DIAG   feet treated independent     -> decoupled-foot approximation
Part 2: remote-point response proxy (transmissibility, boundary dependence).

No coupled FEM is used in any reconstruction; the coupled solve is TRUTH only.
No sampler (D1).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import (M_PAY, AX, AY, KZ_FOOT, ETA, box_inertia, plate_modal_system,
                    phi_matrix, foot_points, coupled_plate_payload_frf,
                    bare_plate_field, payload_vertical_3dof, FEET_CENTROID,
                    LX, LY, TPL, FIG, RES, save_json, stamp)
from ex_c_notch_distance import fixed_base_payload_modes

SCRIPT = "ex_e_empirical_reconstruction.py"
FOOT_SPACING = np.hypot(2 * AX, 2 * AY) / np.sqrt(2)   # ~0.16 m representative


def load_apparent_mass(freqs, ex=0.0, kz=KZ_FOOT, eta=ETA):
    """4x4 LOAD apparent mass at the foot vertical DOFs (Q10). No plate involved."""
    Mp, Lp = payload_vertical_3dof(ex=ex)
    kc = kz * (1 + 1j * eta)
    Kpp = kc * (Lp.T @ Lp)
    out = np.zeros((len(freqs), 4, 4), dtype=complex)
    for i, fh in enumerate(freqs):
        w = 2 * np.pi * fh
        G = np.linalg.inv(-w**2 * Mp + Kpp)
        out[i] = -(kc * np.eye(4) - kc**2 * (Lp @ G @ Lp.T)) / w**2
    return out, Lp


def source_apparent_mass(freqs, sysd, zeta_pl=0.02):
    """4x4 SOURCE apparent mass at the feet (Q10). No payload involved."""
    wn, mgen = sysd["wn"], sysd["mgen"]
    Phi_f = phi_matrix(sysd, foot_points())            # 4 x nm
    out = np.zeros((len(freqs), 4, 4), dtype=complex)
    for i, fh in enumerate(freqs):
        w = 2 * np.pi * fh
        Dm = mgen * (wn**2 - w**2 + 2j * zeta_pl * wn * w)
        Hacc = -w**2 * (Phi_f / Dm) @ Phi_f.T          # accel/force receptance 4x4
        out[i] = np.linalg.inv(Hacc)
    return out


def rigid_basis():
    """4x3 rigid-interface basis B: columns [z, thx(y-arm), thy(-x-arm)]."""
    fp = np.array(foot_points()) - np.array(FEET_CENTROID)
    B = np.column_stack([np.ones(4), fp[:, 1], -fp[:, 0]])
    return B


def reconstruct(Ms, Ml, A_free):
    """Return dict of per-method reconstructions for one frequency."""
    o = np.ones(4)
    B = rigid_basis()
    xf = -B[:, 2]                                       # foot x-arm
    out = {}
    # FULL (exact coupling)
    a_full = np.linalg.solve(Ms + Ml, Ms @ A_free)
    F_full = Ml @ a_full
    out["full"] = dict(a=a_full, F=F_full,
                       net=F_full.sum(), My=-(F_full * xf).sum(),
                       foot_worst=np.max(np.abs(F_full)))
    # SCALAR single-point condensation
    Ms_s, Ml_s = o @ Ms @ o, o @ Ml @ o
    A_s = (o @ A_free) / 4.0
    a_s = Ms_s / (Ms_s + Ml_s) * A_s
    net_s = Ms_s * Ml_s / (Ms_s + Ml_s) * A_s
    out["scalar"] = dict(a=a_s * o, F=(net_s / 4.0) * o,
                         net=net_s, My=0.0 + 0j, foot_worst=abs(net_s) / 4.0)
    # RIGID3 projection
    Bp = np.linalg.pinv(B)
    Ms3, Ml3, A3 = B.T @ Ms @ B, B.T @ Ml @ B, Bp @ A_free
    q3 = np.linalg.solve(Ms3 + Ml3, Ms3 @ A3)
    gen = Ml3 @ q3                                      # [Fz, Mx, My] generalized force
    F_feet3 = B @ np.linalg.solve(B.T @ B, gen)        # min-norm per-foot
    out["rigid3"] = dict(a=B @ q3, F=F_feet3,
                         net=gen[0], My=gen[2],
                         foot_worst=np.max(np.abs(F_feet3)))
    # DIAG feet independent
    a_d = (np.diag(Ms) / (np.diag(Ms) + np.diag(Ml))) * A_free
    F_d = np.diag(Ml) * a_d
    out["diag"] = dict(a=a_d, F=F_d, net=F_d.sum(), My=-(F_d * xf).sum(),
                       foot_worst=np.max(np.abs(F_d)))
    return out


def run_regime(kz_mult, zeta_pl, t=TPL, label=""):
    kz = KZ_FOOT * kz_mult
    sysd = plate_modal_system(1250.0, t=t)
    f0 = fixed_base_payload_modes(kz)
    modes = sorted(v for v in f0.values() if v < 480)
    base = np.geomspace(20, 500, 1100)
    refine = np.concatenate([np.linspace(v * 0.7, min(v * 1.3, 500), 600) for v in modes])
    freqs = np.unique(np.concatenate([base, refine]))

    Ms = source_apparent_mass(freqs, sysd, zeta_pl)
    Ml, Lp = load_apparent_mass(freqs, ex=0.0, kz=kz)
    A_free = bare_plate_field(freqs, sysd, foot_points(), zeta_pl=zeta_pl)   # nf x 4

    # truth from the coupled solve
    cp = coupled_plate_payload_frf(freqs, sysd, ex=0.0, kz=kz, zeta_pl=zeta_pl)
    w2 = (2 * np.pi * freqs) ** 2
    a_true = -(w2[:, None]) * cp["wfeet"]
    F_true = cp["Ffoot"]
    xf = -rigid_basis()[:, 2]
    net_true = F_true.sum(axis=1)
    My_true = -(F_true * xf).sum(axis=1)
    foot_true = np.max(np.abs(F_true), axis=1)

    methods = ["full", "scalar", "rigid3", "diag"]
    chans = {m: dict(net=[], My=[], foot=[], a=[]) for m in methods}
    for i in range(len(freqs)):
        rec = reconstruct(Ms[i], Ml[i], A_free[i])
        for m in methods:
            chans[m]["net"].append(rec[m]["net"])
            chans[m]["My"].append(rec[m]["My"])
            chans[m]["foot"].append(rec[m]["foot_worst"])
    for m in methods:
        for k in ("net", "My", "foot"):
            chans[m][k] = np.array(chans[m][k])

    # verification: FULL reconstruction == coupled truth
    full_err = max(
        np.max(np.abs(chans["full"]["net"] - net_true) / np.abs(net_true)),
        np.max(np.abs(chans["full"]["My"] - My_true) / np.maximum(np.abs(My_true), 1e-12)),
        np.max(np.abs(chans["full"]["foot"] - foot_true) / foot_true))

    # band-peak relative errors per method per channel at each payload mode
    def bandpeak(arr, fc, half=0.10):
        sel = (freqs >= fc * (1 - half)) & (freqs <= fc * (1 + half))
        return arr[sel]

    truth = dict(net=net_true, My=My_true, foot=foot_true)
    mode_err = {}
    mode_names = {modes[0]: "rock(lower)", modes[1]: "rock(upper)",
                  modes[2]: "bounce"} if len(modes) >= 3 else {}
    for fc in modes:
        row = {}
        for m in methods:
            row[m] = {}
            for ch in ("net", "My", "foot"):
                tt = bandpeak(np.abs(truth[ch]), fc)
                rr = bandpeak(np.abs(chans[m][ch]), fc)
                tpk = tt.max()
                rpk = rr[np.argmax(tt)] if tpk > 0 else 0.0
                row[m][ch] = dict(truth_peak=float(tpk), recon_at_peak=float(rpk),
                                  rel_err=float(abs(rpk - tpk) / tpk) if tpk > 0 else 0.0)
        mode_err[f"{mode_names.get(fc, 'mode')}_{fc:.0f}Hz"] = row

    return dict(label=label, kz_mult=kz_mult, zeta_pl=zeta_pl, t=t,
                freqs=freqs, modes=modes, full_recon_max_err=float(full_err),
                truth=dict(net=net_true, My=My_true, foot=foot_true),
                chans=chans, mode_err=mode_err)


def remote_proxy(kz_mult=1.0, zeta_pl=0.02, t=TPL):
    """Part 2: a remote control accelerometer as an interface proxy via
    transmissibility T = a_remote / a_meanfeet.

    Two distinct error sources, separated honestly:
      (a) IN-CONFIG, LINEAR: T calibrated in a low-level run of the SAME config
          is IDENTICAL at high level (linear system) -> response limiting is
          EXACT regardless of distance. (Stated; trivially true here.)
      (b) CONFIG MISMATCH: T calibrated WITHOUT the payload (bare plate, e.g.
          pre-integration) vs needed WITH it (coupled). This is the real risk.
    We report (b), split into the coupled-resonance bands (where you notch) vs
    off-resonance, and vs distance. Remote points are offset off the symmetry
    centerline to avoid nodal-line division artifacts; frequencies where the
    bare interface response is near a node are masked."""
    kz = KZ_FOOT * kz_mult
    sysd = plate_modal_system(1250.0, t=t)
    freqs = np.geomspace(40, 300, 1600)
    cx, cy = FEET_CENTROID
    dists = [1, 2, 3]
    pts = [(cx - d * FOOT_SPACING, cy + 0.05) for d in dists]   # off centerline
    fp = foot_points()
    aB = bare_plate_field(freqs, sysd, fp, zeta_pl=zeta_pl)
    cp = coupled_plate_payload_frf(freqs, sysd, ex=0.0, kz=kz, zeta_pl=zeta_pl)
    w2 = (2 * np.pi * freqs) ** 2
    aC_feet = -(w2[:, None]) * cp["wfeet"]
    aB_feet_mean, aC_feet_mean = aB.mean(axis=1), aC_feet.mean(axis=1)
    aB_r = bare_plate_field(freqs, sysd, pts, zeta_pl=zeta_pl)
    Phi_p = phi_matrix(sysd, pts)
    aC_r = -(w2[:, None]) * (cp["qm"] @ Phi_p.T)
    # coupled-resonance bands (payload absorber freqs)
    f0 = fixed_base_payload_modes(kz)
    res_bands = np.zeros(len(freqs), bool)
    for v in f0.values():
        res_bands |= (freqs > v * 0.9) & (freqs < v * 1.1)
    out = dict(freqs=freqs, dists=dists, foot_spacing=float(FOOT_SPACING),
               res_bands=res_bands, curves=[])
    for j, d in enumerate(dists):
        T_bare = aB_r[:, j] / aB_feet_mean
        T_coup = aC_r[:, j] / aC_feet_mean
        # mask near-nodal remote response (ill-defined T)
        good = np.abs(aC_r[:, j]) > 0.05 * np.median(np.abs(aC_r[:, j]))
        err = np.abs(T_coup - T_bare) / np.abs(T_coup)
        on = good & res_bands
        off = good & ~res_bands
        out["curves"].append(dict(
            dist_spacings=d, T_bare=T_bare, T_coup=T_coup, proxy_err=err, good=good,
            err_off_resonance_med=float(np.median(err[off])) if off.any() else None,
            err_on_resonance_med=float(np.median(err[on])) if on.any() else None))
    return out


def main():
    regimes = [("soft_Q25", 1.0, 0.02), ("stiff_Q25", 9.0, 0.02),
               ("soft_Q6", 1.0, 0.08), ("stiff_Q6", 9.0, 0.08)]
    runs = {lab: run_regime(kz, z, label=lab) for lab, kz, z in regimes}
    rp = remote_proxy()

    for lab, r in runs.items():
        print(f"{lab:10s} full-recon err {r['full_recon_max_err']:.2e} | modes "
              f"{[f'{m:.0f}' for m in r['modes']]}")
        for mk, row in r["mode_err"].items():
            print(f"   {mk:18s} "
                  + " ".join(f"{m}:net{row[m]['net']['rel_err']*100:4.0f}% "
                             f"My{row[m]['My']['rel_err']*100:4.0f}% "
                             f"foot{row[m]['foot']['rel_err']*100:4.0f}%"
                             for m in ("scalar", "rigid3", "diag")))

    # ---- results json (strip arrays) ----
    res = dict(regimes={}, remote_proxy={}, foot_spacing_m=float(FOOT_SPACING))
    for lab, r in runs.items():
        res["regimes"][lab] = dict(
            kz_mult=r["kz_mult"], zeta_pl=r["zeta_pl"],
            full_recon_max_err=r["full_recon_max_err"],
            modes_hz=[float(m) for m in r["modes"]], mode_err=r["mode_err"])
    for j, c in enumerate(rp["curves"]):
        res["remote_proxy"][f"{c['dist_spacings']}_spacings"] = dict(
            dist_m=float(c["dist_spacings"] * rp["foot_spacing"]),
            err_off_resonance_med=c["err_off_resonance_med"],
            err_on_resonance_med=c["err_on_resonance_med"])
    res["remote_proxy"]["in_config_linear_note"] = (
        "T calibrated in the SAME config at low level is identical at high level "
        "for a linear system -> response limiting EXACT regardless of distance; "
        "the errors above are CONFIG-MISMATCH (bare-plate calibration) only.")
    save_json(os.path.join(RES, "ex_e_results.json"), res)

    # ================= figures =================
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False})
    cols = dict(full="0.1", scalar="#c0392b", rigid3="#27ae60", diag="#8e44ad")
    lbls = dict(full="full 4×4 (exact)", scalar="scalar single-point (7004C)",
                rigid3="rigid-3 (≥3 feet)", diag="diagonal (feet independent)")

    # fig_e1: reconstruction of net F, My, worst-foot vs freq (soft_Q25)
    r = runs["soft_Q25"]
    fq = r["freqs"]
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.4))
    for ax, ch, ttl, unit in [
            (axes[0], "net", "net vertical force ΣFz", "N"),
            (axes[1], "My", "interface moment My", "N·m"),
            (axes[2], "foot", "worst per-foot force", "N")]:
        ax.loglog(fq, np.abs(r["truth"][ch]), color="0.6", lw=3.0, alpha=0.5)
        for m in ("full", "scalar", "rigid3", "diag"):
            ax.loglog(fq, np.maximum(np.abs(r["chans"][m][ch]), 1e-9),
                      color=cols[m], lw=1.1, ls="-" if m != "full" else ":")
        for fc in r["modes"]:
            ax.axvline(fc, color="0.85", lw=0.6, ls=":")
        ax.set_xlabel("frequency, Hz (log)")
        ax.set_title(ttl + f"  [{unit}]", fontsize=9, loc="left")
    axes[0].set_ylabel("magnitude per unit drive force (log)")
    axes[1].annotate("scalar predicts My ≡ 0\n(off the bottom): the rocking\nchannel is "
                     "structurally invisible", (fq[3], 1e-3), fontsize=8, color="#c0392b")
    axes[2].annotate("thick gray = coupled truth", (fq[3], r["truth"]["foot"].max() * 1.3),
                     fontsize=8, color="0.45")
    fig.suptitle("EX-E — Impedance reconstruction from interface measurements vs the "
                 "coupled FEM truth (soft feet, plate Q=25). Full matrix = exact; scalar "
                 "single-point misses moment & per-foot; rigid-3 recovers them.",
                 fontsize=9.5)
    fig.tight_layout(rect=(0, 0.02, 1, 0.93))
    stamp(fig, SCRIPT)
    fig.savefig(os.path.join(FIG, "fig_e1_reconstruction_channels.png"), dpi=160)
    plt.close(fig)

    # fig_e2: band-peak error heat-ish bars per method/channel/regime
    fig, axes = plt.subplots(1, 4, figsize=(13.4, 4.6), sharey=True)
    methods = ["scalar", "rigid3", "diag"]
    for ax, (lab, r) in zip(axes, runs.items()):
        # worst-foot rel err at each mode, per method
        modes = list(r["mode_err"].keys())
        x = np.arange(len(modes))
        w = 0.26
        for k, m in enumerate(methods):
            vals = [r["mode_err"][mk][m]["foot"]["rel_err"] * 100 for mk in modes]
            ax.bar(x + (k - 1) * w, np.maximum(vals, 0.5), w, color=cols[m],
                   label=lbls[m] if lab == "soft_Q25" else None)
        ax.set_yscale("log")
        ax.set_xticks(x)
        ax.set_xticklabels([mk.split("_")[0] for mk in modes], fontsize=7.5, rotation=20)
        ax.axhline(100, color="0.5", lw=0.7, ls="--")
        ax.set_title(f"{lab}\n(modes {[f'{m:.0f}' for m in r['modes']]} Hz)", fontsize=8.5,
                     loc="left")
    axes[0].set_ylabel("worst per-foot force reconstruction error, %\n(log; dashed = 100%)")
    axes[0].legend(fontsize=7.5, loc="upper left")
    fig.suptitle("EX-E — Per-foot force reconstruction error by method, mode, and regime: "
                 "single-point is blind to rocking everywhere; rigid-3 (≥3 feet) recovers "
                 "it; diagonal works only when feet decouple", fontsize=9.5)
    fig.tight_layout(rect=(0, 0.02, 1, 0.91))
    stamp(fig, SCRIPT)
    fig.savefig(os.path.join(FIG, "fig_e2_error_by_regime.png"), dpi=160)
    plt.close(fig)

    # fig_e3: remote proxy — in-config exact vs config-mismatch fatal
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.7),
                             gridspec_kw=dict(width_ratios=[1.55, 1]))
    fq = rp["freqs"]
    c1 = rp["curves"][0]                                  # 1 foot-spacing
    ax = axes[0]
    ax.loglog(fq, np.abs(c1["T_coup"]), color="0.1", lw=1.3)
    ax.loglog(fq, np.abs(c1["T_bare"]), color="#c0392b", lw=1.1, ls="--")
    ax.annotate("T measured WITH payload\n(integrated/coupled config)", (43, 9),
                fontsize=8, color="0.1")
    ax.annotate("T measured on BARE backing\n(wrong config): resonances land at\n"
                "different frequencies", (140, 0.05), fontsize=8, color="#c0392b")
    ax.set_xlabel("frequency, Hz (log)")
    ax.set_ylabel("transmissibility |a_remote / a_meanfeet| (log)")
    ax.set_title("a. Why config matters (control accel 1 foot-spacing away)",
                 fontsize=9, loc="left")
    ax = axes[1]
    x = np.arange(len(rp["curves"]))
    med = [np.median(c["proxy_err"][c["good"]]) * 100 for c in rp["curves"]]
    ax.bar(x, med, 0.5, color="#c0392b")
    ax.axhline(10, color="0.4", lw=0.9, ls="--")
    ax.annotate("in-config linear\ncalibration ≈ 0%\n(exact, any distance)", (0.5, 18),
                fontsize=8.5, color="#27ae60")
    for i, v in enumerate(med):
        ax.annotate(f"{v:.0f}%", (i, v + 4), ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{c['dist_spacings']}" for c in rp["curves"]])
    ax.set_xlabel("distance from foot (foot-spacings)")
    ax.set_ylabel("broadband config-mismatch proxy error, %")
    ax.set_ylim(0, 130)
    ax.set_title("b. Bare-config calibration: ~100% wrong at any distance",
                 fontsize=9, loc="left")
    fig.suptitle("EX-E Part 2 — A remote accelerometer CAN proxy the interface for "
                 "response limiting, but only if transmissibility is calibrated in the "
                 "INTEGRATED config (exact for a linear system, any distance); a bare/"
                 "un-integrated calibration is ~100% wrong because the payload shifts "
                 "every backing mode.", fontsize=9)
    fig.tight_layout(rect=(0, 0.02, 1, 0.92))
    stamp(fig, SCRIPT)
    fig.savefig(os.path.join(FIG, "fig_e3_remote_proxy.png"), dpi=160)
    plt.close(fig)

    print("EX-E done. remote proxy broadband config-mismatch err:",
          {k: f"{v['err_off_resonance_med']*100:.0f}%"
           for k, v in res["remote_proxy"].items() if isinstance(v, dict)})


if __name__ == "__main__":
    main()
