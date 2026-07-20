#!/usr/bin/env python3
"""diag_mf — the agent's amplitude compass (card §3), TRAIN-side only. Extends the study's diag_wide
pattern with three MODEL-FORM-POINTING diagnostics:

  1. per-region MAC/shape defect vs the 33 survey shapes  -> points at connectivity/geometry
  2. residual-vs-local-mesh-size correlation              -> points at mesh refinement
  3. peak-width (curvature) misfit at matched peaks       -> points at element formulation/damping

Card rule: diagnosis reads drives in their TRAIN role only; the model and theta are fold-independent,
so the per-drive residual FIELD is the same object in every fold where that drive trains. NO fold
dev score is computed here (scores only via the exact pipeline). NO reduced-basis TRIAGE SCORES:
proposals are chosen from these diagnostics, never from screening numbers.
"""
from __future__ import annotations
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                  # noqa: E402

F, SW, WFW, WP = C.F, C.SW, C.WFW, C.WP
BANDS = [("sub200", 45.0, 200.0), ("b200_500", 200.0, 500.0)]
TAU_WIN = 0.1641                                     # window apparent damping zeta_w = 1/(2 pi f tau)


def channel_regions(pkg, m):
    xyz = np.asarray(m["xyz"], float)
    tags = np.asarray(m["gfile"]).astype(str)
    chmap = F.channels_map()
    out = {}
    for d in pkg.sens_daq:
        pt, ax = chmap[d]
        j = int(np.argmin(np.linalg.norm(xyz - np.asarray(pt), axis=1)))
        out[d] = {"region": str(tags[j]).split("/")[-1], "axis": ax, "node": j}
    return out


def local_edge_len(m, node):
    """Median edge length of quads touching the node nearest a sensor (mesh-size proxy)."""
    g2i = F.g2i_of(m)
    xyz = np.asarray(m["xyz"], float)
    gid = int(np.asarray(m["gids"])[node])
    q = np.asarray(m["cquad4"])
    hit = (q[:, 2:6] == gid).any(axis=1)
    if not hit.any():
        return None
    Ls = []
    for row in q[hit][:, 2:6]:
        idx = [g2i[int(g)] for g in row]
        for a in range(4):
            Ls.append(np.linalg.norm(xyz[idx[a]] - xyz[idx[(a + 1) % 4]]))
    return float(np.median(Ls))


def region_shape_defect(pkg, theta):
    """Per-region fraction of survey-shape residual energy (optimally scaled), over pairs MAC>=0.3.
    Region = gfile tag of the nearest STRUCTURAL node (ash nodes themselves all carry the
    instrumentation tag, which carries no model-form information)."""
    m = F.load_model()
    obs_dofs = np.load(os.path.join(F.MATD, "obs_dofs.npy"))
    tags = np.asarray(m["gfile"]).astype(str)
    short = np.array([t.split("/")[-1] for t in tags])
    xyz = np.asarray(m["xyz"], float)
    structural = short != "Modal_Test_Instrumentation"
    sidx = np.where(structural)[0]
    reg_of_dof = []
    for d in obs_dofs:
        node = d // 6
        j = sidx[int(np.argmin(np.linalg.norm(xyz[sidx] - xyz[node], axis=1)))]
        reg_of_dof.append(str(short[j]))
    reg_of_dof = np.array(reg_of_dof)
    mm = np.load(os.path.join(F.REMESH, "measured_modes.npz"), allow_pickle=True)
    live = np.asarray(mm["measured"]).reshape(-1)
    msh = np.asarray(mm["shapes"], float).reshape(33, -1)
    f_el, Q = pkg.modes(theta)
    phi = np.asarray(pkg.ash_rows) @ Q                 # (228, r)
    agg = {}
    n_pairs = 0
    for r, k, mc in np.asarray(pkg.pairs):
        if mc < 0.3:
            continue
        n_pairs += 1
        mvec = np.zeros(len(obs_dofs))
        mvec[live] = msh[int(r)][live]
        fvec = phi[:, int(k)]
        a = float(mvec @ fvec) / float(fvec @ fvec)
        res = (mvec - a * fvec) ** 2
        tot = res.sum() + 1e-300
        for reg in np.unique(reg_of_dof):
            agg.setdefault(reg, []).append(float(res[reg_of_dof == reg].sum() / tot))
    return {reg: round(float(np.mean(v)), 4) for reg, v in
            sorted(agg.items(), key=lambda kv: -np.mean(kv[1]))}, n_pairs


def peak_curvature_misfit(pkg, theta, caches):
    """Median (model peak curvature / measured peak curvature) per band at matched survey peaks.
    Both curves on the SAME 2.03 Hz bins (fair even where widths are barely resolved).
    Ratio > 1: model peaks SHARPER than data (underdamped/too-stiff formulation direction)."""
    mfreqs = np.asarray(pkg.mfreqs, float)
    pairs = [(int(r), int(k), float(mc)) for r, k, mc in np.asarray(pkg.pairs) if mc >= 0.5]
    out = {b[0]: [] for b in BANDS}
    for dkey in C.DEV_KEYS:
        c = caches[dkey]
        fc = c["freqs"]
        logHp = np.log10(np.abs(WFW.predict_H(pkg, theta, dkey, fc, windowed=True)) + 1e-300)
        ym = np.log10(np.abs(c["H1"]) + 1e-300)
        rows, cols = SW._usable(pkg, c, c["band"])
        for r, k, mc in pairs:
            ft = mfreqs[r]
            j0 = int(np.argmin(np.abs(fc - ft)))
            if j0 < 3 or j0 > len(fc) - 4:
                continue
            band = next((b for b, lo, hi in BANDS if lo <= ft < hi), None)
            if band is None:
                continue
            # channel with the largest measured peak near ft
            best_ci, best_amp = None, -1e9
            for rr, ci in zip(rows, cols):
                amp = float(ym[ci][j0 - 1:j0 + 2].max())
                if amp > best_amp:
                    best_amp, best_ci, best_r = amp, ci, rr
            if best_ci is None:
                continue
            for curve, sink in ((logHp[best_r], "model"), (ym[best_ci], "meas")):
                jj = j0 - 1 + int(np.argmax(curve[j0 - 1:j0 + 2]))
                if jj < 1 or jj > len(fc) - 2:
                    curv = None
                else:
                    curv = float(-(curve[jj - 1] - 2 * curve[jj] + curve[jj + 1]))
                if sink == "model":
                    cm_model = curv
                else:
                    cm_meas = curv
            if cm_model and cm_meas and cm_meas > 1e-6 and cm_model > 1e-6:
                out[band].append(cm_model / cm_meas)
    return {b: {"median_curv_ratio_model_over_meas": round(float(np.median(v)), 3),
                "n": len(v)} if v else None for b, v in out.items()}


