#!/usr/bin/env python3
"""Sensitivity gate: tabulate headline-QOI RMS for each structural variant vs
the v1 baseline (both pre-D14, so the comparison is consistent; D14's COPV
rotational term is QOI-invisible per d14_compare.json). Variants vary the
parameters most likely to move the QOI/decision (mount/joint stiffness, dome
gauge) + a refined mesh for discretization convergence. Writes
out/variant_summary.json + a markdown table fragment.
"""
import json
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
# Baseline = the D14 NOMINAL (qoi_bcA_summary.json), so every variant ratio is
# consistent with the rotational-mount model. (v1 was the pre-D14 free-spin
# baseline; superseded.)
base = json.load(open(WS / "out" / "qoi_bcA_summary.json"))["rms_headline"]
LABELS = {
    "kmlo": "COPV mount trans soft (k_mount 1e7->1e6)",
    "kmhi": "COPV mount trans stiff (k_mount 1e7->1e8)",
    "krlo": "COPV mount ROT soft (k_rot 1e4->1e3)",
    "krhi": "COPV mount ROT stiff (k_rot 1e4->1e5)",
    "kjlo": "tray joints soft (k_joint 1e7->1e6)",
    "tdlo": "dome thin (t 5->3 mm, model-form)",
    "meshf": "refined mesh (Nth 240->300) — convergence",
}
CHANNELS = ["strut_5_F", "tray_net_punch", "copv_net_punch", "av_acc_z"]
rows = {}
for tag, desc in LABELS.items():
    p = WS / "out" / f"qoi_bcA_{tag}_summary.json"
    if not p.exists():
        rows[tag] = dict(desc=desc, status="pending")
        continue
    rh = json.load(open(p))["rms_headline"]
    rows[tag] = dict(desc=desc, status="done",
                     ratios={c: round(rh[c] / base[c], 3) for c in CHANNELS})
out = dict(baseline_v1_rms={c: round(base[c], 3) for c in CHANNELS},
           channels=CHANNELS, variants=rows,
           note="ratios = variant RMS / v1-baseline RMS (both pre-D14). "
                "meshf = discretization convergence (ratio ~1 confirms the "
                "240-element mesh is converged for the QOI).")
json.dump(out, open(WS / "out" / "variant_summary.json", "w"), indent=1)

# markdown fragment
lines = ["| variant | strut | tray punch | COPV punch | avionics az |",
         "|---|---|---|---|---|"]
for tag, r in rows.items():
    if r["status"] != "done":
        lines.append(f"| {r['desc']} | _pending_ | | | |")
        continue
    rt = r["ratios"]
    lines.append(f"| {r['desc']} | x{rt['strut_5_F']:.2f} | "
                 f"x{rt['tray_net_punch']:.2f} | x{rt['copv_net_punch']:.2f} | "
                 f"x{rt['av_acc_z']:.2f} |")
open(WS / "out" / "variant_table.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
print("\nbaseline v1 RMS:", out["baseline_v1_rms"])
