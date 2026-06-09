#!/usr/bin/env python3
"""Step toward remedying the FEM-vs-test FRF normalization.

The earlier overlay self-normalized each curve to its own peak because a true
magnitude (g/lbf) comparison needs three things reconciled:
  (1) FEM force amplitude/units  -> the SOL111 deck applies a FLAT unit force
      (TABLED1 1001 = 1.0 across 0-400 Hz, FORCE ... 1.0 at grid 11101 +X), so
      the .pch acceleration (g) is already an accelerance: g per 1.0 force unit.
  (2) matched INPUT point  -> SOL111 drives at grid 11101/11110; the measured
      hammer test drives somewhere else. We must compare the SAME drive point.
  (3) matched OUTPUT point + axis -> SOL111 reports at modal grids 1101-7105;
      the tap channels map to 9900xxx grids. We must compare the SAME response
      location and axis.

This script parses the NASTRAN GRID coordinates, maps the three point sets by
physical XYZ, identifies which physical test (if any) matches each SOL111 force
point, and writes a reconciliation table. It does NOT fabricate a magnitude
overlay where the points do not match; it reports the gap honestly.
"""
from __future__ import annotations
import csv
import json
import re
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
CODEX = REPO / "artifacts/reports/shocksat_statfem_runner_20260609"
OUT = REPO / "artifacts/reports/shocksat_opus_20260609"
FEM = CODEX / "extracted/FEM"
INSTR_BLK = FEM / "FEM_20211021/Modal_Test_Instrumentation_092721.blk"
CHANNEL_MAP = CODEX / "channel_map.csv"
TESTLOG = CODEX / "test_log_summary.csv"


def nastran_float(s: str):
    s = s.strip()
    if not s:
        return None
    # insert E for embedded exponent sign, e.g. '8.93748-2' -> '8.93748E-2'
    m = re.match(r"^([+-]?\d*\.?\d+)([+-]\d+)$", s)
    if m:
        s = f"{m.group(1)}E{m.group(2)}"
    try:
        return float(s)
    except ValueError:
        return None


def parse_grids(path: Path) -> dict[int, tuple[float, float, float]]:
    """Parse small-field GRID cards: 8-col fields ID,CP,X1,X2,X3."""
    grids = {}
    if not path.exists():
        return grids
    for line in path.read_text(errors="ignore").splitlines():
        if not line.startswith("GRID") or line.startswith("GRID*"):
            continue
        f = [line[i:i + 8] for i in range(0, max(48, len(line)), 8)]
        try:
            gid = int(f[1])
        except (ValueError, IndexError):
            continue
        x = nastran_float(f[3]) if len(f) > 3 else None
        y = nastran_float(f[4]) if len(f) > 4 else None
        z = nastran_float(f[5]) if len(f) > 5 else None
        if None not in (x, y, z):
            grids[gid] = (x, y, z)
    return grids


def load_channel_grids() -> dict[int, dict]:
    """tap_impact accelerometers: daq_channel -> {grid,xyz,axis}."""
    out = {}
    with open(CHANNEL_MAP) as fh:
        for row in csv.DictReader(fh):
            if row.get("configuration") != "tap_impact":
                continue
            if row.get("quantity") != "acceleration":
                continue
            try:
                ch = int(row["daq_channel"])
                xyz = (float(row["x_in"]), float(row["y_in"]), float(row["z_in"]))
                grid = int(row["fem_grid"]) if row["fem_grid"] else None
            except (ValueError, KeyError):
                continue
            out[ch] = {"grid": grid, "xyz": xyz, "axis": row.get("structural_axis", ""),
                       "desc": row.get("description", "")}
    return out


def load_hammer_points() -> list[dict]:
    pts = []
    with open(TESTLOG) as fh:
        for row in csv.DictReader(fh):
            ip = (row.get("Impact Point") or "").strip()
            if not ip:
                continue
            nums = re.findall(r"[-+]?\d*\.?\d+", ip)
            if len(nums) < 3:
                continue
            pts.append({"file": row.get("Filename", ""), "test_type": row.get("test_type", ""),
                        "desc": row.get("Description", ""), "xyz": tuple(float(x) for x in nums[:3])})
    return pts


def nearest(target, candidates):
    """candidates: list of (key, xyz). Return (key, xyz, dist)."""
    best = None
    for key, xyz in candidates:
        d = float(np.linalg.norm(np.array(target) - np.array(xyz)))
        if best is None or d < best[2]:
            best = (key, xyz, d)
    return best


