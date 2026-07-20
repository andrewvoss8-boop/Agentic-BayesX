#!/usr/bin/env python3
"""Re-freeze the Hungarian pairing of already-built packages under rule D12a (unobservable-mode exclusion).
Applied ONCE, uniformly, to packages built before D12 (A0, v3_dishrefine). Invalidates cached theta_map."""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femlib as F

for cid in sys.argv[1:]:
    p = os.path.join(F.WS, "data", "packages", f"{cid}.npz")
    z = np.load(p, allow_pickle=True)
    d = {k: z[k] for k in z.files}
    mm = np.load(os.path.join(F.REMESH, "measured_modes.npz"), allow_pickle=True)
    live = np.asarray(mm["measured"]).reshape(-1)
    msh = np.asarray(mm["shapes"], float).reshape(33, -1)[:, live]
    mfreqs = np.asarray(mm["freqs"], float)
    allowed = F.participation_mask(np.asarray(d["sens_rows"]))
    pairs, _ = F.hungarian_pairing(np.asarray(d["freqs_el"], float), np.asarray(d["ash_rows"]),
                                   live, mfreqs, msh, allowed=allowed)
    old = np.asarray(d["pairs"])
    d["pairs"] = np.array([[a, b, c] for a, b, c in pairs])
    np.savez_compressed(p, **d)
    tm = os.path.join(F.WS, "out", "theta_map", f"{cid}.json")
    if os.path.exists(tm):
        os.remove(tm)
    n_excl = int((~allowed).sum())
    changed = len(set(map(tuple, old[:, :2].astype(int))) ^ set((int(a), int(b)) for a, b, _ in pairs))
    print(f"{cid}: {n_excl} unobservable modes excluded; {changed} pair assignments changed; "
          f"{len(pairs)} pairs; theta_map cache cleared")
