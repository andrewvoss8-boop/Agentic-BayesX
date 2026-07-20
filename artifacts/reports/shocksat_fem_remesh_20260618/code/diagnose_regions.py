#!/usr/bin/env python3
"""Card D — Phase 1 region diagnosis (READ-ONLY, before any edit).

For each of the 8 data-flagged high-error regions, quantify HOW the as-received
FEM disagrees with the measured `.ash` modal survey, restricted to the region's
sensors:
  - global MAC (paired, all 132 measured DOFs)  -> the BEFORE-baseline global number
  - region-restricted MAC per paired mode       -> which modes are bad WHERE
  - per-mode frequency error                     -> freq vs shape attribution

Inputs (copied read-only into inherited_baseline/):
  obs_V.npy        FEM eigenvectors at the 76 accel nodes (228=76x3 rows, K modes)
  measured_modes.npz  .ash survey: nodes(76), freqs(33), shapes(33,76,3), measured(76,3)
  pairing.json     Hungarian one-to-one test<->FEM mode pairing
  ash_node_coords.npy  (76,3) physical coords of the .ash nodes [in]

MAC(a,b) = |a.b|^2 / ((a.a)(b.b)) in [0,1]; 1 = identical shape, 0 = orthogonal.
"""
import json, numpy as np
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
BASE = HERE / "inherited_baseline"
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)

# --- 8 hard channels (impact-hammer test locations, in) + physical grouping ---
HARD = {
    "ch4":  dict(xyz=(9.0, -1.5, 2.3),  region="source_face", desc="Source +X Face Center"),
    "ch27": dict(xyz=(9.0, 7.1, 1.9),   region="source_face", desc="Source +X Face +Y Edge"),
    "ch38": dict(xyz=(7.0, -9.0, 1.75), region="source_face", desc="Source -Y Face +X Edge (corner)"),
    "ch40": dict(xyz=(9.0, -0.4, 10.4), region="box_column",  desc="Steel Box Below Bulkhead"),
    "ch52": dict(xyz=(9.0, -0.4, 19.1), region="box_column",  desc="Al Box Above Bolted Joint"),
    "ch69": dict(xyz=(9.0, -0.4, 28.7), region="box_column",  desc="Al Box Below Bulkhead"),
    "ch92": dict(xyz=(8.7, 0.0, 49.6),  region="strut_base",  desc="Strut Base (+X)"),
    "ch98": dict(xyz=(1.9, 0.0, 57.0),  region="dish",        desc="Dish Center"),
}

# --- load baseline ---
mm = np.load(BASE / "measured_modes.npz", allow_pickle=True)
nodes = mm["nodes"]                      # (76,)
f_meas_all = mm["freqs"]                 # (33,)
shapes = mm["shapes"]                    # (33,76,3)
measured = mm["measured"]               # (76,3) bool
coords = np.load(BASE / "ash_node_coords.npy")  # (76,3)

obs_V = np.load(BASE / "obs_V.npy")     # (228, K) FEM shapes at accel nodes
pairing = json.load(open(BASE / "pairing.json"))
pairs = pairing["pairs"]                 # list of dicts test_mode/fem_mode/mac/...

# FEM eigenvectors reshaped to (76,3,K)
K = obs_V.shape[1]
obs_V_n = obs_V.reshape(76, 3, K)
# measured shapes reshaped to (76,3,33), zero where not measured
phi_tst_full = np.transpose(shapes, (1, 2, 0))  # (76,3,33)
mmask = measured  # (76,3)

# --- map each hard channel to nearest .ash node ---
for ch, info in HARD.items():
    d = np.linalg.norm(coords - np.array(info["xyz"]), axis=1)
    j = int(np.argmin(d))
    info["ash_node"] = int(nodes[j])
    info["ash_idx"] = j
    info["map_dist_in"] = float(d[j])
    info["node_measured_axes"] = [bool(x) for x in mmask[j]]

# --- region -> set of .ash node indices (the hard channels' nearest nodes) ---
regions = {}
for ch, info in HARD.items():
    regions.setdefault(info["region"], set()).add(info["ash_idx"])
regions = {r: sorted(s) for r, s in regions.items()}


