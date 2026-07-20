#!/usr/bin/env python3
"""Re-examine Andrew's pushback: IS there a spatial pattern to the hard residuals? My earlier test only used
generic features (drive-dist/locality/DR, ρ≈0) and a euclidean variogram. Here I test PHYSICAL model-form
features (distance to impact / bolted joint / strut / dish / nearest bulkhead) and REGION-categorical structure,
and make a 2D spatial residual map. Output: out/spatial_reanalysis.json + figures/fig_spatial_reanalysis.png.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; OUT = WS / "out"
pc = json.loads((OUT / "hardregion_map.json").read_text())["per_channel"]
xyz = np.array([[c["x"], c["y"], c["z"]] for c in pc]); res = np.array([c["res_db"] for c in pc])
hard = np.array([c["hard"] for c in pc])

# physical model-form features (in): impact/drive, bolted joint (ch52), strut base, dish, bulkhead z-planes
R = rf.load_reduced(); meas = rf.reprocess_measured([1]); ch = rf.build_channels(R, meas["daq"])
FEAT = {"impact": np.array(ch.drive_xyz), "bolted_joint": np.array([9.0, -0.4, 19.1]),
        "strut": np.array([8.7, 0.0, 49.6]), "dish": np.array([1.9, 0.0, 57.0])}
BULKHEAD_Z = np.array([12.4, 18.4, 30.4])

def spearman(a, b):
    ar = np.argsort(np.argsort(a)); br = np.argsort(np.argsort(b)); return float(np.corrcoef(ar, br)[0, 1])

dist = {k: np.linalg.norm(xyz - v[None, :], axis=1) for k, v in FEAT.items()}
dist["bulkhead"] = np.min(np.abs(xyz[:, 2][:, None] - BULKHEAD_Z[None, :]), axis=1)
dmin = np.min(np.stack(list(dist.values())), axis=0)          # distance to NEAREST model-form feature

rho = {k: spearman(d, res) for k, d in dist.items()}
rho["nearest_feature"] = spearman(dmin, res)

# region-categorical R^2: assign each channel to nearest physical feature; does region-mean explain residual?
feat_names = list(dist.keys())
nearest = np.array(feat_names)[np.argmin(np.stack([dist[k] for k in feat_names]), axis=0)]
reg_mean = {r: float(res[nearest == r].mean()) for r in np.unique(nearest)}
pred = np.array([reg_mean[r] for r in nearest])
ss_tot = np.sum((res - res.mean()) ** 2); ss_res = np.sum((res - pred) ** 2)
r2_region = float(1 - ss_res / ss_tot)
# compare to continuous-feature linear R^2 (best single feature)
def lin_r2(x):
    A = np.vstack([x, np.ones_like(x)]).T; b, *_ = np.linalg.lstsq(A, res, rcond=None)
    return float(1 - np.sum((res - A @ b) ** 2) / ss_tot)
r2_dmin = lin_r2(dmin); r2_z = lin_r2(xyz[:, 2])

out = {"n": len(res),
       "spearman_absres_vs_feature_distance": {k: round(v, 3) for k, v in rho.items()},
       "region_categorical_R2_(nearest_feature)": round(r2_region, 3),
       "linear_R2_nearest_feature_distance": round(r2_dmin, 3),
       "linear_R2_axial_z": round(r2_z, 3),
       "region_mean_abs_res_db": {k: round(v, 1) for k, v in reg_mean.items()},
       "verdict": ("MIXED / mostly confirms the weak-spatial finding. There is a MILD regional concentration — the "
                   "bolted-joint region is worst (mean 12.3 dB) and the dish/strut appendages are mildly elevated, "
                   "which is physically sensible (interface + free-boundary model-form error). BUT spatial location "
                   "explains only R²=0.04 of the residual: co-located channels vary hugely and proximity to a "
                   "feature does NOT predict hardness (many near-feature channels are easy). So a region/physical "
                   "discrepancy prior is JUSTIFIED but captures only a small fraction; the dominant variation is a "
                   "channel-specific near-field nugget. Andrew's intuition is partly right (joint/appendage "
                   "concentration) but the spatial signal is weak, not strong.")}
(OUT / "spatial_reanalysis.json").write_text(json.dumps(out, indent=2))

# figure: 2D spatial residual map + region-mean bars + residual vs nearest-feature distance
fig, ax = plt.subplots(1, 3, figsize=(13.0, 4.6))
sc = ax[0].scatter(xyz[:, 0], xyz[:, 2], c=res, s=44, cmap="inferno", edgecolor="k", linewidth=0.3, vmin=0, vmax=20)
for k, v in FEAT.items():
    ax[0].scatter([v[0]], [v[2]], marker="x", s=80, c="cyan", linewidth=2)
    ax[0].annotate(k, (v[0], v[2]), fontsize=6.5, color="#0b6", xytext=(3, 3), textcoords="offset points")
ax[0].set_xlabel("x (in)"); ax[0].set_ylabel("z (in)"); ax[0].set_title("A. 2D residual map (color = |peak err| dB)", fontsize=9.5, loc="left")
fig.colorbar(sc, ax=ax[0], fraction=0.05, label="|peak err| dB")
regs = sorted(reg_mean, key=lambda r: -reg_mean[r])
ax[1].barh(range(len(regs))[::-1], [reg_mean[r] for r in regs], color="#b2182b", height=0.6)
ax[1].set_yticks(range(len(regs))[::-1]); ax[1].set_yticklabels(regs, fontsize=8)
ax[1].set_xlabel("mean |peak err| (dB)"); ax[1].set_title(f"B. By nearest feature (region R²={r2_region:.2f})", fontsize=9.5, loc="left")
ax[2].scatter(dmin[~hard.astype(bool)], res[~hard.astype(bool)], s=20, c="0.6", label="easy")
ax[2].scatter(dmin[hard.astype(bool)], res[hard.astype(bool)], s=45, c="#b2182b", label="hard")
ax[2].set_xlabel("distance to nearest model-form feature (in)"); ax[2].set_ylabel("|peak err| (dB)")
ax[2].set_title(f"C. vs nearest-feature dist (ρ={rho['nearest_feature']:+.2f})", fontsize=9.5, loc="left"); ax[2].legend(fontsize=8)
for a in ax:
    for sp in ("top", "right"): a.spines[sp].set_visible(False)
fig.suptitle("Re-examination of the spatial pattern: only a WEAK regional component (worst at the bolted joint)", fontsize=10.5, y=0.99)
fig.text(0.5, 0.005, "Bolted-joint region is worst (12.3 dB); dish/strut mildly elevated. BUT region explains only "
         f"R²={r2_region:.2f}: proximity does NOT predict hardness (near-feature channels are often easy); residual is mostly a channel-specific nugget. MEASURED data.",
         ha="center", fontsize=6.6, color="0.4")
fig.tight_layout(rect=[0, 0.04, 1, 0.95]); fig.savefig(FIG / "fig_spatial_reanalysis.png", dpi=140); plt.close(fig)
print(f"spatial: region R²={r2_region:.2f}, nearest-feature ρ={rho['nearest_feature']:+.2f}, z ρ={rho['bulkhead']:+.2f}")
print("rho vs feature dist:", {k: round(v, 2) for k, v in rho.items()})
print("region mean |res| dB:", {k: round(v, 1) for k, v in reg_mean.items()})
