#!/usr/bin/env python3
"""Parse the ShockSat FEM_20211021 NASTRAN bulk data into numpy structures.

Small-field (8-column) cards only (verified: no large-field cards in deck).
Handles continuation lines starting with '+'. NASTRAN float forms like
'2.536-4' and '1.+6' are converted. Element/property/grid ownership is tagged
by include file so per-part-group stiffness scaling can be built downstream.

Output: fem_model.npz (+ fem_parse_report.json with counts and unit checks).
"""
import glob
import json
import os
import re
import numpy as np

SRC = "../shocksat_statfem_runner_20260609/extracted/FEM/FEM_20211021"

FILES = [
    "Material_Properties_101521.blk", "Bottom_Box_101521.blk",
    "Top_Box_101521.blk", "Angle_Brackets_101521.blk",
    "Cross_Beam_101521.blk", "Rectangular_Plates_101521.blk",
    "Top_Brackets_101521.blk", "Top_Circular_Plate_101521.blk",
    "Joint_Connections_101521.blk", "Rectangular_Plate_Contact_101521.blk",
    "Modal_Test_Instrumentation_092721.blk",
    # "Shock_Test_Instrumentation.blk" DROPPED (decision D10): contains ONLY
    # 37 GRID + 37 RBE2 (zero mass/stiffness shock-response spiders) whose
    # dependent structure grids collide with Joint_Connections RBE2 spiders.
]

NUMRE = re.compile(r'^([+-]?(?:\d+\.?\d*|\.\d+))([+-]\d+)$')

def nfloat(s):
    s = s.strip()
    if not s:
        return 0.0
    m = NUMRE.match(s)
    if m:  # NASTRAN shorthand exponent: 2.536-4 -> 2.536e-4
        return float(m.group(1) + 'e' + m.group(2))
    return float(s)

def nint(s, default=0):
    s = s.strip()
    return int(s) if s else default

def logical_cards(path):
    """Yield lists of 8-char fields (fields[0] = card name)."""
    cards = []
    for raw in open(path, errors='ignore'):
        line = raw.rstrip('\n')
        if not line.strip() or line.startswith('$'):
            continue
        fields = [line[i:i + 8] for i in range(0, 72, 8)]
        if line.startswith('+') or line.startswith(' ' * 8):
            if cards:
                cards[-1].extend(fields[1:])
        else:
            cards.append(fields)
    return cards