# --- parse ------------------------------------------------------------------
grids = parse_grids(INSTR_BLK)
force_pts = {gid: grids[gid] for gid in (11101, 11110) if gid in grids}
resp_pts = {gid: xyz for gid, xyz in grids.items() if 1000 <= gid <= 7999}  # 1101-7105 family
chan = load_channel_grids()
hammer = load_hammer_points()

print(f"parsed grids: {len(grids)}  (sanity 11101={grids.get(11101)})")
print(f"SOL111 force points: {force_pts}")
print(f"SOL111 response points (1101-7105 family): {len(resp_pts)}")
print(f"tap accelerometer channels: {len(chan)}")

# --- (2) which physical hammer test matches each SOL111 force point? --------
force_match = {}
hammer_cand = [(f"{h['file']}|{h['test_type']}", h["xyz"]) for h in hammer]
for gid, xyz in force_pts.items():
    key, mxyz, dist = nearest(xyz, hammer_cand)
    force_match[gid] = {"force_xyz": xyz, "nearest_hammer": key,
                        "hammer_xyz": mxyz, "dist_in": round(dist, 3)}
    print(f"force {gid} {xyz} -> nearest hammer {key} {mxyz} dist={dist:.2f} in")

# --- (3) do tap 9900xxx accelerometers coincide with SOL111 resp points? ----
resp_cand = [(gid, xyz) for gid, xyz in resp_pts.items()]
chan_match = {}
for ch, info in sorted(chan.items()):
    if not resp_cand:
        break
    key, mxyz, dist = nearest(info["xyz"], resp_cand)
    chan_match[ch] = {"tap_grid": info["grid"], "tap_xyz": info["xyz"], "axis": info["axis"],
                      "nearest_sol111_resp_grid": key, "resp_xyz": mxyz, "dist_in": round(dist, 3),
                      "desc": info["desc"]}

coincident = [c for c in chan_match.values() if c["dist_in"] <= 0.5]
print(f"\ntap accelerometers within 0.5 in of a SOL111 response point: "
      f"{len(coincident)} of {len(chan_match)}")
for ch, m in list(chan_match.items())[:6]:
    print(f"  ch{ch} grid{m['tap_grid']} {m['tap_xyz']} ax {m['axis']} -> "
          f"SOL111 {m['nearest_sol111_resp_grid']} {m['resp_xyz']} dist={m['dist_in']} in")

# --- verdict ----------------------------------------------------------------
verdict = {
    "fem_force_is_unit_flat": True,
    "fem_force_units_assumed": "lbf (consistent with inch geometry; confirm via model PARAM/material)",
    "pch_is_accelerance": "yes: g per 1.0 applied force unit (TABLED1 1001 flat 1.0, FORCE 1.0)",
    "sol111_force_points_in": {str(k): v for k, v in force_pts.items()},
    "force_to_hammer_match": {str(k): v for k, v in force_match.items()},
    "test07_is_input_matched_to_11101X": bool(
        any("Test07" in m["nearest_hammer"] and m["dist_in"] < 1.0
            for m in force_match.values() if m["force_xyz"] == force_pts.get(11101))),
    "tap_accel_coincident_with_sol111_resp_count": len(coincident),
    "tap_accel_total": len(chan_match),
    "normalization_blocker": None,
}
# decide the blocker honestly
min_force_dist = min((m["dist_in"] for m in force_match.values()), default=None)
if min_force_dist is None or min_force_dist > 1.0:
    verdict["normalization_blocker"] = (
        "No extracted hammer test drives at the SOL111 force point(s) within 1 in; a true "
        "input-matched magnitude overlay needs either the matching test or a NASTRAN SOL111 run "
        "at the actual hammer drive point. Frequency (peak) comparison remains valid.")
elif len(coincident) == 0:
    verdict["normalization_blocker"] = (
        "Input point matches but tap accelerometers (9900xxx) are not co-located with SOL111 "
        "response grids (1101-7105); need an output-point match or a modal-test channel set.")
else:
    verdict["normalization_blocker"] = (
        "Input and >=1 output point match: a units-consistent g/lbf overlay is feasible for "
        "those channels (pending force-unit confirmation and window/damping reconciliation).")

print("\nVERDICT:", verdict["normalization_blocker"])

out = {
    "purpose": "point/unit reconciliation to remedy FEM-vs-test FRF normalization",
    "force_points_in": {str(k): v for k, v in force_pts.items()},
    "force_to_hammer_match": {str(k): v for k, v in force_match.items()},
    "channel_match_sample": {str(k): v for k, v in list(chan_match.items())[:12]},
    "verdict": verdict,
}
(OUT / "opus_point_reconcile.json").write_text(json.dumps(out, indent=2))
print("\nwrote opus_point_reconcile.json")
