"""Study G GIF frames: sequential data accretion (LDV-scan order) + bandwidth extension.
Each frame = a reduced NUTS run (2 chains x 300+300, R-hat RECORDED AND SHOWN per frame;
the headline run uses 4 chains with full gates). Resumable: skips existing frame files.
Run AFTER run_ums.py (uses the same module-level data).  Outputs -> ../out/frames/
"""
from __future__ import annotations
import json, os
import numpy as np
import jax.numpy as jnp
import run_ums as R

OUTF = os.path.join(os.path.dirname(__file__), "..", "out", "frames")
os.makedirs(OUTF, exist_ok=True)

# raster order of observed points (drive first, then by (ix, iy)) — how an LDV scan accrues
def raster_key(n): return (n // R.U.NY, n % R.U.NY)
obs_sorted = [R.obs_nodes[0]] + sorted(R.obs_nodes[1:], key=raster_key)
SCAN_SIZES = [2, 4, 6, 9, 12, 15]
BAND_MAXES = [25.0, 35.0, 45.0, 60.0]

def frame_run(tag, sub_nodes, fmax):
    path = os.path.join(OUTF, f"{tag}.npz")
    if os.path.exists(path):
        print("skip existing", tag); return
    fmask = R.F_INF <= fmax + 1e-9
    freqs = R.F_INF[fmask]
    cols20 = [R.scan.index(n) for n in sub_nodes]                 # local 20-index
    data = R.data_inf_all[fmask][:, cols20]
    coords = R.xy[sub_nodes]
    res, fl = R.run_nuts(False, 700, 250, 2, tag,
                         data=jnp.array(data), freqs=jnp.array(freqs),
                         obs_local=jnp.array(cols20), coords=coords)
    rng = np.random.default_rng(11)
    obs_cols_for_pred = cols20                                    # already 20-indices
    P = R.predictive(fl, False, 120, rng, obs_cols=obs_cols_for_pred,
                     obs_freqs=freqs, data_obs=data)
    lo, mdn, hi = np.percentile(P["show"], [2.5, 50, 97.5], 0)
    qA = np.percentile(P["qoiA"], [2.5, 50, 97.5], 0)
    qB = np.percentile(P["qoiB"], [2.5, 50, 97.5], 0)
    np.savez(path, lo=lo, med=mdn, hi=hi, qA=qA, qB=qB,
             max_rhat=res["max_rhat"], divergences=res["divergences"],
             n_pts=len(sub_nodes), fmax=fmax, runtime_s=res["runtime_s"],
             sub_nodes=sub_nodes)
    print("frame", tag, "rhat %.2f div %d runtime %.0fs" %
          (res["max_rhat"], res["divergences"], res["runtime_s"]))

if __name__ == "__main__":
    for k in SCAN_SIZES:
        frame_run(f"scan_{k:02d}", obs_sorted[:k], R.BAND[1])
    for fm in BAND_MAXES:
        frame_run(f"band_{int(fm):03d}", obs_sorted, fm)
    print("all frames done ->", OUTF)
