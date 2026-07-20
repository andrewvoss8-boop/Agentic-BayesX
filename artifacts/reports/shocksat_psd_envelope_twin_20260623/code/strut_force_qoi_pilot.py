#!/usr/bin/env python3
"""PILOT (Andrew): goal-oriented / QOI-WEIGHTED twin-vs-FEM-vs-data comparison for an UNMEASURED QOI = force in the
struts. We never measure strut force, but it is a linear functional of the response, so each mode contributes to it by
a computable sensitivity. We weight the model-vs-data comparison by that sensitivity -> the comparison is graded on the
modes that drive strut force, not uniformly (which we showed is dominated by irrelevant local modes).

Strut-force proxy (no element connectivity available -> labeled proxy): the strut/transition region is z in [45,55].
A strut carries force when its two ends move differently, so the per-mode strut RACKING deformation =
   Delta_i = || mean_3D phi_i(strut top, z>=50) - mean_3D phi_i(strut bottom, z<50) ||      (axial + shear)
and the strut-force QOI sensitivity weight c_i ~ Delta_i (strut stiffness common across modes). Also reports the net
z interface force proxy omega^2 * |sum phi_z| (uniform-mass momentum). True strut force needs the FE element forces /
mass matrix (FE re-solve) -- this PILOT demonstrates the QOI-WEIGHTING METHOD and the data-trust decomposition.

Outputs: which modes drive strut force; QOI-weighted vs uniform freq-error/MAC (FEM-vs-data); the QOI TRUST FRACTION
(share of strut-force sensitivity carried by MEASURED/correlated modes); and FEM vs frequency-anchored-twin strut-force
spectra. NO NUTS. figures/strut_force_qoi_pilot.png + out/strut_force_qoi_pilot.json.
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
BAND = (45.0, 260.0)
ZETA = 0.01


def wmed(vals, w):
    w = np.asarray(w, float); vals = np.asarray(vals, float)
    if w.sum() <= 0:
        return float(np.median(vals))
    o = np.argsort(vals); return float(vals[o][np.searchsorted(np.cumsum(w[o] / w.sum()), 0.5)])


def run():
    R = rf.load_reduced()
    K1 = R.A_fix + R.A.sum(0); w2, Q = np.linalg.eigh(K1)
    fmodes = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)
    keep_arr = np.empty(len(R.keeprow), np.int64)
    for dof, row in R.keeprow.items():
        keep_arr[row] = dof
    node = keep_arr // 6; axis = keep_arr % 6
    xyz = R.xyz[node]; z = xyz[:, 2]; rr = np.hypot(xyz[:, 0], xyz[:, 1])

    inb = np.where((fmodes >= BAND[0]) & (fmodes <= BAND[1]))[0]
    U = np.asarray(R.vk[:, :80], np.float64) @ R.T
    field = U @ Q[:, inb]                               # (Ndof, n_inb)

    # strut/transition region z in [45,55]; top/bottom halves, per translational axis -> racking deformation
    strut = (z >= 45) & (z < 55)
    cQOI = np.zeros(len(inb))
    for a in range(3):
        top = strut & (axis == a) & (z >= 50); bot = strut & (axis == a) & (z < 50)
        if top.sum() and bot.sum():
            d = field[top].mean(0) - field[bot].mean(0)
            cQOI += d ** 2
    cQOI = np.sqrt(cQOI)                                # |Delta_i| strut racking (force sensitivity, relative)
    # net z interface force proxy (alt)
    ifz = (axis == 2) & (z >= 45)
    fz = (2 * np.pi * fmodes[inb]) ** 2 * np.abs(field[ifz].sum(0))

    # match to measured survey
    D = SB.build_dofs(R); _, pairs = SB.match_modes(D, Q)
    matched = {int(p[1]): (float(D["mfr"][p[0]]), float(p[2])) for p in pairs}
    fem_k = inb
    is_match = np.array([int(k) in matched for k in fem_k])
    meas_f = np.array([matched[int(k)][0] if int(k) in matched else fmodes[k] for k in fem_k])
    macv = np.array([matched[int(k)][1] if int(k) in matched else np.nan for k in fem_k])
    ferr = 100.0 * np.abs(fmodes[fem_k] - meas_f) / meas_f

    wn = cQOI / (cQOI.sum() + 1e-30)
    trust = float(wn[is_match].sum())                  # QOI sensitivity carried by measured modes
    # QOI-weighted vs uniform comparison over MATCHED in-band modes
    mm = is_match
    uni_ferr = float(np.median(ferr[mm])); qoi_ferr = wmed(ferr[mm], cQOI[mm])
    uni_mac = float(np.median(macv[mm])); qoi_mac = wmed(macv[mm], cQOI[mm])

    order = np.argsort(cQOI)[::-1]
    rows = [{"freq_hz": round(float(fmodes[fem_k[c]]), 1), "qoi_weight_pct": round(float(wn[c] * 100), 1),
             "measured": (round(matched[int(fem_k[c])][0], 1), round(matched[int(fem_k[c])][1], 2))
                         if int(fem_k[c]) in matched else None,
             "freq_err_pct": round(float(ferr[c]), 1) if mm[c] else None} for c in order[:12]]

    # strut-force spectra: QOI(f) = | sum_i c_i / (wi^2 - w^2 + 2j z wi w) | ; twin shifts matched modes to measured f
    fg = np.linspace(40, 300, 1500); w = 2 * np.pi * fg
    def spectrum(mode_f):
        wi = 2 * np.pi * np.asarray(mode_f)
        H = (cQOI[None, :] / (wi[None, :] ** 2 - w[:, None] ** 2 + 2j * ZETA * wi[None, :] * w[:, None])).sum(1)
        return np.abs(H)
    spec_fem = spectrum(fmodes[fem_k]); spec_twin = spectrum(meas_f)

    rec = {"deliverable": "QOI-weighted (goal-oriented) twin/FEM/data comparison for unmeasured QOI = strut force",
           "qoi_proxy": "strut racking deformation |mean_3D phi(z>=50) - mean_3D phi(z<50)| over strut region z45-55",
           "n_inband_modes": int(len(inb)),
           "strut_force_trust_fraction_measured_modes": round(trust, 3),
           "comparison_FEMvsDATA": {"uniform_median_freq_err_pct": round(uni_ferr, 2),
                                     "QOI_weighted_median_freq_err_pct": round(qoi_ferr, 2),
                                     "uniform_median_mac": round(uni_mac, 2),
                                     "QOI_weighted_median_mac": round(qoi_mac, 2)},
           "top_strut_force_modes": rows,
           "caveat": "displacement-based proxy (no element forces / per-DOF mass); twin = frequency-anchored "
                     "approximation of the calibrated twin (matched modes -> measured freq). Demonstrates the METHOD.",
           "note": "EXPLORATORY; YELLOW; NO NUTS."}
    (WS / "out" / "strut_force_qoi_pilot.json").write_text(json.dumps(rec, indent=2))

    # ---- figure
    fig, (axS, axB) = plt.subplots(1, 2, figsize=(13.5, 5), gridspec_kw={"width_ratios": [1.25, 1]})
    axS.semilogy(fg, spec_fem, color="#1f77b4", lw=1.4, label="as-delivered FEM")
    axS.semilogy(fg, spec_twin, color="#d2691e", lw=1.4, label="freq-anchored twin (matched->measured)")
    for c in order[:8]:
        k = fem_k[c]; col = "#2ca02c" if mm[c] else "#d62728"
        axS.axvline(fmodes[k], color=col, lw=0.8, alpha=0.55)
    axS.set_xlim(40, 300); axS.set_xlabel("frequency (Hz)", fontsize=9)
    axS.set_ylabel("strut-force QOI transfer |Q(f)|  (proxy)", fontsize=9)
    axS.set_title(f"Strut-force spectrum: green line=mode anchored by DATA, red=FEM-only (unmeasured).\n"
                  f"Trust = {100*trust:.0f}% of strut-force sensitivity is on MEASURED modes", fontsize=9)
    axS.legend(fontsize=8, frameon=False); axS.spines[["top", "right"]].set_visible(False)

    top = order[:10]; x = np.arange(len(top))
    cols = ["#2ca02c" if mm[c] else "#d62728" for c in top]
    axB.bar(x, wn[top] * 100, color=cols)
    labs = [f"{fmodes[fem_k[c]]:.0f}Hz\n" + (f"meas Δf{ferr[c]:.0f}%\nMAC{macv[c]:.2f}" if mm[c] else "no meas")
            for c in top]
    axB.set_xticks(x); axB.set_xticklabels(labs, fontsize=6.3)
    axB.set_ylabel("strut-force QOI weight (%)", fontsize=9)
    axB.set_title("which modes drive strut force (green=measured, red=not)", fontsize=9)
    axB.spines[["top", "right"]].set_visible(False)

    cap = (f"GOAL-ORIENTED comparison for the UNMEASURED strut-force QOI. Re-weighting the FEM-vs-data check by strut-"
           f"force sensitivity vs uniform: median freq error {uni_ferr:.1f}%->{qoi_ferr:.1f}% (QOI-wtd), MAC "
           f"{uni_mac:.2f}->{qoi_mac:.2f}. Strut-force TRUST = {100*trust:.0f}% of the sensitivity is on measured/"
           f"correlated modes; the rest (mainly the ~251 Hz strut-sway mode) is FEM-only / unmeasured. Proxy QOI "
           f"(strut racking); twin=frequency-anchored. NO NUTS.")
    fig.text(0.01, -0.03, cap, fontsize=7.2, wrap=True, va="top")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    outp = WS / "figures" / "strut_force_qoi_pilot.png"
    fig.savefig(outp, dpi=150, bbox_inches="tight"); plt.close(fig)

    print(f"strut-force TRUST fraction (measured modes): {100*trust:.0f}%")
    print(f"FEM-vs-data freq err: uniform {uni_ferr:.2f}%  -> QOI-weighted {qoi_ferr:.2f}%")
    print(f"FEM-vs-data MAC:      uniform {uni_mac:.2f}   -> QOI-weighted {qoi_mac:.2f}")
    print(f"\n{'freqHz':>7} {'QOIwt%':>7}  measured(Hz,MAC)   ferr%")
    for r in rows:
        print(f"{r['freq_hz']:>7} {r['qoi_weight_pct']:>7}  {str(r['measured']):>16}   {r['freq_err_pct']}")
    print(f"\nwrote {outp}")
    return rec


if __name__ == "__main__":
    run()
