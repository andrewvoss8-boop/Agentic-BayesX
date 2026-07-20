#!/usr/bin/env python3
"""TRAIN-side diagnosis (card §6 step 1). Reads residual FIELDS on the 4 loop drives (never the vault) at
the drive-independent θ_MAP — the D6-recorded reading of "train-side fields" under leave-one-drive-out.
Dev SCORES are produced only by score.py; this module never computes or exposes fold dev scalars.

Outputs out/diagnosis_r{r}.json with:
  - pairing table (matched f_test/f_model/df%/MAC, unmatched .ash modes = shape defects),
  - region MAC (MAC restricted to .ash nodes per structural region),
  - per-(region, axis) channel residual summaries on each loop drive (corr, mean |resid| dB, worst channels),
  - band-resolved mean residual profiles per region,
  - modal strain-energy fractions per θ group (identifiability gate quantity),
  - peak misalignment list.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femlib as F
import score as SC

WS = F.WS


def node_regions(m):
    return np.asarray(m["gfile"]).astype(str)


def ash_regions(m):
    """STRUCTURAL region tag for each of the 76 .ash nodes. The survey nodes are the accelerometer
    (Modal_Test_Instrumentation) grids; the structural region is the bush-99 partner grid's file tag."""
    coords = np.load(os.path.join(F.REMESH, "inherited_baseline", "ash_node_coords.npy"))
    xyz = np.asarray(m["xyz"], float)
    tags = node_regions(m)
    g2i = F.g2i_of(m)
    # instrumentation grid -> structural partner via CBUSH pid 99
    partner = {}
    for eid, pid, ga, gb, cid in np.asarray(m["cbush"]):
        if pid != 99:
            continue
        ta, tb = tags[g2i[int(ga)]], tags[g2i[int(gb)]]
        if ta == "Modal_Test_Instrumentation":
            partner[int(ga)] = tb
        if tb == "Modal_Test_Instrumentation":
            partner[int(gb)] = ta
    out = []
    for c in coords:
        order = np.argsort(np.linalg.norm(xyz - c, axis=1))[:8]
        tag = None
        for nn in order:                                  # nearest instrumentation grid -> its partner
            g = int(np.asarray(m["gids"])[nn])
            if g in partner:
                tag = partner[g]
                break
            if tags[nn] != "Modal_Test_Instrumentation":  # or directly a structure node
                tag = str(tags[nn])
                break
        out.append(tag or "unknown")
    return out, coords


