#!/usr/bin/env python3
"""STEP 0 (Andrew approved): modal effective-mass decomposition of the TOP-PLATE-CENTER apparent mass -- which FEM
modes actually carry the load path into a secondary mounted there, and are THOSE modes the ones we predict well?

Mount = top-plate-center node gid 7000072 (0,0,57.75 in), z (deck-normal), reused from the tray-coupled study.
Reduced FEM is mass-normalized (standard eigh) so phi_i(mount)^2 is the proper drive-point modal residue.

Convention (per the 7004C apparent-mass postmortem): we report DRIVE-POINT accelerance a/F (peaks at resonance =
where a rigid secondary F=m_s*a is driven hardest) and its reciprocal = local apparent mass (dips at resonance).
The 7004C source/load interface apparent mass + total-mass anchor is Step 1 (needs the interface partition). The
RANKING of modes by mount residue is convention-robust: a mode with tiny phi(mount) is tiny in EVERY apparent-mass
flavour AND in the top-plate acceleration -> the local node-line modes that wreck per-sensor FRFs are down-weighted.

Validity gate: is the MOUNT-WEIGHTED frequency-match / MAC BETTER than the unweighted -- i.e. does this QOI lean on
the modes the FEM gets right? NO NUTS. Output: figures/topplate_effmass_step0.png + out/topplate_effmass_step0.json.
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
import shape_borrow_diag as SB          # reuse build_dofs + MAC match (no numpyro)

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; OUT.mkdir(exist_ok=True)
MOUNT_XYZ = (0.0, 0.0, 57.74989); MOUNT_GID = 7000072
SHOCKSAT_MASS_KG = 57.961
BAND = (45.0, 260.0)
ZETA = 0.01                              # physical structural damping for the accelerance (swap measured ~0.45% later)


def drivepoint_accel(freqs_hz, fmodes_hz, phi_mount, zeta=ZETA):
    w = 2 * np.pi * np.asarray(freqs_hz)[:, None]
    wi = 2 * np.pi * np.asarray(fmodes_hz)[None, :]
    denom = wi ** 2 - w ** 2 + 2j * zeta * wi * w
    H = np.sum(-(w ** 2) * (phi_mount[None, :] ** 2) / denom, axis=1)   # a/F at the mount (drive point)
    return H


def run():
    R = rf.load_reduced()
    K1 = R.A_fix + R.A.sum(0)
    w2, Q = np.linalg.eigh(K1)
    fmodes = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)               # Hz
    mount_row, mnode, snap = R.reduced_row(MOUNT_XYZ, "Z")
    phi_mount = mount_row @ Q                                          # modal displacement at mount, z (mass-norm)
    weight = phi_mount ** 2                                            # drive-point modal residue

    in_band = (fmodes >= BAND[0]) & (fmodes <= BAND[1])
    wb = weight.copy(); wb[~in_band] = 0.0
    frac = wb / (wb.sum() + 1e-300)
    order = np.argsort(frac)[::-1]
    cum = np.cumsum(frac[order])
    n90 = int(np.searchsorted(cum, 0.90) + 1)
    dom = order[:n90]                                                  # modes carrying 90% of in-band mount residue

    # MAC-match FEM modes to the measured .ash survey (reuse), to validate the modes that matter
    D = SB.build_dofs(R)
    FemAll, pairs = SB.match_modes(D, Q)                               # pairs: (meas_r, fem_k, mac)
    mfr = D["mfr"]
    fem_k = np.array([p[1] for p in pairs]); meas_r = np.array([p[0] for p in pairs])
    mac = np.array([p[2] for p in pairs])
    f_fem_k = fmodes[fem_k]; f_meas_k = mfr[meas_r]
    fmatch = 100.0 * np.abs(f_fem_k - f_meas_k) / f_meas_k             # % frequency error per matched mode
    w_k = weight[fem_k]                                                # mount residue of each matched mode
    wk_band = w_k.copy(); wk_band[(f_fem_k < BAND[0]) | (f_fem_k > BAND[1])] = 0.0

    def wmed(vals, w):
        w = np.asarray(w, float)
        if w.sum() <= 0:
            return float(np.median(vals))
        o = np.argsort(vals); vs = np.asarray(vals)[o]; ws = w[o] / w.sum()
        return float(vs[np.searchsorted(np.cumsum(ws), 0.5)])

    # which dominant modes are matched/well-predicted
    dom_rows = []
    for k in dom:
        j = np.where(fem_k == k)[0]
        matched = len(j) > 0
        dom_rows.append({"fem_mode": int(k), "freq_hz": round(float(fmodes[k]), 1),
                         "mount_weight_pct": round(float(frac[k] * 100), 1),
                         "matched_to_measured": matched,
                         "meas_freq_hz": round(float(f_meas_k[j[0]]), 1) if matched else None,
                         "freq_err_pct": round(float(fmatch[j[0]]), 1) if matched else None,
                         "mac": round(float(mac[j[0]]), 2) if matched else None})
    dom_matched = [r for r in dom_rows if r["matched_to_measured"]]
    dom_w_total = float(frac[dom].sum())
    dom_w_matched = float(sum(frac[r["fem_mode"]] for r in dom_matched))

    rec = {
        "deliverable": "STEP 0: top-plate-center mount modal effective-mass (drive-point residue) decomposition + "
                       "does this QOI lean on the well-predicted modes?",
        "mount": {"gid": MOUNT_GID, "xyz_in": list(MOUNT_XYZ), "axis": "Z", "snap_in": round(float(snap), 3),
                  "shocksat_mass_kg": SHOCKSAT_MASS_KG},
        "band_hz": list(BAND),
        "n_fem_modes_in_band": int(in_band.sum()),
        "n_modes_for_90pct_mount_residue": n90,
        "dominant_modes_90pct": dom_rows,
        "dominant_residue_fraction_that_is_MAC_matched_to_data": round(dom_w_matched / (dom_w_total + 1e-30), 3),
        "validity_gate": {
            "unweighted_median_freq_err_pct": round(float(np.median(fmatch[(f_fem_k >= BAND[0]) & (f_fem_k <= BAND[1])])), 2),
            "MOUNT_weighted_median_freq_err_pct": round(wmed(fmatch, wk_band), 2),
            "unweighted_median_mac": round(float(np.median(mac[(f_fem_k >= BAND[0]) & (f_fem_k <= BAND[1])])), 2),
            "MOUNT_weighted_median_mac": round(wmed(mac, wk_band), 2)},
        "convention_note": "drive-point a/F (peaks=resonance); reciprocal=local apparent mass (dips). 7004C source/"
                           "load interface apparent mass + total-mass anchor = Step 1. Ranking is convention-robust.",
        "note": "EXPLORATORY; YELLOW; no success claim; ZETA=1% physical (swap measured ~0.45% in Step 1)."}
    (OUT / "topplate_effmass_step0.json").write_text(json.dumps(rec, indent=2))

    # ---- figure
    fg = np.linspace(20, 320, 1200)
    H = drivepoint_accel(fg, fmodes, phi_mount)
    fig, (axA, axB) = plt.subplots(2, 1, figsize=(11, 7.2), gridspec_kw={"height_ratios": [1.3, 1]})
    axA.semilogy(fg, np.abs(H), color="#1f77b4", lw=1.2, label="FEM drive-point accelerance |a/F| at top-plate center")
    for k in dom:
        axA.axvline(fmodes[k], color="#d2691e", lw=0.8, alpha=0.6)
    for r in mfr:
        if BAND[0] <= r <= BAND[1]:
            axA.plot([r], [np.abs(H).min()], marker="^", color="0.35", ms=4)
    axA.axvspan(BAND[0], BAND[1], color="0.92", zorder=0)
    axA.set_xlim(20, 320); axA.set_ylabel("|a/F|  (drive-point)", fontsize=9)
    axA.set_title(f"Top-plate-center load path: {n90} FEM modes carry 90% of the in-band mount residue "
                  f"(orange); grey ^ = measured modes; grey band = data band", fontsize=9.5)
    axA.legend(fontsize=8, frameon=False, loc="upper right")
    axA.spines[["top", "right"]].set_visible(False)

    # bar: top modes by mount weight, colored by freq-match
    top = order[:min(12, in_band.sum())]
    xs = np.arange(len(top))
    cols = []
    labels = []
    for k in top:
        j = np.where(fem_k == k)[0]
        if len(j):
            fe = fmatch[j[0]]
            cols.append("#2ca02c" if fe < 3 else ("#ff7f0e" if fe < 8 else "#d62728"))
            labels.append(f"{fmodes[k]:.0f}Hz\nΔf {fe:.0f}%\nMAC {mac[j[0]]:.2f}")
        else:
            cols.append("0.6"); labels.append(f"{fmodes[k]:.0f}Hz\n(no match)")
    axB.bar(xs, frac[top] * 100, color=cols)
    axB.set_xticks(xs); axB.set_xticklabels(labels, fontsize=6.3)
    axB.set_ylabel("mount residue  (% of in-band)", fontsize=9)
    axB.set_title("green = freq match <3% (well predicted) · orange <8% · red worse · grey = no measured match",
                  fontsize=8.5)
    axB.spines[["top", "right"]].set_visible(False)

    vg = rec["validity_gate"]
    cap = (f"FEM modal effective-mass (drive-point residue phi(mount)^2) at the top-plate-center mount (gid {MOUNT_GID}, "
           f"snap {snap:.2f} in), z. {n90} of {int(in_band.sum())} in-band modes carry 90% of the load path; "
           f"{100*rec['dominant_residue_fraction_that_is_MAC_matched_to_data']:.0f}% of that residue is on modes "
           f"MAC-matched to the measured survey. VALIDITY GATE -- weighting by mount relevance vs treating all modes "
           f"equally: median freq error {vg['unweighted_median_freq_err_pct']}% -> {vg['MOUNT_weighted_median_freq_err_pct']}% "
           f"(mount-weighted); median MAC {vg['unweighted_median_mac']} -> {vg['MOUNT_weighted_median_mac']} (mount-weighted). "
           f"If mount-weighted is BETTER, the QOI leans on the modes we predict well -> usable despite poor per-sensor "
           f"FRFs. Drive-point convention (a/F peaks at resonance); 7004C interface apparent mass = Step 1. NO NUTS.")
    fig.text(0.01, -0.02, cap, fontsize=7.2, wrap=True, va="top")
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    outp = WS / "figures" / "topplate_effmass_step0.png"
    fig.savefig(outp, dpi=150, bbox_inches="tight"); plt.close(fig)

    print(f"mount gid {MOUNT_GID} snap {snap:.2f} in; {int(in_band.sum())} in-band FEM modes")
    print(f"{n90} modes carry 90% of the in-band mount residue; "
          f"{100*rec['dominant_residue_fraction_that_is_MAC_matched_to_data']:.0f}% of that residue is MAC-matched to data")
    print("dominant modes (freq Hz, mount %, measured Hz, freq err %, MAC):")
    for r in rec["dominant_modes_90pct"]:
        print(f"  {r['freq_hz']:>6} Hz  {r['mount_weight_pct']:>5}%  meas {r['meas_freq_hz']}  "
              f"err {r['freq_err_pct']}%  MAC {r['mac']}")
    print(f"VALIDITY GATE  freq err: unweighted {vg['unweighted_median_freq_err_pct']}%  -> "
          f"mount-weighted {vg['MOUNT_weighted_median_freq_err_pct']}%")
    print(f"               MAC:      unweighted {vg['unweighted_median_mac']}     -> "
          f"mount-weighted {vg['MOUNT_weighted_median_mac']}")
    print(f"wrote {outp}")
    return rec


if __name__ == "__main__":
    run()
