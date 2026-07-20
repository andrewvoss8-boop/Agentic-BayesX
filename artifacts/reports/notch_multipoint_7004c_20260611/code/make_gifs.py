"""
Teaching GIFs (matplotlib PillowWriter; decisions_log D6). Each GIF also saves a
_still.png first frame for the packet. Deterministic model output, no measured data.

GIF A: 7004C TDOF system swept through the notch — the absorber mechanism.
GIF B: EX-B rocking mode under lateral drive — per-foot forces large, net ~ 0.
GIF C: EX-C suppression field vs frequency — watch the plate go quiet at the
       payload absorber frequencies (soft feet variant, plate Q=25).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import PillowWriter
from matplotlib.patches import Rectangle, FancyArrow

from common import (QA, coupled_interface, payload_6dof_matrices,
                    transform_O_from_CG, plate_modal_system, phi_matrix,
                    foot_points, coupled_plate_payload_frf, bare_plate_field,
                    AX, AY, H_CG, LBOX, LX, LY, FORCE_PT, FIG, stamp)

FPS = 11


def spring_xy(x0, y0, x1, y1, n=7, w=0.012):
    """Zigzag spring polyline between two points."""
    t = np.linspace(0, 1, 2 * n + 2)
    px = x0 + (x1 - x0) * t
    py = y0 + (y1 - y0) * t
    L = np.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / max(L, 1e-9), (x1 - x0) / max(L, 1e-9)
    for i in range(1, len(t) - 1):
        s = w if i % 2 else -w
        px[i] += nx * s
        py[i] += ny * s
    return px, py


def gif_a():
    r_grid = np.linspace(0.30, 1.90, 90)
    rr = np.linspace(0.25, 2.0, 1200)
    _, _, _, Aif, _ = coupled_interface(rr)

    def coupled_disp(r):
        m = k = 1.0
        c = 1.0 / QA
        w = r
        Xb = -1.0 / w**2
        K = np.array([[2 * (k + 1j * w * c) - w**2 * m, -(k + 1j * w * c)],
                      [-(k + 1j * w * c), k + 1j * w * c - w**2 * m]], dtype=complex)
        X = np.linalg.solve(K, np.array([(k + 1j * w * c) * Xb, 0]))
        return Xb, X[0], X[1]

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(9.2, 4.4),
                                   gridspec_kw=dict(width_ratios=[1, 1.5]))
    fig.suptitle("7004C TDOF system: sweep through the notch — the load becomes a "
                 "vibration absorber at its fixed-base resonance (r=1)", fontsize=9.5)
    stamp(fig, "make_gifs.py (EX-A model)")
    wr = PillowWriter(fps=FPS)
    path = os.path.join(FIG, "gif_a_tdof_notch_sweep.gif")
    phase = 0.0
    with wr.saving(fig, path, dpi=95):
        for fi, r in enumerate(r_grid):
            Xb, X1, X2 = coupled_disp(r)
            sc = 0.16 / max(abs(X1), abs(X2), abs(Xb))
            phase += 0.65
            xb = sc * (Xb * np.exp(1j * phase)).real
            x1 = sc * (X1 * np.exp(1j * phase)).real
            x2 = sc * (X2 * np.exp(1j * phase)).real
            axl.clear()
            axl.set_xlim(-0.6, 0.6); axl.set_ylim(-0.15, 1.25)
            axl.set_axis_off()
            yb, y1, y2 = 0.0, 0.45, 0.95
            axl.add_patch(Rectangle((-0.5 + xb, yb - 0.06), 1.0, 0.06, color="0.4"))
            axl.add_patch(Rectangle((-0.22 + x1, y1), 0.44, 0.16, color="#2980b9"))
            axl.add_patch(Rectangle((-0.16 + x2, y2), 0.32, 0.13, color="#c0392b"))
            for dx in (-0.12, 0.12):
                px, py = spring_xy(dx + xb, yb, dx + x1, y1)
                axl.plot(px, py, color="0.25", lw=1.1)
                px, py = spring_xy(dx + x1, y1 + 0.16, dx + x2, y2)
                axl.plot(px, py, color="0.25", lw=1.1)
            axl.annotate("source m1 (interface on top)", (-0.55, y1 + 0.20), fontsize=7.5,
                         color="#2980b9")
            axl.annotate("load m2", (-0.55, y2 + 0.16), fontsize=7.5, color="#c0392b")
            axl.annotate(f"drive r = {r:.2f}", (-0.55, -0.13), fontsize=8.5)
            if 0.97 < r < 1.03:
                axl.annotate("NOTCH: m2 absorbs,\ninterface goes quiet", (0.05, 1.13),
                             fontsize=8.5, color="#c0392b", weight="bold")
            axr.clear()
            axr.semilogy(rr, np.abs(Aif), color="0.15", lw=1.2)
            ridx = np.argmin(np.abs(rr - r))
            axr.plot([r], [np.abs(Aif[ridx])], "o", ms=7, color="#c0392b")
            axr.set_xlabel("frequency ratio r = ω/ω₀")
            axr.set_ylabel("|interface acceleration| (log)")
            axr.set_title("flight interface acceleration (7004C Fig 9e)", fontsize=8.5)
            wr.grab_frame()
            if fi == 44:
                fig.savefig(os.path.join(FIG, "gif_a_still.png"), dpi=130)
    plt.close(fig)
    print("wrote", os.path.basename(path))


def gif_b():
    # response at the upper x-ry rocking mode under unit lateral base accel
    import scipy.linalg as sla
    p = payload_6dof_matrices(ex=0.0, hysteretic=False)
    lam, vec = sla.eigh(p["K"].real, p["M"])
    f_all = np.sqrt(lam) / (2 * np.pi)
    # pick mode with dominant (x, ry) content, upper one
    iry = [i for i in range(6)
           if abs(vec[3, i]) + abs(vec[5, i]) < 0.2 * (abs(vec[0, i]) + abs(vec[4, i]) * 1)]
    imode = max(iry, key=lambda i: f_all[i])
    fmode = f_all[imode]
    pH = payload_6dof_matrices(ex=0.0, hysteretic=True)
    w = 2 * np.pi * fmode
    rhs = np.zeros(6, dtype=complex)
    JOs, kfs = [], []
    for ft in pH["feet"]:
        ro = ft["r_o"]
        JO = np.hstack([np.eye(3), -np.array([[0, -ro[2], ro[1]],
                                              [ro[2], 0, -ro[0]],
                                              [-ro[1], ro[0], 0]])])
        kf = np.diag(ft["k_diag"] * (1 + 0.04j))
        JOs.append(JO); kfs.append(kf)
    ab = np.zeros(6); ab[0] = 1.0          # lateral x drive
    ub = ab / (-(w**2))
    for ft, JO, kf in zip(pH["feet"], JOs, kfs):
        rhs += ft["J"].T @ kf @ (JO @ ub)
    u = np.linalg.solve(pH["K"] - w**2 * pH["M"], rhs)
    Fz = []
    for ft, JO, kf in zip(pH["feet"], JOs, kfs):
        df = kf @ (JO @ ub - ft["J"] @ u)
        Fz.append(df[2])
    Fz = np.array(Fz)
    netF = Fz.sum()
    My = -(Fz * np.array([ft["r_o"][0] for ft in pH["feet"]])).sum()

    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    fig.suptitle(f"EX-B rocking mode ({fmode:.1f} Hz, lateral base drive):\nper-foot "
                 "forces LARGE, net vertical force ≈ 0 — the resultant trap", fontsize=9)
    stamp(fig, "make_gifs.py (EX-B model)")
    wr = PillowWriter(fps=FPS)
    path = os.path.join(FIG, "gif_b_rocking_trap.gif")
    scd = 0.05 / max(abs(u[0]), abs(u[4]) * AX, 1e-12)     # displacement scale
    scF = 0.14 / np.max(np.abs(Fz))                        # force arrow scale
    cz_bot, cz_cg = 0.06, 0.06 + H_CG                      # drawing geometry
    with wr.saving(fig, path, dpi=95):
        for k in range(64):
            ph = np.exp(1j * 2 * np.pi * k / 32)
            ax.clear()
            ax.set_xlim(-0.44, 0.44); ax.set_ylim(-0.40, 0.46)
            ax.set_aspect("equal"); ax.set_axis_off()
            xb = scd * (ub[0] * ph).real
            ax.add_patch(Rectangle((-0.34 + xb, -0.09), 0.68, 0.05, color="0.4"))
            dx = scd * (u[0] * ph).real
            th = 0.15 * (u[4] * ph).real / max(abs(u[4]), 1e-15)  # rotation, normalized to 0.15 rad max (display exaggeration)
            box_tf = plt.matplotlib.transforms.Affine2D() \
                .rotate_around(dx, cz_cg, th)
            rect = Rectangle((dx - LBOX[0] / 2, cz_bot), LBOX[0], LBOX[2],
                             facecolor="#d5e6f5", edgecolor="#2980b9", lw=1.4,
                             transform=box_tf + ax.transData)
            ax.add_patch(rect)
            for sgn, fz in [(+1, Fz[0]), (-1, Fz[2])]:       # side view feet at +/-AX
                xf0 = dx + sgn * AX                          # corner before rotation
                # rotate corner about CG
                xr = dx + (xf0 - dx) * np.cos(th) - (cz_bot - cz_cg) * np.sin(th)
                zr = cz_cg + (xf0 - dx) * np.sin(th) + (cz_bot - cz_cg) * np.cos(th)
                px, py = spring_xy(sgn * AX + xb, -0.04, xr, zr, n=4)
                ax.plot(px, py, color="0.25", lw=1.1)
                fznow = (fz * ph).real * scF
                if abs(fznow) > 1e-4:
                    ax.add_patch(FancyArrow(sgn * AX, -0.22, 0, fznow, width=0.012,
                                            head_width=0.034, head_length=0.02,
                                            length_includes_head=True,
                                            color="#c0392b"))
                ax.annotate(f"F = {((fz*ph).real):+6.1f} N", (sgn * AX - 0.065, -0.385),
                            fontsize=8.5, color="#c0392b")
            ax.annotate(f"per-foot |F| = {np.max(np.abs(Fz)):.1f} N\n"
                        f"net ΣFz = {abs(netF):.1e} N (≈ 0)\n"
                        f"moment |My| = {abs(My):.1f} N·m\n"
                        "→ net-force limiter is BLIND here",
                        (-0.43, 0.30), fontsize=9)
            wr.grab_frame()
            if k == 8:
                fig.savefig(os.path.join(FIG, "gif_b_still.png"), dpi=130)
    plt.close(fig)
    print("wrote", os.path.basename(path))


def gif_c():
    sysd = plate_modal_system(1250.0)
    nx, ny = 49, 39
    xs = np.linspace(LX * 0.02, LX * 0.98, nx)
    ys = np.linspace(LY * 0.02, LY * 0.98, ny)
    XX, YY = np.meshgrid(xs, ys)
    pts = np.column_stack([XX.ravel(), YY.ravel()])
    freqs = np.linspace(60, 170, 100)
    cp = coupled_plate_payload_frf(freqs, sysd, ex=0.0)
    Phi_p = phi_matrix(sysd, pts)
    w2 = (2 * np.pi * freqs) ** 2
    accL = -(w2[:, None]) * (cp["qm"] @ Phi_p.T)
    accB = bare_plate_field(freqs, sysd, pts)
    Rfield = 20 * np.log10(np.abs(accL) / np.abs(accB))
    fpz = np.array(foot_points())
    accLf = -(w2[:, None]) * cp["wfeet"]
    meanfeet = np.abs(accLf).mean(axis=1)
    accBf = bare_plate_field(freqs, sysd, [tuple(x) for x in fpz])
    meanbare = np.abs(accBf).mean(axis=1)

    fig, (axm, axs_) = plt.subplots(1, 2, figsize=(10.4, 4.3),
                                    gridspec_kw=dict(width_ratios=[1.15, 1]))
    fig.suptitle("EX-C soft feet, plate Q=25: loaded/bare change (dB) vs frequency —\n"
                 "the plate goes quiet (dark blue) around the payload absorber "
                 "frequencies", fontsize=9)
    stamp(fig, "make_gifs.py (EX-C model)")
    wr = PillowWriter(fps=FPS)
    path = os.path.join(FIG, "gif_c_notch_field_sweep.gif")
    with wr.saving(fig, path, dpi=95):
        for i, f in enumerate(freqs):
            axm.clear()
            Z = Rfield[i].reshape(XX.shape)
            axm.pcolormesh(xs, ys, Z, cmap="RdBu_r", vmin=-20, vmax=20, shading="auto")
            axm.plot(fpz[:, 0], fpz[:, 1], "s", ms=6, mfc="none", mec="k", mew=1.4)
            axm.plot(*FORCE_PT, "*", ms=11, mfc="#27ae60", mec="k")
            axm.set_aspect("equal")
            axm.set_title(f"loaded/bare, dB  @ {f:.0f} Hz  (blue = suppressed)",
                          fontsize=8.5)
            axs_.clear()
            axs_.semilogy(freqs, meanbare, color="#2980b9", lw=1.0)
            axs_.semilogy(freqs, meanfeet, color="0.1", lw=1.2)
            axs_.axvline(f, color="#c0392b", lw=1.0)
            axs_.annotate("bare", (62, meanbare.max() * 0.7), fontsize=8, color="#2980b9")
            axs_.annotate("with payload", (62, meanfeet.min() * 1.6), fontsize=8,
                          color="0.1")
            axs_.set_xlabel("frequency, Hz (linear: narrow sweep band)")
            axs_.set_ylabel("mean |a| at feet (log)")
            wr.grab_frame()
            if i == 62:
                fig.savefig(os.path.join(FIG, "gif_c_still.png"), dpi=130)
    plt.close(fig)
    print("wrote", os.path.basename(path))


if __name__ == "__main__":
    gif_a()
    gif_b()
    gif_c()