def build_diagnosis(cid, r):
    pkg = F.Package.load(cid)
    theta = SC.theta_map_cached(pkg)
    m = F.load_model()
    mm = np.load(os.path.join(F.REMESH, "measured_modes.npz"), allow_pickle=True)
    live = np.asarray(mm["measured"]).reshape(-1)
    mfreqs = np.asarray(mm["freqs"], float)
    msh = np.asarray(mm["shapes"], float).reshape(33, -1)[:, live]
    f_el, Q = pkg.modes(theta)
    ash_now = np.asarray(pkg.ash_rows) @ Q                    # shapes at θ_MAP on the 228 ash DOFs
    aregs, acoords = ash_regions(m)
    regions = sorted(set(aregs))
    live228 = live                                             # (228,) bool
    reg_of_dof = np.repeat(aregs, 3)                           # 76 nodes x3 -> 228
    # pairing table at θ_MAP frequencies (pairs FROZEN from build; df recomputed at θ_MAP)
    pairs = np.asarray(pkg.pairs)
    table, region_mac = [], {g: [] for g in regions}
    matched_rows = set()
    for rr, k, mac0 in pairs:
        rr, k = int(rr), int(k)
        matched_rows.add(rr)
        df = float(f_el[k] / mfreqs[rr] - 1.0)
        pm = ash_now[live228, k]
        tm = msh[rr]
        entry = {"test_mode": rr + 1, "f_test": float(mfreqs[rr]), "f_model": float(f_el[k]),
                 "df_pct": round(100 * df, 2), "mac_global": None, "mac_by_region": {}}
        num = float(np.dot(tm, pm)) ** 2
        den = float(np.dot(tm, tm)) * float(np.dot(pm, pm))
        entry["mac_global"] = round(num / (den + 1e-300), 3)
        rdofs_all = reg_of_dof[live228]
        for g in regions:
            s = rdofs_all == g
            if s.sum() < 6:
                continue
            nu = float(np.dot(tm[s], pm[s])) ** 2
            de = float(np.dot(tm[s], tm[s])) * float(np.dot(pm[s], pm[s]))
            mg = nu / (de + 1e-300)
            entry["mac_by_region"][g] = round(mg, 3)
            region_mac[g].append(mg)
        table.append(entry)
    unmatched = [{"test_mode": i + 1, "f_test": float(mfreqs[i])}
                 for i in range(len(mfreqs)) if i not in matched_rows]
    # strain-energy fractions per group for matched modes (identifiability)
    lam = (2 * np.pi * f_el) ** 2
    A = np.asarray(pkg.A)
    se = {}
    for j, g in enumerate(pkg.free_names):
        se[g] = {}
        for rr, k, _ in pairs:
            k = int(k)
            se[g][f"m{int(rr)+1}"] = round(float(theta[j] * Q[:, k] @ A[j] @ Q[:, k] / lam[k]), 4)
    # channel residual fields on the 4 loop drives
    caches = SC.load_caches()
    chmap = F.channels_map()
    xyz = np.asarray(m["xyz"], float)
    tags = node_regions(m)
    drives = {}
    for key in F.DRIVE_KEYS:
        c = caches[key]
        logH = F.predict_logH(pkg, theta, key, c["freqs"])
        rows_of = {d: i for i, d in enumerate(pkg.sens_daq)}
        offs, chans = [], []
        for i, d in enumerate(c["daq"]):
            if d not in rows_of or d not in chmap:
                continue
            if float(np.median(c["coh"][i][c["band"]])) < SC.COH_MIN:
                continue
            ym = np.log10(np.abs(c["H1"][i][c["band"]]) + 1e-300)
            yp = logH[rows_of[d]][c["band"]]
            offs.append(float(np.mean(ym - yp)))
            pt, ax = chmap[d]
            reg = str(tags[int(np.argmin(np.linalg.norm(xyz - np.asarray(pt), axis=1)))])
            chans.append((d, reg, ax, ym, yp))
        gain = float(np.mean(offs))
        per_reg = {}
        prof = {}
        fcb = c["freqs"][c["band"]]
        for d, reg, ax, ym, yp in chans:
            corr = float(np.corrcoef(ym, yp)[0, 1])
            res = ym - yp - gain
            per_reg.setdefault(f"{reg}|{ax}", []).append(
                {"daq": d, "corr": round(corr, 3), "mean_abs_resid_dB": round(20 * float(np.mean(np.abs(res))), 2)})
            prof.setdefault(reg, []).append(res)
        drives[key] = {
            "gain_log10": round(gain, 3),
            "per_region_axis": {k: sorted(v, key=lambda x: x["corr"]) for k, v in per_reg.items()},
            "region_resid_profile_dB": {g: (20 * np.mean(np.stack(v), 0)).round(2).tolist()
                                        for g, v in prof.items()},
            "freqs": fcb.round(2).tolist(),
            "region_median_corr": {g: round(float(np.median([x["corr"] for kk, vv in per_reg.items()
                                                             if kk.startswith(g + "|") for x in vv])), 3)
                                   for g in sorted(set(rg for rg, *_ in [(re, ) for _, re, *_ in chans]))
                                   if any(kk.startswith(g + "|") for kk in per_reg)},
        }
    out = {"cid": cid, "round": r, "theta_map": {g: round(float(t), 4) for g, t in
                                                 zip(pkg.free_names, theta)},
           "pairing": table, "unmatched_ash_modes": unmatched,
           "region_mac_mean": {g: round(float(np.mean(v)), 3) for g, v in region_mac.items() if v},
           "strain_energy_frac": se, "drives": drives}
    p = os.path.join(WS, "out", f"diagnosis_r{r}.json")
    json.dump(out, open(p, "w"), indent=1)
    print(f"wrote {p}")
    return out


if __name__ == "__main__":
    build_diagnosis(sys.argv[1], int(sys.argv[2]))
