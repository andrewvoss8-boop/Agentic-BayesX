#!/usr/bin/env python3
"""One-to-one (Hungarian) test<->model mode pairing at nominal theta.

The greedy per-test argmax pairing in solve_nominal collides (two test modes
grab the same model mode) and lets a high model mode spatially-alias onto a
low test mode. A global assignment that uses each model mode at most once
removes both pathologies and matches how NASA reports a 1:1 correlation.

We maximize total MAC over a frequency-gated cost: pairs with |df|/f > 0.18
are forbidden (cost = +inf) so a 318 Hz model mode cannot pair to a 234 Hz
test mode. Outputs pairing.json: per test mode the assigned NOMINAL elastic
model-mode index (0-based in the elastic ordering), its frequency, MAC, df%,
and a 'calib_ok' flag (MAC>=0.5 AND |df|<=0.12 AND not a duplicate).
"""
import json
import numpy as np
from scipy.optimize import linear_sum_assignment

DF_FORBID = 0.18
MAC_MIN = 0.50
DF_CALIB = 0.12

mm = np.load("measured_modes.npz")
nodes, mfreqs, mshapes, mmask = (mm["nodes"], mm["freqs"], mm["shapes"],
                                 mm["measured"])
live = mmask.reshape(-1)                       # (228,)
phi_tst = mshapes.reshape(33, -1)[:, live]     # (33,132)

obs_V = np.load("matrices/obs_V.npy")[:, 6:]   # (228,74) nominal elastic
freqs = np.sqrt(np.load("matrices/eigvals.npy")[6:]) / (2 * np.pi)
phi_fem = obs_V[live, :]                        # (132,74)

num = (phi_tst @ phi_fem) ** 2
den = (np.sum(phi_tst ** 2, 1)[:, None] * np.sum(phi_fem ** 2, 0)[None, :])
MAC = num / den                                # (33,74)
DF = freqs[None, :] / mfreqs[:, None] - 1.0    # (33,74) signed

cost = -MAC.copy()
cost[np.abs(DF) > DF_FORBID] = 1e3             # forbid wild-frequency pairs
ri, ci = linear_sum_assignment(cost)

pairs = []
for it, jf in zip(ri, ci):
    forb = cost[it, jf] >= 1e3
    pairs.append(dict(
        test_mode=int(it + 1), f_test=float(mfreqs[it]),
        model_mode=int(jf), f_model=float(freqs[jf]),
        mac=float(MAC[it, jf]), df_pct=float(100 * DF[it, jf]),
        calib_ok=bool((not forb) and MAC[it, jf] >= MAC_MIN
                      and abs(DF[it, jf]) <= DF_CALIB)))
pairs.sort(key=lambda p: p["test_mode"])

calib = [p for p in pairs if p["calib_ok"]]
out = dict(df_forbid=DF_FORBID, mac_min=MAC_MIN, df_calib=DF_CALIB,
           n_calib_ok=len(calib),
           calib_test_modes=[p["test_mode"] for p in calib],
           pairs=pairs)
json.dump(out, open("pairing.json", "w"), indent=1)

print(f"unique pairing; calib_ok = {len(calib)} modes: "
      f"{[p['test_mode'] for p in calib]}")
for p in pairs:
    flag = "CAL" if p["calib_ok"] else "   "
    print(f"{flag} test {p['test_mode']:2d} {p['f_test']:7.2f} -> "
          f"model#{p['model_mode']:2d} {p['f_model']:7.2f}  "
          f"MAC {p['mac']:.3f}  df {p['df_pct']:+.2f}%")
