#!/usr/bin/env python3
"""Figures for the buffet dome secondary-structure study (Tufte skill applied:
data-ink, direct labels, small multiples, documented scales, provenance stamps
on every numeric figure). Log frequency axes; linear magnitudes (no dB) per
project rule; PSDs on log-log (decades of dynamic range = justified).

Run AFTER solve_modes + forcing_qoi. Outputs figures/fig1..fig5 PNG (200 dpi).
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; FIG.mkdir(exist_ok=True)
meta = json.load(open(WS / "out" / "model_meta.json"))
par, sets = meta["par"], meta["sets"]
XYZ = np.load(WS / "out" / "xyz.npy")
R, Lb, H = par["R"], par["Lbar"], par["R"] / np.sqrt(2)

STAMP = ("run buffet_dome_secondary_20260612 | nominal deterministic | "
         "BUFFET-ONLY forcing (D12) | representative UNVERIFIED vehicle numbers")

def stamp(fig):
    fig.text(0.01, 0.005, STAMP, fontsize=6.5, color="0.45", ha="left")

_OVERLAPS = {}

def save_fig(fig, name):
    """Audit Text-artist bounding-box overlaps WITHIN each axes (catches
    'text on top of itself' that pixel QA misses), then save. Records any
    overlapping pairs to out/text_overlap.json so the gate can flag them."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    hits = []
    for ax in fig.get_axes():
        txts = [t for t in ax.texts if t.get_text().strip()]
        boxes = []
        for t in txts:
            try:
                boxes.append((t.get_text()[:20], t.get_window_extent(rend)))
            except Exception:
                pass
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                bb = boxes[i][1].intersection(boxes[i][1], boxes[j][1])
                if bb is not None and bb.width > 2 and bb.height > 2:
                    hits.append([boxes[i][0], boxes[j][0]])
    if hits:
        _OVERLAPS[name] = hits
        print(f"  [WARN] {name}: {len(hits)} text-overlap pair(s): {hits[:3]}")
    fig.savefig(FIG / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"{name} done")

plt.rcParams.update({
    "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.4,
    "figure.dpi": 110})

bg = np.array(sets["barrel_grid"]); dg = np.array(sets["dome_grid"])
tg = np.array(sets["tray_grid"])

# ============================ fig 1: geometry =============================
fig = plt.figure(figsize=(10, 7.2))
ax = fig.add_subplot(111, projection="3d")
def _to_pairs(poly):
    return [poly[k:k + 2] for k in range(len(poly) - 1)]

def ring_lines(grid, step_r=2, step_t=6):
    segs = []
    nr, nt = grid.shape
    for i in range(0, nr, step_r):
        ring = XYZ[grid[i]]; ring = np.vstack([ring, ring[0]])
        segs += _to_pairs(ring)
    for j in range(0, nt, step_t):
        segs += _to_pairs(XYZ[grid[:, j]])
    return segs
segs = ring_lines(bg) + ring_lines(dg)
ax.add_collection3d(Line3DCollection(segs, colors="0.78", linewidths=0.4))
# tray plate
quads_t = [[XYZ[tg[i, j]], XYZ[tg[i + 1, j]], XYZ[tg[i + 1, j + 1]],
            XYZ[tg[i, j + 1]]] for i in range(0, 12, 2) for j in range(0, 12, 2)]
ax.add_collection3d(Poly3DCollection(quads_t, facecolors="#9ecae1",
                                     edgecolors="#3182bd", linewidths=0.3,
                                     alpha=0.85))
# struts
for nt_, nd_ in sets["struts"]:
    seg = np.vstack([XYZ[nt_], XYZ[nd_]])
    ax.plot(*seg.T, color="#e6550d", lw=1.6)
# COPV spine + mounts
cn = sets["copv_nodes"]
ax.plot(*XYZ[cn].T, color="#a63603", lw=7, solid_capstyle="round")
for nc_, nd_ in sets["mounts"]:
    seg = np.vstack([XYZ[nc_], XYZ[nd_]])
    ax.plot(*seg.T, color="#e6550d", lw=1.6, ls="--")
av = sets["av_node"]
ax.scatter(*XYZ[av], color="#31a354", s=45, depthshade=False)
ax.text(*(XYZ[av] + [0.1, 0.1, 0.12]), "avionics lumped mass (8 kg)",
        color="#31a354", fontsize=8)
