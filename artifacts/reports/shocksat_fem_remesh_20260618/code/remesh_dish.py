#!/usr/bin/env python3
"""Card D — TRUE local mesh refinement of the dish (Top_Circular_Plate, PID 701).

The dish shares ZERO nodes with other shell components (connected only by 5
CBUSH), so a 2x2 conforming subdivision of its quads is clean (no hanging
nodes at the boundary; edge midpoints shared between adjacent dish quads).

This produces out/dish_refined/fem_model.npz with the dish refined 2x (4056 ->
16224 quads, edge ~0.25 -> ~0.125 in) and EVERYTHING ELSE identical. Re-assemble
+ re-solve there to test whether refining the (already fine) dish moves the
modes / MAC. Expectation (D3): no meaningful change -> mesh is already converged.
"""
import json, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
z = np.load(f"{HERE}/fem_model.npz", allow_pickle=True)
gids = list(z["gids"].tolist()); xyz = list(z["xyz"])
g2i = {int(g): i for i, g in enumerate(gids)}
cquad = z["cquad4"]; cq_file = z["cquad4_file"]

dish = cq_file == "Top_Circular_Plate"
next_gid = max(gids) + 1
edge_mid = {}                       # frozenset({ga,gb}) -> new gid
def coord(g): return np.asarray(xyz[g2i[int(g)]])
def get_mid(ga, gb):
    global next_gid
    key = frozenset((int(ga), int(gb)))
    if key not in edge_mid:
        edge_mid[key] = next_gid
        gids.append(next_gid); xyz.append(0.5*(coord(ga)+coord(gb)))
        g2i[next_gid] = len(gids)-1; next_gid += 1
    return edge_mid[key]

new_quads = []
next_eid = int(cquad[:, 0].max()) + 1
for k in np.where(dish)[0]:
    eid, pid, n0, n1, n2, n3 = (int(x) for x in cquad[k])
    m01, m12, m23, m30 = get_mid(n0,n1), get_mid(n1,n2), get_mid(n2,n3), get_mid(n3,n0)
    # center node (unique per element)
    cgid = next_gid
    gids.append(cgid); xyz.append(0.25*(coord(n0)+coord(n1)+coord(n2)+coord(n3)))
    g2i[cgid] = len(gids)-1; next_gid += 1
    for sub in [(n0,m01,cgid,m30),(m01,n1,m12,cgid),(cgid,m12,n2,m23),(m30,cgid,m23,n3)]:
        new_quads.append([next_eid, pid, *sub]); next_eid += 1

# rebuild cquad4: keep non-dish, append refined dish quads
keep = cquad[~dish]
cquad_new = np.vstack([keep, np.array(new_quads, dtype=cquad.dtype)])
cq_file_new = np.concatenate([cq_file[~dish],
                              np.array(["Top_Circular_Plate"]*len(new_quads), dtype=cq_file.dtype)])

# new gfile array: extend with the dish file tag for new grids
gfile = list(z["gfile"].tolist()) + ["Top_Circular_Plate"]*(len(gids)-len(z["gfile"]))

out = {k: z[k] for k in z.files}
out["gids"] = np.array(gids, dtype=z["gids"].dtype)
out["xyz"] = np.array(xyz, dtype=float)
out["gfile"] = np.array(gfile, dtype=z["gfile"].dtype)
out["cquad4"] = cquad_new
out["cquad4_file"] = cq_file_new

od = f"{HERE}/out/dish_refined"; os.makedirs(od, exist_ok=True)
np.savez_compressed(f"{od}/fem_model.npz", **out)
# copy the solver inputs needed alongside
import shutil
for f in ["measured_modes.npz", "groups.json"]:
    shutil.copy(f"{HERE}/{f}", f"{od}/{f}")
print(f"dish refined: {int(dish.sum())} -> {len(new_quads)} quads; "
      f"grids {len(z['gids'])} -> {len(gids)} (+{len(gids)-len(z['gids'])}); "
      f"new DOF +{6*(len(gids)-len(z['gids']))}")
print(f"wrote {od}/fem_model.npz")
