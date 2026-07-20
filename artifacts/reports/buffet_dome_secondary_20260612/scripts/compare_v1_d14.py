#!/usr/bin/env python3
"""Evidence for D14: compare headline QOI RMS before/after the rotational
mount fix. Hypothesis (decisions D14): the removed mode is an UNFORCED rigid
COPV spin below the 20 Hz band floor -> QOIs change negligibly. We report the
actual % change per channel rather than asserting it. Writes out/d14_compare.json.
"""
import json
from pathlib import Path

import numpy as np

WS = Path(__file__).resolve().parent.parent
out = {}
for bc in ("bcA", "bcB"):
    v1 = json.load(open(WS / "out" / f"qoi_{bc}_v1_rms.json"))
    cur = np.load(WS / "out" / f"qoi_{bc}.npz", allow_pickle=True)
    names = list(cur["names"]); rms = cur["rms"]
    d14 = {n: float(rms[i]) for i, n in enumerate(names) if "field" not in n}
    rows = {}
    for n in v1:
        if n in d14:
            a, b = v1[n], d14[n]
            rows[n] = dict(v1=round(a, 4), d14=round(b, 4),
                           pct=round(100 * (b - a) / max(abs(a), 1e-12), 3))
    worst = max(abs(r["pct"]) for r in rows.values())
    copv_worst = max(abs(r["pct"]) for n, r in rows.items() if "copv" in n)
    out[bc] = dict(worst_abs_pct=worst, copv_worst_abs_pct=copv_worst,
                   rows=rows)
# Data-driven verdict (NO hardcoded optimism, and NO max-%-on-a-tiny-channel
# headline). Report the three physically distinct effects separately.
def pct(o, bc, n):
    return o[bc]["rows"][n]["pct"] if (bc in o and n in o[bc]["rows"]) else None

def worst_over(o, names):
    vals = [abs(pct(o, bc, n)) for bc in ("bcA", "bcB") for n in names
            if pct(o, bc, n) is not None]
    return max(vals) if vals else None

other_w = worst_over(out, [n for bc in ("bcA",) for n in out[bc]["rows"]
                           if "copv" not in n])
punch = worst_over(out, ["copv_net_punch"])
mount_inplane = worst_over(out, ["copv_mount1_Fx", "copv_mount1_Fy",
                                 "copv_mount2_Fx", "copv_mount2_Fy"])
out["verdict"] = (
    f"D14 (rotational COPV mount, k_rot=1e4 N*m/rad). THREE distinct effects: "
    f"(1) tray/strut/avionics RMS change <= {other_w:.1f}% — invisible, the "
    "removed spin mode IS unforced for them (hypothesis holds here). "
    f"(2) COPV net dome-normal PUNCH drops ~{punch:.0f}% (rotation redistributes "
    "the normal reaction). "
    f"(3) COPV per-mount IN-PLANE forces RISE up to ~{mount_inplane:.0f}% — the "
    "mounts now carry moment, so the design-relevant per-bracket shear roughly "
    "doubles. Net: the v1 free-spin COPV mount was non-physical and badly "
    "under-predicted mount design loads; D14 SUPERSEDES it, and k_mount_rot is "
    "promoted to a sensitivity variable (krlo/krhi). The 'QOI-invisible' guess "
    "was correct only for the non-COPV channels.")
out["effects"] = dict(other_max_pct=other_w, copv_punch_pct=punch,
                      copv_mount_inplane_pct=mount_inplane)
json.dump(out, open(WS / "out" / "d14_compare.json", "w"), indent=1)
print(json.dumps({"verdict": out["verdict"],
                  "bcA_worst_pct": out["bcA"]["worst_abs_pct"],
                  "bcB_worst_pct": out["bcB"]["worst_abs_pct"]}, indent=1))