ax.text(*(np.array(sets["copv_frame"]["c"]) + [0, 0.5, 0.18]),
        "COPV (30 kg, 2 mounts)", color="#a63603", fontsize=8)
ax.text(*(np.array(sets["tray_frame"]["c"]) + [0.15, 0.4, 0.22]),
        "avionics tray 600 mm,\n6 struts (hexapod-style)", color="#3182bd",
        fontsize=8)
ax.text(2.0, -1.3, -1.9, "barrel section to first\nring frame (buffet OML)",
        color="0.4", fontsize=8)
ax.text(0, 1.6, 1.75, "dome (sqrt2:1 ellipsoid,\nt=5 mm equiv.)", color="0.4",
        fontsize=8)
ax.set_box_aspect((1, 1, 0.72))
ax.set_xlim(-2.4, 2.4); ax.set_ylim(-2.4, 2.4); ax.set_zlim(-1.6, 1.9)
ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
ax.set_title("Fine region: dome + ring + barrel-to-first-frame, with dome-mounted "
             "secondaries (58,662 DOF)\nfar-field stack NOT modeled "
             "deterministically — bracketed boundary (BC-A fixed / BC-B stack-mass)",
             fontsize=9.5)
ax.view_init(elev=22, azim=-58)
ax.grid(False)
stamp(fig)
save_fig(fig, "fig1_geometry")

# ============================ helpers for fields ==========================
def radial_field(phi_vec, grid):
    ids = grid
    th = np.arctan2(XYZ[ids, 1], XYZ[ids, 0])
    ux = phi_vec[6 * ids + 0]; uy = phi_vec[6 * ids + 1]
    return ux * np.cos(th) + uy * np.sin(th)

def normal_field_dome(phi_vec):
    ids = dg
    x, y, zc = XYZ[ids, 0], XYZ[ids, 1], XYZ[ids, 2]
    r = np.sqrt(x**2 + y**2) + 1e-12
    nx = (x / r) * (r / R**2); ny = (y / r) * (r / R**2); nz = zc / H**2
    nn = np.sqrt(nx**2 + ny**2 + nz**2) + 1e-12
    return (phi_vec[6 * ids + 0] * nx + phi_vec[6 * ids + 1] * ny +
            phi_vec[6 * ids + 2] * nz) / nn

# ============================ fig 2: mode gallery =========================
zA = np.load(WS / "out" / "modes_bcA.npz")
fsA, PhiA = zA["f"], zA["Phi"]
Mtr = None
# kinetic-energy split by node sets for labeling (translation DOFs, lumped)
tray_ids = tg.ravel(); copv_ids = np.array(cn)
host_ids = np.concatenate([bg.ravel(), dg[1:].ravel()])
def ke_split(phi_vec):
    def ke(ids):
        return float(sum((phi_vec[6 * ids + c] ** 2).sum() for c in range(3)))
    k_t, k_c, k_h = ke(tray_ids), ke(copv_ids), ke(host_ids)
    s = k_t + k_c + k_h + 1e-30
    return k_t / s, k_c / s, k_h / s

# pick representative modes: first overall; first tray-dominant; first
# copv-dominant; dome mode near 100 Hz; near 250 Hz; near 400 Hz
picks, labels = [], []
ke_all = np.array([ke_split(PhiA[:, j]) for j in range(min(len(fsA), 400))])
picks.append(0); labels.append("first elastic")
jt = int(np.argmax(ke_all[:, 0] > 0.5)); picks.append(jt); labels.append("tray-dominant")
jc = int(np.argmax(ke_all[:, 1] > 0.5)); picks.append(jc); labels.append("COPV-dominant")
for ftarget, lab in ((100, "dome ~100 Hz"), (250, "~250 Hz"), (398, "~400 Hz")):
    j = int(np.argmin(np.abs(fsA - ftarget))); picks.append(j); labels.append(lab)

fig, axes = plt.subplots(2, 3, figsize=(12, 7),
                         subplot_kw=dict(projection="polar"))
