"""
Generate a ready-to-run MSC/NX Nastran bulk-data deck (SOL 103 normal modes) for the
Phase-1 hexapod, for the HUMAN to solve and visualize in Femap. The agent does NOT solve
it and writes NO frequencies (results.json keeps freqs null, solved_by=human).

Best-practice deck (independent re-derivation; shares only shared/spec.py raw inputs):
  - Tray: CQUAD4 shell (PSHELL, t=12.7 mm), MAT1 6061-T6.
  - Struts (x6): CROD two-force rods (PROD, tube area + torsion constant) -- the faithful
    moment-free idealization of a spherical rod-end push-rod.
  - Joints: stiff CBUSH (PBUSH K1=K2=K3=1e9 N/m, K4=K5=K6=0 => moment-free) between each
    tray apex grid and the coincident rod-top grid (explicit joint => future parametric
    compliance, exactly the spec's "stiff CBUSH k~1e9").
  - Base: SPC1 fixes the six feet (123456).
  - EIGRL extracts the first ~10 modes; PARAM,AUTOSPC,YES removes the massless rod-top
    rotational DOF.

Writes: ../model/model.bdf  and  ../model/deck_meta.json
"""
import os
import sys
import json
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


def build(target_h_mm=22.0, nmodes=10):
    T = spec.TRAY; S = spec.STRUT
    apex = spec.apex_m(); foot = spec.foot_m()
    ax = [a[0] for a in apex.values()]; ay = [a[1] for a in apex.values()]
    xg = grid1d([-T["Lx"]/2, *ax, T["Lx"]/2], target_h_mm*1e-3)
    yg = grid1d([-T["Ly"]/2, *ay, T["Ly"]/2], target_h_mm*1e-3)
    z = T["z_mid"]
    NX, NY = len(xg), len(yg)

    def gid(i, j):
        return 1 + i + j*NX
    grids = {}
    for j in range(NY):
        for i in range(NX):
            grids[gid(i, j)] = (xg[i], yg[j], z)
    nmax = NX*NY
    gnum = nmax
    apex_grid = {}
    for ak in sorted({k for _, k, _ in spec.STRUTS}):
        ix = int(np.argmin(np.abs(xg-apex[ak][0])))
        iy = int(np.argmin(np.abs(yg-apex[ak][1])))
        apex_grid[ak] = gid(ix, iy)

    rod_top = {}; foot_grid = {}
    for name, ak, fk in spec.STRUTS:
        gnum += 1; rod_top[name] = gnum; grids[gnum] = tuple(apex[ak])
        gnum += 1; foot_grid[name] = gnum; grids[gnum] = tuple(foot[fk])

    lines = []
    w = lines.append
    # ---- executive + case control ----
    w("SOL 103")
    w("CEND")
    w("TITLE = Phase-1 hexapod normal modes (Opus deck; human solves in Femap)")
    w("ECHO = NONE")
    w("METHOD = 100")
    w("SPC = 1")
    w("DISPLACEMENT(PLOT) = ALL")
    w("BEGIN BULK")
    w("PARAM,AUTOSPC,YES")
    w("PARAM,POST,-1")
    w("PARAM,PRGPST,NO")
    w("EIGRL,100,,,{0}".format(nmodes))
    # ---- materials / properties ----
    E = T["E"]; nu = T["nu"]; G = E/(2*(1+nu))
    w(f"MAT1,1,{E:.4e},{G:.4e},{nu:.3f},{T['rho']:.1f}")
    w(f"PSHELL,1,1,{T['t']:.6e},1,,1")
    # strut rod: area + torsion constant J
    w(f"PROD,2,1,{S['A']:.6e},{S['J']:.6e}")
    w(f"PBUSH,3,K,{spec.JOINT['k_trans']:.3e},{spec.JOINT['k_trans']:.3e},{spec.JOINT['k_trans']:.3e},0.0,0.0,0.0")
    # ---- grids ----
    for g_ in sorted(grids):
        x, y, zz = grids[g_]
        w(f"GRID,{g_},,{x:.6e},{y:.6e},{zz:.6e}")
    # ---- shell elements ----
    eid = 0
    for j in range(NY-1):
        for i in range(NX-1):
            eid += 1
            w(f"CQUAD4,{eid},1,{gid(i,j)},{gid(i+1,j)},{gid(i+1,j+1)},{gid(i,j+1)}")
    nquad = eid
    # ---- struts (CROD) ----
    for name, ak, fk in spec.STRUTS:
        eid += 1
        w(f"CROD,{eid},2,{rod_top[name]},{foot_grid[name]}")
    # ---- joints (CBUSH, coincident grids, basic CID=0) ----
    for name, ak, fk in spec.STRUTS:
        eid += 1
        w(f"CBUSH,{eid},3,{apex_grid[ak]},{rod_top[name]},,,,0")
    # ---- SPC feet ----
    feet = sorted(foot_grid.values())
    w("SPC1,1,123456," + ",".join(str(g_) for g_ in feet))
    w("ENDDATA")

    out = os.path.join(MODEL, "model.bdf")
    with open(out, "w") as f:
        f.write("\n".join(lines)+"\n")
    meta = dict(NX=NX, NY=NY, nquad=nquad, nstrut=len(spec.STRUTS),
                nmodes=nmodes, target_h_mm=target_h_mm,
                apex_grid={k: int(v) for k, v in apex_grid.items()},
                xg=[float(x) for x in xg], yg=[float(y) for y in yg], z=float(z),
                grids={int(k): list(map(float, v)) for k, v in grids.items()})
    json.dump(meta, open(os.path.join(MODEL, "deck_meta.json"), "w"), indent=2)
    print(f"wrote {out}: {NX}x{NY} shell grids, {nquad} CQUAD4, {len(spec.STRUTS)} CROD + 6 CBUSH")
    return meta


if __name__ == "__main__":
    build()