def build(rnd, cid, theta_source):
    t0 = time.time()
    caches = SW.load_caches()
    pkg = WP.load(cid)
    if theta_source == "ones":
        theta = np.ones(len(pkg.free_names))
    else:
        theta = np.asarray(json.load(open(theta_source))["theta_map_vec"], float)
    m = F.load_model()
    reg_of = channel_regions(pkg, m)
    table = {}
    chan_stats = {}
    for dkey in C.DEV_KEYS:
        c = caches[dkey]
        fc = c["freqs"]
        logHp = np.log10(np.abs(WFW.predict_H(pkg, theta, dkey, fc, windowed=True)) + 1e-300)
        rows, cols = SW._usable(pkg, c, c["band"])
        ym_all = np.log10(np.abs(c["H1"]) + 1e-300)
        off = float(np.mean(ym_all[cols][:, c["band"]] - logHp[rows][:, c["band"]]))
        for r, ci in zip(rows, cols):
            d = c["daq"][ci]
            reg, ax = reg_of[d]["region"], reg_of[d]["axis"]
            for bn, lo, hi in BANDS:
                bm = (fc >= lo) & (fc < min(hi, c["top"])) & c["band"]
                if bm.sum() < 8:
                    continue
                resid = ym_all[ci][bm] - logHp[r][bm] - off
                corr = float(np.corrcoef(logHp[r][bm], ym_all[ci][bm])[0, 1])
                key = f"{reg}|{ax}|{bn}"
                t = table.setdefault(key, {"n": 0, "sum_abs": 0.0, "corrs": []})
                t["n"] += 1
                t["sum_abs"] += float(np.mean(np.abs(resid)))
                t["corrs"].append(corr)
                cs = chan_stats.setdefault(d, {"resid": [], "node": reg_of[d]["node"]})
                if bn == "sub200":
                    cs["resid"].append(float(np.mean(np.abs(resid))))
    summary = {k: {"n_ch_drive": v["n"], "mean_abs_resid_dex": round(v["sum_abs"] / v["n"], 3),
                   "median_corr": round(float(np.median(v["corrs"])), 3)}
               for k, v in sorted(table.items(), key=lambda kv: -kv[1]["sum_abs"] / kv[1]["n"])}
    # residual vs mesh size (sub-200)
    sizes, resids = [], []
    for d, cs in chan_stats.items():
        L = local_edge_len(m, cs["node"])
        if L and cs["resid"]:
            sizes.append(L)
            resids.append(float(np.mean(cs["resid"])))
    mesh_corr = float(np.corrcoef(sizes, resids)[0, 1]) if len(sizes) > 5 else None
    defect, n_pairs = region_shape_defect(pkg, theta)
    curv = peak_curvature_misfit(pkg, theta, caches)
    f_el, _ = pkg.modes(theta)
    peak_df = [{"f_test": round(float(pkg.mfreqs[int(r)]), 1), "f_model": round(float(f_el[int(k)]), 1),
                "df_pct": round(100 * (f_el[int(k)] / pkg.mfreqs[int(r)] - 1), 2),
                "mac": round(float(mc), 3)}
               for r, k, mc in np.asarray(pkg.pairs) if mc >= 0.3]
    out = {"round": rnd, "model": cid, "theta_source": str(theta_source),
           "region_axis_band_residuals": summary,
           "region_shape_defect_fraction": defect, "n_shape_pairs": n_pairs,
           "residual_vs_mesh_size_corr_sub200": mesh_corr,
           "n_mesh_channels": len(sizes),
           "peak_width_curvature": curv,
           "survey_peak_df": peak_df,
           "note": "TRAIN-side residual fields only; no fold dev scores computed here; "
                   "proposals link to these diagnostics (round summaries)"}
    p = os.path.join(C.MY_OUT, f"diagnosis_mf_r{rnd}.json")
    json.dump(out, open(p, "w"), indent=1)
    C.log_step(f"diag_r{rnd}", time.time() - t0, model=cid)
    C.flush_vault_guard(f"diag_r{rnd}")
    print(f"diagnosis r{rnd} on {cid}: {len(summary)} cells, mesh-corr {mesh_corr}, "
          f"shape-defect top {list(defect)[:3]}")
    return out


if __name__ == "__main__":
    rnd = int(sys.argv[1])
    cid = sys.argv[2] if len(sys.argv) > 2 else "A0_wide"
    src = sys.argv[3] if len(sys.argv) > 3 else \
        os.path.join(C.STUDY, "out", "theta_map_wide.json")
    build(rnd, cid, src)