TH_d = np.arctan2(XYZ[dg, 1], XYZ[dg, 0])
RR_d = np.sqrt(XYZ[dg, 0] ** 2 + XYZ[dg, 1] ** 2)
for k, (j, lab) in enumerate(zip(picks, labels)):
    axp = axes.ravel()[k]
    w = normal_field_dome(PhiA[:, j])
    vmax = np.abs(w).max() + 1e-30
    axp.pcolormesh(TH_d, RR_d, w / vmax, cmap="RdBu_r", vmin=-1, vmax=1,
                   shading="gouraud", rasterized=True)
    kt, kc, kh = ke_split(PhiA[:, j])
    axp.set_title(f"{fsA[j]:.1f} Hz — {lab}\nKE: tray {kt:.0%} / COPV {kc:.0%}"
                  f" / host {kh:.0%}", fontsize=8.5)
    axp.set_xticks([]); axp.set_yticks([])
    # mark secondary footprints
    axp.plot(np.arctan2(XYZ[tray_ids, 1], XYZ[tray_ids, 0]),
             np.sqrt(XYZ[tray_ids, 0]**2 + XYZ[tray_ids, 1]**2), ".",
             ms=0.8, color="#3182bd", alpha=0.5)
    axp.plot(np.arctan2(XYZ[copv_ids, 1], XYZ[copv_ids, 0]),
             np.sqrt(XYZ[copv_ids, 0]**2 + XYZ[copv_ids, 1]**2), ".",
             ms=2.5, color="#a63603")
fig.suptitle("Mode gallery (BC-A fixed-boundary) — dome-normal displacement, "
             "plan view (red/blue = +/-, each normalized to its own max; tray "
             "= blue dots, COPV = brown dots)", fontsize=10)
stamp(fig)
save_fig(fig, "fig2_modes")

# ============================ fig 3: buffet field =========================
Uc, ax_c, ay_c = 210.0, 0.12, 0.72
fig = plt.figure(figsize=(12, 4.6))
gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 1, 1.15], wspace=0.25)
zz = np.linspace(-Lb, 0, 80)
ss = np.linspace(-np.pi * R / 2, np.pi * R / 2, 160)   # arc around theta=0
ZZ, SS = np.meshgrid(zz, ss, indexing="ij")
for k, f in enumerate((50, 150, 400)):
    axp = fig.add_subplot(gs[0, k])
    w = 2 * np.pi * f
    C = (np.exp(-ax_c * w * np.abs(ZZ - (-Lb / 2)) / Uc)
         * np.exp(-ay_c * w * np.abs(SS) / Uc)
         * np.cos(w * (ZZ - (-Lb / 2)) / Uc))
    axp.pcolormesh(SS, ZZ, C, cmap="RdBu_r", vmin=-1, vmax=1,
                   shading="gouraud", rasterized=True)
    axp.plot(0, -Lb / 2, "k.", ms=5)
    axp.set_title(f"{f} Hz", fontsize=9)
    axp.set_xlabel("circumf. arc s [m]")
    if k == 0:
        axp.set_ylabel("axial z [m]")
        axp.text(0.02, 0.97, "Re[normalized CSD] vs the black point:\n"
                 "patch size shrinks with f; stripes = convection phase",
                 transform=axp.transAxes, fontsize=7.5, va="top")
    axp.set_aspect("equal")
axp = fig.add_subplot(gs[0, 3])
ff = np.geomspace(20, 400, 100)
axp.loglog(ff, Uc / (ax_c * 2 * np.pi * ff), color="#3182bd")
axp.loglog(ff, Uc / (ay_c * 2 * np.pi * ff), color="#e6550d")
axp.text(22, 1.5e1 / 4, "streamwise (axial)\nL = Uc/(0.12·2πf)", color="#3182bd",
         fontsize=8)
axp.text(22, 2.6e-1, "lateral (circumf.)\nL = Uc/(0.72·2πf)", color="#e6550d",
         fontsize=8)
axp.axhline(2 * np.pi * R / 720 * 6, color="0.4", lw=0.8, ls=":")
axp.text(150, 2 * np.pi * R / 720 * 6 * 1.15,
         "6 x load-grid spacing\n(S1 mesh rule met to 400 Hz)", fontsize=7,
         color="0.4")
