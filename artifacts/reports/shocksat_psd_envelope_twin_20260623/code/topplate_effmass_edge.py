#!/usr/bin/env python3
"""STEP 0b (Andrew approved): re-do the top-plate effective-mass decomposition for a REALISTIC mount footprint --
a rigid secondary bolted on a PERIMETER bolt-circle (foot circle ~20.8 in > 18 in plate -> it lands on the edge,
not the center) -- and compare to the center-point mount.

Physics: a rigid secondary under z drive couples to structural mode i through the NET z-motion its feet see ~
mean_feet phi_i(foot_z). Modes where the feet move in-phase (global whole-deck modes) ADD; modes where the feet
sit on a node ring (local drumhead modes, center antinode/edge node) CANCEL. So an edge/distributed mount should
shift the load path off the poorly-correlated ~230-254 Hz drumhead modes and onto the well-correlated global modes.

Also reports a STATIC-compliance weight (phi^2/omega^2) for a stiff (rigid-in-band) secondary, and the validity gate
(mount-weighted freq-err / MAC vs unweighted) for CENTER vs EDGE. z-translation only (net CG load, per the tray
study); rocking would re-include some drumhead coupling (caveat). NO NUTS.
Output: figures/topplate_effmass_edge.png + out/topplate_effmass_edge.json.
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
import shape_borrow_diag as SB

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; OUT.mkdir(exist_ok=True)
ZTOP = 57.74989
BAND = (45.0, 260.0)
BOLT_R_IN = 9.0                          # bolt-circle radius (plate edge); foot circle ~20.8 in dia
N_FEET = 8


def weighted_median(vals, w):
    w = np.asarray(w, float); vals = np.asarray(vals, float)
    if w.sum() <= 0:
        return float(np.median(vals))
    o = np.argsort(vals); vs = vals[o]; ws = w[o] / w.sum()
    return float(vs[np.searchsorted(np.cumsum(ws), 0.5)])


def gate(fmatch, mac, f_fem_k, weight_k):
    inb = (f_fem_k >= BAND[0]) & (f_fem_k <= BAND[1])
    wk = weight_k.copy(); wk[~inb] = 0.0
    return {"unweighted_median_freq_err_pct": round(float(np.median(fmatch[inb])), 2),
            "weighted_median_freq_err_pct": round(weighted_median(fmatch, wk), 2),
            "unweighted_median_mac": round(float(np.median(mac[inb])), 2),
            "weighted_median_mac": round(weighted_median(mac, wk), 2)}


def dominant_table(fmodes, frac, fem_k, f_meas_k, fmatch, mac, n90):
    order = np.argsort(frac)[::-1]
    cum = np.cumsum(frac[order]); n = int(np.searchsorted(cum, 0.90) + 1) if n90 is None else n90
    rows = []
    for k in order[:n]:
        j = np.where(fem_k == k)[0]
        m = len(j) > 0
        rows.append({"fem_mode": int(k), "freq_hz": round(float(fmodes[k]), 1),
                     "mount_weight_pct": round(float(frac[k] * 100), 1),
                     "meas_freq_hz": round(float(f_meas_k[j[0]]), 1) if m else None,
                     "freq_err_pct": round(float(fmatch[j[0]]), 1) if m else None,
                     "mac": round(float(mac[j[0]]), 2) if m else None})
    matched_frac = float(sum(frac[r["fem_mode"]] for r in rows if r["meas_freq_hz"] is not None))
    return rows, n, matched_frac / (float(frac[order[:n]].sum()) + 1e-30)


def run():
    R = rf.load_reduced()
    K1 = R.A_fix + R.A.sum(0); w2, Q = np.linalg.eigh(K1)
    fmodes = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)
    omega2 = (2 * np.pi * fmodes) ** 2

    # center mount (Step 0)
    crow, _, csnap = R.reduced_row((0.0, 0.0, ZTOP), "Z")
    phi_c = crow @ Q

    # edge / distributed bolt-circle feet
    feet, foot_info = [], []
    for a in np.linspace(0, 2 * np.pi, N_FEET, endpoint=False):
        xyz = (BOLT_R_IN * np.cos(a), BOLT_R_IN * np.sin(a), ZTOP)
        row, nn, snap = R.reduced_row(xyz, "Z")
        feet.append(row @ Q); foot_info.append({"xyz": [round(v, 1) for v in xyz], "snap_in": round(float(snap), 2)})
    feet = np.array(feet)                                  # (N_FEET, n_modes)
    phi_edge = feet.mean(axis=0)                           # net rigid-z participation over the bolt circle

    # MAC-match FEM modes to measured survey (reuse)
    D = SB.build_dofs(R); FemAll, pairs = SB.match_modes(D, Q)
    fem_k = np.array([p[1] for p in pairs]); meas_r = np.array([p[0] for p in pairs])
    mac = np.array([p[2] for p in pairs])
    f_fem_k = fmodes[fem_k]; f_meas_k = D["mfr"][meas_r]
    fmatch = 100.0 * np.abs(f_fem_k - f_meas_k) / f_meas_k

    inb = (fmodes >= BAND[0]) & (fmodes <= BAND[1])
    res = {}
    for name, phi in [("center", phi_c), ("edge_distributed", phi_edge)]:
        w = phi ** 2; w[~inb] = 0.0; frac = w / (w.sum() + 1e-300)
        rows, n90, matched = dominant_table(fmodes, frac, fem_k, f_meas_k, fmatch, mac, None)
        # static-compliance weight (stiff secondary): phi^2/omega^2
        ws = (phi ** 2) / omega2; ws[~inb] = 0.0; fracs = ws / (ws.sum() + 1e-300)
        rows_s, n90s, matched_s = dominant_table(fmodes, fracs, fem_k, f_meas_k, fmatch, mac, None)
        res[name] = {"n_modes_for_90pct": n90, "dominant_modes": rows,
                     "dominant_residue_matched_to_data_frac": round(matched, 3),
                     "validity_gate_resonant": gate(fmatch, mac, f_fem_k, (phi ** 2)[fem_k]),
                     "static_compliance_n_modes_for_90pct": n90s,
                     "static_compliance_dominant_modes": rows_s[:5],
                     "static_compliance_matched_frac": round(matched_s, 3),
                     "frac_resonant": frac, "frac_static": fracs}

    rec = {"deliverable": "STEP 0b: top-plate CENTER vs EDGE/distributed mount effective-mass decomposition",
           "bolt_circle_radius_in": BOLT_R_IN, "n_feet": N_FEET, "feet": foot_info, "center_snap_in": round(float(csnap), 2),
           "band_hz": list(BAND),
           "center": {k: v for k, v in res["center"].items() if not k.startswith("frac")},
           "edge_distributed": {k: v for k, v in res["edge_distributed"].items() if not k.startswith("frac")},
           "headline": "edge mount shifts load path onto global modes if its validity gate (weighted freq-err/MAC) "
                       "is BETTER than center and its dominant residue is more data-matched.",
           "note": "EXPLORATORY; YELLOW; z-translation/net-CG only (rocking would re-add some drumhead); no claim."}
    (OUT / "topplate_effmass_edge.json").write_text(json.dumps(rec, indent=2))

    # ---- figure: center vs edge mode-weight bars
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ax, name, title in [(axes[0], "center", "CENTER mount (Step 0)"),
                            (axes[1], "edge_distributed", f"EDGE / {N_FEET}-foot bolt circle (r={BOLT_R_IN}\")")]:
        frac = res[name]["frac_resonant"]; order = np.argsort(frac)[::-1][:10]
        cols, labs = [], []
        for k in order:
            j = np.where(fem_k == k)[0]
            if len(j):
                fe = fmatch[j[0]]
                cols.append("#2ca02c" if fe < 3 else ("#ff7f0e" if fe < 8 else "#d62728"))
                labs.append(f"{fmodes[k]:.0f}Hz\nΔf{fe:.0f}%\nMAC{mac[j[0]]:.2f}")
            else:
                cols.append("0.6"); labs.append(f"{fmodes[k]:.0f}Hz\n(no match)")
        ax.bar(np.arange(len(order)), frac[order] * 100, color=cols)
        ax.set_xticks(np.arange(len(order))); ax.set_xticklabels(labs, fontsize=6.2)
        g = res[name]["validity_gate_resonant"]
        ax.set_title(f"{title}\n{res[name]['n_modes_for_90pct']} modes=90%; "
                     f"{100*res[name]['dominant_residue_matched_to_data_frac']:.0f}% of load path measured\n"
                     f"freq-err wtd {g['weighted_median_freq_err_pct']}% (unwtd {g['unweighted_median_freq_err_pct']}%) ; "
                     f"MAC wtd {g['weighted_median_mac']}", fontsize=8.2)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("mount residue  (% of in-band)", fontsize=9)
    cap = ("Top-plate load path: CENTER (drumhead antinode) vs EDGE bolt-circle (realistic: foot circle > plate). "
           "Rigid secondary couples to net z-motion over its feet ~ mean phi(foot); global whole-deck modes ADD, "
           "local drumhead modes (feet on a node ring) CANCEL. green=freq match <3% (well predicted), orange<8%, "
           "red worse, grey=no measured match (above ~200 Hz survey ceiling). If EDGE bars go green/measured and its "
           "weighted freq-err drops, a realistically-mounted secondary rides the well-correlated modes. z-only; NO NUTS.")
    fig.text(0.01, -0.03, cap, fontsize=7.2, wrap=True, va="top")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    outp = WS / "figures" / "topplate_effmass_edge.png"
    fig.savefig(outp, dpi=150, bbox_inches="tight"); plt.close(fig)

    print(f"feet snap distances (in): {[f['snap_in'] for f in foot_info]}")
    for name in ("center", "edge_distributed"):
        r = res[name]; g = r["validity_gate_resonant"]
        print(f"\n=== {name} ===  {r['n_modes_for_90pct']} modes carry 90%; "
              f"{100*r['dominant_residue_matched_to_data_frac']:.0f}% of load path is MAC-matched to data")
        for row in r["dominant_modes"]:
            print(f"   {row['freq_hz']:>6} Hz  {row['mount_weight_pct']:>5}%  meas {row['meas_freq_hz']}  "
                  f"err {row['freq_err_pct']}%  MAC {row['mac']}")
        print(f"   validity gate freq-err: unwtd {g['unweighted_median_freq_err_pct']}%  -> wtd "
              f"{g['weighted_median_freq_err_pct']}%   | MAC unwtd {g['unweighted_median_mac']} -> wtd {g['weighted_median_mac']}")
        print(f"   stiff-secondary (static-compliance) 90% in {r['static_compliance_n_modes_for_90pct']} modes, "
              f"{100*r['static_compliance_matched_frac']:.0f}% measured")
    print(f"\nwrote {outp}")
    return rec


if __name__ == "__main__":
    run()
