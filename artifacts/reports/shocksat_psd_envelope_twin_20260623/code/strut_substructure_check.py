#!/usr/bin/env python3
"""Substructuring premise check (Andrew: treat top-plate + struts as the 'secondary structure'). For each FEM mode,
how much of its modal energy lives in the UPPER region (top plate + struts, high z) vs the main box (low z)?

If the QOI-dominant, poorly-correlated, UNMEASURED ~233-254 Hz modes are UPPER-localized (energy concentrated in the
plate+struts), then designating plate+struts as a substructure captures exactly those modes -> the interface drops to
the strut base where the well-correlated GLOBAL box modes live. Cheap, NO NUTS. (Caveat: uses the instrumented DOFs,
which are sparser on the top deck -> indicative, not a full-field energy split.) Output: out/strut_substructure_check.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import shape_borrow_diag as SB

WS = Path(__file__).resolve().parent.parent
BAND = (45.0, 260.0)
ZTOP = 57.74989


def run():
    R = rf.load_reduced()
    K1 = R.A_fix + R.A.sum(0); w2, Q = np.linalg.eigh(K1)
    fmodes = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)
    D = SB.build_dofs(R); coords = D["coord"]; z = coords[:, 2]
    FemAll = D["G"] @ Q                                    # instrumented-DOF modal shapes

    # mount residue (edge bolt-circle, the realistic mount) for weighting context
    feet = []
    for a in np.linspace(0, 2 * np.pi, 8, endpoint=False):
        row, _, _ = R.reduced_row((9.0 * np.cos(a), 9.0 * np.sin(a), ZTOP), "Z"); feet.append(row @ Q)
    w_edge = (np.array(feet).mean(0)) ** 2
    crow, _, _ = R.reduced_row((0, 0, ZTOP), "Z"); w_ctr = (crow @ Q) ** 2

    # MAC-match to measured survey
    FemAllM, pairs = SB.match_modes(D, Q)
    matched = {int(p[1]): (round(float(D["mfr"][p[0]]), 1), round(float(p[2]), 2)) for p in pairs}

    n_up45 = int((z > 45).sum()); n_up50 = int((z > 50).sum()); n_tot = len(z)
    inb = np.where((fmodes >= BAND[0]) & (fmodes <= BAND[1]))[0]
    # rank by edge mount residue
    order = inb[np.argsort(w_edge[inb])[::-1]][:12]
    rows = []
    for k in order:
        e = FemAll[:, k] ** 2
        rows.append({"fem_mode": int(k), "freq_hz": round(float(fmodes[k]), 1),
                     "edge_mount_pct": round(float(w_edge[k] / w_edge[inb].sum() * 100), 1),
                     "center_mount_pct": round(float(w_ctr[k] / w_ctr[inb].sum() * 100), 1),
                     "upper_energy_frac_z45": round(float(e[z > 45].sum() / (e.sum() + 1e-30)), 2),
                     "upper_energy_frac_z50": round(float(e[z > 50].sum() / (e.sum() + 1e-30)), 2),
                     "measured": matched.get(int(k))})
    rec = {"deliverable": "substructuring premise: are the QOI-dominant modes localized to the top plate+struts?",
           "instrumented_dofs": {"total": n_tot, "above_z45": n_up45, "above_z50": n_up50,
                                 "caveat": "sparse top-deck coverage -> indicative energy split"},
           "z_top_in": ZTOP, "band_hz": list(BAND), "modes_by_edge_mount_residue": rows,
           "note": "EXPLORATORY; high upper_energy_frac on the unmeasured ~233-254 Hz modes => they are plate+strut "
                   "(secondary) modes; well-correlated modes spread into the box => global/source modes. NO NUTS."}
    (WS / "out" / "strut_substructure_check.json").write_text(json.dumps(rec, indent=2))

    print(f"instrumented DOFs: {n_tot} total, {n_up45} above z=45, {n_up50} above z=50 (sparse top -> indicative)")
    print(f"{'freqHz':>7} {'edge%':>6} {'ctr%':>6} {'Eup_z45':>8} {'Eup_z50':>8}  measured(Hz,MAC)")
    for r in rows:
        print(f"{r['freq_hz']:>7} {r['edge_mount_pct']:>6} {r['center_mount_pct']:>6} "
              f"{r['upper_energy_frac_z45']:>8} {r['upper_energy_frac_z50']:>8}  {r['measured']}")
    return rec


if __name__ == "__main__":
    run()