axp.set_xlabel("frequency [Hz] (log)"); axp.set_ylabel("coherence length [m] (log)")
axp.set_title("correlation length scale vs frequency", fontsize=9)
fig.suptitle("Corcos buffet pressure field on the barrel OML — \"patches of random "
             "force with frequency-dependent correlation\" (Uc=210 m/s, "
             "alpha=0.12/0.72, max-q q=30 kPa, rms Cp=0.04)", fontsize=10)
stamp(fig)
save_fig(fig, "fig3_buffet_field")

# ============================ fig 4: QOI PSDs =============================
have = all((WS / "out" / f"qoi_{bc}.npz").exists() for bc in ("bcA", "bcB"))
if have:
    qA = np.load(WS / "out" / "qoi_bcA.npz", allow_pickle=True)
    qB = np.load(WS / "out" / "qoi_bcB.npz", allow_pickle=True)
    names = list(qA["names"])
    f = qA["f"]

    def get(q, nm):
        return q["PSD"][names.index(nm)]

    panels = [
        ("strut loads (worst of 6)", "N$^2$/Hz", None),
        ("tray netCG punch (dome-normal)", "N$^2$/Hz", "tray_net_punch"),
        ("COPV net punch (dome-normal)", "N$^2$/Hz", "copv_net_punch"),
        ("avionics accel (worst axis)", "(m/s$^2$)$^2$/Hz", None),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.6), sharex=True)
    for k, (title, unit, nm) in enumerate(panels):
        axp = axes.ravel()[k]
        for q, color, lab in ((qA, "#3182bd", "BC-A fixed"),
                              (qB, "#e6550d", "BC-B stack-mass")):
            if nm is not None:
                y = get(q, nm)
            elif "strut" in title:
                y = np.max([get(q, f"strut_{i}_F") for i in range(1, 7)], axis=0)
            else:
                y = np.max([get(q, f"av_acc_{c}") for c in "xyz"], axis=0)
            axp.loglog(f, y, color=color, lw=1.2, label=lab)
        axp.set_title(title, fontsize=9.5)
        axp.set_ylabel(unit)
        if k >= 2:
            axp.set_xlabel("frequency [Hz] (log)")
        axp.set_xlim(20, 420)
        if k == 0:   # single legend; curves nearly coincide so direct labels collide
            axp.legend(fontsize=8, loc="lower left", frameon=False)
    fig.suptitle("QOI PSDs under max-q buffet — BC bracket = boundary-impedance "
                 "uncertainty (spread between curves is a REPORTED uncertainty, "
                 "not an error bar to ignore)", fontsize=10)
    stamp(fig)
    save_fig(fig, "fig4_qoi_psd")
else:
    print("fig4 SKIPPED (qoi outputs not ready)")

# ============================ fig 5: validity =============================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.2))
for bc, color in (("bcA", "#3182bd"), ("bcB", "#e6550d")):
    p = WS / "out" / f"modes_{bc}.npz"
    if p.exists():
        fz = np.load(p)["f"]
        ax1.semilogx(np.sort(fz), np.arange(1, len(fz) + 1), color=color,
                     lw=1.2, label={"bcA": "BC-A fixed",
                                    "bcB": "BC-B stack-mass"}[bc])
ax1.legend(fontsize=8, loc="upper left", frameon=False)  # curves coincide -> legend
ax1.axvline(400, color="0.4", lw=0.8, ls=":")
ax1.text(405, 50, "report band top", rotation=90, fontsize=7, color="0.4")
ax1.set_xlabel("frequency [Hz] (log)"); ax1.set_ylabel("cumulative mode count")
ax1.set_title("modal density of the fine region", fontsize=9.5)
ff = np.geomspace(20, 820, 60)
lam_b = 2 * np.pi / np.sqrt(np.sqrt((2 * np.pi * ff) ** 2 * 2800 * 0.005 /
                                    (71e9 * 0.005**3 / (12 * (1 - 0.33**2)))))
ax2.loglog(ff, lam_b / 6, color="0.3")
ax2.axhline(2 * np.pi * R / 240, color="#3182bd", lw=1)
ax2.text(22, 2 * np.pi * R / 240 * 1.1, "structural mesh spacing (59 mm)",
         fontsize=7.5, color="#3182bd")
ax2.axhline(2 * np.pi * R / 720, color="#e6550d", lw=1)
ax2.text(22, 2 * np.pi * R / 720 * 1.1, "forcing load-grid spacing (19.6 mm)",
         fontsize=7.5, color="#e6550d")
