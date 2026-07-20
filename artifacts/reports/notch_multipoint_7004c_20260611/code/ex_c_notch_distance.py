"""
EX-C: Notch geography — how far from a mounting foot can you still SEE the notch?

Compliant backing = simply supported aluminum plate (analytic modes). Payload =
the EX-B rigid box on 4 feet (vertical coupling, DOFs z/thx/thy; ledger C4).
"Flight-like" excitation = unit point force on the plate far from the feet.

The notch = the absorber dip the payload carves into the backing response at its
own resonances — same mechanism as the 7004C Fig 9e dip at r=1, but now the
interface is 4 spaced points, and the payload has bounce AND rocking absorber
modes that live in different interface COMBINATION coordinates:
   bounce -> mean of feet accels;  rock_y -> x-differential;  rock_x -> y-differential.

Detection: deepest INTERIOR local minimum (prominence >= 3 dB) of the relevant
interface-combination spectrum within [0.7, 1.3]x the fixed-base payload mode.
Edge hits / shallow dips => notch labeled NOT DETECTED (honest).

Visibility metrics per plate point (quantity contract Q6):
  D_dip(x,y)    = 20log10( band-median |a_loaded| / |a_loaded(f_notch)| )
  D_change(x,y) = 20log10( |a_bare(f_notch)| / |a_loaded(f_notch)| )
r_vis = first 3-dB crossing of the binned-median D_dip vs distance-to-nearest-
foot curve ("GLOBAL" if it never crosses on the plate; 0 if invisible at foot).

Regime axis: modal overlap factor MOF = (f/Q_plate) / mean modal spacing.
MOF << 1: discrete global modes -> absorber retunes modes -> notch global.
MOF >~ 1: diffuse regime -> locality on the bending-wavelength scale.
Variants probe both: foot stiffness x1/x9, plate t 3.5/5/8 mm, plate Q 25 vs 6.

Verification: low-f rigid ride-along; solve path identical to verify.py gates;
modal-truncation convergence (1250 vs 2500 Hz mode sets) on fixed detection.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import (M_PAY, AX, AY, KZ_FOOT, box_inertia, plate_modal_system,
                    phi_matrix, foot_points, coupled_plate_payload_frf,
                    bare_plate_field, LX, LY, TPL, FORCE_PT,
                    FIG, RES, save_json, stamp)

SCRIPT = "ex_c_notch_distance.py"
# interface combination weights over feet [(+,+),(+,-),(-,+),(-,-)]
COMBOS_W = dict(bounce=np.array([1, 1, 1, 1]) / 4.0,
                rock_y=np.array([+1, +1, -1, -1]) / 2.0,   # x-differential
                rock_x=np.array([+1, -1, +1, -1]) / 2.0)   # y-differential


def fixed_base_payload_modes(kz):
    Ixx = box_inertia()[0, 0]
    Iyy = box_inertia()[1, 1]
    return dict(rock_x=np.sqrt(4 * kz * AY**2 / Ixx) / (2 * np.pi),
                rock_y=np.sqrt(4 * kz * AX**2 / Iyy) / (2 * np.pi),
                bounce=np.sqrt(4 * kz / M_PAY) / (2 * np.pi))


def bending_wavelength(f_hz, t):
    from common import E_PL, NU_PL, RHO_PL
    D = E_PL * t**3 / (12 * (1 - NU_PL**2))
    w = 2 * np.pi * f_hz
    return 2 * np.pi / (RHO_PL * t * w**2 / D) ** 0.25


def modal_spacing(sysd, f_hz, half=100.0):
    fr = sysd["wn"] / (2 * np.pi)
    cnt = np.sum((fr > f_hz - half) & (fr < f_hz + half))
    return 2 * half / max(cnt, 1)


def grid_points(nx=81, ny=65):
    xs = np.linspace(LX * 0.015, LX * 0.985, nx)
    ys = np.linspace(LY * 0.015, LY * 0.985, ny)
    XX, YY = np.meshgrid(xs, ys)
    pts = np.column_stack([XX.ravel(), YY.ravel()])
    fp = np.array(foot_points())
    dist = np.min(np.linalg.norm(pts[:, None, :] - fp[None, :, :], axis=2), axis=1)
    return pts, dist, (xs, ys, XX.shape)


def loaded_field_at(freqs, sysd, pts, kz, zeta_pl):
    cp = coupled_plate_payload_frf(freqs, sysd, ex=0.0, kz=kz, zeta_pl=zeta_pl)
    Phi_p = phi_matrix(sysd, pts)
    w2 = (2 * np.pi * freqs) ** 2
    return -(w2[:, None]) * (cp["qm"] @ Phi_p.T), cp


def hit_val(mag, freqs, f_n):
    return float(mag[np.argmin(np.abs(freqs - f_n))])


def interior_minima(freqs, mag, flo, fhi, prom_db=3.0):
    """All interior local minima with >= prom_db prominence: [(f, dB, prom)]."""
    sel = np.where((freqs >= flo) & (freqs <= fhi))[0]
    f, m = freqs[sel], 20 * np.log10(mag[sel])
    out = []
    for i in range(1, len(f) - 1):
        if m[i] <= m[i - 1] and m[i] <= m[i + 1]:
            prom = min(m[:i + 1].max(), m[i:].max()) - m[i]
            if prom >= prom_db:
                out.append((float(f[i]), float(m[i]), float(prom)))
    return out


def interior_min(freqs, mag, flo, fhi, prom_db=3.0, f_anchor=None):
    """Pick from interior_minima: the minimum CLOSEST to f_anchor (the payload
    fixed-base mode) — robust to near-tied deepest minima flipping under modal
    refinement (multi-point systems carve a CLUSTER of dips, see packet §5).
    Falls back to deepest if no anchor. Returns (f, dB, prom, cluster)."""
    mins = interior_minima(freqs, mag, flo, fhi, prom_db)
    if not mins:
        return None
    if f_anchor is None:
        best = min(mins, key=lambda t_: t_[1])
    else:
        best = min(mins, key=lambda t_: abs(t_[0] - f_anchor))
    return (*best, mins)


def analyze_combo(kz_mult, t, zeta_pl, n_modes_fmax=1250.0, label=""):
    kz = KZ_FOOT * kz_mult
    sysd = plate_modal_system(n_modes_fmax, t=t)
    f0 = fixed_base_payload_modes(kz)
    pts, dist, gridinfo = grid_points()

    base = np.geomspace(20, 500, 900)
    refine = np.concatenate([np.linspace(v * 0.68, min(v * 1.32, 500), 700)
                             for v in f0.values() if v < 490])
    freqs = np.unique(np.concatenate([base, refine]))
    fp = foot_points()
    acc_feet_loaded, cp = loaded_field_at(freqs, sysd, fp, kz, zeta_pl)
    acc_feet_bare = bare_plate_field(freqs, sysd, fp, zeta_pl=zeta_pl)
    w2 = (2 * np.pi * freqs) ** 2
    acc_cg = -(w2[:, None]) * cp["qp"]

    i_lo = np.argmin(np.abs(freqs - 22.0))
    ride = abs(acc_cg[i_lo, 0]) / abs(acc_feet_loaded[i_lo].mean())

    notches = []
    for mode_name, fm in f0.items():
        if fm > 480:
            continue
        # detection on the loaded/bare RATIO in the matching interface channel:
        # minima of R = payload-CAUSED suppression (bare-plate antiresonances cancel)
        Rcomb = (np.abs(acc_feet_loaded @ COMBOS_W[mode_name])
                 / np.abs(acc_feet_bare @ COMBOS_W[mode_name]))
        hit = interior_min(freqs, Rcomb, fm * 0.6, min(fm * 1.25, 500.0),
                           prom_db=6.0, f_anchor=fm)
        if hit is None:
            notches.append(dict(mode=mode_name, f_fixed_base=float(fm),
                                detected=False))
            continue
        f_n = float(hit[0])
        cluster = hit[3]
        band = np.linspace(f_n * 0.85, f_n * 1.15, 41)
        accL, _ = loaded_field_at(band, sysd, pts, kz, zeta_pl)
        accB = bare_plate_field(band, sysd, pts, zeta_pl=zeta_pl)
        i_n = np.argmin(np.abs(band - f_n))
        med = np.median(np.abs(accL), axis=0)
        D_dip = 20 * np.log10(med / np.abs(accL[i_n]))           # Q6 secondary
        D_change = 20 * np.log10(np.abs(accB[i_n]) / np.abs(accL[i_n]))  # primary
        bins = np.arange(0.0, 0.68, 0.04)
        bc = 0.5 * (bins[:-1] + bins[1:])

        def binned(D):
            return np.array([np.median(D[(dist >= a) & (dist < b)])
                             if ((dist >= a) & (dist < b)).any() else np.nan
                             for a, b in zip(bins[:-1], bins[1:])])

        med_change, med_dip = binned(D_change), binned(D_dip)

        def vis_radius(mc):
            ok = ~np.isnan(mc)
            bc_ok, mc_ok = bc[ok], mc[ok]
            if not mc_ok[0] >= 3.0:
                return 0.0, "invisible_at_foot", False
            cross = np.where(mc_ok < 3.0)[0]
            if len(cross) == 0:
                return float(bc_ok[-1]), "global", True
            j = cross[0]
            x0, x1 = bc_ok[j - 1], bc_ok[j]
            y0, y1 = mc_ok[j - 1], mc_ok[j]
            return (float(x0 + (3.0 - y0) * (x1 - x0) / (y1 - y0)), "local", True)

        r_vis, regime, visible_at_foot = vis_radius(med_change)
        r_vis_dip, regime_dip, vis_foot_dip = vis_radius(med_dip)
        lam = bending_wavelength(f_n, t)
        dfm = modal_spacing(sysd, f_n)
        notches.append(dict(
            mode=mode_name, f_fixed_base=float(fm), f_notch=f_n, detected=True,
            suppression_at_interface_dB=float(-20 * np.log10(hit_val(Rcomb, freqs, f_n))),
            dip_cluster=[dict(f=c[0], depth_dB=c[1], prominence_dB=c[2])
                         for c in cluster],
            prominence_dB=float(hit[2]),
            notch_shift_pct=float(100 * (f_n - fm) / fm),
            r_vis_3dB_m=r_vis, regime=regime, visible_at_foot=visible_at_foot,
            r_vis_dip_3dB_m=r_vis_dip, regime_dip=regime_dip,
            visible_at_foot_dip=vis_foot_dip,
            lambda_m=float(lam), mof=float((f_n / (1 / (2 * zeta_pl))) / dfm),
            modal_spacing_hz=float(dfm),
            area_frac_3dB=float((D_change >= 3.0).mean()),
            area_frac_dip_3dB=float((D_dip >= 3.0).mean()),
            D_dip=D_dip, D_change=D_change,
            medcurve=med_change.tolist(), medcurve_dip=med_dip.tolist(),
            bin_centers=bc.tolist()))
    return dict(label=label, kz_mult=kz_mult, t=t, zeta_pl=zeta_pl,
                n_modes=sysd["n_modes"], fixed_base_modes=f0,
                ride_along=float(ride), freqs=freqs,
                acc_feet_loaded=acc_feet_loaded, acc_feet_bare=acc_feet_bare,
                acc_cg=acc_cg, notches=notches, pts=pts, dist=dist,
                gridinfo=gridinfo)


def main():
    combos = [
        ("soft_t5_Q25", 1.0, TPL, 0.02), ("stiff_t5_Q25", 9.0, TPL, 0.02),
        ("soft_t5_Q6", 1.0, TPL, 0.08), ("stiff_t5_Q6", 9.0, TPL, 0.08),
        ("stiff_t3p5_Q25", 9.0, 0.0035, 0.02), ("stiff_t8_Q25", 9.0, 0.008, 0.02),
        ("soft_t3p5_Q25", 1.0, 0.0035, 0.02),
    ]
    runs = {}
    for label, kzm, t, z in combos:
        runs[label] = analyze_combo(kzm, t, z, label=label)
        msg = []
        for x in runs[label]["notches"]:
            if x["detected"]:
                msg.append(f"{x['mode']}: fn={x['f_notch']:.0f}Hz({x['notch_shift_pct']:+.0f}%) "
                           f"rvis={x['r_vis_3dB_m']:.2f}m[{x['regime']}] "
                           f"lam={x['lambda_m']:.2f} MOF={x['mof']:.2f}")
            else:
                msg.append(f"{x['mode']}: NOT DETECTED")
        print(f"{label:15s} nm={runs[label]['n_modes']:3d} "
              f"ride={runs[label]['ride_along']:.3f} | " + " | ".join(msg))

    # ---- truncation convergence (fixed detection logic) ----
    conv = {}
    for label, kzm, t, z in [c for c in combos if c[0] in ("soft_t5_Q25", "stiff_t5_Q25")]:
        hi = analyze_combo(kzm, t, z, n_modes_fmax=2500.0, label=label + "_hi")
        pairs = []
        for nl, nh in zip(runs[label]["notches"], hi["notches"]):
            if not (nl.get("detected") and nh.get("detected")):
                pairs.append(dict(mode=nl["mode"], note="detection differs",
                                  lo=nl.get("detected"), hi=nh.get("detected")))
                continue
            pairs.append(dict(
                mode=nl["mode"],
                f_notch_shift_pct=100 * abs(nl["f_notch"] - nh["f_notch"]) / nh["f_notch"],
                r_vis_shift_m=abs(nl["r_vis_3dB_m"] - nh["r_vis_3dB_m"]),
                area_frac_shift=abs(nl["area_frac_3dB"] - nh["area_frac_3dB"])))
        conv[label] = dict(n_modes_lo=runs[label]["n_modes"],
                           n_modes_hi=hi["n_modes"], pairs=pairs)
        print(f"convergence {label}: {pairs}")

    res = dict(combos={}, convergence=conv)
    for label, r in runs.items():
        res["combos"][label] = dict(
            kz_mult=r["kz_mult"], t=r["t"], zeta_pl=r["zeta_pl"],
            n_modes=r["n_modes"], ride_along_lowf=r["ride_along"],
            fixed_base_modes={k: float(v) for k, v in r["fixed_base_modes"].items()},
            notches=[{k: v for k, v in n.items() if k not in ("D_dip", "D_change")}
                     for n in r["notches"]])
    save_json(os.path.join(RES, "ex_c_results.json"), res)

    main_runs = {k: runs[k] for k in ("soft_t5_Q25", "stiff_t5_Q25", "stiff_t5_Q6")}
    np.savez_compressed(
        os.path.join(RES, "ex_c_fields.npz"),
        **{f"{k}__{n['mode']}__Ddip": n["D_dip"] for k, r in main_runs.items()
           for n in r["notches"] if n.get("detected")},
        **{f"{k}__{n['mode']}__Dchange": n["D_change"] for k, r in main_runs.items()
           for n in r["notches"] if n.get("detected")},
        **{f"{k}__{n['mode']}__fnotch": np.array(n["f_notch"])
           for k, r in main_runs.items() for n in r["notches"] if n.get("detected")},
        pts=runs["soft_t5_Q25"]["pts"], dist=runs["soft_t5_Q25"]["dist"],
        xs=runs["soft_t5_Q25"]["gridinfo"][0], ys=runs["soft_t5_Q25"]["gridinfo"][1],
        grid_shape=np.array(runs["soft_t5_Q25"]["gridinfo"][2]))

    # ================= figures =================
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False})
    fp = np.array(foot_points())

    def notch_of(lab, mode):
        return [x for x in runs[lab]["notches"] if x["mode"] == mode][0]

    # --- fig_c1: interface spectra, soft variant ---
    r = runs["soft_t5_Q25"]
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 7.0), sharex=True)
    fq = r["freqs"]
    ax = axes[0]
    ax.loglog(fq, np.abs(r["acc_feet_bare"]).mean(axis=1), color="#2980b9", lw=1.1)
    ax.loglog(fq, np.abs(r["acc_feet_loaded"]).mean(axis=1), color="0.1", lw=1.3)
    for n in r["notches"]:
        if not n.get("detected"):
            continue
        ax.axvline(n["f_notch"], color="0.75", lw=0.7, ls=":")
        ax.annotate(f"{n['mode']}\n{n['f_notch']:.0f} Hz", (n["f_notch"], 2.5e-4),
                    fontsize=7.5, ha="center", color="0.35")
    ax.annotate("bare plate (no payload)", (24, 0.25), color="#2980b9", fontsize=8.5)
    ax.annotate("plate + payload: notches carved at the\npayload's absorber frequencies "
                "(NOT exactly its\nfixed-base modes — see shift, packet §5)",
                (24, 7e-4), color="0.1", fontsize=8.5)
    ax.set_ylabel("mean |a| at the 4 feet\nper unit force, (m/s²)/N (log)")
    ax.set_title("EX-C — The payload carves notches into the backing response "
                 "(soft feet, t=5 mm, plate Q=25; unit point force at (0.18,0.62) m)",
                 fontsize=9.5, loc="left")
    ax = axes[1]
    comb_ry = np.abs(r["acc_feet_loaded"] @ COMBOS_W["rock_y"])
    ax.loglog(fq, np.abs(r["acc_feet_loaded"] @ COMBOS_W["bounce"]), color="0.1", lw=1.1)
    ax.loglog(fq, comb_ry, color="#c0392b", lw=1.1)
    ax.loglog(fq, np.abs(r["acc_cg"][:, 0]), color="#27ae60", lw=1.0, ls="--")
    ax.annotate("mean-feet combination (bounce channel)", (24, 1.2e-1), color="0.1",
                fontsize=8.5)
    ax.annotate("x-differential combination (rock_y channel):\nthe ROCKING notch lives "
                "here, invisible in the mean", (24, 1.1e-4), color="#c0392b", fontsize=8.5)
    ax.annotate("payload CG heave (absorber peaks at the notch)", (24, 6e-3),
                color="#27ae60", fontsize=8.5)
    ax.set_xlabel("frequency, Hz (log)")
    ax.set_ylabel("|a| combination per unit force\n(m/s²)/N (log)")
    fig.tight_layout()
    stamp(fig, SCRIPT)
    fig.savefig(os.path.join(FIG, "fig_c1_interface_spectra.png"), dpi=170)
    plt.close(fig)

    # --- fig_c2: bounce-notch visibility maps across regimes ---
    sel = [("soft_t5_Q25", "a. soft feet, plate Q=25"),
           ("stiff_t5_Q25", "b. stiff feet (9x), plate Q=25"),
           ("soft_t5_Q6", "c. soft feet, plate Q=6"),
           ("stiff_t5_Q6", "d. stiff feet (9x), plate Q=6")]
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 8.6))
    for ax, (lab, ttl) in zip(axes.flat, sel):
        n = notch_of(lab, "bounce")
        xs, ys, shape = runs[lab]["gridinfo"]
        Z = n["D_change"].reshape(shape)
        im = ax.pcolormesh(xs, ys, Z, cmap="viridis", vmin=-3, vmax=15, shading="auto")
        ax.plot(fp[:, 0], fp[:, 1], "s", ms=6, mfc="none", mec="w", mew=1.6)
        ax.plot(*FORCE_PT, "*", ms=11, mfc="#c0392b", mec="w")
        th = np.linspace(0, 2 * np.pi, 100)
        for (fx, fy) in fp:
            ax.plot(fx + n["lambda_m"] / 4 * np.cos(th),
                    fy + n["lambda_m"] / 4 * np.sin(th), "w:", lw=0.9)
        ax.set_title(f"{ttl}\nf_n={n['f_notch']:.0f} Hz, λ={n['lambda_m']:.2f} m, "
                     f"MOF={n['mof']:.2f}, r_vis={n['r_vis_3dB_m']:.2f} m [{n['regime']}]",
                     fontsize=8.5, loc="left")
        ax.set_aspect("equal"); ax.set_xlim(0, LX); ax.set_ylim(0, LY)
    cb = fig.colorbar(im, ax=axes, shrink=0.85, pad=0.02)
    cb.set_label("D_change = suppression vs bare plate at f_notch, dB (clipped [-3,15])")
    fig.suptitle("EX-C — BOUNCE-notch suppression D_change across regimes. White squares = "
                 "feet, star = drive force, dotted = λ/4 circles.\nLow modal overlap "
                 "(MOF<1): notch retunes GLOBAL modes — visible far beyond λ/4. Higher "
                 "damping/MOF: locality emerges.", fontsize=10)
    stamp(fig, SCRIPT)
    fig.savefig(os.path.join(FIG, "fig_c2_notch_maps_bounce.png"), dpi=160)
    plt.close(fig)

    # --- fig_c2b: rocking notch maps ---
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.6))
    shown = 0
    for ax, lab in zip(axes, ("soft_t5_Q25", "stiff_t5_Q25")):
        n = notch_of(lab, "rock_x")
        if not n.get("detected"):
            ax.text(0.5, 0.5, f"{lab}: rock_x notch NOT DETECTED\n(no >=3 dB interior "
                    "dip in the y-differential channel)", ha="center", va="center",
                    transform=ax.transAxes, fontsize=9)
            ax.set_axis_off()
            continue
        xs, ys, shape = runs[lab]["gridinfo"]
        Z = n["D_change"].reshape(shape)
        im = ax.pcolormesh(xs, ys, Z, cmap="viridis", vmin=-3, vmax=15, shading="auto")
        shown += 1
        ax.plot(fp[:, 0], fp[:, 1], "s", ms=6, mfc="none", mec="w", mew=1.6)
        ax.plot(*FORCE_PT, "*", ms=11, mfc="#c0392b", mec="w")
        ax.set_title(f"{lab}: rock_x notch {n['f_notch']:.0f} Hz\n"
                     f"r_vis={n['r_vis_3dB_m']:.2f} m [{n['regime']}], "
                     f"foot-visible: {n['visible_at_foot']}", fontsize=8.5, loc="left")
        ax.set_aspect("equal")
    if shown:
        cb = fig.colorbar(im, ax=axes, shrink=0.85, pad=0.02)
        cb.set_label("D_change, dB")
    fig.suptitle("EX-C — ROCKING notch in POINT spectra: rocking is a differential "
                 "(moment) absorber; a single accelerometer can miss it entirely",
                 fontsize=10)
    stamp(fig, SCRIPT)
    fig.savefig(os.path.join(FIG, "fig_c2b_notch_maps_rocking.png"), dpi=160)
    plt.close(fig)

    # --- fig_c3: D_dip vs distance ---
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.6), sharey=True)
    for ax, lab in zip(axes, ("soft_t5_Q25", "stiff_t5_Q25", "stiff_t5_Q6")):
        rr = runs[lab]
        colors = {"bounce": "0.1", "rock_x": "#c0392b", "rock_y": "#2980b9"}
        ytxt = 20.0
        for n in rr["notches"]:
            if not n.get("detected"):
                continue
            c = colors[n["mode"]]
            ax.plot(rr["dist"], n["D_change"], ".", ms=1.1, color=c, alpha=0.14)
            ax.plot(n["bin_centers"], n["medcurve"], "-", color=c, lw=1.8)
            ax.plot(n["bin_centers"], n["medcurve_dip"], "--", color=c, lw=1.0)
            ax.axvline(n["lambda_m"] / 4, color=c, lw=0.9, ls=":")
            ax.annotate(f"{n['mode']} {n['f_notch']:.0f} Hz  λ/4={n['lambda_m']/4:.2f}  "
                        f"r_vis={n['r_vis_3dB_m']:.2f} [{n['regime']}]",
                        (0.012, ytxt), fontsize=7.5, color=c)
            ytxt -= 1.6
        ax.axhline(3.0, color="0.5", lw=0.8, ls="--")
        ax.set_xlabel("distance to nearest foot, m")
        ax.set_title(lab, fontsize=9, loc="left")
        ax.set_xlim(0, 0.62); ax.set_ylim(-6, 22)
    axes[0].set_ylabel("suppression / dip at f_notch, dB\n(dots+solid = D_change suppression,\ndashed = D_dip single-spectrum dip)")
    axes[0].annotate("3 dB visibility threshold", (0.40, 3.4), fontsize=7.5, color="0.4")
    fig.suptitle("EX-C — Notch visibility vs distance from the nearest foot (dotted "
                 "verticals = λ/4 guess): distance decay only appears once modal "
                 "overlap/damping is high", fontsize=10)
    fig.tight_layout(rect=(0, 0.02, 1, 0.92))
    stamp(fig, SCRIPT)
    fig.savefig(os.path.join(FIG, "fig_c3_depth_vs_distance.png"), dpi=170)
    plt.close(fig)

    # --- fig_c4: r_vis and area fraction vs MOF / lambda ---
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.0))
    mk = {"bounce": "o", "rock_x": "s", "rock_y": "^"}
    ax = axes[0]
    for lab, r_ in runs.items():
        for n in r_["notches"]:
            if not n.get("detected"):
                continue
            col = "#c0392b" if n["mof"] > 1 else "#2980b9"
            fc = col if not n["visible_at_foot"] else "none"
            ax.plot(n["mof"], n["area_frac_3dB"] * 100, mk[n["mode"]], ms=7,
                    mfc=fc, mec=col, mew=1.5)
    ax.axvline(1.0, color="0.6", lw=0.9, ls="--")
    ax.annotate("MOF = 1\n(discrete modes | diffuse)", (1.04, 78), fontsize=8, color="0.4")
    ax.set_xscale("log")
    ax.set_xlabel("modal overlap factor at the notch frequency (log)")
    ax.set_ylabel("% of plate area where dip ≥ 3 dB")
    ax.set_title("a. How much of the backing sees the notch", fontsize=9.5, loc="left")
    ax = axes[1]
    for lab, r_ in runs.items():
        for n in r_["notches"]:
            if not n.get("detected") or not n["visible_at_foot"]:
                continue
            col = "#c0392b" if n["mof"] > 1 else "#2980b9"
            ax.plot(n["lambda_m"], n["r_vis_3dB_m"], mk[n["mode"]], ms=7,
                    mfc="none", mec=col, mew=1.5)
    lam_line = np.linspace(0.2, 1.0, 10)
    ax.plot(lam_line, lam_line / 4, "0.4", lw=1.0, ls=":")
    ax.annotate("r = λ/4", (0.85, 0.85 / 4 + 0.012), fontsize=9, color="0.4")
    ax.set_xlabel("bending wavelength λ at the notch frequency, m")
    ax.set_ylabel("3-dB visibility radius r_vis, m")
    ax.set_title("b. Visibility radius vs λ (only notches visible at a foot;\n"
                 "blue MOF<1 saturate at plate size = global; red MOF>1)",
                 fontsize=9.5, loc="left")
    fig.suptitle("EX-C — Across 7 variants (markers: o=bounce, s=rock_x, ^=rock_y): "
                 "modal overlap — not a fixed radius — decides whether the notch is "
                 "local or global", fontsize=10)
    fig.tight_layout(rect=(0, 0.02, 1, 0.9))
    stamp(fig, SCRIPT)
    fig.savefig(os.path.join(FIG, "fig_c4_rvis_vs_lambda.png"), dpi=170)
    plt.close(fig)

    print("EX-C done.")


if __name__ == "__main__":
    main()
