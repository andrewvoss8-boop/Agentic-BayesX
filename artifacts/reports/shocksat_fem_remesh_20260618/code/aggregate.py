#!/usr/bin/env python3
"""Card D — aggregate the correlated-update campaign into a before/after table.

Reads out/edits/*/result.json. Baseline = baseline_reuse. Reports, per edit, the
change vs baseline in: global matched MAC, global calib MAC (>0.5), mean |df%|
(calib), and the per-region MACs at the hard regions. Flags any edit that
IMPROVES a hard-region metric WITHOUT degrading the global numbers.
"""
import json, os, glob
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)

res = {}
for f in glob.glob("out/edits/*/result.json"):
    s = json.load(open(f))["summary"]
    res[s["edit_id"]] = s
base = res.get("baseline_reuse")
if base is None:
    raise SystemExit("baseline_reuse not done yet")

regions = list(base["region_macs"].keys())
rows = []
for eid, s in sorted(res.items()):
    if eid == "baseline_reuse":
        continue
    d_mac = s["global_mac_matched_mean"] - base["global_mac_matched_mean"]
    d_calib = s["global_mac_calib_mean"] - base["global_mac_calib_mean"]
    d_df = s["mean_abs_df_pct_calib"] - base["mean_abs_df_pct_calib"]
    dreg = {}
    for r in regions:
        bv, sv = base["region_macs"].get(r), s["region_macs"].get(r)
        dreg[r] = (None if (bv is None or sv is None) else round(sv - bv, 4))
    # improvement = some hard-region metric up AND global not degraded
    global_not_worse = (d_mac >= -0.002) and (d_df <= 0.02)
    region_up = any((v is not None and v > 0.005) for v in dreg.values())
    freq_up = d_df < -0.02
    improved = (global_not_worse and (region_up or d_mac > 0.005)) or (freq_up and d_mac >= -0.002)
    rows.append(dict(edit_id=eid, note=s["edit"].get("note", ""),
        global_mac=round(s["global_mac_matched_mean"], 4), d_global_mac=round(d_mac, 4),
        global_calib_mac=round(s["global_mac_calib_mean"], 4), d_calib=round(d_calib, 4),
        mean_abs_df_pct=round(s["mean_abs_df_pct_calib"], 4), d_df_pct=round(d_df, 4),
        f_mode1=round(s["f_mode1_hz"], 3), region_macs={r: round(v, 4) if v else None for r, v in s["region_macs"].items()},
        d_region_macs=dreg, IMPROVED=improved))

out = dict(
    baseline=dict(global_mac=round(base["global_mac_matched_mean"], 4),
                  global_calib_mac=round(base["global_mac_calib_mean"], 4),
                  mean_abs_df_pct=round(base["mean_abs_df_pct_calib"], 4),
                  f_mode1=round(base["f_mode1_hz"], 3),
                  region_macs={r: round(v, 4) if v else None for r, v in base["region_macs"].items()}),
    n_edits=len(rows), n_improved=sum(r["IMPROVED"] for r in rows), edits=rows)
json.dump(out, open("out/before_after.json", "w"), indent=1)

print("BASELINE: global MAC %.4f  calib %.4f  |df%%| %.4f  f1 %.3f" % (
    base["global_mac_matched_mean"], base["global_mac_calib_mean"],
    base["mean_abs_df_pct_calib"], base["f_mode1_hz"]))
print("  region MACs:", out["baseline"]["region_macs"])
print("\n%-22s %8s %8s %8s  %s" % ("edit", "dMAC", "d|df%|", "f1", "regionMAC deltas"))
for r in rows:
    flag = "  <-- IMPROVED" if r["IMPROVED"] else ""
    print("%-22s %+8.4f %+8.4f %8.3f  %s%s" % (
        r["edit_id"], r["d_global_mac"], r["d_df_pct"], r["f_mode1"],
        r["d_region_macs"], flag))
print(f"\n{out['n_improved']} of {out['n_edits']} edits improved a hard-region metric "
      f"without degrading global. -> out/before_after.json")
