"""
Generate a CalculiX .inp deck for the Phase-1 hexapod normal-modes solve.

Best-practice CalculiX build (independent re-derivation; shares only shared/spec.py):
  - Tray: solid 6061-T6 plate meshed with C3D8I (8-node INCOMPATIBLE-MODE hexahedra,
    good in bending vs plain C3D8). Structured graded mesh; 2 elements through thickness;
    mid-plane node layer at z=0.098 for strut attachment.
  - Struts (x6): T3D2 truss (3-D 2-node bar) with the tube cross-section area (A~22 mm^2).
    A truss is a two-force member => moment-free by construction, the exact behaviour of a
    spherical rod-end push-rod (CalculiX has no Nastran-style pin release; a truss is the
    clean, robust realization, and avoids the beam-"knot" expansion conflicting with the
    joint springs). Strut self-bending modes are covered by the JAX beam build instead.
  - Joints: tray-end = the truss top connects to a separate reference node that is tied
    to a small PATCH of tray nodes (within ~18 mm of the apex, all thickness layers) by a
    *RIGID BODY (RBE2) - the real rod-end bracket bolts to the tray over a finite footprint
    and is much stiffer than the tray, so a rigid footprint is faithful AND it removes the
    spurious local mode that a truss/spring loading a SINGLE continuum node produces. The
    truss is moment-free, so the joint is spherical. Base end = truss bottom node fixed.
    (A finite-compliance CBUSH/spring can be inserted between the ref node and the truss
    in a later phase to make joint stiffness an explicit parameter.)
  - *FREQUENCY (Lanczos) for the first modes.

Writes: ../model/hexapod.inp
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import spec

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.abspath(os.path.join(HERE, "..", "model"))
os.makedirs(MODEL, exist_ok=True)


def grid1d(required, target_h):
    req = sorted(set(required))
    out = [req[0]]
    for lo, hi in zip(req[:-1], req[1:]):
        n = max(1, int(round((hi-lo)/target_h)))
        for k in range(1, n+1):
            out.append(lo+(hi-lo)*k/n)
    return np.array(sorted(set(np.round(out, 9))))


def build_deck(target_h_mm=22.0, nz=2, nmodes=16, jobname="hexapod"):
    T = spec.TRAY; S = spec.STRUT
    apex = spec.apex_m(); foot = spec.foot_m()
    ax = [a[0] for a in apex.values()]; ay = [a[1] for a in apex.values()]
    # NOTE: different target mesh size than the TensorMesh build (independent mesh).
    xg = grid1d([-T["Lx"]/2, *ax, T["Lx"]/2], target_h_mm*1e-3)
    yg = grid1d([-T["Ly"]/2, *ay, T["Ly"]/2], target_h_mm*1e-3)
    z0 = T["z_mid"]-T["t"]/2
    zg = np.linspace(z0, z0+T["t"], nz+1)
    NX, NY, NZ = len(xg), len(yg), len(zg)

    # node numbering (1-based). tray nodes first.
    def tray_id(i, j, k):
        return 1 + i + j*NX + k*NX*NY
    nodes = {}
    for k in range(NZ):
        for j in range(NY):
            for i in range(NX):
                nodes[tray_id(i, j, k)] = (xg[i], yg[j], zg[k])
    nmax = NX*NY*NZ
    mid_k = (NZ-1)//2
    r_patch = 0.018  # m, rod-end bracket footprint radius for the distributing coupling
    apex_keys = sorted({ak for _, ak, _ in spec.STRUTS})
    # one bracket footprint patch per UNIQUE apex (the two bipod struts share an apex)
    patch = {}
    for ak in apex_keys:
        ids = []
        for k in range(NZ):
            for j in range(NY):
                for i in range(NX):
                    dx = xg[i]-apex[ak][0]; dy = yg[j]-apex[ak][1]
                    if dx*dx+dy*dy <= r_patch*r_patch:
                        ids.append(tray_id(i, j, k))
        patch[ak] = sorted(set(ids))

    # one reference node per apex (distributed onto its patch); both bipod trusses attach.
    beam_nodes = {}; ref_node = {}
    nid = nmax
    for ak in apex_keys:
        nid += 1; ref_node[ak] = nid; nodes[nid] = tuple(apex[ak])
    for name, ak, fk in spec.STRUTS:
        beam_nodes[(name, "top")] = ref_node[ak]
        nid += 1; beam_nodes[(name, "bot")] = nid; nodes[nid] = tuple(foot[fk])

    # hex elements
    hexes = []
    eid = 0
    for k in range(NZ-1):
        for j in range(NY-1):
            for i in range(NX-1):
                eid += 1
                conn = [tray_id(i, j, k), tray_id(i+1, j, k), tray_id(i+1, j+1, k), tray_id(i, j+1, k),
                        tray_id(i, j, k+1), tray_id(i+1, j, k+1), tray_id(i+1, j+1, k+1), tray_id(i, j+1, k+1)]
                hexes.append((eid, conn))
    # truss elements (T3D2: top=shared apex node, bot=foot)
    beams = []
    for name, ak, fk in spec.STRUTS:
        eid += 1
        beams.append((eid, name, beam_nodes[(name, "top")], beam_nodes[(name, "bot")]))

    L = []
    w = L.append
    w("** Phase-1 hexapod normal modes -- CalculiX (Opus build)")
    w("** Units SI (m, kg, N). Frame: origin tray center, +z up, tray mid z=0.098, base z=0.")
    w("** Independent re-derivation; shared inputs only from shared/spec.py.")
    w("*NODE, NSET=Nall")
    for n_ in sorted(nodes):
        x, y, z = nodes[n_]
        w(f"{n_}, {x:.8e}, {y:.8e}, {z:.8e}")
    # hex element set
    w("*ELEMENT, TYPE=C3D8I, ELSET=TRAY")
    for eid, conn in hexes:
        w(f"{eid}, " + ", ".join(str(c) for c in conn))
    # struts: single elset, T3D2 truss
    w("*ELEMENT, TYPE=T3D2, ELSET=STRUTS")
    for eid, name, nt, nb in beams:
        w(f"{eid}, {nt}, {nb}")
    # distributing-coupling (RBE3) elements: one per apex, spread ref node over its patch
    dcoup = {}
    for ak in apex_keys:
        eid += 1
        dcoup[ak] = eid
        w(f"*ELEMENT, TYPE=DCOUP3D, ELSET=DC_{ak}")
        w(f"{eid}, {ref_node[ak]}")
    # materials
    w("*MATERIAL, NAME=ALU")
    w("*ELASTIC")
    w(f"{T['E']:.6e}, {T['nu']:.4f}")
    w("*DENSITY")
    w(f"{T['rho']:.6e}")
    w("*SOLID SECTION, ELSET=TRAY, MATERIAL=ALU")
    # truss section: cross-sectional area on the data line
    w("*SOLID SECTION, ELSET=STRUTS, MATERIAL=ALU")
    w(f"{S['A']:.6e}")

    # distributing-coupling (RBE3) brackets: spread the truss ref-node load over the patch
    for ak in apex_keys:
        w(f"*DISTRIBUTING COUPLING, ELSET=DC_{ak}")
        for n_ in patch[ak]:
            w(f"{n_}, 1.0")

    # boundary: truss bottom (foot) nodes fixed (truss has only translational DOF)
    w("*NSET, NSET=FEET")
    w(", ".join(str(beam_nodes[(name, 'bot')]) for name, ak, fk in spec.STRUTS))
    w("*BOUNDARY")
    w("FEET, 1, 3")
    # remove unused tray drilling? not needed: solid nodes have only 1-3 DOF.

    # step: frequency
    w("*STEP")
    w("*FREQUENCY, STORAGE=YES")
    w(f"{nmodes}")
    w("*NODE FILE")
    w("U")
    w("*END STEP")

    out = os.path.join(MODEL, jobname+".inp")
    with open(out, "w") as f:
        f.write("\n".join(L)+"\n")
    meta = dict(NX=NX, NY=NY, NZ=NZ, nhex=len(hexes), ntruss=len(beams),
                target_h_mm=target_h_mm, nmodes=nmodes, r_patch_m=r_patch,
                patch_sizes={k: len(v) for k, v in patch.items()},
                ref_nodes={k: int(v) for k, v in ref_node.items()},
                joint="RBE3 distributing coupling over rod-end bracket footprint (r_patch); truss two-force struts (moment-free); feet fixed")
    print(f"wrote {out}: {NX}x{NY}x{NZ} nodes, {len(hexes)} C3D8I hex, {len(beams)} T3D2 truss; "
          f"patch sizes {meta['patch_sizes']}")
    return out, meta


if __name__ == "__main__":
    import json
    out, meta = build_deck()
    with open(os.path.join(MODEL, "deck_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
