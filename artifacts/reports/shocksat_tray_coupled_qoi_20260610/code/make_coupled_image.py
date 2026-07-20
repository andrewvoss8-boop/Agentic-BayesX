#!/usr/bin/env python3
"""To-scale image of the COUPLED system FEM (D13 follow-up): the validated
ShockSat primary with the hexapod tray mounted at the single 6-DOF CBUSH
interface point P (gid 7000072, top circular plate centre).

Both meshes drawn in METRES, equal aspect (genuinely to scale), with a scale
bar. ShockSat grids are subsampled for a silhouette; the tray structure
(plate perimeter + 6 struts + 6 feet + the single condensation/mount point) is
drawn in full. The CBUSH is a zero-length 6-DOF spring at P (tray base point
is condensed to P), annotated as THE single joint between the two FEMs.

Outputs figures/fig_coupled_assembly.png + slides/figs/deck_coupled_assembly.png
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import models  # noqa: E402

IN2M = 0.0254
C = dict(shk="#9bb0c4", shkdk="#5b7da0", tray="#b2453c", mount="#1f7a44",
         ref="0.4")
STAMP = ("Agentic BayesX  |  shocksat_tray_coupled_qoi_20260610  |  to scale "
         "(metres, equal aspect)  |  HYPOTHETICAL coupling (methods demo)")


def tray_lines(meta, Pz):
    """Return strut segments, foot points, apex/plate perimeter, base point —
    in metres, shifted so the tray base point sits at (0,0,Pz)."""
    co = meta["coords"].copy()
    co[:, 2] += Pz                      # base point z=0 -> P_z
    sn = meta["strut_nodes"]
    struts = [(co[sn[(n, "top")]], co[sn[(n, "bot")]])
              for n in [k[0] for k in sn if k[1] == "top"]]
    feet = np.array([co[sn[(n, "bot")]] for n in
                     [k[0] for k in sn if k[1] == "bot"]])
    apex = np.array([co[sn[(n, "top")]] for n in
                     [k[0] for k in sn if k[1] == "top"]])
    base = co[meta["BASE"]]
    # plate perimeter from the tensor grid corners
    xs, ys, nid = meta["xs"], meta["ys"], meta["nid"]
    NX, NY = meta["NX"], meta["NY"]
    corners = [nid[("t", 0, 0)], nid[("t", NX-1, 0)], nid[("t", NX-1, NY-1)],
               nid[("t", 0, NY-1)], nid[("t", 0, 0)]]
    plate = co[corners]
    return struts, feet, apex, base, plate


def draw(ax, xi, shk_xyz, tray, Pz, title, P):
    """xi = 0 (x) or 1 (y); plot that-axis vs z elevation, to scale."""
    ax.scatter(shk_xyz[:, xi], shk_xyz[:, 2], s=0.6, c=C["shk"], alpha=0.5,
               linewidths=0, rasterized=True)
    struts, feet, apex, base, plate = tray
    for a, b in struts:
        ax.plot([a[xi], b[xi]], [a[2], b[2]], color=C["tray"], lw=1.6, zorder=5)
    ax.plot(plate[:, xi], plate[:, 2], color=C["tray"], lw=2.0, zorder=5)
    ax.scatter(feet[:, xi], feet[:, 2], s=22, c=C["tray"], zorder=6)
    ax.scatter([P[xi]], [P[2]], s=130, marker="*", c=C["mount"], zorder=8,
               edgecolors="white", linewidths=0.6)
    ax.set_aspect("equal")
    ax.set_xlabel(f"{'xy'[xi]} [m]")
    ax.set_ylabel("z [m]")
    ax.set_title(title, fontsize=11)
    ax.grid(True, color="0.93", lw=0.4)


def main():
    shk = models.ShockSatInterface()
    xyz = shk.xyz * IN2M
    P = shk.node_xyz_in * IN2M
    sub = xyz[::15]                     # silhouette subsample
    tray = models.build_tray_chain()
    tl = tray_lines(tray["meta"], P[2])

    fig = plt.figure(figsize=(12.8, 6.8))
    # panel 1: full stack, front elevation (x-z)
    ax1 = fig.add_subplot(1, 3, 1)
    draw(ax1, 0, sub, tl, P[2], "front elevation (x–z)", P)
    ax1.annotate("payload tray (secondary)", xy=(0.08, P[2]+0.05),
                 xytext=(0.16, P[2]-0.12), fontsize=9, color=C["tray"],
                 arrowprops=dict(arrowstyle="->", color=C["tray"], lw=0.8))
    ax1.annotate("ShockSat\n(primary,\nvalidated twin)", xy=(-0.05, 0.8),
                 xytext=(0.30, 0.62), fontsize=9, color=C["shkdk"],
                 arrowprops=dict(arrowstyle="->", color=C["shkdk"], lw=0.8))
    # scale bar 0.5 m
    x0 = xyz[:, 0].min()
    ax1.plot([x0, x0+0.5], [0.04, 0.04], color="k", lw=2.5)
    ax1.text(x0+0.25, 0.09, "0.5 m", ha="center", fontsize=8)

    # panel 2: side elevation (y-z)
    ax2 = fig.add_subplot(1, 3, 2)
    draw(ax2, 1, sub, tl, P[2], "side elevation (y–z)", P)

    # panel 3: zoom on the interface (to scale)
    ax3 = fig.add_subplot(1, 3, 3)
    near = xyz[np.abs(xyz[:, 2]-P[2]) < 0.18]
    draw(ax3, 0, near, tl, P[2], "interface zoom (x–z, to scale)", P)
    ax3.set_xlim(P[0]-0.40, P[0]+0.40)
    ax3.set_ylim(P[2]-0.15, P[2]+0.19)
    ax3.annotate("single 6-DOF CBUSH mount = THE one joint between the\n"
                 "two FEMs (zero-length; 6 tray feet condensed to this point)",
                 xy=(P[0], P[2]), xytext=(P[0]-0.38, P[2]-0.115), fontsize=8.3,
                 color=C["mount"], weight="bold",
                 arrowprops=dict(arrowstyle="->", color=C["mount"], lw=1.0))
    ax3.annotate("tray plate + 6 struts (feet span ~0.53 m\noverhangs the "
                 "Ø0.46 m plate → methods demo)", xy=(tl[1][:, 0].max(), P[2]),
                 xytext=(P[0]-0.38, P[2]+0.135), fontsize=8.3, color=C["tray"])
    ax3.annotate("ShockSat top plate", xy=(0.20, P[2]),
                 xytext=(0.06, P[2]+0.055), fontsize=8, color=C["shkdk"],
                 arrowprops=dict(arrowstyle="->", color=C["shkdk"], lw=0.7))

    fig.suptitle("The coupled assembly, to scale: hexapod tray on ShockSat at "
                 "the single condensed interface point P (gid 7000072)",
                 fontsize=12.5, weight="bold", y=0.99)
    fig.text(0.005, 0.005, STAMP, fontsize=7.5, color="0.45")
    fig.tight_layout(rect=(0, 0.02, 1, 0.93))
    for d in (os.path.join(WS, "figures"), os.path.join(WS, "slides", "figs")):
        os.makedirs(d, exist_ok=True)
    fig.savefig(os.path.join(WS, "figures", "fig_coupled_assembly.png"),
                dpi=150)
    fig.savefig(os.path.join(WS, "slides", "figs",
                "deck_coupled_assembly.png"), dpi=150)
    plt.close(fig)
    print("wrote fig_coupled_assembly.png (+ deck copy)")
    print(f"P = {np.round(P,3).tolist()} m; tray feet z = {tl[1][0,2]:.3f} m; "
          f"plate z = {tl[4][0,2]:.3f} m")


if __name__ == "__main__":
    main()