def main():
    grids, gfile = {}, {}
    cquad4, ctria3, cbush, conm2, rbe2 = [], [], [], [], []
    pshell, pbush, mat1, cords = {}, {}, {}, {}
    counts = {}
    for fn in FILES:
        path = os.path.join(SRC, fn)
        tag = fn.split('_101521')[0].split('_092721')[0].split('.blk')[0]
        for f in logical_cards(path):
            name = f[0].strip()
            counts[(tag, name)] = counts.get((tag, name), 0) + 1
            if name == 'GRID':
                gid = nint(f[1]); cp = nint(f[2]); cd = nint(f[6])
                assert cp == 0 and cd == 0, f"GRID {gid} CP/CD nonzero"
                assert gid not in grids, f"duplicate GRID {gid}"
                grids[gid] = (nfloat(f[3]), nfloat(f[4]), nfloat(f[5]))
                gfile[gid] = tag
            elif name == 'CQUAD4':
                cquad4.append((nint(f[1]), nint(f[2]), nint(f[3]), nint(f[4]),
                               nint(f[5]), nint(f[6]), tag))
            elif name == 'CTRIA3':
                ctria3.append((nint(f[1]), nint(f[2]), nint(f[3]), nint(f[4]),
                               nint(f[5]), tag))
            elif name == 'CBUSH':
                # EID PID GA GB GO/X1 X2 X3 CID -> orientation fields blank here
                assert not f[5].strip() and not f[6].strip() and not f[7].strip(), \
                    f"CBUSH {f[1]} uses GO/Xi orientation - unhandled"
                cbush.append((nint(f[1]), nint(f[2]), nint(f[3]), nint(f[4]),
                              nint(f[8]), tag))
            elif name == 'CONM2':
                # EID G CID M X1 X2 X3 _ I11 I21 I22 I31 I32 I33
                assert nint(f[3]) == 0, "CONM2 CID nonzero"
                inertia = [nfloat(x) for x in (f[9:15] + [''] * 6)[:6]]
                conm2.append((nint(f[1]), nint(f[2]), nfloat(f[4]),
                              nfloat(f[5]), nfloat(f[6]), nfloat(f[7]),
                              *inertia, tag))
            elif name == 'RBE2':
                gn = nint(f[2]); cm = f[3].strip()
                gms = [nint(x) for x in f[4:] if x.strip()]
                rbe2.append((nint(f[1]), gn, cm, gms, tag))
            elif name == 'PSHELL':
                # PID MID1 T MID2 12I/T3 MID3 TS/T NSM
                pid = nint(f[1])
                pshell[pid] = dict(
                    mid1=nint(f[2]), t=nfloat(f[3]), mid2=nint(f[4]),
                    bend_ratio=nfloat(f[5]) if f[5].strip() else 1.0,
                    mid3=nint(f[6]),
                    ts_t=nfloat(f[7]) if f[7].strip() else 0.833333,
                    nsm=nfloat(f[8]) if len(f) > 8 and f[8].strip() else 0.0,
                    file=tag)
            elif name == 'PBUSH':
                pid = nint(f[1])
                assert f[2].strip() == 'K', f"PBUSH {pid} non-K row"
                pbush[pid] = dict(k=[nfloat(x) for x in f[3:9]], file=tag)
            elif name == 'MAT1':
                mid = nint(f[1])
                E = nfloat(f[2]); G = nfloat(f[3]); nu = nfloat(f[4])
                mat1[mid] = dict(E=E, G=G, nu=nu, rho=nfloat(f[5]))
            elif name in ('CORD2R', 'CORD2C'):
                cid = nint(f[1])
                pts = [nfloat(x) for x in f[3:9] + f[9:12]]
                a = np.array(pts[0:3]); b = np.array(pts[3:6]); c = np.array(pts[6:9])
                z = b - a; z /= np.linalg.norm(z)
                xz = c - a
                y = np.cross(z, xz); y /= np.linalg.norm(y)
                x = np.cross(y, z)
                cords[cid] = dict(type=name, origin=a.tolist(),
                                  R=np.stack([x, y, z]).tolist())
            else:
                raise ValueError(f"unhandled card {name} in {fn}")

    gids = np.array(sorted(grids), dtype=np.int64)
    xyz = np.array([grids[g] for g in gids])
    np.savez_compressed(
        "fem_model.npz",
        gids=gids, xyz=xyz,
        gfile=np.array([gfile[g] for g in gids]),
        cquad4=np.array([q[:6] for q in cquad4], dtype=np.int64),
        cquad4_file=np.array([q[6] for q in cquad4]),
        ctria3=np.array([t[:5] for t in ctria3], dtype=np.int64),
        ctria3_file=np.array([t[5] for t in ctria3]),
        cbush=np.array([b[:5] for b in cbush], dtype=np.int64),
        cbush_file=np.array([b[5] for b in cbush]),
        conm2=np.array([c[:12] for c in conm2], dtype=np.float64),
        rbe2=np.array(
            [(r[0], r[1], int(r[2]), len(r[3])) for r in rbe2], dtype=np.int64),
        rbe2_gms=np.array(
            [g for r in rbe2 for g in r[3]], dtype=np.int64),
        pshell=json.dumps(pshell), pbush=json.dumps(pbush),
        mat1=json.dumps(mat1), cords=json.dumps(cords))

    rep = dict(
        n_grids=len(gids), n_cquad4=len(cquad4), n_ctria3=len(ctria3),
        n_cbush=len(cbush), n_conm2=len(conm2), n_rbe2=len(rbe2),
        n_rbe2_dep_grids=int(sum(len(r[3]) for r in rbe2)),
        pshell={str(k): v for k, v in pshell.items()},
        pbush={str(k): v for k, v in pbush.items()},
        mat1={str(k): v for k, v in mat1.items()},
        cords={str(k): v for k, v in cords.items()},
        counts={f"{a}:{b}": c for (a, b), c in sorted(counts.items())})
    json.dump(rep, open("fem_parse_report.json", "w"), indent=1)
    print(json.dumps({k: rep[k] for k in
                      ['n_grids', 'n_cquad4', 'n_ctria3', 'n_cbush',
                       'n_conm2', 'n_rbe2', 'n_rbe2_dep_grids']}, indent=1))

if __name__ == "__main__":
    main()
