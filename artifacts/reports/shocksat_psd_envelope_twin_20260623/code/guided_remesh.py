#!/usr/bin/env python3
"""MAP-GUIDED remesh (Andrew): use the residual map (worst = bottom -Y corner + 54 Hz fundamental + 150-210 Hz) to
target a SPECIFIC edit instead of uniform group scaling. Soften the bottom box panels + the bottom-region bolted
joints (which the map says are too stiff / under-responding). Also check whether the 54 Hz fundamental (MAC 0.17 by
nearest-freq pairing) is a real shape gap or just a frequency MIS-PAIRING (best-MAC FEM mode for the measured 54 Hz).
Runs via correlate_all.score (one eigensolve). Output: console + out/edits/guided_*/correlate.json.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import correlate_all as CA
import remodel as RM

# identify bottom-region bolted joints (low column-height z) from the CBUSH node coords
zf = np.load(str(Path(RM.MT) / "fem_model.npz"), allow_pickle=True)
cb = zf["cbush"]; xyz = zf["xyz"]; g2i = RM.G2I
bush_z = {}
for pid in range(801, 808):
    sel = cb[cb[:, 1] == pid]
    if len(sel):
        zs = [xyz[g2i[int(ga)]][2] for _, _, ga, gb, _ in sel] + [xyz[g2i[int(gb)]][2] for _, _, ga, gb, _ in sel]
        bush_z[pid] = float(np.mean(zs))
bottom_bush = [p for p, zz in bush_z.items() if zz < 14.0]
print("bush joint mean-z:", {p: round(zz, 1) for p, zz in bush_z.items()}, "-> bottom joints:", bottom_bush)

edits = {
    "guided_bottom_soft": {"scale": {**{f"shell_{p}": 0.7 for p in (101, 102, 103)},
                                      **{f"bush_{p}": 0.5 for p in bottom_bush}}},
    "guided_bottom_softer": {"scale": {**{f"shell_{p}": 0.55 for p in (101, 102, 103)},
                                       **{f"bush_{p}": 0.3 for p in bottom_bush}}},
}
for eid, e in edits.items():
    r = CA.score(eid, e)
    print(f"{eid}: FRFcorr {r['FRF_logmag_corr_median']:.3f} (baseline 0.296, best-so-far 0.359) | "
          f"ampErr {r['FRF_peak_ampl_err_dB_median']:.1f}dB | MAC {r['global_MAC']:.3f}")
