"""Study C2 — real-panel UMS preparation (unblocked by Andrew's D19 answers).

Inputs (already extracted to out/): panel_fea_xy.npy [924,2], panel_fea_u3.npy [46,924]
plus H1.mat (25 pts x 3200 freqs MOBILITY (m/s)/N, impact at the TOP-RIGHT grid node).

Does:
  1. Assume the photo's 5x5 LDV grid spans the panel with a fractional margin (scanned over a
     few margins); generate candidate point ORDERINGS (8 rasters x 2 transposes).
  2. Measured operating shapes = H1 rows at the first K strong experimental peaks (light damping
     -> proportional to mode shapes for a single-reference impact test).
  3. FEA shapes interpolated to the candidate grid points; MAC(measured, FEA) per matched mode;
     pick the (margin, ordering) maximizing the mean diagonal MAC  ->  THE H1-row mapping.
  4. Save mapping + Ritz pieces for the future real-panel UMS run; figure figC4.
Honest note: this is geometry/identification prep, NOT a calibration.
"""
from __future__ import annotations
import json, os
import numpy as np
import scipy.io as sio
from scipy.signal import find_peaks
from scipy.interpolate import griddata
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "out"); FIG = os.path.join(ROOT, "figures")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
BASE = os.path.join(REPO, "Suspended panel modal testing", "LDV test results", "mat files")

xyF = np.load(os.path.join(OUT, "panel_fea_xy.npy"))      # [924,2]
U3 = np.load(os.path.join(OUT, "panel_fea_u3.npy"))       # [46,924]
H = sio.loadmat(os.path.join(BASE, "H1.mat"))["H1"]       # [25,3200] mobility
fr = sio.loadmat(os.path.join(BASE, "freq.mat"))["freq"].ravel()
FEA_F = json.load(open(os.path.join(OUT, "study_c_summary.json")))  # has matches list

# ---- measured operating shapes at strong peaks (8-60 Hz: clean coherence band) ----
band = (fr >= 8) & (fr <= 60)
mm = np.abs(H[:, band]).mean(0)
pk, _ = find_peaks(20 * np.log10(mm), distance=10, prominence=4)
fpk = fr[band][pk][:8]
shapes_meas = np.array([H[:, np.argmin(np.abs(fr - f))] for f in fpk])   # [K,25] complex

# matched FEA mode indices for those peaks (from study_c matches: (exp, fea, err))
matches = FEA_F["matches"]
import re
DAT = os.path.join(REPO, "Suspended panel modal testing", "FEA results", "Abaqus Files",
                   "CompPanel_SoftSupports.dat")
fea=[]
grab = False
for ln in open(DAT, encoding="latin-1", errors="ignore"):
    if "E I G E N V A L U E" in ln: grab = True; continue
    if grab:
        m = re.match(r"\s*(\d+)\*?\s+([-0-9.E+]+)\s+([0-9.E+]+)\s+([0-9.E+]+)", ln)
        if m: fea.append((int(m.group(1)), float(m.group(4))))
        if "***NOTE" in ln and fea: break
start = [i for i, (lab, _) in enumerate(fea) if lab == 1][-1]
fea_freqs_all = [f for _, f in fea[start:]]
fea_freqs_all = np.array(fea_freqs_all)                    # 46 entries incl. ~0 rigid
mode_idx = []
for f in fpk:
    pairs = [(abs(mf - f), j) for j, mf in enumerate(fea_freqs_all) if mf > 1.0]
    pairs.sort(); mode_idx.append(pairs[0][1])

# ---- candidate grids ----
x0, x1 = xyF[:, 0].min(), xyF[:, 0].max()
y0, y1 = xyF[:, 1].min(), xyF[:, 1].max()
def grid_pts(margin):
    gx = np.linspace(x0 + margin * (x1 - x0), x1 - margin * (x1 - x0), 5)
    gy = np.linspace(y0 + margin * (y1 - y0), y1 - margin * (y1 - y0), 5)
    return gx, gy
def orderings(gx, gy):
    """Return dict name -> [25,2] coordinates in H1-row order under that hypothesis.
    Photo: panel LANDSCAPE; long FEA axis = y. 'col' = photo-columns = FEA y direction."""
    X, Y = np.meshgrid(gx, gy, indexing="ij")              # X: 5 short-axis, Y: 5 long-axis
    out = {}
    P0 = np.stack([X, Y], -1)                              # [5,5,2]
    def serp(Q):                                           # serpentine: every other row reversed
        S = Q.copy()
        for r in range(1, 5, 2): S[r] = S[r, ::-1]
        return S
    for namex, flipx in (("", False), ("fx", True)):
        for namey, flipy in (("", False), ("fy", True)):
            Q = P0[::-1] if flipx else P0
            Q = Q[:, ::-1] if flipy else Q
            out[f"xmajor{namex}{namey}"] = Q.reshape(25, 2)
            out[f"ymajor{namex}{namey}"] = np.transpose(Q, (1, 0, 2)).reshape(25, 2)
            out[f"xserp{namex}{namey}"] = serp(Q).reshape(25, 2)
            out[f"yserp{namex}{namey}"] = serp(np.transpose(Q, (1, 0, 2))).reshape(25, 2)
    return out

