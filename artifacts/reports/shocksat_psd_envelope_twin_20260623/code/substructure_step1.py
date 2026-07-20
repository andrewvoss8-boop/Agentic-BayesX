#!/usr/bin/env python3
"""STEP 1 (Andrew approved): validate the 'top-plate + struts = secondary substructure' premise via FULL-FIELD modal
energy localization, now that the DOF->node map is recoverable (keep_dofs: dof = 6*node + axis).

For every in-band FEM mode, reconstruct the full physical mode shape u = vk @ (T @ Q[:,m]) over all kept translational
DOFs and split the modal motion energy (sum u^2) by region:
    box   z < 45 in     (main structure / source)
    strut 45 <= z < 55  (struts)
    plate z >= 55        (top circular plate)
Then ask: are the QOI-dominant, poorly-correlated, UNMEASURED ~233-254 Hz modes concentrated in the PLATE+STRUTS
(=> the substructure captures them, interface drops to the strut base) while the well-correlated modes live in the BOX
(=> the source side is global/trustworthy)? Bonus: strut-base interface modal residue = which modes drive the interface.

NOTE: energy = sum of translational u^2 (displacement-based; physical per-DOF mass not available from the reduced
model -> indicative localization, not mass-weighted KE). A true fixed-interface Craig-Bampton solve needs the
partitioned physical M/K (full FE re-solve) -- this is the premise check that decides whether that is worth doing.
NO NUTS. Output: figures/substructure_step1.png + out/substructure_step1.json.
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
ZTOP = 57.74989
Z_BOX, Z_PLATE = 45.0, 55.0          # region cuts (in)
IF_LO, IF_HI = 45.0, 47.0            # strut-base interface band (struts attach to box)


def run():
    R = rf.load_reduced()
    K1 = R.A_fix + R.A.sum(0); w2, Q = np.linalg.eigh(K1)
    fmodes = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)

    # DOF -> node/axis/coord map from keeprow (dof = 6*node + axis)
    keep_arr = np.empty(len(R.keeprow), dtype=np.int64)
    for dof, row in R.keeprow.items():
        keep_arr[row] = dof
    node = keep_arr // 6; axis = keep_arr % 6
    xyz = R.xyz[node]; z = xyz[:, 2]; rr = np.hypot(xyz[:, 0], xyz[:, 1])
    trans = axis < 3
    box = trans & (z < Z_BOX); strut = trans & (z >= Z_BOX) & (z < Z_PLATE); plate = trans & (z >= Z_PLATE)
    iface = (axis == 2) & (z >= IF_LO) & (z < IF_HI)               # strut-base z interface DOFs

    # full physical modal field for in-band modes:  U = vk[:,:80] @ T ; field = U @ Q
    inb = np.where((fmodes >= BAND[0]) & (fmodes <= BAND[1]))[0]
    U = np.asarray(R.vk[:, :80], dtype=np.float64) @ R.T          # (Ndof, 74)
    field = U @ Q[:, inb]                                         # (Ndof, n_inb)

    # edge bolt-circle mount residue (the realistic mount) for ordering
    feet = []
    for a in np.linspace(0, 2 * np.pi, 8, endpoint=False):
        rowf, _, _ = R.reduced_row((9.0 * np.cos(a), 9.0 * np.sin(a), ZTOP), "Z"); feet.append(rowf @ Q)
    w_edge = (np.array(feet).mean(0)) ** 2

    # MAC-match to measured survey
    D = SB.build_dofs(R); _, pairs = SB.match_modes(D, Q)
    matched = {int(p[1]): (round(float(D["mfr"][p[0]]), 1), round(float(p[2]), 2)) for p in pairs}

    e = field ** 2
    Ebox = e[box].sum(0); Estr = e[strut].sum(0); Epla = e[plate].sum(0)
    Etot = Ebox + Estr + Epla + 1e-30
    Eif = e[iface].sum(0)
    order = np.argsort(w_edge[inb])[::-1]

    rows = []
    for c in order[:14]:
        k = int(inb[c])
        rows.append({"fem_mode": k, "freq_hz": round(float(fmodes[k]), 1),
                     "edge_mount_pct": round(float(w_edge[k] / w_edge[inb].sum() * 100), 1),
                     "energy_box_pct": round(float(Ebox[c] / Etot[c] * 100), 0),
                     "energy_strut_pct": round(float(Estr[c] / Etot[c] * 100), 0),
                     "energy_plate_pct": round(float(Epla[c] / Etot[c] * 100), 0),
                     "plate_plus_strut_pct": round(float((Estr[c] + Epla[c]) / Etot[c] * 100), 0),
                     "measured": matched.get(k)})

    # interface (strut-base) modal residue ranking
    if_order = np.argsort(Eif)[::-1][:8]
    iface_rows = [{"freq_hz": round(float(fmodes[int(inb[c])]), 1),
                   "iface_residue_pct": round(float(Eif[c] / (Eif.sum() + 1e-30) * 100), 1),
                   "plate_plus_strut_pct": round(float((Estr[c] + Epla[c]) / Etot[c] * 100), 0),
                   "measured": matched.get(int(inb[c]))} for c in if_order]

    # headline aggregates: energy-localization of the QOI-dominant (edge-weighted) vs measured modes
    w = w_edge[inb]; wn = w / w.sum()
    qoi_ps = float(np.sum(wn * (Estr + Epla) / Etot))             # edge-mount-weighted plate+strut energy fraction
    meas_mask = np.array([int(inb[c]) in matched for c in range(len(inb))])
    rec = {
        "deliverable": "STEP 1: full-field modal energy localization (box/strut/plate) -> substructuring premise",
        "region_cuts_in": {"box_z_lt": Z_BOX, "plate_z_ge": Z_PLATE, "strut_between": [Z_BOX, Z_PLATE]},
        "n_kept_dofs": int(len(keep_arr)), "n_inband_modes": int(len(inb)),
        "dof_counts_translational": {"box": int(box.sum()), "strut": int(strut.sum()), "plate": int(plate.sum())},
        "modes_by_edge_mount_residue": rows,
        "edge_mount_weighted_plate_plus_strut_energy_frac": round(qoi_ps, 3),
        "strut_base_interface_top_modes": iface_rows,
        "premise": "If the high edge-mount, UNMEASURED ~233-254 Hz modes show high plate+strut energy AND the measured "
                   "modes show high box energy, the substructuring split is valid: secondary=plate+struts captures the "
                   "hard modes; source=box at the strut base is global/well-correlated.",
        "caveat": "displacement-energy (no per-DOF mass); indicative. True fixed-interface CB modes need partitioned "
                  "physical M/K (FE re-solve).",
        "note": "EXPLORATORY; YELLOW; no success claim; NO NUTS."}
    (WS / "out" / "substructure_step1.json").write_text(json.dumps(rec, indent=2))

    # ---- figure: stacked energy bars for top QOI modes
    fig, ax = plt.subplots(figsize=(12, 5.2))
    n = len(rows); x = np.arange(n)
    bx = np.array([r["energy_box_pct"] for r in rows]); st = np.array([r["energy_strut_pct"] for r in rows])
    pl = np.array([r["energy_plate_pct"] for r in rows])
    ax.bar(x, pl, color="#d62728", label="plate (z>=55)")
    ax.bar(x, st, bottom=pl, color="#ff7f0e", label="struts (45-55)")
    ax.bar(x, bx, bottom=pl + st, color="#1f77b4", label="box (z<45)")
    labs = []
    for r in rows:
        m = r["measured"]
        tag = f"MAC{m[1]}" if m else "no\nmeas"
        labs.append(f"{r['freq_hz']:.0f}Hz\nmount{r['edge_mount_pct']:.0f}%\n{tag}")
    ax.set_xticks(x); ax.set_xticklabels(labs, fontsize=6.4)
    ax.set_ylabel("modal motion energy by region (%)", fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_title("Where each top-plate-load-path mode actually moves (ordered by edge-mount residue). "
                 "Red+orange = plate+struts (the 'secondary'); blue = box (the 'source').", fontsize=9.5)
    ax.legend(fontsize=8, frameon=False, loc="lower right", ncol=3)
    ax.spines[["top", "right"]].set_visible(False)
    cap = (f"Full-field FEM modal energy split (sum of translational u^2; {len(keep_arr)} kept DOFs). "
           f"Edge-mount-weighted plate+strut energy fraction of the load path = {100*qoi_ps:.0f}%. If the unmeasured "
           f"~233-254 Hz mount-dominant modes are red/orange (plate+struts) and the MAC-matched modes are blue (box), "
           f"the substructuring premise holds: secondary=plate+struts captures the hard/unmeasured modes; source=box at "
           f"the strut base is global/well-correlated. Displacement-energy (no per-DOF mass); indicative. NO NUTS.")
    fig.text(0.01, -0.02, cap, fontsize=7.2, wrap=True, va="top")
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    outp = WS / "figures" / "substructure_step1.png"
    fig.savefig(outp, dpi=150, bbox_inches="tight"); plt.close(fig)

    print(f"kept DOFs {len(keep_arr)}; translational region DOFs: box {int(box.sum())}, strut {int(strut.sum())}, "
          f"plate {int(plate.sum())}; in-band modes {len(inb)}")
    print(f"\n{'freqHz':>7} {'mount%':>6} {'box%':>5} {'strut%':>6} {'plate%':>6} {'pl+str%':>7}  measured(Hz,MAC)")
    for r in rows:
        print(f"{r['freq_hz']:>7} {r['edge_mount_pct']:>6} {r['energy_box_pct']:>5.0f} {r['energy_strut_pct']:>6.0f} "
              f"{r['energy_plate_pct']:>6.0f} {r['plate_plus_strut_pct']:>7.0f}  {r['measured']}")
    print(f"\nEDGE-mount-weighted plate+strut energy fraction of the load path = {100*qoi_ps:.0f}%")
    print("\nstrut-base interface (z 45-47, z-DOF) top modes by residue:")
    for r in iface_rows:
        print(f"  {r['freq_hz']:>6} Hz  iface {r['iface_residue_pct']:>5}%  plate+strut {r['plate_plus_strut_pct']:>3.0f}%  "
              f"meas {r['measured']}")
    print(f"\nwrote {outp}")
    return rec


if __name__ == "__main__":
    run()
