"""
Render the Nastran deck geometry (undeformed mesh) and write results.json with NULL
solved frequencies (solved_by=human). The agent does NOT solve this deck.

Run after make_bdf.py: ../../.venv/bin/python render_and_results.py
"""
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import spec

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.abspath(os.path.join(HERE, "..", "model"))
FIG = os.path.abspath(os.path.join(HERE, "..", "figures"))
os.makedirs(FIG, exist_ok=True)


def _eq(ax):
    lim = np.array([ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d()])
    c = lim.mean(1); r = 0.5*(lim[:, 1]-lim[:, 0]).max()
    ax.set_xlim3d(c[0]-r, c[0]+r); ax.set_ylim3d(c[1]-r, c[1]+r); ax.set_zlim3d(c[2]-r, c[2]+r)


def main():
    meta = json.load(open(os.path.join(MODEL, "deck_meta.json")))
    NX, NY = meta["NX"], meta["NY"]
    xg, yg, z = meta["xg"], meta["yg"], meta["z"]

    fig = plt.figure(figsize=(7, 6)); ax = fig.add_subplot(111, projection="3d")
    segs = []
    for j in range(NY):
        for i in range(NX-1):
            segs.append([(xg[i], yg[j], z), (xg[i+1], yg[j], z)])
    for i in range(NX):
        for j in range(NY-1):
            segs.append([(xg[i], yg[j], z), (xg[i], yg[j+1], z)])
    ax.add_collection3d(Line3DCollection(segs, colors="0.6", linewidths=0.4))
    apex = spec.apex_m(); foot = spec.foot_m()
    for name, ak, fk in spec.STRUTS:
        ap = apex[ak]; ft = foot[fk]
        ax.plot([ap[0], ft[0]], [ap[1], ft[1]], [ap[2], ft[2]], "-", color="C3", lw=2)
        ax.scatter([ap[0]], [ap[1]], [ap[2]], color="C0", s=25)  # CBUSH joint
    ax.set_title("Nastran deck — geometry (CQUAD4 shell tray + CROD struts + CBUSH joints)\n"
                 "SOL 103 EIGRL; HUMAN solves + visualizes mode shapes in Femap")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
    _eq(ax); fig.tight_layout()
    fig.savefig(os.path.join(FIG, "nastran_geometry.png"), dpi=130); plt.close(fig)

    nmodes = meta["nmodes"]
    results = {
        "agent": "opus", "tool": "nastran_deck", "solved_by": "human",
        "units": "SI (m, kg, N, Hz)",
        "frame": "origin at tray center; +z up; tray mid-plane z=0.098 m; base z=0",
        "mass_case": "bare tray, no ballast; PSHELL t=12.7 mm => ~3.086 kg",
        "boundary_condition": "feet fixed (SPC1 123456); source plate not modeled",
        "joint_status": "RIGID (stiff CBUSH K1=K2=K3=1e9 N/m, K4=K5=K6=0 => moment-free); CROD struts are two-force/moment-free",
        "frequencies_hz": [None]*nmodes,
        "frequency_label": "PROVISIONAL UPPER BOUND (rigid joints) -- to be filled by human Femap solve",
        "mode_type": [None]*nmodes,
        "element_types": {
            "tray": "CQUAD4 shell (PSHELL t=12.7 mm), MAT1 6061-T6",
            "struts": "CROD two-force rod (PROD: tube area + torsion J); faithful spherical rod-end",
            "joints": "CBUSH stiff translational (PBUSH K1-3=1e9, K4-6=0 => moment-free); explicit joint node",
            "base": "SPC1 123456 at the 6 feet"},
        "solver_setup": "SOL 103 normal modes; EIGRL,100 first %d modes; PARAM,AUTOSPC,YES" % nmodes,
        "mesh": {"tray_grid": f"{NX}x{NY} shell grids, {meta['nquad']} CQUAD4, {meta['nstrut']} CROD, 6 CBUSH",
                 "target_h_mm": meta["target_h_mm"]},
        "mesh_convergence": None,
        "near_degenerate_pairs": None,
        "deck_file": "model/model.bdf",
        "run_instructions": "RUN_IN_FEMAP.md",
        "note": "Deck only -- agent did NOT solve. The human runs SOL 103 in Femap/Nastran, then fills frequencies_hz, mode_type, near_degenerate_pairs, and mesh_convergence. Do NOT invent solved numbers.",
        "integrity": "independent re-derivation; shares only shared/spec.py raw inputs; CQUAD4 shell + CROD + CBUSH deck; no porting of K/M, eigen-results, or frequency tables.",
    }
    json.dump(results, open(os.path.join(HERE, "..", "results.json"), "w"), indent=2)
    print("wrote geometry figure + results.json (solved_by=human, freqs null)")


if __name__ == "__main__":
    main()