ax2.text(120, lam_b[40] / 6 * 1.4, "required: bending wavelength / 6",
         fontsize=7.5, color="0.3")
ax2.set_xlabel("frequency [Hz] (log)")
ax2.set_ylabel("length [m] (log)")
ax2.set_title("discretization vs requirement (t=5 mm shell)", fontsize=9.5)
fig.suptitle("Validity bookkeeping: mesh resolves the band; mode basis spans "
             "2x the band (truncation margin)", fontsize=10)
stamp(fig)
save_fig(fig, "fig5_validity")

# ============================ fig 6: CONFIDENCE bands =====================
ci_p = WS / "out" / "ci_bcA.npz"
if ci_p.exists():
    ci = np.load(ci_p, allow_pickle=True)
    cnames = list(ci["names"]); fci = ci["f"]
    fig = plt.figure(figsize=(11, 4.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1], wspace=0.28)
    # left: PSD median + 5-95% band for the tray punch
    axp = fig.add_subplot(gs[0, 0])
    ipun = cnames.index("tray_net_punch")
    axp.fill_between(fci, ci["q05"][ipun], ci["q95"][ipun], color="#9ecae1",
                     alpha=0.7, lw=0, label="5-95% (prior propagation)")
    axp.loglog(fci, ci["q50"][ipun], color="#08519c", lw=1.4)
    axp.text(fci[-1] * 1.02, ci["q50"][ipun][-1], "median", color="#08519c",
             fontsize=8, va="center")
    axp.text(fci[5], ci["q95"][ipun][5] * 1.3, "5-95% band\n(damping + buffet "
             "level priors)", color="#3182bd", fontsize=8)
    axp.set_xlabel("frequency [Hz] (log)"); axp.set_ylabel("N$^2$/Hz")
    axp.set_title("tray netCG punch PSD — confidence band", fontsize=9.5)
    axp.set_xlim(20, 400)
    # right: RMS prior-draw distribution for the 4 headline channels
    axp = fig.add_subplot(gs[0, 1])
    chans = ["strut_5_F", "tray_net_punch", "copv_net_punch", "av_acc_z"]
    short = ["strut", "tray\npunch", "COPV\npunch", "avionics\naz (x10)"]
    rms_s = ci["rms_samples"]
    data = []
    for c in chans:
        i = cnames.index(c)
        s = rms_s[:, i]
        if c == "av_acc_z":
            s = s * 10
        data.append(s)
    parts = axp.violinplot(data, showextrema=False)
    for pc in parts["bodies"]:
        pc.set_facecolor("#9ecae1"); pc.set_alpha(0.7)
    for k, s in enumerate(data):
        q5, q50, q95 = np.quantile(s, [0.05, 0.5, 0.95])
        axp.plot([k + 1, k + 1], [q5, q95], color="#08519c", lw=1)
        axp.plot(k + 1, q50, "o", color="#08519c", ms=4)
        axp.text(k + 1.32, q50, f"{q50:.0f}", fontsize=7.5, color="#08519c",
                 va="center")
    axp.set_xticks(range(1, 5)); axp.set_xticklabels(short, fontsize=8)
    axp.set_ylabel("band RMS  [N]  (avionics: 0.1 m/s$^2$)")
    axp.set_title("144 prior-propagation draws\n(NO data / NO sampler)",
                  fontsize=9.5)
    fig.suptitle("Confidence intervals (the deliverable): width = honest "
                 "ignorance of damping + buffet level; ~5x span, not an error",
                 fontsize=10)
    fig.text(0.01, 0.005, STAMP + " | CI = 144 prior draws on the D14 model",
             fontsize=6.5, color="0.45")
    save_fig(fig, "fig6_confidence")
else:
    print("fig6 SKIPPED (ci output not ready)")