def mac_restricted(node_idx, fem_idx0, test_idx0):
    """MAC between FEM mode (0-based col of obs_V) and test mode (0-based) over
    given nodes, measured axes only. Returns (mac, n_dof)."""
    fi, ti = fem_idx0, test_idx0
    a, b = [], []
    for j in node_idx:
        for ax in range(3):
            if mmask[j, ax]:
                a.append(obs_V_n[j, ax, fi])
                b.append(phi_tst_full[j, ax, ti])
    a, b = np.array(a), np.array(b)
    if a.size < 2 or np.dot(a, a) == 0 or np.dot(b, b) == 0:
        return float("nan"), int(a.size)
    return float(np.dot(a, b) ** 2 / (np.dot(a, a) * np.dot(b, b))), int(a.size)


# all measured node indices (for global MAC)
all_idx = list(range(76))

# --- per paired mode: global MAC + per-region MAC + freq error ---
mode_rows = []
for p in pairs:
    tm = p["test_mode"]                 # 1-based test mode
    ti0 = tm - 1                         # 0-based test index into shapes
    # pairing's model_mode is 0-based into the ELASTIC modes (after 6 RBM);
    # obs_V columns 0..5 are the rigid-body modes, so add 6.
    fi0 = p["model_mode"] + 6           # 0-based FEM column of obs_V
    f_test = float(f_meas_all[ti0])
    g_mac, g_ndof = mac_restricted(all_idx, fi0, ti0)
    row = dict(test_mode=tm, fem_mode=fi0 - 6 + 1, f_test_hz=f_test,
               f_fem_hz=p.get("f_model"), mac_global=g_mac,
               mac_pairing=p.get("mac"), df_pct=p.get("df_pct"))
    for r, idx in regions.items():
        m, n = mac_restricted(idx, fi0, ti0)
        row[f"mac_{r}"] = m
        row[f"ndof_{r}"] = n
    mode_rows.append(row)

# --- region summaries: mean region MAC over well-paired modes (global MAC>0.3) ---
well = [r for r in mode_rows if r["mac_global"] is not None and r["mac_global"] > 0.3]
region_summary = {}
for r in regions:
    vals = [row[f"mac_{r}"] for row in well if not np.isnan(row[f"mac_{r}"])]
    gvals = [row["mac_global"] for row in well]
    region_summary[r] = dict(
        n_modes=len(vals),
        mean_region_mac=float(np.mean(vals)) if vals else None,
        median_region_mac=float(np.median(vals)) if vals else None,
        mean_global_mac=float(np.mean(gvals)) if gvals else None,
        channels=[c for c, i in HARD.items() if i["region"] == r],
        worst_modes=sorted(
            [(row["test_mode"], round(row[f"mac_{r}"], 3), round(row["f_test_hz"], 1))
             for row in well if not np.isnan(row[f"mac_{r}"])],
            key=lambda t: t[1])[:5],
    )

out = dict(
    note="Card D Phase-1 region diagnosis, READ-ONLY, as-received FEM vs .ash survey",
    n_fem_modes=K, n_test_modes=len(f_meas_all), n_pairs=len(pairs),
    global_mac_matched_mean=float(np.mean([r["mac_global"] for r in well])),
    hard_channels=HARD, regions={r: idx for r, idx in regions.items()},
    region_summary=region_summary, mode_table=mode_rows,
)
json.dump(out, open(OUT / "region_diagnosis.json", "w"), indent=1, default=str)

print("=== global matched MAC (well-paired, MAC>0.3):",
      round(out["global_mac_matched_mean"], 3),
      f"over {len(well)} modes ===")
print("\nchannel -> nearest .ash node (map dist, in):")
for ch, info in HARD.items():
    print(f"  {ch:5s} {info['desc']:32s} node {info['ash_node']:5d} "
          f"d={info['map_dist_in']:.2f} axes={info['node_measured_axes']}")
print("\nregion summary (mean region MAC vs mean global MAC over well-paired modes):")
for r, s in region_summary.items():
    print(f"  {r:12s} chans={s['channels']}")
    print(f"     region MAC mean={s['mean_region_mac']} median={s['median_region_mac']} "
          f"| global mean={s['mean_global_mac']} | n={s['n_modes']}")
    print(f"     worst modes (test_mode, regionMAC, f_test): {s['worst_modes']}")
print("\nwrote out/region_diagnosis.json")