def mac(a, b):
    num = np.abs(np.vdot(a, b)) ** 2
    return num / (np.vdot(a, a).real * np.vdot(b, b).real)

results = []
for margin in (0.05, 0.08, 0.12):
    gx, gy = grid_pts(margin)
    for name, pts in orderings(gx, gy).items():
        # FEA shapes at these points (linear interp; nearest fallback at edges)
        Phi = []
        for mi in mode_idx:
            v = griddata(xyF, U3[mi], pts, method="linear")
            vn = griddata(xyF, U3[mi], pts, method="nearest")
            v[np.isnan(v)] = vn[np.isnan(v)]
            Phi.append(v)
        Phi = np.array(Phi)                                 # [K,25]
        macs = [mac(shapes_meas[k], Phi[k]) for k in range(len(mode_idx))]
        results.append((float(np.mean(macs)), margin, name, [float(m) for m in macs]))
results.sort(reverse=True)
best = results[0]
mean_mac, margin_b, name_b, macs_b = best

# the drive (top-right in the PHOTO) under the best ordering: index of the point with
# max long-axis coord and max short-axis coord... identify by coordinates:
gx, gy = grid_pts(margin_b); pts_b = orderings(gx, gy)[name_b]
drive_row = int(np.argmax(pts_b[:, 0] + pts_b[:, 1]))      # corner with max x+y (one corner)
# drive-point check: the drive row should have the LARGEST mean |H1| trend? report only.

json.dump(dict(
    answers_D19=dict(quantity="mobility (m/s)/N", excitation="impact hammer, back, top-right node",
                     lowf="rigid-body modes"),
    panel_dims_m=[float(x1 - x0), float(y1 - y0)],
    n_fea_nodes=int(xyF.shape[0]), n_fea_modes=int(U3.shape[0]),
    peaks_used_hz=[float(f) for f in fpk],
    matched_fea_mode_idx=[int(i) for i in mode_idx],
    best=dict(mean_MAC=mean_mac, margin=margin_b, ordering=name_b, per_mode_MAC=macs_b),
    runner_up=dict(mean_MAC=results[1][0], ordering=results[1][2], margin=results[1][1]),
    third=dict(mean_MAC=results[2][0], ordering=results[2][2]),
    drive_row_hypothesis=drive_row,
    caveat="geometry/ID prep from an assumed uniform 5x5 grid (photo); NOT a calibration; "
           "exact LDV coordinates would supersede the margin scan"),
    open(os.path.join(OUT, "study_c2_mapping.json"), "w"), indent=2)
np.savez(os.path.join(OUT, "study_c2_ritz.npz"),
         pts=pts_b, ordering=name_b, margin=margin_b,
         fea_xy=xyF, fea_u3=U3, fea_freqs=fea_freqs_all, drive_row=drive_row)

# ---- figure ----
fig, axs = plt.subplots(1, 3, figsize=(13, 4), gridspec_kw={"width_ratios": [1.1, 1, 1.2]})
axs[0].scatter(xyF[:, 1], xyF[:, 0], s=2, color="#ddd", label="FEA nodes")
axs[0].scatter(pts_b[:, 1], pts_b[:, 0], s=40, color="#1f77b4", label="LDV 5×5 (best fit)")
axs[0].scatter([pts_b[drive_row, 1]], [pts_b[drive_row, 0]], s=120, marker="*", color="#d6a700",
               label="drive (top-right)")
axs[0].set_xlabel("panel long axis [m]"); axs[0].set_ylabel("short axis [m]")
axs[0].legend(frameon=False, fontsize=8); axs[0].set_title("Grid mapping (landscape like photo)")
names = [f"{r[2]}@{r[1]:.2f}" for r in results[:8]]
axs[1].barh(range(8), [r[0] for r in results[:8]], color=["#2a7d2a"] + ["#bbb"] * 7)
axs[1].set_yticks(range(8)); axs[1].set_yticklabels(names, fontsize=7)
axs[1].invert_yaxis(); axs[1].set_xlabel("mean diagonal MAC")
axs[1].set_title("Ordering hypotheses")
axs[2].bar(range(len(macs_b)), macs_b, color="#1f77b4")
axs[2].set_xticks(range(len(macs_b)))
axs[2].set_xticklabels([f"{f:.1f}" for f in fpk], fontsize=7, rotation=45)
axs[2].axhline(0.7, color="#888", ls="--", lw=1)
axs[2].set_xlabel("experimental peak [Hz]"); axs[2].set_ylabel("MAC")
axs[2].set_title(f"Best ordering: per-mode MAC (mean {mean_mac:.2f})")
fig.text(0.01, 0.005, "Study C2 · REAL panel + Abaqus U3 shapes · mapping from assumed uniform "
         "photo grid (margin scan) · prep for the real-panel UMS calibration, NOT a calibration",
         fontsize=7.5, color="#777")
fig.suptitle("Real-panel prep: H1-row ↔ grid mapping pinned by MAC against FEA shapes", fontsize=11)
plt.tight_layout()
fig.savefig(os.path.join(FIG, "figC4_grid_mapping.png")); plt.close(fig)
print(f"BEST: ordering={name_b} margin={margin_b} meanMAC={mean_mac:.3f} "
      f"(runner-up {results[1][0]:.3f}) drive_row={drive_row}")
print("per-mode MAC:", [round(m, 2) for m in macs_b])