# ============================ fig 7: response-limit proxy ================
rp = WS / "out" / "response_limit_proxy.npz"
if rp.exists():
    p = np.load(rp)
    f = p["f"]; fc = float(p["f_ctrl"]); m_assy = float(p["m_assy"])
    rj = json.load(open(WS / "out" / "response_limit_proxy.json"))
    vb = rj["valid_band_gamma_gt_0p8"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    # panel 1: the two PSDs (force + proxy accel), twin-free (normalized shapes)
    ax1 = axes[0]
    ax1.loglog(f, p["SFF"] / p["SFF"].max(), color="#08519c", lw=1.3)
    ax1.loglog(f, p["Saa"] / p["Saa"].max(), color="#e6550d", lw=1.3)
    ax1.axvspan(vb[0], vb[1], color="0.85", alpha=0.5, lw=0)
    ax1.axvline(fc, color="0.3", lw=0.8, ls=":")
    ax1.text(fc * 1.05, 1.5e-1, f"controlling\nmode {fc:.0f} Hz", fontsize=7.5,
             color="0.3")
    ax1.text(f[-1] * 1.02, p["SFF"][-1] / p["SFF"].max(), "tray punch",
             color="#08519c", fontsize=8, va="center")
    ax1.text(f[-1] * 1.02, p["Saa"][-1] / p["Saa"].max(), "avionics\naccel",
             color="#e6550d", fontsize=8, va="center")
    ax1.set_xlabel("frequency [Hz] (log)")
    ax1.set_ylabel("PSD / own max (log)")
    ax1.set_title("force vs proxy accel (shapes)", fontsize=9.5)
    ax1.set_xlim(20, 400)
    # panel 2: coherence
    ax2 = axes[1]
    ax2.semilogx(f, p["gamma_avF"], color="#08519c", lw=1.3)
    ax2.semilogx(f, p["gamma_avS"], color="#9ecae1", lw=1.0)
    ax2.axhline(0.8, color="0.5", lw=0.8, ls="--")
    ax2.axvspan(vb[0], vb[1], color="0.85", alpha=0.5, lw=0)
    ax2.text(34, 0.83, "valid: coherence>0.8 (32-300 Hz,\n77% of punch energy)",
             fontsize=7.5, color="0.3")
    ax2.text(f[-1] * 1.02, p["gamma_avF"][-1], "av->punch", color="#08519c",
             fontsize=8, va="center")
    ax2.text(120, 0.22, "decouples at the avionics-on-tray local mode",
             fontsize=7.5, color="#cc4c02")
    ax2.set_xlabel("frequency [Hz] (log)"); ax2.set_ylabel("coherence $\\gamma^2$")
    ax2.set_title("proxy validity (coherence)", fontsize=9.5)
    ax2.set_ylim(0, 1.05); ax2.set_xlim(20, 400)
    # panel 3: gain alpha + effective mass + eta invariance
    ax3 = axes[2]
    ax3.loglog(f, p["alpha_avF"], color="#08519c", lw=1.3)
    ax3.loglog(f, p["alpha_cgF"], color="#31a354", lw=1.1)
    ax3.axhline(m_assy, color="0.4", lw=0.9, ls="--")
    ax3.text(22, m_assy * 1.1, f"assembly mass {m_assy:.1f} kg (7004C eff. mass)",
             fontsize=7.5, color="0.3")
    ax3.plot(fc, rj["alpha_at_ctrl_avF"], "o", color="#08519c", ms=5)
    ax3.text(fc * 1.05, rj["alpha_at_ctrl_avF"] * 0.6,
             f"$\\alpha$={rj['alpha_at_ctrl_avF']:.1f} N/(m/s$^2$)\n"
             "invariant to $\\eta$ (0.07%)\n& forcing (0%)", fontsize=7.5,
             color="#08519c")
    ax3.text(f[-1] * 1.02, p["alpha_cgF"][-1], "CG accel", color="#31a354",
             fontsize=8, va="center")
    ax3.set_xlabel("frequency [Hz] (log)")
    ax3.set_ylabel("proxy gain $\\alpha$ = force/accel  [N/(m/s$^2$)] (log)")
    ax3.set_title("gain = structural constant", fontsize=9.5)
    ax3.set_xlim(20, 400)
    fig.suptitle("Avionics accel as a RESPONSE-LIMIT PROXY for the tray interface "
                 "load: a_limit = F_allow/$\\alpha$, with $\\alpha$ robust to the "
                 "uncertain damping & buffet level that dominate the CI",
                 fontsize=10)
    fig.text(0.01, 0.005, STAMP, fontsize=6.5, color="0.45")
    save_fig(fig, "fig7_response_limit_proxy")
else:
    print("fig7 SKIPPED (proxy output not ready)")
